---
title: "MCP Tool Reference"
description: "OMAR's MCP stdio tool surface for agent orchestration, events, and computer use"
order: 4
---

## Overview

OMAR exposes its orchestration surface as an **MCP (Model Context Protocol) server over stdio**. Each agent backend spawns its own `omar mcp-server` child and talks to it over JSON-RPC framed by line-delimited messages. There is no listening port, no auth surface, and no shared daemon — when the agent dies, its MCP child dies with it.

Tools are typed and have JSON-Schema input definitions; from the agent's perspective every tool is `omar.<tool_name>`.

### How an agent reaches the server

The manager writes a per-EA `McpLaunchContext` to `~/.omar/mcp/ea-<id>/context.json` and configures the backend's MCP integration to launch:

```
omar mcp-server --context-file ~/.omar/mcp/ea-<id>/context.json
```

The launch context bakes in the EA id, so every tool call from that agent is automatically scoped to its EA — no per-call routing argument, no risk of cross-EA action.

## EA Registry

| Tool             | Purpose                                                             |
| ---------------- | ------------------------------------------------------------------- |
| `list_eas`       | List registered EAs with `is_active` markers (read-only).           |
| `get_active_ea`  | Read the persisted active EA pointer used by the dashboard / CLI.   |
| `switch_ea`      | Update the persisted active-EA pointer. Does **not** rescope this MCP server — already-running children stay pinned to their launch EA. |
| `create_ea`      | Register a new EA by name (server-assigned monotonic id).           |
| `delete_ea`      | Unregister an EA. Refuses to delete the only remaining EA, or one with attached tmux sessions; surfaces filesystem errors instead of silently succeeding. |

## Agents

| Tool                  | Purpose                                                                      |
| --------------------- | ---------------------------------------------------------------------------- |
| `list_agents`         | Live agents in the pinned EA, with health and last-output summary.           |
| `get_agent`           | Detailed view of a single agent: pane tail, parent, status, task.            |
| `get_agent_summary`   | Lightweight card view (health, task, status, children).                      |
| `update_agent_status` | Write the agent's self-reported status (persisted under `~/.omar/ea/<id>/status/<session>.md`). |
| `spawn_agent`         | Single unified spawn path. Requires `project_id`. Returns the agent's session name. |
| `kill_agent`          | Kill the tmux session and mark the corresponding `Running` task `Failed`.    |
| `send_input`          | Inject text into an agent's tmux session (e.g. answer a confirmation).       |

`spawn_agent` arguments:

```jsonc
{
  "name":       "auth",
  "task":       "Implement JWT auth",
  "project_id": 1,
  "parent":     "ea",
  "workdir":    "/path/to/project",        // optional, defaults to launch workdir
  "backend":    "codex",                   // optional override (claude/codex/cursor/gemini/opencode)
  "model":      "o3"                       // optional --model override
}
```

There is no `track` flag; every spawn is tracked. `complete_task` and `replace_stuck_task_agent` resolve short names (`auth`) or UUIDs.

## Projects

| Tool               | Purpose                                                                                  |
| ------------------ | ---------------------------------------------------------------------------------------- |
| `list_projects`    | List projects in the pinned EA.                                                          |
| `add_project`      | Register a project bucket; returns `project_id` for `spawn_agent`.                       |
| `complete_project` | Remove a project. Blocks while any of its tasks are still `Running`; `Failed`/`Replaced` rows count as history. |

## Events / Scheduler

| Tool                  | Purpose                                                                |
| --------------------- | ---------------------------------------------------------------------- |
| `schedule_omar_event` | Enqueue a one-shot or recurring event in OMAR's durable scheduler.     |
| `list_events`         | Inspect pending events for the pinned EA.                              |
| `cancel_event`        | Cancel an event by id (only if it belongs to this EA).                 |

The tool is named `schedule_omar_event` to disambiguate from same-named tools published by other MCP servers — muscle-memory `schedule_event` calls fail loudly instead of silently routing to a different server.

