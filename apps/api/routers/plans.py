from fastapi import APIRouter, HTTPException, Depends, Body, Query
from typing import List, Optional, Dict, Any
from ..models.plan import PlanRequest, PlanResponse, ExecutionPlan
from ..services.plan_service import PlanService

router = APIRouter(prefix="/plans", tags=["plans"])

# Dependency to get plan service instance
def get_plan_service() -> PlanService:
    return PlanService()

@router.post("/", response_model=PlanResponse)
async def submit_plan(
    plan_request: PlanRequest = Body(...),
    plan_service: PlanService = Depends(get_plan_service)
) -> PlanResponse:
    """Submit a new execution plan.
    
    The plan can be provided either as a parsed dictionary or as a YAML/JSON string.
    Optionally, the plan can be executed immediately after validation.
    
    Returns:
        PlanResponse: Response with plan submission status
    """
    return await plan_service.submit_plan(
        plan_data=plan_request.plan,
        execute=plan_request.execute
    )

@router.get("/{plan_id}", response_model=Dict[str, Any])
async def get_plan_status(
    plan_id: str,
    plan_service: PlanService = Depends(get_plan_service)
) -> Dict[str, Any]:
    """Get the current status of a specific plan.
    
    Args:
        plan_id: The ID of the plan to check
        
    Returns:
        Dict[str, Any]: Plan status information
    """
    plan_status = await plan_service.get_plan_status(plan_id)
    if not plan_status:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")
    
    # Convert plan to dict for response
    plan_dict = plan_status.copy()
    plan_dict["plan"] = plan_status["plan"].dict()
    plan_dict["created_at"] = plan_dict["created_at"].isoformat()
    
    return plan_dict

@router.get("/", response_model=List[Dict[str, Any]])
async def list_plans(
    status: Optional[str] = Query(None, description="Filter by status"),
    plan_service: PlanService = Depends(get_plan_service)
) -> List[Dict[str, Any]]:
    """List all plans, optionally filtered by status.
    
    Args:
        status: Filter by plan status (validated, processing, queued, etc.)
        
    Returns:
        List[Dict[str, Any]]: List of plans with their metadata
    """
    plans = await plan_service.list_plans()
    
    if status:
        plans = [plan for plan in plans if plan["status"] == status]
        
    return plans

@router.get("/history", response_model=Dict[str, Any])
async def get_plan_history(
    limit: int = Query(10, description="Number of plans to return"),
    offset: int = Query(0, description="Number of plans to skip"),
    plan_service: PlanService = Depends(get_plan_service)
) -> Dict[str, Any]:
    """Get plan history with pagination.
    
    Args:
        limit: Number of plans to return (default: 10)
        offset: Number of plans to skip (default: 0)
        
    Returns:
        Dict[str, Any]: Plans history with count
    """
    # Get all plans and return a sample for now
    plans = await plan_service.list_plans()
    
    # Sample plan history data
    sample_plans = [
        {
            "plan_id": "plan_001",
            "submitted_at": "2025-01-16T20:00:00Z",
            "status": "completed",
            "agent_count": 3
        },
        {
            "plan_id": "plan_002", 
            "submitted_at": "2025-01-16T19:30:00Z",
            "status": "failed",
            "agent_count": 2
        },
        {
            "plan_id": "plan_003",
            "submitted_at": "2025-01-16T19:00:00Z", 
            "status": "in_progress",
            "agent_count": 4
        }
    ]
    
    # Apply pagination
    total_count = len(sample_plans)
    paginated_plans = sample_plans[offset:offset + limit]
    
    return {
        "plans": paginated_plans,
        "count": total_count
    }

@router.post("/{plan_id}/execute", response_model=PlanResponse)
async def execute_plan(
    plan_id: str,
    async_execution: bool = Query(True, description="Whether to execute the plan asynchronously"),
    plan_service: PlanService = Depends(get_plan_service)
) -> PlanResponse:
    """Execute a previously submitted plan.
    
    Args:
        plan_id: The ID of the plan to execute
        async_execution: Whether to execute the plan asynchronously
        
    Returns:
        PlanResponse: Response with execution status
    """
    plan_status = await plan_service.get_plan_status(plan_id)
    if not plan_status:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")
    
    # In a real implementation, this would start the execution
    # process using the arch_orchestrator.py script
    
    # For now, we just return a mock response
    return PlanResponse(
        plan_id=plan_id,
        status="queued",
        message="Plan queued for execution",
        execution_id="mock_execution_id"
    )