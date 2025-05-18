# Bluelabel Agent OS - Dashboard Sample

This document provides a sample of the Bluelabel Agent OS Command Center Dashboard and instructions for using it.

## Screenshot

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                   BLUELABEL AGENT OS                    ┃
┃                COMMAND CENTER DASHBOARD                 ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 🤖 Agents                              Updated: 14:30:45 ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ ┌────────┬────────────┬────────┬────────┬──────────────┐ │
│ │ Agent  │ Status     │ Tasks  │ Outbox │ Last Active  │ │
│ ├────────┼────────────┼────────┼────────┼──────────────┤ │
│ │ ARCH   │ ● Active   │     42 │     15 │ 14:30:42     │ │
│ │ CA     │ ● Active   │     12 │      8 │ 14:30:40     │ │
│ │ CC     │ ● Idle     │     25 │     12 │ 14:25:15     │ │
│ │ WA     │ ○ Inactive │      0 │      0 │ Never        │ │
│ ├────────┼────────────┼────────┼────────┼──────────────┤ │
│ │ Total  │ 2 active   │     79 │     35 │              │ │
│ └────────┴────────────┴────────┴────────┴──────────────┘ │
└──────────────────────────────────────────────────────────┘

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
│ 📋 Tasks                              Showing 5 of 12 tasks ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ ┌──────────┬──────┬───────────┬─────────┬─────────┬────────┐ │
│ │ Task ID  │Agent │ Status    │ Retries │Fallback │Duration│ │
│ ├──────────┼──────┼───────────┼─────────┼─────────┼────────┤ │
│ │ TASK-045 │ ARCH │ ✅ Completed │    0    │    -    │ 1m 23s │ │
│ │ TASK-046 │  CA  │ 🔄 In Progress│    2    │   ARCH  │ 12m 45s│ │
│ │ TASK-044 │  CC  │ ❌ Failed    │    3    │    -    │ 0m 05s │ │
│ │ TASK-043 │ ARCH │ ✅ Completed │    0    │    -    │ 0m 45s │ │
│ │ TASK-042 │  WA  │ ⏳ Pending   │    0    │    -    │   -    │ │
│ ├──────────┼──────┼───────────┼─────────┼─────────┼────────┤ │
│ │ Total: 12 │      │ ✓ 8 | ↻ 2 | ✗ 2 │         │         │        │ │
│ └──────────┴──────┴───────────┴─────────┴─────────┴────────┘ │
└──────────────────────────────────────────────────────────┘
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
│ 📨 Message Feed                     Showing 3 of 15 messages ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 14:30:45 ℹ️  [CA → ARCH] Agent CA connected to the system    │
│                                                          │
│ 14:30:42 📝 [ARCH → BROADCAST]                              │
│ {
│   "task_id": "TASK-046",
│   "description": "Update dashboard UI",
│   "status": "in_progress"
│ }                                                         │
│                                                          │
│ 14:30:40 ✅ [CC → ARCH] Task TASK-045 completed successfully │
│                                                          │
└──────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────┐
│ q: Quit • r: Refresh • s: Save • ↑/↓: Scroll • h: Help  │
└──────────────────────────────────────────────────────────┘
```

## Usage

### Starting the Dashboard

```bash
# Basic usage
python3 tools/dashboard/dashboard_main.py

# With custom refresh interval (in seconds)
python3 tools/dashboard/dashboard_main.py --refresh 5

# With custom postbox directory
python3 tools/dashboard/dashboard_main.py --postbox-dir /path/to/postbox
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `q` | Quit the dashboard |
| `r` | Force refresh |
| `s` | Save current view to a file |
| `↑/↓` | Scroll through messages |
| `h` | Show help |

## Features

### Agent Status Panel
- Displays status of all agents (Active/Idle/Inactive)
- Shows number of completed tasks and messages in outbox
- Indicates when each agent was last active

### Tasks Panel
- Lists all tasks with their current status
- Shows retry count and fallback agent (if any)
- Displays task duration
- Color-coded status indicators

### Message Feed
- Real-time display of inter-agent communication
- Color-coded by message type (task, result, error, info)
- Shows timestamps and message direction
- Pretty-prints JSON content

## Customization

### Colors and Styling
Customize the dashboard appearance by modifying the styles in `tools/dashboard/layout/styles.py`.

### Adding New Components
To add a new component:
1. Create a new Python file in `tools/dashboard/components/`
2. Implement the `update()` and `render()` methods
3. Import and add it to the main dashboard layout

## Troubleshooting

- **Dashboard not updating**: Ensure the postbox directory exists and has correct permissions
- **No agents visible**: Check that agent directories exist in the postbox directory
- **Missing messages**: Verify that outbox.json files are being created by agents

## License

This dashboard is part of the Bluelabel Agent OS project and is licensed under the MIT License.
