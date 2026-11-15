# -*- coding: utf-8 -*-
"""Quick preview render: blender -b file.blend --python render_prev.py -- cam samples pct"""
import bpy, sys, os, math

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
cam = argv[0] if len(argv) > 0 else "相机_主"
spp = int(argv[1]) if len(argv) > 1 else 32
pct = int(argv[2]) if len(argv) > 2 else 50
out = argv[3] if len(argv) > 3 else "preview.png"

sc = bpy.context.scene
sc.camera = bpy.data.objects[cam]
sc.cycles.samples = spp
sc.render.resolution_percentage = pct
sc.render.filepath = os.path.join(os.path.dirname(bpy.data.filepath), out)
bpy.ops.render.render(write_still=True)
print("RENDERED", sc.render.filepath)
