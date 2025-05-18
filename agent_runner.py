#!/usr/bin/env python3
"""
Agent Runner CLI tool for the agent-comms-mvp system.
Reads tasks from agent inbox, validates messages, simulates execution,
and updates task logs and outbox with status messages.
Supports dependency-aware execution with depends_on metadata.
"""

import json
import argparse
import sys
import uuid
from datetime import datetime
from pathlib import Path
from jsonschema import validate, ValidationError
import glob
import re


def load_text_file(filepath):
    """Load text content from a file."""
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: File not found - {filepath}")
        return None
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
        return None


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


def check_task_completed(task_id):
    """Check if a task is marked as completed by searching outboxes and task logs."""
    # Check all agent outboxes for task_status messages
    outbox_files = glob.glob("postbox/*/outbox.json")
    
    for outbox_file in outbox_files:
        try:
            with open(outbox_file, 'r') as f:
                messages = json.load(f)
                
            for msg in messages:
                if (msg.get('type') == 'task_status' and 
                    msg.get('content', {}).get('task_id') == task_id and
                    msg.get('content', {}).get('status') == 'completed'):
                    return True
        except (json.JSONDecodeError, FileNotFoundError):
            continue
    
    # Check all task logs for completed status
    log_files = glob.glob("postbox/*/task_log.md")
    
    for log_file in log_files:
        try:
            with open(log_file, 'r') as f:
                content = f.read()
                
            # Look for completed task entries
            if re.search(f"\\*\\*Task ID\\*\\*: {re.escape(task_id)}.*?\\*\\*Status\\*\\*:.*?Success", 
                        content, re.DOTALL):
                return True
        except FileNotFoundError:
            continue
    
    return False


def check_dependencies_met(message):
    """Check if all dependencies for a task are met."""
    depends_on = message.get('metadata', {}).get('depends_on', [])
    
    if not depends_on:
        return True, []
    
    missing_deps = []
    for dep_task_id in depends_on:
        if not check_task_completed(dep_task_id):
            missing_deps.append(dep_task_id)
    
    return len(missing_deps) == 0, missing_deps


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


def process_inbox(agent, schema, simulate=True, clear=False, force=False):
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
        
        # Check dependencies
        if message['type'] == 'task_assignment' and not force:
            deps_met, missing_deps = check_dependencies_met(message)
            
            if not deps_met:
                print(f"   ⏸️  Task has unmet dependencies: {missing_deps}")
                reason = f"Task deferred - waiting for dependencies: {', '.join(missing_deps)}"
                append_to_task_log(agent, message, False, reason)
                
                # Create status message for deferred task
                status_message = {
                    "type": "task_status",
                    "id": str(uuid.uuid4()),
                    "timestamp": datetime.now().isoformat(),
                    "sender": agent,
                    "recipient": message['sender'],
                    "version": "1.0.0",
                    "content": {
                        "task_id": message['content'].get('task_id', 'N/A'),
                        "status": "deferred",
                        "progress": 0,
                        "details": reason
                    },
                    "metadata": {
                        "protocol_version": "1.0.0",
                        "original_message_id": message['id'],
                        "missing_dependencies": missing_deps
                    }
                }
                outbox.append(status_message)
                print(f"   📤 Added deferred status to outbox")
                continue
        
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


def agent_init(agent):
    """Initialize an agent by loading and displaying their configuration files."""
    print(f"🤖 Initializing agent {agent}...")
    print(f"\n{'=' * 60}")
    
    # Define file paths based on agent name
    profile_path = Path(f"contexts/{agent}_PROFILE.md")
    prompt_paths = {
        "CC": Path("prompts/Claude_Code_PROMPT_TEMPLATE.md"),
        "CA": Path("prompts/Cursor_AI_PROMPT_TEMPLATE.md"),
        "WA": Path("prompts/Web_Assistant_PROMPT_TEMPLATE.md"),
        "ARCH": None  # ARCH doesn't have a prompt template
    }
    context_path = Path("CONTEXT_agent_comms.md")
    
    # Load agent profile
    print(f"\n📋 Agent Profile ({profile_path})")
    print("-" * 50)
    profile_content = load_text_file(profile_path)
    if profile_content:
        print(profile_content)
    else:
        print(f"❌ Could not load agent profile")
    
    # Load prompt template if available
    if agent in prompt_paths and prompt_paths[agent]:
        print(f"\n📝 Prompt Template ({prompt_paths[agent]})")
        print("-" * 50)
        prompt_content = load_text_file(prompt_paths[agent])
        if prompt_content:
            # Print first 500 characters as a preview
            print(prompt_content[:500] + "..." if len(prompt_content) > 500 else prompt_content)
        else:
            print(f"❌ Could not load prompt template")
    else:
        print(f"\n📝 No prompt template available for {agent}")
    
    # Load shared context
    print(f"\n🌐 Shared Context ({context_path})")
    print("-" * 50)
    context_content = load_text_file(context_path)
    if context_content:
        # Extract agent-specific section from context
        agent_sections = {
            "CC": "### Code Creator (CC)",
            "CA": "### Cursor AI (CA)",
            "WA": "### Web Assistant (WA)",
            "ARCH": "### Architect (ARCH)"
        }
        
        if agent in agent_sections:
            section_start = context_content.find(agent_sections[agent])
            if section_start != -1:
                # Find the next section or end of agent roles
                next_section = context_content.find("###", section_start + 1)
                communication_section = context_content.find("## Communication Model")
                end_point = min(filter(lambda x: x > section_start, 
                                     [next_section if next_section != -1 else len(context_content),
                                      communication_section if communication_section != -1 else len(context_content)]))
                
                agent_section = context_content[section_start:end_point].strip()
                print(agent_section)
            else:
                print(f"Could not find section for {agent} in context file")
        else:
            print(f"Unknown agent: {agent}")
    else:
        print(f"❌ Could not load shared context")
    
    print(f"\n{'=' * 60}")
    print(f"✅ Agent {agent} initialization complete")
    print(f"\nExpected behavior:")
    print(f"- Check inbox at: postbox/{agent}/inbox.json")
    print(f"- Send responses to: postbox/{agent}/outbox.json")
    print(f"- Log activities in: postbox/{agent}/task_log.md")
    print(f"- Validate messages using: exchange_protocol.json")
    print(f"\nRun 'python agent_runner.py --agent {agent}' to process inbox")


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
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize agent by displaying role, capabilities, and expected behavior"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force task execution, ignoring dependency checks"
    )
    
    args = parser.parse_args()
    
    # If --init flag is provided, run initialization instead
    if args.init:
        agent_init(args.agent)
        return
    
    # Otherwise, proceed with normal inbox processing
    # Load exchange protocol schema
    schema_path = Path("exchange_protocol.json")
    schema = load_json_file(schema_path)
    
    print(f"🤖 Agent Runner - Processing inbox for {args.agent}")
    print(f"   Mode: {'Simulation' if args.simulate else 'Real execution'}")
    print(f"   Clear inbox: {args.clear}")
    print(f"   Force execution: {args.force}")
    
    # Process the inbox
    process_inbox(args.agent, schema, args.simulate, args.clear, args.force)
    
    print("\n✨ Agent Runner completed successfully")


if __name__ == "__main__":
    main()