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
    'A04_silt_side': '泥沙堆形 2（沙嘴）：3.2 m 長、1.2 m 寬、0.35 m 高，沿一側河岸伸出的低矮沙舌，把細流擠到對岸；頂上有波紋。和堆形 1 的矮壩形體不同。',
    'A04_silt_jam': '泥沙堆形 3（雜物壩）：一根半腐倒木橫過河道當骨架，後方堆泥沙、斷枝和落葉，水從木頭下滲出兩道細流，上游積成淺潭。',
    'A05_tall_sparse': '枯草 2：0.6 m 寬、1.0 m 高，少數又長又硬的葉片，幾片折斷下垂，兩根乾穗。稀疏、透空。',
    'A05_low_mat': '枯草 3：1.1 m 寬、0.3 m 高，順著舊水流方向倒伏、蓋在石頭邊的草墊，上面結著乾泥。',
    'A07': '育幼足跡泥面：3×2.5 m 濕泥，成體 0.22 m、幼獸 0.12 m、小崽 0.06 m 三組四趾爪印並排走向水邊，飲水處踩亂，有斷蘆葦與掉落的灰毛。只供觀察，不是怪物模型。',
    'A08_steps_line': '淺灘踏面 1：六塊平頂踏石排成微彎一列，頂面高出水面約 0.12 m，兩端以碎石坡接到岸腳。',
    'A08_slabs_stagger': '淺灘踏面 2：四塊 0.6–0.8 m 的大石板交錯成之字形，陰面有苔，石板間有淺水流過。',
    'A08_gravel_bar': '淺灘踏面 3：自然卵石灘橫過河道，剛好露出水面，三塊大圓石可踩，低處有淺淺的急流漫過。',
    'A09': '木樁水位尺：1.6 m 方木樁，每 0.1 m 刻痕、每 0.5 m 長刻；0.85 m 處綁繩是舊高水位，以上木色淺、以下深色有乾泥線；現在的水只到 0.3 m。',
    'A10': '倒伏竹林束：4 m 長、2.5 m 寬，八到十根乾竹從活竹叢倒下，一側斜成 1.6 m 高的屏障擋住部分視線，一端留有 1.2 m 寬可通行的缺口。',
    'A11': '觀測亭殘基：3×3 m、高 0.45 m 的石台，三級台階，四個柱座（兩根斷木柱、銅箍），一根倒下的橫梁，後側石凳，散落碎瓦，台側刻水紋。是休息比較線索的地方，不是完整房屋。',
    'A12': '水脈共鳴石：1.1 m 高、0.7 m 寬的深藍灰河石，細細的青白色紋路像支流一樣分岔，光很弱；腳下一圈扁石和淺水盆。沒有浮空零件或箭頭。',
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
