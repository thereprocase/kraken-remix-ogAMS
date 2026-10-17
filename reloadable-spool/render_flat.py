"""Display-only renderer packing: stable exact triangle normals, same positions.
Screen-space derivatives on long, thin CAD triangles produced stippling; this
uses one constant normal per triangle. Facets/positions and print files unchanged.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
SKILL=Path(__file__).resolve().parent/'render_support'
if not SKILL.exists():SKILL=Path('/home/repro/.codex/skills/render')
sys.path.insert(0,str(SKILL/'scripts'))
from prepare import read
from mesh_style import feature_edges
scene=Path(sys.argv[1]);dest=Path(sys.argv[2]);dest.mkdir(parents=True,exist_ok=True);spec=json.loads(scene.read_text());parts=[];prov=[]
for i,part in enumerate(spec['parts']):
 p=(scene.parent/part['mesh']).resolve();v,t=read(p);M=np.array(part.get('transform',np.eye(4)));v=(np.c_[v,np.ones(len(v))]@M.T)[:,:3]
 edges=feature_edges(v,t);flat=v[t].reshape(-1,3);idx=np.arange(len(flat),dtype=np.uint32).reshape(-1,3)
 normals=np.cross(flat[idx[:,1]]-flat[idx[:,0]],flat[idx[:,2]]-flat[idx[:,0]]);normals/=np.linalg.norm(normals,axis=1)[:,None];normals=np.repeat(normals,3,axis=0)
 mapping=np.zeros(len(v),dtype=np.uint32);mapping[t.ravel()]=np.arange(len(flat),dtype=np.uint32);ed=mapping[edges]
 file=f'part-{i}.bin';(dest/file).write_bytes(flat.astype('<f4').tobytes()+idx.astype('<u4').tobytes()+normals.astype('<f4').tobytes()+ed.astype('<u4').tobytes());parts.append({'file':file,'vertices':len(flat),'triangles':len(t),'edges':len(ed),'color':part['color']});prov.append({'input':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'transform':M.tolist(),'display_change':'Duplicate vertices only; exact positions/facets retained. Constant normal per triangle.'})
config={k:spec[k] for k in ('title','subtitle','caption','camera') if k in spec};config['parts']=parts;(dest/'scene.json').write_text(json.dumps(config,indent=2));(dest/'inputs.json').write_text(json.dumps(prov,indent=2))
s=(SKILL/'assets/viewer.html').read_text();s=s.replace('in vec3 pos; in float dev;','in vec3 pos; in float dev; in vec3 nrm; out vec3 faceNormal;').replace('vView = p.xyz; vDev = dev;','vView = p.xyz; vDev = dev; faceNormal = mat3(view)*nrm;').replace('`in vec3 vView; in float vDev;','`in vec3 vView; in float vDev; in vec3 faceNormal;').replace('normalize(cross(dFdx(vView), dFdy(vView)))','normalize(faceNormal)')
s=s.replace('cam.dist*.0022','0.0').replace('p.z -= 0.0004*p.w','p.z -= 0.000006*p.w').replace('cam.dist*.02,cam.dist*6','cam.dist*.5,cam.dist*1.5')
# Omit zero-push hull pass, which would z-fight with back-facing triangles.
s=s.replace('gl.drawElements(gl.TRIANGLES,m.nTri,gl.UNSIGNED_INT,0);\n  gl.disable','/* feature contours supply ink; no hull inflation */\n  gl.disable',1)
start=s.index(' for(const m of models){',s.index('function draw(){'))
end=s.index(' if(models.length)window.renderReady',start)
s=s[:start]+""" gl.enable(gl.CULL_FACE);gl.cullFace(gl.BACK);gl.depthMask(true);
 for(const m of models){
  bind(celProg,m);gl.uniformMatrix4fv(U(celProg,"mvp"),false,mvp);gl.uniformMatrix4fv(U(celProg,"view"),false,view);gl.uniform3fv(U(celProg,"base"),m.info.color);gl.uniform1i(U(celProg,"useDev"),0);gl.uniform1f(U(celProg,"alpha"),1);gl.drawElements(gl.TRIANGLES,m.nTri,gl.UNSIGNED_INT,0);
 }
 gl.depthMask(false);
 for(const m of models){
  bind(lineProg,m,"edges");gl.uniformMatrix4fv(U(lineProg,"mvp"),false,mvp);gl.uniform4fv(U(lineProg,"col"),[.114,.106,.094,1]);gl.drawElements(gl.LINES,m.nEdge,gl.UNSIGNED_INT,0);
 }
 gl.depthMask(true);
"""+s[end:]
(dest/'index.html').write_text(s)
