# -*- coding: utf-8 -*-
"""
Horyu-ji five-storey pagoda (法隆寺五重塔) — procedural build for Blender 5.x
Run:  blender -b --python build_pagoda.py
"""
import bpy, math, os, sys
from mathutils import Vector, Matrix

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import pagoda_lib as PL
from pagoda_lib import MB, mx, RAD, PI, build_materials

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------------------------------- #
#  Global proportions (metres)
# --------------------------------------------------------------------------- #
PLAT_TOP = 1.15
PLAT_HALF = 7.40

H_WALL = [2.75, 1.38, 1.30, 1.22, 1.15]
BR_H = [1.22, 1.15, 1.10, 1.05, 1.00]
B = [4.55, 4.15, 3.88, 3.62, 3.38]          # wall plane half width
W = [8.85, 7.95, 7.30, 6.65, 6.00]          # eave half width
SLOPE = 0.52
LIFT_K = 0.10

F, E, T = [], [], []
_lvl = PLAT_TOP
for i in range(5):
    F.append(_lvl)
    e = _lvl + H_WALL[i] + BR_H[i]
    t = e + (W[i] - B[i]) * SLOPE
    E.append(e)
    T.append(t)
    _lvl = t


def roof_z(x, y, i):
    """Height of roof surface for storey i at plan position (x,y)."""
    wi = W[i]
    win = B[i] - 0.26
    r = max(abs(x), abs(y))
    if r <= win:
        return T[i]
    k = (r - win) / (wi - win)
    z = T[i] - (T[i] - E[i]) * (k ** 0.75)
    if r > 1e-6:
        c = (min(abs(x), abs(y)) / r) ** 8.0
        z += LIFT_K * (wi - B[i]) * (k ** 3.0) * c
    return z


def rot_to(vec):
    z = Vector(vec).normalized()
    up = Vector((0, 0, 1)) if abs(z.z) < 0.95 else Vector((0, 1, 0))
    x = up.cross(z).normalized()
    y = z.cross(x)
    M = Matrix(((x.x, y.x, z.x, 0), (x.y, y.y, z.y, 0), (x.z, y.z, z.z, 0),
                (0, 0, 0, 1)))
    return M


def lin(a, b, n):
    return [a + (b - a) * i / (n - 1) for i in range(n)]


COLL = {}


def coll(name):
    if name not in COLL:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
        COLL[name] = c
    return COLL[name]


# --------------------------------------------------------------------------- #
#  Sub-assemblies
# --------------------------------------------------------------------------- #
def railing(mb, hw, z0, h=1.05, post_r=0.062, rails=True, mat="wood_red",
            mat_post="wood_red"):
    """High railing (koran) around a square of half width hw."""
    n = max(4, int(round(2 * hw / 1.05)))
    xs = lin(-hw, hw, n + 1)
    for s in range(4):
        M = mx(rz=s * PI / 2)
        for x in xs:
            corner = abs(abs(x) - hw) < 1e-4
            ph = h * (1.12 if corner else 1.0)
            mb.box(M, post_r * 2, post_r * 2, ph, mat_post, x, hw, z0 + ph / 2)
            if corner:
                mb.sphere(M, post_r * 1.9, "gold", 12, 6, cz=z0 + ph + post_r * 1.5)
        # rails
        for zz, th, ww in ((h + 0.02, 0.10, 0.15), (h * 0.55, 0.075, 0.11),
                           (0.06, 0.06, 0.10)):
            mb.box(M, 2 * hw + 0.10, ww, th, mat, 0, hw, z0 + zz)
        # balusters
        if rails:
            bn = int(2 * hw / 0.30)
            for k in range(1, bn):
                x = -hw + 2 * hw * k / bn
                if min(abs(x - v) for v in xs) < 0.09:
                    continue
                mb.box(M, 0.045, 0.045, h * 0.38, mat, x, hw, z0 + h * 0.55 + h * 0.19)


