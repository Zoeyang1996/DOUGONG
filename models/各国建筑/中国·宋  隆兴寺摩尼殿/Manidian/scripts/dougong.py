# -*- coding: utf-8 -*-
"""宋式斗拱（五铺作双抄单下昂意象）程序化单元
局部坐标：x 沿墙面，y 向外（出跳方向），z 向上；原点在栌斗底面中心。
"""
import math
from mathutils import Vector, Matrix, Euler


def _unit(mb, Mb, h=1.0, out=1.0):
    """在变换矩阵 Mb 下放置一朵斗拱"""
    def put(c, s, rot=(0, 0, 0), top=(1, 1), bot=(1, 1)):
        v = Mb @ Vector(c)
        R = Mb.to_3x3().to_euler()
        e = Euler((rot[0] + R.x, rot[1] + R.y, rot[2] + R.z), 'XYZ')
        sc = Mb.to_scale()
        mb.cuboid((v.x, v.y, v.z), (s[0] * sc.x, s[1] * sc.y, s[2] * sc.z),
                  rot=(e.x, e.y, e.z), top=top, bot=bot)

    def put_mm(x0, x1, y0, y1, z0, z1, top=None, bot=None):
        c = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
        s = (max(0.02, abs(x1 - x0)), max(0.02, abs(y1 - y0)),
             max(0.02, abs(z1 - z0)))
        put(c, s, top=top or (1, 1), bot=bot or (1, 1))

    S = h
    # 栌斗
    put_mm(-0.23, 0.23, -0.23, 0.23, 0.0, 0.30, top=(1.0, 1.0), bot=(0.72, 0.72))
    put_mm(-0.20, 0.20, -0.20, 0.20, 0.30, 0.36, top=(1.15, 1.15))

    # 泥道拱（横）+ 华拱一抄（出）
    put_mm(-0.62, 0.62, -0.10, 0.10, 0.36, 0.60)
    put_mm(-0.10, 0.10, -0.30, 0.62 * out + 0.10, 0.36, 0.60)
    # 拱头卷杀（略）
    for yy in (0.62 * out + 0.06,):
        put_mm(-0.11, 0.11, yy - 0.06, yy + 0.06, 0.36, 0.52)
    # 两端散斗
    for xx in (-0.62, 0.62):
        put_mm(xx - 0.10, xx + 0.10, -0.10, 0.10, 0.60, 0.74, top=(1.2, 1.2))
    put_mm(-0.10, 0.10, 0.62 * out + 0.10, 0.62 * out + 0.30, 0.60, 0.74,
           top=(1.2, 1.2))

    # 第二层：慢拱（横，长）+ 华拱二抄
    put_mm(-0.86, 0.86, -0.10, 0.10, 0.74, 0.96)
    put_mm(-0.10, 0.10, -0.24, 1.20 * out + 0.10, 0.74, 0.96)
    for xx in (-0.86, 0.86):
        put_mm(xx - 0.10, xx + 0.10, -0.10, 0.10, 0.96, 1.10, top=(1.2, 1.2))
    put_mm(-0.10, 0.10, 1.20 * out + 0.10, 1.20 * out + 0.26, 0.96, 1.10,
           top=(1.2, 1.2))

    # 下昂：向外斜下挑出
    put_mm(-0.09, 0.09, -0.30, 1.60 * out + 0.10, 1.10, 1.26)
    ang_z = -0.16
    put((-0.0, 1.10 * out, 1.10), (0.16, 1.30 * out, 0.20), rot=(0, 0, 0))
    # 昂嘴
    put((0.0, 1.66 * out + 0.10, 1.06), (0.18, 0.42, 0.16), rot=(math.radians(-9), 0, 0))

    # 令拱（横）+ 耍头（出）
    put_mm(-0.72, 0.72, -0.10, 0.10, 1.26, 1.44)
    put_mm(-0.09, 0.09, -0.10, 1.80 * out + 0.06, 1.26, 1.42)
    # 替木 / 撩檐枋底
    put_mm(-0.80, 0.80, -0.11, 0.11, 1.44, 1.58)
    for xx in (-0.72, 0.0, 0.72):
        put_mm(xx - 0.09, xx + 0.09, -0.09, 0.09, 1.44, 1.56, top=(1.2, 1.2))
    return


def row_x(mb, y, z, x0, x1, h=1.0, out=1.0, spacing=1.55, rot_extra=0.0):
    """沿 x 方向排布（墙面朝 +y 或 -y）"""
    n = max(1, int(round(abs(x1 - x0) / spacing)))
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        M = Matrix.Translation((x, y, z)) @ Euler((0, 0, rot_extra), 'XYZ').to_matrix().to_4x4()
        _unit(mb, M, h, out)
    return n


def row_y(mb, x, z, y0, y1, h=1.0, out=1.0, spacing=1.55, rot_extra=math.pi / 2):
    n = max(1, int(round(abs(y1 - y0) / spacing)))
    for i in range(n + 1):
        y = y0 + (y1 - y0) * i / n
        M = Matrix.Translation((x, y, z)) @ Euler((0, 0, rot_extra), 'XYZ').to_matrix().to_4x4()
        _unit(mb, M, h, out)
    return n


def arch_panel(mb, axis, pos, a0, a1, z0, z1, t=0.14):
    """拱眼壁：斗拱行背后的连续板，使斗拱成组而不是散落的方块"""
    if axis == 'x':
        mb.box_minmax(a0, a1, pos, pos + t, z0, z1)
    else:
        mb.box_minmax(pos, pos + t, a0, a1, z0, z1)


def bands(mb, hw, hd, zz, layers=((0.28, 0.15, 0.33),
                                 (0.70, 0.17, 0.45),
                                 (1.12, 0.18, 0.53))):
    """三道连续拱枋（泥道拱／慢拱／令拱）

    单朵斗拱做得很细，纯靠阵列在远处会碎成一排小方块；
    补上三道连续的水平拱枋，斗拱带才有"层叠"的读感——这是宋式檐下的关键特征。
    """
    for (dz, hh, ex) in layers:
        z0b, z1b = zz + dz, zz + dz + hh
        mb.box_minmax(-hw - ex, hw + ex, hd - 0.34, hd + ex, z0b, z1b)
        mb.box_minmax(-hw - ex, hw + ex, -hd - ex, -hd + 0.34, z0b, z1b)
        mb.box_minmax(-hw - ex, -hw + 0.34, -hd, hd, z0b, z1b)
        mb.box_minmax(hw - 0.34, hw + ex, -hd, hd, z0b, z1b)
