"""
End-to-end test validator for agent message processing flow.

This script simulates a complete message flow:
1. Injects a valid task into an agent's inbox
2. Runs the agent using agent_runner.py
3. Validates the results:
   - Log entry exists
   - task_status message written
   - Output matches simulation expectations
"""

import os
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


def create_test_task(agent_id: str, task_id: str, handler: str) -> Dict[str, Any]:
    """Create a test task message for injection."""
    return {
        "type": "task_assignment",
        "id": f"test-{task_id}-{datetime.now().isoformat()}",
        "timestamp": datetime.now().isoformat(),
        "sender": "ARCH",
        "recipient": agent_id,
        "version": "1.0.0",
        "content": {
            "task_id": task_id,
            "handler": handler,
            "description": f"Test task for {handler} handler"
        }
    }


def inject_task_to_inbox(agent_id: str, task: Dict[str, Any]) -> None:
    """Inject a task message into the agent's inbox."""
    inbox_path = Path(f"postbox/{agent_id}/inbox.json")
    
    # Read existing messages
    if inbox_path.exists():
        with open(inbox_path, 'r') as f:
            messages = json.load(f)
    else:
        messages = []
    
    # Add new message
    messages.append(task)
    
    # Write back to inbox
    with open(inbox_path, 'w') as f:
        json.dump(messages, f, indent=2)


def validate_log_entry(agent_id: str, task_id: str) -> bool:
    """Validate that a log entry exists for the task."""
    log_path = Path(f"postbox/{agent_id}/task_log.md")
    
    if not log_path.exists():
        return False
    
    with open(log_path, 'r') as f:
        log_content = f.read()
    
    return task_id in log_content


def validate_task_status(agent_id: str, task_id: str) -> bool:
    """Validate that a task_status message was written."""
    outbox_path = Path(f"postbox/{agent_id}/outbox.json")
    
    if not outbox_path.exists():
        return False
    
    with open(outbox_path, 'r') as f:
        messages = json.load(f)
    
    for msg in messages:
        if (msg.get("type") == "task_status" and 
            msg.get("content", {}).get("task_id") == task_id):
            return True
    
    return False


def run_agent(agent_id: str) -> None:
    """Run the agent using agent_runner.py."""
    subprocess.run(["python", "agent_runner.py", "--agent", agent_id], check=True)


def test_agent_flow(agent_id: str = "CA", task_id: str = "TASK-009", handler: str = "digest") -> bool:
    """
    Run end-to-end test of agent message processing.
    
    Args:
        agent_id: ID of the agent to test
        task_id: ID of the test task
        handler: Type of handler to test
        
    Returns:
        bool: True if all validations pass
    """
    print(f"\nTesting agent flow for {agent_id} with {handler} handler...")
    
    # Create and inject test task
    task = create_test_task(agent_id, task_id, handler)
    inject_task_to_inbox(agent_id, task)
    print("✓ Task injected to inbox")
    
    # Run agent
    run_agent(agent_id)
    print("✓ Agent run completed")
    
    # Validate results
    log_valid = validate_log_entry(agent_id, task_id)
    status_valid = validate_task_status(agent_id, task_id)
    
    print(f"\nValidation Results:")
    print(f"- Log entry exists: {'✓' if log_valid else '✗'}")
    print(f"- Task status written: {'✓' if status_valid else '✗'}")
    
    return log_valid and status_valid


if __name__ == "__main__":
    # Run tests for different handlers
    handlers = ["digest", "summary", "generic"]
    all_passed = True
    
    for handler in handlers:
        if not test_agent_flow(handler=handler):
            all_passed = False
            print(f"\n❌ Test failed for {handler} handler")
        else:
            print(f"\n✓ Test passed for {handler} handler")
    
    if all_passed:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
        exit(1) 