# Web Assistant (WA) Agent Profile

## Role
Web Interface Agent

## Responsibilities
- Manages web-based user interactions
- Handles user input and requests
- Provides web interface updates
- Manages web-related configurations
- Coordinates with other agents for web tasks

## Communication Style
- **Mode**: Asynchronous
- **Pattern**: Task Push
- **Frequency**: Event-driven
- **Priority**: Medium (user-facing)

## Inputs
- User interface requests
- Web configuration updates
- Task assignments for web features
- Error notifications

## Outputs
- Web interface updates
- User feedback
- Task status updates
- Error reports

## Protocol Reference
This agent implements the communication protocol defined in [AGENT_PROTOCOL_MVP.md](../AGENT_PROTOCOL_MVP.md).

## Message Types Handled
- `task_assignment`: Receives web-related tasks
- `task_status`: Sends web task progress updates
- `error`: Reports web interface issues

## Technical Requirements
- Web interface management
- User input handling
- JSON message processing
- Error reporting
- Web configuration management 