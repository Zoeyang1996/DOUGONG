"""佛光寺东大殿 —— 参数化几何构建

坐标：X 面阔（左右），Y 进深（前后，-Y 为正面），Z 高度
单位：米。

实测依据（张荣/刘畅/臧春雨《佛光寺东大殿实测数据解读》，2007）：
  通面阔 3400cm（稍间 1丈4尺1寸、中五间 1丈7尺）
  通进深 1766cm（各间 440/443/443/440）
  平柱高 500cm，檐柱径 54~60cm，角柱生起 24cm
  斗栱高 250cm（柱高之半），总檐出 363cm
  撩檐槫距 2152cm，举高 439cm，脊槫高 1184.5cm
"""
import bpy, math, os, random
from mathutils import Vector, Matrix
from blib import Builder, V, clamp, lerp, smoothstep, rotz
import mats as MAT

R = math.radians
FONT = r"C:\Windows\Fonts\STZHONGS.TTF"

# ============ 主体尺寸 ============
BAYS_W = [4.41, 5.06, 5.06, 5.06, 5.06, 5.06, 4.41]     # 面阔七间 = 34.12
BAYS_D = [4.40, 4.43, 4.43, 4.40]                        # 进深四间 = 17.66
XS = [-17.06]
for b in BAYS_W:
    XS.append(XS[-1] + b)
YS = [-8.83]
for b in BAYS_D:
    YS.append(YS[-1] + b)

XH, YH = 17.06, 8.83
PLAT_Z = 0.95          # 台基高
COL_H = 5.00           # 檐柱高
COL_R = 0.295          # 檐柱半径
SHENGQI = 0.24         # 角柱生起
BR_H = 2.50            # 斗栱层高（柱高之半）
EAVE_OUT = 3.63        # 总檐出
ROOF_W = 2 * XH + 2 * EAVE_OUT
ROOF_D = 2 * YH + 2 * EAVE_OUT
AX, AY = ROOF_W / 2, ROOF_D / 2
RX = AX - AY                          # 正脊半长 8.21
Z_PURLIN = PLAT_Z + COL_H + BR_H      # 撩檐枋背 = 8.45
Z_EAVE = 7.92                         # 檐口瓦口高
RISE = 5.16                           # 檐口至正脊举高
Z_RIDGE = Z_EAVE + RISE               # 13.08
CORNER_LIFT = 0.38                    # 翼角起翘
FLARE = 0.0                          # 翼角出翘


def shengqi(x, y):
    f = max(abs(x) / XH, abs(y) / YH)
    return SHENGQI * f ** 1.8


def z_top(x, y):
    return PLAT_Z + COL_H + shengqi(x, y)


# ============ 屋顶曲面 ============
_CP = [(0.0, 0.0), (0.16, 0.135), (0.34, 0.33), (0.55, 0.545),
       (0.72, 0.70), (0.86, 0.845), (0.95, 0.935), (1.0, 1.0)]


def _fcurve(t):
    """单调三次插值（举折曲线：檐部平缓、近脊陡峻）"""
    t = clamp(t, 0.0, 1.0)
    pts = _CP
    n = len(pts)
    d = [(pts[i + 1][1] - pts[i][1]) / (pts[i + 1][0] - pts[i][0]) for i in range(n - 1)]
    m = [d[0]]
    for i in range(1, n - 1):
        m.append((d[i - 1] + d[i]) / 2)
    m.append(d[-1])
    for i in range(n - 1):
        if abs(d[i]) < 1e-9:
            m[i] = m[i + 1] = 0.0
        else:
            a, b = m[i] / d[i], m[i + 1] / d[i]
            s = a * a + b * b
            if s > 9:
                k = 3 / math.sqrt(s)
                m[i] = k * a * d[i]
                m[i + 1] = k * b * d[i]
    for i in range(n - 1):
        if pts[i][0] <= t <= pts[i + 1][0]:
            h = pts[i + 1][0] - pts[i][0]
            s = (t - pts[i][0]) / h
            return ((2 * s**3 - 3 * s**2 + 1) * pts[i][1] + (s**3 - 2 * s**2 + s) * h * m[i]
                    + (-2 * s**3 + 3 * s**2) * pts[i + 1][1] + (s**3 - s**2) * h * m[i + 1])
    return 1.0


def t_of(x, y):
    d = AY - max(abs(y), abs(x) - RX)
    return clamp(d / AY, 0.0, 1.0)


def corner_w(x, y):
    c = ((abs(x) / AX) * (abs(y) / AY))
    return c ** 2.0


def corner_falloff(x, y):
    """到最近翼角的平面距离 → 平滑权重（1 在角点，衰减约 3m）"""
    d = min(math.hypot(AX - abs(x), AY - abs(y)), 99.0)
    return math.exp(-(d / 5.2) ** 2)


def roof_pt(x, y):
    """屋面点：含举折、柱头生起、翼角起翘"""
    t = t_of(x, y)
    z = Z_EAVE + RISE * _fcurve(t)
    # 檐口随角柱生起抬升（与柱顶同步）
    f0 = max(abs(x) / XH, abs(y) / YH)
    z += SHENGQI * (min(f0, 1.0) ** 1.8) * (1 - t) ** 1.4
    # 翼角起翘
    z += CORNER_LIFT * corner_falloff(x, y) * (1 - t) ** 2.0
    # 出翘
    f = FLARE * corner_falloff(x, y) * (1 - t) ** 2.0
    if f > 1e-5:
        d = Vector((math.copysign(1, x) if abs(x) > 1e-6 else 0,
                    math.copysign(1, y) if abs(y) > 1e-6 else 0, 0))
        if d.length > 0:
            d.normalize()
            return Vector((x + d.x * f, y + d.y * f, z))
    return Vector((x, y, z))


