# Alert Policy Format Specification

## Overview

This document defines the YAML-based alert policy format used by the Bluelabel Agent OS to configure task-level triggers, conditions, and notification actions. Alert policies allow system administrators to define rules that trigger notifications or actions when specific conditions are met during task execution.

> **Version**: 1.0.0  
> **Status**: Active  
> **Last Updated**: 2025-05-21

## File Structure

Alert policies are defined in YAML files (typically named `alert_policy.yaml`) with the following structure:

```yaml
version: "1.0.0"
description: "Policy for monitoring critical tasks"
rules:
  - name: "Notify on CA errors"
    condition:
      type: error
      agent: CA
      retry_count: 2
    action:
      notify: human
      method: console_log
      
  - name: "Low score alert"
    condition:
      type: task_result
      score_below: 0.7
    action:
      notify: webhook
      url: https://hooks.example.com/low-score
```

## Schema Reference

### Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | `string` | Yes | Version of the alert policy format (e.g., "1.0.0") |
| `description` | `string` | No | Human-readable description of the policy |
| `rules` | `array` | Yes | List of alert rules (at least one required) |

### Rule Object

Each rule defines a condition and the action to take when that condition is met.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | Yes | Unique name for the rule |
| `enabled` | `boolean` | No | Whether the rule is active (default: true) |
| `condition` | `object` | Yes | Condition that triggers the alert |
| `action` | `object` | Yes | Action to take when condition is met |

### Condition Types

#### Error Condition
Triggers when a task fails with an error.

```yaml
condition:
  type: error
  agent: CA               # Optional: Filter by agent ID
  retry_count: 2          # Optional: Minimum number of retries before triggering
  error_code: "E_TIMEOUT"  # Optional: Specific error code to match
```

#### Task Result Condition
Triggers based on task result metrics.

```yaml
condition:
  type: task_result
  score_below: 0.7        # Trigger if score < 0.7
  # Alternative: score_above: 0.9  # Trigger if score > 0.9
  duration_above: 60      # Optional: Duration in seconds
  agent: "*"              # Optional: Filter by agent ID ("*" for any)
```

### Action Types

#### Console Log Action
Logs the alert to the console.


```yaml
action:
  notify: human
  method: console_log
  level: warning         # debug, info, warning, error, critical
  message: "Custom alert message"  # Optional
```

#### Webhook Action
Sends an HTTP POST request to a webhook URL.

```yaml
action:
  notify: webhook
  url: https://hooks.example.com/alerts
  method: POST           # Optional, default: POST
  headers:               # Optional headers
    Authorization: "Bearer token"
  template: |           # Optional template for the request body
    {
      "alert": "{{.Name}}",
      "message": "Alert triggered: {{.Message}}",
      "timestamp": "{{.Timestamp}}"
    }
```

## Integration with ARCH Agent

The ARCH agent is responsible for:
1. Loading alert policies from the configured directory
2. Evaluating conditions for each task result or error
3. Executing the corresponding actions when conditions are met
4. Logging all alert activity

### Policy Loading
- Policies are loaded from `/etc/bluelabel/alert_policies/` by default
- Files must have `.yaml` or `.yml` extension
- Multiple policy files are merged (with later files taking precedence)

### Alert Context
When an alert is triggered, the following context is available for templates:

```go
type AlertContext struct {
    Name        string      // Rule name
    Type        string      // Condition type (error, task_result)
    Timestamp   time.Time   // When the alert was triggered
    TaskID      string      // ID of the triggering task
    AgentID     string      // ID of the agent that triggered the alert
    Message     string     // Human-readable message
    Condition   interface{} // Original condition that was met
    TaskResult  interface{} // Full task result (if applicable)
    Error       error      // Error details (if applicable)
}
```

## Example Policies

### 1. Critical Error Notification
```yaml
version: "1.0.0"
description: "Notify on critical errors"
rules:
  - name: "Critical CA errors"
    condition:
      type: error
      agent: CA
      error_code: "E_CRITICAL"
    action:
      notify: webhook
      url: https://alerts.example.com/critical
      headers:
        Authorization: "Bearer abc123"
      template: |
        {
          "text": "🚨 Critical error in {{.AgentID}}: {{.Message}}",
          "task_id": "{{.TaskID}}",
          "timestamp": "{{.Timestamp}}"
        }
```

### 2. Performance Monitoring
```yaml
version: "1.0.0"
description: "Monitor task performance"
rules:
  - name: "Slow tasks"
    condition:
      type: task_result
      duration_above: 300  # 5 minutes
    action:
      notify: human
      method: console_log
      level: warning
      message: "Task {{.TaskID}} took too long to complete"

  - name: "Low confidence results"
    condition:
      type: task_result
      score_below: 0.6
    action:
      notify: webhook
      url: https://alerts.example.com/low-confidence
      template: |
        {
          "text": "⚠️ Low confidence result ({{.TaskResult.score}})",
          "task_id": "{{.TaskID}}",
          "agent": "{{.AgentID}}",
          "details": "{{.TaskResult.notes}}"
        }
```
