"""
ARCH Message Router

This module handles routing messages to appropriate agents and implementing
escalation logic based on message type and phase policy rules.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import shutil

from .message_parser import MessageType, MessageParser
from .phase_policy_loader import PhasePolicy, load_policy, RoutingRule, EscalationLevel, EscalationRule

class MessageRouter:
    """Router for ARCH messages."""
    
    def __init__(
        self,
        postbox_root: Path,
        phase_policy_path: Optional[Path] = None,
        log_dir: Optional[Path] = None
    ):
        """Initialize the message router.
        
        Args:
            postbox_root: Root directory for message postboxes
            phase_policy_path: Optional path to phase policy file
            log_dir: Optional directory for logging
        """
        self.postbox_root = postbox_root
        self.phase_policy_path = phase_policy_path
        self.log_dir = log_dir
        
        # Always set up a logger
        self.logger = logging.getLogger("arch_message_router")
        if not self.logger.handlers:
            if log_dir:
                log_dir.mkdir(parents=True, exist_ok=True)
                handler = logging.FileHandler(log_dir / "message_router.log")
            else:
                handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        # Initialize components
        self.parser = MessageParser(log_dir)
        self.policy = self._load_phase_policy() if phase_policy_path else None
        
        # Retry state tracking
        self.retry_state = {}  # message_id -> retry_count
    
    def _load_phase_policy(self) -> Optional[PhasePolicy]:
        """Load the phase policy from file.
        
        Returns:
            Loaded phase policy or None if loading fails
        """
        if not self.phase_policy_path or not self.phase_policy_path.exists():
            return None
        
        try:
            policy = load_policy(self.phase_policy_path)
            if self.logger:
                self.logger.info(f"Loaded phase policy from {self.phase_policy_path}")
            return policy
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to load phase policy: {str(e)}")
            return None
    
    def route_message(self, message: Dict[str, Any]) -> Optional[RoutingRule]:
        """Route a message to its destination using MCP envelope fields."""
        try:
            # Parse and validate message (now expects MCP envelope)
            parsed = self.parser.parse_message(message)

            # Log trace_id and retry_count
            trace_id = parsed.get("trace_id")
            retry_count = parsed.get("retry_count", 0)
            if self.logger:
                self.logger.info(f"Routing message trace_id={trace_id} retry_count={retry_count}")

            # Extract payload for message type and content
            payload = parsed.get("payload", {})
            message_type_str = payload.get("type")
            if not message_type_str:
                self._escalate_to_human(message, "Message payload missing type field")
                return None
            
            # Get message type
            message_type = MessageType(message_type_str)
            
            # Handle error messages with retry logic
            if message_type == MessageType.ERROR:
                return self._handle_error_with_retry(parsed)

            # Use envelope fields for routing
            sender_id = parsed.get("sender_id")
            recipient_id = parsed.get("recipient_id")
            task_id = parsed.get("task_id")

            # Find matching rule for non-error messages
            rule = self._find_matching_rule(message_type, payload)
            if not rule:
                # Fallback to recipient_id from envelope
                destination = recipient_id
                if not destination:
                    self._escalate_to_human(message, "No recipient_id in envelope and no matching rule")
                    return None
                
                # Write message to destination inbox
                self.write_to_inbox(message, destination)
                return RoutingRule(
                    id=f"route_{task_id}",
                    destination=destination,
                    escalation_level=EscalationLevel.NONE
                )

            # Write message to destination
            self.write_to_inbox(message, rule.destination)
            return rule
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error routing message: {str(e)}")
            self._escalate_to_human(message, f"Routing error: {str(e)}")
            return None
    
    def _find_matching_rule(self, message_type: MessageType, message: Dict[str, Any]) -> Optional[RoutingRule]:
        """Find a matching routing rule for the message.
        
        Args:
            message_type: Type of message
            message: Parsed message
            
        Returns:
            Matching routing rule or None if no match found
        """
        if not self.policy:
            # Use default rules if no policy
            if message_type == MessageType.TASK_RESULT:
                return RoutingRule(
                    id="default_task_result",
                    destination="ARCH",
                    escalation_level=EscalationLevel.NONE
                )
            elif message_type == MessageType.ERROR:
                return RoutingRule(
                    id="default_error",
                    destination="CC",
                    escalation_level=EscalationLevel.AGENT
                )
            elif message_type == MessageType.NEEDS_INPUT:
                return RoutingRule(
                    id="default_needs_input",
                    destination="ARCH",
                    escalation_level=EscalationLevel.HUMAN
                )
            return None
        
        # Find matching rule from policy
        rules = []
        if message_type == MessageType.TASK_RESULT:
            rules = self.policy.task_result_rules
        elif message_type == MessageType.ERROR:
            rules = self.policy.error_rules
        elif message_type == MessageType.NEEDS_INPUT:
            rules = self.policy.input_rules
        
        for rule in rules:
            if self._rule_matches(rule, message):
                return rule
        
        return None
    
    def _rule_matches(self, rule: RoutingRule, message: Dict[str, Any]) -> bool:
        """Check if a rule matches a message.
        
        Args:
            rule: Routing rule to check
            message: Message to match
            
        Returns:
            True if rule matches message, False otherwise
        """
        if not rule.conditions:
            return True
        
        for condition in rule.conditions:
            value = message.get(condition.field)
            if value is None:
                return False
            
            if condition.operator == "eq" and value != condition.value:
                return False
            elif condition.operator == "neq" and value == condition.value:
                return False
            elif condition.operator == "gt" and value <= condition.value:
                return False
            elif condition.operator == "lt" and value >= condition.value:
                return False
        
        return True
    
    def _handle_error_with_retry(self, message: Dict[str, Any]) -> Optional[RoutingRule]:
        """Handle error messages with retry logic.
        
        Args:
            message: Error message to handle (MCP envelope format)
            
        Returns:
            Routing rule for the message or None if escalated
        """
        # Extract information from MCP envelope
        trace_id = message.get("trace_id", "unknown")
        current_retries = message.get("retry_count", 0)
        task_id = message.get("task_id", "unknown")
        payload = message.get("payload", {})
        
        # Determine retry limit from policy
        retry_limit = self._get_retry_limit_for_error(payload)
        
        # Check if we should retry
        if current_retries < retry_limit:
            # Increment retry count in envelope
            message["retry_count"] = current_retries + 1
            
            # Find original recipient to reassign
            original_recipient = self._get_original_task_recipient(payload)
            if original_recipient:
                # Update envelope destination
                message["recipient_id"] = original_recipient
                
                # Reassign to original agent
                self.write_to_inbox(message, original_recipient)
                
                if self.logger:
                    self.logger.info(f"Retrying message {trace_id} (attempt {current_retries + 1}/{retry_limit}) - reassigned to {original_recipient}")
                
                # Return rule for retry
                return RoutingRule(
                    id=f"retry_{trace_id}",
                    destination=original_recipient,
                    escalation_level=EscalationLevel.AGENT,
                    max_retries=retry_limit
                )
        
        # Exceeded retries or no original recipient - escalate
        if self.logger:
            self.logger.warning(f"Message {trace_id} exceeded retry limit ({retry_limit}) - escalating to human")
        
        self._escalate_to_human(message, f"Failed after {current_retries} retry attempts")
        return None
    
    def _get_retry_count(self, message: Dict[str, Any]) -> int:
        """Get current retry count for a message.
        
        Args:
            message: Message to check
            
        Returns:
            Current retry count
        """
        # Check if retry count is in message metadata
        retry_count = message.get("metadata", {}).get("retry_count", 0)
        
        # Also check internal state tracking
        message_id = message.get("metadata", {}).get("message_id", "unknown")
        state_retries = self.retry_state.get(message_id, 0)
        
        # Return the higher of the two
        return max(retry_count, state_retries)
    
    def _increment_retry_count(self, message: Dict[str, Any]) -> None:
        """Increment retry count for a message.
        
        Args:
            message: Message to increment retry count for
        """
        message_id = message.get("metadata", {}).get("message_id", "unknown")
        current_count = self._get_retry_count(message)
        new_count = current_count + 1
        
        # Update message metadata
        if "metadata" not in message:
            message["metadata"] = {}
        message["metadata"]["retry_count"] = new_count
        message["metadata"]["last_retry"] = datetime.now().isoformat()
        
        # Update internal state
        self.retry_state[message_id] = new_count
    
    def _get_retry_limit_for_error(self, message: Dict[str, Any]) -> int:
        """Get retry limit for an error message based on policy.
        
        Args:
            message: Error message
            
        Returns:
            Retry limit for this error type
        """
        if not self.policy or not self.policy.escalation_rules:
            return 3  # Default retry limit
        
        # Determine error type from message content
        error_type = self._classify_error_type(message)
        
        # Find matching escalation rule
        for rule in self.policy.escalation_rules:
            if rule.type == error_type:
                return rule.retry_count
        
        # Default for general errors
        for rule in self.policy.escalation_rules:
            if rule.type == "error":
                return rule.retry_count
        
        return 3  # Fallback default
    
    def _classify_error_type(self, message: Dict[str, Any]) -> str:
        """Classify error type based on message content.
        
        Args:
            message: Error message
            
        Returns:
            Error type classification
        """
        content = message.get("content", {})
        error_message = content.get("error", "").lower()
        
        # Check for critical errors
        critical_keywords = ["security", "data loss", "system breaking", "critical", "fatal"]
        if any(keyword in error_message for keyword in critical_keywords):
            return "critical_error"
        
        # Check for dependency blocking
        dependency_keywords = ["dependency", "blocked", "waiting for", "requires"]
        if any(keyword in error_message for keyword in dependency_keywords):
            return "dependency_blocked"
        
        # Check for resource constraints
        resource_keywords = ["quota", "limit", "memory", "disk", "cpu", "resource"]
        if any(keyword in error_message for keyword in resource_keywords):
            return "resource_constraint"
        
        # Default to general error
        return "error"
    
    def _get_original_task_recipient(self, message: Dict[str, Any]) -> Optional[str]:
        """Get the original recipient for a failed task.
        
        Args:
            message: Error message
            
        Returns:
            Original task recipient or None if not found
        """
        # Check if original recipient is in error message
        content = message.get("content", {})
        
        # Try to get from task_id or related_task_id
        task_id = content.get("task_id") or content.get("related_task_id")
        if task_id:
            # Simple heuristic: assign based on task patterns
            if "CC" in task_id or "code" in content.get("error", "").lower():
                return "CC"
            elif "WA" in task_id or "web" in content.get("error", "").lower():
                return "WA"
            elif "CA" in task_id or "analysis" in content.get("error", "").lower():
                return "CA"
        
        # Default to CC for code-related errors
        return "CC"
    
    def write_to_inbox(self, message: Dict[str, Any], destination: str) -> None:
        """Write a message to a destination inbox.
        
        Args:
            message: Message to write (MCP envelope format)
            destination: Destination inbox name
            
        Raises:
            Exception: If writing to inbox fails
        """
        try:
            # Create destination directory
            inbox_dir = self.postbox_root / destination
            inbox_dir.mkdir(parents=True, exist_ok=True)
            
            # Write message to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Use trace_id for MCP envelope or fallback to task_id
            message_id = message.get("trace_id") or message.get("task_id", "unknown")
            message_file = inbox_dir / f"message_{timestamp}_{message_id}.json"
            
            with open(message_file, "w") as f:
                json.dump(message, f, indent=2)
            
            if self.logger:
                self.logger.info(f"Wrote message to {message_file}")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to write message to inbox: {str(e)}")
            raise Exception(f"Failed to write message to inbox: {str(e)}")
    
    def _escalate_to_human(self, message: Dict[str, Any], reason: str) -> None:
        """Escalate a message to human attention.
        
        Args:
            message: Message to escalate
            reason: Reason for escalation
        """
        # Add escalation metadata
        message["escalation"] = {
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        
        # Write to human inbox
        try:
            self.write_to_inbox(message, "HUMAN")
            if self.logger:
                self.logger.info(f"Escalated to human: {reason}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to escalate to human: {str(e)}") 