#!/usr/bin/env python3
"""
Central message router with TTL, retry, and learning support.

This module handles message routing between agents, including:
- TTL enforcement for message expiration
- Retry countdown and tracking
- Message archiving and logging
- Learning-based routing optimization
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


def load_learning_data() -> Optional[Dict[str, Any]]:
    """
    Load agent learning data from insights directory.
    
    Returns:
        Optional[Dict]: Learning data or None if not found
    """
    try:
        with open('insights/agent_learning_snapshot.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Learning data not found")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding learning data: {e}")
        return None


def get_best_agent_for_task(task_type: str, learning_data: Dict[str, Any]) -> Optional[str]:
    """
    Determine the best agent for a task type based on performance data.
    
    Args:
        task_type: Type of task to route
        learning_data: Learning snapshot data
        
    Returns:
        Optional[str]: Agent ID or None if no data available
    """
    if not learning_data:
        return None
    
    # Extract performance metrics from learning data
    performances = learning_data.get('agent_performances', {})
    
    best_agent = None
    best_score = -1
    
    for agent, metrics in performances.items():
        if task_type in metrics.get('successful_tasks', []):
            score = metrics.get('success_rate', 0) * 100 + (100 - metrics.get('avg_duration', 100))
            if score > best_score:
                best_score = score
                best_agent = agent
    
    return best_agent


def route_with_learning(message: Dict[str, Any], learning_data: Dict[str, Any]) -> Optional[str]:
    """
    Use learning data to determine optimal routing.
    
    Args:
        message: Message to route
        learning_data: Learning snapshot data
        
    Returns:
        Optional[str]: Suggested recipient agent ID
    """
    if not learning_data:
        return None
    
    # Extract task type from message
    task_type = message.get('content', {}).get('task_type')
    if not task_type:
        return None
    
    # Find best agent for task
    best_agent = get_best_agent_for_task(task_type, learning_data)
    
    return best_agent


def route_message(message: Dict[str, Any], source_agent: str, use_learning: bool = False) -> None:
    """
    Route a message to its recipient's inbox, handling TTL, retries, and learning.
    
    Args:
        message: Message dictionary to route
        source_agent: ID of the sending agent
        use_learning: Whether to use learning data for routing
    """
    recipient = message.get('recipient')
    
    # Check if learning-based routing should override the recipient
    if use_learning:
        learning_data = load_learning_data()
        learned_recipient = route_with_learning(message, learning_data)
        if learned_recipient:
            logger.info(f"Override routing: {recipient} -> {learned_recipient} (learning-based)")
            recipient = learned_recipient
    
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


def process_outboxes(use_learning: bool = False) -> None:
    """Process all agent outboxes and route messages.
    
    Args:
        use_learning: Whether to use learning data for routing decisions
    """
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
                route_message(msg, agent_id, use_learning)
            
            # Clear outbox after processing
            with open(outbox_file, 'w') as f:
                json.dump([], f)
                
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Error processing outbox {outbox_file}: {e}")
            continue
    
    logger.info("Message routing cycle complete")


def main():
    """Main entry point for the router."""
    parser = argparse.ArgumentParser(description='Agent Message Router')
    parser.add_argument('--continuous', action='store_true',
                       help='Run continuously, checking every 5 seconds')
    parser.add_argument('--learning', action='store_true',
                       help='Enable learning-based routing')
    parser.add_argument('--interval', type=int, default=5,
                       help='Interval between checks in continuous mode (seconds)')
    
    args = parser.parse_args()
    
    if args.continuous:
        import time
        logger.info(f"Starting continuous routing (interval: {args.interval}s)")
        while True:
            process_outboxes(use_learning=args.learning)
            time.sleep(args.interval)
    else:
        # Single run
        process_outboxes(use_learning=args.learning)


if __name__ == "__main__":
    main()