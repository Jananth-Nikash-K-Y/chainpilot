# ChainPilot Agents

Specialized agent modules invoked by the Orchestrator agent.

```
User -> Orchestrator Agent -> Specialized Agents -> MCP Tools / Services -> Business Data
```

Each agent directory follows the same internal shape:
- `agent.py`       — agent definition (identity, purpose, tool bindings)
- `executor.py`     — runtime execution logic
- `config.py`       — agent-specific configuration
- `prompts.py`      — system/task prompts
- `schemas.py`      — input/output schemas for this agent

No agent logic is implemented yet — this is a structural placeholder only.
