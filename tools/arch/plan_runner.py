import sys
import time
import json
import uuid
from pathlib import Path
from typing import Any, Dict, Set
from tools.arch import plan_utils
from tools.arch.plan_utils import ExecutionDAG, TaskNode, ExecutionTracer, PlanContextEngine, evaluate_conditions, log_conditional_skip
from tools.arch.wa_checklist_enforcer import enforce_wa_checklist_on_message, create_wa_validation_hook

import yaml
from jsonschema import validate, ValidationError

# Configurable constants
PLAN_SCHEMA_PATH = Path('schemas/PLAN_SCHEMA.json')
MCP_SCHEMA_PATH = Path('schemas/MCP_MESSAGE_SCHEMA.json')
POSTBOX_ROOT = Path('postbox')
LOGS_TASKS_DIR = Path('logs/tasks')
LOGS_TRACES_DIR = Path('logs/traces')
PHASE_POLICY_PATH = Path('phase_policy.yaml')
RESPONSE_TIMEOUT = 60  # seconds
RETRY_DELAY = 5        # seconds

# Load phase policy for retry logic
def get_retry_limit() -> int:
    try:
        with open(PHASE_POLICY_PATH) as f:
            policy = yaml.safe_load(f)
        return policy.get('policies', {}).get('retry', {}).get('max_attempts', 3)
    except Exception:
        return 3

# Wait for a response in the agent's outbox for a given trace_id
def wait_for_response(agent: str, trace_id: str, timeout: int = RESPONSE_TIMEOUT) -> Dict[str, Any]:
    outbox_path = POSTBOX_ROOT / agent / 'outbox.json'
    start = time.time()
    while time.time() - start < timeout:
        if outbox_path.exists():
            with open(outbox_path) as f:
                try:
                    messages = json.load(f)
                except Exception:
                    messages = []
            for msg in messages:
                if msg.get('trace_id') == trace_id:
                    return msg
        time.sleep(2)
    raise TimeoutError(f"No response for trace_id {trace_id} from agent {agent} within {timeout}s")

# Construct MCP message for a task
def build_mcp_message(task_node: TaskNode, trace_id: str, plan_id: str, retry_count: int = 0) -> Dict[str, Any]:
    with open(MCP_SCHEMA_PATH) as f:
        mcp_schema = json.load(f)
    now = plan_utils.now_iso()
    
    message = {
        "type": "task_result",
        "protocol_version": "1.3",
        "sender_id": "ARCH",
        "recipient_id": task_node.agent,
        "trace_id": trace_id,
        "retry_count": retry_count,
        "task_id": task_node.task_id,
        "payload": {
            "type": "task_assignment",
            "content": {
                "task_id": task_node.task_id,
                "description": task_node.description,
                "action": task_node.content.get("action"),
                "parameters": task_node.content.get("parameters", {}),
                "requirements": task_node.content.get("requirements", []),
                "input_files": task_node.content.get("input_files", []),
                "output_files": task_node.content.get("output_files", []),
                "priority": task_node.priority,
                "dependencies": task_node.dependencies,
                "deadline": task_node.metadata.get("deadline"),
                "timeout": task_node.metadata.get("timeout"),
                "conditions": task_node.metadata.get("conditions")
            }
        },
        "timestamp": now
    }
    
    try:
        validate(instance=message, schema=mcp_schema)
    except ValidationError as e:
        raise ValueError(f"MCP message validation failed: {e.message}")
    
    # Apply WA checklist enforcement if this is a WA task
    if task_node.agent == "WA":
        message = enforce_wa_checklist_on_message(message)
        # Create validation hook for later compliance review
        validation_data = {
            "task_id": task_node.task_id,
            "description": task_node.description,
            "trace_id": trace_id,
            "plan_id": plan_id
        }
        create_wa_validation_hook(task_node.task_id, validation_data)
    
    return message

