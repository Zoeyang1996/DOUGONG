# -*- coding: utf-8 -*-
"""保国寺山门场景组装
blender -b -P build_gate.py
"""
import bpy, sys, os, math, random
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from temple_core import *          # noqa
import temple_core as TC
import gate_arch as GA

random.seed(11)
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BLEND = os.path.join(OUT, "保国寺山门.blend")


def setup_world_and_light(coll):
    sc = bpy.context.scene
    # 世界：淡环境光（天空由天穹球提供）
    world = bpy.data.worlds.new("环境")
    sc.world = world
    world.use_nodes = True
    nt = world.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    bg.inputs['Color'].default_value = (0.34, 0.40, 0.48, 1)
    bg.inputs['Strength'].default_value = 0.55
    nt.links.new(bg.outputs[0], out.inputs[0])

    # 天穹球：渐变天空，兼作环境光
    bpy.ops.mesh.primitive_uv_sphere_add(radius=260, segments=48, ring_count=24,
                                         location=(0, 0, 0))
    dome = bpy.context.active_object
    dome.name = "天穹"
    me = dome.data
    for p_ in me.polygons:
        p_.flip()
    m = bpy.data.materials.new("MAT_天穹")
    m.use_nodes = True
    mnt = m.node_tree
    for n in list(mnt.nodes):
        mnt.nodes.remove(n)
    mo = mnt.nodes.new('ShaderNodeOutputMaterial')
    em = mnt.nodes.new('ShaderNodeEmission')
    em.inputs['Strength'].default_value = 1.0
    tc = mnt.nodes.new('ShaderNodeTexCoord')
    sep = mnt.nodes.new('ShaderNodeSeparateXYZ')
    mnt.links.new(tc.outputs['Generated'], sep.inputs['Vector'])
    mr = mnt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = 0.50
    mr.inputs['From Max'].default_value = 0.72
    mnt.links.new(sep.outputs['Z'], mr.inputs['Value'])
    ramp = mnt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (*hx('#c6d6dd'), 1)
    ramp.color_ramp.elements[1].position = 0.40
    ramp.color_ramp.elements[1].color = (*hx('#5d92c8'), 1)
    e2 = ramp.color_ramp.elements.new(0.98)
    e2.color = (*hx('#1f5aa6'), 1)
    mnt.links.new(mr.outputs['Result'], ramp.inputs['Fac'])
    mnt.links.new(ramp.outputs['Color'], em.inputs['Color'])
    mnt.links.new(em.outputs[0], mo.inputs['Surface'])
    me.materials.append(m)
    dome.visible_shadow = False


    sd = bpy.data.lights.new("日光", 'SUN')
    sd.energy = 4.2
    sd.angle = math.radians(1.8)
    sd.color = (1.0, 0.95, 0.88)
    ob = bpy.data.objects.new("日光", sd)
    coll.objects.link(ob)
    ob.rotation_euler = (math.radians(48), 0.0, math.radians(-32))

    ad = bpy.data.lights.new("补光", 'AREA')
    ad.energy = 1800
    ad.size = 20
    ad.shape = 'RECTANGLE'
    ad.size_y = 8
    ad.color = (0.95, 0.95, 0.95)
    ob = bpy.data.objects.new("补光", ad)
    coll.objects.link(ob)
    ob.location = (-5, -17, 9)
    d = Vector((0, 0, 4.5)) - Vector(ob.location)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

    # 檐下补光
    ad3 = bpy.data.lights.new("檐下补光", 'AREA')
    ad3.energy = 1500
    ad3.size = 14
    ad3.shape = 'RECTANGLE'
    ad3.size_y = 3
    ad3.color = (1.0, 0.95, 0.88)
    ob3 = bpy.data.objects.new("檐下补光", ad3)
    coll.objects.link(ob3)
    ob3.location = (0, -7.5, 2.4)
    d3 = Vector((0, -3.2, 6.1)) - Vector(ob3.location)
    ob3.rotation_euler = d3.to_track_quat('-Z', 'Y').to_euler()

    # 门洞内透景补光
    ad2 = bpy.data.lights.new("门内光", 'AREA')
    ad2.energy = 3200
    ad2.size = 6.0
    ob2 = bpy.data.objects.new("门内光", ad2)
    coll.objects.link(ob2)
    ob2.location = (0.0, 9.5, 4.0)
    d2 = Vector((0, 5.0, 2.0)) - Vector(ob2.location)
    ob2.rotation_euler = d2.to_track_quat('-Z', 'Y').to_euler()


def add_camera(name, loc, target, lens=50, coll=None):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    ob = bpy.data.objects.new(name, cd)
    (coll or bpy.context.scene.collection).objects.link(ob)
    ob.location = loc
    d = Vector(target) - Vector(loc)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return ob


def main():
    TC.clean_scene()
    M = GA.materials()

    c1 = new_coll("01_台基")
    c2 = new_coll("02_柱梁")
    c3 = new_coll("03_斗拱")
    c4 = new_coll("04_正立面")
    c5 = new_coll("05_屋面")
    c6 = new_coll("06_脊饰")
    c7 = new_coll("07_白墙拱门")
    c8 = new_coll("08_环境")
    c9 = new_coll("09_灯光相机")

    GA.build_platform(c1, M)
    GA.build_frame(c2, M)
    GA.build_dougong(c3, M)
    GA.build_facade(c4, M)
    GA.build_plaques(c4, M)
    GA.build_roof(c5, M)
    GA.build_ridges(c6, M)
    GA.build_side_walls(c7, M)
    GA.build_env(c8, M)
    setup_world_and_light(c9)

    add_camera("相机_正立面", (0, -31.5, 1.65), (0, 0, 4.90), 40, c9)
    add_camera("相机_三分之四", (15.0, -16.0, 4.6), (0, 0, 4.0), 35, c9)
    add_camera("相机_细部", (5.0, -9.0, 3.2), (1.8, -3.2, 4.6), 60, c9)

    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 160
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    sc.render.resolution_x = 2160
    sc.render.resolution_y = 1040
    sc.view_settings.view_transform = 'AgX'
    try:
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass
    sc.camera = bpy.data.objects["相机_正立面"]

    n_obj = len([o for o in bpy.data.objects if o.type == 'MESH'])
    n_vert = sum(len(o.data.vertices) for o in bpy.data.objects if o.type == 'MESH')
    print(f"[统计] 对象 {n_obj} 个，顶点 {n_vert:,}")

    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    print("[完成] 保存:", BLEND)


if __name__ == "__main__":
    main()
