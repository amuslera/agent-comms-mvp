import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.box import ROUNDED

from ..layout.styles import get_agent_style, create_table, create_panel, console

class AgentStatus:
    """Component to display agent status and metrics."""
    
    def __init__(self, postbox_dir: str = "postbox"):
        self.postbox_dir = Path(postbox_dir)
        self.agent_data: Dict[str, Dict] = {}
        self.last_updated = None
    
    def _count_messages(self, agent_dir: Path) -> Tuple[int, int]:
        """Count messages in agent's outbox and task log."""
        outbox_file = agent_dir / "outbox.json"
        task_log = agent_dir / "task_log.md"
        
        outbox_count = 0
        task_count = 0
        
        if outbox_file.exists():
            try:
                with open(outbox_file, 'r') as f:
                    outbox = json.load(f)
                    outbox_count = len(outbox.get("messages", []))
            except (json.JSONDecodeError, IOError):
                pass
                
        if task_log.exists():
            try:
                with open(task_log, 'r') as f:
                    task_count = len([line for line in f if line.startswith("## Task")])
            except IOError:
                pass
                
        return outbox_count, task_count
    
    def _get_agent_status(self, agent_dir: Path) -> str:
        """Determine agent status based on activity."""
        last_activity = self._get_last_activity(agent_dir)
        if not last_activity:
            return "inactive"
            
        time_since = (datetime.now() - last_activity).total_seconds()
        if time_since < 60:  # 1 minute
            return "active"
        elif time_since < 300:  # 5 minutes
            return "idle"
        return "inactive"
    
    def _get_last_activity(self, agent_dir: Path) -> Optional[datetime]:
        """Get the last activity timestamp for an agent."""
        outbox_file = agent_dir / "outbox.json"
        task_log = agent_dir / "task_log.md"
        
        latest_time = None
        
        for file in [outbox_file, task_log]:
            if file.exists():
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                if latest_time is None or mtime > latest_time:
                    latest_time = mtime
                    
        return latest_time
    
    def update(self) -> None:
        """Update agent status from postbox directory."""
        self.last_updated = datetime.now()
        
        if not self.postbox_dir.exists():
            return
            
        for agent_dir in self.postbox_dir.iterdir():
            if not agent_dir.is_dir():
                continue
                
            agent_id = agent_dir.name.upper()
            outbox_count, task_count = self._count_messages(agent_dir)
            status = self._get_agent_status(agent_dir)
            last_active = self._get_last_activity(agent_dir)
            
            if agent_id not in self.agent_data:
                self.agent_data[agent_id] = {
                    "tasks_completed": 0,
                    "tasks_failed": 0,
                }
            
            # Update counts
            self.agent_data[agent_id].update({
                "outbox_count": outbox_count,
                "task_count": task_count,
                "status": status,
                "last_active": last_active,
            })
    
    def render(self) -> Panel:
        """Render the agent status component."""
        table = create_table("Agent Status", box=ROUNDED)
        
        # Add columns
        table.add_column("Agent", style="cyan", no_wrap=True)
        table.add_column("Status", width=12)
        table.add_column("Tasks", justify="right")
        table.add_column("Outbox", justify="right")
        table.add_column("Last Active", width=16)
        
        # Add rows
        for agent_id, data in sorted(self.agent_data.items()):
            last_active = data.get("last_active", "Never")
            if isinstance(last_active, datetime):
                last_active = last_active.strftime("%H:%M:%S")
                
            status_style = {
                "active": "[green]●[/] Active",
                "idle": "[yellow]●[/] Idle",
                "inactive": "[red]●[/] Inactive"
            }.get(data.get("status", "inactive"), "[grey]?")
            
            agent_style = get_agent_style(agent_id)
            
            table.add_row(
                f"[{agent_style}]{agent_id}[/]",
                status_style,
                f"[cyan]{data.get('task_count', 0)}[/]",
                f"[magenta]{data.get('outbox_count', 0)}[/]",
                f"[dim]{last_active}"
            )
        
        # Add summary row if we have data
        if self.agent_data:
            total_tasks = sum(d.get("task_count", 0) for d in self.agent_data.values())
            total_outbox = sum(d.get("outbox_count", 0) for d in self.agent_data.values())
            active_agents = sum(1 for d in self.agent_data.values() if d.get("status") == "active")
            
            table.add_section()
            table.add_row(
                "[bold]Total",
                f"[bold]{active_agents} active",
                f"[bold cyan]{total_tasks}",
                f"[bold magenta]{total_outbox}",
                ""
            )
        
        return create_panel(
            "🤖 Agents",
            table,
            border_style="blue",
            subtitle=f"Updated: {self.last_updated.strftime('%H:%M:%S') if self.last_updated else 'Never'}"
        )
