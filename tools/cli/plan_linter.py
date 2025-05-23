#!/usr/bin/env python3

import sys
import yaml
import argparse
import json
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Union, Literal

# Add parent directory to path to import plan_utils and lint_utils
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.arch.plan_utils import (
    ExecutionDAG, TaskNode, DAGValidationError,
    load_and_validate_plan, validate_dag_integrity
)
from tools.cli.lint_utils import (
    LintResult, ValidationIssue, ValidationLevel, 
    create_issue
)

# Type aliases
PathLike = Union[str, Path]

# Constants for validation
VALID_AGENTS = {'ARCH', 'CA', 'CC', 'WA'}
VALID_TASK_TYPES = {
    'task_assignment', 'data_processing', 'report_generation',
    'health_check', 'notification', 'validation', 'custom'
}


class PlanLinter:
    def __init__(self, plan_path: Path, schema_path: Path):
        self.plan_path = plan_path
        self.schema_path = schema_path
        self.lint_result = LintResult(plan_path)
        self.plan_dict: Optional[Dict[str, Any]] = None
        self.dag: Optional[ExecutionDAG] = None

    def validate(self) -> bool:
        """Run all validations and return True if plan is valid."""
        try:
            # Load and validate against schema
            self.plan_dict = load_and_validate_plan(self.plan_path, self.schema_path)
            
            # Update task count for summary
            if self.plan_dict and 'tasks' in self.plan_dict:
                self.lint_result.stats['total_tasks'] = len(self.plan_dict['tasks'])
            
            # Build DAG
            self.dag = ExecutionDAG(
                nodes={},
                edges={},
                reverse_edges={},
                root_nodes=[],
                leaf_nodes=[],
                execution_order=[]
            )
            
            # Run all validations
            self._validate_task_structure()
            self._validate_dependencies()
            self._validate_cycles()
            self._validate_unreachable()
            
            # Run DAG integrity check
            if self.dag:
                integrity_results = validate_dag_integrity(self.dag)
                if not integrity_results['is_valid']:
                    for error in integrity_results['errors']:
                        self.lint_result.add_issue(create_issue(
                            'error',
                            f"DAG validation error: {error}",
                            details={"type": "dag_validation"}
                        ))
                
                for warning in integrity_results.get('warnings', []):
                    self.lint_result.add_issue(create_issue(
                        'warning',
                        f"DAG validation warning: {warning}",
                        details={"type": "dag_validation"}
                    ))
            
            return not self.lint_result.has_errors
            
        except yaml.YAMLError as e:
            self.lint_result.add_issue(create_issue(
                'error',
                f"Failed to parse YAML: {str(e)}",
                details={"type": "yaml_parse_error"}
            ))
            return False
        except json.JSONDecodeError as e:
            self.lint_result.add_issue(create_issue(
                'error',
                f"Failed to parse JSON schema: {str(e)}",
                details={"type": "json_parse_error"}
            ))
            return False
        except FileNotFoundError as e:
            self.lint_result.add_issue(create_issue(
                'error',
                f"File not found: {str(e)}",
                details={"type": "file_not_found"}
            ))
            return False
        except Exception as e:
            self.lint_result.add_issue(create_issue(
                'error',
                f"Unexpected error during validation: {str(e)}",
                details={"type": "unexpected_error"}
            ))
            return False

    def _validate_task_structure(self):
        """Validate task structure and required fields with detailed feedback."""
        if not self.plan_dict or 'tasks' not in self.plan_dict:
            self.lint_result.add_issue(create_issue(
                'error',
                "Plan is missing required 'tasks' field",
                details={'type': 'missing_field', 'field': 'tasks'},
                suggestion="Ensure your plan has a 'tasks' list containing task definitions"
            ))
            return
            
        task_ids = set()
        for task in self.plan_dict['tasks']:
            # Check required fields
            if 'task_id' not in task:
                self.lint_result.add_issue(create_issue(
                    'error',
                    "Task is missing required field: task_id",
                    details={
                        'type': 'missing_field',
                        'field': 'task_id',
                        'task': {k: v for k, v in task.items() if k != 'dependencies'}
                    },
                    suggestion="Add a unique task_id to identify this task"
                ))
                continue
                
            task_id = task['task_id']
            
            # Check for duplicate task IDs
            if task_id in task_ids:
                self.lint_result.add_issue(create_issue(
                    'error',
                    f"Duplicate task_id: {task_id}",
                    task_id=task_id,
                    details={
                        'type': 'duplicate_task_id',
                        'existing_task_ids': list(task_ids)
                    },
                    suggestion=f"Rename one of the tasks to ensure all task_ids are unique"
                ))
                continue
            task_ids.add(task_id)
            
            # Check required fields first
            for field in ['agent', 'task_type', 'description']:
                if field not in task:
                    self.lint_result.add_issue(create_issue(
                        'error',
                        f"Task '{task_id}' is missing required field: {field}",
                        task_id=task_id,
                        field=field,
                        details={
                            'type': 'missing_field',
                            'field': field,
                            'required_fields': ['agent', 'task_type', 'description']
                        },
                        suggestion=f"Add the required '{field}' field to this task"
                    ))
            
            # Validate agent field if present
            agent = task.get('agent')
            if agent is not None:  # Field exists (may be empty)
                if not agent:  # Empty string
                    self.lint_result.add_issue(create_issue(
                        'error',
                        f"Task '{task_id}' has empty agent field",
                        task_id=task_id,
                        field='agent',
                        details={'type': 'empty_field', 'field': 'agent'},
                        suggestion="Specify a valid agent for this task"
                    ))
                elif agent not in VALID_AGENTS:  # Invalid agent value
                    self.lint_result.add_issue(create_issue(
                        'error',
                        f"Task '{task_id}' has invalid agent: '{agent}'",
                        task_id=task_id,
                        field='agent',
                        details={
                            'type': 'invalid_agent',
                            'valid_agents': sorted(VALID_AGENTS),
                            'actual_agent': agent
                        },
                        suggestion=f"Use one of: {', '.join(sorted(VALID_AGENTS))}"
                    ))
            
            # Validate task_type if present
            task_type = task.get('task_type')
            if task_type is not None:  # Field exists (may be empty)
                if not task_type:  # Empty string
                    self.lint_result.add_issue(create_issue(
                        'error',
                        f"Task '{task_id}' has empty task_type field",
                        task_id=task_id,
                        field='task_type',
                        details={'type': 'empty_field', 'field': 'task_type'},
                        suggestion="Specify a valid task type for this task"
                    ))
                elif task_type not in VALID_TASK_TYPES:  # Non-standard task type
                    self.lint_result.add_issue(create_issue(
                        'warning',
                        f"Task '{task_id}' has non-standard task_type: '{task_type}'",
                        task_id=task_id,
                        field='task_type',
                        details={
                            'type': 'non_standard_task_type',
                            'valid_task_types': sorted(VALID_TASK_TYPES),
                            'actual_task_type': task_type
                        },
                        suggestion="Consider using one of the standard task types or 'custom'"
                    ))
            
            # Validate description if present
            if 'description' in task:
                if not task['description']:  # Empty or None
                    self.lint_result.add_issue(create_issue(
                        'warning',
                        f"Task '{task_id}' has empty description",
                        task_id=task_id,
                        field='description',
                        details={'type': 'empty_field', 'field': 'description'},
                        suggestion="Add a meaningful description to explain what this task does"
                    ))
                elif not task['description'].strip():
                    self.lint_result.add_issue(create_issue(
                        'info',
                        f"Task '{task_id}' has a whitespace-only description",
                        task_id=task_id,
                        field='description',
                        details={'type': 'whitespace_description'},
                        suggestion="Consider adding a more descriptive text"
                    ))
            
            # Validate content field if present
            if 'content' in task and task['content'] is not None and not isinstance(task['content'], dict):
                self.lint_result.add_issue(create_issue(
                    'error',
                    f"Task '{task_id}' content must be an object",
                    task_id=task_id,
                    field='content',
                    details={
                        'type': 'invalid_content_type',
                        'expected_type': 'dict',
                        'actual_type': type(task['content']).__name__
                    },
                    suggestion="Ensure the content field is a valid YAML/JSON object"
                ))
            
            # Validate dependencies format if present
            if 'dependencies' in task and task['dependencies'] is not None and not isinstance(task['dependencies'], list):
                self.lint_result.add_issue(create_issue(
                    'error',
                    f"Task '{task_id}' has invalid dependencies format",
                    task_id=task_id,
                    field='dependencies',
                    details={
                        'type': 'invalid_dependencies_format',
                        'expected_type': 'list',
                        'actual_type': type(task['dependencies']).__name__
                    },
                    suggestion="Ensure dependencies is a list of task_ids"
                ))

    def _validate_dependencies(self):
        """Validate all dependencies reference existing tasks and check for circular deps."""
        if not self.plan_dict or 'tasks' not in self.plan_dict:
            return
            
        task_map = {task['task_id']: task for task in self.plan_dict['tasks'] if 'task_id' in task}
        
        for task_id, task in task_map.items():
            if 'dependencies' not in task:
                continue
                
            dependencies = task['dependencies']
            if not isinstance(dependencies, list):
                self.lint_result.add_issue(create_issue(
                    'error',
                    f"Task '{task_id}' has invalid dependencies format",
                    task_id=task_id,
                    field='dependencies',
                    actual=type(dependencies).__name__,
                    expected='list',
                    suggestion="Ensure dependencies is a list of task_ids"
                ))
                continue
                
            for dep in dependencies:
                if not isinstance(dep, str):
                    self.lint_result.add_issue(create_issue(
                        'error',
                        f"Task '{task_id}' has invalid dependency format",
                        task_id=task_id,
                        field='dependencies',
                        details={"invalid_dependency": dep},
                        suggestion="Dependencies must be strings (task_ids)"
                    ))
                    continue
                    
                if dep not in task_map:
                    self.lint_result.add_issue(create_issue(
                        'error',
                        f"Task '{task_id}' depends on non-existent task: '{dep}'",
                        task_id=task_id,
                        field='dependencies',
                        details={"missing_task": dep},
                        suggestion=f"Remove the dependency or add a task with task_id: '{dep}'"
                    ))
                
                # Check for self-dependencies
                if dep == task_id:
                    self.lint_result.add_issue(create_issue(
                        'error',
                        f"Task '{task_id}' depends on itself",
                        task_id=task_id,
                        field='dependencies',
                        details={"self_dependency": dep},
                        suggestion="Remove the self-referential dependency"
                    ))
                
                # Check for circular dependencies (basic check, full cycle detection is in _validate_cycles)
                if dep in task_map and task_id in task_map.get(dep, {}).get('dependencies', []):
                    self.lint_result.add_issue(create_issue(
                        'error',
                        f"Circular dependency detected between tasks: '{task_id}' and '{dep}'",
                        task_id=task_id,
                        field='dependencies',
                        details={"circular_with": dep},
                        suggestion="Break the circular dependency by restructuring the task dependencies"
                    ))

    def _validate_cycles(self):
        """Check for cycles in the dependency graph with detailed feedback."""
        if not self.dag or not self.plan_dict or 'tasks' not in self.plan_dict:
            return
            
        try:
            self.dag._validate_structure()
        except ValueError as e:
            error_msg = str(e)
            if "Cycle detected" in error_msg:
                # Extract cycle information if available
                cycle_info = error_msg
                if "Cycle: " in error_msg:
                    cycle_info = error_msg.split("Cycle: ")[1].strip("'")
                    
                self.lint_result.add_issue(create_issue(
                    'error',
                    "Circular dependency detected in task dependencies",
                    details={
                        'cycle': cycle_info,
                        'type': 'circular_dependency'
                    },
                    suggestion="Break the cycle by restructuring task dependencies. "
                            "Each task should form a directed acyclic graph (DAG)."
                ))
            else:
                self.lint_result.add_issue(create_issue(
                    'error',
                    f"DAG structure validation failed: {error_msg}",
                    details={'type': 'dag_validation'}
                ))

    def _validate_unreachable(self):
        """Check for tasks that are not reachable from any root task with detailed feedback."""
        if not self.dag or not self.plan_dict or 'tasks' not in self.plan_dict:
            return
            
        try:
            # Get all task IDs for reference
            all_task_ids = {task.get('task_id') for task in self.plan_dict['tasks'] 
                          if task.get('task_id')}
            
            # Find unreachable tasks
            unreachable = self.dag.find_unreachable_tasks()
            
            # Check if there are tasks with no dependencies and no dependents (potential roots/leaves)
            for task_id in unreachable:
                task = next((t for t in self.plan_dict['tasks'] 
                           if t.get('task_id') == task_id), None)
                
                if task:
                    has_deps = bool(task.get('dependencies'))
                    is_referenced = any(
                        task_id in t.get('dependencies', []) 
                        for t in self.plan_dict['tasks']
                    )
                    
                    if not has_deps and not is_referenced:
                        # This is a potential root task that's not referenced anywhere
                        self.lint_result.add_issue(create_issue(
                            'warning',
                            f"Task '{task_id}' is not connected to any other tasks",
                            task_id=task_id,
                            details={
                                'type': 'isolated_task',
                                'has_dependencies': has_deps,
                                'is_referenced': is_referenced
                            },
                            suggestion=(
                                "If this is a root task, consider adding it to the 'root_tasks' list. "
                                "If it should be connected to other tasks, add the appropriate dependencies."
                            )
                        ))
                    else:
                        # This task has dependencies but is unreachable
                        self.lint_result.add_issue(create_issue(
                            'warning',
                            f"Task '{task_id}' is unreachable from any root task",
                            task_id=task_id,
                            details={
                                'type': 'unreachable_task',
                                'has_dependencies': has_deps,
                                'is_referenced': is_referenced
                            },
                            suggestion=(
                                "Make sure this task is reachable by either:\n"
                                "1. Adding it as a dependency of another task, or\n"
                                "2. Marking it as a root task if it should be executed independently"
                            )
                        ))
                        
        except Exception as e:
            self.lint_result.add_issue(create_issue(
                'error',
                f"Error while checking for unreachable tasks: {str(e)}",
                details={"type": "unreachable_check_error"}
            ))

    def print_issues(self, output_format: str = 'text', output_file: Optional[Path] = None) -> None:
        """Print all validation issues using the lint result formatter.
        
        Args:
            output_format: The output format ('text' or 'json')
            output_file: Optional file path to write the output to
        """
        if output_format not in ['text', 'json']:
            raise ValueError(f"Invalid output format: {output_format}. Must be 'text' or 'json'.")
            
        # Get the formatted output from lint_result
        output = self.lint_result.get_formatted_output(format=output_format)
        
        # Write to file if specified, otherwise print to stdout
        if output_file:
            try:
                output_file = Path(output_file)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                with output_file.open('w') as f:
                    f.write(output)
                print(f"Lint results written to: {output_file}", file=sys.stderr)
            except Exception as e:
                print(f"Error writing to output file: {e}", file=sys.stderr)
        else:
            print(output)
            
        # Print summary
        self.lint_result.print_summary(output_format=output_format)

    def print_dry_run(self):
        """Print execution order and parallel groups."""
        if not self.dag:
            return
            
        print("\n📋 Dry Run Execution Plan:")
        layers = self.dag.get_execution_layers()
        
        for i, layer in enumerate(layers):
            print(f"\nLayer {i}:")
            for task_id in layer:
                node = self.dag.nodes[task_id]
                deps = ", ".join(node.dependencies) if node.dependencies else "none"
                print(f"  • {task_id} (agent: {node.agent}, deps: {deps})")

