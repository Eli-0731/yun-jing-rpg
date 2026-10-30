#!/usr/bin/env bash
# usage: generate_three_view.sh <ID> [out_dir]   (subject text is read from prompts.json)
# Calls the local Codex CLI, which uses OpenAI image generation, to make one FRONT / SIDE / BACK sheet per asset or variant.
D="$(cd "$(dirname "$0")" && pwd)"
ID="$1"; OUT="${2:-$D}"
SUBJ="$(python -c "import json,sys; print(json.load(open(sys.argv[1], encoding='utf8'))[sys.argv[2]])" "$D/prompts.json" "$ID")"
PROMPT="Use your built-in image generation tool (do not write code to draw it). Generate ONE image: a clean orthographic three-view game asset concept sheet on a plain warm off-white background, three panels left to right labeled FRONT, SIDE, BACK, all at the same scale and true orthographic (no perspective), with simple dimension lines in metres. Style: ancient-Chinese xianxia mountain stream above a riverside village (Qingxi), the stream is running low; painterly realistic stylized game art like high-end anime open-world games; palette of warm grey stone, aged wood, a little oxidised green bronze, low-saturation blue-green water, dry ochre grass, damp dark soil and moss; soft daylight; no characters, no text other than the panel labels and the dimensions. Subject: ${SUBJ} After it is generated, copy the final PNG file into the current working directory as ${ID}_three_view.png and print its absolute path."
mkdir -p "$OUT" && cd "$OUT" && timeout 900 codex exec --skip-git-repo-check -s workspace-write -C "$OUT" "$PROMPT" < /dev/null > "$OUT/${ID}.log" 2>&1
ls -la "$OUT/${ID}_three_view.png" 2>&1
