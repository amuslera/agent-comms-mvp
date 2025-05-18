#!/usr/bin/env python3
"""
Task Dispatcher - CLI tool for injecting tasks into agent inboxes.

This tool allows users to create and send structured tasks to agent inboxes
following the agent communication protocol.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

# Protocol version
PROTOCOL_VERSION = "1.0.0"

# Base directory for agent communication
BASE_DIR = Path(__file__).parent.parent / "postbox"

# Example task template
EXAMPLE_TASK = {
    "type": "task_assignment",
    "content": {
        "task_id": "TASK-XXX",
        "description": "Task description here",
        "priority": 1,
        "deadline": "2024-01-01T00:00:00Z",
        "requirements": ["file1.txt"]
    }
}


def generate_message_id() -> str:
    """Generate a UUID v4 string."""
    return str(uuid.uuid4())


def get_current_timestamp() -> str:
    """Get current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def get_agent_directories() -> list[str]:
    """Get list of available agent directories."""
    if not BASE_DIR.exists():
        return []
    return [d.name for d in BASE_DIR.iterdir() if d.is_dir()]


def validate_recipient(recipient: str) -> bool:
    """Check if recipient directory exists."""
    return (BASE_DIR / recipient).exists()


def get_task_from_user() -> Dict[str, Any]:
    """Prompt user for task details."""
    print("\nEnter task details (press Enter to use default values):")
    
    task_type = input(f"Task type [task_assignment]: ") or "task_assignment"
    task_id = input(f"Task ID [TASK-{datetime.now().strftime('%Y%m%d')}]: ") or f"TASK-{datetime.now().strftime('%Y%m%d')}"
    description = input("Description: ") or "No description provided"
    priority = int(input("Priority (1-5) [3]: ") or "3")
    deadline = input(f"Deadline (YYYY-MM-DD) [{(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')}]: ") or (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Convert deadline to ISO format with timezone
    try:
        deadline_dt = datetime.strptime(deadline, '%Y-%m-%d')
        deadline_iso = deadline_dt.replace(tzinfo=timezone.utc).isoformat()
    except ValueError:
        print("Invalid date format. Using default (tomorrow).")
        deadline_iso = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    
    requirements = []
    print("\nEnter requirements (one per line, empty line to finish):")
    while True:
        req = input("Requirement: ").strip()
        if not req:
            break
        requirements.append(req)
    
    return {
        "type": task_type,
        "content": {
            "task_id": task_id,
            "description": description,
            "priority": priority,
            "deadline": deadline_iso,
            "requirements": requirements
        }
    }


def create_message(task: Dict[str, Any], sender: str, recipient: str) -> Dict[str, Any]:
    """Create a properly formatted message."""
    return {
        "type": task["type"],
        "id": generate_message_id(),
        "timestamp": get_current_timestamp(),
        "sender": sender,
        "recipient": recipient,
        "version": PROTOCOL_VERSION,
        "content": task["content"]
    }


def write_to_inbox(recipient: str, message: Dict[str, Any]) -> bool:
    """Write message to recipient's inbox."""
    try:
        inbox_path = BASE_DIR / recipient / "inbox.json"
        
        # Create directory if it doesn't exist
        inbox_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Read existing messages or initialize empty list
        if inbox_path.exists():
            with open(inbox_path, 'r') as f:
                try:
                    messages = json.load(f)
                    if not isinstance(messages, list):
                        messages = []
                except json.JSONDecodeError:
                    messages = []
        else:
            messages = []
        
        # Add new message
        messages.append(message)
        
        # Write back to file
        with open(inbox_path, 'w') as f:
            json.dump(messages, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error writing to inbox: {e}")
        return False

def main():
    """Main CLI entry point."""
    print("🚀 Task Dispatcher - Send tasks to agent inboxes\n")
    
    # Get available agents
    agents = get_agent_directories()
    if not agents:
        print(f"❌ No agent directories found in {BASE_DIR}")
        return
    
    print("Available agents:")
    for i, agent in enumerate(agents, 1):
        print(f"  {i}. {agent}")
    
    # Select recipient
    while True:
        try:
            choice = int(input("\nSelect recipient (number): "))
            if 1 <= choice <= len(agents):
                recipient = agents[choice - 1]
                break
            print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a number.")
    
    # Get sender (default to 'user')
    sender = input(f"\nYour name [user]: ") or "user"
    
    # Get task details
    use_example = input("\nUse example task? (y/n) [n]: ").lower() == 'y'
    if use_example:
        task = EXAMPLE_TASK
        print("\nUsing example task:")
        print(json.dumps(task, indent=2))
    else:
        task = get_task_from_user()
    
    # Create and send message
    message = create_message(task, sender, recipient)
    
    print("\nSending message:")
    print(json.dumps(message, indent=2))
    
    if write_to_inbox(recipient, message):
        print(f"\n✅ Message sent to {recipient}'s inbox!")
    else:
        print("\n❌ Failed to send message.")


if __name__ == "__main__":
    from datetime import timedelta  # Moved here to avoid circular import
    main()
