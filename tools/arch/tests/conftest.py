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

@pytest.fixture
def test_messages() -> Dict[str, Dict[str, Any]]:
    """Sample test messages for different types."""
    base_metadata = {
        "message_id": "msg_123",
        "timestamp": datetime.utcnow().isoformat(),
        "sender_id": "CC",
        "protocol_version": "1.0.0",
        "sender": "CC",
        "recipient": "ARCH"
    }
    
    return {
        "task_result": {
            "type": "task_result",
            "metadata": base_metadata.copy(),
            "content": {
                "task_id": "TASK-001",
                "status": "completed",
                "progress": 100,
                "details": "Task completed successfully"
            }
        },
        "error": {
            "type": "error",
            "metadata": {
                **base_metadata,
                "message_id": "msg_456",
                "sender_id": "CA",
                "sender": "CA"
            },
            "content": {
                "error_type": "validation_error",
                "error_message": "Invalid message format",
                "task_id": "TASK-002"
            }
        },
        "needs_input": {
            "type": "needs_input",
            "metadata": {
                "message_id": "msg_789",
                "timestamp": "2025-05-21T17:00:00Z",
                "sender_id": "WA",
                "protocol_version": "1.0.0",
                "recipient": "ARCH",
                "sender": "WA"
            },
            "content": {
                "task_id": "TASK-003",
                "request_type": "user_confirmation",
                "prompt": "Please confirm task execution",
                "input_type": "string"
            }
        },
        "malformed": {
            "type": "invalid_type",
            "metadata": {
                "message_id": "msg_999",
                "timestamp": datetime.utcnow().isoformat(),
                "sender_id": "CC",
                "protocol_version": "1.0.0"
            }
        },
        "missing_metadata": {
            "type": "task_result",
            "metadata": {
                "message_id": "msg_123"
            }
        },
        "invalid_timestamp": {
            "type": "task_result",
            "metadata": {
                "message_id": "msg_123",
                "timestamp": "invalid_timestamp",
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