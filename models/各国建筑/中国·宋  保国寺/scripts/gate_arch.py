# -*- coding: utf-8 -*-
"""保国寺山门（天王殿）· 依照参考照片重建
坐标：X 面阔，Y 进深（-Y 为正立面），Z 向上，单位米
"""
import bpy, math, random
from mathutils import Vector, Matrix

from temple_core import (MeshAccum, hx, lerp, TAU, mat_simple, mat_wood,
                         mat_surface, mat_tile, mat_gold, mat_paving,
                         mat_slab, make_text, FONT_CALLI)
import temple_arch as TA

# ============================================================================
# 尺度（依照片比例：面阔三间、明间门洞、次间碑窗碑、单檐歇山）
# ============================================================================
G = 1.30                     # 台基高
COL_X = [-7.10, -1.60, 1.60, 7.10]     # 檐柱（明间 3.2，次间 5.5）
COL_Y = [-3.10, 3.10]                   # 前后檐
COL_H = 3.90
COL_R = 0.22
COL_TOP = G + COL_H                      # 5.20
LANE_H = 0.45                            # 阑额
PUPAI_H = 0.15
PUPAI_TOP = COL_TOP + LANE_H + PUPAI_H   # 5.80
DOUG_H = 0.62
DOUG_TOP = PUPAI_TOP + DOUG_H            # 6.42
TIAO = 0.82                              # 出跳
EAVE_Z = 6.58

# 屋面（单檐歇山）
RA = 8.10                    # 半宽
RB = 4.35                    # 半深
RXR = 4.60                   # 正脊半长
RH = 3.55                    # 屋面举高
LIFT = 1.10                  # 翼角起翘

WALL_Y = COL_Y[0]            # 正立面板壁所在平面


# ============================================================================
# 材质
# ============================================================================
def materials():
    M = {}
    M["stone"] = mat_surface("MAT_石材", "#8a8578", "#635f55", scale=3.2,
                             rough=0.85, bump=0.35, bump_scale=38,
                             grime=(0.1, 2.2, 0.66))
    M["stone_dark"] = mat_surface("MAT_台基", "#6f6b60", "#4c4942", scale=2.4,
                                  rough=0.88, bump=0.4, bump_scale=30,
                                  grime=(0.0, 2.0, 0.7))
    M["paving"] = mat_paving()
    M["wood"] = mat_wood("MAT_木壁", "#45291f", "#2a1811", axis='Z',
                         scale=2.4, rough=0.66, bump=0.18)
    M["wood_col"] = mat_wood("MAT_檐柱", "#5d2b21", "#3a1a13", axis='Z',
                             scale=2.0, rough=0.62, bump=0.16)
    M["wood_mid"] = mat_wood("MAT_中层木", "#5a3a2c", "#3a2318", axis='Z',
                             scale=2.6, rough=0.66, bump=0.14)
    M["wood_dark"] = mat_wood("MAT_深木", "#31201a", "#1c120e", axis='Z',
                              scale=3.0, rough=0.7, bump=0.14)
    M["dado"] = mat_surface("MAT_墙裙", "#a4746a", "#7e534b", scale=2.0,
                            rough=0.85, bump=0.2, bump_scale=26,
                            grime=(1.3, 2.6, 0.78))
    M["slab"] = mat_slab("MAT_碑面")
    M["slab_text"] = mat_simple("MAT_碑文", "#b8b1a1", rough=0.84)
    M["slab_ink"] = mat_simple("MAT_碑刻", "#6f695e", rough=0.86)
    M["plaster"] = mat_surface("MAT_白墙", "#ded9cb", "#bfb9a9", scale=1.8,
                               rough=0.88, bump=0.25, bump_scale=26,
                               grime=(0.6, 4.8, 0.62))
    M["tile"] = mat_tile("MAT_青瓦")
    M["tile_dark"] = mat_surface("MAT_脊瓦", "#31342d", "#1d1f19", scale=8,
                                 rough=0.72, bump=0.25, bump_scale=55)
    M["tile_light"] = mat_surface("MAT_瓦当", "#5a5d55", "#3e413b", scale=12,
                                  rough=0.55, bump=0.2, bump_scale=60)
    M["plaque"] = mat_wood("MAT_匾底", "#241a14", "#130d0a", axis='X',
                           scale=3.0, rough=0.45, bump=0.05)
    M["gold"] = mat_gold()
    M["dark"] = mat_simple("MAT_暗部", "#0e0b08", rough=0.95)
    M["door_red"] = mat_wood("MAT_红门", "#8a3b34", "#5c221d", axis='Z',
                             scale=2.6, rough=0.6, bump=0.14)
    M["ground"] = mat_surface("MAT_庭院", "#8f8b7e", "#706d62", scale=1.4,
                              rough=0.92, bump=0.32, bump_scale=22)
    M["leaf"] = mat_surface("MAT_树叶", "#26401f", "#162610", scale=8.0,
                            rough=0.88, bump=0.6, bump_scale=30)
    M["trunk"] = mat_wood("MAT_树干", "#4a3b2c", "#2e2419", axis='Z', scale=4,
                          rough=0.8, bump=0.3)
    M["rock"] = mat_surface("MAT_山石", "#8d8a7e", "#636053", scale=2.0,
                            rough=0.9, bump=0.5, bump_scale=18)
    return M


