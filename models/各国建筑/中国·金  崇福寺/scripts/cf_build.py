# -*- coding: utf-8 -*-
"""
cf_build.py —— 崇福寺弥陀殿 三维建模主程序
依据：用户提供的正面全景 + 转角近景两张照片
风格：金代（1143）单檐歇山顶、面阔七间、进深四间、七铺作双杪双下昂
"""
import bpy
import addon_utils
addon_utils.enable("cycles", default_set=True)
import math
import os
import sys
import numpy as np
from mathutils import Vector, Matrix, Euler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cf_lib import (Geo, new_coll, clear_scene, pbr, flat, sun_setup, camera,
                    TEX_DIR, ROOT)
import cf_tex

# =============================================================================
# 一、参数（可在 .blend 的 PARAMS 物体上调整同名自定义属性）
# =============================================================================
P = {
    "bay_x": [5.6, 5.8, 5.9, 6.0, 5.9, 5.8, 5.6],   # 面阔七间
    "bay_y": [6.2, 6.2, 6.2, 6.2],                   # 进深四间
    "col_h": 7.00,           # 檐柱高
    "col_r": 0.33,           # 檐柱半径
    "platform_h": 2.00,
    "platform_x": 24.6,      # 台基半宽
    "platform_y": 16.6,      # 台基半深
    "eave_out": 4.60,        # 出檐
    "eave_z": 9.10,          # 檐口高（相对台面上皮）
    "ridge_rise": 11.20,     # 举高
    "shoushan": 4.60,        # 收山（宋式：收山 ≈ 出檐，保持山花位置不变）
    "gable_y": 8.60,         # 山花底边半宽
    "corner_rise": 2.55,     # 起翘
    "tile_gap": 0.34,        # 瓦垄间距
    "wall_t": 0.55,
    "white_base": 1.05,      # 白灰墙基高
    "door_bays": [0, 1, 2, 3, 4, 5, 6],
    "dougong_jian": 3,       # 每间补间铺作数
}

X_TOTAL = sum(P["bay_x"])
Y_TOTAL = sum(P["bay_y"])
HX = X_TOTAL / 2
HY = Y_TOTAL / 2
EAVE_X = HX + P["eave_out"]
EAVE_Y = HY + P["eave_out"]
XG = EAVE_X - P["shoushan"]
Y1 = P["gable_y"]
Z_EAVE = P["eave_z"]
EAVE_Z = Z_EAVE
H_RIDGE = Z_EAVE + P["ridge_rise"]
COL_TOP = P["col_h"]
RISE = P["corner_rise"]
GAP = P["tile_gap"]
GROUND_Z = -1.30         # 院坪标高：台基露出 1.30 m，其余为埋深

# 柱网坐标
XS = [-HX]
for b in P["bay_x"]:
    XS.append(XS[-1] + b)
YS = [-HY]
for b in P["bay_y"]:
    YS.append(YS[-1] + b)


# =============================================================================
# 二、屋面数学：统一高度场（前后长坡 + 两山撒头，戗脊 = 二者交线）
#     z(x,y) = min( 长坡 f(y), 撒头 h(x) ) + 翼角起翘
# =============================================================================
def clamp01(v):
    return 0.0 if v < 0.0 else (1.0 if v > 1.0 else v)


def smooth01(v):
    v = clamp01(v)
    return v * v * (3.0 - 2.0 * v)


PROF_T = [0.0, 0.22, 0.46, 0.72, 1.0]
PROF_D = [0.0, 3.40, 6.30, 8.70, 11.00]      # 九举→七五举→六五举→五举
PROF_M = [13.60, 12.60, 10.70, 8.50, 7.20]


def prof(t):
    """举折曲线：t=0 脊，t=1 檐口，返回自脊下落高度（Hermite 平滑）"""
    t = clamp01(t)
    k = P["ridge_rise"] / 11.0
    for i in range(4):
        if t <= PROF_T[i + 1] or i == 3:
            t0, t1 = PROF_T[i], PROF_T[i + 1]
            d0, d1 = PROF_D[i], PROF_D[i + 1]
            m0, m1 = PROF_M[i], PROF_M[i + 1]
            dd = t1 - t0
            u = (t - t0) / dd
            return k * ((2 * u ** 3 - 3 * u ** 2 + 1) * d0
                        + (u ** 3 - 2 * u ** 2 + u) * dd * m0
                        + (-2 * u ** 3 + 3 * u ** 2) * d1
                        + (u ** 3 - u ** 2) * dd * m1)
    return k * 11.0


def f_main(y):
    """前后长坡：y=0 正脊，y=±EAVE_Y 檐口"""
    return H_RIDGE - prof(abs(y) / EAVE_Y)


Z_BASE = f_main(Y1)          # 山花底边 = 撒头顶边


def prof_end(s):
    return 0.30 * s + 0.70 * s ** 0.82


def h_end(x):
    """两山撒头：x=±XG 起（山花底边），x=±EAVE_X 收至檐口"""
    s = clamp01((abs(x) - XG) / max(1e-6, EAVE_X - XG))
    return Z_BASE - (Z_BASE - Z_EAVE) * prof_end(s)


def corner_lift(x, y):
    """翼角起翘：集中于角部（近 40% 范围）急剧上扬，向内平缓衰减"""
    u = smooth01((abs(x) / EAVE_X - 0.60) / 0.40)
    v = smooth01((abs(y) / EAVE_Y - 0.56) / 0.44)
    return RISE * (u * v) ** 1.28


def z_roof(x, y):
    z = f_main(y)
    ax = abs(x)
    if ax > XG:
        z = min(z, h_end(ax))
    return z + corner_lift(x, y)


def hip_y(x):
    """戗脊线：给定 |x| 返回 |y|（f_main 与 h_end 的交点）"""
    target = h_end(x)
    lo, hi = 0.0, EAVE_Y
    for _ in range(34):
        mid = 0.5 * (lo + hi)
        if f_main(mid) > target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def hip_x(y):
    """戗脊线：给定 |y| 返回 |x|"""
    ay = abs(y)
    if ay <= Y1:
        return XG
    target = f_main(ay)
    lo, hi = XG, EAVE_X
    for _ in range(34):
        mid = 0.5 * (lo + hi)
        if h_end(mid) > target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)

# =============================================================================
# 三、贴图与材质
# =============================================================================
def make_materials(T):
    M = {}
    M["wall"] = pbr("朱红灰泥墙", T["wall_red"], T["wall_red_n"], rough=0.86, uv_scale=0.22, bump=1.0)
    M["white"] = pbr("白灰墙基", T["plaster_white"], T["plaster_white_n"], rough=0.90, uv_scale=0.35, tint=(0.88, 0.86, 0.80))
    M["stone"] = pbr("台基条石", T["stone"], T["stone_n"], rough=0.84, uv_scale=0.45, tint=(0.90, 0.89, 0.87))
    M["stone_d"] = pbr("阶条石", T["stone_dark"], T["stone_dark_n"], rough=0.82, uv_scale=0.55, tint=(0.66, 0.66, 0.64))
    M["brick"] = pbr("青砖铺地", T["brick"], T["brick_n"], rough=0.92, uv_scale=0.62)
    M["tile"] = pbr("布瓦屋面", T["roof_tile"], T["roof_tile_n"], rough=0.93, uv_scale=0.42, bump=0.55, spec=0.15)
    M["glaze"] = pbr("绿琉璃", T["glaze_green"], T["glaze_green_n"], rough=0.52, uv_scale=1.1, spec=0.45)
    M["gold"] = pbr("鎏金饰", T["glaze_gold"], T["glaze_gold_n"], rough=0.30, metallic=0.75, uv_scale=1.4)
    M["wood"] = pbr("深褐木构", T["wood_dark"], T["wood_dark_n"], rough=0.68, uv_scale=0.55, tint=(0.82, 0.80, 0.78))
    M["wood_r"] = pbr("朱红木作", T["wood_red"], T["wood_red_n"], rough=0.64, uv_scale=0.6, tint=(0.72, 0.60, 0.55))
    M["beam"] = pbr("梁枋彩画", T["wood_beam"], T["wood_beam_n"], rough=0.66, uv_scale=0.5, tint=(0.62, 0.58, 0.56))
    M["dg"] = pbr("斗拱木", T["wood_dark"], T["wood_dark_n"], rough=0.72, uv_scale=0.55, tint=(1.10, 1.05, 1.00))
    M["panel"] = pbr("裙板雕饰", T["door_panel"], T["door_panel_n"], rough=0.55, uv_scale=0.5)
    M["dark"] = flat("门内暗部", (0.012, 0.010, 0.009), rough=0.95)
    M["plaque"] = flat("匾额底板", (0.0085, 0.0095, 0.0130), rough=0.80)
    M["bronze"] = pbr("铜香炉", T["bronze"], T["bronze_n"], rough=0.45, metallic=0.55, uv_scale=1.6)
    M["bark"] = pbr("柏树皮", T["bark"], T["bark_n"], rough=0.85, uv_scale=1.2)
    M["leaf"] = flat("柏树叶", (0.038, 0.072, 0.036), rough=0.85)
    M["leaf2"] = flat("柏树叶2", (0.052, 0.095, 0.044), rough=0.85)
    M["red_paint"] = flat("栏杆朱漆", (0.42, 0.085, 0.062), rough=0.55)
    M["brickbase"] = pbr("砖砌墙基", T["brick"], None, rough=0.94, uv_scale=0.26, tint=(0.92, 0.90, 0.86), spec=0.2)
    M["board"] = flat("山花板", (0.092, 0.052, 0.040), rough=0.82)
    M["timber"] = flat("山花梁架", (0.058, 0.038, 0.027), rough=0.84)
    M["brickwall"] = pbr("砖砌台基", T["brick"], None, rough=0.94, uv_scale=0.55, tint=(0.74, 0.74, 0.72), spec=0.2)
    return M


