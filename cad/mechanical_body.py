"""Native mechanical features. No mesh, recovered outlines, or fitted vertices.
Sketch coordinates are arithmetic on named mechanical parameters and datums.
"""
import math
from build123d import Solid,Plane,Compound,Vector,Edge,Wire,Face,Axis
from native_features import profile_extrusion,box_bounds,sketch_wire

def norm(s):
    return Compound(list(s)) if type(s).__name__=='ShapeList' else s

def union(parts,names=None):
    """Fuse native features with a useful name on every failure."""
    from native_features import normalize_native_topology
    import inspect
    caller=inspect.currentframe().f_back.f_code.co_name
    labels=names or [f'{caller} part {i+1}' for i in range(len(parts))]
    s=parts[0]
    assert s.is_valid, f'Invalid input feature: {labels[0]}'
    for index,part in enumerate(parts[1:],1):
        label=labels[index]
        assert part.is_valid, f'Invalid input feature: {label}'
        # Tangent floor/support faces need consistent OCCT p-curves before
        # the multi-feature massing fuse. Transfer stays entirely in memory.
        if names:
            s=normalize_native_topology(s);part=normalize_native_topology(part)
        previous=s.volume
        result=norm(s.fuse(part))
        if not result.is_valid:
            result=norm(normalize_native_topology(s).fuse(normalize_native_topology(part)))
        assert result.is_valid, f'Invalid union while adding {label}'
        assert result.volume>=max(previous,part.volume)-.001, f'Union lost volume while adding {label}'
        s=result
    return s

def cut(s,tool):return norm(s.cut(tool))
def prism(points,a,b,axis='X'):
    edges=[dict(kind='line',start=u,end=v) for u,v in zip(points,points[1:]+points[:1])]
    return profile_extrusion(edges,a,b,axis)
def cylinder(radius,a,b,y,z):
    return Solid.make_cylinder(radius,b-a,Plane(origin=(a,y,z),z_dir=(1,0,0)))

def stepped_bore_y(x,z,top,bottom,pilot,thread_depth,access_radius,head_radius=None,head_depth=0):
    """One revolved stepped screw-clearance profile, instanced at screw axes."""
    points=[Vector(x,top,z)]
    if head_radius is not None:
        points.extend([Vector(x+head_radius,top,z),Vector(x+head_radius,top+head_depth,z),Vector(x+pilot,top+head_depth,z)])
    else:points.append(Vector(x+pilot,top,z))
    points.extend([Vector(x+pilot,top+thread_depth,z),Vector(x+access_radius,top+thread_depth,z),Vector(x+access_radius,bottom,z),Vector(x,bottom,z)])
    wire=Wire([Edge.make_line(a,b) for a,b in zip(points,points[1:]+points[:1])])
    return Solid.revolve(Face(wire),360,Axis((x,top,z),(0,1,0)))
def polar(y,z,r,angle):
    return y+r*math.cos(math.radians(angle)),z+r*math.sin(math.radians(angle))
def ring_sector(p,a,b):
    cy,cz=p['floor_y'],p['floor_z'];ri=p['cradle_radius'];ro=ri+p['cradle_skin']
    af,ar=p['cradle_front_angle'],p['cradle_rear_angle'];am=(af+ar)/2
    inner_start=polar(cy,cz,ri,af);inner_end=polar(cy,cz,ri,ar)
    outer_start=polar(cy,cz,ro,af);outer_end=polar(cy,cz,ro,ar)
    edges=[dict(kind='arc',start=inner_start,mid=polar(cy,cz,ri,am),end=inner_end),
           dict(kind='line',start=inner_end,end=outer_end),
           dict(kind='arc',start=outer_end,mid=polar(cy,cz,ro,am),end=outer_start),
           dict(kind='line',start=outer_start,end=inner_start)]
    return profile_extrusion(edges,a,b)
def circle_intersection(ca,ra,cb,rb,branch=-1):
    dy,dz=cb[0]-ca[0],cb[1]-ca[1];distance=math.hypot(dy,dz)
    assert abs(ra-rb)<distance<ra+rb, f'Case blend circles cannot meet: radii {ra}, {rb}; centre separation {distance}'
    uy,uz=dy/distance,dz/distance
    along=(ra*ra-rb*rb+distance*distance)/(2*distance)
    height=math.sqrt(ra*ra-along*along)
    return ca[0]+along*uy-branch*height*uz,ca[1]+along*uz+branch*height*uy

def front_case_geometry(p):
    """Tangent case blend constrained by cradle and the non-feed hub pilot seat.

    R200 is the AMS entrance envelope; its location is solved from the R5
    cradle blend and the known pilot stop, rather than independent XY offsets.
    """
    floor=(p['floor_y'],p['floor_z']);rf=p['cradle_radius']+p['cradle_skin'];blend=p['case_front_blend']
    centre=polar(*floor,rf+blend,-p['case_blend_floor_angle'])
    anchor=(p['hub_land_levels'][1]-p['hub_end_pilot_depth'],p['z_nonfeed']+p['hub_end_offsets'][1])
    case=circle_intersection(centre,p['case_front_radius']+blend,anchor,p['case_front_radius'])
    return case,centre

def front_case_limit(p,a,b,rear):
    # AMS front-case arc blended into the circular cradle underside.
    case,center=front_case_geometry(p)
    floor_center=(p['floor_y'],p['floor_z']);rc=p['case_front_radius'];rf=p['cradle_radius']+p['cradle_skin'];blend=p['case_front_blend']
    tc=tuple(case[k]+rc/(rc+blend)*(center[k]-case[k]) for k in range(2))
    tf=tuple(floor_center[k]+rf/(rf+blend)*(center[k]-floor_center[k]) for k in range(2))
    front=p['z_nonfeed'];start=(case[0]+math.sqrt(rc*rc-(front-case[1])**2),front)
    end=(floor_center[0]+math.sqrt(rf*rf-(rear-floor_center[1])**2),rear)
    top=p['axle_y']-p['crown_height']-eps(p)
    edges=[line((top,front),start),arc(start,tc,case),arc(tc,tf,center),arc(tf,end,floor_center),line(end,(top,rear)),line((top,rear),(top,front))]
    return profile_extrusion(edges,a,b)

def wall(p,a,b,end=False):
    p=dict(p)
    if end:
        p['crown_length']=p['end_crown_length'];p['shoulder_run']=p['end_shoulder_height']
        p['shoulder_angle']=p['end_shoulder_angle']
    top=p['axle_y']-p['crown_height'];front=p['z_nonfeed'];bottom=p['bottom_y']
    crown_front=p['axle_z']-p['crown_front_reach'];crown_rear=crown_front+p['crown_length']
    shoulder_z=crown_rear+p['shoulder_run']/math.tan(math.radians(p['shoulder_angle']));shoulder_y=top+p['shoulder_run']
    nose_y=top+(crown_front-front)*math.tan(math.radians(p['front_shoulder_angle']))
    foot_front=front+p['front_foot_run']
    case,_=front_case_geometry(p)
    case_limit=case[0]+math.sqrt(p['case_front_radius']**2-(front-case[1])**2)
    foot_bottom=min(case_limit,nose_y+p['nose_foot_width'])
    foot_top=foot_bottom-p['nose_foot_width']
    foot_join=front+p['nose_foot_rise']
    join_y=nose_y-p['nose_foot_rise']*math.tan(math.radians(p['front_shoulder_angle']))
    plate=prism([(foot_top,front),(join_y,foot_join),(top,crown_front),(top,crown_rear),(shoulder_y,shoulder_z),(shoulder_y,p['platform_front']),(bottom,p['platform_front']),(bottom,foot_front),(foot_bottom,front)],a,b)
    # The undercut leaves the wall edge concentric with the spool envelope.
    cy,cz=p['floor_y'],p['floor_z'];outer=p['cradle_radius']+p['cradle_skin']
    _,start=polar(cy,cz,outer,p['cradle_front_angle']);_,rear_end=polar(cy,cz,outer,p['cradle_rear_angle'])
    below=box_bounds(a-p['boolean_overlap'],b+p['boolean_overlap'],cy,bottom+p['boolean_overlap'],start,rear_end)
    plate=cut(plate,cut(below,cylinder(outer,a-p['boolean_overlap'],b+p['boolean_overlap'],cy,cz)))
    if not end:
        region=box_bounds(a-eps(p),b+eps(p),top-eps(p),bottom+eps(p),front,rear_end)
        plate=cut(plate,cut(region,front_case_limit(p,a-2*eps(p),b+2*eps(p),rear_end)))
    return plate
