#!/usr/bin/env python3
"""
Agent Learning CLI - View and analyze agent performance metrics.

This tool provides insights into agent performance, success rates, and recommendations
for task assignments based on historical data.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# ANSI color codes for terminal output
COLORS = {
    'HEADER': '\033[95m',
    'BLUE': '\033[94m',
    'CYAN': '\033[96m',
    'GREEN': '\033[92m',
    'YELLOW': '\033[93m',
    'RED': '\033[91m',
    'ENDC': '\033[0m',
    'BOLD': '\033[1m',
    'UNDERLINE': '\033[4m',
}

def color_text(text: str, color: str) -> str:
    """Apply ANSI color to text if output is a terminal."""
    if sys.stdout.isatty() and color in COLORS:
        return f"{COLORS[color]}{text}{COLORS['ENDC']}"
    return text

class AgentLearningCLI:
    """CLI for analyzing and reporting on agent learning and performance."""
    
    def __init__(self, snapshot_path: str = "agent_learning_snapshot.json"):
        """Initialize with path to the learning snapshot file."""
        self.snapshot_path = Path(snapshot_path)
        self.data = self._load_snapshot()
    
    def _load_snapshot(self) -> Dict:
        """Load the agent learning snapshot JSON file."""
        try:
            with open(self.snapshot_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Snapshot file not found at {self.snapshot_path}")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in snapshot file {self.snapshot_path}")
            sys.exit(1)
    
    def get_summary(self) -> str:
        """Generate a summary of agent performance."""
        output = [
            color_text("\n🤖 Agent Performance Summary", "HEADER"),
            "=" * 40,
            f"Last Updated: {self.data.get('last_updated', 'N/A')}\n"
        ]
        
        # Overall stats
        total_tasks = sum(agent['completed_tasks'] + agent['failed_tasks'] 
                         for agent in self.data['agents'].values())
        success_rate = (sum(agent['completed_tasks'] for agent in self.data['agents'].values()) / 
                       total_tasks) * 100 if total_tasks > 0 else 0
        
        output.extend([
            f"📊 {color_text('Overall Stats', 'BOLD')}",
            f"  • Total Tasks: {total_tasks}",
            f"  • Overall Success Rate: {success_rate:.1f}%\n"
        ])
        
        # Per-agent stats
        output.append(f"👥 {color_text('Agent Performance', 'BOLD')}")
        for agent_id, agent_data in self.data['agents'].items():
            success_rate = agent_data['success_rate'] * 100
            color = (
                'GREEN' if success_rate >= 90 else
                'YELLOW' if success_rate >= 75 else
                'RED'
            )
            success_text = f"{success_rate:.1f}% success"
            output.append(
                f"  • {color_text(agent_id, 'BOLD')}: "
                f"{agent_data['completed_tasks']} completed, "
                f"{agent_data['failed_tasks']} failed, "
                f"{color_text(success_text, color)}"
            )
        
        return "\n".join(output)
    
    def get_recommendation(self, task_type: str) -> str:
        """Get the best agent recommendation for a task type."""
        if task_type not in self.data.get('task_types', []):
            return f"Error: Unknown task type '{task_type}'. Available types: {', '.join(self.data.get('task_types', []))}"
        
        agents = []
        for agent_id, agent_data in self.data['agents'].items():
            if task_type in agent_data.get('by_task_type', {}):
                task_data = agent_data['by_task_type'][task_type]
                agents.append({
                    'id': agent_id,
                    'success_rate': task_data['success_rate'],
                    'completed': task_data['completed'],
                    'avg_time': task_data.get('avg_time_seconds', 0)
                })
        
        if not agents:
            return f"No agents found with data for task type: {task_type}"
        
        # Sort by success rate (descending) and completed count (descending)
        agents_sorted = sorted(
            agents,
            key=lambda x: (-x['success_rate'], -x['completed'])
        )
        
        output = [
            color_text(f"\n🎯 Top Agents for Task Type: {task_type}", "HEADER"),
            "=" * 40
        ]
        
        for i, agent in enumerate(agents_sorted, 1):
            success_rate = agent['success_rate'] * 100
            color = (
                'GREEN' if success_rate >= 90 else
                'YELLOW' if success_rate >= 75 else
                'RED'
            )
            status_icon = (
                '✅' if success_rate >= 90 else
                '⚠️' if success_rate >= 75 else
                '❌'
            )
            agent_id = agent['id']
            completed = agent['completed']
            avg_time = agent['avg_time']
            success_text = f"{success_rate:.1f}% success"
            
            output.append(
                f"{status_icon} {color_text(f'{i}. {agent_id}', 'BOLD')}: "
                f"{completed} completed, "
                f"{color_text(success_text, color)}, "
                f"avg. {avg_time:.1f}s"
            )
        
        return "\n".join(output)
    
    def get_error_analysis(self) -> str:
        """Analyze and report on agent errors and retries."""
        output = [
            color_text("\n⚠️ Agent Error Analysis", "HEADER"),
            "=" * 40,
            "Agents with potential issues:\n"
        ]
        
        issues_found = False
        for agent_id, agent_data in self.data['agents'].items():
            # Check for high failure rate
            failure_rate = (agent_data['failed_tasks'] / 
                          (agent_data['completed_tasks'] + agent_data['failed_tasks'])) * 100
            
            # Check for high retry rate
            retry_rate = (agent_data.get('retried_tasks', 0) / 
                         agent_data['completed_tasks']) * 100 if agent_data['completed_tasks'] > 0 else 0
            
            issues = []
            if failure_rate > 10:  # More than 10% failure rate
                issues.append(f"high failure rate ({failure_rate:.1f}%)")
            if retry_rate > 15:  # More than 15% retry rate
                issues.append(f"high retry rate ({retry_rate:.1f}%)")
            
            # Check for problematic task types
            problematic_tasks = []
            for task_type, task_data in agent_data.get('by_task_type', {}).items():
                task_failure_rate = (task_data.get('failed', 0) / 
                                   (task_data.get('completed', 0) + task_data.get('failed', 1))) * 100
                if task_failure_rate > 20:  # More than 20% failure rate for a task type
                    problematic_tasks.append(f"{task_type} ({task_failure_rate:.1f}% failure)")
            
            if issues or problematic_tasks:
                issues_found = True
                output.append(f"🔴 {color_text(agent_id, 'BOLD')}:")
                if issues:
                    output.append(f"  • Issues: {', '.join(issues)}")
                if problematic_tasks:
                    output.append(f"  • Problematic tasks: {', '.join(problematic_tasks)}")
                output.append("")
        
        if not issues_found:
            output.append("✅ No significant issues detected across agents.")
        
        return "\n".join(output)
    
    def export_report(self, output_dir: str = "insights") -> str:
        """Export a detailed report to a file."""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_dir / f"agent_insights_{timestamp}.md"
        
        # Generate report sections
        sections = [
            "# Agent Performance Insights Report\n",
            f"Generated: {datetime.now().isoformat()}\n",
            "## 📊 Performance Summary\n",
            self.get_summary().replace("\033[95m", "**").replace("\033[0m", "**"),
            "\n## 🎯 Task Type Recommendations\n"
        ]
        
        # Add recommendations for each task type
        for task_type in self.data.get('task_types', []):
            sections.append(f"### {task_type.capitalize()} Tasks\n")
            sections.append(
                self.get_recommendation(task_type)
                .replace("\033[95m", "**")
                .replace("\033[0m", "**")
                .replace("\033[92m", "✅ ")
                .replace("\033[93m", "⚠️ ")
                .replace("\033[91m", "❌ ")
                .replace("\033[1m", "**")
                .replace("\033[0m", "**")
            )
            sections.append("")
        
        # Add error analysis
        sections.extend([
            "## ⚠️ Error Analysis\n",
            self.get_error_analysis()
                .replace("\033[95m", "**")
                .replace("\033[0m", "**")
                .replace("🔴 ", "### ")
                .replace("\033[1m", "**")
                .replace("\033[0m", "**")
        ])
        
        # Write to file
        with open(report_path, 'w') as f:
            f.write("\n".join(sections))
        
        return f"✅ Report exported to {report_path}"

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description='Agent Learning CLI - View and analyze agent performance metrics.'
    )
    parser.add_argument(
        '--snapshot', 
        default='agent_learning_snapshot.json',
        help='Path to agent learning snapshot JSON file'
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Summary command
    summary_parser = subparsers.add_parser('summary', help='Show agent performance summary')
    
    # Recommend command
    recommend_parser = subparsers.add_parser('recommend', help='Get agent recommendations')
    recommend_parser.add_argument('task_type', help='Type of task to get recommendations for')
    
    # Errors command
    errors_parser = subparsers.add_parser('errors', help='Show agent error analysis')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export detailed report')
    export_parser.add_argument(
        '--output-dir', 
        default='insights',
        help='Directory to save the report (default: insights/)'
    )
    
    args = parser.parse_args()
    
    cli = AgentLearningCLI(args.snapshot)
    
    if args.command == 'summary':
        print(cli.get_summary())
    elif args.command == 'recommend':
        print(cli.get_recommendation(args.task_type))
    elif args.command == 'errors':
        print(cli.get_error_analysis())
    elif args.command == 'export':
        print(cli.export_report(args.output_dir))
    else:
        # Default to summary if no command provided
        print(cli.get_summary())
        print("\nUse --help for more options and commands.")

if __name__ == "__main__":
    main()
