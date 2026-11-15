# -*- coding: utf-8 -*-
"""Diagnostic: visualise the cloud mask as the world colour."""
import bpy

w = bpy.context.scene.world
nt = w.node_tree
nodes = nt.nodes
bg = next(n for n in nodes if n.bl_idname == 'ShaderNodeBackground')
mix = next(n for n in nodes if n.bl_idname == 'ShaderNodeMix' and n.data_type == 'RGBA')
m1 = mix.inputs['Factor'].links[0].from_node
print("FACTOR SOURCE:", m1.bl_idname, m1.operation, "FROM", mix.inputs['Factor'].links[0].from_socket.name)
for s in m1.inputs:
    print("  in", s.name, s.enabled, [l.from_node.bl_idname for l in s.links])
# rewire m1 -> background colour
nt.links.new(m1.outputs[0], bg.inputs['Color'])
nt.links.new(m1.outputs[0], bg.inputs['Strength'])
sc = bpy.context.scene
sc.camera = bpy.data.objects['相机_主']
sc.cycles.samples = 24
sc.render.resolution_percentage = 40
sc.render.filepath = "D:/技能大赛/各国建筑/日本法隆寺/tsky.png"
bpy.ops.render.render(write_still=True)
