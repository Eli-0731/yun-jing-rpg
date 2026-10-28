"""Generate a labeled vector dimension diagram from measured export bounds."""
import json,html
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
r=json.loads((ROOT/'art/exports/qingxi-return-c/batch2-manifest.json').read_text(encoding='utf-8'))
names=['回村背籠','低木分揀桌','收納竹匣','藥草布包','委託封條盒','木製座凳','簡易油紙燈','手札皮扣與木托']
parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="850" viewBox="0 0 1200 850"><rect width="1200" height="850" fill="#efecdf"/><g font-family="Microsoft JhengHei, sans-serif" fill="#2d4438"><text x="55" y="45" font-size="26">青溪回村角落 · 尺寸與擺位</text><text x="55" y="74" font-size="14">Eli-0731 / Codex · 公尺 · 依 GLB 實測外包尺寸，含繩帶與扣件</text><rect x="80" y="115" width="480" height="640" fill="#d5dccb" stroke="#566a51" stroke-width="2"/><text x="275" y="105" font-size="18">3.00 m</text><text x="20" y="445" font-size="18" transform="rotate(-90 20 445)">4.00 m</text><text x="230" y="785" font-size="14">平面圖：上方 +Y，前方 −Y</text>']
colors=['#a38c56','#7b5a3b','#b49a58','#718957','#8c714c','#8c6a46','#d0b669','#765946']
for i,a in enumerate(r['assets']):
    x,y,z=r['placements_xyz'][a['id']];w,d,h=a['dimensions_xyz'];sx=80+(x+1.5-w/2)*160;sy=115+(2-y-d/2)*160
    parts.append(f'<rect x="{sx:.2f}" y="{sy:.2f}" width="{w*160:.2f}" height="{d*160:.2f}" fill="{colors[i]}" fill-opacity=".65" stroke="#3d5039"/><text x="{sx+3:.2f}" y="{sy+14:.2f}" font-size="11">{a["id"]}</text>')
    ty=154+i*60
    parts.append(f'<text x="625" y="{ty}" font-size="18">{a["id"]} · {html.escape(names[i])}</text><text x="625" y="{ty+23}" font-size="14">{w:.3f} × {d:.3f} × {h:.3f} m · 底部 z={z:.2f} m</text>')
parts.append('<text x="625" y="690" font-size="14">C03／C04 放桌上；C08 放凳上，重疊為上下擺放。</text><text x="625" y="718" font-size="14">尺寸為原型實測，不代表碰撞、LOD 或手機效能驗收。</text><text x="625" y="746" font-size="14">角色尺度參考：1.70 m，見同目錄 scale-3x4m.png。</text></g></svg>')
(ROOT/'tools/qingxi-return-c/previews/dimensions.svg').write_text(''.join(parts),encoding='utf-8')
print('DIMENSION_PLAN_WRITTEN')
