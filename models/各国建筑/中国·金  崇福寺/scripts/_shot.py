# -*- coding: utf-8 -*-
"""通用快照：blender -b file.blend -P _shot.py -- camX camY camZ tgX tgY tgZ lens W H samples out.png"""
import bpy, sys, os
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
loc = Vector([float(argv[i]) for i in range(3)])
tgt = Vector([float(argv[i]) for i in range(3, 6)])
lens = float(argv[6])
W, H = int(argv[7]), int(argv[8])
spp = int(argv[9])
out = argv[10]

scene = bpy.context.scene
cd = bpy.data.cameras.new("shot")
cd.lens = lens
cam = bpy.data.objects.new("shot", cd)
scene.collection.objects.link(cam)
cam.location = loc
cam.rotation_euler = (tgt - loc).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
scene.render.resolution_x = W
scene.render.resolution_y = H
scene.render.resolution_percentage = 100
scene.cycles.samples = spp
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print("Saved:", out)
