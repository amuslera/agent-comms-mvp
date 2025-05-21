# Agent Communication System - Shared Context

## Project Purpose
The agent-comms-mvp is a proof-of-concept system demonstrating multi-agent collaboration through file-based communication. It showcases how AI assistants can work together on complex development tasks using a shared postbox architecture.

## Architecture Vision
This system enables multiple AI agents to collaborate asynchronously on software development tasks through:
- Clear role separation and responsibilities
- File-based message passing via postbox directories
- Structured task delegation and coordination
- Persistent communication logs for transparency

## Agent Roles

### Code Creator (CC)
- **Primary Role**: Implements technical solutions and code artifacts
- **Responsibilities**:
  - Write, modify, and refactor code
  - Create technical documentation
  - Implement tests and validation
  - Handle git operations (commits, branches, PRs)
- **Profile**: `contexts/CC_PROFILE.md`
- **Prompt Template**: `prompts/Claude_Code_PROMPT_TEMPLATE.md`

### Cursor AI (CA)
- **Primary Role**: Code analysis, debugging, and optimization
- **Responsibilities**:
  - Review code for quality and best practices
  - Debug issues and suggest fixes
  - Optimize performance
  - Assist with complex refactoring
- **Profile**: `contexts/CA_PROFILE.md`
- **Prompt Template**: `prompts/Cursor_AI_PROMPT_TEMPLATE.md`

### Web Assistant (WA)
- **Primary Role**: Research, documentation, and external resource gathering
- **Responsibilities**:
  - Research technologies and solutions
  - Gather documentation and examples
  - Create user-facing documentation
  - Provide external context and references
- **Profile**: `contexts/WA_PROFILE.md`
- **Prompt Template**: `prompts/Web_Assistant_PROMPT_TEMPLATE.md`

### Architect (ARCH)
- **Primary Role**: System design and task coordination
- **Responsibilities**:
  - Define system architecture
  - Break down complex tasks
  - Coordinate agent activities
  - Ensure design consistency
- **Profile**: `contexts/ARCH_PROFILE.md`

## Communication Model

### File-Based Postbox System
Each agent has a dedicated postbox directory at `postbox/{AGENT_NAME}/`:
- `inbox.json`: Messages received from other agents
- `outbox.json`: Messages sent to other agents
- `task_log.md`: Record of completed tasks and actions

### Message Format
Messages follow the structure defined in `AGENT_PROTOCOL_MVP.md`:
```json
{
  "message_id": "unique-identifier",
  "from": "SENDER_AGENT",
  "to": "RECIPIENT_AGENT",
  "timestamp": "ISO-8601",
  "message_type": "task|response|notification",
  "content": "message content",
  "metadata": {}
}
```

### Communication Flow
1. Agent writes message to their `outbox.json`
2. System (human facilitator) transfers message to recipient's `inbox.json`
3. Recipient processes message and responds if needed
4. All actions logged in respective `task_log.md` files

## Task Management

### Task Assignment
- Tasks are defined in `TASK_CARDS.md`
- Each task specifies:
  - Assigned agent
  - Goal and deliverables
  - Branch naming convention
  - Commit message format
  - Completion criteria

### Task Workflow
1. Agent receives task assignment
2. Creates feature branch following naming convention
3. Implements solution
4. Documents actions in task log
5. Commits with specified prefix
6. Updates task status in `TASK_CARDS.md`
7. Opens PR to main branch

### Task Tracking
- All tasks listed in `TASK_CARDS.md`
- Status indicators:
  - 🔄 In Progress
  - ✅ Done
  - ⏸️ Blocked
  - 📝 Review Needed

## References
- **Protocol Definition**: `AGENT_PROTOCOL_MVP.md`
- **Prompt Templates**: `prompts/` directory
- **Agent Profiles**: `contexts/` directory
- **Task List**: `TASK_CARDS.md`

## Best Practices
1. Always check inbox before starting work
2. Document all significant actions in task logs
3. Use structured message format for communication
4. Follow branch and commit conventions
5. Update task status promptly
6. Reference other agents when coordination needed