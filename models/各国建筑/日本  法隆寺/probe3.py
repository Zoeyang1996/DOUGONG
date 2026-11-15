# -*- coding: utf-8 -*-
"""Sample the cloud-mask value across the sky."""
import bpy

sc = bpy.context.scene
sc.render.resolution_x = 120
sc.render.resolution_y = 120
sc.cycles.samples = 8
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
sc.view_settings.exposure = 0.0
sc.render.image_settings.file_format = 'OPEN_EXR'
sc.camera = bpy.data.objects['相机_主']

nt = bpy.context.scene.world.node_tree
bg = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeBackground')
mixc = [n for n in nt.nodes if n.bl_idname == 'ShaderNodeMix' and n.data_type == 'RGBA']
print("MIXCOUNT", len(mixc))
mask_node = mixc[0].inputs[0].links[0].from_node if mixc[0].inputs[0].links else None
print("MASK", mask_node.bl_idname if mask_node else None)

nt.links.new(mask_node.outputs[0], bg.inputs['Color'])
bg.inputs['Strength'].default_value = 1.0
sc.render.filepath = "D:/技能大赛/各国建筑/日本法隆寺/_probe.exr"
bpy.ops.render.render(write_still=True)
im = bpy.data.images.load(sc.render.filepath, check_existing=False)
px = list(im.pixels)
vals = sorted(px[i] for i in range(0, len(px), 4))
n = len(vals)
print("MASKSTATS min %.3f p25 %.3f p50 %.3f p75 %.3f max %.3f" % (
    vals[0], vals[n // 4], vals[n // 2], vals[3 * n // 4], vals[-1]))
