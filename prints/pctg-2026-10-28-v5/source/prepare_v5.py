"""Test slice of a v5 body in the lead's PCTG recipe (copy of print-2026-10-28-bodies-pctg-matte-06/prepare.py, 2026-10-28;
the original is not edited). Differences from the lead's file: the released v4 body mesh (object 4 part 1) is replaced by
the v5 mesh in the same frame, the reclipped v5 masks replace parts 2 and 3 when they changed, no rear_restore foot, and
the owner's safety brim (outer brim, 0.5 mm object gap, 5 mm wide) replaces no_brim.
Usage: prepare_v5.py left|right
"""
import json, re, shutil, subprocess, sys, zipfile
from pathlib import Path
import numpy as np
sys.path.insert(0, '/home/repro/lab/kraken-ams/body-v5-agent')
from humebeam_load import humebeam
R = Path('/home/repro/lab/kraken-ams/body-v5-agent/work/proj')
SIDE = sys.argv[1]
LIVE = Path('/home/repro/code/orca-settings/live')
APP = Path('/home/repro/lab/p1s-usb-light-riser/one-plate-2026-10-22/ci-d80c/squashfs-root/AppRun')
HB = Path('/mnt/cachy/attic-2026-10-25-delete-after-2027-04-25/home_repro_lab_kraken-ams_download-2026-10-14/extract/Print Profiles/kraken-ams-full-set-with-stackable-support-boxes-100b-asa.3mf')
SRC = Path('/home/repro/lab/kraken-ams/print-2026-10-28-bodies-pctg-matte-06/src')
V5 = Path('/home/repro/lab/kraken-ams/body-v5-agent/work/v5') / SIDE / 'artifacts' / f'{SIDE}_body_pocket_cut5_v5_display.npz'
MASKS = Path('/home/repro/lab/kraken-ams/body-v5-agent/work/v5chk/masks')
HBSPEC = {'left': ('53', ('50', '51'), 128.0), 'right': ('57', ('54', '55'), 435.2)}
OUT = R / SIDE
MATTE = 100  # mm/s -> 15.8 mm3/s
BRIM = dict(brim_type='outer_only', brim_object_gap='0.5', brim_width='5')


def mesh_xml(v, t):
    return '<mesh><vertices>%s</vertices><triangles>%s</triangles></mesh>' % (
        ''.join('<vertex x="%.6f" y="%.6f" z="%.6f"/>' % tuple(p) for p in v),
        ''.join('<triangle v1="%d" v2="%d" v3="%d"/>' % tuple(f) for f in t))


def replace_part_mesh(objmodel, oid, comp_transform, v_native, t):
    """Replace object `oid`'s mesh in an Objects/*.model file. Orca stores each part centred and restores it with the
    component transform; stored = native - translation."""
    tr = np.array(comp_transform.split(), float)[9:]
    v = v_native - tr
    return re.sub(r'(<object id="%s"[^>]*>)\s*<mesh>.*?</mesh>' % oid, lambda m: m.group(1) + mesh_xml(v, t), objmodel, count=1, flags=re.S)


def build_input(src, dst):
    asm, boxes, cx = HBSPEC[SIDE]
    parts = humebeam(HB, asm)
    z = zipfile.ZipFile(src)
    files = {n: z.read(n) for n in z.namelist() if not re.match(r'Metadata/plate_\d+\.gcode', n)}
    top = files['3D/3dmodel.model'].decode()
    comps = dict(re.findall(r'<component p:path="/3D/Objects/(%s-body_1\.model)" objectid="(\d+)"[^>]*transform="[^"]+"' % SIDE, top))
    transforms = {oid: tr for oid, tr in re.findall(r'<component p:path="/3D/Objects/%s-body_1\.model" objectid="(\d+)"[^>]*transform="([^"]+)"' % SIDE, top)}
    objmodel = files[f'3D/Objects/{SIDE}-body_1.model'].decode()
    d = np.load(V5); objmodel = replace_part_mesh(objmodel, '1', transforms['1'], d['v'], d['t'])
    swapped = ['body part 1 <- v5']
    for oid, kind in (('2', 'walls'), ('3', 'dense')):
        m = MASKS / f'{SIDE}-body-{kind}.npz'
        rep = json.loads((MASKS.parent / 'reports' / f'{SIDE}-masks.json').read_text()) if (MASKS.parent / 'reports' / f'{SIDE}-masks.json').exists() else None
        changed = rep and any(r['kind'] == kind and 'unchanged' not in r['action'] for r in rep['modifiers'])
        if m.exists() and changed:
            md = np.load(m); objmodel = replace_part_mesh(objmodel, oid, transforms[oid], md['v'], md['t']); swapped.append(f'part {oid} <- reclipped {kind} mask')
    files[f'3D/Objects/{SIDE}-body_1.model'] = objmodel.encode()
    objs, comps, cfg = [], [], []
    for k, bid in enumerate(boxes):
        v, t = parts[bid]
        v = v - np.array([cx, 128.0, 124.95])          # humebeam plate -> body object frame
        oid = 100 + k
        objs.append('<object id="%d" type="model">%s</object>' % (oid, mesh_xml(v, t)))
        comps.append('<component p:path="/3D/Objects/support-boxes.model" objectid="%d" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>' % oid)
        cfg.append('    <part id="%d" subtype="normal_part">\n      <metadata key="name" value="humebeam support box %d"/>\n'
                   '      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n'
                   '      <metadata key="wall_loops" value="1"/>\n      <metadata key="sparse_infill_density" value="5%%"/>\n'
                   '      <metadata key="top_shell_layers" value="2"/>\n      <metadata key="bottom_shell_layers" value="2"/>\n    </part>\n' % (oid, k + 1))
    files['3D/Objects/support-boxes.model'] = ('<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xml:lang="en-US" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><resources>' + ''.join(objs) + '</resources><build/></model>').encode()
    top = re.sub(r'(<object id="4"[^>]*>\s*<components>)', lambda m: m.group(1) + ''.join(comps), top, count=1)
    top = re.sub(r'\s*<item objectid="6"[^>]*/>', '', top)   # no bar in the body colour (owner 2026-10-28)
    files['3D/3dmodel.model'] = top.encode()
    rels = files['3D/_rels/3dmodel.model.rels'].decode().replace('</Relationships>',
        ' <Relationship Target="/3D/Objects/support-boxes.model" Id="rel-boxes" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n</Relationships>')
    files['3D/_rels/3dmodel.model.rels'] = rels.encode()
    ms = files['Metadata/model_settings.config'].decode()
    i = ms.index('  </object>')
    ms = ms[:i] + ''.join(cfg) + ms[i:]
    ms = re.sub(r'  <object id="6">.*?  </object>\n', '', ms, flags=re.S)
    ms = re.sub(r'    <model_instance>\s*<metadata key="object_id" value="6"/>.*?</model_instance>\n', '', ms, flags=re.S)
    ms = ms.replace('<metadata key="brim_object_gap" value="0.15"/>', '<metadata key="brim_object_gap" value="%s"/>' % BRIM['brim_object_gap'])
    ms = ms.replace('<metadata key="brim_width" value="8"/>', '<metadata key="brim_width" value="%s"/>' % BRIM['brim_width'])
    files['Metadata/model_settings.config'] = ms.encode()
    with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as o:
        for n, b in files.items():
            o.writestr(n, b)
    return swapped


