#!/usr/bin/env python3
"""
Error recovery and fallback task routing system.

This module handles error message processing and fallback task activation:
- Detects error messages in agent inboxes
- Extracts fallback task information
- Creates and routes fallback tasks
- Logs recovery actions
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import uuid


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('recovery/recovery_log.md'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def is_error_message(message: Dict[str, Any]) -> bool:
    """
    Check if a message is an error message.
    
    Args:
        message: Message dictionary to check
        
    Returns:
        bool: True if message is an error message
    """
    return message.get('type') == 'error'


def has_fallback_task(message: Dict[str, Any]) -> bool:
    """
    Check if an error message has a fallback task defined.
    
    Args:
        message: Error message dictionary to check
        
    Returns:
        bool: True if message has fallback task
    """
    return 'fallback_task' in message.get('metadata', {})


def create_fallback_message(error_msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Create a new message from the fallback task definition.
    
    Args:
        error_msg: Error message containing fallback task
        
    Returns:
        Optional[Dict[str, Any]]: New message for fallback task or None if invalid
    """
    try:
        fallback_task = error_msg['metadata']['fallback_task']
        
        # Create new message with fallback task content
        new_message = {
            'id': str(uuid.uuid4()),
            'type': 'task_assignment',
            'timestamp': datetime.now().isoformat(),
            'content': fallback_task.get('content', {}),
            'metadata': {
                'is_fallback': True,
                'original_task_id': error_msg.get('content', {}).get('context', {}).get('task_id'),
                'error_code': error_msg.get('content', {}).get('error_code'),
                'error_message': error_msg.get('content', {}).get('message')
            }
        }
        
        # Copy recipient from fallback task or use default
        new_message['recipient'] = fallback_task.get('recipient', 'CA')
        
        return new_message
        
    except (KeyError, TypeError) as e:
        logger.error(f"Error creating fallback message: {e}")
        return None


def route_fallback_message(message: Dict[str, Any]) -> bool:
    """
    Route a fallback task message to the recipient's inbox.
    
    Args:
        message: Fallback task message to route
        
    Returns:
        bool: True if routing was successful
    """
    recipient = message.get('recipient')
    if not recipient:
        logger.error("Fallback message missing recipient")
        return False
    
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
            
        logger.info(f"Routed fallback task {message.get('id')} to {recipient}")
        return True
        
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Error routing fallback task to {recipient}: {e}")
        return False


def process_error_messages() -> None:
    """Process all agent inboxes for error messages and handle fallbacks."""
    logger.info("Starting error recovery cycle")
    
    # Find all inbox.json files
    inbox_files = Path("postbox").glob("*/inbox.json")
    
    for inbox_file in inbox_files:
        try:
            with open(inbox_file, 'r') as f:
                messages = json.load(f)
            
            # Process each message
            for msg in messages:
                if is_error_message(msg) and has_fallback_task(msg):
                    logger.info(f"Processing error message with fallback: {msg.get('id', 'unknown')}")
                    
                    # Create and route fallback task
                    fallback_msg = create_fallback_message(msg)
                    if fallback_msg:
                        if route_fallback_message(fallback_msg):
                            logger.info(f"Successfully activated fallback for error: {msg.get('content', {}).get('error_code')}")
                        else:
                            logger.error(f"Failed to route fallback task for error: {msg.get('content', {}).get('error_code')}")
            
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Error processing inbox {inbox_file}: {e}")
            continue
    
    logger.info("Error recovery cycle complete")


if __name__ == "__main__":
    process_error_messages() 