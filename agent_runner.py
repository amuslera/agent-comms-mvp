#!/usr/bin/env python3
"""
Agent Runner CLI tool for the agent-comms-mvp system.
Reads tasks from agent inbox, validates messages, simulates execution,
and updates task logs and outbox with status messages.
"""

import json
import argparse
import sys
import uuid
from datetime import datetime
from pathlib import Path
from jsonschema import validate, ValidationError


def load_json_file(filepath):
    """Load JSON content from a file."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found - {filepath}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {filepath} - {e}")
        sys.exit(1)


def save_json_file(filepath, data):
    """Save JSON content to a file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def validate_message(message, schema):
    """Validate a message against the exchange protocol schema."""
    try:
        validate(instance=message, schema=schema)
        return True, None
    except ValidationError as e:
        return False, str(e)


def simulate_task_execution(message):
    """Simulate task execution and return execution result."""
    print(f"\n🚀 Executing task from {message['sender']}...")
    print(f"   Message ID: {message['id']}")
    print(f"   Type: {message['type']}")
    
    if message['type'] == 'task_assignment':
        task_id = message['content']['task_id']
        description = message['content']['description']
        print(f"   Task ID: {task_id}")
        print(f"   Description: {description}")
        print(f"   Priority: {message['content']['priority']}")
        print(f"   Deadline: {message['content']['deadline']}")
        
        # Simulate successful execution
        print(f"   ✅ Task {task_id} executed successfully (simulated)")
        return True, f"Task {task_id} completed successfully (simulated execution)"
    
    else:
        print(f"   ℹ️  Processing {message['type']} message")
        return True, f"Message {message['id']} processed successfully"


def append_to_task_log(agent, message, success, details):
    """Append an entry to the agent's task log."""
    log_path = Path(f"postbox/{agent}/task_log.md")
    
    # Ensure the file exists
    if not log_path.exists():
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, 'w') as f:
            f.write(f"# Task Log - {agent}\n\n")
    
    timestamp = datetime.now().isoformat()
    status_icon = "✅" if success else "❌"
    
    log_entry = f"\n## {timestamp}\n"
    log_entry += f"**Status**: {status_icon} {'Success' if success else 'Failed'}\n"
    log_entry += f"**Message ID**: {message['id']}\n"
    log_entry += f"**From**: {message['sender']}\n"
    log_entry += f"**Type**: {message['type']}\n"
    
    if message['type'] == 'task_assignment':
        log_entry += f"**Task ID**: {message['content']['task_id']}\n"
    
    log_entry += f"**Details**: {details}\n"
    
    with open(log_path, 'a') as f:
        f.write(log_entry)
    
    print(f"   📝 Updated task log: {log_path}")


def create_status_message(agent, original_message, success, details):
    """Create a task status message for the outbox."""
    status_message = {
        "type": "task_status",
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "sender": agent,
        "recipient": original_message['sender'],
        "version": "1.0.0",
        "content": {
            "task_id": original_message['content'].get('task_id', 'N/A'),
            "status": "completed" if success else "failed",
            "progress": 100 if success else 0,
            "details": details
        },
        "metadata": {
            "protocol_version": "1.0.0",
            "original_message_id": original_message['id']
        }
    }
    
    return status_message


def process_inbox(agent, schema, simulate=True, clear=False):
    """Process all messages in the agent's inbox."""
    inbox_path = Path(f"postbox/{agent}/inbox.json")
    outbox_path = Path(f"postbox/{agent}/outbox.json")
    
    # Load inbox messages
    messages = load_json_file(inbox_path)
    
    if not messages:
        print(f"No messages in {agent}'s inbox")
        return
    
    print(f"Processing {len(messages)} message(s) from {agent}'s inbox...")
    
    # Load current outbox
    outbox = load_json_file(outbox_path)
    
    processed_messages = []
    
    for message in messages:
        print(f"\n{'='*50}")
        print(f"Processing message {message['id']}...")
        
        # Validate message
        valid, error = validate_message(message, schema)
        
        if not valid:
            print(f"   ❌ Validation failed: {error}")
            append_to_task_log(agent, message, False, f"Validation error: {error}")
            
            # Create error message for outbox
            error_message = {
                "type": "error",
                "id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "sender": agent,
                "recipient": message['sender'],
                "version": "1.0.0",
                "content": {
                    "error_code": "INVALID_MESSAGE",
                    "message": f"Message validation failed: {error}",
                    "context": {
                        "original_message_id": message['id']
                    }
                },
                "metadata": {
                    "protocol_version": "1.0.0"
                }
            }
            outbox.append(error_message)
            continue
        
        print("   ✓ Message validated successfully")
        
        # Simulate task execution
        if simulate:
            success, details = simulate_task_execution(message)
        else:
            print("   ⚠️  Real execution not implemented (using simulation)")
            success, details = simulate_task_execution(message)
        
        # Log the execution result
        append_to_task_log(agent, message, success, details)
        
        # Create status message for outbox
        if message['type'] == 'task_assignment':
            status_message = create_status_message(agent, message, success, details)
            outbox.append(status_message)
            print(f"   📤 Added status message to outbox")
        
        processed_messages.append(message)
    
    # Save updated outbox
    save_json_file(outbox_path, outbox)
    print(f"\n✅ Updated outbox with {len(outbox)} message(s)")
    
    # Clear inbox if requested
    if clear:
        save_json_file(inbox_path, [])
        print(f"🗑️  Cleared {agent}'s inbox")
    else:
        # Remove processed messages from inbox
        remaining_messages = [m for m in messages if m not in processed_messages]
        save_json_file(inbox_path, remaining_messages)
        print(f"📥 {len(remaining_messages)} message(s) remaining in inbox")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Agent Runner - Execute tasks from agent inbox"
    )
    parser.add_argument(
        "--agent",
        required=True,
        choices=["CC", "CA", "WA", "ARCH"],
        help="Agent identifier to run tasks for"
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        default=True,
        help="Simulate task execution (default: True)"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear inbox after processing messages"
    )
    
    args = parser.parse_args()
    
    # Load exchange protocol schema
    schema_path = Path("exchange_protocol.json")
    schema = load_json_file(schema_path)
    
    print(f"🤖 Agent Runner - Processing inbox for {args.agent}")
    print(f"   Mode: {'Simulation' if args.simulate else 'Real execution'}")
    print(f"   Clear inbox: {args.clear}")
    
    # Process the inbox
    process_inbox(args.agent, schema, args.simulate, args.clear)
    
    print("\n✨ Agent Runner completed successfully")


if __name__ == "__main__":
    main()