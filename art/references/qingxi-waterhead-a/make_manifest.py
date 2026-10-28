"""Write image-manifest.json: size, SHA-256 and the review note for every saved three-view (run after generating)."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REVIEW = {
    'A01_straight': '直段：7 m 寬、6 m 長，河道 2.4 m、河床低於岸頂 0.9 m；中間細流，兩側露出卵石與濕泥，岸上一圈淺色舊水位。兩端剖面相同，可拼接。',
    'A01_bend_left': '左彎約 25°：內岸卵石灘、外岸斜倒大石；兩端剖面與直段相同。',
    'A01_bend_right': '右彎約 40°：外岸是有樹根的高層理岩壁，內岸低矮沙洲。圖中兩端畫成整齊石柱收邊，建模改為自然斷面。',
    'A01_narrow': '收窄：兩塊大岩把河道夾到約 1.2 m，有小落差與白水，兩端仍為 2.4 m 接口。圖中水畫得偏深，建模保持低水位。',
    'A01_end_source': '收尾件：4 m 長，下游端是與其他段相同的 2.4 m 接口；往上游河床抬升進入亂石堆，腳下有小泉潭與兩道細流，背面封閉沒有開口。',
    'A02_side_crack': '石槽變體 1：3 m 長、0.7 m 寬、0.55 m 高的 U 形槽，外側雲紋帶；中間一塊側面裂開缺角，細流漏到地上。正面看得見破口。',
    'A02_end_break': '石槽變體 2：最後一塊斜裂，末端一截與端柱往外傾倒，水從缺口流下，地上有碎石。和變體 1 的破口位置、形狀不同。',
    'A03': '半埋舊陣基：直徑 1.8 m 圓台，石塊分件，一側傾斜沉入土中；青綠銅環有卦象刻槽，缺一段，地上有掉落的銅片。是殘件，不是修復完整品。',
    'A04': '泥沙堆：2.4×2.2×0.6 m，夾斷枝、落葉、卵石，堵住大半河道，後方積水、一側細流；下方附清理後只剩兩側低矮殘沙的狀態。',
    'A05': '枯黃水草：0.9 m 寬、0.7 m 高的莎草叢，葉片下垂、尖端枯褐，根部一點綠，龜裂乾泥；和綠色蘆葦明顯不同。',
    'A06': '示跡石：1.2 m 高、1.0 m 寬，0.35 m 處是現在的濕線，往上是淺色乾痕，0.85 m 處一圈乾苔是舊高水位，頂部有苔。',
}
out = []
for p in sorted(HERE.glob('*_three_view.png')):
    key = p.name.replace('_three_view.png', '')
    out.append({
        'id': key, 'file': p.name, 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
        'views': ['FRONT', 'SIDE', 'BACK'], 'generator': 'OpenAI image generation via Codex CLI (codex exec), 2026-10-28; prompts in prompts.json',
        'review': REVIEW[key], 'reviewed': 'before modelling; build_waterhead.py refuses to build an asset whose three-view is missing',
    })
(HERE / 'image-manifest.json').write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8')
print(len(out), 'entries')
