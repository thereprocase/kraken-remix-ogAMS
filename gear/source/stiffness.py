"""Comparative linear plate/membrane FE evidence, not print qualification.

Q4 plane stress for in-plane torsion. Cartesian MITC4 assumed edge shear for
Reissner-Mindlin bending. Independently implemented; no external FE package.
Structured cells approximate the actual section boundaries; refine the grid.
"""
from pathlib import Path
import argparse,json,math,time,sys,gc,hashlib
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import splu
from gear_web import ROOT,read_stl,make_manifold

E=2000.;NU=.38;THICKNESS=4.;WALL_WIDTH=.42+4*.45
RIM=96.;CLAMP=18.

def basis(xi,eta,h):
    sx=np.array([-1,1,1,-1]);sy=np.array([-1,-1,1,1])
    return .25*(1+sx*xi)*(1+sy*eta),.5/h*sx*(1+sy*eta),.5/h*sy*(1+sx*xi)

def elements(h,E=E,nu=NU,t=THICKNESS):
    D=E/(1-nu*nu)*np.array([[1,nu,0],[nu,1,0],[0,0,(1-nu)/2]])
    membrane=np.zeros((8,8));bend=np.zeros((12,12));shear=np.zeros((12,12))
    def raw(xi,eta):
        n,dx,dy=basis(xi,eta,h);b=np.zeros((2,12));b[0,0::3]=dx;b[1,0::3]=dy
        b[0,1::3]=-n;b[1,2::3]=-n
        return b
    for xi in [-1/math.sqrt(3),1/math.sqrt(3)]:
        for eta in [-1/math.sqrt(3),1/math.sqrt(3)]:
            n,dx,dy=basis(xi,eta,h);weight=h*h/4
            b=np.zeros((3,8));b[0,0::2]=dx;b[1,1::2]=dy;b[2,0::2]=dy;b[2,1::2]=dx
            membrane+=b.T@D@b*t*weight
            b=np.zeros((3,12));b[0,1::3]=dx;b[1,2::3]=dy;b[2,1::3]=dy;b[2,2::3]=dx
            bend+=b.T@D@b*t**3/12*weight
            b=np.zeros((2,12))
            b[0]=.5*(1-eta)*raw(0,-1)[0]+.5*(1+eta)*raw(0,1)[0]
            b[1]=.5*(1-xi)*raw(-1,0)[1]+.5*(1+xi)*raw(1,0)[1]
            shear+=b.T@b*(5/6*E/(2*(1+nu))*t)*weight
    return membrane,bend,shear

def polygon_inside(points,polygon):
    p=np.asarray(polygon);lo=p.min(0);hi=p.max(0)
    ids=np.flatnonzero(np.all((points>=lo)&(points<=hi),axis=1));q=points[ids];result=np.zeros(len(points),dtype=bool)
    inside=np.zeros(len(q),dtype=bool)
    for a,b in zip(p,np.roll(p,-1,axis=0)):
        if abs(b[1]-a[1])<1e-14:continue
        crossing=((a[1]>q[:,1])!=(b[1]>q[:,1]))&(q[:,0]<(b[0]-a[0])*(q[:,1]-a[1])/(b[1]-a[1])+a[0])
        inside^=crossing
    result[ids]=inside
    return result

