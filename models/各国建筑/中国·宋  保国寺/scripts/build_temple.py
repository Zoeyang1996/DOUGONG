# -*- coding: utf-8 -*-
"""保国寺大殿 · 场景组装
blender -b -P build_temple.py
"""
import bpy, sys, os, math, random
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from temple_core import *          # noqa
import temple_core as TC
import temple_arch as TA

random.seed(7)
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BLEND = os.path.join(OUT, "保国寺大殿.blend")


# ---------------------------------------------------------------------------
def materials():
    M = {}
    M["stone"] = mat_surface("MAT_石材_阶条", "#7d796a", "#585449", scale=3.0,
                             rough=0.84, bump=0.35, bump_scale=40,
                             grime=(0.1, 2.6, 0.62))
    M["stone_dark"] = mat_surface("MAT_石材_台基", "#6b675c", "#4a473f", scale=2.2,
                                  rough=0.88, bump=0.4, bump_scale=32)
    M["paving"] = mat_paving()
    M["wood_red"] = mat_wood("MAT_朱红木", "#6b3125", "#43201a", axis='Z',
                             scale=2.0, rough=0.62, bump=0.16)
    M["wood_red_dark"] = mat_wood("MAT_深红木", "#4e2519", "#321811", axis='Z',
                                  scale=2.6, rough=0.6, bump=0.14)
    M["wood_dark"] = mat_wood("MAT_深褐木", "#4c3427", "#31231b", axis='Z',
                              scale=3.0, rough=0.6, bump=0.12)
    M["wood_lattice"] = mat_wood("MAT_窗棂", "#5c3527", "#3b2018", axis='Z',
                                 scale=6.0, rough=0.55, bump=0.1)
    M["tile"] = mat_tile("MAT_青瓦")
    M["tile_dark"] = mat_surface("MAT_脊瓦", "#31342d", "#1d1f19", scale=8,
                                 rough=0.72, bump=0.25, bump_scale=55)
    M["tile_light"] = mat_surface("MAT_瓦当", "#5e6159", "#40433d", scale=12,
                                  rough=0.5, bump=0.2, bump_scale=70)
    M["plaque"] = mat_wood("MAT_匾底", "#241c17", "#140f0c", axis='X',
                           scale=3.0, rough=0.42, bump=0.05)
    M["gold"] = mat_gold()
    M["dark"] = mat_simple("MAT_暗部", "#15100c", rough=0.9)
    M["win_shadow"] = mat_simple("MAT_窗内暗底", "#2a201a", rough=0.85)
    M["plaster"] = mat_surface("MAT_白灰墙", "#d9d5c8", "#bcb8ab", scale=2.2,
                               rough=0.86, bump=0.22, bump_scale=30,
                               grime=(0.6, 4.5, 0.66))
    M["ground"] = mat_surface("MAT_庭院地", "#8d8a7e", "#757267", scale=1.6,
                              rough=0.9, bump=0.3, bump_scale=24)
    M["leaf"] = mat_surface("MAT_树叶", "#26401f", "#162610", scale=8.0,
                            rough=0.88, bump=0.6, bump_scale=30)
    M["trunk"] = mat_wood("MAT_树干", "#4a3b2c", "#2e2419", axis='Z', scale=4,
                          rough=0.8, bump=0.3)
    return M


