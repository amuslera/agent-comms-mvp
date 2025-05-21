"""Tests for message processing in the dashboard."""
import json
import os
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
import pytest

from .. import dashboard_config
from ..components.message_feed import MessageFeed
from ..components.live_tasks import LiveTasks


@pytest.fixture(autouse=True)
def setup_temp_dirs():
    """Set up temporary directories for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        # Update the global config
        dashboard_config.config.postbox_dir = temp_dir
        dashboard_config.config.context_dir = temp_dir / "context"
        dashboard_config.config.export_dir = temp_dir / "exports"
        
        # Create required directories
        dashboard_config.config.postbox_dir.mkdir(exist_ok=True)
        dashboard_config.config.context_dir.mkdir(exist_ok=True)
        dashboard_config.config.export_dir.mkdir(exist_ok=True)
        
        yield temp_dir


def create_test_outbox(dir_path: Path, content):
    """Create a test outbox file with the given content."""
    outbox = dir_path / "outbox.json"
    with open(outbox, 'w', encoding='utf-8') as f:
        if isinstance(content, (dict, list)):
            json.dump(content, f, indent=2, default=str)
        else:
            f.write(content)
    return outbox


def create_test_task_log(dir_path: Path, content):
    """Create a test task log file with the given content."""
    task_log = dir_path / "task_log.md"
    with open(task_log, 'w', encoding='utf-8') as f:
        f.write(content)
    return task_log


def test_message_feed_with_list(setup_temp_dirs):
    """Test that MessageFeed can handle a list of messages directly."""
    temp_dir = setup_temp_dirs
    agent_dir = temp_dir / "AGENT1"
    agent_dir.mkdir()
    
    # Create a list of messages directly with timezone-aware timestamps
    now = datetime.now(timezone.utc)
    messages = [
        {
            "from": "AGENT1",
            "to": "AGENT2",
            "type": "task",
            "content": "Test message 1",
            "timestamp": now.isoformat()
        },
        {
            "from": "AGENT2",
            "to": "AGENT1",
            "type": "result",
            "content": "Test result 1",
            "timestamp": (now + timedelta(seconds=1)).isoformat()
        }
    ]
    
    create_test_outbox(agent_dir, messages)
    
    # Test message feed
    feed = MessageFeed()
    
    # Should not raise an exception
    feed.update(force=True)
    assert len(feed.messages) == 2, f"Expected 2 messages, got {len(feed.messages)}"


def test_message_feed_with_messages_key(setup_temp_dirs):
    """Test that MessageFeed can handle messages in a 'messages' key."""
    temp_dir = setup_temp_dirs
    agent_dir = temp_dir / "AGENT1"
    agent_dir.mkdir()
    
    # Create messages in a 'messages' key with timezone-aware timestamp
    now = datetime.now(timezone.utc)
    outbox = {
        "metadata": {
            "version": "1.0",
            "agent": "AGENT1"
        },
        "messages": [
            {
                "from": "AGENT1",
                "to": "AGENT2",
                "type": "task",
                "content": "Test message 1",
                "timestamp": now.isoformat()
            }
        ]
    }
    
    create_test_outbox(agent_dir, outbox)
    
    # Test message feed
    feed = MessageFeed()
    
    # Should not raise an exception
    feed.update(force=True)
    assert len(feed.messages) == 1


def test_message_feed_with_invalid_format(setup_temp_dirs):
    """Test that MessageFeed handles invalid formats gracefully."""
    temp_dir = setup_temp_dirs
    agent_dir = temp_dir / "AGENT1"
    agent_dir.mkdir()
    
    # Create invalid JSON
    outbox = "This is not valid JSON"
    create_test_outbox(agent_dir, outbox)
    
    # Test message feed
    feed = MessageFeed()
    
    # Should not raise an exception
    feed.update(force=True)
    assert len(feed.messages) == 0


def test_live_tasks_parsing(setup_temp_dirs):
    """Test that LiveTasks can parse task logs correctly."""
    temp_dir = setup_temp_dirs
    agent_dir = temp_dir / "AGENT1"
    agent_dir.mkdir()
    
    # Create a task log with proper markdown formatting
    # Using recent timestamps to avoid being filtered out by retention
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    recent_time = now - timedelta(minutes=5)  # 5 minutes ago
    
    task_log = f"""## TASK-123 - in_progress
- Started at: {recent_time.strftime('%Y-%m-%d %H:%M:%S')}
- Description: Test task
- Retry count: 0

## TASK-124 - completed
- Started at: {recent_time.strftime('%Y-%m-%d %H:%M:%S')}
- Completed at: {(recent_time + timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S')}
- Result: Success
"""
    task_log_file = create_test_task_log(agent_dir, task_log)
    
    # Test live tasks with show_archived=True to ensure we see completed tasks
    tasks_component = LiveTasks()
    tasks_component._show_archived = True  # Show completed tasks for testing
    
    # Should not raise an exception
    tasks_component.update(force=True)
    
    # Debug output
    print(f"Found tasks: {len(tasks_component.tasks)}")
    for task in tasks_component.tasks:
        print(f"Task: {task['task_id']}, status: {task['status']}")
    
    # Check that we found the expected number of tasks
    # We expect both tasks because we set _show_archived=True
    assert len(tasks_component.tasks) == 2, f"Expected 2 tasks, found {len(tasks_component.tasks)}"
    
    # Check task statuses
    task_statuses = {t["task_id"]: t["status"] for t in tasks_component.tasks}
    assert "TASK-123" in task_statuses, "TASK-123 not found in tasks"
    assert task_statuses["TASK-123"] == "in_progress", f"TASK-123 has unexpected status: {task_statuses['TASK-123']}"
    assert "TASK-124" in task_statuses, "TASK-124 not found in tasks"
    assert task_statuses["TASK-124"] == "completed", f"TASK-124 has unexpected status: {task_statuses['TASK-124']}"
    
    # Test filtering of completed tasks when _show_archived is False
    tasks_component._show_archived = False
    tasks_component.update(force=True)
    visible_tasks = tasks_component._visible_tasks
    print(f"\nAfter filtering completed tasks: {len(visible_tasks)}")
    for task in visible_tasks:
        print(f"Task: {task['task_id']}, status: {task['status']}")
    
    # Now we should only see the in_progress task in visible_tasks
    assert len(visible_tasks) == 1, f"Expected 1 visible task, found {len(visible_tasks)}"
    assert visible_tasks[0]["task_id"] == "TASK-123", f"Expected TASK-123, found {visible_tasks[0]['task_id']}"
    
    # But the tasks list should still contain both tasks
    assert len(tasks_component.tasks) == 2, f"Expected 2 total tasks, found {len(tasks_component.tasks)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
