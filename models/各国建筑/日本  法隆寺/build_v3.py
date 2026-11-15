# -*- coding: utf-8 -*-
"""
法隆寺五重塔 (Horyu-ji five-storey pagoda) — procedural rebuild v3
    blender -b --python build_v3.py -- [--preview]

Reference: 法隆寺 五重塔, Nara.  Unpainted weathered timber, white lime
plaster walls, dark grey hongawara tile roofs, bronze sorin.
"""
import bpy
import math
import os
import sys
import random
from mathutils import Vector, Matrix

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from pagoda_lib import MB, mx, PI, RAD          # noqa: E402
import mat_v3 as MAT                            # noqa: E402

OUT = os.path.dirname(os.path.abspath(__file__))
PREVIEW = "--preview" in sys.argv

# --------------------------------------------------------------------------- #
#  Proportions (metres)
# --------------------------------------------------------------------------- #
PLAT_H = 1.10
PLAT_HALF = 8.30

B = [6.25, 5.65, 5.05, 4.45, 3.90]        # wall plane, half width
W = [10.44, 9.30, 8.35, 7.35, 6.45]       # eave tip,  half width
H_WALL = [2.66, 1.92, 1.82, 1.70, 1.58]   # storey wall height
BR_H = [1.16, 0.96, 0.91, 0.86, 0.81]     # bracket (kumimono) height
SLOPE = 0.470
LIFT = 0.64                             # corner up-turn
ROT_SKY = 118.0     # yaw of the HDRI sky
ROOF_T = 0.42

F, E, T = [], [], []
_lv = PLAT_H
for i in range(5):
    F.append(_lv)
    _brtop = _lv + H_WALL[i] + BR_H[i]
    _e = _brtop - 0.085 * (W[i] - B[i])
    _t = _e + (W[i] - B[i]) * SLOPE
    E.append(_e)
    T.append(_t)
    _lv = _t

COLL = {}


def coll(name):
    if name not in COLL:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
        COLL[name] = c
    return COLL[name]


def bake(mb, name, coll_name, angle=30.0):
    me = bpy.data.meshes.new(name)
    me.from_pydata(mb.v, [], mb.f)
    me.validate(verbose=False)
    if any(u is not None for u in mb.uv):
        uvl = me.uv_layers.new(name="UVMap")
        k = 0
        for fi, face in enumerate(mb.f):
            u = mb.uv[fi]
            for j in range(len(face)):
                uvl.data[k + j].uv = u[j] if (u is not None and j < len(u)) else (0.0, 0.0)
            k += len(face)
    for m in mb.mats:
        me.materials.append(bpy.data.materials[m])
    for i, p in enumerate(me.polygons):
        p.material_index = min(mb.mi[i], len(mb.mats) - 1)
        p.use_smooth = True
    me.update()
    ob = bpy.data.objects.new(name, me)
    coll(coll_name).objects.link(ob)
    if angle is not None:
        md = ob.modifiers.new("EdgeSplit", 'EDGE_SPLIT')
        md.split_angle = RAD(angle)
        md.use_edge_angle = True
        md.use_edge_sharp = True
    return ob


def roof_z(x, y, i):
    """Top surface height of the roof of storey i at plan (x, y)."""
    wi, win = W[i], B[i] - 0.25
    r = max(abs(x), abs(y))
    if r <= win:
        return T[i]
    t = min(1.0, (r - win) / (wi - win))
    # concave Japanese profile: steep at the ridge, nearly flat at the eave tip
    z = T[i] - (T[i] - E[i]) * (t ** 0.72)
    if r > 1e-6:
        c = (min(abs(x), abs(y)) / r) ** 4.2
        z += LIFT * (t ** 2.4) * c
    return z


def lin(a, b, n):
    n = max(2, n)
    return [a + (b - a) * i / (n - 1) for i in range(n)]


CLOUD_PROF = [(-0.50, -0.50), (0.50, -0.50), (0.50, -0.10), (0.42, 0.26),
              (0.22, 0.47), (0.00, 0.52), (-0.22, 0.47), (-0.42, 0.26),
              (-0.50, -0.10)]


# --------------------------------------------------------------------------- #
#  基壇  platform
# --------------------------------------------------------------------------- #
def build_platform():
    mb = MB(["stone"])
    h = PLAT_H
    mb.box(mx(), 2 * PLAT_HALF, 2 * PLAT_HALF, h - 0.22, "stone", 0, 0, (h - 0.22) / 2)
    mb.box(mx(), 2 * PLAT_HALF + 0.34, 2 * PLAT_HALF + 0.34, 0.13, "stone_step",
           0, 0, h - 0.065)
    mb.box(mx(), 2 * PLAT_HALF + 0.54, 2 * PLAT_HALF + 0.54, 0.11, "stone_step",
           0, 0, 0.055)
    # stone facing courses (creates the joint rhythm)
    for k in range(3):
        zz = 0.24 + k * 0.30
        mb.box(mx(), 2 * PLAT_HALF + 0.14, 2 * PLAT_HALF + 0.14, 0.26, "stone",
               0, 0, zz)
    # steps, four sides
    for s in range(4):
        M = mx(rz=s * PI / 2)
        n = 5
        dep = 0.36
        for k in range(n):
            zz = (h - 0.14) * (k + 1) / n
            yy = PLAT_HALF + 0.22 + (n - k - 0.5) * dep
            mb.box(M, 4.90, dep + 0.03, zz, "stone_step", 0, yy, zz / 2)
        for sx in (-1, 1):
            mb.box(M, 0.30, n * dep + 0.24, h * 0.96, "stone_step",
                   sx * 2.62, PLAT_HALF + 0.22 + (n * dep) / 2, h * 0.48)
            mb.box(M, 0.42, 0.34, 0.30, "stone_step", sx * 2.62,
                   PLAT_HALF + 0.22 + n * dep + 0.10, h * 0.15)
    bake(mb, "基壇", "01_基壇")


