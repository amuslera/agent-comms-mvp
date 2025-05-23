import sys
import time
import json
import uuid
from pathlib import Path
from typing import Any, Dict
from tools.arch import plan_utils

import yaml
from jsonschema import validate, ValidationError

# Configurable constants
PLAN_SCHEMA_PATH = Path('schemas/PLAN_SCHEMA.json')
MCP_SCHEMA_PATH = Path('schemas/MCP_MESSAGE_SCHEMA.json')
POSTBOX_ROOT = Path('postbox')
LOGS_TASKS_DIR = Path('logs/tasks')
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
def build_mcp_message(task: Dict[str, Any], trace_id: str, plan_id: str, agent: str) -> Dict[str, Any]:
    with open(MCP_SCHEMA_PATH) as f:
        mcp_schema = json.load(f)
    now = plan_utils.now_iso()
    message = {
        "sender_id": "ARCH",
        "recipient_id": agent,
        "trace_id": trace_id,
        "retry_count": 0,
        "task_id": task.get('id', str(uuid.uuid4())),
        "payload": {
            "type": "task_assignment",
            "content": task.get('input', {})
        },
        "timestamp": now
    }
    try:
        validate(instance=message, schema=mcp_schema)
    except ValidationError as e:
        raise ValueError(f"MCP message validation failed: {e.message}")
    return message

# Main plan runner logic
def run_plan(plan_path: Path):
    plan = plan_utils.load_and_validate_plan(plan_path, PLAN_SCHEMA_PATH)
    plan_id = plan.get('id', plan_path.stem)
    tasks = plan.get('tasks', [])
    retry_limit = get_retry_limit()
    for idx, task in enumerate(tasks):
        agent = task.get('agent')
        if not agent:
            print(f"[ERROR] Task {idx} missing agent. Skipping.")
            continue
        trace_id = plan_utils.generate_trace_id(plan_id, idx)
        mcp_msg = build_mcp_message(task, trace_id, plan_id, agent)
        attempt = 0
        result = None
        while attempt < retry_limit:
            mcp_msg['retry_count'] = attempt
            plan_utils.write_to_inbox(agent, mcp_msg, POSTBOX_ROOT)
            print(f"[INFO] Sent task {task.get('id', idx)} to {agent} (attempt {attempt+1}/{retry_limit})")
            try:
                response = wait_for_response(agent, trace_id)
                result = response
                print(f"[INFO] Received response for {trace_id} from {agent}")
                break
            except TimeoutError as e:
                print(f"[WARN] {e}")
                attempt += 1
                time.sleep(RETRY_DELAY)
        # Log result
        log_data = {
            "trace_id": trace_id,
            "plan_id": plan_id,
            "task_index": idx,
            "agent": agent,
            "task": task,
            "attempts": attempt + 1,
            "result": result,
            "status": (result or {}).get('payload', {}).get('content', {}).get('status', 'timeout'),
            "score": (result or {}).get('payload', {}).get('content', {}).get('score'),
            "duration_sec": (result or {}).get('payload', {}).get('content', {}).get('duration_sec'),
            "timestamp": plan_utils.now_iso()
        }
        plan_utils.write_task_log(trace_id, log_data, LOGS_TASKS_DIR)
        if not result:
            print(f"[ERROR] Task {trace_id} failed after {retry_limit} attempts. Escalating.")
            # Escalation logic could be added here
            continue

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python plan_runner.py <plan_path>")
        sys.exit(1)
    run_plan(Path(sys.argv[1])) 