# =============================================================================
# 四、台基与踏跺
# =============================================================================
def build_platform(coll, M):
    g = Geo()
    ph = P["platform_h"]
    px, py = P["platform_x"], P["platform_y"]
    # 台基主体（下大上小，收分）
    g.frustum((0, 0, -ph / 2), (px * 2 + 0.30, py * 2 + 0.30), (px * 2, py * 2), ph, mat=3)
    # 压阑石
    g.box((0, 0, -0.11), (px * 2 - 0.02, py * 2 - 0.02, 0.22), mat=1)
    # 台面铺砖
    g.box((0, 0, 0.005), (px * 2 - 1.0, py * 2 - 1.0, 0.02), mat=2)
    obj = g.build("台基", coll, [M["stone"], M["stone_d"], M["brick"], M["brickwall"]], box_uv=True)

    # 正面踏跺：实体台阶 + 垂带石（自地面砌至台面上皮）
    g2 = Geo()
    hh = 0.0 - GROUND_Z                 # 台阶总高
    steps = 8
    rise = hh / steps
    tread = 0.42
    w = 11.6
    y_top = -py - 0.02
    y_bot = y_top - steps * tread
    # 阶梯实体（每级自地面砌起，无缝隙）
    for i in range(steps):
        h = (i + 1) * rise
        yy = y_bot + (i + 0.5) * tread
        g2.box((0, yy, GROUND_Z + h / 2), (w, tread + 0.02, h), mat=2)
        # 踏步前缘的暗缝，强化台阶级数
        g2.box((0, yy - tread / 2 + 0.035, GROUND_Z + h - 0.022),
               (w - 0.02, 0.07, 0.045), mat=1)
    # 两侧三角封板
    for sx in (-1, 1):
        xw = sx * (w / 2 + 0.01)
        g2.add([(xw, y_top, GROUND_Z), (xw, y_top, 0.0), (xw, y_bot, GROUND_Z)],
               [(0, 1, 2)] if sx > 0 else [(2, 1, 0)], mat=0)
    # 垂带石（斜面石板，高出踏步 0.08）
    slope = math.atan2(hh, steps * tread)
    L = math.hypot(hh, steps * tread) + 0.50
    for sx in (-1, 1):
        g2.box((sx * (w / 2 - 0.22), (y_top + y_bot) / 2, GROUND_Z / 2 + 0.05),
               (0.52, L, 0.22), mat=1, rot=(slope, 0, 0))
    g2.build("踏跺", coll, [M["brickwall"], M["stone_d"], M["stone"]], box_uv=True)
    return obj


# =============================================================================
# 五、柱、额枋、墙体
# =============================================================================
def build_frame(coll, M):
    g = Geo()     # 柱
    for x in XS:
        for y in (YS[0], YS[-1]):
            g.cyl((x, y, 0.12), (x, y, COL_TOP), P["col_r"], 16, 0, r1=P["col_r"] * 0.90)
    for y in YS[1:-1]:
        for x in (XS[0], XS[-1]):
            g.cyl((x, y, 0.12), (x, y, COL_TOP), P["col_r"], 16, 0, r1=P["col_r"] * 0.90)
    # 柱础
    for x in XS:
        for y in (YS[0], YS[-1]):
            g.frustum((x, y, 0.085), (P["col_r"] * 2.5, P["col_r"] * 2.5),
                      (P["col_r"] * 2.05, P["col_r"] * 2.05), 0.17, mat=1)
    for y in YS[1:-1]:
        for x in (XS[0], XS[-1]):
            g.frustum((x, y, 0.085), (P["col_r"] * 2.5, P["col_r"] * 2.5),
                      (P["col_r"] * 2.05, P["col_r"] * 2.05), 0.17, mat=1)
    g.build("檐柱与柱础", coll, [M["wood_r"], M["stone"]])

    # 额枋 + 普拍枋（四周）
    g = Geo()
    for i in range(len(P["bay_x"])):
        x0, x1 = XS[i], XS[i + 1]
        for y in (YS[0], YS[-1]):
            g.box(((x0 + x1) / 2, y, COL_TOP - 0.25), (x1 - x0, 0.42, 0.50), mat=0)
            g.box(((x0 + x1) / 2, y, COL_TOP + 0.06), (x1 - x0, 0.56, 0.12), mat=0)
    for j in range(len(P["bay_y"])):
        y0, y1 = YS[j], YS[j + 1]
        for x in (XS[0], XS[-1]):
            g.box((x, (y0 + y1) / 2, COL_TOP - 0.25), (0.42, y1 - y0, 0.50), mat=0)
            g.box((x, (y0 + y1) / 2, COL_TOP + 0.06), (0.56, y1 - y0, 0.12), mat=0)
    # 拱眼壁（斗拱后的封板）
    g.box((0, YS[0] + 0.06, COL_TOP + 0.62), (X_TOTAL, 0.14, 1.05), mat=1)
    g.box((0, YS[-1] - 0.06, COL_TOP + 0.62), (X_TOTAL, 0.14, 1.05), mat=1)
    for x in (XS[0] + 0.06, XS[-1] - 0.06):
        g.box((x, 0, COL_TOP + 0.62), (0.14, Y_TOTAL, 1.05), mat=1)
    g.build("额枋与拱眼壁", coll, [M["beam"], M["wood"]])


def build_walls(coll, M):
    g = Geo()
    wt = P["wall_t"]
    wb = P["white_base"]
    # 正面：五间门，两端砌墙
    for i, x0 in enumerate(XS[:-1]):
        x1 = XS[i + 1]
        if i in P["door_bays"]:
            continue
        g.box(((x0 + x1) / 2, YS[0], COL_TOP / 2), (x1 - x0, wt, COL_TOP), mat=0)
    # 背面
    g.box((0, YS[-1], COL_TOP / 2), (X_TOTAL + 0.5, wt, COL_TOP), mat=0)
    # 两山
    for x in (XS[0], XS[-1]):
        g.box((x, 0, COL_TOP / 2), (wt, Y_TOTAL + 0.5, COL_TOP), mat=0)
    # 门间墙：门洞上方走马板
    for i in P["door_bays"]:
        x0, x1 = XS[i], XS[i + 1]
        g.box(((x0 + x1) / 2, YS[0], (4.70 + COL_TOP) / 2), (x1 - x0, wt, COL_TOP - 4.70), mat=0)
    wall = g.build("墙体", coll, [M["wall"]])

    # 白灰墙基（四周围一圈）+ 石压顶
    g = Geo()
    g.box((0, YS[0], wb / 2), (X_TOTAL + 0.06, wt + 0.10, wb), mat=0)
    g.box((0, YS[-1], wb / 2), (X_TOTAL + 0.06, wt + 0.10, wb), mat=0)
    for x in (XS[0], XS[-1]):
        g.box((x, 0, wb / 2), (wt + 0.10, Y_TOTAL + 0.06, wb), mat=0)
    for z in (wb + 0.05,):
        g.box((0, YS[0], z), (X_TOTAL + 0.12, wt + 0.16, 0.12), mat=1)
        g.box((0, YS[-1], z), (X_TOTAL + 0.12, wt + 0.16, 0.12), mat=1)
        for x in (XS[0], XS[-1]):
            g.box((x, 0, z), (wt + 0.16, Y_TOTAL + 0.12, 0.12), mat=1)
    g.build("砖砌墙基", coll, [M["brickbase"], M["stone"]])
    return wall


