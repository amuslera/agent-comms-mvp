import os
import json
from tools.arch.output_tracker import extract_and_log_from_mcp, get_agent_rolling_summary, LOG_PATH

def test_log_and_summary():
    # Clean log file
    if LOG_PATH.exists():
        os.remove(LOG_PATH)
    # Log 3 MCP messages
    messages = [
        {
            'sender_id': 'CC', 'recipient_id': 'ARCH', 'trace_id': 't1', 'retry_count': 0, 'task_id': 'TASK-001',
            'payload': {'type': 'task_result', 'content': {'success': True, 'score': 0.95, 'duration_sec': 12.3, 'notes': 'ok'}}
        },
        {
            'sender_id': 'CC', 'recipient_id': 'ARCH', 'trace_id': 't2', 'retry_count': 0, 'task_id': 'TASK-002',
            'payload': {'type': 'task_result', 'content': {'success': False, 'score': 0.5, 'duration_sec': 20.0, 'notes': 'timeout'}}
        },
        {
            'sender_id': 'CA', 'recipient_id': 'ARCH', 'trace_id': 't3', 'retry_count': 0, 'task_id': 'TASK-003',
            'payload': {'type': 'task_result', 'content': {'success': True, 'score': 0.8, 'duration_sec': 15.0, 'notes': 'partial'}}
        },
    ]
    for msg in messages:
        extract_and_log_from_mcp(msg)
    # Check log file
    with open(LOG_PATH) as f:
        data = json.load(f)
    assert len(data) >= 3
    # Print rolling summary for CC
    summary = get_agent_rolling_summary('CC', n=10)
    print('CC summary:', summary)
    assert summary['count'] >= 2
    assert summary['avg_score'] is not None
    assert summary['success_rate'] is not None 