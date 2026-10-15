"""Place hardware from assembled datums and reusable patterns, before modelling."""

def locate_hardware(p):
    p=dict(p);hand=-1 if p['mirror'] else 1
    seam=p['bay_datum']+2*p['bay_width']+p['middle_wall']+p['seam_wall']
    def local_x(assembled_x):return assembled_x if hand==1 else 2*seam-assembled_x

    feeder=p['feeder'];fy=p['bottom_y']-feeder['floor_setback'];fz=p['z_feed']-feeder['feed_end_setback']
    p.update(feeder_origin_y=fy,feeder_origin_z=fz,
        mount_x_offset=hand*feeder['assembly_lateral_offset'],
        mount_top=fy,platform_y=fy+feeder['platform_y_offset'],platform_front=fz+feeder['platform_z_offset'],
        motor_pocket_y=fy+feeder['second_land_offset'],motor_floor_y=fy+feeder['floor_y_offset'],
        motor_floor_ramp_start=fz+feeder['floor_ramp_station'],motor_neck_z=fz+feeder['neck_station'],
        motor_round_z=fz+feeder['round_station'],mount_front=fz+feeder['mount_front_offset'],
        mount_rear=fz+feeder['mount_rear_offset'],feeder_key_floor_y=fy-feeder['key_seat_drop'],
        roller_axis_z=fz+feeder['roller_station'],motor_axis_y=fy+feeder['motor_center_offsets'][0],
        motor_axis_z=fz+feeder['motor_center_offsets'][1],heel_z=fz+feeder['heel_station'],
        mount_screw_pitch=feeder['screw_pitch_x'],mount_row_pitch=feeder['screw_pitch_z'],
        mount_screw_z=fz-feeder['screw_pitch_z']/2)

    hub=p['hub'];hz=p['z_nonfeed']+p['box_screw_z_offset']+hub['box_screw_station_offset']
    hx=seam+hand*hub['seam_center_offset'];hy=p['bottom_y']-hub['floor_setback']
    p.update(hub_origin=(hx,hy,hz),
        hub_seam_offsets=[seam-hx+width for width in hub['row_half_widths']],
        hub_end_offsets=[hz+hub['row_pitch']/2-p['z_nonfeed'],hz-hub['row_pitch']/2-p['z_nonfeed']],
        hub_land_levels=[hy,hy-hub['land_step']])

    board=p['board'];bx=seam+board['origin_seam_offset'];bz=fz+board['origin_feeder_offset']
    by=p['platform_y']+p['platform_depth']+p['board_post_height']
    p.update(board_origin=(bx,by,bz),board_outline=(board['width'],board['length']),
        board_screw_x=local_x(bx+board['screw_from_edge']),
        board_screw_station=bz+board['screw_front_offset'],board_screw_pitch=board['screw_pitch'],
        board_edge_x=local_x(bx if hand==1 else bx+board['width']),
        board_tab_underside=by+board['edge_slot_height'],
        board_tab_backs=[bz+p['board_tab_lengths'][0],bz+board['length']],
        board_tab_tops=[by+board['edge_slot_height']+rise for rise in board['tab_end_rises']],
        capacitor_x=local_x(bx+board['screw_from_edge']+(board['capacitor_pitch'] if hand==-1 else 0)),
        capacitor_z=bz+board['capacitor_station'])

    box=p['box'];span=4*p['bay_width']+2*p['middle_wall']+2*p['seam_wall']+box['locator_extra_span']
    outside=seam+hand*box['locator_center_offset']-span/2
    p.update(box_locator_offset=p['bay_datum']-outside,
        box_locator_y=p['bottom_y']-box['locator_floor_setback'],
        box_locator_stations=[p['z_nonfeed']+box['locator_end_setback']+i*box['locator_pitch'] for i in range(2)],
        box_contact_y=p['bottom_y']-box['pillar_floor_setback'],
        box_head_seat_y=p['bottom_y']-box['pillar_floor_setback']-box['head_recess_depth'],
        box_clip_top=p['bottom_y']+box['clip_floor_rise'],
        box_clip_slot_low=p['bottom_y']-box['clip_slot_floor_setback'])
    return p
