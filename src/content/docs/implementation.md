---
title: "Implementation"
description: "OMAR's implementation - tech stack, project structure, and key modules"
order: 3
---

## Tech Stack

| Component   | Choice                   | Rationale                                 |
| ----------- | ------------------------ | ----------------------------------------- |
| Language    | Rust                     | Memory safety, concurrency, single binary |
| TUI         | ratatui 0.29 + crossterm | Active community, performant              |
| Async       | tokio (full)             | Industry standard                         |
| MCP server  | hand-rolled stdio JSON-RPC | Line-delimited and Content-Length, no extra dep |
| CLI         | clap 4 (derive)          | Excellent UX                              |
| Config      | toml + toml_edit + serde | toml_edit preserves sections on partial writes |
| Errors      | anyhow + thiserror       | Ergonomic handling                        |
| Persistence | atomic temp+rename writes | Resilient to crashes mid-write           |

## Project Structure

```
omar/
├── Cargo.toml              # Workspace root (workspace + omar bin)
├── src/
│   ├── main.rs             # Entry point, CLI, tmux relaunching
│   ├── app.rs              # Core state machine, refresh/render
│   ├── config.rs           # Configuration loading + auto-detection
│   ├── ea.rs               # EA registry, id allocation, selector resolution
│   ├── event.rs            # Input/tick event handling
│   ├── memory.rs           # Persistent state management
│   ├── computer.rs         # X11 computer use integration
│   ├── projects.rs         # Project CRUD
│   ├── metrics.rs          # Optional spawn-metrics JSONL sink
│   ├── backend_probe.rs    # Bounded `--version` probe for list_backends
│   ├── process.rs          # PID liveness + stale lock detection
│   ├── panic_hook.rs       # Persisted panic dumps to ~/.omar/logs/panics
│   ├── mcp.rs              # MCP stdio server (JSON-RPC, ~30 typed tools)
│   ├── tmux/
│   │   ├── mod.rs
│   │   ├── client.rs       # tmux command wrapper, deliver_prompt, popup
│   │   └── health.rs       # Health checking, auth-failure detection
│   ├── manager/
│   │   └── mod.rs          # EA session lifecycle, MCP context materialization
│   ├── scheduler/
│   │   ├── mod.rs          # Persistent event scheduling + delivery
│   │   └── event.rs        # ScheduledEvent type + ordering
│   └── ui/
│       ├── mod.rs
│       └── dashboard.rs    # TUI rendering, settings panel
├── bridges/
│   ├── slack/              # Slack bridge (omar-slack)
│   └── computer/           # Computer-use bridge (omar-computer)
├── prompts/                # Embedded prompt templates
└── tests/
    └── integration_test.rs # Black-box CLI + MCP integration tests
```

## Key Modules

### `main.rs`

Entry point with CLI parsing (clap) and the `mcp-server` subcommand. Auto-relaunches inside tmux if not already in a tmux session. Installs the panic hook before tokio's runtime starts so panics on worker threads are persisted to disk.

### `app.rs`

Core application state machine. Manages agent list, selection, focus, projects, and UI state. Each refresh tick re-reads the active EA, agents, parent map, worker tasks, and project list from disk so MCP-driven changes (made by agents through `omar mcp-server`) land live without an explicit IPC channel.

### `mcp.rs`

The MCP stdio server (~2,800 lines). Reads its `McpLaunchContext` (omar dir, EA id, session prefix, default workdir, health window, optional tmux server) at startup and pins all tool calls to that context. Supports both Content-Length and line-delimited framing on stdin/stdout. Tool dispatch in `handle_tool_call` covers EA management, agents, projects, scheduling, computer use, and Slack reply queueing — see the MCP Tool Reference for the canonical list.

### `manager/mod.rs`

Owns the EA tmux session lifecycle. Per backend, it materializes the appropriate MCP integration:

- Claude: `~/.omar/mcp/ea-<id>/claude-mcp.json`, passed as `--mcp-config`.
- Codex: `-c mcp_servers.omar.command=… -c mcp_servers.omar.args=…` overrides.
- Cursor: entry written into `~/.cursor/mcp.json`.
- Gemini: `gemini mcp add -s user omar …` bootstrap on session start.
- Opencode: env var pointing at `omar mcp-server --context-file …`.

The same module enforces argv-level deny rules for backend-native wake / dispatch tools (`ScheduleWakeup`, `TaskReminder`, `task_reminder`, `scheduled_tasks`) so agents always route timing through OMAR's durable scheduler.

### `scheduler/mod.rs`

Event scheduling system using a `BinaryHeap` (min-heap by timestamp). Supports one-shot and recurring events. **Persistent** — all mutations atomically rewrite `~/.omar/scheduled_events.json` so the queue survives restarts. A bounded cross-process lock (with stale-PID reclamation) serializes writes between the dashboard, the manager, and any MCP server child mutating the queue. Delivers events by injecting text into the agent's tmux session via `deliver_prompt` (sentinel-wrapped to survive paste mode).

### `ea.rs`

EA registry, id allocation (monotonic, never reused), and selector resolution. `resolve_or_create_ea_selector` lets `--ea <name>` auto-create a missing EA when given a non-numeric name; numeric ids that don't exist still error because ids are server-assigned.

### `memory.rs` / `projects.rs`

Per-EA snapshots and project CRUD. Writes use atomic temp-file + rename to survive crashes mid-write. Memory and notes are bounded before being inlined into prompts to stay under Linux's 128 KB `MAX_ARG_STRLEN` argv limit.

## CLI Interface

```bash
# Start dashboard (default - auto-detects backend)
omar

# Use specific agent backend
omar --agent opencode

# Auto-create an EA by name and target it
omar --ea Research

# Run the MCP stdio server (used internally by spawned agents and the Slack bridge)
omar mcp-server --context-file ~/.omar/mcp/ea-0/context.json

# Manager subcommand (started automatically by the dashboard)
omar manager start

# Custom config
omar --config ~/.omar/config.toml
```

## Bridges

Both bridges are optional and auto-spawned when their environment is available:

- **Slack Bridge** (`omar-slack`): Spawns if `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN` are set. Spawns its own `omar mcp-server` child and routes inbound Slack messages to OMAR via the `schedule_omar_event` tool. Replies flow back through the `slack_reply` tool, which writes a file into `~/.omar/slack_outbox/` that the bridge polls and posts to Slack. The bridge's target EA is read from `[slack_bridge].active_ea` in `config.toml` and re-checked on every inbound message, so dashboard-side edits land without a restart.
- **Computer Bridge** (`omar-computer`): Spawns if `DISPLAY` is set. Provides X11 mouse/keyboard/screenshot control with exclusive locking per agent.

## Embedded Prompts

Prompts in `/prompts/` are compiled into the binary and synced to `~/.omar/prompts/` on first run:

- `executive-assistant.md` — EA system prompt (gets memory + manager-notes context prepended)
- `agent.md` — Unified agent prompt (injected for all spawned agents)
- `watchdog.md` — Optional auth-failure watchdog
- `prompts/tests/` — End-to-end test scenarios (`project-factory.md`, `binary-tree-127-agents.md`, `flat-100-agents.md`)
- `prompts/demos/` — Demo scenarios (`swarm-15.md`)

`{{EA_ID}}` / `{{EA_NAME}}` placeholders are substituted at launch — for Claude, on disk before `--system-prompt-file` reads them; for inline-prompt backends, via shell expansion at the spawn command.
