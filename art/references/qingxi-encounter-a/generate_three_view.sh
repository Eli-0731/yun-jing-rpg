#!/usr/bin/env bash
# usage: gen.sh <ID> "<subject description>"
D="$(cd "$(dirname "$0")" && pwd)"
ID="$1"; SUBJ="$2"
PROMPT="Use your built-in image generation tool (do not write code to draw it). Generate ONE image: a clean orthographic three-view game asset concept sheet on a plain warm off-white background, three panels left to right labeled FRONT, SIDE, BACK, all at the same scale and true orthographic (no perspective), with simple dimension lines in metres. Style: cozy ancient-Chinese xianxia riverside forest village (Qingxi); painterly realistic stylized game art like high-end anime open-world games; palette of warm grey stone, aged wood, grass green, moss, clear water accents; soft daylight; no characters, no text other than the panel labels and the dimensions. Subject: ${SUBJ} After it is generated, copy the final PNG file into the current working directory as ${ID}_three_view.png and print its absolute path."
cd "$D" && timeout 900 codex exec --skip-git-repo-check -s workspace-write -C "$D" "$PROMPT" > "$D/${ID}.log" 2>&1
ls -la "$D/${ID}_three_view.png" 2>&1
