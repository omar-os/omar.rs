---
title: "Compiler and bytecode"
order: 5
---

## Source to runtime

The Lean compiler and Rust runtime meet at a JSON file:

```text
.omar source + imported schemas
    -> omarc
    -> JSON bytecode
    -> Rust VM validation
    -> workflow execution
```

[lang/Main.lean](https://github.com/omar-os/omar/blob/main/lang/Main.lean) reads source and imported schemas and selects the compiler mode. [lang/Omar/Compiler.lean](https://github.com/omar-os/omar/blob/main/lang/Omar/Compiler.lean) contains tokenization, parsing, elaboration, and bytecode generation. [lang/spec.md](https://github.com/omar-os/omar/blob/main/lang/spec.md) defines the language contract.

The CLI modes are:

```text
omarc [--local-imports] input.omar output.json
omarc [--local-imports] --diff old.omar new.omar diff.json
omarc [--local-imports] --lean input.omar model.lean
omarc [--local-imports] --prove input.omar properties.json verdicts.json
```

`--local-imports` restricts imports to relative paths within the program's directory. HTTP-submitted companion files need this boundary because the source arrives from a request.

## Bytecode contract

[Bytecode and Instruction](https://github.com/omar-os/omar/blob/main/src/topology.rs) are the Rust wire definitions. `Bytecode` carries `version`, `team`, and `instructions`. Instructions use an `op` discriminator with snake-case names. The VM accepts versions 1 and 2. The compiler emits version 2 when a `spawn_agent` instruction carries a `lifetime` with a `unit` (`task` or `tag`) and a positive `count`. The compiler and VM both check that the backend supports fresh conversations. See [the generated compiler allowlist](https://github.com/omar-os/omar/blob/main/lang/Omar/Backends.lean).

Instructions describe declarations and connections: instances, agents, ports, imported types, state, parameters, timers, and reactions. They also include plan/control operations. Read the enum for the complete vocabulary rather than copying it into a second specification.

The runtime validates declarations, identifiers, references, types, and topology before execution. Compiler output is not a substitute for runtime validation.

`.omar` source remains canonical. Bytecode can be rebuilt; source is what recovery and live program changes preserve.

## Models and proofs

[Omar.Model](https://github.com/omar-os/omar/blob/main/lang/Omar/Model.lean) renders a program model. [Omar.Reactor](https://github.com/omar-os/omar/blob/main/lang/Omar/Reactor.lean) supplies reactor semantics; [Omar.Verify](https://github.com/omar-os/omar/blob/main/lang/Omar/Verify.lean) supplies verification support. [Omar.Prove](https://github.com/omar-os/omar/blob/main/lang/Omar/Prove.lean) checks requested Lean properties against the model.

These properties concern the program model. Agent task results still cross the Rust invocation validation boundary at runtime. [src/properties.rs](https://github.com/omar-os/omar/blob/main/src/properties.rs) connects property checks to the server.