def bracket_set(mb, M, s=1.0, hz=None):
    """Cloud bracket cluster (kumimono). Local: origin at column head, +Y out."""
    hz = 1.30 * s if hz is None else hz
    def f(v):
        return v * hz / 1.30
    # big block (daito)
    mb.box(M, 0.60 * s, 0.60 * s, f(0.26), "wood_red", 0, 0.10 * s, f(0.13))
    # first tier arms
    mb.box(M, 1.95 * s, 0.26 * s, f(0.20), "wood_red", 0, 0.12 * s, f(0.36))
    mb.box(M, 0.26 * s, 0.95 * s, f(0.20), "wood_red", 0, 0.45 * s, f(0.36))
    # small blocks
    for xx, yy in ((-0.86, 0.12), (0.86, 0.12), (0.0, 0.86)):
        mb.box(M, 0.34 * s, 0.34 * s, f(0.20), "wood_dark",
               xx * s, yy * s, f(0.56))
    # second tier arms
    mb.box(M, 2.45 * s, 0.24 * s, f(0.18), "wood_red", 0, 0.16 * s, f(0.75))
    mb.box(M, 0.24 * s, 1.45 * s, f(0.18), "wood_red", 0, 0.62 * s, f(0.75))
    for xx, yy in ((-1.05, 0.16), (1.05, 0.16), (0.0, 1.20)):
        mb.box(M, 0.30 * s, 0.30 * s, f(0.18), "wood_dark",
               xx * s, yy * s, f(0.93))
    # tail rafter (odaruki)
    mb.swept([(0, 0.30 * s, f(0.30)), (0, 1.05 * s, f(0.62)),
              (0, 1.95 * s, f(0.92))], 0.20 * s, 0.20 * s, "wood_beam",
             side_axis=(1, 0, 0))


def body_side(mb, M, i, b, z0, hw):
    """One facade of a storey in local coordinates (+Y outward)."""
    top = z0 + hw
    # main wall slab
    mb.box(M, 2 * b, 0.24, hw, "plaster", 0, b - 0.12, z0 + hw / 2)
    # sill / lintel beams
    mb.box(M, 2 * b + 0.06, 0.34, 0.20, "wood_beam", 0, b - 0.02, z0 + 0.10)
    mb.box(M, 2 * b + 0.06, 0.36, 0.26, "wood_beam", 0, b - 0.02, top - 0.16)
    # columns
    cols = [-b, -0.33 * b, 0.33 * b, b]
    for x in cols:
        mb.cyl(M, 0.205, hw, "wood_dark", 14, x, b - 0.04, z0)
        mb.cyl(M, 0.25, 0.10, "wood_beam", 14, x, b - 0.04, z0)
    bays = [(-b, -0.33 * b), (-0.33 * b, 0.33 * b), (0.33 * b, b)]
    for bi, (x0, x1) in enumerate(bays):
        wdt = x1 - x0 - 0.30
        cx = (x0 + x1) / 2
        if i == 0:
            if bi == 1:      # doors
                zb, zt = z0 + 0.18, z0 + 1.98
                mb.box(M, wdt + 0.16, 0.10, 0.16, "wood_beam", cx, b + 0.04, zt)
                mb.box(M, wdt + 0.16, 0.10, 0.16, "wood_beam", cx, b + 0.04, zb - 0.08)
                for dx in (-wdt / 4, wdt / 4):
                    mb.box(M, wdt / 2 - 0.02, 0.11, zt - zb, "wood_dark",
                           cx + dx, b + 0.02, (zb + zt) / 2)
                    for k in range(4):
                        zz = zb + 0.22 + k * (zt - zb - 0.35) / 3
                        mb.box(M, wdt / 2 - 0.06, 0.05, 0.09, "wood_beam",
                               cx + dx, b + 0.085, zz)
                    mb.box(M, 0.05, 0.05, zt - zb - 0.1, "wood_beam",
                           cx + dx, b + 0.085, (zb + zt) / 2)
            else:            # slat window
                zb, zt = z0 + 1.02, z0 + 1.90
                mb.box(M, wdt, 0.06, zt - zb, "wood_dark", cx, b - 0.06,
                       (zb + zt) / 2)
                nb = int(wdt / 0.135)
                for k in range(nb):
                    xx = cx - wdt / 2 + wdt * (k + 0.5) / nb
                    mb.box(M, 0.062, 0.09, zt - zb, "wood_beam", xx, b + 0.02,
                           (zb + zt) / 2)
                mb.box(M, wdt + 0.10, 0.12, 0.10, "wood_beam", cx, b + 0.03, zt)
                mb.box(M, wdt + 0.10, 0.12, 0.10, "wood_beam", cx, b + 0.03, zb)
        else:
            if bi == 1:      # narrow door
                zb, zt = z0 + 0.14, z0 + 0.86
                mb.box(M, wdt * 0.62, 0.09, zt - zb, "wood_dark", cx, b + 0.02,
                       (zb + zt) / 2)
                mb.box(M, wdt * 0.62 + 0.12, 0.11, 0.09, "wood_beam", cx, b + 0.04, zt)
                for k in range(3):
                    mb.box(M, wdt * 0.58, 0.04, 0.05, "wood_beam", cx, b + 0.075,
                           zb + 0.18 + k * 0.24)
    # long horizontal mouldings (nageshi)
    for zz in (z0 + 0.30, top - 0.52):
        mb.box(M, 2 * b + 0.02, 0.06, 0.09, "wood_beam", 0, b + 0.10, zz)


