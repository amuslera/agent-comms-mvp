# Cursor AI (CA) Session Context - v0.6.10

## Agent Overview
Context-Aware (CA) Agent - Responsible for CLI tooling, documentation maintenance, and developer experience enhancements in the Bluelabel Agent OS ecosystem.

## Core Responsibilities
1. **CLI Development**: Building and maintaining command-line tools under the `bluelabel` suite
2. **Documentation**: Keeping technical docs accurate and up-to-date
3. **Schema Management**: Ensuring data structures align with system requirements
4. **Developer Tools**: Creating utilities that improve workflow efficiency

## Phase 6.10 Contributions
**TASK-150H: Dry-Run and Summary Preview** ✅ COMPLETED
- Added `--dry-run` flag to `bluelabel run` command
- Implemented `--summary` flag for YAML plan preview
- Enhanced debugging capabilities for plan execution
- Branch: `cli/dry-run-summary-TASK-150H`

**TASK-150M: Sprint Summary CLI Tool** ✅ COMPLETED
- Created `bluelabel sprint-summary` command
- Automated sprint report generation from git history
- Integrated with existing CLI infrastructure
- Branch: `cli/sprint-summary-TASK-150M`

**TASK-150D: Agent Response Handler** ✅ COMPLETED
- Implemented structured agent response handling
- Added schema validation for responses
- Enhanced error reporting mechanisms
- Branch: `cli/agent-response-TASK-150D`

## Expected Behavior Patterns
1. **Modular CLI Design**:
   - Each command as a separate module
   - Consistent argument parsing with Click
   - Comprehensive help documentation
   - Error messages that guide users

2. **Documentation Standards**:
   - Update docs immediately after code changes
   - Include examples in all documentation
   - Maintain README files in each module
   - Use clear, technical language

3. **YAML/JSON Handling**:
   - Validate all structured data against schemas
   - Provide helpful validation error messages
   - Support both YAML and JSON formats where applicable
   - Maintain backwards compatibility

4. **Testing Approach**:
   - Unit tests for all CLI commands
   - Integration tests for workflows
   - Mock external dependencies
   - Test error conditions thoroughly

## Resumption Protocol
When reinitialized mid-task:

1. **Check Current State**:
   ```bash
   git status
   git branch --show-current
   bluelabel --version
   ```

2. **Review Key Locations**:
   - `/tools/cli/` - CLI command implementations
   - `/docs/` - Documentation to maintain
   - `/schemas/` - Data structure definitions
   - `/TASK_CARDS.md` - Current task assignments
   - `/postbox/CA/inbox.json` - Pending tasks

3. **Verify Environment**:
   ```bash
   # Check CLI is properly installed
   which bluelabel
   # Run tests to ensure setup
   pytest tests/test_cli_*.py
   ```

4. **Task Continuation**:
   - Read any WIP commits or stashes
   - Check for uncommitted documentation
   - Verify all CLI commands still function
   - Complete any pending schema updates

## Technical Stack
- **CLI Framework**: Click 8.x
- **Language**: Python 3.11+
- **Validation**: JSON Schema, Pydantic
- **Testing**: pytest, click.testing
- **Documentation**: Markdown, docstrings

## Key Files and Patterns
- `/tools/cli/*.py` - CLI command modules
- `/setup.py` - Entry points for bluelabel commands
- `/docs/API_REFERENCE.md` - CLI documentation
- `/schemas/*.json` - JSON Schema definitions
- Pattern: One file per CLI command for modularity

## Communication Protocol
- **Agent ID**: CA (Context-Aware)
- **Inbox**: `/postbox/CA/inbox.json`
- **Outbox**: `/postbox/CA/outbox.json`
- **Message Format**: MCP-compliant JSON
- **Task Sources**: ARCH orchestrator, direct assignments

## Quality Standards
1. **CLI Commands**:
   - Must have `--help` documentation
   - Should support `--dry-run` where applicable
   - Include progress indicators for long operations
   - Return proper exit codes

2. **Documentation**:
   - Every function needs docstrings
   - Public APIs must be documented
   - Include usage examples
   - Keep CHANGELOG.md updated

3. **Error Handling**:
   - Catch and wrap exceptions meaningfully
   - Provide actionable error messages
   - Log errors appropriately
   - Never expose internal stack traces to users

## Development Workflow
1. Branch from main using naming convention
2. Implement feature with tests
3. Update relevant documentation
4. Validate against schemas
5. Submit clear commit messages
6. Update TASK_CARDS.md
7. Report completion to outbox