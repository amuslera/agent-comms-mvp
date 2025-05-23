#!/usr/bin/env python3

import sys
import yaml
import argparse
import json
from pathlib import Path
from typing import Dict, List, Set, Any, Optional

# Add parent directory to path to import plan_utils and lint_utils
sys.path.append(str(Path(__file__).parent.parent.parent))
from tools.arch.plan_utils import (
    ExecutionDAG, TaskNode, DAGValidationError,
    load_and_validate_plan, validate_dag_integrity
)
from tools.cli.lint_utils import LintResult, ValidationIssue, ValidationLevel, create_issue

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
        """Validate task structure and required fields."""
        if not self.plan_dict or 'tasks' not in self.plan_dict:
            return
            
        task_ids = set()
        valid_agents = {'ARCH', 'CA', 'CC', 'WA'}
        valid_task_types = {
            'task_assignment', 'data_processing', 'report_generation',
            'health_check', 'notification', 'validation', 'custom'
        }
        
        for i, task in enumerate(self.plan_dict['tasks'], 1):
            if not isinstance(task, dict):
                self.lint_result.add_issue(create_issue(
                    'error',
                    f"Task at position {i} is not a valid object",
                    details={"task_index": i},
                    suggestion="Each task must be a YAML/JSON object with required fields"
                ))
                continue
                
            task_id = task.get('task_id')
            
            # Check for required fields
            required_fields = ['task_id', 'agent', 'task_type', 'content']
            for field in required_fields:
                if field not in task:
                    self.lint_result.add_issue(create_issue(
                        'error',
                        f"Missing required field: '{field}'",
                        task_id=task_id,
                        field=field,
                        expected=f"A value for the {field} field",
                        suggestion=f"Add the {field} field to the task with a valid value"
                    ))
            
            # Skip further validation if we don't have a task_id
            if not task_id:
                continue
                
            # Check for duplicate task_id
            if task_id in task_ids:
                self.lint_result.add_issue(create_issue(
                    'error',
                    f"Duplicate task_id: '{task_id}'",
                    task_id=task_id,
                    field='task_id',
                    expected="Unique task identifier",
                    actual=f"Duplicate of task_id '{task_id}'",
                    suggestion=f"Rename one of the tasks to ensure all task_ids are unique"
                ))
            task_ids.add(task_id)
            
            # Validate agent field
            agent = task.get('agent')
            if agent and agent not in valid_agents:
                self.lint_result.add_issue(create_issue(
                    'error',
                    f"Invalid agent: '{agent}'",
                    task_id=task_id,
                    field='agent',
                    expected=f"One of: {', '.join(sorted(valid_agents))}",
                    actual=agent,
                    suggestion="Use one of the valid agent types: " + 
                              ", ".join(f"'{a}'" for a in sorted(valid_agents))
                ))
            
            # Validate task_type field
            task_type = task.get('task_type')
            if task_type and task_type not in valid_task_types:
                self.lint_result.add_issue(create_issue(
                    'warning',
                    f"Non-standard task_type: '{task_type}'",
                    task_id=task_id,
                    field='task_type',
                    expected=f"One of: {', '.join(sorted(valid_task_types))}",
                    actual=task_type,
                    suggestion="Consider using one of the standard task types or 'custom'"
                ))
            
            # Check for description (recommended but not required)
            if 'description' not in task or not task['description'].strip():
                self.lint_result.add_issue(create_issue(
                    'info',
                    f"Task '{task_id}' is missing a description",
                    task_id=task_id,
                    field='description',
                    suggestion="Add a clear description of what this task does"
                ))
            
            # Validate content field
            content = task.get('content')
            if content and not isinstance(content, dict):
                self.lint_result.add_issue(create_issue(
                    'error',
                    f"Task content must be an object",
                    task_id=task_id,
                    field='content',
                    expected="A YAML/JSON object",
                    actual=type(content).__name__,
                    suggestion="Ensure the content field is a valid YAML/JSON object"
                ))

    def _validate_dependencies(self):
        """Validate all dependencies reference existing tasks and check for circular deps."""
        if not self.plan_dict or 'tasks' not in self.plan_dict:
            return
            
        # Build a map of task_id to task for quick lookup
        task_map = {}
        for task in self.plan_dict['tasks']:
            if 'task_id' in task:
                task_map[task['task_id']] = task
        
        # Check each task's dependencies
        for task in self.plan_dict['tasks']:
            task_id = task.get('task_id')
            if not task_id:
                continue
                
            dependencies = task.get('dependencies', [])
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
            
            # Check each dependency
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
                details={'type': 'unreachable_check_error'}
            ))

    def print_issues(self):
        """Print all validation issues with color coding."""
        if not self.issues:
            print("✅ Plan is valid!")
            return
            
        for issue in self.issues:
            prefix = {
                ValidationLevel.INFO: "ℹ️ ",
                ValidationLevel.WARNING: "⚠️ ",
                ValidationLevel.ERROR: "❌ "
            }[issue.level]
            
            print(f"{prefix} {issue.message}")
            if issue.details:
                print(f"   Details: {json.dumps(issue.details, indent=2)}")

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
    parser = argparse.ArgumentParser(description="Validate and optionally dry-run YAML plans")
    parser.add_argument("plan_path", type=Path, help="Path to the plan YAML file")
    parser.add_argument("--dry-run", action="store_true", help="Show execution order and parallel groups")
    parser.add_argument("--schema", type=Path, default=Path("schemas/PLAN_SCHEMA.json"),
                      help="Path to the plan schema JSON file")
    
    args = parser.parse_args()
    
    if not args.plan_path.exists():
        print(f"Error: Plan file not found: {args.plan_path}")
        sys.exit(1)
        
    if not args.schema.exists():
        print(f"Error: Schema file not found: {args.schema}")
        sys.exit(1)
    
    linter = PlanLinter(args.plan_path, args.schema)
    is_valid = linter.validate()
    
    linter.print_issues()
    
    if is_valid and args.dry_run:
        linter.print_dry_run()
    
    sys.exit(0 if is_valid else 1)

if __name__ == "__main__":
    main() 