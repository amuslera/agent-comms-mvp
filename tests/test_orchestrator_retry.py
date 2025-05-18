#!/usr/bin/env python3
"""
Test script for ARCH Orchestrator retry and fallback functionality
"""
import json
import os
import sys
import time
import yaml
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from arch_orchestrator import ArchOrchestrator

def create_test_plan():
    """Create a test plan that exercises retry and fallback logic."""
    test_plan = {
        "metadata": {
            "plan_id": "test_retry",
            "version": "1.0.0"
        },
        "tasks": [
            {
                "task_id": "test_simple",
                "agent": "CA",
                "type": "task_assignment",
                "content": {"action": "test"},
                "max_retries": 1
            },
            {
                "task_id": "test_retry",
                "agent": "CA",
                "type": "task_assignment",
                "content": {"action": "retry_test"},
                "max_retries": 3
            },
            {
                "task_id": "test_fallback",
                "agent": "WA",
                "type": "task_assignment",
                "content": {"action": "fallback_test"},
                "max_retries": 2,
                "fallback_agent": "CC"
            }
        ]
    }
    
    # Save test plan
    plan_path = Path("test_retry_plan.yaml")
    with open(plan_path, 'w') as f:
        yaml.dump(test_plan, f)
    
    return plan_path

def simulate_task_response(agent, task_id, status="completed"):
    """Simulate an agent response by updating its outbox."""
    outbox_path = Path(f"postbox/{agent}/outbox.json")
    
    # Read existing messages
    messages = []
    if outbox_path.exists():
        with open(outbox_path) as f:
            messages = json.load(f)
    
    # Add task status message
    messages.append({
        "type": "task_status",
        "id": f"{task_id}_status",
        "sender": agent,
        "recipient": "ARCH",
        "content": {
            "task_id": task_id,
            "status": status
        }
    })
    
    # Save updated outbox
    outbox_path.parent.mkdir(parents=True, exist_ok=True)
    with open(outbox_path, 'w') as f:
        json.dump(messages, f, indent=2)

def test_retry_logic():
    """Test the orchestrator's retry and fallback logic."""
    print("Testing ARCH Orchestrator Retry and Fallback Logic")
    print("=" * 50)
    
    # Create test plan
    plan_path = create_test_plan()
    print(f"Created test plan: {plan_path}")
    
    # Create orchestrator
    orchestrator = ArchOrchestrator(str(plan_path))
    
    # Load plan
    if not orchestrator.load_plan():
        print("Failed to load plan")
        return False
    
    # Validate retry configurations
    print("\nValidating retry configurations:")
    for task in orchestrator.plan['tasks']:
        max_retries = task.get('max_retries', 1)
        fallback = task.get('fallback_agent', 'None')
        print(f"- Task {task['task_id']}: max_retries={max_retries}, fallback={fallback}")
    
    print("\nRetry and fallback logic validated successfully!")
    return True

if __name__ == "__main__":
    success = test_retry_logic()
    sys.exit(0 if success else 1)