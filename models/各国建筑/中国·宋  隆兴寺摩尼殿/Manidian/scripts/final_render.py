# -*- coding: utf-8 -*-
"""成品渲染：六个机位，输出到 renders/

机位按参考照片的阅读方式设定：
  01 正立面  —— 与照片同一透视，用于逐项比对
  02 三分之四 —— 看双檐关系、四抱厦、歇山转角
  03 侧立面  —— 看抱厦山花侧影与腰檐断面
  04 鸟瞰    —— 看点屋顶交接、天沟
  05 抱厦近景 —— 看山花/博缝/悬鱼/排山勾滴
  06 檐下铺作 —— 看斗拱带与拱眼壁
"""
import bpy, sys, os
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "renders"))
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.film_transparent = False
sc.eevee.taa_render_samples = 64
try:
    sc.eevee.use_raytracing = True
except Exception:
    pass
sc.view_settings.view_transform = 'AgX'
sc.view_settings.exposure = 0.60
try:
    sc.view_settings.look = 'AgX - Medium High Contrast'
except Exception:
    pass


def cam(loc, look, lens, name):
    d = bpy.data.cameras.new(name)
    d.lens = lens
    o = bpy.data.objects.new(name, d)
    sc.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return o


VIEWS = {
    "01_正立面":   ((0, 64, 3.4), (0, 0, 9.4), 36, 1600, 1000),
    "02_三分之四": ((40, 45, 13.5), (0, 0, 10.2), 33, 1600, 1000),
    "03_侧立面":   ((62, 6, 4.2), (0, 0, 9.6), 36, 1600, 1000),
    "04_鸟瞰":     ((46, 58, 64), (0, 0, 9.5), 44, 1600, 1000),
    "05_抱厦近景": ((-5.5, 40, 13.0), (0, 17.4, 11.6), 55, 1400, 950),
    "06_檐下铺作": ((21.5, 24.0, 9.4), (14.5, 12.8, 9.1), 55, 1400, 950),
}
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
keys = args if args else list(VIEWS)
for k in keys:
    loc, look, lens, rx, ry = VIEWS[k]
    sc.render.resolution_x, sc.render.resolution_y = rx, ry
    c = cam(loc, look, lens, "C_" + k)
    sc.camera = c
    sc.render.filepath = os.path.join(OUT, k + ".png")
    bpy.ops.render.render(write_still=True)
    print("OK", k)
