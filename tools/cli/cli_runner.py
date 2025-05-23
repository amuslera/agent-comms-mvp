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
from tools.cli.plan_linter import PlanLinter
from core.branch_utils import GitBranchManager, BranchCreationError

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
    
    def create_branches_for_plan(self, base_branch: str = "main", dry_run: bool = False) -> bool:
        """Create Git branches for all tasks in the loaded plan."""
        if not self.plan_path:
            print("Error: No plan loaded")
            return False
            
        try:
            manager = GitBranchManager()
            results = manager.create_branches_for_plan(
                str(self.plan_path), 
                base_branch=base_branch,
                dry_run=dry_run
            )
            
            if not dry_run:
                manager.print_summary(results)
            
            # Return success if no errors occurred
            return len(results['errors']) == 0 and results['branches_failed'] == 0
            
        except BranchCreationError as e:
            print(f"❌ Branch creation failed: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error during branch creation: {e}")
            return False

    def run_plan(self, create_branches: bool = True, base_branch: str = "main") -> bool:
        """Execute the loaded plan and return success status."""
        if not self.orchestrator:
            print("Error: No plan loaded")
            return False
            
        print(f"\nExecuting plan: {self.plan_path.name}")
        print("-" * 60)
        
        try:
            # Create branches first if requested
            if create_branches:
                print("🌿 Creating branches for plan tasks...")
                if not self.create_branches_for_plan(base_branch=base_branch):
                    print("⚠️  Branch creation had issues, but continuing with plan execution...")
            
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

    def lint_plan(self, dry_run: bool = False) -> bool:
        """Validate the plan and optionally show execution order."""
        if not self.plan_path:
            print("Error: No plan loaded")
            return False
            
        schema_path = Path("schemas/PLAN_SCHEMA.json")
        if not schema_path.exists():
            print(f"Error: Schema file not found: {schema_path}")
            return False
            
        linter = PlanLinter(self.plan_path, schema_path)
        is_valid = linter.validate()
        
        linter.print_issues()
        
        if is_valid and dry_run:
            linter.print_dry_run()
            
        return is_valid

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='ARCH Plan Runner CLI')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run a plan')
    run_parser.add_argument('plan', help='Path to plan file (YAML)')
    run_parser.add_argument('--summary', '-s', action='store_true', 
                          help='Show plan summary without executing')
    run_parser.add_argument('--no-branch', action='store_true',
                          help='Skip automatic branch creation for plan tasks')
    run_parser.add_argument('--base-branch', '-b', default='main',
                          help='Base branch for creating new task branches (default: main)')
    
    # Lint command
    lint_parser = subparsers.add_parser('lint', help='Validate a plan')
    lint_parser.add_argument('plan', help='Path to plan file (YAML)')
    lint_parser.add_argument('--dry-run', action='store_true',
                           help='Show execution order and parallel groups')
    
    # Branch command for standalone branch creation
    branch_parser = subparsers.add_parser('branch', help='Create branches for plan tasks')
    branch_parser.add_argument('plan', help='Path to plan file (YAML)')
    branch_parser.add_argument('--base-branch', '-b', default='main',
                             help='Base branch for creating new task branches (default: main)')
    branch_parser.add_argument('--dry-run', '-n', action='store_true',
                             help='Show what branches would be created without creating them')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    runner = CLIRunner()
    
    # Load the plan
    if not runner.load_plan(args.plan):
        sys.exit(1)
    
    if args.command == 'run':
        # Get and display task summary
        tasks = runner.get_task_summary()
        runner.print_summary(tasks)
        
        # Execute the plan unless --summary flag is set
        if not args.summary:
            # Auto-branch creation is enabled by default, disabled with --no-branch
            create_branches = not args.no_branch
            success = runner.run_plan(
                create_branches=create_branches,
                base_branch=args.base_branch
            )
            sys.exit(0 if success else 1)
    elif args.command == 'lint':
        success = runner.lint_plan(dry_run=args.dry_run)
        sys.exit(0 if success else 1)
    elif args.command == 'branch':
        success = runner.create_branches_for_plan(
            base_branch=args.base_branch,
            dry_run=args.dry_run
        )
        sys.exit(0 if success else 1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
