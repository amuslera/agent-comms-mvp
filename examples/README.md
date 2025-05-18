# Examples Directory

This directory contains example files demonstrating various aspects of the Bluelabel Agent OS system.

## Contents

- `task_assignment.json`: Example task assignment message
- `task_status.json`: Example task status update message
- `error.json`: Example error message format

## Usage

These examples can be used as templates when creating new messages or testing the system. They follow the schema defined in `exchange_protocol.json`.

## Testing

To test with these examples:
1. Use `task_dispatcher.py` to inject example tasks
2. Monitor execution with `flow_visualizer.py`
3. Check results in agent task logs 