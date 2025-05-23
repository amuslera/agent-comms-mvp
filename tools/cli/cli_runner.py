#!/usr/bin/env python3
"""
ARCH Plan Runner CLI

A command-line utility for executing YAML plans using the ARCH orchestrator.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from arch_orchestrator import ArchOrchestrator

class CLIRunner:
    """CLI interface for running ARCH plans."""
    
    def __init__(self):
        self.plan_path = None
        self.plan = None
        self.orchestrator = None
    
    def load_plan(self, plan_path: str) -> bool:
        """Load and validate a YAML plan file."""
        self.plan_path = Path(plan_path).resolve()
        
        if not self.plan_path.exists():
            print(f"Error: Plan file not found: {self.plan_path}")
            return False
            
        try:
            self.orchestrator = ArchOrchestrator(str(self.plan_path))
            if not self.orchestrator.load_plan():
                print("Error: Failed to load plan")
                return False
            return True
        except Exception as e:
            print(f"Error loading plan: {e}")
            return False
    
    def get_task_summary(self) -> List[Dict]:
        """Extract summary information for all tasks in the plan."""
        if not self.orchestrator or not hasattr(self.orchestrator, 'plan'):
            return []
            
        tasks = []
        for task in self.orchestrator.plan.get('tasks', []):
            task_id = task.get('task_id', 'unknown')
            agent = task.get('agent', 'unknown')
            task_type = task.get('type', 'unknown')
            
            # Get execution status if available
            status = "pending"
            retries = 0
            score = "N/A"
            
            # In a real implementation, you would get this from the task tracker
            # For now, we'll just use placeholders
            tasks.append({
                'task_id': task_id,
                'agent': agent,
                'type': task_type,
                'status': status,
                'retries': retries,
                'score': score
            })
            
        return tasks
    
    def print_summary(self, tasks: List[Dict]) -> None:
        """Print a formatted summary of task execution."""
        if not tasks:
            print("No tasks found in plan.")
            return
            
        print("\n" + "=" * 80)
        print(f"ARCH Plan Execution Summary: {self.plan_path.name}")
        print("=" * 80)
        print(f"{'Task ID':<15} {'Agent':<15} {'Type':<20} {'Status':<15} {'Retries':<8} {'Score'}")
        print("-" * 80)
        
        for task in tasks:
            print(f"{task['task_id']:<15} {task['agent']:<15} {task['type']:<20} {task['status']:<15} {task['retries']:<8} {task['score']}")
        
        print("=" * 80 + "\n")
    
    def run_plan(self) -> bool:
        """Execute the loaded plan and return success status."""
        if not self.orchestrator:
            print("Error: No plan loaded")
            return False
            
        print(f"\nExecuting plan: {self.plan_path.name}")
        print("-" * 60)
        
        try:
            # Get initial task summary
            tasks = self.get_task_summary()
            self.print_summary(tasks)
            
            # Execute the plan
            success = self.orchestrator.execute_plan()
            
            # Get final task summary
            tasks = self.get_task_summary()
            self.print_summary(tasks)
            
            if success:
                print("✅ Plan executed successfully!")
            else:
                print("❌ Plan execution failed or was interrupted.")
                
            return success
            
        except KeyboardInterrupt:
            print("\nExecution interrupted by user.")
            return False
        except Exception as e:
            print(f"\nError executing plan: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='ARCH Plan Runner CLI')
    parser.add_argument('plan', help='Path to plan file (YAML)')
    parser.add_argument('--summary', '-s', action='store_true', 
                       help='Show plan summary without executing')
    
    args = parser.parse_args()
    
    runner = CLIRunner()
    
    # Load the plan
    if not runner.load_plan(args.plan):
        sys.exit(1)
    
    # Get and display task summary
    tasks = runner.get_task_summary()
    runner.print_summary(tasks)
    
    # Execute the plan unless --summary flag is set
    if not args.summary:
        success = runner.run_plan()
        sys.exit(0 if success else 1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