def build_ground():
    me = bpy.data.meshes.new("地面_砂利")
    s = 480.0
    me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [],
                   [(0, 1, 2, 3)])
    me.materials.append(bpy.data.materials["gravel"])
    ob = bpy.data.objects.new("地面_砂利", me)
    coll("05_環境").objects.link(ob)
    # stone apron
    mb = MB(["stone_step"])
    a = PLAT_HALF + 4.2
    mb.box(mx(), 2 * a, 2 * a, 0.09, "stone", 0, 0, -0.005)
    for k in range(9):                       # paving joint lines
        x = -a + 2 * a * k / 8
        mb.box(mx(), 0.035, 2 * a, 0.014, "stone_step", x, 0, 0.044)
        mb.box(mx(), 2 * a, 0.035, 0.014, "stone_step", 0, x, 0.044)
    bake(mb, "石畳", "01_基壇")


# --------------------------------------------------------------------------- #
#  高欄  railing
# --------------------------------------------------------------------------- #
def railing(mb, hw, z0, h=0.92, wood="wood_light", style=1):
    """Square railing of half width hw; style 1 = 卍崩し pattern."""
    n = max(4, int(round(2 * hw / 1.15)))
    xs = lin(-hw, hw, n + 1)
    for s in range(4):
        M = mx(rz=s * PI / 2)
        for x in xs:
            corner = abs(abs(x) - hw) < 1e-4
            ph = h * (1.16 if corner else 1.0)
            mb.box(M, 0.11, 0.11, ph, wood, x, hw, z0 + ph / 2)
            if corner:
                mb.sphere(M, 0.085, "gold", 10, 6, cz=z0 + ph + 0.05)
        # top rail + bottom rail
        mb.box(M, 2 * hw + 0.13, 0.15, 0.10, wood, 0, hw, z0 + h + 0.03)
        mb.box(M, 2 * hw + 0.13, 0.13, 0.08, wood, 0, hw, z0 + h * 0.52)
        mb.box(M, 2 * hw + 0.13, 0.12, 0.07, wood, 0, hw, z0 + 0.05)
        # vertical balusters
        bn = int(2 * hw / 0.30)
        for k in range(1, bn):
            x = -hw + 2 * hw * k / bn
            if min(abs(x - v) for v in xs) < 0.075:
                continue
            mb.box(M, 0.040, 0.040, h * 0.56, wood, x, hw, z0 + h * 0.30 + h * 0.28)
        # 卍崩し: short diagonals in the upper field
        if style:
            bn2 = int(2 * hw / 0.62)
            for k in range(bn2):
                x = -hw + 0.31 + 2 * hw * k / bn2
                if abs(x) > hw - 0.12:
                    continue
                for sgn in (-1, 1):
                    Md = M @ Matrix.Translation((x, hw, z0 + h * 0.76))
                    Md = Md @ Matrix.Rotation(sgn * RAD(30), 4, 'Y')
                    mb.box(Md, 0.26, 0.028, 0.032, wood, 0, 0, 0)


# --------------------------------------------------------------------------- #
#  縁 / 廻縁  veranda and balconies
# --------------------------------------------------------------------------- #
def build_veranda():
    mb = MB(["wood_light"])
    b = B[0]
    hw = b + 1.55
    z = F[0]
    for s in range(4):
        M = mx(rz=s * PI / 2)
        mb.box(M, 2 * hw, 1.72, 0.17, "wood_light", 0, hw - 0.86, z - 0.085)
        mb.box(M, 2 * hw + 0.05, 0.12, 0.22, "wood_beam", 0, hw, z - 0.18)
        n = int(2 * hw / 0.33)
        for k in range(1, n):
            x = -hw + 2 * hw * k / n
            mb.box(M, 0.013, 1.66, 0.010, "wood_dark", x, hw - 0.85, z + 0.002)
        # joists under the deck
        for k in range(0, n, 3):
            x = -hw + 2 * hw * k / n
            mb.box(M, 0.10, 1.66, 0.16, "wood_beam", x, hw - 0.86, z - 0.22)
        # stone plinths
        for x in (-b, -0.33 * b, 0.33 * b, b):
            mb.cyl(M, 0.28, 0.12, "stone_step", 14, x, b - 0.04, z - 0.20)
    railing(mb, hw - 0.10, z, 0.96, "vermilion", 1)
    bake(mb, "初重縁", "02_塔身")


def build_balcony(i):
    mb = MB(["wood_light"])
    b = B[i]
    hw = b + 0.55
    z = F[i]
    for s in range(4):
        M = mx(rz=s * PI / 2)
        mb.box(M, 2 * hw, 0.66, 0.12, "wood_light", 0, hw - 0.33, z - 0.06)
        mb.box(M, 2 * hw + 0.02, 0.09, 0.14, "wood_beam", 0, hw, z - 0.13)
        # cantilever arms under the deck
        n = max(3, int(2 * hw / 0.75))
        for k in range(n + 1):
            x = -hw + 2 * hw * k / n
            mb.box(M, 0.13, 0.62, 0.20, "wood_beam", x, hw - 0.34, z - 0.20)
    railing(mb, hw - 0.07, z, 0.80, "vermilion", 1)
    bake(mb, "廻縁_%d" % i, "02_塔身")


