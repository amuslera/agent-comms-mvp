"""
Execution Trace Logger Module

This module provides structured JSON logging for YAML plan execution,
capturing complete execution traces including DAG structure, task assignments,
timing, warnings, errors, and conditional execution paths.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict, field
from enum import Enum


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    SKIPPED_CONDITION = "skipped_due_to_condition"
    RETRYING = "retrying"


@dataclass
class TaskTrace:
    """Trace information for a single task execution."""
    task_id: str
    agent: str
    status: TaskStatus
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_sec: Optional[float] = None
    trace_id: Optional[str] = None
    retry_count: int = 0
    branch_created: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    conditions: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    warning: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PlanTrace:
    """Complete execution trace for a plan run."""
    trace_id: str
    plan_id: str
    plan_name: str
    plan_path: str
    start_time: str
    end_time: Optional[str] = None
    duration_sec: Optional[float] = None
    status: str = "running"
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    skipped_tasks: int = 0
    dag_structure: Optional[Dict[str, Any]] = None
    tasks: Dict[str, TaskTrace] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ExecutionTraceLogger:
    """Handles structured logging of plan execution traces."""
    
    def __init__(self, logs_dir: Path = None):
        """
        Initialize the trace logger.
        
        Args:
            logs_dir: Directory for log files (default: logs/tasks)
        """
        self.logs_dir = logs_dir or Path("logs/tasks")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.current_trace: Optional[PlanTrace] = None
        self._start_times: Dict[str, float] = {}
    
    def start_plan(self, trace_id: str, plan_id: str, plan_name: str, 
                   plan_path: str, dag_structure: Dict[str, Any] = None) -> PlanTrace:
        """
        Start logging a new plan execution.
        
        Args:
            trace_id: Unique trace identifier
            plan_id: Plan identifier
            plan_name: Human-readable plan name
            plan_path: Path to the YAML plan file
            dag_structure: DAG structure with nodes and edges
            
        Returns:
            PlanTrace object
        """
        self.current_trace = PlanTrace(
            trace_id=trace_id,
            plan_id=plan_id,
            plan_name=plan_name,
            plan_path=plan_path,
            start_time=datetime.now().isoformat(),
            dag_structure=dag_structure
        )
        
        # Count total tasks from DAG
        if dag_structure and "nodes" in dag_structure:
            self.current_trace.total_tasks = len(dag_structure["nodes"])
        
        # Write initial trace file
        self._write_trace()
        return self.current_trace
    
    def start_task(self, task_id: str, agent: str, dependencies: List[str] = None,
                   trace_id: str = None, branch: str = None) -> None:
        """Start logging a task execution."""
        if not self.current_trace:
            return
        
        task_trace = TaskTrace(
            task_id=task_id,
            agent=agent,
            status=TaskStatus.RUNNING,
            start_time=datetime.now().isoformat(),
            trace_id=trace_id,
            dependencies=dependencies or [],
            branch_created=branch
        )
        
        self.current_trace.tasks[task_id] = task_trace
        self._start_times[task_id] = time.time()
        self._write_trace()
    
    def complete_task(self, task_id: str, status: TaskStatus, 
                     result: Dict[str, Any] = None, error: str = None) -> None:
        """Complete a task execution."""
        if not self.current_trace or task_id not in self.current_trace.tasks:
            return
        
        task = self.current_trace.tasks[task_id]
        task.status = status
        task.end_time = datetime.now().isoformat()
        
        # Calculate duration
        if task_id in self._start_times:
            task.duration_sec = round(time.time() - self._start_times[task_id], 2)
            del self._start_times[task_id]
        
        # Set result or error
        if result:
            task.result = result
        if error:
            task.error = error
            self.current_trace.errors.append(f"Task {task_id}: {error}")
        
        # Update counters
        if status == TaskStatus.SUCCESS:
            self.current_trace.completed_tasks += 1
        elif status in [TaskStatus.FAILED]:
            self.current_trace.failed_tasks += 1
        elif status in [TaskStatus.SKIPPED, TaskStatus.SKIPPED_CONDITION]:
            self.current_trace.skipped_tasks += 1
        
        self._write_trace()
    
    def skip_task(self, task_id: str, agent: str, reason: str, 
                  condition: Dict[str, Any] = None) -> None:
        """Log a skipped task."""
        if not self.current_trace:
            return
        
        task_trace = TaskTrace(
            task_id=task_id,
            agent=agent,
            status=TaskStatus.SKIPPED_CONDITION if condition else TaskStatus.SKIPPED,
            warning=reason,
            conditions=condition,
            start_time=datetime.now().isoformat(),
            end_time=datetime.now().isoformat()
        )
        
        self.current_trace.tasks[task_id] = task_trace
        self.current_trace.skipped_tasks += 1
        self.current_trace.warnings.append(f"Task {task_id} skipped: {reason}")
        self._write_trace()
    
    def add_warning(self, warning: str) -> None:
        """Add a warning to the trace."""
        if self.current_trace:
            self.current_trace.warnings.append(warning)
            self._write_trace()
    
    def add_error(self, error: str) -> None:
        """Add an error to the trace."""
        if self.current_trace:
            self.current_trace.errors.append(error)
            self._write_trace()
    
    def update_context(self, context: Dict[str, Any]) -> None:
        """Update the plan execution context."""
        if self.current_trace:
            self.current_trace.context.update(context)
            self._write_trace()
    
    def retry_task(self, task_id: str, retry_count: int) -> None:
        """Log a task retry."""
        if not self.current_trace or task_id not in self.current_trace.tasks:
            return
        
        task = self.current_trace.tasks[task_id]
        task.status = TaskStatus.RETRYING
        task.retry_count = retry_count
        self.add_warning(f"Task {task_id} retrying (attempt {retry_count + 1})")
        self._write_trace()
    
    def complete_plan(self, status: str = "completed") -> None:
        """Complete the plan execution trace."""
        if not self.current_trace:
            return
        
        self.current_trace.end_time = datetime.now().isoformat()
        self.current_trace.status = status
        
        # Calculate total duration
        start_dt = datetime.fromisoformat(self.current_trace.start_time)
        end_dt = datetime.fromisoformat(self.current_trace.end_time)
        self.current_trace.duration_sec = round((end_dt - start_dt).total_seconds(), 2)
        
        # Determine final status if not provided
        if status == "completed":
            if self.current_trace.failed_tasks > 0:
                self.current_trace.status = "failed"
            elif self.current_trace.completed_tasks == self.current_trace.total_tasks:
                self.current_trace.status = "success"
            else:
                self.current_trace.status = "partial"
        
        self._write_trace()
    
    def get_trace_path(self, trace_id: str = None) -> Path:
        """Get the path for a trace file."""
        if not trace_id and self.current_trace:
            trace_id = self.current_trace.trace_id
        return self.logs_dir / f"trace_{trace_id}.json"
    
    def _write_trace(self) -> None:
        """Write the current trace to file."""
        if not self.current_trace:
            return
        
        trace_path = self.get_trace_path()
        
        # Convert dataclass to dict, handling nested TaskTrace objects
        trace_dict = asdict(self.current_trace)
        
        # Ensure TaskStatus enums are converted to strings
        for task_id, task_data in trace_dict.get("tasks", {}).items():
            if isinstance(task_data.get("status"), TaskStatus):
                task_data["status"] = task_data["status"].value
        
        # Write with pretty formatting
        with open(trace_path, 'w') as f:
            json.dump(trace_dict, f, indent=2, default=str)
    
    def load_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Load a trace file by ID."""
        trace_path = self.get_trace_path(trace_id)
        if trace_path.exists():
            with open(trace_path) as f:
                return json.load(f)
        return None
    
    def export_summary(self) -> Dict[str, Any]:
        """Export a summary of the current trace."""
        if not self.current_trace:
            return {}
        
        return {
            "trace_id": self.current_trace.trace_id,
            "plan_id": self.current_trace.plan_id,
            "plan_name": self.current_trace.plan_name,
            "status": self.current_trace.status,
            "duration_sec": self.current_trace.duration_sec,
            "task_summary": {
                "total": self.current_trace.total_tasks,
                "completed": self.current_trace.completed_tasks,
                "failed": self.current_trace.failed_tasks,
                "skipped": self.current_trace.skipped_tasks
            },
            "warnings_count": len(self.current_trace.warnings),
            "errors_count": len(self.current_trace.errors)
        }