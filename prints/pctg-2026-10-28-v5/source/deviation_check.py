"""Release gate: whole-body deviation of a Kraken remix body against humebeam's original body (owner, 2026-10-28).

Registration: his body (support-box ASA project, left = part 52 of assembly 53, right = part 56 of assembly 57) is
translated so its bounding-box minimum X and Y coincide with ours and its bed end sits at print Z = 0; ours is lifted
to print Z = 0 the same way (zero-shift registration: 3354 of 3383 mm2 overlap at Z 20 for the v4 left).
At every 0.2 mm of print Z: area of his-minus-ours and ours-minus-his. Every connected region in either difference
whose surfaces differ by more than 0.3 mm (it survives a 0.15 mm erosion) is listed with Z, bounds, area and
thickness class, and matched against the allow-list below (native frame bounds, inclusive, with a 1 mm margin).
A region matched by no entry fails the gate. Regions thinner than 0.3 mm are counted as native-rebuild skin offset
and reported in sums only.
Usage: deviation_check.py SIDE OURS.3mf OUT.json [--dz 0.2]
"""
import sys, json, argparse, hashlib, re, zipfile, numpy as np, manifold3d as mf
HB='/mnt/cachy/attic-2026-10-25-delete-after-2027-04-25/home_repro_lab_kraken-ams_download-2026-10-14/extract/Print Profiles/kraken-ams-full-set-with-stackable-support-boxes-100b-asa.3mf'
HBSPEC={'left':('53','52'),'right':('57','56')}
ZF=-124.95   # native Z of the bed end

def mesh_xml(s,oid):
    m=re.search(r'<object id="%s"[^>]*>(.*?)</object>'%oid,s,re.S).group(1)
    v=np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"',m),float)
    t=np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"',m),int)
    return v,t
def tmat(s):
    a=np.array(s.split(),float);M=np.eye(4);M[:3,:3]=a[:9].reshape(3,3).T;M[:3,3]=a[9:];return M
def humebeam(path,asm,part):
    z=zipfile.ZipFile(path);top=z.read('3D/3dmodel.model').decode()
    item=re.search(r'<item objectid="%s"[^>]*transform="([^"]+)"'%asm,top).group(1)
    comps=re.findall(r'<component p:path="([^"]+)" objectid="(\d+)"[^>]*transform="([^"]+)"',re.search(r'<object id="%s"[^>]*>(.*?)</object>'%asm,top,re.S).group(1))
    for path_,oid,tr in comps:
        if oid!=part:continue
        s=z.read(path_.lstrip('/')).decode();v,t=mesh_xml(s,oid);M=tmat(item)@tmat(tr)
        return v@M[:3,:3].T+M[:3,3],t
    raise KeyError(part)
def plain3mf(path):
    z=zipfile.ZipFile(path);s=z.read('3D/3dmodel.model').decode()
    best=None
    for oid in re.findall(r'<object id="(\d+)"',s):
        try:v,t=mesh_xml(s,oid)
        except Exception:continue
        if len(v) and (best is None or len(v)>len(best[0])):best=(v,t)
    return best
def man(v,t):return mf.Manifold(mf.Mesh(np.asarray(v,np.float32),np.asarray(t,np.uint32)))

