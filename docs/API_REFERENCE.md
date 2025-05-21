# Bluelabel Agent OS API Reference

## Overview

The Bluelabel Agent OS API provides a RESTful interface for monitoring and managing the multi-agent system. It exposes endpoints for checking system health, retrieving agent information, and tracking task execution status.

### Base URL

```
http://localhost:8000
```

### Authentication

Currently, the API does not require authentication. In production, this will be updated to use secure authentication mechanisms.

### Response Format

All responses are returned in JSON format with appropriate HTTP status codes:
- 200: Success
- 404: Resource not found
- 500: Server error

## Endpoints

### Health Check

#### GET /health

Check the health status of the API server.

**Response**

```json
{
    "status": "healthy",
    "timestamp": "2025-05-21T10:15:30Z",
    "version": "0.1.0"
}
```

### Agents

#### GET /agents

Retrieve a list of all agents in the system.

**Query Parameters**

- `status` (optional): Filter agents by status (active, idle, inactive, error)

**Response**

```json
{
    "agents": [
        {
            "id": "CC",
            "name": "Claude Code",
            "status": "active",
            "description": "Backend Infrastructure Agent",
            "role": "Core system implementation, message handling",
            "capabilities": ["task_execution", "code_generation", "routing"],
            "last_active": "2025-05-21T10:15:30Z",
            "tasks_completed": 42,
            "tasks_failed": 3,
            "tasks_in_progress": 2
        }
    ],
    "count": 1
}
```

#### GET /agents/{agent_id}

Retrieve details for a specific agent.

**Path Parameters**

- `agent_id`: The ID of the agent to retrieve

**Response**

```json
{
    "id": "CC",
    "name": "Claude Code",
    "status": "active",
    "description": "Backend Infrastructure Agent",
    "role": "Core system implementation, message handling",
    "capabilities": ["task_execution", "code_generation", "routing"],
    "last_active": "2025-05-21T10:15:30Z",
    "tasks_completed": 42,
    "tasks_failed": 3,
    "tasks_in_progress": 2
}
```

### Tasks

#### GET /tasks

Retrieve a list of recent task runs.

**Query Parameters**

- `status` (optional): Filter tasks by status (pending, in_progress, completed, failed, cancelled)
- `agent_id` (optional): Filter tasks by agent ID
- `limit` (optional, default: 10): Maximum number of tasks to return
- `offset` (optional, default: 0): Number of tasks to skip

**Response**

```json
{
    "tasks": [
        {
            "id": "TASK-001",
            "description": "Process data files",
            "status": "in_progress",
            "agent_id": "CA",
            "priority": "medium",
            "created_at": "2025-05-21T09:30:00Z",
            "updated_at": "2025-05-21T09:35:00Z",
            "start_time": "2025-05-21T09:35:00Z",
            "end_time": null,
            "retries": 0,
            "fallback_agent": null,
            "details": [
                "Started at: 2025-05-21 09:35:00",
                "Processing file1.txt"
            ],
            "content": {
                "task_id": "TASK-001",
                "action": "process",
                "parameters": {
                    "file": "file1.txt"
                }
            }
        }
    ],
    "count": 1
}
```

#### GET /tasks/{task_id}

Retrieve details for a specific task.

**Path Parameters**

- `task_id`: The ID of the task to retrieve

**Response**

```json
{
    "id": "TASK-001",
    "description": "Process data files",
    "status": "in_progress",
    "agent_id": "CA",
    "priority": "medium",
    "created_at": "2025-05-21T09:30:00Z",
    "updated_at": "2025-05-21T09:35:00Z",
    "start_time": "2025-05-21T09:35:00Z",
    "end_time": null,
    "retries": 0,
    "fallback_agent": null,
    "details": [
        "Started at: 2025-05-21 09:35:00",
        "Processing file1.txt"
    ],
    "content": {
        "task_id": "TASK-001",
        "action": "process",
        "parameters": {
            "file": "file1.txt"
        }
    }
}
```

## Data Models

### Agent

```typescript
interface Agent {
    id: string;
    name: string;
    status: "active" | "idle" | "inactive" | "error";
    description: string;
    role: string;
    capabilities: string[];
    last_active: string | null;
    tasks_completed: number;
    tasks_failed: number;
    tasks_in_progress: number;
}
```

### Task

```typescript
interface Task {
    id: string;
    description: string;
    status: "pending" | "in_progress" | "completed" | "failed" | "cancelled" | "timeout";
    agent_id: string;
    priority: "low" | "medium" | "high";
    created_at: string;
    updated_at: string | null;
    start_time: string | null;
    end_time: string | null;
    retries: number;
    fallback_agent: string | null;
    details: string[];
    content: {
        task_id: string;
        action: string;
        parameters: Record<string, any>;
    } | null;
}
```

## Versioning and Future Extensions

The API is currently at version 0.1.0. Future versions will include:

1. Authentication and authorization
2. WebSocket endpoints for real-time updates
3. Task creation and management endpoints
4. Agent configuration endpoints
5. System metrics and monitoring endpoints

## Error Handling

The API uses standard HTTP status codes and returns error details in the response body:

```json
{
    "detail": "Agent CC not found"
}
```

Common error codes:
- 400: Bad Request
- 404: Not Found
- 500: Internal Server Error 