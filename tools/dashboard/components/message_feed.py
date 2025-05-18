import json
import time
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Set, Any, Union
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich.box import ROUNDED
from rich.console import Group, RenderableType

from ..layout.styles import get_agent_style, create_panel, console
from ..dashboard_config import config

class MessageFeed:
    """Component to display a feed of messages between agents."""
    
    MESSAGE_TYPES = {
        "task": "📝",
        "result": "✅",
        "error": "❌",
        "info": "ℹ️ ",
        "warning": "⚠️ ",
        "debug": "🐛",
        "heartbeat": "💓",
        "command": "⌨️ ",
    }
    
    # How long to keep messages in the feed (in seconds)
    MESSAGE_RETENTION = 3600  # 1 hour
    
    def __init__(self):
        self.messages: List[Dict] = []
        self.message_hashes: Set[str] = set()
        self.last_updated: Optional[datetime] = None
        self._last_file_mtimes: Dict[Path, float] = {}
        self._filtered_agents: Set[str] = set()
        self._visible_messages: List[Dict] = []
        self._scroll_position: int = 0
        self._show_raw_json: bool = False
        
    @property
    def postbox_dir(self) -> Path:
        """Get the current postbox directory."""
        return config.postbox_dir
        
    @property
    def max_messages(self) -> int:
        """Get the maximum number of messages to display."""
        return config.max_messages
        
    @property
    def filtered_agents(self) -> Set[str]:
        """Get the set of filtered agent IDs."""
        return self._filtered_agents
        
    @filtered_agents.setter
    def filtered_agents(self, agents: Set[str]) -> None:
        """Set the filtered agent IDs."""
        self._filtered_agents = {a.upper() for a in agents}
        self._update_visible_messages()
    
    def _update_visible_messages(self) -> None:
        """Update the list of visible messages based on filters."""
        if not self._filtered_agents:
            self._visible_messages = self.messages
        else:
            self._visible_messages = [
                msg for msg in self.messages
                if (msg.get("from") in self._filtered_agents or 
                    msg.get("to") in self._filtered_agents or
                    (msg.get("to") == "BROADCAST" and self._filtered_agents.intersection(msg.get("broadcast_to", []))))
            ]
        
        # Ensure scroll position is valid
        self._scroll_position = max(0, min(self._scroll_position, len(self._visible_messages) - 1))
    
    def scroll_up(self, lines: int = 1) -> None:
        """Scroll up in the message feed."""
        self._scroll_position = max(0, self._scroll_position - lines)
    
    def scroll_down(self, lines: int = 1) -> None:
        """Scroll down in the message feed."""
        if self._visible_messages:
            self._scroll_position = min(
                len(self._visible_messages) - 1,
                self._scroll_position + lines
            )
    
    def scroll_to_top(self) -> None:
        """Scroll to the top of the message feed."""
        self._scroll_position = 0
    
    def scroll_to_bottom(self) -> None:
        """Scroll to the bottom of the message feed."""
        if self._visible_messages:
            self._scroll_position = len(self._visible_messages) - 1
    
    def toggle_raw_json(self) -> None:
        """Toggle between formatted and raw JSON view."""
        self._show_raw_json = not self._show_raw_json
    
    def _hash_message(self, message: Dict) -> str:
        """Create a unique hash for a message to detect duplicates."""
        import hashlib
        # Use a combination of fields that should be unique for each message
        msg_str = (
            f"{message.get('from', 'unknown')}:"
            f"{message.get('to', 'unknown')}:"
            f"{message.get('timestamp', '0')}:"
            f"{message.get('type', 'unknown')}:"
            f"{str(hash(frozenset(message.get('content', {}).items()))) if isinstance(message.get('content'), dict) else str(hash(str(message.get('content', ''))))}"
        )
        return hashlib.md5(msg_str.encode()).hexdigest()
    
    def _parse_outbox(self, agent_dir: Path) -> List[Dict]:
        """Parse messages from an agent's outbox."""
        outbox_file = agent_dir / "outbox.json"
        messages = []
        
        if not outbox_file.exists():
            return messages
            
        try:
            with open(outbox_file, 'r', encoding='utf-8') as f:
                outbox_data = json.load(f)
            
            # Handle case where the outbox is a list
            if isinstance(outbox_data, list):
                message_list = outbox_data
            # Handle case where messages are in a 'messages' key
            elif isinstance(outbox_data, dict) and 'messages' in outbox_data:
                message_list = outbox_data.get('messages', [])
            else:
                console.print(f"[yellow]Warning: Unexpected outbox format in {outbox_file}[/]")
                return messages
            
            # Process each message
            for msg in message_list:
                try:
                    if not isinstance(msg, dict):
                        console.print(f"[yellow]Warning: Skipping non-dict message in {outbox_file}[/]")
                        continue
                        
                    # Create a new dict to avoid modifying the original
                    processed_msg = dict(msg)
                    
                    # Add agent info if not present
                    if "from" not in processed_msg:
                        processed_msg["from"] = agent_dir.name.upper()
                    
                    # Ensure sender and recipient are strings
                    if "from" in processed_msg:
                        processed_msg["from"] = str(processed_msg["from"])
                    if "to" in processed_msg:
                        processed_msg["to"] = str(processed_msg["to"])
                    
                    # Ensure timestamp is in datetime format
                    if "timestamp" in processed_msg:
                        try:
                            if isinstance(processed_msg["timestamp"], str):
                                processed_msg["timestamp"] = datetime.fromisoformat(processed_msg["timestamp"].replace('Z', '+00:00'))
                            elif isinstance(processed_msg["timestamp"], (int, float)):
                                processed_msg["timestamp"] = datetime.fromtimestamp(processed_msg["timestamp"])
                        except (ValueError, TypeError) as e:
                            console.print(f"[yellow]Warning: Invalid timestamp in message from {processed_msg.get('from', 'unknown')}: {e}[/]")
                            processed_msg["timestamp"] = datetime.now()
                    else:
                        processed_msg["timestamp"] = datetime.now()
                    
                    # Ensure required fields
                    processed_msg.setdefault("type", "info")
                    processed_msg.setdefault("content", "")
                    
                    messages.append(processed_msg)
                    
                except Exception as e:
                    console.print(f"[red]Error processing message in {outbox_file}: {e}[/]")
                    continue
                
        except json.JSONDecodeError as e:
            console.print(f"[red]Error parsing JSON in {outbox_file}: {e}[/]")
        except IOError as e:
            console.print(f"[red]Error reading outbox {outbox_file}: {e}[/]")
        except Exception as e:
            console.print(f"[red]Unexpected error processing {outbox_file}: {e}[/]")
            
        return messages
    
    def _has_changes(self) -> bool:
        """Check if any outbox files have changed."""
        if not self.postbox_dir.exists():
            return False
            
        # Check for new or modified outbox files
        for agent_dir in self.postbox_dir.iterdir():
            if not agent_dir.is_dir():
                continue
                
            outbox_file = agent_dir / "outbox.json"
            if not outbox_file.exists():
                continue
                
            try:
                mtime = outbox_file.stat().st_mtime
                if outbox_file not in self._last_file_mtimes or \
                   self._last_file_mtimes[outbox_file] < mtime:
                    return True
            except (OSError, AttributeError):
                continue
                
        return False
    
    def update(self, force: bool = False) -> bool:
        """Update message feed from postbox directory.
        
        Args:
            force: If True, force update even if no changes detected
            
        Returns:
            bool: True if any messages were updated/added, False otherwise
        """
        updated = False
        self.last_updated = datetime.now()
        
        if not self.postbox_dir.exists():
            return False
            
        # Skip update if no changes detected and not forced
        if not force and not self._has_changes():
            return False
            
        # Collect new messages from all agent outboxes
        new_messages = []
        for agent_dir in self.postbox_dir.iterdir():
            if not agent_dir.is_dir():
                continue
                
            outbox_file = agent_dir / "outbox.json"
            if not outbox_file.exists():
                continue
                
            try:
                # Update last modified time
                self._last_file_mtimes[outbox_file] = outbox_file.stat().st_mtime
                new_messages.extend(self._parse_outbox(agent_dir))
            except (OSError, AttributeError) as e:
                console.print(f"[red]Error accessing {outbox_file}: {e}[/]")
        
        # Add only new messages
        for msg in new_messages:
            msg_hash = self._hash_message(msg)
            if msg_hash not in self.message_hashes:
                updated = True
                self.messages.append(msg)
                self.message_hashes.add(msg_hash)
        
        if not updated and not force:
            return False
        
        # Sort messages by timestamp (newest first)
        self.messages.sort(
            key=lambda x: x.get("timestamp", datetime.min),
            reverse=True
        )
        
        # Keep only the most recent messages
        if len(self.messages) > self.max_messages * 2:  # Keep more in memory for filtering
            self.messages = self.messages[:self.max_messages * 2]
            # Rebuild hashes
            self.message_hashes = {self._hash_message(m) for m in self.messages}
        
        # Remove old messages (older than MESSAGE_RETENTION seconds)
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=self.MESSAGE_RETENTION)
        initial_count = len(self.messages)
        
        # Ensure we're comparing timezone-aware datetimes
        filtered_messages = []
        for msg in self.messages:
            msg_time = msg.get("timestamp")
            if not msg_time:
                continue
                
            # Convert to timezone-aware datetime if it's not already
            if isinstance(msg_time, str):
                try:
                    msg_time = datetime.fromisoformat(msg_time.replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    continue
            elif isinstance(msg_time, (int, float)):
                msg_time = datetime.fromtimestamp(msg_time, timezone.utc)
            elif not hasattr(msg_time, 'tzinfo') or msg_time.tzinfo is None:
                # Make naive datetime timezone-aware by assuming UTC
                msg_time = msg_time.replace(tzinfo=timezone.utc)
                
            if msg_time > cutoff_time:
                # Update the timestamp in the message to ensure it's timezone-aware
                msg = msg.copy()
                msg["timestamp"] = msg_time
                filtered_messages.append(msg)
                
        self.messages = filtered_messages
        
        # Update seen message hashes if we removed any messages
        if len(self.messages) < initial_count:
            self.message_hashes = {self._hash_message(m) for m in self.messages}
            updated = True
        
        # Update visible messages
        self._update_visible_messages()
        
        return updated
    
    def _format_message_content(self, content: Any) -> Union[Text, Syntax, str]:
        """Format message content for display."""
        if isinstance(content, dict):
            try:
                content_str = json.dumps(content, indent=2, ensure_ascii=False)
                return Syntax(
                    content_str,
                    "json",
                    theme="monokai",
                    word_wrap=True,
                    code_width=60
                )
            except (TypeError, ValueError):
                return str(content)
        elif isinstance(content, (list, tuple)):
            try:
                content_str = json.dumps(content, indent=2, ensure_ascii=False)
                return Syntax(
                    content_str,
                    "json",
                    theme="monokai",
                    word_wrap=True,
                    code_width=60
                )
            except (TypeError, ValueError):
                return "\n".join(str(item) for item in content)
        else:
            return str(content)
    
    def _format_message(self, msg: Dict, show_raw: bool = False) -> Union[Text, Group]:
        """Format a single message for display.
        
        Args:
            msg: The message dictionary to format
            show_raw: If True, show raw JSON instead of formatted content
            
        Returns:
            A Rich renderable (Text or Group) representing the message
        """
        from_agent = msg.get("from", "UNKNOWN")
        to_agent = msg.get("to", "ALL")
        msg_type = msg.get("type", "info").lower()
        content = msg.get("content", "")
        timestamp = msg.get("timestamp", datetime.now())
        
        # Parse timestamp if it's a string
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except (ValueError, TypeError):
                timestamp = datetime.now()
        
        # Format timestamp
        if (datetime.now() - timestamp).days > 1:
            time_str = timestamp.strftime("%Y-%m-%d %H:%M")
        else:
            time_str = timestamp.strftime("%H:%M:%S")
        
        # Get message type icon
        msg_icon = self.MESSAGE_TYPES.get(msg_type, "✉️")
        
        # Get agent styles
        from_style = get_agent_style(from_agent) or "cyan"
        to_style = get_agent_style(to_agent) or "magenta"
        
        # Format message header
        header = Text()
        header.append(f"{time_str} ", style="dim")
        header.append(f"{msg_icon} ", style="bold")
        header.append(f"[", style="dim")
        header.append(f"{from_agent}", style=f"bold {from_style}")
        header.append(f" → ", style="dim")
        header.append(f"{to_agent}", style=f"bold {to_style}")
        header.append(f"] ", style="dim")
        
        # Handle raw JSON view
        if show_raw:
            try:
                raw_content = json.dumps(msg.get("raw", msg), indent=2, ensure_ascii=False)
                return Group(
                    header,
                    "",
                    Syntax(
                        raw_content,
                        "json",
                        theme="monokai",
                        word_wrap=True,
                        code_width=80
                    )
                )
            except (TypeError, ValueError):
                return Group(header, "", str(msg))
        
        # Format message content
        content_display = self._format_message_content(content)
        
        # If content is already a rich renderable, group it with the header
        if isinstance(content_display, (Text, Syntax)):
            return Group(header, "", content_display)
        
        # Otherwise, append to the header
        header.append(content_display)
        return header
    
    def render(self, height: int = 20) -> Panel:
        """Render the message feed component.
        
        Args:
            height: Available height for the panel
            
        Returns:
            A Rich Panel containing the message feed
        """
        # Calculate how many messages we can show
        max_messages = max(1, height - 2)  # Account for borders and header
        
        # Get visible messages (filtered if needed)
        visible_msgs = self._visible_messages if hasattr(self, '_visible_messages') else self.messages
        
        # Determine which messages to show based on scroll position
        start_idx = max(0, min(
            len(visible_msgs) - max_messages,
            self._scroll_position if hasattr(self, '_scroll_position') else 0
        ))
        end_idx = min(start_idx + max_messages, len(visible_msgs))
        
        # Create a list of formatted messages
        formatted_messages = []
        
        # Add messages in reverse chronological order (newest at bottom)
        for msg in visible_msgs[start_idx:end_idx]:
            formatted_msg = self._format_message(msg, self._show_raw_json)
            formatted_messages.append(formatted_msg)
            # Only add spacing if not the last message
            if msg != visible_msgs[end_idx - 1]:
                formatted_messages.append("")  # Add space between messages
        
        if not formatted_messages:
            formatted_messages.append(Text("No messages to display", style="dim"))
            
            if self._filtered_agents:
                formatted_messages.append("")
                formatted_messages.append(
                    Text(f"Filter active: showing only messages from/to {', '.join(sorted(self._filtered_agents))}", 
                         style="yellow")
                )
        
        # Add scroll indicator if not all messages are visible
        scroll_info = ""
        if len(visible_msgs) > max_messages:
            if start_idx > 0 and end_idx < len(visible_msgs):
                scroll_info = f"↑↓ {start_idx+1}-{end_idx}/{len(visible_msgs)}"
            elif start_idx > 0:
                scroll_info = f"↑ {start_idx+1}-{end_idx}/{len(visible_msgs)}"
            elif end_idx < len(visible_msgs):
                scroll_info = f"↓ 1-{end_idx}/{len(visible_msgs)}"
        
        # Add last updated time
        last_updated = "Never"
        if self.last_updated:
            last_updated = self.last_updated.strftime("%H:%M:%S.%f")[:-3]
            
        # Create subtitle with status info
        status_parts = []
        if scroll_info:
            status_parts.append(scroll_info)
        if self._filtered_agents:
            status_parts.append(f"Filter: {', '.join(sorted(self._filtered_agents))}")
        if self._show_raw_json:
            status_parts.append("RAW")
            
        subtitle = " | ".join(status_parts) if status_parts else f"Updated: {last_updated}"
        
        return create_panel(
            "💬 Messages",
            formatted_messages,
            border_style="green",
            subtitle=subtitle
        )
    
    def export_to_file(self, file_path: str) -> bool:
        """Export messages to a file.
        
        Args:
            file_path: Path to the output file
            
        Returns:
            bool: True if export was successful, False otherwise
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # Get all messages (not just visible ones)
                messages_to_export = sorted(
                    self.messages,
                    key=lambda x: x.get("timestamp", datetime.min),
                    reverse=True
                )
                
                # Convert to a list of dicts for JSON serialization
                export_data = []
                for msg in messages_to_export:
                    msg_copy = msg.copy()
                    # Convert datetime to ISO format if needed
                    if "timestamp" in msg_copy and isinstance(msg_copy["timestamp"], datetime):
                        msg_copy["timestamp"] = msg_copy["timestamp"].isoformat()
                    export_data.append(msg_copy)
                
                # Write to file
                json.dump(export_data, f, indent=2, ensure_ascii=False)
                return True
                
        except (IOError, TypeError, ValueError) as e:
            console.print(f"[red]Error exporting messages: {e}[/]")
            return False
