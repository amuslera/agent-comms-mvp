"""Tests for the Bluelabel Agent OS Dashboard."""

import os
import json
import time
import shutil
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timedelta

# Import components to test
from tools.dashboard.components.agent_status import AgentStatus
from tools.dashboard.components.live_tasks import LiveTasks
from tools.dashboard.components.message_feed import MessageFeed

class TestDashboardComponents(unittest.TestCase):
    """Test cases for dashboard components."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.postbox_dir = self.test_dir / "postbox"
        self.postbox_dir.mkdir()
        
        # Create test agent directories
        self.agent_dirs = {
            "ARCH": self.postbox_dir / "ARCH",
            "CA": self.postbox_dir / "CA",
            "CC": self.postbox_dir / "CC",
            "WA": self.postbox_dir / "WA",
        }
        
        for agent_dir in self.agent_dirs.values():
            agent_dir.mkdir()
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)
    
    def _create_test_outbox(self, agent: str, num_messages: int = 3) -> None:
        """Create a test outbox file with sample messages."""
        outbox = {
            "agent": agent,
            "messages": []
        }
        
        for i in range(num_messages):
            outbox["messages"].append({
                "from": agent,
                "to": "BROADCAST" if i % 2 == 0 else "ARCH",
                "type": ["task", "result", "error", "info"][i % 4],
                "content": f"Test message {i} from {agent}",
                "timestamp": (datetime.now() - timedelta(minutes=i)).isoformat()
            })
        
        outbox_file = self.agent_dirs[agent] / "outbox.json"
        with open(outbox_file, 'w') as f:
            json.dump(outbox, f, indent=2)
    
    def _create_test_task_log(self, agent: str, num_tasks: int = 2) -> None:
        """Create a test task log file."""
        task_log = []
        now = datetime.now()
        
        for i in range(num_tasks):
            task_time = now - timedelta(minutes=30*i)
            task_log.extend([
                f"## Task-{i:03d} - {'completed' if i % 2 == 0 else 'in_progress'}",
                f"- Started at: {task_time.strftime('%Y-%m-%d %H:%M:%S')}",
                f"- Description: Test task {i}",
                f"- Retry count: {i}",
            ])
            
            if i % 2 == 0:  # Completed task
                task_log.extend([
                    f"- Completed at: {(task_time + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')}",
                    "- Result: Success"
                ])
            
            if i == 1:  # Add a fallback for the second task
                task_log.append("- Fallback to: ARCH")
            
            task_log.append("\n")  # Add space between tasks
        
        task_log_file = self.agent_dirs[agent] / "task_log.md"
        with open(task_log_file, 'w') as f:
            f.write("\n".join(task_log))
    
    def test_agent_status_component(self):
        """Test the AgentStatus component."""
        # Create test data
        self._create_test_outbox("ARCH")
        self._create_test_task_log("ARCH")
        
        # Initialize component
        agent_status = AgentStatus(postbox_dir=str(self.postbox_dir))
        
        # Test update
        agent_status.update()
        
        # Verify data
        self.assertIn("ARCH", agent_status.agent_data)
        self.assertEqual(agent_status.agent_data["ARCH"]["outbox_count"], 3)
        self.assertEqual(agent_status.agent_data["ARCH"]["task_count"], 2)
        
        # Test render
        panel = agent_status.render()
        self.assertIsNotNone(panel)
    
    def test_live_tasks_component(self):
        """Test the LiveTasks component."""
        # Create test data
        self._create_test_task_log("ARCH")
        
        # Initialize component
        live_tasks = LiveTasks(postbox_dir=str(self.postbox_dir))
        
        # Test update
        live_tasks.update()
        
        # Verify data
        self.assertEqual(len(live_tasks.tasks), 2)
        self.assertEqual(live_tasks.tasks[0]["task_id"], "Task-001")
        self.assertEqual(live_tasks.tasks[1]["task_id"], "Task-000")
        
        # Test render
        panel = live_tasks.render()
        self.assertIsNotNone(panel)
    
    def test_message_feed_component(self):
        """Test the MessageFeed component."""
        # Create test data
        self._create_test_outbox("ARCH")
        
        # Initialize component
        message_feed = MessageFeed(postbox_dir=str(self.postbox_dir))
        
        # Test update
        message_feed.update()
        
        # Verify data
        self.assertEqual(len(message_feed.messages), 3)
        self.assertEqual(message_feed.messages[0]["from"], "ARCH")
        
        # Test render
        panel = message_feed.render()
        self.assertIsNotNone(panel)
    
    def test_agent_status_with_multiple_agents(self):
        """Test AgentStatus with multiple agents."""
        # Create test data for multiple agents
        for agent in ["ARCH", "CA", "CC"]:
            self._create_test_outbox(agent, num_messages=2)
            self._create_test_task_log(agent, num_tasks=1)
        
        # Initialize component
        agent_status = AgentStatus(postbox_dir=str(self.postbox_dir))
        agent_status.update()
        
        # Verify data
        self.assertEqual(len(agent_status.agent_data), 3)
        for agent in ["ARCH", "CA", "CC"]:
            self.assertIn(agent, agent_status.agent_data)
            self.assertEqual(agent_status.agent_data[agent]["outbox_count"], 2)
            self.assertEqual(agent_status.agent_data[agent]["task_count"], 1)

if __name__ == "__main__":
    unittest.main()
