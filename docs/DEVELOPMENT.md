# Development Guide - Bluelabel Agent OS

This guide covers the complete development workflow for the Bluelabel Agent OS, a multi-agent communication framework with modern web interfaces.

## 🏗️ Project Architecture Overview

The Bluelabel Agent OS is structured as a monorepo with the following key components:

```
agent-comms-mvp/
├── apps/
│   ├── api/                    # FastAPI backend service
│   └── web/                    # React + Vite frontend
├── docs/                       # Documentation
├── postbox/                    # Agent message storage
├── tools/                      # CLI utilities and agents
├── contexts/                   # Agent profiles and capabilities
├── plans/                      # YAML execution plans
├── tests/                      # Test suites
└── requirements-*.txt          # Python dependencies
```

### Core Components

- **Agents**: Autonomous components that communicate via file-based messages
- **Orchestrator**: Executes complex workflows defined in YAML plans
- **API Layer**: FastAPI service exposing system state to frontends
- **Web Interface**: React dashboard for monitoring and control
- **CLI Tools**: Command-line utilities for development and operation

## 🛠️ Local Development Setup

### Prerequisites

- **Python**: 3.8+ (recommended: 3.10+)
- **Node.js**: 18+ (for React frontend)
- **Git**: For version control

### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/amuslera/agent-comms-mvp.git
cd agent-comms-mvp

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -e .
pip install -r requirements-dev.txt
pip install -r requirements-dashboard.txt

# For FastAPI backend, also install:
pip install fastapi uvicorn pydantic

# Install Node.js dependencies for web frontend
cd apps/web
npm install
cd ../..
```

### 2. Configuration

Copy the example environment file (if it exists):
```bash
cp .env.example .env  # Edit as needed
```

## 🚀 Running the System

### Running Agents Locally

The system includes four main agents:

#### Agent Profiles

| Agent | Role | Capabilities |
|-------|------|-------------|
| **CC** (Claude Code) | Backend Infrastructure | System implementation, message routing, debugging |
| **CA** (Cursor AI) | Task Implementation | Code validation, runtime flow, task execution |
| **WA** (Web Assistant) | UI/Tooling | Dashboard development, CLI tools, visualization |
| **ARCH** | Orchestrator | Task routing, coordination, plan execution |

#### Start Individual Agents

```bash
# Run an agent (CC, CA, WA, or ARCH)
python agent_runner.py CC

# Initialize an agent with its profile
python agent_runner.py CC --init

# Run in simulation mode
python agent_runner.py CA --simulate

# Clear agent's message queue
python agent_runner.py WA --clear
```

#### ARCH Orchestrator

```bash
# Execute a plan file
python arch_orchestrator.py plans/sample_plan.yaml

# Execute with specific timeout
python arch_orchestrator.py plans/sample_plan.yaml --timeout 300

# Dry run (validate without executing)
python arch_orchestrator.py plans/sample_plan.yaml --dry-run
```

### Task Submission and Tracking

#### Manual Task Injection

```bash
# Interactive task dispatcher
python tools/task_dispatcher.py

# Monitor agent inboxes
python tools/inbox_monitor.py

# Track task statuses across all agents
python tools/task_status_tracker.py

# Real-time message flow visualization
python tools/flow_visualizer.py
```

#### Message Router

```bash
# Route messages between agents
python router/router.py --route

# Route specific agent's messages
python router/router.py --agent CC --route
```

### FastAPI Backend

The API service exposes system state for frontend consumption:

```bash
# Start FastAPI development server
cd apps/api
python -m uvicorn main:app --reload --port 8000

# Alternative: Run with Python directly
python main.py
```

**API Endpoints:**
- `GET /health` - Health check
- `GET /agents` - List all agents
- `GET /agents/{agent_id}` - Get specific agent details
- `GET /tasks` - List tasks with filtering
- `GET /tasks/{task_id}` - Get specific task details
- `POST /plans` - Submit execution plans
- `GET /plans` - List submitted plans
- `GET /plans/{plan_id}` - Get plan status

**API Documentation:** Available at `http://localhost:8000/docs` when running

### React Frontend

The web interface provides real-time monitoring and control:

```bash
# Start development server
cd apps/web
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

**Frontend Features:**
- Agent status monitoring
- Task execution dashboard
- Outbox message visualization
- Plan submission interface
- Real-time updates via polling

**Access:** `http://localhost:5173` (development)

## 🔄 Development Workflow

### Branch Naming Convention

```
feat/TASK-XXX-description          # New features
fix/TASK-XXX-description           # Bug fixes
docs/TASK-XXX-description          # Documentation updates
refactor/TASK-XXX-description      # Code refactoring
test/TASK-XXX-description          # Test additions
```

Examples:
- `feat/TASK-061I-dev-docs`
- `fix/TASK-052-dashboard-bugfix`
- `docs/TASK-045A-system-overview`

