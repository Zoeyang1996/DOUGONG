# -*- coding: utf-8 -*-
"""
build_urnes.py -- Urnes Stave Church (乌尔内斯木板教堂), procedural model.

Reference: photographs of the west front and of the south-west three-quarter view.
Blender 5.0 / Cycles.  Every board, shingle and post is real geometry.

    blender -b -P build_urnes.py             # build + save + final renders
    blender -b -P build_urnes.py -- --quick  # build + one small preview

Coordinate system
    X : across the nave   (west front is -Y)
    Y : long axis, +Y towards the chancel (east)
    Z : up, ground at 0
Metres, proportions taken from the reference photographs.
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from urnes_lib import (MB, Frame, clip_poly, ccw, area2, revolve, strip_solid,
                       lathe_object, ensure_tint,
                       make_wood, make_shingle, make_stone, make_simple, _set)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLEND_PATH = os.path.join(ROOT, "Urnes_Stave_Church.blend")
RENDER_DIR = os.path.join(ROOT, "renders")
os.makedirs(RENDER_DIR, exist_ok=True)

QUICK = "--quick" in sys.argv
rng = random.Random(20261112)

# --------------------------------------------------------------------------- #
#  dimensions (m)
# --------------------------------------------------------------------------- #
NAVE_HX = 4.10                 # nave wall half width
NAVE_Y0, NAVE_Y1 = -4.60, 4.60
GAL_HX, GAL_Y0, GAL_Y1 = 6.30, -6.80, 6.80

Z_STONE = 0.95                 # top of the rubble plinth
Z_DECK = 1.02                  # gallery floor
Z_BEAM0 = 3.92                 # underside of the arcade plate
Z_BEAM1 = 4.22

AISLE_EAVE_X, AISLE_EAVE_Y, AISLE_EAVE_Z = 6.62, 7.12, 4.40
AISLE_TOP_Z = 6.15

NAVE_EAVE_X, NAVE_EAVE_Z = 4.55, 6.35
RIDGE_Z = 12.45
BAND_TOP = 8.60                # diamond cladding stops here

CH_Y0, CH_Y1 = 4.60, 9.10
CH_HX = 2.62
CH_EAVE = 5.10
CH_RIDGE = 8.80

TOW_HX = 1.72
TOW_Y0, TOW_Y1 = -4.30, -0.90
TOW_Z0, TOW_Z1 = 10.20, 14.65
SPIRE_R = 2.00
SPIRE_Z0, SPIRE_Z1 = 14.65, 22.10

ROOF_SLOPE = (RIDGE_Z - NAVE_EAVE_Z) / NAVE_EAVE_X


def roof_z(x):
    return RIDGE_Z - abs(x) * ROOF_SLOPE


# --------------------------------------------------------------------------- #
#  scene reset
# --------------------------------------------------------------------------- #
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def coll(name):
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c


C_SITE = coll("01_Site")
C_FND = coll("02_Foundation")
C_GAL = coll("03_Gallery_Porch")
C_NVE = coll("04_Nave")
C_CHN = coll("05_Chancel")
C_TOW = coll("06_Tower")
C_ROF = coll("07_Roofs")
C_DET = coll("08_Details")
C_CAM = coll("09_Cameras_Lights")

# --------------------------------------------------------------------------- #
#  materials
# --------------------------------------------------------------------------- #
MAT = {}
MAT["tar"] = make_wood("MAT_Wood_Tarred", (0.0700, 0.0450, 0.0290),
                       (0.0260, 0.0170, 0.0115), rough=0.58,
                       grain=(7.0, 7.0, 55.0), plank=(0.245, 0.70),
                       bump=0.35, tint_mul=0.30, mossy=0.25, spec=0.30)
MAT["board"] = make_wood("MAT_Wood_Board_Weathered", (0.0850, 0.0480, 0.0300),
                         (0.0330, 0.0180, 0.0110), rough=0.68,
                         grain=(9.0, 9.0, 48.0), bump=0.40,
                         tint_mul=0.38, mossy=0.30, spec=0.30)
MAT["timber"] = make_wood("MAT_Wood_Timber_Grey", (0.1220, 0.1100, 0.0930),
                          (0.0470, 0.0405, 0.0330), rough=0.78,
                          grain=(8.0, 8.0, 40.0), bump=0.45,
                          tint_mul=0.42, mossy=0.45, spec=0.28)
MAT["shingle"] = make_shingle("MAT_Shingle_Roof", (0.1480, 0.1290, 0.1080),
                              (0.0330, 0.0280, 0.0230), rough=0.87, moss=0.34)
MAT["diamond"] = make_shingle("MAT_Shingle_Diamond_Clad", (0.1010, 0.0620, 0.0390),
                              (0.0345, 0.0205, 0.0135), rough=0.82, moss=0.28,
                              tile=(0.06, 0.06, 80.0))
MAT["stone"] = make_stone("MAT_Stone_Rubble", (0.072, 0.069, 0.064))
MAT["door"] = make_wood("MAT_Wood_Door", (0.0770, 0.0420, 0.0250),
                        (0.0250, 0.0130, 0.0080), rough=0.55,
                        grain=(10.0, 10.0, 60.0), bump=0.5, tint_mul=0.35,
                        mossy=0.10, spec=0.38)
MAT["iron"] = make_simple("MAT_Iron_Forged", (0.018, 0.017, 0.016),
                          rough=0.52, metal=0.95)
MAT["glass"] = make_simple("MAT_Glass_Leaded", (0.085, 0.095, 0.100),
                           rough=0.25, spec=0.55)
MAT["lead"] = make_simple("MAT_Lead_Came", (0.030, 0.030, 0.031),
                          rough=0.45, metal=0.7)
MAT["paint"] = make_simple("MAT_Paint_Window_Frame", (0.190, 0.178, 0.155),
                           rough=0.62)
MAT["soffit"] = make_wood("MAT_Wood_Soffit", (0.1080, 0.0820, 0.0580),
                          (0.0420, 0.0300, 0.0210), rough=0.82,
                          grain=(6.0, 6.0, 30.0), bump=0.3, tint_mul=0.2)


def make_grass():
    mat = bpy.data.materials.new("MAT_Ground_Grass")
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    out.location = (600, 0)
    bsdf.location = (380, 0)
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    tex = nt.nodes.new("ShaderNodeTexCoord")
    tex.location = (-800, 0)
    n1 = nt.nodes.new("ShaderNodeTexNoise")
    n1.location = (-600, 120)
    n1.inputs["Scale"].default_value = 0.35
    n1.inputs["Detail"].default_value = 8.0
    nt.links.new(tex.outputs["Object"], n1.inputs["Vector"])
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.location = (-380, 120)
    cr.color_ramp.elements[0].color = (0.035, 0.062, 0.020, 1)
    cr.color_ramp.elements[0].position = 0.30
    cr.color_ramp.elements[1].color = (0.075, 0.105, 0.032, 1)
    cr.color_ramp.elements[1].position = 0.72
    nt.links.new(n1.outputs["Fac"], cr.inputs["Fac"])
    nt.links.new(cr.outputs["Color"], bsdf.inputs["Base Color"])
    _set(bsdf, "Roughness", 0.95)
    bmp = nt.nodes.new("ShaderNodeBump")
    bmp.location = (160, -200)
    bmp.inputs["Strength"].default_value = 0.4
    bmp.inputs["Distance"].default_value = 0.05
    n2 = nt.nodes.new("ShaderNodeTexNoise")
    n2.location = (-20, -260)
    n2.inputs["Scale"].default_value = 22.0
    nt.links.new(tex.outputs["Object"], n2.inputs["Vector"])
    nt.links.new(n2.outputs["Fac"], bmp.inputs["Height"])
    nt.links.new(bmp.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


MAT["grass"] = make_grass()


# --------------------------------------------------------------------------- #
#  geometry helpers
# --------------------------------------------------------------------------- #
def bar(mb, p0, p1, w, h, tint=(1, 1, 1), up=(0, 0, 1)):
    """rectangular beam between two points; w lateral, h across."""
    a, b = Vector(p0), Vector(p1)
    u = (b - a)
    if u.length < 1e-6:
        return
    u.normalize()
    up = Vector(up)
    n = u.cross(up)
    if n.length < 1e-6:
        n = u.cross(Vector((1, 0, 0)))
    n.normalize()
    v = n.cross(u).normalized()
    pts = []
    for end in (a, b):
        for s in (-1, 1):
            for t in (-1, 1):
                pts.append(end + n * (s * w * 0.5) + v * (t * h * 0.5))
    idx = [mb.vert(p) for p in pts]
    for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
              (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
        mb.face([idx[i] for i in f], tint)


def plank_clad(mb, fr, region, width, thick, tint, gap=0.012, rnd=rng):
    """vertical boards clipped to a convex region in a Frame's uv plane."""
    us = [p[0] for p in region]
    vs = [p[1] for p in region]
    u = math.floor(min(us) / width) * width
    while u < max(us):
        w = width - gap
        quad = [(u, min(vs)), (u + w, min(vs)),
                (u + w, max(vs)), (u, max(vs))]
        cp = clip_poly(quad, region)
        if len(cp) >= 3 and abs(area2(cp)) > w * (max(vs) - min(vs)) * 0.03:
            mb.prism(fr, cp, rnd.uniform(-0.004, 0.006),
                     thick * rnd.uniform(0.75, 1.15), tint)
        u += width


