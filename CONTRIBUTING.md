# Contributing to Bluelabel Agent OS

Thank you for your interest in contributing! This guide will help you get started and understand our workflow and structure.

## Quickstart

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd agent-comms-mvp
   ```
2. **Install dependencies:**
   - **Backend (Python):**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     pip install -r requirements.txt
     ```
   - **Frontend (React/Node):**
     ```bash
     cd apps/web
     npm install
     # or
     yarn install
     ```
3. **Run development servers:**
   - **Backend:**
     ```bash
     uvicorn apps.api.main:app --reload
     ```
   - **Frontend:**
     ```bash
     cd apps/web
     npm run dev
     ```

## Folder Overview

- `/apps/`      — Application code (API backend, web frontend)
- `/tools/`     — CLI tools, agent runners, routers, utilities
- `/docs/`      — Documentation (system, protocols, features)
- `/schemas/`   — JSON/YAML schemas and examples
- `/postbox/`   — Agent inboxes/outboxes for message passing
- `/contexts/`  — Agent context and profile files
- `/features/`  — Feature-specific modules (if present)

## Using .env

- Copy `.env.example` to `.env` and fill in required values (API keys, secrets, config).
- Both backend and frontend may use environment variables for configuration.
- Never commit secrets or credentials to the repository.

## Task Workflow

- **Task Cards:**
  - All work is tracked in `TASK_CARDS.md`.
  - Each task has a unique ID (e.g., TASK-076E) and status.
- **Branches:**
  - Use feature branches named after the task (e.g., `feat/TASK-076E-contributing-and-structure`).
- **Prompts:**
  - Prompt templates for agents are in `/prompts/`.
- **ARCH Notifications:**
  - Major task completions are reported to ARCH via outbox (see `/postbox/ARCH/outbox.json`).

## Opening a New Task or PR

1. **Open a Task:**
   - Add a new entry to `TASK_CARDS.md` with a unique ID, description, and owner.
2. **Create a Branch:**
   - Name your branch after the task (e.g., `feat/TASK-077A-new-feature`).
3. **Make Changes:**
   - Follow code style and naming conventions (see below).
   - Add or update tests and documentation as needed.
4. **Open a Pull Request:**
   - Target the main branch.
   - Reference the task ID in the PR title and description.
   - Request review from relevant owners.
5. **Notify ARCH:**
   - Upon completion, update `TASK_CARDS.md` and notify ARCH via outbox.

## Code Style & Naming

- Use consistent naming for files and folders (see FOLDER_STRUCTURE_PLAN.md for conventions).
- Write clear, descriptive commit messages.
- Add docstrings and comments where helpful.
- Run tests and linters before submitting a PR.

---

For more details, see `/docs/`, `TASK_CARDS.md`, and `/docs/system/FOLDER_STRUCTURE_PLAN.md`. 