### Task Assignment Process

1. **Task Creation**: Tasks are tracked in `TASK_CARDS.md`
2. **Branch Creation**: Create feature branch following naming convention
3. **Development**: Implement changes following coding standards
4. **Testing**: Run relevant test suites
5. **Documentation**: Update docs as needed
6. **Review**: Submit for code review (via CC agent)
7. **Merge**: CC agent handles all merges to main

### Merge Policy

- **All merges go through CC (Claude Code)**
- CC reviews code quality, architecture, and integration
- Use pull requests for review process
- Squash commits when merging to main
- Update `TASK_CARDS.md` on completion
- Notify ARCH via outbox message

### Development Standards

#### Python Code Style
```bash
# Format code
black .
isort .

# Lint code
flake8 .
mypy .

# Run tests
pytest --cov=.
```

#### TypeScript/React Standards
```bash
# Lint and format
npm run lint
npm run build  # Ensures type checking

# Type checking
npx tsc --noEmit
```

## 🧪 Testing

### Python Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test files
pytest tests/test_agent_flow.py
pytest tests/test_orchestrator_retry.py

# Run dashboard tests
pytest tests/test_dashboard.py
```

### Integration Tests

```bash
# End-to-end agent flow test
python tests/test_agent_flow.py

# Orchestrator retry logic test
python tools/test_retry_fallback.py

# Context awareness test
python tests/test_context_awareness.py
```

### Frontend Tests

```bash
cd apps/web
# Run any configured tests (add as needed)
npm test
```

## 📁 Key Directories Explained

### `/postbox/`
File-based message storage for agent communication:
```
postbox/
├── ARCH/          # Orchestrator messages
├── CA/            # Cursor AI messages  
├── CC/            # Claude Code messages
└── WA/            # Web Assistant messages
```

Each agent folder contains:
- `inbox.json` - Incoming messages
- `outbox.json` - Outgoing messages
- `task_log.md` - Task execution history

### `/contexts/`
Agent profiles and capabilities:
- `*_PROFILE.md` - Agent role definitions
- `*_context.json` - Agent memory/state

### `/plans/`
YAML execution plans for complex workflows:
- Task definitions
- Dependencies
- Retry/fallback logic
- Agent assignments

### `/tools/`
CLI utilities for system operation:
- Agent learning and insights
- Task monitoring and visualization
- System administration tools

## 🔧 Configuration

### Environment Variables

Create `.env` file in project root:
```env
# API Configuration
API_PORT=8000
API_HOST=0.0.0.0

# Frontend Configuration
VITE_API_BASE_URL=http://localhost:8000

# Agent Configuration
DEFAULT_TIMEOUT=120
MAX_RETRIES=3

# Development
DEBUG=true
LOG_LEVEL=INFO
```

### Agent Configuration

Agent behavior can be configured through:
- Context files (`context/*.json`)
- Plan files (`plans/*.yaml`)
- Environment variables
- Command-line flags

## 🚨 Troubleshooting

### Common Issues

**Agent Not Responding**
```bash
# Check agent logs
python agent_runner.py CC --init

# Clear message queue
python agent_runner.py CC --clear

# Monitor inbox
python tools/inbox_monitor.py
```

**FastAPI Import Errors**
```bash
# Install FastAPI dependencies
pip install fastapi uvicorn pydantic

# Verify installation
python -c "import fastapi; print('FastAPI OK')"
```

**Frontend Build Issues**
```bash
cd apps/web
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check for TypeScript errors
npx tsc --noEmit
```

**Message Routing Problems**
```bash
# Run router manually
python router/router.py --route

# Check message validation
python tools/inbox_monitor.py
```

### Debugging Tools

- **Agent Logs**: Check `postbox/*/task_log.md`
- **System Insights**: Use `tools/agent_learning_cli.py`
- **Message Flow**: Use `tools/flow_visualizer.py`
- **Execution Summary**: Use `tools/generate_execution_summary.py`

## 📚 Additional Resources

- **[API Reference](API_REFERENCE.md)** - Complete API documentation
- **[Architecture Guide](ARCHITECTURE.md)** - System architecture details
- **[Agent Architecture](AGENT_ARCHITECTURE.md)** - Agent design patterns
- **[Execution Flow](EXECUTION_FLOW.md)** - Task execution lifecycle
- **[System Overview](SYSTEM_OVERVIEW.md)** - High-level system concepts

## 🤝 Contributing

1. Check `TASK_CARDS.md` for available tasks
2. Create feature branch using naming convention
3. Follow coding standards and testing requirements
4. Update documentation as needed
5. Submit for review through CC agent
6. Ensure ARCH is notified of completion

For questions or issues, create a task in `TASK_CARDS.md` or contact the development team.