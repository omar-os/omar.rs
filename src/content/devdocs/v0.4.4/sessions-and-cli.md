---
title: "Sessions and CLI"
order: 2
---

## CLI boundary

[Commands in src/omar.rs](https://github.com/omar-os/omar/blob/043fda0feda519bb48af18307984776d668720e3/src/omar.rs) defines the Clap command tree and dispatch. Global `--session` selects a runtime, `--ea` selects an assistant inside it, and `--json` requests structured command results.

The session-facing commands are implemented in [src/sessions.rs](https://github.com/omar-os/omar/blob/043fda0feda519bb48af18307984776d668720e3/src/sessions.rs):

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

## Daemon ownership

The session registry lives under `OMAR_HOME` (default `~/.omar`). `Session` records the name, process, state directory, socket, executable/build identity, tmux server, and HTTP URL. `OMAR_STATE_DIR` selects the runtime state root.

The hidden `session-daemon` command reads its private `launch.json`, loads configuration, recovers EA lifecycle state, starts `Serve`, and owns one scheduled-event delivery loop. The loop remains available without a dashboard client.

The Unix control socket accepts JSON requests with `protocol`, `id`, `incarnation`, and `operation`. The daemon checks all three identity fields before executing the operation. Responses identify the session and contain either `result` or `error`. A restarted session receives a new incarnation, preventing a stale client from addressing it as the old process.

## Assistant scope and terminal UI

[src/ea.rs](https://github.com/omar-os/omar/blob/043fda0feda519bb48af18307984776d668720e3/src/ea.rs) defines EA IDs, registry entries, and scoped tmux names. [src/ea_lifecycle.rs](https://github.com/omar-os/omar/blob/043fda0feda519bb48af18307984776d668720e3/src/ea_lifecycle.rs) handles lifecycle admission and recovery.

[src/app.rs](https://github.com/omar-os/omar/blob/043fda0feda519bb48af18307984776d668720e3/src/app.rs) holds terminal application state; [src/ui/dashboard.rs](https://github.com/omar-os/omar/blob/043fda0feda519bb48af18307984776d668720e3/src/ui/dashboard.rs) renders it. Tmux operations live in [src/tmux](https://github.com/omar-os/omar/tree/043fda0feda519bb48af18307984776d668720e3/src/tmux). Persistent scheduled events and delivery belong to [src/scheduler](https://github.com/omar-os/omar/tree/043fda0feda519bb48af18307984776d668720e3/src/scheduler), separate from the workflow runtime's logical timers.
