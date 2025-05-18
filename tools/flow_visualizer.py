#!/usr/bin/env python3
"""
Outbox message flow visualizer.

This script scans all agent outbox.json files and generates a timeline
of message flows between agents, showing task assignments, status updates,
and other message types.
"""

import json
import glob
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict


def load_outbox_messages() -> List[Dict[str, Any]]:
    """
    Load all messages from agent outbox files.
    
    Returns:
        List of messages with their source agent
    """
    messages = []
    
    # Find all outbox.json files
    outbox_files = glob.glob("postbox/*/outbox.json")
    
    for outbox_file in outbox_files:
        agent_id = Path(outbox_file).parent.name
        
        try:
            with open(outbox_file, 'r') as f:
                agent_messages = json.load(f)
                
            # Add source agent to each message
            for msg in agent_messages:
                msg['source_agent'] = agent_id
                messages.append(msg)
                
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error reading {outbox_file}: {e}")
            continue
    
    return messages


def format_timestamp(iso_timestamp: str) -> str:
    """Format ISO timestamp to HH:MM format."""
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        return dt.strftime("%H:%M")
    except ValueError:
        return iso_timestamp


def format_message_flow(msg: Dict[str, Any]) -> str:
    """
    Format a single message into a timeline entry.
    
    Format: [HH:MM] SENDER → RECIPIENT | TASK-ID | MESSAGE-TYPE: STATUS
    """
    timestamp = format_timestamp(msg['timestamp'])
    sender = msg['source_agent']
    recipient = msg['recipient']
    msg_type = msg['type']
    
    # Get task ID from content if available
    task_id = msg.get('content', {}).get('task_id', 'N/A')
    
    # Get status for task_status messages
    status = ""
    if msg_type == "task_status":
        status = f": {msg['content'].get('status', 'unknown')}"
    
    return f"[{timestamp}] {sender} → {recipient} | {task_id} | {msg_type}{status}"


def group_messages_by_task(messages: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group messages by their task ID for better visualization."""
    task_groups = defaultdict(list)
    
    for msg in messages:
        task_id = msg.get('content', {}).get('task_id', 'N/A')
        task_groups[task_id].append(msg)
    
    return task_groups


def visualize_message_flow() -> None:
    """Main function to visualize message flows."""
    print("\n📨 Agent Communication Timeline\n")
    
    # Load and sort messages by timestamp
    messages = load_outbox_messages()
    messages.sort(key=lambda x: x['timestamp'])
    
    # Group messages by task
    task_groups = group_messages_by_task(messages)
    
    # Print timeline
    for task_id, task_messages in task_groups.items():
        print(f"\nTask: {task_id}")
        print("-" * 80)
        
        for msg in task_messages:
            print(format_message_flow(msg))
    
    # Print summary
    print("\n📊 Summary")
    print("-" * 80)
    print(f"Total messages: {len(messages)}")
    print(f"Total tasks: {len(task_groups)}")
    
    # Count message types
    msg_types = defaultdict(int)
    for msg in messages:
        msg_types[msg['type']] += 1
    
    print("\nMessage Types:")
    for msg_type, count in msg_types.items():
        print(f"- {msg_type}: {count}")


if __name__ == "__main__":
    visualize_message_flow() 