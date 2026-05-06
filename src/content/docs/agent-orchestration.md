---
title: "Agent Orchestration"
description: "How OMAR orchestrates hierarchical agents for complex tasks"
order: 5
---

## Overview

OMAR uses a hierarchical agent model. An Executive Assistant (EA) breaks high-level tasks into parallel sub-tasks and spawns worker agents — each agent can in turn spawn its own children, creating arbitrary depth. Every agent drives OMAR through the **MCP tool surface** delivered by its private `omar mcp-server` stdio child.

## Unified Agent Model

All spawned agents use the same prompt (`agent.md`). There is no PM/worker distinction — every spawned agent is autonomous: it receives a task, decides whether to do the work itself or spawn sub-agents, and reports completion.

The EA (`executive-assistant.md`) is special: it acts purely as a dispatcher — it never does work directly, only spawns agents, monitors them, and manages projects. It gets memory context prepended to its prompt.

## Agent Lifecycle

```
User gives task to EA
        │
        ▼
EA registers a project (add_project) and spawns agents (spawn_agent)
        │
        ▼
  agent-1 (working)   agent-2 (working)   agent-3 (idle)
        │
        ▼
Agents schedule_omar_event back to their parent on completion
        │
        ▼
EA aggregates results, calls complete_project when done
```

## Parent-Child Hierarchy

Agents track their parent via `~/.omar/ea/<id>/agent_parents.json`. This enables:

- Tree visualization in the TUI (command tree with box-drawing)
- Navigation: `↑/↓` moves selection, `←/→` switches panels, `Tab` drills into children, `Shift+Tab` returns to parent
- Hierarchical status monitoring

Any agent can spawn children, creating arbitrary depth.

## EA Protocol

The EA communicates with OMAR exclusively via MCP tool calls. It never does work directly — it only spawns agents, monitors their output, and manages projects. Tool names below are written as the agent sees them in its tool palette (e.g. `omar.spawn_agent`).

### Registering a project

Every spawn requires a `project_id`, so the EA opens a project before delegating:

```jsonc
omar.add_project({ "name": "Build REST API" })
// → { "project_id": 1, "name": "Build REST API" }
```

### Spawning agents

```jsonc
omar.spawn_agent({
  "name":       "api",
  "task":       "Create Express server with /users and /posts endpoints",
  "project_id": 1,
  "parent":     "ea"
})
```

### Monitoring agents

```jsonc
omar.list_agents()                         // → all agents in this EA, with health
omar.get_agent({ "name": "api" })          // → pane tail + status + parent
omar.get_agent_summary({ "name": "api" })  // → lightweight card view
```

### Sending input to agents

```jsonc
omar.send_input({
  "name": "api",
  "text": "Also add /comments endpoint",
  "enter": true
})
```

### Killing agents

```jsonc
omar.kill_agent({ "name": "api" })
```

`kill_agent` flips any `Running` task row for that agent to `Failed` and cancels its scheduled events, so the project board never holds orphan rows.

### Managing projects

```jsonc
omar.list_projects()
omar.complete_project({ "project_id": 1 })   // blocks while any task is still Running
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

Agents signal completion by outputting `[TASK COMPLETE]` followed by a summary, then immediately wake the parent:

```jsonc
omar.schedule_omar_event({
  "receiver":      "ea",
  "payload":       "[CHILD COMPLETE] api: Express server with /users and /posts endpoints",
  "delay_seconds": 0
})
```

The parent (the EA, or another agent) sees the message land in its tmux session and aggregates accordingly.

## Event-Driven Coordination

OMAR's scheduler is the single coordination primitive for timed waits. Backend-native wake tools (`ScheduleWakeup`, `TaskReminder`, etc.) are denied at the spawn level — agents must use `schedule_omar_event` so wake-ups appear in the dashboard's event queue and survive restarts.

### One-shot wake-up

```jsonc
omar.schedule_omar_event({
  "receiver":      "api",
  "payload":       "Check progress on API implementation",
  "delay_seconds": 60
})
```

### Recurring cron-style check-in

```jsonc
omar.schedule_omar_event({
  "receiver":          "api",
  "payload":           "Progress check",
  "recurring_seconds": 300
})
```

Events are durable: they're persisted to `~/.omar/scheduled_events.json` and replayed across dashboard restarts. They're delivered by injecting the payload into the receiver's tmux session.

## Memory Persistence

OMAR maintains state across sessions, scoped per EA:

- **`~/.omar/ea/<id>/memory.md`** — Snapshot of active projects, agents, and tasks
- **`~/.omar/ea/<id>/worker_tasks.json`** — Map of session name to task description
- **`~/.omar/ea/<id>/task_registry.json`** — Authoritative task records (id, status, history)
- **`~/.omar/ea/<id>/agent_parents.json`** — Parent-child relationships
- **`~/.omar/ea/<id>/status/<session>.md`** — Agent self-reported status
- **`~/.omar/manager_notes_ea<id>.md`** — Free-form EA notes (the EA writes these via shell heredoc)
- **`~/.omar/scheduled_events.json`** — Durable event queue (shared across EAs, scoped by `ea_id`)

On restart, the EA prompt includes the last memory snapshot for continuity, and pending events resume firing on schedule.
