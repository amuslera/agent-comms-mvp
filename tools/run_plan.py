#!/usr/bin/env python3
"""
ARCH Plan Runner

A CLI tool to execute ARCH orchestration plans.
"""

import argparse
import json
import os
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from arch_orchestrator import ArchOrchestrator

class PlanRunner:
    """CLI tool for running ARCH execution plans."""
    
    def __init__(self):
        self.plans_dir = Path("plans")
        self.plans_dir.mkdir(exist_ok=True)
    
    def list_plans(self) -> List[Path]:
        """List all available plan files."""
        return sorted(self.plans_dir.glob("*.yaml")) + sorted(self.plans_dir.glob("*.yml"))
    
    def get_plan_info(self, plan_path: Path) -> Dict:
        """Extract basic info from a plan file."""
        try:
            with open(plan_path) as f:
                plan = yaml.safe_load(f)
            
            return {
                'path': str(plan_path),
                'id': plan.get('metadata', {}).get('plan_id', 'N/A'),
                'description': plan.get('metadata', {}).get('description', 'No description'),
                'num_tasks': len(plan.get('tasks', [])),
                'priority': plan.get('metadata', {}).get('priority', 'medium').capitalize(),
                'created': plan.get('metadata', {}).get('created', 'Unknown')
            }
        except Exception as e:
            return {
                'path': str(plan_path),
                'error': f"Error reading plan: {str(e)}"
            }
    
    def interactive_select_plan(self) -> Optional[Path]:
        """Interactively select a plan from available options."""
        plans = self.list_plans()
        
        if not plans:
            print("No plan files found in 'plans/' directory.")
            print("Create a plan file with a .yaml or .yml extension in the plans/ directory.")
            return None
        
        print("\nAvailable plans:")
        print("-" * 80)
        
        plan_info_list = []
        for i, plan_path in enumerate(plans, 1):
            info = self.get_plan_info(plan_path)
            plan_info_list.append((plan_path, info))
            
            if 'error' in info:
                print(f"{i}. {plan_path.name} - ERROR: {info['error']}")
            else:
                print(f"{i}. {info['id']} - {info['description']}")
                print(f"   Priority: {info['priority']} | Tasks: {info['num_tasks']} | Created: {info['created']}")
        
        print("\nSelect a plan to execute (or 'q' to quit):")
        
        while True:
            choice = input("> ").strip()
            
            if choice.lower() == 'q':
                return None
                
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(plans):
                    return plan_info_list[idx][0]
                print(f"Please enter a number between 1 and {len(plans)}")
            except ValueError:
                print("Please enter a valid number or 'q' to quit")
    
    def validate_plan(self, plan_path: Path) -> bool:
        """Validate a plan file structure."""
        try:
            with open(plan_path) as f:
                plan = yaml.safe_load(f)
            
            # Check required top-level fields
            required_fields = ['metadata', 'tasks']
            for field in required_fields:
                if field not in plan:
                    print(f"Error: Missing required field: {field}")
                    return False
            
            # Check metadata fields
            metadata = plan['metadata']
            required_metadata = ['plan_id', 'version', 'description']
            for field in required_metadata:
                if field not in metadata:
                    print(f"Error: Missing required metadata field: {field}")
                    return False
            
            # Check tasks
            if not isinstance(plan['tasks'], list):
                print("Error: 'tasks' must be a list")
                return False
                
            for i, task in enumerate(plan['tasks'], 1):
                if not isinstance(task, dict):
                    print(f"Error: Task {i} is not a dictionary")
                    return False
                
                required_task_fields = ['task_id', 'agent', 'type', 'description', 'content']
                for field in required_task_fields:
                    if field not in task:
                        print(f"Error: Task {i} missing required field: {field}")
                        return False
            
            return True
            
        except yaml.YAMLError as e:
            print(f"YAML parsing error: {e}")
            return False
        except Exception as e:
            print(f"Error validating plan: {e}")
            return False
    
    def run_plan(self, plan_path: Path) -> bool:
        """Execute a plan using the ArchOrchestrator."""
        if not self.validate_plan(plan_path):
            print("\nPlan validation failed. Please fix the errors before running.")
            return False
        
        print(f"\nExecuting plan: {plan_path.name}")
        print("-" * 60)
        
        try:
            orchestrator = ArchOrchestrator(str(plan_path))
            if not orchestrator.load_plan():
                print("Failed to load plan")
                return False
                
            print("Plan loaded successfully. Starting execution...\n")
            success = orchestrator.execute_plan()
            
            if success:
                print("\n✅ Plan executed successfully!")
            else:
                print("\n❌ Plan execution failed or was interrupted.")
                
            return success
            
        except KeyboardInterrupt:
            print("\n\nExecution interrupted by user.")
            return False
        except Exception as e:
            print(f"\nError executing plan: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='ARCH Plan Runner')
    parser.add_argument('plan', nargs='?', help='Path to plan file (YAML)')
    parser.add_argument('--list', '-l', action='store_true', help='List available plans')
    
    args = parser.parse_args()
    runner = PlanRunner()
    
    if args.list:
        plans = runner.list_plans()
        if plans:
            print("\nAvailable plans:")
            print("-" * 80)
            for plan in plans:
                print(f"- {plan}")
        else:
            print("No plan files found in 'plans/' directory.")
        return
    
    plan_path = None
    if args.plan:
        plan_path = Path(args.plan)
        if not plan_path.exists():
            print(f"Error: Plan file not found: {plan_path}")
            return 1
    else:
        plan_path = runner.interactive_select_plan()
        if not plan_path:
            return 0
    
    if plan_path:
        return 0 if runner.run_plan(plan_path) else 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
