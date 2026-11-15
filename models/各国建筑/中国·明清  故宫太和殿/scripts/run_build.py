# -*- coding: utf-8 -*-
"""场景组装 + 灯光相机 + 渲染保存"""
import bpy
import sys
import os
import math
import importlib

HERE = r"D:\技能大赛\各国建筑\故宫太和殿\scripts"
sys.path.insert(0, HERE)
import lib_taihe
import build_taihe as BT
importlib.reload(lib_taihe)
importlib.reload(BT)
from lib_taihe import *

OUT_DIR = BT.OUT_DIR
ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
QUICK = "--quick" in ARGV
NORENDER = "--norender" in ARGV


def ground(coll, M):
    mb = MB()
    mb.box((0, 0, -0.12), (420, 420, 0.24), 0)
    o = mb.build("G01_广场地面", coll, [M['ground']])
    # 御道（中轴石板）
    mb2 = MB()
    mb2.box((0, -110, 0.02), (11.0, 200, 0.06), 0)
    mb2.build("G02_御道", coll, [M['stone']])
    # 两侧铺砖分格线
    mb3 = MB()
    for i in range(-14, 15):
        if abs(i) < 6:
            continue
        mb3.box((i * 6.0, -110, 0.01), (0.06, 200, 0.02), 0)
    for i in range(40):
        mb3.box((0, -20 - i * 6.0, 0.01), (420, 0.06, 0.02), 0)
    mb3.build("G03_铺砖缝", coll, [M['dark']])


def bronze_ding(coll, M, x, y, z, s=1.0):
    """铜鼎（三足双耳）"""
    mb = MB()
    mb.cyl((x, y, z + 0.18), (x, y, z + 1.05 * s), 0.52 * s, 20, 0, 0.60 * s)
    mb.cyl((x, y, z + 1.05 * s), (x, y, z + 1.12 * s), 0.60 * s, 20, 0, 0.58 * s)
    for a in (0.4, 2.5, 4.6):
        mb.cyl((x + 0.34 * s * math.cos(a), y + 0.34 * s * math.sin(a), z + 0.20),
               (x + 0.30 * s * math.cos(a), y + 0.30 * s * math.sin(a), z),
               0.09 * s, 8)
    for sgn in (-1, 1):
        mb.box((x + sgn * 0.55 * s, y, z + 1.32 * s), (0.10 * s, 0.10 * s, 0.42 * s))
    mb.box((x, y, z + 1.06 * s), (1.24 * s, 1.24 * s, 0.10 * s))
    o = mb.build("N_铜鼎", coll, [M['bronze']])
    for p in o.data.polygons:
        p.use_smooth = True


