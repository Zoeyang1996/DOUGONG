# -*- coding: utf-8 -*-
"""保国寺大殿 · 建筑构件生成
坐标：X 面阔方向，Y 进深方向（-Y 为正面/南），Z 向上，单位米
"""
import bpy, math, random
from mathutils import Vector, Matrix
from temple_core import (MeshAccum, hx, lerp, smoothstep, TAU, mat_simple,
                         mat_wood, mat_surface, mat_tile, mat_gold,
                         mat_paving, make_text, FONT_CALLI, recalc)

# ============================================================================
# 全局尺度（宋式殿堂，面阔五间、进深三间、重檐歇山）
# ============================================================================
P = dict(
    plat_x=13.0, plat_y=8.2, plat_h=1.40,        # 台基
    col_x=[-10.6, -6.36, -2.12, 2.12, 6.36, 10.6],
    col_y=[-6.6, -2.2, 2.2, 6.6],
    col_h=5.86,                                   # 檐柱高
    col_r=0.40,
    lane_h=0.52,                                  # 阑额高
    pupai_h=0.16,                                 # 普拍枋
    doug_h=1.15,                                  # 斗拱层高
    # 下檐（腰檐）
    low_ai=9.30, low_bi=5.78, low_ao=12.95, low_bo=9.00,
    low_zin=11.00, low_zout=9.36,
    # 上檐（歇山）
    up_a=10.85, up_b=7.28, up_xr=8.35, up_H=4.20,
    up_z0=13.50, up_lift=1.42,
    # 上层墙
    up_wall_z0=10.95, up_wall_z1=12.10,
)
G = P["plat_h"]
COL_BASE = G + 0.42
COL_TOP = COL_BASE + P["col_h"]
LANE_TOP = COL_TOP + P["lane_h"]
PUPAI_TOP = LANE_TOP + P["pupai_h"]
DOUG_TOP = PUPAI_TOP + P["doug_h"]
DOUG_ROOF = DOUG_TOP + 0.10          # 撩檐枋顶
UP_DOUG_TOP = P["up_wall_z1"] + P["doug_h"]
TIAO = 1.25                          # 斗拱出跳（撩檐枋位置）


# ============================================================================
# 1. 台基
# ============================================================================
def build_platform(coll, M):
    px, py, ph = P["plat_x"], P["plat_y"], P["plat_h"]
    # 主体（须弥座简化：上下枋 + 束腰）
    a = MeshAccum()
    a.box((0, 0, ph * 0.5), (px * 2, py * 2, ph))
    a.finish("台基_主体", M["stone_dark"], coll, bevel=0.012)

    # 阶条石：外圈压面石
    a = MeshAccum()
    w, t = 0.62, 0.26
    step = 1.15
    n = int(px * 2 / step)
    for i in range(n):
        x0 = -px + i * (px * 2 / n)
        x1 = x0 + px * 2 / n - 0.03
        a.box2(x0, x1, -py, -py + w, ph - t, ph + 0.01)   # 前
        a.box2(x0, x1, py - w, py, ph - t, ph + 0.01)     # 后
    m = int(py * 2 / step)
    for i in range(m):
        y0 = -py + i * (py * 2 / m)
        y1 = y0 + py * 2 / m - 0.03
        a.box2(-px, -px + w, y0, y1, ph - t, ph + 0.01)
        a.box2(px - w, px, y0, y1, ph - t, ph + 0.01)
    a.finish("台基_阶条石", M["stone"], coll, bevel=0.008)

    # 台面铺地
    a = MeshAccum()
    a.box2(-px + 0.5, px - 0.5, -py + 0.5, py - 0.5, ph - 0.12, ph + 0.005)
    a.finish("台基_台面", M["paving"], coll)

    # 踏跺（中 + 两侧）
    def stairs(cx, width, y_out, n_step=8, name="踏跺"):
        a = MeshAccum()
        rise = ph / n_step
        run = 0.40
        for i in range(n_step):
            z1 = ph - i * rise
            z0 = z1 - rise
            y1 = -py - i * run
            y0 = y1 - run
            a.box2(cx - width / 2, cx + width / 2, y0, y1, z0 - 0.10, z1)
        # 垂带石
        for sd in (-1, 1):
            xx = cx + sd * (width / 2 + 0.20)
            p0 = (xx, -py, ph + 0.14)
            p1 = (xx, -py - run * n_step, 0.14)
            rings = []
            for (yy, zz) in ((p0[1], p0[2]), (p1[1], p1[2])):
                rings.append([(xx - 0.22, yy, zz + 0.10), (xx + 0.22, yy, zz + 0.10),
                              (xx + 0.22, yy, zz - 0.28), (xx - 0.22, yy, zz - 0.28)])
            a.loft(rings, closed_profile=True, cap_ends=True)
        a.finish(name, M["stone"], coll, bevel=0.01)

    stairs(0.0, 5.4, -py, name="踏跺_正中")
    stairs(-9.9, 2.6, -py, name="踏跺_西侧")
    stairs(9.9, 2.6, -py, name="踏跺_东侧")

    # 柱础
    a = MeshAccum()
    for x in P["col_x"]:
        for y in (P["col_y"][0], P["col_y"][-1]):
            a.box((x, y, ph + 0.11), (0.98, 0.98, 0.22))
            a.frustum((x, y, ph + 0.30), (0.92, 0.92), (0.68, 0.68), 0.16)
            a.cyl((x, y, ph + 0.40), 0.40, 0.10, seg=24)
    for y in P["col_y"][1:-1]:
        for x in (P["col_x"][0], P["col_x"][-1]):
            a.box((x, y, ph + 0.11), (0.98, 0.98, 0.22))
            a.frustum((x, y, ph + 0.30), (0.92, 0.92), (0.68, 0.68), 0.16)
            a.cyl((x, y, ph + 0.40), 0.40, 0.10, seg=24)
    a.finish("柱础", M["stone"], coll, bevel=0.015)


