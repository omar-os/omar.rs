#!/bin/bash
# check "..." wrapper for the coder task / final delivery: SkySynth's TaskCompleted hook (delivery_check.sh) needs
# SKYDISCOVER_RUN etc. in its environment, which a check command does not inherit from the lead. Set them, then run
# the original script from the read-only framework copy (same bytes as the live checkout). Stdin is empty, so the hook
# takes its "SKYDISCOVER_* set => checked delivery" path. Exit 2 = refused, with run_tests.py's failures on stderr.
# usage: delivery_check_wrap.sh <tutorial|proof>
mode=${1:-tutorial}
BASE=$(cd "$(dirname "$0")" && pwd)
case $mode in tutorial) SLUG=tutorial-cache;; proof) SLUG=proved-kvstore;; esac
ROOT=$BASE/$mode
export PATH=/opt/homebrew/bin:$PATH
export PYTHONPATH=$ROOT/framework SKYDISCOVER_RUNS=$ROOT/runs SKYDISCOVER_OUTPUTS=$ROOT/outputs SKYDISCOVER_HOME=$ROOT/home PYTHONDONTWRITEBYTECODE=1
export SKYDISCOVER_RUN=$ROOT/runs/$SLUG
exec bash "$ROOT/framework/skydiscover/synthesize/workflow/hooks/delivery_check.sh" < /dev/null
