"""Package RI01 state subobjects and 1 m snapping bund pieces with three LODs."""
import bpy
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/"art/source/valley-and-home-v1/RI01/RI01-paddy-material-v007.blend"
OUT=ROOT/"art/source/valley-and-home-v1/RI01/RI01-paddy-pack-v014.blend"
EXPORT=ROOT/"art/exports/valley-and-home-v1/RI01/v014"
EXPORT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SRC))
for name,delta in {
    "RI01_NorthBund_Stone.038":(0,0,-0.025),
    "RI01_WestBund_Stone.018":(0.030,0,0),
    "RI01_T_1_Stone.001":(0,0,-0.030),
}.items():
    obj=bpy.data.objects[name]
    obj.location=tuple(a+b for a,b in zip(obj.location,delta))
mesh_objects=[o for o in bpy.data.objects if o.type=="MESH"]

def child_mesh(parent_name):
    return sorted((o for o in mesh_objects if o.parent and o.parent.name==parent_name),key=lambda o:o.name)

def take_level(objs,lod):
    if lod==0:return objs
    out=[]
    count=0
    for obj in objs:
        name=obj.name
        if "EarthBase" in name or "EarthCore" in name or "Soil" in name or "Water" in name:
            out.append(obj)
        elif "Stone" in name:
            if (lod==1 and count%3!=0) or (lod==2 and count%7==0): out.append(obj)
            count+=1
        elif any(x in name for x in ("RiceBlade","YoungShoot")):
            if count%(2 if lod==1 else 7)==0: out.append(obj)
            count+=1
        elif "EdgeGrass" in name and lod==1 and count%3==0:
            out.append(obj)
            count+=1
    return out

def combine(name,source):
    assert source,name
    copies=[]
    for src in source:
        obj=src.copy()
        obj.data=src.data.copy()
        # All component meshes must expose the same active UV layer before
        # joining. Otherwise GLB writes zero UVs for faces from another layer.
        active_uv=obj.data.uv_layers.active
        if active_uv:
            keep=active_uv.name
            for layer in list(obj.data.uv_layers):
                if layer.name!=keep:
                    obj.data.uv_layers.remove(layer)
            obj.data.uv_layers.active.name="UVMap"
        if "RiceBlade" in src.name:
            for vert in obj.data.vertices:
                vert.co.z-=0.04  # anchor planted blades in the wet soil
        bpy.context.collection.objects.link(obj)
        obj.parent=None
        obj.matrix_world=src.matrix_world.copy()
        obj.hide_render=False
        copies.append(obj)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in copies:obj.select_set(True)
    bpy.context.view_layer.objects.active=copies[0]
    bpy.ops.object.join()
    combined=bpy.context.object
    combined.name=name
    combined.data.name=name+"_Mesh"
    return combined

base_all=child_mesh("RI01_Paddy_10x6")
detail=[obj for obj in base_all if "EdgeGrass" in obj.name]
base=[obj for obj in base_all if "EdgeGrass" not in obj.name]
states={state:child_mesh("RI01_State_"+state) for state in ("Dry","Flooded","Grown")}
connectors={kind:child_mesh("RI01_Bund_"+kind) for kind in ("Straight","Corner","T")}
pack={}
pack["Detail_EdgeGrass_LOD0"]=combine("Detail_RI01_Bund_EdgeGrass_LOD0",detail)
for lod in range(3):
    pack[f"Paddy_Base_LOD{lod}"]=combine(f"SM_RI01_Paddy_Base_LOD{lod}",take_level(base,lod))
    for state,objs in states.items():
        pack[f"Paddy_{state}_LOD{lod}"]=combine(
            f"SM_RI01_State_{state}_LOD{lod}",take_level(objs,lod))
    for kind,objs in connectors.items():
        pack[f"Bund_{kind}_LOD{lod}"]=combine(
            f"SM_RI01_Bund_{kind}_LOD{lod}",take_level(objs,lod))

# v013 QA identified two overlapping stones in the LOD0 base. Move the
# smaller connected stone along the bund, preserving its height and shape.
base_mesh=pack['Paddy_Base_LOD0'].data
seed=set(base_mesh.polygons[1579].vertices)
adj={v.index:set() for v in base_mesh.vertices}
for edge in base_mesh.edges:
    a,b=edge.vertices
    adj[a].add(b);adj[b].add(a)