def horizontal_clad(mb, fr, region, board_h, thick, tint, gap=0.01, rnd=rng):
    vs = [p[1] for p in region]
    us = [p[0] for p in region]
    v = math.floor(min(vs) / board_h) * board_h
    while v < max(vs):
        h = board_h - gap
        quad = [(min(us), v), (max(us), v), (max(us), v + h), (min(us), v + h)]
        cp = clip_poly(quad, region)
        if len(cp) >= 3:
            mb.prism(fr, cp, rnd.uniform(0.0, 0.008), thick, tint)
        v += board_h


def _tint(base, rnd, lo=0.70, hi=1.22):
    k = rnd.uniform(lo, hi)
    warm = rnd.uniform(-0.07, 0.07)
    return (max(0.0, base[0] * k * (1 + warm)),
            max(0.0, base[1] * k),
            max(0.0, base[2] * k * (1 - warm)))


def shingle_plane(mb, mb_deck, pl, pr, tl, tr, tile_w, course, tint,
                  thick=0.019, deck=0.10, rnd=rng, gap=0.0055, zstep=0.0016):
    """Interlocking fish-scale shingle field over a trapezoidal roof plane.

    Diamonds are pitched half a tile horizontally and a full course
    vertically, so neighbouring tiles share edges: the thin ``gap`` left
    between them exposes the dark sheathing below and draws the diagonal
    coursing lines seen on the real church.  Each tile gets a wide random
    value spread (a few near-black, a few bleached) which is what makes the
    old tarred roof read as a mosaic of individual shingles.
    """
    O = Vector(pl)
    U = Vector(pr) - O
    L = U.length
    if L < 1e-5:
        return None
    U.normalize()
    w = Vector(tl) - O
    w = w - U * w.dot(U)
    Vlen = w.length
    if Vlen < 1e-5:
        return None
    V = w.normalized()
    fr = Frame(O, U, V)
    if fr.N.z < 0:                      # keep the sheathing on the outer face
        fr = Frame(O, -fr.U, fr.V)

    def uv(p):
        d = Vector(p) - O
        return (d.dot(fr.U), d.dot(fr.V))

    quad = ccw([uv(pl), uv(pr), uv(tr), uv(tl)])
    if mb_deck is not None:
        mb_deck.prism(fr, quad, -deck, 0.0, (1, 1, 1))

    umin = min(p[0] for p in quad)
    umax = max(p[0] for p in quad)
    vmin = min(p[1] for p in quad)
    vmax = max(p[1] for p in quad)

    h = course * 1.16                # tile height (tips tuck under the next row)
    hw = tile_w * 0.5
    pitch_u = tile_w * 0.5
    k = max(0.55, 1.0 - gap / hw)    # inset so a dark groove is left between tiles
    row = 0
    cv = vmin - course * 1.8
    while cv < vmax + course:
        cu = umin - tile_w + (pitch_u * 0.5 if row % 2 else 0.0)
        while cu < umax + tile_w:
            cx = cu + rnd.uniform(-0.0016, 0.0016)
            cy = cv + rnd.uniform(-0.0016, 0.0016)
            pts = [(cx - hw * k, cy),
                   (cx, cy + h * 0.5 * k),
                   (cx + hw * k, cy),
                   (cx, cy - h * 0.5 * k)]
            cp = clip_poly(pts, quad)
            if len(cp) >= 3 and abs(area2(cp)) > tile_w * course * 0.20:
                r = rnd.random()
                if r < 0.11:
                    m = rnd.uniform(0.34, 0.58)      # tar-black tile
                elif r < 0.25:
                    m = rnd.uniform(1.22, 1.62)      # bleached grey tile
                else:
                    m = rnd.uniform(0.80, 1.16)
                z0 = 0.0025 + row * zstep + rnd.uniform(0.0, 0.0013)
                mb.prism(fr, cp, z0, z0 + thick * rnd.uniform(0.85, 1.15),
                         (tint[0] * m, tint[1] * m, tint[2] * m))
            cu += pitch_u
        cv += course
        row += 1
    return fr, quad


def diamond_clad(mb, fr, region, s, tint, thick=0.020, rnd=rng, holes=()):
    """diamond-pattern wall cladding (the Urnes fish-scale facing)."""
    us = [p[0] for p in region]
    vs = [p[1] for p in region]
    u0, u1 = min(us), max(us)
    v0, v1 = min(vs), max(vs)
    j = 0
    v = v0 - s * 0.6
    while v < v1 + s:
        u = u0 - s * (0.5 if j % 2 else 0.0) - s
        while u < u1 + s:
            sw = s * rnd.uniform(0.94, 1.06)
            sh = s * 0.70 * rnd.uniform(0.95, 1.05)
            cu, cv = u + sw * 0.5, v
            skip = False
            for (hx0, hx1, hy0, hy1) in holes:
                if hx0 < cu < hx1 and hy0 < cv < hy1:
                    skip = True
                    break
            if not skip:
                pts = [(cu, cv + sh), (cu + sw * 0.5, cv),
                       (cu, cv - sh), (cu - sw * 0.5, cv)]
                jx = rnd.uniform(-0.012, 0.012) * sw
                jy = rnd.uniform(-0.012, 0.012) * sh
                pts = [(a + jx, b + jy) for a, b in pts]
                cp = clip_poly(pts, region)
                if len(cp) >= 3 and abs(area2(cp)) > sw * sh * 0.35:
                    z0 = 0.004 + (cv - v0) * 0.007 + rnd.uniform(0.0, 0.0015)
                    mb.prism(fr, cp, z0, z0 + thick,
                             _tint(tint, rnd, 0.82, 1.18))
            u += sw * 0.985
        v += s * 0.90
        j += 1


def stone_ring(mb, x0, x1, y0, y1, z0, z1, depth=0.34, rnd=rng, base=(1, 1, 1)):
    sides = [
        ((x0, y0), (x1, y0), (0, -1)),
        ((x1, y1), (x0, y1), (0, 1)),
        ((x0, y1), (x0, y0), (-1, 0)),
        ((x1, y0), (x1, y1), (1, 0)),
    ]
    z = z0
    while z < z1 - 0.02:
        h = min(rnd.uniform(0.155, 0.245), z1 - z)
        for (a, b, n) in sides:
            A, B = Vector(a), Vector(b)
            L = (B - A).length
            p = 0.0
            while p < L - 0.05:
                w = min(rnd.uniform(0.20, 0.44), L - p)
                c = A + (B - A) * ((p + w * 0.5) / L)
                d = depth * rnd.uniform(0.92, 1.04)
                bulge = rnd.uniform(-0.01, 0.022)
                centre = Vector((c.x + n[0] * (d * 0.5 + bulge),
                                 c.y + n[1] * (d * 0.5 + bulge),
                                 z + h * 0.5))
                ang = math.atan2(n[1], n[0])
                if abs(n[0]) > 0.5:
                    size = (d, w * rnd.uniform(0.94, 1.0), h * rnd.uniform(0.9, 1.0))
                else:
                    size = (w * rnd.uniform(0.94, 1.0), d, h * rnd.uniform(0.9, 1.0))
                g = rnd.uniform(0.60, 1.00)
                mb.obox(centre, size, ry=rnd.uniform(-0.015, 0.015),
                        tint=(g * base[0], g * base[1], g * base[2] * 0.98),
                        rz=ang + rnd.uniform(-0.015, 0.015))
                p += w * rnd.uniform(0.92, 0.99)
        z += h * 0.92


def arch_board(mb, fr, u0, u1, z_bot, z_top, rise, thick, tint, n=12):
    poly = []
    for i in range(n + 1):
        t = i / n
        u = u0 + (u1 - u0) * t
        poly.append((u, z_bot + rise * math.sin(math.pi * t) ** 0.7))
    poly.append((u1, z_top))
    poly.append((u0, z_top))
    mb.prism(fr, poly, 0.0, thick, tint)