# ============================================================================
# 2. 柱网与额枋
# ============================================================================
def build_columns(coll, M):
    acc = MeshAccum()
    h = P["col_h"]
    for x in P["col_x"]:
        for y in (P["col_y"][0], P["col_y"][-1]):
            acc.cyl((x, y, COL_BASE + h / 2), P["col_r"], h, seg=28, rtop=P["col_r"] * 0.92)
    for y in P["col_y"][1:-1]:
        for x in (P["col_x"][0], P["col_x"][-1]):
            acc.cyl((x, y, COL_BASE + h / 2), P["col_r"], h, seg=28, rtop=P["col_r"] * 0.92)
    # 内柱（可见柱列）
    for x in (-2.12, 2.12):
        for y in (-2.2, 2.2):
            acc.cyl((x, y, COL_BASE + h / 2), P["col_r"] * 1.05, h, seg=28,
                    rtop=P["col_r"] * 0.88)
    acc.finish("檐柱", M["wood_red"], coll, smooth=False)

    # 柱头箍
    a = MeshAccum()
    for x in P["col_x"]:
        for y in (P["col_y"][0], P["col_y"][-1]):
            a.cyl((x, y, COL_TOP - 0.28), P["col_r"] * 0.955, 0.06, seg=24)
    a.finish("柱箍", M["wood_dark"], coll)

    # 阑额 / 普拍枋 / 地栿
    a = MeshAccum()
    z0 = COL_TOP
    fz = P["col_y"][0]
    # 前后檐
    for y in (P["col_y"][0], P["col_y"][-1]):
        for i in range(len(P["col_x"]) - 1):
            x0, x1 = P["col_x"][i], P["col_x"][i + 1]
            a.box2(x0 + 0.05, x1 - 0.05, y - 0.13, y + 0.13, z0, z0 + P["lane_h"])
    # 山面
    for x in (P["col_x"][0], P["col_x"][-1]):
        for i in range(len(P["col_y"]) - 1):
            y0, y1 = P["col_y"][i], P["col_y"][i + 1]
            a.box2(x - 0.13, x + 0.13, y0 + 0.05, y1 - 0.05, z0, z0 + P["lane_h"])
    a.finish("阑额", M["wood_red"], coll, bevel=0.012)

    a = MeshAccum()
    for y in (P["col_y"][0], P["col_y"][-1]):
        a.box2(P["col_x"][0] - 0.3, P["col_x"][-1] + 0.3, y - 0.26, y + 0.26,
               LANE_TOP, LANE_TOP + P["pupai_h"])
    for x in (P["col_x"][0], P["col_x"][-1]):
        a.box2(x - 0.26, x + 0.26, P["col_y"][0] - 0.3, P["col_y"][-1] + 0.3,
               LANE_TOP, LANE_TOP + P["pupai_h"])
    a.finish("普拍枋", M["wood_red"], coll, bevel=0.01)

    # 地栿
    a = MeshAccum()
    for y in (P["col_y"][0], P["col_y"][-1]):
        for i in range(len(P["col_x"]) - 1):
            x0, x1 = P["col_x"][i], P["col_x"][i + 1]
            a.box2(x0, x1, y - 0.12, y + 0.12, G + 0.02, G + 0.20)
    a.finish("地栿", M["wood_dark"], coll, bevel=0.01)

    # 内部梁架（隐约可见）
    a = MeshAccum()
    for x in (-6.36, -2.12, 2.12, 6.36):
        a.box2(x - 0.18, x + 0.18, -6.6, 6.6, COL_TOP - 0.7, COL_TOP - 0.45)
    a.finish("内梁架", M["wood_dark"], coll)


# ============================================================================
# 3. 斗拱（五铺作双下昂，柱头铺作 / 补间铺作）
# ============================================================================
def dougong_module(acc, M, scale=1.0):
    """五铺作双下昂斗拱：+Y 出跳，Z 向上，原点在栌斗底面中心，总高约 1.15"""
    s = scale

    def B(c, sz):
        acc.box((c[0] * s, c[1] * s, c[2] * s), (sz[0] * s, sz[1] * s, sz[2] * s), M)

    # 栌斗
    acc.frustum((0, 0, 0.12 * s), (0.44 * s, 0.44 * s), (0.66 * s, 0.66 * s), 0.24 * s, M)
    B((0, 0, 0.29), (0.66, 0.66, 0.10))
    # 泥道拱（横）+ 华拱第一跳（出）
    B((0, 0, 0.46), (1.16, 0.19, 0.24))
    B((0, 0.24, 0.46), (0.19, 0.86, 0.24))
    # 散斗
    for sx in (-0.54, 0.54):
        B((sx, 0, 0.66), (0.28, 0.24, 0.16))
    B((0, 0.60, 0.66), (0.28, 0.28, 0.17))
    # 慢拱（第二层横拱）+ 华拱第二跳
    B((0, 0, 0.74), (1.34, 0.19, 0.22))
    B((0, 0.38, 0.76), (0.19, 0.90, 0.22))
    for sx in (-0.64, 0.64):
        B((sx, 0, 0.90), (0.28, 0.24, 0.16))
    # 下昂（斜出，昂嘴下垂）
    ang = math.radians(-17)
    L = 1.15
    Mx = Matrix.Translation(Vector((0, 0.62 * s, 0.92 * s))) @ Matrix.Rotation(ang, 4, 'X')
    acc.box((0, 0, 0), (0.19 * s, L * s, 0.24 * s), M @ Mx)
    acc.box((0, (L * 0.52) * s, -0.06 * s), (0.17 * s, 0.20 * s, 0.17 * s), M @ Mx)
    # 交互斗（昂上）
    B((0, 1.06, 0.80), (0.28, 0.28, 0.17))
    # 令拱 + 散斗
    B((0, 1.14, 0.96), (1.02, 0.19, 0.21))
    for sx in (-0.44, 0.0, 0.44):
        B((sx, 1.14, 1.08), (0.24, 0.22, 0.15))
    # 耍头
    B((0, 1.10, 0.84), (0.17, 0.46, 0.15))
    # 柱头枋
    B((0, 0.02, 0.80), (1.46, 0.22, 0.16))


