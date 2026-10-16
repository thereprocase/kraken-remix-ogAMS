"""Independent checks of delivered two-key coupons and local production stock."""
from pathlib import Path
import json
import sys
import numpy as np
import manifold3d as mf

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT / "cad"))
sys.path.insert(0,str(HERE.parent/'cut5_fit'))
from build123d import import_step
from validate_coupons import read_mesh
from mesh_ops import make_manifold
from build_alignment import audit_preserved, sha


def hits(mesh, axis, center, z, reach=9.):
    start=[center,0.,z];end=start.copy()
    start[axis]-=reach;end[axis]+=reach
    return sorted(set(round(h.position[axis],6) for h in mesh.ray_cast(start,end)))


def part_audit(name,height):
    path=HERE/'artifacts'/name
    native=import_step(str(path)+'.step')
    v,mesh=read_mesh(Path(str(path)+'.3mf'))
    assert native.is_valid and len(native.solids())==1
    assert len(mesh.decompose())==1
    assert abs(v[:,2].min())<1e-5 and abs(v[:,2].max()-height)<1e-5
    assert abs(np.ptp(v[:,0])-104.)<1e-5
    assert abs(native.volume-mesh.volume())<.1
    prior=mesh.slice(.001);bed=prior.area();islands=[];bridges=[]
    for z in np.arange(.2,height,.2):
        section=mesh.slice(float(z))
        count=sum((piece ^ prior.offset(.2)).area()<1e-7 for piece in section.decompose())
        if count:islands.append(dict(z_mm=float(z),count=int(count)))
        extra=section-prior.offset(.2)
        if extra.area()>.01:bridges.append(dict(z_mm=float(z),area_mm2=extra.area()))
        prior=section
    assert bed>400 and not islands
    return native,mesh,dict(name=name,status='PASS',valid_native_solids=1,manifold_components=1,
        bounds_mm=[v.min(axis=0).tolist(),v.max(axis=0).tolist()],bed_area_mm2=bed,
        native_mesh_volume_error_mm3=abs(native.volume-mesh.volume()),
        unsupported_layer_islands=islands,overhang_or_bridge_layers=bridges)


