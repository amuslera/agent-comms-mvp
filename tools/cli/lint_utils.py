#!/usr/bin/env python3

import sys
import json
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Union, Literal
from dataclasses import dataclass, asdict
from enum import Enum
import yaml
from colorama import init, Fore, Style, Back

# Initialize colorama
init(autoreset=True)

class ValidationLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

@dataclass
class ValidationIssue:
    level: ValidationLevel
    message: str
    task_id: Optional[str] = None
    field: Optional[str] = None
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    suggestion: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON output."""
        return {
            'level': self.level.value,
            'message': self.message,
            'task_id': self.task_id,
            'field': self.field,
            'expected': self.expected,
            'actual': self.actual,
            'suggestion': self.suggestion,
            'details': self.details
        }

class LintResult:
    def __init__(self, plan_path: Union[str, Path]):
        self.plan_path = Path(plan_path)
        self.issues: List[ValidationIssue] = []
        self.stats = {
            'total_tasks': 0,
            'tasks_with_issues': set(),
            'error_count': 0,
            'warning_count': 0,
            'info_count': 0
        }
    
    def add_issue(self, issue: ValidationIssue):
        self.issues.append(issue)
        if issue.task_id:
            self.stats['tasks_with_issues'].add(issue.task_id)
        
        if issue.level == ValidationLevel.ERROR:
            self.stats['error_count'] += 1
        elif issue.level == ValidationLevel.WARNING:
            self.stats['warning_count'] += 1
        else:
            self.stats['info_count'] += 1
    
    @property
    def has_errors(self) -> bool:
        return self.stats['error_count'] > 0
    
    @property
    def has_warnings(self) -> bool:
        return self.stats['warning_count'] > 0
    
    def group_by_task(self) -> Dict[Optional[str], List[ValidationIssue]]:
        """Group issues by task_id."""
        grouped = {}
        for issue in self.issues:
            if issue.task_id not in grouped:
                grouped[issue.task_id] = []
            grouped[issue.task_id].append(issue)
        return grouped
    
    def print_summary(self, output_format: str = 'text') -> None:
        """Print a summary of the linting results."""
        if output_format == 'json':
            self._print_json_summary()
        else:
            self._print_text_summary()
    
    def _print_text_summary(self) -> None:
        """Print a human-readable summary of the linting results."""
        print(f"\n{Style.BRIGHT}📋 Lint Summary for {self.plan_path.name}{Style.RESET_ALL}")
        print(f"  {Style.BRIGHT}Tasks:{Style.RESET_ALL} {self.stats['total_tasks']} total, "
              f"{len(self.stats['tasks_with_issues'])} with issues")
        
        # Print issue counts with colors
        error_str = f"{Fore.RED if self.stats['error_count'] > 0 else ''}{self.stats['error_count']} errors{Style.RESET_ALL}"
        warn_str = f"{Fore.YELLOW if self.stats['warning_count'] > 0 else ''}{self.stats['warning_count']} warnings{Style.RESET_ALL}"
        info_str = f"{Fore.CYAN}{self.stats['info_count']} info{Style.RESET_ALL}"
        
        print(f"  {Style.BRIGHT}Issues:{Style.RESET_ALL} {error_str}, {warn_str}, {info_str}")
        
        if not self.issues:
            print(f"\n{Fore.GREEN}✅ No issues found!{Style.RESET_ALL}")
            return
        
        # Group issues by task_id
        grouped_issues = self.group_by_task()
        
        # Print issues for each task
        for task_id, issues in sorted(grouped_issues.items(), key=lambda x: (x[0] is None, x[0] or '')):
            if task_id is None:
                print(f"\n{Style.BRIGHT}📄 Plan-level issues:{Style.RESET_ALL}")
            else:
                print(f"\n{Style.BRIGHT}📌 Task: {task_id}{Style.RESET_ALL}")
            
            for issue in issues:
                # Choose icon and color based on issue level
                if issue.level == ValidationLevel.ERROR:
                    icon = "❌"
                    color = Fore.RED
                elif issue.level == ValidationLevel.WARNING:
                    icon = "⚠️"
                    color = Fore.YELLOW
                else:
                    icon = "ℹ️"
                    color = Fore.CYAN
                
                # Print main message
                print(f"  {color}{icon} {issue.message}{Style.RESET_ALL}")
                
                # Print field and expected/actual if available
                if issue.field:
                    print(f"     {Style.DIM}field:{Style.RESET_ALL} {issue.field}")
                if issue.expected is not None:
                    print(f"     {Style.DIM}expected:{Style.RESET_ALL} {issue.expected}")
                if issue.actual is not None:
                    print(f"     {Style.DIM}found:{Style.RESET_ALL} {issue.actual}")
                
                # Print suggestion if available
                if issue.suggestion:
                    print(f"     {Fore.GREEN}💡 Suggestion: {issue.suggestion}{Style.RESET_ALL}")
                
                # Print any additional details
                if issue.details:
                    print(f"     {Style.DIM}details: {json.dumps(issue.details, indent=4).replace('\n', '\n     ')}")
    
    def _print_json_summary(self) -> None:
        """Print a JSON summary of the linting results."""
        result = {
            'plan': str(self.plan_path),
            'stats': {
                'total_tasks': self.stats['total_tasks'],
                'tasks_with_issues': len(self.stats['tasks_with_issues']),
                'issues': {
                    'error': self.stats['error_count'],
                    'warning': self.stats['warning_count'],
                    'info': self.stats['info_count']
                }
            },
            'issues': [issue.to_dict() for issue in self.issues]
        }
        print(json.dumps(result, indent=2))

def create_issue(
    level: Union[ValidationLevel, str],
    message: str,
    task_id: Optional[str] = None,
    field: Optional[str] = None,
    expected: Any = None,
    actual: Any = None,
    suggestion: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> ValidationIssue:
    """Helper function to create a validation issue with consistent formatting."""
    if isinstance(level, str):
        level = ValidationLevel[level.upper()]
    
    return ValidationIssue(
        level=level,
        message=message,
        task_id=task_id,
        field=field,
        expected=expected,
        actual=actual,
        suggestion=suggestion,
        details=details
    )
