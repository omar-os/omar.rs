---
title: "Workflow runtime"
order: 6
---

## VM and execution loop

[src/topology.rs](https://github.com/omar-os/omar/blob/main/src/topology.rs) contains bytecode validation, `VmState`, invocation handling, deployment, and the execution loop. It is the central file for following a compiled workflow.

The VM records agents, instances, typed ports, connections, state, timers, and reactions. Execution advances through ordered tags: `(timestamp, microstep)`. Timestamps use nanoseconds; microsteps order work at the same logical time.

Plain connections propagate within a tag. `after 0` introduces a microstep; positive delays advance time. Timers enqueue future triggers. The runtime normally paces logical time against elapsed time; `--fast` removes that wait.

For a tag, the runtime propagates events and runs triggered reactions. Agent invocations must finish before the tag completes. Future delayed work goes onto the queue. The diagram observer receives execution updates.

## Two reaction implementations

Agent tasks become prompts delivered through a backend. An invocation records trigger values, permitted effects, and team state. The agent buffers writes through MCP and completes the invocation; the runtime validates those writes before accepting them.

Native Rust bodies use [src/reaction.rs](https://github.com/omar-os/omar/blob/main/src/reaction.rs). It generates a crate, builds an executable with Cargo, and invokes that executable with a line-based input/output protocol. Rust bodies are captured by the Lean compiler as source; Cargo compiles them.

`OMAR_CARGO` selects the Cargo executable. By default, the runtime tries `cargo` on `PATH`, then `$CARGO_HOME/bin/cargo` if configured, then `~/.cargo/bin/cargo`. Only a missing executable advances the search.

Shared contexts are string state associated with selected agents. Their values and directives are included in task context, and completion requires an update or explicit preservation.

## Control and observation

[src/deploy.rs](https://github.com/omar-os/omar/blob/main/src/deploy.rs) defines deployment lifecycle states and control operations. A pause takes effect at a tag boundary and produces a durable checkpoint. The runner exits; resume starts a new runner from that checkpoint.

[src/diagram.rs](https://github.com/omar-os/omar/blob/main/src/diagram.rs) defines snapshots, events, and the observer interface used by diagram clients. [src/serve.rs](https://github.com/omar-os/omar/blob/main/src/serve.rs) maintains the externally visible run record and relays diagram requests.

For persistence, mutation, and the distinction between file snapshots and runtime checkpoints, continue to [state and recovery](state-and-recovery.md).
