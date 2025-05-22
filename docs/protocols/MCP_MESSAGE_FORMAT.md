# MCP-Compatible Message Envelope Specification

## Overview

This document defines the standard message envelope format for inter-agent communication within the Bluelabel Agent OS. The format is inspired by the MCP (Message Control Protocol) and ensures consistent message handling across all agents.

## Envelope Structure

### Core Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | `string` | Yes | Message type. One of: `task_result`, `error`, `needs_input` |
| `protocol_version` | `string` | Yes | Version of the message protocol (e.g., "1.0") |
| `sender_id` | `string` | Yes | Identifier of the sending agent (e.g., "CA", "ARCH") |
| `recipient_id` | `string` | Yes | Identifier of the intended recipient agent |
| `timestamp` | `string` | Yes | ISO 8601 timestamp of message creation |
| `task_id` | `string` | Yes | Identifier of the task this message relates to |
| `retry_count` | `integer` | No | Number of times this message has been retried (default: 0) |
| `trace_id` | `string` | No | Distributed tracing identifier |
| `payload` | `object` | Yes | Message-specific content |
| `context` | `object` | No | Additional context or metadata |

### Message Types

#### 1. Task Result (`task_result`)
Sent when an agent successfully completes a task.

**Example Payload:**
```json
{
  "status": "success",
  "result": {
    "output": "Task completed successfully",
    "artifacts": [
      {
        "type": "file",
        "path": "/output/result.json",
        "description": "Generated output file"
      }
    ]
  },
  "metrics": {
    "duration_ms": 1234,
    "memory_usage_mb": 256
  }
}
```

#### 2. Error (`error`)
Sent when an error occurs during task processing.

**Example Payload:**
```json
{
  "code": "VALIDATION_ERROR",
  "message": "Invalid input format",
  "details": {
    "field": "input_data",
    "issue": "Expected string, got number"
  },
  "retryable": true,
  "suggested_actions": ["validate_input", "retry"]
}
```

#### 3. Needs Input (`needs_input`)
Sent when an agent requires additional input to proceed.

**Example Payload:**
```json
{
  "requested_inputs": [
    {
      "id": "api_key",
      "type": "string",
      "description": "API key for the external service",
      "sensitive": true
    },
    {
      "id": "preference",
      "type": "enum",
      "options": ["option1", "option2"],
      "description": "Select preferred approach"
    }
  ],
  "context": "Configuring the deployment pipeline"
}
```

## JSON Schema

See [MCP_MESSAGE_SCHEMA.json](../../schemas/MCP_MESSAGE_SCHEMA.json) for the complete JSON Schema definition.

## Implementation Notes

1. **Message Validation**: All agents should validate incoming messages against the JSON schema before processing.
2. **Error Handling**: Implement appropriate error handling for malformed messages.
3. **Versioning**: The `protocol_version` field allows for future evolution of the message format.
4. **Security**: Sensitive data should be properly handled and not logged in plaintext.
5. **Idempotency**: Message handlers should be idempotent to safely handle duplicate messages.

## Examples

### Complete Example: Task Result
```json
{
  "type": "task_result",
  "protocol_version": "1.0",
  "sender_id": "CA",
  "recipient_id": "ARCH",
  "timestamp": "2025-05-21T20:00:00Z",
  "task_id": "TASK-070C",
  "retry_count": 0,
  "trace_id": "abc123",
  "payload": {
    "status": "success",
    "result": {
      "output": "Deployment completed successfully",
      "artifacts": [
        {
          "type": "file",
          "path": "/deployments/deploy-20250521/output.log",
          "description": "Deployment log"
        }
      ]
    }
  },
  "context": {
    "deployment_id": "dep-12345",
    "environment": "staging"
  }
}
```

## Version History

- **1.0.0**: Initial version

## Related Documents

- [Agent Communication Protocol](../AGENT_PROTOCOL.md)
- [Error Handling Guidelines](../ERROR_HANDLING.md)
