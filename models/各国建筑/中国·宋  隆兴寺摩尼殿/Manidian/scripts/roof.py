# -*- coding: utf-8 -*-
"""宋代歇山屋顶生成器（重写版）

几何定义（这是修掉破洞的关键）：
  正坡  z = He + rise·f(a)                      |x| ≤ LR
  撒头  z = He + (min(正坡, Hg) − He)·f(b)        |x| > LR
  山花  在 |x| = LR 处，正坡与撒头之间留下的垂直落差，由山花板封堵

上一版把「|x|>LR 且 z>Hg」的面直接删掉，等于把整块撒头挖走，
而山花板只封在 |x|=LR 的平面上，于是从上方可以穿过山花两侧看进殿内
——这就是截图里那片褐色空洞的成因（屋顶_上檐 有 1882 条边界边）。

本版另外三处针对性修正：
  1. 山花、博缝、悬鱼改为随曲面走的实体，不再是贴在洞口的薄板；
  2. 正脊/垂脊/戗脊按檐口实际曲面定位，不再悬空成黑条；
  3. 檐口瓦当对齐瓦垄波峰，不再错位成流苏。
"""
import math
import numpy as np
from mathutils import Vector
from blib import MB, lerp, clamp, add_solidify, fix_normals


class RoofSpec:
    def __init__(self, HW, HD, He, Hr, LR, Hg, lift=0.85, lift_r=4.6,
                 p=1.90, tile_p=0.355, tile_amp=0.038,
                 ridge_w=0.46, name=""):
        self.HW, self.HD = HW, HD
        self.He, self.Hr = He, Hr
        self.LR, self.Hg = LR, Hg
        self.lift, self.lift_r = lift, lift_r
        self.p = p
        self.tile_p, self.tile_amp = tile_p, tile_amp
        self.ridge_w = ridge_w
        self.rise = Hr - He
        self.name = name
        # 山花底线的半宽：正坡降到 Hg 处对应的 y
        frac = clamp((Hg - He) / max(1e-6, self.rise), 0.001, 0.999)
        self.a_g = HD * self._inv(frac)
        self.Yg = HD - self.a_g

    # ---------------- 举折：檐口平缓、近脊加陡
    W0 = 0.60
    QQ = 2.00

    def _f(self, u):
        u = np.clip(u, 0.0, 1.0)
        return self.W0 * u + (1.0 - self.W0) * u ** self.QQ

    def _inv(self, h):
        lo, hi = 0.0, 1.0
        for _ in range(40):
            mid = (lo + hi) / 2
            if self._f(mid) < h:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    def z_np(self, X, Y):
        a = np.clip(self.HD - np.abs(Y), 0.0, None)
        b = np.clip(self.HW - np.abs(X), 0.0, None)
        main = self.He + self.rise * self._f(a / self.HD)
        # 撒头：一条水平上沿（山花底线 Hg）的单坡，向外落到山面檐口。
        # 这是歇山的正解——上部悬山（两坡＋两端垂直山花），
        # 下部庑殿（四坡）；两者的分界就是 Hg 这条水平线。
        # 若让撒头的上沿跟着山花斜边走（上一版的错），撒头会被拉成
        # 近乎垂直的锥面，整座抱厦看着像一座攒尖亭子。
        hb = np.clip(b / max(1e-6, self.HW - self.LR), 0.0, 1.0)
        side = self.He + (np.minimum(main, self.Hg) - self.He) * self._f(hb)
        Z = np.where(np.abs(X) <= self.LR, main, side)
        dc = np.sqrt(a * a + b * b)
        return Z + self.lift * np.exp(-(dc / self.lift_r) ** 2)

    def z(self, x, y):
        return float(self.z_np(np.array([x], float), np.array([y], float))[0])

    def normal_np(self, X, Y, e=0.06):
        dx = (self.z_np(X + e, Y) - self.z_np(X - e, Y)) / (2 * e)
        dy = (self.z_np(X, Y + e) - self.z_np(X, Y - e)) / (2 * e)
        N = np.stack([-dx, -dy, np.ones_like(dx)], -1)
        return N / np.linalg.norm(N, axis=-1, keepdims=True)


