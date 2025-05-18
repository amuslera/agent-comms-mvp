"""
Simulated task handlers for agent message processing.

This module provides stub implementations of task handlers that can be used
by the agent runner to simulate agent behavior during message processing.
"""

from typing import Dict, Any
import json
from datetime import datetime


def simulate_digest_generation(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate the generation of a content digest.
    
    Args:
        task: Dictionary containing task details and content
        
    Returns:
        Dictionary with simulation results
    """
    print(f"[{datetime.now().isoformat()}] Simulating digest generation for task {task['content']['task_id']}")
    
    return {
        "status": "success",
        "digest": "This is a simulated digest output.",
        "summary_count": 3,
        "timestamp": datetime.now().isoformat(),
        "task_id": task["content"]["task_id"]
    }


def simulate_summary_extraction(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate the extraction of a summary from content.
    
    Args:
        task: Dictionary containing task details and content
        
    Returns:
        Dictionary with simulation results
    """
    print(f"[{datetime.now().isoformat()}] Simulating summary extraction for task {task['content']['task_id']}")
    
    return {
        "status": "success",
        "summary": "Simulated summary from content.",
        "timestamp": datetime.now().isoformat(),
        "task_id": task["content"]["task_id"]
    }


def simulate_generic_response(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate a generic task response.
    
    Args:
        task: Dictionary containing task details and content
        
    Returns:
        Dictionary with simulation results
    """
    print(f"[{datetime.now().isoformat()}] Simulating generic response for task {task['content']['task_id']}")
    
    return {
        "status": "success",
        "message": "Generic task processed successfully.",
        "timestamp": datetime.now().isoformat(),
        "task_id": task["content"]["task_id"]
    }


def route_simulation(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Route incoming tasks to appropriate simulation handlers.
    
    Args:
        task: Dictionary containing task details and content
        
    Returns:
        Dictionary with simulation results
        
    Raises:
        ValueError: If task format is invalid
    """
    if not isinstance(task, dict) or "content" not in task:
        raise ValueError("Invalid task format: missing 'content' field")
    
    handler = task["content"].get("handler", "generic")
    
    print(f"[{datetime.now().isoformat()}] Routing task {task['content']['task_id']} to {handler} handler")
    
    if handler == "digest":
        return simulate_digest_generation(task)
    elif handler == "summary":
        return simulate_summary_extraction(task)
    else:
        return simulate_generic_response(task)


if __name__ == "__main__":
    # Example usage
    test_task = {
        "type": "task_assignment",
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "timestamp": datetime.now().isoformat(),
        "sender": "ARCH",
        "recipient": "CA",
        "version": "1.0.0",
        "content": {
            "task_id": "TASK-008",
            "handler": "digest",
            "description": "Test simulation handler"
        }
    }
    
    result = route_simulation(test_task)
    print("\nSimulation Result:")
    print(json.dumps(result, indent=2)) 