def tangent(ca,ra,cb,rb,branch):
    """Common internal tangent of two circular mechanical envelopes."""
    dy,dz=cb[0]-ca[0],cb[1]-ca[1];distance=math.hypot(dy,dz)
    assert distance>ra+rb, f'Equipment/floor tangent cannot exist: radii {ra}, {rb}; centre separation {distance}'
    angle=math.atan2(dz,dy)+branch*math.acos((ra+rb)/distance)
    normal=(math.cos(angle),math.sin(angle))
    return ((ca[0]+ra*normal[0],ca[1]+ra*normal[1]),
            (cb[0]-rb*normal[0],cb[1]-rb*normal[1]))
def line(a,b):return dict(kind='line',start=a,end=b)
def arc(a,b,center):
    ta=math.atan2(a[1]-center[1],a[0]-center[0]);tb=math.atan2(b[1]-center[1],b[0]-center[0])
    delta=(tb-ta+math.pi)%(2*math.pi)-math.pi;r=math.dist(a,center)
    return dict(kind='arc',start=a,mid=polar(*center,r,math.degrees(ta+delta/2)),end=b)
def deep_beam_centres(p):
    # R25 between the tray's descending bevel and the rear 35-degree support.
    front=math.radians(p['tray_support_angle']);back=math.radians(p['rear_support_angle'])
    nf=(math.cos(front),math.sin(front));nb=(math.cos(back),-math.sin(back))
    df=nf[0]*p['bottom_y']+nf[1]*p['tray_support_sharp_z']
    heel=(p['platform_y']+p['platform_depth']-p['heel_radius'],p['heel_z'])
    db=nb[0]*heel[0]+nb[1]*heel[1]+p['heel_radius'];r=p['motor_clearance_radius']
    determinant=nf[0]*nb[1]-nf[1]*nb[0]
    motor=(( (df+r)*nb[1]-nf[1]*(db+r))/determinant,
           (nf[0]*(db+r)-(df+r)*nb[0])/determinant)
    fy=p['bottom_y']-p['tray_heel_radius'];fz=(df-p['tray_heel_radius']-nf[0]*fy)/nf[1]
    return motor,(fy,fz),nf
def rear_beam(p,a,b,envelope=False):
    """Load path around the motor clearance: two tangent arcs and a ramp."""
    floor_center=(p['floor_y'],p['floor_z']);motor_center=(p['motor_axis_y'],p['motor_axis_z'])
    if p.get('deep_tray'):motor_center,front_heel,front_normal=deep_beam_centres(p)
    heel_center=(p['platform_y']+p['platform_depth']-p['heel_radius'],p['heel_z'])
    outer=p['cradle_radius']+p['cradle_skin']
    floor_touch,motor_front=tangent(floor_center,outer,motor_center,p['motor_clearance_radius'],-1)
    motor_back,heel_touch=tangent(motor_center,p['motor_clearance_radius'],heel_center,p['heel_radius'],1)
    upper=polar(*floor_center,p['cradle_radius'],p['cradle_rear_angle'])
    ramp_end=(p['ramp_end_y'],p['platform_front']);shelf_front=(p['platform_y'],p['platform_front'])
    shelf_rear=(p['platform_y'],p['z_feed']);heel_rear=(p['platform_y']+p['platform_depth'],p['z_feed'])
    heel_start=(heel_center[0]+p['heel_radius'],heel_center[1])
    if envelope:
        upper=(p['axle_y']-p['crown_height']-eps(p),upper[1]);roof_rear=(upper[0],p['z_feed'])
        edges=[line(upper,roof_rear),line(roof_rear,heel_rear)]
    else:
        edges=[line(upper,ramp_end),line(ramp_end,shelf_front),line(shelf_front,shelf_rear),line(shelf_rear,heel_rear)]
    edges.extend([line(heel_rear,heel_start),arc(heel_start,heel_touch,heel_center),line(heel_touch,motor_back)])
    if p.get('deep_tray'):
        motor_front=tuple(motor_center[k]-p['motor_clearance_radius']*front_normal[k] for k in range(2))
        heel_contact=tuple(front_heel[k]+p['tray_heel_radius']*front_normal[k] for k in range(2))
        floor_contact=(p['bottom_y'],front_heel[1]);leading=(p['bottom_y'],upper[1])
        edges.extend([arc(motor_back,motor_front,motor_center),line(motor_front,heel_contact),arc(heel_contact,floor_contact,front_heel),line(floor_contact,leading),line(leading,upper)])
    else:
        edges.extend([arc(motor_back,motor_front,motor_center),line(motor_front,floor_touch),line(floor_touch,upper)])
    return profile_extrusion(edges,a,b)
def feed_platform(p,a,b):
    """Continuous feeder plate with one board-clearance recess on its underside.

    The board datum fixes the side step. Two tangent return radii carry the
    recessed plate back into the box-bearing depth at the feed end.
    """
    top=p['platform_y'];base=top+p['platform_depth'];bottom=base+p['case_step']
    front=p['platform_front'];back=p['z_feed'];r=p['heel_radius']
    heel_z=p['heel_z']+p['case_step']/math.tan(math.radians(p['rear_support_angle']))
    heel=(bottom-r,heel_z)
    first=(heel[0]+math.sqrt(r*r-(front-heel_z)**2),front)
    last=(bottom,heel_z);lead=p['platform_end_round']
    tip_start=(bottom,back-lead);tip_end=(bottom-lead,back);tip_center=(bottom-lead,back-lead)
    edges=[line((top,front),first),arc(first,last,heel),line(last,tip_start),
           arc(tip_start,tip_end,tip_center),line(tip_end,(top,back)),line((top,back),(top,front))]
    plate=profile_extrusion(edges,a,b)
    r1,r2=p['platform_return_radii'];rise=bottom-base
    dz=math.sqrt((r1+r2)**2-(r1+r2-rise)**2)
    c2=(bottom-r2,back+p['platform_return_overrun']);c1=(base+r1,c2[1]-dz)
    start=(base,c1[1]);join=tuple(c1[k]+r1/(r1+r2)*(c2[k]-c1[k]) for k in range(2))
    tip_z=back-lead;tip_y=c2[0]+math.sqrt((r2-lead)**2-(tip_z-c2[1])**2)
    tip_center=(tip_y,tip_z)
    tangent_end=tuple(c2[k]+r2/(r2-lead)*(tip_center[k]-c2[k]) for k in range(2))
    end=(tip_y,back)
    roof=bottom+eps(p);begin=(base,front-eps(p))
    edges=[line(begin,start),arc(start,join,c1),arc(join,tangent_end,c2),arc(tangent_end,end,tip_center),
           line(end,(roof,back)),line((roof,back),(roof,begin[1])),line((roof,begin[1]),begin)]
    recess=profile_extrusion(edges,p['board_edge_x'],b+eps(p))
    return cut(plate,recess)

def front_guide(p,a,b):
    """The entrance roll is externally tangent to the cambered floor circle."""
    r=p['guide_radius'];floor_center=(p['floor_y'],p['floor_z']);ri=p['cradle_radius'];skin=p['cradle_skin']
    if p['guide_from_lip']:
        cy=p['front_lip_y']+r
        cz=p['floor_z']-math.sqrt((ri+r)**2-(cy-p['floor_y'])**2)
        inner_start=(p['front_lip_y'],p['z_nonfeed']);inner_roll=(p['front_lip_y'],cz)
        outer_start=(p['front_lip_y']+skin,p['z_nonfeed']);outer_roll=(p['front_lip_y']+skin,cz)
    else:
        cz=p['z_nonfeed']-p['guide_front_offset']
        cy=p['floor_y']+math.sqrt((ri+r)**2-(cz-p['floor_z'])**2)
        inner_start=(cy-math.sqrt(r*r-(p['z_nonfeed']-cz)**2),p['z_nonfeed']);inner_roll=inner_start
        outer_start=(cy-math.sqrt((r-skin)**2-(p['z_nonfeed']-cz)**2),p['z_nonfeed']);outer_roll=outer_start
    center=(cy,cz);angle=math.degrees(math.atan2(cz-p['floor_z'],cy-p['floor_y']))
    inner_touch=polar(*floor_center,ri,angle);outer_touch=polar(*floor_center,ri+skin,angle)
    edges=[]
    if p['guide_from_lip']:edges.append(line(inner_start,inner_roll))
    edges.extend([arc(inner_roll,inner_touch,center),line(inner_touch,outer_touch),arc(outer_touch,outer_roll,center)])
    if p['guide_from_lip']:edges.append(line(outer_roll,outer_start))
    edges.append(line(outer_start,inner_start))
    return profile_extrusion(edges,a,b),angle

def floor(p,a,b,index):
    local=dict(p);local['guide_radius']=p['front_guide_radii'][index];local['guide_from_lip']=index==0
    local['platform_depth']=p['platform_depth'];local['deep_tray']=index==1
    guide,angle=front_guide(local,a,b);local['cradle_front_angle']=angle
    return union([ring_sector(local,a,b),guide,rear_beam(local,a,b),entrance_backing(local,a,b,index)])