# ============================================================================
# 1. 台基与踏跺
# ============================================================================
def build_platform(coll, M):
    px = 16.40
    py = 7.90
    a = MeshAccum()
    a.box2(-px / 2, px / 2, -py / 2, py / 2, 0, G)
    a.finish("台基_主体", M["stone_dark"], coll, bevel=0.012)

    # 阶条石
    a = MeshAccum()
    w, t = 0.52, 0.22
    n = 14
    for i in range(n):
        x0 = -px / 2 + i * px / n
        x1 = x0 + px / n - 0.03
        a.box2(x0, x1, -py / 2, -py / 2 + w, G - t, G + 0.008)
    m = 7
    for i in range(m):
        y0 = -py / 2 + i * py / m
        y1 = y0 + py / m - 0.03
        a.box2(-px / 2, -px / 2 + w, y0, y1, G - t, G + 0.008)
        a.box2(px / 2 - w, px / 2, y0, y1, G - t, G + 0.008)
    a.finish("台基_阶条石", M["stone"], coll, bevel=0.008)

    # 台面
    a = MeshAccum()
    a.box2(-px / 2 + 0.4, px / 2 - 0.4, -py / 2 + 0.4, py / 2 - 0.4, G - 0.10, G + 0.004)
    a.finish("台基_台面", M["paving"], coll)

    # 踏跺：通面阔，9 级
    a = MeshAccum()
    n_step = 9
    rise = G / n_step
    run = 0.50
    for i in range(n_step):
        z1 = G - i * rise
        z0 = z1 - rise
        y1 = -py / 2 - i * run
        y0 = y1 - run
        a.box2(-px / 2, px / 2, y0, y1, z0 - 0.12, z1 - 0.03)
    # 两侧垂带
    for sx in (-1, 1):
        xx = sx * (px / 2 + 0.05)
        rings = []
        for (yy, zz) in ((-py / 2, G + 0.06), (-py / 2 - run * n_step, 0.06)):
            rings.append([(xx - 0.18, yy, zz + 0.10), (xx + 0.18, yy, zz + 0.10),
                          (xx + 0.18, yy, zz - 0.30), (xx - 0.18, yy, zz - 0.30)])
        a.loft(rings, closed_profile=True, cap_ends=True)
    a.finish("踏跺", M["stone"], coll, bevel=0.01)

    a = MeshAccum()
    for i in range(n_step):
        z1 = G - i * rise
        y1 = -py / 2 - i * run
        a.box2(-px / 2, px / 2, y1 - 0.055, y1, z1 - 0.055, z1 - 0.030)
    a.finish("踏跺_踢面阴影", M["stone_dark"], coll)

    # 柱础
    a = MeshAccum()
    for x in COL_X:
        for y in (COL_Y[0], COL_Y[-1]):
            a.cyl((x, y, G + 0.14), 0.30, 0.28, seg=18, rtop=0.26)
    a.finish("柱础", M["stone"], coll, bevel=0.012)


# ============================================================================
# 2. 柱、额枋
# ============================================================================
def build_frame(coll, M):
    a = MeshAccum()
    for x in COL_X:
        for y in (COL_Y[0], COL_Y[-1]):
            a.cyl((x, y, G + 0.28 + COL_H / 2), COL_R, COL_H, seg=20, rtop=COL_R * 0.94)
    # 山面中柱
    for y in COL_Y:
        for x in (COL_X[0], COL_X[-1]):
            a.cyl((x, y, G + 0.28 + COL_H / 2), COL_R, COL_H, seg=20, rtop=COL_R * 0.94)
    a.finish("檐柱", M["wood_col"], coll)

    # 阑额
    a = MeshAccum()
    for y in (COL_Y[0], COL_Y[-1]):
        for i in range(len(COL_X) - 1):
            x0, x1 = COL_X[i], COL_X[i + 1]
            a.box2(x0 - 0.06, x1 + 0.06, y - 0.12, y + 0.12, COL_TOP, COL_TOP + LANE_H)
    for x in (COL_X[0], COL_X[-1]):
        a.box2(x - 0.12, x + 0.12, COL_Y[0] - 0.06, COL_Y[-1] + 0.06, COL_TOP, COL_TOP + LANE_H)
    a.finish("阑额", M["wood_col"], coll, bevel=0.01)

    # 普拍枋
    a = MeshAccum()
    for y in (COL_Y[0], COL_Y[-1]):
        a.box2(COL_X[0] - 0.28, COL_X[-1] + 0.28, y - 0.22, y + 0.22,
               COL_TOP + LANE_H, PUPAI_TOP)
    for x in (COL_X[0], COL_X[-1]):
        a.box2(x - 0.22, x + 0.22, COL_Y[0] - 0.28, COL_Y[-1] + 0.28,
               COL_TOP + LANE_H, PUPAI_TOP)
    a.finish("普拍枋", M["wood_col"], coll, bevel=0.008)

    # 地栿
    a = MeshAccum()
    for y in (COL_Y[0], COL_Y[-1]):
        a.box2(COL_X[0], COL_X[-1], y - 0.11, y + 0.11, G + 0.02, G + 0.24)
    a.finish("地栿", M["wood_dark"], coll, bevel=0.008)


