# Bluelabel Agent OS API Reference

## Overview

This document provides a comprehensive reference for the Bluelabel Agent OS API, which allows you to interact with the system programmatically. The API exposes information about agents and tasks in the system, enabling frontend and external integrations.

> **API Version**: 0.1.0  
> **Base URL**: `http://localhost:8000`

## Authentication

Authentication is not implemented in the current version. For production deployments, proper authentication should be added.

## CORS

Cross-Origin Resource Sharing (CORS) is enabled for all origins (`*`) in the current development version. For production deployments, this should be restricted to specific trusted origins.

## Endpoints

### Health Check

#### `GET /health`

Provides a simple heartbeat endpoint to check API health.

**Response Example**:
```json
{
  "status": "healthy",
  "timestamp": "2025-05-21T11:25:30.123456Z",
  "version": "0.1.0"
}
```

### Agents

#### `GET /agents`

Returns a list of all agents in the system.

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | Filter agents by status (active, idle, inactive, error) |

**Response Schema**:
```typescript
interface AgentList {
  agents: Agent[];
  count: number;
}

interface Agent {
  id: string;
  name: string;
  status: "active" | "idle" | "inactive" | "error";
  description: string;
  role: string;
  capabilities: string[];
  last_active?: string;
  tasks_completed: number;
  tasks_failed: number;
  tasks_in_progress: number;
}
```

**Response Example**:
```json
{
  "agents": [
    {
      "id": "ARCH",
      "name": "Architecture Agent",
      "status": "active",
      "description": "System orchestrator and task router",
      "role": "orchestrator",
      "capabilities": ["planning", "routing", "monitoring"],
      "last_active": "2025-05-21T11:20:15.123456Z",
      "tasks_completed": 42,
      "tasks_failed": 3,
      "tasks_in_progress": 2
    },
    {
      "id": "CA",
      "name": "Context Awareness Agent",
      "status": "idle",
      "description": "Task implementation and context manager",
      "role": "implementer",
      "capabilities": ["coding", "documentation", "testing"],
      "last_active": "2025-05-21T11:15:10.123456Z",
      "tasks_completed": 36,
      "tasks_failed": 2,
      "tasks_in_progress": 0
    }
  ],
  "count": 2
}
```

#### `GET /agents/{agent_id}`

Returns details for a specific agent by ID.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| agent_id | string | The ID of the agent to retrieve |

**Response Schema**: Same as the Agent schema above

**Response Example**:
```json
{
  "id": "ARCH",
  "name": "Architecture Agent",
  "status": "active",
  "description": "System orchestrator and task router",
  "role": "orchestrator",
  "capabilities": ["planning", "routing", "monitoring"],
  "last_active": "2025-05-21T11:20:15.123456Z",
  "tasks_completed": 42,
  "tasks_failed": 3,
  "tasks_in_progress": 2
}
```

**Error Responses**:
| Status Code | Description |
|-------------|-------------|
| 404 | Agent not found |

### Tasks

#### `GET /tasks`

Returns a list of tasks with optional filtering and pagination.

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | Filter tasks by status (pending, in_progress, completed, failed, cancelled) |
| agent_id | string | Filter tasks by agent ID |
| limit | integer | Maximum number of tasks to return (default: 10) |
| offset | integer | Number of tasks to skip (default: 0) |

**Response Schema**:
```typescript
interface TaskList {
  tasks: Task[];
  count: number;
}

interface Task {
  id: string;
  description: string;
  status: "pending" | "in_progress" | "completed" | "failed" | "cancelled";
  agent_id: string;
  priority: "high" | "medium" | "low";
  created_at: string;
  updated_at?: string;
  start_time?: string;
  end_time?: string;
  retries: number;
  fallback_agent?: string;
  details: string[];
  content?: Record<string, any>;
}
```

