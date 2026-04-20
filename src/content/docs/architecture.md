---
title: "Architecture & Design"
description: "OMAR's architecture - how the TUI dashboard manages agents via tmux"
order: 2
---

## Overview

OMAR is a TUI dashboard for orchestrating AI coding agents via tmux. It provides a real-time terminal interface, an MCP stdio server for agent orchestration, and integration bridges for Slack and computer use.

## Architecture

```
tmux server
├── omar-dashboard (session)
│   ├── TUI Dashboard
│   │   ├── agent-1 (● running)
│   │   ├── agent-2 (○ idle)
│   │   └── agent-3 (● running)
│   └── tmux popup (attach to any agent)
│
├── omar-agent-ea (Executive Assistant)
│   └── MCP stdio server (per-agent, auto-wired into coding tool)
├── omar-agent-worker1 (claude / cursor / codex / ...)
│   └── MCP stdio server
└── omar-agent-worker2 (codex)
    └── MCP stdio server
```

## Core Components

### Workspace Structure

OMAR is a Rust workspace with 3 crates:

- **`omar`** - Main binary: TUI dashboard, MCP server, event scheduler
- **`omar-slack-bridge`** - Slack Socket Mode integration
- **`omar-computer-bridge`** - X11 computer use (mouse, keyboard, screenshots)

### Session Types

- **Dashboard**: `omar-dashboard` - the TUI session (auto-created on launch)
- **Executive Assistant**: `omar-agent-ea-<id>` - one per EA (EA 0 is the default)
- **Work Agents**: `omar-agent-<ea_id>-<name>` - spawned by EA via MCP tools

Multiple EAs are supported. Switch between them with `[`/`]`; create with `N`, delete with `D`.

### Unified Agent Model

All agents use the same role - there is no PM/worker distinction in code. Every agent (except the EA) receives `agent.md` as its system prompt. The EA receives `executive-assistant.md` with memory context.

### Parent-Child Hierarchy

Agents track parent-child relationships in `~/.omar/agent_parents.json`. The TUI renders this as a navigable command tree with Unicode box-drawing characters. Navigate with arrow keys to drill into child agents.

## Health Monitoring

Health is determined by pane content change between refresh frames:

| State   | Icon | Meaning                               |
| ------- | ---- | ------------------------------------- |
| Running | ●    | Pane content changed since last check |
| Idle    | ○    | No output change detected             |

## Dashboard UI Layout

1. **Status Bar** (top) - Agent counts, event countdown, warnings
2. **Agent Grid** (55%) - Cards for each agent, sorted by health
3. **Focus Panel** (33%) - Selected agent's output + command tree
4. **Help Bar** (bottom) - Key bindings

## Persistent State

```
~/.omar/
├── eas.json                   # EA registry
├── active_ea                  # Currently active EA ID
├── manager_notes_ea<N>.md     # Persistent notes for EA N
├── ea/<id>/
│   ├── memory.md              # Snapshot of active state (prepended to EA prompt)
│   ├── task_registry.json     # Authoritative task lifecycle state
│   ├── worker_tasks.json      # Session → task description cache
│   ├── agent_parents.json     # Parent-child relationships
│   └── status/<session>.md    # Agent self-reported status
└── prompts/                   # Synced prompt templates
```

## Configuration

```toml
# ~/.config/omar/config.toml

[dashboard]
refresh_interval = 1
session_prefix = "omar-agent-"

[health]
idle_warning = 15
idle_critical = 300
error_patterns = ["error", "failed", "rate limit", "exception"]

[agent]
default_command = "claude --dangerously-skip-permissions"
default_workdir = "."

[mcp]
enabled = true
```

Agent backend is auto-detected from installed tools (Claude Code, Codex, Cursor, or Opencode) and can be overridden with `--agent`.

## Key Bindings

| Key                  | Action                              |
| -------------------- | ----------------------------------- |
| `←/→` or `h/l`      | Switch panel (sidebar / main)       |
| `↑/↓` or `j/k`      | Move selection up/down              |
| `Tab`                | Drill into selected agent           |
| `Shift+Tab` or `Esc` | Back (drill up)                    |
| `Enter`              | Attach to selected agent            |
| `n`                  | Spawn new agent                     |
| `d`                  | Kill selected agent                 |
| `N`                  | Spawn new EA (prompts for name)     |
| `D`                  | Delete current EA                   |
| `[`                  | Previous EA                         |
| `]`                  | Next EA                             |
| `p`                  | Add a project                       |
| `e`                  | Show scheduled events               |
| `S`                  | Settings                            |
| `G`                  | Debug console                       |
| `r`                  | Refresh agent list                  |
| `z`                  | Detach (dashboard keeps running)    |
| `?`                  | Toggle help                         |
| `Q`                  | Quit                                |
