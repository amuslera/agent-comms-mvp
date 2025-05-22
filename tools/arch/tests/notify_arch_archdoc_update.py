import json
from datetime import datetime
from pathlib import Path

msg = {
    'sender_id': 'CC',
    'recipient_id': 'ARCH',
    'trace_id': f'doc-{datetime.now().isoformat()}',
    'retry_count': 0,
    'task_id': 'TASK-074D-A',
    'payload': {
        'type': 'doc_update',
        'content': {
            'summary': 'System architecture and roadmap docs updated for v0.6.2: MCP envelope, retry logic, output evaluation logging, metrics API, Phase 6.2 complete, Phase 6.3 planned.'
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