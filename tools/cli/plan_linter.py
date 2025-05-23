#!/usr/bin/env python3

import sys
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json

# Add parent directory to path to import plan_utils
sys.path.append(str(Path(__file__).parent.parent.parent))
from tools.arch.plan_utils import (
    ExecutionDAG, TaskNode, DAGValidationError,
    load_and_validate_plan, validate_dag_integrity
)

class ValidationLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

@dataclass
class ValidationIssue:
    level: ValidationLevel
    message: str
    task_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class PlanLinter:
    def __init__(self, plan_path: Path, schema_path: Path):
        self.plan_path = plan_path
        self.schema_path = schema_path
        self.issues: List[ValidationIssue] = []
        self.plan_dict: Optional[Dict[str, Any]] = None
        self.dag: Optional[ExecutionDAG] = None

    def validate(self) -> bool:
        """Run all validations and return True if plan is valid."""
        try:
            # Load and validate against schema
            self.plan_dict = load_and_validate_plan(self.plan_path, self.schema_path)
            
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
            self._validate_task_ids()
            self._validate_dependencies()
            self._validate_cycles()
            self._validate_unreachable()
            
            # Run DAG integrity check
            if self.dag:
                integrity_results = validate_dag_integrity(self.dag)
                if not integrity_results['is_valid']:
                    for error in integrity_results['errors']:
                        self.issues.append(ValidationIssue(
                            level=ValidationLevel.ERROR,
                            message=error
                        ))
                for warning in integrity_results['warnings']:
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        message=warning
                    ))
            
            return len([i for i in self.issues if i.level == ValidationLevel.ERROR]) == 0
            
        except Exception as e:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                message=f"Failed to validate plan: {str(e)}"
            ))
            return False

    def _validate_task_ids(self):
        """Check for unique task IDs."""
        if not self.plan_dict:
            return
            
        task_ids = set()
        for task in self.plan_dict.get('tasks', []):
            task_id = task.get('task_id')
            if not task_id:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message="Task missing task_id",
                    details={"task": task}
                ))
                continue
                
            if task_id in task_ids:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message=f"Duplicate task_id: {task_id}",
                    task_id=task_id
                ))
            task_ids.add(task_id)

    def _validate_dependencies(self):
        """Validate all dependencies reference existing tasks."""
        if not self.plan_dict:
            return
            
        task_ids = {task['task_id'] for task in self.plan_dict.get('tasks', [])}
        for task in self.plan_dict.get('tasks', []):
            task_id = task.get('task_id')
            for dep in task.get('dependencies', []):
                if dep not in task_ids:
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.ERROR,
                        message=f"Task '{task_id}' depends on non-existent task '{dep}'",
                        task_id=task_id,
                        details={"dependency": dep}
                    ))

    def _validate_cycles(self):
        """Check for cycles in the dependency graph."""
        if not self.dag:
            return
            
        try:
            self.dag._validate_structure()
        except ValueError as e:
            if "Cycle detected" in str(e):
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message=str(e)
                ))

    def _validate_unreachable(self):
        """Check for unreachable tasks."""
        if not self.dag:
            return
            
        all_referenced = set()
        for node in self.dag.nodes.values():
            all_referenced.update(node.dependencies)
        for dependents in self.dag.edges.values():
            all_referenced.update(dependents)
            
        unreachable = set(self.dag.nodes.keys()) - all_referenced - set(self.dag.root_nodes)
        for task_id in unreachable:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message=f"Unreachable task: {task_id}",
                task_id=task_id
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