# --------------------------------------------------------------------------- #
#  塔身  storey body
# --------------------------------------------------------------------------- #
def body_side(mb, M, i, b, z0, hw):
    top = z0 + hw
    first = (i == 0)
    # plaster infill wall
    mb.box(M, 2 * b - 0.06, 0.16, hw - 0.10, "plaster", 0, b - 0.14,
           z0 + hw / 2 - 0.02)
    # 地覆 sill and 頭貫 head tie
    mb.box(M, 2 * b + 0.10, 0.38, 0.20, "vermilion", 0, b - 0.02, z0 + 0.10)
    mb.box(M, 2 * b + 0.10, 0.40, 0.28, "vermilion", 0, b - 0.02, top - 0.15)
    # 内法長押 / 腰長押
    mb.box(M, 2 * b, 0.10, 0.11, "vermilion", 0, b + 0.04, top - 0.55)
    if not first:
        mb.box(M, 2 * b, 0.09, 0.09, "vermilion", 0, b + 0.03, z0 + 0.13)
    # columns
    for x in (-b, -b / 3, b / 3, b):
        mb.cyl(M, 0.215, hw, "vermilion", 16, x, b - 0.02, z0)
        mb.cyl(M, 0.255, 0.09, "vermilion_b", 16, x, b - 0.02, z0)
        mb.cyl(M, 0.245, 0.08, "vermilion_b", 16, x, b - 0.02, top - 0.08)
    bays = [(-b, -b / 3), (-b / 3, b / 3), (b / 3, b)]
    for bi, (x0, x1) in enumerate(bays):
        wdt = x1 - x0 - 0.46
        cx = (x0 + x1) / 2
        if first:
            if bi == 1:                       # 板扉 double doors
                zb, zt = z0 + 0.20, z0 + 2.06
                for dx in (-wdt / 4 - 0.01, wdt / 4 + 0.01):
                    mb.box(M, wdt / 2 - 0.02, 0.11, zt - zb, "wood_light",
                           cx + dx, b + 0.03, (zb + zt) / 2)
                    # plank joints
                    for k in range(5):
                        xx = cx + dx - wdt / 4 + 0.06 + (wdt / 2 - 0.12) * k / 4
                        mb.box(M, 0.012, 0.02, zt - zb - 0.05, "wood_dark",
                               xx, b + 0.095, (zb + zt) / 2)
                    # 八双金具 (metal straps + ring)
                    for k in range(3):
                        zz = zb + 0.30 + k * 0.62
                        mb.box(M, 0.06, 0.03, 0.34, "bronze",
                               cx + dx, b + 0.10, zz)
                    mb.torus(M @ Matrix.Translation((cx + dx, b + 0.12,
                                                     zb + 0.92)),
                             0.075, 0.014, "gold", 16, 6)
                mb.box(M, wdt + 0.30, 0.13, 0.20, "vermilion", cx, b + 0.03,
                       zt + 0.10)
                mb.box(M, wdt + 0.30, 0.11, 0.14, "vermilion", cx, b + 0.03,
                       zb - 0.07)
            else:                             # 連子窓 slat window
                zb, zt = z0 + 0.98, z0 + 1.94
                mb.box(M, wdt + 0.10, 0.16, 0.13, "vermilion", cx, b + 0.02, zt)
                mb.box(M, wdt + 0.10, 0.16, 0.13, "vermilion", cx, b + 0.02, zb)
                nb = int(wdt / 0.125)
                for k in range(nb):
                    xx = cx - wdt / 2 + wdt * (k + 0.5) / nb
                    mb.box(M, 0.055, 0.10, zt - zb, "vermilion_b", xx, b + 0.05,
                           (zb + zt) / 2)
        else:
            if bi == 1:                       # central plank door
                zb, zt = z0 + 0.10, z0 + hw * 0.44
                mb.box(M, wdt * 0.48, 0.10, zt - zb, "wood_light", cx, b + 0.03,
                       (zb + zt) / 2)
                for k in range(4):
                    xx = cx - wdt * 0.21 + wdt * 0.42 * k / 3
                    mb.box(M, 0.012, 0.02, zt - zb - 0.04, "wood_dark", xx,
                           b + 0.085, (zb + zt) / 2)
                mb.box(M, wdt * 0.48 + 0.14, 0.12, 0.10, "vermilion", cx,
                       b + 0.03, zt)
            else:                             # 連子窓 high in the plaster wall
                zb, zt = z0 + hw * 0.50, z0 + hw * 0.78
                mb.box(M, wdt * 0.72 + 0.06, 0.14, 0.10, "vermilion", cx, b + 0.02, zt)
                mb.box(M, wdt * 0.72 + 0.06, 0.14, 0.10, "vermilion", cx, b + 0.02, zb)
                nb = int(wdt * 0.72 / 0.135)
                for k in range(nb):
                    xx = cx - wdt * 0.36 + wdt * 0.72 * (k + 0.5) / nb
                    mb.box(M, 0.05, 0.09, zt - zb, "vermilion_b", xx, b + 0.04,
                           (zb + zt) / 2)


def build_body(i):
    b, z0, hw = B[i], F[i], H_WALL[i]
    mb = MB(["plaster"])
    for s in range(4):
        M = mx(rz=s * PI / 2)
        body_side(mb, M, i, b, z0, hw)
        # 小壁 : band between bracket top and the roof soffit
        x0, x1 = -b - 1.28, b + 1.28
        zt_l = roof_z(x0, b + 1.28, i) - ROOF_T - 0.02
        zt_r = roof_z(x1, b + 1.28, i) - ROOF_T - 0.02
        mb.poly([M @ Vector((x0, b + 1.28, E[i])),
                 M @ Vector((x0, b + 1.28, zt_l)),
                 M @ Vector((x1, b + 1.28, zt_r)),
                 M @ Vector((x1, b + 1.28, E[i]))], "plaster")
        # soffit from wall out to the bracket edge
        mb.poly([M @ Vector((x0, b - 0.24, E[i] + 0.02)),
                 M @ Vector((x0, b + 1.28, E[i] + 0.02)),
                 M @ Vector((x1, b + 1.28, E[i] + 0.02)),
                 M @ Vector((x1, b - 0.24, E[i] + 0.02))], "soffit_wood")
    bake(mb, "塔身_%d重" % (i + 1), "02_塔身")


