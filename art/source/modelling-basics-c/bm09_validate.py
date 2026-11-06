"""Validate exported GLB/FBX geometry, roots, tiers, double-sided alpha, and exact tile edges.
Blender 4.5.3 -b --factory-startup -P bm09_validate.py
"""
import bpy, json, struct
from pathlib import Path
from mathutils import Vector
import numpy as np
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'art/exports/modelling-basics-c';PRE=ROOT/'art/previews/modelling-basics-c'
info=json.loads((OUT/'model_info_bm09_bm10.json').read_text(encoding='utf-8'))
results={};edges={}
for pid,meta in info.items():
    data=(OUT/(pid+'.glb')).read_bytes();magic,version,length=struct.unpack_from('<III',data)
    assert magic==0x46546c67 and version==2 and length==len(data)
    n,typ=struct.unpack_from('<II',data,12);doc=json.loads(data[20:20+n])
    assert any(node.get('name')==pid+'_GroundOrigin' for node in doc['nodes'])
    for mat in doc['materials']:
        assert mat.get('doubleSided') is True,(pid,mat)
        if 'Fronds' in mat['name'] or pid in ('BM10_02','BM10_03'):assert mat.get('alphaMode')=='MASK',(pid,mat.get('alphaMode'))
    tri=sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes'] for p in m['primitives'])
    assert tri==meta['triangles_total'][0],(pid,tri,meta['triangles_total'])
    result={'glb_triangles':tri,'glb_materials':[{k:m.get(k) for k in ['name','doubleSided','alphaMode','alphaCutoff']} for m in doc['materials']]}
    for ext in ['glb','fbx']:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        if ext=='glb':bpy.ops.import_scene.gltf(filepath=str(OUT/(pid+'.glb')))
        else:bpy.ops.import_scene.fbx(filepath=str(OUT/(pid+'.fbx')))
        objs=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert not any('Collision' in o.name for o in objs)
        roots=[o for o in bpy.context.scene.objects if o.name==pid+'_GroundOrigin'];assert len(roots)==1
        lodcounts=[];dimensions=[]
        for lod in range(1 if ext=='glb' else 3):
            mesh=[o for o in objs if o.name.endswith('LOD'+str(lod))]
            assert len(mesh)==len(meta['groups'])
            for o in mesh:
                assert o.data.uv_layers and all(np.isfinite(v.co[:]).all() for v in o.data.vertices)
                assert all(p.area>1e-13 for p in o.data.polygons),(pid,o.name,'zero-area polygon')
                assert o.parent and o.parent.name==pid+'_GroundOrigin'
            count=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in mesh)
            assert count==meta['triangles_total'][lod],(pid,ext,lod,count)
            lodcounts.append(count)
            pts=np.array([tuple(o.matrix_world@v.co) for o in mesh for v in o.data.vertices]);lo,hi=pts.min(0),pts.max(0)
            assert abs(lo[2])<1e-5,(pid,ext,lod,lo)
            if lod==0:assert np.allclose(hi-lo,meta['dimensions_xyz_m'],atol=2e-5),(pid,ext,hi-lo)
            dimensions.append([round(float(v),6) for v in hi-lo])
        result[ext]={'lod_triangles':lodcounts,'lod_dimensions_xyz_m':dimensions,'no_collision':True,'root':roots[0].name}
    if pid.startswith('BM09'):assert meta['detailObjects'] and meta['detailMeshes']
    else:
        assert meta['minTier']=='ultra'
        for kind,relative in meta['textures']['Ground'].items():
            p=ROOT/relative;im=bpy.data.images.load(str(p),check_existing=False);im.colorspace_settings.name='Non-Color'
            w,h=im.size;assert (w,h)==(2048,2048)
            a=np.empty(w*h*4,np.float32);im.pixels.foreach_get(a);a=np.rint(a.reshape(h,w,4)*255).astype(np.int16)
            lr=int(np.abs(a[:,0]-a[:,-1]).max());tb=int(np.abs(a[0]-a[-1]).max())
            assert lr==tb==0,(pid,kind,lr,tb)
            record={'size':[w,h],'left_right_max_8bit':lr,'top_bottom_max_8bit':tb}
            if kind=='Albedo':
                record['alpha_zero_fraction']=round(float((a[...,3]==0).mean()),5)
                record['alpha_opaque_fraction']=round(float((a[...,3]==255).mean()),5)
                if pid!='BM10_01':assert .1<record['alpha_zero_fraction']<.95
            edges[p.name]=record;bpy.data.images.remove(im)
    results[pid]=result
(PRE/'BM09/validation.json').write_text(json.dumps({'passed':True,'blender':bpy.app.version_string,'models':results},indent=2),encoding='utf-8')
(PRE/'BM10/tiling_check.json').write_text(json.dumps(edges,indent=2),encoding='utf-8')
print('VALIDATION_PASSED',json.dumps({p:m['glb_triangles'] for p,m in results.items()}));print('ALL_12_MAPS_EDGE_MAX_0')
