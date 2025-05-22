"""
ARCH Message Parser

This module handles parsing and validation of messages received by the ARCH agent.
It defines message schemas and provides validation functions for different message types.
"""

import json
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path
import logging

class MessageType(str, Enum):
    """Message types supported by ARCH."""
    TASK_RESULT = "task_result"
    ERROR = "error"
    NEEDS_INPUT = "needs_input"

@dataclass
class MessageMetadata:
    """Metadata for all messages."""
    timestamp: str
    sender_id: str
    message_id: str
    protocol_version: str

@dataclass
class TaskResult:
    """Task result message structure."""
    task_id: str
    status: str
    progress: int
    details: Optional[str] = None
    files_updated: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ErrorMessage:
    """Error message structure."""
    error_type: str
    error_message: str
    context: Optional[Dict[str, Any]] = None
    stack_trace: Optional[str] = None

@dataclass
class NeedsInput:
    """Input request message structure."""
    request_type: str
    prompt: str
    options: Optional[List[str]] = None
    timeout: Optional[int] = None

class MCPEnvelopeFields(str, Enum):
    SENDER_ID = "sender_id"
    RECIPIENT_ID = "recipient_id"
    TRACE_ID = "trace_id"
    RETRY_COUNT = "retry_count"
    TASK_ID = "task_id"
    PAYLOAD = "payload"

class MessageParser:
    """Parser for ARCH messages supporting MCP envelope."""
    
    def __init__(self, log_dir: Optional[Path] = None):
        """Initialize the message parser.
        
        Args:
            log_dir: Optional directory for logging parsed messages
        """
        self.log_dir = log_dir
        if log_dir:
            log_dir.mkdir(parents=True, exist_ok=True)
            logging.basicConfig(
                filename=log_dir / "message_parser.log",
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            self.logger = logging.getLogger("arch_message_parser")
    
    def parse(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate a message.
        
        Args:
            message: Raw message dictionary
            
        Returns:
            Parsed and validated message
            
        Raises:
            ValueError: If message is invalid
        """
        return self.parse_message(message)
    
    def parse_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate a message.
        
        Args:
            message: Raw message dictionary
            
        Returns:
            Parsed and validated message
            
        Raises:
            ValueError: If message is invalid
        """
        # Validate MCP envelope fields
        required_fields = [
            MCPEnvelopeFields.SENDER_ID,
            MCPEnvelopeFields.RECIPIENT_ID,
            MCPEnvelopeFields.TRACE_ID,
            MCPEnvelopeFields.RETRY_COUNT,
            MCPEnvelopeFields.TASK_ID,
            MCPEnvelopeFields.PAYLOAD,
        ]
        missing = [f for f in required_fields if f not in message]
        if missing:
            err = f"MCP envelope missing required fields: {', '.join(missing)}"
            if self.log_dir:
                self.logger.error(err)
            raise ValueError(err)
        # Validate types
        if not isinstance(message["sender_id"], str):
            raise ValueError("sender_id must be a string")
        if not isinstance(message["recipient_id"], str):
            raise ValueError("recipient_id must be a string")
        if not isinstance(message["trace_id"], str):
            raise ValueError("trace_id must be a string")
        if not isinstance(message["retry_count"], int):
            raise ValueError("retry_count must be an integer")
        if not isinstance(message["task_id"], str):
            raise ValueError("task_id must be a string")
        if not isinstance(message["payload"], dict):
            raise ValueError("payload must be a dict")
        # Optionally validate payload content here
        if self.log_dir:
            self.logger.info(f"Parsed MCP message: {json.dumps(message)}")
        return message 