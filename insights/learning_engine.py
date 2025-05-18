#!/usr/bin/env python3
"""
Learning engine for analyzing agent behavior and generating scorecards.

This module processes various logs to extract insights about agent performance:
- Task completion rates and response times
- Error patterns and recovery effectiveness
- Retry statistics and failure analysis
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict
import statistics


class LearningEngine:
    """Core learning engine for agent behavior analysis."""
    
    def __init__(self):
        """Initialize the learning engine with empty data structures."""
        self.agent_stats = defaultdict(lambda: {
            'tasks_completed': 0,
            'response_times': [],
            'failures': 0,
            'retries': 0,
            'failure_patterns': defaultdict(int)
        })
        self.task_logs = []
        self.router_logs = []
        self.recovery_logs = []
    
    def parse_logs(self) -> None:
        """Parse all relevant logs to extract agent activity data."""
        # Parse task logs
        task_log_files = Path("postbox").glob("*/task_log.md")
        for log_file in task_log_files:
            agent_id = log_file.parent.name
            with open(log_file, 'r') as f:
                content = f.read()
                self._parse_task_log(content, agent_id)
        
        # Parse router logs
        router_log = Path("router/router_log.md")
        if router_log.exists():
            with open(router_log, 'r') as f:
                content = f.read()
                self._parse_router_log(content)
        
        # Parse recovery logs
        recovery_log = Path("recovery/recovery_log.md")
        if recovery_log.exists():
            with open(recovery_log, 'r') as f:
                content = f.read()
                self._parse_recovery_log(content)
    
    def _parse_task_log(self, content: str, agent_id: str) -> None:
        """Parse a task log file for agent activity."""
        # Extract task completion entries
        task_pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - Completed task (\w+-\d+)"
        for match in re.finditer(task_pattern, content):
            timestamp, task_id = match.groups()
            self.agent_stats[agent_id]['tasks_completed'] += 1
            self.task_logs.append({
                'timestamp': timestamp,
                'task_id': task_id,
                'agent_id': agent_id,
                'type': 'completion'
            })
        
        # Extract error entries
        error_pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - Error: (\w+) - (.+)"
        for match in re.finditer(error_pattern, content):
            timestamp, error_code, message = match.groups()
            self.agent_stats[agent_id]['failures'] += 1
            self.agent_stats[agent_id]['failure_patterns'][error_code] += 1
            self.task_logs.append({
                'timestamp': timestamp,
                'error_code': error_code,
                'message': message,
                'agent_id': agent_id,
                'type': 'error'
            })
    
    def _parse_router_log(self, content: str) -> None:
        """Parse the router log for message routing and retry data."""
        # Extract retry entries
        retry_pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - Retrying message (\w+) for agent (\w+)"
        for match in re.finditer(retry_pattern, content):
            timestamp, message_id, agent_id = match.groups()
            self.agent_stats[agent_id]['retries'] += 1
            self.router_logs.append({
                'timestamp': timestamp,
                'message_id': message_id,
                'agent_id': agent_id,
                'type': 'retry'
            })
    
    def _parse_recovery_log(self, content: str) -> None:
        """Parse the recovery log for fallback task data."""
        # Extract fallback activation entries
        fallback_pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - Activated fallback for error: (\w+)"
        for match in re.finditer(fallback_pattern, content):
            timestamp, error_code = match.groups()
            self.recovery_logs.append({
                'timestamp': timestamp,
                'error_code': error_code,
                'type': 'fallback'
            })
    
    def build_agent_scorecard(self, agent_id: str) -> Dict[str, Any]:
        """
        Build a comprehensive scorecard for an agent.
        
        Args:
            agent_id: ID of the agent to analyze
            
        Returns:
            Dict containing agent performance metrics
        """
        stats = self.agent_stats[agent_id]
        
        # Calculate average response time
        avg_response_time = None
        if stats['response_times']:
            avg_response_time = statistics.mean(stats['response_times'])
        
        # Calculate retry rate
        retry_rate = 0
        if stats['tasks_completed'] > 0:
            retry_rate = stats['retries'] / stats['tasks_completed']
        
        # Get top failure patterns
        top_failures = sorted(
            stats['failure_patterns'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        return {
            'agent_id': agent_id,
            'tasks_completed': stats['tasks_completed'],
            'average_response_time': avg_response_time,
            'total_failures': stats['failures'],
            'retry_rate': retry_rate,
            'top_failure_patterns': dict(top_failures)
        }
    
    def extract_failure_patterns(self) -> Dict[str, Any]:
        """
        Extract common failure patterns across all agents.
        
        Returns:
            Dict containing failure pattern analysis
        """
        all_failures = defaultdict(int)
        error_messages = defaultdict(list)
        
        # Aggregate failures from task logs
        for log in self.task_logs:
            if log['type'] == 'error':
                all_failures[log['error_code']] += 1
                error_messages[log['error_code']].append(log['message'])
        
        # Get most common failures
        top_failures = sorted(
            all_failures.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            'total_failures': sum(all_failures.values()),
            'failure_distribution': dict(top_failures),
            'common_error_messages': {
                code: messages[:3]  # Top 3 messages per error code
                for code, messages in error_messages.items()
            }
        }
    
    def write_learning_snapshot(self) -> None:
        """Write the current analysis to a JSON snapshot file."""
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'agent_scorecards': {
                agent_id: self.build_agent_scorecard(agent_id)
                for agent_id in self.agent_stats.keys()
            },
            'failure_analysis': self.extract_failure_patterns(),
            'summary': {
                'total_agents': len(self.agent_stats),
                'total_tasks': sum(stats['tasks_completed'] for stats in self.agent_stats.values()),
                'total_failures': sum(stats['failures'] for stats in self.agent_stats.values()),
                'total_retries': sum(stats['retries'] for stats in self.agent_stats.values())
            }
        }
        
        # Write to snapshot file
        snapshot_path = Path("insights/agent_learning_snapshot.json")
        with open(snapshot_path, 'w') as f:
            json.dump(snapshot, f, indent=2)


def main():
    """Main entry point for the learning engine."""
    engine = LearningEngine()
    engine.parse_logs()
    engine.write_learning_snapshot()


if __name__ == "__main__":
    main() 