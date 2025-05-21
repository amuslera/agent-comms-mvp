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
