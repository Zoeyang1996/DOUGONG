import bpy, os
from mathutils import Vector
sc = bpy.context.scene
out = os.path.join(os.path.dirname(bpy.data.filepath), "renders", "check")
sc.render.engine = 'BLENDER_EEVEE'
sc.eevee.taa_render_samples = 28
sc.render.resolution_x, sc.render.resolution_y = 1120, 700
sc.view_settings.view_transform = 'AgX'
sc.view_settings.exposure = 0.62
def shot(name, loc, look, lens):
    cd = bpy.data.cameras.new(name); cd.lens = lens
    c = bpy.data.objects.new(name, cd); sc.collection.objects.link(c)
    c.location = loc
    c.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = c
    sc.render.filepath = os.path.join(out, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("CHK", name)
shot("v_q", (40, 47, 14), (0, 0, 10.0), 33)
shot("v_f", (0, 60, 3.2), (0, 0, 9.4), 32)
