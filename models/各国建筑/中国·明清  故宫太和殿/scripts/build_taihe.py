# -*- coding: utf-8 -*-
"""
故宫太和殿 高精度 Blender 建模
build_taihe.py

坐标约定：X = 面阔方向，Y = 进深方向（-Y 为正面/南），Z = 高度
单位：米     台基顶面 z = 8.13，地面 z = 0
"""
import bpy
import bmesh
import sys
import os
import math
import random

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else r"D:\技能大赛\各国建筑\故宫太和殿\scripts"
sys.path.insert(0, HERE)
import importlib
import lib_taihe
importlib.reload(lib_taihe)
from lib_taihe import *
from mathutils import Vector, Matrix, Euler

random.seed(20261112)

OUT_DIR = r"D:\技能大赛\各国建筑\故宫太和殿"
TEX_DIR = os.path.join(OUT_DIR, "textures")
os.makedirs(TEX_DIR, exist_ok=True)

# ============================================================================
# 一、总体尺寸参数（依《太和殿》实测数据折算）
# ============================================================================
W_TOTAL = 60.0          # 通面阔 60.01m（十一间）
D_TOTAL = 33.3          # 通进深 33.33m（五间）
H_TERRACE = 8.13        # 三台总高
H_BUILD = 26.92         # 殿身高（台基以上）
Z_TT = H_TERRACE        # 三台顶
H_TAIMING = 0.95        # 台明高
Z_FLOOR = Z_TT + H_TAIMING      # 9.08 殿内地面/檐廊地面
H_COL = 12.55           # 檐柱高
Z_ECOL = Z_FLOOR + H_COL        # 21.63 檐柱顶

Z_RIDGE = Z_TT + H_BUILD        # 35.05 正脊顶面

BAYS_X = [5.0, 5.05, 5.15, 5.3, 5.5, 8.0, 5.5, 5.3, 5.15, 5.05, 5.0]
BAYS_Y = [5.6, 6.9, 8.3, 6.9, 5.6]

def cum(bays, start):
    out = [start]
    for b in bays:
        out.append(out[-1] + b)
    return out

XS = cum(BAYS_X, -sum(BAYS_X) / 2)      # 12 根
YS = cum(BAYS_Y, -sum(BAYS_Y) / 2)      # 6 根

R_COL = 0.315          # 檐柱半径 d≈0.63
R_JIN = 0.44           # 金柱半径

# 下檐
Z_EAVE1 = Z_ECOL + 2.82                 # 24.45 下檐檐口（抬高以容纳斗拱层）
HX1, HY1 = 32.95, 19.7                  # 下檐出檐后平面
HX1_IN, HY1_IN = 27.2, 14.35            # 下檐上端（围脊）
Z_TOP1 = 25.60                          # 下檐上端高度
# 上檐
HX2, HY2 = 31.6, 18.75
Z_EAVE2 = 28.85
RIDGE_HX, RIDGE_HY = 14.0, 0.95
Z_RIDGE_C = Z_RIDGE - 0.92
P_LOW, LIFT_LOW = 2.45, 0.55            # 下檐举折指数 / 翼角起翘
P_UP, LIFT_UP = 2.85, 0.78              # 上檐
LIFT_SC = 4.8                           # 翼角影响半径

# 殿身（墙体内侧）
HXW, HYW = 27.2, 13.85


def build_materials():
    M = {}
    # 生成程序化贴图
    p_hexi = os.path.join(TEX_DIR, "caihua_hexi.png")
    p_hexi2 = os.path.join(TEX_DIR, "caihua_hexi_green.png")
    if not os.path.exists(p_hexi):
        make_caihua_image(p_hexi, 2048, 256, "hexi", 3)
    if not os.path.exists(p_hexi2):
        make_caihua_image(p_hexi2, 2048, 256, "hexi2", 9)
    M['tile'] = mat_glazed_tile()
    M['tile_dark'] = mat_simple("MAT_瓦_板瓦", (0.20, 0.088, 0.014), 0.55)
    M['tile_dark'].node_tree.nodes['Principled BSDF'].inputs['Coat Weight'].default_value = 0.3
    M['red'] = mat_lacquer("MAT_朱红大漆", (0.365, 0.055, 0.035), 0.42, 0.42)
    M['red_deep'] = mat_lacquer("MAT_朱红_墙", (0.315, 0.052, 0.038), 0.55, 0.5, 1.1)
    M['green'] = mat_lacquer("MAT_石绿", (0.055, 0.20, 0.145), 0.5, 0.4, 2.0)
    M['blue'] = mat_lacquer("MAT_石青", (0.055, 0.155, 0.255), 0.5, 0.4, 2.0)
    M['marble'] = mat_marble()
    M['gold'] = mat_gold()
    M['wood'] = mat_wood()
    M['stone'] = mat_simple("MAT_墁地金砖", (0.30, 0.29, 0.275), 0.62)
    M['ground'] = mat_simple("MAT_广场石", (0.34, 0.33, 0.315), 0.66)
    M['plaque'] = mat_simple("MAT_匾额_群青", (0.035, 0.075, 0.24), 0.4, coat=0.4)
    M['bronze'] = mat_simple("MAT_铜器", (0.16, 0.13, 0.08), 0.42, 1.0)
    M['dark'] = mat_simple("MAT_殿内暗部", (0.085, 0.055, 0.042), 0.85)
    M['caihua'] = mat_caihua_image("MAT_彩画_和玺",
                                   os.path.join(TEX_DIR, "caihua_hexi.png"))
    M['caihua2'] = mat_caihua_image("MAT_彩画_和玺_绿",
                                    os.path.join(TEX_DIR, "caihua_hexi_green.png"))
    M['rafter'] = mat_lacquer("MAT_椽头彩画", (0.052, 0.16, 0.23), 0.5, 0.3, 3.0)
    return M


