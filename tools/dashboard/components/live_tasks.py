import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.box import ROUNDED

from ..layout.styles import get_agent_style, get_status_style, create_table, create_panel, console

class LiveTasks:
    """Component to display live task status."""
    
    STATUS_ICONS = {
        "completed": "✅",
        "in_progress": "🔄",
        "failed": "❌",
        "pending": "⏳"
    }
    
    def __init__(self, postbox_dir: str = "postbox"):
        self.postbox_dir = Path(postbox_dir)
        self.tasks: List[Dict] = []
        self.last_updated = None
    
    def _parse_task_log(self, agent_dir: Path) -> List[Dict]:
        """Parse task log for a specific agent."""
        task_log = agent_dir / "task_log.md"
        tasks = []
        
        if not task_log.exists():
            return tasks
            
        try:
            with open(task_log, 'r') as f:
                current_task = None
                
                for line in f:
                    line = line.strip()
                    if line.startswith("## Task"):
                        if current_task:
                            tasks.append(current_task)
                            
                        # Extract task ID and status
                        parts = line.split(" - ")
                        task_id = parts[0].replace("## ", "").strip()
                        status = parts[1].lower() if len(parts) > 1 else "pending"
                        
                        current_task = {
                            "task_id": task_id,
                            "status": status,
                            "agent": agent_dir.name.upper(),
                            "start_time": None,
                            "end_time": None,
                            "retries": 0,
                            "fallback": None,
                            "details": []
                        }
                    elif current_task and line.startswith("- "):
                        current_task["details"].append(line[2:])
                        
                        # Extract metadata
                        if "Started at:" in line:
                            try:
                                time_str = line.split("Started at: ")[1].strip()
                                current_task["start_time"] = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                            except (IndexError, ValueError):
                                pass
                        elif "Retry count:" in line:
                            try:
                                current_task["retries"] = int(line.split("Retry count: ")[1].strip())
                            except (IndexError, ValueError):
                                pass
                        elif "Fallback to:" in line:
                            try:
                                current_task["fallback"] = line.split("Fallback to: ")[1].strip()
                            except IndexError:
                                pass
                        elif "Completed at:" in line:
                            try:
                                time_str = line.split("Completed at: ")[1].strip()
                                current_task["end_time"] = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                            except (IndexError, ValueError):
                                pass
                                
                if current_task:  # Add the last task
                    tasks.append(current_task)
                    
        except IOError as e:
            console.print(f"[red]Error reading task log {task_log}: {e}[/]")
            
        return tasks
    
    def update(self) -> None:
        """Update task list from postbox directory."""
        self.last_updated = datetime.now()
        self.tasks = []
        
        if not self.postbox_dir.exists():
            return
            
        for agent_dir in self.postbox_dir.iterdir():
            if agent_dir.is_dir():
                self.tasks.extend(self._parse_task_log(agent_dir))
        
        # Sort tasks by start time (newest first)
        self.tasks.sort(
            key=lambda x: x.get("start_time") or datetime.min,
            reverse=True
        )
    
    def render(self, max_tasks: int = 10) -> Panel:
        """Render the live tasks component."""
        table = create_table("Live Tasks", box=ROUNDED)
        
        # Add columns
        table.add_column("Task ID", style="cyan", no_wrap=True)
        table.add_column("Agent", style="magenta")
        table.add_column("Status", width=12)
        table.add_column("Retries", justify="center")
        table.add_column("Fallback", style="dim")
        table.add_column("Duration", width=10)
        
        # Add rows
        for task in self.tasks[:max_tasks]:
            task_id = task.get("task_id", "N/A")
            agent = task.get("agent", "UNKNOWN")
            status = task.get("status", "pending")
            retries = task.get("retries", 0)
            fallback = task.get("fallback", "-")
            
            # Calculate duration if available
            duration = "-"
            start_time = task.get("start_time")
            end_time = task.get("end_time", datetime.now() if status == "in_progress" else None)
            
            if start_time and end_time:
                delta = end_time - start_time
                if delta.days > 0:
                    duration = f"{delta.days}d {delta.seconds//3600}h"
                elif delta.seconds > 3600:
                    duration = f"{delta.seconds//3600}h {(delta.seconds%3600)//60}m"
                elif delta.seconds > 60:
                    duration = f"{delta.seconds//60}m {delta.seconds%60}s"
                else:
                    duration = f"{delta.seconds}s"
            
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
            
            table.add_section()
            table.add_row(
                f"[bold]Total: {total_tasks}",
                "",
                f"[green]✓ {completed}[/] | [yellow]↻ {in_progress}[/] | [red]✗ {failed}[/]",
                "",
                "",
                ""
            )
        
        return create_panel(
            "📋 Tasks",
            table,
            border_style="green",
            subtitle=f"Showing {min(len(self.tasks), max_tasks)} of {len(self.tasks)} tasks"
        )