# ============================================================================
# 3. 斗拱（单跳五铺作简化）
# ============================================================================
def dougong_module(acc, M, s=1.0):
    """局部坐标：+Y 出跳，Z 向上，原点在栌斗底"""
    def B(c, sz):
        acc.box((c[0] * s, c[1] * s, c[2] * s), (sz[0] * s, sz[1] * s, sz[2] * s), M)

    acc.frustum((0, 0, 0.07 * s), (0.26 * s, 0.26 * s), (0.40 * s, 0.40 * s), 0.14 * s, M)
    B((0, 0, 0.17), (0.40, 0.40, 0.07))
    # 泥道拱 + 华拱
    B((0, 0, 0.27), (0.72, 0.13, 0.15))
    B((0, 0.18, 0.27), (0.13, 0.62, 0.15))
    # 散斗
    for sx in (-0.32, 0.32):
        B((sx, 0, 0.39), (0.18, 0.16, 0.11))
    B((0, 0.42, 0.39), (0.18, 0.18, 0.11))
    # 下昂（斜出）
    ang = math.radians(-16)
    L = 0.72
    Mx = Matrix.Translation(Vector((0, 0.34 * s, 0.56 * s))) @ Matrix.Rotation(ang, 4, 'X')
    acc.box((0, 0, 0), (0.13 * s, L * s, 0.16 * s), M @ Mx)
    acc.box((0, (L * 0.50) * s, -0.05 * s), (0.12 * s, 0.14 * s, 0.12 * s), M @ Mx)
    # 交互斗 + 令拱
    B((0, 0.72, 0.50), (0.18, 0.18, 0.11))
    B((0, 0.78, 0.58), (0.62, 0.13, 0.14))
    for sx in (-0.26, 0.0, 0.26):
        B((sx, 0.78, 0.66), (0.15, 0.15, 0.09))
    B((0, 0.02, 0.46), (0.82, 0.14, 0.10))


def build_dougong(coll, M):
    rows = [("x", COL_Y[0], math.pi), ("x", COL_Y[-1], 0.0),
            ("y", COL_X[0], math.pi / 2), ("y", COL_X[-1], -math.pi / 2)]
    acc = MeshAccum()
    step = 0.86
    for axis, fixed, rot in rows:
        if axis == "x":
            span = COL_X[-1] - COL_X[0]
            n = int(span / step) + 1
            for i in range(n + 1):
                x = COL_X[0] + i * span / n
                Mx = Matrix.Translation(Vector((x, fixed, PUPAI_TOP))) @ Matrix.Rotation(rot, 4, 'Z')
                dougong_module(acc, Mx)
        else:
            span = COL_Y[-1] - COL_Y[0]
            n = int(span / step) + 1
            for i in range(n + 1):
                y = COL_Y[0] + i * span / n
                Mx = Matrix.Translation(Vector((fixed, y, PUPAI_TOP))) @ Matrix.Rotation(rot, 4, 'Z')
                dougong_module(acc, Mx)
    # 转角
    for x in (COL_X[0], COL_X[-1]):
        for y in (COL_Y[0], COL_Y[-1]):
            ux = 1.0 if x > 0 else -1.0
            uy = 1.0 if y > 0 else -1.0
            rot = math.atan2(-ux * 0.7071, uy * 0.7071)
            Mx = Matrix.Translation(Vector((x, y, PUPAI_TOP))) @ Matrix.Rotation(rot, 4, 'Z')
            dougong_module(acc, Mx, s=1.05)
    acc.finish("斗拱", M["wood_col"], coll, bevel=0.006)

    # 撩檐枋
    a = MeshAccum()
    z = DOUG_TOP - 0.10
    fy, by = COL_Y[0] - TIAO, COL_Y[-1] + TIAO
    fx, bx = COL_X[0] - TIAO, COL_X[-1] + TIAO
    a.box2(fx - 0.30, bx + 0.30, fy - 0.13, fy + 0.13, z - 0.11, z + 0.11)
    a.box2(fx - 0.30, bx + 0.30, by - 0.13, by + 0.13, z - 0.11, z + 0.11)
    a.box2(fx - 0.13, fx + 0.13, fy, by, z - 0.11, z + 0.11)
    a.box2(bx - 0.13, bx + 0.13, fy, by, z - 0.11, z + 0.11)
    a.finish("撩檐枋", M["wood_col"], coll, bevel=0.008)

    # 拱眼壁（带雕花小格）
    a = MeshAccum()
    a.box2(COL_X[0] - 0.5, COL_X[-1] + 0.5, COL_Y[0] - 0.045, COL_Y[0] + 0.045,
           PUPAI_TOP, DOUG_TOP - 0.05)
    a.box2(COL_X[0] - 0.5, COL_X[-1] + 0.5, COL_Y[-1] - 0.045, COL_Y[-1] + 0.045,
           PUPAI_TOP, DOUG_TOP - 0.05)
    a.box2(COL_X[0] - 0.045, COL_X[0] + 0.045, COL_Y[0] - 0.5, COL_Y[-1] + 0.5,
           PUPAI_TOP, DOUG_TOP - 0.05)
    a.box2(COL_X[-1] - 0.045, COL_X[-1] + 0.045, COL_Y[0] - 0.5, COL_Y[-1] + 0.5,
           PUPAI_TOP, DOUG_TOP - 0.05)
    a.finish("拱眼壁", M["wood_mid"], coll)

    # 檐椽
    a = MeshAccum()
    n = 54
    for i in range(n):
        x = COL_X[0] - TIAO + 0.1 + i * (COL_X[-1] - COL_X[0] + 2 * TIAO - 0.2) / (n - 1)
        TA.cyl_between(a, (x, fy - 0.05, DOUG_TOP + 0.02),
                       (x, fy + 0.55, DOUG_TOP + 0.30), 0.055)
    a.finish("檐椽", M["wood_dark"], coll)


