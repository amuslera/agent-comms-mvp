"""
Task and Plan Action Router for Bluelabel Agent OS API.
Provides endpoints for task control operations like resubmit, escalate, and cancel.
"""
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, Field

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["Actions"]
)

# Response models
class ActionResult(BaseModel):
    """Standard response model for action endpoints."""
    success: bool = Field(..., description="Whether the action completed successfully")
    message: str = Field(..., description="Human-readable result message")
    plan_id: str = Field(..., description="The plan ID that was acted upon")
    action: str = Field(..., description="The action that was performed")
    timestamp: str = Field(..., description="ISO timestamp when action was performed")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional action metadata")

class ResubmitMetadata(BaseModel):
    """Metadata specific to resubmit actions."""
    original_submission_time: Optional[str] = None
    resubmission_count: int = 1
    reason: str = "Manual resubmission requested"

class EscalationMetadata(BaseModel):
    """Metadata specific to escalation actions."""
    escalation_level: str = "HUMAN"
    escalated_to: str = "human-inbox"
    priority: str = "normal"
    reason: str = "Manual escalation requested"

class CancellationMetadata(BaseModel):
    """Metadata specific to cancellation actions."""
    cancelled_by: str = "api-request"
    reason: str = "Manual cancellation requested"
    final_status: str = "cancelled"

# Helper functions
def log_action_event(plan_id: str, action: str, metadata: Dict[str, Any]) -> None:
    """Log action events to a structured log file."""
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "plan_id": plan_id,
        "action": action,
        "metadata": metadata
    }
    
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Append to action log file
    log_file = "logs/plan_actions.log"
    try:
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        logger.info(f"Logged {action} action for plan {plan_id}")
    except Exception as e:
        logger.error(f"Failed to log action: {e}")

def simulate_plan_resubmission(plan_id: str) -> Dict[str, Any]:
    """Simulate resubmitting a plan to the system."""
    # In a real implementation, this would:
    # 1. Load the original plan from storage
    # 2. Reset task statuses to pending
    # 3. Repost the plan to the orchestrator queue
    # 4. Update plan metadata
    
    # For now, simulate the behavior
    plans_dir = "plans"
    plan_file = f"{plans_dir}/{plan_id}.yaml"
    
    metadata = {
        "simulated": True,
        "plan_file": plan_file,
        "action_taken": "Plan marked for resubmission",
        "next_steps": "Plan would be reposted to orchestrator queue"
    }
    
    # Check if plan file exists (optional validation)
    if os.path.exists(plan_file):
        metadata["plan_file_found"] = True
    else:
        metadata["plan_file_found"] = False
        metadata["note"] = "Plan file not found, but action simulated"
    
    return metadata

def simulate_plan_escalation(plan_id: str) -> Dict[str, Any]:
    """Simulate escalating a plan to human review."""
    # In a real implementation, this would:
    # 1. Create an escalation record
    # 2. Write to HUMAN inbox/notification system
    # 3. Set plan status to "escalated"
    # 4. Trigger notification (email, Slack, etc.)
    
    # For now, simulate writing to a human inbox
    human_inbox_dir = "postbox/HUMAN"
    os.makedirs(human_inbox_dir, exist_ok=True)
    
    escalation_message = {
        "type": "plan_escalation",
        "plan_id": plan_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "priority": "normal",
        "message": f"Plan {plan_id} has been escalated for human review",
        "requested_by": "api-action-endpoint"
    }
    
    # Write to human inbox
    inbox_file = f"{human_inbox_dir}/inbox.json"
    try:
        if os.path.exists(inbox_file):
            with open(inbox_file, "r") as f:
                inbox_data = json.load(f)
        else:
            inbox_data = []
        
        inbox_data.append(escalation_message)
        
        with open(inbox_file, "w") as f:
            json.dump(inbox_data, f, indent=2)
        
        return {
            "simulated": True,
            "escalation_written_to": inbox_file,
            "action_taken": "Escalation message written to HUMAN inbox",
            "message_id": f"escalation_{plan_id}_{int(datetime.now().timestamp())}"
        }
    except Exception as e:
        logger.error(f"Failed to write escalation: {e}")
        return {
            "simulated": True,
            "error": str(e),
            "action_taken": "Escalation simulation attempted but failed to write inbox"
        }

