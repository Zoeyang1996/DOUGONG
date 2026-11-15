# -*- coding: utf-8 -*-
"""Final renders:  blender -b 法隆寺五重塔_v3.blend --python render_final.py"""
import bpy, os

OUT = os.path.dirname(bpy.data.filepath)
sc = bpy.context.scene
sc.cycles.samples = 256
sc.cycles.use_denoising = True
sc.render.resolution_percentage = 100
jobs = [
    ("相机_主",   (1300, 1950), "01_正面"),
    ("相机_斜",   (1300, 1950), "02_斜视"),
    ("相机_仰",   (1300, 1950), "03_仰视"),
    ("相机_細部", (1300, 1950), "04_细部"),
    ("相机_相輪", (1100, 1650), "05_相輪"),
]
for cam, res, name in jobs:
    sc.camera = bpy.data.objects[cam]
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = os.path.join(OUT, "out_%s.png" % name)
    bpy.ops.render.render(write_still=True)
    print("DONE", name)
