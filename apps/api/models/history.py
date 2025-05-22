"""
Pydantic models for task and plan history endpoints.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class PlanHistoryItem(BaseModel):
    """History item for a single plan execution."""
    plan_id: str = Field(..., description="Plan identifier")
    submitted_at: datetime = Field(..., description="Plan submission timestamp")
    agent_count: int = Field(..., description="Number of agents involved in the plan")
    status: str = Field(..., description="Plan execution status (complete, running, failed, etc.)")
    duration_sec: Optional[float] = Field(None, description="Plan execution duration in seconds")
    success_rate: Optional[float] = Field(None, description="Overall success rate of plan tasks")


class PlanHistoryList(BaseModel):
    """List of plan history items."""
    plans: List[PlanHistoryItem] = Field(..., description="List of plan history items")
    count: int = Field(..., description="Number of plans")


class TaskRecentItem(BaseModel):
    """Recent task execution item."""
    trace_id: str = Field(..., description="Task trace identifier")
    agent: str = Field(..., description="Agent that executed the task")
    score: Optional[float] = Field(None, description="Task execution score (0.0-1.0)")
    success: Optional[bool] = Field(None, description="Task success status")
    retry_count: int = Field(0, description="Number of retry attempts")
    duration_sec: Optional[float] = Field(None, description="Task duration in seconds")
    task_id: Optional[str] = Field(None, description="Task identifier")
    timestamp: datetime = Field(..., description="Task completion timestamp")
    error_code: Optional[str] = Field(None, description="Error code if task failed")


class TaskRecentList(BaseModel):
    """List of recent task items."""
    tasks: List[TaskRecentItem] = Field(..., description="List of recent task items")
    count: int = Field(..., description="Number of tasks")