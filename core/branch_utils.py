#!/usr/bin/env python3
"""
Branch Creation Utilities for YAML Plans

Automatically creates Git branches for tasks in YAML plans to enable
proper development workflow and tracking.
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import yaml
from datetime import datetime


class BranchCreationError(Exception):
    """Exception raised when branch creation fails."""
    pass


class GitBranchManager:
    """Manages Git branch creation and validation for YAML plan tasks."""
    
    def __init__(self, repository_path: str = "."):
        """Initialize with repository path."""
        self.repo_path = Path(repository_path).resolve()
        self._validate_git_repo()
    
    def _validate_git_repo(self) -> None:
        """Validate that we're in a Git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise BranchCreationError(f"Not a Git repository: {self.repo_path}")
    
    def _run_git_command(self, args: List[str]) -> Tuple[str, str]:
        """Run a Git command and return stdout, stderr."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip(), result.stderr.strip()
        except subprocess.CalledProcessError as e:
            raise BranchCreationError(f"Git command failed: {' '.join(args)}\n{e.stderr}")
    
    def _sanitize_task_id(self, task_id: str) -> str:
        """Sanitize task ID for use in branch names."""
        # Remove any characters that aren't alphanumeric, hyphens, or underscores
        sanitized = re.sub(r'[^a-zA-Z0-9\-_]', '-', task_id)
        # Remove consecutive hyphens
        sanitized = re.sub(r'-+', '-', sanitized)
        # Remove leading/trailing hyphens
        sanitized = sanitized.strip('-')
        # Convert to lowercase for consistency
        return sanitized.lower()
    
    def _create_branch_name(self, task_id: str, description: str = "") -> str:
        """Create a standardized branch name from task ID and optional description."""
        sanitized_task_id = self._sanitize_task_id(task_id)
        
        if description:
            # Sanitize description and limit length
            sanitized_desc = re.sub(r'[^a-zA-Z0-9\s\-_]', '', description)
            sanitized_desc = re.sub(r'\s+', '-', sanitized_desc.strip())
            sanitized_desc = sanitized_desc.lower()[:30]  # Limit to 30 chars
            sanitized_desc = sanitized_desc.strip('-')
            
            if sanitized_desc:
                return f"feat/{sanitized_task_id}-{sanitized_desc}"
        
        return f"feat/{sanitized_task_id}"
    
    def get_current_branch(self) -> str:
        """Get the current Git branch name."""
        stdout, _ = self._run_git_command(["branch", "--show-current"])
        return stdout
    
    def branch_exists(self, branch_name: str) -> bool:
        """Check if a branch exists locally."""
        try:
            self._run_git_command(["show-ref", "--verify", f"refs/heads/{branch_name}"])
            return True
        except BranchCreationError:
            return False
    
    def create_branch(self, branch_name: str, base_branch: str = "main") -> bool:
        """Create a new branch from the specified base branch."""
        if self.branch_exists(branch_name):
            print(f"⚠️  Branch '{branch_name}' already exists, skipping...")
            return False
        
        try:
            # Switch to base branch first to ensure it's up to date
            self._run_git_command(["checkout", base_branch])
            
            # Create and switch to new branch
            self._run_git_command(["checkout", "-b", branch_name])
            
            print(f"✅ Created branch: {branch_name}")
            return True
            
        except BranchCreationError as e:
            print(f"❌ Failed to create branch '{branch_name}': {e}")
            return False
    
    def extract_tasks_from_plan(self, plan_path: str) -> List[Dict[str, Any]]:
        """Extract task information from a YAML plan file."""
        plan_file = Path(plan_path)
        
        if not plan_file.exists():
            raise BranchCreationError(f"Plan file not found: {plan_path}")
        
        try:
            with open(plan_file, 'r', encoding='utf-8') as f:
                plan_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise BranchCreationError(f"Invalid YAML in plan file: {e}")
        
        if not isinstance(plan_data, dict):
            raise BranchCreationError("Plan file must contain a YAML object")
        
        tasks = plan_data.get('tasks', [])
        if not tasks:
            raise BranchCreationError("No tasks found in plan file")
        
        extracted_tasks = []
        for task in tasks:
            if not isinstance(task, dict):
                continue
            
            task_id = task.get('task_id', '')
            description = task.get('description', '')
            agent = task.get('agent', '')
            
            if task_id:
                extracted_tasks.append({
                    'task_id': task_id,
                    'description': description,
                    'agent': agent,
                    'branch_name': self._create_branch_name(task_id, description)
                })
        
        return extracted_tasks
    
    def create_branches_for_plan(
        self, 
        plan_path: str, 
        base_branch: str = "main",
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Create branches for all tasks in a YAML plan.
        
        Args:
            plan_path: Path to the YAML plan file
            base_branch: Base branch to create new branches from
            dry_run: If True, only show what would be created
            
        Returns:
            Dictionary with creation results
        """
        results = {
            'plan_file': plan_path,
            'base_branch': base_branch,
            'tasks_found': 0,
            'branches_created': 0,
            'branches_skipped': 0,
            'branches_failed': 0,
            'branch_details': [],
            'errors': []
        }
        
        try:
            # Extract tasks from plan
            tasks = self.extract_tasks_from_plan(plan_path)
            results['tasks_found'] = len(tasks)
            
            if not tasks:
                results['errors'].append("No valid tasks found in plan")
                return results
            
            # Store original branch to return to later
            original_branch = self.get_current_branch()
            
            if dry_run:
                print(f"\n🔍 DRY RUN: Would create the following branches from '{base_branch}':")
                print("-" * 70)
                
            # Create branches for each task
            for task in tasks:
                task_id = task['task_id']
                branch_name = task['branch_name']
                description = task['description']
                agent = task['agent']
                
                branch_detail = {
                    'task_id': task_id,
                    'branch_name': branch_name,
                    'agent': agent,
                    'description': description,
                    'created': False,
                    'skipped': False,
                    'error': None
                }
                
                if dry_run:
                    print(f"  📝 {task_id:<20} → {branch_name}")
                    print(f"     Agent: {agent}, Description: {description[:50]}{'...' if len(description) > 50 else ''}")
                    print()
                    branch_detail['created'] = True  # Would be created
                else:
                    # Actually create the branch
                    if self.create_branch(branch_name, base_branch):
                        branch_detail['created'] = True
                        results['branches_created'] += 1
                    elif self.branch_exists(branch_name):
                        branch_detail['skipped'] = True
                        results['branches_skipped'] += 1
                    else:
                        branch_detail['error'] = "Unknown error during creation"
                        results['branches_failed'] += 1
                
                results['branch_details'].append(branch_detail)
            
            # Return to original branch
            if not dry_run and original_branch:
                try:
                    self._run_git_command(["checkout", original_branch])
                    print(f"\n🔄 Returned to original branch: {original_branch}")
                except BranchCreationError as e:
                    results['errors'].append(f"Failed to return to original branch: {e}")
            
        except Exception as e:
            results['errors'].append(str(e))
        
        return results
    
    def print_summary(self, results: Dict[str, Any]) -> None:
        """Print a formatted summary of branch creation results."""
        print(f"\n" + "=" * 70)
        print(f"BRANCH CREATION SUMMARY")
        print("=" * 70)
        print(f"Plan file: {results['plan_file']}")
        print(f"Base branch: {results['base_branch']}")
        print(f"Tasks found: {results['tasks_found']}")
        print(f"Branches created: {results['branches_created']}")
        print(f"Branches skipped: {results['branches_skipped']}")
        print(f"Branches failed: {results['branches_failed']}")
        
        if results['errors']:
            print(f"\n❌ Errors:")
            for error in results['errors']:
                print(f"   {error}")
        
        if results['branch_details']:
            print(f"\n📋 Branch Details:")
            for detail in results['branch_details']:
                status_icon = "✅" if detail['created'] else ("⚠️" if detail['skipped'] else "❌")
                status_text = "created" if detail['created'] else ("skipped" if detail['skipped'] else "failed")
                print(f"   {status_icon} {detail['task_id']:<20} → {detail['branch_name']:<40} ({status_text})")
                if detail['error']:
                    print(f"      Error: {detail['error']}")
        
        print("=" * 70)


def main():
    """CLI entry point for branch creation utilities."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Create Git branches for YAML plan tasks')
    parser.add_argument('plan', help='Path to YAML plan file')
    parser.add_argument('--base-branch', '-b', default='main', 
                       help='Base branch to create new branches from (default: main)')
    parser.add_argument('--dry-run', '-n', action='store_true',
                       help='Show what would be created without actually creating branches')
    parser.add_argument('--repo-path', '-r', default='.',
                       help='Path to Git repository (default: current directory)')
    
    args = parser.parse_args()
    
    try:
        manager = GitBranchManager(args.repo_path)
        results = manager.create_branches_for_plan(
            args.plan, 
            args.base_branch, 
            args.dry_run
        )
        manager.print_summary(results)
        
        # Exit with error code if there were failures
        if results['errors'] or results['branches_failed'] > 0:
            sys.exit(1)
            
    except BranchCreationError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)


if __name__ == "__main__":
    main()