"""Editable analytic web with immutable supplied gear/hub interfaces.

Only the web is reconstructed. Source teeth and hub are retained mesh geometry,
not reverse-engineered involutes, threads, or falsely described native surfaces.
"""
from pathlib import Path
import argparse,json,hashlib,math,sys,zipfile
import numpy as np
import manifold3d as mf
from build123d import Solid,Face,Wire,Edge,Plane,Axis,export_step
ROOT=Path(__file__).resolve().parent
from mesh_tools import triangulate,export_3mf,make_manifold

P=dict(disc_thickness=4.0,web_inner_radius=18.0,web_overlap_radius=91.0,
       protected_tooth_band_radius=95.0,spoke_count=8,spoke_width=26.0,
       hub_pad_radius=42.0,window_outer_radius=88.0,window_fillet=3.0,
       spoke_phase_degrees=0.0)

def window_face(p):
    """One four-edge annular window between two constant-width radial spokes."""
    ri,ro=p['hub_pad_radius'],p['window_outer_radius'];half=p['spoke_width']/2
    pitch=2*math.pi/p['spoke_count'];ai,ao=math.asin(half/ri),math.asin(half/ro)
    assert 2*ai<pitch
    def point(r,a):return (r*math.cos(a),r*math.sin(a),0)
    a,b,c,d=point(ri,ai),point(ro,ao),point(ro,pitch-ao),point(ri,pitch-ai)
    wire=Wire([Edge.make_line(a,b),Edge.make_three_point_arc(b,point(ro,pitch/2),c),
               Edge.make_line(c,d),Edge.make_three_point_arc(d,point(ri,pitch/2),a)])
    face=Face(wire)
    return face.fillet_2d(p['window_fillet'],face.vertices())

def analytic_web(variant,p=P):
    outer=Solid.make_cylinder(p['web_overlap_radius'],p['disc_thickness'])
    inner=Solid.make_cylinder(p['web_inner_radius'],p['disc_thickness'])
    web=outer.cut(inner);windows=[]
    if variant=='spokes':
        tool=Solid.extrude(window_face(p),(0,0,p['disc_thickness']))
        for index in range(p['spoke_count']):
            window=tool.rotate(Axis.Z,p['spoke_phase_degrees']+index*360/p['spoke_count'])
            windows.append(window);web=web.cut(window)
    assert web.is_valid and len(web.solids())==1
    return web,windows

def write_stl(v,t,path):
    tri=v[t];norm=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);norm/=np.maximum(np.linalg.norm(norm,axis=1)[:,None],1e-30)
    data=np.zeros(len(t),dtype=np.dtype([('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attribute','<u2')]))
    data['normal']=norm;data['vertices']=tri
    header=b'Kraken analytic web; original source teeth and hub retained'.ljust(80,b' ')
    path.write_bytes(header+len(t).to_bytes(4,'little')+data.tobytes())

def read_stl(path):
    raw=Path(path).read_bytes();n=int.from_bytes(raw[80:84],'little')
    d=np.frombuffer(raw,dtype=np.dtype([('n','<f4',(3,)),('v','<f4',(3,3)),('a','<u2')]),count=n,offset=84)
    v,t=np.unique(d['v'].reshape(-1,3).astype(float),axis=0,return_inverse=True)
    return v,t.reshape(-1,3)

def build(variant,p=P):
    ref=json.loads((ROOT/'REFERENCE.json').read_text());source=Path(ref['path'])
    assert hashlib.sha256(source.read_bytes()).hexdigest()==ref['sha256']
    v,t=read_stl(source);original=make_manifold(v,t)
    web,windows=analytic_web(variant,p)
    from retained_mesh import assemble
    window_meshes=[triangulate(tool,linear=.005,angular=.02) for tool in windows]
    v,t,retention=assemble(v,t,window_meshes,p['disc_thickness'],p['protected_tooth_band_radius'])
    prefix=ROOT/'artifacts'/f'gear-{variant}'
    write_stl(v,t,prefix.with_suffix('.stl'))
    # Validate the actual float32 STL delivered to the slice harness.
    v,t=read_stl(prefix.with_suffix('.stl'));delivered=make_manifold(v,t)
    assert delivered.status()==mf.Error.NoError and len(delivered.decompose())==1
    export_3mf(None,prefix.with_suffix('.3mf'),mesh=(v,t))
    # Preserve every supplied float32 coordinate exactly in the XML as well.
    path=prefix.with_suffix('.3mf')
    with zipfile.ZipFile(path) as archive:entries={name:archive.read(name) for name in archive.namelist()}
    import xml.etree.ElementTree as ET
    ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
    doc=ET.fromstring(entries['3D/3dmodel.model'])
    for vertex,point in zip(doc.findall('.//m:vertex',ns),v):
        for key,value in zip(['x','y','z'],point):vertex.set(key,format(value,'.17g'))
    entries['3D/3dmodel.model']=ET.tostring(doc,encoding='utf-8',xml_declaration=True)
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,data in entries.items():archive.writestr(name,data)
    np.savez(str(prefix)+'_mesh.npz',v=v,t=t)
    export_step(web,str(prefix)+'-analytic-web.step')
    report=dict(variant=variant,parameters=p,source=ref,retention=retention,volume_mm3=delivered.volume(),
                original_volume_mm3=original.volume(),mesh_valid=True,connected_components=1,
                native_web_valid=web.is_valid,native_web_solids=len(web.solids()),
                bounds_mm=list(delivered.bounding_box()),interface_provenance='Retained supplied source mesh; no analytic tooth/thread reconstruction',
                status='GEOMETRY_CANDIDATE_PENDING_INTERFACE_AND_STIFFNESS_CHECKS')
    (ROOT/'artifacts'/f'gear-{variant}.json').write_text(json.dumps(report,indent=2)+'\n')
    print(variant,report['volume_mm3'],'mm3',len(t),'triangles',flush=True)
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('variant',choices=['plain','spokes','all'])
    args=parser.parse_args()
    for variant in (['plain','spokes'] if args.variant=='all' else [args.variant]):build(variant)