# --------------------------------------------------------------------------- #
#  組物  bracket sets
# --------------------------------------------------------------------------- #
def bracket_set(mb, M, s, brh):
    """Local: origin on the column head, +Y points outward."""
    def f(v):
        return v * brh / 1.20
    # 大斗
    mb.box(M, 0.64 * s, 0.64 * s, f(0.22), "vermilion", 0, 0.05 * s, f(0.11))
    # tier 1 : 雲肘木 crossing arms
    mb.swept([(0, 0.02 * s, f(0.28)), (0, 0.30 * s, f(0.28)),
              (0, 0.62 * s, f(0.28))], 0.26 * s, f(0.20), "vermilion",
             side_axis=(1, 0, 0))
    for dx in (-0.86 * s, 0.0, 0.86 * s):
        mb.box(M, 0.34 * s, 0.30 * s, f(0.17), "vermilion", dx, 0.28 * s, f(0.46))
    # tier 2
    mb.swept([(-1.02 * s, 0.10 * s, f(0.60)), (0, 0.10 * s, f(0.60)),
              (1.02 * s, 0.10 * s, f(0.60))], 0.24 * s, f(0.17), "vermilion",
             side_axis=(0, 1, 0))
    mb.swept([(0, 0.04 * s, f(0.60)), (0, 0.60 * s, f(0.60)),
              (0, 1.18 * s, f(0.60))], 0.24 * s, f(0.17), "vermilion",
             side_axis=(1, 0, 0))
    for dx, dy in ((-0.78 * s, 0.10 * s), (0.78 * s, 0.10 * s),
                   (0.0, 0.86 * s), (0.0, 0.0)):
        mb.box(M, 0.30 * s, 0.30 * s, f(0.15), "vermilion", dx, dy, f(0.76))
    # tier 3 : outer arm carrying the purlin
    mb.swept([(-0.92 * s, 0.62 * s, f(0.90)), (0, 0.62 * s, f(0.90)),
              (0.92 * s, 0.62 * s, f(0.90))], 0.22 * s, f(0.16), "vermilion",
             side_axis=(0, 1, 0))
    # 尾垂木 : tail rafter running outward
    mb.swept([(0, 0.10 * s, f(0.34)), (0, 0.78 * s, f(0.62)),
              (0, 1.52 * s, f(0.92))], 0.22 * s, 0.26 * s, "vermilion",
             side_axis=(1, 0, 0))


def build_brackets(i):
    b, z0, hw = B[i], F[i], H_WALL[i]
    mb = MB(["vermilion"])
    s = (b / 6.25) ** 0.85
    xs = [-b, -b / 3, b / 3, b]
    mids = [-b * 2 / 3, 0.0, b * 2 / 3]
    for side in range(4):
        M = mx(rz=side * PI / 2)
        for x in xs + mids:
            Ms = M @ Matrix.Translation((x, b - 0.02, z0 + hw))
            bracket_set(mb, Ms, s, BR_H[i])
        # continuous 通肘木 bands
        for zz, w in ((0.28, 0.26), (0.60, 0.24)):
            mb.box(M, 2 * b + 0.60, w, 0.18, "vermilion", 0, b + 0.22,
                   z0 + hw + BR_H[i] * zz / 1.20)
    bake(mb, "組物_%d重" % (i + 1), "02_塔身")


