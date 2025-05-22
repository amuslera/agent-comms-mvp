"""
Test suite for NotificationDispatcher.
"""
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from tools.arch.notification_dispatcher import NotificationDispatcher, create_sample_alert


class TestNotificationDispatcher:
    """Test cases for NotificationDispatcher."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.dispatcher = NotificationDispatcher(base_path=self.temp_dir)
        self.sample_alert = create_sample_alert()
    
    def test_console_delivery(self):
        """Test console log delivery."""
        with patch('builtins.print') as mock_print:
            result = self.dispatcher._deliver_console(self.sample_alert)
            assert result is True
            assert mock_print.called
            # Verify alert information was printed
            printed_output = ''.join([str(call) for call in mock_print.call_args_list])
            assert "ALERT from CA" in printed_output
            assert "TASK-075C-TEST" in printed_output
    
    def test_file_delivery(self):
        """Test file log delivery."""
        log_file = Path(self.temp_dir) / "test_notifications.log"
        result = self.dispatcher._deliver_file(self.sample_alert, str(log_file))
        
        assert result is True
        assert log_file.exists()
        
        # Verify log content
        with open(log_file, 'r') as f:
            log_content = f.read()
            log_data = json.loads(log_content)
            assert log_data["alert_message"]["task_id"] == "TASK-075C-TEST"
            assert log_data["delivery_method"] == "file_log"
    
    @patch('requests.post')
    def test_webhook_delivery_success(self, mock_post):
        """Test successful webhook delivery."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        result = self.dispatcher._deliver_webhook(
            self.sample_alert, 
            "https://example.com/webhook"
        )
        
        assert result is True
        assert mock_post.called
        
        # Verify request data
        call_args = mock_post.call_args
        assert call_args[1]["json"]["alert"] == self.sample_alert
        assert call_args[1]["headers"]["Content-Type"] == "application/json"
    
    @patch('requests.post')
    def test_webhook_delivery_server_error_retry(self, mock_post):
        """Test webhook retry logic on server errors."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        result = self.dispatcher._deliver_webhook(
            self.sample_alert, 
            "https://example.com/webhook"
        )
        
        assert result is False
        # Should retry 3 times total (initial + 2 retries)
        assert mock_post.call_count == 3
    
    @patch('requests.post')
    def test_webhook_delivery_client_error_no_retry(self, mock_post):
        """Test webhook doesn't retry on client errors."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response
        
        result = self.dispatcher._deliver_webhook(
            self.sample_alert, 
            "https://example.com/webhook"
        )
        
        assert result is False
        # Should only try once for client errors
        assert mock_post.call_count == 1
    
    def test_webhook_invalid_url(self):
        """Test webhook with invalid URL."""
        result = self.dispatcher._deliver_webhook(
            self.sample_alert, 
            "invalid-url"
        )
        
        assert result is False
    
    def test_dispatch_alert_console(self):
        """Test dispatch_alert with console method."""
        with patch.object(self.dispatcher, '_deliver_console', return_value=True) as mock_console:
            result = self.dispatcher.dispatch_alert(self.sample_alert, "console_log")
            assert result is True
            assert mock_console.called
    
    def test_dispatch_alert_file(self):
        """Test dispatch_alert with file method."""
        with patch.object(self.dispatcher, '_deliver_file', return_value=True) as mock_file:
            result = self.dispatcher.dispatch_alert(self.sample_alert, "file_log", log_file="test.log")
            assert result is True
            assert mock_file.called
    
    def test_dispatch_alert_webhook(self):
        """Test dispatch_alert with webhook method."""
        with patch.object(self.dispatcher, '_deliver_webhook', return_value=True) as mock_webhook:
            result = self.dispatcher.dispatch_alert(
                self.sample_alert, 
                "webhook", 
                webhook_url="https://example.com/webhook"
            )
            assert result is True
            assert mock_webhook.called
    
    def test_dispatch_alert_unknown_method(self):
        """Test dispatch_alert with unknown method."""
        result = self.dispatcher.dispatch_alert(self.sample_alert, "unknown_method")
        assert result is False
    
    def test_dry_run_mode(self):
        """Test dry run mode."""
        dry_dispatcher = NotificationDispatcher(base_path=self.temp_dir, dry_run=True)
        
        # All methods should return True in dry run mode
        result = dry_dispatcher.dispatch_alert(self.sample_alert, "console_log")
        assert result is True
        
        result = dry_dispatcher.dispatch_alert(self.sample_alert, "file_log")
        assert result is True
        
        result = dry_dispatcher.dispatch_alert(self.sample_alert, "webhook", webhook_url="https://example.com")
        assert result is True
    
    def test_dispatch_from_policy(self):
        """Test dispatch from policy configuration."""
        policy_config = {
            "notifications": {
                "console_enabled": True,
                "file_enabled": True,
                "webhook_enabled": False
            }
        }
        
        with patch.object(self.dispatcher, 'dispatch_alert', return_value=True) as mock_dispatch:
            results = self.dispatcher.dispatch_from_policy(self.sample_alert, policy_config)
            
            # Should call dispatch twice (console + file)
            assert len(results) == 2
            assert all(results)
            assert mock_dispatch.call_count == 2
    
    def test_process_alert_from_arch(self):
        """Test processing alert from ARCH agent."""
        arch_message = {
            "payload": {
                "type": "alert",
                "content": {
                    "summary": "Test alert from ARCH"
                }
            }
        }
        
        with patch.object(self.dispatcher, 'dispatch_alert', return_value=True) as mock_dispatch:
            result = self.dispatcher.process_alert_from_arch(arch_message)
            assert result is True
            # Should dispatch to both console and file
            assert mock_dispatch.call_count == 2
    
    def test_process_non_alert_from_arch(self):
        """Test processing non-alert message from ARCH."""
        arch_message = {
            "payload": {
                "type": "task_result",
                "content": {
                    "summary": "Not an alert"
                }
            }
        }
        
        result = self.dispatcher.process_alert_from_arch(arch_message)
        assert result is False
    
    def test_create_sample_alert(self):
        """Test sample alert creation."""
        alert = create_sample_alert()
        
        assert alert["sender_id"] == "CA"
        assert alert["recipient_id"] == "ARCH"
        assert alert["task_id"] == "TASK-075C-TEST"
        assert alert["message_type"] == "alert"
        assert alert["payload"]["type"] == "alert"
        assert alert["payload"]["severity"] == "high"


if __name__ == "__main__":
    # Run tests directly
    test_class = TestNotificationDispatcher()
    test_methods = [method for method in dir(test_class) if method.startswith('test_')]
    
    passed = 0
    failed = 0
    
    for method_name in test_methods:
        try:
            test_class.setup_method()
            method = getattr(test_class, method_name)
            method()
            print(f"✅ {method_name}")
            passed += 1
        except Exception as e:
            print(f"❌ {method_name}: {str(e)}")
            failed += 1
    
    print(f"\nTest Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
    else:
        print("❗ Some tests failed")