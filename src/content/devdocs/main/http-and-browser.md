---
title: "HTTP and browser"
order: 3
---

## Long-lived admission

[src/serve.rs](https://github.com/omar-os/omar/blob/main/src/serve.rs) implements `Serve`: it accepts programs, compiles them, supervises runs on worker threads, and keeps run records. It outlives individual runs. Each run also has a diagram server, implemented in [src/diagram.rs](https://github.com/omar-os/omar/blob/main/src/diagram.rs).

The HTTP implementation uses TCP streams and blocking connection handlers. Request/response structs and route dispatch in `serve.rs` are the source of truth for payloads.

## Route families

| Route                                                 | Purpose                                            |
| ----------------------------------------------------- | -------------------------------------------------- |
| `GET /health`                                         | Runtime health and protocol information            |
| `POST /v1/runs`                                       | Admit source and inputs as a run                   |
| `GET /v1/runs`, `GET /v1/runs/{id}`                   | List runs or read a run record                     |
| `POST /v1/runs/{id}/pause`, `/resume`, `/stop`        | Control execution                                  |
| `GET /v1/runs/{id}/program`, `/snapshot`, `/timeline` | Inspect source and execution                       |
| `GET /v1/runs/{id}/checkpoints`                       | Inspect recovery points                            |
| `POST /v1/runs/{id}/rollback`, `/mutate`              | Restore or change a run                            |
| `/v1/chat`, `/v1/chats`                               | Messages and conversation lifecycle                |
| `/v1/workspaces`                                      | Saved workflow drafts and properties               |
| `POST /v1/programs/check`, `/v1/properties/check`     | Compile or check properties without starting a run |

Run diagram traffic is relayed through `/v1/runs/{id}/diagram`. Chat updates use the event stream at `GET /v1/chat/events`. Agent terminals use WebSocket routes under `/v1/agents/{name}/terminal`.

The full listener binds loopback. An optional view listener serves unauthenticated read-only access; its route restrictions are enforced by `view_refusal`. EA callback routes such as `/v1/agent/reply` resolve their conversation through a token in the request body.

## Browser contract

[runtime-client.ts](https://github.com/omar-os/omar/blob/main/web/app/lib/runtime-client.ts) implements browser requests and terminal URLs. [protocol.ts](https://github.com/omar-os/omar/blob/main/web/app/lib/protocol.ts) contains protocol handling; [protocol-generated.ts](https://github.com/omar-os/omar/blob/main/web/app/lib/protocol-generated.ts) contains generated Rust wire types and runtime vocabularies.

[src/protocol.rs](https://github.com/omar-os/omar/blob/main/src/protocol.rs) generates the TypeScript contract under Rust tests and checks that the committed output matches. Change the Rust wire definitions when changing shared types.

The standalone browser entry is [web/spa/main.tsx](https://github.com/omar-os/omar/blob/main/web/spa/main.tsx). The optional Cargo `ui` feature embeds the prebuilt `web/dist/spa` bundle through [src/web_assets.rs](https://github.com/omar-os/omar/blob/main/src/web_assets.rs); a plain Rust build does not require Node. Build commands live in [web/package.json](https://github.com/omar-os/omar/blob/main/web/package.json).