# --------------------------------------------------------------------------- #
#  屋根  roof
# --------------------------------------------------------------------------- #
def build_roof(i):
    N = 62
    wi, win = W[i], B[i] - 0.25
    verts, faces, uvs = [], [], []
    for a in range(N + 1):
        x = -wi + 2 * wi * a / N
        for c in range(N + 1):
            y = -wi + 2 * wi * c / N
            verts.append((x, y, roof_z(x, y, i)))
    for a in range(N):
        for c in range(N):
            i0 = a * (N + 1) + c
            faces.append((i0, i0 + N + 1, i0 + N + 2, i0 + 1))
            uvl = []
            for (va, vc) in ((a, c), (a, c + 1), (a + 1, c + 1), (a + 1, c)):
                xx = -wi + 2 * wi * va / N
                yy = -wi + 2 * wi * vc / N
                uvl.append((xx if abs(yy) >= abs(xx) else yy,
                            max(abs(xx), abs(yy)) - win))
            uvs.append(tuple(uvl))
    me = bpy.data.meshes.new("屋根_%d" % (i + 1))
    me.from_pydata(verts, [], faces)
    uvl = me.uv_layers.new(name="UVMap")
    k = 0
    for f in range(len(faces)):
        for j in range(4):
            uvl.data[k + j].uv = uvs[f][j]
        k += 4
    me.materials.append(bpy.data.materials["tile"])
    me.materials.append(bpy.data.materials["soffit_wood"])
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    me.update()
    ob = bpy.data.objects.new("屋根_%d" % (i + 1), me)
    coll("03_屋根").objects.link(ob)
    sol = ob.modifiers.new("thick", 'SOLIDIFY')
    sol.thickness = ROOF_T
    sol.offset = -1.0
    sol.use_rim = True
    sol.material_offset = 1          # underside -> white plaster soffit
    sol.material_offset_rim = 0      # eave edge stays tile-dark

    mb = MB(["tile_dark"])
    for s in range(4):
        M = mx(rz=s * PI / 2)
        # ---- 丸瓦 ridges running down the slope
        pitch = 0.315
        ncol = int(2 * (wi - 0.26) / pitch)
        for k2 in range(ncol + 1):
            u = -(wi - 0.26) + 2 * (wi - 0.26) * k2 / ncol
            pts = []
            for y in lin(win + 0.02, wi - 0.01, 9):
                pts.append((M @ Vector((u, y, roof_z(u, y, i) + 0.062)))[:])
            mb.swept(pts, 0.135, 0.075, "tile_dark", side_axis=(1, 0, 0),
                     profile=[(-0.5, -0.55), (0.5, -0.55), (0.5, -0.12),
                              (0.34, 0.28), (0.0, 0.5), (-0.34, 0.28),
                              (-0.5, -0.12)])
        # ---- 軒丸瓦 : round tile mouths at the eave
        cnt = int(2 * (wi - 0.30) / pitch)
        for k2 in range(cnt + 1):
            x = -(wi - 0.30) + 2 * (wi - 0.30) * k2 / cnt
            z = roof_z(x, wi, i)
            Me = M @ Matrix.Translation((x, wi - 0.05, z - 0.125))
            Me = Me @ Matrix.Rotation(RAD(-90), 4, 'X')
            mb.cyl(Me, 0.076, 0.085, "tile_edge", 12, 0, 0, 0)
        # ---- 茅負 fascia following the curved eave
        pts = []
        for x in lin(-wi + 0.02, wi - 0.02, 26):
            pts.append((M @ Vector((x, wi - 0.02,
                                    roof_z(x, wi, i) - 0.47)))[:])
        mb.swept(pts, 0.11, 0.26, "vermilion_b", side_axis=(0, 1, 0))
        # ---- hip ridge 隅棟
        pts = []
        for rr in lin(win + 0.15, wi * 0.965, 14):
            pts.append((M @ Vector((rr, rr, roof_z(rr, rr, i) + 0.085)))[:])
        mb.swept(pts, 0.42, 0.26, "tile_dark", side_axis=(-1, 1, 0),
                 profile=CLOUD_PROF)
        mb.swept([(p[0], p[1], p[2] + 0.15) for p in pts], 0.26, 0.13,
                 "tile_dark", side_axis=(-1, 1, 0), profile=CLOUD_PROF)
        # 鬼瓦 at the hip end
        M2 = M @ Matrix.Translation((wi * 0.935, wi * 0.935,
                                     roof_z(wi, wi, i) - 0.02))
        M2 = M2 @ Matrix.Rotation(-PI / 4, 4, 'Z')
        mb.box(M2, 0.46, 0.20, 0.30, "tile_dark", 0, 0, 0.06)
        mb.box(M2, 0.34, 0.17, 0.16, "tile_dark", 0, 0.02, 0.24)
        # 風鐸 wind bell
        p = M @ Vector((wi * 0.93, wi * 0.93, 0))
        cz = roof_z(wi, wi, i) - 0.10
        mb.cyl(Matrix.Translation((p.x, p.y, cz)), 0.014, -0.42, "gold", 6, 0, 0, 0)
        mb.cyl(Matrix.Translation((p.x, p.y, cz - 0.52)), 0.085, -0.20, "bronze",
               10, 0, 0, 0, r2=0.045)
        mb.sphere(Matrix.Translation((p.x, p.y, cz - 0.60)), 0.055, "bronze", 10, 6)
        # ---- 垂木 rafters (two tiers), under the eave
        nr = int(2 * (wi - 0.36) / 0.435)
        for k2 in range(nr + 1):
            u = -(wi - 0.36) + 2 * (wi - 0.36) * k2 / nr
            y0 = b_out = B[i] + 0.95
            pts = []
            for y in lin(b_out - 0.55, wi - 0.16, 7):
                pts.append((M @ Vector((u, y, roof_z(u, y, i) - ROOF_T - 0.15)))[:])
            mb.swept(pts, 0.125, 0.20, "vermilion_b", side_axis=(1, 0, 0))
            pts = []
            for y in lin(B[i] + 0.06, B[i] + 1.05, 4):
                pts.append((M @ Vector((u, y, E[i] - 0.24)))[:])
            mb.swept(pts, 0.115, 0.15, "vermilion_b", side_axis=(1, 0, 0))
        # 丸桁 purlin below the rafters
        pz = roof_z(B[i] + 0.98, B[i] + 1.02, i) - ROOF_T - 0.30
        mb.box(M, 2 * B[i] + 2.34, 0.30, 0.30, "vermilion_b", 0, B[i] + 1.02, pz)
    bake(mb, "屋根詳細_%d" % (i + 1), "03_屋根", 34.0)
    return ob


# --------------------------------------------------------------------------- #
#  相輪  sorin
# --------------------------------------------------------------------------- #

def annulus(mb, M, r_in, r_out, h, mat, seg=40):
    """Flat washer (ring plate) - used for the nine rings of the sorin."""
    base = len(mb.v)
    for zz in (0.0, h):
        for rr in (r_in, r_out):
            for k in range(seg):
                a = 2 * PI * k / seg
                q = M @ Vector((rr * math.cos(a), rr * math.sin(a), zz))
                mb.v.append((q.x, q.y, q.z))
    # vertex block order: bottom-in, bottom-out, top-in, top-out
    bi, bo, ti, to = base, base + seg, base + 2 * seg, base + 3 * seg
    for k in range(seg):
        k2 = (k + 1) % seg
        for quad in ((bo + k, bo + k2, to + k2, to + k),          # outer wall
                     (bi + k2, bi + k, ti + k, ti + k2),          # inner wall
                     (ti + k, ti + k2, to + k2, to + k),          # top face
                     (bi + k2, bi + k, bo + k, bo + k2)):         # bottom face
            mb.f.append(quad)
            mb.mi.append(mb._m(mat))
            mb.uv.append(None)


