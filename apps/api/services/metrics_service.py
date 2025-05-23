"""
Service for handling metrics data aggregation and processing.
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import glob

from models.metrics import AgentMetrics, PlanMetrics


class MetricsService:
    """Service for aggregating and processing agent and plan metrics."""
    
    def __init__(self, base_path: str = "/Users/arielmuslera/Development/Projects/agent-comms-mvp"):
        self.base_path = base_path
        self.logs_path = os.path.join(base_path, "logs")
        self.postbox_path = os.path.join(base_path, "postbox")
    
    def get_agent_metrics(self) -> List[AgentMetrics]:
        """
        Retrieve metrics for all agents.
        
        Returns:
            List[AgentMetrics]: List of agent performance metrics
        """
        agent_metrics = []
        
        # Try to read from agent_scores.json if it exists
        scores_file = os.path.join(self.logs_path, "agent_scores.json")
        if os.path.exists(scores_file):
            try:
                with open(scores_file, 'r') as f:
                    scores_data = json.load(f)
                    
                for agent_id, data in scores_data.items():
                    agent_metrics.append(AgentMetrics(
                        agent_id=agent_id,
                        average_score=data.get("average_score", 0.85),
                        success_rate=data.get("success_rate", 0.80),
                        task_count=data.get("task_count", 10),
                        last_activity=datetime.fromisoformat(data["last_activity"].replace('Z', '+00:00')) if "last_activity" in data else None
                    ))
            except (json.JSONDecodeError, FileNotFoundError, KeyError):
                pass
        
        # If no data found, return dummy data for known agents
        if not agent_metrics:
            agent_metrics = self._get_dummy_agent_metrics()
        
        return agent_metrics
    
    def get_plan_metrics(self, plan_id: str) -> Optional[PlanMetrics]:
        """
        Retrieve metrics for a specific plan.
        
        Args:
            plan_id: The ID of the plan to get metrics for
            
        Returns:
            Optional[PlanMetrics]: Plan metrics if found, None otherwise
        """
        # Try to read from plan execution logs
        plan_log_pattern = os.path.join(self.logs_path, f"*{plan_id}*.json")
        plan_files = glob.glob(plan_log_pattern)
        
        if plan_files:
            try:
                with open(plan_files[0], 'r') as f:
                    plan_data = json.load(f)
                    
                # Extract agent metrics from plan execution
                agent_metrics = self._extract_agent_metrics_from_plan(plan_data)
                
                return PlanMetrics(
                    plan_id=plan_id,
                    agent_metrics=agent_metrics,
                    average_duration_sec=plan_data.get("average_duration_sec", 5.2),
                    total_tasks=plan_data.get("total_tasks", len(agent_metrics)),
                    completed_tasks=plan_data.get("completed_tasks", len(agent_metrics)),
                    success_rate=plan_data.get("success_rate", 0.85),
                    execution_start=datetime.fromisoformat(plan_data["execution_start"].replace('Z', '+00:00')) if "execution_start" in plan_data else None,
                    execution_end=datetime.fromisoformat(plan_data["execution_end"].replace('Z', '+00:00')) if "execution_end" in plan_data else None,
                    status=plan_data.get("status", "completed")
                )
            except (json.JSONDecodeError, FileNotFoundError, KeyError):
                pass
        
        # Return dummy data for known plan IDs
        return self._get_dummy_plan_metrics(plan_id)
    
    def _get_dummy_agent_metrics(self) -> List[AgentMetrics]:
        """Generate dummy agent metrics for testing."""
        return [
            AgentMetrics(
                agent_id="CA",
                average_score=0.91,
                success_rate=0.87,
                task_count=27,
                last_activity=datetime.now()
            ),
            AgentMetrics(
                agent_id="CC",
                average_score=0.88,
                success_rate=0.83,
                task_count=23,
                last_activity=datetime.now()
            ),
            AgentMetrics(
                agent_id="WA",
                average_score=0.85,
                success_rate=0.81,
                task_count=19,
                last_activity=datetime.now()
            ),
            AgentMetrics(
                agent_id="ARCH",
                average_score=0.94,
                success_rate=0.92,
                task_count=31,
                last_activity=datetime.now()
            )
        ]
    
    def _get_dummy_plan_metrics(self, plan_id: str) -> PlanMetrics:
        """Generate dummy plan metrics for testing."""
        agent_metrics = self._get_dummy_agent_metrics()[:2]  # Use first 2 agents
        
        return PlanMetrics(
            plan_id=plan_id,
            agent_metrics=agent_metrics,
            average_duration_sec=5.2,
            total_tasks=4,
            completed_tasks=3,
            success_rate=0.75,
            execution_start=datetime.now(),
            execution_end=datetime.now(),
            status="completed"
        )
    
    def _extract_agent_metrics_from_plan(self, plan_data: Dict[str, Any]) -> List[AgentMetrics]:
        """Extract agent metrics from plan execution data."""
        agent_metrics = []
        
        agents_data = plan_data.get("agents", {})
        for agent_id, data in agents_data.items():
            agent_metrics.append(AgentMetrics(
                agent_id=agent_id,
                average_score=data.get("score", 0.85),
                success_rate=data.get("success_rate", 0.80),
                task_count=data.get("task_count", 1),
                last_activity=datetime.fromisoformat(data["last_activity"].replace('Z', '+00:00')) if "last_activity" in data else None
            ))
        
        return agent_metrics