def build_dougong(coll, M):
    """沿四周布置铺作：柱头铺作 + 每间一朵补间铺作"""
    rows = []
    # (轴, 固定值, 局部+Y 的朝向)，正面朝 -Y
    for y, rot in ((P["col_y"][0], math.pi), (P["col_y"][-1], 0.0)):
        rows.append(("x", y, rot))
    for x, rot in ((P["col_x"][0], math.pi / 2), (P["col_x"][-1], -math.pi / 2)):
        rows.append(("y", x, rot))

    acc = MeshAccum()
    for axis, fixed, rot in rows:
        if axis == "x":
            xs = list(P["col_x"])
            bays = []
            for i in range(5):
                a0, a1 = P["col_x"][i], P["col_x"][i + 1]
                bays += [a0 + (a1 - a0) / 3, a0 + (a1 - a0) * 2 / 3]
            xs += bays
            for x in xs:
                Mx = Matrix.Translation(Vector((x, fixed, PUPAI_TOP))) @ Matrix.Rotation(rot, 4, 'Z')
                dougong_module(acc, Mx)
        else:
            ys = list(P["col_y"])
            bays = []
            for i in range(3):
                a0, a1 = P["col_y"][i], P["col_y"][i + 1]
                bays += [a0 + (a1 - a0) / 3, a0 + (a1 - a0) * 2 / 3]
            ys += bays
            for y in ys:
                Mx = Matrix.Translation(Vector((fixed, y, PUPAI_TOP))) @ Matrix.Rotation(rot, 4, 'Z')
                dougong_module(acc, Mx)
    # 转角铺作（45° 附加）
    for x in (P["col_x"][0], P["col_x"][-1]):
        for y in (P["col_y"][0], P["col_y"][-1]):
            ux = 1.0 if x > 0 else -1.0
            uy = 1.0 if y > 0 else -1.0
            rot = math.atan2(-ux * 0.7071, uy * 0.7071)
            Mx = Matrix.Translation(Vector((x, y, PUPAI_TOP))) @ Matrix.Rotation(rot, 4, 'Z')
            dougong_module(acc, Mx, scale=1.06)
    acc.finish("斗拱_下檐", M["wood_red"], coll, bevel=0.008)

    # 撩檐枋（下檐）—— 位于令拱之上
    a = MeshAccum()
    z = DOUG_TOP - 0.12
    fy = P["col_y"][0] - TIAO
    by = P["col_y"][-1] + TIAO
    fx = P["col_x"][0] - TIAO
    bx = P["col_x"][-1] + TIAO
    a.box2(fx - 0.35, bx + 0.35, fy - 0.17, fy + 0.17, z - 0.14, z + 0.14)
    a.box2(fx - 0.35, bx + 0.35, by - 0.17, by + 0.17, z - 0.14, z + 0.14)
    a.box2(fx - 0.17, fx + 0.17, fy, by, z - 0.14, z + 0.14)
    a.box2(bx - 0.17, bx + 0.17, fy, by, z - 0.14, z + 0.14)
    a.finish("撩檐枋", M["wood_red"], coll, bevel=0.01)

    # 拱眼壁（斗拱之后的封护板）
    a = MeshAccum()
    zz0, zz1 = PUPAI_TOP - 0.02, DOUG_TOP - 0.06
    fy2, by2 = P["col_y"][0], P["col_y"][-1]
    fx2, bx2 = P["col_x"][0], P["col_x"][-1]
    a.box2(fx2 - 0.5, bx2 + 0.5, fy2 - 0.06, fy2 + 0.06, zz0, zz1)
    a.box2(fx2 - 0.5, bx2 + 0.5, by2 - 0.06, by2 + 0.06, zz0, zz1)
    a.box2(fx2 - 0.06, fx2 + 0.06, fy2 - 0.5, by2 + 0.5, zz0, zz1)
    a.box2(bx2 - 0.06, bx2 + 0.06, fy2 - 0.5, by2 + 0.5, zz0, zz1)
    a.finish("拱眼壁", M["wood_red"], coll)

    # 上檐斗拱
    acc = MeshAccum()
    for axis, fixed, rot in rows:
        if axis == "x":
            xs = [x for x in P["col_x"]]
            for i in range(5):
                a0, a1 = P["col_x"][i], P["col_x"][i + 1]
                xs += [a0 + (a1 - a0) / 3, a0 + (a1 - a0) * 2 / 3]
            for x in xs:
                Mx = Matrix.Translation(Vector((x, fixed * 0.88, P["up_wall_z1"]))) @ Matrix.Rotation(rot, 4, 'Z')
                dougong_module(acc, Mx, scale=0.92)
        else:
            ys = [y for y in P["col_y"]]
            for i in range(3):
                a0, a1 = P["col_y"][i], P["col_y"][i + 1]
                ys += [a0 + (a1 - a0) / 3, a0 + (a1 - a0) * 2 / 3]
            for y in ys:
                Mx = Matrix.Translation(Vector((fixed * 0.88, y, P["up_wall_z1"]))) @ Matrix.Rotation(rot, 4, 'Z')
                dougong_module(acc, Mx, scale=0.92)
    acc.finish("斗拱_上檐", M["wood_red"], coll, bevel=0.008)

    a = MeshAccum()
    z = UP_DOUG_TOP - 0.10
    ty = TIAO * 0.92
    fy, by = P["col_y"][0] * 0.88 - ty, P["col_y"][-1] * 0.88 + ty
    fx, bx = P["col_x"][0] * 0.88 - ty, P["col_x"][-1] * 0.88 + ty
    a.box2(fx - 0.3, bx + 0.3, fy - 0.16, fy + 0.16, z - 0.13, z + 0.13)
    a.box2(fx - 0.3, bx + 0.3, by - 0.16, by + 0.16, z - 0.13, z + 0.13)
    a.box2(fx - 0.16, fx + 0.16, fy, by, z - 0.13, z + 0.13)
    a.box2(bx - 0.16, bx + 0.16, fy, by, z - 0.13, z + 0.13)
    a.finish("撩檐枋_上檐", M["wood_red"], coll, bevel=0.01)

    # 檐椽（圆形椽头）移动到屋面函数内，随坡生成


# ============================================================================
# 4. 屋面
# ============================================================================
def surf_hip(x, y, a, b, xr, H, z0, k=1.90, lift=0.0, lp=3.0):
    ax, ay = abs(x), abs(y)
    u, v = ax / a, ay / b
    fx = 0.0 if ax <= xr else (ax - xr) / max(1e-6, (a - xr))
    t = min(1.0, max(fx, v))
    z = z0 + H * (1 - t) ** k
    L = lift * ((u * v) ** lp)
    return z + L, L



def surf_xi(x, y, a, b, xg, H, z0, lift=0.0, k=1.70, br=0.44):
    """歇山：|x|<=xg 为悬山两坡；之外为撇山小庑殿，山花由此形成"""
    v = min(1.0, abs(y) / b)
    zg = z0 + H * (1 - v) ** k
    zb = z0 + H * br
    ystar = b * (1 - br ** (1.0 / k))
    ax = abs(x)
    if ax <= xg:
        z = zg
    else:
        t = max((ax - xg) / (a - xg), max(0.0, (abs(y) - ystar) / (b - ystar)))
        z = min(zb - (zb - z0) * (t ** 0.9), zg)
    L = lift * (((ax / a) * v) ** 3.0)
    return z + L, L


