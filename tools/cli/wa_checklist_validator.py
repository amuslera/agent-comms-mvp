#!/usr/bin/env python3
"""
WA Checklist Validation CLI

Provides a command-line interface for validating WA task compliance
and reviewing validation hooks.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.arch.wa_checklist_enforcer import WAChecklistEnforcer, validate_wa_task


class WAChecklistValidator:
    """CLI for WA checklist validation and compliance review."""
    
    def __init__(self):
        self.enforcer = WAChecklistEnforcer()
        self.validation_path = Path("logs/wa_validations")
    
    def list_validation_hooks(self) -> List[Dict[str, Any]]:
        """List all pending validation hooks."""
        if not self.validation_path.exists():
            return []
        
        hooks = []
        for hook_file in self.validation_path.glob("*.json"):
            with open(hook_file, 'r') as f:
                hook = json.load(f)
                hooks.append(hook)
        
        return sorted(hooks, key=lambda x: x.get('created_at', ''), reverse=True)
    
    def show_validation_hook(self, hook_id: str) -> Dict[str, Any]:
        """Show details of a specific validation hook."""
        hook_file = self.validation_path / f"{hook_id}.json"
        if not hook_file.exists():
            raise ValueError(f"Validation hook not found: {hook_id}")
        
        with open(hook_file, 'r') as f:
            return json.load(f)
    
    def validate_task_completion(self, task_id: str, branch: str, 
                               files_modified: List[str], 
                               screenshots: bool) -> Dict[str, Any]:
        """Validate a completed WA task against the checklist."""
        completion_data = {
            "branch": branch,
            "files_modified": files_modified,
            "screenshots_included": screenshots
        }
        
        return self.enforcer.validate_wa_task_completion(task_id, completion_data)
    
    def mark_hook_validated(self, hook_id: str, validation_status: str, notes: str = "") -> None:
        """Mark a validation hook as reviewed."""
        hook_file = self.validation_path / f"{hook_id}.json"
        if not hook_file.exists():
            raise ValueError(f"Validation hook not found: {hook_id}")
        
        with open(hook_file, 'r') as f:
            hook = json.load(f)
        
        hook['validation_status'] = validation_status
        hook['validated_at'] = datetime.now().isoformat()
        hook['validation_notes'] = notes
        
        with open(hook_file, 'w') as f:
            json.dump(hook, f, indent=2)
    
    def print_validation_summary(self, validation_result: Dict[str, Any]) -> None:
        """Print a formatted validation summary."""
        print("\n" + "=" * 60)
        print("WA CHECKLIST VALIDATION RESULTS")
        print("=" * 60)
        print(f"Task ID: {validation_result['task_id']}")
        print(f"Validation Time: {validation_result['validation_timestamp']}")
        print(f"Compliance Score: {validation_result['compliance_score']}")
        print(f"Compliant: {'✅ Yes' if validation_result['compliant'] else '❌ No'}")
        
        if validation_result['issues_found']:
            print("\n🚨 Issues Found:")
            for issue in validation_result['issues_found']:
                print(f"   - {issue}")
        
        if validation_result['recommendations']:
            print("\n💡 Recommendations:")
            for rec in validation_result['recommendations']:
                print(f"   - {rec}")
        
        print("=" * 60)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='WA Checklist Validation Tool')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # List hooks command
    list_parser = subparsers.add_parser('list', help='List pending validation hooks')
    list_parser.add_argument('--all', action='store_true', 
                           help='Show all hooks including validated ones')
    
    # Show hook command
    show_parser = subparsers.add_parser('show', help='Show validation hook details')
    show_parser.add_argument('hook_id', help='Validation hook ID')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate a completed WA task')
    validate_parser.add_argument('task_id', help='Task ID to validate')
    validate_parser.add_argument('--branch', required=True, help='Git branch name')
    validate_parser.add_argument('--files', nargs='+', required=True, 
                               help='List of modified files')
    validate_parser.add_argument('--screenshots', action='store_true',
                               help='Screenshots were included')
    
    # Mark reviewed command
    mark_parser = subparsers.add_parser('mark', help='Mark a validation hook as reviewed')
    mark_parser.add_argument('hook_id', help='Validation hook ID')
    mark_parser.add_argument('--status', choices=['approved', 'rejected', 'partial'],
                           required=True, help='Validation status')
    mark_parser.add_argument('--notes', default='', help='Validation notes')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    validator = WAChecklistValidator()
    
    try:
        if args.command == 'list':
            hooks = validator.list_validation_hooks()
            if not args.all:
                hooks = [h for h in hooks if h.get('validation_status') == 'pending']
            
            if not hooks:
                print("No pending validation hooks found.")
            else:
                print(f"\n{'ID':<40} {'Task ID':<15} {'Created':<20} {'Status'}")
                print("-" * 90)
                for hook in hooks:
                    hook_id = hook['hook_id']
                    task_id = hook['task_id']
                    created = hook['created_at'][:19]  # Trim milliseconds
                    status = hook.get('validation_status', 'pending')
                    print(f"{hook_id:<40} {task_id:<15} {created:<20} {status}")
        
        elif args.command == 'show':
            hook = validator.show_validation_hook(args.hook_id)
            print(f"\nValidation Hook: {hook['hook_id']}")
            print(f"Task ID: {hook['task_id']}")
            print(f"Created: {hook['created_at']}")
            print(f"Status: {hook.get('validation_status', 'pending')}")
            
            print("\nChecklist Items:")
            for category in hook['checklist_items']:
                print(f"\n{category['category']}:")
                for item in category['items']:
                    print(f"  □ {item}")
            
            if hook.get('validation_notes'):
                print(f"\nNotes: {hook['validation_notes']}")
        
        elif args.command == 'validate':
            result = validator.validate_task_completion(
                args.task_id, 
                args.branch,
                args.files,
                args.screenshots
            )
            validator.print_validation_summary(result)
        
        elif args.command == 'mark':
            validator.mark_hook_validated(args.hook_id, args.status, args.notes)
            print(f"✅ Validation hook {args.hook_id} marked as {args.status}")
            if args.notes:
                print(f"   Notes: {args.notes}")
    
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()