"""Run the unchanged shared renderer on exported files; no Unity or shared-file writes.
Use bundled Python: python.exe bm09_reviews.py --quick | --full
"""
import sys, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
B=ROOT.parent/'tooling/blender-4.5.3-windows-x64/blender.exe'
RENDER=ROOT/'art/source/modelling-basics-c/render_basics.py'
OUT=ROOT/'art/exports/modelling-basics-c'
PRE=ROOT/'art/previews/modelling-basics-c'
jobs=[]
def job(pid,tag,files=None,extra=()):
    d=PRE/pid[:4];d.mkdir(parents=True,exist_ok=True)
    args=['--glb',files or str(OUT/(pid+'.glb')),'--out',str(d),'--tag',tag,'--res','1200x900','--samples','48']+list(extra)
    jobs.append((d,tag,args))

if '--quick' in sys.argv:
    for pid in ['BM10_01','BM10_02','BM10_03']:
        job(pid,pid+'-close',extra=['--views','','--no-ruler','--at','0,0,0,0.005','--cam','0,-0.35,1.5,0,0,0,55','--light','neutral'])
else:
    for pid in ['BM09_01','BM09_02']:
        job(pid,pid+'-scale',extra=['--views','front,side,back,threequarter','--wire'])
        for lod in [0,1]:
            job(pid,pid+f'-lod{lod}-nodetail',str(OUT/(pid+'.fbx')),['--views','threequarter','--no-ruler','--hide','Detail_','--lod',str(lod)])
        comparison=ROOT/'art/exports/qingxi-detail-props-v2/qingxi-fern-flower-v2.glb'
        job(pid,pid+'-vs-qingxi',str(OUT/(pid+'.glb'))+','+str(comparison),['--views','threequarter','--no-ruler','--at','-0.8,0,0;0.7,0,0'])
    for pid in ['BM10_01','BM10_02','BM10_03']:
        tiled=','.join([str(OUT/(pid+'.glb'))]*16)
        at=';'.join(f'{x-1.5},{y-1.5},0,0.005' for y in range(4) for x in range(4))
        job(pid,pid+'-tile4x4',tiled,['--views','','--no-ruler','--at',at,'--cam','4.6,-5.8,6.5,0,0,0,52','--light','neutral'])
        job(pid,pid+'-tile4x4-top',tiled,['--views','','--no-ruler','--at',at,'--cam','0,-0.001,6.5,0,0,0,52','--light','neutral'])
        job(pid,pid+'-close',extra=['--views','','--no-ruler','--at','0,0,0,0.005','--cam','0,-0.35,1.5,0,0,0,55','--light','neutral'])
for d,tag,args in jobs:
    print('REVIEW_BEGIN',tag,flush=True)
    with (d/(tag+'.log')).open('w',encoding='utf-8') as log:
        r=subprocess.run([str(B),'-b','--factory-startup','-P',str(RENDER),'--']+args,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,creationflags=0x08000000)
    if r.returncode:raise RuntimeError(f'{tag} failed: {r.returncode}; see log')
    print('REVIEW_DONE',tag,flush=True)
