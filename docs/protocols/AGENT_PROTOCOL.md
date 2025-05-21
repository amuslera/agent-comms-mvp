# Agent Communication Protocol

## Version: 1.2.0
**Last Updated**: 2025-05-28

## Related Documentation
- [ARCH_PROTOCOL.md](./ARCH_PROTOCOL.md) - ARCH orchestrator protocol
- [AGENT_TASK_PROTOCOL.md](./AGENT_TASK_PROTOCOL.md) - Task handling protocol
- [EXECUTION_FLOW.md](../system/EXECUTION_FLOW.md) - System execution flow

## Version History
- v1.0.0 (MVP): Initial file-based communication system
- v2.0.0 (Current): Enhanced protocol with security and advanced features

## Overview
This document defines the protocol for communication between agents in the system. The protocol is designed to be extensible, secure, and efficient for agent-to-agent communication.

## Message Format
All messages between agents follow a JSON structure with the following fields:

```json
{
  "type": "string",      // Message type identifier
  "id": "string",        // Unique message identifier
  "timestamp": "string", // ISO 8601 timestamp
  "sender": "string",    // Sender agent identifier
  "recipient": "string", // Recipient agent identifier
  "content": object,     // Message content (type-specific)
  "metadata": object,    // Optional metadata
  "version": "string"    // Protocol version
}
```

## Message Types

### 1. Task Assignment
```json
{
  "type": "task_assignment",
  "content": {
    "task_id": "string",
    "description": "string",
    "priority": "number",
    "deadline": "string",
    "requirements": ["string"]
  }
}
```

### 2. Task Status Update
```json
{
  "type": "task_status",
  "content": {
    "task_id": "string",
    "status": "string",
    "progress": "number",
    "details": "string"
  }
}
```

### 3. Resource Request
```json
{
  "type": "resource_request",
  "content": {
    "resource_type": "string",
    "quantity": "number",
    "priority": "number",
    "duration": "string"
  }
}
```

### 4. Resource Allocation
```json
{
  "type": "resource_allocation",
  "content": {
    "request_id": "string",
    "allocated": "boolean",
    "resources": ["string"],
    "valid_until": "string"
  }
}
```

### 5. Error Notification
```json
{
  "type": "error",
  "content": {
    "error_code": "string",
    "message": "string",
    "context": object
  }
}
```

## Communication Flow

### File-Based (MVP)
1. Agent writes message to outbox directory
2. Message filename format: `{timestamp}_{message_id}.json`
3. Recipient polls inbox directory
4. Processed messages moved to archive

### WebSocket-Based (Current)
1. Secure connection establishment
2. Asynchronous message exchange
3. Message acknowledgment
4. Automatic retry mechanism

## Security

### Authentication
- Agent certificates required
- Message signing with private keys
- Public key verification

### Encryption
- TLS 1.3 for all connections
- End-to-end encryption
- Regular key rotation

## Best Practices

### Message Handling
- Validate message format
- Implement error handling
- Log all exchanges
- Maintain message history

### Resource Management
- Release resources after use
- Implement timeouts
- Handle concurrent requests

### Error Recovery
- Graceful degradation
- State consistency
- Clear error messages

## Implementation Notes

### Language Support
- TypeScript/JavaScript implementation
- JSON Schema validation
- Type definitions available

### Performance
- Message compression
- Batch processing
- Connection pooling

### Monitoring
- Latency tracking
- Error rate monitoring
- Resource usage metrics

## Future Considerations

### Planned Features
- Message queuing
- Advanced routing
- Enhanced security

### Known Limitations
- Max message size: 10MB
- Max connections: 1000
- Max rate: 1000/second

## References
1. [WebSocket Protocol](https://tools.ietf.org/html/rfc6455)
2. [JSON Schema](https://json-schema.org/)
3. [TLS 1.3](https://tools.ietf.org/html/rfc8446)

## Extensions

The protocol can be extended by:
1. Adding new message types
2. Extending existing message content
3. Adding new metadata fields

All extensions must be documented and versioned appropriately.

## Implementation Notes

1. **Language Support**
   - Protocol implementation available in TypeScript/JavaScript
   - Message validation using JSON Schema
   - Type definitions for all message types

2. **Performance Considerations**
   - Message compression for large payloads
   - Batch processing for multiple messages
   - Connection pooling for multiple agents

3. **Monitoring**
   - Message latency tracking
   - Error rate monitoring
   - Resource usage metrics

## Future Considerations

1. **Planned Features**
   - Message queuing for offline agents
   - Advanced routing capabilities
   - Enhanced security features

2. **Known Limitations**
   - Maximum message size: 10MB
   - Maximum concurrent connections: 1000
   - Maximum message rate: 1000/second

## References

1. [WebSocket Protocol](https://tools.ietf.org/html/rfc6455)
2. [JSON Schema](https://json-schema.org/)
3. [TLS 1.3](https://tools.ietf.org/html/rfc8446) 