# ---------------------------------------------------------------------------
def build_environment(coll, M):
    # 庭院地面
    a = MeshAccum()
    a.box2(-60, 60, -60, 60, -0.30, 0.0)
    a.finish("庭院地面", M["ground"], coll)

    # 前庭石板路（略高一层）
    a = MeshAccum()
    a.box2(-14, 14, -30, -11.4, -0.02, 0.06)
    a.finish("前庭石板", M["paving"], coll)

    # 两侧白墙廊庑
    for sx in (-1, 1):
        x = sx * 15.0
        a = MeshAccum()
        a.box2(x - 0.30, x + 0.30, -26, 10.0, 0.0, 3.9)
        a.finish(f"白墙_{'左右'[sx > 0]}", M["plaster"], coll, bevel=0.01)
        # 瓦顶（两坡）
        a = MeshAccum()
        for s in (-1, 1):
            a.box((x + s * 0.52, -8.0, 4.20), (1.10, 36.0, 0.11),
                  M=Matrix.Rotation(s * math.radians(22), 4, 'Y'))
        a.finish(f"白墙瓦顶_{'左右'[sx > 0]}", M["tile"], coll)
        # 小脊
        a = MeshAccum()
        a.box2(x - 0.16, x + 0.16, -26, 10.0, 4.34, 4.52)
        a.finish(f"白墙脊_{'左右'[sx > 0]}", M["tile_dark"], coll, bevel=0.01)
        # 拱门（暗部）
        a = MeshAccum()
        a.cyl((x - sx * 0.28, -7.0, 2.0), 1.05, 0.10, seg=18,
              M=Matrix.Rotation(math.pi / 2, 4, 'Y'))
        a.box2(x - sx * 0.33, x - sx * 0.23, -8.05, -5.95, 0.0, 2.0)
        a.finish(f"拱门_{'左右'[sx > 0]}", M["dark"], coll)

    # 树木
    def tree(x, y, h=9.0, r=3.2, seed=0):
        rnd = random.Random(seed)
        a = MeshAccum()
        a.cyl((x, y, h * 0.34), 0.34, h * 0.68, seg=10, rtop=0.20)
        a.finish(f"树干_{seed}", M["trunk"], coll)
        a = MeshAccum()
        for k in range(22):
            ang = rnd.uniform(0, 6.283)
            rad = r * rnd.uniform(0.15, 1.0)
            cx = x + math.cos(ang) * rad
            cy = y + math.sin(ang) * rad * 0.8
            cz = h * 0.60 + rnd.uniform(-0.25, 0.55) * h * 0.4 + (1 - rad / r) * 0.6
            rr = r * rnd.uniform(0.22, 0.42)
            a.cyl((cx, cy, cz), rr, rr * 1.05, seg=10, rtop=rr * 0.45)
        a.finish(f"树冠_{seed}", M["leaf"], coll, smooth=True)

    positions = [(-20, 20, 12, 4.2), (20, 19, 13, 4.6), (-26, 6, 11, 3.6),
                 (26, 7, 12, 4.0), (-24, -12, 9, 3.0), (24, -13, 9.5, 3.2),
                 (-27, 30, 15, 5.0), (25, 31, 15, 4.8), (-30, -2, 12, 3.8),
                 (30, 0, 12, 4.0)]
    for i, (x, y, h, r) in enumerate(positions):
        tree(x, y, h, r, i)

    # 山影（远山）
    a = MeshAccum()
    for i, (x, w, h) in enumerate([(-40, 60, 26), (0, 70, 30), (40, 60, 24)]):
        a.cyl((x, 95, h * 0.5), w * 0.5, h, seg=24, rtop=w * 0.10)
    a.finish("远山", mat_simple("MAT_远山", "#8a9c8e", rough=1.0), coll, smooth=True)

    # 石台座（庭院中轴）
    a = MeshAccum()
    a.box((0, -13.5, 0.55), (2.4, 2.4, 1.1))
    a.box((0, -13.5, 1.16), (2.9, 2.9, 0.12))
    a.finish("石台座", M["stone"], coll, bevel=0.02)


