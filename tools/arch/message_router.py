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

from .message_parser import MessageType, MessageParser
from tools.phase_policy_loader import PhasePolicy, load_policy

class EscalationLevel(Enum):
    """Enumeration of escalation levels."""
    NONE = "none"
    AGENT = "agent"
    HUMAN = "human"

@dataclass
class RoutingRule:
    """Configuration for message routing rules."""
    destination: str
    escalation_level: EscalationLevel
    max_retries: int = 3
    retry_delay: int = 60  # seconds
    policy_rule: Optional[str] = None  # ID of policy rule that created this

class MessageRouter:
    """Routes messages to appropriate destinations and handles escalation."""
    
    def __init__(
        self,
        postbox_root: Path,
        phase_policy_path: Optional[Path] = None,
        log_dir: Optional[Path] = None
    ):
        """Initialize the message router.
        
        Args:
            postbox_root: Root directory containing agent postboxes
            phase_policy_path: Optional path to phase policy YAML
            log_dir: Optional directory for logging
        """
        self.postbox_root = postbox_root
        self.phase_policy_path = phase_policy_path
        self.parser = MessageParser(log_dir)
        self.routing_rules: Dict[str, RoutingRule] = {}
        self.phase_policy: Optional[PhasePolicy] = None
        
        # Set up logging
        self.logger = logging.getLogger("arch_message_router")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
            
        # Load default routing rules
        self._load_default_rules()
        
        # Load phase policy if provided
        if phase_policy_path and phase_policy_path.exists():
            self._load_phase_policy()
    
    def _load_default_rules(self) -> None:
        """Load default routing rules."""
        self.routing_rules = {
            MessageType.TASK_RESULT.value: RoutingRule(
                destination="ARCH",
                escalation_level=EscalationLevel.NONE,
                policy_rule="default_task_result"
            ),
            MessageType.ERROR.value: RoutingRule(
                destination="CC",
                escalation_level=EscalationLevel.AGENT,
                max_retries=3,
                policy_rule="default_error"
            ),
            MessageType.NEEDS_INPUT.value: RoutingRule(
                destination="ARCH",
                escalation_level=EscalationLevel.HUMAN,
                policy_rule="default_needs_input"
            )
        }
    
    def _load_phase_policy(self) -> None:
        """Load routing rules from phase policy file."""
        try:
            self.phase_policy = load_policy(self.phase_policy_path)
            self.logger.info(f"Loaded phase policy from {self.phase_policy_path}")
            
            # Update routing rules based on policy
            self._update_routing_rules()
            
        except Exception as e:
            self.logger.error(f"Error loading phase policy: {e}")
            self.logger.info("Using default routing rules")
    
    def _update_routing_rules(self) -> None:
        """Update routing rules based on phase policy."""
        if not self.phase_policy:
            return
            
        # Update task result rules
        if self.phase_policy.task_result_rules:
            for rule in self.phase_policy.task_result_rules:
                self.routing_rules[MessageType.TASK_RESULT.value] = RoutingRule(
                    destination=rule.destination,
                    escalation_level=EscalationLevel(rule.escalation_level),
                    max_retries=rule.max_retries,
                    retry_delay=rule.retry_delay,
                    policy_rule=rule.id
                )
                
        # Update error rules
        if self.phase_policy.error_rules:
            for rule in self.phase_policy.error_rules:
                self.routing_rules[MessageType.ERROR.value] = RoutingRule(
                    destination=rule.destination,
                    escalation_level=EscalationLevel(rule.escalation_level),
                    max_retries=rule.max_retries,
                    retry_delay=rule.retry_delay,
                    policy_rule=rule.id
                )
                
        # Update input request rules
        if self.phase_policy.input_rules:
            for rule in self.phase_policy.input_rules:
                self.routing_rules[MessageType.NEEDS_INPUT.value] = RoutingRule(
                    destination=rule.destination,
                    escalation_level=EscalationLevel(rule.escalation_level),
                    max_retries=rule.max_retries,
                    retry_delay=rule.retry_delay,
                    policy_rule=rule.id
                )
    
    def route_message(self, message: Dict[str, Any]) -> None:
        """Route a message to its destination.
        
        Args:
            message: Message to route
        """
        try:
            # Parse and validate message
            parsed = self.parser.parse_message(message)
            msg_type = parsed["type"].value
            
            # Get routing rule
            rule = self.routing_rules.get(msg_type)
            if not rule:
                self.logger.warning(f"No routing rule for message type: {msg_type}")
                return
                
            # Check for retries
            retry_count = message.get("metadata", {}).get("retry_count", 0)
            if retry_count >= rule.max_retries:
                self._handle_max_retries(parsed, rule)
                return
                
            # Route based on type
            if msg_type == MessageType.TASK_RESULT.value:
                self._handle_task_result(parsed, rule)
            elif msg_type == MessageType.ERROR.value:
                self._handle_error(parsed, rule)
            elif msg_type == MessageType.NEEDS_INPUT.value:
                self._handle_input_request(parsed, rule)
                
        except Exception as e:
            self.logger.error(f"Error routing message: {e}")
            self._escalate_to_human(message, f"Routing error: {str(e)}")
    
    def _handle_task_result(self, parsed: Dict[str, Any], rule: RoutingRule) -> None:
        """Handle a task result message.
        
        Args:
            parsed: Parsed message
            rule: Routing rule
        """
        # Write to destination inbox
        self._write_to_inbox(rule.destination, parsed)
        self.logger.info(
            f"Routed task result to {rule.destination}: "
            f"Task {parsed['content'].task_id} {parsed['content'].status} "
            f"(Policy rule: {rule.policy_rule})"
        )
    
    def _handle_error(self, parsed: Dict[str, Any], rule: RoutingRule) -> None:
        """Handle an error message.
        
        Args:
            parsed: Parsed message
            rule: Routing rule
        """
        if rule.escalation_level == EscalationLevel.HUMAN:
            self._escalate_to_human(parsed, parsed["content"].error_message)
        else:
            # Route to agent for handling
            self._write_to_inbox(rule.destination, parsed)
            self.logger.info(
                f"Routed error to {rule.destination}: "
                f"{parsed['content'].error_type} "
                f"(Policy rule: {rule.policy_rule})"
            )
    
    def _handle_input_request(self, parsed: Dict[str, Any], rule: RoutingRule) -> None:
        """Handle an input request message.
        
        Args:
            parsed: Parsed message
            rule: Routing rule
        """
        if rule.escalation_level == EscalationLevel.HUMAN:
            self._escalate_to_human(parsed, parsed["content"].prompt)
        else:
            # Route to agent for handling
            self._write_to_inbox(rule.destination, parsed)
            self.logger.info(
                f"Routed input request to {rule.destination}: "
                f"{parsed['content'].request_type} "
                f"(Policy rule: {rule.policy_rule})"
            )
    
    def _handle_max_retries(self, parsed: Dict[str, Any], rule: RoutingRule) -> None:
        """Handle message that has exceeded max retries.
        
        Args:
            parsed: Parsed message
            rule: Routing rule
        """
        self.logger.warning(
            f"Message exceeded max retries ({rule.max_retries}): "
            f"{parsed['metadata'].message_id} "
            f"(Policy rule: {rule.policy_rule})"
        )
        self._escalate_to_human(
            parsed,
            f"Max retries ({rule.max_retries}) exceeded for message"
        )
    
    def _write_to_inbox(self, agent: str, message: Dict[str, Any]) -> None:
        """Write a message to an agent's inbox.
        
        Args:
            agent: Agent identifier
            message: Message to write
        """
        inbox_path = self.postbox_root / agent / "inbox.json"
        
        try:
            # Read existing messages
            if inbox_path.exists():
                with open(inbox_path, "r") as f:
                    messages = json.load(f)
            else:
                messages = []
                
            # Add new message
            messages.append(message)
            
            # Write back to file
            with open(inbox_path, "w") as f:
                json.dump(messages, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error writing to {agent} inbox: {e}")
            raise
    
    def _escalate_to_human(self, message: Dict[str, Any], reason: str) -> None:
        """Escalate a message to human attention.
        
        Args:
            message: Message to escalate
            reason: Reason for escalation
        """
        # Add escalation metadata
        message["escalation"] = {
            "reason": reason,
            "timestamp": message["metadata"]["timestamp"]
        }
        
        # Write to ARCH inbox for human review
        self._write_to_inbox("ARCH", message)
        self.logger.info(f"Escalated to human: {reason}") 