def build_storey(i):
    b = B[i]
    z0, hw = F[i], H_WALL[i]
    mb = MB(["plaster"])
    for s in range(4):
        M = mx(rz=s * PI / 2)
        body_side(mb, M, i, b, z0, hw)
        # spandrel band behind the brackets
        hband = roof_z(b - 0.26, 1.0, i) - (z0 + hw) - 0.06
        mb.box(M, 2 * b - 0.5, 0.26, hband, "wood_shadow", 0, b - 0.26,
               z0 + hw + hband / 2)
        # continuous bracket beams
        for zz, ww, hh in ((0.36, 0.24, 0.20), (0.75, 0.22, 0.18)):
            zz2 = z0 + hw + BR_H[i] * zz / 1.30
            mb.box(M, 2 * b + 0.32, ww, hh, "wood_red", 0, b + 0.16, zz2)
    # bracket clusters
    cols = [-b, -0.33 * b, 0.33 * b, b]
    mids = [-0.665 * b, 0.0, 0.665 * b]
    s = (b / 4.55) ** 0.92
    for side in range(4):
        M = mx(rz=side * PI / 2)
        for x in cols + mids:
            Ms = M @ Matrix.Translation((x, b - 0.06, z0 + hw))
            bracket_set(mb, Ms, s, BR_H[i])
    ob = mb.build("塔身_%d重" % (i + 1), coll("02_塔身"))
    return ob


