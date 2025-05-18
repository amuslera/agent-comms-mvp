#!/usr/bin/env python3
"""
Central message router with TTL and retry support.

This module handles message routing between agents, including:
- TTL enforcement for message expiration
- Retry countdown and tracking
- Message archiving and logging
"""

import argparse
import json
import os
import glob
from datetime import datetime
from pathlib import Path
import jsonschema
from typing import Dict, List, Tuple, Any, Optional
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('router/router_log.md'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_schema() -> Dict:
    """Load the exchange protocol schema for message validation."""
    schema_path = Path(__file__).parent.parent / "exchange_protocol.json"
    with open(schema_path, 'r') as f:
        return json.load(f)


def validate_message(message: Dict, schema: Dict) -> Tuple[bool, str]:
    """Validate a message against the exchange protocol schema."""
    try:
        jsonschema.validate(instance=message, schema=schema)
        return True, ""
    except jsonschema.exceptions.ValidationError as e:
        return False, str(e)


def scan_outbox(agent: str, postbox_dir: Path) -> List[Dict]:
    """Scan an agent's outbox for messages to route."""
    outbox_path = postbox_dir / agent / "outbox.json"
    if not outbox_path.exists():
        return []
    
    with open(outbox_path, 'r') as f:
        messages = json.load(f)
    
    return messages if isinstance(messages, list) else []


def is_message_expired(message: Dict[str, Any]) -> bool:
    """
    Check if a message has expired based on its TTL.
    
    Args:
        message: Message dictionary with optional TTL in metadata
        
    Returns:
        bool: True if message has expired
    """
    ttl = message.get('metadata', {}).get('ttl')
    if not ttl:
        return False
        
    try:
        ttl_dt = datetime.fromisoformat(ttl.replace('Z', '+00:00'))
        return datetime.now(ttl_dt.tzinfo) > ttl_dt
    except (ValueError, AttributeError):
        logger.error(f"Invalid TTL format in message: {ttl}")
        return False


def should_retry(message: Dict[str, Any]) -> bool:
    """
    Check if a message should be retried based on retry count.
    
    Args:
        message: Message dictionary with optional retry count in metadata
        
    Returns:
        bool: True if message should be retried
    """
    retries = message.get('metadata', {}).get('retries', 0)
    return retries > 0


def decrement_retry_count(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decrement the retry count in message metadata.
    
    Args:
        message: Message dictionary with retry count
        
    Returns:
        Updated message dictionary
    """
    if 'metadata' not in message:
        message['metadata'] = {}
    
    current_retries = message['metadata'].get('retries', 0)
    message['metadata']['retries'] = max(0, current_retries - 1)
    
    return message


def archive_message(message: Dict[str, Any], reason: str) -> None:
    """
    Archive a message that has expired or exhausted retries.
    
    Args:
        message: Message dictionary to archive
        reason: Reason for archiving ('expired' or 'retry_exhausted')
    """
    archive_dir = Path('postbox/archive')
    archive_dir.mkdir(exist_ok=True)
    
    # Create archive file with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    archive_file = archive_dir / f"archived_{timestamp}.json"
    
    # Add archiving metadata
    archived_message = message.copy()
    archived_message['archive_metadata'] = {
        'archived_at': datetime.now().isoformat(),
        'reason': reason
    }
    
    try:
        with open(archive_file, 'w') as f:
            json.dump(archived_message, f, indent=2)
        logger.info(f"Archived message {message.get('id', 'unknown')} - Reason: {reason}")
    except Exception as e:
        logger.error(f"Error archiving message: {e}")


def route_message(message: Dict[str, Any], source_agent: str) -> None:
    """
    Route a message to its recipient's inbox, handling TTL and retries.
    
    Args:
        message: Message dictionary to route
        source_agent: ID of the sending agent
    """
    recipient = message.get('recipient')
    if not recipient:
        logger.error(f"Message missing recipient: {message}")
        return
    
    # Check TTL
    if is_message_expired(message):
        logger.info(f"Message expired (TTL): {message.get('id', 'unknown')}")
        archive_message(message, 'expired')
        return
    
    # Check retries
    if not should_retry(message):
        logger.info(f"Message out of retries: {message.get('id', 'unknown')}")
        archive_message(message, 'retry_exhausted')
        return
    
    # Decrement retry count
    message = decrement_retry_count(message)
    
    # Route to recipient's inbox
    inbox_path = Path(f"postbox/{recipient}/inbox.json")
    
    try:
        # Read existing messages
        if inbox_path.exists():
            with open(inbox_path, 'r') as f:
                messages = json.load(f)
        else:
            messages = []
        
        # Add new message
        messages.append(message)
        
        # Write back to inbox
        with open(inbox_path, 'w') as f:
            json.dump(messages, f, indent=2)
            
        logger.info(f"Routed message {message.get('id', 'unknown')} from {source_agent} to {recipient}")
        
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Error routing message to {recipient}: {e}")


def process_outboxes() -> None:
    """Process all agent outboxes and route messages."""
    logger.info("Starting message routing cycle")
    
    # Find all outbox.json files
    outbox_files = glob.glob("postbox/*/outbox.json")
    
    for outbox_file in outbox_files:
        agent_id = Path(outbox_file).parent.name
        
        try:
            with open(outbox_file, 'r') as f:
                messages = json.load(f)
            
            # Route each message
            for msg in messages:
                route_message(msg, agent_id)
            
            # Clear outbox after processing
            with open(outbox_file, 'w') as f:
                json.dump([], f)
                
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Error processing outbox {outbox_file}: {e}")
            continue
    
    logger.info("Message routing cycle complete")


def route_all_messages(dry_run: bool = False) -> Dict[str, List[str]]:
    """Route all messages from all agent outboxes."""
    postbox_dir = Path(__file__).parent.parent / "postbox"
    processed_dir = postbox_dir / "archive"
    schema = load_schema()
    
    agents = ['CC', 'CA', 'WA', 'ARCH']
    results = {
        'routed': [],
        'failed': [],
        'errors': []
    }
    
    print(f"🚀 Central Router starting {'(DRY RUN)' if dry_run else ''}...")
    print(f"📦 Scanning outboxes in {postbox_dir}")
    
    for agent in agents:
        print(f"\n📤 Checking {agent} outbox...")
        messages = scan_outbox(agent, postbox_dir)
        
        if not messages:
            print(f"   ✓ No messages to route")
            continue
        
        print(f"   Found {len(messages)} message(s)")
        routed_messages = []
        
        for msg in messages:
            msg_id = msg.get('id', 'unknown')
            recipient = msg.get('recipient', 'unknown')
            
            if dry_run:
                print(f"   [DRY RUN] Would route {msg_id} to {recipient}")
                results['routed'].append(f"{agent} -> {recipient}: {msg_id}")
            else:
                route_message(msg, agent)
                results['routed'].append(f"{agent} -> {recipient}: {msg_id}")
                routed_messages.append(msg)
        
        # Clear successfully routed messages from outbox
        if routed_messages and not dry_run:
            with open(postbox_dir / agent / "outbox.json", 'w') as f:
                json.dump([], f)
            print(f"   ✓ Cleared {len(routed_messages)} routed message(s) from outbox")
    
    # Summary
    print(f"\n📊 Routing Summary:")
    print(f"   ✓ Successfully routed: {len(results['routed'])}")
    print(f"   ❌ Failed: {len(results['failed'])}")
    
    if results['errors']:
        print("\n⚠️  Errors encountered:")
        for error in results['errors']:
            print(f"   - {error}")
    
    return results


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Central message router for agent communication")
    parser.add_argument('--route', action='store_true', help='Route all pending messages')
    parser.add_argument('--dry-run', action='store_true', help='Preview routing without making changes')
    
    args = parser.parse_args()
    
    if not args.route:
        print("Usage: router.py --route [--dry-run]")
        print("\nOptions:")
        print("  --route    Route all messages from agent outboxes to recipient inboxes")
        print("  --dry-run  Preview routing without making changes")
        return
    
    try:
        route_all_messages(dry_run=args.dry_run)
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())