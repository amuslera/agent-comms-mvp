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
import logging
from datetime import datetime
from pathlib import Path
from jsonschema import validate, ValidationError
import glob
import re

# Add the parent directory to the path so we can import context_manager
sys.path.insert(0, str(Path(__file__).parent))
from tools.context_manager import ContextManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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


def simulate_task_execution(message, agent_context=None):
    """Simulate task execution and return execution result.
    
    Args:
        message: The task message to process
        agent_context: The agent's context dictionary (may be modified)
        
    Returns:
        Tuple of (success: bool, details: str, updated_context: dict)
    """
    task_type = message.get('content', {}).get('type', 'unknown')
    task_id = message.get('content', {}).get('task_id', 'unknown')
    
    print(f"\n{'='*40}")
    print(f"SIMULATING TASK EXECUTION")
    print(f"Task ID: {task_id}")
    print(f"Type: {task_type}")
    print(f"From: {message.get('sender', 'unknown')}")
    print(f"To: {message.get('recipient', 'unknown')}")
    print(f"Agent Context: {'Available' if agent_context else 'Not available'}")
    print(f"{'='*40}")
    
    # Initialize context if not provided
    if agent_context is None:
        agent_context = {}
    
    # Update context with task information
    if 'history' not in agent_context:
        agent_context['history'] = {}
    if 'tasks' not in agent_context['history']:
        agent_context['history']['tasks'] = []
    
    # Add task to history
    task_entry = {
        'task_id': task_id,
        'type': task_type,
        'timestamp': datetime.now().isoformat(),
        'status': 'completed'
    }
    agent_context['history']['tasks'].append(task_entry)
    
    # Update last active time
    agent_context['state'] = agent_context.get('state', {})
    agent_context['state']['last_active'] = datetime.now().isoformat()
    
    # Simulate different outcomes based on task type
    if task_type == 'data_processing':
        return True, "Data processed successfully", agent_context
    elif task_type == 'api_call':
        return True, "API call completed", agent_context
    elif task_type == 'report_generation':
        return True, "Report generated", agent_context
    else:
        return True, f"Task {task_id} executed successfully", agent_context


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


def process_inbox(agent, schema, simulate=True, clear=False, force=False, context_dir='context'):
    """Process all messages in the agent's inbox.
    
    Args:
        agent: The agent ID to process messages for
        schema: The JSON schema to validate messages against
        simulate: Whether to simulate task execution
        clear: Whether to clear processed messages from the inbox
        force: Whether to force execution even if dependencies aren't met
        context_dir: Directory containing context files
    """
    inbox_path = Path(f"postbox/{agent}/inbox.json")
    outbox_path = Path(f"postbox/{agent}/outbox.json")
    
    # Initialize context manager
    context_manager = ContextManager(context_dir)
    
    # Load agent context
    try:
        agent_context = context_manager.load_context(agent)
        logger.debug(f"Loaded context for agent {agent}")
    except Exception as e:
        logger.error(f"Error loading context for {agent}: {e}")
        agent_context = {}
    
    # Load inbox
    if not inbox_path.exists():
        print(f"No inbox found for agent {agent}")
        return
    
    try:
        with open(inbox_path, 'r') as f:
            inbox = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error reading inbox for {agent}: {e}")
        return
    
    if not isinstance(inbox, list):
        print(f"Invalid inbox format for {agent}")
        return
    
    if not inbox:
        print(f"No messages in {agent}'s inbox")
        return
    
    print(f"\nProcessing {len(inbox)} message(s) in {agent}'s inbox...")
    
    # Load outbox
    outbox = []
    if outbox_path.exists():
        try:
            with open(outbox_path, 'r') as f:
                outbox = json.load(f)
                if not isinstance(outbox, list):
                    outbox = []
        except (json.JSONDecodeError, FileNotFoundError):
            outbox = []
    
    processed_messages = []
    context_modified = False
    
    for message in inbox:
        try:
            # Validate message against schema
            validate(instance=message, schema=schema)
            
            # Check dependencies if not forcing
            if not force and not check_dependencies_met(message):
                print(f"Skipping {message.get('id', 'unknown')}: Dependencies not met")
                continue
            
            # Make a copy of the context for this task
            task_context = json.loads(json.dumps(agent_context)) if agent_context else {}
            
            # Simulate task execution with context
            if simulate:
                success, details, updated_context = simulate_task_execution(message, task_context)
                
                # Check if context was modified
                if json.dumps(task_context) != json.dumps(agent_context):
                    agent_context = updated_context
                    context_modified = True
                    logger.debug(f"Context updated during task execution for {agent}")
            else:
                success = True
                details = "Simulation skipped"
            
            # Log the result
            append_to_task_log(agent, message, success, details)
            
            # Create status message
            status_msg = create_status_message(agent, message, success, details)
            outbox.append(status_msg)
            
            print(f"Processed message {message.get('id', 'unknown')}: {'✓' if success else '✗'}")
            processed_messages.append(message['id'])
            
        except ValidationError as e:
            print(f"Invalid message format: {e}")
        except Exception as e:
            print(f"Error processing message: {e}")
    
    # Save updated context if modified
    if context_modified:
        try:
            if context_manager.save_context(agent, agent_context):
                logger.debug(f"Saved updated context for agent {agent}")
            else:
                logger.error(f"Failed to save context for agent {agent}")
        except Exception as e:
            logger.error(f"Error saving context for {agent}: {e}")
    
    # Save outbox
    try:
        with open(outbox_path, 'w') as f:
            json.dump(outbox, f, indent=2)
    except Exception as e:
        print(f"Error saving outbox: {e}")
    
    # Clear processed messages from inbox if requested
    if clear and processed_messages:
        remaining_messages = [msg for msg in inbox if msg.get('id') not in processed_messages]
        try:
            with open(inbox_path, 'w') as f:
                json.dump(remaining_messages, f, indent=2)
            print(f"\nCleared {len(processed_messages)} processed message(s) from inbox")
        except Exception as e:
            print(f"Error clearing inbox: {e}")


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
    parser = argparse.ArgumentParser(description='Agent Runner CLI')
    parser.add_argument('agent', help='Agent ID (e.g., WA, CA, CC)')
    parser.add_argument('--schema', default='exchange_protocol.json', 
                       help='Path to JSON schema file')
    parser.add_argument('--no-simulate', action='store_true', 
                       help='Skip task simulation')
    parser.add_argument('--clear', action='store_true',
                       help='Clear processed messages from inbox')
    parser.add_argument('--force', '-f', action='store_true',
                       help='Force execution even if dependencies are not met')
    parser.add_argument('--init', action='store_true',
                       help='Initialize agent configuration')
    parser.add_argument('--context-dir', default='context',
                       help='Directory containing context files')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    if args.init:
        agent_init(args.agent)
        return
    
    # Load schema
    try:
        with open(args.schema, 'r') as f:
            schema = json.load(f)
    except FileNotFoundError:
        print(f"Schema file not found: {args.schema}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in schema file: {e}")
        sys.exit(1)
    
    # Process inbox
    process_inbox(
        agent=args.agent,
        schema=schema,
        simulate=not args.no_simulate,
        clear=args.clear,
        force=args.force,
        context_dir=args.context_dir
    )
    print(f"   Force execution: {args.force}")
    
    # Process the inbox
    process_inbox(args.agent, schema, args.simulate, args.clear, args.force)
    
    print("\n✨ Agent Runner completed successfully")


if __name__ == "__main__":
    main()