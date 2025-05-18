from rich.console import Console
from rich.theme import Theme
from rich.style import Style
from rich.panel import Panel
from rich.table import Table
from rich.box import ROUNDED, SIMPLE, HEAVY

# Custom Theme
custom_theme = Theme({
    "success": "green",
    "warning": "yellow",
    "error": "red",
    "info": "blue",
    "header": "bold cyan",
    "agent.ca": "bright_cyan",
    "agent.cc": "bright_magenta",
    "agent.wa": "bright_green",
    "agent.arch": "bright_yellow",
    "status.completed": "green",
    "status.in_progress": "yellow",
    "status.failed": "red",
    "status.pending": "blue",
})

# Initialize console with custom theme
console = Console(theme=custom_theme)

def get_agent_style(agent_id: str) -> str:
    """Get the style for a specific agent."""
    agent_map = {
        "CA": "agent.ca",
        "CC": "agent.cc",
        "WA": "agent.wa",
        "ARCH": "agent.arch",
    }
    return agent_map.get(agent_id.upper(), "")

def get_status_style(status: str) -> str:
    """Get the style for a status."""
    status_map = {
        "completed": "status.completed",
        "in_progress": "status.in_progress",
        "failed": "status.failed",
        "pending": "status.pending",
    }
    return status_map.get(status.lower(), "")

def create_table(title: str = "", box=ROUNDED) -> Table:
    """Create a styled table with consistent formatting."""
    table = Table(
        box=box,
        show_header=True,
        header_style="bold magenta",
        border_style="dim",
        title=title,
        title_justify="left",
        expand=True,
    )
    return table

def create_panel(title: str, renderable, **kwargs) -> Panel:
    """Create a styled panel."""
    return Panel(
        renderable,
        title=f"[bold]{title}[/]",
        border_style="dim",
        padding=(1, 2),
        **kwargs
    )

def print_header():
    """Print the dashboard header."""
    header = """
    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃                   BLUELABEL AGENT OS                   ┃
    ┃                [dim]COMMAND CENTER DASHBOARD[/]             ┃
    ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
    """
    console.print(header, style="bold blue")

def print_footer():
    """Print the dashboard footer."""
    footer = """
    [dim]└─ [bold]q[/]: Quit  [bold]r[/]: Refresh  [bold]s[/]: Save  [bold]↑/↓[/]: Scroll  [bold]h[/]: Help[/]
    """
    console.print(footer, style="dim")

# Export commonly used styles
STYLES = {
    "success": Style(color="green"),
    "warning": Style(color="yellow"),
    "error": Style(color="red"),
    "info": Style(color="blue"),
    "header": Style(bold=True, color="cyan"),
}