# ============================================================================
# 二、台基：三台 + 栏板 + 踏跺 + 御路
# ============================================================================
def build_terrace(M, coll):
    tier_h = H_TERRACE / 3.0
    tiers = [(44.0, 31.0), (40.0, 27.0), (36.0, 23.0)]   # 半宽、半深
    mb = MB()
    mi_m = 0
    for i, (hx, hy) in enumerate(tiers):
        z0 = i * tier_h
        z1 = z0 + tier_h
        # 圭角
        mb.box((0, 0, z0 + 0.16), (2 * hx, 2 * hy, 0.32), mi_m)
        # 下枋
        mb.box((0, 0, z0 + 0.55), (2 * hx, 2 * hy, 0.46), mi_m)
        # 束腰（内收）
        mb.box((0, 0, z0 + 1.35), (2 * hx - 0.36, 2 * hy - 0.36, 1.15), mi_m)
        # 上枋 + 压面石
        mb.box((0, 0, z1 - 0.5), (2 * hx, 2 * hy, 1.0), mi_m)
        mb.box((0, 0, z1 - 0.06), (2 * hx + 0.16, 2 * hy + 0.16, 0.12), mi_m)
    ob = mb.build("T01_三台_须弥座", coll, [M['marble']])
    add_bevel(ob, 0.02, 2)

    # 台面铺地
    mb2 = MB()
    mb2.box((0, 0, Z_TT - 0.02), (71.8, 45.8, 0.1), 0)
    mb2.build("T02_三台_台面", coll, [M['stone']])

    # 各层栏板望柱
    bal = MB()
    for i, (hx, hy) in enumerate(tiers):
        zt = (i + 1) * tier_h
        perim = balustrade_ring(bal, hx + 0.06, hy + 0.06, zt, 0)
    o = bal.build("T03_三台_栏板望柱", coll, [M['marble']])
    add_bevel(o, 0.008, 1)

    # 螭首（外沿排水兽）
    mb3 = MB()
    for i, (hx, hy) in enumerate(tiers):
        zt = (i + 1) * tier_h
        for (x, y, dx, dy) in edge_points(hx + 0.14, hy + 0.14, 3.0):
            mb3.box((x + dx * 0.16, y + dy * 0.16, zt - 0.42), (0.34, 0.34, 0.26), 0,
                    rz=math.atan2(dy, dx))
            mb3.sphere((x + dx * 0.42, y + dy * 0.42, zt - 0.40), 0.17, 8, 6, 0,
                       (1.5, 0.8, 0.7))
    o = mb3.build("T04_三台_螭首", coll, [M['marble']])

    # 踏跺（正面三出陛，中间御路）
    build_stairs(M, coll, tiers, tier_h)


def edge_points(hx, hy, step):
    """沿矩形周边等距取点，返回 (x,y,dirx,diry)"""
    pts = []
    n = int((2 * hx) / step)
    for i in range(n):
        x = -hx + (i + 0.5) * (2 * hx / n)
        pts.append((x, -hy, 0, -1))
    n = int((2 * hy) / step)
    for i in range(n):
        y = -hy + (i + 0.5) * (2 * hy / n)
        pts.append((hx, y, 1, 0))
        pts.append((-hx, y, -1, 0))
    n = int((2 * hx) / step)
    for i in range(n):
        x = -hx + (i + 0.5) * (2 * hx / n)
        pts.append((x, hy, 0, 1))
    return pts


