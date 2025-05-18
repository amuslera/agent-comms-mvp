#!/usr/bin/env python3
"""
Task Status Tracker - CLI tool for monitoring task statuses across all agents.

This tool scans agent outboxes and generates a real-time status report
of all active and completed tasks.
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Base directory for agent communication
BASE_DIR = Path(__file__).parent.parent / "postbox"

# ANSI color codes for terminal output
COLORS = {
    'HEADER': '\033[95m',
    'BLUE': '\033[94m',
    'CYAN': '\033[96m',
    'GREEN': '\033[92m',
    'WARNING': '\033[93m',
    'FAIL': '\033[91m',
    'ENDC': '\033[0m',
    'BOLD': '\033[1m',
    'DIM': '\033[2m',
    'UNDERLINE': '\033[4m',
}

# Status symbols and colors
STATUS_SYMBOLS = {
    'completed': ('✓', 'GREEN'),
    'success': ('✓', 'GREEN'),
    'failed': ('✗', 'FAIL'),
    'error': ('✗', 'FAIL'),
    'in_progress': ('↻', 'BLUE'),
    'pending': ('…', 'WARNING'),
    'cancelled': ('✕', 'DIM'),
    'default': ('?', 'WARNING')
}

def color_text(text: str, color: str) -> str:
    """Apply ANSI color to text if output is a terminal."""
    if sys.stdout.isatty() and color in COLORS:
        return f"{COLORS[color]}{text}{COLORS['ENDC']}"
    return text

def get_available_agents() -> List[str]:
    """Get list of available agent directories."""
    if not BASE_DIR.exists():
        return []
    return [d.name for d in BASE_DIR.iterdir() if d.is_dir()]

def load_outbox_messages(agent: str) -> List[Dict[str, Any]]:
    """Load messages from an agent's outbox."""
    outbox_path = BASE_DIR / agent / "outbox.json"
    if not outbox_path.exists():
        return []
    
    try:
        with open(outbox_path, 'r') as f:
            messages = json.load(f)
            if not isinstance(messages, list):
                return []
            return messages
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading {outbox_path}: {e}", file=sys.stderr)
        return []

def parse_timestamp(timestamp: str) -> datetime:
    """Parse ISO 8601 timestamp string to datetime object."""
    try:
        # Handle timezone info if present
        if timestamp.endswith('Z'):
            timestamp = timestamp[:-1] + '+00:00'
        return datetime.fromisoformat(timestamp)
    except (ValueError, TypeError):
        return datetime.min

def format_duration(dt: datetime) -> str:
    """Format duration from now to the given datetime."""
    if dt == datetime.min:
        return "unknown time ago"
    
    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    delta = now - dt
    
    if delta.days > 0:
        return f"{delta.days}d ago"
    elif delta.seconds >= 3600:
        hours = delta.seconds // 3600
        return f"{hours}h ago"
    elif delta.seconds >= 60:
        minutes = delta.seconds // 60
        return f"{minutes}m ago"
    else:
        return "just now"

def get_status_symbol(status: str) -> Tuple[str, str]:
    """Get the symbol and color for a status."""
    status_lower = status.lower()
    for key, (symbol, color) in STATUS_SYMBOLS.items():
        if key in status_lower:
            return symbol, color
    return STATUS_SYMBOLS['default']

def collect_task_statuses() -> Dict[str, List[Dict[str, Any]]]:
    """Collect task statuses from all agent outboxes."""
    tasks = defaultdict(list)
    
    for agent in get_available_agents():
        messages = load_outbox_messages(agent)
        
        for msg in messages:
            if msg.get('type') != 'task_status':
                continue
                
            content = msg.get('content', {})
            task_id = content.get('task_id')
            
            if not task_id:
                continue
                
            status = content.get('status', 'unknown').lower()
            timestamp = parse_timestamp(msg.get('timestamp', ''))
            
            tasks[task_id].append({
                'agent': agent,
                'status': status,
                'timestamp': timestamp,
                'details': content.get('details', ''),
                'progress': content.get('progress'),
                'raw_message': msg
            })
    
    # Sort each task's statuses by timestamp (newest first)
    for task_id in tasks:
        tasks[task_id].sort(key=lambda x: x['timestamp'], reverse=True)
    
    return tasks

def print_status_report(tasks: Dict[str, List[Dict[str, Any]]], show_all: bool = False) -> None:
    """Print a formatted status report of all tasks."""
    if not tasks:
        print("No task statuses found in any outbox.")
        return
    
    # Sort tasks by most recent update
    sorted_tasks = sorted(
        tasks.items(),
        key=lambda x: x[1][0]['timestamp'] if x[1] else datetime.min,
        reverse=True
    )
    
    print(color_text("\n=== Task Status Report ===\n", 'HEADER'))
    
    for task_id, statuses in sorted_tasks:
        if not statuses:
            continue
            
        latest = statuses[0]
        symbol, color = get_status_symbol(latest['status'])
        
        # Format the main status line
        time_ago = format_duration(latest['timestamp'])
        status_line = (
            f"{color_text(task_id, 'BOLD')}: "
            f"{color_text(latest['status'].title(), color)} {color_text(symbol, color)} "
            f"by {color_text(latest['agent'], 'CYAN')} {color_text(f'({time_ago})', 'DIM')}"
        )
        
        # Add progress if available
        if latest['progress'] is not None:
            progress_bar = generate_progress_bar(latest['progress'])
            status_line += f" {progress_bar} {latest['progress']}%"
        
        print(status_line)
        
        # Show details if available
        if latest['details']:
            details = latest['details']
            if len(details) > 80 and not show_all:
                details = details[:77] + '...'
            print(f"  {color_text('Details:', 'DIM')} {details}")
        
        # Show previous statuses if in verbose mode
        if show_all and len(statuses) > 1:
            print(f"  {color_text('History:', 'DIM')}")
            for status in statuses[1:]:
                symbol, _ = get_status_symbol(status['status'])
                time_ago = format_duration(status['timestamp'])
                print(f"    {status['status'].title()} {symbol} ({time_ago})")
        
        print()  # Add spacing between tasks

def generate_progress_bar(percentage: int, width: int = 20) -> str:
    """Generate a text-based progress bar."""
    filled = int(width * percentage / 100)
    bar = '█' * filled + '░' * (width - filled)
    return bar

def main():
    """Main entry point for the task status tracker."""
    parser = argparse.ArgumentParser(description='Track task statuses across all agents.')
    parser.add_argument('--all', '-a', action='store_true',
                       help='Show all details including history')
    parser.add_argument('--watch', '-w', action='store_true',
                       help='Watch mode: continuously update the status')
    parser.add_argument('--interval', '-i', type=int, default=5,
                       help='Update interval in seconds (default: 5)')
    
    args = parser.parse_args()
    
    try:
        if args.watch:
            import time
            try:
                while True:
                    # Clear screen
                    print('\033c', end='')
                    # Print header
                    print(f"{color_text('Task Status Monitor', 'HEADER')} "
                          f"{color_text('(Ctrl+C to exit)', 'DIM')}\n")
                    print(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    # Print status
                    tasks = collect_task_statuses()
                    print_status_report(tasks, args.all)
                    # Wait for next update
                    time.sleep(args.interval)
            except KeyboardInterrupt:
                print("\nMonitoring stopped.")
        else:
            tasks = collect_task_statuses()
            print_status_report(tasks, args.all)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
