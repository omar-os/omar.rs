#!/bin/bash
# Stub dry-run stand-in for helper.sh: same commands, canned answers, so the Stub-backend copies exercise the control flow
# (including the DSA stall counter: the proof dry run fails the checker 3 times on the same obligation, then passes).
BASE=$(cd "$(dirname "$0")" && pwd)
mode=$1; cmd=$2; D=$BASE/dry-$mode; mkdir -p $D
echo "$mode $cmd $3 $4" >> $D/calls.log
n() { f=$D/n-$1; v=$(cat $f 2>/dev/null || echo 0); v=$((v+1)); echo $v > $f; echo $v; }
case $cmd in
  tests) c=$(n tests); if [ $mode = proof ] && [ $c -le 3 ]; then echo "checker: obligation open"; exit 1; fi; echo "ok" ;;
  lb) echo "candidate_rows=1 checkpoints=1" ;;
  auditdec) c=$(n auditdec); if [ $((c%2)) = 1 ]; then echo "run (reason: dry new best)"; else echo "skip (reason: dry no new best)"; fi ;;
  auditcov) echo "stale: dry" ;;
  vetoes) [ "$3" = inc ] && n vetoes >/dev/null; cat $D/n-vetoes 2>/dev/null || echo 0 ;;
  finish) echo "$D/outputs/dry_result" ;;
  recheck) echo '{"dry":1}' ;;
  *) : ;;
esac
exit 0