# =============================================================================
# 六、隔扇门
# =============================================================================
def build_doors(coll, M):
    g = Geo()       # 木框
    gl = Geo()      # 格心（不同材质更亮）
    back = Geo()    # 暗部
    wt = P["wall_t"]
    yd = YS[0]
    for i in P["door_bays"]:
        x0, x1 = XS[i], XS[i + 1]
        bw = x1 - x0
        if i == 3:
            # 明间敞开：门框、门槛、暗室与敞开的两扇门
            g.box((x0 + 0.15, yd, 2.38), (0.16, 0.36, 4.76), mat=0)
            g.box((x1 - 0.15, yd, 2.38), (0.16, 0.36, 4.76), mat=0)
            g.box(((x0 + x1) / 2, yd, 4.78), (bw, 0.36, 0.28), mat=0)
            g.box(((x0 + x1) / 2, yd, 0.11), (bw - 0.2, 0.46, 0.22), mat=2)
            # 敞开的门扇（折向室内）
            for xx in (x0 + 0.34, x1 - 0.34):
                g.box((xx, yd + 0.42, 2.25), (0.09, 0.78, 4.34), mat=0)
            back.box(((x0 + x1) / 2, yd + 1.15, 2.4), (bw - 0.3, 0.12, 4.7), mat=0)
            back.box(((x0 + x1) / 2, yd + 0.6, 4.66), (bw - 0.3, 1.1, 0.12), mat=0)
            continue
        nleaf = 4
        lw = bw / nleaf
        for k in range(nleaf):
            cx = x0 + lw * (k + 0.5)
            lx0 = cx - lw / 2 + 0.02
            lx1 = cx + lw / 2 - 0.02
            w = lx1 - lx0
            # 边框：上下左右
            g.box((cx, yd, 0.21), (w, 0.13, 0.42), mat=0)              # 下裙板框
            g.box((cx, yd, 4.52), (w, 0.13, 0.30), mat=0)              # 上框
            g.box((lx0 + 0.055, yd, 2.35), (0.11, 0.13, 4.35), mat=0)
            g.box((lx1 - 0.055, yd, 2.35), (0.11, 0.13, 4.35), mat=0)
            # 裙板（雕饰）
            g.box((cx, yd - 0.02, 1.05), (w - 0.22, 0.075, 1.32), mat=1)
            # 绦环板
            g.box((cx, yd - 0.015, 1.86), (w - 0.22, 0.07, 0.30), mat=1)
            # 格心：竖棂 + 横棂
            z0, z1 = 2.10, 4.36
            nv = max(4, int(round((w - 0.24) / 0.175)))
            for a in range(nv + 1):
                xx = lx0 + 0.11 + (w - 0.22) * a / nv
                gl.box((xx, yd - 0.02, (z0 + z1) / 2), (0.028, 0.045, z1 - z0), mat=0)
            nh = int(round((z1 - z0) / 0.30))
            for b in range(nh + 1):
                zz = z0 + (z1 - z0) * b / nh
                gl.box((cx, yd - 0.02, zz), (w - 0.22, 0.045, 0.026), mat=0)
            # 门内暗部
            back.box((cx, yd + 0.015, 2.35), (w - 0.18, 0.02, 4.3), mat=0)
        # 门洞侧框与上槛
        g.box((x0 + 0.06, yd, 2.35), (0.12, 0.30, 4.7), mat=0)
        g.box((x1 - 0.06, yd, 2.35), (0.12, 0.30, 4.7), mat=0)
        g.box(((x0 + x1) / 2, yd, 4.72), (bw, 0.30, 0.24), mat=0)
        # 门槛
        g.box(((x0 + x1) / 2, yd, 0.09), (bw, 0.34, 0.18), mat=2)
    g.build("隔扇门", coll, [M["wood_r"], M["panel"], M["stone_d"]], bevel=0.008)
    gl.build("格心棂条", coll, [M["wood_r"]], box_uv=True)
    back.build("门内暗部", coll, [M["dark"]], box_uv=False)


# =============================================================================
# 七、斗拱（七铺作双杪双下昂）
# =============================================================================
def dougong_geo(corner=False):
    """局部坐标：原点柱心，+Y 朝外，+X 沿墙，z=0 为额枋顶；总高约 1.72m"""
    g = Geo()
    W = 0.26
    # 栌斗：斗欹 + 斗平
    g.frustum((0, 0, 0.11), (0.84, 0.84), (0.68, 0.68), 0.22, mat=0)
    g.box((0, 0, 0.35), (0.70, 0.70, 0.26), mat=0)
    # 第一跳：华拱（外）+ 泥道拱（顺墙）
    g.box((0, 0.90, 0.62), (W, 2.55, 0.28), mat=0)
    g.box((0, 0, 0.62), (1.98, W, 0.28), mat=0)
    for yy in (0.98, 2.10):
        g.frustum((0, yy, 0.83), (0.40, 0.40), (0.33, 0.33), 0.16, mat=0)
    g.frustum((0, 0, 0.83), (0.40, 0.40), (0.33, 0.33), 0.16, mat=0)
    # 第二跳：华拱 + 慢拱
    g.box((0, 1.35, 0.99), (W, 3.15, 0.28), mat=0)
    g.box((0, 0, 0.99), (2.80, W, 0.28), mat=0)
    for yy in (1.70, 2.80):
        g.frustum((0, yy, 1.20), (0.40, 0.40), (0.33, 0.33), 0.16, mat=0)
    for xx in (-1.10, 1.10):
        g.frustum((xx, 0, 1.20), (0.38, 0.38), (0.31, 0.31), 0.15, mat=0)
    # 第三跳：下昂（斜出，昂嘴下垂）
    g.box((0, 2.30, 1.28), (0.26, 2.55, 0.30), mat=1, rot=(math.radians(19), 0, 0))
    g.box((0, 3.02, 0.96), (0.28, 0.62, 0.34), mat=1)
    g.box((0, 2.62, 1.42), (0.26, 1.30, 0.26), mat=1, rot=(math.radians(14), 0, 0))
    # 令拱 + 耍头 + 替木
    g.box((0, 2.98, 1.52), (1.58, 0.28, 0.30), mat=0)
    g.box((0, 2.98, 1.40), (0.30, 1.15, 0.26), mat=1)
    g.box((0, 2.98, 1.70), (1.50, 0.40, 0.12), mat=0)
    for xx in (-0.62, 0.62):
        g.frustum((xx, 2.98, 1.42), (0.36, 0.36), (0.30, 0.30), 0.14, mat=0)
    # 柱头枋（顺墙连系，两跳之间）
    g.box((0, 0.34, 1.24), (2.85, 0.24, 0.24), mat=0)
    g.box((0, 0.34, 1.50), (2.85, 0.22, 0.22), mat=0)
    if corner:
        g.box((0, 0, 0.62), (0.26, 2.60, 0.28), mat=0, rot=(0, 0, math.radians(-45)))
        g.box((0, 0, 1.02), (0.24, 3.40, 0.26), mat=1,
              rot=(math.radians(17), 0, math.radians(-45)))
    return g


DG_CACHE = {}


def place_dougong(coll, M, clusters, name="斗拱"):
    """clusters: [(x, y, angle, corner_bool, bay_w)]，角度 0 = 朝 -Y"""
    g = Geo()
    for (x, y, ang, corner, bw) in clusters:
        key = (round(bw, 2), corner)
        if key not in DG_CACHE:
            DG_CACHE[key] = dougong_geo(corner)
        src = DG_CACHE[key]
        O = Vector((-math.sin(ang), -math.cos(ang), 0))
        T = Vector((0, 0, 1)).cross(O)
        Mx = Matrix(((T.x, O.x, 0, x), (T.y, O.y, 0, y), (0, 0, 1, COL_TOP + 0.12), (0, 0, 0, 1)))
        off = len(g.v)
        g.v.extend([tuple(Mx @ Vector(p)) for p in src.v])
        for fc, mi in zip(src.f, src.m):
            g.f.append(tuple(i + off for i in fc))
            g.m.append(mi)
    return g.build(name, coll, [M["dg"], M["beam"]], bevel=0.006)


