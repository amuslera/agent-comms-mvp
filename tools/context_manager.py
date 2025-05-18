#!/usr/bin/env python3
"""
Context Manager for Agent Context Persistence

This module provides functionality to load, save, and manage agent context files.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ContextManager:
    """Manages agent context persistence."""
    
    def __init__(self, context_dir: str = "context"):
        """Initialize the context manager with the directory containing context files.
        
        Args:
            context_dir: Directory where context files are stored
        """
        self.context_dir = Path(context_dir)
        self.context_dir.mkdir(exist_ok=True)
        self.contexts = {}
    
    def get_context_path(self, agent_id: str) -> Path:
        """Get the path to an agent's context file.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Path to the context file
        """
        return self.context_dir / f"{agent_id}_context.json"
    
    def load_context(self, agent_id: str, create_if_missing: bool = True) -> Dict[str, Any]:
        """Load an agent's context from disk.
        
        Args:
            agent_id: ID of the agent
            create_if_missing: Whether to create a default context if none exists
            
        Returns:
            The agent's context as a dictionary
        """
        context_path = self.get_context_path(agent_id)
        
        if context_path.exists():
            try:
                with open(context_path, 'r') as f:
                    context = json.load(f)
                logger.debug(f"Loaded context for agent {agent_id} from {context_path}")
                self.contexts[agent_id] = context
                return context
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading context for {agent_id}: {e}")
                if create_if_missing:
                    return self._create_default_context(agent_id)
                raise
        elif create_if_missing:
            return self._create_default_context(agent_id)
        else:
            raise FileNotFoundError(f"Context file not found for agent {agent_id}")
    
    def save_context(self, agent_id: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Save an agent's context to disk.
        
        Args:
            agent_id: ID of the agent
            context: The context to save. If None, uses the in-memory context.
            
        Returns:
            True if successful, False otherwise
        """
        if context is None:
            context = self.contexts.get(agent_id)
            if context is None:
                logger.warning(f"No context found for agent {agent_id}")
                return False
        
        # Update the timestamp
        context['updated_at'] = datetime.now().isoformat()
        
        context_path = self.get_context_path(agent_id)
        
        try:
            # Ensure the directory exists
            context_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to a temporary file first to avoid corruption
            temp_path = context_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(context, f, indent=2)
            
            # Atomically replace the old file
            temp_path.replace(context_path)
            
            # Update the in-memory context
            self.contexts[agent_id] = context
            
            logger.debug(f"Saved context for agent {agent_id} to {context_path}")
            return True
        except (IOError, TypeError) as e:
            logger.error(f"Error saving context for {agent_id}: {e}")
            # Clean up temp file if it exists
            if 'temp_path' in locals() and temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            return False
    
    def update_context(
        self, 
        agent_id: str, 
        updates: Dict[str, Any], 
        save: bool = True
    ) -> bool:
        """Update specific fields in an agent's context.
        
        Args:
            agent_id: ID of the agent
            updates: Dictionary of updates to apply
            save: Whether to save the context after updating
            
        Returns:
            True if successful, False otherwise
        """
        context = self.contexts.get(agent_id)
        if context is None:
            context = self.load_context(agent_id)
        
        # Deep update the context
        self._deep_update(context, updates)
        
        # Update the in-memory context
        self.contexts[agent_id] = context
        
        if save:
            return self.save_context(agent_id, context)
        return True
    
    def _deep_update(self, original: Dict[str, Any], updates: Dict[str, Any]) -> None:
        """Recursively update a dictionary."""
        for key, value in updates.items():
            if (key in original and isinstance(original[key], dict) 
                    and isinstance(value, dict)):
                self._deep_update(original[key], value)
            else:
                original[key] = value
    
    def _create_default_context(self, agent_id: str) -> Dict[str, Any]:
        """Create a default context for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            A new default context dictionary
        """
        now = datetime.now().isoformat()
        default_context = {
            "agent_id": agent_id,
            "created_at": now,
            "updated_at": now,
            "version": "1.0.0",
            "preferences": {},
            "knowledge": {},
            "state": {},
            "history": {},
            "custom": {}
        }
        
        # Save the default context
        self.save_context(agent_id, default_context)
        return default_context


def get_context(agent_id: str) -> Dict[str, Any]:
    """Helper function to get an agent's context."""
    return ContextManager().load_context(agent_id)

def save_context(agent_id: str, context: Dict[str, Any]) -> bool:
    """Helper function to save an agent's context."""
    return ContextManager().save_context(agent_id, context)

def update_context(agent_id: str, updates: Dict[str, Any], save: bool = True) -> bool:
    """Helper function to update an agent's context."""
    return ContextManager().update_context(agent_id, updates, save)


if __name__ == "__main__":
    # Example usage
    manager = ContextManager()
    
    # Load or create a context
    context = manager.load_context("TEST_AGENT")
    print(f"Loaded context: {context}")
    
    # Update the context
    updates = {
        "preferences": {
            "theme": "dark",
            "notifications": True
        },
        "state": {
            "status": "active"
        }
    }
    
    manager.update_context("TEST_AGENT", updates)
    
    # Save the context
    manager.save_context("TEST_AGENT")
    
    print(f"Updated context: {manager.load_context('TEST_AGENT')}")