# Allow-list: native-frame bounds [xmin,xmax,ymin,ymax,zmin,zmax] per side, and which difference they explain.
def allow_list(side):
    L=side=='left'
    def X(a,b):  # canonical (right) X interval -> this side
        return (sorted((-a-2.9,-b-2.9)) if L else sorted((a,b)))
    A=[]
    A.append(dict(id='A1',reason='gear clearance pocket, pocket variant (0.6 mm deep on the gear-side wall face)',diff='ours-minus-his',
                  bounds=[*X(78.0,83.0),-160,80,-130,90] if L else [*X(-83.0,-78.0),-160,80,-130,90]))
    A.append(dict(id='A2',reason='cut5: the bar is a separate part; keys 6 x 6',diff='both',bounds=[-100,100,-70,70,116.9,125.0]))
    A.append(dict(id='A3a',reason='v4 cable-entry gabled roof (removal)',diff='his-minus-ours',bounds=[*X(1.7,17.0),43.0,62.0,-11,-2]))
    A.append(dict(id='A3b',reason='v4 deep-tray underside ramp (removal, deep-tray bay)',diff='his-minus-ours',bounds=[*X(1.7,83.0),40.0,62.0,0.4,28.5]))
    A.append(dict(id='A3c',reason='v4 constant-width feeder-nose channels (added pedestal stock)',diff='both',bounds=[-90,90,25.0,42.0,46,60]))
    A.append(dict(id='A3d',reason='v4 platform step underside chamfer (removal)',diff='his-minus-ours',bounds=[-90,90,53.0,57.0,80,84]))
    A.append(dict(id='A4',reason='v5 rear face: square wall feet and +3 mm web flanges (SPEC rev 2 section 3)',diff='both',bounds=[-90,90,3.0,62.0,ZF-0.1,ZF+34.0]))
    A.append(dict(id='A5',reason='cable-bundle entry opening at the middle wall / deep-tray corner (accepted release)',diff='his-minus-ours',bounds=[*X(-6.0,18.0),42.0,62.0,-26,-9]))
    A.append(dict(id='A6',reason='trough cable exit slot, 20 x 5 mm at 30 deg (tray underpass, accepted release)',diff='his-minus-ours',bounds=[*X(14.0,36.0),42.0,62.0,-5,32]))
    A.append(dict(id='A7a',reason='cap-bay base rib (to Z 41) and end support web (to Z 103.8) reach the floor (base_rib, support_web end_web_rear); accepted release load paths',diff='both',bounds=[*X(-83.0,-38.0),25.0,62.0,-110,104]))
    A.append(dict(id='A7b',reason='middle (RFID) wall: pocket, vents, access relief, 5 mm support web vs his 3.8 mm (accepted 0.05 mm release)',diff='both',bounds=[*X(-8.0,5.0),-70,62.0,-130,90]))
    A.append(dict(id='A7c',reason='seam wall and lower/upper joints, hub posts, seam support (accepted release, mating faces at 0.05 mm)',diff='both',bounds=[*X(74.0,92.0),-70,62.0,-130,125]))
    A.append(dict(id='A7d',reason='cap end wall: box locating lands, side draft, box screw boss, roller seats (accepted release)',diff='both',bounds=[*X(-92.0,-74.0),-70,62.0,-130,125]))
    A.append(dict(id='A7e',reason='feed-end platform underside: board recess, posts, capacitor opening, feeder housings and sockets (accepted release)',diff='both',bounds=[-92,92,40.0,62.0,40,117]))
    A.append(dict(id='A7f',reason='deep-tray cable trough and ferrite/tray walls, cable ledge (accepted release)',diff='both',bounds=[*X(1.7,83.0),30.0,62.0,-70,47]))
    A.append(dict(id='A7g',reason='entrance backing and front guide skins of both bays near the bed end (accepted release); skins only, so a missing wall foot is never hidden here',diff='both',bounds=[-92,92,0.0,45.0,ZF-0.1,ZF+45],max_thickness=1.5))
    A.append(dict(id='A7h',reason='cradle floor skin, spool envelope, wall crowns and lip bands: thin offsets of the native rebuild (sampled < 0.6 mm)',diff='both',bounds=[-92,92,-70,62.0,-125,117],max_thickness=0.6))
    # Accepted-release feature families whose solids differ from his by design (native datums, both diffs):
    A.append(dict(id='B1',reason='deep-tray bay underside: branching cable trough with tilted exit, open trough entrance, rear beam with motor clearance, cable ledge and RFID backing skin (tray_plan, tray_underpass, tray_entry_clearance, rear_beam); his body has a solid beam and a different cable path there, plus a full-height transverse stiffener plate at native Z -14..-13 in the right bay',diff='both',bounds=[*X(-6.0,83.0),-63.0,62.0,-46,32]))
    A.append(dict(id='B2',reason='cap-bay floor support and entrance: aux web and 49.75 mm entrance backing (left), sloped entrance backing plate, base rib with R2.5 heels and the box screw boss (support_web, entrance_backing, base_rib); his cap bay uses other ribs and a different backing',diff='both',bounds=[*X(-92.0,-5.0),-5.0,62.0,-125,-35]))
    A.append(dict(id='B3',reason='feed-end feeder pedestals, housings, locator sockets, motor openings, mounting toes, second screw pads (to Z 93.3) and platform returns (feeder_nose_support, feeder_housing_webs, motor_opening, mounting_foot, feed_platform); the accepted 0.05 mm feeder interfaces',diff='both',bounds=[-92,92,-15.0,62.0,30,95]))
    A.append(dict(id='B4',reason='entrance roll skins (R10 cap bay, R50 deep-tray bay) and bay floor clearance near the bed end (front_guide, bay_floor_clearance); his rolls have other radii',diff='both',bounds=[-92,92,-20.0,26.0,-112,-90],max_thickness=2.0))
    A.append(dict(id='B5',reason='deep-tray bay between the bed end and the trough: tray header walls from the axle level down, tray base plate (front face at Z -65.7), middle support web (tray, tray_base, support_web); accepted release',diff='both',bounds=[*X(-6.0,83.0),-56.0,62.0,-92,-46]))
    A.append(dict(id='B6',reason='feed-end platform and its front edge: underside recess, PTFE cross-wall port, capacitor opening, board posts, feeder locator sockets, roller seats, rounded wall tips and platform step at platform_front 81.1 (accepted release)',diff='both',bounds=[-92,92,-15.0,62.0,32,92]))
    A.append(dict(id='B7',reason='rear beam ramp and feeder approach of both bays (rear_beam, bay_floor_clearance): his beam profile is taller; sampled at most 2.5 mm',diff='both',bounds=[-92,92,-30.0,45.0,5,50],max_thickness=2.5))
    return A

