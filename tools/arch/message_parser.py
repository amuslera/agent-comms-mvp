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

class MessageType(Enum):
    """Enumeration of supported message types."""
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

class MessageParser:
    """Parser for ARCH agent messages."""
    
    def __init__(self, log_dir: Optional[Path] = None):
        """Initialize the message parser.
        
        Args:
            log_dir: Optional directory for logging parsed messages
        """
        self.log_dir = log_dir
        if log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def parse_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate a message.
        
        Args:
            message: Raw message dictionary
            
        Returns:
            Parsed and validated message
            
        Raises:
            ValueError: If message is invalid
        """
        # Validate required fields
        if not all(k in message for k in ["type", "metadata"]):
            raise ValueError("Message missing required fields: type, metadata")
            
        # Validate metadata
        metadata = message["metadata"]
        if not all(k in metadata for k in ["timestamp", "sender_id", "message_id", "protocol_version"]):
            raise ValueError("Message metadata missing required fields")
            
        # Parse based on message type
        msg_type = MessageType(message["type"])
        parsed = {
            "type": msg_type,
            "metadata": MessageMetadata(**metadata)
        }
        
        # Parse message-specific content
        if msg_type == MessageType.TASK_RESULT:
            parsed["content"] = TaskResult(**message["content"])
        elif msg_type == MessageType.ERROR:
            parsed["content"] = ErrorMessage(**message["content"])
        elif msg_type == MessageType.NEEDS_INPUT:
            parsed["content"] = NeedsInput(**message["content"])
            
        # Log if configured
        if self.log_dir:
            self._log_message(parsed)
            
        return parsed
    
    def _log_message(self, message: Dict[str, Any]) -> None:
        """Log a parsed message to file.
        
        Args:
            message: Parsed message to log
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"message_{timestamp}_{message['metadata'].message_id}.json"
        
        with open(log_file, "w") as f:
            json.dump(message, f, indent=2, default=str) 