"""
Sample data for the Bluelabel Agent OS API.
This will be replaced with actual data in a production environment.
"""
from datetime import datetime, timedelta
from typing import Dict, List

from models.agent import Agent, AgentStatus, AgentCapability
from models.task import Task, TaskStatus, TaskPriority

# Current time for reference
NOW = datetime.utcnow()

# Sample agent data
AGENTS = [
    Agent(
        id="ARCH",
        name="Architect",
        status=AgentStatus.ACTIVE,
        description="Task Router and Coordinator",
        role="Routes tasks, monitors progress, ensures completion",
        capabilities=[
            AgentCapability.ORCHESTRATION,
            AgentCapability.ROUTING,
            AgentCapability.TASK_EXECUTION
        ],
        last_active=(NOW - timedelta(minutes=5)).isoformat() + "Z",
        tasks_completed=42,
        tasks_failed=3,
        tasks_in_progress=2
    ),
    Agent(
        id="CC",
        name="Claude Code",
        status=AgentStatus.ACTIVE,
        description="Backend Infrastructure Agent",
        role="Core system implementation, message handling",
        capabilities=[
            AgentCapability.CODE_GENERATION,
            AgentCapability.TASK_EXECUTION,
            AgentCapability.DOCUMENTATION
        ],
        last_active=(NOW - timedelta(minutes=3)).isoformat() + "Z",
        tasks_completed=38,
        tasks_failed=2,
        tasks_in_progress=1
    ),
    Agent(
        id="CA",
        name="Cursor AI",
        status=AgentStatus.IDLE,
        description="Task Implementation Agent",
        role="Code implementation and validation",
        capabilities=[
            AgentCapability.CODE_GENERATION,
            AgentCapability.CODE_REVIEW,
            AgentCapability.TASK_EXECUTION
        ],
        last_active=(NOW - timedelta(hours=1)).isoformat() + "Z",
        tasks_completed=25,
        tasks_failed=4,
        tasks_in_progress=0
    ),
    Agent(
        id="WA",
        name="Web Assistant",
        status=AgentStatus.INACTIVE,
        description="Web Interface Agent",
        role="Web interface updates and user interaction",
        capabilities=[
            AgentCapability.WEB_INTERFACE,
            AgentCapability.DOCUMENTATION
        ],
        last_active=(NOW - timedelta(days=1)).isoformat() + "Z",
        tasks_completed=15,
        tasks_failed=1,
        tasks_in_progress=0
    )
]

# Create a lookup dictionary for agents by ID
AGENTS_BY_ID = {agent.id: agent for agent in AGENTS}

# Sample task data
TASKS = [
    Task(
        id="TASK-061A",
        description="Create Web UI Shell (React + Tailwind)",
        status=TaskStatus.COMPLETED,
        agent_id="CC",
        priority=TaskPriority.HIGH,
        created_at=NOW - timedelta(days=1, hours=5),
        updated_at=NOW - timedelta(days=1),
        start_time=NOW - timedelta(days=1, hours=4),
        end_time=NOW - timedelta(days=1),
        retries=0,
        fallback_agent=None,
        details=[
            f"Started at: {(NOW - timedelta(days=1, hours=4)).strftime('%Y-%m-%d %H:%M:%S')}",
            "Set up Vite with React and TypeScript",
            "Implemented layout and routing",
            f"Completed at: {(NOW - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')}"
        ],
        content={
            "task_id": "TASK-061A",
            "action": "create",
            "parameters": {"component": "web-ui-shell"}
        }
    ),
    Task(
        id="TASK-061B",
        description="Create ARCHITECTURE.md documentation",
        status=TaskStatus.COMPLETED,
        agent_id="CC",
        priority=TaskPriority.MEDIUM,
        created_at=NOW - timedelta(days=1),
        updated_at=NOW - timedelta(hours=18),
        start_time=NOW - timedelta(hours=20),
        end_time=NOW - timedelta(hours=18),
        retries=0,
        fallback_agent=None,
        details=[
            f"Started at: {(NOW - timedelta(hours=20)).strftime('%Y-%m-%d %H:%M:%S')}",
            "Documented system architecture",
            "Added component diagrams",
            f"Completed at: {(NOW - timedelta(hours=18)).strftime('%Y-%m-%d %H:%M:%S')}"
        ],
        content={
            "task_id": "TASK-061B",
            "action": "document",
            "parameters": {"file": "ARCHITECTURE.md"}
        }
    ),
    Task(
        id="TASK-061C",
        description="Implement FastAPI Endpoints",
        status=TaskStatus.IN_PROGRESS,
        agent_id="CC",
        priority=TaskPriority.HIGH,
        created_at=NOW - timedelta(hours=2),
        updated_at=NOW - timedelta(hours=1),
        start_time=NOW - timedelta(hours=1),
        end_time=None,
        retries=0,
        fallback_agent=None,
        details=[
            f"Started at: {(NOW - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')}",
            "Creating API project structure",
            "Implementing agent and task endpoints"
        ],
        content={
            "task_id": "TASK-061C",
            "action": "implement",
            "parameters": {"component": "fastapi-endpoints"}
        }
    ),
    Task(
        id="TASK-062",
        description="Add authentication to API endpoints",
        status=TaskStatus.PENDING,
        agent_id="CA",
        priority=TaskPriority.MEDIUM,
        created_at=NOW - timedelta(hours=1),
        updated_at=None,
        start_time=None,
        end_time=None,
        retries=0,
        fallback_agent=None,
        details=[],
        content={
            "task_id": "TASK-062",
            "action": "implement",
            "parameters": {"component": "api-auth"}
        }
    ),
    Task(
        id="TASK-052",
        description="Dashboard task filtering fixes",
        status=TaskStatus.COMPLETED,
        agent_id="WA",
        priority=TaskPriority.HIGH,
        created_at=NOW - timedelta(days=3),
        updated_at=NOW - timedelta(days=2),
        start_time=NOW - timedelta(days=3),
        end_time=NOW - timedelta(days=2),
        retries=2,
        fallback_agent=None,
        details=[
            f"Started at: {(NOW - timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S')}",
            "First attempt failed",
            "Second attempt failed",
            "Fixed timezone issues in task filtering",
            f"Completed at: {(NOW - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')}"
        ],
        content={
            "task_id": "TASK-052",
            "action": "fix",
            "parameters": {"component": "dashboard-filtering"}
        }
    )
]

# Create a lookup dictionary for tasks by ID
TASKS_BY_ID = {task.id: task for task in TASKS}