# --------------------------------------------------------------------------- #
#  1. foundation
# --------------------------------------------------------------------------- #
def build_foundation():
    mb = MB("FND_Rubble_Plinth")
    stone_ring(mb, -GAL_HX - 0.18, GAL_HX + 0.18, GAL_Y0 - 0.18, GAL_Y1 + 0.18,
               0.0, Z_STONE, depth=0.36)
    stone_ring(mb, -CH_HX - 0.24, CH_HX + 0.24, CH_Y1 - 0.4, CH_Y1 + 1.42,
               0.0, Z_STONE, depth=0.34)
    mb.box(-GAL_HX - 0.04, GAL_HX + 0.04, GAL_Y0 - 0.04, GAL_Y1 + 0.04,
           -0.30, Z_STONE - 0.05, (0.62, 0.60, 0.57))
    mb.obox((0, CH_Y1 + 0.55, Z_STONE * 0.5),
            ((CH_HX + 0.08) * 2, 1.7, Z_STONE - 0.05), tint=(0.62, 0.60, 0.57))
    mb.build(MAT["stone"], C_FND)

    cap = MB("FND_Cap_Course")
    stone_ring(cap, -GAL_HX - 0.16, GAL_HX + 0.16, GAL_Y0 - 0.16, GAL_Y1 + 0.16,
               Z_STONE - 0.07, Z_STONE + 0.02, depth=0.30, base=(1.05, 1.05, 1.02))
    cap.build(MAT["stone"], C_FND)

    st = MB("FND_Steps_West")
    for i in range(3):
        w = 1.42 - i * 0.02
        st.box(-w, w, GAL_Y0 - 1.36 + i * 0.30, GAL_Y0 - 0.52 + i * 0.30,
               i * 0.31 - 0.02, i * 0.31 + 0.30, (0.95, 0.95, 0.92))
    st.build(MAT["stone"], C_FND)


# --------------------------------------------------------------------------- #
#  2. gallery (svalgang)
# --------------------------------------------------------------------------- #
POST_Z0 = Z_DECK
POST_Z1 = 3.46


def turned_post(mb, x, y, z0, z1, tint, rot=0.0):
    base = [(0.185, 0.000), (0.188, 0.045), (0.163, 0.085), (0.185, 0.120),
            (0.208, 0.165), (0.202, 0.240), (0.172, 0.350), (0.155, 0.470),
            (0.152, 0.600), (0.174, 0.645), (0.177, 0.690), (0.147, 0.735),
            (0.138, 0.820), (0.133, 1.740), (0.146, 2.190), (0.156, 2.310),
            (0.132, 2.375), (0.186, 2.450), (0.196, 2.520), (0.198, 2.575)]
    k = max(0.55, (z1 - z0 - 0.30) / base[-1][1])
    prof = [(r, dz * k) for (r, dz) in base]
    shaft = base[-1][1] * k
    seg = 22
    rings = []
    for (r, dz) in prof:
        ring = []
        for i in range(seg):
            a = 2 * math.pi * i / seg + rot
            ring.append(mb.vert((x + r * math.cos(a), y + r * math.sin(a),
                                 z0 + dz)))
        rings.append(ring)
    for k in range(len(rings) - 1):
        for i in range(seg):
            j = (i + 1) % seg
            mb.face((rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]),
                    tint)
    mb.face(list(reversed(rings[0])), tint)
    mb.face(rings[-1], tint)
    mb.box(x - 0.205, x + 0.205, y - 0.205, y + 0.205, z0 - 0.10, z0 + 0.004,
           tint)
    mb.box(x - 0.218, x + 0.218, y - 0.218, y + 0.218, z0 + shaft, z1, tint)


WEST_POSTS = [-GAL_HX, -4.68, -3.05, -1.42, 1.42, 3.05, 4.68, GAL_HX]
EAST_POSTS = [-GAL_HX, -3.15, 0.0, 3.15, GAL_HX]
SIDE_POSTS_Y = [-4.80, -2.85, -0.90, 1.05, 3.00, 4.95]


def build_gallery():
    d = MB("GAL_Deck")
    d.box(-GAL_HX - 0.16, GAL_HX + 0.16, GAL_Y0 - 0.16, GAL_Y1 + 0.16,
          Z_STONE - 0.02, Z_DECK, (1, 1, 1))
    for (y0, y1) in ((GAL_Y0 - 0.24, GAL_Y0 - 0.04), (GAL_Y1 + 0.04, GAL_Y1 + 0.24)):
        d.box(-GAL_HX - 0.24, GAL_HX + 0.24, y0, y1, Z_STONE - 0.28,
              Z_DECK + 0.05, (0.8, 0.8, 0.8))
    for (x0, x1) in ((-GAL_HX - 0.24, -GAL_HX - 0.04), (GAL_HX + 0.04, GAL_HX + 0.24)):
        d.box(x0, x1, GAL_Y0 - 0.24, GAL_Y1 + 0.24, Z_STONE - 0.28,
              Z_DECK + 0.05, (0.8, 0.8, 0.8))
    d.build(MAT["tar"], C_GAL)

    wt = 0.22
    door_w = 0.82
    walls = MB("GAL_Wall_Planked")
    for (xa, xb) in ((-GAL_HX, -door_w), (door_w, GAL_HX)):
        walls.box(xa, xb, GAL_Y0 - wt * 0.5, GAL_Y0 + wt * 0.5, Z_DECK, Z_BEAM1,
                  (0.9, 0.9, 0.9))
    walls.box(-door_w, door_w, GAL_Y0 - wt * 0.5, GAL_Y0 + wt * 0.5,
              Z_DECK + 2.06, Z_BEAM1, (0.9, 0.9, 0.9))
    ins = 0.62
    walls.box(-GAL_HX, GAL_HX, GAL_Y1 - wt * 0.5 - ins, GAL_Y1 + wt * 0.5 - ins,
              Z_DECK, Z_BEAM1, (0.86, 0.86, 0.86))
    walls.box(-GAL_HX - wt * 0.5 + ins, -GAL_HX + wt * 0.5 + ins, GAL_Y0, GAL_Y1,
              Z_DECK, Z_BEAM1, (0.78, 0.78, 0.78))
    walls.box(GAL_HX - wt * 0.5 - ins, GAL_HX + wt * 0.5 - ins, GAL_Y0, GAL_Y1,
              Z_DECK, Z_BEAM1, (0.78, 0.78, 0.78))
    walls.build(MAT["tar"], C_GAL)

    posts = MB("GAL_Posts_Turned")
    pos = [(x, GAL_Y0) for x in WEST_POSTS]
    pos += [(x, GAL_Y1) for x in EAST_POSTS]
    for y in SIDE_POSTS_Y:
        pos += [(-GAL_HX, y), (GAL_HX, y)]
    seen = set()
    for (x, y) in pos:
        key = (round(x, 2), round(y, 2))
        if key in seen:
            continue
        seen.add(key)
        turned_post(posts, x, y, POST_Z0, POST_Z1, (1, 1, 1),
                    rot=rng.uniform(0, 0.3))
    posts.build(MAT["timber"], C_GAL)

    arch = MB("GAL_Arches")
    for i in range(len(WEST_POSTS) - 1):
        a, b = WEST_POSTS[i], WEST_POSTS[i + 1]
        if abs(a) < 1.45 and abs(b) < 1.45:
            continue
        fr = Frame((a, GAL_Y0 - 0.21, 0), (1, 0, 0), (0, 0, 1))
        arch_board(arch, fr, 0.0, b - a, Z_BEAM0 - 0.58, Z_BEAM0, 0.38, 0.16,
                   (0.95, 0.95, 0.95))
    for i in range(len(EAST_POSTS) - 1):
        a, b = EAST_POSTS[i], EAST_POSTS[i + 1]
        fr = Frame((a, GAL_Y1 + 0.21, 0), (1, 0, 0), (0, 0, 1))
        arch_board(arch, fr, 0.0, b - a, Z_BEAM0 - 0.58, Z_BEAM0, 0.38, 0.16,
                   (0.95, 0.95, 0.95))
    for sx in (-1, 1):
        ys = [GAL_Y0] + SIDE_POSTS_Y + [GAL_Y1]
        for i in range(len(ys) - 1):
            a, b = ys[i], ys[i + 1]
            fr = Frame((sx * (GAL_HX + 0.21), a, 0), (0, 1, 0), (0, 0, 1))
            arch_board(arch, fr, 0.0, b - a, Z_BEAM0 - 0.58, Z_BEAM0, 0.38,
                       0.16, (0.95, 0.95, 0.95))
    arch.build(MAT["timber"], C_GAL)

    pl = MB("GAL_Arcade_Plate")
    pl.box(-GAL_HX - 0.30, GAL_HX + 0.30, GAL_Y0 - 0.32, GAL_Y0 + 0.22,
           Z_BEAM0, Z_BEAM1, (1, 1, 1))
    pl.box(-GAL_HX - 0.30, GAL_HX + 0.30, GAL_Y1 - 0.22, GAL_Y1 + 0.32,
           Z_BEAM0, Z_BEAM1, (1, 1, 1))
    pl.box(-GAL_HX - 0.32, -GAL_HX + 0.22, GAL_Y0, GAL_Y1, Z_BEAM0, Z_BEAM1,
           (1, 1, 1))
    pl.box(GAL_HX - 0.22, GAL_HX + 0.32, GAL_Y0, GAL_Y1, Z_BEAM0, Z_BEAM1,
           (1, 1, 1))
    pl.box(-GAL_HX - 0.40, GAL_HX + 0.40, GAL_Y0 - 0.42, GAL_Y0 + 0.28,
           Z_BEAM1 - 0.05, Z_BEAM1 + 0.07, (1, 1, 1))
    pl.box(-GAL_HX - 0.40, GAL_HX + 0.40, GAL_Y1 - 0.28, GAL_Y1 + 0.42,
           Z_BEAM1 - 0.05, Z_BEAM1 + 0.07, (1, 1, 1))
    pl.box(-GAL_HX - 0.42, -GAL_HX + 0.28, GAL_Y0, GAL_Y1, Z_BEAM1 - 0.05,
           Z_BEAM1 + 0.07, (1, 1, 1))
    pl.box(GAL_HX - 0.28, GAL_HX + 0.42, GAL_Y0, GAL_Y1, Z_BEAM1 - 0.05,
           Z_BEAM1 + 0.07, (1, 1, 1))
    pl.build(MAT["timber"], C_GAL)


