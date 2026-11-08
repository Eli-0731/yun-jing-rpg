"""Turns the Unity walkthrough frames (artifacts/tea-terraces-unity/walkthrough_frames/frame_00000.jpg ...) into an H.264 mp4 with Blender's sequencer.

  blender --background --factory-startup --python art/source/tea-terraces-b/walkthrough_video.py -- [frames_dir] [out.mp4]

Defaults: frames from artifacts/tea-terraces-unity/walkthrough_frames, video to art/previews/tea-terraces-b/showcase/showcase_walkthrough_unity.mp4.
The frames are Unity URP renders; this script only encodes them (30 fps, no effects).
"""
import bpy, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
frames = Path(argv[0]) if argv else REPO / 'artifacts' / 'tea-terraces-unity' / 'walkthrough_frames'
out = Path(argv[1]) if len(argv) > 1 else REPO / 'art' / 'previews' / 'tea-terraces-b' / 'showcase' / 'showcase_walkthrough_unity.mp4'
files = sorted(frames.glob('frame_*.jpg'))
if not files: raise SystemExit(f'no frames in {frames}')
img = bpy.data.images.load(str(files[0])); w, h = img.size
scene = bpy.context.scene
ed = scene.sequence_editor_create()
strips = ed.strips if hasattr(ed, 'strips') else ed.sequences
st = strips.new_image('walk', str(files[0]), channel=1, frame_start=1)
for f in files[1:]: st.elements.append(f.name)
scene.frame_start, scene.frame_end = 1, len(files)
scene.render.fps = 30; scene.render.resolution_x, scene.render.resolution_y = w, h; scene.render.resolution_percentage = 75   # 960 x 540 keeps the clip small enough for the repo
scene.view_settings.view_transform = 'Standard'   # the frames are already display-ready
if hasattr(scene.render.image_settings, 'media_type'): scene.render.image_settings.media_type = 'VIDEO'   # Blender 5
scene.render.image_settings.file_format = 'FFMPEG'
ff = scene.render.ffmpeg; ff.format = 'MPEG4'; ff.codec = 'H264'; ff.constant_rate_factor = 'MEDIUM'; ff.ffmpeg_preset = 'GOOD'; ff.audio_codec = 'NONE'
out.parent.mkdir(parents=True, exist_ok=True)
scene.render.filepath = str(out)
bpy.ops.render.render(animation=True)
if not out.exists():   # Blender may append the frame range to the name
    made = sorted(out.parent.glob(out.stem + '*.mp4'), key=lambda p: p.stat().st_mtime)
    if made: made[-1].replace(out)
print('WALKTHROUGH_VIDEO', out, len(files), 'frames', f'{len(files) / 30:.1f} s', flush=True)
