# Claude Code (CC) Session Context - v0.6.10

## Project Overview
Bluelabel Agent OS - Multi-agent system for AI-assisted software development with DAG-based task execution, MCP-compliant messaging, and comprehensive CLI/UI tooling.

## Phase 6.10 Summary (CC Contributions)
**TASK-150C: MCP Schema Compliance Fix** ✅ MERGED
- Fixed MCP schema validation issues with strict compliance
- Updated message format validation
- Enhanced error handling for schema violations
- Branch: `core/mcp-schema-fix-TASK-150C`

**TASK-100A: Plan Context Engine + Conditional Evaluator** ✅ COMPLETED
- Implemented PlanContextEngine for runtime context management
- Added when/unless conditional execution support
- Safe expression evaluation with sandboxed environment
- Automatic context updates from task results
- 25+ unit tests for comprehensive coverage

**Supporting Work**:
- Code review and merge support for other Phase 6.10 tasks
- Schema validation improvements
- Test coverage enhancements

## Current Architecture (Post v0.6.10)
```
/agent-comms-mvp/
├── apps/              # Application layer
│   ├── api/          # FastAPI backend
│   └── web/          # React frontend with DAG visualization
├── tools/            # CLI and utilities
│   ├── arch/         # ARCH-specific tools (plan runner, router)
│   └── cli/          # General CLI tools
├── postbox/          # Agent communication (inbox/outbox)
├── schemas/          # JSON schemas for validation
├── contexts/         # Agent profile documents
├── docs/             # Documentation
│   ├── system/       # Architecture and design docs
│   ├── protocols/    # Communication protocols
│   └── releases/     # Sprint and release notes
└── plans/            # YAML execution plans
```

## Working Patterns
1. **Branching Strategy**:
   - Feature branches: `feat/TASK-XXX-description`
   - Core branches: `core/feature-TASK-XXX`
   - Meta branches: `meta/topic-TASK-XXX`
   - Always create PR-ready branches from main

2. **Development Flow**:
   - Use TodoWrite/TodoRead for task planning
   - Read existing code before implementing
   - Write tests alongside implementation
   - Update TASK_CARDS.md upon completion
   - Report to /postbox/CC/outbox.json

3. **Code Standards**:
   - Type hints and dataclasses preferred
   - Comprehensive error handling
   - MCP schema compliance mandatory
   - JSON Schema validation for all messages

4. **Testing Discipline**:
   - Unit tests for all new functionality
   - Integration tests for cross-component features
   - Schema validation tests required
   - Mock external dependencies

## Last Known State (v0.6.10)
- **Current Tag**: v0.6.10 (Phase 6.10 complete)
- **Branch Status**: All Phase 6.10 branches merged
- **Pending**: WA review tasks may be ongoing
- **System State**: Production-ready with full DAG execution
- **Key Features Active**:
  - Conditional task execution (when/unless)
  - DAG-aware logging with execution traces
  - MCP-compliant messaging
  - CLI tools suite (bluelabel commands)
  - React UI with plan visualization

## Reinitialization Protocol
When restarting mid-task:

1. **Check Current Branch**: `git status` and `git branch`
2. **Read Key Files**:
   - `/TASK_CARDS.md` - Current task status
   - `/postbox/CC/inbox.json` - Pending tasks
   - `/CLAUDE_CONTEXT.md` - This file
   - Task-specific files from branch name

3. **Review Recent Work**:
   - `git log --oneline -10` - Recent commits
   - Check TodoRead for in-progress items
   - Review any test failures

4. **Resume Pattern**:
   - If tests exist, run them first
   - Check for uncommitted changes
   - Complete any in-progress todos
   - Update TASK_CARDS.md if needed
   - Report completion to outbox

## Key Dependencies & Tools
- **Language**: Python 3.11+
- **Backend**: FastAPI, Pydantic, YAML
- **Frontend**: React, TypeScript, Tailwind CSS, ReactFlow
- **Testing**: pytest, Jest
- **CLI**: Click-based `bluelabel` command suite
- **Validation**: JSON Schema 2020-12

## Agent Communication
- **Role**: Claude Code (CC) - Core implementation agent
- **Inbox**: `/postbox/CC/inbox.json`
- **Outbox**: `/postbox/CC/outbox.json`
- **Message Format**: MCP-compliant JSON
- **Task Assignment**: Via ARCH orchestrator

## Critical Files for Context
- `/tools/arch/plan_runner.py` - DAG execution engine
- `/tools/arch/plan_utils.py` - Plan utilities & context engine
- `/schemas/MCP_MESSAGE_SCHEMA.json` - Message format
- `/docs/protocols/AGENT_PROTOCOL.md` - Communication rules
- `/contexts/CC_PROFILE.md` - Agent capabilities