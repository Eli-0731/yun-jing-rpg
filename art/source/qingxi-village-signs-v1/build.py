"""Blender 4.5.3; build only after the saved AI reference review exists.
Original geometry: Eli-0731 / Codex. No third-party meshes.
Run: blender -b --python-exit-code 1 --python art/source/qingxi-village-signs-v1/build.py
"""
import bpy, math, json, hashlib
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
REF = ROOT / 'art/references/qingxi-village-signs-v1'
OUT = ROOT / 'art/exports/qingxi-village-signs-v1'
PRE = ROOT / 'tools/novice-field-guide/previews'
assert (REF / 'review.json').exists()
assert all((REF / f'Q{i:02}-three-view.png').stat().st_size > 10000 for i in range(1,5))
OUT.mkdir(parents=True, exist_ok=True); PRE.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.unit_settings.system='METRIC'
scene.render.engine='CYCLES'; scene.cycles.samples=24
scene.render.resolution_x=960; scene.render.resolution_y=720; scene.render.resolution_percentage=100
scene.world.color=(.35,.35,.35)
scene.view_settings.view_transform='AgX'

def material(name, color, grain=False):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*color,1); bs.inputs['Roughness'].default_value=.82
    if grain:
        image=bpy.data.images.new(name+'_basecolor',width=128,height=128)
        pixels=[]
        for y in range(128):
            for x in range(128):
                t=.82+.11*math.sin(x*.62+math.sin(y*.05)*1.6)+.07*math.sin(x*2.1+y*.027)
                pixels.extend([min(1,c*t) for c in color]+[1])
        image.pixels.foreach_set(pixels); image.pack()
        tex=m.node_tree.nodes.new('ShaderNodeTexImage'); tex.image=image
        m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    return m

wood=material('weathered_oak',(.30,.17,.075),True)
edge=material('endgrain_dark',(.16,.085,.035),True)
bamboo=material('aged_bamboo',(.32,.30,.12),True)
green=material('faded_sage',(.16,.25,.14),True)
paper=material('blank_hemp_paper',(.73,.65,.46))
rope=material('hemp',(.40,.31,.16))
stone=material('warm_gray_stone',(.28,.30,.27))
dark=material('groove_shadow',(.055,.038,.02))

def cube(name,loc,size,mat, bevel=.008):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object; o.name=name; o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(mat)
    if bevel:
        mod=o.modifiers.new('soft_handworn_edges','BEVEL'); mod.width=bevel; mod.segments=2
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return o

def beam(name,a,b,r,mat,vertices=10):
    a,b=Vector(a),Vector(b); v=b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=v.length,location=(a+b)/2)
    o=bpy.context.object; o.name=name; o.rotation_euler=v.to_track_quat('Z','Y').to_euler(); o.data.materials.append(mat)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return o

def tie(x,y,z,r):
    for h in range(3):
        bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=.007,major_segments=16,minor_segments=5,location=(x,y,z+h*.016))
        bpy.context.object.name='hemp_binding'; bpy.context.object.data.materials.append(rope)

groups={}
def start(): return set(bpy.data.objects)
def finish(id,before):
    obs=[o for o in bpy.data.objects if o not in before]
    bpy.context.view_layer.update()
    ground=min((o.matrix_world@Vector(v)).z for o in obs for v in o.bound_box)
    for o in obs:o.location.z-=ground
    col=bpy.data.collections.new(id); scene.collection.children.link(col)
    for o in obs:
        for c in list(o.users_collection): c.objects.unlink(o)
        col.objects.link(o)
        if o.type=='MESH':
            bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
            bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
            bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.uv.smart_project(island_margin=.02); bpy.ops.object.mode_set(mode='OBJECT')
    groups[id]=obs

# Q01: shallow slatted canopy, papers and pegged timber frame.
s=start()
for x in [-.50,.50]:
    cube('stone_foot',(x,0,.075),(.19,.36,.15),stone)
    cube('post',(x,0,.92),(.085,.085,1.69),wood)
    cube('lower_brace',(x*.82,.01,.48),(.28,.06,.055),wood).rotation_euler.y=(-1 if x<0 else 1)*.65