def dougong_clusters():
    clusters = []
    for i in range(len(P["bay_x"])):
        x0, x1 = XS[i], XS[i + 1]
        bw = x1 - x0
        n = P["dougong_jian"]
        pos = [x0] + [x0 + bw * (k + 1) / (n + 1) for k in range(n)]
        for x in pos:
            clusters.append((x, YS[0], 0, False, bw))
            clusters.append((x, YS[-1], math.pi, False, bw))
    clusters.append((XS[0], YS[0], math.radians(-45), True, 5.6))
    clusters.append((XS[-1], YS[0], math.radians(45), True, 5.6))
    clusters.append((XS[0], YS[-1], math.radians(-135), True, 5.6))
    clusters.append((XS[-1], YS[-1], math.radians(135), True, 5.6))
    for j in range(len(P["bay_y"])):
        y0, y1 = YS[j], YS[j + 1]
        bw = y1 - y0
        n = P["dougong_jian"]
        pos = [y0 + bw * (k + 1) / (n + 1) for k in range(n)]
        for y in pos:
            clusters.append((XS[0], y, math.radians(-90), False, bw))
            clusters.append((XS[-1], y, math.radians(90), False, bw))
    return clusters


# =============================================================================
# 八、撩檐枋、檐椽、飞椽
# =============================================================================
def build_eave(coll, M):
    g = Geo()
    # 撩檐枋（四周，位于斗拱外端）
    d = 2.95
    zf = EAVE_Z - 0.26
    for y in (YS[0] - d, YS[-1] + d):
        g.box((0, y, zf), (EAVE_X * 2 - 0.4, 0.34, 0.42), mat=0)
    for x in (XS[0] - d, XS[-1] + d):
        g.box((x, 0, zf), (0.34, EAVE_Y * 2 - 0.4, 0.42), mat=0)

    # 檐椽（圆）+ 飞椽（方）
    for sign in (1, -1):
        n = int((EAVE_X * 2 - 0.8) / 0.30)
        y_in = sign * (HY + 0.85)
        y_out = sign * (EAVE_Y - 0.12)
        for i in range(n + 1):
            x = -EAVE_X + 0.40 + i * (EAVE_X * 2 - 0.80) / n
            g.cyl((x, y_in, z_roof(x, y_in) - 0.60),
                  (x, y_out, z_roof(x, y_out) - 0.54), 0.085, 8, mat=0)
            yf = sign * (EAVE_Y - 0.30)
            g.box((x, yf, z_roof(x, yf) - 0.42), (0.115, 0.66, 0.13), mat=1,
                  rot=(math.radians(-14 * sign), 0, 0))
    for sx in (1, -1):
        n = int((EAVE_Y * 2 - 0.8) / 0.30)
        x_in = sx * (HX + 0.85)
        x_out = sx * (EAVE_X - 0.12)
        for i in range(n + 1):
            y = -EAVE_Y + 0.40 + i * (EAVE_Y * 2 - 0.80) / n
            g.cyl((x_in, y, z_roof(x_in, y) - 0.60),
                  (x_out, y, z_roof(x_out, y) - 0.54), 0.085, 8, mat=0)
            xf = sx * (EAVE_X - 0.30)
            g.box((xf, y, z_roof(xf, y) - 0.42), (0.66, 0.115, 0.13), mat=1,
                  rot=(0, math.radians(14 * sx), 0))
    g.build("檐椽与飞椽", coll, [M["wood"], M["wood_r"]])


# =============================================================================
# 九、屋面（瓦面 / 望板 / 瓦口）
# =============================================================================
def _surf_dir(g, grid, mat, want):
    """按期望法线方向生成曲面片，杜绝翻面导致的死黑"""
    a = Vector(grid[0][0]); b = Vector(grid[0][1]); d = Vector(grid[1][0])
    n = (b - a).cross(d - a)
    g.surface(grid, mat=mat, flip=(n.dot(Vector(want)) < 0))


def _grid_center(sign):
    """正身中段（收山线以内）：自正脊起至檐口"""
    nx, ny = 56, 26
    rows = []
    for i in range(nx + 1):
        x = -XG + 2 * XG * i / nx
        row = []
        for j in range(ny + 1):
            y = sign * (0.03 + (EAVE_Y - 0.03) * j / ny)
            row.append((x, y, z_roof(x, y)))
        rows.append(row)
    return rows


def _grid_corner(sign, sx):
    """两端翼角段（收山线以外）：自戗脊起至檐口

    与 _grid_center 各自独立成片——两者之间是敞开的山花，不再跨列连面，
    因此不会出现覆盖山花的竖直瓦面。
    """
    nx, ny = 26, 26
    rows = []
    for i in range(nx + 1):
        ax = XG + (EAVE_X - XG) * i / nx
        y0 = min(hip_y(ax), EAVE_Y - 0.12)
        row = []
        for j in range(ny + 1):
            y = sign * (y0 + (EAVE_Y - 0.03 - y0) * j / ny)
            row.append((sx * ax, y, z_roof(sx * ax, y)))
        rows.append(row)
    return rows


def _grid_end(sx):
    """两山撒头：自山花底边（±Y1）斜出至山面檐口

    注意 ax 恰好等于 XG 时 z_roof 会退回 f_main（那属于正身坡），
    故此处直接以 h_end 定高，保证首行即 Z_BASE，不产生竖折面。
    """
    nu, nv = 26, 30
    rows = []
    for i in range(nu + 1):
        ax = XG + (EAVE_X - XG - 0.02) * i / nu
        ze = h_end(ax)
        yh = min(hip_y(ax), EAVE_Y - 0.03)
        row = []
        for j in range(nv + 1):
            y = yh * (-1.0 + 2.0 * j / nv)
            row.append((sx * ax, y, ze + corner_lift(sx * ax, y)))
        rows.append(row)
    return rows


def _slab(g, rows, side):
    """一片坡面：瓦面 + 望板 + 檐口瓦口板（side: 'y' 前后檐 / 'x' 山面）"""
    _surf_dir(g, rows, 0, (0, 0, 1))
    under = [[(p[0], p[1], p[2] - 0.36) for p in r] for r in rows]
    _surf_dir(g, under, 1, (0, 0, -1))
    if side == 'y':
        edge = [rows[i][-1] for i in range(len(rows))]
        sgn = 1.0 if edge[0][1] > 0 else -1.0
        top = [(p[0], sgn * (EAVE_Y + 0.02), p[2] + 0.02) for p in edge]
        bot = [(p[0], sgn * (EAVE_Y + 0.02), p[2] - 0.38) for p in edge]
        _surf_dir(g, [top, bot], 1, (0, sgn, 0))
    else:
        edge = rows[-1]
        sgn = 1.0 if edge[0][0] > 0 else -1.0
        top = [(sgn * (EAVE_X + 0.02), p[1], p[2] + 0.02) for p in edge]
        bot = [(sgn * (EAVE_X + 0.02), p[1], p[2] - 0.38) for p in edge]
        _surf_dir(g, [top, bot], 1, (sgn, 0, 0))


def build_roof(coll, M):
    g = Geo()      # 0=瓦面 1=望板
    # 正身中段：前后坡各一片
    for sign in (1, -1):
        _slab(g, _grid_center(sign), 'y')
    # 两端翼角段：前后坡延伸（与中段断开设缝，山花由此敞开）
    for sx in (1, -1):
        for sign in (1, -1):
            _slab(g, _grid_corner(sign, sx), 'y')
    # 两山撒头
    for sx in (1, -1):
        _slab(g, _grid_end(sx), 'x')
    # 檐下望板：自檐口内缘斜向撩檐枋，封住仰视空隙
    n = 96
    for sign in (1, -1):
        rows = []
        for i in range(n + 1):
            x = -EAVE_X + 2 * EAVE_X * i / n
            rows.append([(x, sign * (EAVE_Y + 0.01), z_roof(x, sign * EAVE_Y) - 0.40),
                         (x, sign * (HY + 0.30), EAVE_Z - 0.04)])
        _surf_dir(g, rows, 1, (0, 0, -1))
    for sx in (1, -1):
        rows = []
        for j in range(65):
            y = -EAVE_Y + 2 * EAVE_Y * j / 64
            rows.append([(sx * (EAVE_X + 0.01), y, z_roof(sx * EAVE_X, y) - 0.40),
                         (sx * (HX + 0.30), y, EAVE_Z - 0.04)])
        _surf_dir(g, rows, 1, (0, 0, -1))

    roof = g.build("屋面（瓦面+望板）", coll, [M["tile"], M["wood"]],
                   smooth=True, box_uv=False)
    me = roof.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uvl = me.uv_layers[0].data
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uvl[li].uv = (co.x * 0.55, (co.y + co.z) * 0.55)
    return roof


