# Plan Templates Documentation

This document provides an overview of the available plan templates and their use cases.

## Available Templates

### 1. Basic Single-Agent Plan
**File**: `/plans/templates/basic-single-agent.yaml`  
**Description**: A simple template for single-agent tasks with no dependencies.  
**Use Case**: Ideal for straightforward tasks that can be completed by one agent without dependencies or approvals.

### 2. Multi-Agent DAG Plan
**File**: `/plans/templates/multi-agent-dag.yaml`  
**Description**: A complex template demonstrating parallel task execution and agent handoffs.  
**Use Case**: Perfect for data processing pipelines where multiple agents work together in a specific sequence.

### 3. Approval-Gated Flow Plan
**File**: `/plans/templates/approval-gated-flow.yaml`  
**Description**: A template for workflows requiring human approval at specific stages.  
**Use Case**: Suitable for critical operations where human review is required before proceeding.

## Template Fields

Each template uses the following core fields:

- `plan_id`: Unique identifier for the plan
- `version`: Plan version number
- `name`: Human-readable plan name
- `owner`: Agent responsible for the plan
- `created_at`: Creation timestamp
- `tasks`: Array of task definitions

### Task Fields

Each task includes:

- `task_id`: Unique identifier for the task
- `agent`: Agent assigned to the task (CA, CC, WA, or ARCH)
- `task_type`: Type of task (e.g., data_processing, validation)
- `description`: Human-readable task description
- `content`: Task-specific configuration
  - `input`: Input data or task reference
  - `parameters`: Task-specific parameters
- `requires`: Array of task dependencies
- `approval`: Boolean indicating if human approval is required

## Usage

To use these templates with the CLI:

```bash
# Create a new plan from template
bluelabel new-plan my-plan --template basic-single-agent

# List available templates
bluelabel new-plan --list-templates
```

## Best Practices

1. Always use descriptive task IDs
2. Keep task descriptions clear and concise
3. Use approval gates for critical operations
4. Consider agent strengths when assigning tasks
5. Test plan execution with `--dry-run` before running 