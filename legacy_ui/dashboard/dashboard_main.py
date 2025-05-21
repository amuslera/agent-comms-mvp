#!/usr/bin/env python3
"""
Bluelabel Agent OS - Command Center Dashboard

A rich terminal dashboard for monitoring agent activities, tasks, and messages.
"""
import os
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Union
from datetime import datetime

from rich.console import Console, ConsoleOptions, RenderResult
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box

# Import dashboard components
from .components.agent_status import AgentStatus
from .components.live_tasks import LiveTasks
from .components.message_feed import MessageFeed
from .layout.styles import (
    console, print_header, print_footer, 
    get_agent_style, get_status_style
)
from .dashboard_config import config, update_config

class Dashboard:
    """Main dashboard application class."""
    
    def __init__(self):
        """Initialize the dashboard with components."""
        self.components = {
            'agent_status': AgentStatus(),
            'live_tasks': LiveTasks(),
            'message_feed': MessageFeed()
        }
        self.running = False
        self._setup_key_handlers()
        self.layout = self._create_layout()
    
    def _setup_key_handlers(self) -> None:
        """Set up keyboard shortcuts and their handlers."""
        self.key_handlers = {
            'q': self._quit,
            'f': self._show_filter_menu,
            'e': self._export_data,
            'a': self._toggle_archived,
            'up': lambda: self.components['live_tasks'].scroll_up(),
            'down': lambda: self.components['live_tasks'].scroll_down(),
            'pageup': lambda: self.components['live_tasks'].scroll_up(5),
            'pagedown': lambda: self.components['live_tasks'].scroll_down(5),
            'home': lambda: self.components['live_tasks'].scroll_to_top(),
            'end': lambda: self.components['live_tasks'].scroll_to_bottom(),
            '?': self._show_help,
        }
    
    def _create_layout(self) -> Layout:
        """Create the dashboard layout."""
        layout = Layout()
        
        # Split into main content and footer
        layout.split_column(
            Layout(name="main", ratio=9),
            Layout(name="footer", size=3)
        )
        
        # Split main into left (agents + tasks) and right (messages)
        layout["main"].split_row(
            Layout(name="left", ratio=1, minimum_size=40),
            Layout(name="right", ratio=2)
        )
        
        # Split left into agent status and tasks
        layout["left"].split_column(
            Layout(name="agent_status", size=10, minimum_size=8),
            Layout(name="tasks", ratio=1)
        )
        
        return layout
    
    def update(self) -> None:
        """Update all dashboard components and the UI."""
        try:
            # Update components
            for component in self.components.values():
                component.update()
            
            # Get terminal size for responsive layout
            console_width, console_height = console.size
            
            # Calculate available height for components
            main_height = console_height - 4  # Account for header and footer
            left_height = main_height
            right_height = main_height
            
            # Update layout with component renders
            self.layout["agent_status"].update(
                self.components['agent_status'].render()
            )
            
            # Calculate available height for tasks (left column - agent status)
            tasks_height = left_height - 10  # Reserve space for agent status
            self.layout["tasks"].update(
                self.components['live_tasks'].render(height=max(10, tasks_height))
            )
            
            self.layout["right"].update(
                self.components['message_feed'].render(height=right_height)
            )
            
            # Update footer with status and help
            self._update_footer()
            
        except Exception as e:
            console.print(f"[red]Error updating dashboard: {e}[/]")
    
    def _update_footer(self) -> None:
        """Update the footer with current status and help."""
        # Get current time
        now = datetime.now().strftime("%H:%M:%S")
        
        # Get filter status
        filter_status = "[dim]No filters"
        if config.filtered_agents:
            agents = ", ".join(sorted(config.filtered_agents))
            filter_status = f"[cyan]Agents: {agents}"
        
        # Build help text
        help_text = Text.assemble(
            ("[q] ", "bold green"), ("Quit  ", "dim"),
            ("[f] ", "bold green"), ("Filter  ", "dim"),
            ("[e] ", "bold green"), ("Export  ", "dim"),
            ("[a] ", "bold green"), (f"Archived ({'on' if config.show_archived else 'off'})  ", "dim"),
            ("[?] ", "bold green"), ("Help", "dim"),
            (f"  │  {filter_status}", ""),
            (f"  │  {now}", "dim")
        )
        
        self.layout["footer"].update(
            Panel(help_text, border_style=config.colors["border"])
        )
    
    def _show_filter_menu(self) -> None:
        """Show the agent filter menu."""
        console.clear()
        console.print("[bold blue]Filter Agents[/]")
        console.print("Enter agent IDs to show (comma-separated), or leave empty to show all\n")
        
        # Show current filters
        current_filters = ", ".join(sorted(config.filtered_agents)) or "None"
        console.print(f"Current filters: [cyan]{current_filters}[/]\n")
        
        # Get agent suggestions
        agent_status = self.components['agent_status']
        if hasattr(agent_status, 'get_agent_ids'):
            agents = agent_status.get_agent_ids()
            if agents:
                console.print("Available agents: [dim]" + ", ".join(agents) + "[/]\n")
        
        try:
            # Get user input
            user_input = console.input("Filter agents > ").strip()
            
            if not user_input:
                # Clear filters
                update_config(filtered_agents=set())
                console.print("[yellow]✓ Cleared all filters[/]")
            else:
                # Parse agent IDs
                new_filters = {a.strip().upper() for a in user_input.split(",") if a.strip()}
                update_config(filtered_agents=new_filters)
                console.print(f"[green]✓ Filtering by agents: {', '.join(sorted(new_filters))}[/]")
            
            # Update components with new filters
            if hasattr(self.components['live_tasks'], 'filtered_agents'):
                self.components['live_tasks'].filtered_agents = config.filtered_agents
            
            time.sleep(1)  # Show success message
            
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Filter update cancelled[/]")
            time.sleep(0.5)
    
    def _toggle_archived(self) -> None:
        """Toggle display of archived tasks."""
        config.show_archived = not config.show_archived
        if hasattr(self.components['live_tasks'], 'toggle_archived'):
            self.components['live_tasks'].toggle_archived()
    
    def _export_data(self) -> None:
        """Export dashboard data to files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = config.export_dir / f"export_{timestamp}"
        export_dir.mkdir(parents=True, exist_ok=True)
        
        console.clear()
        console.print(f"[bold blue]Exporting data to:[/] {export_dir}\n")
        
        try:
            # Export tasks
            tasks_file = export_dir / "tasks.json"
            if hasattr(self.components['live_tasks'], 'export_to_file'):
                if self.components['live_tasks'].export_to_file(str(tasks_file)):
                    console.print(f"[green]✓[/] Exported tasks to {tasks_file}")
                else:
                    console.print(f"[red]✗[/] Failed to export tasks")
            
            # Export messages
            messages_file = export_dir / "messages.json"
            if hasattr(self.components['message_feed'], 'export_to_file'):
                if self.components['message_feed'].export_to_file(str(messages_file)):
                    console.print(f"[green]✓[/] Exported messages to {messages_file}")
                else:
                    console.print(f"[red]✗[/] Failed to export messages")
            
            console.print("\n[green]Export complete![/]")
            console.input("\nPress Enter to continue...")
            
        except Exception as e:
            console.print(f"[red]Error during export: {e}[/]")
            time.sleep(2)
    
    def _show_help(self) -> None:
        """Show help screen with available commands."""
        help_text = """
