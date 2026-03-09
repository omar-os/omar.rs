---
title: "Introducing OMAR"
description: "Meet OMAR - a TUI for creating powerful agentic organizations, built on Rust and tmux."
date: "2026-03-07"
author: "OMAR Team"
---

We're excited to introduce **OMAR** (one-man army) - a TUI for creating powerful agentic organizations.

## Why OMAR?

AI coding agents are powerful individually, but real-world projects need teams. You need agents that can work in parallel, specialize in different areas, and coordinate their work - just like a company.

OMAR gives you a professional terminal dashboard to orchestrate all of this from one place.

## What Can You Do?

- **Spawn hierarchies of agents** - Create deep, parallel organizations with managers and workers
- **Monitor everything** - See health status, idle time, and last output for every agent at a glance
- **Stay in control** - Navigate to any agent at any level and interact directly
- **Integrate with tools** - Connect agents to Slack channels or give them computer use capabilities

## How It Works

OMAR runs on tmux. Each agent gets its own tmux session, and OMAR's TUI dashboard monitors them all. You start with an executive assistant (EA), give it a high-level task, and watch as it spawns worker agents to tackle the problem in parallel.

```bash
$ make install
$ omar
```

Navigate with arrow keys. Drill into agent hierarchies. Attach to any agent via popup. It's all keyboard-driven and fast.

## Built With

- **Rust** - Fast, safe, single binary
- **ratatui** - Beautiful TUI framework
- **tmux** - Battle-tested session management
- **HTTP API** - Agent-agnostic orchestration on port 9876

## What's Next

We're working on:

- More agent backends beyond Claude Code and Opencode
- Enhanced manager-worker orchestration protocols
- Distribution via Homebrew, AUR, and Nix
- Computer use improvements

Check out the [docs](/docs/) to get started, and join our [Discord](https://discord.gg/X76PSzmfWr) to connect with the community.

Star us on [GitHub](https://github.com/lsk567/omar) if you find OMAR useful!
