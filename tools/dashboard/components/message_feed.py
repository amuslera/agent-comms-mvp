import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich.box import ROUNDED

from ..layout.styles import get_agent_style, create_panel, console

class MessageFeed:
    """Component to display a feed of messages between agents."""
    
    MESSAGE_TYPES = {
        "task": "📝",
        "result": "✅",
        "error": "❌",
        "info": "ℹ️ ",
        "debug": "🐛"
    }
    
    def __init__(self, postbox_dir: str = "postbox", max_messages: int = 50):
        self.postbox_dir = Path(postbox_dir)
        self.max_messages = max_messages
        self.messages: List[Dict] = []
        self.message_hashes = set()
        self.last_updated = None
    
    def _hash_message(self, message: Dict) -> str:
        """Create a unique hash for a message to detect duplicates."""
        import hashlib
        msg_str = f"{message.get('from')}-{message.get('to')}-{message.get('timestamp')}-{message.get('content')}"
        return hashlib.md5(msg_str.encode()).hexdigest()
    
    def _parse_outbox(self, agent_dir: Path) -> List[Dict]:
        """Parse messages from an agent's outbox."""
        outbox_file = agent_dir / "outbox.json"
        messages = []
        
        if not outbox_file.exists():
            return messages
            
        try:
            with open(outbox_file, 'r') as f:
                outbox = json.load(f)
                
            for msg in outbox.get("messages", []):
                # Add agent info if not present
                if "from" not in msg:
                    msg["from"] = agent_dir.name.upper()
                
                # Ensure timestamp is in datetime format
                if "timestamp" in msg and isinstance(msg["timestamp"], str):
                    try:
                        msg["timestamp"] = datetime.fromisoformat(msg["timestamp"])
                    except (ValueError, TypeError):
                        msg["timestamp"] = datetime.now()
                
                messages.append(msg)
                
        except (json.JSONDecodeError, IOError) as e:
            console.print(f"[red]Error reading outbox {outbox_file}: {e}[/]")
            
        return messages
    
    def update(self) -> None:
        """Update message feed from postbox directory."""
        self.last_updated = datetime.now()
        new_messages = []
        
        if not self.postbox_dir.exists():
            return
            
        # Collect new messages from all agent outboxes
        for agent_dir in self.postbox_dir.iterdir():
            if agent_dir.is_dir():
                new_messages.extend(self._parse_outbox(agent_dir))
        
        # Add only new messages
        for msg in new_messages:
            msg_hash = self._hash_message(msg)
            if msg_hash not in self.message_hashes:
                self.messages.append(msg)
                self.message_hashes.add(msg_hash)
        
        # Sort messages by timestamp (newest first)
        self.messages.sort(
            key=lambda x: x.get("timestamp", datetime.min),
            reverse=True
        )
        
        # Keep only the most recent messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[:self.max_messages]
            # Rebuild hashes
            self.message_hashes = {self._hash_message(m) for m in self.messages}
    
    def _format_message(self, msg: Dict) -> Text:
        """Format a single message for display."""
        from_agent = msg.get("from", "UNKNOWN")
        to_agent = msg.get("to", "ALL")
        msg_type = msg.get("type", "info").lower()
        content = msg.get("content", "")
        timestamp = msg.get("timestamp", datetime.now())
        
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except (ValueError, TypeError):
                timestamp = datetime.now()
        
        # Format timestamp
        time_str = timestamp.strftime("%H:%M:%S")
        
        # Get message type icon
        msg_icon = self.MESSAGE_TYPES.get(msg_type, "✉️")
        
        # Get agent styles
        from_style = get_agent_style(from_agent) or "cyan"
        to_style = get_agent_style(to_agent) or "magenta"
        
        # Format message
        text = Text()
        text.append(f"{time_str} ", style="dim")
        text.append(f"{msg_icon} ", style="bold")
        text.append(f"[", style="dim")
        text.append(f"{from_agent}", style=f"bold {from_style}")
        text.append(f" → ", style="dim")
        text.append(f"{to_agent}", style=f"bold {to_style}")
        text.append(f"] ", style="dim")
        
        # Add content with appropriate formatting
        if isinstance(content, dict):
            # Pretty-print JSON content
            try:
                content_str = json.dumps(content, indent=2)
                text.append("\n")
                text.append(Syntax(
                    content_str,
                    "json",
                    theme="monokai",
                    word_wrap=True,
                    code_width=60
                ))
            except (TypeError, ValueError):
                text.append(str(content))
        else:
            text.append(str(content))
        
        return text
    
    def render(self, max_messages: int = 10) -> Panel:
        """Render the message feed component."""
        # Create a list of formatted messages
        formatted_messages = []
        
        for msg in self.messages[:max_messages]:
            formatted_messages.append(self._format_message(msg))
            formatted_messages.append("")  # Add space between messages
        
        if not formatted_messages:
            formatted_messages.append(Text("No messages yet. Waiting for agent communication...", style="dim"))
        
        return create_panel(
            "📨 Message Feed",
            formatted_messages,
            border_style="yellow",
            subtitle=f"Showing {min(len(self.messages), max_messages)} of {len(self.messages)} messages"
        )
