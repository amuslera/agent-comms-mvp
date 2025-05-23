<<<<<<< HEAD:legacy_ui/dashboard/dashboard_config.py
"""Dashboard configuration settings."""
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Set, Any, Optional
import os

@dataclass
class DashboardConfig:
    """Configuration for the Dashboard application."""
    # Directory paths
    postbox_dir: Path = field(default_factory=lambda: Path(os.getenv("POSTBOX_DIR", "postbox")))
    context_dir: Path = field(default_factory=lambda: Path(os.getenv("CONTEXT_DIR", "context")))
    export_dir: Path = field(default_factory=lambda: Path(os.getenv("EXPORT_DIR", "exports")))
    
    # Display settings
    refresh_rate: float = 1.0  # seconds between updates
    max_tasks: int = 100  # maximum tasks to keep in memory
    max_messages: int = 200  # maximum messages to keep in memory
    
    # UI settings
    colors: Dict[str, str] = field(default_factory=lambda: {
        "agent_active": "green",
        "agent_idle": "yellow",
        "agent_error": "red",
        "message_sent": "cyan",
        "message_received": "blue",
        "message_error": "magenta",
        "task_success": "green",
        "task_retry": "yellow",
        "task_failed": "red",
        "task_pending": "blue",
        "border": "dim",
        "header": "bold cyan",
        "footer": "dim",
    })
    
    # Feature toggles
    mock_mode: bool = False  # Use mock data for development
    watch_mode: bool = False  # Watch for file changes
    
    # State
    filtered_agents: Set[str] = field(default_factory=set)
    show_archived: bool = False
    
    def __post_init__(self):
        """Ensure paths are Path objects and directories exist."""
        self.postbox_dir = Path(self.postbox_dir).resolve()
        self.context_dir = Path(self.context_dir).resolve()
        self.export_dir = Path(self.export_dir).resolve()
        
        # Create directories if they don't exist
        self.postbox_dir.mkdir(parents=True, exist_ok=True)
        self.context_dir.mkdir(parents=True, exist_ok=True)
        self.export_dir.mkdir(parents=True, exist_ok=True)

# Global configuration instance
config = DashboardConfig()

def update_config(**kwargs) -> None:
    """Update the global configuration."""
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)

# For backward compatibility
refresh_rate = config.refresh_rate
max_tasks_displayed = config.max_tasks
=======
"""
Dashboard configuration and settings management.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Set

class DashboardConfig:
    """Manages dashboard configuration and settings."""
    
    def __init__(self, config_path: str = None):
        """Initialize dashboard configuration.
        
        Args:
            config_path: Path to config file. Defaults to ~/.bluelabel/dashboard.json
        """
        self.config_path = config_path or os.path.expanduser("~/.bluelabel/dashboard.json")
        self.config = self._load_config()
        
        # Runtime state
        self.filtered_agents: Set[str] = set()
        self.watch_mode: bool = False
        self.export_path: Optional[str] = None
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or return defaults."""
        try:
            config_dir = os.path.dirname(self.config_path)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
                
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
            
        # Default configuration
        return {
            "postbox_dir": "postbox",
            "context_dir": "contexts",
            "refresh_interval": 3.0,
            "max_tasks": 50,
            "max_messages": 100,
            "recent_tasks": 20,
            "theme": "default"
        }
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save config: {e}")
    
    def update_setting(self, key: str, value: Any) -> None:
        """Update a configuration setting."""
        self.config[key] = value
        self.save_config()
    
    def toggle_agent_filter(self, agent_id: str) -> None:
        """Toggle filter for a specific agent."""
        agent_id = agent_id.upper()
        if agent_id in self.filtered_agents:
            self.filtered_agents.remove(agent_id)
        else:
            self.filtered_agents.add(agent_id)
    
    def clear_agent_filters(self) -> None:
        """Clear all agent filters."""
        self.filtered_agents.clear()
    
    def is_agent_visible(self, agent_id: str) -> bool:
        """Check if an agent should be visible based on current filters."""
        if not self.filtered_agents:
            return True
        return agent_id.upper() in self.filtered_agents
    
    @property
    def postbox_dir(self) -> Path:
        """Get the postbox directory path."""
        return Path(self.config["postbox_dir"])
    
    @postbox_dir.setter
    def postbox_dir(self, value: str) -> None:
        """Set the postbox directory path."""
        self.config["postbox_dir"] = str(Path(value).expanduser().absolute())
        self.save_config()
    
    @property
    def context_dir(self) -> Path:
        """Get the context directory path."""
        return Path(self.config["context_dir"])
    
    @context_dir.setter
    def context_dir(self, value: str) -> None:
        """Set the context directory path."""
        self.config["context_dir"] = str(Path(value).expanduser().absolute())
        self.save_config()
    
    @property
    def refresh_interval(self) -> float:
        """Get the refresh interval in seconds."""
        return float(self.config["refresh_interval"])
    
    @refresh_interval.setter
    def refresh_interval(self, value: float) -> None:
        """Set the refresh interval in seconds."""
        self.config["refresh_interval"] = max(0.5, float(value))
        self.save_config()
    
    @property
    def max_tasks(self) -> int:
        """Get the maximum number of tasks to display."""
        return int(self.config["max_tasks"])
    
    @property
    def max_messages(self) -> int:
        """Get the maximum number of messages to display."""
        return int(self.config["max_messages"])
    
    @property
    def recent_tasks(self) -> int:
        """Get the number of recent tasks to keep in memory."""
        return int(self.config["recent_tasks"])

# Global config instance
config = DashboardConfig()
>>>>>>> feat/TASK-047-dashboard-enhancements-merge:tools/dashboard/dashboard_config.py
