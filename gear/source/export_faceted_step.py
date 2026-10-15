"""Complete gear STEP is a faceted BRep; separate web STEP is analytic.

This preserves the mesh-defined tooth/thread surfaces without fitting them.
It is intentionally not advertised as the unavailable original native CAD.
"""
from pathlib import Path
import sys,json,time,hashlib
from OCP.StlAPI import StlAPI_Reader
from OCP.TopoDS import TopoDS_Shape,TopoDS
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing,BRepBuilderAPI_MakeSolid
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SHELL
from OCP.BRep import BRep_Tool
from build123d import Solid,export_step
from gear_web import ROOT,read_stl,make_manifold

for variant in sys.argv[1:]:
    start=time.monotonic();path=ROOT/'artifacts'/f'gear-{variant}.stl'
    source=TopoDS_Shape();reader=StlAPI_Reader();assert reader.Read(source,str(path))
    print(variant,'STL surfaces read',time.monotonic()-start,flush=True)
    sewing=BRepBuilderAPI_Sewing(1e-7);sewing.Add(source);sewing.Perform()
    sewn=sewing.SewedShape();explorer=TopExp_Explorer(sewn,TopAbs_SHELL);shells=[]
    while explorer.More():shells.append(TopoDS.Shell(explorer.Current()));explorer.Next()
    assert len(shells)==1,len(shells)
    assert BRep_Tool.IsClosed_s(shells[0])
    shape=Solid(BRepBuilderAPI_MakeSolid(shells[0]).Solid())
    assert shape.is_valid and len(shape.solids())==1
    print(variant,'valid faceted solid',len(shape.faces()),time.monotonic()-start,flush=True)
    v,t=read_stl(path);volume=make_manifold(v,t).volume();error=abs(shape.volume-volume)
    assert error<1e-4,(shape.volume,volume)
    dst=path.with_suffix('.step');export_step(shape,dst)
    report=dict(variant=variant,representation='Complete single-solid faceted BRep from the delivered STL; analytic editable web is supplied separately',
                valid=True,solids=1,faces=len(shape.faces()),volume_mm3=shape.volume,stl_volume_mm3=volume,volume_difference_mm3=error,
                stl_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),step_sha256=hashlib.sha256(dst.read_bytes()).hexdigest(),elapsed_seconds=time.monotonic()-start)
    (ROOT/'artifacts'/f'gear-{variant}-step-check.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report,flush=True)