def build_roof(i):
    N = 60
    wi, win = W[i], B[i] - 0.02
    verts, faces, uvs = [], [], []
    for a in range(N + 1):
        x = -wi + 2 * wi * a / N
        for c in range(N + 1):
            y = -wi + 2 * wi * c / N
            verts.append((x, y, roof_z(x, y, i)))
    for a in range(N):
        for c in range(N):
            i0 = a * (N + 1) + c
            faces.append((i0, i0 + N + 1, i0 + N + 2, i0 + 1))
            # per-face uv (tiles run down each slope)
            uvl = []
            for (va, vc) in ((a, c), (a, c + 1), (a + 1, c + 1), (a + 1, c)):
                xx = -wi + 2 * wi * va / N
                yy = -wi + 2 * wi * vc / N
                uvl.append((xx if abs(yy) >= abs(xx) else yy,
                            max(abs(xx), abs(yy)) - win))
            uvs.append(tuple(uvl))
    me = bpy.data.meshes.new("屋根_%d" % (i + 1))
    me.from_pydata(verts, [], faces)
    uvl = me.uv_layers.new(name="UVMap")
    k = 0
    for f in range(len(faces)):
        for j in range(4):
            uvl.data[k + j].uv = uvs[f][j]
        k += 4
    me.materials.append(bpy.data.materials["tile"])
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    me.update()
    ob = bpy.data.objects.new("屋根_%d" % (i + 1), me)
    coll("03_屋根").objects.link(ob)
    sol = ob.modifiers.new("thick", 'SOLIDIFY')
    sol.thickness = 0.44
    sol.offset = -1.0

    # ---- extra roof details ------------------------------------------------
    mb = MB(["tile"])
    # hip ridges + eave tiles + rafters
    for s in range(4):
        M = mx(rz=s * PI / 2)
        # hip ridge along the diagonal
        pts = []
        n = 14
        for k2 in range(n):
            t = k2 / (n - 1)
            rr = win + (wi - win) * t
            pts.append((rr, rr, roof_z(rr, rr, i) + 0.10))
        hip_prof = [(-0.5, -0.6), (0.5, -0.6), (0.5, -0.1), (0.42, 0.25),
                    (0.2, 0.45), (0.0, 0.5), (-0.2, 0.45), (-0.42, 0.25),
                    (-0.5, -0.1)]
        mb.swept(pts, 0.46, 0.34, "tile", side_axis=(-1, 1, 0), profile=hip_prof)
        mb.swept([(p[0], p[1], p[2] + 0.20) for p in pts], 0.30, 0.20,
                 "tile", side_axis=(-1, 1, 0), profile=hip_prof)
        # onigawara at the corner
        M2 = M @ Matrix.Translation((wi * 0.975, wi * 0.975,
                                     roof_z(wi, wi, i) + 0.02))
        M2 = M2 @ Matrix.Rotation(-PI / 4, 4, 'Z')
        mb.box(M2, 0.58, 0.22, 0.40, "tile", 0, 0, 0)
        mb.box(M2, 0.30, 0.26, 0.46, "tile", 0, 0, 0.02)
        # wind bell
        cz = roof_z(wi, wi, i) - 0.05
        p = M @ Vector((wi * 0.95, wi * 0.95, 0))
        mb.cyl(Matrix.Translation((p.x, p.y, cz)), 0.018, -0.55, "gold", 6,
               0, 0, 0)
        mb.sphere(Matrix.Translation((p.x, p.y, cz - 0.60)), 0.11, "bronze", 10, 6)
        # ---- tile ridge rows (hongawara) -----------------------------
        pitch_r = 0.335
        ncol = int(2 * (wi * 0.945) / pitch_r)
        prof = [(-0.5, -0.5), (0.5, -0.5), (0.5, -0.15), (0.36, 0.28),
                (0.0, 0.5), (-0.36, 0.28), (-0.5, -0.15)]
        for k2 in range(ncol + 1):
            u = -wi * 0.945 + 2 * wi * 0.945 * k2 / ncol
            pts = []
            for y in lin(win + 0.03, wi, 8):
                pts.append((u, y, roof_z(u, y, i) + 0.035))
            pts = [(M @ Vector(q))[:] for q in pts]
            mb.swept(pts, 0.155, 0.115, "tile", side_axis=(1, 0, 0),
                     profile=prof)
        # eave round tiles
        pitch = 0.285
        cnt = int(2 * (wi - 0.20) / pitch)
        for k2 in range(cnt + 1):
            x = -(wi - 0.20) + k2 * (2 * (wi - 0.20)) / cnt
            z = roof_z(x, wi, i)
            Me = M @ Matrix.Translation((x, wi - 0.02, z - 0.10))
            Me = Me @ rot_to((0, 1, 0.22))
            mb.cyl(Me, 0.115, 0.20, "tile", 8, 0, 0, -0.10)
        # rafters
        nraf = int(2 * (wi * 0.95) / 0.44)
        for k2 in range(nraf + 1):
            x = -wi * 0.95 + 2 * wi * 0.95 * k2 / nraf
            pts = []
            ys = lin(win * 0.30, wi - 0.03, 9)
            for y in ys:
                pts.append((x, y, roof_z(x, y, i) - 0.30))
            mb.swept(pts, 0.155, 0.17, "wood_dark", side_axis=(1, 0, 0))
    ob2 = mb.build("屋根詳細_%d" % (i + 1), coll("03_屋根"))
    return ob, ob2


