"""
Service for handling task and plan history data.
"""
import json
import os
import glob
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

from models.history import PlanHistoryItem, TaskRecentItem


class HistoryService:
    """Service for retrieving task and plan history data."""
    
    def __init__(self, base_path: str = "/Users/arielmuslera/Development/Projects/agent-comms-mvp"):
        self.base_path = Path(base_path)
        self.logs_path = self.base_path / "logs"
        self.plans_path = self.base_path / "plans"
        self.postbox_path = self.base_path / "postbox"
    
    def get_plan_history(self, limit: int = 50) -> List[PlanHistoryItem]:
        """
        Retrieve plan execution history.
        
        Args:
            limit: Maximum number of plans to return
            
        Returns:
            List[PlanHistoryItem]: List of plan history items
        """
        plan_history = []
        
        # Try to read from plan logs and execution history
        try:
            # Look for plan files in plans directory
            plan_files = list(self.plans_path.glob("*.yaml")) if self.plans_path.exists() else []
            
            # Also check for plan execution logs
            if self.logs_path.exists():
                log_files = list(self.logs_path.glob("*plan*.json"))
                plan_files.extend(log_files)
            
            for plan_file in plan_files[:limit]:
                try:
                    plan_item = self._extract_plan_history_from_file(plan_file)
                    if plan_item:
                        plan_history.append(plan_item)
                except Exception:
                    continue
        except Exception:
            pass
        
        # If no real data found, return dummy data
        if not plan_history:
            plan_history = self._get_dummy_plan_history(limit)
        
        # Sort by submission time (newest first)
        plan_history.sort(key=lambda x: x.submitted_at, reverse=True)
        
        return plan_history[:limit]
    
    def get_recent_tasks(self, limit: int = 100, hours: int = 24) -> List[TaskRecentItem]:
        """
        Retrieve recent task executions.
        
        Args:
            limit: Maximum number of tasks to return
            hours: Number of hours to look back
            
        Returns:
            List[TaskRecentItem]: List of recent task items
        """
        recent_tasks = []
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        try:
            # Read from agent scores log
            scores_file = self.logs_path / "agent_scores.json"
            if scores_file.exists():
                with open(scores_file, 'r') as f:
                    scores_data = json.load(f)
                    
                # If it's a flat array format, extract tasks
                if isinstance(scores_data, list):
                    for entry in scores_data:
                        task_item = self._extract_task_from_log_entry(entry)
                        if task_item and task_item.timestamp >= cutoff_time:
                            recent_tasks.append(task_item)
                # If it's the summary format, create synthetic entries
                elif isinstance(scores_data, dict):
                    for agent_id, data in scores_data.items():
                        task_item = self._create_synthetic_task_from_summary(agent_id, data)
                        if task_item:
                            recent_tasks.append(task_item)
            
            # Also check postbox outboxes for recent task status messages
            if self.postbox_path.exists():
                for agent_dir in self.postbox_path.iterdir():
                    if agent_dir.is_dir():
                        outbox_file = agent_dir / "outbox.json"
                        if outbox_file.exists():
                            tasks_from_outbox = self._extract_tasks_from_outbox(outbox_file, cutoff_time)
                            recent_tasks.extend(tasks_from_outbox)
        except Exception:
            pass
        
        # If no real data found, return dummy data
        if not recent_tasks:
            recent_tasks = self._get_dummy_recent_tasks(limit, hours)
        
        # Sort by timestamp (newest first) and limit
        recent_tasks.sort(key=lambda x: x.timestamp, reverse=True)
        
        return recent_tasks[:limit]
    
    def _extract_plan_history_from_file(self, plan_file: Path) -> Optional[PlanHistoryItem]:
        """Extract plan history from plan file or log."""
        try:
            if plan_file.suffix == '.yaml':
                # This is a plan definition file
                plan_id = plan_file.stem
                stat = plan_file.stat()
                return PlanHistoryItem(
                    plan_id=plan_id,
                    submitted_at=datetime.fromtimestamp(stat.st_mtime),
                    agent_count=3,  # Default estimate
                    status="submitted",
                    duration_sec=None,
                    success_rate=None
                )
            elif plan_file.suffix == '.json':
                # This might be an execution log
                with open(plan_file, 'r') as f:
                    log_data = json.load(f)
                
                return PlanHistoryItem(
                    plan_id=log_data.get("plan_id", plan_file.stem),
                    submitted_at=datetime.fromisoformat(log_data.get("start_time", datetime.now().isoformat()).replace('Z', '+00:00')),
                    agent_count=log_data.get("agent_count", 3),
                    status=log_data.get("status", "complete"),
                    duration_sec=log_data.get("duration_sec"),
                    success_rate=log_data.get("success_rate")
                )
        except Exception:
            return None
    
    def _extract_task_from_log_entry(self, entry: Dict[str, Any]) -> Optional[TaskRecentItem]:
        """Extract task info from agent scores log entry."""
        try:
            return TaskRecentItem(
                trace_id=entry.get("trace_id", f"log-{entry.get('timestamp', '')}"),
                agent=entry.get("agent_id", "UNKNOWN"),
                score=entry.get("score"),
                success=entry.get("success"),
                retry_count=entry.get("retry_count", 0),
                duration_sec=entry.get("duration_sec"),
                task_id=entry.get("task_id"),
                timestamp=datetime.fromisoformat(entry["timestamp"].replace('Z', '+00:00')),
                error_code=entry.get("error_code")
            )
        except Exception:
            return None
    
    def _create_synthetic_task_from_summary(self, agent_id: str, data: Dict[str, Any]) -> Optional[TaskRecentItem]:
        """Create synthetic task entry from agent summary data."""
        try:
            last_activity = data.get("last_activity")
            if last_activity:
                timestamp = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
            else:
                timestamp = datetime.now()
            
            return TaskRecentItem(
                trace_id=f"summary-{agent_id}-{int(timestamp.timestamp())}",
                agent=agent_id,
                score=data.get("average_score"),
                success=data.get("success_rate", 0) > 0.5,
                retry_count=0,
                duration_sec=None,
                task_id=f"latest-{agent_id}",
                timestamp=timestamp,
                error_code=None
            )
        except Exception:
            return None
    
    def _extract_tasks_from_outbox(self, outbox_file: Path, cutoff_time: datetime) -> List[TaskRecentItem]:
        """Extract task information from agent outbox messages."""
        tasks = []
        try:
            with open(outbox_file, 'r') as f:
                outbox_data = json.load(f)
            
            if isinstance(outbox_data, list):
                for message in outbox_data:
                    try:
                        msg_time = datetime.fromisoformat(message.get("timestamp", "").replace('Z', '+00:00'))
                        if msg_time >= cutoff_time:
                            # Extract task info from message
                            content = message.get("content", {})
                            if "task_id" in content:
                                task = TaskRecentItem(
                                    trace_id=message.get("id", f"outbox-{int(msg_time.timestamp())}"),
                                    agent=message.get("sender", "UNKNOWN"),
                                    score=content.get("score"),
                                    success=content.get("status") == "completed",
                                    retry_count=message.get("retry_count", 0),
                                    duration_sec=content.get("duration_sec"),
                                    task_id=content.get("task_id"),
                                    timestamp=msg_time,
                                    error_code=content.get("error_code")
                                )
                                tasks.append(task)
                    except Exception:
                        continue
        except Exception:
            pass
        
        return tasks
    
    def _get_dummy_plan_history(self, limit: int) -> List[PlanHistoryItem]:
        """Generate dummy plan history data."""
        dummy_plans = []
        base_time = datetime.now()
        
        for i in range(min(limit, 10)):
            dummy_plans.append(PlanHistoryItem(
                plan_id=f"test-plan-{i+1:03d}",
                submitted_at=base_time - timedelta(hours=i*2, minutes=i*15),
                agent_count=3 + (i % 3),
                status=["complete", "running", "failed", "complete", "complete"][i % 5],
                duration_sec=120.5 + (i * 30.2),
                success_rate=0.75 + (i * 0.05) if i % 5 != 2 else None
            ))
        
        return dummy_plans
    
    def _get_dummy_recent_tasks(self, limit: int, hours: int) -> List[TaskRecentItem]:
        """Generate dummy recent task data."""
        dummy_tasks = []
        base_time = datetime.now()
        agents = ["CA", "CC", "WA", "ARCH"]
        
        for i in range(min(limit, 20)):
            agent = agents[i % len(agents)]
            success = i % 4 != 3  # 75% success rate
            
            dummy_tasks.append(TaskRecentItem(
                trace_id=f"trace-{i+1:04d}-{agent.lower()}",
                agent=agent,
                score=0.91 - (i * 0.02) if success else 0.3 + (i * 0.01),
                success=success,
                retry_count=1 if i % 5 == 0 else 0,
                duration_sec=3.8 + (i * 0.5),
                task_id=f"TASK-{i+1:03d}",
                timestamp=base_time - timedelta(minutes=i*30),
                error_code="E_TIMEOUT" if not success else None
            ))
        
        return dummy_tasks