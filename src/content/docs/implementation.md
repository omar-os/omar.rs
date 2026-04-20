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
| MCP       | rmcp                     | Native MCP stdio server for agent tools   |
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
│   ├── mcp.rs              # MCP stdio server: all agent-facing tools
│   ├── tasks.rs            # Task registry (task_registry.json)
│   ├── computer.rs         # X11 computer use integration
│   ├── projects.rs         # Project CRUD
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

### mcp.rs

MCP stdio server implementing all agent-facing tools: `create_task`, `check_task`, `complete_task`, `replace_stuck_task_agent`, `spawn_agent_session`, `kill_agent`, `send_input`, `notify_parent`, `schedule_event`, `log_action`, `append_manager_note`, `get_agent_summary`, `list_backends`, and more. Each spawned agent gets its own server instance with a context file scoped to its EA. Tools are function-call definitions outside the LLM context window — agents always see the full catalog regardless of conversation length.

### scheduler/mod.rs

Event scheduling system using a BinaryHeap (min-heap by timestamp). Supports one-shot and recurring events. Delivers events by injecting text into agent tmux sessions via `send-keys`. Thread-safe with `Arc<Mutex<>>`.

### memory.rs

Persistent state snapshots. Writes active state (projects, agents, tasks) to `~/.omar/memory.md`. This gets injected into the EA prompt on startup for context continuity.

## CLI Interface

```bash
# Start dashboard (default)
omar
omar --agent opencode          # override default backend
omar --ea 1                    # target EA by ID or name
omar --config ~/.config/omar/config.toml

# Agent management
omar spawn <name>              # spawn a named agent
omar list                      # list agents for active EA
omar list --all-eas            # list agents across all EAs
omar kill <name>               # kill an agent

# Event scheduling
omar event schedule --receiver <name> --payload "..." --delay-seconds 60
omar event list
omar event cancel <id>

# Setup
omar setup-tmux                # configure tmux for OMAR

# Internal (used by the runtime, not by users directly)
omar mcp-server --context-file <path>   # start MCP stdio server for an agent
omar manager start                       # start EA manager session
```

## Bridges

Both bridges are optional and auto-spawned when their environment is available:

- **Slack Bridge**: Spawns if `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN` are set. Routes Slack messages to OMAR agents via MCP tools.
- **Computer Bridge**: Spawns if `DISPLAY` is set. Provides X11 mouse/keyboard/screenshot control with exclusive locking per agent.

## Embedded Prompts

Prompts in `/prompts/` are compiled into the binary and synced to `~/.omar/prompts/` on first run:

- `executive-assistant.md` - EA system prompt (gets memory context prepended)
- `agent.md` - Unified agent prompt (injected for all spawned agents)
- `prompts/tests/` - Test scenarios like `project-factory.md`