def roof_z(x, y):
    return roof_pt(x, y).z


# ============ 构件 ============
def column(B, x, y):
    zt = z_top(x, y)
    top = Vector((x - 0.010 * x, y - 0.012 * y, zt))
    base = Vector((x, y, PLAT_Z - 0.02))
    B.cyl("stone_dark", Vector((x, y, PLAT_Z - 0.06)), Vector((x, y, PLAT_Z + 0.12)), 0.45, 16)
    B.cyl("wood_red", base, top, COL_R, 20, r1=COL_R * 0.86, caps=True)


def gong(B, mat, ang, org, x0, x1, y, z0, h, w, taper=0.14):
    """栱：沿局部 X 的构件，端部卷杀"""
    segs = [(x0, h * 0.55), (x0 + taper, h), (x1 - taper, h), (x1, h * 0.55)]
    verts, faces = [], []
    for (sx, hh) in segs:
        for (sy, sz) in [(-w / 2, 0), (w / 2, 0), (w / 2, hh), (-w / 2, hh)]:
            verts.append(Vector((sx, y + sy, z0 + sz)))
    for i in range(len(segs) - 1):
        a, b = i * 4, (i + 1) * 4
        for k in range(4):
            k2 = (k + 1) % 4
            faces.append((a + k, a + k2, b + k2, b + k))
    faces.append((0, 1, 2, 3))
    o = (len(segs) - 1) * 4
    faces.append((o + 3, o + 2, o + 1, o))
    M = Matrix.Rotation(ang, 3, 'Z')
    B.poly(mat, [Vector(org) + M @ v for v in verts], faces)


def dou(B, mat, ang, org, cx, cy, z, s=0.30, h=0.22):
    M = Matrix.Rotation(ang, 3, 'Z')

    def quad(size, zz):
        return [Vector(org) + M @ Vector((cx + dx * size, cy + dy * size, z + zz))
                for (dx, dy) in [(-.5, -.5), (.5, -.5), (.5, .5), (-.5, .5)]]
    p0 = quad(s * 0.70, 0)
    p1 = quad(s, h * 0.55)
    p2 = quad(s * 0.90, h)
    verts = p0 + p1 + p2
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (8, 9, 10, 11),
             (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
             (4, 5, 9, 8), (5, 6, 10, 9), (6, 7, 11, 10), (7, 4, 8, 11)]
    B.poly(mat, verts, faces)


def bracket(B, org, ang, s=1.0):
    """七铺作双抄双下昂：出跳约1.93m，高2.5m（局部 X 向外）"""
    o = Vector(org)
    M = Matrix.Rotation(ang, 3, 'Z')

    def P(x, y, z):
        return o + M @ Vector((x * s, y * s, z * s))

    md = "wood_dark"
    # 栌斗
    dou(B, md, ang, o, 0, 0, 0.00, 0.70 * s, 0.50 * s)
    # 泥道栱 + 散斗 + 慢栱（顺墙方向）
    gong(B, md, ang + R(90), o, -0.64 * s, 0.64 * s, 0, 0.50 * s, 0.30 * s, 0.22 * s)
    for yy in (-0.55, 0.55):
        dou(B, md, ang, o, 0, yy * s, 0.80 * s, 0.28 * s, 0.20 * s)
    gong(B, md, ang + R(90), o, -0.98 * s, 0.98 * s, 0, 1.00 * s, 0.30 * s, 0.22 * s)
    for yy in (-0.88, 0, 0.88):
        dou(B, md, ang, o, 0, yy * s, 1.30 * s, 0.26 * s, 0.20 * s)
    # 柱头枋（两道）
    for zz in (1.50, 1.88):
        gong(B, md, ang + R(90), o, -1.05 * s, 1.05 * s, 0, zz * s, 0.30 * s, 0.24 * s)

    # 第一抄华栱
    gong(B, md, ang, o, -0.36 * s, 0.80 * s, 0, 0.50 * s, 0.30 * s, 0.23 * s)
    dou(B, md, ang, o, 0.74 * s, 0, 0.80 * s, 0.27 * s, 0.20 * s)
    # 第二抄华栱
    gong(B, md, ang, o, 0.50 * s, 1.26 * s, 0, 0.80 * s, 0.30 * s, 0.23 * s)
    dou(B, md, ang, o, 1.20 * s, 0, 1.10 * s, 0.27 * s, 0.20 * s)
    # 瓜子栱（第一跳跳头横栱）
    gong(B, md, ang + R(90), o, -0.64 * s, 0.64 * s, 0, 1.10 * s, 0.30 * s, 0.22 * s)
    for yy in (-0.55, 0.55):
        dou(B, md, ang, o, 0.95 * s, yy * s, 1.40 * s, 0.25 * s, 0.19 * s)

    # 第一下昂：自内向外斜下
    p0 = Vector((0.86 * s, 0, 1.42 * s))
    p1 = Vector((1.86 * s, 0, 1.14 * s))
    B.beam(md, P(p0.x, 0, p0.z), P(p1.x, 0, p1.z), 0.24 * s, 0.30 * s, rot=M)
    tipdir = (p1 - p0).normalized()
    B.poly(md, [P(p1.x, -0.12 * s, p1.z + 0.15 * s), P(p1.x, 0.12 * s, p1.z + 0.15 * s),
                P(p1.x + 0.42 * s, 0, p1.z - 0.10 * s),
                P(p1.x, 0.12 * s, p1.z - 0.10 * s), P(p1.x, -0.12 * s, p1.z - 0.10 * s)],
           [(0, 1, 2), (0, 2, 4), (1, 3, 2), (4, 2, 3), (0, 4, 3, 1)])
    # 第二下昂
    q0 = Vector((0.60 * s, 0, 1.80 * s))
    q1 = Vector((2.02 * s, 0, 1.52 * s))
    B.beam(md, P(q0.x, 0, q0.z), P(q1.x, 0, q1.z), 0.24 * s, 0.30 * s, rot=M)
    B.poly(md, [P(q1.x, -0.12 * s, q1.z + 0.15 * s), P(q1.x, 0.12 * s, q1.z + 0.15 * s),
                P(q1.x + 0.40 * s, 0, q1.z - 0.10 * s),
                P(q1.x, 0.12 * s, q1.z - 0.10 * s), P(q1.x, -0.12 * s, q1.z - 0.10 * s)],
           [(0, 1, 2), (0, 2, 4), (1, 3, 2), (4, 2, 3), (0, 4, 3, 1)])

    # 令栱 + 散斗（托撩檐枋）
    gong(B, md, ang + R(90), o, -0.70 * s, 0.70 * s, 0, 1.84 * s, 0.30 * s, 0.23 * s)
    for yy in (-0.62, 0.62):
        dou(B, md, ang, o, 1.88 * s, yy * s, 2.14 * s, 0.26 * s, 0.20 * s)
    # 耍头
    B.beam(md, P(1.10 * s, 0, 2.02 * s), P(2.42 * s, 0, 2.02 * s), 0.22 * s, 0.26 * s, rot=M)
    dou(B, md, ang, o, 2.05 * s, 0, 1.78 * s, 0.24 * s, 0.18 * s)


