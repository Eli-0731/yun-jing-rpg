"""Labeled layout diagram from this package's measured bounds, no outside assets."""
import json,html
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
r=json.loads((ROOT/'art/exports/qingxi-water-report-c/batch2-manifest.json').read_text(encoding='utf-8'))
names=['村民議事矮桌','可翻面水情告示','小型水桶組','竹製取水扁擔','田邊濕度木牌','水渠施工布旗','修渠手工具箱','共修紀錄石牌']
scale=126;left=88;top=115;colors=['#93704a','#9b7952','#b18d54','#8a925c','#879062','#b59a5c','#826a4c','#81917f']
p=['<svg xmlns="http://www.w3.org/2000/svg" width="1250" height="850" viewBox="0 0 1250 850"><rect width="1250" height="850" fill="#eeecdf"/><g font-family="Microsoft JhengHei, sans-serif" fill="#29483e"><text x="55" y="44" font-size="26">青溪水路回聲 · 3 × 5 m 村角尺寸</text><text x="55" y="74" font-size="14">Eli-0731 / Codex · 實測公尺 · 1.75 m 角色參考 · C05 尖端入土 0.12m</text>']
p.append(f'<rect x="{left}" y="{top}" width="{3*scale}" height="{5*scale}" fill="#d3dcc8" stroke="#526d50" stroke-width="2"/><rect x="{left+2.02*scale}" y="{top}" width="{.98*scale}" height="{5*scale}" fill="#e7e7d5"/><text x="{left+2.35*scale}" y="{top+40}" font-size="14" writing-mode="tb">預留約 0.98 m 通行帶</text><text x="230" y="104" font-size="18">3.00 m</text><text x="25" y="460" font-size="18" transform="rotate(-90 25 460)">5.00 m</text>')
for i,a in enumerate(r['assets']):
    id=a['id'];x,y,z=r['placements_xyz'][id];w,d,h=a['dimensions_xyz'];pd=h if id=='C04' else d
    sx=left+(x+1.5-w/2)*scale;sy=top+(2.5-y-pd/2)*scale
    p.append(f'<rect x="{sx:.2f}" y="{sy:.2f}" width="{w*scale:.2f}" height="{pd*scale:.2f}" fill="{colors[i]}" fill-opacity=".75" stroke="#435a42"/><text x="{sx+2:.2f}" y="{sy+13:.2f}" font-size="10">{id}</text>')
    ty=145+i*65
    p.append(f'<text x="535" y="{ty}" font-size="18">{id} · {html.escape(names[i])}</text><text x="535" y="{ty+23}" font-size="14">{w:.3f} × {d:.3f} × {h:.3f} m · {a["triangles"]} 三角面 · {a["materials"]} 材質</text>')
p.append('<text x="535" y="705" font-size="14">C04 在配置中平放；C07 放在 C01 桌面，為上下擺放。</text><text x="535" y="733" font-size="14">出村主路在樣片之外；此圖不代表主場景碰撞驗收。</text><text x="90" y="784" font-size="14">上方 +Y；正面 −Y。水桶開放水面為視覺材質，不計碰撞。</text></g></svg>')
(ROOT/'art/previews/qingxi-water-report-c/dimensions.svg').write_text(''.join(p),encoding='utf-8')
print('WATER_REPORT_DIMENSIONS_WRITTEN')
