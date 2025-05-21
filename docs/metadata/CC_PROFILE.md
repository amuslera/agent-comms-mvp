# Claude Code (CC) Agent Profile

## Role
Backend Infrastructure Agent

## Responsibilities
- Implements and maintains the core agent communication system
- Handles file-based message routing and processing
- Manages message validation and error handling
- Maintains system state and message archives
- Provides debugging and logging capabilities

## Communication Style
- **Mode**: Asynchronous
- **Pattern**: Task Push
- **Frequency**: Continuous monitoring of inbox
- **Priority**: High (core system component)

## Inputs
- Task assignments from other agents
- System configuration updates
- Error notifications
- Status update requests

## Outputs
- Task status updates
- System health reports
- Error notifications
- Implementation results

## Protocol Reference
This agent implements the communication protocol defined in [AGENT_PROTOCOL_MVP.md](../AGENT_PROTOCOL_MVP.md).

## Message Types Handled
- `task_assignment`: Receives and processes task assignments
- `task_status`: Sends status updates for ongoing tasks
- `error`: Sends and receives error notifications

## Technical Requirements
- File system access for message handling
- JSON parsing and validation
- UUID generation
- Timestamp management
- Error logging capabilities 