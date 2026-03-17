---
title: "Introducing OMAR"
description: "A TUI for creating powerful agentic organizations, built on Rust and tmux."
date: "2026-03-07"
author: "OMAR Team"
---

We're introducing **OMAR** (one-man army) — a TUI for creating powerful agentic organizations.

## Why OMAR?

AI coding agents are powerful individually, but real-world projects need teams. You need agents that can work in parallel, specialize in different areas, and coordinate — just like a company.

OMAR gives you a terminal dashboard to orchestrate all of this from one place.

## What Can You Do?

- **Deep hierarchies** — Create parallel organizations with managers and workers, to any depth
- **Heterogeneous backends** — Let Claude, Codex, Cursor, and Opencode collaborate as a team
- **Full control** — Navigate to any agent at any level and interact directly
- **Integrations** — Connect agents to Slack channels or give them computer use capabilities
- **Event-driven coordination** — Schedule status checks, handoffs, and reminders between agents

## How It Works

OMAR runs on tmux. Each agent gets its own tmux session, and OMAR's TUI dashboard monitors them all. You start with an Executive Assistant (EA), give it a high-level task, and watch as it spawns worker agents in parallel.

```bash
$ curl -fsSL https://omarmy.ai/install.sh | sh
$ omar
```

Navigate with arrow keys. Drill into agent hierarchies. Attach to any agent via popup. Keyboard-driven and fast.

## Built With

- **Rust** — Fast, safe, single binary
- **ratatui** — TUI framework
- **tmux** — Battle-tested session management
- **HTTP API** — Agent-agnostic orchestration on port 9876

## Supported Backends

| Backend                                                                                 | How to launch                   |
| --------------------------------------------------------------------------------------- | ------------------------------- |
| [Claude Code](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview) | `omar` or `omar --agent claude` |
| [Codex CLI](https://developers.openai.com/codex/cli)                                    | `omar --agent codex`            |
| [Opencode](https://github.com/anomalyco/opencode)                                       | `omar --agent opencode`         |
| [Cursor CLI](https://cursor.com/cli)                                                    | `omar --agent cursor`           |

Check out the [docs](/docs/) to get started, and join our [Discord](https://discord.gg/X76PSzmfWr) to connect with the community.