# =============================================================================
# 九之二、瓦垄（筒瓦）+ 剪边 + 檐口勾头滴水
# =============================================================================
PROF_HALF = [(-1.00, 0.00), (-0.92, 0.55), (-0.62, 0.88), (-0.22, 1.00),
             (0.22, 1.00), (0.62, 0.88), (0.92, 0.55), (1.00, 0.00)]

EAVE_CAPS = []      # (终点, 切向, 宽度) 供勾头滴水使用


def _rib(g, path, hw, hh, glaze_len=1.15):
    pts = [Vector(p) for p in path]
    n = len(pts)
    if n < 2:
        return
    dist = [0.0] * n
    for i in range(n - 2, -1, -1):
        dist[i] = dist[i + 1] + (pts[i + 1] - pts[i]).length
    if dist[0] <= 0.3:
        return
    rings = []
    for i, p in enumerate(pts):
        if i == 0:
            t = pts[1] - p
        elif i == n - 1:
            t = p - pts[-2]
        else:
            t = pts[i + 1] - pts[i - 1]
        if t.length < 1e-6:
            return
        t.normalize()
        s = Vector((0, 0, 1)).cross(t)
        if s.length < 1e-4:
            s = Vector((1, 0, 0)).cross(t)
        s.normalize()
        up = t.cross(s).normalized()
        rings.append([p + s * (a * hw) + up * (b * hh) for a, b in PROF_HALF])
    m = len(PROF_HALF)
    off = len(g.v)
    for r in rings:
        g.v.extend([tuple(p) for p in r])
    for i in range(n - 1):
        mi = 1 if (dist[i] < glaze_len and dist[i + 1] < glaze_len) else 0
        a = i * m
        for k in range(m - 1):
            g.f.append((off + a + k, off + a + m + k, off + a + m + k + 1, off + a + k + 1))
            g.m.append(mi)
    t_end = (pts[-1] - pts[-2]).normalized()
    EAVE_CAPS.append((pts[-1], t_end, hw))


def build_tiles(coll, M):
    g = Geo()       # 0 青瓦  1 绿琉璃剪边
    hw, hh = 0.100, 0.034
    EAVE_CAPS.clear()

    # 前后长坡瓦垄（自戗脊/正脊侧向檐口）
    for sign in (1, -1):
        x = -EAVE_X + 0.24
        while x < EAVE_X - 0.24:
            y0 = 0.34 if abs(x) <= XG else hip_y(x) + 0.20
            if EAVE_Y - 0.16 - y0 > 0.45:
                steps = 18 if abs(x) <= XG else 7
                path = []
                for i in range(steps + 1):
                    y = y0 + (EAVE_Y - 0.16 - y0) * i / steps
                    path.append((x, sign * y, z_roof(x, sign * y) + 0.012))
                _rib(g, path, hw, hh)
            x += GAP

    # 两山撒头瓦垄（自山花侧向山面檐口）
    for sx in (1, -1):
        y = -EAVE_Y + 0.24
        while y < EAVE_Y - 0.24:
            x0 = hip_x(y) + 0.20
            if EAVE_X - 0.16 - x0 > 0.45:
                steps = 7 if abs(y) > Y1 else 13
                path = []
                for i in range(steps + 1):
                    ax = x0 + (EAVE_X - 0.16 - x0) * i / steps
                    path.append((sx * ax, y, z_roof(sx * ax, y) + 0.012))
                _rib(g, path, hw, hh)
            y += GAP

    tiles = g.build("瓦垄（筒瓦+剪边）", coll, [M["tile"], M["glaze"]], smooth=True, box_uv=False)
    me = tiles.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uvl = me.uv_layers[0].data
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uvl[li].uv = (co.x * 1.2, (co.y + co.z) * 1.2)
    return tiles


def build_eave_tiles(coll, M):
    """檐口勾头（绿琉璃圆瓦当）与滴水"""
    g = Geo()
    for (p, t, hw) in EAVE_CAPS:
        base = p + t * 0.02
        g.cyl(base - t * 0.06, base + t * 0.055, hw * 0.80, 10, mat=0)
        # 滴水舌片
        side = Vector((0, 0, 1)).cross(t).normalized()
        g.add([base + side * hw * 1.02 + Vector((0, 0, 0.02)),
               base - side * hw * 1.02 + Vector((0, 0, 0.02)),
               base + t * 0.06 + Vector((0, 0, -0.10))],
              [(0, 1, 2)], 1)
    return g.build("檐口勾头滴水", coll, [M["glaze"], M["glaze"]], smooth=True)

# =============================================================================
# 十、屋脊、鸱吻、脊刹、走兽
# =============================================================================
def add_chiwen(g, sx, mat=0, xpos=None, scale=1.52):
    """正脊鸱吻：底座 + 卷尾 + 龙首"""
    x = sx * XG if xpos is None else xpos
    z0 = H_RIDGE + 0.32
    K = scale
    # 座
    g.box((x, 0, z0 + 0.25 * K), (0.90 * K, 1.05 * K, 0.50 * K), mat=mat)
    # 卷尾（向上向内弯）
    path = [(x, 0.05 * sx, z0 + 0.45 * K),
            (x, 0.02 * sx, z0 + 0.85 * K),
            (x, -0.16 * sx, z0 + 1.22 * K),
            (x, -0.46 * sx, z0 + 1.48 * K),
            (x, -0.78 * sx, z0 + 1.60 * K)]
    g.sweep(path, 0.70 * K, 0.70 * K, mat=mat, up=Vector((1, 0, 0)))
    # 龙首
    g.frustum((x, 0.46 * sx, z0 + 1.05 * K), (0.70 * K, 1.02 * K), (0.56 * K, 0.78 * K), 0.58 * K, mat=mat)
    g.box((x, 0.68 * sx, z0 + 0.84 * K), (0.50 * K, 0.60 * K, 0.28 * K), mat=mat)
    # 吻尖
    g.box((x, 0.28 * sx, z0 + 1.70 * K), (0.38 * K, 0.46 * K, 0.38 * K), mat=mat,
          rot=(math.radians(-18 * sx), 0, 0))
    # 背鳍
    for k in range(4):
        g.box((x, (-0.10 - 0.14 * k) * sx * K, z0 + (1.22 + 0.06 * k) * K),
              (0.34 * K, 0.18 * K, (0.36 - 0.05 * k) * K), mat=mat)


def add_beast(g, p, dirv, scale=1.0, mat=0):
    """戗脊走兽"""
    x, y, z = p
    s = scale
    g.box((x, y, z + 0.10 * s), (0.20 * s, 0.30 * s, 0.20 * s), mat=mat)
    g.frustum((x, y, z + 0.30 * s), (0.22 * s, 0.26 * s), (0.16 * s, 0.18 * s), 0.24 * s, mat=mat)
    # 头
    g.frustum((x, y + dirv * 0.06 * s, z + 0.50 * s), (0.16 * s, 0.20 * s),
              (0.12 * s, 0.14 * s), 0.16 * s, mat=mat)


