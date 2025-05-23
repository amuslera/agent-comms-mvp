import re
from datetime import datetime
from pathlib import Path

TASK_CARDS_PATH = Path("TASK_CARDS.md")

STATUS_MAP = {
    "done": "✅ Done",
    "cancelled": "❌ Cancelled",
    "paused": "⏸️ Paused",
}

def mark_task(task_id, status, summary=None, time_spent=None, resolution=None):
    """
    Update TASK_CARDS.md: mark status, add summary, time, and resolution for a task.
    """
    if status not in STATUS_MAP:
        raise ValueError(f"Invalid status: {status}")
    status_str = STATUS_MAP[status]
    lines = TASK_CARDS_PATH.read_text(encoding="utf-8").splitlines()
    task_header = f"### {task_id}:"
    found = False
    for i, line in enumerate(lines):
        if line.strip().startswith(task_header):
            found = True
            # Update or insert status line
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("**Status**:"):
                j += 1
            if j < len(lines):
                lines[j] = f"**Status**: {status_str}"
            else:
                lines.insert(i+1, f"**Status**: {status_str}")
            # Insert or update summary, time, resolution
            def upsert_field(field, value):
                if not value:
                    return
                k = i + 1
                while k < len(lines) and not lines[k].strip().startswith(f"**{field}**:"):
                    k += 1
                if k < len(lines) and lines[k].strip().startswith(f"**{field}**:"):
                    lines[k] = f"**{field}**: {value}"
                else:
                    lines.insert(i+2, f"**{field}**: {value}")
            upsert_field("Summary", summary)
            upsert_field("Time Spent", time_spent)
            upsert_field("Resolution", resolution)
            break
    if not found:
        raise ValueError(f"Task {task_id} not found in TASK_CARDS.md")
    TASK_CARDS_PATH.write_text("\n".join(lines), encoding="utf-8")
    return True

def cli():
    import argparse
    parser = argparse.ArgumentParser(description="Update TASK_CARDS.md for a task.")
    parser.add_argument("task_id", help="Task ID, e.g. TASK-140C")
    parser.add_argument("--status", required=True, choices=STATUS_MAP.keys())
    parser.add_argument("--summary", help="Task summary")
    parser.add_argument("--time", help="Time spent (e.g. 1.5h)")
    parser.add_argument("--resolution", help="Resolution notes")
    args = parser.parse_args()
    mark_task(args.task_id, args.status, args.summary, args.time, args.resolution)
    print(f"Updated {args.task_id} in TASK_CARDS.md.")

if __name__ == "__main__":
    cli() 