# ============================================================================
# 4. 屋面（单檐歇山）
# ============================================================================
def build_roof(coll, M):
    z0 = EAVE_Z
    fn = lambda x, y: TA.surf_xi(x, y, RA, RB, RXR, RH, z0, lift=LIFT)

    TA.make_roof_slab(coll, M, "屋面", RA, RB, fn, M["tile"], M["wood_dark"],
                      nx=190, ny=130, thick=0.15, flare=0.28)

    # 瓦垄
    acc = MeshAccum()
    outers = []
    spacing = 0.30
    for edge in range(4):
        if edge < 2:
            L = 2 * RA
            n = int(L / spacing)
            for i in range(n):
                x = -RA + (i + 0.5) * L / n
                outers.append((x, -RB if edge == 0 else RB))
        else:
            L = 2 * RB
            n = int(L / spacing)
            for i in range(n):
                y = -RB + (i + 0.5) * L / n
                outers.append((-RA if edge == 2 else RA, y))

    br = 0.44
    ystar = RB * (1 - br ** (1.0 / 1.70))

    def proj(x, y):
        if abs(x) <= RXR:
            return (x, 0.0)
        return (math.copysign(RXR - 0.05, x), max(-ystar, min(ystar, y)))

    TA.rib_fan(acc, fn, outers, proj, samples=34, r=0.078)
    acc.finish("瓦垄", M["tile"], coll, smooth=True)

    a = MeshAccum()
    TA.tile_caps(a, fn, outers, r=0.080)
    a.finish("瓦当", M["tile_light"], coll)

    a = MeshAccum()
    TA.eave_trim(a, fn, TA._perimeter(RA, RB, 220))
    a.finish("檐口滴水", M["tile_dark"], coll)

    # 檐椽沿坡
    a = MeshAccum()
    n = 48
    for sy in (-1, 1):
        for i in range(n):
            x = -7.2 + i * (14.4 / (n - 1))
            y1 = sy * (RB - 0.06)
            y2 = sy * (RB - 1.55)
            TA.cyl_between(a, (x, y1, fn(x, y1)[0] - 0.26),
                           (x, y2, fn(x, y2)[0] - 0.32), 0.055)
    a.finish("屋面檐椽", M["wood_dark"], coll)

    # 山花 + 博风
    zb = z0 + RH * br
    a2 = MeshAccum()
    ns = 20
    for sx in (-1, 1):
        x = sx * (RXR - 0.02)
        top, bot = [], []
        for i in range(ns + 1):
            y = -ystar + 2 * ystar * i / ns
            v = min(1.0, abs(y) / RB)
            top.append((x, y, z0 + RH * (1 - v) ** 1.70))
            bot.append((x, y, zb))
        o = len(a2.v)
        a2.v.extend(top)
        a2.v.extend(bot)
        for i in range(ns):
            if sx > 0:
                a2.f.append((o + i, o + i + 1, o + ns + 1 + i + 1, o + ns + 1 + i))
            else:
                a2.f.append((o + i, o + ns + 1 + i, o + ns + 1 + i + 1, o + i + 1))
        for i in range(ns):
            p0, p1 = Vector(top[i]), Vector(top[i + 1])
            o2 = len(a2.v)
            a2.v += [(p0.x + sx * 0.05, p0.y, p0.z + 0.02),
                     (p1.x + sx * 0.05, p1.y, p1.z + 0.02),
                     (p1.x + sx * 0.05, p1.y, p1.z - 0.24),
                     (p0.x + sx * 0.05, p0.y, p0.z - 0.24),
                     (p0.x - sx * 0.02, p0.y, p0.z - 0.24),
                     (p1.x - sx * 0.02, p1.y, p1.z - 0.24)]
            a2.f += [(o2, o2 + 1, o2 + 2, o2 + 3), (o2 + 3, o2 + 2, o2 + 5, o2 + 4)]
    a2.finish("山花博风", M["wood_dark"], coll)

    # 悬鱼
    a = MeshAccum()
    for sx in (-1, 1):
        Mx = Matrix.Translation(Vector((sx * (RXR - 0.14), 0, z0 + RH - 0.48)))
        a.cyl((0, 0, 0), 0.17, 0.05, seg=14, M=Mx @ Matrix.Rotation(math.pi / 2, 4, 'Y'))
    a.finish("悬鱼", M["wood_dark"], coll)