def build_sorin():
    """相輪 : 露盤・伏鉢・請花・擦管・九輪・水煙・竜車・宝珠"""
    mb = MB(["bronze"])
    z = T[4]
    # ---- 露盤 : stepped square plinth
    mb.box(mx(), 3.34, 3.34, 0.16, "bronze", 0, 0, z + 0.08)
    mb.box(mx(), 2.88, 2.88, 0.46, "bronze", 0, 0, z + 0.39)
    mb.box(mx(), 3.06, 3.06, 0.13, "bronze", 0, 0, z + 0.68)
    mb.box(mx(), 2.32, 2.32, 0.30, "bronze", 0, 0, z + 0.89)
    for sx in (-1, 1):                       # 四隅の露盤宝珠
        for sy in (-1, 1):
            mb.box(mx(), 0.26, 0.26, 0.32, "bronze", sx * 1.02, sy * 1.02, z + 0.96)
    # ---- 伏鉢 : inverted bowl
    mb.cyl(mx(), 1.28, 0.14, "bronze", 40, 0, 0, z + 1.03, r2=1.14)
    mb.cyl(mx(), 1.12, 0.54, "bronze", 40, 0, 0, z + 1.17, r2=0.50)
    # ---- 請花 : lotus corolla
    mb.cyl(mx(), 0.48, 0.20, "bronze", 40, 0, 0, z + 1.70, r2=0.60)
    mb.cyl(mx(), 1.04, 0.15, "bronze", 40, 0, 0, z + 1.87, r2=0.74)
    for k in range(16):
        a = 2 * PI * k / 16
        Mp = mx(math.cos(a) * 0.86, math.sin(a) * 0.86, z + 1.87, rz=a)
        Mp = Mp @ Matrix.Rotation(RAD(34), 4, 'X')
        mb.box(Mp, 0.21, 0.34, 0.10, "bronze", 0, 0.05, 0)
    z0 = z + 1.99
    # ---- 擦管 + shaft
    mb.cyl(mx(), 0.26, 0.24, "bronze", 24, 0, 0, z0 - 0.12)
    mb.cyl(mx(), 0.135, 6.20, "bronze", 24, 0, 0, z0)
    # ---- 九輪 : nine narrow rings
    for k in range(9):
        R = 0.585 - 0.015 * k
        annulus(mb, mx(z=z0 + 0.50 + k * 0.49), 0.14, R, 0.062, "bronze_l", 32)
        if k < 8:
            for q in range(4):
                a = PI / 2 * q + PI / 4
                mb.box(mx(), 0.048, 0.048, 0.42, "bronze",
                       math.cos(a) * 0.24, math.sin(a) * 0.24, z0 + 0.72 + k * 0.49)
    # ---- 水煙 : flame openwork, four plates
    flame = [(0.00, 0.00), (0.36, 0.09), (0.54, 0.27), (0.38, 0.41),
             (0.62, 0.55), (0.44, 0.69), (0.60, 0.84), (0.36, 0.98),
             (0.48, 1.13), (0.26, 1.26), (0.32, 1.41), (0.14, 1.52),
             (0.08, 1.63), (0.00, 1.70)]
    flame = [(x * 1.42, zz * 1.12) for (x, zz) in flame]
    poly = flame + [(-x, zz) for (x, zz) in reversed(flame[1:])]
    n = len(poly)
    zs = z0 + 4.62
    for s in range(4):
        Ms = mx(rz=s * PI / 2) @ Matrix.Translation((0, 0, zs))
        for yy in (0.026, -0.026):
            pts = [Ms @ Vector((x, yy, zz)) for (x, zz) in poly]
            ctr = Ms @ Vector((0, yy, 0.42))
            i0 = len(mb.v)
            for q in pts:
                mb.v.append((q.x, q.y, q.z))
            for q in range(n):
                mb.poly([ctr, mb.v[i0 + q], mb.v[i0 + (q + 1) % n]], "bronze_l")
        for q in range(n):
            q2 = (q + 1) % n
            a0 = Ms @ Vector((poly[q][0], 0.026, poly[q][1]))
            a1 = Ms @ Vector((poly[q][0], -0.026, poly[q][1]))
            b0 = Ms @ Vector((poly[q2][0], 0.026, poly[q2][1]))
            b1 = Ms @ Vector((poly[q2][0], -0.026, poly[q2][1]))
            mb.poly([a0, a1, b1, b0], "bronze_l")
    # ---- 竜車 + 宝珠
    mb.cyl(mx(), 0.44, 0.13, "bronze_l", 32, 0, 0, zs + 1.98, r2=0.36)
    mb.cyl(mx(), 0.30, 0.10, "gold", 24, 0, 0, zs + 2.12)
    mb.sphere(mx(), 0.31, "gold", 28, 18, cz=zs + 2.36)
    mb.cyl(mx(), 0.13, 0.34, "gold", 18, 0, 0, zs + 2.55, r2=0.012)
    mb.cyl(mx(), 0.15, 2.34, "bronze", 16, 0, 0, zs - 0.30)
    bake(mb, "相輪", "04_相輪", 40.0)