stack=list(seed);island=set(seed)
while stack:
    for neighbour in adj[stack.pop()]:
        if neighbour not in island:
            island.add(neighbour);stack.append(neighbour)
assert len(island)==14, f'unexpected stone island size: {len(island)}'
assert -4.6 < min(base_mesh.vertices[i].co.x for i in island) < -4.2
for i in island:base_mesh.vertices[i].co.y += .35
base_mesh.update()

# The three mutually exclusive state surfaces sat within QA's 1 mm coplanar
# tolerance of the soil base. Lift their LOD0 geometry by five millimetres.
for state in ('Dry','Flooded','Grown'):
    mesh=pack[f'Paddy_{state}_LOD0'].data
    for vertex in mesh.vertices:
        vertex.co.z += .005
        # At the west bund the state side wall shared x=-4.525 m with a
        # sloping base stone; pull only that boundary 15 mm into the field.
        if abs(vertex.co.x + 4.525) < .001:vertex.co.x += .015
    mesh.update()

# Reversible collision geometry follows the walkable field and its bunds.
# Core team decides collider setup; this file only supplies a mesh asset.
collision_material=bpy.data.materials.new("RI01_Collision_Only")
def collision_box(name,center,size):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center)
    obj=bpy.context.object
    obj.name=name
    obj.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    obj.data.materials.append(collision_material)
    return obj
coll=[collision_box("RI01_Coll_Field",(0,0,0.045),(10,6,0.09))]
for name,center,size in (
    ("North",(0,2.61,0.22),(9.22,0.48,0.36)),
    ("West",(-4.61,0,0.22),(0.48,5.22,0.36)),
    ("East",(4.61,0,0.22),(0.48,5.22,0.36)),
    ("SouthLeft",(-3.905,-2.61,0.22),(1.41,0.48,0.36)),
    ("SouthRight",(1.105,-2.61,0.22),(7.01,0.48,0.36))):
    coll.append(collision_box("RI01_Coll_"+name,center,size))
pack["Paddy_Collision"]=combine("SM_RI01_Paddy_Collision",coll)
for obj in coll:bpy.data.objects.remove(obj,do_unlink=True)

for obj in mesh_objects:
    obj.hide_render=True
    obj.hide_set(True)
for key,obj in pack.items():
    obj.hide_render=(not key.endswith("LOD0") or "_Dry_" in key or "_Grown_" in key or key=="Paddy_Collision")

bpy.ops.wm.save_as_mainfile(filepath=str(OUT))

def export_group(name,keys):
    bpy.ops.object.select_all(action="DESELECT")
    for key in keys:
        obj=pack[key]
        obj.select_set(True)
        obj.hide_set(False)
        obj.hide_render=False
    bpy.context.view_layer.objects.active=pack[keys[0]]
    bpy.ops.export_scene.fbx(filepath=str(EXPORT/(name+".fbx")),use_selection=True,
        apply_unit_scale=True,bake_space_transform=False,path_mode="AUTO")
    bpy.ops.export_scene.gltf(filepath=str(EXPORT/(name+".glb")),
        export_format="GLB",use_selection=True)

export_group("RI01_Paddy",[key for key in pack if key.startswith("Paddy_")]+["Detail_EdgeGrass_LOD0"])
for kind in connectors:
    export_group("RI01_Bund_"+kind,[f"Bund_{kind}_LOD{lod}" for lod in range(3)])

triangles={key:sum(len(p.vertices)-2 for p in obj.data.polygons) for key,obj in pack.items()}
info={"asset":"RI01","version":"v014","minTier":"standard",
      "detailObjects":["Detail_RI01_Bund_EdgeGrass_LOD0"],"triangles":triangles,
      "states":["Dry","Flooded","Grown"],
      "inlet":{"name":"Slot_Inlet","width_m":0.8,"center_x_m":-2.8},
      "bounds_m":[10,6],"grid_m":1,
      "source":str(OUT),"three_view":"art/references/valley-and-home-v1/RI01/RI01-paddy-threeview-v002.png",
      "status":"packaged candidate; export reimport, dimension and visual LOD checks pending"}
(EXPORT/"model_info.json").write_text(json.dumps(info,indent=2,ensure_ascii=False),encoding="utf-8")
print(json.dumps(info,ensure_ascii=False))