# ============================================================================
# 5. 脊饰
# ============================================================================
def build_ridges(coll, M):
    z0 = EAVE_Z
    zr = z0 + RH
    # 正脊
    a = MeshAccum()
    pts = [(-RXR, 0, zr - 0.05), (0, 0, zr + 0.02), (RXR, 0, zr - 0.05)]
    TA.sweep(a, pts, TA.ridge_profile(0.96, 0.54))
    a.finish("正脊", M["tile_dark"], coll, bevel=0.012)

    a = MeshAccum()
    TA.sweep(a, [(p[0], p[1], p[2] + 0.52) for p in pts], TA.ridge_profile(0.56, 0.30))
    a.finish("正脊瓦条", M["tile_dark"], coll, bevel=0.008)

    # 鸱吻
    a = MeshAccum()
    for sx in (-1, 1):
        TA.chiwen(a, M, sx * (RXR + 0.02), 0, zr - 0.14, s=1.10, flip=sx)
    a.finish("鸱吻", M["tile_dark"], coll, bevel=0.008)

    # 垂脊 + 走兽
    fn = lambda x, y: TA.surf_xi(x, y, RA, RB, RXR, RH, z0, lift=LIFT)
    a = MeshAccum()
    for sx in (-1, 1):
        for sy in (-1, 1):
            pts = []
            for i in range(16):
                t = i / 15
                y = sy * RB * (1 - t * 0.999)
                x = sx * lerp(RA, RXR, t)
                pts.append((x, y, fn(x, y)[0] + 0.02))
            TA.sweep(a, pts, TA.ridge_profile(0.38, 0.28))
            for k in range(4):
                t = 0.04 + k * 0.06
                y = sy * RB * (1 - t)
                x = sx * lerp(RA, RXR, t)
                a.box((x, y, fn(x, y)[0] + 0.32), (0.18, 0.16, 0.24))
    a.finish("垂脊走兽", M["tile_dark"], coll, bevel=0.01)


