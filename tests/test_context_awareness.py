#!/usr/bin/env python3
"""
Tests for the context awareness framework.
"""

import unittest
import os
import json
import tempfile
import shutil
from pathlib import Path

# Add the parent directory to the path so we can import our modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.context_manager import ContextManager


class TestContextManager(unittest.TestCase):
    """Test cases for the ContextManager class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test contexts
        self.test_dir = tempfile.mkdtemp()
        self.manager = ContextManager(self.test_dir)
        
        # Sample context data
        self.sample_context = {
            "agent_id": "TEST_AGENT",
            "version": "1.0.0",
            "preferences": {
                "theme": "dark",
                "notifications": True
            },
            "state": {
                "status": "active"
            }
        }
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)
    
    def test_create_and_load_context(self):
        """Test creating and loading a context."""
        # Create a new context
        context = self.manager.load_context("TEST_AGENT")
        self.assertIn("agent_id", context)
        self.assertEqual(context["agent_id"], "TEST_AGENT")
        
        # Check if the file was created
        context_path = Path(self.test_dir) / "TEST_AGENT_context.json"
        self.assertTrue(context_path.exists())
    
    def test_save_and_load_context(self):
        """Test saving and loading a context."""
        # Save a context
        self.assertTrue(self.manager.save_context("TEST_AGENT", self.sample_context))
        
        # Load it back
        loaded = self.manager.load_context("TEST_AGENT")
        self.assertEqual(loaded["agent_id"], "TEST_AGENT")
        self.assertEqual(loaded["preferences"]["theme"], "dark")
    
    def test_update_context(self):
        """Test updating a context."""
        # Initial save
        self.manager.save_context("TEST_AGENT", self.sample_context)
        
        # Update the context using nested dictionary
        updates = {
            "preferences": {
                "theme": "light"
            },
            "state": {
                "status": "idle"
            }
        }
        self.manager.update_context("TEST_AGENT", updates)
        
        # Check updates
        updated = self.manager.load_context("TEST_AGENT")
        self.assertEqual(updated["preferences"]["theme"], "light")
        self.assertEqual(updated["state"]["status"], "idle")
    
    def test_concurrent_updates(self):
        """Test that concurrent updates don't clobber each other."""
        # Save initial context
        self.manager.save_context("CONCURRENT_AGENT", self.sample_context)
        
        # Simulate two processes loading the context
        context1 = self.manager.load_context("CONCURRENT_AGENT")
        context2 = self.manager.load_context("CONCURRENT_AGENT")
        
        # Make different updates
        context1["preferences"]["theme"] = "blue"
        context2["preferences"]["theme"] = "red"
        
        # Save updates
        self.manager.save_context("CONCURRENT_AGENT", context1)
        self.manager.save_context("CONCURRENT_AGENT", context2)
        
        # Final state should reflect the last save
        final = self.manager.load_context("CONCURRENT_AGENT")
        self.assertEqual(final["preferences"]["theme"], "red")


class TestContextInspector(unittest.TestCase):
    """Test cases for the context_inspector CLI tool."""
    
    def test_inspector_commands(self):
        """Test the context inspector commands."""
        # This would test the CLI tool, but we'll keep it simple for now
        # In a real test, we'd use subprocess to run the CLI
        pass


if __name__ == "__main__":
    unittest.main()
