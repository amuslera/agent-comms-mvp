"""
Notification Dispatcher for delivering alert messages via multiple channels.

Supports console logging, file logging, and webhook delivery with retry logic.
"""
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import requests
from urllib.parse import urlparse


class NotificationDispatcher:
    """Handles delivery of alert messages via console, file, or webhook."""
    
    def __init__(self, base_path: str = "/Users/arielmuslera/Development/Projects/agent-comms-mvp", dry_run: bool = False):
        self.base_path = Path(base_path)
        self.logs_path = self.base_path / "logs"
        self.logs_path.mkdir(parents=True, exist_ok=True)
        self.dry_run = dry_run
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def dispatch_alert(self, alert_message: Dict[str, Any], method: str = "console_log", **kwargs) -> bool:
        """
        Dispatch an alert message using the specified method.
        
        Args:
            alert_message: The alert message to dispatch
            method: Delivery method ('console_log', 'file_log', 'webhook')
            **kwargs: Additional parameters for specific methods
            
        Returns:
            bool: True if delivery succeeded, False otherwise
        """
        try:
            if self.dry_run:
                self.logger.info(f"[DRY RUN] Would dispatch via {method}: {alert_message}")
                return True
            
            if method == "console_log":
                return self._deliver_console(alert_message)
            elif method == "file_log":
                return self._deliver_file(alert_message, kwargs.get("log_file"))
            elif method == "webhook":
                return self._deliver_webhook(alert_message, kwargs.get("webhook_url"), kwargs.get("headers"))
            else:
                self.logger.error(f"Unknown delivery method: {method}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to dispatch alert via {method}: {str(e)}")
            return False
    
    def _deliver_console(self, alert_message: Dict[str, Any]) -> bool:
        """
        Deliver alert message to console output.
        
        Args:
            alert_message: The alert message to log
            
        Returns:
            bool: Always True for console logging
        """
        try:
            # Format the alert message for console output
            timestamp = datetime.now().isoformat()
            alert_type = alert_message.get("type", "ALERT")
            sender = alert_message.get("sender_id", "UNKNOWN")
            content = alert_message.get("payload", {}).get("content", {})
            
            print(f"\n🚨 [{timestamp}] {alert_type.upper()} from {sender}")
            print(f"Task ID: {alert_message.get('task_id', 'N/A')}")
            print(f"Trace ID: {alert_message.get('trace_id', 'N/A')}")
            
            if isinstance(content, dict):
                if "summary" in content:
                    print(f"Summary: {content['summary']}")
                if "severity" in content:
                    print(f"Severity: {content['severity']}")
                if "details" in content:
                    print(f"Details: {content['details']}")
            else:
                print(f"Message: {content}")
            
            print("=" * 60)
            
            self.logger.info(f"Alert delivered to console: {alert_message.get('task_id', 'N/A')}")
            return True
            
        except Exception as e:
            self.logger.error(f"Console delivery failed: {str(e)}")
            return False
    
    def _deliver_file(self, alert_message: Dict[str, Any], log_file: Optional[str] = None) -> bool:
        """
        Deliver alert message to log file.
        
        Args:
            alert_message: The alert message to log
            log_file: Optional custom log file path
            
        Returns:
            bool: True if file write succeeded, False otherwise
        """
        try:
            # Use default log file if not specified
            if log_file is None:
                log_file = self.logs_path / "notifications.log"
            else:
                log_file = Path(log_file)
                log_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare log entry
            timestamp = datetime.now().isoformat()
            log_entry = {
                "timestamp": timestamp,
                "alert_message": alert_message,
                "delivery_method": "file_log"
            }
            
            # Append to log file
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, indent=2) + "\n")
            
            self.logger.info(f"Alert logged to file: {log_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"File delivery failed: {str(e)}")
            return False
    
    def _deliver_webhook(self, alert_message: Dict[str, Any], webhook_url: Optional[str] = None, 
                        headers: Optional[Dict[str, str]] = None, max_retries: int = 2) -> bool:
        """
        Deliver alert message via webhook POST request.
        
        Args:
            alert_message: The alert message to send
            webhook_url: URL to POST the alert to
            headers: Optional headers for the request
            max_retries: Maximum number of retry attempts
            
        Returns:
            bool: True if webhook delivery succeeded, False otherwise
        """
        if not webhook_url:
            self.logger.error("Webhook URL not provided")
            return False
        
        # Validate URL
        try:
            parsed_url = urlparse(webhook_url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                raise ValueError("Invalid webhook URL format")
        except Exception as e:
            self.logger.error(f"Invalid webhook URL: {str(e)}")
            return False
        
        # Prepare request data
        request_data = {
            "timestamp": datetime.now().isoformat(),
            "alert": alert_message,
            "source": "bluelabel-agent-os"
        }
        
        # Default headers
        request_headers = {
            "Content-Type": "application/json",
            "User-Agent": "Bluelabel-Agent-OS/1.0"
        }
        if headers:
            request_headers.update(headers)
        
        # Attempt delivery with retries
        for attempt in range(max_retries + 1):
            try:
                self.logger.info(f"Webhook delivery attempt {attempt + 1}/{max_retries + 1} to {webhook_url}")
                
                response = requests.post(
                    webhook_url,
                    json=request_data,
                    headers=request_headers,
                    timeout=10
                )
                
                if response.status_code < 400:
                    self.logger.info(f"Webhook delivery successful: {response.status_code}")
                    return True
                elif 500 <= response.status_code < 600:
                    # Server error - retry
                    self.logger.warning(f"Server error {response.status_code}, will retry if attempts remain")
                    if attempt < max_retries:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                else:
                    # Client error - don't retry
                    self.logger.error(f"Client error {response.status_code}: {response.text}")
                    return False
                    
            except requests.exceptions.Timeout:
                self.logger.warning(f"Webhook timeout on attempt {attempt + 1}")
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    continue
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Webhook request failed on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    continue
        
        self.logger.error(f"Webhook delivery failed after {max_retries + 1} attempts")
        return False
    
    def dispatch_from_policy(self, alert_message: Dict[str, Any], policy_config: Dict[str, Any]) -> List[bool]:
        """
        Dispatch alert using configuration from policy file.
        
        Args:
            alert_message: The alert message to dispatch
            policy_config: Policy configuration containing notification settings
            
        Returns:
            List[bool]: Results for each configured delivery method
        """
        results = []
        notifications = policy_config.get("notifications", {})
        
        # Console logging
        if notifications.get("console_enabled", True):
            results.append(self.dispatch_alert(alert_message, "console_log"))
        
        # File logging
        if notifications.get("file_enabled", True):
            log_file = notifications.get("log_file")
            results.append(self.dispatch_alert(alert_message, "file_log", log_file=log_file))
        
        # Webhook delivery
        if notifications.get("webhook_enabled", False):
            webhook_url = notifications.get("webhook_url")
            headers = notifications.get("webhook_headers", {})
            if webhook_url:
                results.append(self.dispatch_alert(alert_message, "webhook", 
                                                webhook_url=webhook_url, headers=headers))
        
        return results
    
    def process_alert_from_arch(self, arch_message: Dict[str, Any]) -> bool:
        """
        Process an alert message received from ARCH agent.
        
        Args:
            arch_message: MCP-formatted message from ARCH
            
        Returns:
            bool: True if alert was processed successfully
        """
        try:
            # Extract alert information from ARCH message
            payload = arch_message.get("payload", {})
            if payload.get("type") != "alert":
                self.logger.warning(f"Received non-alert message type: {payload.get('type')}")
                return False
            
            # Default to console logging for now
            # In a real implementation, this would read from phase_policy.yaml
            success = self.dispatch_alert(arch_message, "console_log")
            
            # Also log to file
            file_success = self.dispatch_alert(arch_message, "file_log")
            
            return success or file_success
            
        except Exception as e:
            self.logger.error(f"Failed to process alert from ARCH: {str(e)}")
            return False


def create_sample_alert() -> Dict[str, Any]:
    """Create a sample alert message for testing."""
    return {
        "trace_id": f"alert-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "sender_id": "CA",
        "recipient_id": "ARCH",
        "task_id": "TASK-075C-TEST",
        "timestamp": datetime.now().isoformat() + "Z",
        "retry_count": 0,
        "message_type": "alert",
        "protocol_version": "1.0.0",
        "payload": {
            "type": "alert",
            "severity": "high",
            "content": {
                "summary": "Task execution failed with critical error",
                "details": "Agent CA failed to complete TASK-075C-TEST due to timeout",
                "error_code": "TIMEOUT_ERROR",
                "suggested_action": "Retry with increased timeout or escalate to human"
            }
        }
    }


if __name__ == "__main__":
    # Test the notification dispatcher
    dispatcher = NotificationDispatcher()
    sample_alert = create_sample_alert()
    
    print("Testing Notification Dispatcher...")
    print("\n1. Console delivery:")
    dispatcher.dispatch_alert(sample_alert, "console_log")
    
    print("\n2. File delivery:")
    dispatcher.dispatch_alert(sample_alert, "file_log")
    
    print("\n3. Webhook delivery (dry run):")
    dispatcher_dry = NotificationDispatcher(dry_run=True)
    dispatcher_dry.dispatch_alert(sample_alert, "webhook", webhook_url="https://httpbin.org/post")
    
    print("\nTesting complete!")