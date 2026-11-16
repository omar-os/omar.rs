---
title: "Codebase overview"
order: 1
---

## The main parts

OMAR runs agent processes and coordinates their work. The Rust `omar` binary owns runtime sessions, launches backends, serves HTTP, and renders the terminal dashboard. A separate Lean executable, `omarc`, compiles `.omar` programs into JSON bytecode for the Rust runtime.

| Part                                   | Start reading here                                                                                                                                             |
| -------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CLI dispatch and terminal entry point  | [src/omar.rs](https://github.com/omar-os/omar/blob/main/src/omar.rs)                                                                                           |
| Session ownership and control socket   | [src/sessions.rs](https://github.com/omar-os/omar/blob/main/src/sessions.rs)                                                                                   |
| HTTP admission and Mission Control API | [src/serve.rs](https://github.com/omar-os/omar/blob/main/src/serve.rs)                                                                                         |
| Compiler                               | [lang/Main.lean](https://github.com/omar-os/omar/blob/main/lang/Main.lean), [Omar.Compiler](https://github.com/omar-os/omar/blob/main/lang/Omar/Compiler.lean) |
| Bytecode, VM, and workflow execution   | [src/topology.rs](https://github.com/omar-os/omar/blob/main/src/topology.rs)                                                                                   |
| Agent tool server                      | [src/mcp.rs](https://github.com/omar-os/omar/blob/main/src/mcp.rs)                                                                                             |
| Backend adapters                       | [src/backend](https://github.com/omar-os/omar/tree/main/src/backend)                                                                                           |
| Browser client                         | [web](https://github.com/omar-os/omar/tree/main/web)                                                                                                           |

## Ownership and execution

A runtime session has its own daemon, state directory, control socket, and tmux server. Within it, an executive assistant (EA) owns a namespace of agents, projects, memory, and scheduled events. A session can contain several EAs.

There are two paths for coordinating work:

- An assistant uses MCP tools to spawn workers, send messages, and track tasks.
- A compiled `.omar` program defines teams, ports, connections, reactions, and timers. The runtime decides which reactions run and validates their results.

Both paths use the backend adapters to launch and communicate with agents. The terminal dashboard and browser are interfaces to this machinery; the session daemon owns the background runtime.

## Reading path

Start with [sessions and CLI](sessions-and-cli.md), then [HTTP and browser](http-and-browser.md) and [MCP](mcp.md). For workflow execution, read [compiler and bytecode](compiler-and-bytecode.md), [runtime](runtime.md), and [state and recovery](state-and-recovery.md). [Backends and tests](backends-and-tests.md) points to extension points and validation.
