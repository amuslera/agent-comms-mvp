# AGENT_SCORECARD.md

## ARCH (Orchestrator)
- **Strengths:** System context, task routing, protocol enforcement, continuity
- **Recent Highlights:** Maintained one-task-per-agent discipline, clear handoffs
- **Reliability:** 9/10
- **Speed:** 7/10
- **Autonomy:** 8/10
- **Notable Issues:** Manual prompt delivery required; no auto-escalation
- **Override Rules:** May reassign tasks or pause agents for compliance

---

## CC (Core/Backend)
- **Strengths:** Merges, backend infra, schema validation, test coverage
- **Recent Highlights:** Fast merges, robust backend, reliable schema enforcement
- **Reliability:** 10/10
- **Speed:** 8/10
- **Autonomy:** 9/10
- **Notable Issues:** None significant; high trust
- **Override Rules:** Can override agent assignments for infra emergencies

---

## CA (CLI/Docs/Plans)
- **Strengths:** CLI tools, documentation, plan authoring, rapid prototyping
- **Recent Highlights:** CLI enhancements, plan templates, dry-run preview
- **Reliability:** 9/10
- **Speed:** 10/10
- **Autonomy:** 8/10
- **Notable Issues:** Needs clear scope to avoid overreach
- **Override Rules:** May request scope clarification from ARCH
- **TASK-150E Outcome:** ✅ Reassigned from WA, completed correctly within minutes. Included grouping, severity levels, help text, --json support. Score: ✅ CLI clarity, task matching, execution speed.

---

## WA (Web/UI)
- **Strengths:** UI implementation, plan compliance, user feedback
- **Recent Highlights:** UI/plan compliance under review, checklist enforcement
- **Reliability:** 7/10
- **Speed:** 7/10
- **Autonomy:** 6/10
- **Notable Issues:** Must follow WA checklist; backend/CLI changes restricted
- **Override Rules:** All UI work must be reviewed by ARCH/CC before merge
- **TASK-150E Outcome:** ✘ Task was incorrectly assigned, WA implemented unscoped DAG validation, work not merged. Score: ✘ CLI ownership and self-correction.

---

*Update this scorecard at the end of each sprint or after major agent role changes.* 