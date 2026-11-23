---
title: "Backends and tests"
order: 8
---

## Backend boundary

[src/backend/mod.rs](https://github.com/omar-os/omar/blob/043fda0feda519bb48af18307984776d668720e3/src/backend/mod.rs) defines the `Backend` trait and registry. Adapter files implement command detection, launch preparation, readiness, delivery, and conversation handling. Start here when adding a backend or changing an agent launch contract.

[src/manager/mod.rs](https://github.com/omar-os/omar/blob/043fda0feda519bb48af18307984776d668720e3/src/manager/mod.rs) combines prompts and MCP launch context with backend launch commands. [src/tmux/client.rs](https://github.com/omar-os/omar/blob/043fda0feda519bb48af18307984776d668720e3/src/tmux/client.rs) supplies tmux operations; [src/backend_runner.rs](https://github.com/omar-os/omar/blob/043fda0feda519bb48af18307984776d668720e3/src/backend_runner.rs) supports managed backend execution.

Delivery follows the transport recorded at launch: managed runner sockets, hook spools, or backend-specific channels such as the Codex app server and opencode HTTP API. Readiness failures can return `NotReady` for retry before sending. The registry's delivery code reports channel failures without falling back to typing into the terminal composer.

[src/backend/connect.rs](https://github.com/omar-os/omar/blob/043fda0feda519bb48af18307984776d668720e3/src/backend/connect.rs) and [src/backend/connection.rs](https://github.com/omar-os/omar/blob/043fda0feda519bb48af18307984776d668720e3/src/backend/connection.rs) manage backend connection/setup state. The deterministic [stub backend](https://github.com/omar-os/omar/blob/043fda0feda519bb48af18307984776d668720e3/src/backend/stub.rs) supports tests without a live model.

## Where behavior is tested

| Layer                                                  | Tests                                                                                                                                                            |
| ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Rust data structures, VM, routes, tool scope, delivery | Inline `#[cfg(test)]` modules beside implementation                                                                                                              |
| CLI and tmux sessions                                  | [tests/integration_test.rs](https://github.com/omar-os/omar/blob/043fda0feda519bb48af18307984776d668720e3/tests/integration_test.rs)                                                                 |
| Compiler                                               | [lang/Tests.lean](https://github.com/omar-os/omar/blob/043fda0feda519bb48af18307984776d668720e3/lang/Tests.lean)                                                                                     |
| Runtime contracts and recovery                         | [tests/ci](https://github.com/omar-os/omar/tree/043fda0feda519bb48af18307984776d668720e3/tests/ci)                                                                                                   |
| Workflow fixtures                                      | [tests/topology](https://github.com/omar-os/omar/tree/043fda0feda519bb48af18307984776d668720e3/tests/topology)                                                                                       |
| Browser protocol, rendering, and end-to-end behavior   | [web/tests](https://github.com/omar-os/omar/tree/043fda0feda519bb48af18307984776d668720e3/web/tests), [web/playwright.config.ts](https://github.com/omar-os/omar/blob/043fda0feda519bb48af18307984776d668720e3/web/playwright.config.ts) |
| Pi adapter JavaScript                                  | [src/backend/pi/test](https://github.com/omar-os/omar/tree/043fda0feda519bb48af18307984776d668720e3/src/backend/pi/test)                                                                             |

Integration tests create temporary homes and runtime sessions with dedicated tmux servers. They require tmux. Compiler and workflow tests also need the Lean toolchain; fixtures and test scripts show which compiler path or backend each test expects.

## Build and validation entry points

The Rust package declares a minimum Rust version of 1.89 in [Cargo.toml](https://github.com/omar-os/omar/blob/043fda0feda519bb48af18307984776d668720e3/Cargo.toml). Lean targets and the test driver are in [lang/lakefile.lean](https://github.com/omar-os/omar/blob/043fda0feda519bb48af18307984776d668720e3/lang/lakefile.lean); the Lean version is pinned in [lang/lean-toolchain](https://github.com/omar-os/omar/blob/043fda0feda519bb48af18307984776d668720e3/lang/lean-toolchain).

```sh
cargo check --all-targets
cargo fmt --all -- --check
cargo clippy --all-targets -- -D warnings
cargo test -- --test-threads=1
```

From `lang/`, `lake build` builds the compiler/library and `lake test` runs the compiler tests. Browser scripts are in [web/package.json](https://github.com/omar-os/omar/blob/043fda0feda519bb48af18307984776d668720e3/web/package.json), including `build:spa`, `test`, and `test:e2e`.

Use [CI workflows](https://github.com/omar-os/omar/tree/043fda0feda519bb48af18307984776d668720e3/.github/workflows) for the exact toolchain setup and test matrix. Rust tests also check that the generated browser protocol matches the committed TypeScript.
