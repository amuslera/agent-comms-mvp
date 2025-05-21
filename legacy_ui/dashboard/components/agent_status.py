import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set, Any
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.box import ROUNDED

from ..layout.styles import get_agent_style, create_table, create_panel, console
from ..dashboard_config import config

class AgentStatus:
    """Component to display agent status and metrics."""
    
    def __init__(self):
        self.agent_data: Dict[str, Dict] = {}
        self.last_updated: Optional[datetime] = None
        self._last_file_mtimes: Dict[Path, float] = {}
        self._filtered_agents: Set[str] = set()
        self._visible_agents: Set[str] = set()
        
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
        self._update_visible_agents()
    
    def _update_visible_agents(self) -> None:
        """Update the set of visible agents based on filters."""
        if not self._filtered_agents:
            self._visible_agents = set(self.agent_data.keys())
        else:
            self._visible_agents = {
                agent_id for agent_id in self.agent_data.keys()
                if agent_id in self._filtered_agents
            }
    
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
    
    def _has_changes(self, agent_dir: Path) -> bool:
        """Check if any files in the agent directory have changed."""
        if not agent_dir.exists():
            return False
            
        # Check for new files
        current_files = set(agent_dir.glob("*"))
        known_files = set(self._last_file_mtimes.keys())
        
        if current_files != known_files:
            return True
            
        # Check for modified files
        for file_path in current_files:
            try:
                mtime = file_path.stat().st_mtime
                if file_path not in self._last_file_mtimes or \
                   self._last_file_mtimes[file_path] < mtime:
                    return True
            except (OSError, AttributeError):
                continue
                
        return False
    
    def update(self, force: bool = False) -> bool:
        """Update agent status from postbox directory.
        
        Args:
            force: If True, force update even if no changes detected
            
        Returns:
            bool: True if any data was updated, False otherwise
        """
        updated = False
        self.last_updated = datetime.now()
        
        if not self.postbox_dir.exists():
            return False
            
        # Track which agents we've seen in this update
        seen_agents = set()
        
        for agent_dir in self.postbox_dir.iterdir():
            if not agent_dir.is_dir():
                continue
                
            agent_id = agent_dir.name.upper()
            seen_agents.add(agent_id)
            
            # Skip if no changes detected and not forced
            if not force and not self._has_changes(agent_dir):
                continue
                
            outbox_count, task_count = self._count_messages(agent_dir)
            status = self._get_agent_status(agent_dir)
            last_active = self._get_last_activity(agent_dir)
            
            # Update file mtimes
            for file_path in agent_dir.glob("*"):
                try:
                    self._last_file_mtimes[file_path] = file_path.stat().st_mtime
                except (OSError, AttributeError):
                    continue
            
            if agent_id not in self.agent_data:
                self.agent_data[agent_id] = {
                    "tasks_completed": 0,
                    "tasks_failed": 0,
                }
                updated = True
            
            # Check if data has actually changed
            current_data = self.agent_data[agent_id]
            if (current_data.get("outbox_count") != outbox_count or
                current_data.get("task_count") != task_count or
                current_data.get("status") != status or
                current_data.get("last_active") != last_active):
                updated = True
            
            # Update counts
            current_data.update({
                "outbox_count": outbox_count,
                "task_count": task_count,
                "status": status,
                "last_active": last_active,
            })
        
        # Remove agents that no longer exist
        removed_agents = set(self.agent_data.keys()) - seen_agents
        if removed_agents:
            for agent_id in removed_agents:
                del self.agent_data[agent_id]
            updated = True
        
        # Update visible agents based on filters
        if updated:
            self._update_visible_agents()
        
        return updated
    
    def render(self) -> Panel:
        """Render the agent status component."""
        table = create_table("Agent Status", box=ROUNDED)
        
        # Add columns
        table.add_column("Agent", style="cyan", no_wrap=True)
        table.add_column("Status", width=12)
        table.add_column("Tasks", justify="right")
        table.add_column("Outbox", justify="right")
        table.add_column("Last Active", width=16)
        
        visible_agents = sorted(
            (agent_id for agent_id in self.agent_data.items() 
             if agent_id[0] in self._visible_agents or not self._filtered_agents),
            key=lambda x: x[0]  # Sort by agent ID
        )
        
        # Add rows for visible agents
        for agent_id, data in visible_agents:
            last_active = data.get("last_active", "Never")
            if isinstance(last_active, datetime):
                if datetime.now() - last_active < timedelta(days=1):
                    last_active = last_active.strftime("%H:%M:%S")
                else:
                    last_active = last_active.strftime("%Y-%m-%d")
                
            status_style = {
                "active": "[green]●[/] Active",
                "idle": "[yellow]●[/] Idle",
                "inactive": "[red]●[/] Inactive"
            }.get(data.get("status", "inactive"), "[grey]?")
            
            agent_style = get_agent_style(agent_id)
            
            # Highlight filtered agents
            row_style = ""
            if agent_id in self._filtered_agents:
                row_style = "on grey23"
            
            table.add_row(
                f"[{agent_style}]{agent_id}[/]",
                status_style,
                f"[cyan]{data.get('task_count', 0)}[/]",
                f"[magenta]{data.get('outbox_count', 0)}[/]",
                f"[dim]{last_active}",
                style=row_style
            )
        
        # Add summary row if we have data
        if self.agent_data:
            visible_data = [
                data for agent_id, data in self.agent_data.items()
                if agent_id in self._visible_agents or not self._filtered_agents
            ]
            
            total_tasks = sum(d.get("task_count", 0) for d in visible_data)
            total_outbox = sum(d.get("outbox_count", 0) for d in visible_data)
            active_agents = sum(1 for d in visible_data if d.get("status") == "active")
            
            # Add filter indicator
            filter_indicator = ""
            if self._filtered_agents:
                filter_indicator = f" (Filtered: {', '.join(sorted(self._filtered_agents))})"
            
            table.add_section()
            table.add_row(
                f"[bold]Total{filter_indicator}",
                f"[bold]{active_agents} active",
                f"[bold cyan]{total_tasks}",
                f"[bold magenta]{total_outbox}",
                ""
            )
        
        # Add last updated time
        last_updated = "Never"
        if self.last_updated:
            last_updated = self.last_updated.strftime("%H:%M:%S.%f")[:-3]
        
        return create_panel(
            "🤖 Agents",
            table,
            border_style="blue",
            subtitle=f"Updated: {last_updated} | {len(visible_agents)}/{len(self.agent_data)} agents"
        )
    
    def get_agent_ids(self) -> List[str]:
        """Get a list of all agent IDs."""
        return sorted(self.agent_data.keys())
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get status for a specific agent."""
        return self.agent_data.get(agent_id.upper())
