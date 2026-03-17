---
title: "HTTP API Reference"
description: "OMAR's REST API for agent orchestration, events, and computer use"
order: 4
---

## Overview

OMAR runs an HTTP API on port 9876 (configurable) for programmatic agent control. Any tool that can make HTTP calls can orchestrate agents - Claude, opencode, Python scripts, curl, etc.

CORS is fully enabled (`Access-Control-Allow-Origin: *`).

## Backend Endpoints

### `GET /api/backends`

List installed agent backends and their availability.

```json
{
  "backends": [
    {
      "name": "claude",
      "command": "claude --dangerously-skip-permissions",
      "available": true
    },
    {
      "name": "codex",
      "command": "codex --no-alt-screen ...",
      "available": true
    },
    { "name": "cursor", "command": "cursor agent --yolo", "available": false },
    { "name": "opencode", "command": "opencode", "available": false }
  ]
}
```

## Agent Endpoints

### `POST /api/agents`

Spawn a new agent. If `task` is provided, the agent receives `agent.md` as its system prompt with the task injected.

```json
// Request
{
  "name": "worker-1",
  "task": "Implement feature X",
  "workdir": "/path/to/project",
  "backend": "codex",
  "model": "o3",
  "parent": "ea"
}

// Response
{
  "id": "worker-1",
  "status": "running",
  "session": "omar-agent-worker-1",
  "created_at": "2025-01-26T12:00:00Z"
}
```

Fields:

- `name` — Agent name (auto-generated if omitted)
- `task` — Task description; triggers `agent.md` prompt injection
- `workdir` — Working directory
- `backend` — Backend shorthand: `"claude"`, `"codex"`, `"cursor"`, `"opencode"`. Cannot be used with `command`.
- `model` — Model override, appended as `--model <value>` to the base command
- `command` — Explicit command to run. Cannot be used with `backend`.
- `parent` — Parent agent name for hierarchy tracking

### `GET /api/agents`

List all agents with health and status.

```json
{
  "agents": [
    {
      "id": "worker-1",
      "status": "running",
      "health": "working",
      "idle_seconds": 5,
      "last_output": "Writing tests..."
    }
  ],
  "manager": {
    "id": "omar-agent-ea",
    "status": "running",
    "health": "working"
  }
}
```

### `GET /api/agents/:id`

Get agent details including recent output tail.

### `GET /api/agents/:id/summary`

Lightweight card view: health, task, status, children.

### `PUT /api/agents/:id/status`

Update an agent's self-reported status (stored in `~/.omar/status/<session>.md`).

```json
{ "status": "Implementing auth module - 60% done" }
```

### `POST /api/agents/:id/send`

Send text input to an agent's tmux session.

```json
{ "text": "Yes, proceed", "enter": true }
```

### `DELETE /api/agents/:id`

Kill an agent session.

**Note:** Session names accept both short form (`worker-1`) and full form (`omar-agent-worker-1`).

## Event Endpoints

### `POST /api/events`

Schedule an event for delivery to an agent.

```json
{
  "sender": "ea",
  "receiver": "worker-1",
  "payload": "Status check: how is the implementation going?",
  "timestamp": 1772904000000000000,
  "recurring_ns": 300000000000
}
```

### `GET /api/events`

List scheduled events. Supports `?receiver=<name>` query filter.

### `DELETE /api/events/:id`

Cancel a scheduled event.

## Project Endpoints

### `GET /api/projects`

List projects from `~/.omar/tasks.md`.

### `POST /api/projects`

Add a new project.

### `DELETE /api/projects/:id`

Complete/remove a project.

## Computer Use Endpoints

### `GET /api/computer/status`

Check if computer use is available and who holds the lock.

### `POST /api/computer/lock`

Acquire exclusive computer access (one agent at a time).

### `DELETE /api/computer/lock`

Release computer lock.

### `POST /api/computer/screenshot`

Take a screenshot (must hold lock). Returns base64-encoded image.

### `POST /api/computer/mouse`

Mouse control: move, click, drag, scroll.

### `POST /api/computer/keyboard`

Keyboard input: type text or press key combinations.

### `GET /api/computer/screen-size`

Get display dimensions.

### `GET /api/computer/mouse-position`

Get current cursor position.

## System Endpoints

### `GET /api/health`

Health check.

```json
{ "status": "ok", "version": "0.1.0" }
```

## Configuration

```toml
# ~/.config/omar/config.toml
[api]
enabled = true
port = 9876
host = "127.0.0.1"
```

## Usage Examples

```bash
# Spawn a worker
curl -X POST http://localhost:9876/api/agents \
  -H "Content-Type: application/json" \
  -d '{"name": "auth", "task": "Implement JWT auth", "parent": "ea"}'

# Check status
curl http://localhost:9876/api/agents/auth

# Send input
curl -X POST http://localhost:9876/api/agents/auth/send \
  -H "Content-Type: application/json" \
  -d '{"text": "y", "enter": true}'

# Schedule recurring status check
curl -X POST http://localhost:9876/api/events \
  -H "Content-Type: application/json" \
  -d '{"sender": "ea", "receiver": "auth", "payload": "Status?", "recurring_ns": 300000000000}'

# Kill agent
curl -X DELETE http://localhost:9876/api/agents/auth
```