def main():
    """Main entry point for the plan linter CLI."""
    parser = argparse.ArgumentParser(
        description="Validate YAML plan files against the Bluelabel Agent OS schema",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Required arguments
    parser.add_argument(
        "plan_path", 
        type=Path,
        help="Path to the YAML plan file to validate"
    )
    
    # Optional arguments
    parser.add_argument(
        "--schema", 
        type=Path,
        default=Path(__file__).parent.parent.parent / "schemas" / "PLAN_SCHEMA.json",
        help="Path to the JSON schema file"
    )
    
    parser.add_argument(
        "--format",
        choices=['text', 'json'],
        default='text',
        help="Output format"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output file path (default: print to stdout)"
    )
    
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )
    
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Show execution order and parallel groups"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="count",
        default=0,
        help="Increase verbosity (can be used multiple times)"
    )
    
    args = parser.parse_args()
    
    # Configure color output
    if args.no_color:
        from colorama import init, reinit
        init(strip=True, convert=False)
        reinit()
    
    # Validate file paths
    if not args.plan_path.exists():
        print(f"Error: Plan file not found: {args.plan_path}", file=sys.stderr)
        sys.exit(1)
        
    if not args.schema.exists():
        print(f"Error: Schema file not found: {args.schema}", file=sys.stderr)
        sys.exit(1)
    
    # Run the linter
    linter = PlanLinter(args.plan_path, args.schema)
    is_valid = linter.validate()
    
    # Print or save the results
    linter.print_issues(
        output_format=args.format,
        output_file=args.output
    )
    
    # Show dry run if requested and no errors
    if is_valid and args.dry_run:
        linter.print_dry_run()
    
    # Exit with appropriate status code
    sys.exit(0 if is_valid else 1)

if __name__ == "__main__":
    main() 