"""
Agent data models for the Bluelabel Agent OS API.
"""
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Status of an agent in the system."""
    ACTIVE = "active"
    IDLE = "idle"
    INACTIVE = "inactive"
    ERROR = "error"


class AgentCapability(str, Enum):
    """Capabilities that an agent can have."""
    TASK_EXECUTION = "task_execution"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    DOCUMENTATION = "documentation"
    ORCHESTRATION = "orchestration"
    ROUTING = "routing"
    LEARNING = "learning"
    WEB_INTERFACE = "web_interface"


class Agent(BaseModel):
    """Represents an agent in the Bluelabel Agent OS."""
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
    
    class Config:
        schema_extra = {
            "example": {
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
        }


class AgentList(BaseModel):
    """A list of agents."""
    agents: List[Agent]
    count: int = Field(..., description="Total number of agents")