# --------------------------------------------------------------------------- #
#  3. west porch
# --------------------------------------------------------------------------- #
POR_Y_FRONT = -8.48
POR_HX = 1.30
POR_EAVE = 4.34
POR_RIDGE = 5.74


def build_porch():
    mb = MB("POR_Structure")
    mb.box(-POR_HX - 0.34, POR_HX + 0.34, POR_Y_FRONT - 0.14, GAL_Y0,
           Z_STONE - 0.02, Z_DECK - 0.02, (0.9, 0.9, 0.9))
    for sx in (-1, 1):
        turned_post(mb, sx * POR_HX, POR_Y_FRONT, Z_DECK, Z_BEAM0,
                    (1, 1, 1), rot=rng.uniform(0, 0.3))
    bar(mb, (-POR_HX - 0.30, POR_Y_FRONT, POR_EAVE - 0.26),
        (POR_HX + 0.30, POR_Y_FRONT, POR_EAVE - 0.26), 0.30, 0.20)
    for sx in (-1, 1):
        mb.box(sx * (POR_HX - 0.10), sx * (POR_HX + 0.10), POR_Y_FRONT,
               GAL_Y0 - 0.06, Z_DECK, POR_EAVE - 0.02, (0.9, 0.9, 0.9))
    mb.build(MAT["tar"], C_GAL)

    g = MB("POR_Gable_Diamond")
    fr = Frame((0, POR_Y_FRONT - 0.07, 0), (1, 0, 0), (0, 0, 1))
    region = [(-POR_HX - 0.34, POR_EAVE - 0.06), (POR_HX + 0.34, POR_EAVE - 0.06),
              (POR_HX + 0.34, POR_EAVE - 0.02), (0.0, POR_RIDGE),
              (-POR_HX - 0.34, POR_EAVE - 0.02)]
    diamond_clad(g, fr, region, 0.235, (0.95, 0.9, 0.9), thick=0.028)
    g.build(MAT["diamond"], C_GAL)

    gb = MB("POR_Gable_Backing")
    gb.prism(fr, ccw(region), -0.07, -0.012, (1, 1, 1))
    gb.build(MAT["tar"], C_GAL)

    b = MB("POR_Bargeboard")
    for sx in (-1, 1):
        bar(b, (sx * (POR_HX + 0.46), POR_Y_FRONT - 0.12, POR_EAVE - 0.14),
            (0.0, POR_Y_FRONT - 0.12, POR_RIDGE + 0.05), 0.09, 0.24)
        bar(b, (sx * (POR_HX + 0.46), POR_Y_FRONT - 0.12, POR_EAVE - 0.14),
            (sx * (POR_HX + 0.46), GAL_Y0, POR_EAVE - 0.14), 0.10, 0.22)
    b.build(MAT["timber"], C_GAL)

    sh = MB("ROF_Porch_Shingles")
    dk = MB("ROF_Porch_Deck")
    for sx in (-1, 1):
        shingle_plane(sh, dk,
                      (sx * (POR_HX + 0.50), POR_Y_FRONT - 0.16, POR_EAVE - 0.16),
                      (sx * (POR_HX + 0.50), GAL_Y0 + 0.15, POR_EAVE - 0.16),
                      (0.0, POR_Y_FRONT - 0.16, POR_RIDGE),
                      (0.0, GAL_Y0 + 0.15, POR_RIDGE),
                      0.250, 0.175, (1, 1, 1), thick=0.019, deck=0.07)
    sh.build(MAT["shingle"], C_ROF)
    dk.build(MAT["soffit"], C_ROF)

    fin = MB("POR_Finial_Carved")
    z = POR_RIDGE
    fin.box(-0.042, 0.042, POR_Y_FRONT - 0.18, POR_Y_FRONT - 0.04, z, z + 0.40,
            (1, 1, 1))
    fin.box(-0.19, 0.19, POR_Y_FRONT - 0.15, POR_Y_FRONT - 0.07, z + 0.24,
            z + 0.31, (1, 1, 1))
    fin.box(-0.10, 0.10, POR_Y_FRONT - 0.15, POR_Y_FRONT - 0.07, z + 0.31,
            z + 0.36, (1, 1, 1))
    fin.build(MAT["timber"], C_GAL)


# --------------------------------------------------------------------------- #
#  4. nave
# --------------------------------------------------------------------------- #
WIN_W, WIN_SILL, WIN_H = 0.60, 7.06, 1.42


def build_window(cx, y_wall, cz, w, h, name, facing=-1):
    """round-headed leaded window set into a wall at y=y_wall.
    facing = -1 -> west facing, +1 -> east facing."""
    out = 0.095
    if abs(facing) > 1:                       # side wall: cx is the x of the wall
        fr = Frame((cx, y_wall, 0), (0, -1, 0) if facing > 0 else (0, 1, 0), (0, 0, 1))
    else:
        ux = 1.0 if facing < 0 else -1.0
        fr = Frame((cx, y_wall, 0), (ux, 0, 0), (0, 0, 1))
    zs = cz - h * 0.5
    zc = cz + h * 0.5 - w * 0.5
    rb, rt = w * 0.5 + 0.012, w * 0.5 + 0.105

    rec = MB(name + "_Reveal")
    rec.prism(fr, [(-rb, zs - 0.02), (rb, zs - 0.02), (rb, zc), (0, zc + rb),
                   (-rb, zc)], -0.30, 0.0, (0.28, 0.28, 0.28))
    rec.build(MAT["tar"], C_DET)

    sur = MB(name + "_Surround")
    seg = 12
    for i in range(seg):
        a0 = math.pi * i / seg
        a1 = math.pi * (i + 1) / seg
        p = [(math.cos(a0) * rb, zc + math.sin(a0) * rb),
             (math.cos(a1) * rb, zc + math.sin(a1) * rb),
             (math.cos(a1) * rt, zc + math.sin(a1) * rt),
             (math.cos(a0) * rt, zc + math.sin(a0) * rt)]
        sur.prism(fr, p, out - 0.02, out + 0.045, (1, 1, 1))
    for sx in (-1, 1):
        sur.prism(fr, [(sx * rb, zs), (sx * rt, zs), (sx * rt, zc), (sx * rb, zc)],
                  out - 0.02, out + 0.045, (1, 1, 1))
    sur.prism(fr, [(-rt - 0.05, zs - 0.08), (rt + 0.05, zs - 0.08),
                   (rt + 0.05, zs + 0.005), (-rt - 0.05, zs + 0.005)],
              out - 0.04, out + 0.10, (1, 1, 1))
    sur.build(MAT["paint"], C_DET)

    # lead backing + diamond glass panes
    lead = MB(name + "_Lead_Backing")
    op = [(-w * 0.5, zs), (w * 0.5, zs)]
    for i in range(seg + 1):
        a = math.pi * i / seg
        op.append((math.cos(a) * w * 0.5, zc + math.sin(a) * w * 0.5))
    lead.prism(fr, op, -0.185, -0.175, (1, 1, 1))
    lead.build(MAT["lead"], C_DET)

    gl = MB(name + "_Leaded_Glass")
    s = 0.115
    j = 0
    v = zs - s
    while v < zc + w * 0.5:
        u = -w * 0.5 - s * (0.5 if j % 2 else 0.0)
        while u < w * 0.5 + s:
            cu = u + s * 0.5
            pts = [(cu, v + s * 0.72), (cu + s * 0.46, v),
                   (cu, v - s * 0.72), (cu - s * 0.46, v)]
            cp = clip_poly(pts, op)
            if len(cp) >= 3 and abs(area2(cp)) > s * s * 0.12:
                gl.prism(fr, cp, -0.172, -0.166, (1, 1, 1))
            u += s * 0.5
        v += s * 0.36
        j += 1
    gl.build(MAT["glass"], C_DET)


