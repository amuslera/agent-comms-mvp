# Context Files Refactoring Recommendations

## Summary Table

| File | Current Status | Recommendation | New Location/Name | Notes |
|------|---------------|----------------|-------------------|-------|
| AGENT_PROTOCOL_MVP.md | MVP version | Merge into AGENT_PROTOCOL.md | /docs/protocols/AGENT_PROTOCOL.md | Keep MVP content as historical reference section |
| AGENT_PROTOCOL.md | Current version | Keep and enhance | /docs/protocols/AGENT_PROTOCOL.md | Add MVP section and update references |
| Claude_Code_PROMPT_TEMPLATE.md | Agent prompt | Move to new structure | /docs/prompts/CC_PROMPT.md | Consolidate with other agent prompts |
| Cursor_AI_PROMPT_TEMPLATE.md | Agent prompt | Move to new structure | /docs/prompts/CA_PROMPT.md | Consolidate with other agent prompts |
| Web_Assistant_PROMPT_TEMPLATE.md | Agent prompt | Move to new structure | /docs/prompts/WA_PROMPT.md | Consolidate with other agent prompts |
| router.py | Implementation | Keep | /tools/router/router.py | No changes needed |
| router_log.md | Log file | Move to logs | /logs/router/router_log.md | Standardize log location |
| retry_fallback_guide.md | Documentation | Merge with example | /docs/features/retry_fallback.md | Combine guide and example |
| retry_fallback_example.yaml | Example | Merge with guide | /docs/features/retry_fallback.md | Include as code block |
| exchange_protocol.json | Schema | Move to schemas | /schemas/exchange_protocol.json | Standardize schema location |
| task_status.json | Schema | Move to schemas | /schemas/task_status.json | Standardize schema location |

## Implementation Plan

### 1. Protocol Documentation
- Create `/docs/protocols/` directory
- Merge AGENT_PROTOCOL_MVP.md into AGENT_PROTOCOL.md
- Update all references in other files
- Add version history section

### 2. Prompt Templates
- Create `/docs/prompts/` directory
- Move and rename prompt templates
- Update references in agent profiles
- Add template version tracking

### 3. Logs and Schemas
- Create `/logs/` directory for all log files
- Create `/schemas/` directory for JSON schemas
- Move files to new locations
- Update references in code

### 4. Feature Documentation
- Create `/docs/features/` directory
- Merge retry/fallback documentation
- Add implementation examples
- Update references

## Benefits
1. Clearer documentation structure
2. Better version tracking
3. Standardized file locations
4. Reduced redundancy
5. Improved maintainability

## Next Steps
1. Create new directory structure
2. Move files to new locations
3. Update references in code
4. Update documentation
5. Verify all links work 