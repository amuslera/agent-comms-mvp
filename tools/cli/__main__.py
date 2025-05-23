import sys
import argparse
from tools.taskcard_writer import mark_task

def main():
    parser = argparse.ArgumentParser(prog="bluelabel", description="Bluelabel Agent OS CLI")
    subparsers = parser.add_subparsers(dest="command", help="Subcommand to run")

    # mark command
    mark_parser = subparsers.add_parser("mark", help="Update TASK_CARDS.md for a task")
    mark_parser.add_argument("task_id", help="Task ID, e.g. TASK-140C")
    mark_parser.add_argument("--status", required=True, choices=["done", "cancelled", "paused"])
    mark_parser.add_argument("--summary", help="Task summary")
    mark_parser.add_argument("--time", help="Time spent (e.g. 1.5h)")
    mark_parser.add_argument("--resolution", help="Resolution notes")

    args = parser.parse_args()

    if args.command == "mark":
        mark_task(args.task_id, args.status, args.summary, args.time, args.resolution)
        print(f"Updated {args.task_id} in TASK_CARDS.md.")
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main() 