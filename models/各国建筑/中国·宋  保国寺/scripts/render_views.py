# -*- coding: utf-8 -*-
"""渲染视图
blender -b 保国寺大殿.blend -P render_views.py -- [quick|final] [视图名...]
"""
import bpy, sys, os, math

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
mode = argv[0] if argv else "quick"
only = argv[1:]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, "renders")
os.makedirs(OUTDIR, exist_ok=True)

sc = bpy.context.scene
sc.render.engine = 'CYCLES'

# GPU
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
                print(f"[GPU] {backend}")
                break
        except Exception as e:
            print("[GPU跳过]", backend, e)
except Exception as e:
    print("[GPU不可用]", e)

if mode == "quick":
    sc.cycles.samples = 40
    sc.render.resolution_x = 1100
    sc.render.resolution_y = 620
    sc.cycles.use_denoising = True
else:
    sc.cycles.samples = 300
    sc.render.resolution_x = 2560
    sc.render.resolution_y = 1440
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 8

sc.render.image_settings.file_format = 'PNG'
sc.cycles.use_adaptive_sampling = True

views = {
    "front": "相机_正立面",
    "corner": "相机_东南角",
    "detail": "相机_翼角特写",
    "top": "相机_俯瞰",
}

for key, cam in views.items():
    if only and key not in only:
        continue
    if cam not in bpy.data.objects:
        print("缺少相机", cam)
        continue
    sc.camera = bpy.data.objects[cam]
    sc.render.filepath = os.path.join(OUTDIR, f"{key}_{mode}.png")
    bpy.ops.render.render(write_still=True)
    print("[渲染]", sc.render.filepath)