def brackets(B):
    for sy in (-1, 1):
        y = sy * YH
        ang = R(-90) if sy < 0 else R(90)
        for x in XS:
            bracket(B, (x - 0.010 * x, y, z_top(x, y) + 0.16), ang)
        for i in range(len(XS) - 1):
            xm = (XS[i] + XS[i + 1]) / 2
            bracket(B, (xm - 0.010 * xm, y, z_top(xm, y) + 0.16), ang)
    for sx in (-1, 1):
        x = sx * XH
        ang = 0 if sx > 0 else R(180)
        for y in YS:
            bracket(B, (x, y - 0.012 * y, z_top(x, y) + 0.16), ang)
        for j in range(len(YS) - 1):
            ym = (YS[j] + YS[j + 1]) / 2
            bracket(B, (x, ym - 0.012 * ym, z_top(x, ym) + 0.16), ang)
    # 转角铺作
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * XH, sy * YH
            bracket(B, (x, y, z_top(x, y) + 0.16), math.atan2(sy, sx))
            bracket(B, (x, y, z_top(x, y) + 0.16), R(0) if sx > 0 else R(180), 0.98)
            bracket(B, (x, y, z_top(x, y) + 0.16), R(-90) if sy < 0 else R(90), 0.98)


# ============ 屋顶 ============
def roof_faces(B):
    NT, NS = 22, 56
    faces = []
    for sy in (-1, 1):
        pts_t, pts_b = [], []
        for i in range(NS + 1):
            u = -1 + 2 * i / NS
            ct, cb = [], []
            for j in range(NT + 1):
                t = j / NT
                x = u * (RX + AY * (1 - t))
                y = sy * AY * (1 - t)
                p = roof_pt(x, y)
                ct.append(p)
                cb.append(Vector((p.x, p.y, p.z - 0.19)))
            pts_t.append(ct)
            pts_b.append(cb)
        B.quad_grid("tile_gap", pts_t, NS + 1, NT + 1)
        B.quad_grid("wood_dark", pts_b, NS + 1, NT + 1)
        faces.append((pts_t, pts_b))
    for sx in (-1, 1):
        pts_t, pts_b = [], []
        for i in range(NS + 1):
            v = -1 + 2 * i / NS
            ct, cb = [], []
            for j in range(NT + 1):
                t = j / NT
                y = v * AY * (1 - t)
                x = sx * (RX + AY * (1 - t))
                p = roof_pt(x, y)
                ct.append(p)
                cb.append(Vector((p.x, p.y, p.z - 0.19)))
            pts_t.append(ct)
            pts_b.append(cb)
        B.quad_grid("tile_gap", pts_t, NS + 1, NT + 1)
        B.quad_grid("wood_dark", pts_b, NS + 1, NT + 1)
        faces.append((pts_t, pts_b))
    return faces


def eave_rim(B, faces):
    """檐口：连檐（木）+ 瓦口（瓦），使边缘有厚度"""
    for (pt, pb) in faces:
        n = len(pt[0])
        up = list(pt[i][0] for i in range(n))
        lo = list(pb[i][0] for i in range(n))
        lo2 = [Vector((p.x, p.y, p.z - 0.34)) for p in up]
        verts = up + lo2
        fs = [(i, i + 1, n + i + 1, n + i) for i in range(n - 1)]
        B.poly("wood_dark", verts, fs)
        # 瓦口压边
        v2 = [Vector((p.x, p.y, p.z + 0.03)) for p in up] + [Vector((p.x, p.y, p.z - 0.10)) for p in up]
        f2 = [(i, i + 1, n + i + 1, n + i) for i in range(n - 1)]
        B.poly("tile_ridge", v2, f2)
        # 底面封口
        v3 = lo2 + lo
        f3 = [(i, i + 1, n + i + 1, n + i) for i in range(n - 1)]
        B.poly("wood_dark", v3, f3)


