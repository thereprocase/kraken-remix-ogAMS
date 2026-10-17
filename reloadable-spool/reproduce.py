"""Regenerate in a scratch copy. Does not slice, publish or contact a printer."""
from pathlib import Path
import subprocess,sys,os,json,importlib.metadata as md
R=Path(__file__).resolve().parent
for p in ('analysis','artifacts','renders'):(R/p).mkdir(exist_ok=True)
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
steps=['build.py','check_thread.py','check_paths.py','check_tool.py','package_assembly.py','validate.py']
for step in steps:subprocess.run([sys.executable,str(R/step)],check=True,env=env)
record={'python':sys.version,'packages':{p:md.version(p) for p in ['build123d','numpy','scipy','manifold3d']+(md.packages_distributions().get('OCP') or [])},'steps':steps,'status':'PASS available native/export/source/path checks; installed drive clearance UNVERIFIED','scope':'No physical fit, clamp strength or slicing certification.'}
(R/'analysis/REPRODUCTION.json').write_text(json.dumps(record,indent=2)+'\n')
print(record)
