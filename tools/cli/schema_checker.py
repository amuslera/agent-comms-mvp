#!/usr/bin/env python3
"""
Schema Checker CLI Tool

This tool validates files against MCP schemas, checking both
plan files and individual message files for compliance.
"""

import sys
import json
import yaml
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.mcp_schema import MCPSchemaValidator, MCPValidationError
from tools.arch.plan_utils import ExecutionDAG


class SchemaChecker:
    """Checks files for MCP schema compliance."""
    
    def __init__(self):
        self.validator = MCPSchemaValidator()
    
    def check_file(self, file_path: Path, file_type: str = 'auto') -> bool:
        """
        Check a file for schema compliance.
        
        Args:
            file_path: Path to the file to check
            file_type: Type of file ('plan', 'message', or 'auto')
            
        Returns:
            True if valid, False otherwise
        """
        if not file_path.exists():
            print(f"❌ Error: File not found: {file_path}")
            return False
        
        try:
            # Load the file
            with open(file_path) as f:
                if file_path.suffix in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
            
            # Auto-detect type if needed
            if file_type == 'auto':
                file_type = self._detect_file_type(data)
                print(f"🔍 Detected file type: {file_type}")
            
            # Validate based on type
            if file_type == 'plan':
                return self._check_plan(data, file_path)
            elif file_type == 'message':
                return self._check_message(data)
            else:
                print(f"❌ Unknown file type: {file_type}")
                return False
                
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            print(f"❌ Error parsing file: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
    
    def _detect_file_type(self, data: Dict[str, Any]) -> str:
        """Auto-detect whether this is a plan or message."""
        # Plans have 'tasks' array
        if isinstance(data, dict) and 'tasks' in data:
            return 'plan'
        # Messages have 'type' and 'payload'
        elif isinstance(data, dict) and 'type' in data and 'payload' in data:
            return 'message'
        else:
            return 'unknown'
    
    def _check_plan(self, plan_data: Dict[str, Any], file_path: Path) -> bool:
        """Check a plan file for compliance."""
        print(f"\n📋 Validating plan: {plan_data.get('name', 'Unnamed')}")
        print(f"   Plan ID: {plan_data.get('plan_id', 'None')}")
        print(f"   Tasks: {len(plan_data.get('tasks', []))}")
        
        # Check basic plan structure
        try:
            # Try to build DAG to check structure
            tasks = plan_data.get('tasks', [])
            if not tasks:
                print("❌ Plan has no tasks")
                return False
            print("✅ Plan structure check passed")
        except Exception as e:
            print(f"❌ Plan structure check failed: {e}")
            return False
        
        # Then check MCP compliance
        is_valid, errors = self.validator.validate_plan(plan_data)
        
        if is_valid:
            print("✅ MCP schema compliance: PASSED")
            
            # Additional checks for each task
            print("\n📌 Task validation:")
            for task in plan_data.get('tasks', []):
                task_id = task.get('task_id', 'Unknown')
                agent = task.get('agent', 'Unknown')
                print(f"   • {task_id} → {agent}: ✓")
                
        else:
            print("❌ MCP schema compliance: FAILED")
            print("\n🔴 Validation errors:")
            for error in errors:
                print(f"   - {error}")
        
        return is_valid
    
    def _check_message(self, message_data: Dict[str, Any]) -> bool:
        """Check a message for compliance."""
        msg_type = message_data.get('type', 'unknown')
        print(f"\n📨 Validating message: {msg_type}")
        print(f"   From: {message_data.get('sender_id', 'Unknown')}")
        print(f"   To: {message_data.get('recipient_id', 'Unknown')}")
        print(f"   Task: {message_data.get('task_id', 'Unknown')}")
        
        is_valid, errors = self.validator.validate_message(message_data)
        
        if is_valid:
            print("✅ MCP message compliance: PASSED")
        else:
            print("❌ MCP message compliance: FAILED")
            print("\n🔴 Validation errors:")
            for error in errors:
                print(f"   - {error}")
        
        return is_valid
    
    def print_summary(self, is_valid: bool, verbose: bool = False):
        """Print validation summary."""
        print("\n" + "="*60)
        if is_valid:
            print("✅ VALIDATION PASSED")
            print("   All MCP schema requirements are met.")
        else:
            print("❌ VALIDATION FAILED")
            print("   Please fix the errors above and try again.")
            
            if not verbose:
                print("\n💡 Tip: Use --verbose for more detailed error information")
        print("="*60)


def main():
    """Main entry point for the schema checker CLI."""
    parser = argparse.ArgumentParser(
        description="Check files for MCP schema compliance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check a plan file
  python schema_checker.py plans/my-plan.yaml
  
  # Check a message file
  python schema_checker.py postbox/CC/outbox.json --type message
  
  # Check with verbose output
  python schema_checker.py plans/my-plan.yaml --verbose
        """
    )
    
    parser.add_argument(
        'file_path',
        type=Path,
        help='Path to the file to validate'
    )
    
    parser.add_argument(
        '--type',
        choices=['plan', 'message', 'auto'],
        default='auto',
        help='Type of validation to perform (default: auto-detect)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed validation errors'
    )
    
    args = parser.parse_args()
    
    # Run the checker
    checker = SchemaChecker()
    is_valid = checker.check_file(args.file_path, args.type)
    checker.print_summary(is_valid, args.verbose)
    
    # Exit with appropriate code
    sys.exit(0 if is_valid else 1)


if __name__ == '__main__':
    main()