def mesh(variant,h):
    ref=json.loads((ROOT/'REFERENCE.json').read_text())
    path=ref['path'] if variant=='original' else ROOT/'artifacts'/f'gear-{variant}.stl'
    v,t=read_stl(path);section=make_manifold(v,t).slice(2.).simplify(.001)
    holes=[]
    for p in section.to_polygons():
        p=np.asarray(p);area=np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))/2
        if area<0:holes.append(p)
    n=int(math.ceil(2*RIM/h));origin=-n*h/2
    ix,iy=np.meshgrid(np.arange(n),np.arange(n));centers=np.column_stack([origin+(ix.ravel()+.5)*h,origin+(iy.ravel()+.5)*h])
    occupied=np.linalg.norm(centers,axis=1)<=RIM
    for p in holes:occupied&=~polygon_inside(centers,p)
    ids=np.flatnonzero(occupied);i=ix.ravel()[ids];j=iy.ravel()[ids];centers=centers[ids]
    cells=np.column_stack([j*(n+1)+i,j*(n+1)+i+1,(j+1)*(n+1)+i+1,(j+1)*(n+1)+i])
    nodes,inverse=np.unique(cells,return_inverse=True);cells=inverse.reshape(-1,4)
    xy=np.column_stack([origin+(nodes%(n+1))*h,origin+(nodes//(n+1))*h])
    distance=RIM-np.linalg.norm(centers,axis=1)
    for p in holes:
        for a,b in zip(p,np.roll(p,-1,axis=0)):
            ab=b-a;u=np.clip((centers-a)@ab/max(ab@ab,1e-30),0,1)
            distance=np.minimum(distance,np.linalg.norm(centers-a-u[:,None]*ab,axis=1))
    return xy,cells,distance

def assemble(cells,parts,ndof,nodes):
    indices=(cells[:,:,None]*ndof+np.arange(ndof)).reshape(len(cells),-1)
    size=indices.shape[1]
    values=sum(factors[:,None,None]*matrix for factors,matrix in parts)
    row=np.repeat(indices,size,axis=1).ravel();col=np.tile(indices,(1,size)).ravel()
    return coo_matrix((values.ravel(),(row,col)),shape=(nodes*ndof,nodes*ndof)).tocsc()

def loads(xy,ndof):
    radius=np.linalg.norm(xy,axis=1);theta=np.arctan2(xy[:,1],xy[:,0]);band=(radius>=93)&(radius<=95.5)
    cases=[];columns=[]
    if ndof==2:
        masks=[('distributed_torque',band)]
        masks += [(f'local_torque_{angle:03}',band&(abs(np.angle(np.exp(1j*(theta-math.radians(angle)))))<=math.radians(7.5))) for angle in range(0,360,15)]
        for name,mask in masks:
            assert mask.any();f=np.zeros((len(xy),2));f[mask,0]=-xy[mask,1];f[mask,1]=xy[mask,0]
            f/=np.sum(radius[mask]**2);cases.append(name);columns.append(f.ravel())
    else:
        for name,weights in [('ring_axial_force',band.astype(float)),('ring_tilt_x',band*xy[:,1]),('ring_tilt_y',band*(-xy[:,0]))]:
            f=np.zeros((len(xy),3));den=weights.sum() if name=='ring_axial_force' else np.sum(weights**2)
            f[:,0]=weights/den;cases.append(name);columns.append(f.ravel())
        for angle in range(0,360,15):
            mask=band&(abs(np.angle(np.exp(1j*(theta-math.radians(angle)))))<=math.radians(7.5));assert mask.any()
            f=np.zeros((len(xy),3));f[mask,0]=1/mask.sum();cases.append(f'local_bending_{angle:03}');columns.append(f.ravel())
    return cases,np.column_stack(columns)

def solve(variant,h,core):
    start=time.monotonic();xy,cells,dist=mesh(variant,h);n=len(xy)
    # Ten solid skin layers total: 2 mm of 4 mm. Remaining 2 mm core is
    # homogenized. Local five-perimeter regions retain full material stiffness.
    solid=dist<=WALL_WIDTH
    af=np.where(solid,1.,.5+.5*core)
    df=np.where(solid,1.,.875+.125*core)
    km,kb,ks=elements(h);rows=[]
    for mode,ndof,parts in [('in_plane',2,[(af,km)]),('out_of_plane',3,[(df,kb),(af,ks)])]:
        K=assemble(cells,parts,ndof,n);fixed=np.linalg.norm(xy,axis=1)<=CLAMP
        free=np.flatnonzero(~np.repeat(fixed,ndof));names,F=loads(xy,ndof)
        reduced=K[free][:,free];solver=splu(reduced)
        U=solver.solve(F[free]);residual=float(np.linalg.norm(reduced@U-F[free])/np.linalg.norm(F[free]))
        assert residual<1e-6,residual
        compliance=np.sum(F[free]*U,axis=0);assert np.all(compliance>0)
        for name,c in zip(names,compliance):rows.append(dict(mode=mode,load=name,compliance=float(c),stiffness=float(1/c),relative_solver_residual=residual))
        print(variant,h,core,mode,'solved',len(free),'DOFs',flush=True)
        del K,reduced,solver,U;gc.collect()
    source_path=Path(json.loads((ROOT/'REFERENCE.json').read_text())['path']) if variant=='original' else ROOT/'artifacts'/f'gear-{variant}.stl'
    result=dict(input_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),variant=variant,grid_mm=h,core_modulus_fraction=core,nodes=n,elements=len(cells),
                represented_area_mm2=len(cells)*h*h,full_perimeter_area_fraction=float(solid.mean()),
                elapsed_seconds=time.monotonic()-start,checks=rows,
                assumptions=dict(E_MPa=E,poisson=NU,thickness_mm=THICKNESS,wall_width_mm=WALL_WIDTH,
                                 clamp_radius_mm=CLAMP,load_band_mm=[93,95.5],section_z_mm=2.,
                                 outer_trim_radius_mm=RIM,source_polygon_simplification_mm=.001,
                                 print_model='Isotropic homogenized core; 1mm solid bottom and top skin; five full-material wall widths. Not resolved toolpaths or calibrated PETG.'))
    path=ROOT/'analysis'/f'stiffness-{variant}-h{h:g}-core{core:g}.json';path.write_text(json.dumps(result,indent=2)+'\n')
    return result

def benchmarks():
    h=2.;km,kb,ks=elements(h,E=1000.,nu=0.)
    xy=np.array([[0,0],[h,0],[h,h],[0,h]])
    rigid=np.column_stack([np.tile([1,0],4),np.tile([0,1],4),np.column_stack([-xy[:,1],xy[:,0]]).ravel()])
    assert np.max(abs(km@rigid))<1e-8
    plate=np.zeros((12,3));plate[0::3,0]=1
    plate[0::3,1]=xy[:,0];plate[1::3,1]=1
    plate[0::3,2]=xy[:,1];plate[2::3,2]=1
    assert np.max(abs((kb+ks)@plate))<1e-8
    eigen=np.linalg.eigvalsh(kb+ks);assert sum(eigen>1e-7)==9,eigen
    u=np.zeros(12);u[0::3]=xy[:,0]**2/2;u[1::3]=xy[:,0]
    exact=1000*THICKNESS**3/12*h*h
    assert abs(u@(kb+ks)@u/exact-1)<1e-10
    # Slender beam limit, nu=0 eliminates plate/beam Poisson discrepancy.
    h=2.;nx,ny=50,5
    x,y=np.meshgrid(np.arange(nx+1)*h,np.arange(ny+1)*h);xy=np.column_stack([x.ravel(),y.ravel()])
    i,j=np.meshgrid(np.arange(nx),np.arange(ny));i=i.ravel();j=j.ravel()
    cells=np.column_stack([j*(nx+1)+i,j*(nx+1)+i+1,(j+1)*(nx+1)+i+1,(j+1)*(nx+1)+i])
    km,kb,ks=elements(h,E=2000.,nu=0.);K=assemble(cells,[(np.ones(len(cells)),kb+ks)],3,len(xy))
    fixed=xy[:,0]==0;free=np.flatnonzero(~np.repeat(fixed,3));f=np.zeros((len(xy),3));tip=xy[:,0]==100
    weights=np.ones(tip.sum());weights[[0,-1]]=.5;f[tip,0]=weights/weights.sum();f=f.ravel()
    u=splu(K[free][:,free]).solve(f[free]);measured=float(f[free]@u)
    exact=100**3/(3*2000*(10*THICKNESS**3/12))+100/((5/6)*1000*10*THICKNESS)
    assert abs(measured/exact-1)<.01,(measured,exact)
    result=dict(rigid_modes='PASS',plate_positive_nonrigid_modes=9,constant_curvature_patch='PASS',
                cantilever_measured_mm_per_N=measured,cantilever_theory_mm_per_N=exact,relative_error=measured/exact-1)
    (ROOT/'analysis/solver-benchmarks.json').write_text(json.dumps(result,indent=2)+'\n');print(result,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--variant',choices=['original','plain','spokes','all'],default='all');p.add_argument('--grid',type=float,default=2.);p.add_argument('--core',type=float,nargs='+',default=[1.,.5]);p.add_argument('--benchmarks-only',action='store_true');a=p.parse_args()
    benchmarks()
    if not a.benchmarks_only:
        for variant in (['original','plain','spokes'] if a.variant=='all' else [a.variant]):
            for core in a.core:solve(variant,a.grid,core)