for x in range(9): cube('backboard_slats',(-.44+x*.11,.012,1.03),(.105,.045,.72),wood)
for z in [.65,1.39]: cube('crossrail',(0,-.025,z),(1.14,.075,.07),edge)
for i in range(12):
    o=cube('rain_canopy_slats',(-.572+i*.104,0,1.66),(.10,.55,.045),wood)
    o.rotation_euler.x=.18
cube('roof_ridge',(0,.25,1.72),(1.25,.06,.06),edge)
beam('paper_cord',(-.44,-.06,1.31),(.44,-.06,1.31),.009,rope)
for x in [-.29,0,.29]:
    cube('blank_notice',(x,-.067,1.09),(.23,.008,.35),paper,.003)
    for dx in [-.07,.07]: cube('notice_peg',(x+dx,-.08,1.29),(.018,.018,.065),edge,.002)
finish('Q01',s)

# Q02: actual shallow mesh grooves, not painted borrowed imagery.
s=start()
board=cube('three_groove_plaque',(0,0,.50),(.48,.065,.70),wood,.012)
for z in [.37,.50,.63]:
    cutter=cube('groove_cutter',(0,-.031,z),(.40,.018,.016),dark,0); cutter.rotation_euler.y=.38
    bpy.context.view_layer.objects.active=board
    m=board.modifiers.new('carved_line','BOOLEAN'); m.operation='DIFFERENCE'; m.object=cutter
    bpy.ops.object.modifier_apply(modifier=m.name); bpy.data.objects.remove(cutter,do_unlink=True)
for x in [-.195,.195]:
    beam('A_frame_front',(x,-.14,.03),(x,.02,.51),.028,edge,8)
    beam('A_frame_back',(x,.17,.03),(x,.02,.51),.028,edge,8)
cube('A_frame_crossbar',(0,.12,.15),(.42,.035,.035),wood)
finish('Q02',s)

# Q03: bamboo, bindings, pointed tag and raised leaf symbol.
s=start()
beam('bamboo_stake',(0,0,.03),(0,0,1.05),.043,bamboo,12)
for z in [.25,.52,.80]:
    beam('bamboo_node',(0,0,z-.012),(0,0,z+.012),.048,edge,12)
for i in range(5):
    a=i*math.tau/5
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(math.cos(a)*.072,math.sin(a)*.065,.045))
    o=bpy.context.object; o.name='ground_stone'; o.scale=(.065,.055,.045); o.data.materials.append(stone)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
verts=[(-.09,-.058,.78),(-.09,-.058,.55),(0,-.058,.48),(.09,-.058,.55),(.09,-.058,.78),(0,-.058,.84)]
verts+= [(x,y+.023,z) for x,y,z in verts]
faces=[tuple(range(5,-1,-1)),tuple(range(6,12))]+[(i,(i+1)%6,(i+1)%6+6,i+6) for i in range(6)]
mesh=bpy.data.meshes.new('pointed_tag'); mesh.from_pydata(verts,[],faces); mesh.update()
o=bpy.data.objects.new('pointed_tag',mesh); scene.collection.objects.link(o); o.data.materials.append(green)
tie(0,0,.88,.05)
beam('tag_cord',(0,-.04,.91),(0,-.075,.79),.009,rope)
for i in range(3):
    a=i*math.tau/3
    o=cube('three_leaf_symbol',(math.sin(a)*.031,-.073,.665+math.cos(a)*.031),(.018,.008,.065),paper,.002); o.rotation_euler.y=a
finish('Q03',s)

# Q04: open-slatted inn frame; visually distinct from canopy notice.
s=start()
for x in [-.35,.35]:
    cube('inn_post',(x,0,.61),(.065,.065,1.18),wood)
    cube('cross_foot',(x,0,.03),(.10,.42,.06),edge)
    beam('diagonal_brace',(x,.17,.06),(x,0,.31),.022,wood,8)
    tie(x,0,.31,.042); tie(x,0,1.12,.042)