def vec(cfg, key, value):
    cur = cfg[key]
    return [str(value)] * len(cur) if isinstance(cur, list) else ','.join([str(value)] * len(str(cur).split(',')))


def profiles():
    for kind, name in (('machine', 'Repro P1S - 0.6 nozzle'), ('process', 'Repro Normal - 0.6 nozzle'),
                       ('filament', 'Repro PETG - Generic - 0.6 nozzle')):
        cfg = json.loads((LIVE / kind / (name + '.json')).read_text())
        if kind == 'process':
            cfg.update(layer_height='0.3', initial_layer_print_height='0.3', wall_loops='2', sparse_infill_density='15%',
                       sparse_infill_pattern='rectilinear', top_shell_layers='4', bottom_shell_layers='3',
                       enable_support='0', enable_prime_tower='0',
                       outer_wall_speed=str(MATTE), top_surface_speed=str(MATTE), small_perimeter_speed='100%',
                       enable_overhang_speed='0', top_surface_acceleration='5000', outer_wall_acceleration='5000',
                       seam_position='aligned', elefant_foot_compensation='0.15', **BRIM)
            cfg.update(initial_layer_speed='30', initial_layer_infill_speed='30')
        elif kind == 'filament':
            for k, val in (('nozzle_temperature', 260), ('nozzle_temperature_initial_layer', 260),
                           ('textured_plate_temp', 70), ('textured_plate_temp_initial_layer', 70),
                           ('filament_max_volumetric_speed', 17), ('slow_down_min_speed', MATTE),
                           ('dont_slow_down_outer_wall', 1)):
                cfg[k] = vec(cfg, k, val)
            cfg['filament_type'] = vec(cfg, 'filament_type', 'PCTG')
            cfg['filament_density'] = vec(cfg, 'filament_density', 1.23)
            cfg['filament_colour'] = '#F2D7DC'
            cfg['filament_shrink'] = '99.66%'
        (OUT / f'{kind}.json').write_text(json.dumps(cfg, indent=2) + '\n')


if __name__ == '__main__':
    shutil.rmtree(OUT, ignore_errors=True); OUT.mkdir(parents=True)
    swapped = build_input(SRC / f'kraken-{SIDE}-asa.3mf', OUT / 'input.3mf')
    (OUT / 'swapped.json').write_text(json.dumps(swapped))
    profiles()
    stem = f'kraken-{SIDE}-v5-pctg-matte-06-test'
    cmd = [str(APP), '--datadir', str(OUT / 'data'), '--load-settings', f"{OUT/'machine.json'};{OUT/'process.json'}",
           '--load-filaments', str(OUT / 'filament.json'), '--curr-bed-type', 'Textured PEI Plate',
           '--orient', '0', '--arrange', '0', '--slice', '0', '--summary', str(OUT / 'summary.json'),
           '--export-3mf', f'{stem}.gcode.3mf', '--outputdir', str(OUT), str(OUT / 'input.3mf')]
    (OUT / 'command.json').write_text(json.dumps(cmd))
    print('swapped', swapped, flush=True)
    p = subprocess.run(cmd, cwd=OUT, capture_output=True, timeout=3600)
    (OUT / 'slice.log').write_bytes(p.stdout + p.stderr)
    print('rc', p.returncode)
