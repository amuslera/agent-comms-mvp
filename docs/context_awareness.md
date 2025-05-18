# Context Awareness Framework

This document describes the context awareness framework that enables agents to maintain persistent memory across task executions.

## Overview

The context awareness framework provides a way for agents to maintain state and knowledge between task executions. Each agent has its own context file that persists across sessions and can be used to store preferences, state, history, and other relevant information.

## Context Structure

Each agent's context is stored in a JSON file with the following structure:

```json
{
  "agent_id": "AGENT_ID",
  "created_at": "ISO_TIMESTAMP",
  "updated_at": "ISO_TIMESTAMP",
  "version": "1.0.0",
  "preferences": {},
  "knowledge": {},
  "state": {},
  "history": {},
  "custom": {}
}
```

### Sections:

1. **preferences**: Agent-specific settings and preferences
2. **knowledge**: Persistent knowledge and learned information
3. **state**: Current runtime state (resets on restart)
4. **history**: Historical data and logs
5. **custom**: Custom data specific to the agent's implementation

## Context Manager

The `ContextManager` class provides methods to load, save, and update agent contexts:

```python
from tools.context_manager import ContextManager

# Initialize with custom context directory (optional)
manager = ContextManager(context_dir="path/to/contexts")

# Load a context (creates default if not exists)
context = manager.load_context("AGENT_ID")

# Update context
updates = {
    "state": {
        "last_activity": "2023-01-01T12:00:00Z",
        "status": "active"
    }
}
manager.update_context("AGENT_ID", updates)

# Save context (automatically updates timestamp)
manager.save_context("AGENT_ID")
```

## Context Inspector CLI

The `context_inspector.py` tool provides a command-line interface to inspect and modify agent contexts:

```bash
# View an agent's entire context
python tools/context_inspector.py --agent AGENT_ID --view

# Get a specific value
python tools/context_inspector.py --agent AGENT_ID --get preferences.theme

# Set a value
python tools/context_inspector.py --agent AGENT_ID --set preferences.theme dark

# Delete a key
python tools/context_inspector.py --agent AGENT_ID --delete preferences.old_setting

# List all available agent contexts
python tools/context_inspector.py --list-agents
```

## Integration with Agent Runner

The agent runner has been updated to automatically load and save agent contexts during task execution. The context is made available to tasks via the `agent_context` parameter:

```python
def process_task(task_data, agent_context=None):
    # Access context
    if agent_context is None:
        agent_context = {}
    
    # Update context if needed
    agent_context.setdefault("task_count", 0)
    agent_context["task_count"] += 1
    
    # Return updated context to be saved
    return {"result": "success"}, agent_context
```

## Best Practices

1. **Namespace your keys**: Use dot notation to organize related settings (e.g., `ui.theme`, `api.retry_count`)
2. **Handle missing values**: Always check if a key exists before accessing it
3. **Keep context small**: Store only essential data in the context
4. **Use appropriate data types**: Store data in the most appropriate format (e.g., timestamps as ISO strings)
5. **Version your schema**: Include a version number to handle schema migrations

## Security Considerations

- Context files may contain sensitive information. Ensure proper file permissions are set.
- Validate and sanitize all context data before use.
- Be cautious when sharing context between different security contexts.

## Example Contexts

### Web Assistant (WA)

```json
{
  "agent_id": "WA",
  "preferences": {
    "theme": "light",
    "notifications": true,
    "language": "en"
  },
  "knowledge": {
    "user_preferences": {
      "favorite_topics": ["technology", "science"]
    }
  }
}
```

### Code Assistant (CA)
```json
{
  "agent_id": "CA",
  "preferences": {
    "indent_style": "spaces",
    "indent_size": 2
  },
  "knowledge": {
    "recent_files": ["app.py", "utils/helpers.py"]
  }
}
```