# ---------------------------------------------------------------- 屋面
def build_xieshan(mats, S, name, coll, res_x=0.058, res_y=0.14,
                  gable_signs=(1, -1), thick=0.17):
    """屋面（含瓦垄位移）+ 檐口瓦当 + 山花"""
    xs = np.linspace(-S.HW, S.HW, max(24, int(2 * S.HW / res_x) + 1))
    xs = np.unique(np.concatenate([xs, [-S.LR, S.LR]]))
    ys = np.linspace(-S.HD, S.HD, max(20, int(2 * S.HD / res_y) + 1))
    nx, ny = len(xs), len(ys)
    X, Y = np.meshgrid(xs, ys, indexing='ij')

    Z0 = S.z_np(X, Y)
    N = S.normal_np(X, Y)

    # 瓦垄：正坡按 x 排布，撒头按 y 排布；折角处（山花立面）不加位移
    phase = np.where(np.abs(X) <= S.LR, X, Y)
    disp = S.tile_amp * (0.70 * np.cos(2 * math.pi * phase / S.tile_p)
                         + 0.30 * np.cos(4 * math.pi * phase / S.tile_p))
    fold = np.abs(np.abs(X) - S.LR) < res_x * 1.05
    disp = np.where(fold, 0.0, disp)
    P = np.stack([X, Y, Z0], -1) + N * disp[..., None]

    idx = np.arange(nx * ny).reshape(nx, ny)
    faces = np.stack([idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]],
                     -1).reshape(-1, 4)

    mb = MB()
    mb.v = P.reshape(-1, 3).tolist()
    mb.f = [tuple(int(k) for k in q) for q in faces]
    mb.sm = [True] * len(mb.f)
    roof = mb.build(name, mats.tile, coll, auto_smooth=34)
    add_solidify(roof, thick)

    objs = [roof, build_eave_tiles(mats, S, name + "_瓦当", coll)]
    for sg in gable_signs:
        objs += list(build_shanhua(mats, S, name + ("_山花L" if sg < 0 else "_山花R"),
                                   coll, sg))
    return objs


def build_eave_tiles(mats, S, name, coll, r=None, ln=None):
    """檐口瓦当：压在瓦垄波峰上，朝外下方伸出"""
    r = 0.075 if r is None else r
    ln = 0.085 if ln is None else ln
    mb = MB()
    p = S.tile_p
    # 前后檐
    for sy in (1, -1):
        k0 = int(math.ceil(-S.HW / p))
        k1 = int(math.floor(S.HW / p))
        for k in range(k0, k1 + 1):
            x = k * p
            z = S.z(x, sy * S.HD)
            mb.cyl_dir((x, sy * (S.HD + 0.005), z - 0.035), r, ln,
                       (0, sy * 0.62, -0.78), seg=10)
    # 两山檐
    for sx in (1, -1):
        k0 = int(math.ceil(-S.HD / p))
        k1 = int(math.floor(S.HD / p))
        for k in range(k0, k1 + 1):
            y = k * p
            z = S.z(sx * S.HW, y)
            mb.cyl_dir((sx * (S.HW + 0.005), y, z - 0.035), r, ln,
                       (sx * 0.62, 0, -0.78), seg=10)
    return mb.build(name, mats.tile, coll, auto_smooth=40)


# ---------------------------------------------------------------- 山花
def _extrude_profile(mb, pts, x0, x1):
    """把 (y,z) 多边形沿 x 挤出成闭合实体（星形多边形，中心扇形三角化）"""
    n = len(pts)
    F = [mb.addv((x0, y, z)) for (y, z) in pts]
    B = [mb.addv((x1, y, z)) for (y, z) in pts]
    for i in range(n):
        j = (i + 1) % n
        mb.addf((F[i], F[j], B[j], B[i]), False)
    cy = sum(p[0] for p in pts) / n
    cz = sum(p[1] for p in pts) / n
    cf = mb.addv((x0, cy, cz))
    cb = mb.addv((x1, cy, cz))
    for i in range(n):
        j = (i + 1) % n
        mb.addf((cf, F[j], F[i]), False)
        mb.addf((cb, B[i], B[j]), False)