def execute_task_with_dag_logging(task_node: TaskNode, dag: ExecutionDAG, tracer: ExecutionTracer, 
                                  plan_id: str, task_index: int, execution_layer: int, 
                                  parallel_tasks: list, depth: int, plan_context: PlanContextEngine = None) -> bool:
    """Execute a single task with enhanced DAG-aware logging."""
    
    trace_id = plan_utils.generate_trace_id(plan_id, task_index)
    retry_limit = get_retry_limit()
    
    # Create enhanced task log
    task_log = plan_utils.create_enhanced_task_log(
        trace_id, plan_id, task_node, execution_layer, parallel_tasks, depth
    )
    
    # Write initial task log
    LOGS_TASKS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOGS_TASKS_DIR / f"{trace_id}.json"
    with open(log_path, 'w') as f:
        json.dump(task_log, f, indent=2)
    
    # Log task creation event
    tracer.log_event("task_created", task_node.task_id, task_node.agent, 
                     execution_layer, {"trace_id": trace_id}, trace_id)
    
    # Update state to ready
    plan_utils.update_task_log_state(trace_id, LOGS_TASKS_DIR, "waiting", "ready", 
                                     "All dependencies satisfied")
    tracer.log_event("task_ready", task_node.task_id, task_node.agent, execution_layer)
    
    # Evaluate conditional execution (when/unless)
    if plan_context:
        # Create task dict from TaskNode for evaluation
        # Support both direct metadata fields and nested conditions object
        when_condition = task_node.metadata.get('when') or task_node.metadata.get('conditions', {}).get('when')
        unless_condition = task_node.metadata.get('unless') or task_node.metadata.get('conditions', {}).get('unless')
        
        task_dict = {
            'task_id': task_node.task_id,
            'when': when_condition,
            'unless': unless_condition
        }
        
        should_execute, condition_reason = evaluate_conditions(task_dict, plan_context)
        
        if not should_execute:
            print(f"[INFO] Skipping task {task_node.task_id}: {condition_reason}")
            
            # Log conditional skip
            log_conditional_skip(trace_id, LOGS_TASKS_DIR, task_node.task_id, condition_reason)
            tracer.log_event("task_skipped_condition", task_node.task_id, task_node.agent, 
                           execution_layer, {"reason": condition_reason}, trace_id)
            
            return True  # Return True as this is a successful skip, not a failure
        else:
            print(f"[INFO] Task {task_node.task_id} passed conditional evaluation: {condition_reason}")
            tracer.log_event("task_condition_passed", task_node.task_id, task_node.agent,
                           execution_layer, {"reason": condition_reason}, trace_id)
    
    # Execute task with retries
    attempt = 0
    result = None
    task_start_time = time.time()
    
    while attempt < retry_limit:
        # Update state to running
        plan_utils.update_task_log_state(trace_id, LOGS_TASKS_DIR, "ready" if attempt == 0 else "retrying", 
                                         "running", f"Starting attempt {attempt + 1}", attempt)
        
        if attempt == 0:
            tracer.log_event("task_started", task_node.task_id, task_node.agent, execution_layer)
        else:
            tracer.log_event("task_retry", task_node.task_id, task_node.agent, execution_layer, 
                           {"attempt": attempt + 1})
        
        # Build and send MCP message
        mcp_msg = build_mcp_message(task_node, trace_id, plan_id, attempt)
        plan_utils.write_to_inbox(task_node.agent, mcp_msg, POSTBOX_ROOT)
        
        print(f"[INFO] Sent task {task_node.task_id} to {task_node.agent} "
              f"(layer {execution_layer}, attempt {attempt+1}/{retry_limit})")
        
        try:
            response = wait_for_response(task_node.agent, trace_id)
            result = response
            
            # Calculate duration
            duration = time.time() - task_start_time
            
            # Update task log with result
            plan_utils.update_task_log_result(trace_id, LOGS_TASKS_DIR, result, duration)
            
            # Update state to completed
            plan_utils.update_task_log_state(trace_id, LOGS_TASKS_DIR, "running", "completed", 
                                             "Task executed successfully")
            
            tracer.log_event("task_completed", task_node.task_id, task_node.agent, execution_layer,
                           {"duration_sec": duration, "score": result.get('payload', {}).get('content', {}).get('score')})
            
            # Update plan context with task result
            if plan_context:
                plan_context.update_from_task_result(task_node.task_id, result)
                print(f"[INFO] Updated plan context from task {task_node.task_id}")
            
            print(f"[INFO] Task {task_node.task_id} completed successfully (layer {execution_layer})")
            return True
            
        except TimeoutError as e:
            duration = time.time() - task_start_time
            print(f"[WARN] Task {task_node.task_id} timeout: {e}")
            
            # Add retry to log
            plan_utils.add_retry_to_task_log(trace_id, LOGS_TASKS_DIR, attempt + 1, "timeout", 
                                             str(e), duration)
            
            attempt += 1
            if attempt < retry_limit:
                plan_utils.update_task_log_state(trace_id, LOGS_TASKS_DIR, "running", "retrying", 
                                                 f"Timeout, retrying (attempt {attempt + 1})")
                time.sleep(RETRY_DELAY)
            else:
                plan_utils.update_task_log_state(trace_id, LOGS_TASKS_DIR, "running", "timeout", 
                                                 "Max retries exceeded")
                tracer.log_event("task_timeout", task_node.task_id, task_node.agent, execution_layer)
    
    print(f"[ERROR] Task {task_node.task_id} failed after {retry_limit} attempts")
    return False

