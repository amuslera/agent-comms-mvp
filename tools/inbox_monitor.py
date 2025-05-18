#!/usr/bin/env python3
"""
Inbox Monitor - CLI tool for monitoring and inspecting agent inboxes.

This tool allows users to view and inspect messages in agent inboxes.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Base directory for agent communication
BASE_DIR = Path(__file__).parent.parent / "postbox"
CONTEXTS_DIR = Path(__file__).parent.parent / "contexts"

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
    'UNDERLINE': '\033[4m',
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

def load_messages(agent: str) -> List[Dict[str, Any]]:
    """Load messages from an agent's inbox."""
    inbox_path = BASE_DIR / agent / "inbox.json"
    if not inbox_path.exists():
        return []
    
    try:
        with open(inbox_path, 'r') as f:
            messages = json.load(f)
            if not isinstance(messages, list):
                return []
            return messages
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading {inbox_path}: {e}", file=sys.stderr)
        return []

def format_timestamp(timestamp: str) -> str:
    """Format ISO timestamp to a more readable format."""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S %Z')
    except (ValueError, AttributeError):
        return timestamp

def display_message_summary(message: Dict[str, Any], index: int) -> None:
    """Display a summary of a message."""
    msg_id = message.get('id', 'N/A')
    msg_type = message.get('type', 'unknown')
    sender = message.get('sender', 'unknown')
    timestamp = format_timestamp(message.get('timestamp', 'N/A'))
    
    # Add color to different message types
    if msg_type == 'task_assignment':
        msg_type = color_text(msg_type, 'GREEN')
    elif msg_type == 'task_status':
        msg_type = color_text(msg_type, 'BLUE')
    elif msg_type == 'error':
        msg_type = color_text(msg_type, 'FAIL')
    
    print(f"{color_text(f'[{index}]', 'BOLD')} {msg_type}")
    print(f"  From: {color_text(sender, 'CYAN')}")
    print(f"  ID: {color_text(msg_id, 'CYAN')}")
    print(f"  Time: {color_text(timestamp, 'CYAN')}")
    
    # Show task-specific summary
    content = message.get('content', {})
    if 'task_id' in content:
        print(f"  Task: {color_text(content['task_id'], 'BOLD')}")
    if 'description' in content:
        desc = content['description']
        if len(desc) > 60:
            desc = desc[:57] + '...'
        print(f"  Description: {desc}")
    
    print()  # Add spacing between messages

def display_message_detail(message: Dict[str, Any]) -> None:
    """Display detailed view of a message."""
    print(color_text("\n=== Message Details ===\n", 'HEADER'))
    
    # Basic message info
    print(color_text("Message ID:", 'BOLD'), message.get('id', 'N/A'))
    print(color_text("Type:", 'BOLD'), message.get('type', 'unknown'))
    print(color_text("From:", 'BOLD'), message.get('sender', 'unknown'))
    print(color_text("To:", 'BOLD'), message.get('recipient', 'unknown'))
    print(color_text("Timestamp:", 'BOLD'), format_timestamp(message.get('timestamp', 'N/A')))
    print(color_text("Version:", 'BOLD'), message.get('version', 'N/A'))
    
    # Content section
    print("\n" + color_text("Content:", 'BOLD'))
    print(json.dumps(message.get('content', {}), indent=2))
    
    # Metadata if present
    if 'metadata' in message and message['metadata']:
        print("\n" + color_text("Metadata:", 'BOLD'))
        print(json.dumps(message['metadata'], indent=2))

def get_agent_prompt(agent: str) -> Optional[str]:
    """Get the agent's prompt from their profile."""
    profile_path = CONTEXTS_DIR / f"{agent}_PROFILE.md"
    if not profile_path.exists():
        return None
    
    try:
        with open(profile_path, 'r') as f:
            return f.read()
    except IOError:
        return None