def setup_world_and_light(coll):
    sc = bpy.context.scene

    # 天空（渐变穹顶）
    world = bpy.data.worlds.new("天空")
    sc.world = world
    world.use_nodes = True
    nt = world.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputWorld')
    out.location = (600, 0)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    tc.location = (-600, 0)
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    sep.location = (-420, 0)
    nt.links.new(tc.outputs['Generated'], sep.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.location = (-240, 0)
    cr = ramp.color_ramp
    cr.elements[0].position = 0.42
    cr.elements[0].color = (*hx('#cfd6d4'), 1)
    cr.elements[1].position = 0.58
    cr.elements[1].color = (*hx('#8fb4d8'), 1)
    e = cr.elements.new(0.98)
    e.color = (*hx('#3f74b4'), 1)
    nt.links.new(sep.outputs['Z'], ramp.inputs['Fac'])
    bg = nt.nodes.new('ShaderNodeBackground')
    bg.inputs['Strength'].default_value = 1.05
    bg.location = (380, 0)
    nt.links.new(ramp.outputs['Color'], bg.inputs['Color'])
    nt.links.new(bg.outputs[0], out.inputs[0])

    # 主光（日光）
    sd = bpy.data.lights.new("日光", 'SUN')
    sd.energy = 4.0
    sd.angle = math.radians(1.6)
    sd.color = (1.0, 0.94, 0.86)
    ob = bpy.data.objects.new("日光", sd)
    coll.objects.link(ob)
    ob.rotation_euler = (math.radians(52), 0.0, math.radians(-38))

    # 上层檐下补光（模拟庭院反射）
    ad2 = bpy.data.lights.new("上层补光", 'AREA')
    ad2.energy = 1900
    ad2.size = 16
    ad2.shape = 'RECTANGLE'
    ad2.size_y = 5
    ad2.color = (1.0, 0.93, 0.85)
    ob2 = bpy.data.objects.new("上层补光", ad2)
    coll.objects.link(ob2)
    ob2.location = (0, -13.5, 11.6)
    d2 = Vector((0, -5.8, 11.6)) - Vector(ob2.location)
    ob2.rotation_euler = d2.to_track_quat('-Z', 'Y').to_euler()

    # 补光（天光反射）
    ad = bpy.data.lights.new("补光", 'AREA')
    ad.energy = 2200
    ad.size = 22
    ad.color = (0.92, 0.90, 0.86)
    ob = bpy.data.objects.new("补光", ad)
    coll.objects.link(ob)
    ob.location = (-4, -30, 17)
    d = Vector((0, 0, 9)) - Vector(ob.location)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def add_camera(name, loc, target, lens=50, coll=None, ortho=None):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    if ortho:
        cd.type = 'ORTHO'
        cd.ortho_scale = ortho
    ob = bpy.data.objects.new(name, cd)
    (coll or bpy.context.scene.collection).objects.link(ob)
    ob.location = loc
    d = Vector(target) - Vector(loc)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return ob


# ---------------------------------------------------------------------------
def main():
    TC.clean_scene()
    M = materials()

    root = bpy.context.scene.collection
    c1 = new_coll("01_台基")
    c2 = new_coll("02_柱梁")
    c3 = new_coll("03_斗拱")
    c4 = new_coll("04_墙体门窗")
    c5 = new_coll("05_屋面")
    c6 = new_coll("06_脊饰")
    c7 = new_coll("07_环境")
    c8 = new_coll("08_灯光相机")

    TA.build_platform(c1, M)
    TA.build_columns(c2, M)
    TA.build_dougong(c3, M)
    TA.build_walls(c4, M)
    TA.build_plaques(c4, M)
    TA.build_backdrop(c4, M)
    TA.build_low_roof(c5, M)
    TA.build_up_roof(c5, M)
    TA.build_ridges(c6, M)
    build_environment(c7, M)
    setup_world_and_light(c8)

    add_camera("相机_正立面", (0, -54, 3.4), (0, 0, 8.4), 50, c8)
    add_camera("相机_东南角", (26, -30, 10.5), (0, 0, 8.2), 50, c8)
    add_camera("相机_翼角特写", (16.5, -16.5, 8.6), (10.6, -6.6, 11.9), 85, c8)
    add_camera("相机_俯瞰", (16, -24, 34), (0, 0, 8.0), 45, c8)

    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 128
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    sc.render.resolution_x = 1920
    sc.render.resolution_y = 1080
    sc.render.film_transparent = False
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.camera = bpy.data.objects["相机_正立面"]

    # 统计
    n_obj = len([o for o in bpy.data.objects if o.type == 'MESH'])
    n_vert = sum(len(o.data.vertices) for o in bpy.data.objects if o.type == 'MESH')
    print(f"[统计] 对象 {n_obj} 个，顶点 {n_vert:,}")

    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    print("[完成] 保存:", BLEND)


if __name__ == "__main__":
    main()
