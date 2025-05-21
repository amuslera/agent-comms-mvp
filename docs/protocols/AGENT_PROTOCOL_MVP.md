# Agent Communication Protocol (MVP)

## Overview
This MVP protocol defines a simple, file-based communication system between agents. Messages are exchanged through a local file system using inbox/outbox directories, making it ideal for development and testing scenarios.

## Directory Structure
Each agent maintains the following directory structure:
```
agent/
├── inbox/          # Incoming messages
├── outbox/         # Outgoing messages
└── archive/        # Processed messages
```

## Message Format
All messages follow a simplified JSON structure:

```json
{
  "type": "string",      // Message type identifier
  "id": "string",        // Unique message identifier (UUID v4)
  "timestamp": "string", // ISO 8601 timestamp
  "sender": "string",    // Sender agent identifier
  "recipient": "string", // Recipient agent identifier
  "content": object,     // Message content (type-specific)
  "version": "string"    // Protocol version (e.g., "1.0.0")
}
```

## Message Types

### 1. Task Assignment
```json
{
  "type": "task_assignment",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2024-03-20T10:00:00Z",
  "sender": "agent-1",
  "recipient": "agent-2",
  "version": "1.0.0",
  "content": {
    "task_id": "TASK-001",
    "description": "Process data files",
    "priority": 1,
    "deadline": "2024-03-21T10:00:00Z",
    "requirements": ["file1.txt", "file2.txt"]
  }
}
```

### 2. Task Status Update
```json
{
  "type": "task_status",
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "timestamp": "2024-03-20T10:05:00Z",
  "sender": "agent-2",
  "recipient": "agent-1",
  "version": "1.0.0",
  "content": {
    "task_id": "TASK-001",
    "status": "in_progress",
    "progress": 50,
    "details": "Processing file1.txt"
  }
}
```

### 3. Error Notification
```json
{
  "type": "error",
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "timestamp": "2024-03-20T10:06:00Z",
  "sender": "agent-2",
  "recipient": "agent-1",
  "version": "1.0.0",
  "content": {
    "error_code": "FILE_NOT_FOUND",
    "message": "Required file file2.txt not found",
    "context": {
      "task_id": "TASK-001",
      "attempted_path": "/path/to/file2.txt"
    }
  }
}
```

## Message Flow

1. **Sending Messages**
   - Agent writes message to its outbox directory
   - Message filename format: `{timestamp}_{message_id}.json`
   - Example: `20240320100000_550e8400-e29b-41d4-a716-446655440000.json`

2. **Receiving Messages**
   - Agent polls its inbox directory for new messages
   - Messages are processed in chronological order
   - After processing, messages are moved to archive directory

3. **Message Processing**
   - Validate message format and required fields
   - Process based on message type
   - Generate appropriate response if needed
   - Archive processed message

## Status Values
For task status updates, use these predefined values:
- `pending`: Task received but not started
- `in_progress`: Task is being processed
- `completed`: Task finished successfully
- `failed`: Task encountered an error
- `cancelled`: Task was cancelled

## Error Codes
Common error codes for the MVP:
- `INVALID_MESSAGE`: Message format is invalid
- `FILE_NOT_FOUND`: Required file is missing
- `PROCESSING_ERROR`: Error during task execution
- `INVALID_TASK`: Task definition is invalid

## Versioning
The protocol version is specified in each message. The MVP uses version "1.0.0".

## Recommended Extensions
For future versions, consider adding:
1. Message acknowledgment system
2. Message priority levels
3. Message expiration
4. Batch processing support
5. Message retry mechanism

## Implementation Notes

1. **File Operations**
   - Use atomic file operations when possible
   - Implement file locking for concurrent access
   - Regular cleanup of archive directory

2. **Error Handling**
   - Log all message processing errors
   - Implement basic retry logic for failed operations
   - Maintain error logs in agent directory

3. **Performance**
   - Regular polling interval: 5 seconds
   - Maximum message size: 1MB
   - Archive cleanup: Keep last 1000 messages

## Example Usage

1. **Sending a Task**
```bash
# Agent-1 creates task assignment
echo '{
  "type": "task_assignment",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2024-03-20T10:00:00Z",
  "sender": "agent-1",
  "recipient": "agent-2",
  "version": "1.0.0",
  "content": {
    "task_id": "TASK-001",
    "description": "Process data files",
    "priority": 1,
    "deadline": "2024-03-21T10:00:00Z",
    "requirements": ["file1.txt", "file2.txt"]
  }
}' > agent-1/outbox/20240320100000_550e8400-e29b-41d4-a716-446655440000.json
```

2. **Receiving and Processing**
```bash
# Agent-2 processes incoming message
mv agent-2/inbox/20240320100000_550e8400-e29b-41d4-a716-446655440000.json agent-2/archive/
```

## References
1. [JSON Schema](https://json-schema.org/)
2. [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601)
3. [UUID](https://tools.ietf.org/html/rfc4122) 