def tile_runs(B):
    """筒瓦垄：前后坡沿 Y 铺至脊/垂脊，两山沿 X 铺至垂脊"""
    prof = [(0.088 * math.cos(math.pi * k / 8), 0.088 * math.sin(math.pi * k / 8)) for k in range(9)]
    SP = 0.345
    for sy in (-1, 1):
        x = -AX + 0.18
        while x <= AX - 0.18:
            y_e = sy * AY
            y_end = -sy * max(0.0, abs(x) - RX)
            if abs(y_e - y_end) > 0.30:
                path = []
                steps = 22
                for j in range(steps + 1):
                    y = y_e + (y_end - y_e) * (j / steps)
                    p = roof_pt(x, y)
                    path.append(Vector((p.x, p.y, p.z + 0.010)))
                B.sweep("tile", path, prof, closed=False)
                p0 = path[0]
                d = (path[1] - path[0]).normalized()
                B.cyl("tile", p0 - d * 0.03, p0 + d * 0.09, 0.098, 10)
            x += SP
    for sx in (-1, 1):
        y = -AY + 0.18
        while y <= AY - 0.18:
            x_e = sx * AX
            x_end = sx * (RX + abs(y))
            if abs(x_e - x_end) > 0.30:
                path = []
                steps = 20
                for j in range(steps + 1):
                    x = x_e + (x_end - x_e) * (j / steps)
                    p = roof_pt(x, y)
                    path.append(Vector((p.x, p.y, p.z + 0.010)))
                B.sweep("tile", path, prof, closed=False)
                p0 = path[0]
                d = (path[1] - path[0]).normalized()
                B.cyl("tile", p0 - d * 0.03, p0 + d * 0.09, 0.098, 10)
            y += SP


def rafters(B):
    """檐椽（沿屋面举折铺满，彻上明造可见）+ 飞椽 + 翼角辐射椽"""
    prof = [(-0.075, 0.0), (0.075, 0.0), (0.075, 0.17), (-0.075, 0.17)]
    SP = 0.315
    OFF = 0.20
    # 前后坡：沿 Y 向铺
    for sy in (-1, 1):
        x = -AX + 0.20
        while x <= AX - 0.20:
            y_e = sy * AY
            y_r = 0.0 if abs(x) <= RX else None
            if y_r is None:
                y_r = sy * (abs(x) - RX) * 0.0
            y_e = y_e - sy * 0.06
            y_end = -sy * max(0.0, abs(x) - RX)
            if abs(y_e - y_end) > 0.35:
                path = []
                steps = 16
                for j in range(steps + 1):
                    y = y_e + (y_end - y_e) * (j / steps)
                    p = roof_pt(x, y)
                    path.append(Vector((p.x, p.y, p.z - OFF)))
                B.sweep("wood_dark", path, prof, closed=True)
                # 飞椽（檐口一段，方截面浅置）
                p0 = roof_pt(x, y_e)
                p1 = roof_pt(x, y_e - sy * 1.15)
                B.beam("wood_dark",
                       Vector((p0.x, p0.y, p0.z - 0.135)),
                       Vector((p1.x, p1.y, p1.z - 0.175)), 0.135, 0.085)
            x += SP
    # 两山坡
    for sx in (-1, 1):
        y = -AY + 0.20
        while y <= AY - 0.20:
            x_e = sx * (AX - 0.06)
            x_r = sx * (RX + abs(y))
            path = []
            steps = 14
            for j in range(steps + 1):
                x = x_e + (x_r - x_e) * (j / steps)
                p = roof_pt(x, y)
                path.append(Vector((p.x, p.y, p.z - OFF)))
            B.sweep("wood_dark", path, prof, closed=True)
            p0 = roof_pt(x_e, y)
            p1 = roof_pt(x_e - sx * 1.15, y)
            B.beam("wood_dark",
                   Vector((p0.x, p0.y, p0.z - 0.135)),
                   Vector((p1.x, p1.y, p1.z - 0.175)), 0.135, 0.085)
            y += SP
    # 翼角辐射椽
    for sx in (-1, 1):
        for sy in (-1, 1):
            for k in range(8):
                a = R(5 + 11.5 * k)
                base = roof_pt(sx * AX, sy * AY)
                base = Vector((base.x, base.y, base.z - 0.32))
                dirv = Vector((-sx * math.cos(a), -sy * math.sin(a), 0)).normalized()
                p1 = base + dirv * 2.4
                q = roof_pt(p1.x, p1.y)
                B.beam("wood_dark", base, Vector((p1.x, p1.y, q.z - 0.30)), 0.14, 0.17)


