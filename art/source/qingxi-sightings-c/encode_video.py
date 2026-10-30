# Blender VSE: screencast frames (variable timing) -> constant 30 fps H.264 mp4.
# blender -b --factory-startup -P encode.py -- <framesDir> <out.mp4>
import bpy, sys, json, os, bisect
fdir, out = sys.argv[sys.argv.index('--') + 1:][:2]
j = json.load(open(os.path.join(fdir, 'frames.json'), encoding='utf8'))
fr = j['frames']; t0 = fr[0]['t']; ts = [f['t'] - t0 for f in fr]
FPS = 30; n = int(ts[-1] * FPS) + 1
names = [fr[max(0, bisect.bisect_right(ts, i / FPS) - 1)]['file'] for i in range(n)]
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1440, 900, 100
sc.render.fps = FPS; sc.frame_start = 1; sc.frame_end = n
se = sc.sequence_editor_create()
st = se.strips.new_image('rec', os.path.join(fdir, names[0]), 1, 1)
for nm in names[1:]:
    st.elements.append(nm)
st.frame_final_duration = n
r = sc.render; r.image_settings.file_format = 'FFMPEG'
r.ffmpeg.format = 'MPEG4'; r.ffmpeg.codec = 'H264'; r.ffmpeg.constant_rate_factor = 'HIGH'; r.ffmpeg.ffmpeg_preset = 'GOOD'
r.ffmpeg.audio_codec = 'NONE'; r.filepath = os.path.abspath(out)
sc.view_settings.view_transform = 'Standard'
bpy.ops.render.render(animation=True)
print('ENCODED', n, 'frames', n / FPS, 's ->', out)
