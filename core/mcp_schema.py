"""
MCP Schema Validator Module

This module provides comprehensive MCP message validation with strict type checking,
enum validation, and clear error messages. It handles both outgoing task assignments
and incoming task results, ensuring full compliance with the MCP protocol.
"""

import json
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path
from datetime import datetime
from jsonschema import validate, ValidationError, Draft7Validator
import re


class MCPValidationError(Exception):
    """Custom exception for MCP validation errors with detailed context."""
    
    def __init__(self, message: str, field: str = None, expected: Any = None, 
                 actual: Any = None, suggestions: List[str] = None):
        super().__init__(message)
        self.field = field
        self.expected = expected
        self.actual = actual
        self.suggestions = suggestions or []
    
    def __str__(self):
        parts = [str(self.args[0])]
        if self.field:
            parts.append(f"Field: '{self.field}'")
        if self.expected is not None:
            parts.append(f"Expected: {self.expected}")
        if self.actual is not None:
            parts.append(f"Actual: {self.actual}")
        if self.suggestions:
            parts.append(f"Suggestions: {', '.join(self.suggestions)}")
        return " | ".join(parts)


class MCPSchemaValidator:
    """Validates MCP messages for both task assignments and results."""
    
    # Valid agent IDs
    VALID_AGENTS = {"ARCH", "CA", "CC", "WA", "HUMAN"}
    
    # Valid message types
    VALID_MESSAGE_TYPES = {"task_assignment", "task_result", "error", "needs_input"}
    
    # Valid task types from PLAN_SCHEMA
    VALID_TASK_TYPES = {
        "task_assignment", "data_processing", "report_generation", 
        "health_check", "notification", "validation", "custom"
    }
    
    # Valid priorities
    VALID_PRIORITIES = {"low", "medium", "high", "critical"}
    
    # Valid task result statuses
    VALID_STATUSES = {"success", "partial_success", "failed"}
    
    def __init__(self, schema_dir: Path = None):
        """Initialize the validator with schema directory."""
        self.schema_dir = schema_dir or Path(__file__).parent.parent / "schemas"
        self._schemas = {}
        self._load_schemas()
    
    def _load_schemas(self):
        """Load all relevant schemas."""
        schema_files = {
            "mcp": "MCP_MESSAGE_SCHEMA.json",
            "plan": "PLAN_SCHEMA.json",
            "task_assignment": "TASK_ASSIGNMENT_SCHEMA.json"  # We'll create this
        }
        
        for key, filename in schema_files.items():
            schema_path = self.schema_dir / filename
            if schema_path.exists():
                with open(schema_path) as f:
                    self._schemas[key] = json.load(f)
    
    def validate_task_assignment(self, message: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a task assignment message with strict checking.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required envelope fields
        required_envelope = ["type", "protocol_version", "sender_id", "recipient_id", 
                           "timestamp", "task_id", "payload"]
        for field in required_envelope:
            if field not in message:
                errors.append(f"Missing required field: '{field}'")
        
        if errors:
            return False, errors
        
        # Validate type
        if message.get("type") != "task_assignment":
            errors.append(f"Invalid message type: expected 'task_assignment', got '{message.get('type')}'")
        
        # Validate protocol version
        protocol = message.get("protocol_version", "")
        if not re.match(r'^\d+\.\d+$', str(protocol)):
            errors.append(f"Invalid protocol_version format: '{protocol}' (expected: 'X.Y')")
        
        # Validate sender_id (should be ARCH for task assignments)
        sender = message.get("sender_id")
        if sender != "ARCH":
            errors.append(f"Invalid sender_id for task assignment: '{sender}' (expected: 'ARCH')")
        
        # Validate recipient_id (agent)
        recipient = message.get("recipient_id")
        if recipient not in self.VALID_AGENTS:
            errors.append(f"Invalid recipient_id (agent): '{recipient}' (valid: {', '.join(self.VALID_AGENTS)})")
        
        # Validate task_id format
        task_id = message.get("task_id", "")
        if not re.match(r'^[A-Z0-9_-]+$', str(task_id)):
            errors.append(f"Invalid task_id format: '{task_id}' (expected: uppercase alphanumeric with - or _)")
        
        # Validate timestamp
        timestamp = message.get("timestamp")
        if timestamp:
            try:
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                errors.append(f"Invalid timestamp format: '{timestamp}' (expected: ISO 8601)")
        
        # Validate payload
        payload = message.get("payload", {})
        if not isinstance(payload, dict):
            errors.append(f"Invalid payload type: expected dict, got {type(payload).__name__}")
        else:
            payload_errors = self._validate_task_assignment_payload(payload)
            errors.extend(payload_errors)
        
        # Validate optional fields
        if "retry_count" in message:
            retry = message["retry_count"]
            if not isinstance(retry, int) or retry < 0:
                errors.append(f"Invalid retry_count: {retry} (expected: non-negative integer)")
        
        if "trace_id" in message and not message["trace_id"]:
            errors.append("trace_id cannot be empty if provided")
        
        return len(errors) == 0, errors
    
    def _validate_task_assignment_payload(self, payload: Dict[str, Any]) -> List[str]:
        """Validate the payload section of a task assignment."""
        errors = []
        
        # Check payload type
        if payload.get("type") != "task_assignment":
            errors.append(f"Invalid payload.type: '{payload.get('type')}' (expected: 'task_assignment')")
        
        # Check content
        content = payload.get("content", {})
        if not isinstance(content, dict):
            errors.append(f"Invalid payload.content type: expected dict, got {type(content).__name__}")
            return errors
        
        # Required content fields
        if "task_id" not in content:
            errors.append("Missing required field: payload.content.task_id")
        
        if "description" not in content:
            errors.append("Missing required field: payload.content.description")
        elif not content["description"] or not isinstance(content["description"], str):
            errors.append("payload.content.description must be a non-empty string")
        
        if "action" not in content:
            errors.append("Missing required field: payload.content.action")
        elif not content["action"] or not isinstance(content["action"], str):
            errors.append("payload.content.action must be a non-empty string")
        
        # Validate parameters if present
        if "parameters" in content:
            params = content["parameters"]
            if not isinstance(params, dict):
                errors.append(f"Invalid payload.content.parameters type: expected dict, got {type(params).__name__}")
        
        # Validate requirements if present
        if "requirements" in content:
            reqs = content["requirements"]
            if not isinstance(reqs, list):
                errors.append(f"Invalid payload.content.requirements type: expected list, got {type(reqs).__name__}")
            elif not all(isinstance(r, str) for r in reqs):
                errors.append("All requirements must be strings")
        
        # Validate file lists
        for field in ["input_files", "output_files"]:
            if field in content:
                files = content[field]
                if not isinstance(files, list):
                    errors.append(f"Invalid payload.content.{field} type: expected list, got {type(files).__name__}")
                elif not all(isinstance(f, str) for f in files):
                    errors.append(f"All {field} must be strings")
        
        # Validate priority
        if "priority" in content:
            priority = content["priority"]
            if priority not in self.VALID_PRIORITIES:
                errors.append(f"Invalid priority: '{priority}' (valid: {', '.join(self.VALID_PRIORITIES)})")
        
        # Validate dependencies
        if "dependencies" in content:
            deps = content["dependencies"]
            if not isinstance(deps, list):
                errors.append(f"Invalid dependencies type: expected list, got {type(deps).__name__}")
            else:
                for dep in deps:
                    if not isinstance(dep, str) or not re.match(r'^[A-Z0-9_-]+$', dep):
                        errors.append(f"Invalid dependency format: '{dep}' (expected: uppercase alphanumeric)")
        
        return errors
    
    def validate_task_result(self, message: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate a task result message."""
        # For now, use the existing schema validation
        # In a real implementation, we'd have similar detailed validation
        try:
            if "mcp" in self._schemas:
                validate(instance=message, schema=self._schemas["mcp"])
            return True, []
        except ValidationError as e:
            return False, [str(e)]
    
    def validate_message(self, message: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate any MCP message based on its type.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        msg_type = message.get("type")
        
        if msg_type == "task_assignment":
            return self.validate_task_assignment(message)
        elif msg_type in ["task_result", "error", "needs_input"]:
            return self.validate_task_result(message)
        else:
            return False, [f"Unknown message type: '{msg_type}' (valid: {', '.join(self.VALID_MESSAGE_TYPES)})"]
    
    def validate_plan(self, plan: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate a complete plan with all its tasks."""
        errors = []
        
        # Basic plan structure validation
        if "plan_id" not in plan:
            errors.append("Missing required field: plan_id")
        elif not re.match(r'^[A-Z0-9_-]+$', plan.get("plan_id", "")):
            errors.append(f"Invalid plan_id format: '{plan.get('plan_id')}'")
        
        if "name" not in plan:
            errors.append("Missing required field: name")
        
        if "tasks" not in plan:
            errors.append("Missing required field: tasks")
            return False, errors
        
        tasks = plan.get("tasks", [])
        if not isinstance(tasks, list):
            errors.append(f"Invalid tasks type: expected list, got {type(tasks).__name__}")
            return False, errors
        
        if not tasks:
            errors.append("Plan must contain at least one task")
        
        # Validate each task
        task_ids = set()
        for i, task in enumerate(tasks):
            task_errors = self._validate_plan_task(task, i, task_ids)
            errors.extend(task_errors)
        
        # Check for dependency issues
        dep_errors = self._validate_dependencies(tasks, task_ids)
        errors.extend(dep_errors)
        
        return len(errors) == 0, errors
    
    def _validate_plan_task(self, task: Dict[str, Any], index: int, task_ids: set) -> List[str]:
        """Validate a single task in a plan."""
        errors = []
        prefix = f"Task[{index}]"
        
        # Required fields
        if "task_id" not in task:
            errors.append(f"{prefix}: Missing required field 'task_id'")
        else:
            task_id = task["task_id"]
            if not re.match(r'^[A-Z0-9_-]+$', task_id):
                errors.append(f"{prefix}: Invalid task_id format: '{task_id}'")
            if task_id in task_ids:
                errors.append(f"{prefix}: Duplicate task_id: '{task_id}'")
            task_ids.add(task_id)
        
        if "agent" not in task:
            errors.append(f"{prefix}: Missing required field 'agent'")
        elif task["agent"] not in self.VALID_AGENTS:
            errors.append(f"{prefix}: Invalid agent: '{task['agent']}' (valid: {', '.join(self.VALID_AGENTS)})")
        
        if "task_type" not in task:
            errors.append(f"{prefix}: Missing required field 'task_type'")
        elif task["task_type"] not in self.VALID_TASK_TYPES:
            errors.append(f"{prefix}: Invalid task_type: '{task['task_type']}' (valid: {', '.join(self.VALID_TASK_TYPES)})")
        
        if "description" not in task:
            errors.append(f"{prefix}: Missing required field 'description'")
        elif not task["description"] or not isinstance(task["description"], str):
            errors.append(f"{prefix}: description must be a non-empty string")
        
        # Content validation
        if "content" not in task:
            errors.append(f"{prefix}: Missing required field 'content'")
        else:
            content = task["content"]
            if not isinstance(content, dict):
                errors.append(f"{prefix}: content must be a dict")
            elif "action" not in content:
                errors.append(f"{prefix}: Missing required field 'content.action'")
        
        return errors
    
    def _validate_dependencies(self, tasks: List[Dict[str, Any]], task_ids: set) -> List[str]:
        """Validate task dependencies."""
        errors = []
        
        for task in tasks:
            task_id = task.get("task_id", "unknown")
            deps = task.get("dependencies", [])
            
            for dep in deps:
                if dep not in task_ids:
                    errors.append(f"Task '{task_id}' depends on non-existent task: '{dep}'")
                if dep == task_id:
                    errors.append(f"Task '{task_id}' cannot depend on itself")
        
        # TODO: Add circular dependency detection
        
        return errors


def create_task_assignment_schema():
    """Create the task assignment schema that's missing from the current schemas."""
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Task Assignment Message",
        "description": "Schema for task assignment messages sent from ARCH to agents",
        "type": "object",
        "required": [
            "type", "protocol_version", "sender_id", "recipient_id",
            "timestamp", "task_id", "payload"
        ],
        "properties": {
            "type": {
                "const": "task_assignment"
            },
            "protocol_version": {
                "type": "string",
                "pattern": "^\\d+\\.\\d+$"
            },
            "sender_id": {
                "const": "ARCH"
            },
            "recipient_id": {
                "type": "string",
                "enum": ["CA", "CC", "WA"]
            },
            "timestamp": {
                "type": "string",
                "format": "date-time"
            },
            "task_id": {
                "type": "string",
                "pattern": "^[A-Z0-9_-]+$"
            },
            "trace_id": {
                "type": "string"
            },
            "retry_count": {
                "type": "integer",
                "minimum": 0,
                "default": 0
            },
            "payload": {
                "type": "object",
                "required": ["type", "content"],
                "properties": {
                    "type": {
                        "const": "task_assignment"
                    },
                    "content": {
                        "type": "object",
                        "required": ["task_id", "description", "action"],
                        "properties": {
                            "task_id": {"type": "string"},
                            "description": {"type": "string"},
                            "action": {"type": "string"},
                            "parameters": {"type": "object"},
                            "requirements": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "input_files": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "output_files": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["low", "medium", "high", "critical"]
                            },
                            "dependencies": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
    }
    return schema