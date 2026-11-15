# -*- coding: utf-8 -*-
"""墙体、门窗、柱额、台基"""
import math
from mathutils import Vector
from blib import MB, lerp

TAU = math.pi * 2


def wall_face(mb, axis, face_pos, t, a0, a1, z0, z1, openings=()):
    """带洞口的墙板。axis='x' → 墙面法向为 y；a0,a1 为沿墙走向范围。"""
    ops = sorted(openings, key=lambda o: o[0])
    segs = []
    cur = a0
    for (oc, ow, oz0, oz1) in ops:
        lo, hi = oc - ow / 2, oc + ow / 2
        if lo > cur:
            segs.append((cur, lo, z0, z1))
        segs.append((lo, hi, z0, oz0))
        segs.append((lo, hi, oz1, z1))
        cur = hi
    if cur < a1:
        segs.append((cur, a1, z0, z1))
    for (s0, s1, sz0, sz1) in segs:
        if s1 - s0 < 1e-3 or sz1 - sz0 < 1e-3:
            continue
        if axis == 'x':
            mb.box_minmax(s0, s1, face_pos, face_pos + t, sz0, sz1)
        else:
            mb.box_minmax(face_pos, face_pos + t, s0, s1, sz0, sz1)


def column(mb, x, y, z0, z1, r=0.27, stone=True, mb_stone=None):
    prof = [(r * 1.06, 0.0), (r * 1.06, 0.06), (r, 0.10), (r * 0.94, (z1 - z0) * 0.75),
            (r * 0.90, z1 - z0)]
    mb.revolve(prof, center=(x, y, z0), seg=14, smooth=True)
    if stone and mb_stone is not None:
        mb_stone.revolve([(r * 1.5, 0), (r * 1.5, 0.08), (r * 1.35, 0.16),
                          (r * 1.12, 0.24), (r * 1.12, 0.30)],
                         center=(x, y, z0 - 0.30), seg=14, smooth=True)


def lintel(mb, axis, face_pos, a0, a1, z, h=0.34, d=0.26):
    if axis == 'x':
        mb.box_minmax(a0, a1, face_pos, face_pos + d, z, z + h)
    else:
        mb.box_minmax(face_pos, face_pos + d, a0, a1, z, z + h)


def _box(mb, axis, u0, u1, n0, n1, z0, z1):
    """按「宽度方向 u / 法向 n」落一个箱体；n 自动排序，允许 out 为负向。"""
    if mb is None:
        return
    n0, n1 = (n0, n1) if n0 <= n1 else (n1, n0)
    if axis == 'y':
        mb.box_minmax(u0, u1, n0, n1, z0, z1)
    else:
        mb.box_minmax(n0, n1, u0, u1, z0, z1)


def door_leaf(mb, cx, zb, w, h, face, out=1.0, t=0.10, studs=5, mb2=None,
              axis='y'):
    """板门一扇：门板 + 竖缝 + 横串 + 门钉 + 铺首
    face 为门扇**外表面**沿法向的坐标，out 为外法向符号；
    门板向 -out 方向取厚 t，门钉/铺首一律贴在外表面（旧版按 tdir 偏移，
    外法向为负时五金会埋进门板里，从外面看门就是一块光板）。
    axis='y' 法向沿 y（宽度沿 x）；axis='x' 法向沿 x（宽度沿 y）
    """
    u0, u1 = cx - w / 2, cx + w / 2
    n_in = face - t * out
    # 门板
    _box(mb, axis, u0, u1, n_in, face, zb, zb + h)
    # 竖向拼板（凸出板面 0.014）
    n = max(3, int(w / 0.34))
    for i in range(1, n):
        u = lerp(u0, u1, i / n)
        _box(mb, axis, u - 0.014, u + 0.014, n_in, face + 0.014 * out,
             zb + 0.05, zb + h - 0.05)
    # 上下横串（凸出 0.022）
    for zz in (zb + h * 0.22, zb + h * 0.78):
        _box(mb, axis, u0, u1, n_in, face + 0.022 * out, zz - 0.07, zz + 0.07)
    # 门钉（圆钉贴外表面，凸出 0.028）；铺首位置留空
    nd = 0.030
    d = Vector((0.0, out, 0.0)) if axis == 'y' else Vector((out, 0.0, 0.0))
    tgt = mb2 if mb2 is not None else mb
    cu = cx + w * 0.30
    pz0 = zb + h * 0.52
    for i in range(studs):
        for j in range(studs):
            pu = lerp(u0 + w * 0.15, u1 - w * 0.15, i / (studs - 1.0))
            pz = lerp(zb + h * 0.13, zb + h * 0.88, j / (studs - 1.0))
            if abs(pu - cu) < 0.17 and abs(pz - pz0) < 0.17:
                continue
            c = Vector((pu, face - 0.006 * out, pz)) if axis == 'y' \
                else Vector((face - 0.006 * out, pu, pz))
            tgt.cyl_dir(c, nd, 0.034, d, seg=9)
    # 铺首（门环底座），沿外法向叠两级
    if mb2 is not None:
        c = Vector((cu, face, pz0)) if axis == 'y' else Vector((face, cu, pz0))
        mb2.cyl_dir(c, 0.092, 0.022, d, seg=16)
        mb2.cyl_dir(c + d * 0.020, 0.054, 0.030, d, seg=16)


