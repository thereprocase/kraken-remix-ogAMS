"""Analytic mating features for stock hardware; all coordinates use design drivers."""
import math
from build123d import Solid,Plane
from native_features import box_bounds
from mechanical_body import union,cut,norm,cylinder,eps,prism,line,arc,bay_floor_clearance,front_case_geometry
from native_features import profile_extrusion

def small_post(p,shape,x,z,land,base,outer,tip,pilot,outer_lead,end_lead=False):
    """A screw post with a flat contact annulus and 0.25 mm lead-in chamfers."""
    chamfer=outer_lead;e=eps(p)
    stem=Solid.make_cylinder(outer,land-chamfer-base,Plane(origin=(x,base,z),z_dir=(0,1,0)))
    end=Solid.make_cone(outer,tip,chamfer,Plane(origin=(x,land-chamfer,z),z_dir=(0,1,0)))
    post=union([stem,end])
    depth=p['hub_pilot_depths'][1 if end_lead else 0]
    if end_lead:
        anchor=(land-depth,z);angle=math.radians(p['hub_end_pilot_stop_angle'])
        stop_center=(anchor[0]-p['case_front_radius']*math.cos(angle),anchor[1]+p['case_front_radius']*math.sin(angle))
        preserve=cylinder(p['case_front_radius'],x-outer-e,x+outer+e,*stop_center)
        root_radius=p['cradle_radius']
    else:
        stop_radius=math.hypot(land-depth-p['floor_y'],z-p['floor_z'])
        preserve=cylinder(stop_radius,x-outer-e,x+outer+e,p['floor_y'],p['floor_z'])
        root_radius=min(p['cradle_radius'],stop_radius-p['cradle_skin'])
    floor_clearance=cylinder(root_radius-e,x-outer-e,x+outer+e,p['floor_y'],p['floor_z'])
    post=cut(post,floor_clearance)
    if end_lead:
        front=p['z_nonfeed'];stop=front+p['hub_end_lead_run'];slope=p['hub_end_lead_slope']
        lead=prism([(land-slope*(stop-front),front-e),(land+e,front-e),(land+e,stop+e),(land,stop)],x-outer-e,x+outer+e)
        post=cut(post,lead)
    if not end_lead:
        shoulder_y=land-p['hub_shoulder_exposure'];height=p['bottom_y']-shoulder_y+e
        outer_tool=Solid.make_cylinder(outer+p['hub_bushing_radial_clearance'],height,Plane(origin=(x,shoulder_y,z),z_dir=(0,1,0)))
        keep=Solid.make_cylinder(outer,height+2*e,Plane(origin=(x,shoulder_y-e,z),z_dir=(0,1,0)))
        shape=cut(shape,cut(outer_tool,keep))
    probe=(x+outer/2,land-e,z)
    original=shape
    shape=union([original,post])
    if not shape.is_inside(probe):
        from native_features import normalize_native_topology
        healed=normalize_native_topology(original)
        shape=union([healed,post])
    assert shape.is_valid and shape.is_inside(probe), 'Hub post union lost contact land'
    # The pilot stops on the existing curved outside skin, preserving that skin.
    bore=Solid.make_cylinder(pilot,land-p['floor_y']+e,Plane(origin=(x,p['floor_y'],z),z_dir=(0,1,0)))
    chamfer=p['hardware_lead']
    lead=Solid.make_cone(pilot,pilot+chamfer+e,chamfer+e,Plane(origin=(x,land-chamfer,z),z_dir=(0,1,0)))
    shape=cut(shape,union([cut(bore,preserve),lead]))
    assert shape.is_inside((x+outer/2,land-e,z)), 'Hub contact land lost during native construction'
    return shape

