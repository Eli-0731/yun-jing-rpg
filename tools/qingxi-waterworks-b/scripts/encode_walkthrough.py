"""Encode walkthrough frames (walkthrough.js via serve.mjs /__frame) into an H.264 MP4.

  uv run --no-project --with imageio-ffmpeg python -I tools/qingxi-waterworks-b/scripts/encode_walkthrough.py <frames_dir> <out.mp4> [fps]

Uses the ffmpeg binary bundled with imageio-ffmpeg (uv cache only; nothing installed system-wide).
"""
import subprocess, sys
from pathlib import Path
import imageio_ffmpeg

frames, out = Path(sys.argv[1]), Path(sys.argv[2])
fps = int(sys.argv[3]) if len(sys.argv) > 3 else 12
files = sorted(frames.glob('f0[0-8]*.jpg'))   # f09xxx are still shots, not part of the video
assert files, f'no frames in {frames}'
out.parent.mkdir(parents=True, exist_ok=True)
lst = frames / 'frames.txt'
lst.write_text(''.join(f"file '{f.as_posix()}'\nduration {1 / fps}\n" for f in files) + f"file '{files[-1].as_posix()}'\n", encoding='utf-8')
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', str(lst),
                '-vf', f'fps={fps},format=yuv420p', '-c:v', 'libx264', '-crf', '20', '-movflags', '+faststart', str(out)], check=True)
print('ENCODED', out, len(files), 'frames', f'{len(files) / fps:.1f}s')
