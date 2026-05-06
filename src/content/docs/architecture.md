---
title: "Architecture & Design"
description: "OMAR's architecture - how the TUI dashboard manages agents via tmux and MCP"
order: 2
---

## Overview

OMAR is a TUI dashboard for orchestrating AI coding agents via tmux. Agents drive the system through a typed **MCP (Model Context Protocol) tool surface** delivered over each agent's own `omar mcp-server` stdio child. There is no listening port — every agent talks to OMAR over JSON-RPC on its private stdin/stdout.

## Architecture

```
tmux server
├── omar-dashboard            (TUI session, drives the UI)
│
├── omar-agent-ea-0           (Executive Assistant for EA 0)
├── omar-agent-ea-1           (Executive Assistant for EA 1, optional)
├── omar-agent-0-worker1      (claude, parented to EA 0)
├── omar-agent-0-worker2      (codex,  parented to EA 0)
└── omar-agent-1-research     (gemini, parented to EA 1)
                │
                ▼  each agent spawns its own MCP child
        ┌─────────────────────────────────────────┐
        │  omar mcp-server (stdio JSON-RPC)       │
        │  pinned to the agent's launch EA        │
        │  ~30 typed tools:                       │
        │    spawn_agent, kill_agent, send_input, │
        │    list_agents, get_agent,              │
        │    add_project, complete_project,       │
        │    schedule_omar_event, list_events,    │
        │    list_eas, switch_ea, create_ea,      │
        │    log_justification, slack_reply,      │
        │    computer_*, ...                      │
        └─────────────────────────────────────────┘

State on disk:    ~/.omar/ea/<id>/{worker_tasks,task_registry,...}.json
                  ~/.omar/{config.toml, eas.json, active_ea, ...}
```

The dashboard, agents, the Slack bridge, and any external client all converge on the same on-disk state under `~/.omar/`. They never talk to each other directly.

## Core Components

### Workspace Structure

OMAR is a Rust workspace with 3 binary crates:

- **`omar`** — main binary: TUI dashboard, MCP stdio server (`omar mcp-server`), event scheduler, manager subcommand
- **`omar-slack-bridge`** — Slack Socket Mode integration; spawns its own `omar mcp-server` child
- **`omar-computer-bridge`** — X11 computer-use helper (mouse, keyboard, screenshots)

### Multi-EA

OMAR supports multiple Executive Assistants in parallel. Each EA owns:

- A tmux manager session (`omar-agent-ea-<id>`)
- A worker namespace (`omar-agent-<id>-<name>`)
- A state directory (`~/.omar/ea/<id>/`)
- An isolated project board, memory, and event queue

The `eas.json` registry, the `active_ea` pointer, and per-EA state directories are managed by `src/ea.rs`. Agents are pinned to their launch EA — `switch_ea` only flips the dashboard's default; live MCP children stay on their original EA.

### Session Types

- **Dashboard**: `omar-dashboard` — the TUI session (auto-created on launch)
- **Manager / EA**: `omar-agent-ea-<id>` — the EA's tmux session, one per EA
- **Worker agents**: `omar-agent-<ea_id>-<name>` — spawned by the EA via `spawn_agent`

### Unified Agent Model

All agents (except the EA) receive `agent.md` as their system prompt. Every spawned agent is autonomous: it gets a task, decides whether to do the work itself or spawn sub-agents via `spawn_agent`, and reports completion. The EA receives `executive-assistant.md` with memory context prepended.

### Parent-Child Hierarchy

Agents track parent-child relationships in `~/.omar/ea/<id>/agent_parents.json`. The TUI renders this as a navigable command tree. Any agent can spawn children, creating arbitrary depth.

## How Agents Reach the MCP Server

The manager writes per-EA launch context (`~/.omar/mcp/ea-<id>/context.json`) before spawning each agent, then configures the backend's MCP integration to launch `omar mcp-server --context-file <path>`:

| Backend  | Mechanism                                                          |
| -------- | ------------------------------------------------------------------ |
| Claude   | `~/.omar/mcp/ea-<id>/claude-mcp.json` referenced via `--mcp-config` |
| Codex    | `-c mcp_servers.omar.command=…` / `mcp_servers.omar.args=…`        |
| Cursor   | entry written into `~/.cursor/mcp.json` (key `omar-ea-<id>`)        |
| Gemini   | `gemini mcp add -s user omar <omar> mcp-server --context-file …`   |
| Opencode | env var pointing at `omar mcp-server --context-file …`             |