def entrance_backing(p,a,b,index):
    """Thick entrance backing carries the lip into the cradle and screw supports."""
    _,rear=polar(p['floor_y'],p['floor_z'],p['cradle_radius'],p['cradle_front_angle'])
    front=p['z_nonfeed'];start=p['front_lip_y']+p['entrance_backing_skin'];peak_z=front+p['entrance_backing_run']
    peak_y=start+p['entrance_backing_run']*math.tan(math.radians(p['entrance_backing_front_angle']))
    end_y=peak_y-(rear-peak_z)*math.tan(math.radians(p['entrance_backing_back_angle']))
    top=p['axle_y'];end_x=b if index==0 else a+p['nonfeed_support_width']
    backing=prism([(top,front),(start,front),(peak_y,peak_z),(end_y,rear),(top,rear)],a,end_x)
    if index==1:backing=union([front_case_limit(p,a,b,rear),backing])
    return cut(backing,bay_floor_clearance(p,a-eps(p),b+eps(p),index))

def bay_floor_clearance(p,a,b,index):
    """Space above the entrance roll, cradle and feeder approach, from their drivers."""
    radius=p['front_guide_radii'][index]
    if index==0:
        cy=p['front_lip_y']+radius
        cz=p['floor_z']-math.sqrt((p['cradle_radius']+radius)**2-(cy-p['floor_y'])**2)
        start=(p['front_lip_y'],p['z_nonfeed']);roll=(p['front_lip_y'],cz)
    else:
        cz=p['z_nonfeed']-p['guide_front_offset']
        cy=p['floor_y']+math.sqrt((p['cradle_radius']+radius)**2-(cz-p['floor_z'])**2)
        start=(cy-math.sqrt(radius*radius-(p['z_nonfeed']-cz)**2),p['z_nonfeed']);roll=start
    center=(cy,cz);floor_center=(p['floor_y'],p['floor_z'])
    angle=math.degrees(math.atan2(cz-p['floor_z'],cy-p['floor_y']))
    touch=polar(*floor_center,p['cradle_radius'],angle)
    rear=polar(*floor_center,p['cradle_radius'],p['cradle_rear_angle'])
    end=(p['ramp_end_y'],p['platform_front']);top=p['axle_y']-p['crown_height']-2*eps(p)
    edges=[line((top,p['z_nonfeed']),start)]
    if index==0:edges.append(line(start,roll))
    edges.extend([arc(roll,touch,center),arc(touch,rear,floor_center),line(rear,end),line(end,(top,p['platform_front'])),line((top,p['platform_front']),(top,p['z_nonfeed']))])
    return profile_extrusion(edges,a,b)

def tray_entry_clearance(p,shape,wall_x,seam_x):
    """Broad sloped access into the cable trough, continuous with the bay opening."""
    start=p['tray_header_z']+p['tray_header_width']/2
    floor=p['bottom_y']-p['plate_thickness'];end=p['motor_front']
    roof=floor-(end-start)*math.tan(math.radians(p['tray_access_angle']))
    top=p['axle_y'];tool=prism([(top,start),(floor,start),(roof,end),(top,end)],wall_x,seam_x)
    shape=cut(shape,tool)
    # Open the complete cradle skin where the cable entrance crosses it;
    # a sloping access roof must not leave a feathered membrane across the route.
    entrance=box_bounds(wall_x,seam_x,p['floor_y'],p['bottom_y'],min(start,p['tray_entry_z']),p['tray_entry_z']+p['tray_entry_width'])
    skin=cylinder(p['cradle_radius']+p['cradle_skin']+eps(p),wall_x,seam_x,p['floor_y'],p['floor_z'])
    return cut(shape,norm(entrance.intersect(skin)))

def mounting_foot(p,a,b):
    # A chamfered equipment tab, with a return lip engaging the blind beam pocket.
    top=p['mount_top'];front=p['mount_front'];chamfer_start=front+p['mount_top_length']
    back=chamfer_start+p['mount_chamfer'];land=top+p['mount_chamfer'];base=p['motor_pocket_y']
    tip=back+p['mount_return_length'];bottom=base+p['mount_return_thickness']
    # The identical feeder housing nose has two tangent radii before its
    # screw land. Its support reaches the motor entrance, not just the screws.
    r1,r2=p['feeder_nose_radii'];rise=p['feeder_nose_rise']
    c2=(top-r2,front);c1=(top-rise+r1,front-math.sqrt((r1+r2)**2-(r1+r2-rise)**2))
    join=tuple(c1[k]+r1/(r1+r2)*(c2[k]-c1[k]) for k in range(2))
    nose=(top-rise,p['motor_front']);start=(top-rise,c1[1]);end=(top,front)
    edges=[line(nose,start),arc(start,join,c1),arc(join,end,c2),line(end,(top,chamfer_start)),
           line((top,chamfer_start),(land,back)),line((land,back),(bottom,back)),
           line((bottom,back),(bottom,nose[1])),line((bottom,nose[1]),nose)]
    foot=profile_extrusion(edges,a,b)
    return foot

def feeder_nose_support(p,cx,index):
    """One broad feeder pedestal, split by its tube/cable routing slot.

    The same R5/R7 support serves both screw columns and joins the housing
    sides. Slot angle follows each route; a 45deg underside flare gives an
    insertion lead and avoids a flat overhang beside the tube.
    """
    e=eps(p);body=cx+p['mount_x_offset'];half=p['feeder_body_width']/2
    front=p['motor_front'];back=p['mount_front'];top=p['mount_top']-p['feeder_nose_rise']
    bottom=p['motor_pocket_y']+p['mount_return_thickness']
    nose=mounting_foot(p,body-half-e,body+half+e)
    nose=norm(nose.intersect(box_bounds(body-half-e,body+half+e,top-e,bottom+e,front,back+e)))
    local=dict(p);local['deep_tray']=index==1
    nose=norm(nose.intersect(rear_beam(local,body-half-2*e,body+half+2*e,True)))
    angle=math.radians(p['feeder_nose_channel_angles'][index])
    width=p['feeder_nose_channel_widths'][index]/2
    lead=(bottom-p['mount_top'])*math.tan(math.radians(p['feeder_nose_relief_angle']))
    reach=width+lead+e;start=front-reach;end=back+reach
    centre=body+p['feeder_nose_channel_offsets'][index]-(start-front)*math.tan(angle)
    profile=[(-width,top-e),(width,top-e),(width,p['mount_top']),
             (width+lead,bottom+e),(-width-lead,bottom+e),(-width,p['mount_top'])]
    points=[Vector(centre+n*math.cos(angle),y,start+n*math.sin(angle)) for n,y in profile]
    face=Face(Wire([Edge.make_line(a,b) for a,b in zip(points,points[1:]+points[:1])]))
    length=(end-start)/math.cos(angle)
    slot=Solid.extrude(face,Vector(-math.sin(angle)*length,0.,math.cos(angle)*length))
    return cut(nose,slot)

def motor_opening(p,cx,index):
    y0=p['axle_y'];y1=p['bottom_y']+p['boolean_overlap'];z0=p['motor_front'];z1=p['platform_front']+p['shelf_corner_radius']
    z2=p['motor_neck_z'];z3=p['motor_round_z'];half=p['motor_width']/2
    body=cx+p['mount_x_offset'];half=p['feeder_body_width']/2
    inlet=box_bounds(body-half,body+half,y0,p['motor_pocket_y'],z0,z1)
    header=box_bounds(cx-p['motor_header_width']/2,cx+p['motor_header_width']/2,y0,y1,z1,z2)
    neck=box_bounds(cx-p['motor_round_radius'],cx+p['motor_round_radius'],y0,y1,z2,z3)
    end=Solid.make_cylinder(p['motor_round_radius'],y1-y0,Plane(origin=(cx,y0,z3),z_dir=(0,1,0)))
    drain=box_bounds(cx-p['mount_inner_gap']/2,cx+p['mount_inner_gap']/2,y0,y1,z0,z1)
    # Rear equipment sits over a closed shelf with an inclined pocket floor.
    start=p['motor_floor_ramp_start'];rear=p['z_feed']+eps(p)
    rear_y=p['motor_floor_y']-(rear-start)*math.tan(math.radians(p['motor_floor_angle']))
    limit=prism([(y0,z1),(p['motor_floor_y'],z1),(p['motor_floor_y'],start),(rear_y,rear),(y0,rear)],cx-p['motor_header_width'],cx+p['motor_header_width'])
    rear_tool=norm(union([header,neck,end]).intersect(limit))
    return union([inlet,rear_tool,drain])

