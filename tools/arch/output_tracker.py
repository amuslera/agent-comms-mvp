import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

LOG_PATH = Path(__file__).parent.parent / 'logs' / 'agent_scores.json'
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

def append_evaluation_log(agent_id: str, task_id: str, plan_id: Optional[str], success: Optional[bool], score: Optional[float], duration_sec: Optional[float], notes: Optional[str] = None):
    entry = {
        'timestamp': datetime.now().isoformat(),
        'agent_id': agent_id,
        'task_id': task_id,
        'plan_id': plan_id,
        'success': success,
        'score': score,
        'duration_sec': duration_sec,
        'notes': notes
    }
    try:
        if LOG_PATH.exists():
            with open(LOG_PATH, 'r') as f:
                data = json.load(f)
        else:
            data = []
    except Exception:
        data = []
    data.append(entry)
    with open(LOG_PATH, 'w') as f:
        json.dump(data, f, indent=2)


def extract_and_log_from_mcp(message: Dict[str, Any]):
    """Extract evaluation fields from MCP message and log them."""
    payload = message.get('payload', {})
    agent_id = message.get('sender_id')
    task_id = message.get('task_id')
    plan_id = payload.get('plan_id') if isinstance(payload, dict) else None
    content = payload.get('content', {}) if isinstance(payload, dict) else {}
    success = content.get('success')
    score = content.get('score')
    duration_sec = content.get('duration_sec')
    notes = content.get('notes')
    append_evaluation_log(agent_id, task_id, plan_id, success, score, duration_sec, notes)


def get_last_n_for_agent(agent_id: str, n: int = 10):
    try:
        if LOG_PATH.exists():
            with open(LOG_PATH, 'r') as f:
                data = json.load(f)
        else:
            return []
    except Exception:
        return []
    return [entry for entry in reversed(data) if entry['agent_id'] == agent_id][:n]


def get_agent_rolling_summary(agent_id: str, n: int = 10):
    last_n = get_last_n_for_agent(agent_id, n)
    if not last_n:
        return {}
    scores = [e['score'] for e in last_n if e['score'] is not None]
    successes = [e['success'] for e in last_n if e['success'] is not None]
    avg_score = sum(scores) / len(scores) if scores else None
    success_rate = sum(1 for s in successes if s) / len(successes) if successes else None
    return {
        'agent_id': agent_id,
        'count': len(last_n),
        'avg_score': avg_score,
        'success_rate': success_rate
    } 