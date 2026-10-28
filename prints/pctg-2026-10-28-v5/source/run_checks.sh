#!/bin/sh
# Stage 2 release checks on the v5 bodies, in the attic pipeline's own scripts. Usage: run_checks.sh
set -u
P=/home/repro/lab/kraken-ams/body-v5-agent/work/full/printable_bottom_20261016
C=/home/repro/lab/kraken-ams/body-v5-agent/work/v5chk
PY=/home/repro/venvs/kraken-cad/bin/python
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
side_chain() {
  s=$1
  $PY $P/check_candidate.py $s $C > $C/reports/$s-check_candidate.log 2>&1; echo "check_candidate $s rc=$?"
  $PY $P/revalidate.py $s $C > $C/reports/$s-revalidate.log 2>&1; echo "revalidate $s rc=$?"
  $PY $P/revalidate.py $s $C --walls > $C/reports/$s-revalidate_walls.log 2>&1; echo "walls $s rc=$?"
  $PY $P/reclip_masks.py $s $C > $C/reports/$s-reclip_masks.log 2>&1; echo "reclip $s rc=$?"
}
side_chain left > $C/reports/chain-left.log 2>&1 &
side_chain right > $C/reports/chain-right.log 2>&1 &
wait
$PY $P/check_loadpaths_joint_v5.py $C > $C/reports/loadpaths-joint.log 2>&1; echo "loadpaths rc=$?" >> $C/reports/chain-left.log
$PY $P/layer_screen.py $C/layer $C/reports/layer_screen.json > $C/reports/layer_screen.log 2>&1; echo "layer_screen rc=$?" >> $C/reports/chain-left.log
echo ALLDONE >> $C/reports/chain-left.log