def support_web(p,a,b,rear,motor_clearance=True):
    # Chassis support below the rotating envelope; front slope clears the AMS box.
    bottom=p['bottom_y'];front=p['z_nonfeed'];nose=p['front_support_y']
    foot=front+(bottom-nose)/math.tan(math.radians(p['front_support_angle']))
    points=[(p['front_lip_y'],front),(nose,front),(bottom,foot),(bottom,rear),(p['front_lip_y'],rear)]
    web=prism(points,a,b)
    envelope=cylinder(p['cradle_radius']+p['cradle_skin']-p['web_overlap'],a-p['boolean_overlap'],b+p['boolean_overlap'],p['floor_y'],p['floor_z'])
    web=cut(web,envelope)
    if rear>p['platform_front']:
        ry,rz=polar(p['floor_y'],p['floor_z'],p['cradle_radius'],p['cradle_rear_angle'])
        clearance=[(p['axle_y'],rz),(ry,rz),(p['ramp_end_y'],p['platform_front']),(p['platform_y'],p['platform_front']),(p['platform_y'],rear),(p['axle_y'],rear)]
        web=cut(web,prism(clearance,a-p['boolean_overlap'],b+p['boolean_overlap']))
    if motor_clearance and rear>p['motor_axis_z']:
        web=cut(web,cylinder(p['motor_clearance_radius'],a-p['boolean_overlap'],b+p['boolean_overlap'],p['motor_axis_y'],p['motor_axis_z']))
    return web
def base_rib(p,cx):
    # Flat AMS contact foot, with print-friendly front/rear bevels and R2.5 heels.
    a=cx+p['rib_center_offset']-p['rib_width']/2;b=a+p['rib_width']
    bottom=p['bottom_y'];top=p['front_lip_y'];radius=p['rib_heel_radius']
    front=p['axle_z']-p['rib_front_run'];back=p['axle_z']+p['rib_rear_run']
    af=math.radians(p['rib_front_angle']);ab=math.radians(p['rib_rear_angle'])
    cf=(bottom-radius,front+radius*math.tan(af/2))
    cb=(bottom-radius,back-radius*math.tan(ab/2))
    tf=(cf[0]+radius*math.cos(af),cf[1]-radius*math.sin(af))
    tb=(cb[0]+radius*math.cos(ab),cb[1]+radius*math.sin(ab))
    ff=(bottom,cf[1]);fb=(bottom,cb[1])
    uf=(top,front-(bottom-top)/math.tan(af));ub=(top,back+(bottom-top)/math.tan(ab))
    edges=[line(uf,tf),arc(tf,ff,cf),line(ff,fb),arc(fb,tb,cb),line(tb,ub),line(ub,uf)]
    rib=profile_extrusion(edges,a,b)
    return cut(rib,bay_floor_clearance(p,a-eps(p),b+eps(p),0))

def tray_base(p,wall_x,seam_x):
    # Continuous cable-trough bottom, tied to the neighbouring support web.
    anchor=wall_x-p['middle_wall']+p['middle_web_offset']+p['rib_width']
    front=p['tray_base_front_z'];slope=math.tan(math.radians(p['tray_base_front_angle']))
    line_start=p['middle_web_rear']+(anchor-wall_x)*slope
    transition=anchor+(p['middle_web_rear']-front)/slope
    rear=p['tray_rear_z'];relief_x=wall_x+p['tray_header_start']
    relief_z=front+p['tray_base_relief_length']
    plate=prism([(wall_x,line_start),(transition,front),(relief_x,front),(relief_x,relief_z),(seam_x,relief_z),(seam_x,rear),(wall_x,rear)],p['bottom_y']-p['plate_thickness'],p['bottom_y'],'Y')
    return plate

def tray_underpass(p,shape,wall_x):
    # Tilted cable exit plus a shallow clearance recess on the AMS contact side.
    a=wall_x+p['tray_slot_wall_offset'];b=a+p['tray_slot_width'];bottom=p['bottom_y'];angle=math.radians(p['tray_slot_angle'])
    front=p['tray_slot_front'];back=front+p['tray_slot_gap']/math.sin(angle)
    top=p['platform_y'];rise=(bottom-top)/math.tan(angle);e=eps(p)
    slot=prism([(top,front+rise),(top,back+rise),(bottom+e,back-e/math.tan(angle)),(bottom+e,front-e/math.tan(angle))],a,b)
    recess=box_bounds(a,b,bottom-p['tray_recess_depth'],bottom+e,p['z_nonfeed'],front+p['tray_recess_depth']/math.tan(angle))
    return cut(shape,union([slot,recess]))

def tray_plan(p,wall_x,seam_x,margin=0):
    """Branching cable tray: a tapered diagonal inlet, header, and rear leg."""
    front_margin=margin/math.cos(math.radians(p['tray_inlet_front_angle']))
    back_margin=margin/math.cos(math.radians(p['tray_inlet_back_angle']))
    entry_front=p['tray_entry_z']-front_margin;entry_back=p['tray_entry_z']+p['tray_entry_width']+back_margin
    header_front=p['tray_header_z']-p['tray_header_width']/2-front_margin
    header_back=p['tray_header_z']+p['tray_header_width']/2+back_margin
    front_x=wall_x+(entry_front-header_front)/math.tan(math.radians(p['tray_inlet_front_angle']))
    back_x=wall_x+(entry_back-header_back)/math.tan(math.radians(p['tray_inlet_back_angle']))
    inlet=[(wall_x,entry_front),(front_x,header_front),(back_x,header_back),(wall_x,entry_back)]
    header_start=wall_x+p['tray_header_start']-margin
    header=[(min(front_x,back_x),header_front),(seam_x+margin,header_front),(seam_x+margin,header_back),(min(front_x,back_x),header_back)]
    cx=wall_x+p['tray_rear_anchor'];z=p['tray_rear_z'];half=p['tray_rear_width']/2+margin
    # Two independently drafted flanks form the ferrite/cable insertion channel.
    left=cx-half;right=cx+half;run=z-header_back
    start_left=left+run*math.tan(math.radians(p['tray_slot_left_angle']))
    start_right=right+run*math.tan(math.radians(p['tray_slot_right_angle']))
    end=p['mount_front'];end_left=left-(end-z)*math.tan(math.radians(p['tray_slot_left_angle']));end_right=right-(end-z)*math.tan(math.radians(p['tray_slot_right_angle']))
    leg=[(start_left,header_back),(start_right,header_back),(end_right,end),(end_left,end)]
    return [inlet,header,leg]
def tray(p,wall_x,seam_x):
    plans=tray_plan(p,wall_x,seam_x,p['tray_wall'])
    support=union([prism(q,p['axle_y'],p['bottom_y'],'Y') for q in plans])
    support=cut(support,cylinder(p['cradle_radius'],wall_x-p['tray_wall']-p['boolean_overlap'],seam_x+p['tray_wall']+p['boolean_overlap'],p['floor_y'],p['floor_z']))
    # Motor-body clearance governs the tray underside as well as the rear beam.
    motor,_,_=deep_beam_centres(p)
    support=cut(support,cylinder(p['motor_clearance_radius'],wall_x-p['tray_wall']-p['boolean_overlap'],seam_x+p['tray_wall']+p['boolean_overlap'],*motor))
    limits=box_bounds(wall_x,seam_x,p['axle_y'],p['bottom_y'],p['z_nonfeed'],p['z_feed'])
    return norm(support.intersect(limits))
def seam_support(p,seam_face):
    # Outer seam flange transfers the trough load into the mating face.
    front=p['axle_z']-p['seam_foot_front_run'];rear=p['axle_z']+p['seam_foot_rear_run']
    bottom=p['bottom_y'];relieved=bottom-p['seam_bottom_relief'];roof=p['floor_y']
    a=seam_face-p['seam_toe_thickness'];b=seam_face
    foot=box_bounds(a,b,roof,bottom,front,rear)
    # Keep the flange below the common rotating envelope; upper wall already exists.
    floor=cylinder(p['cradle_radius']+p['cradle_skin']-p['web_overlap'],a-eps(p),b+eps(p),p['floor_y'],p['floor_z'])
    foot=cut(foot,floor)
    return foot