def build_nave():
    mb = MB("NVE_Walls_Core")
    t = 0.24
    mb.box(-NAVE_HX, NAVE_HX, NAVE_Y0, NAVE_Y0 + t, Z_DECK, 7.30, (0.85, 0.85, 0.85))
    mb.box(-NAVE_HX, NAVE_HX, NAVE_Y1 - t, NAVE_Y1, Z_DECK, 7.30, (0.8, 0.8, 0.8))
    mb.box(-NAVE_HX, -NAVE_HX + t, NAVE_Y0, NAVE_Y1, Z_DECK, 7.30, (0.9, 0.9, 0.9))
    mb.box(NAVE_HX - t, NAVE_HX, NAVE_Y0, NAVE_Y1, Z_DECK, 7.30, (0.9, 0.9, 0.9))
    mb.build(MAT["tar"], C_NVE)

    gable = [(-NAVE_HX, Z_DECK), (NAVE_HX, Z_DECK),
             (NAVE_HX, roof_z(NAVE_HX)), (0.0, RIDGE_Z),
             (-NAVE_HX, roof_z(NAVE_HX))]
    body = MB("NVE_Gable_West_Body")
    frw = Frame((0, NAVE_Y0, 0), (1, 0, 0), (0, 0, 1))
    body.prism(frw, gable, -0.30, 0.0, (0.86, 0.86, 0.86))
    body.build(MAT["tar"], C_NVE)

    dia = MB("NVE_Clad_Diamond_West")
    band = clip_poly(gable, [(-NAVE_HX - 1, 5.55),
                             (NAVE_HX + 1, AISLE_TOP_Z - 0.04),
                             (NAVE_HX + 1, BAND_TOP), (-NAVE_HX - 1, BAND_TOP)])
    hole = [(-WIN_W * 0.5 - 0.06, WIN_W * 0.5 + 0.06,
             WIN_SILL - 0.05, WIN_SILL + WIN_H + 0.05)]
    diamond_clad(dia, frw, band, 0.445, (1, 1, 1), thick=0.034, holes=hole)
    dia.build(MAT["diamond"], C_NVE)

    back = MB("NVE_Clad_Backing_Panel")
    back.prism(frw, band, 0.004, 0.0055, (0.95, 0.95, 0.95))
    back.build(MAT["board"], C_NVE)

    bd = MB("NVE_Clad_Boards_West")
    upper = clip_poly(gable, [(-NAVE_HX - 1, BAND_TOP + 0.03),
                              (NAVE_HX + 1, BAND_TOP + 0.03),
                              (NAVE_HX + 1, RIDGE_Z + 1), (-NAVE_HX - 1, RIDGE_Z + 1)])
    plank_clad(bd, frw, upper, 0.158, 0.030, (1, 1, 1), gap=0.008)
    bd.build(MAT["board"], C_NVE)

    collar = MB("NVE_Collar_Beam_West")
    cw = (RIDGE_Z - BAND_TOP) / ROOF_SLOPE - 0.12
    bar(collar, (-cw, NAVE_Y0 - 0.16, BAND_TOP),
        (cw, NAVE_Y0 - 0.16, BAND_TOP), 0.16, 0.19)
    bar(collar, (-0.56, NAVE_Y0 - 0.17, WIN_SILL - 0.10),
        (0.56, NAVE_Y0 - 0.17, WIN_SILL - 0.10), 0.15, 0.13)
    collar.build(MAT["timber"], C_NVE)

    build_window(0.0, NAVE_Y0, WIN_SILL + WIN_H * 0.5, WIN_W, WIN_H,
                 "NVE_Win_Gable", facing=-1)

    # east gable (closes the nave against the chancel roof)
    gab_e = [(-NAVE_HX, 7.20), (NAVE_HX, 7.20),
             (NAVE_HX, roof_z(NAVE_HX)), (0.0, RIDGE_Z), (-NAVE_HX, roof_z(NAVE_HX))]
    fwd = Frame((0, NAVE_Y1, 0), (-1, 0, 0), (0, 0, 1))
    body_e = MB("NVE_Gable_East_Body")
    body_e.prism(fwd, gab_e, -0.30, 0.0, (0.86, 0.86, 0.86))
    body_e.build(MAT["tar"], C_NVE)

    bd_e = MB("NVE_Clad_Boards_East")
    upper_e = clip_poly(gab_e, [(-NAVE_HX - 1, 9.30), (NAVE_HX + 1, 9.30),
                                (NAVE_HX + 1, RIDGE_Z + 1), (-NAVE_HX - 1, RIDGE_Z + 1)])
    plank_clad(bd_e, fwd, upper_e, 0.158, 0.030, (1, 1, 1), gap=0.008)
    bd_e.build(MAT["board"], C_NVE)

    dia_e = MB("NVE_Clad_Diamond_East")
    band_e = clip_poly(gab_e, [(-NAVE_HX - 1, 7.20), (NAVE_HX + 1, 7.20),
                               (NAVE_HX + 1, 9.30), (-NAVE_HX - 1, 9.30)])
    diamond_clad(dia_e, fwd, band_e, 0.445, (1, 1, 1), thick=0.032)
    dia_e.build(MAT["diamond"], C_NVE)
    back_e = MB("NVE_Clad_Backing_East")
    back_e.prism(fwd, band_e, 0.004, 0.0055, (0.95, 0.95, 0.95))
    back_e.build(MAT["board"], C_NVE)
    col_e = MB("NVE_Collar_Beam_East")
    bar(col_e, (-(RIDGE_Z - 9.30) / ROOF_SLOPE + 0.12, NAVE_Y1 + 0.16, 9.30),
        ((RIDGE_Z - 9.30) / ROOF_SLOPE - 0.12, NAVE_Y1 + 0.16, 9.30), 0.16, 0.19)
    col_e.build(MAT["timber"], C_NVE)
    build_west_door()


def build_west_door():
    y = GAL_Y0
    w, h = 0.82, 2.04
    z0 = Z_DECK + 0.01
    mb = MB("DET_Door_Main")
    n = 7
    pw = (2 * w) / n
    for i in range(n):
        x0 = -w + i * pw + 0.005
        mb.box(x0, x0 + pw - 0.010, y - 0.095, y - 0.02, z0, z0 + h, (1, 1, 1))
    mb.box(-w - 0.06, -w + 0.05, y - 0.12, y - 0.01, z0, z0 + h, (1, 1, 1))
    mb.box(w - 0.05, w + 0.06, y - 0.12, y - 0.01, z0, z0 + h, (1, 1, 1))
    mb.box(-w - 0.06, w + 0.06, y - 0.12, y - 0.01, z0 + h, z0 + h + 0.10,
           (1, 1, 1))
    mb.build(MAT["door"], C_DET)

    ir = MB("DET_Door_Ironwork")
    for zz in (0.42, 1.12, 1.72):
        ir.box(-w - 0.02, w + 0.02, y - 0.112, y - 0.088, z0 + zz,
               z0 + zz + 0.05, (1, 1, 1))
        for sx in (-1, 1):
            ir.obox((sx * (w - 0.02), y - 0.100, z0 + zz + 0.025),
                    (0.10, 0.038, 0.11))
    # ring handle
    cx, cz, r = 0.44, 1.30, 0.072
    seg = 14
    for i in range(seg):
        a0 = 2 * math.pi * i / seg
        a1 = 2 * math.pi * (i + 1) / seg
        bar(ir, (cx + r * math.cos(a0), y - 0.135, cz + r * math.sin(a0)),
            (cx + r * math.cos(a1), y - 0.135, cz + r * math.sin(a1)),
            0.016, 0.016, up=(0, 1, 0))
    ir.box(cx - 0.03, cx + 0.03, y - 0.150, y - 0.105, cz + 0.05, cz + 0.10,
           (1, 1, 1))
    ir.build(MAT["iron"], C_DET)


