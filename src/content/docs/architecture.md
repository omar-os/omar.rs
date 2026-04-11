---
title: "Architecture & Design"
description: "OMAR's architecture - how the TUI dashboard manages agents via tmux"
order: 2
---

## Overview

OMAR is a TUI dashboard for orchestrating AI coding agents via tmux. It provides a real-time terminal interface, an HTTP API, and integration bridges for Slack and computer use.

## Architecture

```
┌─ tmux server ───────────────────────────────────────────────┐
│                                                             │
│  ┌─ omar-dashboard (session) ────────────────────────────┐  │
│  │                                                       │  │
│  │  ┌─ TUI Dashboard ─────────────────────────────────┐  │  │
│  │  │ Agents: 3 running / 2 idle                      │  │  │
│  │  │ ┌─────────┐ ┌─────────┐ ┌─────────┐            │  │  │
│  │  │ │ agent-1 │ │ agent-2 │ │ agent-3 │            │  │  │
│  │  │ │ ● run   │ │ ○ idle  │ │ ● run   │            │  │  │
│  │  │ └─────────┘ └─────────┘ └─────────┘            │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                                                       │  │
│  │     ┌─ tmux popup ──────────────────────┐            │  │
│  │     │ $ claude                          │            │  │
│  │     │ > Analyzing src/auth.py...        │            │  │
│  │     └───────────────────────────────────┘            │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ omar-agent-ea ─────┐  ┌─ omar-agent-worker1 ────┐      │
│  │ Executive Assistant │  │ claude working...       │      │
│  └─────────────────────┘  └─────────────────────────┘      │
│                                                             │
│  ┌─ HTTP API (:9876) ─────────────────────────────────────┐ │
│  │ REST endpoints for agent spawning, messaging, events   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### Workspace Structure

OMAR is a Rust workspace with 3 crates:

- **`omar`** - Main binary: TUI dashboard, HTTP API, event scheduler
- **`omar-slack-bridge`** - Slack Socket Mode integration
- **`omar-computer-bridge`** - X11 computer use (mouse, keyboard, screenshots)

### Session Types

- **Dashboard**: `omar-dashboard` - the TUI session (auto-created on launch)
- **Executive Assistant**: `omar-agent-ea` - auto-started manager agent
- **Work Agents**: `omar-agent-<name>` - spawned by EA or API

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
├── memory.md                  # Snapshot of active state
├── tasks.md                   # Project list
├── worker_tasks.json          # Agent task assignments
├── agent_parents.json         # Parent-child relationships
├── status/<session>.md        # Agent self-reported status
└── prompts/                   # Synced prompt templates
```

## Configuration

```toml
# ~/.omar/config.toml

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

[api]
enabled = true
host = "127.0.0.1"
port = 9876

[watchdog]
command = ""  # empty = disabled; see "Watchdog" below
slack_channel = ""  # Slack channel ID for alerts
```

Agent backend is auto-detected from installed tools (Claude Code, Codex, Cursor, or Opencode) and can be overridden with `--agent`.

### Watchdog

If a backend's authentication expires (e.g., Claude subscription login), OMAR can auto-detect the outage and spawn a watchdog agent on a free backend to monitor errors and notify the user via Slack. Original agents stay alive and resume when the backend recovers.

**Prerequisites**: [opencode](https://opencode.ai) installed, [OpenRouter](https://openrouter.ai) account connected via `opencode /connect`.

```toml
[watchdog]
# Use OpenRouter's free models router through opencode
command = "opencode --model openrouter/openrouter/free"

# Slack channel ID to send alerts to (optional)
slack_channel = "C0123456789"

# Patterns that trigger the watchdog (case-insensitive, defaults shown)
auth_failure_patterns = [
  "please run /login",
  "401 unauthorized",
]
```

When triggered, OMAR:
1. Detects auth failure patterns in agent pane output
2. Spawns a single watchdog agent to monitor all sessions
3. Watchdog sends Slack alerts and periodically checks agent health
4. Shows a persistent warning banner in the dashboard

No API keys or secrets are passed to the watchdog agent.

## Key Bindings

| Key            | Action                           |
| -------------- | -------------------------------- |
| `↑/↓` or `j/k` | Navigate agents                  |
| `→` or `Tab`   | Drill into child agents          |
| `←`            | Back to parent                   |
| `Enter`        | Attach to agent (tmux popup)     |
| `n`            | Spawn new agent                  |
| `d`            | Delete agent (with confirmation) |
| `p`            | Add project                      |
| `e`            | Show events                      |
| `r`            | Refresh                          |
| `z`            | Detach from tmux                 |
| `D`            | Debug console                    |
| `?`            | Help                             |
| `Q`            | Quit (with confirmation)         |
