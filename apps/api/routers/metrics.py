"""
API routes for metrics endpoints.
"""
from typing import List
from fastapi import APIRouter, HTTPException, Path

from models.metrics import AgentMetrics, AgentMetricsList, PlanMetrics
from services.metrics_service import MetricsService

router = APIRouter(prefix="/metrics", tags=["Metrics"])

# Initialize metrics service
metrics_service = MetricsService()


@router.get("/agents", response_model=AgentMetricsList)
async def get_agent_metrics() -> AgentMetricsList:
    """
    Get performance metrics for all agents.
    
    Returns success rates, average scores, and performance logs for agents.
    Reads from CA's /logs/agent_scores.json or returns dummy data if not found.
    
    Returns:
        AgentMetricsList: List of agent metrics including success rates and scores
    """
    try:
        agent_metrics = metrics_service.get_agent_metrics()
        return AgentMetricsList(agents=agent_metrics, count=len(agent_metrics))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve agent metrics: {str(e)}")


@router.get("/plans/{plan_id}", response_model=PlanMetrics)
async def get_plan_metrics(
    plan_id: str = Path(..., description="The ID of the plan to get metrics for")
) -> PlanMetrics:
    """
    Get performance metrics for a specific plan execution.
    
    Returns agent metrics for the plan, average duration, and execution details.
    Uses basic aggregation logic without database dependency.
    
    Args:
        plan_id: The ID of the plan to retrieve metrics for
        
    Returns:
        PlanMetrics: Plan execution metrics including agent performance and duration
        
    Raises:
        HTTPException: If plan metrics cannot be retrieved
    """
    try:
        plan_metrics = metrics_service.get_plan_metrics(plan_id)
        if not plan_metrics:
            raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")
        
        return plan_metrics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve plan metrics: {str(e)}")