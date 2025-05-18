#!/usr/bin/env python3
"""
Execution Summary Generator

A CLI tool to generate summary reports from agent task logs.
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any

import yaml

# Constants
POSTBOX_DIR = (Path(__file__).parent.parent / "postbox").resolve()
INSIGHTS_DIR = (Path(__file__).parent.parent / "insights").resolve()
DEFAULT_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"

class TaskLogParser:
    """Parse task logs from agent postboxes."""
    
    def __init__(self, postbox_dir: Path = POSTBOX_DIR):
        self.postbox_dir = postbox_dir
        self.tasks = []
        
    def parse_all_agent_logs(self, agent: Optional[str] = None, date_range: Optional[Tuple[datetime, datetime]] = None):
        """Parse task logs from all agents or a specific agent."""
        self.tasks = []
        
        # Get list of agent directories
        if agent:
            agent_dirs = [self.postbox_dir / agent]
        else:
            agent_dirs = [d for d in self.postbox_dir.iterdir() if d.is_dir()]
        
        # Parse logs for each agent
        for agent_dir in agent_dirs:
            log_file = agent_dir / "task_log.md"
            if log_file.exists():
                self._parse_agent_log(agent_dir.name, log_file, date_range)
    
    def _parse_agent_log(self, agent: str, log_file: Path, date_range: Optional[Tuple[datetime, datetime]] = None):
        """Parse a single agent's task log."""
        current_task = None
        
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            
            # Match timestamp line (start of a new task entry)
            timestamp_match = re.match(r'^## (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[-+]\d{2}:\d{2})?)$', line)
            if timestamp_match:
                # Save previous task if exists
                if current_task and self._is_in_date_range(current_task.get('timestamp'), date_range):
                    self.tasks.append(current_task)
                
                # Start new task
                current_task = {
                    'agent': agent,
                    'timestamp': timestamp_match.group(1),
                    'status': 'unknown',
                    'details': {}
                }
                continue
                
            # Match status line
            status_match = re.match(r'^\*\*Status\*\*: ([^\s]+)(?:\s+(.*))?$', line)
            if status_match and current_task:
                current_task['status'] = status_match.group(1)
                if status_match.group(2):
                    current_task['details']['status_details'] = status_match.group(2)
                continue
                
            # Match other key-value pairs
            kv_match = re.match(r'^\*\*([^:]+)\*\*: (.+)$', line)
            if kv_match and current_task:
                key = kv_match.group(1).lower().replace(' ', '_')
                current_task['details'][key] = kv_match.group(2).strip()
                
        # Add the last task if it exists and is in date range
        if current_task and self._is_in_date_range(current_task.get('timestamp'), date_range):
            self.tasks.append(current_task)
    
    def _is_in_date_range(self, timestamp_str: Optional[str], date_range: Optional[Tuple[datetime, datetime]]) -> bool:
        """Check if a timestamp is within the specified date range."""
        if not date_range or not timestamp_str:
            return True
            
        try:
            # Try parsing with timezone first, then without
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S%z")
            except ValueError:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S")
                
            start, end = date_range
            return start <= timestamp <= end
        except (ValueError, TypeError):
            return False