def balustrade_ring(mb, hx, hy, z, mi, step=1.75, back=True):
    """一圈栏板望柱"""
    # 地栿
    mb.box((0, -hy, z + 0.11), (2 * hx, 0.34, 0.22), mi)
    mb.box((0, hy, z + 0.11), (2 * hx, 0.34, 0.22), mi)
    mb.box((hx, 0, z + 0.11), (0.34, 2 * hy, 0.22), mi)
    mb.box((-hx, 0, z + 0.11), (0.34, 2 * hy, 0.22), mi)

    def run(p0, p1, nrm):
        L = math.dist(p0, p1)
        n = max(2, int(round(L / step)))
        d = ((p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L)
        for i in range(n):
            a = i / n
            b = (i + 1) / n
            cx = p0[0] + (p1[0] - p0[0]) * (a + b) / 2
            cy = p0[1] + (p1[1] - p0[1]) * (a + b) / 2
            # 栏板
            mb.box((cx, cy, z + 0.72), (L / n - 0.24, 0.20, 0.80), mi,
                   rz=math.atan2(d[1], d[0]))
            mb.box((cx - nrm[0] * 0.02, cy - nrm[1] * 0.02, z + 0.72),
                   (L / n - 0.40, 0.14, 0.52), mi, rz=math.atan2(d[1], d[0]))
            # 望柱
            px = p0[0] + (p1[0] - p0[0]) * a
            py = p0[1] + (p1[1] - p0[1]) * a
            mb.box((px, py, z + 0.66), (0.24, 0.24, 0.92), mi)
            mb.box((px, py, z + 1.16), (0.30, 0.30, 0.12), mi)
            mb.sphere((px, py, z + 1.30), 0.135, 10, 6, mi, (1.0, 1.0, 1.25))

    run((-hx, -hy), (hx, -hy), (0, -1))
    run((hx, -hy), (hx, hy), (1, 0))
    run((-hx, hy), (-hx, -hy), (-1, 0))
    if back:
        run((hx, hy), (-hx, hy), (0, 1))


def build_stairs(M, coll, tiers, tier_h):
    """三出陛：中为御路，两侧踏跺"""
    z_top = H_TERRACE
    hx_top, hy_top = tiers[2]
    y_edge = -hy_top          # -23 顶层前沿
    # 总落差 8.13，每级踏步高 0.155
    rise = 0.155
    tread = 0.30
    n_total = int(round(z_top / rise))
    y0 = y_edge + 0.9
    mb = MB()
    # 三段踏跺，各段之间为平台
    seg_tiers = [0, 1, 2]
    y_cur = y0
    z_cur = z_top
    for seg in range(3):
        n_steps = int(round(tier_h / rise))
        for s in range(n_steps):
            z = z_cur - rise
            mb.box((0, y_cur - tread * 0.5, z + rise / 2),
                   (21.0, tread, rise), 0)
            y_cur -= tread
            z_cur = z
    # 两侧垂带石 + 御路
    mb_steps = mb.build("T05_踏跺", coll, [M['marble']])

    # 御路石（居中，云龙浮雕）
    mb2 = MB()
    yr0 = y_edge + 0.9
    yr1 = y_cur
    L = yr0 - yr1
    ang = math.atan2(H_TERRACE, L)
    # 主斜面
    mb2.box((0, (yr0 + yr1) / 2, H_TERRACE / 2 + 0.06), (5.6, math.hypot(L, H_TERRACE), 0.36),
            0, rx=ang)
    # 边框
    for s in (-1, 1):
        mb2.box((s * 2.95, (yr0 + yr1) / 2, H_TERRACE / 2 + 0.12),
                (0.42, math.hypot(L, H_TERRACE), 0.30), 0, rx=ang)
    # 云龙浮雕：起伏的云头
    rng = random.Random(41)
    for i in range(46):
        u = rng.uniform(0.03, 0.97)
        v = rng.uniform(-2.2, 2.2)
        y = yr0 - u * L
        z = H_TERRACE * (1 - u) + 0.30
        mb2.sphere((v, y, z), rng.uniform(0.18, 0.36), 8, 5, 0,
                   (1.0, 1.5, 0.42))
    # 龙身：一条起伏的脊线
    for i in range(26):
        u = i / 25.0
        y = yr0 - u * L
        z = H_TERRACE * (1 - u) + 0.34
        x = 1.15 * math.sin(u * math.pi * 3.4)
        mb2.sphere((x, y, z), 0.24, 8, 5, 0, (1.0, 1.2, 0.55))
    o = mb2.build("T06_御路石雕", coll, [M['marble']])

    # 踏跺两侧栏板（垂带）
    mb3 = MB()
    for s in (-1, 1):
        # 垂带石
        mb3.beam((s * 11.0, yr0, H_TERRACE + 0.1), (s * 11.0, y_cur, 0.1),
                 1.1, 0.5, 0)
        mb3.beam((s * 11.0, yr0 - 0.05, H_TERRACE + 0.85), (s * 11.0, y_cur - 0.05, 0.85),
                 0.26, 0.95, 0)
    o = mb3.build("T07_垂带", coll, [M['marble']])
    add_bevel(o, 0.01, 1)


# ============================================================================
# 三、柱网 / 墙体
# ============================================================================
def build_columns(M, coll):
    mb = MB()
    for x in XS:
        for y in (YS[0], YS[-1]):
            mb.cyl((x, y, Z_FLOOR), (x, y, Z_ECOL + 0.1), R_COL, 24, 0, R_COL * 0.94)
            mb.cyl((x, y, Z_FLOOR), (x, y, Z_FLOOR + 0.22), R_COL + 0.16, 24, 0, R_COL + 0.10)
    for y in YS[1:-1]:
        for x in (XS[0], XS[-1]):
            mb.cyl((x, y, Z_FLOOR), (x, y, Z_ECOL + 0.1), R_COL, 24, 0, R_COL * 0.94)
            mb.cyl((x, y, Z_FLOOR), (x, y, Z_FLOOR + 0.22), R_COL + 0.16, 24, 0, R_COL + 0.10)
    # 金柱（承上檐）
    for x in XS:
        for y in (YS[1], YS[-2]):
            mb.cyl((x, y, Z_FLOOR), (x, y, Z_TOP1 + 0.2), R_JIN, 20, 0, R_JIN * 0.92)
    o = mb.build("C01_柱网_檐柱金柱", coll, [M['red']])
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def build_walls(M, coll):
    """殿身墙：前后檐装隔扇，两山为红墙"""
    mb = MB()
    z0, z1 = Z_FLOOR, Z_ECOL
    # 两山墙
    for s in (-1, 1):
        mb.box((s * HXW, 0, (z0 + z1) / 2), (0.85, 2 * HYW, z1 - z0), 0)
    # 后檐墙（下槛以上做隔扇）
    mb.box((0, HYW, (z0 + z1) / 2 - 0.2), (2 * HXW, 0.85, z1 - z0 - 0.4), 0)
    # 檐廊地面
    mb.box((0, 0, z0 - 0.03), (2 * HXW + 1.6, 2 * HYW + 1.6, 0.08), 1)
    o = mb.build("W01_殿身墙体", coll, [M['red_deep'], M['stone']])
    return o


def build_facade(M, coll):
    """隔扇门、槛窗、匾额 —— 正面十一间"""
    mb_wood = MB()
    mb_gold = MB()
    mb_dark = MB()
    y_front = -HYW
    y_back = HYW
    for side, yy in ((1, y_front), (-1, y_back)):
        for bi in range(len(XS) - 1):
            x0, x1 = XS[bi] + 0.36, XS[bi + 1] - 0.36
            bw = x1 - x0
            # 每间 4 扇（明间 6 扇）
            n = 6 if bi == 5 else 4
            dw = bw / n
            for k in range(n):
                dx0 = x0 + k * dw
                door_panel(mb_wood, mb_gold, mb_dark, dx0, dx0 + dw, yy, side)
            # 横披窗（门上方）
            lattice(mb_wood, x0, x1, yy, Z_ECOL - 1.05, Z_ECOL - 0.15, side, 0.055)
    ob = mb_wood.build("D01_隔扇门_木作", coll, [M['wood']])
    add_bevel(ob, 0.006, 1)
    mb_gold.build("D02_隔扇门_金饰", coll, [M['gold']])
    mb_dark.build("D03_殿内暗腔", coll, [M['dark']])


def door_panel(mb, mbg, mbd, x0, x1, y, side, z0=None, h=None):
    """一扇隔扇：边梃 + 格心 + 绦环板 + 裙板"""
    z0 = Z_FLOOR if z0 is None else z0
    h = (Z_ECOL - 1.15 - z0) if h is None else h
    w = x1 - x0
    t = 0.11
    yy = y
    xm = (x0 + x1) / 2
    # 边框（边梃）
    for xx in (x0 + 0.045, x1 - 0.045):
        mb.box((xx, yy, z0 + h / 2), (0.09, t, h), 0)
    # 抹头
    for zz in (0.97, 0.94, 0.42, 0.385, 0.05, 0.02):
        mb.box((xm, yy, z0 + h * zz), (w, t * 1.02, 0.10), 0)
    # 格心（上段）：透空菱花格
    gz0, gz1 = z0 + h * 0.435, z0 + h * 0.925
    lattice(mb, x0 + 0.10, x1 - 0.10, yy, gz0, gz1, side, 0.038, 0.155)
    mbd.box((xm, yy + side * 0.16, (gz0 + gz1) / 2), (w - 0.10, 0.03, gz1 - gz0), 0)
    # 绦环板
    mb.box((xm, yy, z0 + h * 0.403), (w - 0.12, t * 0.85, h * 0.035), 0)
    mbg.box((xm, yy - side * t * 0.44, z0 + h * 0.403), (w - 0.30, 0.006, 0.022), 0)
    # 裙板（浮雕云龙：木质浅浮雕 + 细金线）
    mb.box((xm, yy, z0 + h * 0.215), (w - 0.10, t * 0.9, h * 0.33), 0)
    mb.box((xm, yy - side * t * 0.48, z0 + h * 0.215), (w - 0.26, 0.022, h * 0.255), 0)
    mbg.box((xm, yy - side * t * 0.55, z0 + h * 0.215), (w - 0.30, 0.006, 0.022), 0)
    for zz in (0.085, 0.345):
        mbg.box((xm, yy - side * t * 0.55, z0 + h * zz), (w - 0.30, 0.006, 0.018), 0)
    for sx in (-1, 1):
        mbg.box((xm + sx * (w / 2 - 0.15), yy - side * t * 0.55, z0 + h * 0.215),
                (0.018, 0.006, h * 0.26), 0)
    # 团龙浅浮雕
    mb.sphere((xm, yy - side * 0.05, z0 + h * 0.215), 0.14, 10, 6, 0, (1.4, 0.30, 1.0))
    for k in (-1, 1):
        for dz in (0.13, 0.30):
            mb.sphere((xm + k * (w * 0.23), yy - side * 0.05, z0 + h * dz), 0.075, 8, 5, 0,
                      (1.2, 0.28, 0.9))
    # 看叶（金角饰）
    for zz in (0.95, 0.40, 0.035):
        for xx in (x0 + 0.045, x1 - 0.045):
            mbg.box((xx, yy - side * t * 0.52, z0 + h * zz), (0.10, 0.012, 0.13), 0)


def lattice(mb, x0, x1, y, z0, z1, side, bar=0.035, step=0.145):
    """格心：三交六椀菱花（直棂 + 45° 斜棂，交点处贴金钉）"""
    w = x1 - x0
    h = z1 - z0
    nv = max(2, int(round(w / step)))
    nh = max(2, int(round(h / step)))
    for i in range(nv + 1):
        x = x0 + w * i / nv
        mb.box((x, y, (z0 + z1) / 2), (bar, 0.055, h), 0)
    for j in range(nh + 1):
        z = z0 + h * j / nh
        mb.box(((x0 + x1) / 2, y, z), (w, 0.055, bar), 0)
    # 斜棂：每个格子交叉两根
    sw = w / nv
    sh = h / nh
    diag = math.hypot(sw, sh) * 0.92
    ang = math.atan2(sh, sw)
    for i in range(nv):
        for j in range(nh):
            cx = x0 + sw * (i + 0.5)
            cz = z0 + sh * (j + 0.5)
            mb.box((cx, y - 0.004, cz), (diag, 0.032, bar * 0.85), 0, ry=-ang)
            mb.box((cx, y - 0.004, cz), (diag, 0.032, bar * 0.85), 0, ry=ang)


def build_plaque(M, coll):
    """太和殿匾额：蓝底金字，木质边框，竖排，悬于上檐当心间额枋"""
    mb = MB()
    w, h, t = 1.68, 3.30, 0.20          # 竖长形匾额
    y = -14.48
    zc = 26.65
    mb.box((0, y, zc), (w, t, h), 0)                       # 匾身（群青）
    # 金色边框（上下长边 + 左右短边）
    for (dx, dz, sx, sz) in ((0, h / 2, w + 0.22, 0.13), (0, -h / 2, w + 0.22, 0.13),
                             (-w / 2, 0, 0.13, h + 0.22), (w / 2, 0, 0.13, h + 0.22)):
        mb.box((dx, y - t * 0.06, zc + dz), (sx, t + 0.05, sz), 1)
    # 边框内金线
    mb.box((0, y - t * 0.55, zc), (w - 0.20, 0.008, h - 0.20), 2)
    o = mb.build("P01_匾额", coll, [M['plaque'], M['gold'], M['blue']])

    # 文字：竖排（太 / 和 / 殿 自上而下）
    try:
        font = bpy.data.fonts.load(r"C:\Windows\Fonts\simhei.ttf")
        for i, ch in enumerate("太和殿"):
            cu = bpy.data.curves.new("txt_%d" % i, 'FONT')
            cu.body = ch
            cu.font = font
            cu.size = 1.10
            cu.extrude = 0.06
            cu.align_x = 'CENTER'
            cu.align_y = 'CENTER'
            tob = bpy.data.objects.new("P02_匾文_%s" % ch, cu)
            coll.objects.link(tob)
            # 竖排：三个字沿 Z 轴自上而下（i=0 在最上）
            tob.location = (0.0, y - t * 0.72, zc + 1.10 - i * 1.10)
            tob.rotation_euler = (math.radians(90), 0, 0)
            bpy.context.view_layer.objects.active = tob
            tob.select_set(True)
            bpy.ops.object.convert(target='MESH')
            tob.data.materials.append(M['gold'])
            tob.select_set(False)
    except Exception as e:
        print("牌匾文字失败：", e)


# ============================================================================
# 四、额枋 / 斗拱 / 椽头
# ============================================================================
def ring_box(mb, hx, hy, z0, z1, thick, mi, out=0.0):
    """沿矩形的一圈"枋"（四面墙板）"""
    hx += out
    hy += out
    mb.box((0, -hy, (z0 + z1) / 2), (2 * hx, thick, z1 - z0), mi)
    mb.box((0, hy, (z0 + z1) / 2), (2 * hx, thick, z1 - z0), mi)
    mb.box((hx, 0, (z0 + z1) / 2), (thick, 2 * hy, z1 - z0), mi)
    mb.box((-hx, 0, (z0 + z1) / 2), (thick, 2 * hy, z1 - z0), mi)


def build_architrave(M, coll):
    """额枋、平板枋（上下两圈），带彩画贴图 UV"""
    parts = []
    # ---- 下檐额枋（檐柱之间）----
    mb = MB()
    z0, z1 = Z_ECOL - 1.55, Z_ECOL - 0.15
    ring_box(mb, 30.0, 16.65, z0, z1, 0.55, 0)
    ring_box(mb, 30.0, 16.65, z1, z1 + 0.28, 0.62, 0)     # 平板枋
    # 柱头之间的额枋分段（细节：每间一根）
    o = mb.build("B01_下檐额枋", coll, [M['caihua']])
    uv_project_len(o, repeat=1.0)
    parts.append(o)

    # ---- 上檐额枋 ----
    mb = MB()
    z0, z1 = 26.20, 27.20
    ring_box(mb, 27.1, 14.25, z0, z1, 0.5, 0)
    ring_box(mb, 27.1, 14.25, z1, z1 + 0.22, 0.56, 0)
    o = mb.build("B02_上檐额枋", coll, [M['caihua2']])
    uv_project_len(o, repeat=1.0)
    parts.append(o)
    return parts


def uv_project_len(ob, repeat=1.0):
    """按世界坐标做盒式 UV：U 沿水平周长方向，V 沿高度"""
    me = ob.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uvl = me.uv_layers.active.data
    for poly in me.polygons:
        n = poly.normal
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            if abs(n.z) > 0.7:
                u, w = v.x, v.y
            elif abs(n.x) > abs(n.y):
                u, w = v.y, v.z
            else:
                u, w = v.x, v.z
            uvl[li].uv = (u * 0.075 * repeat, (w - 20.0) * 0.42)


def dougong_unit(mb, cx, cy, cz, out, sw, mi_a, mi_b, mi_g, scale=1.0):
    """一组斗拱（外跳五踩），out = 外法线单位向量（2D）"""
    ox, oy = out
    tx, ty = -oy, ox           # 沿檐口切向
    s = scale

    def box(off_t, off_o, z, st, so, sz, mi):
        mb.box((cx + tx * off_t + ox * off_o, cy + ty * off_t + oy * off_o, cz + z * s),
               (st * s, so * s, sz * s), mi, rz=math.atan2(ty, tx))

    # 坐斗
    box(0, 0, 0.17, 0.56, 0.56, 0.34, mi_a)
    # 一层：正心瓜拱（沿檐口）
    box(0, 0, 0.44, 1.55, 0.24, 0.22, mi_b)
    box(-0.60, 0, 0.60, 0.32, 0.34, 0.14, mi_a)
    box(0.60, 0, 0.60, 0.32, 0.34, 0.14, mi_a)
    # 一层：头翘（外跳）
    box(0, 0.42, 0.60, 0.24, 1.25, 0.20, mi_b)
    box(0, 0.95, 0.74, 0.32, 0.34, 0.14, mi_a)
    # 二层：万拱
    box(0, 0.42, 0.78, 1.85, 0.24, 0.22, mi_b)
    box(-0.78, 0.42, 0.94, 0.30, 0.32, 0.14, mi_a)
    box(0.78, 0.42, 0.94, 0.30, 0.32, 0.14, mi_a)
    # 二层：二翘
    box(0, 0.85, 0.92, 0.24, 1.7, 0.20, mi_b)
    box(0, 1.55, 1.06, 0.30, 0.32, 0.14, mi_a)
    # 三层：厢拱 + 耍头
    box(0, 0.85, 1.10, 2.10, 0.24, 0.20, mi_b)
    box(-0.90, 0.85, 1.24, 0.28, 0.30, 0.12, mi_a)
    box(0.90, 0.85, 1.24, 0.28, 0.30, 0.12, mi_a)
    # 昂（斜置，向外下探）
    mb.beam((cx + ox * 0.2, cy + oy * 0.2, cz + 1.30 * s),
            (cx + ox * 1.95, cy + oy * 1.95, cz + 0.98 * s),
            0.22 * s, 0.26 * s, mi_b)
    # 挑檐枋位置
    box(0, 1.85, 1.26, 2.35, 0.22, 0.18, mi_b)
    # 垫拱板
    box(0, 0.05, 0.95, 1.75, 0.10, 0.72, mi_g)


def build_dougong(M, coll, hx, hy, base_z, step=1.16, scale=1.0, name="DG"):
    mb = MB()
    n1 = int(2 * hx / step)
    for i in range(n1):
        x = -hx + (i + 0.5) * (2 * hx / n1)
        dougong_unit(mb, x, -hy, base_z, (0, -1), 0, 0, 1, 2, scale)
        dougong_unit(mb, x, hy, base_z, (0, 1), 0, 0, 1, 2, scale)
    n2 = int(2 * hy / step)
    for i in range(n2):
        y = -hy + (i + 0.5) * (2 * hy / n2)
        dougong_unit(mb, -hx, y, base_z, (-1, 0), 0, 0, 1, 2, scale)
        dougong_unit(mb, hx, y, base_z, (1, 0), 0, 0, 1, 2, scale)
    return mb.build(name, coll, [M['red'], M['green'], M['blue']])


def build_rafters(M, coll, hx, hy, z, drop=0.30, name="R"):
    """檐下椽头"""
    mb = MB()
    step = 0.42
    n1 = int(2 * hx / step)
    for i in range(n1):
        x = -hx + (i + 0.5) * (2 * hx / n1)
        for (y, d) in ((hy, 1), (-hy, -1)):
            mb.cyl((x, y - d * 0.30, z + 0.14), (x, y + d * 0.22, z - 0.10),
                   0.085, 8, 0)
    n2 = int(2 * hy / step)
    for i in range(n2):
        y = -hy + (i + 0.5) * (2 * hy / n2)
        for (x, d) in ((hx, 1), (-hx, -1)):
            mb.cyl((x - d * 0.30, y, z + 0.14), (x + d * 0.22, y, z - 0.10),
                   0.085, 8, 0)
    return mb.build(name, coll, [M['rafter']])


def build_eave_beam(M, coll, hx, hy, z, name="EB"):
    """挑檐枋 / 檐口封板（红色带彩画）"""
    mb = MB()
    ring_box(mb, hx - 0.30, hy - 0.30, z - 0.55, z - 0.12, 0.38, 0)
    o = mb.build(name, coll, [M['red']])
    return o


# ============================================================================
# 五、屋顶
# ============================================================================
def make_roof(name, coll, M, hx, hy, rx, ry, ze, zr, p=1.85, ribs=True,
             rib_space=0.44, lift=1.05, thickness=0.55, rib_r=0.105):
    v, f = hip_roof_mesh(hx, hy, rx, ry, ze, zr, p=p, nx=18, ny=14, nt=34,
                         lift=lift, lift_t=2.4, lift_scale=LIFT_SC)
    mb = MB()
    mb.add(v, f, 0)
    ob = mb.build(name, coll, [M['tile_dark']])
    md = ob.modifiers.new("Solidify", 'SOLIDIFY')
    md.thickness = thickness
    md.offset = -1.0
    md.use_even_offset = True
    # 平滑
    for pol in ob.data.polygons:
        pol.use_smooth = True
    if ribs:
        make_roof_ribs(name + "_瓦垄", coll, M, hx, hy, rx, ry, ze, zr,
                       p, rib_space, lift, rib_r)
    return ob


def roof_pt(u, t, side, hx, hy, rx, ry, ze, zr, p, lift):
    """u: 沿檐口方向的归一化坐标(-1..1)"""
    t = min(1.0, max(0.0, t))
    a = rx + (hx - rx) * t
    b = ry + (hy - ry) * t
    _u = 1.0 - t
    z = ze + (zr - ze) * (0.55 * _u + 0.45 * _u ** 1.9)
    if side in ('F', 'B'):
        x = u * a
        y = b if side == 'F' else -b
    else:
        y = u * b
        x = a if side == 'R' else -a
    d = min(math.hypot(x - sx * a, y - sy * b) for sx in (-1, 1) for sy in (-1, 1))
    w = max(0.0, 1.0 - d / LIFT_SC) ** 2
    zz = z + lift * (w ** 1.5) * (t ** 2.4)
    sc = 1.0 + 0.007 * (w ** 2) * (t ** 2)
    return (x * sc, y * sc, zz)


def make_roof_ribs(name, coll, M, hx, hy, rx, ry, ze, zr, p, spacing, lift, rib_r):
    mb = MB()
    mb_wd = MB()
    nt = 24
    # 前后坡：沿 X 方向的瓦垄
    n_full = int(2 * hx / spacing)
    for i in range(n_full + 1):
        x = -hx + i * (2 * hx / n_full)
        t_start = 0.0 if abs(x) < rx else (abs(x) - rx) / (hx - rx)
        t_start = max(0.0, min(0.97, t_start))
        for side in ('F', 'B'):
            pts = []
            for k in range(nt + 1):
                t = t_start + (1.0 - t_start) * k / nt
                a = rx + (hx - rx) * t
                u = x / a if a > 1e-6 else 0
                pts.append(roof_pt(u, t, side, hx, hy, rx, ry, ze, zr, p, lift))
            tube(mb, pts, rib_r, 0, 8, tuck=0.12)
            tile_end(mb_wd, pts[-1], pts[-2], rib_r)
    # 两山坡：沿 Y 方向的瓦垄
    n_full = int(2 * hy / spacing)
    for i in range(n_full + 1):
        y = -hy + i * (2 * hy / n_full)
        t_start = 0.0 if abs(y) < ry else (abs(y) - ry) / (hy - ry)
        t_start = max(0.0, min(0.97, t_start))
        for side in ('R', 'L'):
            pts = []
            for k in range(nt + 1):
                t = t_start + (1.0 - t_start) * k / nt
                b = ry + (hy - ry) * t
                u = y / b if b > 1e-6 else 0
                pts.append(roof_pt(u, t, side, hx, hy, rx, ry, ze, zr, p, lift))
            tube(mb, pts, rib_r, 0, 8, tuck=0.12)
            tile_end(mb_wd, pts[-1], pts[-2], rib_r)
    o = mb.build(name, coll, [M['tile']], smooth=True)
    mb_wd.build(name + "_瓦当", coll, [M['tile']], smooth=True)
    return o


def tile_end(mb, pe, pin, r):
    """瓦当+滴水：檐口圆瓦头 + 下垂三角滴水，形成锯齿状檐口轮廓"""
    d = Vector(pe) - Vector(pin)
    if d.length < 1e-6:
        return
    d.normalize()
    # 瓦当中心：沿瓦垄走向向外延伸，圆盘面朝檐口外侧
    p0 = Vector(pe) + d * 0.03
    p1 = p0 + d * 0.22
    r_w = max(0.32, r * 2.0)
    mb.cyl(tuple(p0), tuple(p1), r_w, 12, 0)
    # 瓦当正面圆形凸起（钉帽纹）
    pn = p1 + d * 0.02
    mb.cyl(tuple(pn), tuple(pn + d * 0.03), r_w * 0.5, 8, 0)
    # 滴水：瓦当下方下垂的三角形如意头（切向方向排布）
    half = r_w * 0.85
    tip = Vector((p1.x, p1.y, p1.z - 0.52))
    if abs(d.y) > abs(d.x):
        s1 = Vector((p1.x - half, p1.y, p1.z - 0.02))
        s2 = Vector((p1.x + half, p1.y, p1.z - 0.02))
    else:
        s1 = Vector((p1.x, p1.y - half, p1.z - 0.02))
        s2 = Vector((p1.x, p1.y + half, p1.z - 0.02))
    mb.loft([[tuple(s1), tuple(s2), tuple(tip)],
             [tuple(s1 + d * 0.05), tuple(s2 + d * 0.05), tuple(tip + d * 0.05)]],
            0, close_bottom=True, close_top=True)


def tube(mb, pts, r, mi, seg=6, tuck=0.0):
    """沿折线生成半圆柱形瓦垄"""
    if len(pts) < 2:
        return
    rings = []
    for i, p in enumerate(pts):
        if i == 0:
            d = Vector(pts[1]) - Vector(pts[0])
        elif i == len(pts) - 1:
            d = Vector(pts[-1]) - Vector(pts[-2])
        else:
            d = Vector(pts[i + 1]) - Vector(pts[i - 1])
        if d.length < 1e-9:
            continue
        d.normalize()
        ref = Vector((0, 0, 1))
        if abs(d.dot(ref)) > 0.98:
            ref = Vector((0, 1, 0))
        x = ref.cross(d).normalized()
        y = d.cross(x).normalized()
        z = -d * tuck if tuck else Vector((0, 0, 0))
        ring = []
        for k in range(seg + 1):
            a = math.pi * k / seg
            ring.append(tuple(Vector(p) + x * (math.cos(a) * r) + y * (math.sin(a) * r) + z))
        rings.append(ring)
    mb.loft(rings, mi, closed_ring=False)


def build_roofs(M, coll1, coll2):
    # 下檐（重檐下层）
    make_roof("RF01_下檐屋面", coll1, M, HX1, HY1, HX1_IN, HY1_IN, Z_EAVE1, Z_TOP1,
              p=P_LOW, rib_space=0.40, lift=LIFT_LOW, thickness=0.5, rib_r=0.145)
    # 上檐
    make_roof("RF02_上檐屋面", coll2, M, HX2, HY2, RIDGE_HX, RIDGE_HY, Z_EAVE2,
              Z_RIDGE_C, p=P_UP, rib_space=0.40, lift=LIFT_UP, thickness=0.62, rib_r=0.155)


# ============================================================================
# 六、屋脊 / 吻兽 / 走兽
# ============================================================================
def build_ridges(M, coll):
    mb = MB()
    # ---- 正脊 ----
    zc = Z_RIDGE_C
    mb.box((0, 0, zc + 0.09), (2 * RIDGE_HX + 1.30, 1.98, 0.18), 0)     # 瓦条
    mb.box((0, 0, zc + 0.40), (2 * RIDGE_HX + 1.24, 1.52, 0.46), 0)     # 脊筒
    mb.box((0, 0, zc + 0.70), (2 * RIDGE_HX + 1.34, 1.72, 0.16), 0)     # 出檐
    mb.box((0, 0, zc + 0.84), (2 * RIDGE_HX + 1.20, 1.44, 0.14), 0)     # 脊帽
    # 脊筒竖向分块
    n = int(2 * RIDGE_HX / 0.42)
    for i in range(n):
        x = -RIDGE_HX + (i + 0.5) * (2 * RIDGE_HX / n)
        mb.box((x, 0, zc + 0.40), (0.09, 1.56, 0.46), 0)
    o = mb.build("RD01_正脊", coll, [M['tile']])
    add_bevel(o, 0.012, 2)

    # ---- 鸱吻（正脊两端）----
    for s in (-1, 1):
        chiven(M, coll, s * (RIDGE_HX + 0.70), 0.0, zc + 0.02, s, 1.30)

    # ---- 四条垂脊 ----
    build_hip_ridges(M, coll)
    # ---- 围脊（下檐与上檐交接处）----
    mb2 = MB()
    ring_box(mb2, HX1_IN - 0.05, HY1_IN - 0.05, Z_TOP1 - 0.42, Z_TOP1 + 0.30, 0.62, 0)
    o = mb2.build("RD04_围脊", coll, [M['tile']])
    add_bevel(o, 0.012, 2)


def chiven(M, coll, x, y, z, s, k=1.0):
    """正吻：鱼龙形，张口吞脊，背插剑把"""
    mb = MB()
    # 侧视轮廓（沿脊向外为 +x，向上为 +z）
    prof = [(0.00, 0.00), (0.95, 0.00), (1.12, 0.42), (1.10, 1.05), (0.95, 1.62),
            (0.72, 2.10), (0.40, 2.52), (0.02, 2.86), (-0.34, 3.02), (-0.62, 2.86),
            (-0.72, 2.50), (-0.60, 2.10), (-0.40, 1.72), (-0.30, 1.25),
            (-0.36, 0.72), (-0.30, 0.28)]
    th = 0.42
    ring_a = [(x + s * px * k, y - th * k, z + pz * k) for (px, pz) in prof]
    ring_b = [(x + s * px * k, y + th * k, z + pz * k) for (px, pz) in prof]
    mb.loft([ring_a, ring_b], 0, close_bottom=True, close_top=True)
    # 吻口（吞脊）
    mb.box((x - s * 0.05, y, z + 0.22), (0.95, 0.80, 0.46), 0)
    # 牙齿/卷唇
    for i in range(3):
        mb.box((x + s * (0.42 - i * 0.06), y, z + 0.10 + i * 0.16),
               (0.22, 0.86, 0.12), 0)
    # 背鳍
    for i in range(5):
        px, pz = 0.55 - i * 0.13, 1.15 + i * 0.32
        mb.box((x + s * px, y, z + pz), (0.30, 0.74, 0.20), 0, ry=-s * 0.5)
    # 剑把
    mb.box((x + s * 0.10, y, z + 2.95), (0.16, 0.26, 0.52), 0, ry=-s * 0.15)
    mb.box((x + s * 0.10, y, z + 3.20), (0.34, 0.40, 0.10), 0)
    o = mb.build("RD02_正吻_%s" % ("L" if s < 0 else "R"), coll, [M['tile']])
    for p in o.data.polygons:
        p.use_smooth = True


def build_hip_ridges(M, coll):
    """四条垂脊：沿戗脊曲线，带走兽"""
    mb = MB()
    for sx in (-1, 1):
        for sy in (-1, 1):
            side = 'R' if sx > 0 else 'L'
            u = 1.0 if sy > 0 else -1.0
            pts = []
            n = 30
            for k in range(n + 1):
                t = k / n
                pts.append(roof_pt(u, t, side, HX2, HY2, RIDGE_HX, RIDGE_HY,
                                   Z_EAVE2, Z_RIDGE_C, P_UP, LIFT_UP))
            # 脊身
            for k in range(len(pts) - 1):
                p0, p1 = Vector(pts[k]), Vector(pts[k + 1])
                d = p1 - p0
                L = d.length
                if L < 1e-5:
                    continue
                mid = (p0 + p1) / 2
                ang = math.atan2(d.y, d.x)
                pitch = math.atan2(d.z, math.hypot(d.x, d.y))
                for (dz, wd, ht) in ((0.12, 0.98, 0.24), (0.44, 0.74, 0.46),
                                     (0.72, 0.90, 0.12)):
                    mb.box((mid.x, mid.y, mid.z + dz), (L * 1.14, wd, ht), 0,
                           rz=ang, ry=-pitch)
            # 走兽（仙人 + 九兽）
            for i in range(9):
                t = 0.93 - i * 0.023
                p = roof_pt(u, t, side, HX2, HY2, RIDGE_HX, RIDGE_HY,
                            Z_EAVE2, Z_RIDGE_C, P_UP, LIFT_UP)
                beast(mb, p[0], p[1], p[2] + 0.62, math.atan2(sy, sx), i)
    o = mb.build("RD03_垂脊走兽", coll, [M['tile']])
    for p in o.data.polygons:
        p.use_smooth = True


def beast(mb, x, y, z, ang, i):
    """脊兽剪影：座 + 身 + 头"""
    mb.box((x, y, z), (0.34, 0.34, 0.14), 0, rz=ang)
    mb.sphere((x, y, z + 0.28), 0.16 + 0.01 * (9 - i), 8, 6, 0, (1.0, 1.15, 1.25))
    mb.sphere((x + 0.10 * math.cos(ang + 1.0), y + 0.10 * math.sin(ang + 1.0), z + 0.44),
              0.10, 8, 6, 0)