def build_ridges(coll, M):
    """正脊、鸱吻、宝顶、垂脊、戗脊、走兽"""
    g = Geo()      # 0=绿琉璃 1=鎏金
    # 正脊：压当条 + 低矮脊身 + 盖脊瓦
    g.box((0, 0, H_RIDGE + 0.12), (2 * XG + 0.24, 0.86, 0.26), mat=0)
    g.box((0, 0, H_RIDGE + 0.50), (2 * XG + 0.06, 0.62, 0.48), mat=0)
    g.box((0, 0, H_RIDGE + 0.80), (2 * XG + 0.20, 0.80, 0.16), mat=0)
    # 脊心小脊饰（图版式）
    for k in (-4, -3, -2, -1, 1, 2, 3, 4):
        xx = k * (XG / 4.6)
        g.frustum((xx, 0, H_RIDGE + 0.98), (0.26, 0.30), (0.12, 0.16), 0.22, mat=1)
        g.box((xx, 0, H_RIDGE + 0.90), (0.32, 0.36, 0.08), mat=1)
    # 鸱吻
    add_chiwen(g, 1, 0)
    add_chiwen(g, -1, 0)
    # 中央宝顶
    zc = H_RIDGE + 0.86
    g.frustum((0, 0, zc + 0.12), (1.05, 0.86), (0.86, 0.70), 0.24, mat=1)
    g.frustum((0, 0, zc + 0.36), (0.72, 0.60), (0.58, 0.48), 0.26, mat=1)
    for i in range(3):
        w = 0.50 - i * 0.09
        g.frustum((0, 0, zc + 0.54 + i * 0.26), (w, w * 0.82), (w * 0.80, w * 0.66), 0.20, mat=1)
        g.box((0, 0, zc + 0.66 + i * 0.26), (w * 1.26, w * 1.04, 0.05), mat=1)
    g.cyl((0, 0, zc + 1.34), (0, 0, zc + 1.86), 0.065, 10, mat=1)
    g.frustum((0, 0, zc + 1.42), (0.22, 0.22), (0.10, 0.10), 0.14, mat=1)

    # 垂脊（山花博风上，自正脊端延至山花底边）
    for sx in (1, -1):
        for sy in (1, -1):
            pts = []
            for i in range(15):
                y = sy * Y1 * i / 14
                pts.append((sx * (XG + 0.16), y, f_main(y) + 0.14))
            g.sweep(pts, 0.42, 0.34, mat=0)
            for k in range(3):
                y = sy * Y1 * (0.66 + 0.10 * k)
                add_beast(g, (sx * (XG + 0.16), y, f_main(y) + 0.38), sy, 0.95, 1)

    # 戗脊（自山花底边角点延至翼角）
    for sx in (1, -1):
        for sy in (1, -1):
            pts = []
            for i in range(17):
                t = i / 16
                ax = XG + (EAVE_X - XG) * t
                y = hip_y(sx * ax)
                pts.append((sx * ax, sy * y, z_roof(sx * ax, sy * y) + 0.15))
            g.sweep(pts, 0.34, 0.30, mat=0)
            for k in range(4):
                t = 0.50 + 0.10 * k
                ax = XG + (EAVE_X - XG) * t
                y = hip_y(sx * ax)
                add_beast(g, (sx * ax, sy * y, z_roof(sx * ax, sy * y) + 0.38), sy, 0.92, 1)
            # 翼角端头（套兽）
            ax = EAVE_X - 0.10
            y = hip_y(sx * ax)
            g.frustum((sx * ax, sy * y, z_roof(sx * ax, sy * y) + 0.22),
                      (0.34, 0.34), (0.22, 0.22), 0.34, mat=1)
    return g.build("屋脊与脊饰", coll, [M["glaze"], M["gold"]], bevel=0.012)


# =============================================================================
# 十一、山花、博风板、悬鱼
# =============================================================================
def build_gable(coll, M):
    """敞开山花：内部梁架 + 暗背景 + 博风板 + 悬鱼 + 排山勾滴"""
    g = Geo()      # 0=暗背景 1=博风木 2=琉璃 3=梁架木
    N = 30
    ys = [-Y1 + 2 * Y1 * i / N for i in range(N + 1)]
    zt = f_main(0.0)
    xa = XG - 0.42                 # 梁架所在平面
    for sx in (1, -1):
        # 内部暗背景（退进 2.1m，形成阴影底衬，同时挡住对面山花）
        xi = sx * (XG - 2.10)
        bg = [[(xi, y, Z_BASE - 0.55) for y in ys], [(xi, y, f_main(y) - 0.46) for y in ys]]
        _surf_dir(g, bg, 0, (sx, 0, 0))
        # 山花底边封檐板
        g.box((sx * (XG - 1.05), 0, Z_BASE - 0.28), (2.20, 2 * Y1 + 0.10, 0.58), mat=3)
        # —— 内部梁架（细木作，深色，处于阴影中）——
        xm = sx * xa
        # 承椽枋（山花底枋）
        g.box((xm, 0, Z_BASE + 0.22), (0.50, 2 * Y1 - 0.16, 0.42), mat=3)
        # 下丁栿
        g.box((xm, 0, Z_BASE + 1.55), (0.48, 11.0, 0.46), mat=3)
        # 太平梁
        g.box((xm, 0, Z_BASE + 3.35), (0.44, 5.4, 0.38), mat=3)
        # 脊瓜柱
        g.box((xm, 0, (Z_BASE + 3.35 + zt - 0.46) / 2),
              (0.34, 0.34, zt - 0.46 - (Z_BASE + 3.35)), mat=3)
        # 瓜柱
        for sy in (1, -1):
            g.box((xm, sy * 2.55, Z_BASE + 2.45), (0.32, 0.32, 1.44), mat=3)
            g.box((xm, sy * 5.30, Z_BASE + 0.88), (0.30, 0.30, 0.92), mat=3)
        # 叉手（斜撑）：自太平梁端至脊瓜柱上段
        for sy in (1, -1):
            p0 = Vector((xm, sy * 2.70, Z_BASE + 3.35))
            p1 = Vector((xm, sy * 0.72, zt - 1.05))
            g.cyl(p0, p1, 0.13, 6, mat=3)
        # 山花外框（沿三角边缘的窄边框）
        for sy in (1, -1):
            pts = []
            for i in range(15):
                y = sy * Y1 * i / 14
                pts.append((sx * (XG + 0.06), y, f_main(y) - 0.26))
            g.sweep(pts, 0.10, 0.24, mat=1, up=Vector((0, 0, 1)))
        g.box((sx * (XG + 0.06), 0, Z_BASE + 0.08), (0.10, 2 * Y1 - 0.24, 0.18), mat=1)
        # 博风板：沿两坡斜边
        for sy in (1, -1):
            pts = []
            for i in range(21):
                y = sy * Y1 * i / 20
                pts.append((sx * (XG + 0.16), y, f_main(y) + 0.02))
            g.sweep(pts, 0.13, 0.56, mat=1, up=Vector((0, 0, 1)))
        # 悬鱼
        zv = H_RIDGE - 1.45
        g.box((sx * (XG + 0.20), 0, zv), (0.10, 0.60, 0.90), mat=1)
        g.box((sx * (XG + 0.20), 0, zv - 0.62), (0.10, 0.34, 0.40), mat=1)
        g.cyl((sx * (XG + 0.20), 0, zv - 0.84), (sx * (XG + 0.20), 0, zv - 1.22), 0.05, 8, mat=1)
        # 排山勾滴
        for sy in (1, -1):
            for i in range(14):
                t = 0.05 + 0.90 * i / 13
                y = sy * Y1 * t
                g.cyl((sx * (XG + 0.10), y, f_main(y) - 0.16),
                      (sx * (XG + 0.26), y, f_main(y) - 0.18), 0.055, 8, mat=2)
    return g.build("山花与博风板", coll,
                   [M["dark"], M["wood"], M["glaze"], M["timber"]], box_uv=True)


# =============================================================================
# 十二、匾额
# =============================================================================
def build_plaque(coll, M):
    g = Geo()
    cx, cy = 0, YS[0] - 0.98
    z0, z1 = 5.05, 8.55
    hw = 0.85
    g.box((cx, cy, (z0 + z1) / 2), (hw * 2, 0.13, z1 - z0), mat=0)
    # 边框
    g.box((cx, cy - 0.06, z0 + 0.07), (hw * 2 + 0.13, 0.16, 0.18), mat=1)
    g.box((cx, cy - 0.06, z1 - 0.07), (hw * 2 + 0.13, 0.16, 0.18), mat=1)
    for s in (-1, 1):
        g.box((cx + s * hw, cy - 0.06, (z0 + z1) / 2), (0.16, 0.16, z1 - z0), mat=1)
    # 吊挂
    for s in (-1, 1):
        g.cyl((cx + s * 0.52, cy, z1), (cx + s * 0.52, cy, z1 + 0.42), 0.026, 6, mat=1)
    obj = g.build("匾额", coll, [M["plaque"], M["wood_r"]], box_uv=True)

    # 金色榜书（文字转网格）
    try:
        cu = bpy.data.curves.new("plaque_text", 'FONT')
        cu.body = "弥\n陀\n殿"
        cu.align_x = 'CENTER'
        cu.align_y = 'CENTER'
        cu.size = 0.92
        cu.space_line = 0.96
        cu.extrude = 0.012
        fnt = bpy.data.fonts.load("C:/Windows/Fonts/STZHONGS.TTF")
        cu.font = fnt
        tob = bpy.data.objects.new("匾额榜书", cu)
        coll.objects.link(tob)
        tob.location = (cx, cy - 0.10, (z0 + z1) / 2 - 0.16)
        tob.rotation_euler = (math.radians(90), 0, 0)
        bpy.context.view_layer.objects.active = tob
        for o in bpy.context.selected_objects:
            o.select_set(False)
        tob.select_set(True)
        bpy.ops.object.convert(target='MESH')
        tob = bpy.context.view_layer.objects.active
        tob.data.materials.append(M["gold"])
        if not tob.data.uv_layers:
            tob.data.uv_layers.new(name="UVMap")
        from cf_lib import box_project_uv
        box_project_uv(tob.data, 1.0)
    except Exception as e:
        print("[plaque] text failed:", e)
    return obj


