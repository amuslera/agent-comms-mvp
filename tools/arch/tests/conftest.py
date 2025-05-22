"""
Shared test fixtures for ARCH core component tests.
"""

import json
import pytest
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from tools.arch.message_parser import MessageType
from tools.arch.message_router import MessageRouter, RoutingRule, EscalationLevel

def mcp_message(
    sender_id: str,
    recipient_id: str,
    trace_id: str,
    retry_count: int,
    task_id: str,
    payload: dict
) -> Dict[str, Any]:
    return {
        "sender_id": sender_id,
        "recipient_id": recipient_id,
        "trace_id": trace_id,
        "retry_count": retry_count,
        "task_id": task_id,
        "payload": payload
    }

@pytest.fixture
def test_messages() -> Dict[str, Dict[str, Any]]:
    return {
        "task_result": mcp_message(
            sender_id="CC",
            recipient_id="ARCH",
            trace_id="trace-001",
            retry_count=0,
            task_id="TASK-001",
            payload={
                "type": "task_result",
                "content": {
                    "task_id": "TASK-001",
                    "status": "completed",
                    "progress": 100,
                    "details": "Task completed successfully"
                }
            }
        ),
        "error": mcp_message(
            sender_id="CA",
            recipient_id="ARCH",
            trace_id="trace-002",
            retry_count=0,
            task_id="TASK-002",
            payload={
                "type": "error",
                "content": {
                    "error_type": "validation_error",
                    "error_message": "Invalid message format",
                    "task_id": "TASK-002"
                }
            }
        ),
        "needs_input": mcp_message(
            sender_id="WA",
            recipient_id="ARCH",
            trace_id="trace-003",
            retry_count=0,
            task_id="TASK-003",
            payload={
                "type": "needs_input",
                "content": {
                    "task_id": "TASK-003",
                    "request_type": "user_confirmation",
                    "prompt": "Please confirm task execution",
                    "input_type": "string"
                }
            }
        ),
        # Edge case: missing trace_id
        "missing_trace_id": {
            "sender_id": "CC",
            "recipient_id": "ARCH",
            # missing trace_id
            "retry_count": 0,
            "task_id": "TASK-004",
            "payload": {
                "type": "task_result",
                "content": {"task_id": "TASK-004", "status": "completed", "progress": 100}
            }
        },
        # Edge case: invalid retry_count
        "invalid_retry_count": {
            "sender_id": "CC",
            "recipient_id": "ARCH",
            "trace_id": "trace-005",
            "retry_count": "not_an_int",
            "task_id": "TASK-005",
            "payload": {
                "type": "task_result",
                "content": {"task_id": "TASK-005", "status": "completed", "progress": 100}
            }
        },
        # Edge case: malformed payload
        "malformed_payload": mcp_message(
            sender_id="CC",
            recipient_id="ARCH",
            trace_id="trace-006",
            retry_count=0,
            task_id="TASK-006",
            payload={"notype": "oops"}
        ),
        # Edge case: unknown type
        "unknown_type": mcp_message(
            sender_id="CC",
            recipient_id="ARCH",
            trace_id="trace-007",
            retry_count=0,
            task_id="TASK-007",
            payload={"type": "unknown_type", "content": {}}
        ),
    }

@pytest.fixture
def mock_postbox(tmp_path: Path) -> Path:
    """Create a temporary postbox directory structure."""
    postbox = tmp_path / "postbox"
    for agent in ["ARCH", "CC", "CA", "WA"]:
        inbox = postbox / agent / "inbox.json"
        inbox.parent.mkdir(parents=True)
        with open(inbox, "w") as f:
            json.dump([], f)
    return postbox

@pytest.fixture
def mock_phase_policy(tmp_path: Path) -> Path:
    """Create a temporary phase policy file."""
    policy = tmp_path / "phase_policy.yaml"
    policy_content = """
    task_result_rules:
      - id: test_task_result
        destination: ARCH
        escalation_level: none
        max_retries: 3
        retry_delay: 60
    
    error_rules:
      - id: test_error
        destination: CC
        escalation_level: agent
        max_retries: 2
        retry_delay: 30
    
    input_rules:
      - id: test_input
        destination: ARCH
        escalation_level: human
        max_retries: 1
        retry_delay: 0
    
    escalation_rules:
      - type: error
        description: General task errors
        retry_count: 2
        retry_delay_minutes: 30
        escalate_if_unresolved: true
        escalation_timeout_hours: 2
        
      - type: critical_error
        description: Security, data loss, or system breaking errors
        retry_count: 1
        retry_delay_minutes: 0
        escalate_if_unresolved: true
        escalation_timeout_hours: 0
        immediate_human_notification: true
    """
    policy.write_text(policy_content)
    return policy

@pytest.fixture
def message_router(mock_postbox: Path, mock_phase_policy: Path) -> MessageRouter:
    """Create a MessageRouter instance with test configuration."""
    return MessageRouter(
        postbox_root=mock_postbox,
        phase_policy_path=mock_phase_policy,
        log_dir=None
    ) 