class InsightsAggregator:
    """Aggregate insights from task logs and other sources."""
    
    def __init__(self, tasks: List[Dict], insights_dir: Path = INSIGHTS_DIR):
        self.tasks = tasks
        self.insights_dir = insights_dir
        self.agent_insights = self._load_agent_insights()
    
    def _load_agent_insights(self) -> Dict:
        """Load agent insights from the insights directory."""
        insights = {}
        
        # Load agent learning snapshot if available
        snapshot_file = self.insights_dir / "agent_learning_snapshot.json"
        if snapshot_file.exists():
            try:
                with open(snapshot_file, 'r', encoding='utf-8') as f:
                    insights['snapshot'] = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load agent learning snapshot: {e}", file=sys.stderr)
        
        return insights
    
    def generate_summary(self, output_format: str = 'markdown') -> Union[str, Dict]:
        """Generate a summary of the execution data."""
        summary = {
            'meta': {
                'generated_at': datetime.now().isoformat(),
                'time_range': {
                    'start': min((t['timestamp'] for t in self.tasks), default=None),
                    'end': max((t['timestamp'] for t in self.tasks), default=None)
                },
                'total_tasks': len(self.tasks),
                'format': output_format
            },
            'agents': {},
            'task_types': {},
            'metrics': {}
        }
        
        # Process tasks
        for task in self.tasks:
            agent = task['agent']
            task_type = task.get('details', {}).get('type', 'unknown')
            
            # Initialize agent data if not exists
            if agent not in summary['agents']:
                summary['agents'][agent] = {
                    'total_tasks': 0,
                    'successful_tasks': 0,
                    'failed_tasks': 0,
                    'task_types': {}
                }
            
            # Initialize task type data if not exists
            if task_type not in summary['task_types']:
                summary['task_types'][task_type] = {
                    'total': 0,
                    'successful': 0,
                    'failed': 0,
                    'agents': {}
                }
            
            # Update agent stats
            summary['agents'][agent]['total_tasks'] += 1
            if task['status'] == '✅' or 'success' in task['status'].lower():
                summary['agents'][agent]['successful_tasks'] += 1
            elif task['status'] == '❌' or 'fail' in task['status'].lower():
                summary['agents'][agent]['failed_tasks'] += 1
            
            # Update task type stats
            summary['task_types'][task_type]['total'] += 1
            if task['status'] == '✅' or 'success' in task['status'].lower():
                summary['task_types'][task_type]['successful'] += 1
            elif task['status'] == '❌' or 'fail' in task['status'].lower():
                summary['task_types'][task_type]['failed'] += 1
            
            # Update agent-task type matrix
            if task_type not in summary['agents'][agent]['task_types']:
                summary['agents'][agent]['task_types'][task_type] = {
                    'total': 0,
                    'successful': 0,
                    'failed': 0
                }
            
            summary['agents'][agent]['task_types'][task_type]['total'] += 1
            if task['status'] == '✅' or 'success' in task['status'].lower():
                summary['agents'][agent]['task_types'][task_type]['successful'] += 1
            elif task['status'] == '❌' or 'fail' in task['status'].lower():
                summary['agents'][agent]['task_types'][task_type]['failed'] += 1
        
        # Calculate success rates
        for agent in summary['agents'].values():
            agent['success_rate'] = (
                agent['successful_tasks'] / agent['total_tasks'] 
                if agent['total_tasks'] > 0 else 0
            )
            
            for task_type in agent['task_types'].values():
                task_type['success_rate'] = (
                    task_type['successful'] / task_type['total'] 
                    if task_type['total'] > 0 else 0
                )
        
        for task_type in summary['task_types'].values():
            task_type['success_rate'] = (
                task_type['successful'] / task_type['total'] 
                if task_type['total'] > 0 else 0
            )
            
            for agent_id, agent_data in task_type.get('agents', {}).items():
                agent_data['success_rate'] = (
                    agent_data['successful'] / agent_data['total'] 
                    if agent_data['total'] > 0 else 0
                )
        
        # Add metrics
        summary['metrics'] = {
            'overall_success_rate': (
                sum(a['successful_tasks'] for a in summary['agents'].values()) / 
                sum(a['total_tasks'] for a in summary['agents'].values())
                if any(a['total_tasks'] > 0 for a in summary['agents'].values()) else 0
            ),
            'total_agents': len(summary['agents']),
            'unique_task_types': len(summary['task_types'])
        }
        
        if output_format.lower() == 'json':
            return summary
        else:
            return self._format_markdown(summary)
    
    def _format_markdown(self, summary: Dict) -> str:
        """Format the summary as Markdown."""
        output = [
            "# Agent Task Execution Summary",
            f"Generated: {summary['meta']['generated_at']}\n",
            f"Time Range: {summary['meta']['time_range']['start']} to {summary['meta']['time_range']['end']}",
            f"Total Tasks: {summary['meta']['total_tasks']}",
            f"Overall Success Rate: {summary['metrics']['overall_success_rate']:.1%}\n",
            "## Agent Performance\n"
        ]
        
        # Agent performance table
        agent_table = ["| Agent | Tasks | Success Rate | Failed |",
                      "|-------|-------|--------------|--------|"]
        
        for agent_id, agent_data in sorted(summary['agents'].items()):
            agent_table.append(
                f"| **{agent_id}** | {agent_data['total_tasks']} | "
                f"{agent_data['success_rate']:.1%} | {agent_data['failed_tasks']} |"
            )
        
        output.extend(agent_table)
        output.append("\n## Task Type Performance\n")
        
        # Task type performance
        task_table = ["| Task Type | Total | Success Rate | Failed |",
                     "|-----------|-------|--------------|--------|"]
        
        for task_type, data in sorted(summary['task_types'].items()):
            task_table.append(
                f"| **{task_type}** | {data['total']} | "
                f"{data['success_rate']:.1%} | {data['failed']} |"
            )
        
        output.extend(task_table)
        
        # Add agent-task type matrix
        output.append("\n## Agent-Task Performance Matrix\n")
        
        # Get all task types for the header
        task_types = sorted(summary['task_types'].keys())
        if not task_types:
            task_types = sorted({
                task_type 
                for agent in summary['agents'].values() 
                for task_type in agent['task_types']
            })
        
        # Create header
        header = ["| Agent | " + " | ".join(task_types) + " |"]
        separator = ["|-------" + "|--------" * len(task_types) + "|"]
        
        # Create rows
        rows = []
        for agent_id in sorted(summary['agents'].keys()):
            row = [f"| **{agent_id}** |"]
            for task_type in task_types:
                if task_type in summary['agents'][agent_id]['task_types']:
                    stats = summary['agents'][agent_id]['task_types'][task_type]
                    row.append(f"{stats['successful']}/{stats['total']} ({stats['success_rate']:.0%})")
                else:
                    row.append("-")
            rows.append(" ".join(row) + " |")
        
        output.extend(header + separator + rows)
        
        # Add insights from learning data if available
        if 'snapshot' in self.agent_insights:
            output.extend(["\n## Agent Learning Insights\n"])
            snapshot = self.agent_insights['snapshot']
            
            # Add overall stats
            output.extend([
                f"- **Total Tasks Analyzed**: {snapshot.get('meta', {}).get('total_tasks_analyzed', 0)}",
                f"- **Snapshot Version**: {snapshot.get('meta', {}).get('version', 'N/A')}\n"
            ])
            
            # Add agent-specific insights
            for agent_id, agent_data in snapshot.get('agent_performance', {}).items():
                output.append(f"### {agent_id} Performance")
                output.append(f"- **Overall Success Rate**: {agent_data.get('overall_success_rate', 0):.1%}")
                output.append(f"- **Total Tasks**: {agent_data.get('total_tasks', 0)}")
                
                if 'task_types' in agent_data:
                    output.append("#### Task Type Performance")
                    for task_type, stats in agent_data['task_types'].items():
                        output.append(
                            f"- **{task_type.title()}**: {stats.get('success_rate', 0):.1%} "
                            f"({stats.get('total_tasks', 0)} tasks, "
                            f"avg. {stats.get('average_duration', 0):.1f}s)"
                        )
                output.append("")
        
        return "\n".join(output)

