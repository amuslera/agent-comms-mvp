# ARCH Orchestration Protocol

## 1. 🔧 Purpose and Responsibilities

### Purpose
ARCH (Architecture Orchestrator) is the central orchestration agent responsible for coordinating multi-agent workflows within the Bluelabel AIOS project. It manages task execution, agent coordination, and system-wide process flow.

### Core Responsibilities
- Load and parse execution plans (YAML format)
- Dispatch tasks to appropriate agent inboxes
- Trigger agent runners for task processing
- Monitor agent outboxes for responses
- Handle errors, retries, and escalations
- Ensure task completion and report status
- Manage cross-agent dependencies
- Maintain system-wide execution logs

### Permissions
ARCH is authorized to:
- Read/write to all agent postboxes (`/postbox/{agent}/`)
- Execute `agent_runner.py` for any agent
- Access task logs and system state
- Route messages between agents
- Create recovery plans for failed tasks
- Escalate critical issues to human operators

### Boundaries
ARCH must NOT:
- Modify agent core logic or prompts
- Execute code outside of agent runners
- Access system resources beyond the project scope
- Override agent-specific security policies

## 2. 🧭 Execution Flow

### Plan Loading
1. Read YAML plan from designated location (`/plans/`)
2. Validate plan structure and syntax
3. Parse task definitions, dependencies, and metadata
4. Create execution graph respecting dependencies
5. Initialize tracking structures for task state

### Task Dispatch
1. Select ready tasks (dependencies satisfied)
2. Create task messages following exchange protocol:
   ```json
   {
     "message_id": "unique-uuid",
     "type": "task",
     "sender": "ARCH",
     "recipient": "target-agent",
     "timestamp": "ISO-8601",
     "task": {
       "task_id": "TASK-XXX",
       "action": "specific-action",
       "payload": { ... }
     }
   }
   ```
3. Write message to `/postbox/{agent}/inbox.json`
4. Trigger agent runner: `python agent_runner.py {agent}`
5. Log dispatch event to `/postbox/ARCH/task_log.md`

### Monitoring & Response Collection
1. Poll agent outboxes periodically (configurable interval)
2. Read messages from `/postbox/{agent}/outbox.json`
3. Process based on message type:
   - `task_status`: Update task tracking
   - `task_result`: Collect outputs
   - `error`: Trigger error handling
   - `request`: Route to appropriate agent
4. Clear processed messages from outbox
5. Update execution state and logs

### Progress Tracking
- Maintain task states: `pending`, `dispatched`, `processing`, `completed`, `failed`
- Track timing: dispatch time, start time, completion time
- Monitor resource usage and agent availability
- Update dashboard/status for visibility

## 3. ⚠️ Escalation & Error Handling

### Retry Strategy
1. **Immediate Retry** (for transient failures):
   - Network timeouts
   - Temporary file access issues
   - Agent busy states
   - Max attempts: 3, backoff: exponential

2. **Delayed Retry** (for resource issues):
   - Memory constraints
   - Processing capacity
   - External dependencies
   - Max attempts: 5, backoff: linear (5-minute intervals)

### Rerouting (Fallback)
When primary agent fails repeatedly:
1. Check fallback mapping in plan metadata
2. Attempt alternate agent if specified
3. Simplify task parameters if possible
4. Route to manual queue if no fallback exists

### Escalation to Human
Trigger escalation when:
- Task fails all retry attempts
- Critical path task blocks execution
- Security or permission issues detected
- Unhandled exception in core system
- Data corruption or inconsistency found

Escalation format:
```markdown
## ESCALATION: {task_id}
- Agent: {agent_name}
- Error: {error_type}
- Details: {error_message}
- Attempts: {retry_count}
- Impact: {affected_tasks}
- Recommended Action: {suggestion}
```

## 4. ✅ Completion Conditions

### Task Success
A task is considered successfully completed when:
- Agent returns `status: "completed"` message
- All required outputs are present
- Validation rules pass (if defined)
- No active error flags

### Partial Success
Handle partial completions:
- Mark primary objective complete
- Log incomplete secondary objectives
- Allow dependent tasks if minimum criteria met
- Generate warning for incomplete aspects

### Task Failure
A task definitively fails when:
- All retry attempts exhausted
- Agent returns unrecoverable error
- Timeout exceeded (configurable per task)
- Required resources unavailable
- Security violation detected

### Timeout Handling
- Default timeout: 30 minutes per task
- Extended timeout for specified heavy tasks
- Warning at 80% of timeout
- Grace period for cleanup: 5 minutes
- Force termination after grace period

## 5. 🧪 Future Extensibility

### Input Sources (Planned)
- **Webhook Integration**: REST API for external triggers
- **Slack Bot**: Natural language task requests
- **Voice Interface**: Audio command processing
- **Email Gateway**: Task submission via email
- **Git Hooks**: Automatic deployment tasks

### Execution Modes
1. **Batch Execution**: Current mode, plan-based
2. **Continuous Mode**: Always-on, event-driven
3. **Scheduled Mode**: Cron-based triggers
4. **Interactive Mode**: Step-by-step with approvals
5. **Parallel Mode**: Multi-plan concurrent execution

### Security Enhancements
- **Authentication**: Agent identity verification
- **Authorization**: Role-based task permissions
- **Encryption**: Secure message transport
- **Audit Trail**: Comprehensive activity logging
- **Sandboxing**: Isolated execution environments

### Performance Optimization
- **Load Balancing**: Distribute tasks across agents
- **Caching**: Store frequent query results
- **Compression**: Optimize large payloads
- **Streaming**: Handle real-time data flows
- **Clustering**: Multi-instance ARCH support

### Integration Points
- **Monitoring**: Prometheus/Grafana metrics
- **Logging**: ELK stack integration
- **Tracing**: Distributed trace support
- **Service Mesh**: Kubernetes-native operation
- **Message Queue**: Kafka/RabbitMQ bridge

## Protocol Versioning
- Current Version: 1.0.0
- Compatibility: Backward compatible within major version
- Migration Path: Automated upgrade scripts provided
- Deprecation Policy: 6-month notice for breaking changes

## Configuration
Default configuration location: `/config/arch_config.yaml`
```yaml
orchestrator:
  poll_interval: 5s
  default_timeout: 30m
  max_retries: 3
  backoff_multiplier: 2
  
agents:
  health_check_interval: 60s
  max_concurrent_tasks: 10
  
logging:
  level: info
  retention: 30d
  max_size: 100MB
```

---
This protocol serves as the definitive guide for ARCH orchestration behavior and will be used by Cursor AI (CA) to implement `arch_orchestrator.py`.