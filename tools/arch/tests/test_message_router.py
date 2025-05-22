"""
Tests for the ARCH message router.
"""

import json
import pytest
from pathlib import Path
from tools.arch.message_router import MessageRouter, RoutingRule, EscalationLevel

def test_route_task_result(tmp_path, test_messages):
    router = MessageRouter(tmp_path)
    message = test_messages["task_result"]
    route = router.route_message(message)
    assert route.destination == "ARCH"
    assert route.escalation_level == EscalationLevel.NONE

def test_route_error(tmp_path, test_messages):
    router = MessageRouter(tmp_path)
    message = test_messages["error"]
    route = router.route_message(message)
    assert route.destination == "CC"
    assert route.escalation_level == EscalationLevel.AGENT

def test_route_needs_input(tmp_path, test_messages):
    router = MessageRouter(tmp_path)
    message = test_messages["needs_input"]
    route = router.route_message(message)
    assert route.destination == "ARCH"
    assert route.escalation_level == EscalationLevel.HUMAN

def test_route_with_missing_trace_id(tmp_path, test_messages):
    router = MessageRouter(tmp_path)
    message = test_messages["missing_trace_id"]
    route = router.route_message(message)
    assert route is None

def test_route_with_invalid_retry_count(tmp_path, test_messages):
    router = MessageRouter(tmp_path)
    message = test_messages["invalid_retry_count"]
    route = router.route_message(message)
    assert route is None

def test_route_with_malformed_payload(tmp_path, test_messages):
    router = MessageRouter(tmp_path)
    message = test_messages["malformed_payload"]
    route = router.route_message(message)
    assert route is None

def test_route_with_unknown_type(tmp_path, test_messages):
    router = MessageRouter(tmp_path)
    message = test_messages["unknown_type"]
    route = router.route_message(message)
    assert route is None

def test_route_with_retries(message_router, test_messages):
    """Test message routing with retry handling."""
    # Use an error message for retry testing
    error_message = test_messages["error"]
    
    # First routing attempt should succeed with retry
    route = message_router.route_message(error_message)
    
    # Should have retry information
    assert route is not None
    assert route.destination in ["CC", "CA", "WA"]  # Should be reassigned to original agent
    assert route.escalation_level == EscalationLevel.AGENT
    
    # Check that retry count was incremented (MCP envelope format)
    retry_count = error_message.get("retry_count", 0)
    assert retry_count >= 1
    
    # Simulate multiple retries to test escalation
    for _ in range(5):  # Exceed typical retry limit
        route = message_router.route_message(error_message)
    
    # Should eventually escalate to human after max retries
    assert route is None  # None indicates escalation to human occurred

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