#!/usr/bin/env python3
"""
Context Inspector - CLI tool for viewing and modifying agent contexts.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, List, Any, Dict

# Add the parent directory to the path so we can import context_manager
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.context_manager import ContextManager

# ANSI color codes for terminal output
COLORS = {
    'HEADER': '\033[95m',
    'BLUE': '\033[94m',
    'CYAN': '\033[96m',
    'GREEN': '\033[92m',
    'WARNING': '\033[93m',
    'FAIL': '\033[91m',
    'ENDC': '\033[0m',
    'BOLD': '\033[1m',
    'UNDERLINE': '\033[4m',
}

def color_text(text: str, color: str) -> str:
    """Apply ANSI color to text if output is a terminal."""
    if sys.stdout.isatty() and color in COLORS:
        return f"{COLORS[color]}{text}{COLORS['ENDC']}"
    return text

def print_context(context: Dict[str, Any], indent: int = 0) -> None:
    """Pretty-print a context dictionary."""
    indent_str = ' ' * indent
    
    if not isinstance(context, dict):
        print(f"{indent_str}{context}")
        return
    
    for key, value in context.items():
        if isinstance(value, dict):
            print(f"{indent_str}{color_text(key, 'CYAN')}:")
            print_context(value, indent + 2)
        elif isinstance(value, list):
            print(f"{indent_str}{color_text(key, 'CYAN')}: [")
            for item in value:
                if isinstance(item, (dict, list)):
                    print_context(item, indent + 4)
                else:
                    print(f"{' ' * (indent + 4)}{item}")
            print(f"{indent_str}]")
        else:
            value_str = str(value)
            if len(value_str) > 80:  # Truncate long values
                value_str = value_str[:77] + '...'
            print(f"{indent_str}{color_text(key, 'CYAN')}: {value_str}")

def get_nested_value(data: Dict[str, Any], path: str) -> Any:
    """Get a nested value from a dictionary using dot notation."""
    keys = path.split('.')
    value = data
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    return value

def set_nested_value(data: Dict[str, Any], path: str, value: Any) -> bool:
    """Set a nested value in a dictionary using dot notation."""
    keys = path.split('.')
    current = data
    
    for i, key in enumerate(keys[:-1]):
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    
    # Handle JSON string values
    if isinstance(value, str):
        try:
            # Try to parse as JSON if it looks like a JSON object/array
            if (value.startswith('{') and value.endswith('}')) or \
               (value.startswith('[') and value.endswith(']')):
                value = json.loads(value)
            # Try to parse as int/float/bool if possible
            elif value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            elif value.isdigit():
                value = int(value)
            else:
                try:
                    float_val = float(value)
                    value = float_val
                except ValueError:
                    pass  # Keep as string
        except json.JSONDecodeError:
            pass  # Keep original value if JSON parsing fails
    
    current[keys[-1]] = value
    return True

def main():
    """Main entry point for the context inspector CLI."""
    parser = argparse.ArgumentParser(description='Inspect and modify agent contexts.')
    parser.add_argument('--agent', '-a', required=True, help='Agent ID (e.g., WA, CA, CC)')
    
    # Action group (mutually exclusive)
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('--view', '-v', action='store_true', help='View the entire context')
    action_group.add_argument('--get', '-g', metavar='PATH', help='Get a specific value using dot notation (e.g., preferences.theme)')
    action_group.add_argument('--set', '-s', nargs=2, metavar=('PATH', 'VALUE'), 
                            help='Set a value using dot notation (e.g., --set preferences.theme dark)')
    action_group.add_argument('--delete', '-d', metavar='PATH', help='Delete a key using dot notation')
    action_group.add_argument('--list-agents', action='store_true', help='List all available agent contexts')
    
    parser.add_argument('--context-dir', default='context', help='Directory containing context files (default: context)')
    parser.add_argument('--pretty', '-p', action='store_true', help='Pretty-print JSON output')
    
    args = parser.parse_args()
    
    manager = ContextManager(args.context_dir)
    
    if args.list_agents:
        context_dir = Path(args.context_dir)
        if not context_dir.exists():
            print("No context directory found.")
            return
            
        print(f"Available agent contexts in '{args.context_dir}':")
        for file in context_dir.glob('*_context.json'):
            agent_id = file.name.split('_context.json')[0]
            print(f"- {agent_id}")
        return
    
    try:
        if args.view:
            context = manager.load_context(args.agent)
            if args.pretty:
                print(json.dumps(context, indent=2))
            else:
                print_context(context)
        
        elif args.get:
            context = manager.load_context(args.agent)
            value = get_nested_value(context, args.get)
            if value is not None:
                if args.pretty and isinstance(value, (dict, list)):
                    print(json.dumps(value, indent=2))
                else:
                    print(value)
            else:
                print(f"Key '{args.get}' not found in context.", file=sys.stderr)
                sys.exit(1)
        
        elif args.set:
            path, value = args.set
            context = manager.load_context(args.agent)
            set_nested_value(context, path, value)
            if manager.save_context(args.agent, context):
                print(f"Updated {path} = {value}")
            else:
                print(f"Failed to update context for {args.agent}", file=sys.stderr)
                sys.exit(1)
        
        elif args.delete:
            context = manager.load_context(args.agent)
            keys = args.delete.split('.')
            current = context
            
            # Navigate to the parent of the key to delete
            for key in keys[:-1]:
                if key not in current or not isinstance(current[key], dict):
                    print(f"Key '{args.delete}' not found in context.", file=sys.stderr)
                    sys.exit(1)
                current = current[key]
            
            # Delete the key
            if keys[-1] in current:
                del current[keys[-1]]
                if manager.save_context(args.agent, context):
                    print(f"Deleted '{args.delete}' from context.")
                else:
                    print(f"Failed to save context after deletion.", file=sys.stderr)
                    sys.exit(1)
            else:
                print(f"Key '{args.delete}' not found in context.", file=sys.stderr)
                sys.exit(1)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
