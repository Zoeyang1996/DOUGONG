import bpy, os, math
from mathutils import Vector
sc = bpy.context.scene
out = os.path.join(os.path.dirname(bpy.data.filepath), "renders", "check")
os.makedirs(out, exist_ok=True)
sc.render.engine = 'BLENDER_EEVEE'
sc.eevee.taa_render_samples = 24
sc.render.resolution_x, sc.render.resolution_y = 1100, 720
sc.view_settings.view_transform = 'AgX'
sc.view_settings.exposure = 0.55
sc.view_settings.look = 'AgX - Medium High Contrast'

def shot(name, loc, look, lens=55):
    cd = bpy.data.cameras.new(name); cd.lens = lens
    c = bpy.data.objects.new(name, cd); sc.collection.objects.link(c)
    c.location = loc
    c.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = c
    sc.render.filepath = os.path.join(out, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("CHK", name)

shot("f1_front", (0, 104, 7.5), (0, 0, 11.0), 80)
shot("f2_three", (58, 74, 12), (0, 0, 10.5), 62)
shot("f3_aerial", (38, 46, 62), (0, 0, 6.0), 52)
shot("f4_porch", (8, 40, 9.0), (0, 16, 10.0), 50)
shot("f5_top", (0.1, 0.1, 90), (0, 0, 0), 50)
