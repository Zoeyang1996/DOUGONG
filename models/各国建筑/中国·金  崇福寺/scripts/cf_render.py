# -*- coding: utf-8 -*-
"""cf_render.py —— 渲染预览 / 成品图
用法: blender -b file.blend -P cf_render.py -- <camera> <samples> <w> <h> <out.png>
"""
import bpy, sys, os

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
cam_name = argv[0] if len(argv) > 0 else "相机_正面"
samples = int(argv[1]) if len(argv) > 1 else 64
w = int(argv[2]) if len(argv) > 2 else 1280
h = int(argv[3]) if len(argv) > 3 else 720
out = argv[4] if len(argv) > 4 else None

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU'
scene.cycles.samples = samples
scene.cycles.use_denoising = True
scene.render.resolution_x = w
scene.render.resolution_y = h
scene.render.resolution_percentage = 100

try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    for d in prefs.devices:
        d.use = (d.type == 'OPTIX')
    print("[dev]", [(d.name, d.use) for d in prefs.devices])
except Exception as e:
    print("device err", e)

cam = bpy.data.objects.get(cam_name)
if cam:
    scene.camera = cam
if out is None:
    out = os.path.join(os.path.dirname(bpy.data.filepath), "renders", cam_name + ".png")
os.makedirs(os.path.dirname(out), exist_ok=True)
scene.render.filepath = out
scene.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(write_still=True)
print("[render]", out)
