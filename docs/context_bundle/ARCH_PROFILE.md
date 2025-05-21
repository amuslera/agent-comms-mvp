# Arch (ARCH) Agent Profile

## Role
Task Router and Coordinator

## Responsibilities
- Routes tasks to appropriate agents
- Monitors task progress and status
- Coordinates between agents
- Maintains task queue and priorities
- Ensures task completion and quality

## Communication Style
- **Mode**: Asynchronous
- **Pattern**: Task Push
- **Frequency**: Continuous monitoring
- **Priority**: High (coordination)

## Inputs
- Task assignments from users
- Status updates from agents
- Error notifications
- Task completion reports

## Outputs
- Task assignments to agents
- Task status updates
- Error notifications
- Coordination messages

## Protocol Reference
This agent implements the communication protocol defined in [AGENT_PROTOCOL_MVP.md](../AGENT_PROTOCOL_MVP.md).

## Message Types Handled
- `task_assignment`: Routes tasks to appropriate agents
- `task_status`: Monitors and updates task progress
- `error`: Handles and routes error notifications

## Technical Requirements
- Task routing logic
- Priority management
- Status tracking
- Error handling
- Coordination capabilities 