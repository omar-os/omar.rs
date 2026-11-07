#!/usr/bin/env python3
"""Generates SkySynth.omar and SkySynthProof.omar (the long shared context string and the
repetitive gate reactions are the same everywhere, so they are written once here).
Usage: python3 gen.py /path/to/skydiscover [--stub]   (--stub swaps every backend for Stub into *Stub.omar copies)
Programs, helpers and run state live next to this file; the generated programs carry absolute paths for this machine."""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
args = [a for a in sys.argv[1:] if not a.startswith("--")]
if len(args) != 1 or not os.path.isfile(os.path.join(args[0], "skydiscover/synthesize/scripts/install.sh")):
    sys.exit("usage: python3 gen.py /path/to/skydiscover [--stub]")
SKY = os.path.abspath(args[0])
open(os.path.join(BASE, ".skydiscover"), "w").write(SKY + "\n")
STUB = "--stub" in sys.argv
SS = f"{BASE}/helper_dry.sh" if STUB else f"{BASE}/helper.sh"
WRAP = f"{BASE}/delivery_check_wrap.sh"
INSTALL = f"{SKY}/skydiscover/synthesize/scripts/install.sh"
OPUS, SONNET = "claude-opus-5-5", "claude-sonnet-5-5"
STUB = "--stub" in sys.argv


def chk(mode):
    return "" if STUB else f'check "bash {WRAP} {mode}"'


def be(name, model=None, per=None):
    """Agent backend text; the Stub dry-run swaps every backend for Stub (no model, no per-less change)."""
    if STUB:
        return "Stub" + (f" per {per}" if per else "")
    return name + (f'(model = "{model}")' if model else "") + (f" per {per}" if per else "")


def setup(agent):
    return f'setup "bash {INSTALL} --agent {agent} ."' if not STUB else ""


def ctx(mode):
    root = f"{BASE}/{mode}"
    slug = "tutorial-cache" if mode == "tutorial" else "proved-kvstore"
    run = f"{root}/runs/{slug}"
    fw = f"{root}/framework"
    what = ("SkySynth run by OMAR (tutorial cache task, 3 iterations: smoke, NOT a 1:1 run). Project dir: "
            f"{root}/project (contains workload.py)." if mode == "tutorial" else
            "SkySynth proof-path run by OMAR (examples/proved-dist-kvstore, smoke budget, NOT a 1:1 run). Project dir: "
            f"{root}/project.")
    links = "; ".join(f"ln -sfn {run}/{d} {d}" for d in ("synthesis", "specification", "review"))
    return (f"{what} Run dir: {run}. This run dir is the one shared place for all roles: ignore any instruction to keep "
            "persistent files in your own worktree; every relative path in your brief (synthesis/..., specification/..., plan.md) "
            "means that run dir, never your current directory, and you must never create real synthesis/ or specification/ "
            f"directories in your current directory: FIRST run `{links}` there (the worker rules that tell you to keep files in "
            "your worktree are satisfied by these links, which resolve into the run dir), and write only the files the brief names, "
            f"at their run-dir paths. Before every helper command run: export PYTHONPATH={fw} SKYDISCOVER_RUNS={root}/runs "
            f"SKYDISCOVER_OUTPUTS={root}/outputs SKYDISCOVER_HOME={root}/home SKYDISCOVER_RUN={run} PYTHONDONTWRITEBYTECODE=1. "
            f"The skydiscover framework you import and read is a READ-ONLY copy at {fw}; skill dir: "
            f"{fw}/skydiscover/synthesize/workflow (read SKILL.md Rules That Hold Everywhere; your brief is agents/<phase>/<role>.md; "
            "layout in references/artifacts.md). Never modify the framework, any copy of it or the original checkout "
            "(a change fails the whole run). Never install packages or call external LLM APIs. Never kill or stop processes you did "
            "not start. Do exactly one role and mode as stated below, then set the output port named at the end to a one-line "
            "summary of what you did.")


def call(mode, *args):
    a = ", ".join(f'"{x}"' for x in (mode,) + args)
    return f'std::process::Command::new("{SS}").args([{a}]).output().unwrap()'


def gate(mode, inp, local, out, tag, enforce, note=""):
    """A code step after a role: framework guard + SkySynth's `run check` backstop; passes the role's output on."""
    return f"""
    action {out} : string
    reaction({inp}) -> {out} {{=
        let o = {call(mode, "after", tag, str(enforce))};
        if !o.status.success() {{ panic!("after {tag} failed: {{}}{{}}", String::from_utf8_lossy(&o.stdout), String::from_utf8_lossy(&o.stderr)); }}
        {out} = {local}.clone();
    =}}
"""