Each backend launches the `omar mcp-server` child itself; the bake-in EA id at launch is what gives every agent its EA pinning without needing any per-call routing argument.

## Health Monitoring

Health is determined by pane content change between refresh frames:

| State   | Icon | Meaning                               |
| ------- | ---- | ------------------------------------- |
| Running | ●    | Pane content changed since last check |
| Idle    | ○    | No output change detected             |

## Dashboard UI Layout

1. **Status Bar** (top) — Agent counts, event countdown, warnings
2. **Agent Grid** — Cards for each agent, sorted by health
3. **Focus Panel** — Selected agent's output + command tree
4. **Help Bar** (bottom) — Key bindings

## Persistent State

```
~/.omar/
├── config.toml                       # User config
├── eas.json                          # EA registry
├── active_ea                         # Dashboard / CLI default EA pointer
├── ea_next_id                        # Monotonic EA-id high-water mark
├── ea/<id>/
│   ├── worker_tasks.json             # Agent → task mapping
│   ├── task_registry.json            # Authoritative task records
│   ├── agent_parents.json            # Parent-child relationships
│   ├── memory.md                     # EA memory snapshot
│   ├── ea_prompt_combined.md         # Rendered EA system prompt
│   └── status/<session>.md           # Agent self-reported status
├── mcp/ea-<id>/
│   ├── context.json                  # McpLaunchContext for spawned agents
│   ├── claude-mcp.json               # Claude --mcp-config target
│   └── gemini-deny-native-wake.toml  # Per-backend wake-tool denylist
├── slack_outbox/                     # slack_reply MCP outputs awaiting delivery
├── scheduled_events.json             # Persistent event queue (durable across restarts)
├── prompts/                          # Synced prompt templates
├── logs/panics/                      # Persisted panic dumps
└── manager_notes_ea<id>.md           # Per-EA notes the EA writes via shell heredoc
```

## Configuration

```toml
# ~/.omar/config.toml

[dashboard]
refresh_interval = 1
session_prefix = "omar-agent-"
show_event_queue = true
sidebar_right = true
show_quotes = false

[health]
idle_warning = 15
idle_critical = 300
error_patterns = ["error", "failed", "rate limit", "exception"]

[agent]
default_command = "claude --dangerously-skip-permissions"
default_workdir = "."

[watchdog]
command = ""                          # Empty disables the watchdog
slack_channel = ""

[metrics]
spawn_metrics_enabled = false         # Optional ~/.omar/metrics/spawn_metrics.jsonl

[slack_bridge]
# active_ea = "Research"              # Set via the dashboard settings panel ('S')
                                      # or by manual edit; the Slack bridge
                                      # picks up changes on the next inbound
                                      # message without a restart.
```

Backend is auto-detected from installed tools (Claude Code, Codex, Cursor, Gemini, Opencode) and can be overridden with `--agent`. The slack-bridge target EA is read from `[slack_bridge].active_ea`; if missing or unresolvable the bridge falls back to the first registered EA at runtime.

## Key Bindings

| Key                  | Action                             |
| -------------------- | ---------------------------------- |
| `←/→` or `h/l`       | Switch panel (sidebar / main)      |
| `↑/↓` or `j/k`       | Move selection up/down             |
| `Tab`                | Drill into selected agent          |
| `Shift+Tab` or `Esc` | Back (drill up)                    |
| `Enter`              | Attach to selected agent           |
| `n`                  | Spawn new agent                    |
| `d`                  | Kill selected agent                |
| `N`                  | Spawn new EA (prompts for name)    |
| `D`                  | Delete current EA                  |
| `[`                  | Previous EA                        |
| `]`                  | Next EA                            |
| `p`                  | Add a project                      |
| `e`                  | Show scheduled events              |
| `S`                  | Settings (incl. Slack bridge EA)   |
| `G`                  | Debug console                      |
| `r`                  | Refresh agent list                 |
| `z`                  | Detach (dashboard keeps running)   |
| `?`                  | Toggle help                        |
| `Q`                  | Quit                               |
