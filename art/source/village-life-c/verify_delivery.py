"""Verify delivered village props without changing meshes or running Unity.

blender -b --factory-startup --python-exit-code 1 -P art/source/village-life-c/verify_delivery.py -- LV01 LV02
No IDs: checks every entry in model_info.json. Blender's FBX importer can remove
faces; source FBX polygon counts are authoritative, with imported counts recorded
separately. Existing Unity report consistency is checked, not a new Unity run.
"""
import bpy,hashlib,json,re,struct,sys
from pathlib import Path
from mathutils import Vector
from io_scene_fbx import parse_fbx

ROOT=Path(__file__).resolve().parents[3]
info=json.loads((ROOT/'art/exports/village-life-c/model_info.json').read_text(encoding='utf-8'))
ids=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else list(info)
unity=(ROOT/'art/previews/village-life-c/unity/report.txt').read_text(encoding='utf-8')
rows=[]
for id in ids:
    d=info[id]
    refs=ROOT/'art/references'/id
    assert len(list(refs.glob('*cand-*.png')))>=4,id
    assert '選用' in (refs/'prompt.txt').read_text(encoding='utf-8'),id
    for filename,px in d['lods']['LOD0']['textures_px'].items():
        data=(ROOT/'art/textures/village-life-c'/filename).read_bytes()
        assert data[:8]==b'\x89PNG\r\n\x1a\n',filename
        width,height=struct.unpack_from('>II',data,16)
        assert [width,height]==px and max(width,height)<=1024,(filename,width,height)
    for key in ['blend','fbx','glb']:
        assert (ROOT/d['files'][key]).stat().st_size>2000,(id,key)

    tree,_=parse_fbx.parse(str(ROOT/d['files']['fbx']))
    objects=next(e for e in tree.elems if e.id==b'Objects')
    connections=next(e for e in tree.elems if e.id==b'Connections')
    names={e.props[0]:e.props[1].split(b'\x00')[0].decode('utf-8') for e in objects.elems if e.id==b'Model'}
    parents={e.props[1]:e.props[2] for e in connections.elems if e.id==b'C' and e.props[0]==b'OO'}
    raw={lod:0 for lod in d['lods']}
    for e in objects.elems:
        if e.id!=b'Geometry':continue
        name=names.get(parents.get(e.props[0]),'')
        lod=next((lod for lod in raw if name.endswith('_'+lod)),None)
        if lod is None:continue
        indices=next(c for c in e.elems if c.id==b'PolygonVertexIndex').props[0]
        count=0
        for index in indices:
            count+=1
            if index<0:raw[lod]+=count-2;count=0

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(ROOT/d['files']['fbx']))
    assert not any(o.type=='ARMATURE' for o in bpy.data.objects),id
    lods={}
    for lod,expected in d['lods'].items():
        meshes=[o for o in bpy.data.objects if o.type=='MESH' and o.name.endswith('_'+lod)]
        assert meshes,(id,lod)
        triangles=sum(len(p.vertices)-2 for o in meshes for p in o.data.polygons)
        materials={m.name for o in meshes for m in o.data.materials if m}
        assert raw[lod]==expected['triangles'],(id,lod,'FBX source count',raw[lod],expected)
        assert len(meshes)==expected['objects'] and len(materials)==expected['materials']==1,(id,lod)
        assert all(o.data.uv_layers for o in meshes),(id,lod,'UV')
        lods[lod]={'source_triangles':raw[lod],'blender_import_triangles':triangles,'importer_removed':raw[lod]-triangles,'objects':len(meshes),'materials':len(materials)}
    match=re.search(r'PASS '+re.escape(id)+r': triangles LOD0/1/2 = (\d+) / (\d+) / (\d+)',unity)
    assert match and list(map(int,match.groups()))==[raw['LOD0'],raw['LOD1'],raw['LOD2']],(id,'archived Unity count consistency')
    meshes=[o for o in bpy.data.objects if o.type=='MESH' and o.name.endswith('_LOD0')]
    points=[o.matrix_world@Vector(v) for o in meshes for v in o.bound_box]
    bounds=[[min(p[i] for p in points),max(p[i] for p in points)] for i in range(3)]
    size=[b-a for a,b in bounds]
    assert all(abs(a-b)<=.02 for a,b in zip(size,d['dimensions_xyz_m'])),(id,size)
    assert all(a<=b+.002 for a,b in zip(size,d['size_limit_xyz_m'])),(id,size)
    assert abs(bounds[2][0])<=.002,(id,bounds)
    assert bpy.data.objects.get(id+'_GroundOrigin') is not None,(id,'root')
    rows.append({'id':id,'fbx_sha256':hashlib.sha256((ROOT/d['files']['fbx']).read_bytes()).hexdigest(),'dimensions':size,'bottom_z':bounds[2][0],'lods':lods,'pass':True})
report={'blender':bpy.app.version_string,'pass':True,'unity_report':'Existing report checked for consistency; Unity was not rerun by this script.','items':rows}
(ROOT/'art/previews/village-life-c/qa/fbx-roundtrip.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('VILLAGE_DELIVERY_PASS',len(rows))