def hub_motor_posts(p,shape,seam_face):
    """Two stock motor/bushing screw posts per half, measured from the seam."""
    for index,(offset,station,land) in enumerate(zip(p['hub_seam_offsets'],p['hub_end_offsets'],p['hub_land_levels'])):
        x=seam_face-offset;z=p['z_nonfeed']+station
        # The posts grow from the underside of the rotating/entrance envelope.
        radius=p['front_guide_radii'][1];cz=p['z_nonfeed']-p['guide_front_offset']
        cy=p['floor_y']+math.sqrt((p['cradle_radius']+radius)**2-(cz-p['floor_z'])**2)
        touch=p['floor_z']+p['cradle_radius']/(p['cradle_radius']+radius)*(cz-p['floor_z'])
        if z<touch:
            base=cy-math.sqrt(radius*radius-(z-cz)**2)+p['cradle_skin']/2
        else:
            # Short boss starts at the local skin with a named root overlap.
            base=min(p['floor_y']+math.sqrt(p['cradle_radius']**2-(z+sign*p['hub_boss_radii'][index]-p['floor_z'])**2) for sign in (-1,1))-p['hub_root_embed']
        base=min(base,land-p['hub_pilot_depths'][index]-p['cradle_skin']-p['hub_root_embed'])
        shape=small_post(p,shape,x,z,land,base,p['hub_boss_radii'][index],p['hub_boss_radii'][index]-p['hub_outer_leads'][index],p['small_pilot_radius'],p['hub_outer_leads'][index],index==1)
    return shape

def main_board_posts(p,shape,inner):
    """Two posts on the right half; the stock board bridges both body halves."""
    if not p['main_board_posts']:return shape
    x=p['board_screw_x'];base=p['platform_y']+p['platform_depth'];land=base+p['board_post_height']
    for index in range(p['board_screw_count']):
        z=p['board_screw_station']+index*p['board_screw_pitch']
        boss=Solid.make_cone(p['board_base_radius'],p['board_land_radius'],land-base,Plane(origin=(x,base,z),z_dir=(0,1,0)))
        shape=union([shape,boss])
        bore=Solid.make_cylinder(p['small_pilot_radius'],land-p['platform_y']+eps(p),Plane(origin=(x,p['platform_y'],z),z_dir=(0,1,0)))
        lead=Solid.make_cone(p['small_pilot_radius'],p['small_pilot_radius']+p['hardware_lead']+eps(p),p['hardware_lead']+eps(p),Plane(origin=(x,land-p['hardware_lead'],z),z_dir=(0,1,0)))
        shape=cut(shape,union([bore,lead]))
    return shape

def capacitor_clearance(p,shape,inner):
    """Separate component opening on each half, positioned from its board datum."""
    x=p['capacitor_x'];z=p['capacitor_z']
    opening=Solid.make_cylinder(p['capacitor_clearance_radius'],p['bottom_y']-p['platform_y']+2*eps(p),Plane(origin=(x,p['platform_y']-eps(p),z),z_dir=(0,1,0)))
    return cut(shape,opening)

def roller_seats(p,shape,inner):
    """Four blind front-roller axle seats with open insertion clearance pockets."""
    y=p['roller_axis_y'];z=p['roller_axis_z'];depth=p['roller_relief_depth'];pilot=p['roller_pilot_depth'];e=eps(p)
    for index,(face,sign) in enumerate(((inner[0],1),(inner[1],-1),(inner[2],1),(inner[3],-1))):
        # Positive sign means the bay is on the positive-X side of this wall.
        back=face-sign*depth;front=face+sign*e
        radius=p['roller_clearance_radius'];entry=radius+(depth+e)*math.tan(math.radians(p['roller_entry_angle']))
        # The non-feed flank follows the pilot; only the feed-side flank is tapered.
        left=z-p['roller_pilot_radius']
        mouth=prism([(back,left),(front,left),(front,z+entry),(back,z+radius)],p['axle_y']-p['crown_height'],y,'Y')
        top=p['axle_y']-p['crown_height']+(p['end_shoulder_height'] if index==0 else p['shoulder_run'])
        blend=p['roller_entry_blend'];lo,hi=sorted((back,front))
        corner=box_bounds(lo,hi,top-e,top+blend,left-blend,left+e)
        keep=cylinder(blend,lo-e,hi+e,top+blend,left-blend)
        mouth=union([mouth,cut(corner,keep)])
        aa,bb=sorted((face-sign*(depth+pilot),face+sign*e))
        seat=cylinder(p['roller_pilot_radius'],aa,bb,y,z)
        shape=cut(shape,union([mouth,seat]))
    return shape