def build_veranda():
    mb = MB(["wood_light"])
    b = B[0]
    hw = b + 1.42
    z = F[0]
    for s in range(4):
        M = mx(rz=s * PI / 2)
        mb.box(M, 2 * hw, 1.62, 0.16, "wood_light", 0, hw - 0.81, z - 0.08)
        mb.box(M, 2 * hw + 0.06, 0.10, 0.20, "wood_beam", 0, hw, z - 0.18)
        # plank joints
        n = int(2 * hw / 0.34)
        for k in range(1, n):
            x = -hw + 2 * hw * k / n
            mb.box(M, 0.014, 1.55, 0.012, "wood_dark", x, hw - 0.80, z + 0.005)
    railing(mb, hw - 0.06, z, 1.02, mat="wood_red")
    # stone plinths under the veranda posts
    for s in range(4):
        M = mx(rz=s * PI / 2)
        for x in (-b, -0.33 * b, 0.33 * b, b):
            mb.cyl(M, 0.30, 0.10, "stone_step", 12, x, b - 0.04, z - 0.02)
    mb.build("縁", coll("02_塔身"))


def build_balcony(i):
    mb = MB(["wood_light"])
    b = B[i]
    hw = b + 0.45
    z = F[i]
    for s in range(4):
        M = mx(rz=s * PI / 2)
        mb.box(M, 2 * hw, 0.62, 0.13, "wood_light", 0, hw - 0.31, z - 0.07)
    railing(mb, hw - 0.05, z, 0.88, mat="wood_red")
    mb.build("廻縁_%d" % (i + 1), coll("02_塔身"))


