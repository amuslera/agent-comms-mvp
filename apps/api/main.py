"""
Main FastAPI application for the Bluelabel Agent OS API.
Exposes system state to frontend through HTTP endpoints.
"""
import os
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .models.agent import Agent, AgentList
from .models.task import Task, TaskList, TaskStatus
from .sample_data import AGENTS, AGENTS_BY_ID, TASKS, TASKS_BY_ID
from .routers import plans, metrics, history, actions

# Create FastAPI application
app = FastAPI(
    title="Bluelabel Agent OS API",
    description="API for monitoring and managing Bluelabel Agent OS",
    version="0.1.0",
)

# Add CORS middleware to allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(history.router)
app.include_router(plans.router)
app.include_router(metrics.router)
app.include_router(actions.router)

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Simple heartbeat endpoint to check API health.
    
    Returns:
        dict: Status information including timestamp
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": app.version
    }


@app.get("/agents", response_model=AgentList, tags=["Agents"])
async def get_agents(
    status: Optional[str] = Query(None, description="Filter agents by status")
):
    """
    Get a list of all agents in the system.
    
    Args:
        status: Optional status filter (active, idle, inactive, error)
        
    Returns:
        AgentList: List of agents and count
    """
    filtered_agents = AGENTS
    
    # Apply status filter if provided
    if status:
        filtered_agents = [
            agent for agent in AGENTS 
            if agent.status.value.lower() == status.lower()
        ]
    
    return AgentList(agents=filtered_agents, count=len(filtered_agents))


@app.get("/agents/{agent_id}", response_model=Agent, tags=["Agents"])
async def get_agent(
    agent_id: str = Path(..., description="The ID of the agent to retrieve")
):
    """
    Get details for a specific agent by ID.
    
    Args:
        agent_id: The ID of the agent to retrieve
        
    Returns:
        Agent: Agent details
        
    Raises:
        HTTPException: If agent not found
    """
    agent_id = agent_id.upper()
    if agent_id not in AGENTS_BY_ID:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    return AGENTS_BY_ID[agent_id]


@app.get("/tasks", response_model=TaskList, tags=["Tasks"])
async def get_tasks(
    status: Optional[str] = Query(None, description="Filter tasks by status"),
    agent_id: Optional[str] = Query(None, description="Filter tasks by agent ID"),
    limit: int = Query(10, description="Maximum number of tasks to return"),
    offset: int = Query(0, description="Number of tasks to skip")
):
    """
    Get a list of recent task runs.
    
    Args:
        status: Optional status filter (pending, in_progress, completed, failed, cancelled)
        agent_id: Optional agent ID filter
        limit: Maximum number of tasks to return
        offset: Number of tasks to skip
        
    Returns:
        TaskList: List of tasks and count
    """
    filtered_tasks = TASKS
    
    # Apply status filter if provided
    if status:
        filtered_tasks = [
            task for task in filtered_tasks 
            if task.status.value.lower() == status.lower()
        ]
    
    # Apply agent filter if provided
    if agent_id:
        agent_id = agent_id.upper()
        filtered_tasks = [
            task for task in filtered_tasks 
            if task.agent_id.upper() == agent_id
        ]
    
    # Sort by updated_at or created_at (newest first)
    filtered_tasks.sort(
        key=lambda x: (x.updated_at or x.created_at),
        reverse=True
    )
    
    # Apply pagination
    paginated_tasks = filtered_tasks[offset:offset + limit]
    
    return TaskList(tasks=paginated_tasks, count=len(filtered_tasks))


@app.get("/tasks/{task_id}", response_model=Task, tags=["Tasks"])
async def get_task(
    task_id: str = Path(..., description="The ID of the task to retrieve")
):
    """
    Get details for a specific task by ID.
    
    Args:
        task_id: The ID of the task to retrieve
        
    Returns:
        Task: Task details
        
    Raises:
        HTTPException: If task not found
    """
    if task_id not in TASKS_BY_ID:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    return TASKS_BY_ID[task_id]


class RecentTask(BaseModel):
    trace_id: str
    agent: str
    score: Optional[float]
    retry_count: int
    success: bool
    submitted_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_sec: Optional[float] = None
    input_payload: Optional[dict] = None
    output_payload: Optional[dict] = None


class RecentTasksResponse(BaseModel):
    tasks: List[RecentTask]
    count: int


@app.get("/tasks/recent", response_model=RecentTasksResponse, tags=["Tasks"])
async def get_recent_tasks(
    limit: int = Query(10, description="Maximum number of tasks to return"),
    offset: int = Query(0, description="Number of tasks to skip")
):
    """
    Get recent task runs with execution details.
    
    Args:
        limit: Maximum number of tasks to return
        offset: Number of tasks to skip
        
    Returns:
        RecentTasksResponse: List of recent tasks with execution details
    """
    # Sample recent tasks data with more realistic information
    sample_tasks = [
        RecentTask(
            trace_id="summary-ARCH-1737071400",
            agent="ARCH",
            score=0.95,
            success=True,
            retry_count=0,
            duration_sec=2.3,
            submitted_at="2025-01-16T23:50:00Z",
            started_at="2025-01-16T23:50:01Z",
            completed_at="2025-01-16T23:50:03Z",
            input_payload={"task": "orchestrate_plan", "plan_id": "plan_001"},
            output_payload={"status": "completed", "tasks_assigned": 3}
        ),
        RecentTask(
            trace_id="summary-CA-1737071100",
            agent="CA",
            score=0.89,
            success=True,
            retry_count=1,
            duration_sec=4.7,
            submitted_at="2025-01-16T23:45:00Z",
            started_at="2025-01-16T23:45:02Z",
            completed_at="2025-01-16T23:45:07Z",
            input_payload={"task": "analyze_context", "data": "user_request"},
            output_payload={"analysis": "task_classification", "confidence": 0.89}
        ),
        RecentTask(
            trace_id="summary-CC-1737070800",
            agent="CC", 
            score=0.92,
            success=True,
            retry_count=0,
            duration_sec=1.8,
            submitted_at="2025-01-16T23:40:00Z",
            started_at="2025-01-16T23:40:01Z",
            completed_at="2025-01-16T23:40:03Z",
            input_payload={"task": "generate_code", "requirements": "api_endpoint"},
            output_payload={"code_generated": True, "files_created": 2}
        ),
        RecentTask(
            trace_id="summary-WA-1737070500",
            agent="WA",
            score=0.87,
            success=True,
            retry_count=0,
            duration_sec=3.1,
            submitted_at="2025-01-16T23:35:00Z",
            started_at="2025-01-16T23:35:01Z",
            completed_at="2025-01-16T23:35:04Z",
            input_payload={"task": "web_interaction", "url": "https://example.com"},
            output_payload={"data_extracted": True, "pages_processed": 1}
        ),
        RecentTask(
            trace_id="failed-task-1737070200",
            agent="CC",
            score=0.25,
            success=False,
            retry_count=3,
            duration_sec=12.5,
            submitted_at="2025-01-16T23:30:00Z",
            started_at="2025-01-16T23:30:02Z",
            completed_at="2025-01-16T23:30:15Z",
            input_payload={"task": "complex_analysis", "timeout": 10},
            output_payload={"error": "timeout_exceeded", "partial_results": True}
        )
    ]
    
    # Apply pagination
    total_count = len(sample_tasks)
    paginated_tasks = sample_tasks[offset:offset + limit]
    
    return RecentTasksResponse(tasks=paginated_tasks, count=total_count)


if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable or use default 8000
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run("apps.api.main:app", host="0.0.0.0", port=port, reload=True)