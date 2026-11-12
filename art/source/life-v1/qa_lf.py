"""檢查交付 GLB 的動畫樞軸、顏色變體與粒子貼圖。"""
from pathlib import Path
import json, struct
from PIL import Image

root=Path(__file__).resolve().parents[2]/'exports/life-v1'
for code,labels in {'LF01':['slate','warm','pale'],'LF02':['ivory','yellow']}.items():
    for label in labels:
        p=root/code/f'{code}_{label}.glb'
        with p.open('rb') as f:
            header=f.read(20)
            magic,version,total=struct.unpack_from('<4sII',header)
            json_len,chunk_type=struct.unpack_from('<II',header,12)
            data=json.loads(f.read(json_len).decode('utf-8'))
        assert magic==b'glTF' and version==2 and total==p.stat().st_size
        assert chunk_type==0x4E4F534A
        assert data.get('animations'),p
        names={n.get('name') for n in data.get('nodes',[])}
        assert {'Wing_L_Pivot','Wing_R_Pivot'}<=names,p
        print(code,label,'animations',len(data['animations']),'nodes',len(names))
    assert Image.open(root/code/f'{code}_animation-preview.png').size==(1920,480)
glow=Image.open(root/'LF03/LF03_Glow.png')
assert glow.size==(256,256) and glow.mode=='RGBA'
assert glow.getpixel((0,0))[3]==0 and glow.getpixel((128,128))[3]>200
params=json.loads((root/'LF03/particle_params.json').read_text(encoding='utf-8'))
assert params['minTier']=='high' and params['unity_particle_recommendation']['maxParticles']<=60
print('LF_QA_PASS')
