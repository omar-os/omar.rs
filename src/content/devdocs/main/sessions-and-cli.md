---
title: "Sessions and CLI"
order: 2
---

## CLI boundary

[Commands in src/omar.rs](https://github.com/omar-os/omar/blob/main/src/omar.rs) defines the Clap command tree and dispatch. Global `--session` selects a runtime, `--ea` selects an assistant inside it, and `--json` requests structured command results.

The session-facing commands are implemented in [src/sessions.rs](https://github.com/omar-os/omar/blob/main/src/sessions.rs):

| Commands                       | Responsibility                                                  |
| ------------------------------ | --------------------------------------------------------------- |
| `up`, `serve`                  | Start or restart a runtime; foreground/background startup paths |
| `ls`, `info`, `logs`           | Discover and inspect runtimes                                   |
| `attach --tui`, `attach --web` | Open a runtime interface                                        |
| `run`, `runs`                  | Submit a program and inspect runs                               |
| `ea`                           | Manage assistants and their events                              |
| `down`                         | Pause workflows and stop the runtime                            |
| `rm`                           | Remove a runtime and its state                                  |

Follow the command enum for the remaining agent, workspace, checkpoint, and backend commands rather than treating this table as a full CLI reference.

`omar run` reads source and imported files before creating a scratch session. When no runtime is selected, it creates a session for that run and cleans it up on failed admission or when a foreground run completes, stops, or fails. A paused run keeps its session.

`omar messaging slack` dispatches to the standalone connector before session command handling. The connector communicates with the runtime through the [messaging HTTP interface](http-and-browser.md#messaging-and-workflow-review). See [src/messaging/mod.rs](https://github.com/omar-os/omar/blob/main/src/messaging/mod.rs).

## Daemon ownership

The session registry lives under `OMAR_HOME` (default `~/.omar`). `Session` records the name, process, state directory, socket, executable/build identity, tmux server, and HTTP URL. `OMAR_STATE_DIR` selects the runtime state root.

The hidden `session-daemon` command reads its private `launch.json`, loads configuration, recovers EA lifecycle state, starts `Serve`, and owns one scheduled-event delivery loop. The loop remains available without a dashboard client.

The Unix control socket accepts JSON requests with `protocol`, `id`, `incarnation`, and `operation`. The daemon checks all three identity fields before executing the operation. Responses identify the session and contain either `result` or `error`. A restarted session receives a new incarnation, preventing a stale client from addressing it as the old process.

## Assistant scope and terminal UI

[src/ea.rs](https://github.com/omar-os/omar/blob/main/src/ea.rs) defines EA IDs, registry entries, and scoped tmux names. [src/ea_lifecycle.rs](https://github.com/omar-os/omar/blob/main/src/ea_lifecycle.rs) handles lifecycle admission and recovery.

[src/app.rs](https://github.com/omar-os/omar/blob/main/src/app.rs) holds terminal application state; [src/ui/dashboard.rs](https://github.com/omar-os/omar/blob/main/src/ui/dashboard.rs) renders it. Tmux operations live in [src/tmux](https://github.com/omar-os/omar/tree/main/src/tmux). Persistent scheduled events and delivery belong to [src/scheduler](https://github.com/omar-os/omar/tree/main/src/scheduler), separate from the workflow runtime's logical timers.
