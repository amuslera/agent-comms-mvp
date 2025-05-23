import yaml
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Any, Dict
from jsonschema import validate, ValidationError

# Load and validate a plan YAML file against PLAN_SCHEMA.json
def load_and_validate_plan(plan_path: Path, schema_path: Path) -> Dict[str, Any]:
    with open(plan_path, 'r') as f:
        plan_data = yaml.safe_load(f)
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    try:
        validate(instance=plan_data, schema=schema)
    except ValidationError as e:
        raise ValueError(f"Plan validation failed: {e.message}")
    return plan_data

# Generate a unique trace_id for a task
def generate_trace_id(plan_id: str, task_index: int) -> str:
    return f"{plan_id}-{task_index}-{uuid.uuid4().hex[:8]}"

# Get current ISO timestamp
def now_iso() -> str:
    return datetime.utcnow().isoformat() + 'Z'

# Write a message to an agent's inbox
def write_to_inbox(agent: str, message: Dict[str, Any], postbox_root: Path) -> None:
    inbox_path = postbox_root / agent / 'inbox.json'
    inbox_path.parent.mkdir(parents=True, exist_ok=True)
    if inbox_path.exists():
        with open(inbox_path, 'r') as f:
            inbox = json.load(f)
    else:
        inbox = []
    inbox.append(message)
    with open(inbox_path, 'w') as f:
        json.dump(inbox, f, indent=2)

# Write a log entry for a task execution
def write_task_log(trace_id: str, log_data: Dict[str, Any], logs_dir: Path) -> None:
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / f"{trace_id}.json"
    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2) 