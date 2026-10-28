#!/bin/sh
# Stage 2 orchestration: rebuild v5 bodies, refresh the check workspace, run the release checks, the deviation gate
# and the test slices. One log: work/stage2.log
set -u
B=/home/repro/lab/kraken-ams/body-v5-agent; V=$B/work/v5; C=$B/work/v5chk; P=$B/work/full/printable_bottom_20261016
PY=/home/repro/venvs/kraken-cad/bin/python; export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
for s in left right; do $PY $P/rear_face_v5.py $s --out $V/$s > $V/$s-v5.log 2>&1 & done; wait; echo "rebuild done $(date +%T)"; grep -q DONE $V/left-v5.log && grep -q DONE $V/right-v5.log || { echo REBUILD_FAILED; exit 1; }
for s in left right; do
  cp $V/$s/artifacts/${s}_body_pocket_cut5_v5.step $C/artifacts/${s}_body_pocket_cut5_printable.step
  cp $V/$s/artifacts/${s}_body_pocket_cut5_v5.3mf $C/artifacts/${s}_body_pocket_cut5_printable.3mf
  cp $V/$s/artifacts/${s}_body_pocket_cut5_v5_display.npz $C/artifacts/${s}_body_pocket_cut5_printable_display.npz
  cp $V/$s/artifacts/${s}_bar_slot_v5_display.npz $C/artifacts/
  $PY -c "import numpy as np; d=np.load('$V/$s/artifacts/${s}_body_pocket_cut5_v5_display.npz'); np.savez('$C/layer/$s-body.npz', v=d['v'].astype(float), t=d['t'].astype(np.int64))"
done
rm -rf $C/masks $C/analysis/*assembled* ; mkdir -p $C/masks
$B/tools/run_checks.sh > $C/run_checks.log 2>&1; echo "checks done $(date +%T)"; cat $C/reports/chain-left.log $C/reports/chain-right.log
for s in left right; do $PY -I $B/tools/deviation_check.py $s $V/$s/artifacts/${s}_body_pocket_cut5_v5.3mf $C/reports/$s-deviation.json > $C/reports/$s-deviation.log 2>&1 & done; wait; echo "deviation done $(date +%T)"; head -n 1 $C/reports/left-deviation.log $C/reports/right-deviation.log
for s in left right; do $PY $B/tools/prepare_v5.py $s > $B/work/proj/$s-prepare.log 2>&1; echo "slice $s rc=$? $(date +%T)"; done
echo STAGE2DONE
