#!/bin/bash
# Helper for SkySynth.omar / SkySynthProof.omar code reactions and the delivery check.
# usage: helper.sh <tutorial|proof> <cmd> [args]
# Every root is absolute; the framework the workers import is a read-only COPY under $ROOT/framework.
SKY=$(cat "$(cd "$(dirname "$0")" && pwd)/.skydiscover")  # written by gen.py
BASE=$(cd "$(dirname "$0")" && pwd)
mode=$1; cmd=$2; shift 2
case $mode in tutorial) SLUG=tutorial-cache;; proof) SLUG=proved-kvstore;; *) echo "mode?" >&2; exit 64;; esac
ROOT=$BASE/$mode
FW=$ROOT/framework
export PATH=/opt/homebrew/bin:$PATH
export PYTHONPATH=$FW SKYDISCOVER_RUNS=$ROOT/runs SKYDISCOVER_OUTPUTS=$ROOT/outputs SKYDISCOVER_HOME=$ROOT/home PYTHONDONTWRITEBYTECODE=1
RUN=$ROOT/runs/$SLUG
export SKYDISCOVER_RUN=$RUN
SC=$FW/skydiscover/synthesize/workflow/scripts

fwdigest() { (cd "$FW" && find . -type f -print0 | sort -z | xargs -0 shasum | shasum | cut -d' ' -f1); }
# The live checkout minus examples/ (the user's other work lives there and changes on its own).
livedigest() { (cd "$SKY" && find skydiscover/synthesize -type f -not -path '*/examples/*' -print0 | sort -z | xargs -0 shasum | shasum | cut -d' ' -f1); }

case $cmd in
setup)
  # Fresh read-only copy of the whole checkout minus .git, then the run dir.
  if [ -d "$FW" ]; then chmod -R u+w "$FW"; rm -rf "$FW"; fi
  mkdir -p "$ROOT/project" "$ROOT/runs" "$ROOT/outputs" "$ROOT/home" "$FW"
  (cd "$SKY" && tar --exclude=.git -cf - .) | (cd "$FW" && tar -xf -)
  chmod -R a-w "$FW"
  fwdigest > "$ROOT/digest.fw"; livedigest > "$ROOT/digest.live"
  : > "$ROOT/after.log"; rm -f "$ROOT/best.txt" "$ROOT/vetoes.txt"
  printf '%s\n' "$1" > "$ROOT/ask.txt"
  rm -f "$ROOT/project/workload.py"
  if [ "$mode" = tutorial ]; then cp -f "$FW/skydiscover/synthesize/examples/tutorial/workload.py" "$ROOT/project/"; chmod u+w "$ROOT/project/workload.py"; fi
  cd "$ROOT/project" && python3 -m skydiscover.synthesize.spec.paths run $SLUG
  echo "framework copy $(cat $ROOT/digest.fw) live $(cat $ROOT/digest.live)" ;;
guard)
  # Framework edit guard: the copy and the live tree (minus examples/) must equal the start digests, and nothing in the copy may be writable.
  bad=0
  [ "$(fwdigest)" = "$(cat $ROOT/digest.fw)" ] || { echo "framework copy CHANGED" >&2; bad=1; }
  [ "$(livedigest)" = "$(cat $ROOT/digest.live)" ] || { echo "live skydiscover/synthesize (minus examples) CHANGED" >&2; bad=1; }
  w=$(find "$FW" -perm +222 2>/dev/null | head -1); [ -z "$w" ] || { echo "writable in framework copy: $w" >&2; bad=1; }
  exit $bad ;;
after)
  # after <role-tag> <enforce-run-check:0|1>: framework guard, then SkySynth's own run check as a backstop.
  tag=$1; enf=$2
  "$0" $mode guard || { echo "$tag guard FAIL" >> "$ROOT/after.log"; exit 1; }
  out=$(python3 -m skydiscover.synthesize.spec.run check "$RUN" 2>&1); rc=$?
  echo "$tag guard ok; run check exit $rc (enforced=$enf)" >> "$ROOT/after.log"
  if [ "$rc" != 0 ] && [ "$enf" = 1 ]; then echo "$out" >&2; exit 1; fi
  exit 0 ;;
