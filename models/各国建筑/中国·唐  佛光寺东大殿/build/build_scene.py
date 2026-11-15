"""场景装配 + 渲染"""
import bpy, sys, os, math
from mathutils import Vector, Euler, Matrix

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "build"))
import blib, mats, hall
import importlib
importlib.reload(blib); importlib.reload(mats); importlib.reload(hall)

R = math.radians


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)


def setup_world():
    w = bpy.data.worlds.new("W")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = 1.15
    # 天空渐变：天顶偏蓝，地平线偏暖白
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    mp = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    el = ramp.color_ramp.elements
    el[0].position = 0.30
    el[0].color = (0.62, 0.60, 0.56, 1)
    el[1].position = 0.62
    el[1].color = (0.52, 0.62, 0.76, 1)
    e2 = el.new(0.42)
    e2.color = (0.78, 0.80, 0.84, 1)
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])


def backdrop():
    """环形天幕：摄影棚式渐变背景，各角度均可用"""
    import bmesh
    me = bpy.data.meshes.new("Backdrop")
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=64, radius1=105, radius2=105, depth=70)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("Backdrop", me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = (0, 0, 33)
    m = bpy.data.materials.new("M_backdrop")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            nt.nodes.remove(n)
    out = nt.nodes.get("Material Output")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 0.82
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -35
    mr.inputs["From Max"].default_value = 35
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    el = ramp.color_ramp.elements
    el[0].position = 0.40
    el[0].color = (0.60, 0.58, 0.55, 1)
    el[1].position = 0.53
    el[1].color = (0.74, 0.75, 0.75, 1)
    e2 = el.new(0.72)
    e2.color = (0.50, 0.60, 0.74, 1)
    nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    me.materials.append(m)
    ob.visible_shadow = False
    return ob


def setup_lights():
    sun = bpy.data.lights.new("Sun", 'SUN')
    sun.energy = 5.0
    sun.angle = R(4.5)
    sun.color = (1.0, 0.965, 0.925)
    ob = bpy.data.objects.new("Sun", sun)
    bpy.context.scene.collection.objects.link(ob)
    ob.rotation_euler = Euler((R(52), 0, R(-38)), 'XYZ')

    fill = bpy.data.lights.new("Fill", 'AREA')
    fill.energy = 520
    fill.size = 30
    fill.color = (0.78, 0.85, 1.0)
    ob2 = bpy.data.objects.new("Fill", fill)
    bpy.context.scene.collection.objects.link(ob2)
    ob2.location = (28, -30, 18)
    d = Vector((0, 0, 8)) - ob2.location
    ob2.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

    bounce = bpy.data.lights.new("Bounce", 'AREA')
    bounce.energy = 420
    bounce.size = 40
    bounce.color = (1.0, 0.95, 0.88)
    ob3 = bpy.data.objects.new("Bounce", bounce)
    bpy.context.scene.collection.objects.link(ob3)
    ob3.location = (-25, -40, 4)
    d = Vector((0, 0, 5)) - ob3.location
    ob3.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def make_cam(name, loc, target, lens=35, ortho=None, shift_z=0.0):
    cam = bpy.data.cameras.new(name)
    cam.lens = lens
    cam.sensor_width = 36
    if ortho:
        cam.type = 'ORTHO'
        cam.ortho_scale = ortho
    ob = bpy.data.objects.new(name, cam)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    d = Vector(target) - Vector(loc)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return ob


def setup_render(res=(1600, 900), samples=64):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = 'PNG'
    ee = sc.eevee
    for attr, val in [("taa_render_samples", samples), ("use_gtao", True),
                      ("use_raytracing", True), ("use_shadows", True),
                      ("use_bloom", False), ("shadow_ray_count", 2)]:
        try:
            setattr(ee, attr, val)
        except Exception:
            pass
    sc.view_settings.view_transform = 'AgX'
    try:
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass
    sc.view_settings.exposure = 0.15
    # 色彩管理：稍微提饱和
    sc.view_settings.use_curve_mapping = False


def build_scene():
    clear()
    setup_world()
    backdrop()
    setup_lights()
    coll = bpy.data.collections.new("FoguangEastHall")
    bpy.context.scene.collection.children.link(coll)
    M = mats.build_all()
    B = hall.build(coll, M)
    objs = B.build(coll, M, name_prefix="")

    # 语义化命名 + 分组
    NAME = {
        "tile": ("屋面_筒瓦", "屋顶"),
        "tile_gap": ("屋面_底瓦", "屋顶"),
        "tile_ridge": ("屋面_脊饰", "屋顶"),
        "wood_dark": ("斗栱椽望_深木", "木构"),
        "wood_red": ("柱额门窗_土朱", "木构"),
        "wood_door": ("板门", "木构"),
        "plaque": ("匾额", "木构"),
        "plaster": ("走马板_白灰", "墙体"),
        "wall_red": ("檐墙_土朱", "墙体"),
        "stone": ("石作_台基栏杆", "石作"),
        "stone_dark": ("石作_踏道柱础", "石作"),
        "pave": ("月台铺石", "石作"),
        "ground": ("地面铺砖", "场地"),
        "iron": ("门饰_铁", "门饰"),
        "stud": ("门钉_铜", "门饰"),
        "gold": ("匾文_贴金", "门饰"),
        "bronze": ("铜活", "门饰"),
    }
    subs = {}
    for ob in list(objs):
        key = ob.name
        if key in NAME:
            cn, grp = NAME[key]
            ob.name = cn
            ob.data.name = cn
            if grp not in subs:
                c = bpy.data.collections.new(grp)
                coll.children.link(c)
                subs[grp] = c
            coll.objects.unlink(ob)
            subs[grp].objects.link(ob)
    # 平滑
    bpy.context.view_layer.update()
    for ob in objs:
        if len(ob.data.polygons) < 200000:
            try:
                bpy.ops.object.select_all(action='DESELECT')
                ob.select_set(True)
                bpy.context.view_layer.objects.active = ob
                bpy.ops.object.shade_auto_smooth(angle=math.radians(24))
            except Exception as e:
                print("smooth fail", ob.name, e)
    return coll, objs


def add_cameras():
    cams = {}
    cams["front"] = make_cam("CAM_Front", (0, -95, 6.6), (0, -95, 6.6), lens=80, ortho=44)
    cams["front"].location = (0, -95, 6.6)
    cams["front"].rotation_euler = Euler((R(90), 0, 0))
    cams["three"] = make_cam("CAM_Three", (-42, -54, 7.0), (-1.0, 1.0, 7.4), lens=46)
    cams["corner"] = make_cam("CAM_Corner", (-21.5, -19.0, 3.0), (-13.0, -7.5, 8.9), lens=24)
    cams["detail"] = make_cam("CAM_Detail", (-8.6, -16.0, 4.0), (-5.6, -8.4, 7.2), lens=42)
    cams["side"] = make_cam("CAM_Side", (48, -24, 11), (2, 0, 6.5), lens=52)
    return cams


def render(cams, which, res, samples, outdir):
    setup_render(res, samples)
    sc = bpy.context.scene
    paths = []
    for k in which:
        sc.camera = cams[k]
        sc.render.filepath = os.path.join(outdir, f"{k}.png")
        bpy.ops.render.render(write_still=True)
        paths.append(sc.render.filepath)
        print("RENDERED", sc.render.filepath)
    return paths


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    views = "front,three,corner".split(",")
    res = (1200, 700)
    samples = 32
    save = True
    for a in argv:
        if a.startswith("views="):
            views = a.split("=")[1].split(",")
        elif a.startswith("res="):
            w, h = a.split("=")[1].split("x")
            res = (int(w), int(h))
        elif a.startswith("samples="):
            samples = int(a.split("=")[1])
        elif a == "nosave":
            save = False
    coll, objs = build_scene()
    nv = sum(len(o.data.vertices) for o in objs)
    nf = sum(len(o.data.polygons) for o in objs)
    print(f"STATS objects={len(objs)} verts={nv} faces={nf}")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "佛光寺东大殿.blend"))
    cams = add_cameras()
    render(cams, views, res, samples, os.path.join(ROOT, "render"))
    if save:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "佛光寺东大殿.blend"))