def upper_joint(p,shape,seam_face):
    center=p['axle_y']+p['joint_axle_offset'];half=p['joint_neck_height']/2
    depth=p['joint_projection'];clearance=p['joint_clearance'];draft=math.tan(math.radians(p['joint_draft_angle']))
    front=p['axle_z']-p['joint_front_run'];back=p['platform_front'];over=eps(p)
    if p['mirror']:
        depth+=clearance;half+=clearance*math.sqrt(1+draft*draft)
        coords=[(seam_face+over,center-half),(seam_face-depth,center-half-depth*draft),(seam_face-depth,center+half+depth*draft),(seam_face+over,center+half)]
        return cut(shape,prism(coords,front-clearance,back,'Z'))
    coords=[(seam_face-over,center-half),(seam_face+depth,center-half-depth*draft),(seam_face+depth,center+half+depth*draft),(seam_face-over,center+half)]
    joint=prism(coords,front,back,'Z')
    # End entry is a two-to-one lead-in, derived from the same depth.
    start=seam_face-over;end=seam_face+depth+over
    lead=prism([(start,front-over),(end,front-over),(end,front+depth*p['joint_entry_slope'])],center-half-depth*draft-over,center+half+depth*draft+over,'Y')
    joint=cut(joint,lead)
    # Clip to the upper wall shoulder so the rail ends at the mating envelope.
    top=p['axle_y']-p['crown_height'];cz=p['axle_z']-p['crown_front_reach']+p['crown_length']
    shoulder=prism([(top-over,p['z_nonfeed']),(top-over,cz),(top+p['shoulder_run'],cz+p['shoulder_run']/math.tan(math.radians(p['shoulder_angle']))),(p['bottom_y'],p['platform_front']),(p['bottom_y'],p['z_nonfeed'])],seam_face-over,seam_face+depth+over)
    joint=norm(joint.intersect(shoulder))
    return union([shape,joint])

def eps(p):return p['boolean_overlap']
def seat(p,s,x,sign):
    projection=p['cap_boss_projection'] if ((sign>0)==p['cap_faces_positive']) else p['gear_boss_projection'];a,b=sorted((x,x+sign*projection))
    boss=Solid.make_cone(p['boss_land_radius']+projection*math.tan(math.radians(p['boss_taper_angle'])),p['boss_land_radius'],projection,Plane(origin=(x,p['axle_y']-p['boss_lift'],p['axle_z']),z_dir=(sign,0,0)))
    boss=norm(boss.intersect(box_bounds(a-eps(p),b+eps(p),p['axle_y']-p['boss_top_land'],p['axle_y']+p['boss_radius'],p['axle_z']-p['boss_radius'],p['axle_z']+p['boss_radius'])))
    s=union([s,boss]);a,b=sorted((x-sign*p['seat_depth'],x+sign*(projection+p['boolean_overlap'])))
    bore=cylinder(p['peg_radius'],a,b,p['axle_y'],p['axle_z'])
    entrance=box_bounds(a,b,p['axle_y']-p['boss_radius']-p['crown_height'],p['axle_y'],p['axle_z']-p['peg_radius'],p['axle_z']+p['peg_radius'])
    front=x+sign*projection;lead=p['peg_mouth_lead']
    bevel=Solid.make_cone(p['peg_radius'],p['peg_radius']+lead+eps(p),lead+eps(p),Plane(origin=(front-sign*lead,p['axle_y'],p['axle_z']),z_dir=(sign,0,0)))
    return cut(s,union([bore,entrance,bevel]))
def resolve_design(p):
    p=dict(p);p['bay_width']=p['spool_width']+p['gear_thickness']+p['axial_clearance']
    p['middle_wall']=p['rfid_gap']+2*p['rfid_skin'];p['pitch']=p['bay_width']+p['middle_wall']
    from hardware_datums import locate_hardware
    p=locate_hardware(p)
    p['floor_y']=p['axle_y']-p['floor_camber_rise'];p['floor_z']=p['axle_z']+p['floor_camber_backshift']
    p['cradle_radius']=p['gear_radius']+p['radial_clearance']+p['floor_camber_rise'];p['seat_depth']=p['peg_recess']
    p['front_lip_y']=p['floor_y']+(p['cradle_radius']+p['front_guide_radii'][0])*math.cos(math.radians(p['front_roll_contact_angle']))-p['front_guide_radii'][0]
    return p

