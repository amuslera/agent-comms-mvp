# Bluelabel Agent OS - Context Bundle

This directory contains all system context, protocol, and configuration files collected from across the repository for centralized review and validation.

## 📁 Bundle Contents

### 🤖 Agent Behavior & Protocols
- `AGENT_PROTOCOL.md` - Core agent communication protocol
- `AGENT_PROTOCOL_MVP.md` - MVP version of agent protocol
- `ARCH_PROTOCOL.md` - ARCH orchestrator protocol specification
- `AGENT_TASK_PROTOCOL.md` - Task-specific protocol documentation
- `exchange_protocol.json` - Machine-readable message format schema

### 👤 Agent Profiles & Context
- `ARCH_PROFILE.md` - ARCH (Orchestrator) agent profile
- `CA_PROFILE.md` - CA (Cursor AI) agent profile  
- `CC_PROFILE.md` - CC (Claude Code) agent profile
- `WA_PROFILE.md` - WA (Web Assistant) agent profile
- `ARCH_context.json` - ARCH agent persistent context
- `CA_context.json` - CA agent persistent context
- `CC_context.json` - CC agent persistent context
- `WA_context.json` - WA agent persistent context

### 📋 Task Format Templates & Examples
- `task_assignment.json` - Task assignment message template
- `task_status.json` - Task status update template
- `error.json` - Error message template
- `test_dependency_task.json` - Task dependency example
- `TASK_CARDS.md` - Complete task tracking and history

### 🔄 Workflow & Execution Plans
- `live_test_plan.yaml` - Live testing workflow example
- `retry_fallback_example.yaml` - Retry and fallback logic example
- `sample_plan.yaml` - Basic execution plan template
- `test_retry_plan.yaml` - Retry testing plan (from /plans/)
- `test_retry_plan.yaml` - Retry testing plan (from root)

### 💬 Prompt Guidelines & Templates
- `Claude_Code_PROMPT_TEMPLATE.md` - CC agent prompt template
- `Cursor_AI_PROMPT_TEMPLATE.md` - CA agent prompt template
- `Web_Assistant_PROMPT_TEMPLATE.md` - WA agent prompt template

### 🏗️ Architecture & System Overview
- `AGENT_ARCHITECTURE.md` - Detailed agent architecture documentation
- `SYSTEM_OVERVIEW.md` - Comprehensive system overview
- `EXECUTION_FLOW.md` - Complete execution flow documentation
- `context_awareness.md` - Context management documentation
- `retry_fallback_guide.md` - Retry and fallback mechanisms guide

### 🌐 Internal Routing & Communication
- `router.py` - Core message routing implementation
- `router_log.md` - Router execution logging format

### ⚙️ Configuration & Context Files
- `CONTEXT_agent_comms.md` - Shared system context documentation
- `agent_learning_snapshot.json` - Learning system state (root)
- `agent_learning_snapshot_insights.json` - Learning system state (insights)

### 📚 Main Documentation
- `README.md` - Primary project documentation
- `CHANGELOG.md` - Project change history

## 🎯 Purpose

This bundle serves several key purposes:

1. **Centralized Review** - All system-defining files in one location
2. **Version Control** - Track changes to critical system components
3. **Validation** - Ensure consistency across all protocol and context definitions
4. **Integration Testing** - Verify all components work together coherently
5. **Documentation Audit** - Review completeness and accuracy of system documentation

## 📋 Collection Criteria

Files were selected based on the following criteria:
- Define agent behavior or protocols
- Specify task formats or assignment rules  
- Document workflow schemas or message formats
- Contain prompt guidelines or shared components
- Define execution or logging conventions
- Specify internal routing rules
- Provide architecture summaries
- Document communication or merge policies

## 🔍 Next Steps

1. **ARCH Review** - ARCH agent will review all files for consistency
2. **Validation** - Check for conflicts or inconsistencies between files
3. **Integration** - Ensure all components work together as intended
4. **Updates** - Apply any necessary corrections or improvements
5. **Versioning** - Tag and version the validated context bundle

## 📅 Created

Generated on: 2025-05-21 by TASK-065  
Last Updated: 2025-05-21  
Total Files: 32  
Bundle Version: 1.0.0