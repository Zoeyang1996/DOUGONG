# -*- coding: utf-8 -*-
"""Quick preview renderer: blender -b file.blend -P quick_render.py -- CAM RES% SAMPLES OUT"""
import bpy, sys, os

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
cam_name = argv[0] if len(argv) > 0 else "CAM_Hero_ThreeQuarter"
pct = int(argv[1]) if len(argv) > 1 else 40
samples = int(argv[2]) if len(argv) > 2 else 48
out = argv[3] if len(argv) > 3 else "D:/技能大赛/各国建筑/乌尔内斯木板教堂/renders/quick.png"

sc = bpy.context.scene
cam = bpy.data.objects.get(cam_name)
if cam:
    sc.camera = cam
sc.render.resolution_percentage = pct
sc.cycles.samples = samples
sc.render.filepath = out

prefs = bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    for d in prefs.devices:
        d.use = True
    sc.cycles.device = 'GPU'
except Exception as e:
    print("GPU setup failed", e)
    sc.cycles.device = 'CPU'

bpy.ops.render.render(write_still=True)
print("RENDERED", out)
