# -*- coding: utf-8 -*-
"""Measure the distribution of the cloud noise across the visible sky."""
import bpy

sc = bpy.context.scene
sc.render.resolution_x = 120
sc.render.resolution_y = 120
sc.cycles.samples = 8
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
sc.view_settings.exposure = 0.0
sc.render.image_settings.file_format = 'OPEN_EXR'
sc.render.image_settings.color_depth = '32'
sc.camera = bpy.data.objects['相机_主']

nt = bpy.context.scene.world.node_tree
bg = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeBackground')
noises = [n for n in nt.nodes if n.bl_idname == 'ShaderNodeTexNoise']
for idx, nz in enumerate(noises):
    nt.links.new(nz.outputs['Fac'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = 1.0
    sc.render.filepath = "D:/技能大赛/各国建筑/日本法隆寺/_probe.exr"
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(sc.render.filepath, check_existing=False)
    px = list(im.pixels)
    vals = [px[i] for i in range(0, len(px), 4)]
    vals.sort()
    n = len(vals)
    print("NOISE", idx, "scale", round(nz.inputs['Scale'].default_value, 2),
          "min %.3f p10 %.3f p50 %.3f p90 %.3f max %.3f" % (
              vals[0], vals[int(n * .1)], vals[n // 2], vals[int(n * .9)], vals[-1]))
    bpy.data.images.remove(im)
