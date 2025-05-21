#!/usr/bin/env python3
"""
Bluelabel Agent OS - Command Center Dashboard

A rich terminal dashboard for monitoring agent activities, tasks, and messages.
"""

import os
import sys
import time
import signal
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

# Import dashboard components
from .components.agent_status import AgentStatus
from .components.live_tasks import LiveTasks
from .components.message_feed import MessageFeed
from .layout.styles import print_header, print_footer, console

class Dashboard:
    """Main dashboard class that orchestrates all components."""
    
    def __init__(self, refresh_interval: float = 3.0, postbox_dir: str = "postbox"):
        """Initialize the dashboard.
        
        Args:
            refresh_interval: Time in seconds between updates
            postbox_dir: Directory containing agent postboxes
        """
        self.refresh_interval = refresh_interval
        self.postbox_dir = Path(postbox_dir)
        self.running = True
        self.layout = self._create_layout()
        
        # Initialize components
        self.agent_status = AgentStatus(postbox_dir=postbox_dir)
        self.live_tasks = LiveTasks(postbox_dir=postbox_dir)
        self.message_feed = MessageFeed(postbox_dir=postbox_dir)
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._handle_exit)
        signal.signal(signal.SIGTERM, self._handle_exit)
    
    def _create_layout(self) -> Layout:
        """Create the dashboard layout."""
        layout = Layout()
        
        # Split the screen into top and bottom
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=1)
        )
        
        # Split main area into left and right
        layout["main"].split_row(
            Layout(name="left", size=60, minimum_size=30),
            Layout(name="right")
        )
        
        # Split left into agent status and tasks
        layout["left"].split_column(
            Layout(name="agent_status", size=12, minimum_size=8),
            Layout(name="tasks")
        )
        
        return layout
    
    def update(self) -> None:
        """Update all dashboard components."""
        try:
            # Update components
            self.agent_status.update()
            self.live_tasks.update()
            self.message_feed.update()
            
            # Update layout with new data
            self._update_layout()
            
        except Exception as e:
            console.print(f"[red]Error updating dashboard: {e}[/]")
    
    def _update_layout(self) -> None:
        """Update the layout with current data."""
        # Header
        header_text = Text("BLUELABEL AGENT OS - COMMAND CENTER", style="bold blue")
        self.layout["header"].update(Panel(header_text, border_style="blue"))
        
        # Agent Status
        self.layout["agent_status"].update(self.agent_status.render())
        
        # Tasks
        self.layout["tasks"].update(self.live_tasks.render())
        
        # Message Feed
        self.layout["right"].update(self.message_feed.render())
        
        # Footer
        footer_text = Text(" q: Quit • r: Refresh • s: Save • ↑/↓: Scroll • h: Help ", style="reverse")
        self.layout["footer"].update(footer_text)
    
    def _handle_exit(self, signum, frame) -> None:
        """Handle exit signals gracefully."""
        self.running = False
        console.print("\n[dim]Shutting down dashboard...[/]")
    
    def run(self) -> None:
        """Run the dashboard."""
        console.clear()
        
        with Live(
            self.layout,
            refresh_per_second=10,
            screen=True,
            redirect_stdout=False,
            redirect_stderr=False,
            console=console
        ) as live:
            try:
                while self.running:
                    self.update()
                    live.update(self.layout)
                    time.sleep(self.refresh_interval)
                    
            except KeyboardInterrupt:
                self._handle_exit(None, None)

def parse_args() -> Dict[str, Any]:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Bluelabel Agent OS - Command Center Dashboard")
    
    parser.add_argument(
        "--refresh",
        type=float,
        default=3.0,
        help="Refresh interval in seconds (default: 3.0)"
    )
    
    parser.add_argument(
        "--postbox-dir",
        type=str,
        default="postbox",
        help="Directory containing agent postboxes (default: 'postbox')"
    )
    
    parser.add_argument(
        "--agent",
        type=str,
        default=None,
        help="Filter to show only a specific agent's data"
    )
    
    return vars(parser.parse_args())

def main():
    """Entry point for the dashboard."""
    args = parse_args()
    
    # Create postbox directory if it doesn't exist
    postbox_dir = Path(args["postbox_dir"])
    postbox_dir.mkdir(parents=True, exist_ok=True)
    
    dashboard = Dashboard(
        refresh_interval=args["refresh"],
        postbox_dir=str(postbox_dir)
    )
    
    try:
        dashboard.run()
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/]")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