# ============================================================================
# 6. 正立面
# ============================================================================
def build_facade(coll, M):
    y0 = WALL_Y
    a = MeshAccum()   # 木壁
    b = MeshAccum()   # 框/线脚
    c = MeshAccum()   # 格心
    d = MeshAccum()   # 碑面
    e = MeshAccum()   # 墙裙
    f = MeshAccum()   # 暗部
    t = MeshAccum()   # 碑文

    dw, dz0, dz1 = 2.40, G + 0.16, G + 3.20

    # 墙裙（门洞两侧断开）
    e.box2(COL_X[0], -dw / 2 - 0.16, y0 - 0.10, y0 + 0.06, G + 0.02, G + 0.86)
    e.box2(dw / 2 + 0.16, COL_X[-1], y0 - 0.10, y0 + 0.06, G + 0.02, G + 0.86)
    # 上部木壁（门洞两侧 + 门洞上方）
    a.box2(COL_X[0], -dw / 2 - 0.16, y0 - 0.09, y0 + 0.04, G + 0.86, COL_TOP)
    a.box2(dw / 2 + 0.16, COL_X[-1], y0 - 0.09, y0 + 0.04, G + 0.86, COL_TOP)
    a.box2(-dw / 2 - 0.16, dw / 2 + 0.16, y0 - 0.09, y0 + 0.04, dz1 + 0.14, COL_TOP)

    # ---- 明间：门洞 ----
    # 门内不封，形成穿堂
    # 门框
    b.box2(-dw / 2 - 0.16, -dw / 2, y0 - 0.14, y0 + 0.02, dz0 - 0.06, dz1 + 0.14)
    b.box2(dw / 2, dw / 2 + 0.16, y0 - 0.14, y0 + 0.02, dz0 - 0.06, dz1 + 0.14)
    b.box2(-dw / 2, dw / 2, y0 - 0.14, y0 + 0.02, dz1, dz1 + 0.16)
    b.box2(-dw / 2, dw / 2, y0 - 0.14, y0 + 0.02, dz0 - 0.10, dz0)
    # 门洞两侧的抱框
    b.box2(-dw / 2 - 0.30, -dw / 2 - 0.16, y0 - 0.12, y0 + 0.02, G + 0.06, COL_TOP)
    b.box2(dw / 2 + 0.16, dw / 2 + 0.30, y0 - 0.12, y0 + 0.02, G + 0.06, COL_TOP)

    # ---- 次间：碑 + 窗 + 碑 ----
    for (x0, x1) in ((COL_X[1], COL_X[2]), (COL_X[2], COL_X[3]))[:0] + \
                    ((COL_X[0], COL_X[1]), (COL_X[2], COL_X[3])):
        pass
    for (x0, x1) in ((COL_X[0], COL_X[1]), (COL_X[2], COL_X[3])):
        inner0, inner1 = x0 + 0.30, x1 - 0.30
        w = inner1 - inner0
        pw = w * 0.265
        ww = w * 0.33
        gap = (w - 2 * pw - ww) / 2
        # 画面幅左碑
        p1a, p1b = inner0, inner0 + pw
        p2a, p2b = p1b + gap, p1b + gap + ww
        p3a, p3b = p2b + gap, p2b + gap + pw
        for (pa, pb) in ((p1a, p1b), (p3a, p3b)):
            b.box2(pa - 0.06, pb + 0.06, y0 - 0.12, y0 + 0.02, G + 0.90, G + 3.22)
            d.box2(pa, pb, y0 - 0.145, y0 - 0.04, G + 0.98, G + 3.14)
            # 碑文区（略深底色）+ 竖行字块
            t.box2(pa + 0.10, pb - 0.10, y0 - 0.160, y0 - 0.150, G + 1.06, G + 3.06)
            ncol, nrow = 7, 16
            for k in range(ncol):
                xx = pa + (k + 0.7) * (pb - pa) / (ncol + 0.4)
                for r in range(nrow):
                    zz = G + 1.12 + r * (1.86 / nrow)
                    t.box2(xx - 0.026, xx + 0.026, y0 - 0.172, y0 - 0.159,
                           zz, zz + 0.034)

        # 窗
        b.box2(p2a - 0.07, p2a, y0 - 0.13, y0 + 0.02, G + 0.86, G + 3.26)
        b.box2(p2b, p2b + 0.07, y0 - 0.13, y0 + 0.02, G + 0.86, G + 3.26)
        b.box2(p2a, p2b, y0 - 0.13, y0 + 0.02, G + 0.86, G + 0.98)
        b.box2(p2a, p2b, y0 - 0.13, y0 + 0.02, G + 3.14, G + 3.26)
        f.box2(p2a, p2b, y0 + 0.02, y0 + 0.10, G + 0.98, G + 3.14)
        # 菱形格心 + 中心团花
        w2 = (p2b - p2a)
        h2 = G + 3.14 - (G + 0.98)
        zc = (G + 0.98 + G + 3.14) / 2
        xc = (p2a + p2b) / 2
        step = 0.24
        k = -int((w2 + h2) / step)
        for i in range(k, int((w2 + h2) / step) + 1):
            # 45 度斜棂（两族）
            for sgn in (1, -1):
                # 直线：x = xc + t, z = zc + sgn*t + i*step
                # 与窗口矩形求交
                pts = _clip_diag(xc, zc + i * step, sgn, p2a, p2b, G + 0.98, G + 3.14)
                if pts:
                    (ax, az), (bx, bz) = pts
                    L = math.hypot(bx - ax, bz - az)
                    if L < 0.05:
                        continue
                    ang = -math.atan2(bz - az, bx - ax)
                    c.box(((ax + bx) / 2, y0 - 0.105, (az + bz) / 2),
                          (L, 0.035, 0.026), M=Matrix.Rotation(ang, 4, 'Y'))
        # 团花（圆环 + 花瓣）
        seg = 14
        for i in range(seg):
            ang = TAU * i / seg
            c.box((xc + 0.26 * math.cos(ang), y0 - 0.11, zc + 0.26 * math.sin(ang)),
                  (0.075, 0.04, 0.05), M=Matrix.Rotation(ang, 4, 'Y'))
        for i in range(8):
            ang = TAU * i / 8
            c.box((xc + 0.12 * math.cos(ang), y0 - 0.11, zc + 0.12 * math.sin(ang)),
                  (0.12, 0.035, 0.04), M=Matrix.Rotation(ang, 4, 'Y'))

    a.finish("正立面_木壁", M["wood"], coll, bevel=0.006)
    b.finish("正立面_门框窗框", M["wood_dark"], coll, bevel=0.006)
    c.finish("正立面_格心", M["wood_dark"], coll)
    d.finish("正立面_碑面", M["slab"], coll, bevel=0.006)
    e.finish("正立面_墙裙", M["dado"], coll, bevel=0.006)
    f.finish("正立面_暗部", M["dark"], coll)
    t.finish("正立面_碑文", M["slab_ink"], coll)

    # 山墙、背墙（暗）
    a = MeshAccum()
    for x in (COL_X[0], COL_X[-1]):
        a.box2(x - 0.09, x + 0.09, y0, COL_Y[-1], G, COL_TOP)
    # 背墙（留穿堂洞）
    yb = COL_Y[-1]
    a.box2(COL_X[0], -dw / 2, yb - 0.09, yb + 0.09, G, COL_TOP)
    a.box2(dw / 2, COL_X[-1], yb - 0.09, yb + 0.09, G, COL_TOP)
    a.box2(-dw / 2, dw / 2, yb - 0.09, yb + 0.09, dz1, COL_TOP)
    a.finish("山墙背墙", M["wood"], coll, bevel=0.008)

    # 穿堂两侧暗壁
    a = MeshAccum()
    a.box2(COL_X[0] + 0.2, -dw / 2, y0 + 0.08, yb - 0.08, G, DOUG_TOP)
    a.box2(dw / 2, COL_X[-1] - 0.2, y0 + 0.08, yb - 0.08, G, DOUG_TOP)
    a.finish("殿内暗室", M["dark"], coll)


def _clip_diag(xc, z0, sgn, xa, xb, za, zb):
    """直线 z = z0 + sgn*(x-xc) 与矩形求交"""
    ts = []
    for x in (xa, xb):
        z = z0 + sgn * (x - xc)
        if za - 1e-6 <= z <= zb + 1e-6:
            ts.append((x, z))
    for z in (za, zb):
        x = xc + sgn * (z - z0)
        if xa - 1e-6 <= x <= xb + 1e-6:
            ts.append((x, z))
    if len(ts) < 2:
        return None
    pts = sorted(set([(round(a, 5), round(b, 5)) for a, b in ts]))
    if len(pts) < 2:
        return None
    return pts[0], pts[-1]