def parse_date_range(date_range_str: str) -> Tuple[datetime, datetime]:
    """Parse a date range string into start and end datetimes."""
    now = datetime.now()
    
    if date_range_str == 'today':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
    elif date_range_str == 'yesterday':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        end = start + timedelta(days=1)
    elif date_range_str == 'this_week':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=now.weekday())
        end = start + timedelta(weeks=1)
    elif date_range_str == 'last_week':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=now.weekday() + 7)
        end = start + timedelta(weeks=1)
    elif date_range_str == 'this_month':
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=start.month + 1)
    elif date_range_str == 'last_month':
        if now.month == 1:
            start = now.replace(year=now.year - 1, month=12, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start = now.replace(month=now.month - 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = start.replace(month=start.month + 1) if start.month < 12 else start.replace(year=start.year + 1, month=1)
    else:
        # Default to all time if unknown range
        start = datetime.min
        end = datetime.max
    
    return start, end

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='Generate execution summary reports from agent task logs.')
    parser.add_argument(
        '--format', 
        choices=['markdown', 'json'], 
        default='markdown',
        help='Output format (default: markdown)'
    )
    parser.add_argument(
        '--agent',
        help='Filter by agent ID (e.g., CA, WA, CC, ARCH)'
    )
    parser.add_argument(
        '--range',
        choices=['today', 'yesterday', 'this_week', 'last_week', 'this_month', 'last_month'],
        help='Time range for the report'
    )
    parser.add_argument(
        '--output',
        help='Output file path (default: stdout)'
    )
    
    args = parser.parse_args()
    
    try:
        # Parse task logs
        date_range = parse_date_range(args.range) if args.range else None
        parser = TaskLogParser()
        parser.parse_all_agent_logs(agent=args.agent, date_range=date_range)
        
        # Generate summary
        aggregator = InsightsAggregator(parser.tasks)
        result = aggregator.generate_summary(args.format)
        
        # Output result
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                if isinstance(result, dict):
                    json.dump(result, f, indent=2)
                else:
                    f.write(result)
            print(f"Report generated: {args.output}")
        else:
            if isinstance(result, dict):
                print(json.dumps(result, indent=2))
            else:
                print(result)
                
    except Exception as e:
        print(f"Error generating report: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
