# Bluelabel Agent OS - Multi-Agent Communication Framework

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A robust framework for building and orchestrating autonomous agents with built-in communication protocols, task management, and monitoring capabilities.

## 🚀 Features

- **Multi-Agent Architecture**: Coordinate multiple specialized agents
- **File-based Communication**: Simple, reliable message passing
- **Task Orchestration**: Plan and execute complex workflows
- **Monitoring & Logging**: Built-in observability tools
- **Extensible**: Easy to add new agents and capabilities

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/amuslera/agent-comms-mvp.git
   cd agent-comms-mvp
   ```

2. **Set up a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e .
   ```

   For development, install additional tools:
   ```bash
   pip install -r requirements-dev.txt
   ```

## 🛠️ Usage

### Running the Orchestrator
```bash
python -m tools.run_plan --help
```

### Using the CLI Runner
Run a plan:
```bash
python -m tools.cli.cli_runner plans/your-plan.yaml
```

View plan summary without executing:
```bash
python -m tools.cli.cli_runner plans/your-plan.yaml --summary
```

### Generating Execution Summaries
```bash
python -m tools.generate_execution_summary --help
```

### Monitoring the System
```bash
python -m tools.inbox_monitor
```

## 📂 Project Structure

```
agent-comms-mvp/
├── agents/               # Agent implementations
├── docs/                 # Documentation
├── plans/                # Task plan definitions
├── postbox/              # Message storage
├── tools/                # CLI tools and utilities
├── .env.example          # Example environment variables
├── README.md             # This file
└── setup.py             # Package configuration
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📚 Documentation

For detailed documentation, please see the [docs](docs/) directory.

## 📬 Contact

For questions or feedback, please open an issue on GitHub.
