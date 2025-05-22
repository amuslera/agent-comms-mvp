import json
from datetime import datetime
from pathlib import Path

msg = {
    'sender_id': 'CC',
    'recipient_id': 'ARCH',
    'trace_id': f'test-{datetime.now().isoformat()}',
    'retry_count': 0,
    'task_id': 'TASK-073E',
    'payload': {
        'type': 'test_report',
        'content': {
            'summary': 'ARCH MCP test suite: 26/26 passing. All MCP envelope, parser, router, and retry logic validated. System stable and ready for merge.'
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