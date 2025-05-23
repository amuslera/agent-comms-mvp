#!/usr/bin/env python3
"""
Outbox Summary CLI Tool for Bluelabel Agent OS

Usage:
  bluelabel outbox-summary [--agent AGENT] [--json]

Summarizes agent output logs across the /postbox/ directory with:
- Task completion counts per agent
- Common errors and warnings
- Incomplete tasks
- Time estimates
- Unusual gaps between tasks

Options:
  --agent AGENT  Filter to specific agent (e.g., CC, CA, WA)
  --json         Emit machine-readable summary
"""
import argparse
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

def parse_timestamp(ts: str) -> datetime:
    """Parse timestamp string into datetime object."""
    try:
        return datetime.fromisoformat(ts.replace('Z', '+00:00'))
    except ValueError:
        return datetime.fromisoformat(ts)

def analyze_outbox(outbox_path: Path) -> Dict[str, Any]:
    """Analyze a single agent's outbox file."""
    with open(outbox_path) as f:
        messages = json.load(f)
    
    agent = outbox_path.parent.name
    task_completions = []
    errors = []
    warnings = []
    incomplete = []
    timestamps = []
    
    for msg in messages:
        # Track timestamps for gap analysis
        if 'timestamp' in msg:
            timestamps.append(parse_timestamp(msg['timestamp']))
        
        # Track task completions
        if msg.get('type') == 'task_status' and msg.get('content', {}).get('status') == 'completed':
            task_completions.append(msg['content']['task_id'])
        
        # Track errors
        if msg.get('type') == 'error':
            errors.append(msg.get('content', {}).get('message', 'Unknown error'))
        
        # Track warnings
        if msg.get('type') == 'task_report' and 'warning' in msg.get('summary', '').lower():
            warnings.append(msg.get('summary'))
        
        # Track incomplete tasks
        if msg.get('type') == 'task_status' and msg.get('content', {}).get('status') != 'completed':
            incomplete.append(msg['content']['task_id'])
    
    # Analyze time gaps
    gaps = []
    if len(timestamps) > 1:
        timestamps.sort()
        for i in range(1, len(timestamps)):
            gap = timestamps[i] - timestamps[i-1]
            if gap > timedelta(hours=1):  # Flag gaps > 1 hour
                gaps.append({
                    'start': timestamps[i-1].isoformat(),
                    'end': timestamps[i].isoformat(),
                    'duration_hours': gap.total_seconds() / 3600
                })
    
    return {
        'agent': agent,
        'task_completions': task_completions,
        'completion_count': len(task_completions),
        'errors': errors,
        'warnings': warnings,
        'incomplete_tasks': incomplete,
        'unusual_gaps': gaps
    }

def summarize_outboxes(postbox_dir: Path, agent_filter: Optional[str] = None) -> Dict[str, Any]:
    """Summarize all agent outboxes in the postbox directory."""
    agent_summaries = {}
    all_errors = defaultdict(int)
    all_warnings = defaultdict(int)
    
    # Find all agent outbox files
    for agent_dir in postbox_dir.iterdir():
        if not agent_dir.is_dir():
            continue
        if agent_filter and agent_dir.name != agent_filter:
            continue
            
        outbox_path = agent_dir / 'outbox.json'
        if not outbox_path.exists():
            continue
            
        summary = analyze_outbox(outbox_path)
        agent_summaries[agent_dir.name] = summary
        
        # Aggregate errors and warnings
        for error in summary['errors']:
            all_errors[error] += 1
        for warning in summary['warnings']:
            all_warnings[warning] += 1
    
    # Calculate overall statistics
    total_completions = sum(s['completion_count'] for s in agent_summaries.values())
    total_incomplete = sum(len(s['incomplete_tasks']) for s in agent_summaries.values())
    
    return {
        'agent_summaries': agent_summaries,
        'total_completions': total_completions,
        'total_incomplete': total_incomplete,
        'common_errors': dict(sorted(all_errors.items(), key=lambda x: x[1], reverse=True)[:5]),
        'common_warnings': dict(sorted(all_warnings.items(), key=lambda x: x[1], reverse=True)[:5])
    }

def format_summary(summary: Dict[str, Any], as_json: bool = False) -> str:
    """Format the summary for display."""
    if as_json:
        return json.dumps(summary, indent=2)
    
    output = []
    output.append("\nOutbox Summary:")
    output.append(f"Total task completions: {summary['total_completions']}")
    output.append(f"Total incomplete tasks: {summary['total_incomplete']}")
    
    output.append("\nPer-Agent Summary:")
    for agent, agent_summary in summary['agent_summaries'].items():
        output.append(f"\n{agent}:")
        output.append(f"  Completed tasks: {agent_summary['completion_count']}")
        if agent_summary['incomplete_tasks']:
            output.append(f"  Incomplete tasks: {', '.join(agent_summary['incomplete_tasks'])}")
        if agent_summary['errors']:
            output.append(f"  Errors: {len(agent_summary['errors'])}")
        if agent_summary['warnings']:
            output.append(f"  Warnings: {len(agent_summary['warnings'])}")
        if agent_summary['unusual_gaps']:
            output.append(f"  Unusual gaps: {len(agent_summary['unusual_gaps'])}")
    
    if summary['common_errors']:
        output.append("\nCommon Errors:")
        for error, count in summary['common_errors'].items():
            output.append(f"  {error} ({count} occurrences)")
    
    if summary['common_warnings']:
        output.append("\nCommon Warnings:")
        for warning, count in summary['common_warnings'].items():
            output.append(f"  {warning} ({count} occurrences)")
    
    return "\n".join(output)

def main():
    parser = argparse.ArgumentParser(
        description="Summarize agent output logs across the /postbox/ directory.",
        epilog="""
Examples:
  bluelabel outbox-summary
  bluelabel outbox-summary --agent CC
  bluelabel outbox-summary --json
        """
    )
    parser.add_argument('--agent', help='Filter to specific agent (e.g., CC, CA, WA)')
    parser.add_argument('--json', action='store_true', help='Emit machine-readable summary')
    args = parser.parse_args()
    
    postbox_dir = Path('/postbox')
    if not postbox_dir.exists():
        print("Error: /postbox directory not found")
        return 1
        
    summary = summarize_outboxes(postbox_dir, args.agent)
    print(format_summary(summary, args.json))
    return 0

if __name__ == '__main__':
    main() 