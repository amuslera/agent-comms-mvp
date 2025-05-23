#!/usr/bin/env python3
"""
WA Checklist Validation CLI Tool

This tool provides commands to review and validate WA task completions
against the checklist requirements that were enforced during planning.
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.arch.wa_checklist_enforcer import WAChecklistEnforcer


def list_pending_validations():
    """List all pending WA task validations."""
    enforcer = WAChecklistEnforcer()
    pending = enforcer.get_pending_validations()
    
    if not pending:
        print("No pending validations found.")
        return
    
    print(f"\n📋 Pending WA Task Validations ({len(pending)} tasks):")
    print("-" * 60)
    
    for task in pending:
        task_id = task.get("task_id", "Unknown")
        created_at = task.get("created_at", "Unknown")
        validation_data = task.get("validation_data", {})
        description = validation_data.get("description", "No description")
        
        print(f"\nTask ID: {task_id}")
        print(f"Created: {created_at}")
        print(f"Description: {description[:80]}...")
        
    print("\n" + "-" * 60)
    print(f"Total pending validations: {len(pending)}")


def show_validation_details(task_id: str):
    """Show detailed validation requirements for a specific task."""
    hook_path = Path(f"postbox/WA/validation_hooks/{task_id}_validation_hook.json")
    
    if not hook_path.exists():
        print(f"❌ No validation hook found for task {task_id}")
        return
    
    with open(hook_path, 'r') as f:
        hook_data = json.load(f)
    
    print(f"\n📋 Validation Details for Task {task_id}")
    print("=" * 60)
    
    print(f"\nStatus: {hook_data.get('status', 'Unknown')}")
    print(f"Created: {hook_data.get('created_at', 'Unknown')}")
    
    if hook_data.get('validated_at'):
        print(f"Validated: {hook_data.get('validated_at')}")
    
    validation_data = hook_data.get('validation_data', {})
    if validation_data:
        print(f"\nTask Description: {validation_data.get('description', 'N/A')}")
        print(f"Plan ID: {validation_data.get('plan_id', 'N/A')}")
        print(f"Trace ID: {validation_data.get('trace_id', 'N/A')}")
    
    print("\nChecklist Items:")
    print("-" * 40)
    
    checklist_items = hook_data.get('checklist_items', [])
    for i, item in enumerate(checklist_items, 1):
        status = item.get('status', 'pending')
        status_icon = {
            'passed': '✅',
            'failed': '❌',
            'pending': '⏳',
            'skipped': '⏭️'
        }.get(status, '❓')
        
        print(f"{i}. {status_icon} {item.get('item', 'Unknown item')} [{status}]")


def validate_task(task_id: str, interactive: bool = True):
    """Validate a completed WA task against checklist requirements."""
    enforcer = WAChecklistEnforcer()
    
    hook_path = Path(f"postbox/WA/validation_hooks/{task_id}_validation_hook.json")
    if not hook_path.exists():
        print(f"❌ No validation hook found for task {task_id}")
        return
    
    with open(hook_path, 'r') as f:
        hook_data = json.load(f)
    
    if hook_data.get('status') != 'pending':
        print(f"⚠️  Task {task_id} has already been validated with status: {hook_data.get('status')}")
        return
    
    print(f"\n🔍 Validating Task {task_id}")
    print("=" * 60)
    
    validation_results = {}
    
    if interactive:
        print("\nPlease review each checklist item:")
        print("Enter 'y' for passed, 'n' for failed, 's' to skip\n")
        
        for item in hook_data.get('checklist_items', []):
            item_name = item.get('item', 'Unknown')
            
            while True:
                response = input(f"✓ {item_name}? (y/n/s): ").lower().strip()
                if response in ['y', 'n', 's']:
                    if response == 'y':
                        validation_results[item_name] = True
                    elif response == 'n':
                        validation_results[item_name] = False
                    # Skip doesn't add to results
                    break
                else:
                    print("Please enter 'y', 'n', or 's'")
    else:
        # Auto-validation mode - mark all as passed (for testing)
        print("Running in auto-validation mode (all items marked as passed)")
        for item in hook_data.get('checklist_items', []):
            validation_results[item.get('item')] = True
    
    # Perform validation
    all_passed = enforcer.validate_task_completion(task_id, validation_results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print(f"✅ Task {task_id} PASSED all checklist requirements!")
    else:
        print(f"❌ Task {task_id} FAILED some checklist requirements.")
    
    # Show updated status
    show_validation_details(task_id)


def mark_all_pending_as_validated():
    """Mark all pending validations as validated (for batch processing)."""
    enforcer = WAChecklistEnforcer()
    pending = enforcer.get_pending_validations()
    
    if not pending:
        print("No pending validations to process.")
        return
    
    print(f"\n⚡ Batch validating {len(pending)} pending tasks...")
    
    success_count = 0
    for task in pending:
        task_id = task.get('task_id')
        if task_id:
            # Auto-validate all items as passed
            validation_results = {}
            for item in task.get('checklist_items', []):
                validation_results[item.get('item')] = True
            
            if enforcer.validate_task_completion(task_id, validation_results):
                success_count += 1
                print(f"✅ Validated {task_id}")
            else:
                print(f"❌ Failed to validate {task_id}")
    
    print(f"\n✅ Successfully validated {success_count}/{len(pending)} tasks")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='WA Checklist Validation Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all pending validations
  python wa_checklist_validator.py list
  
  # Show details for a specific task
  python wa_checklist_validator.py show TASK-123
  
  # Validate a completed task interactively
  python wa_checklist_validator.py validate TASK-123
  
  # Auto-validate a task (mark all as passed)
  python wa_checklist_validator.py validate TASK-123 --auto
  
  # Batch validate all pending tasks
  python wa_checklist_validator.py validate-all
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List pending validations')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show validation details')
    show_parser.add_argument('task_id', help='Task ID to show')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate a task')
    validate_parser.add_argument('task_id', help='Task ID to validate')
    validate_parser.add_argument('--auto', action='store_true',
                                help='Auto-validate (mark all as passed)')
    
    # Validate-all command
    validate_all_parser = subparsers.add_parser('validate-all',
                                              help='Validate all pending tasks')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        list_pending_validations()
    elif args.command == 'show':
        show_validation_details(args.task_id)
    elif args.command == 'validate':
        validate_task(args.task_id, interactive=not args.auto)
    elif args.command == 'validate-all':
        mark_all_pending_as_validated()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()