def _curved_band(mb, pts, x0, x1, hh, cap=True):
    """沿 (y,z) 折线拉一条矩形截面的带（x0..x1 为厚度），闭合成实体"""
    A = [mb.addv((x0, y, z)) for (y, z) in pts]
    B = [mb.addv((x1, y, z)) for (y, z) in pts]
    C = [mb.addv((x1, y, z - hh)) for (y, z) in pts]
    D = [mb.addv((x0, y, z - hh)) for (y, z) in pts]
    n = len(pts)
    for i in range(n - 1):
        mb.addf((A[i], A[i + 1], B[i + 1], B[i]), False)
        mb.addf((B[i], B[i + 1], C[i + 1], C[i]), False)
        mb.addf((C[i], C[i + 1], D[i + 1], D[i]), False)
        mb.addf((D[i], D[i + 1], A[i + 1], A[i]), False)
    if cap:
        mb.addf((A[0], B[0], C[0], D[0]), False)
        mb.addf((D[-1], C[-1], B[-1], A[-1]), False)


def build_shanhua(mats, S, name, coll, sg):
    """山花板 + 博缝板 + 排山勾滴 + 悬鱼

    山花是 |x|=LR 处的垂直三角面：它的上边就是主坡剖面本身
    （z 从山面檐口沿 y 升到正脊），因此三角形的两个底角天然落在檐口上，
    形状随屋面举折一起弯——这正是参考照片里那块「扁宽、斜边微凹」的山花。
    """
    gable = getattr(mats, "gable", mats.wood_red)
    boxue = getattr(mats, "boxue", mats.wood_red)
    carve = getattr(mats, "carve_red", gable)

    n = 64
    ys = np.linspace(-S.Yg - 0.02, S.Yg + 0.02, n)
    top = np.array([S.z(S.LR, y) for y in ys])
    zb = S.Hg - 0.42
    xa = sg * (S.LR - 0.17)
    xb = sg * (S.LR + 0.03)
    x0, x1 = min(xa, xb), max(xa, xb)

    mb = MB()
    for i, y in enumerate(ys):
        zt = max(top[i] + 0.03, zb + 0.06)
        a = mb.addv((x0, y, zb))
        b = mb.addv((x0, y, zt))
        c = mb.addv((x1, y, zt))
        d = mb.addv((x1, y, zb))
        if i:
            p = prev
            mb.addf((p[0], a, b, p[1]), False)      # 外皮
            mb.addf((p[1], b, c, p[2]), False)      # 上沿
            mb.addf((p[2], c, d, p[3]), False)      # 内皮
            mb.addf((p[3], d, a, p[0]), False)      # 底
        prev = (a, b, c, d)
    mb.addf((prev[0], prev[3], prev[2], prev[1]), False)
    objs = [mb.build(name, gable, coll, auto_smooth=None)]

    # 博缝板：压在山花外皮上沿，是照片里那条很显眼的浅灰白斜带
    mb = MB()
    xf0 = x1 + sg * 0.004
    xf1 = x1 + sg * 0.175
    pts = list(zip(ys, top + 0.05))
    _curved_band(mb, pts, min(xf0, xf1), max(xf0, xf1), 0.26)
    objs.append(mb.build(name + "_博缝", boxue, coll, auto_smooth=None))

    # 排山勾滴：博缝外皮上一排小圆瓦头
    mb = MB()
    step = S.tile_p * 0.92
    s = 0.0
    for i in range(n - 1):
        y0, z0 = pts[i]
        y1, z1 = pts[i + 1]
        seg = math.hypot(y1 - y0, z1 - z0)
        while s <= seg:
            t = s / max(seg, 1e-6)
            mb.cyl_dir((xf1 + sg * 0.012, lerp(y0, y1, t), lerp(z0, z1, t) - 0.115),
                       0.052, 0.044, (sg, 0, 0), seg=8)
            s += step
        s -= seg
    objs.append(mb.build(name + "_勾滴", mats.tile_dark, coll, auto_smooth=40))

    # 悬鱼：主轴 + 中央大菱形 + 上下小菱形 + 两侧圆头，按照片的云头十字
    ztop = float(top[n // 2])
    hh = max(0.9, (ztop - zb) * 0.54)
    zc = zb + (ztop - zb) * 0.33
    xc = xf1 + sg * 0.05
    mb = MB()
    t = 0.11

    def _piece(prof, hy=1.0):
        q = [(y * hh * hy, zc + z * hh) for (y, z) in prof]
        _extrude_profile(mb, q, min(xc - sg * t / 2, xc + sg * t / 2),
                         max(xc - sg * t / 2, xc + sg * t / 2))

    # 主轴（上宽下尖）
    _piece([(0.00, 0.50), (0.052, 0.34), (0.046, -0.22),
            (0.00, -0.52), (-0.046, -0.22), (-0.052, 0.34)])
    # 中央菱形（最宽处）
    _piece([(0.00, 0.20), (0.235, 0.02), (0.00, -0.19), (-0.235, 0.02)])
    # 上方小菱形
    _piece([(0.00, 0.35), (0.105, 0.24), (0.00, 0.13), (-0.105, 0.24)])
    # 两侧圆头
    for sy in (-1, 1):
        _piece([(sy * 0.255, 0.00), (sy * 0.335, 0.085),
                (sy * 0.415, 0.00), (sy * 0.335, -0.085)])
    objs.append(mb.build(name + "_悬鱼", carve, coll, auto_smooth=32))
    return objs


# ---------------------------------------------------------------- 脊
def build_zhengji(mats, S, name, coll, sg_ends=True, x0=None, x1=None,
                  ends=(1, -1)):
    """正脊：脊座 + 三层瓦条 + 脊上小瓦当 + 两端鸱吻"""
    mb = MB()
    w = S.ridge_w
    z = S.Hr
    xa = -S.LR if x0 is None else x0
    xb = S.LR if x1 is None else x1
    # 脊座（压住两坡交汇）
    mb.box_minmax(xa, xb, -w * 0.82, w * 0.82, z - 0.18, z + 0.10)
    # 三层收分
    mb.box_minmax(xa, xb, -w * 0.62, w * 0.62, z + 0.10, z + 0.44)
    mb.box_minmax(xa, xb, -w * 0.52, w * 0.52, z + 0.44, z + 0.76)
    mb.box_minmax(xa, xb, -w * 0.40, w * 0.40, z + 0.76, z + 0.96)
    # 脊顶筒瓦节奏
    n = max(2, int((xb - xa) / 0.62))
    for i in range(n + 1):
        x = xa + i * ((xb - xa) / n)
        mb.cyl_dir((x, 0, z + 0.96), w * 0.36, 0.12, (0, 0, 1), seg=8)
    obj = mb.build(name, mats.tile_dark, coll, auto_smooth=32)

    objs = [obj]
    if sg_ends:
        for sg in ends:
            xx = xb if sg > 0 else xa
            objs.append(build_chiwen(mats, S, name + ("_吻L" if sg < 0 else "_吻R"),
                                     coll, sg, xx))
    return objs


def build_chiwen(mats, S, name, coll, sg, x0=None):
    """鸱吻：卷尾 + 背鳍 + 剑把，绿琉璃"""
    mb = MB()
    if x0 is None:
        x0 = sg * S.LR
    z0 = S.Hr + 0.55
    # 吻座
    mb.box_minmax(min(x0, x0 - sg * 0.95), max(x0, x0 - sg * 0.95),
                  -0.52, 0.52, S.Hr - 0.10, z0 + 0.26)
    # 卷尾
    key = [(0.00, 0.00), (-0.12, 0.56), (-0.34, 1.06), (-0.66, 1.42),
           (-1.04, 1.60), (-1.42, 1.50), (-1.64, 1.18), (-1.70, 0.86)]
    ss = [1.46, 1.40, 1.28, 1.12, 0.96, 0.78, 0.60, 0.46]
    pts, sc = [], []
    for (dx, dz), kk in zip(key, ss):
        pts.append((x0 + sg * dx, 0.0, z0 + dz))
        sc.append(kk)
    prof = [(-0.62, -0.34), (0.62, -0.34), (0.66, 0.14), (0.40, 0.40),
            (-0.40, 0.40), (-0.66, 0.14)]
    mb.sweep(pts, prof, up=Vector((0, 0, 1)), smooth=False, close=True, scale=sc)
    # 背鳍
    for (dx, dz, hh) in ((-0.30, 1.00, 0.20), (-0.62, 1.34, 0.24),
                         (-0.98, 1.52, 0.18)):
        mb.cuboid((x0 + sg * (dx + 0.10), 0, z0 + dz + hh * 0.4),
                  (0.22, 0.20, hh * 1.8), rot=(0, sg * 0.45, 0))
    # 剑把
    mb.cuboid((x0 + sg * 0.06, 0, z0 + 0.72), (0.16, 0.18, 0.70),
              rot=(0, sg * 0.20, 0))
    return mb.build(name, mats.tile_dark, coll, auto_smooth=34)


def sweep_ridge(mb, path, w=0.30, h=0.26, s0=1.0, s1=1.0):
    """沿路径放样一条脊（截面为带卷边的梯形）"""
    prof = [(-w / 2, -h * 0.5), (w / 2, -h * 0.5), (w * 0.46, 0.0),
            (w * 0.30, h * 0.5), (-w * 0.30, h * 0.5), (-w * 0.46, 0.0)]
    n = len(path)
    sc = [lerp(s0, s1, i / max(1, n - 1)) for i in range(n)]
    mb.sweep(path, prof, up=Vector((0, 0, 1)), smooth=False, close=True, scale=sc)


def build_gable_ridges(mats, S, name, coll, sg):
    """垂脊（沿山花斜边）+ 戗脊（撒头内角 → 山面檐角）+ 走兽"""
    mb = MB()
    xg = sg * (S.LR + 0.08)
    yb = S.Yg
    # 垂脊：从脊尖沿山花斜边到撒头上沿
    for sy in (-1, 1):
        n = 30
        path = []
        for i in range(n):
            y = lerp(0.0, sy * yb, i / (n - 1.0))
            path.append((xg, y, S.z(S.LR, y) + 0.10))
        sweep_ridge(mb, path, w=0.34, h=0.30, s0=1.0, s1=0.86)
        # 戗脊：撒头内角 → 山面檐角
        p0 = (sg * (S.LR + 0.02), sy * yb, S.Hg + 0.06)
        p1 = (sg * S.HW, sy * S.HD, S.He + S.lift * 0.92)
        m = 16
        path2 = []
        for i in range(m):
            t = i / (m - 1.0)
            x = lerp(p0[0], p1[0], t)
            y = lerp(p0[1], p1[1], t)
            path2.append((x, y, S.z(x, y) + 0.09))
        sweep_ridge(mb, path2, w=0.30, h=0.26, s0=0.86, s1=0.70)
        # 走兽
        for k in range(3):
            t = 0.26 + 0.20 * k
            i = int(t * (m - 1))
            px, py, pz = path2[i]
            mb.cuboid((px, py, pz + 0.20), (0.13, 0.13, 0.22), top=(0.7, 0.7))
        # 檐角翘头（套兽）
        mb.cuboid((p1[0], p1[1], p1[2] + 0.18), (0.30, 0.30, 0.30),
                  rot=(0, 0, math.radians(45)), top=(0.6, 0.6))
    return mb.build(name, mats.tile_dark, coll, auto_smooth=32)


# ---------------------------------------------------------------- 围脊
def build_weiji(mats, S, hw, hd, ztop, coll, name="围脊_上檐"):
    """重檐围脊：腰檐上端与上层墙身之间的一圈脊"""
    mb = MB()
    t = 0.30
    mb.box_minmax(-hw - 0.16, hw + 0.16, hd - t, hd + t, ztop - 0.14, ztop + 0.30)
    mb.box_minmax(-hw - 0.16, hw + 0.16, -hd - t, -hd + t, ztop - 0.14, ztop + 0.30)
    mb.box_minmax(-hw - t, -hw + t, -hd + 0.16, hd - 0.16, ztop - 0.14, ztop + 0.30)
    mb.box_minmax(hw - t, hw + t, -hd + 0.16, hd - 0.16, ztop - 0.14, ztop + 0.30)
    return mb.build(name, mats.tile_dark, coll, auto_smooth=32)