for i in range(5): cube('message_slat',(0,.01,.49+i*.115),(.78,.04,.10),wood)
cap=cube('flat_rain_cap',(0,0,1.21),(.85,.24,.04),bamboo); cap.rotation_euler.x=.10
for x,z in [(-.18,.80),(.18,.76)]:
    cube('blank_message',(x,-.023,z),(.23,.009,.29),paper,.003)
    cube('message_clip',(x,-.038,z+.14),(.025,.02,.07),edge,.003)
finish('Q04',s)

def bounds(obs):
    p=[o.matrix_world@Vector(v) for o in obs for v in o.bound_box]
    return [max(v[i] for v in p)-min(v[i] for v in p) for i in range(3)]

manifest={'author':'Eli-0731 / Codex','blender':bpy.app.version_string,'units':'meters','source_axes':'Z up, front -Y','glb_axes':'Y up, front +Z','reference_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in REF.glob('*.png')},'assets':[]}
for id,obs in groups.items():
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:o.select_set(True)
    bpy.context.view_layer.objects.active=obs[0]
    bpy.ops.export_scene.gltf(filepath=str(OUT/f'{id}.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True)
    tris=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in obs)
    errors=[]
    for o in obs:
        if not o.data.uv_layers: errors.append(o.name+': missing UV')
        if any(p.area < 1e-10 for p in o.data.polygons): errors.append(o.name+': degenerate polygon')
        if any(not math.isfinite(c) for v in o.data.vertices for c in v.co): errors.append(o.name+': nonfinite')
    manifest['assets'].append({'id':id,'dimensions_xyz':list(bounds(obs)),'triangles':tris,'meshes':len(obs),'errors':errors,'lod':'single prototype LOD; integrate distance culling at 25m, low LOD not delivered','collision':'one box or capsule around main silhouette, decorative cords non-colliding'})
assert not any(a['errors'] for a in manifest['assets']),manifest

# Neutral contact shadows and a camera independent of the export collections.
floor=cube('preview_ground',(0,0,-.025),(20,20,.05),material('ground',(.28,.31,.26)),0)
bpy.ops.object.light_add(type='AREA',location=(3,-4,6)); bpy.context.object.data.energy=650; bpy.context.object.data.shape='DISK'; bpy.context.object.data.size=5
bpy.ops.object.light_add(type='AREA',location=(-3,2,4)); bpy.context.object.data.energy=420; bpy.context.object.data.size=4
bpy.ops.object.camera_add(); cam=bpy.context.object; scene.camera=cam; cam.data.type='ORTHO'
def shot(path,target,eye,scale):
    cam.location=eye; cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.ortho_scale=scale
    scene.render.filepath=str(path); bpy.ops.render.render(write_still=True)
for id,obs in groups.items():
    for oid,objs in groups.items():
        for o in objs:o.hide_render=oid!=id
    h=bounds(obs)[2]
    shot(PRE/f'{id}-close.png',(0,0,h*.48),(2,-4,h*1.8),max(1.3,h*1.5))
for i,(id,obs) in enumerate(groups.items()):
    for o in obs:o.hide_render=False; o.location.x+=(i-1.5)*1.45
shot(PRE/'all-four.png',(0,0,.65),(5,-8,5),6.7)
# Restore local origins in source file, so a collection never exports with assembly offset.
for i,obs in enumerate(groups.values()):
    for o in obs:o.location.x-=(i-1.5)*1.45
bpy.ops.wm.save_as_mainfile(filepath=str(Path(__file__).parent/'Qingxi_Village_Signs_v1.blend'))

# Round-trip in clean scenes. Compare world bounding size after Y-up conversion.
for a in manifest['assets']:
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(OUT/f"{a['id']}.glb"))
    obs=[o for o in scene.objects if o.type=='MESH']; dims=bounds(obs)
    a['roundtrip_dimensions_xyz']=dims
    a['roundtrip_pass']=all(abs(x-y)<.002 for x,y in zip(dims,a['dimensions_xyz'])) and all(o.data.uv_layers for o in obs)
    assert a['roundtrip_pass'],a
(OUT/'asset-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('SIGNS_QA_PASS: four independent GLBs and clean roundtrips')
