#!/usr/bin/env python3
"""
Test runner for retry/fallback functionality based on live_test_plan.yaml
Simulates the orchestrator behavior with retry and fallback logic
"""

import json
import yaml
import time
from datetime import datetime
from pathlib import Path
import sys

def log_event(event_type, task_id, message, details=None):
    """Log an event with timestamp"""
    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "event": event_type,
        "task_id": task_id,
        "message": message
    }
    if details:
        log_entry["details"] = details
    
    print(f"[{timestamp}] {event_type} | {task_id} | {message}")
    if details:
        print(f"  Details: {json.dumps(details, indent=2)}")
    print("-" * 60)
    
    # Also write to log file
    with open("logs/retry_fallback_test.log", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

def simulate_task_execution(task, retry_count=0):
    """Simulate task execution with failure/success based on task config"""
    task_id = task["task_id"]
    agent = task["agent"]
    
    # Simulate the "fail_first" mode for the first task
    # CA should fail all attempts to trigger fallback to CC
    if task_id == "live-test-summary" and agent == "CA":
        return False, f"Simulated failure (retry {retry_count})"
    
    # CC (fallback agent) should succeed
    if task_id == "live-test-summary" and agent == "CC":
        return True, "Task completed successfully by fallback agent CC"
    
    # All other tasks succeed
    return True, "Task completed successfully"

def execute_with_retry_fallback(task, log_file):
    """Execute a task with retry and fallback logic"""
    task_id = task["task_id"]
    original_agent = task["agent"]
    max_retries = task.get("max_retries", 0)
    fallback_agent = task.get("fallback_agent")
    
    log_event("TASK_START", task_id, f"Starting task execution with agent {original_agent}")
    
    # Try with the original agent
    retry_count = 0
    current_agent = original_agent
    
    while retry_count <= max_retries:
        log_event("ATTEMPT", task_id, f"Attempt {retry_count + 1} with agent {current_agent}")
        
        success, result = simulate_task_execution(task, retry_count)
        
        if success:
            log_event("SUCCESS", task_id, f"Task completed by {current_agent}", {"result": result})
            return True
        else:
            log_event("FAILURE", task_id, f"Attempt failed: {result}", {"retry_count": retry_count})
            
            if retry_count < max_retries:
                log_event("RETRY", task_id, f"Will retry (attempt {retry_count + 2} of {max_retries + 1})")
                time.sleep(2)  # Simulate delay between retries
            retry_count += 1
    
    # If we have a fallback agent, try with that
    if fallback_agent:
        log_event("FALLBACK", task_id, f"Falling back from {original_agent} to {fallback_agent}")
        task["agent"] = fallback_agent
        success, result = simulate_task_execution(task, 0)
        
        if success:
            log_event("FALLBACK_SUCCESS", task_id, f"Task completed by fallback agent {fallback_agent}", {"result": result})
            return True
        else:
            log_event("FALLBACK_FAILURE", task_id, f"Fallback agent {fallback_agent} also failed", {"result": result})
            return False
    
    log_event("TASK_FAILED", task_id, "Task failed after all retries and fallback attempts")
    return False

def main():
    # Load the test plan
    plan_path = "plans/live_test_plan.yaml"
    log_file = "logs/retry_fallback_test.log"
    
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)
    
    # Clear previous log
    with open(log_file, "w") as f:
        f.write("")
    
    print("=== LIVE TEST: RETRY AND FALLBACK FUNCTIONALITY ===")
    print(f"Test Plan: {plan_path}")
    print(f"Log File: {log_file}")
    print("=" * 50)
    
    # Load the test plan
    with open(plan_path, "r") as f:
        plan = yaml.safe_load(f)
    
    log_event("TEST_START", "SYSTEM", "Starting retry/fallback live test", {
        "plan_id": plan["metadata"]["plan_id"],
        "description": plan["metadata"]["description"]
    })
    
    # Execute tasks in order
    for task_config in plan["tasks"]:
        task = {
            "task_id": task_config["task_id"],
            "agent": task_config["agent"],
            "description": task_config["description"],
            "max_retries": task_config.get("max_retries", 0),
            "fallback_agent": task_config.get("fallback_agent")
        }
        
        success = execute_with_retry_fallback(task, log_file)
        
        # For dependency handling (simplified)
        if not success and task_config.get("dependencies"):
            log_event("DEPENDENCY_SKIP", task["task_id"], 
                     "Skipping dependent tasks due to failure")
            break
    
    log_event("TEST_COMPLETE", "SYSTEM", "Live test completed")
    
    # Generate summary
    print("\n=== TEST SUMMARY ===")
    with open(log_file, "r") as f:
        events = [json.loads(line) for line in f if line.strip()]
    
    retry_events = [e for e in events if e["event"] == "RETRY"]
    fallback_events = [e for e in events if e["event"] == "FALLBACK"]
    success_events = [e for e in events if "SUCCESS" in e["event"]]
    
    print(f"Total events logged: {len(events)}")
    print(f"Retry events: {len(retry_events)}")
    print(f"Fallback events: {len(fallback_events)}")
    print(f"Success events: {len(success_events)}")
    
    # Check if fallback was triggered as expected
    if fallback_events:
        print("\n✅ FALLBACK TRIGGERED AS EXPECTED")
        for event in fallback_events:
            print(f"  - Task {event['task_id']}: {event['message']}")
    else:
        print("\n❌ NO FALLBACK EVENTS FOUND")
    
    print("\n=== END OF TEST ===")

if __name__ == "__main__":
    main()