def simulate_plan_cancellation(plan_id: str) -> Dict[str, Any]:
    """Simulate cancelling a plan and marking it inactive."""
    # In a real implementation, this would:
    # 1. Stop any running tasks for this plan
    # 2. Update plan status to "cancelled"
    # 3. Clean up resources
    # 4. Notify affected agents
    
    # Simulate marking plan as inactive
    metadata = {
        "simulated": True,
        "action_taken": "Plan marked as cancelled/inactive",
        "status_change": "active -> cancelled",
        "cleanup_actions": [
            "Stop running tasks",
            "Update plan status",
            "Notify agents",
            "Release resources"
        ]
    }
    
    return metadata

# Action endpoints
@router.post("/plans/{plan_id}/resubmit", response_model=ActionResult)
async def resubmit_plan(
    plan_id: str = Path(..., description="The ID of the plan to resubmit")
):
    """
    Resubmit a plan for execution.
    
    This endpoint simulates reposting a plan to the orchestrator queue,
    resetting task statuses and triggering a fresh execution cycle.
    
    Args:
        plan_id: The ID of the plan to resubmit
        
    Returns:
        ActionResult: Result of the resubmission action
    """
    try:
        # Simulate resubmission
        sim_metadata = simulate_plan_resubmission(plan_id)
        
        # Create response metadata
        resubmit_meta = ResubmitMetadata(
            original_submission_time=datetime.now(timezone.utc).isoformat(),
            resubmission_count=1,
            reason="Manual resubmission via API"
        )
        
        # Combine metadata
        full_metadata = {
            **sim_metadata,
            **resubmit_meta.dict()
        }
        
        # Log the action
        log_action_event(plan_id, "resubmit", full_metadata)
        
        return ActionResult(
            success=True,
            message=f"Plan {plan_id} has been resubmitted for execution",
            plan_id=plan_id,
            action="resubmit",
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=full_metadata
        )
        
    except Exception as e:
        logger.error(f"Failed to resubmit plan {plan_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resubmit plan: {str(e)}"
        )

@router.post("/plans/{plan_id}/escalate", response_model=ActionResult)
async def escalate_plan(
    plan_id: str = Path(..., description="The ID of the plan to escalate")
):
    """
    Escalate a plan to human review.
    
    This endpoint simulates writing an escalation request to the HUMAN inbox,
    triggering manual review of the plan execution.
    
    Args:
        plan_id: The ID of the plan to escalate
        
    Returns:
        ActionResult: Result of the escalation action
    """
    try:
        # Simulate escalation
        sim_metadata = simulate_plan_escalation(plan_id)
        
        # Create response metadata
        escalation_meta = EscalationMetadata(
            escalation_level="HUMAN",
            escalated_to="human-inbox",
            priority="normal",
            reason="Manual escalation via API"
        )
        
        # Combine metadata
        full_metadata = {
            **sim_metadata,
            **escalation_meta.dict()
        }
        
        # Log the action
        log_action_event(plan_id, "escalate", full_metadata)
        
        return ActionResult(
            success=True,
            message=f"Plan {plan_id} has been escalated to human review",
            plan_id=plan_id,
            action="escalate",
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=full_metadata
        )
        
    except Exception as e:
        logger.error(f"Failed to escalate plan {plan_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to escalate plan: {str(e)}"
        )

@router.post("/plans/{plan_id}/cancel", response_model=ActionResult)
async def cancel_plan(
    plan_id: str = Path(..., description="The ID of the plan to cancel")
):
    """
    Cancel a plan and mark it as inactive.
    
    This endpoint simulates stopping plan execution, cancelling running tasks,
    and marking the plan status as cancelled/inactive.
    
    Args:
        plan_id: The ID of the plan to cancel
        
    Returns:
        ActionResult: Result of the cancellation action
    """
    try:
        # Simulate cancellation
        sim_metadata = simulate_plan_cancellation(plan_id)
        
        # Create response metadata
        cancel_meta = CancellationMetadata(
            cancelled_by="api-request",
            reason="Manual cancellation via API",
            final_status="cancelled"
        )
        
        # Combine metadata
        full_metadata = {
            **sim_metadata,
            **cancel_meta.dict()
        }
        
        # Log the action
        log_action_event(plan_id, "cancel", full_metadata)
        
        return ActionResult(
            success=True,
            message=f"Plan {plan_id} has been cancelled and marked inactive",
            plan_id=plan_id,
            action="cancel",
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=full_metadata
        )
        
    except Exception as e:
        logger.error(f"Failed to cancel plan {plan_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel plan: {str(e)}"
        )