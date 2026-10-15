"""Left half: one mirrored instance of the shared design, with functional overrides."""
from copy import deepcopy
from pathlib import Path
import argparse,json
from right import P as RIGHT
from mechanical_body import build
from native_features import export_stage

LEFT_OVERRIDES = {'nonfeed_support_width': 49.75,
 'aux_support_web': True,
 'case_locating_thickness': 1.67,
 'case_locating_edge_radius': 3.35,
 'cap_faces_positive': True,
 'rfid_access_depth': 1.45,
 'rfid_connector_stop_setback': 0.38,
 'rfid_connector_stop_draft': 2.65,
 'ferrite_holder': False,
 'main_board_posts': False,
 'case_feed_center_offset': 12.83,
 'case_feed_end_offset': 30.4,
 'mirror': True,
 'mirror_translation': -2.9}
P = {**deepcopy(RIGHT), **LEFT_OVERRIDES}

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--stage',default='M4');a.add_argument('--gear-pocket',action='store_true');args=a.parse_args()
 root=Path(__file__).resolve().parent;shape=build(P,args.stage,args.gear_pocket)
 label=args.stage+('_gear_edit' if args.gear_pocket else '')
 report=export_stage(shape,root,'left',label)
 (root/'reports'/f'left_{label}_build.json').write_text(json.dumps(report,indent=2))
 print(f"left {label}: {report['solids']} valid solid; {report['volume_mm3']:.3f} mm3; STEP and 3MF exported")