def build(p,stage='M2',gear_pocket=False):
    p=resolve_design(p)
    x=p['bay_datum'];w=p['bay_width'];m=p['middle_wall'];e=p['boolean_overlap']
    inner=[x,x+w,x+w+m,x+2*w+m]
    intervals=[(inner[0]-p['end_wall'],inner[0]),(inner[1],inner[2]),(inner[3],inner[3]+p['seam_wall'])]
    parts=[wall(p,a,b,end=index==0) for index,(a,b) in enumerate(intervals)]
    names=['cap end wall','middle RFID wall','seam wall']
    for index in range(p['bay_count']):
        a=x+index*p['pitch'];b=a+w;cx=(a+b)/2
        parts.append(floor(p,a-e,b+e,index));names.append(f'bay {index+1} floor and entrance')

    platform=feed_platform(p,inner[0],intervals[-1][1])
    parts.append(platform);names.append('continuous feed platform and board recess')
    parts.append(support_web(p,inner[1]+p['middle_web_offset'],inner[1]+p['middle_web_offset']+p['rib_width'],p['middle_web_rear']))
    names.append('middle support web')
    if p['aux_support_web']:
        start=inner[2]+p['aux_web_wall_offset']
        parts.append(support_web(p,start,start+p['rib_width'],p['aux_web_rear']));names.append('left entrance support web')
    # Backing skin separates the cable route from the RFID pocket below the
    # circular cradle. The intentional oblique tube port is cut later.
    skin=inner[2]-p['rfid_skin']+(0 if p['mirror'] else p['rfid_access_depth'])
    top=p['platform_y']-e;bottom=p['bottom_y'];front=p['middle_web_rear']-e
    end=p['tray_rear_z']-p['rfid_skin_support_end_setback']
    upper_end=end+(bottom-top)*math.tan(math.radians(p['rfid_skin_support_angle']))
    parts.append(prism([(top,front),(top,upper_end),(bottom,end),(bottom,front)],skin,inner[2]))
    names.append('RFID cable-side backing skin')
    parts.append(tray(p,inner[2],inner[3]))
    parts.append(tray_base(p,inner[2],inner[3]))
    parts.append(seam_support(p,intervals[-1][1]))
    parts.append(box_bounds(inner[3]-e,intervals[-1][1],p['platform_y'],p['platform_y']+p['platform_depth'],p['platform_front']-e,p['z_feed']))
    names.extend(['cable trough walls','cable trough plate','seam support','feed platform tie'])
    shape=union(parts,names=names)
    assert len(shape.solids())==1, 'Massing contains disconnected features'
    if stage!='M1':
        for index in range(p['bay_count']):
            cx=x+index*p['pitch']+w/2;half=p['motor_width']/2
            shape=cut(shape,motor_opening(p,cx,index))
            if index==0:
                entry_x=inner[1]-p['cable_wall_land'];entry_z=p['cable_entry_z']
                exit_x=cx+p['cable_exit_offset'];exit_z=p['motor_front']
                direction=math.atan2(exit_z-entry_z,exit_x-entry_x);half=p['cable_width']/2
                ox=-math.sin(direction)*half;oz=math.cos(direction)*half
                route=[(entry_x+ox,entry_z+oz),(exit_x+ox,exit_z+oz),(exit_x-ox,exit_z-oz),(entry_x-ox,entry_z-oz)]
                route_tool=prism(route,p['axle_y'],p['bottom_y']+e,'Y')
                # The cable leaves the bay under the wall; it does not cut a
                # full-height slot through the middle-wall skin. Preserve the
                # old internal pocket void without perpetuating that skin cut.
                bay_region=box_bounds(inner[0],inner[1],p['axle_y']-e,p['bottom_y']+2*e,p['z_nonfeed'],p['z_feed'])
                prior_gap=box_bounds(inner[1]+p['rfid_skin'],inner[2]-p['rfid_skin'],p['axle_y']-e,p['bottom_y']+2*e,p['z_nonfeed'],p['z_feed'])
                ox=-math.sin(direction)*(half+p['cable_pocket_preservation_allowance']);oz=math.cos(direction)*(half+p['cable_pocket_preservation_allowance'])
                dx=math.cos(direction)*p['cable_pocket_preservation_allowance'];dz=math.sin(direction)*p['cable_pocket_preservation_allowance']
                relief=[(entry_x-dx+ox,entry_z-dz+oz),(exit_x+dx+ox,exit_z+dz+oz),(exit_x+dx-ox,exit_z+dz-oz),(entry_x-dx-ox,entry_z-dz-oz)]
                old_void=norm(prism(relief,p['axle_y'],p['bottom_y']+e,'Y').intersect(prior_gap))
                shape=cut(shape,union([norm(route_tool.intersect(bay_region)),old_void]))
        for plan in tray_plan(p,inner[2],inner[3]):
            shape=cut(shape,prism(plan,p['axle_y'],p['bottom_y']-p['plate_thickness'],'Y'))
        for index in range(p['bay_count']):
            cx=x+index*p['pitch']+w/2
            shape=union([shape,feeder_nose_support(p,cx,index)],names=['body','feeder nose pedestal'])
            for sign in (-1,1):
                mx=cx+p['mount_x_offset']+sign*(p['mount_inner_gap']+p['mount_width'])/2
                local=dict(p);local['deep_tray']=index==1
                # Only the motor/box underside limits the fixed feeder foot.
                # The cradle's moving upper ramp must not shave its nose
                # when gear radius or running clearance increases.
                support=rear_beam(local,mx-p['mount_width'],mx+p['mount_width'],True)
                foot=mounting_foot(p,mx-p['mount_width']/2,mx+p['mount_width']/2)
                rear=box_bounds(mx-p['mount_width'],mx+p['mount_width'],p['axle_y'],p['bottom_y'],p['mount_front'],p['z_feed'])
                foot=norm(norm(foot.intersect(support)).intersect(rear))
                sx=cx+p['mount_x_offset']+sign*p['mount_screw_pitch']/2
                pad_start=p['mount_front']+p['mount_top_length']+p['mount_chamfer']
                pad=box_bounds(sx-p['mount_second_pad_width']/2,sx+p['mount_second_pad_width']/2,p['motor_pocket_y'],p['motor_pocket_y']+p['mount_return_thickness']+e,pad_start,pad_start+p['mount_second_pad_length'])
                shape=union([shape,foot,pad])
        for index in range(p['bay_count']):
            cx=x+index*p['pitch']+w/2+p['mount_x_offset']
            for sign in (-1,1):
                sx=cx+sign*p['mount_screw_pitch']/2;sy=p['mount_top']-e;sz=p['mount_screw_z']
                first=stepped_bore_y(sx,sz,sy,p['bottom_y']+e,p['mount_screw_radius'],p['mount_front_thread_depth']+e,p['mount_lower_access_radius'],p['mount_counterbore_radius'],p['mount_counterbore_depth']+e)
                second_z=sz+p['mount_row_pitch'];second_y=p['motor_pocket_y']
                second=stepped_bore_y(sx,second_z,second_y-e,p['bottom_y']+e,p['mount_screw_radius'],p['mount_second_thread_depth']+e,p['mount_lower_access_radius'])
                shape=cut(shape,union([first,second]))
        shape=tray_underpass(p,shape,inner[2])
        shape=tray_entry_clearance(p,shape,inner[2],inner[3])
        # Service opening interrupts the header's bottom, leaving its outer wall.
        service=box_bounds(inner[2]+p['tray_header_start'],inner[3]+p['seam_wall']-p['seam_toe_thickness'],p['floor_y'],p['bottom_y']+e,p['tray_base_front_z']-p['tray_wall'],p['tray_base_front_z']+p['tray_base_relief_length'])
        preserve=cylinder(p['cradle_radius']+p['cradle_skin'],inner[2]-e,intervals[-1][1]+e,p['floor_y'],p['floor_z'])
        shape=cut(shape,cut(service,preserve))
        # The rear plate and tray share the same rounded bottom-beam bevel.
        local=dict(p);local['deep_tray']=True
        beam=rear_beam(local,inner[2]-e,inner[3]+e)
        _,rear_start=polar(p['floor_y'],p['floor_z'],p['cradle_radius'],p['cradle_rear_angle'])
        clip=box_bounds(inner[2],inner[3],p['platform_y'],p['bottom_y']+e,rear_start,p['motor_front'])
        shape=cut(shape,cut(clip,beam))
        for index in range(p['bay_count']):
            cx=x+index*p['pitch']+w/2+p['mount_x_offset']
            for sign in (-1,1):
                opening=cx+sign*p['mount_opening_width']/2
                edge=cx+sign*(p['mount_inner_gap']/2+p['mount_width'])
                a,b=sorted((opening,edge-sign*e))
                toe=box_bounds(a,b,p['mount_top'],p['mount_top']+p['mount_toe_depth'],p['mount_front'],p['mount_front']+p['mount_toe_length'])
                local=dict(p);local['deep_tray']=index==1
                toe=norm(toe.intersect(rear_beam(local,a-e,b+e)))
                shape=union([shape,toe])
        # Two PCB edge stops define the diagonal insertion roof. The lower end is open.
        corner_y=p['axle_y']+p['rfid_corner_axle_y'];corner_z=p['axle_z']+p['rfid_corner_axle_z']
        front_slope=math.tan(math.radians(p['rfid_front_roof_angle']));back_slope=math.tan(math.radians(p['rfid_rear_roof_angle']))
        front=p['axle_z']-p['rfid_entry_axle_offset'];back=p['roller_axis_z']+p['rfid_roller_end_offset'];roof=p['rfid_roof_flat_y'];bottom=p['bottom_y']+e
        front_y=corner_y+(corner_z-front)*front_slope;back_y=corner_y+(back-corner_z)*back_slope
        roof_front=corner_z-(roof-corner_y)/front_slope;roof_back=corner_z+(roof-corner_y)/back_slope
        slot=[(front_y,front),(roof,roof_front),(roof,roof_back),(back_y,back),(bottom,back),(bottom,front)]
        shape=cut(shape,prism(slot,inner[1]+p['rfid_skin'],inner[2]-p['rfid_skin']))
        shape=rfid_access_relief(p,shape,inner)
        # One regular hex profile on the measured occupied lattice.
        for row,columns in enumerate(p['vent_cells']):
            cy=p['axle_y']+p['vent_axle_offset_y']+row*p['vent_pitch']*math.sqrt(3)/2
            for col in columns:
                cz=p['axle_z']+p['vent_axle_offset_z']+(col-(row%2)/2)*p['vent_pitch']
                points=[polar(cy,cz,p['vent_radius'],p['vent_orientation']+index*60) for index in range(6)]
                shape=cut(shape,prism(points,inner[1]-e,inner[2]+e))
        # Preserve the previous pocket's small internal entry relief. This does
        # not perforate either skin and satisfies the owner's no-addition rule.
        cy=p['axle_y']+p['rfid_preserved_relief_y'];cz=p['axle_z']+p['rfid_preserved_relief_z']
        points=[polar(cy,cz,p['rfid_preserved_relief_radius'],index*60) for index in range(6)]
        shape=cut(shape,prism(points,inner[1]+p['rfid_skin'],inner[2]-p['rfid_skin']))
        # The cap flange needs a shallow rotating clearance; the central peg boss stays.
        for index in range(p['bay_count']):
            sign=1 if p['cap_faces_positive'] else -1
            face=inner[2*index] if sign>0 else inner[2*index+1]
            a,b=sorted((face-sign*p['cap_relief_depth'],face+sign*e))
            relief=cylinder(p['cap_flange_radius']+p['cap_relief_clearance'],a,b,p['axle_y'],p['axle_z'])
            root=cylinder(p['boss_land_radius']+p['cap_boss_projection']*math.tan(math.radians(p['boss_taper_angle'])),a-e,b+e,p['axle_y']-p['boss_lift'],p['axle_z'])
            shape=cut(shape,cut(relief,root))
        for face,sign in ((inner[0],1),(inner[1],-1),(inner[2],1),(inner[3],-1)):
            shape=seat(p,shape,face,sign)
    # The AMS/equipment clearance under the feeder beam limits every adjoining wall.
    _,start=polar(p['floor_y'],p['floor_z'],p['cradle_radius'],p['cradle_rear_angle'])
    split=(inner[1]+inner[2])/2
    for index,(a,b) in enumerate(((intervals[0][0],split),(split,intervals[-1][1]))):
        local=dict(p);local['deep_tray']=index==1
        envelope=rear_beam(local,a-e,b+e,True)
        region=box_bounds(a-e,b+e,p['axle_y']-p['crown_height'],p['bottom_y']+e,start,p['z_feed'])
        shape=cut(shape,cut(cut(region,envelope),platform))
    # This box-bearing outer rail is beside the equipment envelope. Applying
    # the bay-wide motor clearance to it would sever its bottom load path.
    shape=union([shape,support_web(p,inner[0]-e,inner[0]+p['end_web_width'],p['end_web_rear'],False)])
    # The cap support is a load path beside the equipment envelope.
    shape=union([shape,base_rib(p,inner[0]+w/2)])
    if stage!='M1':
        # One broad box-seating strip at the cap side, tied to the feeder plate.
        level=p['platform_y']+p['platform_depth']
        pad=box_bounds(inner[0],inner[0]+p['box_feed_land_width'],level-e,level+p['case_step'],p['z_feed']-p['box_feed_land_front_offset'],p['z_feed'])
        shape=union([shape,pad])
    if stage!='M1':
        # The cap-bay support locates and fastens the body to the stock AMS pillar.
        bx=x+w/2+p['rib_center_offset'];bz=p['z_nonfeed']+p['box_screw_z_offset']
        base=p['box_contact_y'];chamfer=p['box_boss_chamfer'];top=p['floor_y']
        boss=Solid.make_cylinder(p['box_boss_radius'],base-chamfer-top,Plane(origin=(bx,top,bz),z_dir=(0,1,0)))
        heel=Solid.make_cone(p['box_boss_radius'],p['box_boss_land_radius'],chamfer,Plane(origin=(bx,base-chamfer,bz),z_dir=(0,1,0)))
        boss=union([boss,heel]);boss=cut(boss,bay_floor_clearance(p,bx-p['box_boss_radius']-e,bx+p['box_boss_radius']+e,0))
        shape=union([shape,boss])
        head=Solid.make_cylinder(p['box_head_radius'],p['box_head_seat_y']-top,Plane(origin=(bx,top,bz),z_dir=(0,1,0)))
        screw=Solid.make_cylinder(p['box_screw_radius'],base-top+e,Plane(origin=(bx,top,bz),z_dir=(0,1,0)))
        pillar_clearance=Solid.make_cylinder(p['box_boss_land_radius'],p['bottom_y']-base+e,Plane(origin=(bx,base,bz),z_dir=(0,1,0)))
        shape=cut(shape,union([head,screw,pillar_clearance]))
    # AMS-box envelope: circular side draft and the rear floor camber.
    radius=p['case_side_radius'];case_x=inner[0]-p['case_side_axis_from_bay']
    side_clearance=Solid.make_cylinder(radius,p['z_feed']-p['z_nonfeed']+2*e,Plane(origin=(case_x,p['case_side_y'],p['z_nonfeed']-e)))
    # Tangential outer-wall draft gives installation clearance below the curved side.
    angle=math.radians(p['case_draft_angle']);ty=p['case_side_y']-radius*math.sin(angle)
    tx=case_x+radius*math.cos(angle);bottom=p['bottom_y']+e
    end_x=tx+(bottom-ty)*math.tan(angle);outside=intervals[0][0]-e
    draft=prism([(outside,ty),(tx,ty),(end_x,bottom),(outside,bottom)],p['z_nonfeed']-e,p['z_feed']+e,'Z')
    # Stop both clearance tools at the independent locating land. The rounded
    # termination blends the flat contact into the cradle/side skin.
    land=case_locating_land(p,inner[0])
    shape=cut(shape,cut(union([side_clearance,draft]),land))
    floor_radius=p['case_floor_radius'];crown=p['case_floor_crown_z']
    rear_box=box_bounds(intervals[0][0]-e,intervals[-1][1]+e,p['axle_y'],p['bottom_y']+e,crown,p['z_feed']+e)
    inside=cylinder(floor_radius,intervals[0][0]-2*e,intervals[-1][1]+2*e,p['bottom_y']-floor_radius,crown)
    # The board platform has its own measured underside; the cradle camber
    # must not shave the flat bearing land or its board-pocket return.
    shape=cut(shape,cut(cut(rear_box,inside),platform))
    if stage!='M1':
        shape=wall_entry_finish(p,shape,intervals)
        from native_features import normalize_native_topology
        shape=normalize_native_topology(shape)
        from hardware_features import fit_features
        shape=fit_features(p,shape,inner)
        # Cable bundle turns through a simple rectangular entry; a short ledge
        # supports it above the gear envelope without closing the passage.
        entry=box_bounds(inner[2],inner[2]+p['tray_entry_width']+e,p['platform_y']-e,p['bottom_y']+e,p['tray_entry_z']+p['tray_entry_relief_station']-e,p['tray_entry_z']+p['tray_entry_relief_station']+p['tray_entry_relief_length']+e)
        shape=cut(normalize_native_topology(shape),entry)
        ledge_x=inner[2]+p['cable_ledge_wall_offset'];ledge_z=p['tray_entry_z']+p['cable_ledge_entry_offset'];ledge_y=p['bottom_y']-p['cable_ledge_floor_gap']
        ledge_tip=ledge_y-p['cable_ledge_height']
        root_z=min(ledge_z,p['tray_slot_front'])
        lead=root_z+(p['cable_ledge_height']+e)/math.tan(math.radians(p['cable_ledge_underside_angle']))
        ledge=prism([(ledge_y+e,root_z),(ledge_tip,lead),(ledge_tip,ledge_z+p['cable_ledge_length']),(ledge_y+e,ledge_z+p['cable_ledge_length'])],ledge_x,ledge_x+p['cable_ledge_width'])
        shape=union([shape,ledge])
        shape=upper_joint(p,shape,intervals[-1][1])
        shape=lower_joint(p,shape,intervals[-1][1])
    shape=case_feed_finish(p,shape,inner)
    shape=case_corner_blend(p,shape,inner)
    if stage!='M1':
        from hardware_features import hub_motor_posts
        shape=hub_motor_posts(p,shape,intervals[-1][1])
    if gear_pocket:
        depth=p['pocket_depth'];radius=p['gear_radius']+p['pocket_clearance']
        taper=depth*math.tan(math.radians(p['pocket_taper']))
        # Right gear faces the end wall; left gear faces the seam wall. Neither is RFID.
        face=inner[3] if p['cap_faces_positive'] else inner[0]
        into=1 if p['cap_faces_positive'] else -1
        back=face+into*depth
        pocket=Solid.make_cone(radius-taper,radius+e*math.tan(math.radians(p['pocket_taper'])),depth+e,Plane(origin=(back,p['axle_y'],p['axle_z']),z_dir=(-into,0,0)))
        a,b=sorted((back,face-into*e))
        root=cylinder(p['boss_land_radius']+p['gear_boss_projection']*math.tan(math.radians(p['boss_taper_angle']))+p['pocket_root_margin'],a-e,b+e,p['axle_y']-p['boss_lift'],p['axle_z'])
        if not p['cap_faces_positive']:
            # Keep a minimum web behind the edit where the outer box wall
            # becomes thin. Its safe height follows the circular case datum.
            radius_outer=p['case_side_radius']
            run=p['case_side_axis_from_bay']-depth-p['pocket_min_web']
            safe_y=p['case_side_y']-math.sqrt(radius_outer**2-run**2)
            envelope=box_bounds(a-e,b+e,p['axle_y']-radius-e,safe_y,p['axle_z']-radius-e,p['axle_z']+radius+e)
            pocket=norm(pocket.intersect(envelope))
        if p['cap_faces_positive']:
            # The female seam rail occupies the opposite face of this wall.
            # Leave its spine intact instead of thinning it with the pocket.
            joint_depth=p['joint_projection']+p['joint_clearance']
            half=p['joint_neck_height']/2+p['joint_clearance']/math.cos(math.radians(p['joint_draft_angle']))+joint_depth*math.tan(math.radians(p['joint_draft_angle']))+p['pocket_min_web']
            centre=p['axle_y']+p['joint_axle_offset']
            spine=box_bounds(a-e,b+e,centre-half,centre+half,p['axle_z']-p['joint_front_run']-p['joint_clearance']-p['pocket_min_web'],p['platform_front']+p['pocket_min_web'])
            pocket=cut(pocket,spine)
        # A shallow full-span relief remains even where box or seam walls
        # prohibit the deeper cut. Both true mating faces remain fixed.
        available=p['seam_wall']-p['joint_projection']-p['joint_clearance'] if p['cap_faces_positive'] else p['case_locating_thickness']
        shallow=min(depth,available-p['pocket_min_web']-p['pocket_skin_allowance'])
        assert shallow>0, 'No retained-wall allowance for full-span gear pocket'
        full=Solid.make_cone(radius-shallow*math.tan(math.radians(p['pocket_taper'])),radius+e*math.tan(math.radians(p['pocket_taper'])),shallow+e,Plane(origin=(face+into*shallow,p['axle_y'],p['axle_z']),z_dir=(-into,0,0)))
        shape=cut(shape,cut(union([pocket,full]),root))
    # Every derived rib, entry ramp and hardware feature obeys the print end datums.
    limits=box_bounds(intervals[0][0]-p['end_wall'],intervals[-1][1]+p['lower_joint_projection']+e,p['axle_y']-p['boss_radius']-p['crown_height'],p['bottom_y']+p['platform_depth'],p['z_nonfeed'],p['z_feed'])
    shape=norm(shape.intersect(limits))
    if stage!='M1':
        for offset,station,land,radius in zip(p['hub_seam_offsets'],p['hub_end_offsets'],p['hub_land_levels'],p['hub_boss_radii']):
            point=(intervals[-1][1]-offset+radius/2,land-e,p['z_nonfeed']+station)
            assert shape.is_inside(point), 'Finished body lost a hub contact land'
    if p['mirror']:
        shape=shape.mirror(Plane.YZ).translate((p['mirror_translation'],0.,0.))
    assert shape.is_valid, 'Invalid finished mechanical body'
    return norm(shape)