**Response Example**:
```json
{
  "tasks": [
    {
      "id": "5a824519-e15c-4b84-a0dd-ac4742d0d006",
      "description": "Implement FastAPI endpoints",
      "status": "completed",
      "agent_id": "CC",
      "priority": "high",
      "created_at": "2025-05-18T01:19:26.000000Z",
      "updated_at": "2025-05-18T02:45:30.000000Z",
      "start_time": "2025-05-18T01:20:15.000000Z",
      "end_time": "2025-05-18T02:45:30.000000Z",
      "retries": 0,
      "details": [
        "Created FastAPI application",
        "Implemented agent and task endpoints",
        "Added filtering and pagination"
      ],
      "content": {
        "task_type": "implementation",
        "files_modified": [
          "/apps/api/main.py",
          "/apps/api/models/agent.py",
          "/apps/api/models/task.py"
        ]
      }
    }
  ],
  "count": 1
}
```

#### `GET /tasks/{task_id}`

Returns details for a specific task by ID.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| task_id | string | The ID of the task to retrieve |

**Response Schema**: Same as the Task schema above

**Response Example**:
```json
{
  "id": "5a824519-e15c-4b84-a0dd-ac4742d0d006",
  "description": "Implement FastAPI endpoints",
  "status": "completed",
  "agent_id": "CC",
  "priority": "high",
  "created_at": "2025-05-18T01:19:26.000000Z",
  "updated_at": "2025-05-18T02:45:30.000000Z",
  "start_time": "2025-05-18T01:20:15.000000Z",
  "end_time": "2025-05-18T02:45:30.000000Z",
  "retries": 0,
  "details": [
    "Created FastAPI application",
    "Implemented agent and task endpoints",
    "Added filtering and pagination"
  ],
  "content": {
    "task_type": "implementation",
    "files_modified": [
      "/apps/api/main.py",
      "/apps/api/models/agent.py",
      "/apps/api/models/task.py"
    ]
  }
}
```

**Error Responses**:
| Status Code | Description |
|-------------|-------------|
| 404 | Task not found |

## Error Handling

The API uses standard HTTP status codes to indicate the success or failure of requests:

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters or data |
| 404 | Not Found - The requested resource does not exist |
| 500 | Internal Server Error - Something went wrong on the server |

Error responses include a detail field with more information:

```json
{
  "detail": "Agent UNKNOWN not found"
}
```

## Data Models

### Agent Model

The system uses the following Pydantic model for agents:

```python
class AgentStatus(Enum):
    ACTIVE = "active"
    IDLE = "idle" 
    INACTIVE = "inactive"
    ERROR = "error"

class AgentCapability(Enum):
    PLANNING = "planning"
    ROUTING = "routing"
    MONITORING = "monitoring"
    CODING = "coding"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    ANALYSIS = "analysis"

class Agent(BaseModel):
    id: str
    name: str
    status: AgentStatus = AgentStatus.INACTIVE
    description: str
    role: str
    capabilities: List[AgentCapability] = []
    last_active: Optional[str] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_in_progress: int = 0
```

### Task Model

The system uses the following Pydantic model for tasks:

```python
class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class Task(BaseModel):
    id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    agent_id: str
    priority: TaskPriority = TaskPriority.MEDIUM
    created_at: datetime
    updated_at: Optional[datetime] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    retries: int = 0
    fallback_agent: Optional[str] = None
    details: List[str] = []
    content: Optional[Dict[str, Any]] = None
```

## Client Integration Notes

The web client includes TypeScript interfaces in `agentApi.ts` and `taskApi.ts` that may have slight differences from the API models:

- Web client interfaces use camelCase for some properties (e.g., `tasks_in_progress` vs `tasksInProgress`)
- Task status names differ slightly between the API and web client models
- The web client adds some additional types for response handling

Developers should be aware of these differences when integrating the API with frontend applications.

## Versioning

The API follows semantic versioning (MAJOR.MINOR.PATCH):

- MAJOR: Breaking changes to the API
- MINOR: Backwards-compatible feature additions
- PATCH: Backwards-compatible bug fixes

The current version is 0.1.0, indicating that the API is still in early development and may change significantly before reaching a stable 1.0.0 release.

## Future Improvements

Planned improvements for future API versions:

1. Authentication and authorization
2. Rate limiting
3. More comprehensive filtering and search options
4. Webhook support for notifications
5. WebSocket support for real-time updates
6. POST/PUT/DELETE endpoints for creating and managing agents and tasks
7. Integration with external systems