def fit_features(p,shape,inner):
    shape=feeder_housing_webs(p,shape,inner)
    shape=main_board_posts(p,shape,inner)
    shape=capacitor_clearance(p,shape,inner)
    shape=roller_seats(p,shape,inner)
    shape=ferrite_holder(p,shape,inner)
    shape=ptfe_crosswall_port(p,shape,inner)
    shape=feeder_locator_sockets(p,shape,inner)
    shape=board_edge_tabs(p,shape,inner)
    shape=front_box_clip(p,shape,inner)
    return box_locating_lands(p,shape,inner)


def ptfe_crosswall_port(p,shape,inner):
    """A single oblique round PTFE passage ties the two underside routes together."""
    angle=math.radians(p['ptfe_port_angle']);e=eps(p)
    radius=p['ptfe_radius']+p['ptfe_port_clearance']
    # A tilted cylinder's end face must clear the entire wall thickness,
    # including its radial projection, or it leaves a wedge across the exit.
    overrun=e+radius*math.sin(angle)
    x=inner[1]-overrun;z=p['tray_entry_z']+p['tray_entry_width']/2+(inner[2]-x)*math.tan(angle)
    y=p['platform_y']+p['platform_depth'];length=(inner[2]-inner[1]+2*overrun)/math.cos(angle)
    tool=Solid.make_cylinder(radius,length,Plane(origin=(x,y,z),z_dir=(math.cos(angle),0.,-math.sin(angle))))
    return cut(shape,tool)


def feeder_housing_webs(p,shape,inner):
    """Two feeder side walls, each one profile with a 45-degree insertion lead."""
    front=p['platform_front'];back=p['motor_neck_z'];top=p['platform_y']
    root=top-(back-front)*math.tan(math.radians(p['feeder_web_angle']))
    bottom=p['platform_y']+p['platform_depth']
    profile=[(root,front),(top,back),(bottom,back),(bottom,front)]
    for bay in range(p['bay_count']):
        center=(inner[2*bay]+inner[2*bay+1])/2;body=center+p['mount_x_offset']
        half=p['feeder_body_width']/2;header=p['motor_header_width']/2
        for a,b in [(center-header,body-half),(body+half,center+header)]:
            shape=union([shape,prism(profile,a,b)])
    return shape


def board_edge_tabs(p,shape,inner):
    """Two board-edge retainers; the 0.7 mm lip locates the PCB, stems carry load."""
    edge=p['board_edge_x']
    base=p['platform_y']+p['platform_depth'];underside=p['board_tab_underside'];e=eps(p)
    for back,length,top,width in zip(p['board_tab_backs'],p['board_tab_lengths'],p['board_tab_tops'],p['board_tab_stems']):
        front=back-length;rise=top-base
        stem=prism([(base-e,front-rise),(top,front),(top,back),(base-e,back)],edge-width,edge)
        lip=box_bounds(edge-e,edge+p['board_tab_overlap'],underside,top,front,back)
        shape=union([shape,stem,lip])
    return shape

