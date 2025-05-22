"""
Pydantic models for metrics endpoints.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AgentMetrics(BaseModel):
    """Metrics for a single agent."""
    agent_id: str = Field(..., description="Agent identifier")
    average_score: float = Field(..., description="Average performance score (0.0-1.0)")
    success_rate: float = Field(..., description="Success rate (0.0-1.0)")
    task_count: int = Field(..., description="Total number of tasks completed")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")


class AgentMetricsList(BaseModel):
    """List of agent metrics."""
    agents: List[AgentMetrics] = Field(..., description="List of agent metrics")
    count: int = Field(..., description="Number of agents")


class PlanMetrics(BaseModel):
    """Metrics for a specific plan execution."""
    plan_id: str = Field(..., description="Plan identifier")
    agent_metrics: List[AgentMetrics] = Field(..., description="Metrics for agents involved in plan")
    average_duration_sec: float = Field(..., description="Average execution duration in seconds")
    total_tasks: int = Field(..., description="Total number of tasks in plan")
    completed_tasks: int = Field(..., description="Number of completed tasks")
    success_rate: float = Field(..., description="Overall plan success rate")
    execution_start: Optional[datetime] = Field(None, description="Plan execution start time")
    execution_end: Optional[datetime] = Field(None, description="Plan execution end time")
    status: str = Field(..., description="Plan execution status")