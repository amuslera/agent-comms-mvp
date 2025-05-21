from datetime import datetime
import json
import uuid
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union

from ..models.plan import ExecutionPlan, PlanResponse

class PlanService:
    """Service for handling execution plans."""
    
    def __init__(self):
        """Initialize the plan service."""
        self.plans_dir = Path("plans")
        self.plans_dir.mkdir(exist_ok=True)
        
        # In-memory storage for plans and their execution status
        self._plans: Dict[str, Dict[str, Any]] = {}
    
    async def validate_plan(self, plan_data: Union[Dict[str, Any], str]) -> Tuple[bool, Optional[ExecutionPlan], List[Dict[str, Any]]]:
        """Validate a plan against the schema.
        
        Args:
            plan_data: Plan data either as a dict or as a YAML/JSON string
            
        Returns:
            Tuple containing:
            - bool: Whether validation passed
            - Optional[ExecutionPlan]: Validated plan if successful
            - List[Dict[str, Any]]: List of validation errors if any
        """
        errors = []
        
        # Parse plan data if it's a string
        if isinstance(plan_data, str):
            try:
                if plan_data.strip().startswith('{'):
                    # Assume JSON
                    plan_dict = json.loads(plan_data)
                else:
                    # Assume YAML
                    plan_dict = yaml.safe_load(plan_data)
            except Exception as e:
                errors.append({"loc": ["plan"], "msg": f"Failed to parse plan data: {str(e)}"})
                return False, None, errors
        else:
            plan_dict = plan_data
        
        # Validate against Pydantic model
        try:
            validated_plan = ExecutionPlan(**plan_dict)
            return True, validated_plan, []
        except Exception as e:
            errors.append({"loc": ["plan"], "msg": f"Plan validation failed: {str(e)}"})
            return False, None, errors
    
    async def save_plan(self, plan: ExecutionPlan) -> str:
        """Save a validated plan to disk.
        
        Args:
            plan: Validated execution plan
            
        Returns:
            str: Path to the saved plan file
        """
        # Ensure plan ID is unique
        plan_id = plan.metadata.plan_id
        file_name = f"{plan_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.yaml"
        file_path = self.plans_dir / file_name
        
        # Convert to dict and save as YAML
        with open(file_path, 'w') as f:
            yaml.dump(plan.dict(), f, default_flow_style=False)
        
        return str(file_path)
    
    async def submit_plan(self, plan_data: Union[Dict[str, Any], str], execute: bool = False) -> PlanResponse:
        """Submit a new execution plan.
        
        Args:
            plan_data: Plan data either as a dict or as a YAML/JSON string
            execute: Whether to execute the plan immediately
            
        Returns:
            PlanResponse: Response with plan submission status
        """
        # Validate plan
        is_valid, validated_plan, errors = await self.validate_plan(plan_data)
        
        if not is_valid:
            return PlanResponse(
                plan_id="invalid_plan",
                status="rejected",
                message="Plan validation failed",
                errors=errors
            )
        
        # Save plan to disk
        plan_path = await self.save_plan(validated_plan)
        
        # Store plan in memory
        plan_id = validated_plan.metadata.plan_id
        self._plans[plan_id] = {
            "plan": validated_plan,
            "status": "validated",
            "created_at": datetime.utcnow(),
            "file_path": plan_path
        }
        
        # Handle execution if requested
        execution_id = None
        status = "validated"
        message = "Plan validated successfully"
        
        if execute:
            execution_id = str(uuid.uuid4())
            status = "queued"
            message = "Plan queued for execution"
            
            # In a real implementation, we would start the execution
            # process here, either synchronously or asynchronously
            if self._should_mock_execution():
                # This is a placeholder for real execution logic
                self._plans[plan_id]["status"] = "processing"
                self._plans[plan_id]["execution_id"] = execution_id
                
                # In a real implementation, this would start a background task
                # that runs the plan using arch_orchestrator.py
        
        return PlanResponse(
            plan_id=plan_id,
            status=status,
            message=message,
            execution_id=execution_id
        )
    
    async def get_plan_status(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a plan.
        
        Args:
            plan_id: The ID of the plan to check
            
        Returns:
            Optional[Dict[str, Any]]: Plan status information or None if not found
        """
        return self._plans.get(plan_id)
    
    async def list_plans(self) -> List[Dict[str, Any]]:
        """List all plans.
        
        Returns:
            List[Dict[str, Any]]: List of plans with their metadata
        """
        return [
            {
                "plan_id": plan_id,
                "status": plan_info["status"],
                "created_at": plan_info["created_at"].isoformat(),
                "description": plan_info["plan"].metadata.description,
                "task_count": len(plan_info["plan"].tasks)
            }
            for plan_id, plan_info in self._plans.items()
        ]
    
    def _should_mock_execution(self) -> bool:
        """Determine if we should mock execution for development.
        
        Returns:
            bool: True if execution should be mocked
        """
        # In a real implementation, this would be determined by
        # configuration or environment variables. For now, we always mock.
        return True