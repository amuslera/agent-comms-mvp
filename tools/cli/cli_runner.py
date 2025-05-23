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
import shutil
import os

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from arch_orchestrator import ArchOrchestrator
from tools.cli.plan_linter import PlanLinter
from tools.arch.plan_runner import run_plan as run_plan_with_trace

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
    
    def run_plan(self, enable_trace_logging: bool = False) -> bool:
        """Execute the loaded plan and return success status."""
        # If trace logging is enabled, use the plan_runner directly
        if enable_trace_logging:
            print("[INFO] Using plan_runner with trace logging enabled")
            return run_plan_with_trace(self.plan_path, enable_trace_logging=True)
        
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
                          help='Show one-line summary per task (with or without execution)')
    run_parser.add_argument('--dry-run', action='store_true',
                          help='Preview execution plan, DAG, routing, and approvals without running any tasks')
    run_parser.add_argument('--log-trace', action='store_true',
                          help='Enable execution trace logging to JSON files')
    
    # Lint command
    lint_parser = subparsers.add_parser('lint', help='Validate a plan')
    lint_parser.add_argument('plan', help='Path to plan file (YAML)')
    lint_parser.add_argument('--dry-run', action='store_true',
                           help='Show execution order and parallel groups')

    # New-plan command
    new_plan_parser = subparsers.add_parser('new-plan', help='Create a new plan from a template')
    new_plan_parser.add_argument('name', help='Name for the new plan YAML file (no extension)')
    new_plan_parser.add_argument('--template', choices=['basic-single-agent', 'multi-agent-dag', 'approval-gated-flow'], required=True, help='Template to use for the new plan')

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'new-plan':
        # Copy the selected template to /plans/<name>.yaml
        template_map = {
            'basic-single-agent': 'basic-single-agent.yaml',
            'multi-agent-dag': 'multi-agent-dag.yaml',
            'approval-gated-flow': 'approval-gated-flow.yaml',
        }
        template_file = Path('plans/templates') / template_map[args.template]
        dest_file = Path('plans') / f"{args.name}.yaml"
        if dest_file.exists():
            print(f"Error: {dest_file} already exists.")
            sys.exit(1)
        if not template_file.exists():
            print(f"Error: Template file {template_file} not found.")
            sys.exit(1)
        shutil.copyfile(template_file, dest_file)
        print(f"✅ Created new plan: {dest_file}")
        print("You should now edit the plan to customize it for your use case.")
        try:
            import subprocess
            subprocess.run([os.environ.get('EDITOR', 'nano'), str(dest_file)])
        except Exception:
            print(f"Open {dest_file} in your preferred editor to continue.")
        sys.exit(0)
    
    runner = CLIRunner()
    
    # Load the plan
    if not runner.load_plan(getattr(args, 'plan', None)):
        sys.exit(1)
    
    if args.command == 'run':
        if args.dry_run:
            # Dry-run preview mode: no execution, just show plan structure
            from tools.arch.plan_utils import load_and_validate_plan, build_execution_dag
            plan_path = Path(args.plan)
            schema_path = Path('schemas/PLAN_SCHEMA.json')
            plan_dict = load_and_validate_plan(plan_path, schema_path)
            dag = build_execution_dag(plan_dict)
            print(f"\n=== DRY RUN: Execution Plan Preview for {plan_path.name} ===")
            print(f"Total tasks: {len(dag.nodes)}")
            print(f"Execution order: {dag.execution_order}")
            print(f"Execution layers (parallelizable):")
            for i, layer in enumerate(dag.get_execution_layers()):
                print(f"  Layer {i}: {layer}")
            print("\nAgent routing table:")
            for task_id in dag.execution_order:
                node = dag.nodes[task_id]
                print(f"  {task_id}: {node.agent} ({node.task_type})")
            print("\nTask approvals and blockers:")
            for task_id in dag.execution_order:
                node = dag.nodes[task_id]
                approval = node.content.get('approval', False)
                deps = node.dependencies
                blockers = [dep for dep in deps if dep not in dag.nodes]
                print(f"  {task_id}: approval={approval}, dependencies={deps}, blockers={blockers if blockers else 'None'}")
            if args.summary:
                print("\n--- SUMMARY (one-liner per task) ---")
                for task_id in dag.execution_order:
                    node = dag.nodes[task_id]
                    approval = node.content.get('approval', False)
                    deps = node.dependencies
                    print(f"{task_id} | agent={node.agent} | type={node.task_type} | deps={deps} | approval={approval}")
            print("\n(No tasks were executed. This is a dry-run preview.)\n")
            sys.exit(0)
        # Get and display task summary
        tasks = runner.get_task_summary()
        if args.summary:
            print("\n--- SUMMARY (one-liner per task) ---")
            for task in tasks:
                print(f"{task['task_id']} | agent={task['agent']} | type={task['type']} | status={task['status']} | retries={task['retries']} | score={task['score']}")
        else:
            runner.print_summary(tasks)
        # Execute the plan unless --summary or --dry-run flag is set
        if not args.summary and not args.dry_run:
            success = runner.run_plan(enable_trace_logging=args.log_trace)
            sys.exit(0 if success else 1)
        sys.exit(0)
    elif args.command == 'lint':
        success = runner.lint_plan(dry_run=args.dry_run)
        sys.exit(0 if success else 1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
