# AGENT_ORCHESTRATION_GUIDE.md

## 🎯 Purpose

This guide defines how to consistently assign and manage tasks across agents in the Bluelabel Agent OS. It standardizes prompt structure, branch discipline, deliverable expectations, and reporting. It also includes a continuation guide if the orchestrator (ARCH) role is reassigned.

---

## 🧱 1. Agent Prompt Structure Guidelines

Every task assignment must include:

- ✅ Task ID and clearly named branch (e.g., `core/feature-TASK-123X`)
- ✅ Exact file paths or directories the agent may modify
- ✅ CLI command or subsystem to test (if relevant)
- ✅ List of required deliverables
- ✅ Explicit instruction to start report with `XX Reports:`

---

## 🪴 2. Branch Setup Protocol

Before any agent starts work, the following command must be included in the prompt:

```bash
git checkout -b <task-specific-branch>
```

No agent should commit work directly to `main`, `dev`, or another system branch.

---

## 📸 3. Agent-Specific Requirements

| Agent | Notes |
|-------|-------|
| **WA** | Must follow `/WA_CHECKLIST.md`. Required: branch name, screenshot, path restrictions, task report. No CLI or backend files. |
| **CA** | Best for CLI tools, docs, plans. Fast and versatile. Needs structured scope. |
| **CC** | Owns core logic, backend infra, merges, and schema validation. High reliability. Prefer for testable infra. |

---

## 📝 4. Agent Report Format Standard

All agent reports must begin with:

```
XX Reports: TASK-XXXX Completed

✅ Summary of actions
📁 Files modified
🧪 What was tested
⚠️ Edge cases or known limitations
📦 Confirmed updates to /TASK_CARDS.md and outbox
```

This format ensures easy copy-paste and re-ingestion into ARCH.

---

## 🔁 5. Continuation Instructions for ARCH

If orchestration is ever reassigned:

- Maintain strict one-task-per-agent policy
- Use `/TASK_CARDS.md`, `/SPRINT_HISTORY.md`, and `/postbox/` to maintain state
- Ensure branch discipline and enforce per-agent scope
- Use `/WA_CHECKLIST.md` and this guide to onboard new agents quickly
- Carry forward unresolved issues from each phase's postmortem

---

## 🗂️ System Metadata

See also:
- [ARCH_CONTINUITY.md](./ARCH_CONTINUITY.md): Current phase, agent-task map, ARCH preferences
- [AGENT_SCORECARD.md](./AGENT_SCORECARD.md): Agent strengths, reliability, autonomy, and issues
- [ARCH_AI_CONTEXT.md](./ARCH_AI_CONTEXT.md): ARCH-AI role, responsibilities, and operating protocol

---

Keep this file updated as processes evolve.