def main():
    metadata=json.loads((HERE/'build.json').read_text())
    configs=[];parts=[]
    for config in metadata['configurations']:
        side=config['side']
        kn,keys,kr=part_audit(f'{side}_keys_84_nominal',6.)
        sn,sockets,sr=part_audit(f'{side}_sockets_84_nominal',8.)
        parts.extend([kr,sr])
        seated=sockets.translate([0.,0.,3.])
        source_record=next(p for p in config['parts'] if '_sockets_' in p['name'])
        reference=ROOT/source_record['source'].replace('.step','.3mf')
        _, source=read_mesh(reference)
        source=source.translate(source_record['source_to_assembly_mm']).translate(source_record['print_translation_mm'])
        key_centers=[];socket_centers=[];interfaces=[]
        for center in [0.,84.]:
            gaps=[];taper=[]
            for axis in [0,1]:
                kh=hits(keys,axis,center,4.2);sh=hits(sockets,axis,center,1.2)
                # The left outer pad also retains a nearby production X wall.
                # Select cavity crossings separately from its outside skin.
                sh=[x for x in sh if abs(x-(center if axis==0 else 0.))<4.]
                assert len(kh)==2 and len(sh)==2,(side,center,axis,kh,sh)
                assert abs(kh[1]-kh[0]-6.)<1e-5
                assert abs(sh[1]-sh[0]-6.3)<1e-5
                gaps.extend([kh[0]-sh[0],sh[1]-kh[1]])
                if axis==0:
                    key_centers.append(sum(kh)/2);socket_centers.append(sum(sh)/2)
                kh=hits(keys,axis,center,3.3);sh=hits(sockets,axis,center,.3)
                sh=[x for x in sh if abs(x-(center if axis==0 else 0.))<4.]
                taper.extend([kh[0]-sh[0],sh[1]-kh[1]])
            assert max(abs(g-.15) for g in gaps)<1e-5
            assert max(abs(g) for g in taper)<1e-5
            # Compare every wall ray whose production exit lies within the
            # local pad. Far-field exits are deliberately truncated by the crop.
            wall_samples=[];truncated_samples=[]
            for dz in [.001,.2,.65,1.,2.,2.9,3.149]:
                for axis in [0,1]:
                    for lateral in [-1.5,0.,1.5]:
                        for sign in [-1,1]:
                            start=[center,0.,dz];start[1-axis]+=lateral
                            end=start.copy();end[axis]+=sign*200.
                            a=sockets.ray_cast(start,end);b=source.ray_cast(start,end)
                            assert len(a)>=2 and len(b)>=2
                            thickness=abs(a[1].position[axis]-a[0].position[axis])
                            original=abs(b[1].position[axis]-b[0].position[axis])
                            origin=center if axis==0 else 0.
                            local_exit=abs(b[1].position[axis]-origin)<(10. if axis==0 else 8.)-1e-4
                            row=dict(z_mm=dz,axis=axis,lateral_mm=lateral,direction=sign,
                                     wall_mm=thickness,production_wall_mm=original)
                            assert thickness>=1.35
                            if local_exit:
                                error=max(abs(a[i].position[axis]-b[i].position[axis]) for i in [0,1])
                                assert error<=.05 and abs(thickness-original)<=.05
                                wall_samples.append(dict(**row,surface_error_mm=error))
                            else:truncated_samples.append(row)
            roofs=[]
            for dx in [-2.,0.,2.]:
                for y in [-2.,0.,2.]:
                    start=[center+dx,y,-1.];end=[center+dx,y,9.]
                    a=sockets.ray_cast(start,end);b=source.ray_cast(start,end)
                    assert len(a)==2 and len(b)>=2
                    assert max(abs(a[i].position[2]-b[i].position[2]) for i in [0,1])<.05
                    roofs.append(a[1].position[2]-a[0].position[2])
            assert min(roofs)>=4.84999
            # Exact shoulder-plane crop keeps source contact footprint inside pads.
            region=mf.CrossSection.square([20.,16.],center=True).translate([center,0.])
            coupon_shoulder=sockets.slice(.001)^region
            source_shoulder=source.slice(.001)^region
            delta=(coupon_shoulder-source_shoulder)+(source_shoulder-coupon_shoulder)
            assert abs(delta.area())<.001
            contact=coupon_shoulder ^ keys.slice(2.999)
            assert contact.area()>60 and contact.area()/coupon_shoulder.area()>.999
            interfaces.append(dict(center_x_mm=center,four_running_gaps_mm=gaps,
                four_taper_gaps_mm=taper,minimum_retained_local_wall_mm=min(r['wall_mm'] for r in wall_samples),
                maximum_production_wall_surface_error_mm=max(r['surface_error_mm'] for r in wall_samples),
                wall_samples=wall_samples,truncated_far_field_wall_samples=truncated_samples,
                minimum_roof_mm=min(roofs),
                shoulder_vs_production_area_difference_mm2=abs(delta.area()),
                shoulder_contact_area_mm2=contact.area()))
        assert abs(key_centers[1]-key_centers[0]-84.)<1e-5
        assert abs(socket_centers[1]-socket_centers[0]-84.)<1e-5
        sweep=[abs((keys ^ seated.translate([0.,0.,float(z)])).volume()) for z in np.linspace(0,4,41)]
        assert max(sweep)<.001
        native_overlap=[]
        for dz in [0.,.1,1.,3.2,4.]:
            overlap=kn.intersect(sn.translate((0.,0.,3.+dz)))
            native_overlap.append(abs(overlap.volume) if overlap is not None else 0.)
        assert max(native_overlap)<1e-7
        registration=[]
        for shift in [[.05,0.,0.],[-.05,0.,0.],[0.,.05,0.],[0.,-.05,0.],[0.,0.,-.05]]:
            v=(keys ^ seated.translate(shift)).volume();assert v>.001
            registration.append(dict(shift_mm=shift,intersection_mm3=v))
        # Keep the first key and base unchanged; shift only the second pin by
        # 0.30 mm to demonstrate that the test catches a pitch error.
        key_region=mf.Manifold.cube([10.,10.,3.1]).translate([79.,-5.,3.])
        second=keys ^ key_region
        bad_keys=(keys-second)+second.translate([.3,0.,0.])
        negative=(bad_keys ^ seated).volume();assert negative>.1
        configs.append(dict(side=side,status='PASS',key_centers_x_mm=key_centers,
            socket_centers_x_mm=socket_centers,interfaces=interfaces,
            maximum_mesh_path_intersection_mm3=max(sweep),mesh_intersection_tolerance_mm3=.001,
            mesh_path_samples=41,maximum_native_path_intersection_mm3=max(native_overlap),
            native_path_samples=5,registration=registration,
            second_key_pitch_error_030mm_collision_mm3=negative))
    report=dict(status='PASS',parts=parts,configurations=configs,preserved=audit_preserved(),
        hashes={str(p.relative_to(HERE)):sha(p) for p in sorted((HERE/'artifacts').iterdir())},
        source_script_hashes={name:sha(HERE/name) for name in ['build_alignment.py','validate_alignment.py']})
    (HERE/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
