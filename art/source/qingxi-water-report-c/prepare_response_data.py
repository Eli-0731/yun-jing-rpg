"""Generate the file:// compatible browser data from response JSON."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
tool=ROOT/'tools/qingxi-water-report-c'
data=json.loads((tool/'response-data.json').read_text(encoding='utf-8'))['responses']
(tool/'responses.js').write_text('/* Eli-0731 / Codex. Source: response-data.json */\n(function(root){const data='+json.dumps(data,ensure_ascii=False,indent=2)+';if(typeof module!=="undefined")module.exports=data;else root.WaterReportResponses=data;})(typeof globalThis!=="undefined"?globalThis:this);\n',encoding='utf-8')
