import json
from datetime import datetime
from pathlib import Path

msg = {
    'sender_id': 'CC',
    'recipient_id': 'ARCH',
    'trace_id': f'eval-{datetime.now().isoformat()}',
    'retry_count': 0,
    'task_id': 'TASK-074B',
    'payload': {
        'type': 'eval_tracker_report',
        'content': {
            'summary': 'Output evaluation tracker is live. Logs are being generated in logs/agent_scores.json. Rolling summaries and per-agent stats are available.'
        }
    }
}

outbox = Path(__file__).parent.parent.parent / 'postbox' / 'ARCH' / 'outbox.json'
outbox.parent.mkdir(parents=True, exist_ok=True)

try:
    if outbox.exists():
        with open(outbox, 'r') as f:
            data = json.load(f)
    else:
        data = []
except Exception:
    data = []

data.append(msg)
with open(outbox, 'w') as f:
    json.dump(data, f, indent=2)
print(f"ARCH notified in outbox: {outbox}") 