# --------------------------------------------------------------------------- #
#  環境 : stone lantern, trees
# --------------------------------------------------------------------------- #
def build_lantern(x, y, s=1.0):
    mb = MB(["stone_step"])
    M = mx(x, y, 0)
    M = M @ Matrix.Scale(s, 4)
    mb.cyl(M, 0.62, 0.22, "stone_step", 8, 0, 0, 0)
    mb.cyl(M, 0.44, 0.18, "stone_step", 8, 0, 0, 0.22, r2=0.36)
    mb.cyl(M, 0.20, 1.10, "stone_step", 8, 0, 0, 0.40, r2=0.17)
    mb.cyl(M, 0.46, 0.16, "stone_step", 8, 0, 0, 1.50, r2=0.52)
    mb.cyl(M, 0.52, 0.52, "stone_step", 8, 0, 0, 1.66, r2=0.50)
    mb.cyl(M, 1.02, 0.16, "stone_step", 8, 0, 0, 2.18, r2=0.86)
    mb.cyl(M, 0.62, 0.10, "stone_step", 8, 0, 0, 2.34, r2=0.46)
    mb.sphere(M, 0.20, "stone_step", 12, 8, cz=2.52)
    bake(mb, "石灯籠", "05_環境")



def blob(mb, M, r, mat, seed, seg=14, rings=9, amp=0.30):
    """Irregular ellipsoid used for tree canopies."""
    import random as _r
    rnd = _r.Random(seed)
    ph = [rnd.uniform(0, 6.28) for _ in range(4)]
    base = len(mb.v)
    for i in range(rings + 1):
        th = PI * i / rings
        for k in range(seg):
            a = 2 * PI * k / seg
            n = (0.5 + 0.5 * math.sin(3 * a + ph[0]) * math.sin(2.1 * th + ph[1])
                 + 0.30 * math.sin(5 * a + 4.0 * th + ph[2])
                 + 0.18 * math.sin(7 * th + ph[3]))
            rr = r * (1.0 + amp * (n - 0.5) * 2.0)
            q = M @ Vector((rr * math.sin(th) * math.cos(a),
                            rr * math.sin(th) * math.sin(a),
                            rr * math.cos(th) * 0.85))
            mb.v.append((q.x, q.y, q.z))
    for i in range(rings):
        for k in range(seg):
            k2 = (k + 1) % seg
            a0 = base + i * seg + k
            b0 = base + i * seg + k2
            c0 = base + (i + 1) * seg + k2
            d0 = base + (i + 1) * seg + k
            mb.f.append((a0, b0, c0, d0))
            mb.mi.append(mb._m(mat))
            mb.uv.append(None)


def build_tree(x, y, h, seed, kind="broad"):
    rnd = random.Random(seed)
    mb = MB(["bark"])
    M = mx(x, y, -0.15)
    tr = h * (0.46 if kind == "broad" else 0.30)
    mb.cyl(M, h * 0.028, tr, "bark", 8, 0, 0, 0, r2=h * 0.014)
    if kind == "conifer":
        for k in range(9):
            zz = tr * 0.30 + k * h * 0.072
            rr = h * (0.155 - 0.014 * k)
            mb.cyl(M, rr, h * 0.135, "foliage_dark", 9, 0, 0, zz, r2=rr * 0.45)
        for k in range(4):
            a = rnd.uniform(0, 2 * PI)
            rr = rnd.uniform(0.04, 0.11) * h
            blob(mb, M @ Matrix.Translation((math.cos(a) * rr, math.sin(a) * rr,
                                             h * rnd.uniform(0.42, 0.80))),
                 h * rnd.uniform(0.075, 0.105), "foliage_dark", seed * 13 + k, 10, 7, 0.42)
    else:
        for k in range(5):
            a = rnd.uniform(0, 2 * PI)
            rr = h * rnd.uniform(0.04, 0.14)
            blob(mb, M @ Matrix.Translation((math.cos(a) * rr, math.sin(a) * rr,
                                             h * rnd.uniform(0.58, 0.84))),
                 h * rnd.uniform(0.15, 0.21),
                 "foliage" if k % 2 else "foliage_dark",
                 seed * 7 + k, 14, 8, 0.34)
        blob(mb, M @ Matrix.Translation((0, 0, h * 0.88)), h * 0.15,
             "foliage", seed * 3 + 1, 12, 7, 0.30)
    bake(mb, "樹木_%d" % seed, "05_環境", None)


def build_trees():
    # a few trees peeking out behind the pagoda (as in the reference photos)
    near = []
    for k, (x, y, h, kind) in enumerate(near):
        build_tree(x, y, h, 100 + k, kind)
    # continuous wooded belt on the horizon
    rnd = random.Random(11)
    for k in range(150):
        a = 2 * PI * k / 150 + rnd.uniform(-0.012, 0.012)
        r = rnd.uniform(150, 232)
        h = rnd.uniform(12, 19)
        build_tree(math.cos(a) * r, math.sin(a) * r, h, 300 + k,
                   "conifer" if k % 3 else "broad")