# ============================================================================
# 7. 匾额、楹联
# ============================================================================
def build_plaques(coll, M):
    y = WALL_Y - 0.24
    a = MeshAccum()
    a.box((0, y, G + 3.72), (3.36, 0.15, 0.78))
    a.box((0, y - 0.085, G + 3.72), (3.14, 0.05, 0.64))
    a.finish("匾额_底板", M["plaque"], coll, bevel=0.015)
    a = MeshAccum()
    a.box2(-1.63, 1.63, y - 0.11, y - 0.065, G + 4.07, G + 4.12)
    a.box2(-1.63, 1.63, y - 0.11, y - 0.065, G + 3.32, G + 3.37)
    a.box2(-1.63, -1.57, y - 0.11, y - 0.065, G + 3.37, G + 4.07)
    a.box2(1.57, 1.63, y - 0.11, y - 0.065, G + 3.37, G + 4.07)
    a.finish("匾额_边框", M["gold"], coll)
    make_text("保國寺", 0.60, M["gold"], coll, "匾额_文字",
              loc=(0, y - 0.13, G + 3.72), extrude=0.026, spacing=1.22)

    # 楹联（明间两侧柱前）
    for x, txt in ((-COL_X[1], "莊嚴結十方緣"), (COL_X[1], "精進開先覺路")):
        a = MeshAccum()
        yy = WALL_Y - 0.28
        a.box2(x - 0.15, x + 0.15, yy - 0.07, yy + 0.03, G + 1.30, G + 3.80)
        a.finish(f"楹联_{txt[:2]}", M["plaque"], coll, bevel=0.01)
        make_text("\n".join(txt), 0.185, M["gold"], coll, f"楹联文_{txt[:2]}",
                  loc=(x, yy - 0.08, G + 2.52), extrude=0.016, spacing=0.92,
                  rot=(math.pi / 2, 0, 0))


# ============================================================================
# 8. 两侧白墙 + 拱券门
# ============================================================================
def build_side_walls(coll, M):
    for sx in (-1, 1):
        x_in = COL_X[0] if sx < 0 else COL_X[-1]
        x_out = sx * 11.60
        lo, hi = min(x_in, x_out), max(x_in, x_out)
        cx = (lo + hi) / 2
        w = hi - lo
        h = 3.95
        dx = sx * 8.40
        aw = 0.62
        az = 2.02

        # 墙身（扣出拱门洞）
        a = MeshAccum()
        a.box2(lo, dx - aw, WALL_Y - 0.28, WALL_Y + 0.28, 0, h)
        a.box2(dx + aw, hi, WALL_Y - 0.28, WALL_Y + 0.28, 0, h)
        a.box2(dx - aw, dx + aw, WALL_Y - 0.28, WALL_Y + 0.28, az + aw, h)
        a.finish(f"白墙_{'东西'[sx > 0]}", M["plaster"], coll, bevel=0.008)

        # 石基
        a = MeshAccum()
        a.box2(lo, dx - aw, WALL_Y - 0.32, WALL_Y + 0.32, 0, 0.55)
        a.box2(dx + aw, hi, WALL_Y - 0.32, WALL_Y + 0.32, 0, 0.55)
        a.finish(f"白墙石基_{'东西'[sx > 0]}", M["stone"], coll, bevel=0.008)

        # 瓦顶（两坡）+ 脊
        a = MeshAccum()
        nrib = int(w / 0.30)
        for s2 in (-1, 1):
            for i in range(nrib):
                xx0 = cx - (w + 0.3) / 2 + (i + 0.5) * (w + 0.3) / nrib
                a.box((xx0, WALL_Y + s2 * 0.42, h + 0.31), (0.13, 1.02, 0.11),
                      M=Matrix.Rotation(-s2 * math.radians(20), 4, 'X'))
            a.box((cx, WALL_Y + s2 * 0.42, h + 0.24), (w + 0.3, 1.05, 0.10),
                  M=Matrix.Rotation(-s2 * math.radians(20), 4, 'X'))
        a.finish(f"白墙瓦顶_{'东西'[sx > 0]}", M["tile"], coll)
        a = MeshAccum()
        a.box2(cx - (w + 0.3) / 2, cx + (w + 0.3) / 2, WALL_Y - 0.10, WALL_Y + 0.10,
               h + 0.46, h + 0.60)
        a.finish(f"白墙脊_{'东西'[sx > 0]}", M["tile_dark"], coll, bevel=0.008)

        # 门洞内暗部 + 券顶
        a = MeshAccum()
        a.box2(dx - aw + 0.02, dx + aw - 0.02, WALL_Y + 0.10, WALL_Y + 0.60, 0, az + aw)
        a.cyl((dx, WALL_Y + 0.35, az), aw - 0.02, 0.50, seg=20,
              M=Matrix.Rotation(math.pi / 2, 4, 'X'))
        a.finish(f"拱门_洞_{'东西'[sx > 0]}", M["dark"], coll)

        # 券脸石
        a = MeshAccum()
        for i in range(21):
            ang = math.pi * i / 20
            a.box((dx + (aw + 0.06) * math.cos(ang), WALL_Y - 0.29,
                   az + (aw + 0.06) * math.sin(ang)),
                  (0.14, 0.09, 0.13), M=Matrix.Rotation(ang, 4, 'Y'))
        for s2 in (-1, 1):
            a.box2(dx + s2 * (aw + 0.02), dx + s2 * (aw + 0.17),
                   WALL_Y - 0.30, WALL_Y - 0.24, 0, az)
        a.finish(f"拱门_券脸_{'东西'[sx > 0]}", M["stone"], coll, bevel=0.006)

        if sx < 0:
            # 西侧：红色板门（虚掩）
            a = MeshAccum()
            a.box2(dx - aw + 0.03, dx + 0.02, WALL_Y + 0.02, WALL_Y + 0.10, 0.04, az + aw - 0.06)
            a.cyl((dx - 0.01, WALL_Y + 0.45, az), aw - 0.03, 0.16, seg=20,
                  M=Matrix.Rotation(math.pi / 2, 4, 'X'))
            a.finish("拱门_红门", M["door_red"], coll, bevel=0.008)