# --------------------------------------------------------------------------- #
#  5. roofs
# --------------------------------------------------------------------------- #
def build_aisle_roof():
    sh = MB("ROF_Aisle_Shingles")
    dk = MB("ROF_Aisle_Deck")
    ax, ay, az = AISLE_EAVE_X, AISLE_EAVE_Y, AISLE_EAVE_Z
    ix, iy, iz = NAVE_HX - 0.08, NAVE_Y0 * -1, AISLE_TOP_Z

    shingle_plane(sh, dk, (-ax, -ay, az), (ax, -ay, az),
                  (-ix, -iy, iz), (ix, -iy, iz), 0.255, 0.178, (1, 1, 1),
                  thick=0.024, deck=0.12)
    shingle_plane(sh, dk, (ax, ay, az), (-ax, ay, az),
                  (ix, iy, iz), (-ix, iy, iz), 0.255, 0.178, (1, 1, 1),
                  thick=0.024, deck=0.12)
    shingle_plane(sh, dk, (-ax, ay, az), (-ax, -ay, az),
                  (-ix, iy, iz), (-ix, -iy, iz), 0.255, 0.178, (1, 1, 1),
                  thick=0.024, deck=0.12)
    shingle_plane(sh, dk, (ax, -ay, az), (ax, ay, az),
                  (ix, -iy, iz), (ix, iy, iz), 0.255, 0.178, (1, 1, 1),
                  thick=0.024, deck=0.12)
    sh.build(MAT["shingle"], C_ROF)
    dk.build(MAT["soffit"], C_ROF)

    hp = MB("ROF_Aisle_Hip_Boards")
    for sx in (-1, 1):
        for sy in (-1, 1):
            bar(hp, (sx * ax, sy * ay, az + 0.015),
                (sx * ix, sy * iy, iz + 0.015), 0.14, 0.115)
    for s in (-1, 1):
        bar(hp, (-ax - 0.04, s * ay, az - 0.06), (ax + 0.04, s * ay, az - 0.06),
            0.10, 0.22, (0.72, 0.72, 0.74))
        bar(hp, (s * ax, -ay - 0.04, az - 0.06), (s * ax, ay + 0.04, az - 0.06),
            0.10, 0.22)
    hp.build(MAT["timber"], C_ROF)

    dr = MB("ROF_Aisle_Drip_Edge")
    for s in (-1, 1):
        y0 = s * iy + (-0.18 if s < 0 else 0.0)
        dr.box(-ix - 0.02, ix + 0.02, y0, y0 + 0.18, AISLE_TOP_Z - 0.02,
               AISLE_TOP_Z + 0.15, (1, 1, 1))
    dr.build(MAT["tar"], C_ROF)


def build_nave_roof():
    sh = MB("ROF_Nave_Shingles")
    dk = MB("ROF_Nave_Deck")
    ex, ez = NAVE_EAVE_X, NAVE_EAVE_Z
    oy = 5.12          # west: bargeboard overhang past the gable wall
    oy_e = 4.66        # east: roof butts the chancel, so no overhang slot
    for s in (-1, 1):
        shingle_plane(sh, dk, (s * ex, -oy, ez), (s * ex, oy_e, ez),
                      (0.0, -oy, RIDGE_Z), (0.0, oy_e, RIDGE_Z),
                      0.340, 0.235, (1, 1, 1), thick=0.024, deck=0.14)
    sh.build(MAT["shingle"], C_ROF)
    dk.build(MAT["soffit"], C_ROF)

    b = MB("ROF_Nave_Trim")
    for sy, yy in ((-1, -oy), (1, oy_e)):
        for sx in (-1, 1):
            bar(b, (sx * (ex + 0.03), yy, ez),
                (0.0, yy, RIDGE_Z + 0.06), 0.10, 0.19)
    bar(b, (0.0, -oy - 0.12, RIDGE_Z + 0.02), (0.0, oy_e + 0.06, RIDGE_Z + 0.02),
        0.20, 0.22)
    b.build(MAT["timber"], C_ROF)

    fc = MB("ROF_Nave_Fascia")          # eave board: tarred, reads dark
    for s in (-1, 1):
        bar(fc, (s * ex, -oy, ez - 0.07), (s * ex, oy_e, ez - 0.07), 0.09, 0.24,
            (1, 1, 1))
    fc.build(MAT["tar"], C_ROF)


def build_chancel():
    mb = MB("CHN_Walls")
    mb.box(-CH_HX, CH_HX, CH_Y0 - 0.10, CH_Y1, Z_DECK, CH_EAVE, (0.9, 0.9, 0.9))
    fr = Frame((0, CH_Y1, 0), (1, 0, 0), (0, 0, 1))
    gab = [(-CH_HX, Z_DECK), (CH_HX, Z_DECK), (CH_HX, CH_EAVE),
           (0.0, CH_RIDGE), (-CH_HX, CH_EAVE)]
    mb.prism(fr, gab, -0.28, 0.0, (0.88, 0.88, 0.88))
    mb.build(MAT["tar"], C_CHN)

    bd = MB("CHN_Clad_Boards")
    frb = Frame((0, CH_Y1 + 0.015, 0), (-1, 0, 0), (0, 0, 1))
    plank_clad(bd, frb, [(-CH_HX, Z_DECK), (CH_HX, Z_DECK), (CH_HX, CH_EAVE),
                         (0.0, CH_RIDGE), (-CH_HX, CH_EAVE)],
               0.16, 0.04, (1, 1, 1), gap=0.009)
    frs = Frame((CH_HX + 0.015, 0, 0), (0, 1, 0), (0, 0, 1))
    plank_clad(bd, frs, [(CH_Y0, Z_DECK), (CH_Y1, Z_DECK), (CH_Y1, CH_EAVE),
                         (CH_Y0, CH_EAVE)], 0.16, 0.04, (1, 1, 1), gap=0.009)
    frs2 = Frame((-CH_HX - 0.015, 0, 0), (0, -1, 0), (0, 0, 1))
    plank_clad(bd, frs2, [(-CH_Y1, Z_DECK), (-CH_Y0, Z_DECK), (-CH_Y0, CH_EAVE),
                          (-CH_Y1, CH_EAVE)], 0.16, 0.04, (1, 1, 1), gap=0.009)
    bd.build(MAT["board"], C_CHN)

    sh = MB("ROF_Chancel_Shingles")
    dk = MB("ROF_Chancel_Deck")
    for s in (-1, 1):
        shingle_plane(sh, dk,
                      (s * (CH_HX + 0.06), CH_Y0 - 0.45, CH_EAVE - 0.04),
                      (s * (CH_HX + 0.06), CH_Y1 + 0.48, CH_EAVE - 0.04),
                      (0.0, CH_Y0 - 0.45, CH_RIDGE), (0.0, CH_Y1 + 0.48, CH_RIDGE),
                      0.295, 0.205, (1, 1, 1), thick=0.022, deck=0.12)
    sh.build(MAT["shingle"], C_ROF)
    dk.build(MAT["soffit"], C_ROF)

    sh2 = MB("ROF_Chancel_Skirt_Shingles")
    dk2 = MB("ROF_Chancel_Skirt_Deck")
    ox, oy2, oz2 = 3.72, CH_Y1 + 0.34, 3.46
    for s in (-1, 1):
        shingle_plane(sh2, dk2,
                      (s * ox, 6.95, oz2), (s * ox, oy2, oz2),
                      (s * (CH_HX + 0.02), 6.95, 4.46),
                      (s * (CH_HX + 0.02), oy2, 4.46),
                      0.250, 0.175, (1, 1, 1), thick=0.022, deck=0.10)
        if s > 0:
            shingle_plane(sh2, dk2,
                          (-ox, oy2, oz2), (ox, oy2, oz2),
                          (-CH_HX, oy2, 4.46), (CH_HX, oy2, 4.46),
                          0.250, 0.175, (1, 1, 1), thick=0.022, deck=0.10)
    sh2.build(MAT["shingle"], C_ROF)
    dk2.build(MAT["soffit"], C_ROF)

    tr = MB("CHN_Trim")
    for s in (-1, 1):
        bar(tr, (s * (CH_HX + 0.10), CH_Y0 - 0.45, CH_EAVE),
            (0.0, CH_Y0 - 0.45, CH_RIDGE + 0.05), 0.09, 0.22)
        bar(tr, (s * (CH_HX + 0.10), CH_Y1 + 0.48, CH_EAVE),
            (0.0, CH_Y1 + 0.48, CH_RIDGE + 0.05), 0.09, 0.22)
    tr.build(MAT["timber"], C_ROF)

    build_window(0.0, CH_Y1 + 0.01, 6.75, 0.50, 1.10, "CHN_Win_East", facing=1)
    build_window(CH_HX + 0.01, 7.95, 4.05, 0.44, 0.90, "CHN_Win_South", facing=2)


