# AI-First OS Blueprint

This repository contains the initial architecture, specifications, and reference implementation for the AI-First OS, based on the provided blueprint.

The goal is to translate the high-level concepts of an agent-centric, local-first, and secure OS into a set of concrete, actionable artifacts that can be used for prototyping and development.

## Directory Structure

```
.
├── ARCHITECTURE.md
├── README.md
└── spec/
    ├── schemas/
    │   ├── agent_manifest.json
    │   ├── capability_call.json
    │   └── intent.json
    └── reference_agent/
        ├── agent_manifest.json
        ├── calendar_agent.py
        ├── Dockerfile
        └── README.md
```

- **`ARCHITECTURE.md`**: Contains a high-level overview of the system architecture, including a diagram and a summary of the core principles.
- **`spec/`**: Holds the technical specifications for the OS.
  - **`spec/schemas/`**: Contains the JSON schemas that define the core data structures and APIs for communication between the OS components (e.g., Planner, Agents).
  - **`spec/reference_agent/`**: Provides a runnable example of a simple "Calendar" agent that conforms to the OS specifications. This serves as a template for developing new agents.
