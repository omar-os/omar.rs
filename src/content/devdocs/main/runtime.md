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

The Lean compiler captures native Rust bodies as source. [src/reaction.rs](https://github.com/omar-os/omar/blob/main/src/reaction.rs) generates a crate, builds it offline with Cargo, and invokes the executable with a line-based input/output protocol.

`OMAR_CARGO` selects the executable. Without it, the builder tries `cargo` on `PATH`, then `$CARGO_HOME/bin/cargo` if set, then `~/.cargo/bin/cargo`. It advances to the next candidate only if launching Cargo returns a file-not-found error.

Shared contexts are string state associated with selected agents. Their values and directives are included in task context, and completion requires an update or explicit preservation.

## Agent conversations

An agent normally uses one conversation for a run. A `per task`, `per tag`, `per N tasks`, or `per N tags` lifetime tells the runtime when to start a fresh conversation. Tag lifetimes count only tags in which that agent runs. Invocations for the same agent in a tag run sequentially, in declaration order, when the agent has a lifetime.

The first invocation in each window starts a worker. The runtime verifies its conversation before delivery and checks it again before releasing the invocation's effects. The runtime confirms that a retiring worker has stopped before starting its replacement. Each new worker inherits the same instance workspace, and workflow state carries forward across windows. Jev handles invocations as independent requests without a worker or conversation. Runs with agent lifetimes require unsandboxed execution. See [the lifetime contract](https://github.com/omar-os/omar/blob/main/lang/spec.md).

## Control and observation

[src/deploy.rs](https://github.com/omar-os/omar/blob/main/src/deploy.rs) defines deployment lifecycle states and control operations. A pause takes effect at a tag boundary and produces a durable checkpoint. The runner exits; resume starts a new runner from that checkpoint.

[src/diagram.rs](https://github.com/omar-os/omar/blob/main/src/diagram.rs) defines snapshots, events, and the observer interface used by diagram clients. [src/serve.rs](https://github.com/omar-os/omar/blob/main/src/serve.rs) maintains the externally visible run record and relays diagram requests.

The run logs worker windows to `attempts.jsonl`. Diagram snapshots include agent lifetimes and the latest record for each window. An `agent_attempt` event updates a window by attempt ID. See [the diagram publisher](https://github.com/omar-os/omar/blob/main/src/diagram.rs).

For persistence, mutation, and the distinction between file snapshots and runtime checkpoints, continue to [state and recovery](state-and-recovery.md).
