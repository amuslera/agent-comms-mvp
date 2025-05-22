"""Tests for the alert evaluator module."""

import json
import pytest
from pathlib import Path
from datetime import datetime
from ..alert_evaluator import AlertEvaluator
from ..alert_policy_loader import AlertPolicy, AlertRule, AlertCondition, AlertAction

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test files."""
    return tmp_path

@pytest.fixture
def alert_policy_path(temp_dir):
    """Create a test alert policy file."""
    policy = {
        "version": "1.0.0",
        "description": "Test alert policy",
        "rules": [
            {
                "name": "Test Error Rule",
                "enabled": True,
                "condition": {
                    "type": "error",
                    "agent": "CA",
                    "retry_count": 2
                },
                "action": {
                    "notify": "human",
                    "method": "console_log",
                    "level": "warning",
                    "message": "Test error alert"
                }
            },
            {
                "name": "Test Score Rule",
                "enabled": True,
                "condition": {
                    "type": "task_result",
                    "score_below": 0.7
                },
                "action": {
                    "notify": "webhook",
                    "url": "https://test.example.com/alerts",
                    "template": "Test score alert: {{.score}}"
                }
            }
        ]
    }
    
    policy_path = temp_dir / "test_alert_policy.yaml"
    with open(policy_path, "w") as f:
        json.dump(policy, f)
    return policy_path

@pytest.fixture
def evaluator(temp_dir, alert_policy_path):
    """Create an alert evaluator instance."""
    return AlertEvaluator(
        alert_policy_path=alert_policy_path,
        postbox_root=temp_dir / "postbox",
        log_dir=temp_dir / "logs"
    )

def test_load_alert_policy(evaluator):
    """Test loading alert policy."""
    assert evaluator.policy is not None
    assert len(evaluator.policy.rules) == 2
    assert evaluator.policy.rules[0].name == "Test Error Rule"
    assert evaluator.policy.rules[1].name == "Test Score Rule"

def test_error_rule_matching(evaluator):
    """Test matching error messages against rules."""
    message = {
        "sender_id": "CA",
        "recipient_id": "ARCH",
        "trace_id": "test_123",
        "retry_count": 2,
        "task_id": "task_123",
        "payload": {
            "type": "error",
            "content": {
                "error": "Test error",
                "error_code": "E_TEST"
            }
        }
    }
    
    matching_rules = evaluator.evaluate_message(message)
    assert len(matching_rules) == 1
    assert matching_rules[0].name == "Test Error Rule"

def test_score_rule_matching(evaluator):
    """Test matching task result messages against rules."""
    message = {
        "sender_id": "WA",
        "recipient_id": "ARCH",
        "trace_id": "test_456",
        "retry_count": 0,
        "task_id": "task_456",
        "payload": {
            "type": "task_result",
            "content": {
                "score": 0.5,
                "status": "success",
                "duration_sec": 30
            }
        }
    }
    
    matching_rules = evaluator.evaluate_message(message)
    assert len(matching_rules) == 1
    assert matching_rules[0].name == "Test Score Rule"

def test_human_notification(evaluator):
    """Test human notification action."""
    message = {
        "sender_id": "CA",
        "recipient_id": "ARCH",
        "trace_id": "test_789",
        "retry_count": 2,
        "task_id": "task_789",
        "payload": {
            "type": "error",
            "content": {
                "error": "Test error",
                "error_code": "E_TEST"
            }
        }
    }
    
    # Trigger alert
    evaluator.evaluate_message(message)
    
    # Check human inbox
    human_inbox = evaluator.postbox_root / "HUMAN" / "inbox.json"
    assert human_inbox.exists()
    
    with open(human_inbox) as f:
        alerts = json.load(f)
        assert len(alerts) == 1
        assert alerts[0]["payload"]["type"] == "alert"
        assert alerts[0]["payload"]["content"]["level"] == "warning"

def test_alert_logging(evaluator):
    """Test alert logging."""
    message = {
        "sender_id": "WA",
        "recipient_id": "ARCH",
        "trace_id": "test_abc",
        "retry_count": 0,
        "task_id": "task_abc",
        "payload": {
            "type": "task_result",
            "content": {
                "score": 0.5,
                "status": "success"
            }
        }
    }
    
    # Trigger alert
    evaluator.evaluate_message(message)
    
    # Check alert log
    alert_log = evaluator.alert_log_path
    assert alert_log.exists()
    
    with open(alert_log) as f:
        alerts = json.load(f)
        assert len(alerts) == 1
        assert alerts[0]["rule_name"] == "Test Score Rule"
        assert alerts[0]["task_id"] == "task_abc" 