def header(title):
    return f"""// {title}
// Backends: Claude and Codex only. Models: Claude roles claude-sonnet-5-5 (SkySynth's tutorial recommends Sonnet for the loop, for
// cost); the lead claude-opus-5-5; the Codex coder runs Codex's default model. Every role but the lead is `per task`
// (SkySynth: "Run a fresh agent for each step"); the lead is one persistent Claude conversation.
// Hooks: each team gets `setup` = SkySynth's install.sh for its own backend, so the clone-reuse guard and the framework edit
// guard load for Claude and for Codex. The delivery hook (delivery_check.sh) is a `check` on the tasks that deliver.
"""


# ------------------------------------------------------------------------------------------ tutorial
def tutorial():
    C = ctx("tutorial")
    smoke = (" Smoke limits: use at most 2 reference systems for discovery (small ones: one cache library or the tutorial workload, "
             "no deep PR mining), keep any subagent fan-out to 2, keep each test run under 30 s, and finish your role in as few "
             "steps as the brief allows.")
    C_T = C + smoke
    lit = lambda s: s.replace('"', "'")  # prompts are plain literals
    P = {}
    P["kb"] = ("$(ctx) Role: kb-builder (brief agents/1-specification/kb-builder.md), first build in ADAPT mode: adopt the reference systems "
               "already cloned in the run dir under specification/sources/ and specification/references/ instead of selecting sources; write "
               "at most 2 wiki pages into the knowledge base at $SKYDISCOVER_HOME; do not mine PRs or issues. A thin or failed build must "
               "not block anything: report what you managed. Then set report to a one-line summary. Context: $(job)")
    out = header("SkySynth on OMAR with per, model, check and setup (tutorial cache task, N=3 iterations: a smoke run, NOT 1:1 with SkySynth's Quick ~20).\n"
                 "// Run: omar run SkySynth.omar --input synth.ask=\"Build me a fast cache for the workload in workload.py. Ask me what you need to know before starting.\" --input synth.budget=3 --timeout-seconds 86400 --checkpoint-period tag --keep-workspaces\n"
                 "// Fix attempts of the delivery loop: the coder's `check` returns run_tests.py failures to the SAME conversation inside one invocation (SkySynth's\n"
                 "// TaskCompleted hook bounces to the same agent), so the coder is `per task`: fresh across iterations, continuous across fix attempts.")
    out += f"""
team Kb(ctx : string)[kb_builder : {be("Claude", SONNET, "task")}]
{{
    {setup("claude")}
    input job : string
    output report : string

    task kb_builder(job) -> report within(1h)
    "{P['kb']}"
}}

team Coder(ctx : string)[coder : {be("Codex", None, "task")}]
{{
    {setup("codex")}
    input boot_job : string
    input iter_job : string
    output booted : string
    output changed : string

    task coder(boot_job) -> booted within(2h)
    "$(ctx) Role: coding-agent, bootstrap mode (brief agents/2-synthesis-loop/coding-agent.md): build synthesis/evaluator/interface/ and synthesis/evaluator/benchmark/ (benchmark = workload.py replay on the tutorial cache, app_hit_rate, seeded) and an unscored first candidate in synthesis/impl/; it never becomes the trusted reference. Context: $(boot_job). Then set booted to a one-line summary."

    task coder(iter_job) -> changed within(3h)
    "$(ctx) Role: coding-agent, iteration mode: one change, fast tests, exit. Read plan.md ## Brief and ## Learnings (the critic feedback so far) and make the single change the brief asks for in synthesis/impl/. Your completion is checked by SkySynth's delivery hook (every kept test via run_tests.py --run): if it refuses, fix synthesis/impl/ so every kept test passes, change nothing else, and complete again. Previous feedback: $(iter_job). Then set changed to a one-line summary."
    {chk("tutorial")}
}}

team Synth(ctx : string)[
    lead : {be("Claude", OPUS)},
    spec : {be("Claude", SONNET, "task")},
    planner : {be("Claude", SONNET, "task")},
    evaluator : {be("Claude", SONNET, "task")},
    auditor : {be("Claude", SONNET, "task")},
    critic : {be("Claude", SONNET, "task")}
]
{{
    {setup("claude")}
    input ask : string
    input budget : int
    output status : string
    output result : string

    action start : string
    action kbstatus : string
    action disc : string
    action settled : string
    action env : string
    action req : string
    action fixfail : string
    action fixed : string
    action go : string
    action hard : string
    action plan0 : string
    action refdone : string
    action iter_go : string
    action gated : string
    action scored : string
    action to_audit : string
    action to_critic : string
    action audited : string
    action feedback : string
    action phase3 : string
    action to_final_audit : string
    action to_report : string
    action final_audited : string
    action reported : string

    kb = Kb("{C_T}")
    coder = Coder("{C_T}")

    state have_ask : bool = false
    state have_budget : bool = false
    state ask_text : string = ""
    state n : int = 3
    state k : int = 0
    state check_retried : bool = false
    state req_seen : bool = false
    state kb_seen : bool = false
    state gate_done : bool = false

    reaction(ask, budget) -> start?, status? {{=
        if let Some(a) = ask {{ self.ask_text = a.clone(); self.have_ask = true; }}
        if let Some(b) = budget {{ self.n = b; self.have_budget = true; }}
        if self.have_ask && self.have_budget {{
            let o = std::process::Command::new("{SS}").args(["tutorial", "setup"]).arg(&self.ask_text).output().unwrap();
            if !o.status.success() {{ panic!("setup failed: {{}}", String::from_utf8_lossy(&o.stderr)); }}
            start = Some(self.ask_text.clone());
            status = Some(format!("Phase 1: Initial Specification (budget {{}} iterations from run input)", self.n));
        }}
    =}}

    task lead(start) -> kbstatus within(1h)
    "$(ctx) Role: lead, Step 1 of SKILL.md Phase 1 (read it). The user ask is: $(start). Run spec.paths run tutorial-cache is already done (the run dir exists); write task.md in it with front matter domain: cache (and no checked_by key), read the knowledge base read-only, state and record the line knowledge base: cache, N tests, M findings, P wiki pages in the decision log, and do NOT run the spec-builder yourself. Then set kbstatus to a one-line summary."
{gate("tutorial", "kbstatus", "kbstatus", "kbstatus_ok", "lead-step1", 0)}
    task spec(kbstatus_ok) -> disc within(2h)
    "$(ctx) Role: spec-builder, mode discovery (brief agents/1-specification/spec-builder.md). Ground the cache domain in the reference systems. Context: $(kbstatus_ok). Then set disc to a one-line summary."
{gate("tutorial", "disc", "disc", "disc_ok", "spec-discovery", 0)}
    task lead(disc_ok) -> settled within(1h)
    "$(ctx) Role: lead, Step 2 of SKILL.md: settle every property question the sources or the task determine with decisions set ... --by ai --note, leave an optimization target out of the questions, then run decisions <run> answer so each still-open question gets its declared default (the operator is answering with defaults in this smoke run). Do not ask anyone anything. Discovery said: $(disc_ok). Then set settled to a one-line summary."
{gate("tutorial", "settled", "settled", "settled_ok", "lead-step2", 0)}
    task spec(settled_ok) -> env within(2h)
    "$(ctx) Role: spec-builder, mode environment (the score is a rate, so measure the resource limit and the ceiling for tutorial workload.py: FIFO baseline app_hit_rate is about 0.3886; the named workload is workload.py replay() so skip workload mode). Context: $(settled_ok). Then set env to a one-line summary."
{gate("tutorial", "env", "env", "env_ok", "spec-environment", 0)}
    env_ok -> kb.job

    task spec(env_ok) -> req within(2h)
    "$(ctx) Role: spec-builder, mode requirements (the kb-builder is running in parallel with you and writes only under the knowledge base). Context: $(env_ok). Then set req to a one-line summary."
{gate("tutorial", "req", "req", "req_ok", "spec-requirements", 0)}
    reaction(req_ok, kb.report, fixed_ok) -> go?, fixfail?, status? {{=
        if req_ok.is_some() {{ self.req_seen = true; }}
        if let Some(r) = &report {{
            let o = {call("tutorial", "after", "kb-builder", "0")};
            if !o.status.success() {{ panic!("after kb-builder failed: {{}}{{}}", String::from_utf8_lossy(&o.stdout), String::from_utf8_lossy(&o.stderr)); }}
            let _ = r; self.kb_seen = true;
        }}
        let ready = (self.req_seen && self.kb_seen) || fixed_ok.is_some();
        if ready && !self.gate_done {{
            let o = {call("tutorial", "check")};
            let text = format!("{{}}{{}}", String::from_utf8_lossy(&o.stdout), String::from_utf8_lossy(&o.stderr));
            if o.status.success() {{
                self.gate_done = true;
                go = Some("run check exit 0".to_string());
                status = Some("Phase 1: run check passed, hardening next".to_string());
            }} else if !self.check_retried {{
                self.check_retried = true;
                fixfail = Some(text);
            }} else {{
                panic!("run check failed twice: {{}}", text);
            }}
        }}
    =}}

    action fixed_ok : string
    task spec(fixfail) -> fixed within(1h)
    "$(ctx) Role: spec-builder, repair: run check failed with the output below; re-run the mode that owns each missing file (discovery for references, environment for the environment card) and nothing else. Output: $(fixfail). Then set fixed to a one-line summary."
    reaction(fixed) -> fixed_ok {{=
        let o = {call("tutorial", "after", "spec-repair", "0")};
        if !o.status.success() {{ panic!("after spec-repair failed"); }}
        fixed_ok = fixed.clone();
    =}}

    task spec(go) -> hard within(1h)
    "$(ctx) Role: spec-builder, mode hardening (writes cards/properties.json). Context: $(go). Then set hard to a one-line summary."
{gate("tutorial", "hard", "hard", "hard_ok", "spec-hardening", 1)}
    task planner(hard_ok) -> plan0 within(1h)
    "$(ctx) Role: planner, seed mode (brief agents/2-synthesis-loop/planner.md): write synthesis/plan.md. Context: $(hard_ok). Then set plan0 to a one-line summary."
{gate("tutorial", "plan0", "plan0", "plan0_ok", "planner-seed", 1)}
    plan0_ok -> coder.boot_job
{gate("tutorial", "coder.booted", "booted", "boot_ok", "coder-bootstrap", 1)}
    task evaluator(boot_ok) -> refdone within(2h)
    "$(ctx) Role: evaluator, mode correctness (brief agents/2-synthesis-loop/evaluator.md): write the trusted reference, mutants, and the kept tests with synthesis/tests/test.sh; every kept test passes validate_test.py. Keep the suite small (3 to 5 tests). Context: $(boot_ok). Then set refdone to a one-line summary."
{gate("tutorial", "refdone", "refdone", "refdone_ok", "evaluator-correctness", 1)}
    // One loop step: iteration 1 starts from refdone_ok; every later one from the critic's feedback. k counts finished iterations.
    reaction(refdone_ok, feedback_ok) -> iter_go?, phase3?, status? {{=
        if refdone_ok.is_some() {{
            iter_go = Some("iteration 1, no feedback yet".to_string());
            status = Some(format!("Phase 2: Synthesis Loop ({{}}/{{}} iterations)", self.k, self.n));
        }} else {{
            self.k += 1;
            status = Some(format!("Phase 2: Synthesis Loop ({{}}/{{}} iterations)", self.k, self.n));
            if self.k >= self.n {{ phase3 = Some("budget spent".to_string()); }}
            else {{ iter_go = feedback_ok.clone(); }}
        }}
    =}}
    iter_go -> coder.iter_job

    // SkySynth's delivery hook is the coder's `check`; this asserts it held (C-4) before the performance evaluator may score.
    reaction(coder.changed) -> gated, status? {{=
        let a = {call("tutorial", "after", "coder-iteration", "1")};
        if !a.status.success() {{ panic!("after coder-iteration failed: {{}}{{}}", String::from_utf8_lossy(&a.stdout), String::from_utf8_lossy(&a.stderr)); }}
        let o = {call("tutorial", "tests")};
        if !o.status.success() {{ panic!("delivery gate failed after the coder's check passed: {{}}{{}}", String::from_utf8_lossy(&o.stdout), String::from_utf8_lossy(&o.stderr)); }}
        gated = Some("run_tests.py exit 0".to_string());
        status = Some(format!("Phase 2: Synthesis Loop ({{}}/{{}} iterations), tests pass, measuring", self.k, self.n));
    =}}

    task evaluator(gated) -> scored within(2h)
    "$(ctx) Role: evaluator, mode performance (brief agents/2-synthesis-loop/evaluator.md): measure at the scored configuration, append the leaderboard row (and the FIFO baseline row), take a held-out draw with seed=123 before --became-best, write the checkpoint with spec.checkpoint snapshot right after the leaderboard append. Context: $(gated). Then set scored to a one-line summary."

    // Measured, then the mechanical audit decision (SKILL.md: new best, or first candidate to beat the baseline).
    reaction(scored) -> to_audit?, to_critic?, status? {{=
        let a = {call("tutorial", "after", "evaluator-performance", "1")};
        if !a.status.success() {{ panic!("after evaluator-performance failed: {{}}{{}}", String::from_utf8_lossy(&a.stdout), String::from_utf8_lossy(&a.stderr)); }}
        let lb = {call("tutorial", "lb")};
        let m = String::from_utf8_lossy(&lb.stdout).trim().to_string();
        let d = {call("tutorial", "auditdec")};
        let dec = String::from_utf8_lossy(&d.stdout).trim().to_string();
        let line = format!("{{}}; audit decision: {{}}", m, dec);
        status = Some(format!("Phase 2: Synthesis Loop ({{}}/{{}} iterations), measured: {{}}", self.k, self.n, line));
        if dec.starts_with("run") {{ to_audit = Some(line); }} else {{ to_critic = Some(line); }}
    =}}

    task auditor(to_audit) -> audited within(2h)
    "$(ctx) Role: auditor (brief agents/2-synthesis-loop/auditor.md), per-iteration pass (mechanical audit decision said run): audit the candidate in synthesis/impl/ against the kept tests and the spec for reward hacks (smoke: one round, at most 2 probes), add any confirmed finding through the findings CLI, and stamp with spec.checkpoint stamp-audit. Measured state and decision: $(to_audit). Then set audited to a one-line summary."
{gate("tutorial", "audited", "audited", "audited_ok", "auditor-iteration", 1)}
    task critic(to_critic, audited_ok) -> feedback within(45min)
    "$(ctx) Role: critic (brief agents/2-synthesis-loop/critic.md). Read the leaderboard and plan.md, write ranked file:line feedback, append this iteration to plan.md ## Learnings only. Do not edit code. The Learnings append is the only file you write. Measured state: $(to_critic) $(audited_ok). Then set feedback to a one-line summary."
{gate("tutorial", "feedback", "feedback", "feedback_ok", "critic", 1)}
    // Final audit stamp: audit only if the existing stamp does not cover the delivered candidate (audit_covers), as run finish requires.
    reaction(phase3) -> to_final_audit?, to_report?, status? {{=
        let c = {call("tutorial", "auditcov")};
        let t = String::from_utf8_lossy(&c.stdout).trim().to_string();
        status = Some(format!("Phase 3: Final Deliverables ({{}} of {{}} iterations), final audit stamp: {{}}", self.k, self.n, t));
        if t.starts_with("covered") {{ to_report = Some(t); }} else {{ to_final_audit = Some(t); }}
    =}}

    task auditor(to_final_audit) -> final_audited within(2h)
    "$(ctx) Role: auditor (brief agents/2-synthesis-loop/auditor.md), mode completeness/coverage on the delivered candidate (smoke: one round, at most 2 probes): add any confirmed finding through the findings CLI and ALWAYS write the stamp with spec.checkpoint stamp-audit so run finish can proceed. Stamp state: $(to_final_audit). Then set final_audited to a one-line summary."
{gate("tutorial", "final_audited", "final_audited", "final_audited_ok", "auditor-final", 1)}
    task lead(to_report, final_audited_ok) -> reported within(1h)
    "$(ctx) Role: lead, final step: write report.md in the run dir (the lead writes it). It must contain the text k of N iterations, the reason the loop ended, the best score against the 0.3886 FIFO baseline, and say this is a scoped smoke run (production-ready not claimed; the security/reliability/attack lenses and the proof path were not run; audit decisions are in {BASE}/tutorial/audit-decisions.log). Context: $(to_report) $(final_audited_ok). Then set reported to a one-line summary."
    {chk("tutorial")}

    reaction(reported) -> result?, status? {{=
        let a = {call("tutorial", "after", "lead-final", "1")};
        if !a.status.success() {{ panic!("after lead-final failed: {{}}{{}}", String::from_utf8_lossy(&a.stdout), String::from_utf8_lossy(&a.stderr)); }}
        let o = {call("tutorial", "finish")};
        if !o.status.success() {{ panic!("run finish failed: {{}}{{}}", String::from_utf8_lossy(&o.stdout), String::from_utf8_lossy(&o.stderr)); }}
        let r = {call("tutorial", "recheck")};
        if !r.status.success() {{ panic!("final re-check failed: {{}}", String::from_utf8_lossy(&r.stderr)); }}
        result = Some(String::from_utf8_lossy(&o.stdout).trim().to_string());
        status = Some(format!("Phase 3: Final Deliverables ({{}} of {{}} iterations)", self.k, self.n));
        request_stop();
    =}}
}}

main SkySynth {{
    synth = Synth("{C_T}")
}}
"""
    return out


