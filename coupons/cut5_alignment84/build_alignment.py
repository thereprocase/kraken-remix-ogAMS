"""Two-key coupons cropped from accepted analytic STEP parts, never source mesh."""
from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0,str(ROOT / "cad"))
sys.path.insert(0,str(HERE.parent/'cut5_fit'))
from build_coupons import audit_release, sha
from build123d import import_step, export_step
from native_features import box_bounds, export_3mf
from mechanical_body import norm, union, cut, resolve_design
from feed_end_insert import INSERT

P = dict(pad_width=20., pad_depth=16., strip_width=4., base_height=3.,
         id_notch_width=1., id_notch_depth=.6, id_notch_pitch=3.)
SINGLE_MANIFEST = 'a1b20e12a3d6d72493af305e8bc85557a52039499126441794539d9b93578b1a'


def audit_preserved():
    return dict(production=audit_release())


def crop_mask(centers, cy, zmin, zmax):
    pads=[box_bounds(x-P['pad_width']/2,x+P['pad_width']/2,
                     cy-P['pad_depth']/2,cy+P['pad_depth']/2,zmin,zmax) for x in centers]
    strip=box_bounds(min(centers),max(centers),cy-P['strip_width']/2,
                     cy+P['strip_width']/2,zmin,zmax)
    return union(pads+[strip])


def main():
    before=audit_preserved()
    out=HERE/'artifacts';out.mkdir(exist_ok=True)
    records=[]
    for side,base,marks in [('right','M3',1),('left','M4',2)]:
        p=resolve_design(__import__(side).P)
        b=json.loads((HERE.parent/'SOURCE-JOINT.json').read_text())[side]
        centers=sorted((-x+p['mirror_translation'] if p['mirror'] else x)
                       for x in b['rail_centers_canonical'])
        assert abs(centers[1]-centers[0]-84.)<1e-7
        cy=p['platform_y']+p['platform_depth']/2
        shoulder=b['shoulder_plane']
        side_record=dict(side=side,source_base=base,source_centers_x_mm=centers,
                         source_y_mm=cy,source_shoulder_z_mm=shoulder,
                         spacing_mm=centers[1]-centers[0],parts=[])
        for kind,stage,zmin,zmax in [
            ('keys',base+'_cut5',shoulder-P['base_height'],b['rail_tip']),
            ('sockets',base+'_insert_cut5',shoulder,p['z_feed'])]:
            source=ROOT/'models'/f'{side}-{"body" if kind=="keys" else "front-bar"}-standard_cut5.step'
            native=import_step(source)
            source_shift=(0.,0.,0.) if kind=='keys' else (0.,0.,shoulder)
            native=native.translate(source_shift)
            sample=norm(native.intersect(crop_mask(centers,cy,zmin,zmax)))
            # Matching notch counts identify side without touching local pads.
            mid=sum(centers)/2
            for i in range(marks):
                cx=mid+(i-(marks-1)/2)*P['id_notch_pitch']
                notch=box_bounds(cx-P['id_notch_width']/2,cx+P['id_notch_width']/2,
                                 cy+P['strip_width']/2-P['id_notch_depth'],
                                 cy+P['strip_width']/2+P['id_notch_depth'],zmin,zmax)
                sample=cut(sample,notch)
            shift=(-centers[0],-cy,-zmin)
            sample=sample.translate(shift)
            name=f'{side}_{kind}_84_nominal'
            assert sample.is_valid and len(sample.solids())==1, (name,len(sample.solids()))
            export_step(sample,out/f'{name}.step')
            export_3mf(sample,out/f'{name}.3mf')
            side_record['parts'].append(dict(name=name,source=str(source.relative_to(ROOT)),
                source_sha256=sha(source),source_to_assembly_mm=list(source_shift),print_translation_mm=list(shift),
                source_z_crop_mm=[zmin,zmax],native_volume_mm3=sample.volume,
                native_valid=True,solids=1))
        records.append(side_record)
    after=audit_preserved();assert before==after
    report=dict(status='PASS',coupon_parameters=P,joint_parameters=INSERT,
                configurations=records,preserved=after)
    (HERE/'build.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