def roof_ridges(B):
    zr = Z_RIDGE
    B.abox("tile_ridge", -RX - 0.40, RX + 0.40, -0.42, 0.42, zr - 0.12, zr + 0.20)
    B.abox("tile_ridge", -RX - 0.24, RX + 0.24, -0.32, 0.32, zr + 0.14, zr + 0.80)
    B.abox("tile", -RX - 0.16, RX + 0.16, -0.34, 0.34, zr + 0.76, zr + 0.92)
    # 鸱吻
    for sx in (-1, 1):
        kx = sx * (RX + 0.10)
        sil = [(0.0, 0.14), (0.86, 0.14), (0.98, 0.56), (0.76, 0.96), (0.92, 1.32),
               (1.24, 1.60), (1.08, 1.94), (0.70, 2.14), (0.42, 2.28), (0.16, 2.10),
               (-0.02, 1.70), (-0.10, 0.90)]
        verts = [(kx - sx * u, -0.25, zr + 0.60 + v) for (u, v) in sil]
        verts += [(kx - sx * u, 0.25, zr + 0.60 + v) for (u, v) in sil]
        n = len(sil)
        fs = []
        for i in range(n - 1):
            fs.append((i + 1, i, n + i, n + i + 1))
        fs.append(tuple(range(n)))
        fs.append(tuple(range(2 * n - 1, n - 1, -1)))
        B.poly("tile_ridge", verts, fs)
    # 宝顶
    cz = zr + 0.90
    B.cyl("tile_ridge", Vector((0, 0, cz)), Vector((0, 0, cz + 0.14)), 0.30, 12)
    B.sphere("tile_ridge", Vector((0, 0, cz + 0.36)), 0.23, 12, 8)
    B.cyl("tile_ridge", Vector((0, 0, cz + 0.56)), Vector((0, 0, cz + 0.84)), 0.10, 10, r1=0.02)
    B.cyl("gold", Vector((0, 0, cz + 0.82)), Vector((0, 0, cz + 1.00)), 0.05, 8, r1=0.01)
    # 四条垂脊
    for sx in (-1, 1):
        for sy in (-1, 1):
            path = []
            steps = 18
            for j in range(steps + 1):
                f = (j / steps) ** 1.02
                x = lerp(sx * RX, sx * (AX + FLARE * 0.6), f)
                y = lerp(0, sy * (AY + FLARE * 0.6), f)
                p = roof_pt(x, y)
                path.append(Vector((p.x, p.y, p.z + 0.21)))
            B.sweep("tile_ridge", path,
                    [(-0.36, -0.16), (0.36, -0.16), (0.30, 0.22), (-0.30, 0.22)], closed=True)
            p = path[-1]
            # 套兽（收分小兽头）
            B.poly("tile_ridge",
                   [Vector((p.x - 0.20, p.y - 0.20, p.z - 0.14)),
                    Vector((p.x + 0.20, p.y - 0.20, p.z - 0.14)),
                    Vector((p.x + 0.20, p.y + 0.20, p.z - 0.14)),
                    Vector((p.x - 0.20, p.y + 0.20, p.z - 0.14)),
                    Vector((p.x - 0.10, p.y - 0.10, p.z + 0.34)),
                    Vector((p.x + 0.10, p.y - 0.10, p.z + 0.34)),
                    Vector((p.x + 0.10, p.y + 0.10, p.z + 0.34)),
                    Vector((p.x - 0.10, p.y + 0.10, p.z + 0.34))],
                   [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
            # 角梁（承托翼角，藏于瓦下）
            tip = Vector((sx * (AX - 0.10), sy * (AY - 0.10), roof_pt(sx * (AX - 0.1), sy * (AY - 0.1)).z - 0.30))
            B.beam("wood_dark", Vector((sx * RX, 0, Z_RIDGE - 0.50)), tip, 0.28, 0.30)
            # 走兽
            for k in range(3):
                q = path[int(len(path) * (0.62 + 0.10 * k))]
                B.cyl("tile_ridge", Vector((q.x, q.y, q.z + 0.1)), Vector((q.x, q.y, q.z + 0.34)),
                      0.075, 6, r1=0.01)


def ornament_row(B):
    for i in range(-3, 4):
        if i == 0:
            continue
        x = i * (RX / 3.4)
        z = Z_RIDGE + 0.70
        B.cyl("tile_ridge", Vector((x, 0, z)), Vector((x, 0, z + 0.24)), 0.07, 6, r1=0.008)


# ============ 墙体 / 门窗 ============
def wall_shell(B):
    t = 0.52
    y = YH - t / 2 - 0.05
    B.abox("wall_red", -XH + 0.15, XH - 0.15, y - t / 2, y + t / 2, PLAT_Z, PLAT_Z + COL_H - 0.44)
    for sx in (-1, 1):
        x = sx * (XH - t / 2 - 0.05)
        B.abox("wall_red", x - t / 2, x + t / 2, -YH + 0.15, YH - 0.15, PLAT_Z, PLAT_Z + COL_H - 0.44)
        B.abox("stone_dark", x - t / 2 - 0.04, x + t / 2 + 0.04, -YH, YH, PLAT_Z, PLAT_Z + 0.24)


def front_doors(B):
    """正面：中五间板门（门钉、铺首、门环），两梢间直棂窗 + 槛墙"""
    ydoor = -YH + 0.30
    door_top = PLAT_Z + 3.66
    panel_top = PLAT_Z + COL_H - 0.44
    sill_z = PLAT_Z + 1.46
    fm = "wood_dark"
    for i, (x0, x1) in enumerate([(XS[k], XS[k + 1]) for k in range(7)]):
        if i in (0, 6):
            m = 0.60
            wx0, wx1 = x0 + m, x1 - m
            # 槛墙
            B.abox("plaster", wx0 - 0.10, wx1 + 0.10, ydoor - 0.10, ydoor + 0.22, PLAT_Z, sill_z)
            B.abox("stone_dark", wx0 - 0.16, wx1 + 0.16, ydoor - 0.15, ydoor + 0.22, PLAT_Z, PLAT_Z + 0.12)
            # 窗内暗背板
            B.abox("wood_dark", wx0 - 0.02, wx1 + 0.02, ydoor + 0.14, ydoor + 0.24, sill_z, door_top)
            # 窗框（上下左右）
            B.abox(fm, wx0, wx1, ydoor - 0.15, ydoor + 0.12, sill_z, sill_z + 0.16)
            B.abox(fm, wx0, wx1, ydoor - 0.15, ydoor + 0.12, door_top - 0.18, door_top)
            B.abox(fm, wx0, wx0 + 0.17, ydoor - 0.15, ydoor + 0.12, sill_z, door_top)
            B.abox(fm, wx1 - 0.17, wx1, ydoor - 0.15, ydoor + 0.12, sill_z, door_top)
            # 直棂（方棱木条）
            k = 0
            while True:
                xx = wx0 + 0.32 + k * 0.30
                if xx > wx1 - 0.24:
                    break
                B.abox("wood_red", xx - 0.028, xx + 0.028, ydoor - 0.08, ydoor + 0.04,
                       sill_z + 0.16, door_top - 0.18)
                k += 1
            # 窗上走马板
            B.abox("plaster", x0 + 0.08, x1 - 0.08, ydoor - 0.04, ydoor + 0.18, door_top, panel_top)
        else:
            m = 0.34
            dx0, dx1 = x0 + m, x1 - m
            # 门框
            B.abox(fm, dx0 - 0.20, dx0, ydoor - 0.18, ydoor + 0.14, PLAT_Z, door_top)
            B.abox(fm, dx1, dx1 + 0.20, ydoor - 0.18, ydoor + 0.14, PLAT_Z, door_top)
            B.abox(fm, dx0 - 0.20, dx1 + 0.20, ydoor - 0.20, ydoor + 0.14, door_top - 0.34, door_top)
            # 门槛
            B.abox("wood_red", dx0, dx1, ydoor - 0.24, ydoor + 0.14, PLAT_Z, PLAT_Z + 0.20)
            wd = (dx1 - dx0) / 2
            for leaf in (0, 1):
                lx0 = dx0 + leaf * wd
                lx1 = lx0 + wd
                # 门扇
                B.abox("wood_door", lx0 + 0.015, lx1 - 0.015, ydoor - 0.02, ydoor + 0.10,
                       PLAT_Z + 0.20, door_top - 0.34)
                # 三条穿带（横向压条）
                for fz in (0.13, 0.50, 0.87):
                    zc = PLAT_Z + 0.20 + (door_top - 0.34 - PLAT_Z - 0.20) * fz
                    B.abox("wood_red", lx0 + 0.03, lx1 - 0.03, ydoor - 0.055, ydoor - 0.02,
                           zc - 0.055, zc + 0.055)
                # 门钉（四路×三列）
                for r in range(5):
                    for c in range(3):
                        px = lx0 + 0.26 + c * (wd - 0.52) / 2
                        pz = PLAT_Z + 0.72 + r * 0.60
                        B.sphere("stud", Vector((px, ydoor - 0.045, pz)), 0.055, 10, 7)
                # 铺首 + 门环
                cx = lx0 + (wd * 0.32 if leaf == 0 else wd * 0.68)
                B.cyl("iron", Vector((cx, ydoor - 0.02, PLAT_Z + 2.02)),
                      Vector((cx, ydoor - 0.085, PLAT_Z + 2.02)), 0.15, 14)
                ring = []
                for a in range(19):
                    ang = math.pi * 1.25 * a / 18 - math.pi * 0.12
                    ring.append(Vector((cx + 0.155 * math.cos(ang), ydoor - 0.105,
                                        PLAT_Z + 1.96 + 0.155 * math.sin(ang))))
                B.sweep("iron", ring, [(0.022, 0.022)] * 4, closed=True)
            # 门上走马板
            B.abox("plaster", x0 + 0.10, x1 - 0.10, ydoor - 0.06, ydoor + 0.16, door_top, panel_top)


def side_windows(B):
    """两山面直棂窗（前梢间）"""
    for sx in (-1, 1):
        x = sx * (XH - 0.05)
        y0, y1 = YS[0] + 2.1, YS[1] - 1.9
        z0, z1 = PLAT_Z + 2.55, PLAT_Z + 4.25
        fm = "wood_dark"
        # 暗背板
        B.abox("wood_dark", x - sx * 0.02, x + sx * 0.16, y0, y1, z0, z1)
        # 框
        B.abox(fm, x - sx * 0.16, x + sx * 0.06, y0 - 0.14, y1 + 0.14, z0 - 0.16, z0)
        B.abox(fm, x - sx * 0.16, x + sx * 0.06, y0 - 0.14, y1 + 0.14, z1, z1 + 0.16)
        B.abox(fm, x - sx * 0.16, x + sx * 0.06, y0 - 0.14, y0, z0, z1)
        B.abox(fm, x - sx * 0.16, x + sx * 0.06, y1, y1 + 0.14, z0, z1)
        # 棂条
        k = 0
        while True:
            yy = y0 + 0.28 + k * 0.30
            if yy > y1 - 0.24:
                break
            B.abox("wood_red", x - sx * 0.10, x + sx * 0.02, yy - 0.028, yy + 0.028, z0, z1)
            k += 1


def platform_courses(B):
    """台基压阑石与石缝"""
    for k, z in enumerate((0.20, 0.62)):
        B.abox("stone_dark", -XH - 1.55, XH + 1.55, -YH - 1.55, YH + 1.55, z, z + 0.03)


def architrave(B):
    for sy in (-1, 1):
        y = sy * YH
        for i in range(len(XS) - 1):
            x0, x1 = XS[i], XS[i + 1]
            z0, z1 = z_top(x0, y), z_top(x1, y)
            B.beam("wood_red", Vector((x0 - 0.01 * x0, y, z0 - 0.44)),
                   Vector((x1 - 0.01 * x1, y, z1 - 0.44)), 0.28, 0.42, rot=rotz(R(90 if sy > 0 else -90)))
            B.beam("wood_red", Vector((x0 - 0.01 * x0, y, z0 - 0.02)),
                   Vector((x1 - 0.01 * x1, y, z1 - 0.02)), 0.44, 0.18, rot=rotz(R(90 if sy > 0 else -90)))
    for sx in (-1, 1):
        x = sx * XH
        for j in range(len(YS) - 1):
            y0, y1 = YS[j], YS[j + 1]
            z0, z1 = z_top(x, y0), z_top(x, y1)
            B.beam("wood_red", Vector((x, y0, z0 - 0.44)), Vector((x, y1, z1 - 0.44)), 0.28, 0.42)
            B.beam("wood_red", Vector((x, y0, z0 - 0.02)), Vector((x, y1, z1 - 0.02)), 0.44, 0.18)


def columns(B):
    for sy in (-1, 1):
        for x in XS:
            column(B, x, sy * YH)
    for sx in (-1, 1):
        for y in YS[1:-1]:
            column(B, sx * XH, y)


def gongyan_wall(B):
    """拱眼壁：斗栱之间的填塞板（前后檐、两山）"""
    for sy in (-1, 1):
        y = sy * (YH - 0.02)
        for i in range(len(XS) - 1):
            x0, x1 = XS[i] + 0.1, XS[i + 1] - 0.1
            z0 = z_top((x0 + x1) / 2, sy * YH) + 0.50
            B.abox("wall_red", x0, x1, y - sy * 0.06, y + sy * 0.06, z0, z0 + 1.30)
    for sx in (-1, 1):
        x = sx * (XH - 0.02)
        for j in range(len(YS) - 1):
            y0, y1 = YS[j] + 0.1, YS[j + 1] - 0.1
            z0 = z_top(sx * XH, (y0 + y1) / 2) + 0.50
            B.abox("wall_red", x - 0.06, x + 0.06, y0, y1, z0, z0 + 1.30)


def under_eave(B):
    """撩檐槫 + 檐檩 + 柱头枋"""
    for sy in (-1, 1):
        y = sy * YH
        # 撩檐槫（出 1.90）
        pts = []
        for i in range(41):
            x = -AX + 2 * AX * i / 40
            p = roof_pt(x, y + sy * EAVE_OUT)
            pts.append(Vector((x, y + sy * 1.90, p.z - 0.55)))
        B.sweep("wood_dark", pts,
                [(0.16 * math.cos(math.pi * 2 * k / 12), 0.16 * math.sin(math.pi * 2 * k / 12)) for k in range(12)],
                closed=True)
        # 柱头枋
        for zz in (1.50, 1.88):
            p2 = []
            for i in range(31):
                x = -XH + 2 * XH * i / 30
                p2.append(Vector((x, y, z_top(x, y) + 0.16 + zz)))
            B.sweep("wood_dark", p2, [(-0.12, -0.15), (0.12, -0.15), (0.12, 0.15), (-0.12, 0.15)], closed=True)
    for sx in (-1, 1):
        x = sx * XH
        pts = []
        for i in range(41):
            y = -AY + 2 * AY * i / 40
            p = roof_pt(x + sx * EAVE_OUT, y)
            pts.append(Vector((x + sx * 1.90, y, p.z - 0.55)))
        B.sweep("wood_dark", pts,
                [(0.16 * math.cos(math.pi * 2 * k / 12), 0.16 * math.sin(math.pi * 2 * k / 12)) for k in range(12)],
                closed=True)
        for zz in (1.50, 1.88):
            p2 = []
            for i in range(31):
                y = -YH + 2 * YH * i / 30
                p2.append(Vector((x, y, z_top(x, y) + 0.16 + zz)))
            B.sweep("wood_dark", p2, [(-0.12, -0.15), (0.12, -0.15), (0.12, 0.15), (-0.12, 0.15)], closed=True)


def text_mesh(B, mat, txt, size, loc, rz=0.0, extrude=0.02):
    try:
        cur = bpy.data.curves.new(name="txt", type='FONT')
        cur.body = txt
        cur.size = size
        cur.extrude = extrude
        cur.align_x = 'CENTER'
        cur.align_y = 'CENTER'
        try:
            f = bpy.data.fonts.load(FONT, check_existing=True)
            cur.font = f
        except Exception:
            pass
        ob = bpy.data.objects.new("txt", cur)
        bpy.context.scene.collection.objects.link(ob)
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        M = Matrix.Translation(Vector(loc)) @ Matrix.Rotation(rz, 4, 'Z')
        vs = [M @ v.co for v in me.vertices]
        fs = [tuple(p.vertices) for p in me.polygons]
        B.poly(mat, vs, fs)
        bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.meshes.remove(me)
        bpy.data.curves.remove(cur)
    except Exception as e:
        print("text fail", txt, e)


def plaque(B):
    y = -YH - 0.16
    z0 = PLAT_Z + 3.78
    h = 1.78
    B.abox("plaque", -1.02, 1.02, y - 0.10, y + 0.08, z0, z0 + h)
    for (a, b, c, d) in [(-1.14, 1.14, z0 + h, z0 + h + 0.16), (-1.14, 1.14, z0 - 0.16, z0),
                         (-1.14, -1.00, z0 - 0.16, z0 + h + 0.16), (1.00, 1.14, z0 - 0.16, z0 + h + 0.16)]:
        B.abox("wood_red", a, b, y - 0.12, y + 0.10, c, d)
    # 匾文：佛光 / 真容 / 禅寺（自右向左三列）
    rows = [z0 + h - 0.54, z0 + 0.50]
    txts = [("佛", "光"), ("真", "容"), ("禅", "寺")]
    for ci, (c1, c2) in enumerate(txts):
        cx = 0.60 - ci * 0.60
        text_mesh(B, "gold", c1, 0.47, (cx, y - 0.115, rows[0]), R(90))
        text_mesh(B, "gold", c2, 0.47, (cx, y - 0.115, rows[1]), R(90))
    for sx in (-1, 1):
        B.beam("wood_dark", Vector((sx * 1.1, y, z0 + h + 0.1)),
               Vector((sx * 1.1, y, PLAT_Z + COL_H - 0.40)), 0.05, 0.05)


def platform(B):
    # 台基
    B.abox("stone", -XH - 1.45, XH + 1.45, -YH - 1.45, YH + 1.45, 0.0, PLAT_Z - 0.05)
    B.abox("stone", -XH - 1.52, XH + 1.52, -YH - 1.52, YH + 1.52, PLAT_Z - 0.22, PLAT_Z - 0.04)
    B.abox("pave", -XH - 1.50, XH + 1.50, -YH - 1.50, YH + 1.50, PLAT_Z - 0.05, PLAT_Z)
    B.abox("stone_dark", -XH - 1.48, XH + 1.48, -YH - 1.48, YH + 1.48, 0.30, 0.42)
    # 前月台
    B.abox("stone", -12.6, 12.6, -YH - 6.8, -YH - 1.5, 0.0, 0.52)
    B.abox("stone", -12.7, 12.7, -YH - 6.9, -YH - 1.5, 0.36, 0.47)
    B.abox("pave", -12.6, 12.6, -YH - 6.8, -YH - 1.5, 0.44, 0.52)
    # 月台前踏道
    for k in range(4):
        z = 0.52 * (4 - k) / 4
        y0 = -YH - 6.8 - (k + 1) * 0.36
        B.abox("stone_dark", -4.4, 4.4, y0, y0 + 0.38, 0.0, z)
    # 台基至月台踏步
    for k in range(3):
        z = PLAT_Z - (PLAT_Z - 0.52) * (k + 1) / 3.4
        y0 = -YH - 1.5 - (k + 1) * 0.32
        B.abox("stone_dark", -3.8, 3.8, y0, y0 + 0.34, 0.0, z)


def balustrade(B):
    """月台石栏：实心栏板 + 望柱"""
    y = -YH - 6.72
    n = 11
    span = 24.9
    for i in range(n):
        x = -span / 2 + i * span / (n - 1)
        if -4.8 < x < 4.8:
            continue
        B.abox("stone", x - 0.13, x + 0.13, y - 0.13, y + 0.13, 0.52, 1.30)
        B.abox("stone", x - 0.17, x + 0.17, y - 0.17, y + 0.17, 1.30, 1.44)
        B.poly("stone", [Vector((x - 0.17, y - 0.17, 1.44)), Vector((x + 0.17, y - 0.17, 1.44)),
                         Vector((x + 0.17, y + 0.17, 1.44)), Vector((x - 0.17, y + 0.17, 1.44)),
                         Vector((x - 0.10, y - 0.10, 1.62)), Vector((x + 0.10, y - 0.10, 1.62)),
                         Vector((x + 0.10, y + 0.10, 1.62)), Vector((x - 0.10, y + 0.10, 1.62))],
               [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
    # 栏板
    for i in range(n - 1):
        x0 = -span / 2 + i * span / (n - 1) + 0.13
        x1 = -span / 2 + (i + 1) * span / (n - 1) - 0.13
        if x1 <= x0 or (x0 < 4.8 and x1 > -4.8):
            continue
        B.abox("stone", x0, x1, y - 0.09, y + 0.09, 0.52, 1.02)
        B.abox("stone", x0, x1, y - 0.11, y + 0.11, 1.02, 1.14)
    # 两侧小栏板
    for sx in (-1, 1):
        x = sx * 12.55
        for k in range(3):
            yy = -YH - 6.6 + k * 2.55
            B.abox("stone", x - 0.12, x + 0.12, yy - 0.12, yy + 0.12, 0.52, 1.28)
        B.abox("stone", x - 0.08, x + 0.08, -YH - 6.6, -YH - 1.6, 0.52, 1.02)


def ground(B):
    B.abox("ground", -80, 80, -70, 70, -0.6, -0.02)


def sutra_pillar(B):
    x, y = 0.0, -YH - 4.6
    z = 0.52
    B.cyl("stone", Vector((x, y, z)), Vector((x, y, z + 0.22)), 0.50, 12)
    B.cyl("stone", Vector((x, y, z + 0.22)), Vector((x, y, z + 0.34)), 0.34, 12, r1=0.28)
    B.cyl("stone", Vector((x, y, z + 0.34)), Vector((x, y, z + 1.86)), 0.23, 10, r1=0.20)
    B.cyl("stone", Vector((x, y, z + 1.86)), Vector((x, y, z + 1.98)), 0.44, 12, r1=0.29)
    B.cyl("stone", Vector((x, y, z + 1.98)), Vector((x, y, z + 2.12)), 0.29, 12, r1=0.17)
    B.cyl("stone", Vector((x, y, z + 2.12)), Vector((x, y, z + 2.38)), 0.09, 8, r1=0.12)
    B.sphere("stone", Vector((x, y, z + 2.48)), 0.12, 10, 8)
    B.cyl("stone", Vector((x, y, z + 2.58)), Vector((x, y, z + 2.76)), 0.05, 6, r1=0.01)


def build(coll, mats):
    B = Builder()
    ground(B)
    platform(B)
    platform_courses(B)
    balustrade(B)
    columns(B)
    wall_shell(B)
    architrave(B)
    front_doors(B)
    side_windows(B)
    brackets(B)
    gongyan_wall(B)
    under_eave(B)
    _faces = roof_faces(B)
    eave_rim(B, _faces)
    tile_runs(B)
    rafters(B)
    roof_ridges(B)
    ornament_row(B)
    plaque(B)
    sutra_pillar(B)
    return B