# --------------------------------------------------------------------------- #
#  world / lights / cameras
# --------------------------------------------------------------------------- #
def setup_world():
    w = bpy.data.worlds.new("sky")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    L = nt.links.new
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')

    env = nt.nodes.new('ShaderNodeTexEnvironment')
    env.image = bpy.data.images.load(
        os.path.join(OUT, "hdri", "sky_pure.hdr"), check_existing=True)
    env.interpolation = 'Cubic'
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Rotation'].default_value = (0.0, 0.0, RAD(ROT_SKY))
    mp.inputs['Scale'].default_value = (1.0, 1.0, 1.0)
    L(nt.nodes.new('ShaderNodeTexCoord').outputs['Generated'], mp.inputs['Vector'])
    L(mp.outputs['Vector'], env.inputs['Vector'])
    # replace everything below the horizon with a neutral warm ground colour
    geo2 = nt.nodes.new('ShaderNodeNewGeometry')
    neg = nt.nodes.new('ShaderNodeVectorMath')
    neg.operation = 'SCALE'
    neg.inputs['Scale'].default_value = -1.0
    L(geo2.outputs['Incoming'], neg.inputs[0])
    sep2 = nt.nodes.new('ShaderNodeSeparateXYZ')
    L(neg.outputs['Vector'], sep2.inputs['Vector'])
    mr2 = nt.nodes.new('ShaderNodeMapRange')
    mr2.inputs['From Min'].default_value = 0.02
    mr2.inputs['From Max'].default_value = 0.16
    L(sep2.outputs['Z'], mr2.inputs['Value'])
    gnd = nt.nodes.new('ShaderNodeMix')
    gnd.data_type = 'RGBA'
    L(mr2.outputs['Result'], gnd.inputs[0])
    gnd.inputs[6].default_value = (0.30, 0.28, 0.24, 1)
    L(env.outputs['Color'], gnd.inputs[7])

    # keep the sky slightly cooler / brighter than the raw capture
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.blend_type = 'MULTIPLY'
    mix.inputs['Factor'].default_value = 0.30
    L(gnd.outputs[2], mix.inputs[6])
    mix.inputs[7].default_value = (0.94, 1.0, 1.12, 1)
    L(mix.outputs[2], bg.inputs['Color'])

    # camera rays get the full sky; illumination a touch softer
    lp = nt.nodes.new('ShaderNodeLightPath')
    st = nt.nodes.new('ShaderNodeMix')
    st.data_type = 'FLOAT'
    st.inputs[2].default_value = 1.0
    st.inputs[3].default_value = 0.72
    L(lp.outputs['Is Camera Ray'], st.inputs['Factor'])
    L(st.outputs[0], bg.inputs['Strength'])
    L(bg.outputs['Background'], out.inputs['Surface'])


def setup_lights():
    d = bpy.data.lights.new("sun", 'SUN')
    d.energy = 3.3
    d.angle = RAD(0.9)
    d.color = (1.0, 0.958, 0.900)
    ob = bpy.data.objects.new("sun", d)
    bpy.context.scene.collection.objects.link(ob)
    toward = Vector((0.52, -0.60, 1.20)).normalized()
    ob.rotation_euler = (-toward).to_track_quat('-Z', 'Y').to_euler()
    # bounce from the bright gravel courtyard
    d2 = bpy.data.lights.new("fill_bounce", 'AREA')
    d2.shape = 'RECTANGLE'
    d2.size, d2.size_y = 46.0, 30.0
    d2.energy = 900.0
    d2.color = (1.0, 0.95, 0.86)
    o2 = bpy.data.objects.new("fill_bounce", d2)
    bpy.context.scene.collection.objects.link(o2)
    o2.location = (2.0, -34.0, 2.5)
    o2.rotation_euler = (Vector((0, 0, 10)) - Vector(o2.location)).to_track_quat('-Z', 'Y').to_euler()
    # cool sky fill
    d3 = bpy.data.lights.new("fill_sky", 'AREA')
    d3.shape = 'RECTANGLE'
    d3.size, d3.size_y = 36.0, 36.0
    d3.energy = 220.0
    d3.color = (0.72, 0.82, 1.0)
    o3 = bpy.data.objects.new("fill_sky", d3)
    bpy.context.scene.collection.objects.link(o3)
    o3.location = (-30.0, -12.0, 26.0)
    o3.rotation_euler = (Vector((0, 0, 15)) - Vector(o3.location)).to_track_quat('-Z', 'Y').to_euler()


def add_camera(name, loc, target, lens=50.0):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36.0
    cd.clip_start = 0.1
    cd.clip_end = 4000.0
    ob = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return ob


def setup_render(samples=200, res=(1120, 1680)):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'GPU'
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'OPTIX'
        prefs.get_devices()
        for dv in prefs.devices:
            dv.use = (dv.type != 'CPU')
    except Exception as e:
        print("GPU setup failed:", e)
        sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    sc.cycles.max_bounces = 8
    sc.cycles.diffuse_bounces = 4
    sc.cycles.glossy_bounces = 4
    sc.cycles.transmission_bounces = 4
    sc.cycles.transparent_max_bounces = 8
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.010
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    try:
        sc.view_settings.view_transform = 'Khronos PBR Neutral'
        sc.view_settings.look = 'None'
        sc.view_settings.exposure = -0.20
    except Exception:
        sc.view_settings.view_transform = 'AgX'
        sc.view_settings.look = 'AgX - Punchy'
        sc.view_settings.exposure = -0.25
    sc.render.image_settings.file_format = 'PNG'


# --------------------------------------------------------------------------- #
def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    MAT.build_materials()

    build_ground()
    build_platform()
    build_veranda()
    for i in range(5):
        build_body(i)
        build_brackets(i)
        build_roof(i)
        if i > 0:
            build_balcony(i)
    build_sorin()
    build_lantern(-11.2, -12.6, 1.0)
    build_lantern(11.2, -12.6, 1.0)
    build_trees()
    setup_world()
    setup_lights()

    cam = add_camera("相机_主", (0.0, -96.0, 6.8), (0, 0, 15.6), 82.0)
    sc.camera = cam
    add_camera("相机_斜", (52.0, -68.0, 6.4), (0, 0, 15.2), 76.0)
    add_camera("相机_仰", (7.0, -26.0, 1.55), (0, 0, 19.0), 40.0)
    add_camera("相机_細部", (12.0, -21.0, 3.4), (0, 0, 10.2), 50.0)
    add_camera("相机_相輪", (7.0, -28.0, 22.5), (0, 0, 27.4), 70.0)

    setup_render(80 if PREVIEW else 220,
                 (760, 1140) if PREVIEW else (1120, 1680))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "法隆寺五重塔_v3.blend"))
    print("BUILD OK  objects=%d  verts=%d" % (
        len(bpy.data.objects),
        sum(len(o.data.vertices) for o in bpy.data.objects if o.type == 'MESH')))


if __name__ == "__main__":
    main()
