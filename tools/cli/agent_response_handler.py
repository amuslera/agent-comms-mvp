#!/usr/bin/env python3
"""
Agent Response Lifecycle Handler for Bluelabel Agent OS

Usage:
  bluelabel analyze-response /postbox/CA/outbox.json

- Parses agent outbox JSON for task responses
- Validates each entry against the standard schema
- Flags missing fields or errors
- Summarizes status by agent, task, and health
- Optionally writes auto-summary to /TASK_CARDS.md
- Outputs a JSON report for integrations

Standard Response Schema:
{
  "task_id": "TASK-150D",
  "agent": "CA",
  "status": "done",
  "time_spent": "1.5h",
  "output_summary": "...",
  "error": null
}
"""
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any

REQUIRED_FIELDS = ["task_id", "agent", "status", "output_summary"]


def validate_response(entry: Dict[str, Any]) -> List[str]:
    """Validate a single agent response entry."""
    issues = []
    for field in REQUIRED_FIELDS:
        if field not in entry:
            issues.append(f"Missing required field: {field}")
    if entry.get("status") not in {"done", "completed", "error", "cancelled"}:
        issues.append(f"Unexpected status: {entry.get('status')}")
    if "error" in entry and entry["error"]:
        issues.append(f"Error reported: {entry['error']}")
    return issues


def analyze_outbox(path: Path) -> Dict[str, Any]:
    """Parse and analyze agent outbox JSON."""
    with open(path) as f:
        data = json.load(f)
    summary = {
        "total": 0,
        "valid": 0,
        "invalid": 0,
        "errors": 0,
        "by_agent": {},
        "by_status": {},
        "issues": [],
        "entries": []
    }
    for entry in data:
        summary["total"] += 1
        agent = entry.get("agent", "unknown")
        status = entry.get("status", "unknown")
        summary["by_agent"].setdefault(agent, 0)
        summary["by_agent"][agent] += 1
        summary["by_status"].setdefault(status, 0)
        summary["by_status"][status] += 1
        issues = validate_response(entry)
        if issues:
            summary["invalid"] += 1
            if any("Error reported" in i for i in issues):
                summary["errors"] += 1
            summary["issues"].append({"task_id": entry.get("task_id"), "issues": issues})
        else:
            summary["valid"] += 1
        summary["entries"].append(entry)
    return summary


def main():
    parser = argparse.ArgumentParser(description="Analyze agent response logs for validation and summary.")
    parser.add_argument("outbox", type=Path, help="Path to agent outbox JSON (e.g., /postbox/CA/outbox.json)")
    parser.add_argument("--output", type=Path, default=None, help="Optional output JSON report path")
    args = parser.parse_args()
    summary = analyze_outbox(args.outbox)
    print(f"\nAgent Response Analysis for {args.outbox}:")
    print(f"  Total entries: {summary['total']}")
    print(f"  Valid: {summary['valid']}")
    print(f"  Invalid: {summary['invalid']}")
    print(f"  Errors: {summary['errors']}")
    print(f"  By agent: {summary['by_agent']}")
    print(f"  By status: {summary['by_status']}")
    if summary['issues']:
        print("\nIssues found:")
        for issue in summary['issues']:
            print(f"- Task {issue['task_id']}: {', '.join(issue['issues'])}")
    else:
        print("\nNo issues found.")
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"\nJSON report written to {args.output}")

if __name__ == "__main__":
    main() 