check) python3 -m skydiscover.synthesize.spec.run check "$RUN" ;;
tests) python3 "$SC/run_tests.py" --run "$RUN" ;;
lb)
  n=$(jq '[.[] | select((.role // "candidate")=="candidate" and (.draw // "scored")=="scored")] | length' "$RUN/synthesis/bench/leaderboard.json" 2>/dev/null || echo 0)
  c=$(find "$ROOT/outputs" -maxdepth 3 -name 'checkpoint_*' -type d 2>/dev/null | wc -l | tr -d ' ')
  echo "candidate_rows=$n checkpoints=$c" ;;
auditdec)
  # Mechanical audit decision: run iff a new best, or the first candidate beating the baseline; else skip. Logged outside the run dir.
  out=$(python3 - "$RUN/synthesis/bench/leaderboard.json" "$ROOT/best.txt" <<'PY'
import json, sys, os
rows = json.load(open(sys.argv[1])); store = sys.argv[2]
# A row without a role is a candidate, as in spec/checkpoint.py.
cand = [r for r in rows if r.get("role", "candidate") == "candidate" and r.get("draw", "scored") == "scored"]
base = [r for r in rows if r.get("role") == "baseline"]
if not cand: print("skip (reason: no scored candidate)"); sys.exit(0)
last = cand[-1]; obj = last.get("objective"); d = 1 if last.get("direction", "max") == "max" else -1
val = last["metrics"][obj] * d
prev = float(open(store).read()) if os.path.exists(store) else None
bv = base[-1]["metrics"][obj] * d if base and obj in base[-1].get("metrics", {}) else None
if prev is None and bv is not None and val > bv: print("run (reason: first candidate to beat the baseline)")
elif prev is None or val > prev: print("run (reason: new best %s=%s)" % (obj, last["metrics"][obj]))
else: print("skip (reason: no new best; best stays)")
if prev is None or val > prev: open(store, "w").write(str(val))
PY
)
  echo "audit decision: $out" >> "$ROOT/audit-decisions.log"; echo "$out" ;;
auditcov)
  python3 - "$RUN" <<'PY'
import sys
from pathlib import Path
from skydiscover.synthesize.spec import checkpoint as c
run = Path(sys.argv[1])
why = c.audit_covers(run / "synthesis/audit/completeness.json", run / "synthesis/impl", run)
print("covered" if why is None else "stale: " + why)
PY
  ;;
specok)
  # Proof path P0, mechanical: the immutable spec and the shipped proof check are in place, task.md says checked_by: proof.
  [ -d "$RUN/synthesis/evaluator/interface" ] && [ -n "$(ls "$RUN/synthesis/evaluator/interface")" ] || { echo "no synthesis/evaluator/interface/" >&2; exit 1; }
  [ -f "$RUN/synthesis/tests/test.sh" ] || { echo "no synthesis/tests/test.sh" >&2; exit 1; }
  grep -q '^checked_by: proof' "$RUN/task.md" || { echo "task.md lacks checked_by: proof" >&2; exit 1; }
  grep -q '^domain:' "$RUN/task.md" || { echo "task.md lacks domain:" >&2; exit 1; } ;;
proofdone) [ -f "$RUN/synthesis/proof-log.md" ] || { echo "no proof-log.md: the IDS loop did not run" >&2; exit 1; } ;;
vetoes) # vetoes <inc|get>
  v=$(cat "$ROOT/vetoes.txt" 2>/dev/null || echo 0)
  [ "$1" = inc ] && { v=$((v+1)); echo $v > "$ROOT/vetoes.txt"; }
  echo $v ;;
finish)
  cd "$ROOT/project" && python3 -m skydiscover.synthesize.spec.run finish "$RUN" --export-to "$ROOT/project" --keep-run || exit 1
  ls -d "$ROOT"/outputs/${SLUG}_* | tail -1 ;;
recheck)
  # Final-export re-check with PYTHONDONTWRITEBYTECODE (SKILL.md Phase 3 step 7), tutorial only.
  best=$(ls -d "$ROOT"/outputs/${SLUG}_* | tail -1)/best
  [ -f "$best/score.json" ] || { echo "no best/score.json" >&2; exit 1; }
  cat "$best/score.json" ;;
esac
