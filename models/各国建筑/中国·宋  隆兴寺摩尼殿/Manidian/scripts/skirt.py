# -*- coding: utf-8 -*-
"""腰檐（重檐下檐）——极坐标闭合环，按抱厦位置分段

几何思路：外圈是檐口矩形、内圈贴上层墙身，上下两层封口成**闭合实体**，
因此永远不会出现开口亮边。上一版用 mask 挖洞后靠 Solidify 收边，
结果是一圈锯齿白毛刺；这一版改用「按段闭合」——把极坐标采样按抱厦
所在的四个角窗切开，每段单独封端面，段与段之间留出抱厦的缺口：

    前缺口  |x| ≤ SK_GAP_W 且 y ≥ SK_GAP_IN
    后缺口  |x| ≤ SK_GAP_W 且 y ≤ −SK_GAP_IN
    右缺口  |y| ≤ SK_GAP_W 且 x ≥ SK_GAP_IN
    左缺口  |y| ≤ SK_GAP_W 且 x ≤ −SK_GAP_IN

于是腰檐只剩四个转角段（正是照片里抱厦之间那四段），抱厦屋面从缺口
里穿出去，断面藏在抱厦屋面背后，正立面上看到的是「腰檐被抱厦切断」
而不是「腰檐断成两截露着缺口」。
"""
import math
import numpy as np
from blib import MB, lerp, fix_normals
from mathutils import Vector


def _rect_hit(th, HW, HD):
    ct, st = np.cos(th), np.sin(th)
    r = np.minimum(HW / np.maximum(np.abs(ct), 1e-9),
                   HD / np.maximum(np.abs(st), 1e-9))
    return r * ct, r * st


def _runs(keep):
    """把布尔掩码切成若干连续段（不跨越 0/2π 接缝）"""
    out = []
    i = 0
    n = len(keep)
    while i < n:
        if keep[i]:
            j = i
            while j + 1 < n and keep[j + 1]:
                j += 1
            out.append((i, j))
            i = j + 1
        else:
            i += 1
    return out


