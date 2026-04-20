---
title: "MCP Tool Reference"
description: "OMAR's MCP tools for agent orchestration, task lifecycle, events, and more"
order: 4
---

## Overview

OMAR exposes its orchestration interface as an [MCP](https://modelcontextprotocol.io) stdio server. Every spawned agent gets its own MCP server instance automatically wired into its coding tool (e.g., Cursor). Agents call tools natively through function calling — no HTTP, no curl, no memorized endpoint paths.

Because MCP tools arrive as function definitions in a dedicated part of the LLM API call (outside the message history), agents always see the full tool catalog regardless of context length or how many summarizations have occurred. This is the key reliability advantage over REST.

## Agent Tools

### `spawn_agent_session`

Spawn an agent or demo session. Use `create_task` instead for work that needs full project lifecycle tracking.

| Param | Type | Required | Description |
|---|---|---|---|
| `name` | string | ✓ | Agent name |
| `task` | string | ✓ | Work description shown in the dashboard. Clean description only — no `[TASK COMPLETE]` instructions. |
| `workdir` | string | | Working directory |
| `command` | string | | Raw command override |
| `backend` | string | | Backend shorthand: `claude`, `codex`, `cursor`, `opencode` |
| `model` | string | | Model override |
| `parent` | string | | Parent agent name for hierarchy tracking |

### `kill_agent`

Kill an agent session.

| Param | Type | Required |
|---|---|---|
| `name` | string | ✓ |

### `send_input`

Send text input to an agent's tmux session.

| Param | Type | Required | Description |
|---|---|---|---|
| `name` | string | ✓ | Agent name |
| `text` | string | ✓ | Text to send |
| `enter` | boolean | | Whether to press Enter after sending |

### `get_agent_summary`

Get a lightweight summary of a specific agent: health, task, status, children.

| Param | Type | Required |
|---|---|---|
| `name` | string | ✓ |

```json
// Response
{
  "id": "auth",
  "health": "working",
  "task": "Implement JWT authentication module",
  "status": "Writing token validation logic",
  "children": ["auth-tests", "auth-docs"]
}
```

### `list_agents`

List all running agents with health and status.

### `update_agent_status`

Update an agent's self-reported one-line status (shown in the dashboard).

| Param | Type | Required |
|---|---|---|
| `name` | string | ✓ |
| `status` | string | ✓ |

### `list_backends`

List installed agent backends and their availability. Call before picking a `backend` override when availability is unclear.

## Task Lifecycle

The recommended workflow for all tracked work. Handles project creation, agent spawning, and lifecycle state atomically.

### `create_task`

Create a tracked task: add project, spawn worker, persist lifecycle state.

| Param | Type | Required | Description |
|---|---|---|---|
| `task` | string | ✓ | Clean work description. No `[TASK COMPLETE]` or `notify_parent` instructions — those are in every agent's system prompt. |
| `name` | string | ✓ | Worker name |
| `project_name` | string | | Short project label (auto-derived from task if omitted) |
| `parent` | string | | Parent agent name. Omit for EA-owned tasks. |
| `backend` | string | | Backend override |
| `model` | string | | Model override |
| `workdir` | string | | Working directory |

```json
// Response
{
  "task_id": "a3f2c1d4-...",
  "agent": "auth",
  "session": "omar-ea-0-auth",
  "project": "JWT Auth"
}
```

### `check_task`

Inspect tracked task state. Accepts either a task UUID or the agent's short name.

| Param | Type | Required |
|---|---|---|
| `task_id` | string | ✓ |

```json
// Response
{
  "task_id": "a3f2c1d4-...",
  "agent": "auth",
  "status": "running",
  "health": "working",
  "last_status": "Writing token validation logic",
  "last_output": "...",
  "ready_to_complete": false
}
```

### `complete_task`

Complete a tracked task atomically. This is the only correct cleanup path — handles agent teardown, project removal, and task state update.

| Param | Type | Required |
|---|---|---|
| `task_id` | string | ✓ |

### `replace_stuck_task_agent`

Kill a stuck worker and spawn a fresh one for the same task, optionally with additional context. Use when `check_task` shows the agent is idle/stuck.

| Param | Type | Required | Description |
|---|---|---|---|
| `task_id` | string | ✓ | Task to reassign |
| `additional_context` | string | | Extra instructions appended to the original task |

## Event Scheduling

### `schedule_event`

Schedule a wake-up or message for an agent. Supports one-shot and recurring events.

| Param | Type | Required | Description |
|---|---|---|---|
| `receiver` | string | ✓ | Target agent name |
| `payload` | string | ✓ | Message to deliver |
| `sender` | string | | Sender name for logging |
| `delay_seconds` | integer | | Deliver N seconds from now |
| `timestamp_ns` | integer | | Absolute logical timestamp (nanoseconds) |
| `recurring_seconds` | integer | | Auto-reschedule every N seconds (cron) |

```json
// Check in on a worker in 5 minutes
{
  "receiver": "auth",
  "payload": "Status check: how is the auth module going?",
  "delay_seconds": 300
}

// Recurring hourly cron
{
  "receiver": "ea",
  "payload": "Run trading cycle",
  "recurring_seconds": 3600
}
```

### `list_events`

List all scheduled events for the current EA.

### `cancel_event`

Cancel a scheduled event by ID.

| Param | Type | Required |
|---|---|---|
| `event_id` | string | ✓ |

## Coordination

### `notify_parent`

Notify your parent agent that you have completed your task. Call this immediately after printing `[TASK COMPLETE]`. Delivery is handled reliably regardless of payload size.

| Param | Type | Required |
|---|---|---|
| `name` | string | ✓ | Your own agent name |
| `summary` | string | ✓ | Completion summary (same text as your `[TASK COMPLETE]` output) |

### `log_action`

Log a significant action with its reasoning. Used for traceability — all agents are expected to log before state-changing operations.

### `append_manager_note`

Persist a note to the EA's manager log. Use to record active task-to-agent mappings, completed work summaries, user preferences, or recovery context.

## Projects

### `list_projects`

List active projects for the current EA.

## Computer Use

### `computer_status`

Check whether computer use is available and who holds the lock.

### `computer_lock_acquire`

Acquire exclusive computer access. Only one agent may hold the lock at a time.

## Configuration

MCP server settings live in the main config file:

```toml
# ~/.config/omar/config.toml

[mcp]
enabled = true
```

The MCP server binary path and per-agent context file are managed automatically by `omar` — no manual wiring needed.
