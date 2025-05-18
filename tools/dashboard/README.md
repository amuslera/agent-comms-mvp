# Bluelabel Agent OS - Dashboard

An interactive terminal-based dashboard for monitoring agent communications and tasks in the Bluelabel Agent OS.

## Features

- **Real-time Monitoring**: View agent statuses, tasks, and messages in real-time
- **Agent Filtering**: Filter tasks and messages by agent ID
- **Task Management**: View and manage active tasks with status indicators
- **Message Feed**: Monitor inter-agent communication
- **Data Export**: Export task and message data to JSON files
- **Responsive UI**: Adapts to different terminal sizes

## Installation

1. Ensure you have Python 3.8+ installed
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Configuration is handled through environment variables and the `dashboard_config.py` file.

### Environment Variables

- `POSTBOX_DIR`: Directory for agent postboxes (default: `postbox`)
- `CONTEXT_DIR`: Directory for context files (default: `context`)
- `EXPORT_DIR`: Directory for exported data (default: `exports`)

## Usage

```bash
python -m tools.dashboard.dashboard_main
```

### Keyboard Shortcuts

- **q**: Quit the dashboard
- **f**: Show agent filter menu
- **e**: Export data to files
- **a**: Toggle display of archived tasks
- **↑/↓**: Scroll through tasks/messages
- **Page Up/Down**: Scroll faster
- **Home/End**: Jump to top/bottom
- **?**: Show help

## Features in Detail

### Agent Status Panel

Displays the current status of all agents in the system, including:
- Active/Inactive status
- Current task
- Last heartbeat time
- Error status

### Live Tasks Panel

Shows all active and recent tasks with:
- Task ID and description
- Agent assignment
- Status indicators (pending, in progress, completed, failed)
- Timestamps
- Progress indicators for long-running tasks

### Message Feed

Displays inter-agent communication including:
- Message type and content
- Sender and recipient
- Timestamps
- Message status

### Filtering

Filter tasks and messages by agent ID using the filter menu (press `f`).

### Data Export

Export task and message data to JSON files in the export directory.

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

This project uses `black` for code formatting and `flake8` for linting.

```bash
black .
flake8
```

## License

[License Information]
