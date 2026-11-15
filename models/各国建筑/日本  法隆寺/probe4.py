# -*- coding: utf-8 -*-
"""Probe the rendered value of the tile materials on a sphere."""
import bpy
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.ops.wm.append(directory="D:/技能大赛/各国建筑/日本法隆寺/法隆寺五重塔_v3.blend/Material/",
                  filename="tile")
bpy.ops.wm.append(directory="D:/技能大赛/各国建筑/日本法隆寺/法隆寺五重塔_v3.blend/Material/",
                  filename="tile_dark")
for i, mn in enumerate(("tile", "tile_dark")):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(i * 3 - 1.5, 0, 1))
    ob = bpy.context.object
    ob.data.materials.append(bpy.data.materials[mn])
    bpy.ops.object.shade_smooth()

# neutral lighting
sd = bpy.data.lights.new("s", 'SUN')
sd.energy = 3.3
ob = bpy.data.objects.new("s", sd)
sc.collection.objects.link(ob)
ob.rotation_euler = (Vector((0.3, -0.5, 0.8)).to_track_quat('Z', 'Y').to_euler())
w = bpy.data.worlds.new("w")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.5, 0.5, 0.5, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.5
sc.world = w

cam_d = bpy.data.cameras.new("c")
cam = bpy.data.objects.new("c", cam_d)
sc.collection.objects.link(cam)
cam.location = (0, -8, 1.2)
cam.rotation_euler = (Vector((0, 0, 1)) - Vector(cam.location)).to_track_quat('-Z', 'Y').to_euler()
sc.camera = cam
sc.render.resolution_x = sc.render.resolution_y = 200
sc.cycles.samples = 32
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
sc.render.filepath = "D:/技能大赛/各国建筑/日本法隆寺/_sph.png"
bpy.ops.render.render(write_still=True)
im = bpy.data.images.load(sc.render.filepath, check_existing=False)
px = list(im.pixels)
for x, label in ((60, "tile"), (140, "tile_dark")):
    i = (100 * 200 + x) * 4
    print("SPHERE", label, [round(v, 3) for v in px[i:i + 3]])
