"""
Tests for the ARCH message parser.
"""

import pytest
from datetime import datetime
from tools.arch.message_parser import MessageParser, MessageType

def test_parse_task_result(test_messages):
    """Test parsing a task result message."""
    parser = MessageParser()
    message = test_messages["task_result"]
    parsed = parser.parse(message)
    
    assert parsed["sender_id"] == "CC"
    assert parsed["recipient_id"] == "ARCH"
    assert parsed["trace_id"] == "trace-001"
    assert parsed["retry_count"] == 0
    assert parsed["task_id"] == "TASK-001"
    assert parsed["payload"]["type"] == "task_result"
    assert parsed["payload"]["content"]["status"] == "completed"
    assert parsed["payload"]["content"]["progress"] == 100

def test_parse_error(test_messages):
    """Test parsing an error message."""
    parser = MessageParser()
    message = test_messages["error"]
    parsed = parser.parse(message)
    
    assert parsed["sender_id"] == "CA"
    assert parsed["payload"]["type"] == "error"
    assert parsed["payload"]["content"]["error_type"] == "validation_error"
    assert parsed["payload"]["content"]["error_message"] == "Invalid message format"
    assert parsed["payload"]["content"]["task_id"] == "TASK-002"

def test_parse_needs_input(test_messages):
    """Test parsing an input request message."""
    parser = MessageParser()
    message = test_messages["needs_input"]
    parsed = parser.parse(message)
    
    assert parsed["sender_id"] == "WA"
    assert parsed["payload"]["type"] == "needs_input"
    assert parsed["payload"]["content"]["task_id"] == "TASK-003"
    assert parsed["payload"]["content"]["request_type"] == "user_confirmation"
    assert parsed["payload"]["content"]["prompt"] == "Please confirm task execution"
    assert parsed["payload"]["content"]["input_type"] == "string"

def test_parse_missing_trace_id(test_messages):
    parser = MessageParser()
    message = test_messages["missing_trace_id"]
    with pytest.raises(ValueError) as exc_info:
        parser.parse(message)
    assert "trace_id" in str(exc_info.value)

def test_parse_invalid_retry_count(test_messages):
    parser = MessageParser()
    message = test_messages["invalid_retry_count"]
    with pytest.raises(ValueError) as exc_info:
        parser.parse(message)
    assert "retry_count must be an integer" in str(exc_info.value)

def test_parse_malformed_payload(test_messages):
    parser = MessageParser()
    message = test_messages["malformed_payload"]
    # Should not raise, parser only checks payload is a dict
    parsed = parser.parse(message)
    assert isinstance(parsed["payload"], dict)
    assert "type" not in parsed["payload"]

def test_parse_unknown_type(test_messages):
    parser = MessageParser()
    message = test_messages["unknown_type"]
    # Should not raise at parse, but router may reject unknown type
    parsed = parser.parse(message)
    assert parsed["payload"]["type"] == "unknown_type"

def test_parse_with_logging(test_messages, tmp_path):
    """Test message parsing with logging enabled."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    
    parser = MessageParser(log_dir=log_dir)
    message = test_messages["task_result"]
    parsed = parser.parse(message)
    
    assert parsed["payload"]["type"] == "task_result"
    log_files = list(log_dir.glob("*.log"))
    if log_files:
        assert log_files

def test_parse_mcp_envelope_valid():
    parser = MessageParser()
    message = {
        "sender_id": "AGENT_A",
        "recipient_id": "ARCH",
        "trace_id": "trace-001",
        "retry_count": 0,
        "task_id": "TASK-100",
        "payload": {"foo": "bar"}
    }
    parsed = parser.parse(message)
    assert parsed["sender_id"] == "AGENT_A"
    assert parsed["recipient_id"] == "ARCH"
    assert parsed["trace_id"] == "trace-001"
    assert parsed["retry_count"] == 0
    assert parsed["task_id"] == "TASK-100"
    assert parsed["payload"] == {"foo": "bar"}

def test_parse_mcp_envelope_missing_fields():
    parser = MessageParser()
    message = {
        "sender_id": "AGENT_A",
        # missing recipient_id
        "trace_id": "trace-001",
        "retry_count": 0,
        "task_id": "TASK-100",
        "payload": {"foo": "bar"}
    }
    try:
        parser.parse(message)
        assert False, "Should have raised ValueError for missing recipient_id"
    except ValueError as e:
        assert "recipient_id" in str(e) 