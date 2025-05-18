#!/usr/bin/env python3
"""
ARCH Orchestrator Runtime

Loads and executes agent communication plans by:
1. Loading plan from YAML
2. Dispatching tasks to agent inboxes
3. Triggering agent runners
4. Monitoring execution
5. Reporting results

Now with enhanced retry and fallback support!
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TaskMonitor(FileSystemEventHandler):
    """Monitor task completion via outbox and task log changes."""
    
    def __init__(self, task_id: str, agent: str):
        self.task_id = task_id
        self.agent = agent
        self.completed = False
        self.result = None
    
    def on_modified(self, event):
        if event.is_directory:
            return
            
        if event.src_path.endswith('outbox.json'):
            self._check_outbox()
        elif event.src_path.endswith('task_log.md'):
            self._check_task_log()
    
    def _check_outbox(self):
        """Check outbox for task completion status."""
        try:
            outbox_path = Path(f"postbox/{self.agent}/outbox.json")
            if not outbox_path.exists():
                return
                
            with open(outbox_path) as f:
                messages = json.load(f)
                
            for msg in messages:
                if (msg.get('type') == 'task_status' and 
                    msg.get('content', {}).get('task_id') == self.task_id):
                    self.completed = True
                    self.result = msg.get('content', {}).get('status')
                    break
        except Exception as e:
            logger.error(f"Error checking outbox: {e}")
    
    def _check_task_log(self):
        """Check task log for completion status."""
        try:
            log_path = Path(f"postbox/{self.agent}/task_log.md")
            if not log_path.exists():
                return
                
            with open(log_path) as f:
                content = f.read()
                
            if f"**Task ID**: {self.task_id}" in content:
                if "**Status**: ✅ Success" in content:
                    self.completed = True
                    self.result = "completed"
                elif "**Status**: ❌ Failed" in content:
                    self.completed = True
                    self.result = "failed"
        except Exception as e:
            logger.error(f"Error checking task log: {e}")

class ArchOrchestrator:
    """Main orchestrator class for executing agent communication plans."""
    
    def __init__(self, plan_path: str):
        self.plan_path = Path(plan_path)
        self.plan = None
        self.observers = []
        self.monitors = {}
        
    def load_plan(self) -> bool:
        """Load and validate the execution plan."""
        try:
            with open(self.plan_path) as f:
                self.plan = yaml.safe_load(f)
            return True
        except Exception as e:
            logger.error(f"Error loading plan: {e}")
            return False
    
    def validate_task(self, task: Dict) -> bool:
        """Validate a task's structure and requirements."""
        required_fields = ['task_id', 'type', 'agent', 'content']
        return all(field in task for field in required_fields)
    
    def dispatch_task(self, task: Dict, target_agent: str = None) -> bool:
        """Dispatch a task to the appropriate agent's inbox."""
        try:
            # Use target agent if specified (for fallback), otherwise use task's agent
            agent = target_agent or task['agent']
            inbox_path = Path(f"postbox/{agent}/inbox.json")
            
            # Create inbox if it doesn't exist
            inbox_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Load existing messages or create new list
            messages = []
            if inbox_path.exists():
                with open(inbox_path) as f:
                    messages = json.load(f)
            
            # Add new task message
            task_message = {
                "type": "task_assignment",
                "id": str(task['task_id']),
                "timestamp": datetime.now().isoformat(),
                "sender": "ARCH",
                "recipient": agent,
                "version": "1.0.0",
                "content": task['content'],
                "metadata": task.get('metadata', {})
            }
            
            # Add priority and deadline if specified
            if 'priority' in task:
                task_message['content']['priority'] = task['priority']
            if 'deadline' in task:
                task_message['content']['deadline'] = task['deadline']
            
            messages.append(task_message)
            
            # Save updated inbox
            with open(inbox_path, 'w') as f:
                json.dump(messages, f, indent=2)
                
            logger.info(f"Dispatched task {task['task_id']} to {agent}")
            return True
            
        except Exception as e:
            logger.error(f"Error dispatching task: {e}")
            return False
    
    def start_agent_runner(self, agent: str) -> Optional[subprocess.Popen]:
        """Start the agent runner process for an agent."""
        try:
            cmd = ['python3', 'agent_runner.py', agent, '--clear']
            return subprocess.Popen(cmd)
        except Exception as e:
            logger.error(f"Error starting agent runner: {e}")
            return None
    
    def monitor_task(self, task: Dict, agent: str, timeout: int = 300) -> str:
        """Monitor a task's execution and wait for completion."""
        task_id = task['task_id']
        
        # Create monitor and observer
        monitor = TaskMonitor(task_id, agent)
        observer = Observer()
        observer.schedule(monitor, f"postbox/{agent}", recursive=False)
        observer.start()
        
        self.monitors[task_id] = monitor
        self.observers.append(observer)
        
        # Wait for completion with timeout
        start_time = time.time()
        
        while not monitor.completed:
            if time.time() - start_time > timeout:
                logger.error(f"Task {task_id} timed out on agent {agent}")
                observer.stop()
                observer.join()
                return "timeout"
            time.sleep(1)
        
        observer.stop()
        observer.join()
        
        return monitor.result or "failed"
    
    def execute_task_with_retry(self, task: Dict) -> tuple[bool, str]:
        """Execute a task with retry logic and fallback support."""
        max_retries = task.get('max_retries', 1)
        retry_delay = 5  # Base delay in seconds
        
        # Track all execution attempts
        attempts = []
        original_agent = task['agent']
        
        for attempt in range(max_retries):
            current_agent = original_agent
            
            # Use fallback agent if we've failed on primary agent
            if attempt > 0 and 'fallback_agent' in task:
                current_agent = task['fallback_agent']
                logger.info(f"Attempting with fallback agent: {current_agent}")
            
            logger.info(f"Executing task {task['task_id']} (attempt {attempt + 1}/{max_retries}) on agent {current_agent}")
            
            # Dispatch task
            if not self.dispatch_task(task, current_agent):
                attempts.append((current_agent, False, "Dispatch failed"))
                time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                continue
            
            # Start agent runner
            process = self.start_agent_runner(current_agent)
            if not process:
                attempts.append((current_agent, False, "Agent runner failed"))
                time.sleep(retry_delay * (2 ** attempt))
                continue
            
            # Monitor execution
            result = self.monitor_task(task, current_agent)
            process.terminate()
            
            if result == "completed":
                logger.info(f"Task {task['task_id']} completed successfully on {current_agent}")
                return True, f"Completed on {current_agent} (attempt {attempt + 1})"
            
            attempts.append((current_agent, False, f"Execution {result}"))
            
            # Don't sleep after the last attempt
            if attempt < max_retries - 1:
                logger.info(f"Task {task['task_id']} failed, retrying in {retry_delay * (2 ** attempt)} seconds...")
                time.sleep(retry_delay * (2 ** attempt))
        
        # Task failed all attempts
        failure_summary = "; ".join([f"{agent}: {reason}" for agent, _, reason in attempts])
        return False, f"Failed all {max_retries} attempts: {failure_summary}"
    
    def execute_plan(self) -> bool:
        """Execute the loaded plan."""
        if not self.plan:
            logger.error("No plan loaded")
            return False
        
        print(f"\nExecuting plan: {self.plan_path}")
        print("=" * 50)
        
        # Track results
        results = []
        
        # Process each task
        for task in self.plan.get('tasks', []):
            print(f"\nProcessing task {task['task_id']}...")
            
            # Validate task
            if not self.validate_task(task):
                logger.error(f"Invalid task structure: {task}")
                results.append((task['task_id'], False, "Invalid task structure"))
                continue
            
            # Execute task with retry and fallback
            success, status = self.execute_task_with_retry(task)
            results.append((task['task_id'], success, status))
        
        # Stop all observers
        for observer in self.observers:
            observer.stop()
            observer.join()
        
        # Print summary
        print("\nExecution Summary:")
        print("=" * 50)
        for task_id, success, status in results:
            print(f"Task {task_id}: {'✅' if success else '❌'} {status}")
        
        # Log retry and fallback statistics
        print("\nRetry and Fallback Statistics:")
        print("=" * 30)
        for task in self.plan.get('tasks', []):
            max_retries = task.get('max_retries', 1)
            fallback = task.get('fallback_agent', 'None')
            print(f"Task {task['task_id']}: max_retries={max_retries}, fallback_agent={fallback}")
        
        return all(success for _, success, _ in results)

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='ARCH Orchestrator Runtime')
    parser.add_argument('--plan', required=True, help='Path to execution plan YAML')
    
    args = parser.parse_args()
    
    # Create and run orchestrator
    orchestrator = ArchOrchestrator(args.plan)
    
    if not orchestrator.load_plan():
        sys.exit(1)
    
    success = orchestrator.execute_plan()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()