def build_sorin():
    mb = MB(["bronze"])
    z = T[4]
    # --- roban (square plinth) --------------------------------------------
    mb.box(mx(), 2.86, 2.86, 0.12, "bronze", 0, 0, z + 0.06)
    mb.box(mx(), 2.46, 2.46, 0.40, "bronze", 0, 0, z + 0.32)
    mb.box(mx(), 2.58, 2.58, 0.10, "bronze", 0, 0, z + 0.55)
    mb.box(mx(), 2.02, 2.02, 0.32, "bronze", 0, 0, z + 0.76)
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box(mx(), 0.34, 0.34, 0.50, "bronze", sx * 0.98, sy * 0.98, z + 0.80)
            mb.cyl(mx(), 0.20, 0.12, "gold", 12, sx * 0.98, sy * 0.98, z + 1.06)
    # --- fukubachi (bowl) + ukebana (lotus) -------------------------------
    mb.cyl(mx(), 1.04, 0.56, "bronze", 32, 0, 0, z + 0.92, r2=0.62)
    mb.cyl(mx(), 1.08, 0.10, "bronze", 32, 0, 0, z + 0.90, r2=1.03)
    mb.cyl(mx(), 0.60, 0.30, "bronze", 32, 0, 0, z + 1.48, r2=0.72)
    mb.cyl(mx(), 0.72, 0.34, "bronze", 32, 0, 0, z + 1.78, r2=1.18)
    mb.cyl(mx(), 1.18, 0.12, "bronze", 32, 0, 0, z + 2.12, r2=1.02)
    for k in range(18):
        a = 2 * PI * k / 18
        Mp = mx(math.cos(a) * 0.95, math.sin(a) * 0.95, z + 1.96, rz=a)
        mb.box(Mp, 0.26, 0.36, 0.30, "bronze", 0, 0, 0)
    z0 = z + 2.24
    # --- shaft + nine rings -----------------------------------------------
    mb.cyl(mx(), 0.225, 7.30, "bronze", 18, 0, 0, z0 - 0.10)
    for k in range(9):
        R = 1.04 - 0.036 * k
        mb.torus(mx(), R, 0.098, "bronze", 36, 10, cz=z0 + 0.42 + k * 0.52)
    # --- suien (flame openwork) -------------------------------------------
    fl = [(0.00, 0.00), (0.24, 0.16), (0.40, 0.39), (0.28, 0.62),
          (0.47, 0.84), (0.31, 1.06), (0.39, 1.28), (0.22, 1.51),
          (0.17, 1.71), (0.00, 1.96)]
    poly = fl + [(-x, zz) for (x, zz) in reversed(fl[1:])]
    n = len(poly)
    zs = z0 + 5.02
    for s in range(4):
        Ms = mx(rz=s * PI / 2) @ Matrix.Translation((0, 0, zs))
        for yy in (0.032, -0.032):
            pts = [Ms @ Vector((x, yy, zz)) for (x, zz) in poly]
            ctr = Ms @ Vector((0, yy, 0.62))
            i0 = len(mb.v)
            for q in pts:
                mb.v.append((q.x, q.y, q.z))
            for q in range(n):
                mb.poly([ctr, mb.v[i0 + q], mb.v[i0 + (q + 1) % n]], "bronze")
        for q in range(n):
            q2 = (q + 1) % n
            a0 = Ms @ Vector((poly[q][0], 0.032, poly[q][1]))
            a1 = Ms @ Vector((poly[q][0], -0.032, poly[q][1]))
            b0 = Ms @ Vector((poly[q2][0], 0.032, poly[q2][1]))
            b1 = Ms @ Vector((poly[q2][0], -0.032, poly[q2][1]))
            mb.poly([a0, a1, b1, b0], "bronze")
    # --- ryusha + hoju -----------------------------------------------------
    mb.cyl(mx(), 0.58, 0.15, "gold", 32, 0, 0, z0 + 7.02)
    mb.cyl(mx(), 0.36, 0.10, "gold", 24, 0, 0, z0 + 7.17)
    mb.sphere(mx(), 0.34, "gold", 24, 14, cz=z0 + 7.47)
    mb.cyl(mx(), 0.19, 0.42, "gold", 18, 0, 0, z0 + 7.67, r2=0.012)
    mb.build("相輪", coll("04_相輪"))


def build_platform():
    mb = MB(["stone"])
    h = PLAT_TOP
    # core
    mb.box(mx(), 2 * PLAT_HALF, 2 * PLAT_HALF, h - 0.14, "stone", 0, 0, (h - 0.14) / 2)
    # top curb (overhanging)
    mb.box(mx(), 2 * PLAT_HALF + 0.36, 2 * PLAT_HALF + 0.36, 0.14, "stone_step",
           0, 0, h - 0.07)
    mb.box(mx(), 2 * PLAT_HALF + 0.60, 2 * PLAT_HALF + 0.60, 0.12, "stone_step",
           0, 0, 0.06)
    mb.box(mx(), 2 * PLAT_HALF + 0.22, 2 * PLAT_HALF + 0.22, h - 0.30, "stone",
           0, 0, (h - 0.30) / 2 + 0.12)
    # steps on four sides
    for s in range(4):
        M = mx(rz=s * PI / 2)
        n = 5
        for k in range(n):
            zz = (h - 0.16) * (k + 1) / n
            depth = 0.34
            yy = PLAT_HALF + 0.30 + (n - k - 0.5) * depth
            mb.box(M, 3.60, depth + 0.02, zz, "stone_step", 0, yy, zz / 2)
        # cheek walls
        for sx in (-1, 1):
            mb.box(M, 0.34, n * depth + 0.30, h * 0.94, "stone_step",
                   sx * 1.95, PLAT_HALF + 0.30 + (n * depth) / 2, h * 0.47)
    mb.build("基壇", coll("01_基壇"))