`schedule_omar_event` arguments:

```jsonc
{
  "receiver":          "auth",                      // agent short name, or "ea"
  "payload":           "Status check on auth?",
  "sender":            "ea",                        // optional, defaults to "ea"
  "delay_seconds":     300,                         // wake in 5 minutes
  "recurring_seconds": 300                          // OR auto-reschedule every 5 minutes
}
```

For an immediate parent notification on completion, use `delay_seconds: 0` with payload `"[CHILD COMPLETE] <your_name>: <summary>"`.

Backend-native wake tools (`ScheduleWakeup`, `TaskReminder`, `task_reminder`, `scheduled_tasks`) are denied at the spawn level via `--disallowedTools` and per-backend deny configs — agents must use `schedule_omar_event` so wake-ups appear in OMAR's event queue and survive restarts.

## Auditing

| Tool                | Purpose                                                                         |
| ------------------- | ------------------------------------------------------------------------------- |
| `log_justification` | Append a structured JSONL audit entry before significant state-changing actions (spawn, kill, send-input, schedule, project change). |

## Slack

| Tool          | Purpose                                                                            |
| ------------- | ---------------------------------------------------------------------------------- |
| `slack_reply` | Queue a Slack reply file in `~/.omar/slack_outbox/`. The Slack bridge polls this directory and posts to Slack via Web API. |

`slack_reply` is the only Slack-touching tool — the EA never talks to Slack directly. The bridge is a separate process (`omar-slack`) and its EA target is read from `[slack_bridge].active_ea` in `config.toml`.

## Computer Use

The computer-use surface holds an exclusive lock; one agent at a time can issue input. All computer tools require the agent to identify itself by name to prove lock ownership.

| Tool                     | Purpose                                              |
| ------------------------ | ---------------------------------------------------- |
| `computer_status`        | Check availability and current lock owner.           |
| `computer_lock_acquire`  | Acquire exclusive computer access for the named agent.|
| `computer_lock_release`  | Release the lock.                                    |
| `computer_screenshot`    | Take a screenshot (lock required).                   |
| `computer_mouse`         | `move`/`click`/`double_click`/`drag`/`scroll`.       |
| `computer_keyboard`      | `type` text, or `key` for a key combination.         |
| `computer_screen_size`   | Read display dimensions.                             |
| `computer_mouse_position`| Read current cursor position.                        |

## Backends

| Tool             | Purpose                                                              |
| ---------------- | -------------------------------------------------------------------- |
| `list_backends`  | Probe installed agent backends (claude / codex / cursor / gemini / opencode) with bounded `--version` checks; useful for listing options in the dashboard or external tools. |

## Caller's perspective

Most agent harnesses surface MCP tools by name — for example, in Claude Code's tool palette they appear as `omar.spawn_agent`, `omar.schedule_omar_event`, etc. A direct JSON-RPC client (such as the Slack bridge) calls them as:

```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "method": "tools/call",
  "params": {
    "name": "spawn_agent",
    "arguments": {
      "name": "auth",
      "task": "Implement JWT auth",
      "project_id": 1
    }
  }
}
```

## Error semantics

- `tools/call` returns `isError: true` with a single text content block on tool-level failure (e.g. unknown agent, attached session, validation rejection).
- JSON-RPC `error` only carries protocol-level failures (malformed JSON, unknown method, bad framing).
- Tools document their retry safety in the schema description — read-only tools are always safe to retry; mutating tools that aren't idempotent (e.g. `add_project`) advise calling the corresponding `list_*` tool after uncertain results.

## Migration notes

OMAR 0.3+ replaces the legacy `:9876` REST API. If you have an out-of-tree integration that talked to `http://127.0.0.1:9876/api/...`, switch to spawning `omar mcp-server` and calling tools via JSON-RPC over stdio — see the Slack bridge (`bridges/slack/src/omar.rs`) for a reference implementation.