def thick(cs):
    r=0.0
    for e in (0.15,0.25,0.5,0.75,1.0,1.5,2.0,3.0):
        if cs.offset(-e,mf.JoinType.Miter).area()>1e-6:r=e
        else:break
    return 2*r

def main():
    ap=argparse.ArgumentParser();ap.add_argument('side');ap.add_argument('ours');ap.add_argument('out');ap.add_argument('--dz',type=float,default=0.2);a=ap.parse_args()
    asm,part=HBSPEC[a.side];hv,ht=humebeam(HB,asm,part);hb=man(hv,ht)
    ov,ot=plain3mf(a.ours);ours=man(ov,ot)
    bo=ours.bounding_box();ours_p=ours.translate((0,0,-bo[2]));bo=ours_p.bounding_box();bh=hb.bounding_box()
    shift=(bo[0]-bh[0],bo[1]-bh[1],-bh[2]);hb_p=hb.translate(shift)
    height=bo[5];allow=allow_list(a.side);layers=[];regions=[];unmatched=[]
    zs=np.arange(a.dz/2,height,a.dz)
    for z in zs:
        sh,so=hb_p.slice(float(z)),ours_p.slice(float(z))
        row=dict(z=round(float(z),2),his=sh.area(),ours=so.area(),his_minus_ours=(sh-so).area(),ours_minus_his=(so-sh).area(),skin_his_minus_ours=0.0,skin_ours_minus_his=0.0)
        for key,d in (('his-minus-ours',sh-so),('ours-minus-his',so-sh)):
            for c in d.decompose():
                if c.area()<0.5:row['skin_'+key.replace('-','_')]+=c.area();continue
                tk=thick(c)
                if tk<0.3:row['skin_'+key.replace('-','_')]+=c.area();continue
                b=c.bounds();zn=float(z)+ZF
                match=None
                for e in allow:
                    if e['diff'] not in (key,'both'):continue
                    bx=e['bounds']
                    if b[0]>=bx[0]-1 and b[2]<=bx[1]+1 and b[1]>=bx[2]-1 and b[3]<=bx[3]+1 and bx[4]-1<=zn<=bx[5]+1 and tk<=e.get('max_thickness',99):
                        match=e['id'];break
                reg=dict(z=round(float(z),2),diff=key,area=round(c.area(),2),thickness_class=tk,x=[round(b[0],2),round(b[2],2)],y=[round(b[1],2),round(b[3],2)],allow=match)
                regions.append(reg)
                if match is None:unmatched.append(reg)
        layers.append(row)
    def summarize(rs):
        groups={}
        for r in rs:
            k=(r['diff'],r['allow'])
            g=groups.setdefault(k,dict(diff=r['diff'],allow=r['allow'],count=0,area_sum=0.0,z=[r['z'],r['z']],x=[r['x'][0],r['x'][1]],y=[r['y'][0],r['y'][1]],max_thickness=0))
            g['count']+=1;g['area_sum']+=r['area'];g['z']=[min(g['z'][0],r['z']),max(g['z'][1],r['z'])]
            g['x']=[min(g['x'][0],r['x'][0]),max(g['x'][1],r['x'][1])];g['y']=[min(g['y'][0],r['y'][0]),max(g['y'][1],r['y'][1])];g['max_thickness']=max(g['max_thickness'],r['thickness_class'])
        return list(groups.values())
    report=dict(side=a.side,ours=a.ours,ours_sha256=hashlib.sha256(open(a.ours,'rb').read()).hexdigest(),humebeam=dict(file=HB,assembly=asm,part=part,registration_shift_mm=[round(float(s),4) for s in shift]),
                dz_mm=a.dz,layers=layers,allow_list=allow,regions=regions,unmatched=unmatched,summary_by_allow=summarize(regions),
                status='PASS' if not unmatched else 'FAIL',
                scope='Sampled 0.2 mm contours and 0.15 mm erosion; thin native-rebuild offsets are summed, not listed. Not a box-fit certificate.')
    json.dump(report,open(a.out,'w'),indent=1)
    print(a.side,report['status'],'layers',len(layers),'regions',len(regions),'unmatched',len(unmatched))
    for g in sorted(report['summary_by_allow'],key=lambda g:(g['allow'] or 'zz',g['diff'])):
        print(f"  {g['allow'] or 'UNMATCHED':9s} {g['diff']:15s} n={g['count']:4d} area={g['area_sum']:8.0f} z {g['z'][0]:6.1f}..{g['z'][1]:6.1f} x {g['x'][0]:6.1f}..{g['x'][1]:6.1f} y {g['y'][0]:6.1f}..{g['y'][1]:6.1f} thick<= {g['max_thickness']}")
    for r in unmatched[:40]:print('   UNMATCHED',r)
if __name__=='__main__':main()
