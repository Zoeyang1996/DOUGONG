# -*- coding: utf-8 -*-
import bpy

sc = bpy.context.scene
sc.render.resolution_x = 96
sc.render.resolution_y = 96
sc.cycles.samples = 16
sc.render.resolution_percentage = 100
cam = bpy.data.objects['相机_主']
sc.camera = cam
cam.rotation_euler = cam.rotation_euler  # unchanged

for vt, exposure in (('AgX', 0.10), ('Standard', -0.30), ('Filmic', 0.10)):
    sc.view_settings.view_transform = vt
    sc.view_settings.look = 'None'
    sc.view_settings.exposure = exposure
    sc.render.filepath = "D:/技能大赛/各国建筑/日本法隆寺/_probe.png"
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(sc.render.filepath, check_existing=False)
    px = list(im.pixels)
    def at(x, y):
        i = (y * im.size[0] + x) * 4
        return tuple(round(v, 3) for v in px[i:i + 3])
    print("PROBE", vt, exposure, "sky_top", at(48, 84), "sky_mid", at(10, 60))
    bpy.data.images.remove(im)