[bold blue]Bluelabel Agent OS - Dashboard Help[/]

[bold]Navigation:[/]
  [cyan]↑/↓[/]     : Scroll tasks/messages
  [cyan]Page Up/Down[/]: Scroll faster
  [cyan]Home/End[/]: Jump to top/bottom

[bold]Actions:[/]
  [cyan]f[/]: Filter agents
  [cyan]a[/]: Toggle archived tasks
  [cyan]e[/]: Export data to files
  [cyan]?[/]: Show this help
  [cyan]q[/]: Quit dashboard

[dim]Press any key to return to the dashboard...[/]
"""
        with console.screen():
            console.print(Panel(help_text, title="Help", border_style="blue"))
            console.input()
    
    def _quit(self) -> None:
        """Quit the dashboard."""
        self.running = False
    
    def run(self) -> None:
        """Run the dashboard main loop."""
        self.running = True
        console.clear()
        print_header()
        
        try:
            with Live(self.layout, refresh_per_second=10, screen=True) as live:
                while self.running:
                    try:
                        self.update()
                        
                        # Handle input with timeout for non-blocking
                        try:
                            key = console.input(timeout=0.1)
                            handler = self.key_handlers.get(key.lower(), None)
                            if handler:
                                handler()
                                
                        except Exception:
                            # Timeout or other input error, continue
                            pass
                            
                    except KeyboardInterrupt:
                        if console.input("\nQuit dashboard? [y/N] ").lower() == 'y':
                            break
                    except Exception as e:
                        console.print(f"[red]Error: {e}[/]")
                        time.sleep(1)  # Prevent tight error loop
        except Exception as e:
            console.print(f"[bold red]Fatal error in dashboard: {e}[/]")
            if __debug__:
                import traceback
                console.print(traceback.format_exc())
        finally:
            console.clear()
            console.print("[green]Dashboard closed.[/]")

def main() -> int:
    """Entry point for the dashboard."""
    try:
        # Initialize and run the dashboard
        dashboard = Dashboard()
        dashboard.run()
        return 0
    except Exception as e:
        console.print(f"[bold red]Fatal error: {e}[/]")
        if __debug__:
            import traceback
            console.print(traceback.format_exc())
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
