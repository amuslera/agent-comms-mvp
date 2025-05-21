import json
import time
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Set, Any, Union
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.box import ROUNDED
from rich.console import Group, RenderableType

from ..layout.styles import get_agent_style, get_status_style, create_table, create_panel, console
from ..dashboard_config import config

class LiveTasks:
    """Component to display live task status."""
    
    STATUS_ICONS = {
        "completed": "✅",
        "in_progress": "🔄",
        "failed": "❌",
        "pending": "⏳",
        "cancelled": "⏹️",
        "timeout": "⏱️ "
    }
    
    # How long to keep completed/failed tasks in the list (in seconds)
    TASK_RETENTION = 3600 * 4  # 4 hours
    
    def __init__(self):
        self.tasks: List[Dict] = []
        self.last_updated: Optional[datetime] = None
        self._last_file_mtimes: Dict[Path, float] = {}
        self._filtered_agents: Set[str] = set()
        self._filtered_statuses: Set[str] = set()
        self._visible_tasks: List[Dict] = []
        self._scroll_position: int = 0
        self._show_archived: bool = False
        
    @property
    def postbox_dir(self) -> Path:
        """Get the current postbox directory."""
        return config.postbox_dir
        
    @property
    def filtered_agents(self) -> Set[str]:
        """Get the set of filtered agent IDs."""
        return self._filtered_agents
        
    @filtered_agents.setter
    def filtered_agents(self, agents: Set[str]) -> None:
        """Set the filtered agent IDs."""
        self._filtered_agents = {a.upper() for a in agents}
        self._update_visible_tasks()
    
    def toggle_archived(self) -> None:
        """Toggle display of archived (completed/failed) tasks."""
        self._show_archived = not self._show_archived
        self._update_visible_tasks()
    
    def _update_visible_tasks(self) -> None:
        """Update the list of visible tasks based on filters."""
        self._visible_tasks = []
        
        for task in self.tasks:
            task_agent = task.get("agent")
            task_status = task.get("status")
            
            # Apply agent filter
            if self._filtered_agents and task_agent not in self._filtered_agents:
                continue
                
            # Apply status filter
            if self._filtered_statuses and task_status not in self._filtered_statuses:
                continue
                
            # Apply archived filter
            if not self._show_archived and task_status in ["completed", "failed", "cancelled"]:
                continue
                
            self._visible_tasks.append(task)
        
        # Ensure scroll position is valid
        self._scroll_position = max(0, min(self._scroll_position, len(self._visible_tasks) - 1))
    
    def scroll_up(self, lines: int = 1) -> None:
        """Scroll up in the task list."""
        self._scroll_position = max(0, self._scroll_position - lines)
    
    def scroll_down(self, lines: int = 1) -> None:
        """Scroll down in the task list."""
        if self._visible_tasks:
            self._scroll_position = min(
                len(self._visible_tasks) - 1,
                self._scroll_position + lines
            )
    
    def scroll_to_top(self) -> None:
        """Scroll to the top of the task list."""
        self._scroll_position = 0
    
    def scroll_to_bottom(self) -> None:
        """Scroll to the bottom of the task list."""
        if self._visible_tasks:
            self._scroll_position = len(self._visible_tasks) - 1
    
    def _has_changes(self) -> bool:
        """Check if any task log files have changed."""
        if not self.postbox_dir.exists():
            return False
            
        # Check for new or modified task logs
        for agent_dir in self.postbox_dir.iterdir():
            if not agent_dir.is_dir():
                continue
                
            task_log = agent_dir / "task_log.md"
            if not task_log.exists():
                continue
                
            try:
                mtime = task_log.stat().st_mtime
                if task_log not in self._last_file_mtimes or \
                   self._last_file_mtimes[task_log] < mtime:
                    return True
            except (OSError, AttributeError):
                continue
                
        return False
    
    def _parse_task_log(self, agent_dir: Path) -> List[Dict]:
        """Parse task log for a specific agent."""
        task_log = agent_dir / "task_log.md"
        tasks = []
        
        if not task_log.exists():
            return tasks
            
        try:
            # Update last modified time
            self._last_file_mtimes[task_log] = task_log.stat().st_mtime
            
            with open(task_log, 'r', encoding='utf-8') as f:
                current_task = None
                line_number = 0
                
                for line in f:
                    line_number += 1
                    try:
                        line = line.strip()
                        if not line:  # Skip empty lines
                            continue
                            
                        if line.startswith("## "):  # Task header
                            if current_task:  # Save previous task if exists
                                tasks.append(current_task)
                                
                            # Extract task ID and status
                            parts = line[3:].split(" - ", 1)  # Split on first ' - ' only
                            task_id = parts[0].strip()
                            status = parts[1].lower().strip() if len(parts) > 1 else "pending"
                            
                            current_task = {
                                "task_id": task_id,
                                "status": status,
                                "agent": agent_dir.name.upper(),
                                "start_time": None,
                                "end_time": None,
                                "retries": 0,
                                "fallback": None,
                                "details": [],
                                "created_at": datetime.now(timezone.utc),
                                "updated_at": datetime.now(timezone.utc),
                                "source_file": str(task_log),
                                "source_line": line_number
                            }
                            
                        elif current_task and line.startswith("-"):
                            # Remove the leading '-' and any whitespace
                            clean_line = line[1:].strip()
                            if not clean_line:  # Skip empty list items
                                continue
                                
                            current_task["details"].append(clean_line)
                            
                            # Extract metadata
                            try:
                                if "Started at:" in clean_line:
                                    time_str = clean_line.split("Started at: ", 1)[1].strip()
                                    dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                                    # Make timezone-aware if not already
                                    if dt.tzinfo is None:
                                        dt = dt.replace(tzinfo=timezone.utc)
                                    current_task["start_time"] = dt
                                    current_task["updated_at"] = dt
                                elif "Retry count:" in clean_line:
                                    current_task["retries"] = int(clean_line.split("Retry count: ", 1)[1].strip())
                                elif "Fallback to:" in clean_line:
                                    current_task["fallback"] = clean_line.split("Fallback to: ", 1)[1].strip()
                                elif "Completed at:" in clean_line:
                                    time_str = clean_line.split("Completed at: ", 1)[1].strip()
                                    dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                                    if dt.tzinfo is None:
                                        dt = dt.replace(tzinfo=timezone.utc)
                                    current_task["end_time"] = dt
                                    current_task["status"] = "completed"
                                    current_task["updated_at"] = dt
                                elif "Failed at:" in clean_line:
                                    time_str = clean_line.split("Failed at: ", 1)[1].strip()
                                    dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                                    if dt.tzinfo is None:
                                        dt = dt.replace(tzinfo=timezone.utc)
                                    current_task["end_time"] = dt
                                    current_task["status"] = "failed"
                                    current_task["updated_at"] = dt
                            except (IndexError, ValueError) as e:
                                print(f"Error processing line {line_number} in {task_log}: {e}")
                    except Exception as e:
                        print(f"Unexpected error processing line {line_number} in {task_log}: {e}")
                        continue
                        
                # Add the last task if it exists
                if current_task:
                    tasks.append(current_task)
                    
            # Debug output
            print(f"Parsed {len(tasks)} tasks from {task_log}")
            for i, task in enumerate(tasks, 1):
                print(f"  Task {i}: {task['task_id']} - {task['status']}")
                print(f"    Start: {task.get('start_time')}")
                print(f"    End: {task.get('end_time')}")
                
            return tasks
            
        except Exception as e:
            print(f"Error parsing task log {task_log}: {e}")
            import traceback
            traceback.print_exc()
            return tasks
    
    def update(self, force: bool = False) -> bool:
        """Update task list from postbox directory.
        
        Args:
            force: If True, force update even if no changes detected
            
        Returns:
            bool: True if any tasks were updated/added, False otherwise
        """
        updated = False
        self.last_updated = datetime.now(timezone.utc)
        
        if not self.postbox_dir.exists():
            return False
            
        # Skip update if no changes detected and not forced
        if not force and not self._has_changes():
            return False
            
        # Collect tasks from all agent task logs
        new_tasks = []
        for agent_dir in self.postbox_dir.iterdir():
            if not agent_dir.is_dir():
                continue
                
            task_log = agent_dir / "task_log.md"
            if not task_log.exists():
                continue
                
            try:
                # Update last modified time
                self._last_file_mtimes[task_log] = task_log.stat().st_mtime
                new_tasks.extend(self._parse_task_log(agent_dir))
            except (OSError, AttributeError) as e:
                console.print(f"[red]Error accessing {task_log}: {e}[/]")
        
        # Add only new tasks
        existing_task_ids = {t["task_id"] for t in self.tasks}
        for task in new_tasks:
            if task["task_id"] not in existing_task_ids:
                updated = True
                self.tasks.append(task)
        
        if not updated and not force:
            return False
            
        # Ensure all tasks have timezone-aware datetimes
        for task in self.tasks:
            for time_field in ["created_at", "updated_at", "start_time", "end_time"]:
                if time_field in task and task[time_field] is not None:
                    if task[time_field].tzinfo is None:
                        task[time_field] = task[time_field].replace(tzinfo=timezone.utc)
            
        # Sort tasks by updated_at (newest first)
        self.tasks.sort(
            key=lambda x: x.get("updated_at", datetime.min.replace(tzinfo=timezone.utc)),
            reverse=True
        )
        
        # Remove old tasks (older than TASK_RETENTION seconds)
        # But keep all tasks that are still active or recently completed
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=self.TASK_RETENTION)
        initial_count = len(self.tasks)
        
        # Filter tasks
        filtered_tasks = []
        for task in self.tasks:
            status = task.get("status")
            updated_at = task.get("updated_at", datetime.min.replace(tzinfo=timezone.utc))
            
            # Keep tasks that are either:
            # 1. Not in a terminal state, or
            # 2. Were updated recently
            if status not in ["completed", "failed", "cancelled"] or updated_at > cutoff_time:
                filtered_tasks.append(task)
        
        self.tasks = filtered_tasks
        
        # Update task list if we removed any tasks
        if len(self.tasks) < initial_count:
            updated = True
            
        # Always update visible tasks to ensure they reflect current filters
        self._update_visible_tasks()
        
        # Sort tasks by update time (newest first)
        self.tasks.sort(
            key=lambda x: x.get("updated_at") or x.get("start_time") or datetime.min,
            reverse=True
        )
        
        # Update visible tasks
        self._update_visible_tasks()
        
        return updated or bool(new_tasks)
    
    def render(self, height: int = 20) -> Panel:
        """Render the live tasks component.
        
        Args:
            height: Available height for the panel
            
        Returns:
            A Rich Panel containing the task list
        """
        # Calculate how many tasks we can show
        max_tasks = max(1, height - 5)  # Account for borders, header, and summary
        
        # Determine which tasks to show based on scroll position
        start_idx = max(0, min(
            len(self._visible_tasks) - max_tasks,
            self._scroll_position
        ))
        end_idx = min(start_idx + max_tasks, len(self._visible_tasks))
        visible_tasks = self._visible_tasks[start_idx:end_idx]
        
        # Create table
        table = create_table("Live Tasks", box=ROUNDED)
        
        # Add columns
        table.add_column("Task ID", style="cyan", no_wrap=True, ratio=1)
        table.add_column("Agent", style="magenta", width=8)
        table.add_column("Status", width=12)
        table.add_column("Retries", width=6, justify="center")
        table.add_column("Fallback", style="dim", width=10, no_wrap=True)
        table.add_column("Duration", width=10)
        
        # Add rows for visible tasks
        for task in visible_tasks:
            task_id = task.get("task_id", "N/A")[:12]  # Truncate long task IDs
            agent = task.get("agent", "UNKNOWN")
            status = task.get("status", "pending")
            retries = task.get("retries", 0)
            fallback = task.get("fallback", "-")
            
            # Truncate fallback if too long
            if len(fallback) > 10:
                fallback = fallback[:8] + "…"
            
            # Calculate duration if available
            duration = self._format_duration(task)
            
            # Format status with icon and color
            status_icon = self.STATUS_ICONS.get(status, "❓")
            status_style = get_status_style(status)
            status_text = f"[{status_style}]{status_icon} {status.replace('_', ' ').title()}[/]"
            
            # Format agent name with style
            agent_style = get_agent_style(agent)
            
            # Format retries with color
            retry_style = "green"
            if retries > 2:
                retry_style = "red"
            elif retries > 0:
                retry_style = "yellow"
            
            # Add row to table
            table.add_row(
                task_id,
                f"[{agent_style}]{agent}[/]",
                status_text,
                f"[{retry_style}]{retries}[/]",
                fallback,
                duration
            )
        
        # Add summary row if we have tasks
        if self.tasks:
            total_tasks = len(self.tasks)
            completed = sum(1 for t in self.tasks if t.get("status") == "completed")
            in_progress = sum(1 for t in self.tasks if t.get("status") == "in_progress")
            failed = sum(1 for t in self.tasks if t.get("status") == "failed")
            
            # Add filter indicators
            filter_info = []
            if self._filtered_agents:
                filter_info.append(f"Agents: {', '.join(sorted(self._filtered_agents))}")
            if self._show_archived:
                filter_info.append("Archived: Shown")
            
            table.add_section()
            table.add_row(
                f"[bold]Total: {total_tasks}",
                f"[dim]{' | '.join(filter_info)}" if filter_info else "",
                f"[green]✓ {completed}[/] | [yellow]↻ {in_progress}[/] | [red]✗ {failed}[/]",
                "",
                "",
                ""
            )
        
        # Add scroll indicator if not all tasks are visible
        scroll_info = ""
        if len(self._visible_tasks) > max_tasks:
            if start_idx > 0 and end_idx < len(self._visible_tasks):
                scroll_info = f"↑↓ {start_idx+1}-{end_idx}/{len(self._visible_tasks)}"
            elif start_idx > 0:
                scroll_info = f"↑ {start_idx+1}-{end_idx}/{len(self._visible_tasks)}"
            elif end_idx < len(self._visible_tasks):
                scroll_info = f"↓ 1-{end_idx}/{len(self._visible_tasks)}"
        
        # Add last updated time
        last_updated = "Never"
        if self.last_updated:
            last_updated = self.last_updated.strftime("%H:%M:%S")
        
        # Create subtitle with status info
        status_parts = []
        if scroll_info:
            status_parts.append(scroll_info)
        status_parts.append(f"Updated: {last_updated}")
        if not self._show_archived:
            status_parts.append("Archived: Hidden")
        
        return create_panel(
            "📋 Tasks",
            table,
            border_style="green",
            subtitle=" | ".join(status_parts)
        )
    
    def _format_duration(self, task: Dict) -> str:
        """Format task duration for display."""
        status = task.get("status", "pending")
        start_time = task.get("start_time")
        end_time = task.get("end_time", datetime.now() if status == "in_progress" else None)
        
        if not start_time or not end_time:
            return "-"
        
        try:
            delta = end_time - start_time
            if delta.days > 0:
                return f"{delta.days}d {delta.seconds//3600}h"
            elif delta.seconds > 3600:
                return f"{delta.seconds//3600}h {(delta.seconds%3600)//60}m"
            elif delta.seconds > 60:
                return f"{delta.seconds//60}m {delta.seconds%60}s"
            else:
                return f"{delta.seconds}s"
        except (TypeError, ValueError):
            return "-"
    
    def export_to_file(self, file_path: str) -> bool:
        """Export tasks to a file.
        
        Args:
            file_path: Path to the output file
            
        Returns:
            bool: True if export was successful, False otherwise
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # Prepare tasks for export
                export_tasks = []
                for task in self.tasks:
                    task_copy = task.copy()
                    # Convert datetime objects to ISO format strings
                    for time_field in ["start_time", "end_time", "created_at", "updated_at"]:
                        if time_field in task_copy and isinstance(task_copy[time_field], datetime):
                            task_copy[time_field] = task_copy[time_field].isoformat()
                    export_tasks.append(task_copy)
                
                # Write to file
                json.dump(export_tasks, f, indent=2, ensure_ascii=False)
                return True
                
        except (IOError, TypeError, ValueError) as e:
            console.print(f"[red]Error exporting tasks: {e}[/]")
            return False
