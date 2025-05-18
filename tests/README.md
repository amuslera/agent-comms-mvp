# Tests Directory

This directory contains test files and test utilities for the Bluelabel Agent OS system.

## Structure

- `test_agent_flow.py`: End-to-end test validator for agent message processing
- `test_context_awareness.py`: Tests for context management functionality
- `test_orchestrator_retry.py`: Tests for retry and fallback mechanisms

## Running Tests

To run the test suite:

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_agent_flow.py

# Run with verbose output
python -m pytest -v tests/
```

## Test Data

Test data and fixtures are stored in the `tests/fixtures/` directory. Each test file should clean up after itself to maintain a clean test environment. 