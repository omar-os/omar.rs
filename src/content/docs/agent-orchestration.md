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
EA proposes a plan
        │
        ▼
EA calls create_task MCP tool to spawn agents
        │
        ▼
  agent-1 (working)   agent-2 (working)   agent-3 (idle)
        │
        ▼
Agents output [TASK COMPLETE] + call notify_parent
        │
        ▼
EA aggregates results, calls complete_task
```

## Parent-Child Hierarchy

Agents track their parent via `~/.omar/agent_parents.json`. This enables:

- Tree visualization in the TUI (command tree with box-drawing)
- Navigation: `↑/↓` moves selection, `←/→` switches panels, `Tab` drills into children, `Shift+Tab` returns to parent
- Hierarchical status monitoring

Any agent can spawn children, creating arbitrary depth.

## EA Protocol

The EA communicates with OMAR exclusively via MCP tools. It never does work directly — it only spawns agents, monitors them, and manages projects.

### Spawning agents

```json
// create_task
{
  "name": "api",
  "task": "Create Express server with /users and /posts endpoints",
  "parent": "ea"
}
```

### Monitoring agents

```json
// check_task — accepts task UUID or agent short name
{ "task_id": "api" }

// get_ea_summary — overview of all active agents
{}
```

### Sending input to agents

```json
// send_input
{
  "name": "api",
  "text": "Also add /comments endpoint",
  "enter": true
}
```

### Completing tasks

```json
// complete_task — handles cleanup atomically
{ "task_id": "api" }
```

### Replacing stuck agents

```json
// replace_stuck_task_agent
{
  "task_id": "api",
  "additional_context": "Focus on the /users endpoint first"
}
```

## Agent Context

When spawning agents with a task, OMAR injects the unified `agent.md` prompt. Each agent is autonomous — it decides whether to do the work itself or spawn sub-agents:

```
You are an Agent in the OMAR system.
You receive a task from your parent, assess it, and
decide the best way to get it done — either by doing
it yourself or by spawning sub-agents.

YOUR NAME: api
YOUR PARENT: ea
YOUR TASK: Create Express server with /users and /posts endpoints
```

Agents signal completion by outputting `[TASK COMPLETE]` followed by a summary, then immediately calling `notify_parent` with their name and the summary text. This wakes the parent without polling.

## Event-Driven Coordination

The scheduler enables timed coordination between agents:

- **Wake-ups**: Agents schedule self-wake-ups to check on sub-agent progress
- **Handoffs**: Agent A schedules an event for Agent B when a dependency is ready
- **Cron jobs**: Recurring events auto-reschedule after each delivery

Events are delivered by injecting text into the target agent's tmux session.

```json
// schedule_event — one-shot wake-up
{
  "sender": "ea",
  "receiver": "api",
  "payload": "Check progress on API implementation",
  "delay_seconds": 300
}

// schedule_event — recurring cron (every 5 minutes)
{
  "sender": "ea",
  "receiver": "api",
  "payload": "Progress check",
  "recurring_seconds": 300
}
```

## Memory Persistence

OMAR maintains state across sessions (all paths are EA-scoped under `~/.omar/ea/<id>/`):

- **`memory.md`** - Snapshot of active projects, agents, and tasks; prepended to EA prompt on restart
- **`task_registry.json`** - Authoritative task lifecycle state for `create_task` / `check_task` / `complete_task`
- **`worker_tasks.json`** - Session name → task description cache (augmented from task registry)
- **`agent_parents.json`** - Parent-child relationships
- **`status/<session>.md`** - Agent self-reported status

Top-level `~/.omar/`:
- **`eas.json`** - Registry of all EAs
- **`manager_notes_ea<N>.md`** - Persistent manager notes for EA N