# --------------------------------------------------------------------------- #
#  6. tower
# --------------------------------------------------------------------------- #
def build_tower():
    t = 0.20
    x0, x1 = -TOW_HX, TOW_HX
    y0, y1 = TOW_Y0, TOW_Y1
    mb = MB("TOW_Belfry_Body")
    mb.box(x0, x1, y0, y0 + t, TOW_Z0, TOW_Z1, (0.92, 0.92, 0.92))
    mb.box(x0, x1, y1 - t, y1, TOW_Z0, TOW_Z1, (0.88, 0.88, 0.88))
    mb.box(x0, x0 + t, y0, y1, TOW_Z0, TOW_Z1, (0.95, 0.95, 0.95))
    mb.box(x1 - t, x1, y0, y1, TOW_Z0, TOW_Z1, (0.95, 0.95, 0.95))
    mb.build(MAT["tar"], C_TOW)

    cl = MB("TOW_Cladding_Horizontal")
    faces = [
        (Frame((0, y0, 0), (1, 0, 0), (0, 0, 1)), (x0, x1)),
        (Frame((0, y1, 0), (-1, 0, 0), (0, 0, 1)), (-x1, -x0)),
        (Frame((x0, 0, 0), (0, -1, 0), (0, 0, 1)), (-y1, -y0)),
        (Frame((x1, 0, 0), (0, 1, 0), (0, 0, 1)), (y0, y1)),
    ]
    for fr, (a, b) in faces:
        horizontal_clad(cl, fr, [(a, TOW_Z0), (b, TOW_Z0), (b, TOW_Z1),
                                 (a, TOW_Z1)], 0.150, 0.024, (1, 1, 1),
                        gap=0.009)
    cl.build(MAT["board"], C_TOW)

    cb = MB("TOW_Corner_Boards")
    for (px, py) in ((-TOW_HX, y0), (TOW_HX, y0), (-TOW_HX, y1), (TOW_HX, y1)):
        bar(cb, (px, py, TOW_Z0 + 1.2), (px, py, TOW_Z1 + 0.04), 0.105, 0.105,
            (1.12, 1.10, 1.03))
    cb.build(MAT["timber"], C_TOW)

    # louvred bell openings, standing proud of the cladding
    op = MB("TOW_Bell_Openings")
    zc = 13.55
    ow, oh = 0.46, 0.52
    faces_op = [
        ((0.0, y0, zc), (1, 0, 0)),
        ((0.0, y1, zc), (-1, 0, 0)),
        ((x0, (y0 + y1) * 0.5, zc), (0, 1, 0)),
        ((x1, (y0 + y1) * 0.5, zc), (0, -1, 0)),
    ]
    for (org, u) in faces_op:
        fr = Frame(org, u, (0, 0, 1))
        op.prism(fr, [(-ow, -oh), (ow, -oh), (ow, oh), (-ow, oh)],
                 0.010, 0.030, (0.28, 0.26, 0.24))
        for i in range(6):
            uu = -ow + 0.09 + i * 0.155
            op.prism(fr, [(uu, -oh + 0.03), (uu + 0.085, -oh + 0.03),
                          (uu + 0.085, oh - 0.03), (uu, oh - 0.03)],
                     0.030, 0.072, (0.9, 0.88, 0.85))
        # frame
        op.prism(fr, [(-ow - 0.09, -oh - 0.09), (ow + 0.09, -oh - 0.09),
                      (ow + 0.09, -oh), (-ow - 0.09, -oh)],
                 0.005, 0.105, (1.15, 1.12, 1.05))
        op.prism(fr, [(-ow - 0.09, oh), (ow + 0.09, oh),
                      (ow + 0.09, oh + 0.09), (-ow - 0.09, oh + 0.09)],
                 0.005, 0.105, (1.15, 1.12, 1.05))
        for sx in (-1, 1):
            op.prism(fr, [(sx * ow, -oh), (sx * (ow + 0.09), -oh),
                          (sx * (ow + 0.09), oh), (sx * ow, oh)],
                     0.005, 0.105, (1.15, 1.12, 1.05))
    op.build(MAT["timber"], C_TOW)

    # ---- spire: square pyramid rotated 45 deg, bell-cast profile ----------
    # the spire must stand on the belfry axis, not on the world origin
    TCX, TCY = 0.0, 0.5 * (TOW_Y0 + TOW_Y1)
    n_lev = 30
    levels = []
    flare_h = 0.95
    r_flare_top = SPIRE_R - 0.055 * SPIRE_R
    for i in range(n_lev + 1):
        t_ = i / n_lev
        z = SPIRE_Z0 + (SPIRE_Z1 - SPIRE_Z0) * t_
        if z < SPIRE_Z0 + flare_h:
            u = (z - SPIRE_Z0) / flare_h
            r = SPIRE_R + (r_flare_top - SPIRE_R) * (u ** 1.8)   # concave bell
        else:
            r = r_flare_top * \
                ((SPIRE_Z1 - z) / (SPIRE_Z1 - SPIRE_Z0 - flare_h)) ** 1.12
        levels.append((z, max(r, 0.009)))

    sh = MB("TOW_Spire_Shingles")
    dk = MB("TOW_Spire_Sheathing")
    for i in range(len(levels) - 1):
        z0, r0 = levels[i]
        z1, r1 = levels[i + 1]
        for k in range(4):
            a0 = math.radians(90 * k)
            a1 = a0 + math.radians(90)
            p0 = Vector((TCX + r0 * math.cos(a0), TCY + r0 * math.sin(a0), z0))
            p1 = Vector((TCX + r0 * math.cos(a1), TCY + r0 * math.sin(a1), z0))
            p3 = Vector((TCX + r1 * math.cos(a0), TCY + r1 * math.sin(a0), z1))
            L = (p1 - p0).length
            H = (p3 - p0).length
            if L < 1e-4 or H < 1e-4:
                continue
            fr = Frame(p0, p1 - p0, p3 - p0)
            dk.prism(fr, [(0, 0), (L, 0), (L, H), (0, H)], -0.055, 0.0,
                     (1, 1, 1))
            # one clapboard course per band, full width, tucked under the one above
            sh.prism(fr, [(0.004, 0.004), (L - 0.004, 0.004),
                          (L - 0.004, H * 0.885), (0.004, H * 0.885)],
                     0.002 + i * 0.0011, 0.034, _tint((1, 1, 1), rng, 0.72, 1.28))
    sh.build(MAT["shingle"], C_ROF)
    dk.build(MAT["tar"], C_ROF)

    rib = MB("TOW_Spire_Hip_Ribs")
    for k in range(4):
        a = math.radians(90 * k)
        ca, sa = math.cos(a), math.sin(a)
        lat = Vector((-sa, ca, 0.0))
        A, B = [], []
        for (z, r) in levels:
            base = Vector((TCX + r * ca, TCY + r * sa, z + 0.030)) + \
                Vector((ca, sa, 0.0)) * 0.052
            A.append(base + lat * 0.130)
            B.append(base - lat * 0.130)
        strip_solid(rib, A, B, Vector((ca, sa, 0.22)).normalized(), 0.085,
                    (1.26, 1.23, 1.14))
    for k in range(4):
        a0 = math.radians(90 * k)
        a1 = a0 + math.radians(90)
        r = levels[0][1] + 0.03
        bar(rib, (TCX + r * math.cos(a0), TCY + r * math.sin(a0),
                  levels[0][0] - 0.04),
            (TCX + r * math.cos(a1), TCY + r * math.sin(a1),
             levels[0][0] - 0.04),
            0.075, 0.26, (1, 1, 1))
    rib.build(MAT["timber"], C_TOW)

    # ---- skirt: caps the belfry and closes the overhang under the flare ---
    sk = MB("TOW_Spire_Skirt")
    r_sk = levels[0][1] + 0.03
    # eave plate: a solid timber cornice that seals the belfry top and
    # carries the four corners of the flare.  Deep enough to read as a
    # boarded cornice, not as a thin blade.
    sk.box(-TOW_HX - 0.04, TOW_HX + 0.04, TOW_Y0 - 0.04, TOW_Y1 + 0.04,
           SPIRE_Z0 - 0.21, SPIRE_Z0 - 0.05, (0.90, 0.88, 0.86))
    fr0 = Frame((TCX, TCY, 0.0), (1, 0, 0), (0, 1, 0))
    dia = [(r_sk - 0.01, 0.0), (0.0, r_sk - 0.01),
           (-r_sk + 0.01, 0.0), (0.0, -r_sk + 0.01)]
    sk.prism(fr0, ccw(dia), SPIRE_Z0 - 0.150, SPIRE_Z0 + 0.008, (0.94, 0.92, 0.90))
    # boarded valance, proud of the plate edge so no thin lip shows
    for k in range(4):
        a0 = math.radians(90 * k)
        a1 = a0 + math.radians(90)
        pa = (TCX + r_sk * math.cos(a0), TCY + r_sk * math.sin(a0))
        pb = (TCX + r_sk * math.cos(a1), TCY + r_sk * math.sin(a1))
        bar(sk, (pa[0], pa[1], SPIRE_Z0 - 0.17), (pb[0], pb[1], SPIRE_Z0 - 0.17),
            0.075, 0.36, (0.88 + 0.06 * (k % 2), 0.86, 0.82))
    sk.build(MAT["tar"], C_TOW)

    prof = [(0.0, 0.0), (0.075, 0.0), (0.075, 0.10), (0.050, 0.14),
            (0.085, 0.20), (0.095, 0.28), (0.070, 0.38), (0.045, 0.44),
            (0.060, 0.50), (0.060, 0.56), (0.030, 0.60), (0.028, 0.74),
            (0.055, 0.80), (0.050, 0.84), (0.012, 0.90), (0.0, 0.94)]
    lathe_object("TOW_Finial_Shaft", prof, MAT["timber"], C_TOW, segments=18,
                 location=(TCX, TCY, SPIRE_Z1 - 0.04))
    cr = MB("TOW_Finial_Cross")
    z = SPIRE_Z1 + 0.58
    bar(cr, (TCX, TCY, z), (TCX, TCY, z + 0.50), 0.032, 0.032)
    bar(cr, (TCX - 0.14, TCY, z + 0.34), (TCX + 0.14, TCY, z + 0.34),
        0.028, 0.028)
    cr.build(MAT["iron"], C_TOW)


