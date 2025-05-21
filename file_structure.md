# Bluelabel Agent OS - Repository Structure

```
.
├── apps/
│   ├── api/
│   │   ├── models/
│   │   │   ├── agent.py
│   │   │   ├── plan.py
│   │   │   └── task.py
│   │   ├── routers/
│   │   │   └── plans.py
│   │   ├── services/
│   │   │   └── plan_service.py
│   │   ├── main.py
│   │   └── sample_data.py
│   └── web/
│       ├── src/
│       │   ├── components/
│       │   │   ├── nodes/
│       │   │   │   └── TaskNode.tsx
│       │   │   ├── Layout.tsx
│       │   │   └── PlanDAGViewer.tsx
│       │   ├── pages/
│       │   │   ├── Agents.tsx
│       │   │   ├── Dashboard.tsx
│       │   │   └── PlanView.tsx
│       │   ├── api/
│       │   │   ├── agentApi.ts
│       │   │   ├── config.ts
│       │   │   └── taskApi.ts
│       │   ├── hooks/
│       │   │   ├── useAgents.ts
│       │   │   └── useTasks.ts
│       │   └── App.tsx
│       ├── package.json
│       ├── tsconfig.json
│       ├── tailwind.config.js
│       ├── postcss.config.js
│       └── README.md
├── docs/
│   ├── AGENT_ARCHITECTURE.md
│   ├── API_REFERENCE.md
│   ├── ARCHITECTURE.md
│   ├── DEVELOPMENT.md
│   ├── EXECUTION_FLOW.md
│   ├── ROADMAP.md
│   └── SYSTEM_OVERVIEW.md
├── postbox/
│   ├── ARCH/
│   │   ├── inbox.json
│   │   ├── outbox.json
│   │   └── task_log.md
│   ├── CA/
│   │   ├── inbox.json
│   │   ├── outbox.json
│   │   └── task_log.md
│   ├── CC/
│   │   ├── inbox.json
│   │   ├── outbox.json
│   │   └── task_log.md
│   └── WA/
│       ├── inbox.json
│       ├── outbox.json
│       └── task_log.md
├── tools/
│   ├── dashboard/
│   │   ├── components/
│   │   │   ├── agent_status.py
│   │   │   ├── live_tasks.py
│   │   │   └── message_feed.py
│   │   ├── layout/
│   │   │   └── styles.py
│   │   ├── dashboard_main.py
│   │   └── dashboard_config.py
│   ├── context_manager.py
│   ├── context_inspector.py
│   ├── flow_visualizer.py
│   ├── inbox_monitor.py
│   ├── task_dispatcher.py
│   └── task_status_tracker.py
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── AGENT_PROTOCOL.md
├── ARCH_PROTOCOL.md
├── CHANGELOG.md
├── CONTEXT_agent_comms.md
├── DEVELOPMENT.md
├── README.md
├── TASK_CARDS.md
├── file_structure.md
├── setup.py
└── setup.sh
```

## Directory Descriptions

### `/apps`
Contains the main application code split into two parts:
- `/api`: FastAPI backend application
- `/web`: React frontend application

### `/docs`
Documentation files for the project, including architecture, development guides, and API references.

### `/postbox`
Message storage for each agent in the system:
- ARCH: Task Router and Coordinator
- CA: Task Implementation Agent
- CC: Backend Infrastructure Agent
- WA: Web Interface Agent

### `/tools`
Utility scripts and tools for development and monitoring:
- `/dashboard`: Terminal-based dashboard for system monitoring
- Various CLI tools for task management and system inspection

### Root Files
- Configuration files (`.env.example`, `.gitignore`, etc.)
- Documentation files (`README.md`, `TASK_CARDS.md`, etc.)
- Setup scripts (`setup.py`, `setup.sh`) 