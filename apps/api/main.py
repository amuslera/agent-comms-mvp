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
from .routers import plans

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
app.include_router(plans.router)

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


if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable or use default 8000
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run("apps.api.main:app", host="0.0.0.0", port=port, reload=True)