def lower_joint(p,shape,seam_face):
    """Load-bearing feed-end dovetail: 1:4 flanks and a 2:1 insertion lead."""
    centre=p['lower_joint_center_y'];half=p['lower_joint_neck']/2
    depth=p['lower_joint_projection'];slope=p['lower_joint_draft_ratio'];e=eps(p)
    front=p['z_feed']-p['lower_joint_length'];back=p['z_feed']
    if p['mirror']:
        # Normal flank clearance converts to a larger Y intercept.
        clearance=p['lower_joint_clearance'];depth+=clearance;half+=clearance*math.sqrt(1+slope*slope)
        points=[(seam_face+e,centre-half),(seam_face-depth,centre-half-depth*slope),(seam_face-depth,centre+half+depth*slope),(seam_face+e,centre+half)]
        return cut(shape,prism(points,front-clearance,back+e,'Z'))
    points=[(seam_face-e,centre-half),(seam_face+depth,centre-half-depth*slope),(seam_face+depth,centre+half+depth*slope),(seam_face-e,centre+half)]
    joint=prism(points,front,back,'Z')
    lead=prism([(seam_face-e,front-e),(seam_face+depth+e,front-e),(seam_face+depth+e,front+depth*p['lower_joint_entry_ratio'])],centre-half-depth*slope-e,centre+half+depth*slope+e,'Y')
    return union([shape,cut(joint,lead)])