# =============================================================================
# 十三、陈设：香炉、石狮、栏杆
# =============================================================================
def build_smoker(coll, M):
    g = Geo()
    x, y = 0, YS[0] - 11.2
    z0 = GROUND_Z
    # 须弥座
    g.frustum((x, y, z0 + 0.14), (1.40, 1.40), (1.24, 1.24), 0.28, mat=1)
    g.box((x, y, z0 + 0.34), (1.20, 1.20, 0.16), mat=1)
    # 三足
    for i in range(3):
        a = math.radians(90 + i * 120)
        px, py = x + 0.40 * math.cos(a), y + 0.40 * math.sin(a)
        g.cyl((px, py, z0 + 0.40), (px * 1.06, py * 1.06, z0 + 0.86), 0.085, 8, mat=0)
        g.frustum((px, py, z0 + 0.50), (0.22, 0.22), (0.16, 0.16), 0.16, mat=0)
    # 炉身
    g.frustum((x, y, z0 + 1.16), (0.95, 0.95), (1.16, 1.16), 0.62, mat=0)
    g.frustum((x, y, z0 + 1.56), (1.16, 1.16), (1.02, 1.02), 0.24, mat=0)
    g.box((x, y, z0 + 1.70), (1.30, 1.30, 0.10), mat=0)
    # 双耳
    for s in (-1, 1):
        g.box((x + s * 0.68, y, z0 + 1.62), (0.10, 0.42, 0.46), mat=0)
    # 炉盖（多层塔式）
    g.frustum((x, y, z0 + 1.86), (1.06, 1.06), (0.80, 0.80), 0.24, mat=0)
    g.frustum((x, y, z0 + 2.08), (0.80, 0.80), (0.56, 0.56), 0.24, mat=0)
    g.box((x, y, z0 + 2.24), (0.66, 0.66, 0.08), mat=0)
    g.frustum((x, y, z0 + 2.40), (0.52, 0.52), (0.34, 0.34), 0.26, mat=0)
    g.cyl((x, y, z0 + 2.52), (x, y, z0 + 2.95), 0.055, 8, mat=0)
    g.frustum((x, y, z0 + 2.66), (0.18, 0.18), (0.06, 0.06), 0.14, mat=0)
    # 炉口沿
    g.cyl((x, y, z0 + 1.74), (x, y, z0 + 1.80), 0.66, 16, mat=0)
    return g.build("铜香炉", coll, [M["bronze"], M["stone_d"]], smooth=False)


def build_lion(coll, M, px, py, face=-1):
    g = Geo()
    s = 1.0
    # 须弥座
    g.box((px, py, 0.52), (1.05, 0.80, 1.04), mat=1)
    g.box((px, py, 1.10), (0.86, 0.66, 0.12), mat=1)
    g.box((px, py, 0.05), (1.25, 0.95, 0.10), mat=1)
    z0 = 1.16
    # 后胯
    g.frustum((px, py + 0.18 * face, z0 + 0.40), (0.62, 0.78), (0.52, 0.66), 0.80, mat=0)
    # 胸
    g.frustum((px, py - 0.30 * face, z0 + 0.52), (0.66, 0.70), (0.54, 0.60), 0.95, mat=0)
    # 前腿
    for sx in (-1, 1):
        g.box((px + sx * 0.26, py - 0.48 * face, z0 + 0.24), (0.20, 0.24, 0.52), mat=0)
        g.box((px + sx * 0.26, py - 0.58 * face, z0 + 0.04), (0.24, 0.36, 0.12), mat=0)
    # 头
    g.frustum((px, py - 0.42 * face, z0 + 1.16), (0.60, 0.62), (0.46, 0.50), 0.34, mat=0)
    g.frustum((px, py - 0.62 * face, z0 + 1.02), (0.44, 0.42), (0.34, 0.34), 0.30, mat=0)
    # 吻/鼻
    g.box((px, py - 0.78 * face, z0 + 0.98), (0.30, 0.16, 0.16), mat=0)
    # 鬃毛卷
    for i in range(8):
        a = math.radians(i * 45)
        g.frustum((px + 0.34 * math.cos(a), py - 0.30 * face + 0.34 * math.sin(a), z0 + 1.18),
                  (0.20, 0.20), (0.14, 0.14), 0.22, mat=0)
    # 尾
    g.sweep([(px, py + 0.44 * face, z0 + 0.72), (px, py + 0.56 * face, z0 + 1.20),
             (px, py + 0.40 * face, z0 + 1.48)], 0.22, 0.22, mat=0)
    return g.build("石狮", coll, [M["stone"], M["stone_d"]])


def build_fence(coll, M):
    g = Geo()
    # 两侧花坛木栅栏
    for sx in (-1, 1):
        x0, x1 = sx * 8.0, sx * 19.0
        y0, y1 = -22.5, -16.8
        # 四边
        edges = [((x0, y0), (x1, y0)), ((x0, y1), (x1, y1)),
                 ((x0, y0), (x0, y1)), ((x1, y0), (x1, y1))]
        for (a, b) in edges:
            n = max(2, int(abs(b[0] - a[0] + b[1] - a[1]) / 0.55))
            for i in range(n):
                t = i / n
                px = a[0] + (b[0] - a[0]) * t
                py = a[1] + (b[1] - a[1]) * t
                g.box((px, py, -1.8 + 0.31), (0.05, 0.05, 0.62), mat=0)
            for zz in (0.46, 0.16):
                g.box(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, -1.8 + zz),
                      (abs(b[0] - a[0]) + 0.06, abs(b[1] - a[1]) + 0.06, 0.05), mat=0)
    return g.build("朱漆栅栏", coll, [M["red_paint"]])


# =============================================================================
# 十四、环境（地面、柏树）
# =============================================================================
def build_ground(coll, M, z=-1.8):
    g = Geo()
    g.box((0, -6, z - 0.10), (190, 170, 0.20), mat=0)
    # 甬道（中间石板路）
    g.box((0, -34, z + 0.012), (9.0, 26, 0.02), mat=0)
    g.build("铺地与甬道", coll, [M["brick"], M["stone_d"]])

    # 花坛土面
    g = Geo()
    for sx in (-1, 1):
        g.box((sx * 13.5, -19.6, z + 0.18), (11.0, 5.4, 0.36), mat=0)
    g.build("花坛", coll, [flat("泥土", (0.16, 0.115, 0.08), rough=0.95)])


def build_tree(coll, M, px, py, h=9.0, seed=1):
    import random
    rnd = random.Random(seed)
    g = Geo()
    z0 = -1.8
    g.cyl((px, py, z0), (px, py, z0 + h * 0.45), 0.28, 10, mat=0, r1=0.20)
    for i in range(3):
        a = rnd.uniform(0, 6.28)
        g.cyl((px, py, z0 + h * 0.30), (px + math.cos(a) * 1.2, py + math.sin(a) * 1.2, z0 + h * 0.55),
              0.10, 8, mat=0)
    # 树冠：多球叠加 + 噪声扰动
    blobs = [(0, 0, 0.62, 2.75, 2.75), (-0.9, 0.35, 0.50, 2.05, 2.15), (0.85, -0.3, 0.52, 2.1, 2.0),
             (0.15, 0.85, 0.56, 1.85, 1.85), (-0.35, -0.9, 0.54, 1.9, 1.85),
             (0.0, 0.0, 0.80, 2.15, 1.75), (0.0, 0.0, 0.95, 1.5, 1.25),
             (-0.7, -0.2, 0.42, 1.55, 1.6), (0.7, 0.25, 0.44, 1.5, 1.55),
             (0.2, -0.5, 0.74, 1.35, 1.3), (-0.3, 0.5, 0.76, 1.3, 1.25)]
    for (dx, dy, t, rx, rz) in blobs:
        cx = px + dx * 1.4
        cy = py + dy * 1.4
        cz = z0 + h * t
        _blob(g, (cx, cy, cz), (rx, rx * 0.95, rz), seed + int(t * 100), mat=1 if int(t * 10) % 2 else 2)
    return g.build("柏树", coll, [M["bark"], M["leaf"], M["leaf2"]], smooth=True)


