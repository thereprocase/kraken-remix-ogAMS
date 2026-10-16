"""Reproduce the native bodies and removable bars in a fresh output directory."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('build'))
    parser.add_argument('--variant', choices=['pocket','standard'], default='pocket')
    parser.add_argument('--body-height', choices=['cut5','full'], default='cut5',
                        help='244.9 mm body plus bar, or one-piece 249.9 mm body')
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        parser.error('Output directory already exists; choose a fresh directory.')
    output.mkdir(parents=True)
    work = output/'work'
    shutil.copytree(ROOT/'cad', work)
    for folder in ['artifacts','reports','analysis']:
        (work/folder).mkdir()
    env = {**os.environ, 'PYTHONDONTWRITEBYTECODE':'1','OPENBLAS_NUM_THREADS':'1'}
    models = output/'models';models.mkdir()
    summary = []
    for side,standard in [('right','M3'),('left','M4')]:
        pocket = args.variant == 'pocket'
        stage = 'M5' if pocket else standard
        base = 'M5_gear_edit' if pocket else standard
        # Match the accepted release path: split the native build directly.
        # An intermediate STEP import can split/merge trims and change tessellation.
        commands = [['feed_end_insert.py',side,args.variant]] if args.body_height == 'cut5' else \
            [[side+'.py', '--stage', stage] + (['--gear-pocket'] if pocket else [])]
        for index,command in enumerate(commands):
            print('Building',side,args.variant,args.body_height,'from native CAD',flush=True)
            with (output/f'{side}-{index+1}.log').open('w') as log:
                subprocess.run([sys.executable,*command],cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        parts = [(f'{base}_cut5','body'),(f'{base}_insert_flat_cut5','front-bar')] if args.body_height == 'cut5' else [(base,'body')]
        for source,part in parts:
            for suffix in ['step','3mf']:
                dst=models/f'{side}-{part}-{args.variant}_{args.body_height}.{suffix}'
                shutil.copy2(work/'artifacts'/f'{side}_{source}.{suffix}',dst)
        if args.body_height == 'cut5':
            split=json.loads((work/'reports'/f'{side}_{base}_cut5_build.json').read_text())
            build=split['exports'][f'{base}_cut5']
            height=split['body_height']; overlap=split['native_body_insert_overlap_mm3']
            assert abs(height-244.9)<1e-6 and overlap<=1e-6
        else:
            build=json.loads((work/'reports'/f'{side}_{base}_build.json').read_text())
            height=build['length_mm']; overlap=0.0
            assert abs(height-249.9)<1e-5
        assert build['valid'] and build['solids']==1
        assert build['rfid_export_gate']['no_added_pocket_material_pass']
        summary.append(dict(side=side,variant=args.variant,body_height_mm=height,
                            native_valid=True,rfid_scope_gate='PASS',
                            body_insert_overlap_mm3=overlap))
    (output/'BUILD.json').write_text(json.dumps(summary,indent=2)+'\n')
    manifest=[]
    for path in sorted(models.iterdir()):
        manifest.append(hashlib.sha256(path.read_bytes()).hexdigest()+'  '+str(path.relative_to(output)))
    (output/'SHA256SUMS').write_text('\n'.join(manifest)+'\n')
    print('Wrote',models,flush=True)

if __name__ == '__main__':
    main()
