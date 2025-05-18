# Insights Directory

This directory contains learning data and performance insights for the Bluelabel Agent OS system.

## Contents

- `agent_learning_snapshot.json`: Current snapshot of agent performance data
- `learning_engine.py`: Core learning engine for log parsing and metrics
- `performance_metrics/`: Directory for detailed performance analysis

## Usage

The learning engine analyzes agent behavior and generates performance insights that are used for:
- Adaptive routing decisions
- Performance optimization
- Success rate tracking
- Pattern recognition

## Data Structure

The `agent_learning_snapshot.json` file contains:
- Agent performance metrics
- Task type success rates
- Average execution times
- Failure patterns
- Optimization recommendations

## Maintenance

This directory should be regularly cleaned to prevent accumulation of outdated snapshots. Only the most recent snapshot is used by the system. 