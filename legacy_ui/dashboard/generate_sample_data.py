#!/usr/bin/env python3
"""
Generate sample data for the Bluelabel Agent OS Dashboard.
This script creates sample agent directories with outbox and task log files.
"""

import os
import json
import time
import random
from datetime import datetime, timedelta
from pathlib import Path

# Sample agent configurations
AGENTS = ["ARCH", "CA", "CC", "WA"]
TASK_TYPES = ["analysis", "extraction", "summarization", "validation"]
STATUSES = ["completed", "in_progress", "failed", "pending"]
MESSAGE_TYPES = ["task", "result", "error", "info"]

def create_agent_directories(base_dir: Path) -> None:
    """Create agent directories and sample data."""
    for agent in AGENTS:
        agent_dir = base_dir / agent
        agent_dir.mkdir(exist_ok=True)
        
        # Create sample outbox
        create_sample_outbox(agent_dir, agent)
        
        # Create sample task log
        create_sample_task_log(agent_dir, agent)

def create_sample_outbox(agent_dir: Path, agent: str, num_messages: int = 10) -> None:
    """Create a sample outbox file with random messages."""
    outbox = {
        "agent": agent,
        "messages": []
    }
    
    now = datetime.now()
    
    for i in range(num_messages):
        # Randomly select a recipient (sometimes broadcast to all)
        if random.random() > 0.7:  # 30% chance of broadcast
            to_agent = "BROADCAST"
        else:
            to_agent = random.choice([a for a in AGENTS if a != agent])
        
        # Random message type
        msg_type = random.choice(MESSAGE_TYPES)
        
        # Create message content based on type
        if msg_type == "task":
            content = {
                "task_id": f"TASK-{random.randint(100, 999)}",
                "type": random.choice(TASK_TYPES),
                "priority": random.choice(["low", "medium", "high"]),
                "description": f"Sample {msg_type} from {agent} to {to_agent}"
            }
        elif msg_type == "result":
            content = {
                "task_id": f"TASK-{random.randint(100, 999)}",
                "status": random.choice(["success", "partial", "failed"]),
                "details": f"Result details for task from {agent}"
            }
        elif msg_type == "error":
            content = {
                "code": f"ERR-{random.randint(1000, 9999)}",
                "message": f"Sample error occurred in {agent}",
                "severity": random.choice(["warning", "error", "critical"])
            }
        else:  # info
            content = f"Informational message from {agent} to {to_agent}"
        
        # Add timestamp with some randomness
        timestamp = now - timedelta(minutes=random.randint(0, 60))
        
        outbox["messages"].append({
            "from": agent,
            "to": to_agent,
            "type": msg_type,
            "content": content,
            "timestamp": timestamp.isoformat()
        })
    
    # Write outbox file
    outbox_file = agent_dir / "outbox.json"
    with open(outbox_file, 'w') as f:
        json.dump(outbox, f, indent=2)

def create_sample_task_log(agent_dir: Path, agent: str, num_tasks: int = 5) -> None:
    """Create a sample task log file."""
    now = datetime.now()
    task_log = []
    
    for i in range(num_tasks):
        task_id = f"TASK-{100 + i:03d}"
        status = random.choice(STATUSES)
        
        # Task header
        task_log.append(f"## {task_id} - {status}")
        
        # Task details
        start_time = now - timedelta(minutes=random.randint(10, 120))
        task_log.append(f"- Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        task_log.append(f"- Description: Sample {random.choice(TASK_TYPES)} task")
        
        # Add some random metadata
        if random.random() > 0.3:  # 70% chance of retries
            retries = random.randint(0, 3)
            task_log.append(f"- Retry count: {retries}")
        
        if random.random() > 0.7:  # 30% chance of fallback
            fallback = random.choice([a for a in AGENTS if a != agent])
            task_log.append(f"- Fallback to: {fallback}")
        
        # Add completion time for completed tasks
        if status == "completed" or (status == "failed" and random.random() > 0.5):
            completion_time = start_time + timedelta(
                minutes=random.randint(1, 30),
                seconds=random.randint(0, 59)
            )
            task_log.append(f"- Completed at: {completion_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if status == "completed":
                task_log.append("- Result: Task completed successfully")
            else:
                task_log.append("- Error: Sample error message")
        
        # Add some random notes
        if random.random() > 0.5:
            notes = [
                "Processing complete",
                "Waiting for input",
                "Verification needed",
                "Pending review",
                "Awaiting confirmation"
            ]
            task_log.append(f"- Note: {random.choice(notes)}")
        
        # Add space between tasks
        task_log.append("")
    
    # Write task log file
    task_log_file = agent_dir / "task_log.md"
    with open(task_log_file, 'w') as f:
        f.write("\n".join(task_log))

def main():
    """Main function to generate sample data."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate sample data for the Bluelabel Agent OS Dashboard.")
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="sample_postbox",
        help="Output directory for sample data (default: 'sample_postbox')"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean the output directory before generating new data"
    )
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output)
    
    if args.clean and output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)
    
    output_dir.mkdir(exist_ok=True)
    
    # Generate sample data
    print(f"Generating sample data in {output_dir}...")
    create_agent_directories(output_dir)
    print(f"Sample data generated successfully in {output_dir}")
    print(f"\nTo view the dashboard with this sample data, run:")
    print(f"  python3 tools/dashboard/dashboard_main.py --postbox-dir {output_dir}")

if __name__ == "__main__":
    main()
