# JSON Schemas

This directory contains the JSON schemas used for validation and type checking throughout the Bluelabel Agent OS.

## Purpose
The schemas directory provides machine-readable definitions of data structures used in the system, ensuring consistency and validation across all components.

## Contents

### Message Schemas
- [message_schema.json](./message_schema.json) - Schema for agent-to-agent messages
- [task_schema.json](./task_schema.json) - Schema for task definitions
- [plan_schema.json](./plan_schema.json) - Schema for execution plans

### Configuration Schemas
- [agent_config_schema.json](./agent_config_schema.json) - Schema for agent configuration
- [system_config_schema.json](./system_config_schema.json) - Schema for system configuration

### Related Documentation
- [AGENT_PROTOCOL.md](../docs/protocols/AGENT_PROTOCOL.md) - Agent communication protocol
- [API_REFERENCE.md](../docs/API_REFERENCE.md) - API documentation

## Version History
- v1.0.0 (2025-05-15): Initial schema definitions
- v1.1.0 (2025-05-20): Added validation rules
- v1.2.0 (2025-05-28): Enhanced type definitions 