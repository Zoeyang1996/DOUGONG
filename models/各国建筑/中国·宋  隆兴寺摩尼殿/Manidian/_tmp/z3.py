import bpy, os
from mathutils import Vector
sc = bpy.context.scene
out = os.path.join(os.path.dirname(bpy.data.filepath), "renders", "check")
sc.render.engine = 'BLENDER_EEVEE'
sc.eevee.taa_render_samples = 32
sc.render.resolution_x, sc.render.resolution_y = 1000, 720
sc.view_settings.view_transform = 'AgX'
sc.view_settings.exposure = 0.75
def shot(name, loc, look, lens):
    cd = bpy.data.cameras.new(name); cd.lens = lens
    c = bpy.data.objects.new(name, cd); sc.collection.objects.link(c)
    c.location = loc
    c.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = c
    sc.render.filepath = os.path.join(out, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("CHK", name)
shot("w_sh", (-8.5, 26, 12.5), (-7.0, 16.5, 11.5), 48)
