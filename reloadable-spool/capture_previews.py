"""Reproducible render skill invocation with thin-plate depth settings."""
import subprocess,sys,json
from pathlib import Path
R=Path(__file__).resolve().parent;S=(R/'render_support/scripts') if (R/'render_support/scripts').exists() else Path('/home/repro/.codex/skills/render/scripts')
subprocess.run([sys.executable,str(R/'render_previews.py')],check=True)
for mode in ('assembled','exploded','section'):
 work=R/'renders'/f'{mode}-work'
 subprocess.run([sys.executable,str(R/'render_flat.py'),str(R/f'{mode}.scene.json'),str(work)],check=True)
 p=work/'index.html';s=p.read_text();s=s.replace('cam.dist*.0022','cam.dist*.00012').replace('p.z -= 0.0004*p.w','p.z -= 0.000006*p.w').replace('cam.dist*.02,cam.dist*6','cam.dist*.5,cam.dist*1.5');p.write_text(s)
 subprocess.run(['node',str(S/'capture.mjs'),str(work),str(R/'renders'/f'{mode}.png')],check=True)
(R/'renders/settings.json').write_text(json.dumps({'geometry_change':False,'hull_push_distance_factor':0.0,'surface_normals':'Exact per-triangle normals, display-only duplicated vertices','line_clip_depth_bias':.000006,'near_far_distance_factors':[.5,1.5],'reason':'Thin 1.2 mm backing requires reduced silhouette hull extrusion and edge depth bias to prevent hidden gear facets showing through.'},indent=2)+'\n')