def build_ground():
    me = bpy.data.meshes.new("地面")
    s = 2200
    me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [],
                   [(0, 1, 2, 3)])
    me.materials.append(bpy.data.materials["gravel"])
    ob = bpy.data.objects.new("地面", me)
    coll("05_環境").objects.link(ob)
    # stone apron around the platform
    mb = MB(["stone_step"])
    a = PLAT_HALF + 3.4
    mb.box(mx(), 2 * a, 2 * a, 0.06, "stone_step", 0, 0, -0.02)
    mb.build("石畳", coll("01_基壇"))


# --------------------------------------------------------------------------- #
#  Scene
# --------------------------------------------------------------------------- #
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 1.0


def setup_world():
    w = bpy.data.worlds.new("sky")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    L = nt.links.new
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    dirv = tc.outputs['Generated']
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    L(dirv, sep.inputs['Vector'])
    # --- gradient sky ------------------------------------------------------
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = 0.500
    mr.inputs['From Max'].default_value = 0.980
    L(sep.outputs['Z'], mr.inputs['Value'])
    pw = nt.nodes.new('ShaderNodeMath')
    pw.operation = 'POWER'
    pw.inputs[1].default_value = 0.78
    L(mr.outputs['Result'], pw.inputs[0])
    grad = PL._ramp(nt, [(0.00, (0.62, 0.74, 0.86)),
                         (0.10, (0.34, 0.52, 0.76)),
                         (0.40, (0.11, 0.27, 0.66)),
                         (1.00, (0.04, 0.11, 0.42))])
    L(pw.outputs[0], grad.inputs['Fac'])
    # --- clouds ------------------------------------------------------------
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (7.0, 7.0, 9.0)
    L(dirv, mp.inputs['Vector'])
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 1.0
    nz.inputs['Detail'].default_value = 12.0
    nz.inputs['Roughness'].default_value = 0.60
    nz.inputs['Distortion'].default_value = 0.55
    L(mp.outputs['Vector'], nz.inputs['Vector'])
    cm = PL._ramp(nt, [(0.515, (0, 0, 0)), (0.575, (1, 1, 1))])
    L(nz.outputs['Fac'], cm.inputs['Fac'])
    nz2 = nt.nodes.new('ShaderNodeTexNoise')
    nz2.inputs['Scale'].default_value = 3.0
    nz2.inputs['Detail'].default_value = 8.0
    L(mp.outputs['Vector'], nz2.inputs['Vector'])
    sh = PL._ramp(nt, [(0.32, (0.55, 0.60, 0.68)), (0.62, (1.0, 1.0, 1.0))])
    L(nz2.outputs['Fac'], sh.inputs['Fac'])
    # horizon fade so clouds never go below the horizon
    fade = nt.nodes.new('ShaderNodeMapRange')
    fade.inputs['From Min'].default_value = 0.498
    fade.inputs['From Max'].default_value = 0.575
    L(sep.outputs['Z'], fade.inputs['Value'])
    m1 = nt.nodes.new('ShaderNodeMath')
    m1.operation = 'MULTIPLY'
    L(cm.outputs['Color'], m1.inputs[0])
    L(fade.outputs['Result'], m1.inputs[1])
    mixc = nt.nodes.new('ShaderNodeMix')
    mixc.data_type = 'RGBA'
    L(m1.outputs[0], mixc.inputs['Factor'])
    L(grad.outputs['Color'], mixc.inputs[6])
    L(sh.outputs['Color'], mixc.inputs[7])
    # brighten cloud a touch above the sky
    mul = nt.nodes.new('ShaderNodeMix')
    mul.data_type = 'RGBA'
    mul.blend_type = 'ADD'
    mul.inputs['Factor'].default_value = 0.22
    L(mixc.outputs[2], mul.inputs[6])
    mul.inputs[7].default_value = (0.10, 0.10, 0.10, 1)

    # camera rays see the bright sky, lighting rays see a dimmer dome
    lp = nt.nodes.new('ShaderNodeLightPath')
    st = nt.nodes.new('ShaderNodeMix')
    st.data_type = 'FLOAT'
    st.inputs[2].default_value = 1.0
    st.inputs[3].default_value = 0.42
    L(lp.outputs['Is Camera Ray'], st.inputs['Factor'])
    L(mul.outputs[2], bg.inputs['Color'])
    L(st.outputs[0], bg.inputs['Strength'])
    L(bg.outputs['Background'], out.inputs['Surface'])
    return w


