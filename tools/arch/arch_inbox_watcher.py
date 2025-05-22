"""
ARCH Inbox Watcher

This module implements the core polling loop for monitoring the ARCH agent's inbox
and processing incoming messages.
"""

import json
import time
import signal
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Set

from .message_parser import MessageParser, MessageType
from .message_router import MessageRouter

class InboxWatcher:
    """Watches the ARCH agent's inbox for new messages."""
    
    def __init__(
        self,
        inbox_path: Path,
        postbox_root: Path,
        phase_policy_path: Optional[Path] = None,
        poll_interval: float = 1.0,
        log_dir: Optional[Path] = None
    ):
        """Initialize the inbox watcher.
        
        Args:
            inbox_path: Path to the ARCH inbox JSON file
            postbox_root: Root directory containing agent postboxes
            phase_policy_path: Optional path to phase policy YAML
            poll_interval: Time between inbox checks in seconds
            log_dir: Optional directory for logging
        """
        self.inbox_path = inbox_path
        self.poll_interval = poll_interval
        self.parser = MessageParser(log_dir)
        self.router = MessageRouter(postbox_root, phase_policy_path, log_dir)
        self.running = False
        self.processed_messages: Set[str] = set()
        
        # Set up logging
        self.logger = logging.getLogger("arch_inbox_watcher")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def start(self) -> None:
        """Start the inbox watching loop."""
        self.running = True
        self.logger.info("Starting ARCH inbox watcher")
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._handle_exit)
        signal.signal(signal.SIGTERM, self._handle_exit)
        
        try:
            while self.running:
                self._check_inbox()
                time.sleep(self.poll_interval)
        except Exception as e:
            self.logger.error(f"Error in inbox watcher: {e}")
            raise
        finally:
            self.logger.info("ARCH inbox watcher stopped")
    
    def _check_inbox(self) -> None:
        """Check the inbox for new messages."""
        try:
            if not self.inbox_path.exists():
                self.logger.warning(f"Inbox file not found: {self.inbox_path}")
                return
                
            with open(self.inbox_path, "r") as f:
                messages = json.load(f)
                
            if not isinstance(messages, list):
                self.logger.error("Invalid inbox format: expected list of messages")
                return
                
            for message in messages:
                self._process_message(message)
                
        except json.JSONDecodeError:
            self.logger.error("Failed to parse inbox JSON")
        except Exception as e:
            self.logger.error(f"Error checking inbox: {e}")
    
    def _process_message(self, message: Dict[str, Any]) -> None:
        """Process a single message from the inbox.
        
        Args:
            message: Message to process
        """
        try:
            # Skip if already processed
            msg_id = message.get("metadata", {}).get("message_id")
            if not msg_id or msg_id in self.processed_messages:
                return
                
            # Route message
            self.router.route_message(message)
            
            # Mark as processed
            self.processed_messages.add(msg_id)
            
        except ValueError as e:
            self.logger.error(f"Invalid message format: {e}")
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
    
    def _handle_exit(self, signum: int, frame: Any) -> None:
        """Handle exit signals gracefully.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

def main():
    """Entry point for the inbox watcher."""
    import argparse
    
    parser = argparse.ArgumentParser(description="ARCH Inbox Watcher")
    parser.add_argument(
        "--inbox",
        type=str,
        default="postbox/ARCH/inbox.json",
        help="Path to ARCH inbox file"
    )
    parser.add_argument(
        "--postbox-root",
        type=str,
        default="postbox",
        help="Root directory containing agent postboxes"
    )
    parser.add_argument(
        "--phase-policy",
        type=str,
        help="Path to phase policy YAML file"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Polling interval in seconds"
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        help="Directory for message logs"
    )
    
    args = parser.parse_args()
    
    watcher = InboxWatcher(
        inbox_path=Path(args.inbox),
        postbox_root=Path(args.postbox_root),
        phase_policy_path=Path(args.phase_policy) if args.phase_policy else None,
        poll_interval=args.interval,
        log_dir=Path(args.log_dir) if args.log_dir else None
    )
    
    watcher.start()

if __name__ == "__main__":
    main() 