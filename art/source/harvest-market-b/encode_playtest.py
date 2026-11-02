"""Encode the harvest playtest frames (HarvestMarketPlaytest, -harvestFrameEvery) into an MP4 with Blender's VSE.

  blender -b --python-exit-code 1 --python encode_playtest.py -- <frames_dir> [fps]

Writes art/previews/harvest-market-b/demo/harvest_playtest.mp4 (H.264, 1280x720).
"""
import bpy, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[2] / 'art/previews/harvest-market-b/demo/harvest_playtest.mp4'
argv = sys.argv[sys.argv.index('--') + 1:]
frames = sorted(Path(argv[0]).glob('*.png'))
fps = int(argv[1]) if len(argv) > 1 else 10   # one frame every 0.1 s = real time
assert frames, f'no frames in {argv[0]}'

s = bpy.context.scene
s.sequence_editor_create()
strip = s.sequence_editor.strips.new_image('walk', str(frames[0]), 1, 1) if hasattr(s.sequence_editor, 'strips') \
    else s.sequence_editor.sequences.new_image('walk', str(frames[0]), 1, 1)
for f in frames[1:]:
    strip.elements.append(f.name)
s.frame_start, s.frame_end = 1, len(frames)
s.render.fps = fps; s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = 1280, 720, 100
s.render.image_settings.media_type = 'VIDEO' if hasattr(s.render.image_settings, 'media_type') else s.render.image_settings.file_format
if hasattr(s.render.image_settings, 'media_type'):
    s.render.image_settings.media_type = 'VIDEO'
s.render.image_settings.file_format = 'FFMPEG'
s.render.ffmpeg.format = 'MPEG4'; s.render.ffmpeg.codec = 'H264'; s.render.ffmpeg.constant_rate_factor = 'MEDIUM'
s.render.use_sequencer = True
OUT.parent.mkdir(parents=True, exist_ok=True); s.render.filepath = str(OUT)
bpy.ops.render.render(animation=True)
print('ENCODED', OUT, len(frames), 'frames', f'{len(frames) / fps:.1f}s')
