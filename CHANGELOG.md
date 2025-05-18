# Changelog

All notable changes to the Agent Communication System will be documented in this file.

## [v1.0.0] - 2025-05-18

### Initial Agent OS Core Completed

This release marks the completion of Phase 1, establishing the foundational infrastructure for multi-agent communication and task coordination.

### Added

#### Core Infrastructure
- **Agent Runner** (`/agent_runner.py`): CLI tool for agent task execution and lifecycle management
  - Message validation against protocol schema
  - Task simulation and execution
  - Agent self-initialization with `--init` flag
  - Task logging and status reporting

#### Communication Protocol
- **Exchange Protocol** (`/exchange_protocol.json`): JSON schema for standardized agent messaging
  - Support for task_assignment, task_status, and error message types
  - Message validation and routing specifications
  - Example implementations for each message type

#### Agent Tools
- **Task Injection CLI** (`/tools/task_dispatcher.py`): Interactive tool for injecting tasks into agent inboxes
- **Inbox Monitor** (`/tools/inbox_monitor.py`): Real-time monitoring of agent inbox messages
- **Flow Visualizer** (`/tools/flow_visualizer.py`): Terminal-based dashboard for outbox monitoring with curses UI

#### Message Routing
- **Central Router** (`/router/router.py`): Automated message distribution system
  - Scans all agent outboxes for new messages
  - Validates messages against protocol schema
  - Routes messages to recipient inboxes
  - Archives processed messages

#### Testing & Simulation
- **Simulation Framework** (`/simulation/task_handlers.py`): Modular task execution stubs
- **E2E Test Harness** (`/tests/test_agent_flow.py`): Comprehensive message flow validation

#### Documentation
- Agent profiles and contexts for CC, CA, WA, and ARCH agents
- Prompt templates for agent-specific behavior
- Task card system for project management

### System Status
- MVP core functionality achieved
- File-based message passing operational
- Basic agent coordination established
- Testing infrastructure in place

### Contributors
- CC (Claude Code): Core infrastructure and routing
- CA (Cursor AI): Implementation and validation
- WA (Web Assistant): UI tools and monitoring
- ARCH: Task coordination and architecture

[v1.0.0]: https://github.com/amuslera/agent-comms-mvp/releases/tag/v1.0.0-agent-core