def surf_ring(x, y, ai, bi, ao, bo, zin, zout, lift, k=0.62):
    ax, ay = abs(x), abs(y)
    sx = (ax - ai) / (ao - ai)
    sy = (ay - bi) / (bo - bi)
    s = min(1.0, max(0.0, max(sx, sy)))
    z = zin - (zin - zout) * (s ** k)
    u, v = ax / ao, ay / bo
    L = lift * ((u * v) ** 3.0) * (s ** 1.1)
    return z + L, L


def cyl_between(acc, p1, p2, r, seg=10):
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    L = d.length
    if L < 1e-6:
        return
    q = d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
    acc.cyl((p1 + p2) / 2, r, L, seg=seg, M=q)



def _perimeter(a, b, n):
    """矩形周长采样，返回 (x,y) 列表"""
    pts = []
    seg = max(2, n // 4)
    for i in range(seg):
        t = i / seg
        pts.append((-a + 2 * a * t, -b))
    for i in range(seg):
        t = i / seg
        pts.append((a, -b + 2 * b * t))
    for i in range(seg):
        t = i / seg
        pts.append((a - 2 * a * t, b))
    for i in range(seg):
        t = i / seg
        pts.append((-a, b - 2 * b * t))
    return pts


def _outdir(x, y):
    ox = math.copysign(1.0, x) if abs(x) > 1e-9 else 0.0
    oy = math.copysign(1.0, y) if abs(y) > 1e-9 else 0.0
    d = Vector((ox, oy, 0.0))
    if d.length < 0.1:
        d = Vector((x, y, 0.0)).normalized()
    return d.normalized()


def eave_trim(acc, fn, pts, drop=0.17, out=0.015, thick=0.03):
    """檐口滴水带：遮住屋面板端头，形成薄檐边"""
    rings = []
    for (x, y) in pts:
        p, n = _normal(fn, x, y)
        d = _outdir(x, y)
        top = p + n * 0.02 + d * out
        bot = p - Vector((0, 0, drop)) + d * (out * 0.5)
        rings.append([tuple(top), tuple(bot),
                      tuple(bot + n * thick), tuple(top + n * thick)])
    acc.loft(rings, closed_profile=True, cap_ends=True)


def drip_tiles(acc, fn, pts, w=0.13, h=0.09):
    """滴水：瓦垄之间的三角舌片"""
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        p, n = _normal(fn, mx, my)
        d = _outdir(mx, my)
        L = Vector((x1 - x0, y1 - y0, 0)).normalized() * (w * 0.5)
        base = p - Vector((0, 0, 0.02)) + d * 0.10
        o = len(acc.v)
        acc.v += [tuple(base - L + n * 0.01), tuple(base + L + n * 0.01),
                  tuple(base + (L * 0.25) - Vector((0, 0, h)) + d * 0.05),
                  tuple(base - (L * 0.25) - Vector((0, 0, h)) + d * 0.05)]
        acc.f += [(o, o + 1, o + 2, o + 3)]


def tile_caps(acc, fn, pts, r=0.084):
    """瓦当：檐口每个瓦垄端头的圆瓦头"""
    for (x, y) in pts:
        p, n = _normal(fn, x, y)
        d = _outdir(x, y)
        c = p + n * (r * 0.30) + d * (r * 1.05)
        cyl_between(acc, c - d * 0.04, c + d * 0.05, r)


def _normal(fn, x, y, e=0.06):
    z = fn(x, y)[0]
    dx = (fn(x + e, y)[0] - fn(x - e, y)[0]) / (2 * e)
    dy = (fn(x, y + e)[0] - fn(x, y - e)[0]) / (2 * e)
    return Vector((x, y, z)), Vector((-dx, -dy, 1.0)).normalized()


def make_roof_slab(coll, M, name, a, b, fn, mat_top, mat_under, nx=150, ny=110,
                   thick=0.34, flare=0.22):
    """高度场屋面板 + 起翘外扩"""
    verts, faces = [], []
    for j in range(ny + 1):
        y = -b + 2 * b * j / ny
        for i in range(nx + 1):
            x = -a + 2 * a * i / nx
            z, L = fn(x, y)
            xx = x + math.copysign(1.0, x) * L * flare if abs(x) > 1e-6 else x
            yy = y + math.copysign(1.0, y) * L * flare if abs(y) > 1e-6 else y
            verts.append((xx, yy, z))
    for j in range(ny):
        for i in range(nx):
            p = j * (nx + 1) + i
            faces.append((p, p + 1, p + nx + 2, p + nx + 1))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    me.materials.append(mat_top)
    me.materials.append(mat_under)

    md = ob.modifiers.new("厚度", 'SOLIDIFY')
    md.thickness = thick
    md.offset = -1.0
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.modifier_apply(modifier=md.name)
    ob.select_set(False)
    for p in me.polygons:
        if p.normal.z < -0.35:
            p.material_index = 1
        p.use_smooth = True
    return ob


def rib_fan(acc, fn, outers, inner_fn, samples=34, r=0.085, seg=7, cap=False):
    """从檐口沿坡向铺瓦垄（筒瓦）"""
    for Q in outers:
        I = inner_fn(Q[0], Q[1])
        rings = []
        for i in range(samples + 1):
            t = i / samples
            x = lerp(I[0], Q[0], t)
            y = lerp(I[1], Q[1], t)
            p, n = _normal(fn, x, y)
            T = Vector((Q[0] - I[0], Q[1] - I[1], 0))
            if T.length < 1e-6:
                T = Vector((1, 0, 0))
            T.normalize()
            B = T.cross(Vector((0, 0, 1))).normalized()
            c = p + n * r * 0.35
            ring = []
            for k in range(seg + 1):
                th = math.pi * k / seg
                ring.append(tuple(c + B * (r * math.cos(th)) + n * (r * math.sin(th))))
            rings.append(ring)
        acc.loft(rings, closed_profile=False, cap_ends=False)


def corner_beast(acc, M, p, d, s=1.0):
    """翼角套兽（小兽头，扣在角梁端）"""
    px, py, pz = p
    acc.box((px, py, pz + 0.06 * s), (0.30 * s, 0.30 * s, 0.20 * s))
    acc.box((px + d[0] * 0.06, py + d[1] * 0.06, pz + 0.19 * s),
            (0.22 * s, 0.22 * s, 0.16 * s))
    acc.box((px + d[0] * 0.13, py + d[1] * 0.13, pz + 0.14 * s),
            (0.13 * s, 0.13 * s, 0.13 * s))


def build_low_roof(coll, M):
    ai, bi, ao, bo = P["low_ai"], P["low_bi"], P["low_ao"], P["low_bo"]
    zin, zout = P["low_zin"], P["low_zout"]
    lift = 1.38
    fn = lambda x, y: surf_ring(x, y, ai, bi, ao, bo, zin, zout, lift)
    make_roof_slab(coll, M, "下檐_屋面板", ao, bo, fn, M["tile"], M["wood_dark"],
                   nx=170, ny=120, thick=0.15, flare=0.30)

    # 瓦垄
    acc = MeshAccum()
    outers = []
    spacing = 0.31
    for edge in range(4):
        if edge == 0 or edge == 1:
            L = 2 * ao
            n = int(L / spacing)
            for i in range(n):
                x = -ao + (i + 0.5) * L / n
                outers.append((x, -bo if edge == 0 else bo))
        else:
            L = 2 * bo
            n = int(L / spacing)
            for i in range(n):
                y = -bo + (i + 0.5) * L / n
                outers.append((-ao if edge == 2 else ao, y))

    def inner_proj(x, y):
        t = min(ai / abs(x) if abs(x) > 1e-6 else 9e9,
                bi / abs(y) if abs(y) > 1e-6 else 9e9)
        return (x * t, y * t)

    rib_fan(acc, fn, outers, inner_proj, samples=26, r=0.082)
    acc.finish("下檐_瓦垄", M["tile"], coll, smooth=True)

    # 瓦当 + 滴水带
    a = MeshAccum()
    tile_caps(a, fn, outers)
    a.finish("下檐_瓦当", M["tile_light"], coll)

    a = MeshAccum()
    eave_trim(a, fn, _perimeter(ao, bo, 200))
    a.finish("下檐_滴水", M["tile_dark"], coll)


    # 檐椽（沿坡露头）
    a = MeshAccum()
    n = 44
    for sy in (-1, 1):
        for i in range(n):
            x = -11.6 + i * (23.2 / (n - 1))
            y1 = sy * (bo - 0.12)
            y2 = sy * (bi + 1.60)
            cyl_between(a, (x, y1, fn(x, y1)[0] - 0.26),
                        (x, y2, fn(x, y2)[0] - 0.32), 0.072)
    for sx in (-1, 1):
        for i in range(30):
            y = -7.9 + i * (15.8 / (n - 1))
            x1 = sx * (ao - 0.12)
            x2 = sx * (ai + 1.60)
            cyl_between(a, (x1, y, fn(x1, y)[0] - 0.26),
                        (x2, y, fn(x2, y)[0] - 0.32), 0.072)
    a.finish("下檐_檐椽", M["wood_dark"], coll)

    # 翼角（角梁 + 套兽）
    a = MeshAccum()
    for sx in (-1, 1):
        for sy in (-1, 1):
            pts = []
            for i in range(9):
                t = i / 8
                x = sx * lerp(ao, ai * 0.92, t)
                y = sy * lerp(bo, bi * 0.92, t)
                z = fn(x, y)[0] - 0.12
                pts.append((x, y, z))
            rings = []
            for p in pts:
                rings.append([(p[0] + 0.16, p[1] - 0.16, p[2]),
                              (p[0] - 0.16, p[1] + 0.16, p[2]),
                              (p[0] - 0.16, p[1] + 0.16, p[2] - 0.30),
                              (p[0] + 0.16, p[1] - 0.16, p[2] - 0.30)])
            a.loft(rings, closed_profile=True, cap_ends=True)
    a.finish("下檐_角梁", M["wood_red"], coll, bevel=0.01)




def build_up_roof(coll, M):
    a_, b_, xr = P["up_a"], P["up_b"], P["up_xr"]
    H, z0, lift = P["up_H"], P["up_z0"], P["up_lift"]
    fn = lambda x, y: surf_xi(x, y, a_, b_, xr, H, z0, lift=lift)

    make_roof_slab(coll, M, "上檐_屋面板", a_, b_, fn, M["tile"], M["wood_dark"],
                   nx=180, ny=130, thick=0.15, flare=0.26)

    acc = MeshAccum()
    outers = []
    spacing = 0.31
    for edge in range(4):
        if edge < 2:
            L = 2 * a_
            n = int(L / spacing)
            for i in range(n):
                x = -a_ + (i + 0.5) * L / n
                outers.append((x, -b_ if edge == 0 else b_))
        else:
            L = 2 * b_
            n = int(L / spacing)
            for i in range(n):
                y = -b_ + (i + 0.5) * L / n
                outers.append((-a_ if edge == 2 else a_, y))

    br_ = 0.44
    ystar_ = b_ * (1 - br_ ** (1.0 / 1.70))

    def ridge_proj(x, y):
        if abs(x) <= xr:
            return (x, 0.0)
        return (math.copysign(xr - 0.05, x), max(-ystar_, min(ystar_, y)))

    rib_fan(acc, fn, outers, ridge_proj, samples=40, r=0.082)
    acc.finish("上檐_瓦垄", M["tile"], coll, smooth=True)

    # 瓦当 + 滴水带
    a = MeshAccum()
    tile_caps(a, fn, outers)
    a.finish("上檐_瓦当", M["tile_light"], coll)

    a = MeshAccum()
    eave_trim(a, fn, _perimeter(a_, b_, 180))
    a.finish("上檐_滴水", M["tile_dark"], coll)


    # 上檐檐椽
    a = MeshAccum()
    n = 44
    for sy in (-1, 1):
        for i in range(n):
            x = -10.2 + i * (20.4 / (n - 1))
            y1 = sy * (b_ - 0.12)
            y2 = sy * (b_ - 1.85)
            cyl_between(a, (x, y1, fn(x, y1)[0] - 0.26),
                        (x, y2, fn(x, y2)[0] - 0.40), 0.070)
    for sx in (-1, 1):
        for i in range(26):
            y = -6.6 + i * (13.2 / 25)
            x1 = sx * (a_ - 0.12)
            x2 = sx * (a_ - 1.85)
            cyl_between(a, (x1, y, fn(x1, y)[0] - 0.26),
                        (x2, y, fn(x2, y)[0] - 0.40), 0.070)
    a.finish("上檐_檐椽", M["wood_dark"], coll)

    # 山花（竖板）+ 博风板
    br = 0.44
    zb = z0 + H * br
    ystar = b_ * (1 - br ** (1.0 / 1.90))
    a2 = MeshAccum()
    ns = 22
    for sx in (-1, 1):
        x = sx * (xr - 0.02)
        top, bot = [], []
        for i in range(ns + 1):
            y = -ystar + 2 * ystar * i / ns
            v = min(1.0, abs(y) / b_)
            top.append((x, y, z0 + H * (1 - v) ** 1.70))
            bot.append((x, y, zb))
        o = len(a2.v)
        a2.v.extend(top)
        a2.v.extend(bot)
        for i in range(ns):
            if sx > 0:
                a2.f.append((o + i, o + i + 1, o + ns + 1 + i + 1, o + ns + 1 + i))
            else:
                a2.f.append((o + i, o + ns + 1 + i, o + ns + 1 + i + 1, o + i + 1))
        # 博风板（沿山花上缘，外凸）
        for i in range(ns):
            p0 = Vector(top[i])
            p1 = Vector(top[i + 1])
            o2 = len(a2.v)
            a2.v += [(p0.x + sx * 0.06, p0.y, p0.z + 0.02),
                     (p1.x + sx * 0.06, p1.y, p1.z + 0.02),
                     (p1.x + sx * 0.06, p1.y, p1.z - 0.30),
                     (p0.x + sx * 0.06, p0.y, p0.z - 0.30),
                     (p0.x - sx * 0.02, p0.y, p0.z - 0.30),
                     (p1.x - sx * 0.02, p1.y, p1.z - 0.30)]
            a2.f += [(o2, o2 + 1, o2 + 2, o2 + 3), (o2 + 3, o2 + 2, o2 + 5, o2 + 4)]
    a2.finish("山花博风", M["wood_red_dark"], coll)

    # 悬鱼
    a = MeshAccum()
    for sx in (-1, 1):
        Mx = Matrix.Translation(Vector((sx * (xr - 0.16), 0, z0 + H - 0.60)))
        a.cyl((0, 0, 0), 0.22, 0.05, seg=16, M=Mx @ Matrix.Rotation(math.pi / 2, 4, 'Y'))
    a.finish("悬鱼", M["wood_red_dark"], coll)


# ============================================================================
# 5. 脊饰
# ============================================================================
def sweep(acc, pts, prof, up=(0, 0, 1)):
    rings = []
    n = len(pts)
    for i, p in enumerate(pts):
        if i == 0:
            T = Vector(pts[1]) - Vector(pts[0])
        elif i == n - 1:
            T = Vector(pts[-1]) - Vector(pts[-2])
        else:
            T = Vector(pts[i + 1]) - Vector(pts[i - 1])
        T.normalize()
        U = Vector(up)
        L = T.cross(U)
        if L.length < 1e-5:
            L = Vector((1, 0, 0))
        L.normalize()
        V = L.cross(T).normalized()
        rings.append([tuple(Vector(p) + L * a + V * b) for (a, b) in prof])
    acc.loft(rings, closed_profile=True, cap_ends=True)


def ridge_profile(w, h):
    return [(-w / 2, -0.05), (-w / 2, h * 0.55), (-w * 0.30, h),
            (w * 0.30, h), (w / 2, h * 0.55), (w / 2, -0.05)]


def chiwen(acc, M, x, y, z, s=1.0, flip=1):
    """鸱吻（吻座 + 卷尾）"""
    acc.box((x, y, z + 0.30 * s), (0.78 * s, 0.46 * s, 0.62 * s))
    acc.box((x, y, z + 0.64 * s), (0.60 * s, 0.40 * s, 0.26 * s))
    pts = []
    for i in range(13):
        t = i / 12
        ang = -0.30 + t * 2.30
        rr = 1.34 - 0.66 * t
        px = flip * (rr * math.sin(ang) * 0.50)
        pz = 0.62 + rr * (1 - math.cos(ang)) * 0.86
        pts.append((x + px * s, y, z + pz * s))
    prof = [(0.13 * s * math.cos(a), 0.21 * s * math.sin(a) + 0.05 * s)
            for a in [k * TAU / 8 for k in range(8)]]
    sweep(acc, pts, prof)
    # 吻背小鳍
    for i in range(4):
        t = 0.25 + i * 0.16
        ang = -0.30 + t * 2.30
        rr = 1.34 - 0.66 * t
        acc.box((x + flip * rr * math.sin(ang) * 0.50 * s,
                 y, z + (0.62 + rr * (1 - math.cos(ang)) * 0.86) * s),
                (0.10 * s, 0.24 * s, 0.20 * s))


def build_ridges(coll, M):
    a_, b_, xr = P["up_a"], P["up_b"], P["up_xr"]
    H, z0, lift = P["up_H"], P["up_z0"], P["up_lift"]
    fn = lambda x, y: surf_xi(x, y, a_, b_, xr, H, z0, lift=lift)
    zr = z0 + H

    # 正脊
    a = MeshAccum()
    pts = [(-xr, 0, zr - 0.06), (0, 0, zr + 0.02), (xr, 0, zr - 0.06)]
    sweep(a, pts, ridge_profile(0.92, 0.54))
    a.finish("正脊", M["tile_dark"], coll, bevel=0.014)

    a = MeshAccum()
    sweep(a, [(p[0], p[1], p[2] + 0.52) for p in pts], ridge_profile(0.58, 0.30))
    a.finish("正脊_瓦条", M["tile_dark"], coll, bevel=0.01)

    # 鸱吻
    a = MeshAccum()
    for sx in (-1, 1):
        chiwen(a, M, sx * (xr + 0.02), 0, zr - 0.16, s=1.45, flip=sx)
    a.finish("鸱吻", M["tile_dark"], coll, bevel=0.01)

    # 垂脊（四条）
    a = MeshAccum()
    for sx in (-1, 1):
        for sy in (-1, 1):
            pts = []
            for i in range(16):
                t = i / 15
                y = sy * b_ * (1 - t * 0.999)
                x = sx * lerp(a_, xr, t)
                z = fn(x, y)[0] + 0.02
                pts.append((x, y, z))
            sweep(a, pts, ridge_profile(0.46, 0.34))
            # 走兽
            for k in range(4):
                t = 0.03 + k * 0.055
                y = sy * b_ * (1 - t)
                x = sx * lerp(a_, xr, t)
                z = fn(x, y)[0] + 0.40
                a.box((x, y, z), (0.22, 0.20, 0.30))
    a.finish("垂脊走兽", M["tile_dark"], coll, bevel=0.012)

    # 下檐戗脊
    ai, bi, ao, bo = P["low_ai"], P["low_bi"], P["low_ao"], P["low_bo"]
    zin, zout = P["low_zin"], P["low_zout"]
    f2 = lambda x, y: surf_ring(x, y, ai, bi, ao, bo, zin, zout, 1.38)
    a = MeshAccum()
    for sx in (-1, 1):
        for sy in (-1, 1):
            pts = []
            for i in range(12):
                t = i / 11
                x = sx * lerp(ao, ai, t)
                y = sy * lerp(bo, bi, t)
                pts.append((x, y, f2(x, y)[0] + 0.02))
            sweep(a, pts, ridge_profile(0.40, 0.30))
    a.finish("下檐戗脊", M["tile_dark"], coll, bevel=0.012)

    # 围脊（下檐内圈）
    a = MeshAccum()
    for y in (-bi, bi):
        sweep(a, [(-ai, y, zin + 0.02), (0, y, zin + 0.02), (ai, y, zin + 0.02)],
              ridge_profile(0.42, 0.34))
    for x in (-ai, ai):
        sweep(a, [(x, -bi, zin + 0.02), (x, 0, zin + 0.02), (x, bi, zin + 0.02)],
              ridge_profile(0.42, 0.34))
    a.finish("围脊", M["tile_dark"], coll, bevel=0.012)


# ============================================================================
# 6. 墙体、门窗、匾额
# ============================================================================
def lattice_panel(acc, w, h, rects, depth=0.05, bar=0.028):
    """rects: [(x0,y0,x1,y1)] 局部平面内，Z 为竖直"""
    for (x0, z0, x1, z1) in rects:
        acc.box(((x0 + x1) / 2, 0, (z0 + z1) / 2), (abs(x1 - x0), depth, bar))
        acc.box(((x0 + x1) / 2, 0, (z0 + z1) / 2), (bar, depth, abs(z1 - z0)))


def build_walls(coll, M):
    y0 = P["col_y"][0]
    xs = P["col_x"]

    a = MeshAccum()   # 朱红板壁
    b = MeshAccum()   # 深色门窗框
    c = MeshAccum()   # 格心
    d = MeshAccum()   # 窗内暗底

    for i in range(5):
        x0, x1 = xs[i] + 0.36, xs[i + 1] - 0.36
        w = x1 - x0
        cx = (x0 + x1) / 2
        if i == 2:
            # ------- 明间：板门 + 横披窗 -------
            dw = 3.24
            b.box2(cx - dw / 2 - 0.16, cx - dw / 2, y0 - 0.15, y0 - 0.01, G + 0.18, 5.78)
            b.box2(cx + dw / 2, cx + dw / 2 + 0.16, y0 - 0.15, y0 - 0.01, G + 0.18, 5.78)
            b.box2(cx - dw / 2, cx + dw / 2, y0 - 0.15, y0 - 0.01, 5.62, 5.78)
            b.box2(cx - dw / 2, cx + dw / 2, y0 - 0.15, y0 - 0.01, G + 0.18, G + 0.30)
            # 门扇
            a.box2(cx - dw / 2, cx - 0.015, y0 - 0.10, y0 - 0.03, G + 0.30, 5.62)
            a.box2(cx + 0.015, cx + dw / 2, y0 - 0.10, y0 - 0.03, G + 0.30, 5.62)
            # 门钉
            for r in range(4):
                for k in range(4):
                    for s2 in (-1, 1):
                        px = cx + s2 * (0.34 + k * 0.34)
                        c.cyl((px, y0 - 0.115, G + 1.05 + r * 0.62), 0.048, 0.04, seg=8,
                              M=Matrix.Rotation(math.pi / 2, 4, 'X'))
            # 铺首
            for s2 in (-1, 1):
                c.cyl((cx + s2 * 0.30, y0 - 0.13, G + 2.05), 0.12, 0.05, seg=14,
                      M=Matrix.Rotation(math.pi / 2, 4, 'X'))
            # 横披窗
            zt0, zt1 = 5.80, 7.05
            b.box2(cx - dw / 2, cx + dw / 2, y0 - 0.13, y0 - 0.02, zt0 - 0.06, zt0)
            b.box2(cx - dw / 2, cx + dw / 2, y0 - 0.13, y0 - 0.02, zt1, zt1 + 0.08)
            nb = 13
            for k in range(nb + 1):
                px = cx - dw / 2 + k * dw / nb
                c.box2(px - 0.018, px + 0.018, y0 - 0.11, y0 - 0.04, zt0, zt1)
            for r in range(1, 4):
                zz = zt0 + r * (zt1 - zt0) / 4
                c.box2(cx - dw / 2, cx + dw / 2, y0 - 0.11, y0 - 0.04, zz - 0.018, zz + 0.018)
            d.box2(cx - dw / 2, cx + dw / 2, y0 + 0.02, y0 + 0.05, zt0, zt1)
            # 两侧板壁
            a.box2(x0, cx - dw / 2 - 0.16, y0 - 0.08, y0 + 0.02, G + 0.20, COL_TOP)
            a.box2(cx + dw / 2 + 0.16, x1, y0 - 0.08, y0 + 0.02, G + 0.20, COL_TOP)
            for xx in (cx - dw / 2 - 0.16, cx + dw / 2 + 0.16):
                c.box2(xx - 0.03, xx + 0.03, y0 - 0.10, y0 - 0.03, G + 0.20, COL_TOP)
        else:
            # ------- 次间 / 梢间：板壁 + 槛窗 -------
            a.box2(x0, x1, y0 - 0.08, y0 + 0.02, G + 0.20, 2.98)
            for k in range(1, 4):
                c.box2(x0 + k * w / 4 - 0.022, x0 + k * w / 4 + 0.022,
                       y0 - 0.10, y0 - 0.04, G + 0.32, 2.86)
            # 窗框
            b.box2(x0 - 0.05, x0 + 0.10, y0 - 0.13, y0 - 0.01, 2.90, 5.72)
            b.box2(x1 - 0.10, x1 + 0.05, y0 - 0.13, y0 - 0.01, 2.90, 5.72)
            b.box2(x0, x1, y0 - 0.13, y0 - 0.01, 2.98, 3.16)
            b.box2(x0, x1, y0 - 0.13, y0 - 0.01, 5.54, 5.74)
            # 格心
            nv = 9
            for k in range(nv + 1):
                px = x0 + 0.10 + k * (w - 0.20) / nv
                c.box2(px - 0.019, px + 0.019, y0 - 0.105, y0 - 0.035, 3.16, 5.54)
            for r in range(7):
                zz = 3.16 + r * (5.54 - 3.16) / 6
                c.box2(x0 + 0.10, x1 - 0.10, y0 - 0.105, y0 - 0.035, zz - 0.019, zz + 0.019)
            c.box2(x0 + 0.10, x1 - 0.10, y0 - 0.115, y0 - 0.03, 4.30, 4.40)
            # 窗内暗底
            d.box2(x0 + 0.06, x1 - 0.06, y0 + 0.02, y0 + 0.05, 3.10, 5.60)
            # 窗上板壁
            a.box2(x0, x1, y0 - 0.08, y0 + 0.02, 5.74, COL_TOP)
    a.finish("正面_板壁", M["wood_red"], coll, bevel=0.008)
    b.finish("正面_门窗框", M["wood_red_dark"], coll, bevel=0.008)
    c.finish("正面_格心", M["wood_lattice"], coll)
    d.finish("正面_窗内暗底", M["win_shadow"], coll)

    # 山墙 / 背墙
    a = MeshAccum()
    for x in (xs[0], xs[-1]):
        a.box2(x - 0.10, x + 0.10, P["col_y"][0], P["col_y"][-1], G + 0.2, COL_TOP)
    a.box2(xs[0], xs[-1], P["col_y"][-1] - 0.10, P["col_y"][-1] + 0.10, G + 0.2, COL_TOP)
    a.finish("山墙背墙", M["wood_red"], coll, bevel=0.01)

    a = MeshAccum()
    a.box2(xs[0] + 0.6, xs[-1] - 0.6, P["col_y"][-1] - 0.02, P["col_y"][-1] + 0.02, G, COL_TOP)
    a.finish("内壁", M["wood_dark"], coll)

    # 山面壁柱与横枋
    a = MeshAccum()
    for sx in (xs[0], xs[-1]):
        for y in P["col_y"][1:-1]:
            a.box2(sx - 0.30, sx + 0.30, y - 0.24, y + 0.24, G + 0.2, COL_TOP)
        for zz in (4.35, 5.95):
            a.box2(sx - 0.26, sx + 0.26, P["col_y"][0], P["col_y"][-1], zz, zz + 0.26)
    a.finish("山面壁柱", M["wood_red"], coll, bevel=0.012)

    # ---------------- 上层：板壁 + 槛窗 ----------------
    a = MeshAccum()
    b = MeshAccum()
    c = MeshAccum()
    d = MeshAccum()
    z0, z1 = P["up_wall_z0"], P["up_wall_z1"]
    fy = P["col_y"][0] * 0.88
    xa, xb = xs[0] * 0.88, xs[-1] * 0.88
    a.box2(xa, xb, fy - 0.07, fy + 0.03, z0, z1)
    for i in range(5):
        wx0 = xs[i] * 0.88 + 0.55
        wx1 = xs[i + 1] * 0.88 - 0.55
        wz0, wz1 = z0 + 0.42, z1 - 0.22
        b.box2(wx0 - 0.09, wx0, fy - 0.12, fy - 0.01, wz0 - 0.09, wz1 + 0.09)
        b.box2(wx1, wx1 + 0.09, fy - 0.12, fy - 0.01, wz0 - 0.09, wz1 + 0.09)
        b.box2(wx0, wx1, fy - 0.12, fy - 0.01, wz0 - 0.09, wz0)
        b.box2(wx0, wx1, fy - 0.12, fy - 0.01, wz1, wz1 + 0.09)
        nb = 7
        for k in range(nb + 1):
            px = wx0 + k * (wx1 - wx0) / nb
            c.box2(px - 0.017, px + 0.017, fy - 0.10, fy - 0.03, wz0, wz1)
        for r in range(1, 4):
            zz = wz0 + r * (wz1 - wz0) / 4
            c.box2(wx0, wx1, fy - 0.10, fy - 0.03, zz - 0.017, zz + 0.017)
        d.box2(wx0, wx1, fy + 0.02, fy + 0.05, wz0, wz1)
    a.finish("上层_板壁", M["wood_red"], coll, bevel=0.008)
    b.finish("上层_窗框", M["wood_red_dark"], coll, bevel=0.008)
    c.finish("上层_格心", M["wood_lattice"], coll)
    d.finish("上层_窗内暗底", M["win_shadow"], coll)

    a = MeshAccum()
    for x in (xa, xb):
        a.box2(x - 0.07, x + 0.07, -fy, fy, z0, z1)
    a.box2(xa, xb, -fy - 0.07, -fy + 0.07, z0, z1)
    a.finish("上层_山墙", M["wood_red"], coll)


def build_plaques(coll, M):
    """匾额与楹联"""
    y = P["col_y"][0] - 1.30
    # 匾额
    a = MeshAccum()
    a.box((0, y, 8.30), (4.10, 0.24, 1.34))
    a.box((0, y - 0.13, 8.30), (3.82, 0.06, 1.10))
    a.finish("匾额_底板", M["plaque"], coll, bevel=0.02)
    a = MeshAccum()
    a.box2(-1.95, 1.95, y - 0.18, y - 0.11, 8.91, 9.01)
    a.box2(-1.95, 1.95, y - 0.18, y - 0.11, 7.60, 7.70)
    a.box2(-1.95, -1.85, y - 0.18, y - 0.11, 7.70, 8.91)
    a.box2(1.85, 1.95, y - 0.18, y - 0.11, 7.70, 8.91)
    a.finish("匾额_边框", M["gold"], coll)
    make_text("保國寺", 0.94, M["gold"], coll, "匾额_文字",
              loc=(0, y - 0.19, 8.28), extrude=0.035, spacing=1.10)

    # 楹联（明间两侧柱）
    for x, txt in ((-2.12, "莊嚴結十方緣"), (2.12, "精進開先覺路")):
        a = MeshAccum()
        yy = P["col_y"][0] - 0.40
        a.box2(x - 0.19, x + 0.19, yy - 0.10, yy + 0.02, 4.30, 6.90)
        a.finish(f"楹联_{txt[:2]}", M["plaque"], coll, bevel=0.012)
        make_text("\n".join(txt), 0.25, M["gold"], coll, f"楹联文_{txt[:2]}",
                  loc=(x, yy - 0.11, 5.60), extrude=0.02, spacing=0.95,
                  rot=(math.pi / 2, 0, 0))


def build_backdrop(coll, M):
    """殿内暗部 + 背面台阶"""
    a = MeshAccum()
    a.box2(-10.3, 10.3, -6.34, 6.30, G, 10.86)
    a.box2(-9.2, 9.2, -5.70, 5.72, 10.86, 12.9)
    a.finish("殿内暗室", M["dark"], coll)
