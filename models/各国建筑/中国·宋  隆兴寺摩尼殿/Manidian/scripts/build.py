# -*- coding: utf-8 -*-
"""隆兴寺摩尼殿 —— 主装配脚本"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector, Euler, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import params as P
from blib import (clear_scene, ensure_coll, MB, lerp)
import mats as MM
import roof as R
import skirt as SK
import dougong as DG
import walls as W


# ------------------------------------------------------------------ 台基
def build_podium(mats, coll):
    """低台基：照片里殿身只比庭院高两三级踏步，不是宫殿式高台"""
    mb = MB()
    x, y = P.PLAT_W / 2, P.PLAT_D / 2
    mb.box_minmax(-x - 0.10, x + 0.10, -y - 0.10, y + 0.10, 0.02, 0.26)
    mb.box_minmax(-x, x, -y, y, 0.26, P.PLAT_Z)
    # 阶条石分缝（只在压边石上）
    n = 30
    for i in range(n + 1):
        px = -x + 2 * x * i / n
        mb.box_minmax(px - 0.03, px + 0.03, y - 0.34, y + 0.02, 0.26, P.PLAT_Z - 0.02)
        mb.box_minmax(px - 0.03, px + 0.03, -y - 0.02, -y + 0.34, 0.26, P.PLAT_Z - 0.02)
    ob = mb.build("台基_阶条石", mats.stone, coll, auto_smooth=30)

    # 踏跺：三级，整面缓步
    mb = MB()
    steps = 3
    for i in range(steps):
        z1 = P.PLAT_Z * (i + 1) / steps
        z0 = 0.02
        yy = y + 0.06 + (steps - i - 1) * 0.46
        mb.box_minmax(-6.2, 6.2, yy, yy + 0.48, z0, z1)
    # 垂带
    for sx in (-1, 1):
        mb.box_minmax(sx * 6.2, sx * 6.55, y + 0.06, y + 0.06 + steps * 0.46,
                      0.02, P.PLAT_Z)
    ob2 = mb.build("台基_踏跺", mats.stone, coll, auto_smooth=30)
    return [ob, ob2]


# ------------------------------------------------------------------ 下层
def build_lower(mats, coll_wall, coll_dg, coll_door):
    hw, hd = P.BODY_W / 2, P.BODY_D / 2
    mb = MB()
    z0, z1 = P.WALL_Z0, P.WALL_Z1
    pz = z0 + P.BS_PORTAL_H
    # 墙体（十字形，四面居中开抱厦门洞；洞口尺寸与抱厦前檐完全一致）
    W.wall_face(mb, 'x', hd - 0.9, 0.9, -hw, hw, z0, z1,
                [(0, P.BS_PORTAL_W, z0, pz)])
    W.wall_face(mb, 'x', -hd, 0.9, -hw, hw, z0, z1,
                [(0, P.BS_PORTAL_W, z0, pz)])
    W.wall_face(mb, 'y', hw - 0.9, 0.9, -hd, hd, z0, z1,
                [(0, P.BS_PORTAL_W, z0, pz)])
    W.wall_face(mb, 'y', -hw, 0.9, -hd, hd, z0, z1,
                [(0, P.BS_PORTAL_W, z0, pz)])
    # 墙基（石活）—— 让开门洞，避免门槛被埋
    for (a, b, c, d, ax) in ((-hw, hw, hd - 0.9, hd, 'x'),
                             (-hw, hw, -hd, -hd + 0.9, 'x'),
                             (-hw, -hw + 0.9, -hd, hd, 'y'),
                             (hw - 0.9, hw, -hd, hd, 'y')):
        if ax == 'x':
            for u0, u1 in ((a, -P.BS_PORTAL_W / 2), (P.BS_PORTAL_W / 2, b)):
                mb.box_minmax(u0, u1, c, d, z0, z0 + 0.34)
        else:
            for u0, u1 in ((c, -P.BS_PORTAL_W / 2), (P.BS_PORTAL_W / 2, d)):
                mb.box_minmax(a, b, u0, u1, z0, z0 + 0.34)
    wall = mb.build("墙身_下层", mats.wall, coll_wall, auto_smooth=None)

    # 抱厦内门道：与抱厦外檐同一套门洞，无门扇（开敞，通向殿内）
    mb_fr = MB()
    mb_th = MB()
    for (ax, fc, o) in (('y', hd, 1.0), ('y', -hd, -1.0),
                        ('x', hw, 1.0), ('x', -hw, -1.0)):
        W.portal(mb_fr, None, None, mb_th, ax, fc, 0.0, P.BS_PORTAL_W,
                 P.BS_PORTAL_H, z0, out=o, door=False)
    dfr = mb_fr.build("门框_殿身", mats.wood_red, coll_wall, auto_smooth=None)
    dth = mb_th.build("门槛_殿身", mats.stone_dark, coll_wall, auto_smooth=None)

    # 柱、额枋
    mb = MB()
    for sx in (-1, 1):
        for sy in (-1, 1):
            W.column(mb, sx * hw, sy * hd, z0, z1, r=0.32)
    for (a, b, c, d, ax) in ((0, 0, 0, 0, 0),):
        pass
    # 四周额枋
    mb.box_minmax(-hw - 0.10, hw + 0.10, hd - 0.34, hd + 0.06, z1 - 0.02, z1 + 0.55)
    mb.box_minmax(-hw - 0.10, hw + 0.10, -hd - 0.06, -hd + 0.34, z1 - 0.02, z1 + 0.55)
    mb.box_minmax(-hw - 0.06, -hw + 0.34, -hd, hd, z1 - 0.02, z1 + 0.55)
    mb.box_minmax(hw - 0.34, hw + 0.06, -hd, hd, z1 - 0.02, z1 + 0.55)
    # 平板枋
    for (a, b, c, d) in ((-hw - 0.14, hw + 0.14, hd - 0.34, hd + 0.14),
                         (-hw - 0.14, hw + 0.14, -hd - 0.14, -hd + 0.34),
                         (-hw - 0.14, -hw + 0.34, -hd, hd),
                         (hw - 0.34, hw + 0.14, -hd, hd)):
        mb.box_minmax(a, b, c, d, z1 + 0.55, z1 + 0.75)
    frame = mb.build("额枋_下层", mats.wood_beam, coll_wall, auto_smooth=30)

    # 斗拱：单朵放大、间距放宽 —— 远看才不会碎成一排小方块
    mb = MB()
    zz = P.DG0_Z
    DG.row_x(mb, hd + 0.10, zz, -hw + 0.7, hw - 0.7, h=1.10, out=0.74, spacing=1.92)
    DG.row_x(mb, -hd - 0.10, zz, -hw + 0.7, hw - 0.7, h=1.10, out=0.74,
             spacing=1.92, rot_extra=math.pi)
    DG.row_y(mb, -hw - 0.10, zz, -hd + 0.7, hd - 0.7, h=1.10, out=0.74,
             spacing=1.92, rot_extra=math.pi / 2)
    DG.row_y(mb, hw + 0.10, zz, -hd + 0.7, hd - 0.7, h=1.10, out=0.74,
             spacing=1.92, rot_extra=-math.pi / 2)
    DG.bands(mb, hw + 0.10, hd + 0.10, zz,
             layers=((0.30, 0.18, 0.42), (0.76, 0.20, 0.56), (1.22, 0.21, 0.66)))
    # 转角铺作（45° 向心，填住两行斗拱在角部的空档）
    for sx in (-1, 1):
        for sy in (-1, 1):
            M = Matrix.Translation((sx * (hw + 0.10), sy * (hd + 0.10), zz)) @ \
                Euler((0, 0, math.atan2(sy, sx)), 'XYZ').to_matrix().to_4x4()
            DG._unit(mb, M, 1.10, 0.74)
    # 拱眼壁（独立暗色板，衬托斗拱浮雕）
    mb_pl = MB()
    DG.arch_panel(mb_pl, 'x', hd + 0.02, -hw, hw, zz, zz + 1.44)
    DG.arch_panel(mb_pl, 'x', -hd - 0.16, -hw, hw, zz, zz + 1.44)
    DG.arch_panel(mb_pl, 'y', -hw - 0.16, -hd, hd, zz, zz + 1.44)
    DG.arch_panel(mb_pl, 'y', hw + 0.02, -hd, hd, zz, zz + 1.44)
    pl = mb_pl.build("拱眼壁_下檐", mats.panel, coll_dg, auto_smooth=None)
    dg = mb.build("斗拱_下檐", mats.wood, coll_dg, auto_smooth=30)

    # 撩檐枋
    mb = MB()
    for (a, b, c, d) in ((-hw - 0.2, hw + 0.2, hd + 0.95, hd + 1.35),
                         (-hw - 0.2, hw + 0.2, -hd - 1.35, -hd - 0.95),
                         (-hw - 1.35, -hw - 0.95, -hd - 0.2, hd + 0.2),
                         (hw + 0.95, hw + 1.35, -hd - 0.2, hd + 0.2)):
        mb.box_minmax(a, b, c, d, zz + 1.42, zz + 1.68)
    lt = mb.build("撩檐枋_下檐", mats.wood_red, coll_dg, auto_smooth=30)
    return [wall, frame, dg, lt, dfr, dth]


def build_baosha_unit(mats, coll_wall, coll_dg):
    """单座抱厦（局部坐标：沿 +x 外伸，原点在主墙外皮）

    立面按参考照片做成「面阔三间」：明间开敞门道，两次间装格扇窗，
    窗洞与明间洞同高，柱列在 ±2.25 / ±6.15 / ±7.80 三对位置。
    """
    objs = []
    w2 = P.BS_W / 2
    z0, z1 = P.WALL_Z0, P.WALL_Z1
    mw, ww = P.BS_PORTAL_W, P.BS_WIN_W
    st = mw / 2 + ww / 2               # 次间中心 = 4.20
    zt = z0 + P.BS_PORTAL_H            # 洞口上沿
    zw = z0 + P.BS_WIN_Z0              # 窗台（槛墙上沿）

    mb = MB()
    # 前墙：五开间（窗－门－门－门－窗），按照片的洞口排布
    cw = P.BS_PORTAL_W / 2
    dw = P.BS_DOOR_S / 2
    dc = cw + P.BS_POST + dw                      # 次间门中心
    wc = cw + P.BS_POST + P.BS_DOOR_S + P.BS_POST + P.BS_WIN_W / 2
    ops = [(0.0, P.BS_PORTAL_W, z0, z0 + P.BS_PORTAL_H)]
    for sy in (-1, 1):
        ops.append((sy * dc, P.BS_DOOR_S, z0, z0 + P.BS_DOOR_SH))
        ops.append((sy * wc, P.BS_WIN_W, z0 + P.BS_WIN_Z0,
                    z0 + P.BS_WIN_Z0 + P.BS_WIN_H))
    W.wall_face(mb, 'y', P.BS_OUT - 0.85, 0.85, -w2, w2, z0, z1, ops)
    # 两侧墙
    W.wall_face(mb, 'x', w2 - 0.68, 0.68, 0.0, P.BS_OUT, z0, z1)
    W.wall_face(mb, 'x', -w2, 0.68, 0.0, P.BS_OUT, z0, z1)
    # 墙基（石活）：只让开三个门洞，窗下槛墙保留
    for u0, u1 in ((-w2, -(dc + dw)), (cw + P.BS_POST, cw),
                   (dc - dw, dc + dw), (-cw, -cw - P.BS_POST),
                   (dc + dw, w2)):
        if u1 - u0 > 0.01:
            mb.box_minmax(P.BS_OUT - 0.9, P.BS_OUT, u0, u1, z0, z0 + 0.30)
    mb.box_minmax(-w2, P.BS_OUT, w2 - 0.7, w2, z0, z0 + 0.30)
    mb.box_minmax(-w2, P.BS_OUT, -w2, -w2 + 0.7, z0, z0 + 0.30)
    objs.append(mb.build("抱厦_墙身", mats.wall, coll_wall, auto_smooth=None))

    # 柱列 + 额枋 + 平板枋
    mb = MB()
    for sy in (-1, 1):
        W.column(mb, P.BS_OUT - 0.05, sy * w2, z0, z1, r=0.28)
        W.column(mb, P.BS_OUT - 0.05, sy * (cw + P.BS_POST / 2), z0, z1, r=0.17)
        W.column(mb, P.BS_OUT - 0.05,
                 sy * (cw + P.BS_POST + P.BS_DOOR_S + P.BS_POST / 2),
                 z0, z1, r=0.17)
    # 通长阑额（原木本色，照片里最醒目的一条）
    mb.box_minmax(P.BS_OUT - 0.40, P.BS_OUT + 0.06, -w2 - 0.10, w2 + 0.10,
                  z1 - 0.02, z1 + 0.55)
    # 平板枋（朱漆）
    mb.box_minmax(P.BS_OUT - 0.44, P.BS_OUT + 0.14, -w2 - 0.14, w2 + 0.14,
                  z1 + 0.55, z1 + 0.75)
    for sy in (-1, 1):
        mb.box_minmax(0.2, P.BS_OUT + 0.06, sy * w2 - (0.40 if sy > 0 else -0.06),
                      sy * w2 + (0.06 if sy > 0 else 0.40), z1 - 0.02, z1 + 0.55)
    objs.append(mb.build("抱厦_额枋", mats.wood_beam, coll_wall, auto_smooth=30))

    # 斗拱
    mb = MB()
    zz = P.DG0_Z
    DG.row_y(mb, P.BS_OUT + 0.06, zz, -w2 + 0.6, w2 - 0.6, h=1.08, out=0.70,
             spacing=1.94, rot_extra=-math.pi / 2)
    DG.row_x(mb, w2 + 0.06, zz, 0.3, P.BS_OUT - 0.3, h=1.08, out=0.70,
             spacing=1.94, rot_extra=0.0)
    DG.row_x(mb, -w2 - 0.06, zz, 0.3, P.BS_OUT - 0.3, h=1.08, out=0.70,
             spacing=1.94, rot_extra=math.pi)
    for sy in (-1, 1):
        M = Matrix.Translation((P.BS_OUT + 0.06, sy * (w2 + 0.06), zz)) @ \
            Euler((0, 0, sy * math.pi / 4), 'XYZ').to_matrix().to_4x4()
        DG._unit(mb, M, 1.08, 0.70)
    # 三道连续拱枋
    for (dz, hh, ex) in ((0.32, 0.17, 0.38), (0.78, 0.19, 0.52),
                         (1.22, 0.20, 0.60)):
        z0b, z1b = zz + dz, zz + dz + hh
        mb.box_minmax(P.BS_OUT - 0.30, P.BS_OUT + ex, -w2 - 0.06, w2 + 0.06,
                      z0b, z1b)
        for sy in (-1, 1):
            mb.box_minmax(0.10, P.BS_OUT + ex,
                          sy * (w2 + 0.06) - (0.30 if sy > 0 else 0.0),
                          sy * (w2 + 0.06) + (0.0 if sy > 0 else 0.30),
                          z0b, z1b)
    # 拱眼壁
    mb_pl = MB()
    DG.arch_panel(mb_pl, 'y', P.BS_OUT + 0.02, -w2, w2, zz, P.BR_EAVE - 0.30)
    DG.arch_panel(mb_pl, 'x', w2 + 0.02, 0.2, P.BS_OUT, zz, P.BR_EAVE - 0.30)
    DG.arch_panel(mb_pl, 'x', -w2 - 0.16, 0.2, P.BS_OUT, zz, P.BR_EAVE - 0.30)
    objs.append(mb_pl.build("抱厦_拱眼壁", mats.panel, coll_dg, auto_smooth=None))
    # 撩檐枋
    mb.box_minmax(P.BS_OUT + 0.95, P.BS_OUT + 1.32, -w2 - 0.2, w2 + 0.2,
                  P.BR_EAVE - 0.42, P.BR_EAVE - 0.12)
    for sy in (-1, 1):
        mb.box_minmax(0.1, P.BS_OUT + 1.32, sy * (w2 + 0.2) - (0.37 if sy > 0 else 0),
                      sy * (w2 + 0.2) + (0 if sy > 0 else 0.37),
                      P.BR_EAVE - 0.42, P.BR_EAVE - 0.12)
    objs.append(mb.build("抱厦_斗拱", mats.wood, coll_dg, auto_smooth=30))

    # 三樘门：门框 + 上槛 + 石门槛（开敞，无门扇）
    mb_fr = MB()
    mb_th = MB()
    for (uc, ww_, hh_) in ((0.0, P.BS_PORTAL_W, P.BS_PORTAL_H),
                           (-dc, P.BS_DOOR_S, P.BS_DOOR_SH),
                           (dc, P.BS_DOOR_S, P.BS_DOOR_SH)):
        xf = P.BS_OUT
        a0, a1 = uc - ww_ / 2, uc + ww_ / 2
        zt = z0 + hh_
        j = 0.11
        # 立颊
        for u0, u1 in ((a0, a0 + j), (a1 - j, a1)):
            mb_fr.box_minmax(xf - 0.26, xf + 0.04, u0, u1, z0, zt + 0.02)
        # 上槛
        mb_fr.box_minmax(xf - 0.26, xf + 0.04, a0, a1, zt - 0.22, zt + 0.02)
        # 石门槛
        mb_th.box_minmax(xf - 0.34, xf + 0.06, a0, a1, z0, z0 + 0.16)
    objs.append(mb_fr.build("抱厦_门框", mats.wood_red, coll_wall,
                            auto_smooth=None))
    objs.append(mb_th.build("抱厦_门槛", mats.stone_dark, coll_wall,
                            auto_smooth=30))

    # 两梢间直棂窗
    mb_w = MB()
    mb_wd = MB()
    for sy in (-1, 1):
        yc = sy * wc
        W.lattice_window(mb_w, mb_wd, 'y', P.BS_OUT - 0.10,
                         yc - P.BS_WIN_W / 2 + 0.02, yc + P.BS_WIN_W / 2 - 0.02,
                         z0 + P.BS_WIN_Z0, z0 + P.BS_WIN_Z0 + P.BS_WIN_H,
                         tdir=1.0, bar=0.042, gap=0.108)
    objs.append(mb_w.build("抱厦_格扇窗", mats.wood_red, coll_wall,
                           auto_smooth=None))
    objs.append(mb_wd.build("抱厦_窗内暗板", mats.panel, coll_wall,
                            auto_smooth=None))
    return objs

# ------------------------------------------------------------------ 上檐
def build_upper(mats, coll_wall, coll_dg):
    hw, hd = P.UP_W / 2, P.UP_D / 2
    z0, z1 = P.UP_Z0, P.UP_Z1
    mb = MB()
    W.wall_face(mb, 'x', hd - 0.7, 0.7, -hw, hw, z0, z1)
    W.wall_face(mb, 'x', -hd, 0.7, -hw, hw, z0, z1)
    W.wall_face(mb, 'y', hw - 0.7, 0.7, -hd, hd, z0, z1)
    W.wall_face(mb, 'y', -hw, 0.7, -hd, hd, z0, z1)
    objs = [mb.build("墙身_上层", mats.wall, coll_wall, auto_smooth=None)]

    mb = MB()
    mb.box_minmax(-hw - 0.08, hw + 0.08, hd - 0.26, hd + 0.06, z1 - 0.02, z1 + 0.36)
    mb.box_minmax(-hw - 0.08, hw + 0.08, -hd - 0.06, -hd + 0.26, z1 - 0.02, z1 + 0.36)
    mb.box_minmax(-hw - 0.06, -hw + 0.26, -hd, hd, z1 - 0.02, z1 + 0.36)
    mb.box_minmax(hw - 0.26, hw + 0.06, -hd, hd, z1 - 0.02, z1 + 0.36)
    for (a, b, c, d) in ((-hw - 0.12, hw + 0.12, hd - 0.30, hd + 0.12),
                         (-hw - 0.12, hw + 0.12, -hd - 0.12, -hd + 0.30),
                         (-hw - 0.12, -hw + 0.30, -hd, hd),
                         (hw - 0.30, hw + 0.12, -hd, hd)):
        mb.box_minmax(a, b, c, d, z1 + 0.36, z1 + 0.54)
    objs.append(mb.build("额枋_上层", mats.wood_beam, coll_wall, auto_smooth=30))

    mb = MB()
    zz = P.DG1_Z
    DG.row_x(mb, hd + 0.08, zz, -hw + 0.6, hw - 0.6, h=1.12, out=0.72, spacing=2.00)
    DG.row_x(mb, -hd - 0.08, zz, -hw + 0.6, hw - 0.6, h=1.12, out=0.72,
             spacing=2.00, rot_extra=math.pi)
    DG.row_y(mb, -hw - 0.08, zz, -hd + 0.6, hd - 0.6, h=1.12, out=0.72,
             spacing=2.00, rot_extra=math.pi / 2)
    DG.row_y(mb, hw + 0.08, zz, -hd + 0.6, hd - 0.6, h=1.12, out=0.72,
             spacing=2.00, rot_extra=-math.pi / 2)
    DG.bands(mb, hw + 0.08, hd + 0.08, zz,
             layers=((0.30, 0.18, 0.42), (0.76, 0.20, 0.56), (1.22, 0.21, 0.64)))
    # 转角铺作
    for sx in (-1, 1):
        for sy in (-1, 1):
            M = Matrix.Translation((sx * (hw + 0.08), sy * (hd + 0.08), zz)) @ \
                Euler((0, 0, math.atan2(sy, sx)), 'XYZ').to_matrix().to_4x4()
            DG._unit(mb, M, 1.12, 0.72)
    # 拱眼壁
    mb_pl = MB()
    DG.arch_panel(mb_pl, 'x', hd + 0.00, -hw, hw, zz, zz + 1.48)
    DG.arch_panel(mb_pl, 'x', -hd - 0.14, -hw, hw, zz, zz + 1.48)
    DG.arch_panel(mb_pl, 'y', -hw - 0.14, -hd, hd, zz, zz + 1.48)
    DG.arch_panel(mb_pl, 'y', hw + 0.00, -hd, hd, zz, zz + 1.48)
    objs.append(mb_pl.build("拱眼壁_上檐", mats.panel, coll_dg, auto_smooth=None))
    objs.append(mb.build("斗拱_上檐", mats.wood, coll_dg, auto_smooth=30))

    mb = MB()
    for (a, b, c, d) in ((-hw - 0.2, hw + 0.2, hd + 1.0, hd + 1.42),
                         (-hw - 0.2, hw + 0.2, -hd - 1.42, -hd - 1.0),
                         (-hw - 1.42, -hw - 1.0, -hd - 0.2, hd + 0.2),
                         (hw + 1.0, hw + 1.42, -hd - 0.2, hd + 0.2)):
        mb.box_minmax(a, b, c, d, zz + 1.46, zz + 1.74)
    objs.append(mb.build("撩檐枋_上檐", mats.wood_red, coll_dg, auto_smooth=30))
    return objs


# ------------------------------------------------------------------ 屋顶
def build_roofs(mats, c_roof, c_orn):
    objs = []
    S = R.RoofSpec(P.R_HW, P.R_HD, P.R_EAVE, P.R_RIDGE, P.R_LR, P.R_HG,
                   lift=0.58, lift_r=3.2, ridge_w=0.56, name="上檐",
                   tile_p=P.TILE_P, tile_amp=P.TILE_AMP)
    objs += R.build_xieshan(mats, S, "屋顶_上檐", c_roof)
    objs += R.build_zhengji(mats, S, "正脊_上檐", c_orn)
    for sg in (1, -1):
        objs.append(R.build_gable_ridges(mats, S, "垂脊戗脊_上檐", c_orn, sg))
    return objs, S


def baosha_spec():
    return R.RoofSpec(P.BR_HW, P.BR_HD, P.BR_EAVE, P.BR_RIDGE, P.BR_LR, P.BR_HG,
                      lift=0.55, lift_r=2.6, ridge_w=0.42, name="抱厦",
                      tile_p=P.TILE_P, tile_amp=P.TILE_AMP * 0.85)


def build_baosha_roof(mats, c_roof, c_orn, idx, S=None):
    """抱厦歇山：山花朝外（局部 +x 即外），只做外端山花与脊饰

    内端山花不建：它埋在殿身里，一旦从腰檐缺口露出来就是一块
    莫名其妙悬在屋面上的红三角（3/4 视角里能直接看到）。
    """
    S = S or baosha_spec()
    name = "屋顶_抱厦%d" % idx
    objs = R.build_xieshan(mats, S, name, c_roof, res_x=0.052, res_y=0.13,
                           gable_signs=(1,))
    objs += R.build_zhengji(mats, S, name + "_脊", c_orn, sg_ends=False)
    # 山花尖上的宝顶（照片里抱厦正脊端头是一枚小立饰，不是鸱吻）
    mb = MB()
    mb.cuboid((S.LR - 0.05, 0, S.Hr + 0.55), (0.30, 0.30, 0.22), top=(0.6, 0.6))
    mb.cuboid((S.LR - 0.05, 0, S.Hr + 0.76), (0.20, 0.20, 0.30), top=(0.35, 0.35))
    objs.append(mb.build(name + "_宝顶", mats.tile_dark, c_orn, auto_smooth=32))
    objs.append(R.build_gable_ridges(mats, S, name + "_垂脊", c_orn, 1))
    return objs


# ------------------------------------------------------------------ 围脊
def boolean_cut(target, cutters, op='DIFFERENCE'):
    """用 cutter 的**求值网格**（含 Solidify）对 target 做布尔差集并应用

    抱厦屋面是「开放曲面 + Solidify」，直接当布尔操作数会因为非流形而失败，
    所以先用 depsgraph 取一份已经加厚过的实体网格做临时 cutter。
    """
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    temps = []
    for c in cutters:
        try:
            me = bpy.data.meshes.new_from_object(c.evaluated_get(dg))
        except Exception as e:
            print("[bool] skip %s: %s" % (c.name, e))
            continue
        t = bpy.data.objects.new("_cut_" + c.name, me)
        bpy.context.scene.collection.objects.link(t)
        temps.append(t)
        m = target.modifiers.new("b_" + c.name, 'BOOLEAN')
        m.operation = op
        m.solver = 'EXACT'
        m.object = t
    for o in bpy.context.selected_objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = target
    target.select_set(True)
    for m in list(target.modifiers):
        if m.type != 'BOOLEAN':
            continue
        try:
            bpy.ops.object.modifier_apply(modifier=m.name)
        except Exception as e:
            print("[bool] apply fail %s: %s" % (m.name, e))
    target.select_set(False)
    for t in temps:
        bpy.data.objects.remove(t, do_unlink=True)
    print("[bool] %s trimmed by %d cutters" % (target.name, len(temps)))
    return target


def build_weiji(mats, c_orn):
    hw, hd = P.UP_W / 2, P.UP_D / 2
    return R.build_weiji(mats, None, hw, hd, P.SKIRT_TOP, c_orn)


# ------------------------------------------------------------------ 匾额
def build_plaque(mats, coll):
    """前抱厦檐下竖匾「摩尼殿」"""
    y0 = P.BODY_D / 2 + P.BS_OUT
    mb = MB()
    W, Hh, T = 1.30, 2.30, 0.14
    yb = y0 + 0.18
    z0p = P.PLAT_Z + P.BS_PORTAL_H + 0.50
    mb.box_minmax(-W / 2, W / 2, yb - T, yb, z0p, z0p + Hh)
    # 边框
    for dz0, dz1 in ((0.0, 0.11), (Hh - 0.11, Hh)):
        mb.box_minmax(-W / 2 - 0.08, W / 2 + 0.08, yb - T - 0.05, yb + 0.02,
                      z0p + dz0, z0p + dz1)
    for sx in (-1, 1):
        mb.box_minmax(sx * (W / 2 + 0.08) - 0.08 if sx > 0 else -W / 2 - 0.08,
                      sx * (W / 2 + 0.08) if sx > 0 else -W / 2 + 0.0,
                      yb - T - 0.05, yb + 0.02, z0p, z0p + Hh)
    # 吊挂
    for sx in (-0.36, 0.36):
        mb.box_minmax(sx - 0.045, sx + 0.045, yb - T - 0.03, yb - T + 0.08,
                      z0p + Hh, z0p + Hh + 0.34)
    ob = mb.build("匾额_框", mats.plaque, coll, auto_smooth=30)

    txt = None
    try:
        cu = bpy.data.curves.new("匾额文", 'FONT')
        fp = "C:/Windows/Fonts/msyhbd.ttc"
        if not os.path.exists(fp):
            fp = "C:/Windows/Fonts/simhei.ttf"
        cu.font = bpy.data.fonts.load(fp)
        cu.body = "摩\n尼\n殿"
        cu.size = 0.58
        cu.align_x = 'CENTER'
        cu.align_y = 'CENTER'
        cu.space_line = 0.92
        cu.extrude = 0.022
        cu.bevel_depth = 0.005
        t = bpy.data.objects.new("匾额文", cu)
        coll.objects.link(t)
        t.location = (0, yb + 0.045, z0p + Hh / 2)
        t.rotation_euler = Euler((math.radians(90), 0, 0), 'XYZ')
        bpy.context.view_layer.objects.active = t
        for o in bpy.context.selected_objects:
            o.select_set(False)
        t.select_set(True)
        bpy.ops.object.convert(target='MESH')
        txt = bpy.context.view_layer.objects.active
        txt.scale.x = -1.0
        txt.data.materials.append(mats.gold)
        txt.select_set(False)
    except Exception as e:
        print("[plaque]", e)
    return [ob] + ([txt] if txt else [])


# ------------------------------------------------------------------ 环境
def build_env(mats, coll):
    """庭院：月台 + 甬道 + 大面铺地

    参考照片里殿前是整片石板地与一条中轴甬道，没有水池与石桥，
    早先按"园林"做的水池是错的，这里改成寺院的规整铺装。
    """
    mb = MB()
    mb.box_minmax(-100, 100, -100, 100, -0.30, 0.0)
    objs = [mb.build("地面", mats.ground, coll, auto_smooth=None)]
    # 月台：与台基等高的一段平台，向三面各出一个台阶
    mb = MB()
    mb.box_minmax(-19.5, 19.5, -16.5, P.PLAT_D / 2 + 4.0, 0.0, 0.26)
    objs.append(mb.build("月台", mats.stone, coll, auto_smooth=30))
    # 中轴甬道
    mb = MB()
    mb.box_minmax(-3.8, 3.8, P.PLAT_D / 2 + 4.0, 52, 0.0, 0.30)
    objs.append(mb.build("甬道", mats.stone, coll, auto_smooth=30))
    # 甬道边沿石
    mb = MB()
    for sx in (-1, 1):
        mb.box_minmax(sx * 3.8, sx * 4.1, P.PLAT_D / 2 + 4.0, 52, 0.0, 0.36)
    objs.append(mb.build("甬道_边石", mats.stone, coll, auto_smooth=30))
    return objs


# ------------------------------------------------------------------ 场景
def setup_world_and_cam():
    sc = bpy.context.scene
    w = bpy.data.worlds.new("天光")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputWorld')
    # 渐变天空：相机所见
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = -0.05
    mr.inputs['From Max'].default_value = 0.75
    ramp.color_ramp.elements[0].position = 0.02
    ramp.color_ramp.elements[0].color = (0.90, 0.92, 0.95, 1)
    ramp.color_ramp.elements[1].position = 0.75
    ramp.color_ramp.elements[1].color = (0.30, 0.50, 0.76, 1)
    bg_cam = nt.nodes.new('ShaderNodeBackground')
    bg_cam.inputs['Strength'].default_value = 1.0
    nt.links.new(tc.outputs['Generated'], sep.inputs['Vector'])
    nt.links.new(sep.outputs['Z'], mr.inputs['Value'])
    nt.links.new(mr.outputs['Result'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bg_cam.inputs['Color'])
    # 环境光（照明用）
    bg_lit = nt.nodes.new('ShaderNodeBackground')
    bg_lit.inputs['Color'].default_value = (0.46, 0.55, 0.68, 1)
    bg_lit.inputs['Strength'].default_value = 0.95
    mix = nt.nodes.new('ShaderNodeMixShader')
    lp = nt.nodes.new('ShaderNodeLightPath')
    nt.links.new(lp.outputs['Is Camera Ray'], mix.inputs['Fac'])
    nt.links.new(bg_lit.outputs['Background'], mix.inputs[1])
    nt.links.new(bg_cam.outputs['Background'], mix.inputs[2])
    nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])

    sun_d = bpy.data.lights.new("日光", 'SUN')
    sun_d.energy = 4.2
    sun_d.angle = math.radians(1.6)
    sun_d.color = (1.0, 0.955, 0.88)
    sun = bpy.data.objects.new("日光", sun_d)
    sc.collection.objects.link(sun)
    sun.rotation_euler = Euler((math.radians(62), 0, math.radians(152)), 'XYZ')
    # 抱厦补光：门扇一组 + 匾额/檐下一组（模拟地面反光，避免檐下死黑）
    hw_, hd_ = P.BODY_W / 2, P.BODY_D / 2
    porches = [((0, 1), (0, hd_)), ((0, -1), (0, -hd_)),
               ((1, 0), (hw_, 0)), ((-1, 0), (-hw_, 0))]
    for i, ((nx, ny), (px, py)) in enumerate(porches):
        for j, (dd, zl, zt, en, sz) in enumerate((
                (8.6, 4.2, 3.4, 200, 4.0),
                (11.2, 7.6, 9.0, 190, 5.0))):
            loc = (px + nx * dd, py + ny * dd, zl)
            tgt = (px + nx * 5.2, py + ny * 5.2, zt)
            ld = bpy.data.lights.new("抱厦补光%d_%d" % (i, j), 'AREA')
            ld.energy = en
            ld.size = sz
            ld.color = (1.0, 0.93, 0.86)
            lo = bpy.data.objects.new("抱厦补光%d_%d" % (i, j), ld)
            sc.collection.objects.link(lo)
            lo.location = loc
            d = Vector(tgt) - Vector(loc)
            lo.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def add_camera(loc, look, lens=50, name="相机"):
    cam_d = bpy.data.cameras.new(name)
    cam_d.lens = lens
    cam = bpy.data.objects.new(name, cam_d)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = loc
    d = Vector(look) - Vector(loc)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return cam


def main():
    clear_scene()
    mats = MM.Mats()
    root = ensure_coll("摩尼殿")
    c_tai = ensure_coll("01_台基", root)
    c_low = ensure_coll("02_下层墙身", root)
    c_dg = ensure_coll("03_斗拱", root)
    c_skirt = ensure_coll("04_下檐", root)
    c_up = ensure_coll("05_上层墙身", root)
    c_roof = ensure_coll("06_屋面", root)
    c_bs = ensure_coll("07_抱厦", root)
    c_orn = ensure_coll("08_脊饰", root)
    c_env = ensure_coll("09_环境", root)

    print("[1/6] 台基")
    build_podium(mats, c_tai)
    print("[2/6] 下层")
    build_lower(mats, c_low, c_dg, c_low)
    print("[3/6] 抱厦")
    S_bs = baosha_spec()
    unit = build_baosha_unit(mats, c_bs, c_dg)
    roofs = build_baosha_roof(mats, c_roof, c_orn, 0, S=S_bs)
    allb = [(o, o.users_collection[0]) for o in unit + roofs]
    hw, hd = P.BODY_W / 2, P.BODY_D / 2
    places = [((0, hd, 0), math.pi / 2), ((hw, 0, 0), 0.0),
              ((0, -hd, 0), -math.pi / 2), ((-hw, 0, 0), math.pi)]
    roof_i = len(unit)
    porch_roofs = []
    for k, (loc, ang) in enumerate(places):
        for oi, (ob, coll) in enumerate(allb):
            tgt = ob
            if k > 0:
                tgt = ob.copy()
                tgt.data = ob.data
                tgt.name = ob.name + "_%d" % k
                coll.objects.link(tgt)
            tgt.location = loc
            tgt.rotation_euler = Euler((0, 0, ang), 'XYZ')
            if oi == roof_i:
                porch_roofs.append(tgt)
    print("[4/6] 上檐")
    build_upper(mats, c_up, c_dg)
    print("[5/6] 屋面")
    build_roofs(mats, c_roof, c_orn)
    build_weiji(mats, c_orn)

    # 下檐：极坐标闭合环，再用四座抱厦屋面做布尔差集。
    # 矩形缺口切不出抱厦屋面的曲面边界，会在两者之间留一块红三角；
    # 布尔差集让腰檐的断口正好落在抱厦屋面上，交界就是一条天沟。
    sk_hw = P.BODY_W / 2 + P.EAVE0_OV
    sk_hd = P.BODY_D / 2 + P.EAVE0_OV
    sk = SK.build_skirt(mats, sk_hw, sk_hd, P.UP_W / 2, P.UP_D / 2,
                        P.EAVE0_Z, P.SKIRT_TOP, "屋顶_下檐", c_skirt,
                        nth=704, nt=36, lift=0.62, lift_r=4.6,
                        tile_p=P.TILE_P, tile_amp=P.TILE_AMP)
    boolean_cut(sk, porch_roofs)

    # 内腔（避免透过门洞看到透空）
    mb = MB()
    mb.box_minmax(-P.UP_W / 2 + 0.7, P.UP_W / 2 - 0.7, -P.UP_D / 2 + 0.7,
                  P.UP_D / 2 - 0.7, P.PLAT_Z, P.UP_Z0 - 0.1)
    mb2 = MB()
    mb2.box_minmax(-P.BODY_W / 2 + 1.6, P.BODY_W / 2 - 1.6,
                   -P.BODY_D / 2 + 1.6, P.BODY_D / 2 - 1.6, P.PLAT_Z,
                   P.WALL_Z1 - 0.1)
    inner = mb2.build("室内暗腔", MM.plain("室内", (0.030, 0.024, 0.020), rough=0.9,
                              emit=((0.011, 0.0075, 0.005), 1.0)),
                      c_low, auto_smooth=None)
    print("[6/6] 环境")
    build_env(mats, c_env)

    setup_world_and_cam()
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x = 1400
    sc.render.resolution_y = 900
    sc.eevee.taa_render_samples = 48
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.exposure = 0.55
    sc.view_settings.look = 'AgX - Medium High Contrast'
    cam = add_camera((0.0, 96.0, 7.0), (0, 0, 10.5), lens=80)
    sc.camera = cam
    out = os.path.join(HERE, "..", "renders")
    os.makedirs(out, exist_ok=True)
    sc.render.filepath = os.path.join(out, "front.png")
    print("BUILD_OK objects=%d" % len(bpy.data.objects))
    return sc


if __name__ == "__main__":
    import time
    t0 = time.time()
    main()
    root = os.path.join(HERE, "..")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(os.path.join(root, "隆兴寺摩尼殿.blend")))
    print("SAVED %.1fs" % (time.time() - t0))
