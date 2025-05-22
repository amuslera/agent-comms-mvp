"""
API routes for task and plan history endpoints.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from ..models.history import PlanHistoryList, TaskRecentList
from ..services.history_service import HistoryService

router = APIRouter(tags=["History"])

# Initialize history service
history_service = HistoryService()


@router.get("/plans/history", response_model=PlanHistoryList)
async def get_plan_history(
    limit: int = Query(50, description="Maximum number of plans to return", ge=1, le=200)
) -> PlanHistoryList:
    """
    Get plan execution history.
    
    Returns recent plans with their execution status, agent count, and timing information.
    Data is sourced from plan files and execution logs, with dummy data fallback.
    
    Args:
        limit: Maximum number of plans to return (1-200)
        
    Returns:
        PlanHistoryList: List of plan history items with execution details
    """
    try:
        plan_history = history_service.get_plan_history(limit)
        return PlanHistoryList(plans=plan_history, count=len(plan_history))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve plan history: {str(e)}")


@router.get("/tasks/recent", response_model=TaskRecentList)
async def get_recent_tasks(
    limit: int = Query(100, description="Maximum number of tasks to return", ge=1, le=500),
    hours: int = Query(24, description="Number of hours to look back", ge=1, le=168)
) -> TaskRecentList:
    """
    Get recent task executions.
    
    Returns recent tasks with their scores, success status, retry counts, and timing information.
    Data is sourced from agent logs and postbox messages, with dummy data fallback.
    
    Args:
        limit: Maximum number of tasks to return (1-500)
        hours: Number of hours to look back (1-168)
        
    Returns:
        TaskRecentList: List of recent task items with execution details
    """
    try:
        recent_tasks = history_service.get_recent_tasks(limit, hours)
        return TaskRecentList(tasks=recent_tasks, count=len(recent_tasks))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve recent tasks: {str(e)}")