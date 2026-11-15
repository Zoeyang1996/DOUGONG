import bpy
objs = [o for o in bpy.data.objects if o.type == 'MESH']
v = sum(len(o.data.vertices) for o in objs)
f = sum(len(o.data.polygons) for o in objs)
print("STAT mesh=%d verts=%d faces=%d mats=%d lights=%d colls=%d"
      % (len(objs), v, f, len(bpy.data.materials),
         len([o for o in bpy.data.objects if o.type == 'LIGHT']),
         len(bpy.data.collections)))
import os
p = bpy.data.filepath
print("STAT file=%.1fMB" % (os.path.getsize(p) / 1048576.0))
