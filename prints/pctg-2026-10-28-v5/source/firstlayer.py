"""First-layer check of a sliced plate G-code: extrusion islands (object only, brim excluded), area, and a PNG."""
import re, sys, subprocess, numpy as np
from PIL import Image, ImageDraw
gcode, out = sys.argv[1], sys.argv[2]
X=Y=Z=E=0.0; absolute_e=True; layer=0; feature=None; segs=[]; cfg={}
for line in open(gcode, errors='ignore'):
    if line.startswith('; ') and ' = ' in line and not line.startswith('; feature'):
        kv=line[2:].strip().split(' = ',1)
        if len(kv)==2: cfg[kv[0]]=kv[1]
        continue
    if line.startswith('; CHANGE_LAYER'): layer+=1
    if line.startswith('; FEATURE:'): feature=line.split(':',1)[1].strip()
    if layer>1: break
    if line.startswith('M83'): absolute_e=False
    if line.startswith('M82'): absolute_e=True
    if line.startswith('G92'):
        m=re.search(r'E([-\d.]+)',line); E=float(m.group(1)) if m else E; continue
    if line.startswith(('G1 ','G0 ')):
        x=re.search(r'X([-\d.]+)',line); y=re.search(r'Y([-\d.]+)',line); e=re.search(r'E([-\d.]+)',line)
        nx=float(x.group(1)) if x else X; ny=float(y.group(1)) if y else Y
        de=(float(e.group(1))-E if absolute_e else float(e.group(1))) if e else 0.0
        if e: E=float(e.group(1)) if absolute_e else E+de
        if de>0 and layer==1 and (x or y): segs.append((X,Y,nx,ny,feature))
        X,Y=nx,ny
print('brim settings:', {k:cfg.get(k) for k in ('brim_type','brim_width','brim_object_gap','initial_layer_print_height','initial_layer_speed','wall_loops','sparse_infill_density')})
segs=np.array([(a,b,c,d,0 if (f or '').lower().startswith('brim') else 1) for a,b,c,d,f in segs])
print('first layer extrusion segments', len(segs), 'brim', int((segs[:,4]==0).sum()), 'object', int((segs[:,4]==1).sum()))
# raster at 0.2 mm/px over the bed 256 x 256 mm
S=5; img=np.zeros((256*S,256*S),np.uint8); im=Image.fromarray(img); d=ImageDraw.Draw(im)
for a,b,c,e,f in segs:
    if f==1: d.line([(a*S,b*S),(c*S,e*S)], fill=255, width=4)
arr=np.array(im)>0
from scipy import ndimage
lab,n=ndimage.label(arr); sizes=ndimage.sum(arr,lab,range(1,n+1))
print('object first-layer islands (0.2 mm raster, 0.8 mm line):', n, 'areas mm2:', sorted((sizes/(S*S)).round(0).tolist(), reverse=True)[:8], 'total mm2', round(arr.sum()/(S*S)))
col=Image.new('RGB',(256*S,256*S),(244,239,230)); dc=ImageDraw.Draw(col)
for a,b,c,e,f in segs: dc.line([(a*S,b*S),(c*S,e*S)], fill=(250,161,71) if f==0 else (10,90,102), width=3)
col=col.transpose(Image.FLIP_TOP_BOTTOM); col.save(out); print('wrote', out)