def lamps():
    # 太阳
    sd = bpy.data.lights.new("Sun_晨光", 'SUN')
    sd.energy = 3.2
    sd.angle = math.radians(2.0)
    sd.color = (1.0, 0.86, 0.70)
    so = bpy.data.objects.new("L01_Sun", sd)
    bpy.context.scene.collection.objects.link(so)
    # 晨光自左前方射入（与参考图一致）
    sun_from = Vector((-0.58, -0.58, 0.66)).normalized()
    so.rotation_euler = sun_from.to_track_quat('Z', 'Y').to_euler()

    # 天光（世界）：渐变晴空，相机可见蓝天、照明取较弱环境
    w = bpy.data.worlds.new("WORLD_晴空渐变")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputWorld')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    cr = ramp.color_ramp
    cr.elements[0].position = 0.00
    cr.elements[0].color = (0.68, 0.76, 0.86, 1)
    e = cr.elements.new(0.22)
    e.color = (0.34, 0.52, 0.80, 1)
    e2 = cr.elements.new(0.70)
    e2.color = (0.085, 0.20, 0.55, 1)
    bg = nt.nodes.new('ShaderNodeBackground')
    bg.inputs['Strength'].default_value = 1.0
    bg2 = nt.nodes.new('ShaderNodeBackground')
    bg2.inputs['Strength'].default_value = 0.30
    lp = nt.nodes.new('ShaderNodeLightPath')
    mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(tc.outputs['Generated'], sep.inputs['Vector'])
    nt.links.new(sep.outputs['Z'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bg.inputs['Color'])
    nt.links.new(ramp.outputs['Color'], bg2.inputs['Color'])
    nt.links.new(lp.outputs['Is Camera Ray'], mx.inputs['Fac'])
    nt.links.new(bg2.outputs['Background'], mx.inputs[1])
    nt.links.new(bg.outputs['Background'], mx.inputs[2])
    nt.links.new(mx.outputs['Shader'], out.inputs['Surface'])

    # 补光（模拟地面反射）
    ad = bpy.data.lights.new("Fill_地面反射", 'AREA')
    ad.energy = 9000
    ad.size = 90
    ad.color = (1.0, 0.92, 0.82)
    ao = bpy.data.objects.new("L02_Fill", ad)
    bpy.context.scene.collection.objects.link(ao)
    ao.location = (0, -55, 2)
    ao.rotation_euler = (math.radians(-75), 0, 0)


def camera(name, loc, target, lens=55, ortho=None):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    if ortho:
        cd.type = 'ORTHO'
        cd.ortho_scale = ortho
    co = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(co)
    co.location = loc
    d = Vector(target) - Vector(loc)
    co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return co


def render_setup(res=(1280, 720), samples=48, cycles=False):
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.view_settings.exposure = 0.12
    if cycles:
        sc.render.engine = 'CYCLES'
        sc.cycles.samples = samples
        sc.cycles.use_denoising = True
        sc.cycles.max_bounces = 6
        sc.cycles.device = 'CPU'
    else:
        sc.render.engine = 'BLENDER_EEVEE'
        sc.eevee.taa_render_samples = samples
        try:
            sc.eevee.use_raytracing = True
        except Exception:
            pass
        try:
            sc.eevee.use_shadows = True
        except Exception:
            pass


def main():
    sc = reset_scene()
    M = BT.build_materials()

    C = {}
    C['00'] = new_coll("00_场地")
    C['01'] = new_coll("01_三台台基")
    C['02'] = new_coll("02_柱网结构")
    C['03'] = new_coll("03_墙体门窗")
    C['04'] = new_coll("04_额枋斗拱")
    C['05'] = new_coll("05_下檐屋面")
    C['06'] = new_coll("06_上檐屋面")
    C['07'] = new_coll("07_屋脊吻兽")
    C['08'] = new_coll("08_陈设")
    C['09'] = new_coll("09_灯光相机")

    ground(C['00'], M)
    BT.build_terrace(M, C['01'])
    BT.build_columns(M, C['02'])
    BT.build_walls(M, C['03'])
    BT.build_facade(M, C['03'])
    BT.build_plaque(M, C['03'])
    BT.build_architrave(M, C['04'])
    BT.build_dougong(M, C['04'], 30.0, 16.65, 21.50, 0.95, 1.55, "DG01_下檐斗拱")
    BT.build_dougong(M, C["04"], 27.1, 14.25, 27.40, 0.95, 1.45, "DG02_上檐斗拱")
    BT.build_rafters(M, C['04'], 33.2, 19.85, BT.Z_EAVE1 - 0.55, 0.30, "R01_下檐椽头")
    BT.build_rafters(M, C['04'], 31.2, 18.35, BT.Z_EAVE2 - 0.55, 0.30, "R02_上檐椽头")
    BT.build_eave_beam(M, C['04'], 33.35, 20.0, BT.Z_EAVE1 - 0.06, "EB01_下檐檐枋")
    BT.build_eave_beam(M, C['04'], 31.35, 18.5, BT.Z_EAVE2 - 0.06, "EB02_上檐檐枋")

    BT.build_roofs(M, C['05'], C['06'])
    BT.build_ridges(M, C['07'])

    for i, x in enumerate((-24, -12, 12, 24)):
        bronze_ding(C['08'], M, x, -21.6, BT.Z_TT, 1.0)

    lamps()
    c1 = camera("CAM_01_主体", (-64, -130, 12.5), (1, -5, 18.5), 58)
    c2 = camera("CAM_02_檐口细部", (-24, -50, 12.0), (2, -11, 27.5), 85)
    c3 = camera("CAM_03_正面", (0, -150, 12), (0, -2, 18.0), 68)
    c4 = camera("CAM_04_屋顶俯视", (-78, -76, 76), (0, 0, 24.0), 60)
    sc.camera = c1

    print("=== 统计 ===")
    dg = bpy.context.evaluated_depsgraph_get()
    tris = 0
    for ob in bpy.data.objects:
        if ob.type == 'MESH':
            tris += len(ob.data.polygons)
    print("objects:", len(bpy.data.objects), "faces:", tris)

    blend = os.path.join(OUT_DIR, "故宫太和殿.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    print("saved", blend)

    if not NORENDER:
        render_setup((1280, 720), 32, cycles=False)
        sc.render.filepath = os.path.join(OUT_DIR, "renders", "preview_01.png")
        bpy.ops.render.render(write_still=True)
        print("rendered")


main()
