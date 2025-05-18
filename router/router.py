#!/usr/bin/env python3
"""
Central message router for agent communication system.
Routes messages from agent outboxes to recipient inboxes.
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
import jsonschema
from typing import Dict, List, Tuple


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


def route_message(message: Dict, schema: Dict, postbox_dir: Path, processed_dir: Path) -> Tuple[bool, str]:
    """Route a single message to the recipient's inbox."""
    # Validate message
    valid, error = validate_message(message, schema)
    if not valid:
        return False, f"Validation error: {error}"
    
    # Get recipient
    recipient = message.get('recipient')
    if not recipient:
        return False, "No recipient specified"
    
    # Check if recipient directory exists
    recipient_inbox = postbox_dir / recipient / "inbox.json"
    if not recipient_inbox.parent.exists():
        return False, f"Recipient {recipient} does not exist"
    
    # Load current inbox
    inbox_messages = []
    if recipient_inbox.exists():
        with open(recipient_inbox, 'r') as f:
            content = json.load(f)
            if isinstance(content, list):
                inbox_messages = content
    
    # Add message to inbox
    inbox_messages.append(message)
    
    # Write updated inbox
    with open(recipient_inbox, 'w') as f:
        json.dump(inbox_messages, f, indent=2)
    
    # Archive the message
    archive_message(message, processed_dir)
    
    return True, f"Message {message.get('id', 'unknown')} routed to {recipient}"


def archive_message(message: Dict, processed_dir: Path):
    """Archive a processed message."""
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    message_id = message.get('id', 'unknown')
    filename = f"{timestamp}_{message_id}.json"
    
    with open(processed_dir / filename, 'w') as f:
        json.dump(message, f, indent=2)


def clear_outbox(agent: str, postbox_dir: Path, messages_to_remove: List[Dict]):
    """Remove routed messages from an agent's outbox."""
    outbox_path = postbox_dir / agent / "outbox.json"
    
    with open(outbox_path, 'r') as f:
        current_messages = json.load(f)
    
    # Remove routed messages by ID
    routed_ids = {msg.get('id') for msg in messages_to_remove}
    remaining_messages = [msg for msg in current_messages if msg.get('id') not in routed_ids]
    
    with open(outbox_path, 'w') as f:
        json.dump(remaining_messages, f, indent=2)


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
                success, result = route_message(msg, schema, postbox_dir, processed_dir)
                
                if success:
                    print(f"   ✓ Routed {msg_id} to {recipient}")
                    results['routed'].append(f"{agent} -> {recipient}: {msg_id}")
                    routed_messages.append(msg)
                else:
                    print(f"   ❌ Failed to route {msg_id}: {result}")
                    results['failed'].append(f"{msg_id}: {result}")
                    results['errors'].append(result)
        
        # Clear successfully routed messages from outbox
        if routed_messages and not dry_run:
            clear_outbox(agent, postbox_dir, routed_messages)
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