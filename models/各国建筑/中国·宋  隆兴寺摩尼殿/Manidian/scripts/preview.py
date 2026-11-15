# -*- coding: utf-8 -*-
"""快速检视渲染（低采样，用于迭代排查）"""
import bpy, os, sys, math
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def look_at(cam, look):
    d = Vector(look) - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


VIEWS = [
    ("p1_front", (0, 116, 8.5), (0, 0, 11.4), 85),
    ("p2_corner", (58, 76, 11), (0, 0, 10.4), 62),
    ("p3_porch", (6, 40, 7), (0, 17, 10.2), 50),
    ("p4_aerial", (40, 52, 74), (0, 0, 5), 50),
]


def main():
    sc = bpy.context.scene
    sc.render.resolution_x = 900
    sc.render.resolution_y = 580
    sc.eevee.taa_render_samples = 32
    out = os.path.join(HERE, "..", "renders", "preview")
    os.makedirs(out, exist_ok=True)
    for name, loc, lk, lens in VIEWS:
        cd = bpy.data.cameras.new(name)
        cd.lens = lens
        cam = bpy.data.objects.new(name, cd)
        sc.collection.objects.link(cam)
        cam.location = loc
        look_at(cam, lk)
        sc.camera = cam
        sc.render.filepath = os.path.join(out, name + ".png")
        bpy.ops.render.render(write_still=True)
        print("PREV_OK", name)


if __name__ == "__main__":
    main()