# ============================================================================
# 9. 环境
# ============================================================================
def build_env(coll, M):
    a = MeshAccum()
    a.box2(-2000, 2000, -2000, 2000, -0.30, 0.0)
    a.finish("庭院地面", M["ground"], coll)

    # 前庭大石板
    a = MeshAccum()
    xx = -12.0
    while xx < 12.0:
        yy = -26.0
        while yy < -8.6:
            w = random.uniform(2.0, 3.2)
            d = random.uniform(1.3, 2.0)
            a.box2(xx + 0.03, min(xx + w, 12.0) - 0.03,
                   yy + 0.03, min(yy + d, -8.6) - 0.03, -0.02, 0.035)
            yy += d
        xx += 2.4
    a.finish("前庭石板", M["stone"], coll)

    # 门后庭院（避免透出天空）
    a = MeshAccum()
    a.box2(-8.0, 8.0, 11.0, 11.5, 0, 4.6)
    a.finish("门后院墙", M["plaster"], coll, bevel=0.01)
    a = MeshAccum()
    a.box2(-8.2, 8.2, 10.8, 11.7, 4.6, 4.9)
    a.finish("门后院墙瓦顶", M["tile_dark"], coll)
    a = MeshAccum()
    a.box2(-8.0, 8.0, 3.2, 11.0, G - 0.02, G + 0.02)
    a.finish("门后地面", M["paving"], coll)

    # 门内庭院（透景）
    a = MeshAccum()
    a.box2(-2.2, 2.2, COL_Y[-1] + 0.6, COL_Y[-1] + 6.0, G, G + 0.04)
    a.finish("门内地面", M["paving"], coll)
    a = MeshAccum()
    for i, (x, y, s) in enumerate(((-0.85, 5.2, 1.0), (0.55, 6.0, 0.85), (1.35, 4.9, 0.65))):
        a.cyl((x, y, G + s * 0.5), s * 0.7, s * 1.2, seg=10, rtop=s * 0.35)
    a.finish("门内山石", M["rock"], coll, smooth=True)
    a = MeshAccum()
    for i in range(34):
        x = random.uniform(-2.8, 2.8)
        y = random.uniform(5.2, 9.0)
        r = random.uniform(0.26, 0.48)
        a.cyl((x, y, G + 0.45 + random.uniform(0, 1.1)), r, r * 1.1, seg=8, rtop=r * 0.4)
    a.finish("门内绿植", M["leaf"], coll, smooth=True)

    # 门后暗背景
    a = MeshAccum()
    a.box2(-4.0, 4.0, 9.2, 9.5, G - 0.1, G + 5.2)
    a.finish("门后暗板", M["dark"], coll)

    # 穿堂顶部暗板
    a = MeshAccum()
    a.box2(-2.2, 2.2, 0.0, 3.2, G + 3.30, G + 3.36)
    a.finish("穿堂顶", M["dark"], coll)

    # 树
    def tree(x, y, h, r, seed):
        rnd = random.Random(seed)
        a = MeshAccum()
        a.cyl((x, y, h * 0.32), 0.30, h * 0.64, seg=8, rtop=0.18)
        a.finish(f"树干_{seed}", M["trunk"], coll)
        a = MeshAccum()
        for k in range(34):
            ang = rnd.uniform(0, TAU)
            rad = r * rnd.uniform(0.1, 1.0)
            cx = x + math.cos(ang) * rad
            cy = y + math.sin(ang) * rad * 0.85
            cz = h * 0.62 + rnd.uniform(-0.2, 0.4) * h * 0.4 + (1 - rad / r) * 0.5
            rr = r * rnd.uniform(0.16, 0.30)
            a.cyl((cx, cy, cz), rr, rr * 1.05, seg=8, rtop=rr * 0.45)
        a.finish(f"树冠_{seed}", M["leaf"], coll, smooth=True)

    for i, (x, y, h, r) in enumerate(((-3.4, 12.0, 12, 3.4), (3.6, 13.0, 13, 3.6),
                                      (-9.5, 14.0, 12, 3.2), (9.8, 15.0, 13, 3.4),
                                      (-16, 20, 15, 4.0), (16, 21, 15, 3.8))):
        tree(x, y, h, r, i)
