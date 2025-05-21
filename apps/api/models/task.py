"""
Task data models for the Bluelabel Agent OS API.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Status of a task in the system."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskPriority(str, Enum):
    """Priority levels for tasks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Task(BaseModel):
    """Represents a task in the Bluelabel Agent OS."""
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
    
    class Config:
        schema_extra = {
            "example": {
                "id": "TASK-001",
                "description": "Process data files",
                "status": "in_progress",
                "agent_id": "CA",
                "priority": "medium",
                "created_at": "2025-05-21T09:30:00Z",
                "updated_at": "2025-05-21T09:35:00Z",
                "start_time": "2025-05-21T09:35:00Z",
                "end_time": None,
                "retries": 0,
                "fallback_agent": None,
                "details": ["Started at: 2025-05-21 09:35:00", "Processing file1.txt"],
                "content": {
                    "task_id": "TASK-001",
                    "action": "process",
                    "parameters": {"file": "file1.txt"}
                }
            }
        }


class TaskList(BaseModel):
    """A list of tasks."""
    tasks: List[Task]
    count: int = Field(..., description="Total number of tasks")