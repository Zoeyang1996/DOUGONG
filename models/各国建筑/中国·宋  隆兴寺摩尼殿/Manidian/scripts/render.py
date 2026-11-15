# -*- coding: utf-8 -*-
import bpy, sys, os, math
from mathutils import Vector, Euler
HERE = os.path.dirname(os.path.abspath(__file__))
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = 1500
sc.render.resolution_y = 950
sc.eevee.taa_render_samples = 64
sc.view_settings.view_transform = 'AgX'
sc.view_settings.exposure = 0.55
try:
    sc.view_settings.look = 'AgX - Medium High Contrast'
except Exception:
    pass

def cam(loc, look, lens, name):
    d = bpy.data.cameras.new(name); d.lens = lens
    o = bpy.data.objects.new(name, d); sc.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector(look)-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    return o

args = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
views = {
 "v1_front":   ((0, 112, 8.0), (0, 0, 11.0), 85),
 "v2_three":   ((56, 74, 11.0), (0, 0, 10.5), 62),
 "v3_aerial":  ((34, 46, 62), (0, 0, 6.0), 52),
 "v0_top":     ((0, 8, 95), (0, 0, 8.0), 40),
 "v4_detail":  ((0, 34, 6.0), (0, 17, 10.0), 55),
}
name = args[0] if args else "v1_front"
loc, look, lens = views[name]
c = cam(loc, look, lens, "C_"+name)
sc.camera = c
sc.render.filepath = os.path.join(HERE, "..", "renders", name + ".png")
bpy.ops.render.render(write_still=True)
print("RENDER_OK", name)
