# Folder Structure Audit & Naming Proposal

## Current Top-Level Folders

- `/apps/`      — Application code (API backend, web frontend)
- `/tools/`     — CLI tools, agent runners, routers, utilities
- `/docs/`      — Documentation (system, protocols, features)
- `/schemas/`   — JSON/YAML schemas and examples
- `/postbox/`   — Agent inboxes/outboxes for message passing
- `/contexts/`  — Agent context and profile files
- `/features/`  — Feature-specific modules (if present)

## Observed Naming Inconsistencies

- Some folders use plural (`/apps/`, `/tools/`, `/schemas/`, `/contexts/`), others are singular or mixed.
- Some subfolders and files use camelCase (e.g., `PlanDAGViewer.tsx`), others use snake_case or kebab-case.
- Occasional use of uppercase (e.g., `ARCH`, `HUMAN` in `/postbox/`).
- Some directories (e.g., `/features/`) are not always present or consistently used.

## Proposed Naming Convention

- **Folders:** Use all lowercase with hyphens (kebab-case) for all directories (e.g., `agent-profiles`, `test-data`).
- **Files:**
  - Python: `snake_case.py`
  - JavaScript/TypeScript: `camelCase.tsx` for components, `snake_case.ts` for utilities
  - JSON/YAML: `snake_case.json`, `kebab-case.yaml`
- **Agent/Role Folders:** Keep uppercase for agent IDs in `/postbox/` for clarity (e.g., `/postbox/ARCH/`).
- **Pluralization:** Use plural for folders containing multiple items (e.g., `/apps/`, `/tools/`, `/schemas/`).

## Migration Suggestions

- Audit all folders and files for naming consistency.
- Plan a migration to rename folders/files to match the above conventions.
- Update all import paths and references after renaming.
- Communicate changes to all contributors before migration.

## Example Structure (Proposed)

```
/apps/
  web/
  api/
/tools/
/docs/
/schemas/
/postbox/
/contexts/
/features/
```

- All subfolders and files should follow the kebab-case or snake_case convention as appropriate.

---

**Note:** This is a proposal. No renaming has been performed yet. Please review and discuss before migration. 