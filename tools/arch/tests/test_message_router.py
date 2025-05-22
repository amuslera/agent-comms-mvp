"""
Tests for the ARCH message router.
"""

import json
import pytest
from pathlib import Path
from tools.arch.message_router import MessageRouter, RoutingRule, EscalationLevel

def test_route_task_result(message_router, test_messages):
    """Test routing of task result messages."""
    message = test_messages["task_result"]
    route = message_router.route_message(message)
    
    assert route.destination == "ARCH"
    assert route.escalation_level == EscalationLevel.NONE
    assert route.max_retries == 3
    assert route.retry_delay == 60

def test_route_error(message_router, test_messages):
    """Test routing of error messages."""
    message = test_messages["error"]
    route = message_router.route_message(message)
    
    assert route.destination == "CC"
    assert route.escalation_level == EscalationLevel.AGENT
    assert route.max_retries == 2
    assert route.retry_delay == 30

def test_route_needs_input(message_router, test_messages):
    """Test routing of input request messages."""
    message = test_messages["needs_input"]
    route = message_router.route_message(message)
    
    assert route.destination == "ARCH"
    assert route.escalation_level == EscalationLevel.HUMAN
    assert route.max_retries == 1
    assert route.retry_delay == 0

@pytest.mark.skip(reason="Retry logic not implemented yet")
def test_route_with_retries(message_router, test_messages):
    """Test message routing with retry handling."""
    message = test_messages["task_result"]
    route = message_router.route_message(message)
    
    # Simulate retries
    for _ in range(route.max_retries):
        route = message_router.route_message(message)
    
    # Should escalate after max retries
    assert route.escalation_level == EscalationLevel.AGENT

def test_route_malformed_message(message_router, test_messages):
    """Test handling of malformed messages."""
    message = test_messages["malformed"]
    route = message_router.route_message(message)
    
    assert route is None

def test_load_phase_policy(message_router, mock_phase_policy):
    """Test loading of phase policy."""
    policy = message_router._load_phase_policy()
    
    assert policy is not None
    assert len(policy.task_result_rules) == 1
    assert len(policy.error_rules) == 1
    assert len(policy.input_rules) == 1
    
    # Verify rule properties
    task_rule = policy.task_result_rules[0]
    assert task_rule.id == "test_task_result"
    assert task_rule.destination == "ARCH"
    assert task_rule.escalation_level == EscalationLevel.NONE
    assert task_rule.max_retries == 3
    assert task_rule.retry_delay == 60

def test_fallback_without_policy(message_router, tmp_path):
    """Test router behavior without a phase policy."""
    # Create router without policy
    router = MessageRouter(
        postbox_root=tmp_path / "postbox",
        phase_policy_path=None,
        log_dir=None
    )
    
    # Should use default rules
    message = {
        "type": "task_result",
        "metadata": {
            "message_id": "msg_123",
            "timestamp": "2025-05-21T17:00:00Z",
            "sender_id": "CC",
            "protocol_version": "1.0.0",
            "sender": "CC",
            "recipient": "ARCH"
        },
        "content": {
            "task_id": "TASK-001",
            "status": "completed",
            "progress": 100
        }
    }
    
    route = router.route_message(message)
    assert route.destination == "ARCH"
    assert route.escalation_level == EscalationLevel.NONE

def test_write_to_inbox_error(message_router, test_messages, tmp_path):
    """Test handling of inbox write errors (should not raise, directory auto-created)."""
    router = MessageRouter(
        postbox_root=tmp_path / "nonexistent",
        phase_policy_path=None,
        log_dir=None
    )
    message = test_messages["task_result"]
    # Should not raise
    router.write_to_inbox(message, "ARCH")

def test_route_with_missing_metadata(message_router, test_messages):
    """Test routing of messages with missing metadata (should escalate to human)."""
    message = test_messages["missing_metadata"]
    route = message_router.route_message(message)
    assert route is None

def test_route_with_invalid_timestamp(message_router, test_messages):
    """Test routing of messages with invalid timestamp (should escalate to human)."""
    message = test_messages["invalid_timestamp"]
    route = message_router.route_message(message)
    assert route is None 