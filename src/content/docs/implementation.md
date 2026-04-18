---
title: "Implementation"
description: "OMAR's implementation - tech stack, project structure, and key modules"
order: 3
---

## Tech Stack

| Component | Choice                   | Rationale                                 |
| --------- | ------------------------ | ----------------------------------------- |
| Language  | Rust                     | Memory safety, concurrency, single binary |
| TUI       | ratatui 0.29 + crossterm | Active community, performant              |
| Async     | tokio (full)             | Industry standard                         |
| HTTP      | axum 0.7                 | Ergonomic, tower-based                    |
| CLI       | clap 4 (derive)          | Excellent UX                              |
| Config    | toml + serde             | Native Rust support                       |
| Errors    | anyhow + thiserror       | Ergonomic handling                        |

## Project Structure

```
omar/
├── Cargo.toml              # Workspace root
├── src/
│   ├── main.rs             # Entry point, CLI, tmux relaunching
│   ├── app.rs              # Core state machine, refresh/render
│   ├── config.rs           # Configuration loading + auto-detection
│   ├── event.rs            # Input/tick event handling
│   ├── memory.rs           # Persistent state management
│   ├── computer.rs         # X11 computer use integration
│   ├── projects.rs         # Project CRUD
│   ├── api/
│   │   ├── mod.rs          # Router setup
│   │   ├── handlers.rs     # HTTP API endpoints (axum)
│   │   └── models.rs       # Request/response types
│   ├── tmux/
│   │   ├── mod.rs          # Module root
│   │   ├── client.rs       # tmux command wrapper
│   │   ├── session.rs      # Session types
│   │   └── health.rs       # Health checking
│   ├── manager/
│   │   └── mod.rs          # EA session lifecycle
│   ├── scheduler/
│   │   ├── mod.rs          # Event scheduling + delivery
│   │   └── event.rs        # ScheduledEvent type + ordering
│   └── ui/
│       ├── mod.rs          # Module root
│       └── dashboard.rs    # TUI rendering
├── bridges/
│   ├── omar-slack-bridge/  # Slack bridge crate
│   └── omar-computer-bridge/ # Computer use bridge crate
└── prompts/                # Embedded prompt templates
```

## Key Modules

### main.rs (~833 lines)

Entry point with CLI parsing (clap). Auto-relaunches inside tmux if not already in a tmux session. Manages daemon lifecycle, bridge auto-spawning, and graceful shutdown (SIGTERM then SIGKILL).

### app.rs (~1,460 lines)

Core application state machine. Manages agent list, selection, focus, projects, and UI state. Handles refresh cycles that poll tmux for session updates. Builds the hierarchical command tree for agent visualization.

### api/handlers.rs (~1,039 lines)

Full REST API on axum with CORS. Endpoints for agent CRUD (with `backend` and `model` fields for heterogeneous spawning), event scheduling, computer use, and project management. Supports session name normalization (short names like "auth" resolve to "omar-agent-auth").

### scheduler/mod.rs

Event scheduling system using a BinaryHeap (min-heap by timestamp). Supports one-shot and recurring events. Delivers events by injecting text into agent tmux sessions via `send-keys`. Thread-safe with `Arc<Mutex<>>`.

### memory.rs

Persistent state snapshots. Writes active state (projects, agents, tasks) to `~/.omar/memory.md`. This gets injected into the EA prompt on startup for context continuity.

## CLI Interface

```bash
# Start dashboard (default - auto-detects backend)
omar

# Use specific agent backend
omar --agent opencode

# Custom config
omar --config ~/.config/omar/config.toml

# Spawn a new agent
omar spawn --name my-agent --command "claude"

# List agents (non-TUI)
omar list

# Kill an agent
omar kill agent-1

# Start executive assistant
omar manager start

# Setup tmux configuration
omar setup-tmux
```

## Auto-Detection

On startup, OMAR auto-detects available agent backends:

1. Checks for `claude` in PATH → `claude --dangerously-skip-permissions`
2. Falls back to `codex` → `codex --no-alt-screen --dangerously-bypass-approvals-and-sandbox`
3. Falls back to `cursor` → `cursor agent --yolo`
4. Falls back to `gemini` → `gemini --yolo`
5. Falls back to `opencode`
6. Override with `--agent <name>` (supports: claude, codex, cursor, gemini, opencode)

## Bridges

Both bridges are optional and auto-spawned when their environment is available:

- **Slack Bridge**: Spawns if `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN` are set. Routes Slack messages to OMAR agents via the API.
- **Computer Bridge**: Spawns if `DISPLAY` is set. Provides X11 mouse/keyboard/screenshot control with exclusive locking per agent.

## Embedded Prompts

Prompts in `/prompts/` are compiled into the binary and synced to `~/.omar/prompts/` on first run:

- `executive-assistant.md` - EA system prompt (gets memory context prepended)
- `agent.md` - Unified agent prompt (injected for all spawned agents)
- `prompts/tests/` - Test scenarios like `project-factory.md`