def case_locating_land(p,bay_face):
    """Flat AMS locating land, with one native circular roll into the floor skin.

    The AMS cylinder datum is independent of the structural wall minimum. Its
    cutter must not erase this land; the edge radius supplies installation lead.
    """
    width=p['case_locating_thickness'];assert width>=p['case_min_wall']-.05
    face=bay_face-width;radius=p['case_locating_edge_radius']
    outer=max(p['case_locating_outer_radius'],p['cradle_radius']+p['cradle_skin']);radial=outer-radius
    end=face+radius+eps(p);cy=p['floor_y'];cz=p['floor_z']
    def point(x,r):return Vector(x,cy+r,cz)
    a=point(face,0);b=point(face,radial);c=point(face+radius,outer)
    mid=point(face+radius-radius/math.sqrt(2),radial+radius/math.sqrt(2))
    d=point(end,outer);f=point(end,0)
    edges=[Edge.make_line(a,b),Edge.make_three_point_arc(b,mid,c),Edge.make_line(c,d),Edge.make_line(d,f),Edge.make_line(f,a)]
    return Solid.revolve(Face(Wire(edges)),360,Axis((face,cy,cz),(1,0,0)))

def case_feed_finish(p,shape,inner):
    """Box-facing feed-end clearance: two drafts joined by one tangent R50 blend."""
    cx=(inner[0]+inner[1])/2+p['case_feed_center_offset'];cz=p['z_feed']-p['case_feed_end_offset'];radius=p['case_feed_radius']
    first=math.radians(p['case_feed_first_angle']);last=math.radians(p['case_feed_last_angle'])
    t1=(cx-radius*math.cos(first),cz+radius*math.sin(first));t2=(cx-radius*math.cos(last),cz+radius*math.sin(last))
    start=p['platform_front'];end=p['z_feed']+eps(p)
    a=(t1[0]+(start-t1[1])*math.tan(first),start);b=(t2[0]+(end-t2[1])*math.tan(last),end)
    outside=inner[0]-p['end_wall']-eps(p)
    edges=[line((outside,start),a),line(a,t1),arc(t1,t2,(cx,cz)),line(t2,b),line(b,(outside,end)),line((outside,end),(outside,start))]
    tool=profile_extrusion(edges,p['platform_y'],p['box_clip_top']+eps(p),'Y')
    return cut(shape,tool)


def case_corner_blend(p,shape,inner):
    """Cylindrical installation blend tangent to the side and feed drafts."""
    alpha=math.radians(p['case_draft_angle']);beta=math.radians(p['case_feed_first_angle'])
    n1=Vector(-math.cos(alpha),math.sin(alpha),0.)
    n2=Vector(-math.cos(beta),0.,math.sin(beta));axis=n1.cross(n2).normalized()
    case_x=inner[0]-p['case_side_axis_from_bay']
    tx=case_x+p['case_side_radius']*math.cos(alpha);ty=p['case_side_y']-p['case_side_radius']*math.sin(alpha)
    cx=(inner[0]+inner[1])/2+p['case_feed_center_offset'];cz=p['z_feed']-p['case_feed_end_offset']
    tangent_x=cx-p['case_feed_radius']*math.cos(beta);tangent_z=cz+p['case_feed_radius']*math.sin(beta)
    z=p['platform_front'];x=tangent_x+(z-tangent_z)*math.tan(beta)
    y=(n1.X*tx+n1.Y*ty-n1.X*x)/n1.Y
    radius=p['case_corner_blend'];center=Vector(x,y,z)-(n1+n2)*(radius/(1+n1.dot(n2)))
    length=p['z_feed']-p['z_nonfeed'];base=center-axis*length;reach=radius*2
    points=[base,base+n1*reach,base+n2*reach]
    wire=Wire([Edge.make_line(a,b) for a,b in zip(points,points[1:]+points[:1])])
    wedge=Solid.extrude(Face(wire),axis*(2*length))
    rounding=Solid.make_cylinder(radius,2*length,Plane(origin=base,z_dir=axis))
    return cut(shape,cut(wedge,rounding))


def rfid_access_relief(p,shape,inner):
    """Wide connector/insertion space beyond the provisional 40 mm PCB strip."""
    a=math.radians(p['rfid_front_roof_angle']);b=math.radians(p['rfid_rear_roof_angle'])
    n1=(math.cos(a),math.sin(a));n2=(math.cos(b),-math.sin(b))
    cy=p['axle_y']+p['rfid_corner_axle_y'];cz=p['axle_z']+p['rfid_corner_axle_z']
    clearance=p['rfid_access_export_clearance']
    first=n1[0]*cy+n1[1]*cz+p['rfid_board_width_provisional']+p['rfid_access_margin']-clearance
    second=n2[0]*cy+n2[1]*cz-clearance
    front=p['axle_z']-p['rfid_entry_axle_offset']-p['rfid_access_entry_extra']-clearance
    stop=p['feeder_origin_z']-p['rfid_connector_stop_setback']+clearance
    draft=math.tan(math.radians(p['rfid_connector_stop_draft']));bottom=p['bottom_y']+eps(p)+clearance
    start=inner[1]+p['rfid_skin'] if p['mirror'] else inner[2]-p['rfid_skin']
    sign=-1 if p['mirror'] else 1;end=start+sign*(p['rfid_access_depth']+clearance)
    profiles=[]
    for x,offset in ((start-sign*eps(p),first-p['rfid_access_taper_run']),(end,first)):
        det=n1[0]*n2[1]-n1[1]*n2[0]
        y=(offset*n2[1]-n1[1]*second)/det;z=(n1[0]*second-offset*n2[0])/det
        yf=(offset-n1[1]*front)/n1[0]
        yb=(second-n2[1]*(stop+p['platform_y']*draft))/(n2[0]-n2[1]*draft)
        back=stop-(yb-p['platform_y'])*draft;lower_back=stop-(bottom-p['platform_y'])*draft
        points=[(yf,front),(y,z),(yb,back),(bottom,lower_back),(bottom,front)]
        profiles.append(sketch_wire([line(u,v) for u,v in zip(points,points[1:]+points[:1])],'X',x))
    return cut(shape,Solid.make_loft(profiles,ruled=True))


def wall_entry_finish(p,shape,intervals):
    """Rounded wall tips and a 1.35 mm cap-end insertion chamfer clear the AMS box."""
    radius=p['wall_end_radius'];end=p['platform_front'];e=eps(p)
    for index,(a,b) in enumerate(intervals):
        rise=p['end_shoulder_height'] if index==0 else p['shoulder_run']
        top=p['axle_y']-p['crown_height']+rise
        square=box_bounds(a-e,b+e,top-e,top+radius,end-radius,end+e)
        keep=cylinder(radius,a-2*e,b+2*e,top+radius,end-radius)
        shape=cut(shape,cut(square,keep))
    # The end lead stops before the roller bearing envelope; its size is a named driver.
    a,b=intervals[0];size=p['bay_a_end_chamfer'];run=size/math.tan(math.radians(p['bay_a_end_chamfer_angle']))
    tool=prism([(b-size-e,end+e),(b+e,end+e),(b+e,end-run-e)],p['axle_y']-p['crown_height'],p['platform_y'],'Y')
    return cut(shape,tool)
