# Bluelabel Agent OS: Refined Architecture & Execution Plan

## 📖 Overview

This document outlines the updated architecture and execution plan for Bluelabel Agent OS, focusing on achieving fully autonomous execution and scalable multi-agent collaboration. This revision builds upon our existing system while introducing new patterns for improved reliability and scalability.

> **Cross-Reference**: This document extends the [System Overview](./SYSTEM_OVERVIEW.md) with updated architectural decisions.

## 🎯 Vision: Fully Autonomous Execution

Bluelabel Agent OS is evolving into a self-sustaining system where AI agents can:

1. **Self-Organize** into dynamic teams based on task requirements
2. **Self-Optimize** their execution strategies using real-time feedback
3. **Self-Heal** through automated recovery and retry mechanisms
4. **Self-Improve** by learning from past executions and outcomes

## 🏗️ Key Components

### 1. CTO Agent (Chief Technology Officer)
- **Role**: System orchestrator and decision-maker
- **Responsibilities**:
  - High-level task planning and decomposition
  - Resource allocation and team formation
  - Performance monitoring and optimization
  - Strategic decision making and course correction

### 2. Agent Teams
- **Specialized Roles**:
  - **Architects**: System design and architecture
  - **Developers**: Implementation and coding
  - **QA Engineers**: Testing and validation
  - **Security Experts**: Security and compliance
  - **DevOps**: Deployment and operations

### 3. Postbox System
- **Purpose**: Asynchronous message bus for inter-agent communication
- **Features**:
  - Persistent message storage
  - Priority-based message queuing
  - Message versioning and conflict resolution
  - End-to-end encryption

### 4. Execution Engine
- **Core Functions**:
  - Task scheduling and prioritization
  - Resource management
  - Dependency resolution
  - Parallel execution coordination
  - State management and checkpointing

## 📨 Messaging & Retry Strategy (MCP-Compatible)

### Message Format
```yaml
message:
  id: uuid
  type: task|status|result|error
  sender: agent_id
  recipients: [agent_id]
  timestamp: iso8601
  payload:
    task_id: string
    content: any
    metadata:
      priority: 0-100
      ttl: seconds
      retry_count: number
      dependencies: [task_id]
```

### Retry Strategy
1. **Immediate Retry** (0-1s): For transient network issues
2. **Backoff Retry** (1s-1m): For temporary resource constraints
3. **Exponential Backoff** (1m-1h): For longer-term issues
4. **Human Intervention** (1h+): For critical failures requiring attention

## 🔄 Task Lifecycle

1. **Plan**
   - Task definition and requirements gathering
   - Dependency resolution
   - Resource estimation

2. **Assignment**
   - Agent team formation
   - Role assignment
   - Task distribution

3. **Execution**
   - Parallel task processing
   - Progress monitoring
   - Intermediate validation

4. **Review**
   - Code review and quality checks
   - Security scanning
   - Performance validation

5. **Merge**
   - Conflict resolution
   - Version control integration
   - Build and test

6. **Report**
   - Execution summary
   - Performance metrics
   - Lessons learned
   - Improvement suggestions

## ⚙️ Phase Autonomy Logic (`phase_policy.yaml`)

```yaml
version: 1.0
phases:
  - name: Planning
    max_duration: 1h
    required_approvals: 1
    fallback_strategy: retry_escalate
    
  - name: Development
    max_duration: 4h
    required_approvals: 2
    fallback_strategy: retry_rotate
    
  - name: Review
    max_duration: 2h
    required_approvals: 3
    fallback_strategy: escalate
    
  - name: Deployment
    max_duration: 1h
    required_approvals: 2
    fallback_strategy: rollback

policies:
  retry:
    max_attempts: 3
    backoff_factor: 2
    max_backoff: 3600  # 1 hour
  
  security:
    require_2fa: true
    audit_logging: true
    
  monitoring:
    metrics_interval: 60s
    health_check_interval: 30s
```

## 🚀 Scalability Strategies

### Horizontal Scaling
- Stateless agent design
- Distributed task queues
- Sharded message storage
- Load-balanced API gateways

### Vertical Scaling
- Resource monitoring and auto-scaling
- Memory optimization
- CPU affinity and isolation

## 🔒 Security Model

1. **Authentication**: OAuth 2.0 with JWT
2. **Authorization**: Role-based access control (RBAC)
3. **Encryption**: End-to-end encryption for all messages
4. **Audit**: Immutable audit logs
5. **Compliance**: SOC 2, GDPR, HIPAA ready

