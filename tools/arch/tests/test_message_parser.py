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
    
    assert parsed["type"] == MessageType.TASK_RESULT
    assert parsed["metadata"]["message_id"] == "msg_123"
    assert parsed["content"]["task_id"] == "TASK-001"
    assert parsed["content"]["status"] == "completed"
    assert parsed["content"]["progress"] == 100
    assert parsed["metadata"]["sender_id"] == "CC"
    assert parsed["metadata"]["protocol_version"] == "1.0.0"

def test_parse_error(test_messages):
    """Test parsing an error message."""
    parser = MessageParser()
    message = test_messages["error"]
    parsed = parser.parse(message)
    
    assert parsed["type"] == MessageType.ERROR
    assert parsed["metadata"]["message_id"] == "msg_456"
    assert parsed["content"]["error_type"] == "validation_error"
    assert parsed["content"]["error_message"] == "Invalid message format"
    assert parsed["content"]["task_id"] == "TASK-002"
    assert parsed["metadata"]["sender_id"] == "CA"
    assert parsed["metadata"]["protocol_version"] == "1.0.0"

def test_parse_needs_input(test_messages):
    """Test parsing an input request message."""
    parser = MessageParser()
    message = test_messages["needs_input"]
    parsed = parser.parse(message)
    
    assert parsed["type"] == MessageType.NEEDS_INPUT
    assert parsed["metadata"]["message_id"] == "msg_789"
    assert parsed["content"]["task_id"] == "TASK-003"
    assert parsed["content"]["request_type"] == "user_confirmation"
    assert parsed["content"]["prompt"] == "Please confirm task execution"
    assert parsed["metadata"]["sender_id"] == "WA"
    assert parsed["metadata"]["protocol_version"] == "1.0.0"

def test_parse_malformed_message(test_messages):
    """Test handling of malformed messages."""
    parser = MessageParser()
    message = test_messages["malformed"]
    
    with pytest.raises(ValueError) as exc_info:
        parser.parse(message)
    assert "Invalid message type" in str(exc_info.value)

def test_parse_missing_required_fields(test_messages):
    """Test handling of messages with missing required fields."""
    parser = MessageParser()
    message = test_messages["missing_metadata"]
    
    with pytest.raises(ValueError) as exc_info:
        parser.parse(message)
    assert "Message metadata missing required fields" in str(exc_info.value)

def test_parse_invalid_timestamp(test_messages):
    """Test handling of messages with invalid timestamps."""
    parser = MessageParser()
    message = test_messages["invalid_timestamp"]
    
    with pytest.raises(ValueError) as exc_info:
        parser.parse(message)
    assert "Invalid timestamp format" in str(exc_info.value)

def test_parse_with_logging(test_messages, tmp_path):
    """Test message parsing with logging enabled."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    
    parser = MessageParser(log_dir=log_dir)
    message = test_messages["task_result"]
    parsed = parser.parse(message)
    
    assert parsed["type"] == MessageType.TASK_RESULT
    log_files = list(log_dir.glob("*.log"))
    if log_files:
        assert log_files 