def front_box_clip(p,shape,inner):
    """Front box-edge capture: open 4.8 mm slot, drafted outer edge and entry bevel."""
    cx=(inner[0]+inner[1])/2;inside=cx-p['box_clip_inner_offset'];back=p['z_feed'];front=back-p['box_clip_base_length']
    outer=inside-p['box_clip_front_width'];slope=math.tan(math.radians(p['box_clip_draft_angle']));outer_front=outer-(back-front)*slope
    base=p['platform_y']+p['platform_depth']+p['case_step'];top=p['box_clip_top'];e=eps(p)
    plan=[(outer_front,front),(inside,front),(inside,back),(outer,back)]
    lower=prism(plan,p['platform_y'],base,'Y')
    cap_plan=[(outer_front,front),(inside+p['box_clip_overhang'],front),(inside+p['box_clip_overhang'],back),(outer,back)]
    cap=prism(cap_plan,base-e,top,'Y')
    start=p['box_clip_lead_start'];lead=prism([(base-e,front-e),(top+e,front-e),(top+e,start+top-base),(base-e,start)],outer_front-e,inside+p['box_clip_overhang']+e)
    cap=cut(cap,lead);clip=union([lower,cap])
    slot=box_bounds(outer_front-e,inside,p['box_clip_slot_low'],p['box_clip_slot_low']+p['box_clip_slot_gap'],back-p['box_clip_slot_depth'],back+e)
    clip=cut(clip,slot)
    # Small end bevel keeps the part within the 249.9 mm print envelope.
    size=p['box_clip_edge_chamfer']
    bevel=prism([(top-size,back+e),(top+e,back+e),(top+e,back-size)],outer_front-e,inside+p['box_clip_overhang']+e)
    return cut(union([shape,clip]),union([slot,bevel]))


def box_locating_lands(p,shape,inner):
    """Two flat side-locating pads wholly inside measured source contact patches."""
    outside=inner[0]-p['box_locator_offset'];inside=inner[0]+eps(p)
    low=p['box_locator_y']-p['box_locator_height']/2;high=low+p['box_locator_height']
    for station in p['box_locator_stations']:
        front=station-p['box_locator_length']/2;back=front+p['box_locator_length']
        shape=union([shape,box_bounds(outside,inside,low,high,front,back)])
    return shape


def feeder_locator_sockets(p,shape,inner):
    """Each feeder's rectangular locating tab seats in a blind 6.15 by 9.15 socket."""
    width=p['feeder_key_width']+p['feeder_key_clearance'];length=p['feeder_key_length']+p['feeder_key_clearance']
    z=p['roller_axis_z']+p['feeder_key_roller_offset'];y=p['feeder_key_floor_y']
    for bay in range(p['bay_count']):
        if p['mirror']:x=inner[2*bay]+p['feeder_key_wall_setback']+width/2
        else:x=inner[2*bay+1]-p['feeder_key_wall_setback']-width/2
        socket=box_bounds(x-width/2,x+width/2,p['axle_y']-p['crown_height'],y,z-length/2,z+length/2)
        shape=cut(shape,socket)
    return shape


def ferrite_holder(p,shape,inner):
    """Two spring rails retain the single stock ferrite; the left has no duplicate."""
    if not p['ferrite_holder']:return shape
    seam=inner[-1]+p['seam_wall'];cx=seam-p['ferrite_seam_offset'];half=p['ferrite_mouth']/2
    top=p['bottom_y']-p['cradle_skin'];base=p['platform_y']-p['heel_radius']
    front=p['tray_rear_z']-p['ferrite_root_overlap'];back=p['motor_front']-p['ferrite_end_setback']
    frame=[];outer=p['ferrite_rail_width']
    for a,b in [(cx-half-outer,cx-half),(cx+half,cx+half+outer)]:
        rail=prism([(base,front),(top,front),(top,back),(base,back+top-base)],a,b)
        rail=cut(rail,bay_floor_clearance(p,a-eps(p),b+eps(p),0))
        frame.append(rail)
    cy=p['bottom_y']-p['ferrite_axis_below_bottom'];w=p['ferrite_body_width']/2;h=p['ferrite_body_height']/2;radius=p['ferrite_corner_radius']
    left,right=cx-w,cx+w;low,high=cy-h,cy+h
    points=[(left+radius,low),(right-radius,low),(right,low+radius),(right,high-radius),(right-radius,high),(left+radius,high),(left,high-radius),(left,low+radius)]
    centers=[(right-radius,low+radius),(right-radius,high-radius),(left+radius,high-radius),(left+radius,low+radius)]
    edges=[]
    for index in range(4):
        edges.extend([line(points[2*index],points[2*index+1]),arc(points[2*index+1],points[(2*index+2)%8],centers[index])])
    cavity=profile_extrusion(edges,front-eps(p),back+top-base+eps(p),'Z')
    holder=cut(union(frame),cavity)
    return union([shape,holder])
