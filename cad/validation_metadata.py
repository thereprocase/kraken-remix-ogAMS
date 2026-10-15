"""Bind validation results to the actual exported artifacts and native drivers."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
ROOT=Path(__file__).resolve().parent

def provenance(side,stage):
 files=[ROOT/f'artifacts/{side}_{stage}{suffix}' for suffix in ['.step','.3mf','_display.npz']]
 files += [ROOT/f'analysis/{side}_source.npz']
 files += [ROOT/name for name in sorted(set([f'{side}.py','right.py']))+['mechanical_body.py','hardware_features.py','hardware_datums.py','native_features.py','export_guards.py']]
 return dict(validated_at_utc=datetime.now(timezone.utc).isoformat(),sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.exists()})
