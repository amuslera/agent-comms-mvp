"""
Alert evaluator for ARCH message routing and alert triggers.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import requests
from .alert_policy_loader import AlertPolicy, AlertRule, AlertCondition, AlertAction

class AlertEvaluator:
    """Evaluates messages against alert rules and triggers actions."""
    
    def __init__(
        self,
        alert_policy_path: Path,
        postbox_root: Path,
        log_dir: Optional[Path] = None
    ):
        """Initialize the alert evaluator.
        
        Args:
            alert_policy_path: Path to alert policy YAML
            postbox_root: Root directory for message postboxes
            log_dir: Optional directory for logging
        """
        self.alert_policy_path = alert_policy_path
        self.postbox_root = postbox_root
        self.log_dir = log_dir
        
        # Set up logging
        self.logger = logging.getLogger("arch_alert_evaluator")
        if not self.logger.handlers:
            if log_dir:
                log_dir.mkdir(parents=True, exist_ok=True)
                handler = logging.FileHandler(log_dir / "alert_evaluator.log")
            else:
                handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        # Load alert policy
        self.policy = self._load_alert_policy()
        
        # Set up alert log path
        self.alert_log_path = Path(log_dir) / "alerts_triggered.json" if log_dir else None
        if self.alert_log_path:
            self.alert_log_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.alert_log_path.exists():
                with open(self.alert_log_path, "w") as f:
                    json.dump([], f)
    
    def _load_alert_policy(self) -> Optional[AlertPolicy]:
        """Load the alert policy from file.
        
        Returns:
            Loaded alert policy or None if loading fails
        """
        try:
            from .alert_policy_loader import load_alert_policy
            policy = load_alert_policy(self.alert_policy_path)
            if self.logger:
                self.logger.info(f"Loaded alert policy from {self.alert_policy_path}")
            return policy
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to load alert policy: {str(e)}")
            return None
    
    def evaluate_message(self, message: Dict[str, Any]) -> List[AlertRule]:
        """Evaluate a message against alert rules.
        
        Args:
            message: MCP message to evaluate
            
        Returns:
            List of matching alert rules
        """
        if not self.policy:
            return []
        
        matching_rules = []
        payload = message.get("payload", {})
        message_type = payload.get("type")
        sender_id = message.get("sender_id")
        retry_count = message.get("retry_count", 0)
        
        for rule in self.policy.rules:
            if not rule.enabled:
                continue
                
            if self._rule_matches(rule.condition, message_type, sender_id, retry_count, payload):
                matching_rules.append(rule)
                self._trigger_alert(rule, message)
        
        return matching_rules
    
    def _rule_matches(
        self,
        condition: AlertCondition,
        message_type: str,
        sender_id: str,
        retry_count: int,
        payload: Dict[str, Any]
    ) -> bool:
        """Check if a rule condition matches a message.
        
        Args:
            condition: Alert condition to check
            message_type: Type of message
            sender_id: ID of sending agent
            retry_count: Current retry count
            payload: Message payload
            
        Returns:
            True if condition matches, False otherwise
        """
        # Check message type
        if condition.type != message_type:
            return False
            
        # Check agent filter
        if condition.agent != "*" and condition.agent != sender_id:
            return False
            
        # Check retry count for error messages
        if message_type == "error" and condition.retry_count is not None:
            if retry_count < condition.retry_count:
                return False
                
        # Check error code
        if message_type == "error" and condition.error_code:
            error_code = payload.get("content", {}).get("error_code")
            if error_code != condition.error_code:
                return False
                
        # Check score thresholds for task results
        if message_type == "task_result":
            score = payload.get("content", {}).get("score")
            if score is not None:
                if condition.score_below is not None and score >= condition.score_below:
                    return False
                if condition.score_above is not None and score <= condition.score_above:
                    return False
                    
            # Check duration
            if condition.duration_above is not None:
                duration = payload.get("content", {}).get("duration_sec")
                if duration is None or duration <= condition.duration_above:
                    return False
                    
            # Check status
            if condition.status:
                status = payload.get("content", {}).get("status")
                if status != condition.status:
                    return False
        
        return True
    
    def _trigger_alert(self, rule: AlertRule, message: Dict[str, Any]) -> None:
        """Trigger an alert action.
        
        Args:
            rule: Matching alert rule
            message: Original message
        """
        try:
            # Create alert context
            context = {
                "name": rule.name,
                "type": rule.condition.type,
                "timestamp": datetime.now().isoformat(),
                "task_id": message.get("task_id"),
                "agent_id": message.get("sender_id"),
                "message": rule.action.message or f"Alert triggered: {rule.name}",
                "condition": rule.condition.dict(),
                "task_result": message.get("payload", {}).get("content", {})
            }
            
            # Execute action
            if rule.action.notify == "human":
                self._handle_human_notification(rule.action, context)
            elif rule.action.notify == "webhook":
                self._handle_webhook_notification(rule.action, context)
                
            # Log alert
            self._log_alert(rule, context)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to trigger alert {rule.name}: {str(e)}")
    
    def _handle_human_notification(self, action: AlertAction, context: Dict[str, Any]) -> None:
        """Handle human notification action.
        
        Args:
            action: Alert action configuration
            context: Alert context
        """
        # Create human postbox if needed
        human_dir = self.postbox_root / "HUMAN"
        human_dir.mkdir(parents=True, exist_ok=True)
        
        # Create alert message
        alert_message = {
            "sender_id": "ARCH",
            "recipient_id": "HUMAN",
            "trace_id": f"alert_{context['task_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "retry_count": 0,
            "task_id": context["task_id"],
            "payload": {
                "type": "alert",
                "content": {
                    "level": action.level or "info",
                    "message": action.message or f"Alert: {context['name']}",
                    "context": context
                }
            }
        }
        
        # Write to human inbox
        inbox_file = human_dir / "inbox.json"
        try:
            if inbox_file.exists():
                with open(inbox_file, "r") as f:
                    messages = json.load(f)
            else:
                messages = []
                
            messages.append(alert_message)
            
            with open(inbox_file, "w") as f:
                json.dump(messages, f, indent=2)
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to write alert to human inbox: {str(e)}")
            raise
    
    def _handle_webhook_notification(self, action: AlertAction, context: Dict[str, Any]) -> None:
        """Handle webhook notification action.
        
        Args:
            action: Alert action configuration
            context: Alert context
        """
        if not action.url:
            raise ValueError("Webhook URL is required")
            
        # Prepare request
        headers = action.headers or {}
        headers.setdefault("Content-Type", "application/json")
        
        # Format template if provided
        if action.template:
            # Simple template replacement for now
            body = action.template
            for key, value in context.items():
                body = body.replace(f"{{{{.{key}}}}}", str(value))
        else:
            body = json.dumps(context)
            
        # Send request
        try:
            response = requests.post(
                action.url,
                headers=headers,
                data=body,
                timeout=action.timeout_seconds or 10
            )
            response.raise_for_status()
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Webhook notification failed: {str(e)}")
            raise
    
    def _log_alert(self, rule: AlertRule, context: Dict[str, Any]) -> None:
        """Log triggered alert.
        
        Args:
            rule: Alert rule that was triggered
            context: Alert context
        """
        if not self.alert_log_path:
            return
            
        try:
            with open(self.alert_log_path, "r") as f:
                alerts = json.load(f)
                
            alerts.append({
                "timestamp": context["timestamp"],
                "rule_name": rule.name,
                "task_id": context["task_id"],
                "agent_id": context["agent_id"],
                "action": rule.action.dict(),
                "context": context
            })
            
            with open(self.alert_log_path, "w") as f:
                json.dump(alerts, f, indent=2)
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to log alert: {str(e)}") 