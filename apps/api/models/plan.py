from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator, root_validator

class TaskMetadata(BaseModel):
    """Optional metadata for a task in the plan."""
    priority: Optional[str] = Field(None, description="Task priority level")
    deadline: Optional[str] = Field(None, description="ISO 8601 deadline timestamp")
    timeout: Optional[str] = Field(None, description="Task timeout (e.g., '30m', '1h')")
    retries: Optional[int] = Field(None, description="Number of retry attempts allowed")

class PlanTask(BaseModel):
    """Represents a single task within an execution plan."""
    task_id: str = Field(..., description="Unique task identifier")
    agent: str = Field(..., description="Target agent to execute the task")
    type: str = Field("task_assignment", description="Message type from protocol")
    description: str = Field(..., description="Human-readable task description")
    priority: Optional[str] = Field("medium", description="Task priority (low, medium, high, critical)")
    deadline: Optional[str] = Field(None, description="ISO 8601 timestamp for task deadline")
    content: Dict[str, Any] = Field(..., description="Task-specific content and parameters")
    dependencies: List[str] = Field(default_factory=list, description="List of task_ids that must complete before this task")
    max_retries: Optional[int] = Field(1, description="Maximum retry attempts for this task")
    fallback_agent: Optional[str] = Field(None, description="Agent to use if primary agent fails")
    timeout: Optional[str] = Field(None, description="Timeout for this specific task")
    notifications: Optional[Dict[str, List[str]]] = Field(None, description="Notification settings for task completion")

    @validator('priority')
    def validate_priority(cls, v):
        valid_priorities = ['low', 'medium', 'high', 'critical']
        if v and v.lower() not in valid_priorities:
            raise ValueError(f"Priority must be one of: {', '.join(valid_priorities)}")
        return v.lower() if v else 'medium'

    @validator('agent')
    def validate_agent(cls, v):
        valid_agents = ['CA', 'CC', 'WA', 'ARCH']
        if v not in valid_agents:
            raise ValueError(f"Agent must be one of: {', '.join(valid_agents)}")
        return v
    
    @validator('dependencies')
    def validate_dependencies(cls, v):
        if not isinstance(v, list):
            raise ValueError("Dependencies must be a list of task IDs")
        return v

class PlanMetadata(BaseModel):
    """Metadata for an execution plan."""
    plan_id: str = Field(..., description="Unique identifier for this plan")
    version: str = Field("1.0.0", description="Plan format version")
    created: Optional[str] = Field(None, description="ISO 8601 timestamp of plan creation")
    description: str = Field(..., description="Description of what this plan does")
    priority: Optional[str] = Field("medium", description="Overall plan priority")
    timeout: Optional[str] = Field(None, description="Maximum time for plan execution")

    @validator('created', pre=True, always=True)
    def set_created(cls, v):
        return v or datetime.utcnow().isoformat()

    @validator('priority')
    def validate_priority(cls, v):
        valid_priorities = ['low', 'medium', 'high', 'critical']
        if v and v.lower() not in valid_priorities:
            raise ValueError(f"Priority must be one of: {', '.join(valid_priorities)}")
        return v.lower() if v else 'medium'

class ExecutionPlan(BaseModel):
    """Complete execution plan with metadata and tasks."""
    metadata: PlanMetadata = Field(..., description="Plan metadata")
    tasks: List[PlanTask] = Field(..., description="List of tasks to execute")

    @root_validator
    def validate_task_dependencies(cls, values):
        """Validate that all task dependencies refer to valid task IDs."""
        if 'tasks' not in values:
            return values
            
        tasks = values['tasks']
        task_ids = {task.task_id for task in tasks}
        
        for task in tasks:
            for dep_id in task.dependencies:
                if dep_id not in task_ids:
                    raise ValueError(f"Task {task.task_id} depends on undefined task {dep_id}")
        
        return values

class PlanResponse(BaseModel):
    """Response after plan submission."""
    plan_id: str = Field(..., description="Unique identifier for the submitted plan")
    status: str = Field(..., description="Status of the plan submission (validated, processing, rejected)")
    message: Optional[str] = Field(None, description="Additional information about the plan submission")
    errors: Optional[List[Dict[str, Any]]] = Field(None, description="Validation errors if any")
    execution_id: Optional[str] = Field(None, description="ID for tracking plan execution (if started)")

    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['validated', 'processing', 'rejected', 'queued']
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v

class PlanRequest(BaseModel):
    """Request body for plan submission."""
    plan: Union[Dict[str, Any], str] = Field(..., description="Plan data (either as parsed dict or YAML/JSON string)")
    execute: bool = Field(False, description="Whether to execute the plan immediately after validation")
    async_execution: bool = Field(True, description="Whether to execute the plan asynchronously")