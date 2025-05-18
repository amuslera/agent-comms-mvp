#!/usr/bin/env python3
"""
Central message router with retry and TTL support.

This module handles message routing between agents, including:
- TTL enforcement for message expiration
- Retry logic for failed messages
- Logging of routing actions
"""

import json
import glob
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
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


def is_message_expired(message: Dict[str, Any]) -> bool:
    """
    Check if a message has expired based on its TTL.
    
    Args:
        message: Message dictionary with optional TTL
        
    Returns:
        bool: True if message has expired
    """
    ttl = message.get('metadata', {}).get('ttl')
    if not ttl:
        return False
        
    try:
        ttl_dt = datetime.fromisoformat(ttl.replace('Z', '+00:00'))
        return datetime.now(tll_dt.tzinfo) > ttl_dt
    except (ValueError, AttributeError):
        logger.error(f"Invalid TTL format in message: {ttl}")
        return False


def should_retry(message: Dict[str, Any]) -> bool:
    """
    Check if a message should be retried.
    
    Args:
        message: Message dictionary with optional retry count
        
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


def route_message(message: Dict[str, Any], source_agent: str, use_learning: bool = False) -> None:
    """
    Route a message to its recipient's inbox.
    
    Args:
        message: Message dictionary to route
        source_agent: ID of the sending agent
        use_learning: Whether to use learning data for routing
    """
    recipient = message.get('recipient')
    
    # Check if learning-based routing should override the recipient
    if use_learning:
        learned_recipient = route_with_learning(message, use_learning)
        if learned_recipient:
            logger.info(f"Override routing: {recipient} -> {learned_recipient} (learning-based)")
            recipient = learned_recipient
    
    if not recipient:
        logger.error(f"Message missing recipient: {message}")
        return
    
    # Check TTL
    if is_message_expired(message):
        logger.info(f"Message expired (TTL): {message.get('id', 'unknown')}")
        return
    
    # Check retries
    if not should_retry(message):
        logger.info(f"Message out of retries: {message.get('id', 'unknown')}")
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
    try:
        task_rankings = learning_data.get('task_type_rankings', {}).get(task_type, {})
        if task_rankings:
            # Return the first (highest-ranked) agent
            return list(task_rankings.keys())[0]
    except Exception as e:
        logger.error(f"Error determining best agent: {e}")
    
    return None


def route_with_learning(message: Dict[str, Any], use_learning: bool = False) -> Optional[str]:
    """
    Enhanced routing with optional learning-based decision making.
    
    Args:
        message: Message to route
        use_learning: Whether to use learning data for routing
        
    Returns:
        Optional[str]: Target agent ID or None to use default routing
    """
    if not use_learning:
        return None
    
    learning_data = load_learning_data()
    if not learning_data:
        return None
    
    # Extract task type from message
    task_desc = message.get('content', {}).get('description', '')
    task_type = task_desc.split(':')[0].strip() if ':' in task_desc else None
    
    if not task_type:
        return None
    
    best_agent = get_best_agent_for_task(task_type, learning_data)
    if best_agent:
        logger.info(f"Learning-based routing: Task type '{task_type}' -> Agent '{best_agent}'")
    
    return best_agent


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Message router with learning support')
    parser.add_argument('--use-learning', action='store_true',
                       help='Enable learning-based routing decisions')
    
    args = parser.parse_args()
    
    if args.use_learning:
        logger.info("Learning-based routing enabled")
    
    process_outboxes(use_learning=args.use_learning) 