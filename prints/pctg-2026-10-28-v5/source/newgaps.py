"""Gaps narrower than 2R created by v5: per 0.25 mm layer (native Z), the closing residue of the v5 section that lies
within 2 mm of material v5 added over v4. Prints clusters with native bounds. Usage: newgaps.py side [R]"""
import sys, numpy as np, manifold3d as mf
A='/home/repro/lab/kraken-ams/body-v5-agent/work/v5/%s/artifacts/%s'
def load(p):
    d=np.load(p); return mf.Manifold(mf.Mesh(np.asarray(d['v'],np.float32),np.asarray(d['t'],np.uint32)))
side=sys.argv[1]; R=float(sys.argv[2]) if len(sys.argv)>2 else 1.5
v5=load(A%(side,f'{side}_body_pocket_cut5_v5_display.npz')); v4=load(A%(side,f'{side}_body_pocket_cut5_printable_display.npz'))
lo,hi=v5.bounding_box()[2],v5.bounding_box()[5]
rows=[]
for z in np.arange(lo+0.15,hi,0.25):
    s5=v5.slice(float(z)); s4=v4.slice(float(z))
    added=s5-s4
    if added.area()<0.5: continue
    res=s5.offset(R,mf.JoinType.Round).offset(-R,mf.JoinType.Round)-s5
    near=res ^ added.offset(2.0,mf.JoinType.Round)
    res4=s4.offset(R,mf.JoinType.Round).offset(-R,mf.JoinType.Round)-s4
    new=near - res4.offset(0.3,mf.JoinType.Round)
    for c in new.decompose():
        if c.area()<1.0: continue
        b=c.bounds(); rows.append((float(z),c.area(),b))
# cluster by overlapping bounds and consecutive z
cl=[]
for z,a,b in rows:
    for c in cl:
        if z-c['z1']<=0.6 and b[0]<c['x1']+1 and b[2]>c['x0']-1 and b[1]<c['y1']+1 and b[3]>c['y0']-1:
            c['z1']=z;c['x0']=min(c['x0'],b[0]);c['x1']=max(c['x1'],b[2]);c['y0']=min(c['y0'],b[1]);c['y1']=max(c['y1'],b[3]);c['a']=max(c['a'],a);c['n']+=1;break
    else: cl.append(dict(z0=z,z1=z,x0=b[0],x1=b[2],y0=b[1],y1=b[3],a=a,n=1))
print(side,'R',R,': new gap clusters next to v5 additions:',len(cl))
for c in sorted(cl,key=lambda c:-c['a']*c['n']):
    print(f"  native Z {c['z0']:8.2f}..{c['z1']:8.2f} (print {c['z0']+124.95:6.1f}..{c['z1']+124.95:6.1f})  X {c['x0']:7.2f}..{c['x1']:7.2f}  Y {c['y0']:7.2f}..{c['y1']:7.2f}  max area {c['a']:6.1f} mm2 over {c['n']} layers")