# --------------------------------------------------------------------------- #
#  7. site
# --------------------------------------------------------------------------- #
def build_site():
    mb = MB("SITE_Ground")
    mb.box(-70, 70, -70, 70, -0.6, 0.0, (1, 1, 1))
    mb.build(MAT["grass"], C_SITE)

    gs = MB("SITE_Gravestones")
    for (x, y, w, h, rot) in ((-3.9, -11.0, 0.55, 1.0, 0.10),
                              (-2.3, -10.3, 0.42, 0.55, -0.20),
                              (4.7, -11.8, 0.62, 1.15, 0.02),
                              (6.3, -9.2, 0.50, 0.75, 0.30),
                              (-6.6, -12.6, 0.48, 0.62, -0.12)):
        gs.obox((x, y, h * 0.5 - 0.02), (w, 0.13, h), rz=rot, tint=(1, 1, 1))
        gs.obox((x, y, h * 0.5 + 0.02), (w * 0.92, 0.03, h * 0.95), rz=rot,
                tint=(1.06, 1.06, 1.02))
    gs.build(MAT["stone"], C_SITE)


# --------------------------------------------------------------------------- #
#  build
# --------------------------------------------------------------------------- #
build_foundation()
build_gallery()
build_porch()
build_nave()
build_aisle_roof()
build_nave_roof()
build_chancel()
build_tower()
build_site()


# --------------------------------------------------------------------------- #
#  world, lights, cameras, render
# --------------------------------------------------------------------------- #
def setup_world():
    w = bpy.data.worlds.new("WRLD_Overcast")
    scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.location = (400, 0)
    out.location = (620, 0)
    nt.links.new(bg.outputs[0], out.inputs["Surface"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    tc.location = (-800, 0)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    sep.location = (-600, 0)
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.location = (-420, 0)
    mr.inputs["From Min"].default_value = -1.0
    mr.inputs["From Max"].default_value = 1.0
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.location = (-220, 0)
    ramp.color_ramp.elements[0].position = 0.42
    ramp.color_ramp.elements[0].color = (0.95, 0.96, 0.97, 1)
    ramp.color_ramp.elements[1].position = 0.95
    ramp.color_ramp.elements[1].color = (0.60, 0.68, 0.80, 1)
    nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 1.55


def setup_lights():
    sun_d = bpy.data.lights.new("LGT_Sun_Soft", 'SUN')
    sun_d.energy = 3.4
    sun_d.angle = math.radians(22)
    sun_d.color = (1.0, 0.98, 0.95)
    sun = bpy.data.objects.new("LGT_Sun_Soft", sun_d)
    C_CAM.objects.link(sun)
    sun.rotation_euler = (math.radians(54), 0, math.radians(-46))

    fill_d = bpy.data.lights.new("LGT_Fill_Front", 'AREA')
    fill_d.energy = 14000
    fill_d.size = 16
    fill_d.color = (0.86, 0.90, 1.0)
    fill = bpy.data.objects.new("LGT_Fill_Front", fill_d)
    fill.location = (-14, -26, 12)
    C_CAM.objects.link(fill)
    d = Vector((0, 0, 7)) - fill.location
    fill.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()

    rim_d = bpy.data.lights.new("LGT_Rim_East", 'AREA')
    rim_d.energy = 4000
    rim_d.size = 14
    rim_d.color = (0.90, 0.93, 1.0)
    rim = bpy.data.objects.new("LGT_Rim_East", rim_d)
    rim.location = (18, 26, 14)
    C_CAM.objects.link(rim)
    d = Vector((0, 0, 8)) - rim.location
    rim.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()


def add_camera(name, loc, target, lens=50.0):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cam = bpy.data.objects.new(name, cd)
    cam.location = loc
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    C_CAM.objects.link(cam)
    return cam


def setup_cameras():
    cams = {}
    cams["front"] = add_camera("CAM_01_West_Front", (0, -33.0, 1.60),
                               (0, -1.0, 10.5), lens=50)
    cams["hero"] = add_camera("CAM_02_Three_Quarter", (-17.8, -29.5, 4.0),
                              (0.6, 1.0, 9.7), lens=38)
    cams["side"] = add_camera("CAM_03_South_East", (26.0, 22.0, 7.0),
                              (0, 1.0, 7.0), lens=45)
    cams["detail"] = add_camera("CAM_04_Tower_Detail", (-6.0, -15.5, 13.6),
                                (0, -3.0, 17.2), lens=70)
    return cams


def setup_render():
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 32 if QUICK else 160
    scene.cycles.use_denoising = True
    try:
        scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    except Exception:
        pass
    scene.cycles.max_bounces = 8
    scene.cycles.diffuse_bounces = 4
    scene.cycles.glossy_bounces = 3
    scene.cycles.transmission_bounces = 4
    try:
        scene.cycles.use_adaptive_sampling = True
        scene.cycles.adaptive_threshold = 0.02
    except Exception:
        pass
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = 'AgX'
    try:
        scene.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass
    scene.view_settings.exposure = 0.32
    scene.render.resolution_percentage = 60 if QUICK else 100
    scene.render.threads_mode = 'AUTO'


setup_world()
setup_lights()
CAMS = setup_cameras()
setup_render()

# cameras / lights are excluded from the geometry stats below
n_obj = len([o for o in scene.objects if o.type == 'MESH'])
n_tri = sum(len(o.data.polygons) for o in scene.objects if o.type == 'MESH')
print("URNES: %d mesh objects, %d faces" % (n_obj, n_tri))

# --------------------------------------------------------------------------- #
#  save
# --------------------------------------------------------------------------- #
scene.camera = CAMS["front"]
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("URNES: saved", BLEND_PATH)

# --------------------------------------------------------------------------- #
#  renders
# --------------------------------------------------------------------------- #
if QUICK:
    scene.camera = CAMS["hero"]
    scene.render.resolution_x, scene.render.resolution_y = 900, 700
    scene.render.filepath = os.path.join(RENDER_DIR, "preview_hero.png")
    bpy.ops.render.render(write_still=True)
    print("URNES: preview written")
else:
    jobs = [("front", 1300, 1730), ("hero", 1700, 1275),
            ("side", 1500, 1100), ("detail", 1100, 1250)]
    for key, rx, ry in jobs:
        scene.camera = CAMS[key]
        scene.render.resolution_x = rx
        scene.render.resolution_y = ry
        scene.render.filepath = os.path.join(RENDER_DIR, "render_%s.png" % key)
        bpy.ops.render.render(write_still=True)
        print("URNES: rendered", key)
print("URNES: done")