# ------------------------------------------------------------------------------------------ proof
def proof():
    C = ctx("proof") + " Smoke limits: keep each Rocq build short and stop a cycle at the first checker verdict."
    ex = f"{BASE}/proof/framework/skydiscover/synthesize/examples/proved-dist-kvstore"
    out = header("SkySynth proof path (checked_by: proof) on OMAR: examples/proved-dist-kvstore, Rocq 9.3.0. Smoke budget, NOT 1:1 (DSA cycles capped by the run input).\n"
                 "// Run: omar run SkySynthProof.omar --input prove.ask=\"prove the Read-Your-Writes store specified in skydiscover/synthesize/examples/proved-dist-kvstore/task.md\" --input prove.cycles=6 --timeout-seconds 86400 --checkpoint-period tag --keep-workspaces\n"
                 "// Roles per SKILL.md proof path: planner once; DSA fresh per cycle (per task); ISA after 3 failed cycles on the same obligation, then a fresh DSA;\n"
                 "// critic veto when task.md carries obligation:; deliver on run_tests.py exit 0 (the final lead task's `check`), final audit stamp, report.md, run finish.\n"
                 "// DSA is Claude Sonnet here (a prover agent; Codex stays the coder of the test-driven program).")
    out += f"""
team Prove(ctx : string)[
    lead : {be("Claude", OPUS)},
    planner : {be("Claude", SONNET, "task")},
    dsa : {be("Claude", SONNET, "task")},
    isa : {be("Claude", SONNET, "task")},
    critic : {be("Claude", SONNET, "task")},
    auditor : {be("Claude", SONNET, "task")}
]
{{
    {setup("claude")}
    input ask : string
    input cycles : int
    output status : string
    output result : string

    action start : string
    action specced : string
    action planned : string
    action redo : string
    action stall : string
    action reseeded : string
    action worked : string
    action obligation : string
    action proved : string
    action accept : string
    action reject : string
    action vetoed : string
    action to_audit : string
    action audited : string
    action giveup : string
    action reported : string
    action reported_fail : string

    state have_ask : bool = false
    state have_cycles : bool = false
    state ask_text : string = ""
    state cap : int = 6
    state done_cycles : int = 0
    state fails : int = 0
    state last_obl : string = ""

    reaction(ask, cycles) -> start?, status? {{=
        if let Some(a) = ask {{ self.ask_text = a.clone(); self.have_ask = true; }}
        if let Some(c) = cycles {{ self.cap = c; self.have_cycles = true; }}
        if self.have_ask && self.have_cycles {{
            let o = std::process::Command::new("{SS}").args(["proof", "setup"]).arg(&self.ask_text).output().unwrap();
            if !o.status.success() {{ panic!("setup failed: {{}}", String::from_utf8_lossy(&o.stderr)); }}
            start = Some(self.ask_text.clone());
            status = Some(format!("Proof P0: spec (DSA cycle cap {{}})", self.cap));
        }}
    =}}

    task lead(start) -> specced within(1h)
    "$(ctx) Role: lead, proof path P0 (SKILL.md Formal-Proof-Driven Synthesis, step 1). The user ask is: $(start). The run dir already exists (spec.paths run proved-kvstore is done). Write task.md in it as a copy of {ex}/task.md with one extra front-matter line `domain: distributed key-value store, read-your-writes` (keep checked_by: proof). Copy the immutable spec, i.e. the contents of {ex}/evaluator/ except tests/, to synthesis/evaluator/interface/, and the contents of {ex}/evaluator/tests/ (test.sh and proof.sh) to synthesis/tests/ (check how proof.sh finds the spec files and fix nothing else). Never edit the spec. Do NOT write the plan, the implementation or the proof yourself. Record the step in the decision log. Then set specced to a one-line summary."
{gate("proof", "specced", "specced", "specced_ok_raw", "lead-p0", 0)}
    action specced_ok : string
    reaction(specced_ok_raw) -> specced_ok {{=
        let o = {call("proof", "specok")};
        if !o.status.success() {{ panic!("P0 spec not in place: {{}}", String::from_utf8_lossy(&o.stderr)); }}
        specced_ok = specced_ok_raw.clone();
    =}}

    task planner(specced_ok) -> planned within(1h)
    "$(ctx) Role: planner, seed mode (brief agents/2-synthesis-loop/planner.md), proof path step 3: run once; write synthesis/plan.md with ## Candidates (representation hypotheses and the simulation relation or invariant each would carry), ## Brief (first direction) and ## Workload (what the spec's guard and history make hard). Context: $(specced_ok). Then set planned to a one-line summary."
{gate("proof", "planned", "planned", "planned_ok", "planner-seed", 0)}
    // The DSA cycle: fresh agent each time. Triggered by the plan, a failed cycle (redo), an ISA reseed, or a critic veto.
    task dsa(planned_ok, redo, reseed, vetoed) -> worked, obligation within(3h)
    "$(ctx) Role: dsa (brief agents/2-synthesis-loop/dsa.md), exactly as written: ONE cycle of co-designed implementation plus proof, type-checked with run_tests.py --run, every attempt appended to synthesis/proof-log.md. Rocq 9.3.0 is at /opt/homebrew/bin (rocq, coqc). Smoke: one tested step per cycle. Input: $(planned_ok) $(redo) $(reseed) $(vetoed). Then set worked to a one-line summary of the checker verdict and obligation to a short stable id of the obligation you worked on (reuse the design log's id when it is the same obligation)."

    // Mechanical stall counter. The checker decides, never the DSA: run_tests.py exit 0 means proved.
    reaction(worked, obligation) -> proved?, redo?, stall?, giveup?, status? {{=
        let a = {call("proof", "after", "dsa", "0")};
        if !a.status.success() {{ panic!("after dsa failed: {{}}{{}}", String::from_utf8_lossy(&a.stdout), String::from_utf8_lossy(&a.stderr)); }}
        self.done_cycles += 1;
        let t = {call("proof", "tests")};
        if t.status.success() {{
            proved = Some(worked.clone().unwrap_or_default());
            status = Some(format!("Proof P2: checker passes after {{}} DSA cycles, critic next", self.done_cycles));
        }} else {{
            let o = obligation.clone().unwrap_or_default().trim().trim_matches('"').to_string();
            if o == self.last_obl {{ self.fails += 1; }} else {{ self.fails = 1; self.last_obl = o.clone(); }}
            let tail: String = String::from_utf8_lossy(&t.stdout).chars().rev().take(3000).collect::<Vec<_>>().into_iter().rev().collect();
            if self.done_cycles >= self.cap {{
                giveup = Some(format!("DSA cycle cap {{}} reached, checker still failing on obligation {{}}", self.cap, o));
                status = Some("Proof: cycle cap reached, not proved".to_string());
            }} else if self.fails >= 3 {{
                stall = Some(format!("obligation {{}} failed {{}} cycles in a row. Checker tail: {{}}", o, self.fails, tail));
                self.fails = 0; self.last_obl = String::new();
                status = Some(format!("Proof P3: cycle {{}}, 3 failed cycles on {{}}, ISA next", self.done_cycles, o));
            }} else {{
                redo = Some(format!("previous cycle failed on obligation {{}} ({{}} in a row). Checker tail: {{}}", o, self.fails, tail));
                status = Some(format!("Proof P2: cycle {{}}/{{}}, obligation {{}} failing ({{}})", self.done_cycles, self.cap, o, self.fails));
            }}
        }}
    =}}

    task isa(stall) -> reseeded within(2h)
    "$(ctx) Role: isa (brief agents/2-synthesis-loop/isa.md), proof path step 5: the DSA stalled; propose a new design seeded by synthesis/proof-log.md and rewrite plan.md ## Brief. Do not write the proof. Stall: $(stall). Then set reseeded to a one-line summary."
{gate("proof", "reseeded", "reseeded", "reseed", "isa", 0)}
    task critic(proved) -> {"accept" if STUB else "(accept | reject)"} within(1h)
    "$(ctx) Role: critic (brief agents/2-synthesis-loop/critic.md), proof-quality veto (proof path step 6): task.md carries obligation: compression. The checker passes; judge the delivered synthesis/impl/ against that quality bar (bounded, end to end, lossy many-to-one, complete). Set accept (one line why) if it clears the bar, or reject (ranked file:line reasons) if it only restates the spec. Append to plan.md ## Learnings only. Context: $(proved)."

    reaction(accept, reject) -> to_audit?, vetoed?, giveup?, status? {{=
        let a = {call("proof", "after", "critic", "0")};
        if !a.status.success() {{ panic!("after critic failed: {{}}{{}}", String::from_utf8_lossy(&a.stdout), String::from_utf8_lossy(&a.stderr)); }}
        if let Some(r) = reject {{
            let v = {call("proof", "vetoes", "inc")};
            let n: i32 = String::from_utf8_lossy(&v.stdout).trim().parse().unwrap_or(9);
            if n > 1 || self.done_cycles >= self.cap {{
                giveup = Some(format!("critic vetoed {{}} time(s) or the cycle cap is reached: {{}}", n, r));
                status = Some("Proof: vetoed, not delivered".to_string());
            }} else {{
                self.fails = 0; self.last_obl = String::new();
                vetoed = Some(format!("critic veto: {{}}", r));
                status = Some("Proof P4: critic veto, a fresh DSA continues".to_string());
            }}
        }} else {{
            to_audit = accept.clone();
            status = Some("Proof P5: critic accepted, final audit".to_string());
        }}
    =}}

    task auditor(to_audit) -> audited within(2h)
    "$(ctx) Role: auditor (brief agents/2-synthesis-loop/auditor.md), proof path step 7, mode completeness/coverage: check the delivered proof for escape hatches or a vacuous example (smoke: one round, at most 2 probes); add any confirmed finding through the findings CLI and ALWAYS write the stamp with spec.checkpoint stamp-audit. Context: $(to_audit). Then set audited to a one-line summary."
{gate("proof", "audited", "audited", "audited_ok", "auditor-final", 0)}
    task lead(audited_ok) -> reported within(1h)
    "$(ctx) Role: lead, proof path step 7 (deliver): write report.md in the run dir: the theorem proved, the spec it refines, the assumptions, the result, the number of DSA cycles, any ISA handoff and critic veto from synthesis/proof-log.md and plan.md, and say this is a scoped smoke run (production-ready not claimed). Context: $(audited_ok). Then set reported to a one-line summary."
    {chk("proof")}

    task lead(giveup) -> reported_fail within(1h)
    "$(ctx) Role: lead, final step of a proof run that did not deliver: write report.md in the run dir saying the proof was NOT delivered, why (below), what synthesis/proof-log.md shows, and that this is a scoped smoke run with a capped budget. Do not write any proof yourself. Reason: $(giveup). Then set reported_fail to a one-line summary."

    reaction(reported) -> result?, status? {{=
        let a = {call("proof", "after", "lead-final", "0")};
        if !a.status.success() {{ panic!("after lead-final failed: {{}}{{}}", String::from_utf8_lossy(&a.stdout), String::from_utf8_lossy(&a.stderr)); }}
        let p = {call("proof", "proofdone")};
        if !p.status.success() {{ panic!("{{}}", String::from_utf8_lossy(&p.stderr)); }}
        let o = {call("proof", "finish")};
        if !o.status.success() {{ panic!("run finish failed: {{}}{{}}", String::from_utf8_lossy(&o.stdout), String::from_utf8_lossy(&o.stderr)); }}
        result = Some(String::from_utf8_lossy(&o.stdout).trim().to_string());
        status = Some(format!("Proof: delivered after {{}} DSA cycles", self.done_cycles));
        request_stop();
    =}}

    reaction(reported_fail) -> result?, status? {{=
        let a = {call("proof", "after", "lead-final", "0")};
        if !a.status.success() {{ panic!("after lead-final failed: {{}}", String::from_utf8_lossy(&a.stderr)); }}
        result = Some(format!("not proved: {{}}", reported_fail.clone().unwrap_or_default()));
        status = Some("Proof: not proved within the smoke budget".to_string());
        request_stop();
    =}}
}}

main SkySynthProof {{
    prove = Prove("{C}")
}}
"""
    return out


suffix = "Stub" if STUB else ""
open(f"{BASE}/SkySynth{suffix}.omar", "w").write(tutorial())
open(f"{BASE}/SkySynthProof{suffix}.omar", "w").write(proof())
print("wrote", suffix or "real")
