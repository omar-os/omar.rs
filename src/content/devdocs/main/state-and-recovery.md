---
title: "State and recovery"
order: 7
---

## Workspaces and checkpoints

Three mechanisms preserve different parts of a run:

| Mechanism          | What it preserves                                                                                  | Implementation                                                                   |
| ------------------ | -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Workspace snapshot | An instance's files as a Git commit                                                                | [src/workspace.rs](https://github.com/omar-os/omar/blob/main/src/workspace.rs)   |
| Runtime checkpoint | Completed tag, future queue, outputs, state, elapsed logical time, program, and workspace versions | [src/checkpoint.rs](https://github.com/omar-os/omar/blob/main/src/checkpoint.rs) |
| Deployment record  | Run identity and lifecycle                                                                         | [src/deploy.rs](https://github.com/omar-os/omar/blob/main/src/deploy.rs)         |

A workspace is a per-instance working directory with immutable Git-backed snapshots. File versioning alone does not capture execution state.

Checkpoints are captured at completed tag boundaries, when no invocation is in flight. Queued tags include their payloads. Workspace contents stay in Git history; the checkpoint references their versions. Publication stages, validates, fsyncs, and renames the checkpoint so a partial directory is not advertised as complete.

The default automatic checkpoint period is one physical hour. Policy can instead follow logical time or every tag, or disable periodic capture. Pause still captures a recovery point.

## Resume and rollback

Recovery code in [src/topology.rs](https://github.com/omar-os/omar/blob/main/src/topology.rs) restores the execution queue, state, source, and workspace versions. Agents start fresh conversations on resume. Logical elapsed time excludes pauses, so a later tag waits its remaining interval rather than treating paused wall time as runtime progress.

Rollback selects an earlier checkpoint, including its program. This can undo a subsequent program mutation as well as restore execution state.

## Run follow-up

[src/serve_recovery.rs](https://github.com/omar-os/omar/blob/main/src/serve_recovery.rs) posts run status notices and watches the response queue for manual Web steps. For the latest failed or completed run, it sends the owning assistant the recorded outcome and artifact paths once the chat is idle. The prompt asks the assistant to diagnose and verify a repair or summarize the results. Reruns require explicit action.

The server can revisit the latest failed or completed run when the assistant resumes. An `assistant-followup-delivered` marker beside the run record records successful delivery.

## Live program changes

[src/mutation.rs](https://github.com/omar-os/omar/blob/main/src/mutation.rs) applies program changes to a paused run. The Lean compiler computes a plan from the two sources with `omarc --diff`; [Omar.Mutation](https://github.com/omar-os/omar/blob/main/lang/Omar/Mutation.lean) defines the diff machinery.

The runtime checks that the plan transforms the old bytecode into the new program before applying it. It carries the checkpoint forward: dropping queued events for removed ports/timers, applying state changes, arming new timers, and creating fresh workspaces for replaced instances. It publishes a `mutation` checkpoint for resume. The previous checkpoint retains the old program. Changing an agent's lifetime replaces the agent in the mutation plan.

## Sandbox boundary

[src/sandbox.rs](https://github.com/omar-os/omar/blob/main/src/sandbox.rs) optionally runs team instances inside Docker Sandboxes. Explicit workspace directories cross the VM boundary, and control uses `sbx exec` pipes. A workspace snapshot is file history; the sandbox supplies the separate execution boundary.
