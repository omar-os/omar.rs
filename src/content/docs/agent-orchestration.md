---
title: "Agent Orchestration"
description: "How OMAR orchestrates hierarchical agents for complex tasks"
order: 5
---

## Overview

OMAR uses a hierarchical agent model where an Executive Assistant (EA) orchestrates worker agents. The EA breaks high-level tasks into parallel sub-tasks and spawns agents to execute them.

## Unified Agent Model

All agents (except the EA) use the same prompt (`agent.md`). There is no PM/worker distinction — every spawned agent is autonomous: it receives a task, decides whether to do the work itself or spawn sub-agents, and reports completion.

The EA (`executive-assistant.md`) is special: it acts purely as a dispatcher — it never does work directly, only spawns agents, monitors them, and manages projects. It gets memory context prepended to its prompt.

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

The EA communicates with OMAR exclusively via the HTTP API. It never does work directly — it only spawns agents, monitors their output, and manages projects.

### Spawning agents

```bash
curl -X POST http://localhost:9876/api/agents \
  -H "Content-Type: application/json" \
  -d '{"name": "api", "task": "Create Express server with /users and /posts endpoints"}'
```

### Monitoring agents

```bash
# Check a specific agent's output
curl http://localhost:9876/api/agents/api

# List all agents with health status
curl http://localhost:9876/api/agents
```

### Sending input to agents

```bash
curl -X POST http://localhost:9876/api/agents/api/send \
  -H "Content-Type: application/json" \
  -d '{"text": "Also add /comments endpoint", "enter": true}'
```

### Killing agents on completion

```bash
curl -X DELETE http://localhost:9876/api/agents/api
```

### Managing projects

```bash
# Add a project
curl -X POST http://localhost:9876/api/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "Build REST API"}'

# Complete a project
curl -X DELETE http://localhost:9876/api/projects/<id>
```

## Agent Context

When spawning agents with a task, OMAR injects the unified `agent.md` prompt. Each agent is autonomous — it decides whether to do the work itself or spawn sub-agents:

```
You are an Agent in the OMAR (One-Man Army) system.
You receive a task from your parent, assess it, and
decide the best way to get it done — either by doing
it yourself or by spawning sub-agents.

YOUR NAME: api
YOUR PARENT: ea
YOUR TASK: Create Express server with /users and /posts endpoints
```

Agents signal completion by outputting `[TASK COMPLETE]` followed by a summary.

## Event-Driven Coordination

The scheduler enables timed coordination between agents:

- **Wake-ups**: Agents schedule self-wake-ups to check on sub-agent progress
- **Handoffs**: Agent A schedules an event for Agent B when a dependency is ready
- **Cron jobs**: Recurring events auto-reschedule after each delivery

Events are delivered by injecting text into the target agent's tmux session.

```bash
# Schedule a one-shot wake-up event
curl -X POST http://localhost:9876/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "ea",
    "receiver": "api",
    "payload": "Check progress on API implementation",
    "timestamp": 1772904000000000000
  }'

# Schedule a recurring cron job (every 5 minutes)
curl -X POST http://localhost:9876/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "ea",
    "receiver": "api",
    "payload": "Progress check",
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
