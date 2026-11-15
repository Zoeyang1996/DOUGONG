# -*- coding: utf-8 -*-
"""在 Blender 中构建南禅寺大殿并渲染多视角预览。"""
import bpy
import sys
import os
import math
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import nanchan_temple as nt

nt.build()

sc = bpy.context.scene


def setup_render(engine="EEVEE"):
    if engine == "CYCLES":
        sc.render.engine = 'CYCLES'
        sc.cycles.device = 'CPU'
        sc.cycles.samples = 48
        sc.cycles.use_denoising = True
        sc.cycles.max_bounces = 4
        sc.cycles.caustics_reflective = False
        sc.cycles.caustics_refractive = False
    else:
        for name in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
            try:
                sc.render.engine = name
                break
            except Exception:
                continue
        try:
            sc.eevee.taa_render_samples = 64
        except Exception:
            pass
    sc.render.resolution_x = 1500
    sc.render.resolution_y = 980
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = 'PNG'
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.exposure = float(os.environ.get("EXPO", "0.0"))
    print("USING", sc.view_settings.view_transform)


def place_cam(eye, tgt, lens=50):
    cam = bpy.data.objects.get("相机_Camera")
    if cam is None:
        cam_data = bpy.data.cameras.new("相机_Camera")
        cam = bpy.data.objects.new("相机_Camera", cam_data)
        sc.collection.objects.link(cam)
    cam.data.lens = lens
    cam.location = eye
    dx, dy, dz = tgt[0] - eye[0], tgt[1] - eye[1], tgt[2] - eye[2]
    horiz = math.hypot(dx, dy)
    cam.rotation_euler = (math.pi / 2 + math.atan2(dz, horiz), 0.0,
                          math.atan2(-dx, dy))
    sc.camera = cam


def shot(name, eye, tgt, lens=50):
    place_cam(eye, tgt, lens)
    sc.render.filepath = os.path.join(HERE, name)
    bpy.ops.render.render(write_still=True)
    print("RENDERED:", name)


setup_render(os.environ.get("ENG", "EEVEE"))

shot("render_3q.png", (18.5, -27.0, 9.6), (0.0, 0.0, 4.9), 52)
shot("render_front.png", (0.0, -46.0, 8.0), (0.0, 0.0, 5.2), 55)
shot("render_corner.png", (13.0, -18.0, 3.4), (0.0, 0.0, 5.4), 36)
shot("render_detail.png", (7.4, -14.5, 7.2), (1.5, -4.2, 5.4), 90)
print("ALL DONE")