def build_skirt(mats, HW0, HD0, HW1, HD1, He, top_z, name, coll,
                nth=576, nt=34, lift=0.62, lift_r=4.2,
                tile_p=0.355, tile_amp=0.036, thick=0.20, curve=0.10,
                gaps=None):
    th = np.linspace(0.0, 2 * math.pi, nth, endpoint=False)
    Ex, Ey = _rect_hit(th, HW0, HD0)
    Wx, Wy = _rect_hit(th, HW1, HD1)

    # 檐口弧长（做瓦垄相位，绕一圈连续无接缝）
    seg = np.hypot(np.roll(Ex, -1) - Ex, np.roll(Ey, -1) - Ey)
    s = np.concatenate([[0.0], np.cumsum(seg)[:-1]])

    # 翼角起翘：按到最近转角的角距
    corners = [math.atan2(sy * HD0, sx * HW0)
               for sx in (1, -1) for sy in (1, -1)]
    dl = np.full(nth, 1e9)
    for c in corners:
        d = np.abs((th - c + math.pi) % (2 * math.pi) - math.pi)
        dl = np.minimum(dl, d * HW0)
    lift_v = lift * np.exp(-(dl / lift_r) ** 2)
    # 转角在平面上收圆，避免檐口出现尖喙
    round_k = 0.062 * np.exp(-(dl / 2.4) ** 2)
    Ex = Ex * (1.0 - round_k)
    Ey = Ey * (1.0 - round_k)

    tt = np.linspace(0.0, 1.045, nt)
    # 竖向举折：檐口平缓、上端略陡
    ft = tt ** (1.0 + curve)

    P = np.zeros((nth, nt, 3))
    for i in range(nth):
        for j, t in enumerate(tt):
            x = lerp(Ex[i], Wx[i], t)
            y = lerp(Ey[i], Wy[i], t)
            z = He + (top_z + 0.06 - He) * ft[j] + lift_v[i] * max(0.0, 1 - t) ** 1.6
            P[i, j] = (x, y, z)

    # 法向
    N = np.zeros_like(P)
    for i in range(nth):
        ip, inx = (i - 1) % nth, (i + 1) % nth
        for j in range(nt):
            jp, jn = max(0, j - 1), min(nt - 1, j + 1)
            ti = P[inx, j] - P[ip, j]
            tj = P[i, jn] - P[i, jp]
            n = np.cross(tj, ti)
            ln = np.linalg.norm(n)
            N[i, j] = n / ln if ln > 1e-9 else (0, 0, 1)

    disp = tile_amp * (0.70 * np.cos(2 * math.pi * s / tile_p)
                       + 0.30 * np.cos(4 * math.pi * s / tile_p))
    for i in range(nth):
        P[i] += N[i] * disp[i]

    # ---- 抱厦缺口
    keep = np.ones(nth, bool)
    if gaps:
        for (gw, gin) in gaps:
            keep &= ~((np.abs(Ex) <= gw) & (Ey >= gin))
            keep &= ~((np.abs(Ex) <= gw) & (Ey <= -gin))
            keep &= ~((np.abs(Ey) <= gw) & (Ex >= gin))
            keep &= ~((np.abs(Ey) <= gw) & (Ex <= -gin))
    runs = _runs(keep)
    if not runs:                                  # 兜底：不切
        runs = [(0, nth - 1)]

    # ---- 组装闭合实体（逐段）
    mb = MB()
    for (i0, i1) in runs:
        seq = list(range(i0, i1 + 1))
        top = [[mb.addv(P[i, j]) for j in range(nt)] for i in seq]
        bot = [[mb.addv(P[i, j] - np.array([0.0, 0.0, thick])) for j in range(nt)]
               for i in seq]
        m = len(seq)
        for a in range(m - 1):
            for j in range(nt - 1):
                mb.addf((top[a][j], top[a + 1][j], top[a + 1][j + 1], top[a][j + 1]), True)
                mb.addf((bot[a][j + 1], bot[a + 1][j + 1], bot[a + 1][j], bot[a][j]), True)
            mb.addf((bot[a][0], bot[a + 1][0], top[a + 1][0], top[a][0]), False)
            mb.addf((top[a][nt - 1], top[a + 1][nt - 1],
                     bot[a + 1][nt - 1], bot[a][nt - 1]), False)
        # 段端封口（缺口断面）
        for a in (0, m - 1):
            for j in range(nt - 1):
                mb.addf((top[a][j], top[a][j + 1], bot[a][j + 1], bot[a][j]), False)
    ob = mb.build(name, mats.tile, coll, auto_smooth=34)
    fix_normals(ob)

    # ---- 檐口瓦当（对齐瓦垄波峰，只在连续段上排）
    mb = MB()
    p = tile_p
    for (i0, i1) in runs:
        i1c = min(i1, nth - 1)
        sv0, sv1 = s[i0], s[i1c]
        k = int(math.ceil(sv0 / p))
        while k * p <= sv1:
            sv = k * p
            idx = int(np.searchsorted(s[i0:i1c + 1], sv)) - 1 + i0
            idx = min(max(idx, i0), i1c - 1)
            seg_len = max(1e-6, s[idx + 1] - s[idx])
            f = (sv - s[idx]) / seg_len
            ia, ib = idx % nth, (idx + 1) % nth
            x = lerp(Ex[ia], Ex[ib], f)
            y = lerp(Ey[ia], Ey[ib], f)
            z = He + lift_v[ia]
            d = Vector((x, y, 0.0))
            d = d.normalized() if d.length > 1e-6 else Vector((0, 1, 0))
            mb.cyl_dir(Vector((x, y, z - 0.04)) + d * 0.01, 0.075, 0.085,
                       (d.x * 0.62, d.y * 0.62, -0.78), seg=10)
            k += 1
    mb.build(name + "_瓦当", mats.tile, coll, auto_smooth=40)
    return ob