def run_plan(plan_path: Path) -> bool:
    """
    Enhanced plan runner with DAG awareness and comprehensive logging.
    
    Returns:
        bool: True if all tasks completed successfully, False otherwise
    """
    print(f"[INFO] Starting DAG-aware plan execution: {plan_path}")
    
    # Load and validate plan
    plan_dict = plan_utils.load_and_validate_plan(plan_path, PLAN_SCHEMA_PATH)
    plan_id = plan_dict.get('metadata', {}).get('plan_id', plan_path.stem)
    
    # Build execution DAG
    dag = plan_utils.build_execution_dag(plan_dict)
    print(f"[INFO] Built execution DAG: {len(dag.nodes)} tasks, {len(dag.get_execution_layers())} layers")
    
    # Initialize execution tracer
    tracer = ExecutionTracer(plan_dict, dag, LOGS_TRACES_DIR)
    tracer.log_event("plan_started", details={"plan_path": str(plan_path)})
    
    # Initialize plan context engine
    initial_context = plan_dict.get('context', {})
    plan_context = PlanContextEngine(initial_context)
    print(f"[INFO] Plan context initialized with: {list(plan_context.context.keys())}")
    
    # Get execution layers for parallel processing
    execution_layers = dag.get_execution_layers()
    completed_tasks = set()
    all_success = True
    
    print(f"[INFO] Execution plan:")
    for i, layer in enumerate(execution_layers):
        print(f"  Layer {i}: {layer}")
    
    # Execute tasks layer by layer
    for layer_index, layer_tasks in enumerate(execution_layers):
        print(f"\n[INFO] Starting execution layer {layer_index} with {len(layer_tasks)} tasks")
        tracer.log_event("layer_started", details={"layer": layer_index, "tasks": layer_tasks})
        
        layer_success = True
        
        # For this MVP, we'll execute tasks in the layer sequentially
        # In a full implementation, you'd want to execute them in parallel
        for task_id in layer_tasks:
            task_node = dag.nodes[task_id]
            
            # Find task index for trace_id generation
            task_index = list(dag.nodes.keys()).index(task_id)
            
            # Get parallel tasks in this layer
            parallel_tasks = [t for t in layer_tasks if t != task_id]
            
            # Calculate depth for this task
            depth = layer_index
            
            # Execute the task
            success = execute_task_with_dag_logging(
                task_node, dag, tracer, plan_id, task_index, 
                layer_index, parallel_tasks, depth, plan_context
            )
            
            if success:
                completed_tasks.add(task_id)
            else:
                layer_success = False
                all_success = False
                
                # Check if we should continue or fail fast
                # For now, we'll continue with other tasks
                continue
        
        if layer_success:
            print(f"[INFO] Layer {layer_index} completed successfully")
            tracer.log_event("layer_completed", details={"layer": layer_index, "success": True})
        else:
            print(f"[WARN] Layer {layer_index} completed with failures")
            tracer.log_event("layer_completed", details={"layer": layer_index, "success": False})
    
    # Finalize execution
    final_status = "success" if all_success else "partial_success" if completed_tasks else "failure"
    tracer.finalize_trace(final_status)
    
    # Save plan context evaluation log
    if plan_context and plan_context.evaluation_log:
        context_log_path = LOGS_TRACES_DIR / f"context_evaluation_{tracer.get_execution_id()}.json"
        LOGS_TRACES_DIR.mkdir(parents=True, exist_ok=True)
        
        context_log = {
            "execution_id": tracer.get_execution_id(),
            "plan_id": plan_id,
            "final_context": plan_context.context,
            "evaluation_log": plan_context.evaluation_log,
            "timestamp": plan_utils.now_iso()
        }
        
        with open(context_log_path, 'w') as f:
            json.dump(context_log, f, indent=2)
        
        print(f"[INFO] Context evaluation log saved: {context_log_path}")
    
    print(f"\n[INFO] Plan execution completed: {final_status}")
    print(f"[INFO] Tasks completed: {len(completed_tasks)}/{len(dag.nodes)}")
    print(f"[INFO] Execution trace: {tracer.get_execution_id()}")
    
    return all_success

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python plan_runner.py <plan_path>")
        print("Example: python plan_runner.py plans/sample-plan-001.yaml")
        sys.exit(1)
    
    success = run_plan(Path(sys.argv[1]))
    sys.exit(0 if success else 1)