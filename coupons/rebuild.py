"""Rebuild both accepted coupon sets in an isolated directory and compare them."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    work = args.output.resolve() / 'work'; work.mkdir()
    for name in ['cad', 'models', 'coupons']:
        shutil.copytree(ROOT/name, work/name)
    (work/'docs').mkdir()
    shutil.copyfile(ROOT/'docs/RELEASE.json', work/'docs/RELEASE.json')
    env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'OPENBLAS_NUM_THREADS': '1'}
    for folder, builder, validator in [
        ('cut5_fit', 'build_coupons.py', 'validate_coupons.py'),
        ('cut5_alignment84', 'build_alignment.py', 'validate_alignment.py')]:
        for script in [builder, validator]:
            with (args.output/(folder+'-'+script+'.log')).open('w') as log:
                subprocess.run([sys.executable, str(work/'coupons'/folder/script)],
                               env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
        print(folder, 'rebuilt and fit/path checks PASS', flush=True)
    sys.path.insert(0, str(ROOT))
    from verify import mesh
    from build123d import import_step
    rows = []
    for folder in ['cut5_fit', 'cut5_alignment84']:
        for original in sorted((ROOT/'coupons'/folder/'artifacts').glob('*.3mf')):
            rebuilt = work/'coupons'/folder/'artifacts'/original.name
            a, b = mesh(original), mesh(rebuilt)
            difference = abs((a-b).volume()) + abs((b-a).volume())
            assert difference < 0.01, (original.name, difference)
            na, nb = import_step(original.with_suffix('.step')), import_step(rebuilt.with_suffix('.step'))
            assert na.is_valid and nb.is_valid and len(na.solids()) == len(nb.solids()) == 1
            volume_error = abs(na.volume-nb.volume)
            assert volume_error < 0.001
            rows.append(dict(set=folder, part=original.stem, status='PASS',
                             native_valid=True, native_volume_difference_mm3=volume_error,
                             mesh_symmetric_difference_mm3=difference))
    (args.output/'REPRODUCTION.json').write_text(json.dumps(rows, indent=2)+'\n')
    print('All eight coupon parts reproduce within comparison gates', flush=True)


if __name__ == '__main__':
    main()