def portal(mb_f, mb_l, mb_m, mb_s, axis, face, uc, w, hh, zb, out=1.0,
           door=True, studs=5, jamb=0.36, head=0.26, sill=0.22,
           leaf_t=0.10, n_in=0.20, n_out=0.055):
    """门洞总成：门框 + 上槛 + 门槛 +（可选）板门两扇。

    有门 / 无门共用同一套洞口尺寸与框料，区别只在于是否填门扇：
      door=True  → 两扇板门严丝合缝填满净空，五金贴在外表面
      door=False → 净空敞开，仅余门框、上槛、门槛，形成可穿行的门道

    mb_f 门框(木) / mb_l 门扇(板门) / mb_m 铺首(金) / mb_s 门槛(石)，
    不需要的传 None。axis、out 同 door_leaf；face 为墙外皮沿法向的坐标；
    w、hh 为墙体开洞的宽与高，zb 为洞口底；jamb 为立颊向洞内的吃入量。
    返回净空宽（供调用方核对）。
    """
    u_lo, u_hi = uc - w / 2, uc + w / 2
    zt = zb + hh
    nf, nb = face + n_out * out, face - n_in * out
    # 立颊（两端各向墙内咬 0.04，避免与洞口侧壁共面闪烁）
    _box(mb_f, axis, u_lo - 0.04, u_lo + jamb, nf, nb, zb, zt)
    _box(mb_f, axis, u_hi - jamb, u_hi + 0.04, nf, nb, zb, zt)
    # 上槛（向洞口上方咬 0.04）
    _box(mb_f, axis, u_lo - 0.04, u_hi + 0.04, nf, nb, zt - head, zt + 0.04)
    # 门槛（缩 0.01 避开与立颊共面）
    cw = w - 2 * jamb
    _box(mb_s, axis, uc - cw / 2 + 0.01, uc + cw / 2 - 0.01,
         face + 0.025 * out, face - 0.34 * out, zb, zb + sill)
    # 板门：净空 = cw × (hh - head - sill)，门扇居中、两侧与中缝各留 18~36 mm
    if door:
        z0d, z1d = zb + sill - 0.012, zt - head     # 下缘咬进门槛 12 mm，避免共面
        gap = 0.018
        lw = (cw - 2 * gap - 2 * gap) / 2
        for s in (-1, 1):
            cx = uc + s * (cw / 2 - gap - lw / 2)
            door_leaf(mb_l, cx, z0d, lw, z1d - z0d, face, out=out,
                      t=leaf_t, studs=studs, mb2=mb_m, axis=axis)
    return cw


def lattice_window(mb, mb2, axis, face_pos, a0, a1, z0, z1, tdir=1.0,
                   bar=0.045, gap=0.135, frame=0.10):
    """直棂窗：外框 + 密集竖棂"""
    # 框
    if axis == 'x':
        mb.box_minmax(a0, a1, face_pos - 0.02, face_pos + 0.14 * tdir, z0, z0 + frame)
        mb.box_minmax(a0, a1, face_pos - 0.02, face_pos + 0.14 * tdir, z1 - frame, z1)
        mb.box_minmax(a0, a0 + frame, face_pos - 0.02, face_pos + 0.14 * tdir, z0, z1)
        mb.box_minmax(a1 - frame, a1, face_pos - 0.02, face_pos + 0.14 * tdir, z0, z1)
        n = max(2, int((a1 - a0 - 2 * frame) / gap))
        for i in range(n + 1):
            x = lerp(a0 + frame, a1 - frame, i / n)
            mb.box_minmax(x - bar / 2, x + bar / 2, face_pos,
                          face_pos + 0.10 * tdir, z0 + frame, z1 - frame)
        # 窗内暗板
        mb2.box_minmax(a0 + frame * 0.5, a1 - frame * 0.5,
                       face_pos - 0.16, face_pos - 0.10, z0 + frame, z1 - frame)
    else:
        mb.box_minmax(face_pos - 0.02, face_pos + 0.14 * tdir, a0, a1, z0, z0 + frame)
        mb.box_minmax(face_pos - 0.02, face_pos + 0.14 * tdir, a0, a1, z1 - frame, z1)
        mb.box_minmax(face_pos - 0.02, face_pos + 0.14 * tdir, a0, a0 + frame, z0, z1)
        mb.box_minmax(face_pos - 0.02, face_pos + 0.14 * tdir, a1 - frame, a1, z0, z1)
        n = max(2, int((a1 - a0 - 2 * frame) / gap))
        for i in range(n + 1):
            y = lerp(a0 + frame, a1 - frame, i / n)
            mb.box_minmax(face_pos, face_pos + 0.10 * tdir, y - bar / 2, y + bar / 2,
                          z0 + frame, z1 - frame)
        mb2.box_minmax(face_pos - 0.16, face_pos - 0.10, a0 + frame * 0.5,
                       a1 - frame * 0.5, z0 + frame, z1 - frame)
