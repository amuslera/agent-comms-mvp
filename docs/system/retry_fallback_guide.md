# ARCH Orchestrator Retry and Fallback Guide

## Overview

The ARCH Orchestrator now supports advanced retry and fallback mechanisms to ensure robust task execution across the multi-agent system. This guide explains how to configure and use these features.

## Features

### 1. Retry Logic
- Tasks can be automatically retried upon failure
- Configurable maximum retry attempts per task
- Exponential backoff between retry attempts
- Detailed logging of retry attempts

### 2. Fallback Support
- Specify alternative agents to handle failed tasks
- Automatic routing to fallback agents after primary agent failures
- Maintains task context during fallback transitions

## Configuration

### Task-Level Configuration

Add these fields to any task in your YAML plan:

```yaml
tasks:
  - task_id: "example_task"
    agent: "CA"  # Primary agent
    type: "task_assignment"
    content:
      action: "process_data"
      # ... other parameters
    
    # Retry configuration
    max_retries: 3  # Number of attempts (default: 1)
    
    # Fallback configuration
    fallback_agent: "CC"  # Alternative agent if primary fails
```

### Behavior

1. **Default Behavior**: If `max_retries` is not specified, tasks will execute once
2. **Retry Logic**: 
   - Tasks are retried on the same agent until `max_retries` is reached
   - Exponential backoff: 5s, 10s, 20s, etc.
3. **Fallback Logic**:
   - After first failure on primary agent, subsequent attempts use fallback agent
   - If no fallback is specified, all retries occur on the primary agent

## Examples

### Simple Retry
```yaml
- task_id: "data_processing"
  agent: "CA"
  type: "task_assignment"
  content:
    action: "process_files"
  max_retries: 3  # Try up to 3 times on CA
```

### Retry with Fallback
```yaml
- task_id: "report_generation"
  agent: "WA"
  type: "task_assignment"
  content:
    action: "generate_report"
  max_retries: 2
  fallback_agent: "CC"  # Try once on WA, then on CC
```

### Critical Task with Aggressive Retry
```yaml
- task_id: "critical_health_check"
  agent: "CC"
  type: "task_assignment"
  content:
    action: "system_health_check"
  max_retries: 5  # Try up to 5 times
  fallback_agent: "CA"  # Use CA if CC fails all attempts
```

## Execution Flow

1. Task dispatched to primary agent
2. Agent runner triggered
3. Monitor task completion
4. On failure:
   - If retries remain and no fallback: retry on same agent
   - If retries remain and fallback exists: try fallback agent
   - If no retries remain: mark task as failed
5. On success: mark task as completed

## Logging and Monitoring

The orchestrator provides detailed logging:

```
Executing task example_task (attempt 1/3) on agent CA
Task example_task failed, retrying in 5 seconds...
Attempting with fallback agent: CC
Task example_task completed successfully on CC (attempt 2)
```

## Best Practices

1. **Set Reasonable Retry Limits**: Too many retries can delay execution
2. **Choose Appropriate Fallbacks**: Select agents with similar capabilities
3. **Consider Task Priority**: Critical tasks may need more aggressive retry strategies
4. **Monitor Performance**: Use logs to identify tasks that frequently require retries

## Error Messages

Common error messages and their meanings:

- `"Task X timed out on agent Y"`: Task exceeded timeout limit
- `"Failed all N attempts"`: Task failed after exhausting retries
- `"Dispatch failed"`: Unable to send task to agent's inbox
- `"Agent runner failed"`: Unable to start agent process

## Future Enhancements

Planned improvements include:
- Configurable backoff strategies (linear, exponential, custom)
- Health-based agent selection
- Retry policies based on error types
- Circuit breaker patterns