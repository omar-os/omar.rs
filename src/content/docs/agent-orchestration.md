---
title: "Agent Orchestration"
description: "How OMAR orchestrates hierarchical agents for complex tasks"
order: 5
---

## Overview

OMAR uses a hierarchical agent model where an Executive Assistant (EA) orchestrates worker agents. The EA breaks high-level tasks into parallel sub-tasks and spawns agents to execute them.

## Unified Agent Model

All agents (except the EA) use the same role and prompt (`agent.md`). There is no PM/worker distinction - every spawned agent is a peer that receives a task and works independently.

The EA (`executive-assistant.md`) is special: it gets memory context prepended to its prompt, including active projects, running agents, and their tasks.

## Agent Lifecycle

```
User gives task to EA
        │
        ▼
EA proposes a plan (JSON)
        │
        ▼
OMAR parses plan, spawns agents via API
        │
        ▼
  ┌─────────┐  ┌─────────┐  ┌─────────┐
  │ Agent 1 │  │ Agent 2 │  │ Agent 3 │
  │ Working │  │ Working │  │ Waiting │
  └─────────┘  └─────────┘  └─────────┘
        │
        ▼
Agents report completion via [TASK COMPLETE]
        │
        ▼
EA aggregates results
```

## Parent-Child Hierarchy

Agents track their parent via `~/.omar/agent_parents.json`. This enables:
- Tree visualization in the TUI (command tree with box-drawing)
- Navigation: `→/Tab` drills into children, `←` returns to parent
- Hierarchical status monitoring

Any agent can spawn children, creating arbitrary depth.

## EA Protocol

The EA communicates with OMAR via structured JSON in its output:

### Spawning agents
```json
{
  "type": "plan",
  "agents": [
    {
      "name": "api",
      "role": "API Developer",
      "task": "Create Express server with /users and /posts endpoints",
      "depends_on": []
    }
  ]
}
```

### Messaging agents
```json
{
  "type": "send",
  "target": "api",
  "message": "Also add /comments endpoint"
}
```

### Querying status
```json
{
  "type": "query",
  "target": "all"
}
```

### Signaling completion
```json
{
  "type": "complete"
}
```

## Worker Context

When spawning agents with a task, OMAR injects the unified `agent.md` prompt with context:

```
You are a worker agent in a multi-agent project.

YOUR TASK: Create Express server with /users and /posts endpoints

INSTRUCTIONS:
- Focus only on your assigned task
- When done, end with: [TASK COMPLETE]
- If blocked, say: [BLOCKED: reason]
- If you need input, say: [NEED INPUT: question]
```

## Event-Driven Coordination

The scheduler enables timed coordination between agents:

- **Status checks**: EA schedules recurring events to poll workers
- **Handoffs**: Agent A schedules an event for Agent B when a dependency is ready
- **Reminders**: Agents can set future events for themselves

Events are delivered by injecting text into the target agent's tmux session.

```bash
# Schedule a recurring status check every 5 minutes
curl -X POST http://localhost:9876/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "ea",
    "receiver": "api",
    "payload": "[STATUS CHECK] Report your progress",
    "recurring_ns": 300000000000
  }'
```

## Memory Persistence

OMAR maintains state across sessions:

- **`~/.omar/memory.md`** - Snapshot of active projects, agents, and tasks
- **`~/.omar/worker_tasks.json`** - Map of session name to task description
- **`~/.omar/agent_parents.json`** - Parent-child relationships
- **`~/.omar/status/<session>.md`** - Agent self-reported status

On restart, the EA prompt includes the last memory snapshot for continuity.