## 👁️ Observability Stack

### Logging
- Structured JSON logging
- Distributed tracing
- Log aggregation and analysis

### Metrics
- Prometheus for time-series data
- Custom business metrics
- Resource utilization

### Tracing
- Distributed request tracing
- Performance profiling
- Dependency mapping

## 🌐 External Ecosystem Integration

### MCP (Multi-Cloud Platform)
- Unified API for cloud providers
- Resource provisioning
- Cost optimization

### A2A (Agent-to-Agent)
- Standardized communication protocol
- Service discovery
- Capability negotiation

### ADK (Agent Development Kit)
- Agent templates
- Testing framework
- Performance profiling tools

### LangGraph
- Language model integration
- Prompt engineering
- Response validation

## 🗺️ Roadmap: Phase 6 to Production

### Phase 6: Enhanced Autonomy (Current)
- [ ] Implement CTO agent
- [ ] Deploy postbox system
- [ ] Basic team formation logic

### Phase 7: Scaling & Optimization
- [ ] Horizontal scaling
- [ ] Advanced scheduling
- [ ] Resource optimization

### Phase 8: Advanced Features
- [ ] Self-healing mechanisms
- [ ] Predictive scaling
- [ ] Automated testing

### Phase 9: Production Readiness
- [ ] Security audit
- [ ] Performance testing
- [ ] Documentation

### Phase 10: GA Release
- [ ] Public beta
- [ ] Customer onboarding
- [ ] Support system

## 📚 References

1. [System Overview](./SYSTEM_OVERVIEW.md)
2. [Agent Architecture](./AGENT_ARCHITECTURE.md)
3. [Execution Flow](./EXECUTION_FLOW.md)

## 📅 Changelog

- **2025-05-21**: Initial version

## Phase 6.1: MCP Envelope Parsing
- All agent messages are now validated and parsed using the MCP-compatible envelope schema.
- Required fields: sender_id, recipient_id, trace_id, retry_count, task_id, payload
- Payload includes type, content, and optional evaluation fields (success, score, duration_sec, notes)

## Retry Logic and Policy-Based Escalation
- ARCH agent enforces retry logic for error messages based on phase_policy.yaml
- Retries are tracked per message (using retry_count in the envelope)
- Escalation to human or fallback agent occurs when retry limits are exceeded
- Policy-based escalation rules are configurable per error type

## Output-Aware Routing
- Routing decisions can now incorporate evaluation results (success, score, etc.)
- Output evaluation fields are extracted from MCP messages and logged for future routing/learning

## ARCH Log Tracking for Evaluation Results
- All output evaluation fields (success, score, duration, notes) are logged per agent/task in logs/agent_scores.json
- Rolling summaries and per-agent statistics are available for monitoring and learning

## Backend Metrics API Endpoints
- FastAPI backend exposes /metrics/agents and /metrics/plans/{plan_id} endpoints
- Endpoints return agent and plan performance metrics (average score, success rate, task count, last activity, etc.)
- Metrics are computed from logs/agent_scores.json

## Alert System

The ARCH agent system includes a flexible alert system for monitoring task execution and system health. The alert system is implemented through the following components:

### Alert Policy

Alert policies are defined in YAML format and specify rules for triggering alerts based on message content and task results. Each policy includes:

- Version and description
- List of alert rules
- Conditions for triggering alerts
- Actions to take when alerts are triggered

Example alert conditions:
- Error codes and retry counts
- Task result scores and durations
- Agent-specific performance metrics
- System health indicators

### Alert Evaluator

The alert evaluator (`AlertEvaluator`) is responsible for:

1. Loading and validating alert policies
2. Evaluating incoming messages against alert rules
3. Triggering appropriate actions when conditions are met
4. Logging alert events for monitoring and analysis

The evaluator supports two types of notifications:
- Human notifications via console logging
- Webhook notifications to external systems

### Integration with Message Router

The alert evaluator is integrated into the message router, allowing for real-time evaluation of messages as they flow through the system. This integration enables:

- Immediate detection of issues
- Proactive alerting for potential problems
- Automated responses to system events
- Comprehensive monitoring of agent performance

### Alert Logging

All triggered alerts are logged to a dedicated alert log file, providing:
- Historical record of system events
- Audit trail for debugging
- Performance metrics for analysis
- Input for system health monitoring
