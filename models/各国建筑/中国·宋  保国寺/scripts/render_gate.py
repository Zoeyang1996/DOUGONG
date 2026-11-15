# -*- coding: utf-8 -*-
"""山门渲染
blender -b 保国寺山门.blend -P render_gate.py -- [quick|final] [view...]
"""
import bpy, sys, os

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
mode = argv[0] if argv else "quick"
only = argv[1:]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, "renders_gate")
os.makedirs(OUTDIR, exist_ok=True)

sc = bpy.context.scene
sc.render.engine = 'CYCLES'
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for backend in ('OPTIX', 'CUDA'):
        try:
            prefs.compute_device_type = backend
            prefs.get_devices()
            if any(d.type != 'CPU' for d in prefs.devices):
                for d in prefs.devices:
                    d.use = (d.type != 'CPU')
                sc.cycles.device = 'GPU'
                break
        except Exception:
            pass
except Exception:
    pass

if mode == "quick":
    sc.cycles.samples = 40
    sc.render.resolution_x = 1280
    sc.render.resolution_y = 616
else:
    sc.cycles.samples = 300
    sc.render.resolution_x = 2160
    sc.render.resolution_y = 1040
sc.cycles.use_denoising = True
sc.render.image_settings.file_format = 'PNG'

views = {
    "front": "相机_正立面",
    "corner": "相机_三分之四",
    "detail": "相机_细部",
}
for key, cam in views.items():
    if only and key not in only:
        continue
    sc.camera = bpy.data.objects[cam]
    sc.render.filepath = os.path.join(OUTDIR, f"{key}_{mode}.png")
    bpy.ops.render.render(write_still=True)
    print("[渲染]", sc.render.filepath)
