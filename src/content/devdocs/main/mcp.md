---
title: "MCP interfaces"
order: 4
---

## Server and launch context

[src/mcp.rs](https://github.com/omar-os/omar/blob/main/src/mcp.rs) implements a JSON-RPC MCP server over standard input/output. It handles `initialize`, `tools/list`, and `tools/call`; tool definitions beside the dispatch code specify argument schemas.

[McpLaunchContext](https://github.com/omar-os/omar/blob/main/src/manager/mod.rs) carries the runtime directory, EA ID, agent identity, launch defaults, and optional topology or HTTP callback context. The manager builds backend launch commands and materializes embedded assistant/worker prompts from [prompts](https://github.com/omar-os/omar/tree/main/prompts).

The exposed tools depend on this context. The call dispatcher enforces scope as well as filtering the advertised list.

## Assistant and worker coordination

General tools cover agent spawning and inspection, task coordination, projects, messages, scheduled events, and computer access. EA memory tools are added for the executive assistant. When HTTP callback context is present, the server also exposes:

- `omar_reply`: send operator-visible text or progress.
- `omar_propose_design`: submit source, companion files, inputs, and optional properties for review. This does not start a run.
- `omar_check_properties`: check Lean properties without submitting a proposal.

Use the definitions in `mcp.rs` for exact signatures and result formats. The hold-mode server restricts its tool set and supports waiting for worker results through `wait_s`.

## Workflow invocation protocol

A topology-scoped agent receives only these tools (the server can also expose bare names):

```text
omar_pending()
omar_set_port(task_id, port, value)
omar_set_state(task_id, name, value)
omar_complete(task_id, keep?)
```

`task_id` is an integer identifying a runtime invocation. `omar_pending` recovers outstanding tasks addressed to that agent. Port writes must belong to the invocation's allowed effects; state writes target its team's state. Repeated writes replace earlier buffered values.

Completion validates the final effect snapshot and releases the runtime barrier. Each shared context supplied to the task must be updated or explicitly listed in `keep`. Expired or failed invocations do not retain buffered state writes.

The receiving invocation registry and ownership/type checks live in [src/topology.rs](https://github.com/omar-os/omar/blob/main/src/topology.rs). This boundary turns an agent's tool calls into values the workflow runtime can accept.
