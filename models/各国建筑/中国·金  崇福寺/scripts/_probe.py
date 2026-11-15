# -*- coding: utf-8 -*-
"""通用射线探测：blender -b file.blend -P _probe.py -- camX camY camZ tgX tgY tgZ lens W H px1 py1 px2 py2 ..."""
import bpy, math, sys
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
cam_loc = Vector([float(argv[0]), float(argv[1]), float(argv[2])])
tgt = Vector([float(argv[3]), float(argv[4]), float(argv[5])])
lens = float(argv[6])
W, H = int(argv[7]), int(argv[8])
pts = [(float(argv[i]), float(argv[i + 1])) for i in range(9, len(argv), 2)]

scene = bpy.context.scene
cam_data = bpy.data.cameras.new("probe_cam")
cam_data.lens = lens
cam_data.sensor_width = 36.0
cam = bpy.data.objects.new("probe_cam", cam_data)
scene.collection.objects.link(cam)
cam.location = cam_loc
d = (tgt - cam_loc).normalized()
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
bpy.context.view_layer.update()

dg = bpy.context.evaluated_depsgraph_get()
# 相机局部坐标 -> 世界
M = cam.matrix_world
half_w = cam_data.sensor_width / 2.0
half_h = half_w * H / W
for (px, py) in pts:
    # NDC: x 向右, y 向上
    nx = (px / W) * 2.0 - 1.0
    ny = 1.0 - (py / H) * 2.0
    dx = nx * half_w / lens
    dy = ny * half_h / lens
    local = Vector((dx, dy, -1.0)).normalized()
    wd = (M.to_3x3() @ local).normalized()
    hit, loc, nor, idx, obj, mat_slot = scene.ray_cast(dg, cam_loc, wd)
    if hit:
        me = obj.data
        mname = "-"
        try:
            if obj.material_slots:
                mname = obj.material_slots[mat_slot].material.name if mat_slot < len(obj.material_slots) else obj.material_slots[0].material.name
        except Exception as e:
            mname = "?" + str(e)
        print("P(%4d,%4d) HIT obj=%-24s mat=%-14s loc=(%.2f,%.2f,%.2f) n=(%.2f,%.2f,%.2f)" %
              (px, py, obj.name, mname, loc.x, loc.y, loc.z, nor.x, nor.y, nor.z))
    else:
        print("P(%4d,%4d) MISS" % (px, py))