def _blob(g, c, r, seed, mat=0, seg=26, rings=16):
    verts = []
    for i in range(rings + 1):
        th = math.pi * i / rings
        for j in range(seg):
            ph = TAU_ * j / seg
            n = 1.0 + 0.085 * math.sin(3 * ph + seed) * math.sin(2 * th + seed * 0.7) \
                + 0.05 * math.sin(7 * ph + 2 * th + seed)
            verts.append((c[0] + r[0] * n * math.sin(th) * math.cos(ph),
                          c[1] + r[1] * n * math.sin(th) * math.sin(ph),
                          c[2] + r[2] * n * math.cos(th)))
    faces = []
    for i in range(rings):
        for j in range(seg):
            a = i * seg + j
            b = i * seg + (j + 1) % seg
            c2 = (i + 1) * seg + (j + 1) % seg
            d = (i + 1) * seg + j
            faces.append((a, b, c2, d))
    g.add(verts, faces, mat)


TAU_ = math.pi * 2


# =============================================================================
# 十五、场景装配
# =============================================================================
def setup_world(sun_az=125, sun_el=26):
    """渐变天空：天顶深蓝 → 地平淡青，营造晴天氛围"""
    scene = bpy.context.scene
    world = bpy.data.worlds.new("Sky")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld"); out.location = (400, 0)
    bg = nt.nodes.new("ShaderNodeBackground"); bg.location = (200, 0)
    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-600, 0)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); sep.location = (-420, 0)
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.location = (-220, 0)
    cr = ramp.color_ramp
    cr.elements[0].position = 0.0
    cr.elements[0].color = (0.560, 0.660, 0.830, 1.0)
    cr.elements[1].position = 0.30
    cr.elements[1].color = (0.150, 0.290, 0.620, 1.0)
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.95
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])


def setup_render(cam, res=(1600, 900), samples=200):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'GPU'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.preview_samples = 16
    scene.cycles.max_bounces = 6
    scene.cycles.diffuse_bounces = 3
    scene.cycles.glossy_bounces = 3
    scene.cycles.transmission_bounces = 2
    scene.cycles.use_fast_gi = True
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.exposure = 0.42
    try:
        scene.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass
    scene.camera = cam
    # OptiX
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'OPTIX'
        prefs.get_devices()
        for d in prefs.devices:
            d.use = (d.type == 'OPTIX')
    except Exception as e:
        print("OptiX setup failed", e)


def main():
    clear_scene()
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    T = cf_tex.build_all()
    M = make_materials(T)

    c_site = new_coll("00_场地与台基")
    c_frame = new_coll("01_柱额与墙体")
    c_door = new_coll("02_隔扇门")
    c_dg = new_coll("03_斗拱")
    c_eave = new_coll("04_檐椽与飞椽")
    c_roof = new_coll("05_屋面与瓦垄")
    c_ridge = new_coll("06_屋脊与脊饰")
    c_gable = new_coll("07_山花博风")
    c_prop = new_coll("08_陈设与小品")
    c_env = new_coll("09_环境")

    build_platform(c_site, M)
    build_frame(c_frame, M)
    build_walls(c_frame, M)
    build_doors(c_door, M)
    place_dougong(c_dg, M, dougong_clusters())
    build_eave(c_eave, M)
    build_roof(c_roof, M)
    build_tiles(c_roof, M)
    build_eave_tiles(c_roof, M)
    build_ridges(c_ridge, M)
    build_gable(c_gable, M)
    build_plaque(c_prop, M)
    build_smoker(c_prop, M)
    build_ground(c_env, M, z=GROUND_Z)
    # 环境保持净空（与参考图一致，不放置树木）

    # 灯光
    sun = sun_setup((0.52, 0.64, -0.57), energy=3.30, color=(1.0, 0.940, 0.835), angle=0.38)
    sun.location = (-40, -50, 45)
    fill = bpy.data.lights.new("SkyFill", 'AREA')
    fill.energy = 130
    fill.size = 40
    fill.color = (0.62, 0.75, 1.0)
    fobj = bpy.data.objects.new("SkyFill", fill)
    scene.collection.objects.link(fobj)
    fobj.location = (45, -55, 28)
    fobj.rotation_euler = (Vector((0, 0, 8)) - fobj.location).to_track_quat('-Z', 'Y').to_euler()
    fobj.visible_camera = False
    setup_world()

    # 相机
    cam_a = camera("相机_正面", (0, -56, 2.8), (0, -1, 9.6), lens=35)
    cam_b = camera("相机_转角", (-52.0, -43.0, 3.8), (0, 0.5, 9.4), lens=32)
    cam_c = camera("相机_细部", (-13.2, -23.5, 5.2), (-13.8, -12.4, 8.5), lens=54)
    cam_d = camera("相机_门前", (7.5, -26.5, 1.55), (-1.0, -12.6, 6.6), lens=42)
    scene.camera = cam_a
    setup_render(cam_a)

    # 参数空物体，便于在 Blender 中查看/调整
    emp = bpy.data.objects.new("PARAMS_弥陀殿", None)
    emp.empty_display_type = 'PLAIN_AXES'
    emp.empty_display_size = 2
    scene.collection.objects.link(emp)
    for k, v in P.items():
        if isinstance(v, (int, float)):
            emp[k] = v
    emp["说明"] = "尺寸单位为米；修改后需运行 scripts/rebuild.py 重新生成几何"

    notes = bpy.data.texts.new("00_模型说明")
    notes.write("""崇福寺弥陀殿 · 参数化三维复原（Blender 5.0.1）
=====================================================
依据：用户提供的正面全景与转角近景照片（金代原构特征）
坐标：X=面阔方向，Y=进深方向（-Y 为正面），Z=高度，单位：米，1 单位 = 1 米

主要可调参数（PARAMS_弥陀殿 物体上的自定义属性，与下方一致）：
  bay_x        面阔七间各间广（5.6/5.8/5.9/6.0/5.9/5.8/5.6 米，合计 40.6 m）
  bay_y        进深四间各间深（6.2 米 x4，合计 24.8 m）
  col_h        檐柱高 7.00 m       col_r        檐柱半径 0.33 m
  platform_h   台基高 2.00 m       platform_x/y 台基半宽/半深 24.6 / 16.6 m
                院坪标高 -1.30 m，故台明露出 1.30 m、埋深 0.70 m
  eave_out     出檐 4.60 m         eave_z       檐口高 9.10 m（相对台面上皮）
  ridge_rise   举高 11.20 m（脊高 20.30 m，含台基总高约 21.6 m）
  shoushan     歇山收山 4.60 m     gable_y      山花底边半宽 8.60 m
  corner_rise  翼角起翘 2.55 m     tile_gap     瓦垄间距 0.34 m
  wall_t       墙厚 0.55 m         white_base   白灰墙基高 1.05 m
  dougong_jian 每间补间铺作数 3（七铺作双杪双下昂）
  door_bays    设隔扇门的间序（0~6 全部七间，明间敞开）

屋面数学（本版核心）：
  z(x,y) = min( 长坡 f_main(y), 撒头 h_end(x) ) + 翼角起翘 corner_lift(x,y)
  戗脊 = 二者交线，由 hip_y(x)/hip_x(y) 二分法求解，两片几何必然贴合。
  长坡拆为「正身中段 |x|<=收山线」「两端翼角段」「两山撒头」三片独立网格，
  山花处于三片之间，因此天然敞开，内部另建丁栿/太平梁/脊瓜柱/叉手与暗背景。

修改参数后重新生成：运行 scripts/cf_build.py（需 Blender 5.x）
  blender -b -P scripts/cf_build.py
渲染：blender -b Blender_崇福寺弥陀殿.blend -P scripts/cf_render.py -- 相机_正面 256 1920 1080 out.png

构件集合：
  00_场地与台基  01_柱额与墙体  02_隔扇门  03_斗拱  04_檐椽与飞椽
  05_屋面与瓦垄  06_屋脊与脊饰  07_山花博风  08_陈设与小品  09_环境
""")
    blend = os.path.join(ROOT, "Blender_崇福寺弥陀殿.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    print("[save]", blend)

    # 统计
    total_v = sum(len(o.data.vertices) for o in bpy.data.objects if o.type == 'MESH')
    print("[stats] objects=%d verts=%d" % (
        len([o for o in bpy.data.objects if o.type == 'MESH']), total_v))


if __name__ == "__main__":
    main()
