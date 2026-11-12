"""One before/after sheet per old set (from the repo root): python art/source/lod-backfill-c/compose_lod_sheets.py"""
import subprocess,sys
P='art/previews/lod-backfill-c';S='art/source/village-life-c/compose_sheet.py'
for out,title,ids in (('Q-lod-before-after.jpg','#34 村內告示 Q01–Q04：原本（只有 LOD0）→ LOD1 → LOD2，同光同角度',['Q01','Q02','Q03','Q04']),
                      ('C-lod-before-after.jpg','#35 回村道具 C01–C08：原本（只有 LOD0）→ LOD1 → LOD2，同光同角度',['C01','C02','C03','C04','C05','C06','C07','C08'])):
    items=[]
    for i in ids:items+=[f'{P}/{i}/{i}-before-threequarter.png={i} 原本',f'{P}/{i}/{i}-LOD1-threequarter.png={i} LOD1',f'{P}/{i}/{i}-LOD2-threequarter.png={i} LOD2']
    subprocess.run([sys.executable,S,f'{P}/{out}',title,'3']+items,check=True)
    items=[]
    for i in ids:items+=[f'{P}/{i}/{i}-LOD0-wire.png={i} LOD0 線框',f'{P}/{i}/{i}-LOD2-wire.png={i} LOD2 線框']
    subprocess.run([sys.executable,S,f'{P}/{out[0]}-lod-wire.jpg',title.replace('原本（只有 LOD0）→ LOD1 → LOD2','LOD0 和 LOD2 線框'),'4']+items,check=True)