def setup_sun():
    d = bpy.data.lights.new("sun", 'SUN')
    d.energy = 4.6
    d.angle = RAD(1.4)
    d.color = (1.0, 0.955, 0.89)
    ob = bpy.data.objects.new("sun", d)
    bpy.context.scene.collection.objects.link(ob)
    direction = Vector((0.58, -0.78, 0.95)).normalized()   # toward the sun
    ob.rotation_euler = (-direction).to_track_quat('-Z', 'Y').to_euler()
    return ob


def add_fill():
    # large soft source simulating bounce from the sunlit gravel courtyard
    d = bpy.data.lights.new("fill_bounce", 'AREA')
    d.shape = 'RECTANGLE'
    d.size = 42.0
    d.size_y = 26.0
    d.energy = 1500.0
    d.color = (1.0, 0.95, 0.86)
    ob = bpy.data.objects.new("fill_bounce", d)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = (2.0, -30.0, 3.0)
    v = Vector((0, 0, 9.0)) - Vector(ob.location)
    ob.rotation_euler = v.to_track_quat('-Z', 'Y').to_euler()
    # cool sky fill from the opposite side
    d2 = bpy.data.lights.new("fill_sky", 'AREA')
    d2.shape = 'RECTANGLE'
    d2.size = 30.0
    d2.size_y = 30.0
    d2.energy = 520.0
    d2.color = (0.72, 0.82, 1.0)
    ob2 = bpy.data.objects.new("fill_sky", d2)
    bpy.context.scene.collection.objects.link(ob2)
    ob2.location = (-26.0, -8.0, 22.0)
    v = Vector((0, 0, 14.0)) - Vector(ob2.location)
    ob2.rotation_euler = v.to_track_quat('-Z', 'Y').to_euler()
    return ob, ob2


def add_camera(name, loc, target, focal=45.0, sensor=36.0):
    cd = bpy.data.cameras.new(name)
    cd.lens = focal
    cd.sensor_width = sensor
    ob = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    d = (Vector(target) - Vector(loc))
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return ob


def setup_render(samples=160, res=(1080, 1620)):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'GPU'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    for d in prefs.devices:
        d.use = (d.type != 'CPU')
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    sc.cycles.max_bounces = 6
    sc.cycles.diffuse_bounces = 4
    sc.cycles.glossy_bounces = 4
    sc.cycles.transmission_bounces = 4
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.exposure = 0.30
    sc.render.image_settings.file_format = 'PNG'
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.012


def main():
    reset()
    build_materials()
    build_ground()
    build_platform()
    build_veranda()
    for i in range(5):
        build_storey(i)
        build_roof(i)
        if i < 4:
            build_balcony(i + 1)
    build_sorin()
    setup_world()
    setup_sun()
    add_fill()
    cam = add_camera("相机_主", (-4.2, -45.0, 3.2), (0, 0, 15.9), 46.0)
    bpy.context.scene.camera = cam
    add_camera("相机_透视", (29, -31, 6.6), (0, 0, 12.0), 50.0)
    add_camera("相机_细节", (8.0, -15.0, 2.8), (0, 0, 7.5), 55.0)
    setup_render()
    bpy.ops.wm.save_as_mainfile(
        filepath=os.path.join(OUT_DIR, "法隆寺五重塔.blend"))
    print("SAVED. verts total:", sum(len(o.data.vertices)
                                     for o in bpy.data.objects if o.type == 'MESH'))


if __name__ == "__main__":
    main()
