# ARCH_CONTINUITY.md

## Current Sprint Phase
- **Phase:** 6.10 (Sprint 10)
- **Status:** In Progress

## Last Completed Tasks
- TASK-150H: YAML Plan Dry-Run Execution Preview (CA)
- TASK-150G: YAML Plan Template Generator (CA)
- TASK-150F-B: WA Checklist Enforcement in Planning (CC)
- TASK-150P: Postmortem Integration for Phase 6.9 (CA)

## Pending Tasks
- TASK-150J: ARCH Continuity & Agent Scorecard Infrastructure (CA, current)
- TASK-151A: Next sprint planning (pending)

## Known Agent Behavior
- **WA:** Under review for UI/plan compliance; must follow WA checklist; no backend/CLI changes
- **CC:** Handles merges, backend infra, schema validation; high reliability
- **CA:** CLI, docs, plans; fast, versatile, needs structured scope
- **ARCH:** Orchestrates, assigns one task per agent, enforces branch discipline, manual prompt delivery

## ARCH Preferences
- One-task-per-agent policy
- Manual prompt delivery (no auto-escalation)
- No early merges; all work reviewed before merge
- Strict branch discipline (no direct commits to main/dev)
- Explicit agent-task mapping and reporting
- Use of /TASK_CARDS.md and /postbox/ for state

## Current Agent-Task Map
| Agent | Current Task(s)                | Notes                                 |
|-------|--------------------------------|---------------------------------------|
| ARCH  | Orchestration, review, routing | One-task-per-agent, manual delivery   |
| CC    | Merge, backend, infra          | Handles merges, schema, infra         |
| CA    | CLI, docs, plan tools          | Fast, versatile, needs clear scope    |
| WA    | UI, plan compliance            | Under review, checklist enforcement   |

---

*This file should be updated at the start and end of each sprint, and whenever ARCH is reassigned or agent roles change.* 