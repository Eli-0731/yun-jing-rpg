"""依已保存的 AI 三視圖建立遠鳥與蝶的輕量動畫模型。"""
from pathlib import Path
import bpy, json, math

ROOT=Path.cwd()
OUT=ROOT/'art/exports/life-v1'

def material(name, rgb):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*rgb,1)
    m.use_backface_culling=False
    bsdf=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value=(*rgb,1)
    bsdf.inputs['Roughness'].default_value=.95
    return m

def poly(name, points, mat, parent=None):
    me=bpy.data.meshes.new(name)
    me.from_pydata([(x,y,0) for x,y in points],[],[tuple(range(len(points)))])
    me.update()
    uv=me.uv_layers.new(name='UV0')
    xs=[p[0] for p in points]; ys=[p[1] for p in points]
    for li in me.polygons[0].loop_indices:
        v=me.vertices[me.loops[li].vertex_index].co
        uv.data[li].uv=((v.x-min(xs))/max(max(xs)-min(xs),.001),(v.y-min(ys))/max(max(ys)-min(ys),.001))
    ob=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat)
    if parent: ob.parent=parent
    return ob

def ellipse(name, center, scale, mat, parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,location=center)
    ob=bpy.context.object; ob.name=name; ob.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ob.data.materials.append(mat)
    if parent: ob.parent=parent
    return ob

def key_wings(left,right,angles):
    for frame,angle in angles:
        left.rotation_euler[1]=angle
        right.rotation_euler[1]=-angle
        left.keyframe_insert(data_path='rotation_euler',frame=frame)
        right.keyframe_insert(data_path='rotation_euler',frame=frame)


def render(sheet_path, camera_scale, frames):
    sc=bpy.context.scene
    sc.render.engine='BLENDER_EEVEE'
    sc.render.resolution_x=480; sc.render.resolution_y=480; sc.render.resolution_percentage=100
    sc.render.film_transparent=True
    sc.view_settings.view_transform='Standard'
    sc.world=bpy.data.worlds.new('PreviewWorld')
    sc.world.use_nodes=True
    sc.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.75,.77,.78,1)
    sc.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.5
    bpy.ops.object.light_add(type='AREA',location=(-1,1,3))
    light=bpy.context.object; light.data.energy=35; light.data.shape='DISK'; light.data.size=3
    bpy.ops.object.camera_add(location=(0,0,4))
    cam=bpy.context.object; cam.data.type='ORTHO'; cam.data.ortho_scale=camera_scale
    sc.camera=cam
    for frame in frames:
        sc.frame_set(frame)
        sc.render.filepath=str(sheet_path.parent/f'{sheet_path.stem}_{frame:02d}.png')
        bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam,do_unlink=True)
    bpy.data.objects.remove(light,do_unlink=True)

def export_asset(code, variants, wing_angles, scale, make):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene; sc.unit_settings.system='METRIC'; sc.frame_start=1; sc.frame_end=25; sc.render.fps=24
    dest=OUT/code; dest.mkdir(parents=True,exist_ok=True)
    mats,wing=make(variants[0][1])
    key_wings(*wing,wing_angles)
    bpy.ops.wm.save_as_mainfile(filepath=str(dest/(code+'.blend')))
    render(dest/(code+'_animation-preview.png'),scale,[1,7,13,19])
    for label,color in variants:
        for m,factor in mats:
            c=tuple(max(0,min(1,v*factor)) for v in color)
            m.diffuse_color=(*c,1)
            bsdf=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
            bsdf.inputs['Base Color'].default_value=(*c,1)
        bpy.ops.export_scene.gltf(filepath=str(dest/f'{code}_{label}.glb'),export_format='GLB',export_animations=True)
    tris=sum(sum(len(p.vertices)-2 for p in ob.data.polygons) for ob in sc.objects if ob.type=='MESH')
    info={'id':code,'units':'m','triangles':tris,'variants':[v[0] for v in variants],
          'animation':'24 fps, frame 1–25 循環；左右翅各自動畫',
          'minTier':'high' if code=='LF02' else 'standard','unity_import':'未驗證'}
    (dest/'model_info.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
    print('DONE',code,tris)

def bird(color):
    body=material('BirdBody',color); wingmat=material('BirdWing',tuple(v*.82 for v in color)); pale=material('BirdChest',(0.62,.62,.57)); dark=material('BirdEye',(.07,.08,.08))
    ellipse('Body',(0,0,0),(.071,.165,.045),body)
    ellipse('Head',(0,.145,0),(.075,.073,.054),body)
    ellipse('Chest',(0,.045,.045),(.044,.106,.008),pale)
    ellipse('Eye_L',(-.045,.156,.047),(.008,.008,.005),dark)
    ellipse('Eye_R',(.045,.156,.047),(.008,.008,.005),dark)
    poly('ForkTail_L',[(0,-.09),(-.015,-.19),(-.067,-.32),(-.018,-.23)],wingmat)
    poly('ForkTail_R',[(0,-.09),(.015,-.19),(.067,-.32),(.018,-.23)],wingmat)
    left=bpy.data.objects.new('Wing_L_Pivot',None); bpy.context.collection.objects.link(left); left.location=(-.058,.062,0)
    right=bpy.data.objects.new('Wing_R_Pivot',None); bpy.context.collection.objects.link(right); right.location=(.058,.062,0)
    outline=[(0,0),(-.12,.045),(-.30,.062),(-.49,.042),(-.44,-.018),(-.27,-.084),(-.08,-.078)]
    poly('Wing_L',outline,wingmat,left)
    poly('Wing_R',list(reversed([(-x,y) for x,y in outline])),wingmat,right)
    return [(body,1),(wingmat,.82)],(left,right)

def butterfly(color):
    wingmat=material('ButterflyWing',color); bodymat=material('ButterflyBody',(.24,.20,.17)); vein=material('ButterflyVein',(.65,.50,.25))
    ellipse('Body',(0,0,.006),(.008,.047,.009),bodymat)
    ellipse('Head',(0,.045,.006),(.012,.012,.010),bodymat)
    for s in (-1,1):
        poly(f'Antenna_{s}',[(s*.004,.05),(s*.018,.09),(s*.022,.094)],vein)
    left=bpy.data.objects.new('Wing_L_Pivot',None); bpy.context.collection.objects.link(left); left.location=(-.008,.015,0)
    right=bpy.data.objects.new('Wing_R_Pivot',None); bpy.context.collection.objects.link(right); right.location=(.008,.015,0)
    pts=[(0,0),(-.020,.055),(-.070,.072),(-.097,.047),(-.083,.012),(-.065,-.005),(-.077,-.036),(-.060,-.058),(-.027,-.052)]
    poly('Wing_L',pts,wingmat,left)
    poly('Wing_R',list(reversed([(-x,y) for x,y in pts])),wingmat,right)
    return [(wingmat,1)],(left,right)

export_asset('LF01',[('slate',(.31,.35,.39)),('warm',(.43,.34,.28)),('pale',(.54,.58,.58))],
             [(1,0),(7,.90),(13,0),(19,-.18),(25,0)],1.25,bird)
export_asset('LF02',[('ivory',(.88,.84,.72)),('yellow',(.95,.75,.30))],
             [(1,.16),(7,1.25),(13,.16),(19,1.25),(25,.16)],.27,butterfly)