def simulate_processing(message: Dict[str, Any], agent: str) -> None:
    """Simulate processing a message (preview only)."""
    print(color_text("\n=== Processing Simulation ===\n", 'HEADER'))
    
    msg_type = message.get('type', 'unknown')
    content = message.get('content', {})
    
    print(f"Agent {color_text(agent, 'BOLD')} would process this {color_text(msg_type, 'BOLD')} message:")
    
    if msg_type == 'task_assignment':
        task_id = content.get('task_id', 'N/A')
        print(f"  • Task ID: {color_text(task_id, 'CYAN')}")
        print(f"  • Priority: {content.get('priority', 'N/A')}")
        print(f"  • Deadline: {content.get('deadline', 'N/A')}")
        
        if 'requirements' in content and content['requirements']:
            print("  • Requirements:")
            for req in content['requirements']:
                print(f"    - {req}")
    
    elif msg_type == 'task_status':
        print(f"  • Status: {color_text(content.get('status', 'N/A'), 'BLUE')}")
        print(f"  • Progress: {content.get('progress', 'N/A')}%")
        print(f"  • Details: {content.get('details', 'No details')}")
    
    elif msg_type == 'error':
        print(f"  • Error Code: {color_text(content.get('error_code', 'N/A'), 'FAIL')}")
        print(f"  • Message: {content.get('message', 'No message')}")
    
    # Show agent's prompt if available
    prompt = get_agent_prompt(agent)
    if prompt:
        print("\n" + color_text("Agent's Prompt:", 'BOLD'))
        print("---")
        print("\n".join(prompt.split('\n')[:10]) + "\n...")
        print("---")
    
    print("\n" + color_text("Note: This is a simulation. No actual processing occurred.", 'WARNING'))

def interactive_mode(agent: str) -> None:
    """Run the interactive inbox monitor."""
    messages = load_messages(agent)
    
    if not messages:
        print(f"No messages found in {agent}'s inbox.")
        return
    
    print(f"\n{color_text(f'=== {agent} Inbox ===', 'HEADER')}\n")
    
    # Display message list
    for i, msg in enumerate(messages):
        display_message_summary(msg, i)
    
    # Main interaction loop
    while True:
        try:
            print("\nOptions:")
            print("  [0-9] - View message details")
            print("  p [0-9] - Simulate processing message")
            print("  r - Refresh inbox")
            print("  q - Quit")
            
            choice = input("\nEnter your choice: ").strip().lower()
            
            if choice == 'q':
                break
            
            elif choice == 'r':
                messages = load_messages(agent)
                print("\nInbox refreshed.")
                for i, msg in enumerate(messages):
                    display_message_summary(msg, i)
            
            elif choice.startswith('p '):
                # Process simulation
                try:
                    idx = int(choice[2:])
                    if 0 <= idx < len(messages):
                        simulate_processing(messages[idx], agent)
                    else:
                        print("Invalid message number.")
                except (ValueError, IndexError):
                    print("Invalid input. Use 'p [number]' to simulate processing.")
            
            elif choice.isdigit():
                # View message details
                idx = int(choice)
                if 0 <= idx < len(messages):
                    display_message_detail(messages[idx])
                else:
                    print("Invalid message number.")
            
            else:
                print("Invalid choice. Please try again.")
        
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            break

def main():
    """Main entry point for the inbox monitor."""
    parser = argparse.ArgumentParser(description='Monitor agent inboxes.')
    parser.add_argument('--agent', '-a', 
                       help='Filter by agent ID (e.g., WA, CA, CC)')
    parser.add_argument('--list', '-l', action='store_true',
                       help='List messages and exit')
    parser.add_argument('--message', '-m', type=int,
                       help='View specific message by index')
    
    args = parser.parse_args()
    
    # Get available agents
    agents = get_available_agents()
    
    if not agents:
        print("No agent directories found.")
        return
    
    # If no agent specified, show agent selection
    if not args.agent:
        print("Available agents:")
        for i, agent in enumerate(agents, 1):
            print(f"  {i}. {agent}")
        
        try:
            choice = input("\nSelect an agent (number or ID), or 'q' to quit: ").strip().lower()
            if choice == 'q':
                return
            
            if choice.isdigit() and 1 <= int(choice) <= len(agents):
                agent = agents[int(choice) - 1]
            elif choice in agents:
                agent = choice
            else:
                print("Invalid selection.")
                return
        except (KeyboardInterrupt, EOFError):
            print("\nOperation cancelled.")
            return
    else:
        agent = args.agent.upper()
        if agent not in agents:
            print(f"Agent {agent} not found. Available agents: {', '.join(agents)}")
            return
    
    # Load messages
    messages = load_messages(agent)
    
    if not messages:
        print(f"No messages found in {agent}'s inbox.")
        return
    
    # Handle different modes
    if args.list:
        # List mode - just show message summaries
        print(f"\n{color_text(f'=== {agent} Inbox ({len(messages)} messages) ===', 'HEADER')}\n")
        for i, msg in enumerate(messages):
            display_message_summary(msg, i)
    
    elif args.message is not None:
        # View specific message
        if 0 <= args.message < len(messages):
            display_message_detail(messages[args.message])
        else:
            print(f"Message index out of range. Valid range: 0-{len(messages)-1}")
    
    else:
        # Interactive mode
        interactive_mode(agent)

if __name__ == "__main__":
    main()
