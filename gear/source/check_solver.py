"""Independent membrane energy and circular-annulus torsion benchmarks."""
import numpy as np,json,math
from scipy.sparse.linalg import splu
from stiffness import ROOT,elements,assemble,E,NU,THICKNESS

h=2.;km,_,_=elements(h);xy=np.array([[0,0],[h,0],[h,h],[0,h]])
u=np.column_stack([.01*xy[:,0],np.zeros(4)]).ravel()
energy=float(u@km@u);exact=E/(1-NU*NU)*THICKNESS*.01**2*h*h
assert abs(energy/exact-1)<1e-12
rows=[]
for h in [2.,1.,.5]:
    a,b=20.,80.;n=int(2*b/h);origin=-b
    i,j=np.meshgrid(np.arange(n),np.arange(n));i=i.ravel();j=j.ravel()
    center=np.column_stack([origin+(i+.5)*h,origin+(j+.5)*h]);radius=np.linalg.norm(center,axis=1)
    keep=(radius>a)&(radius<b);i=i[keep];j=j[keep]
    cells=np.column_stack([j*(n+1)+i,j*(n+1)+i+1,(j+1)*(n+1)+i+1,(j+1)*(n+1)+i])
    ids,inverse=np.unique(cells,return_inverse=True);cells=inverse.reshape(-1,4)
    xy=np.column_stack([origin+(ids%(n+1))*h,origin+(ids//(n+1))*h]);radius=np.linalg.norm(xy,axis=1)
    edges=np.concatenate([cells[:,[0,1]],cells[:,[1,2]],cells[:,[2,3]],cells[:,[3,0]]]);edges=np.sort(edges,axis=1)
    unique,count=np.unique(edges,axis=0,return_counts=True);boundary=np.unique(unique[count==1]);outer=boundary[radius[boundary]>(a+b)/2]
    fixed=np.zeros(len(xy),dtype=bool);fixed[boundary]=True;free=np.flatnonzero(~np.repeat(fixed,2))
    km,_,_=elements(h);K=assemble(cells,[(np.ones(len(cells)),km)],2,len(xy))
    angle=1e-4;U=np.zeros((len(xy),2));U[outer,0]=-angle*xy[outer,1];U[outer,1]=angle*xy[outer,0];U=U.ravel()
    rhs=-(K@U)[free];U[free]=splu(K[free][:,free]).solve(rhs);reaction=(K@U).reshape(-1,2)
    torque=np.sum(xy[outer,0]*reaction[outer,1]-xy[outer,1]*reaction[outer,0])
    expected=4*math.pi*(E/(2*(1+NU)))*THICKNESS*a*a*b*b/(b*b-a*a)
    measured=float(torque/angle);error=measured/expected-1
    rows.append(dict(grid_mm=h,measured_Nmm_per_rad=measured,theory_Nmm_per_rad=expected,relative_error=error))
    print(rows[-1],flush=True)
assert abs(rows[-1]['relative_error'])<.02
assert all(abs(b['relative_error'])<abs(a['relative_error']) for a,b in zip(rows,rows[1:]))
(ROOT/'analysis/membrane-benchmarks.json').write_text(json.dumps(dict(constant_strain_patch='PASS',annulus_torsion=rows),indent=2)+'\n')
