"""檢查新版 LF01/02 GLB 雙面透明卡、尺寸預覽及原版 LF03。"""
from pathlib import Path
import json
import struct
from PIL import Image

root = Path(__file__).resolve().parents[2] / 'exports/life-v1'
variants = {'LF01': {'spread': 'LF01_Spread.png', 'folded': 'LF01_Folded.png'},
            'LF02': {'ivory': 'LF02_Ivory.png', 'ochre': 'LF02_Ochre.png'}}
for code, names in variants.items():
    for label, texture in names.items():
        path = root / code / f'{code}_{label}.glb'
        with path.open('rb') as file:
            header = file.read(20)
            magic, version, total = struct.unpack_from('<4sII', header)
            json_len, chunk_type = struct.unpack_from('<II', header, 12)
            data = json.loads(file.read(json_len).decode('utf-8'))
        assert magic == b'glTF' and version == 2 and total == path.stat().st_size
        assert chunk_type == 0x4E4F534A
        assert len(data['meshes']) == 1 and len(data['materials']) == 1
        assert data['materials'][0]['alphaMode'] == 'BLEND'
        assert data['materials'][0]['doubleSided'] is True
        index = data['meshes'][0]['primitives'][0]['indices']
        assert data['accessors'][index]['count'] == 6
        image = Image.open(root / code / texture)
        assert image.size == (1024, 1024) and image.mode == 'RGBA'
        assert image.getchannel('A').getextrema() == (0, 255)
        print('小卡通過', code, label, '2 三角面')
    assert Image.open(root / code / f'{code}_animation-preview.png').size == (2048, 1024)
    distance = 60 if code == 'LF01' else 3
    assert Image.open(root / code / f'{code}_game-size-{distance}m.png').size == (1920, 1080)

glow = Image.open(root / 'LF03/LF03_Glow.png')
assert glow.size == (256, 256) and glow.mode == 'RGBA'
assert glow.getpixel((0, 0))[3] == 0 and glow.getpixel((128, 128))[3] > 200
params = json.loads((root / 'LF03/particle_params.json').read_text(encoding='utf-8'))
assert params['minTier'] == 'high' and params['unity_particle_recommendation']['maxParticles'] <= 60
print('LF_QA_PASS')
