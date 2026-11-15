# -*- coding: utf-8 -*-
"""
urnes_lib.py -- shared helpers for the Urnes Stave Church procedural build.

Contents
--------
* MB            : mesh accumulator (verts / faces / per-face tint)
* Frame         : local 2D->3D planar coordinate system
* clip_poly     : Sutherland-Hodgman convex clipping
* revolve       : lathe surface from a 2D profile
* material lib  : procedural PBR node groups (no image textures)
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

# --------------------------------------------------------------------------- #
#  mesh accumulator
# --------------------------------------------------------------------------- #
class MB:
    """Accumulates geometry for one logical object, with a per-face tint used
    by the shaders to break up large repeating surfaces."""

    __slots__ = ("name", "v", "f", "c")

    def __init__(self, name="mesh"):
        self.name = name
        self.v = []
        self.f = []
        self.c = []

    # -- low level ---------------------------------------------------------- #
    def vert(self, p):
        self.v.append((p[0], p[1], p[2]))
        return len(self.v) - 1

    def face(self, idxs, tint=(1.0, 1.0, 1.0)):
        self.f.append(tuple(idxs))
        self.c.append(tint)

    def poly(self, pts, tint=(1.0, 1.0, 1.0)):
        i0 = len(self.v)
        for p in pts:
            self.v.append((p[0], p[1], p[2]))
        self.f.append(tuple(range(i0, i0 + len(pts))))
        self.c.append(tint)

    # -- solids ------------------------------------------------------------- #
    def quad_solid(self, a, b, c, d, n, thick, tint):
        """closed slab from a planar quad (a,b,c,d) extruded along n."""
        n = Vector(n).normalized()
        off = n * thick
        pa = [Vector(p) for p in (a, b, c, d)]
        top = [p + off for p in pa]
        self.poly(pa, tint)          # bottom
        self.poly(list(reversed(top)), tint)
        for i in range(4):
            j = (i + 1) % 4
            self.poly([pa[i], pa[j], top[j], top[i]], tint)

    def prism(self, fr, poly2d, z0, z1, tint):
        """closed prism from a convex 2D polygon in a Frame, between z0..z1."""
        poly2d = ccw(poly2d)
        if len(poly2d) < 3 or abs(area2(poly2d)) < 1e-7:
            return
        n = len(poly2d)
        bot = [fr.p(u, v, z0) for (u, v) in poly2d]
        top = [fr.p(u, v, z1) for (u, v) in poly2d]
        self.poly(top, tint)
        self.poly(list(reversed(bot)), tint)
        for i in range(n):
            j = (i + 1) % n
            self.poly([bot[i], bot[j], top[j], top[i]], tint)

    def box(self, x0, x1, y0, y1, z0, z1, tint):
        p = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        idx = [self.vert(q) for q in p]
        v0, v1, v2, v3, v4, v5, v6, v7 = idx
        for f in ((v0, v3, v2, v1), (v4, v5, v6, v7), (v0, v1, v5, v4),
                  (v1, v2, v6, v5), (v2, v3, v7, v6), (v3, v0, v4, v7)):
            self.face(f, tint)

    def obox(self, centre, size, ry=0.0, tint=(1, 1, 1), rz=0.0):
        """oriented box: centre, (sx,sy,sz), optional z/y rotation."""
        cx, cy, cz = centre
        sx, sy, sz = size
        pts = []
        for dz in (-0.5, 0.5):
            for dy in (-0.5, 0.5):
                for dx in (-0.5, 0.5):
                    pts.append(Vector((dx * sx, dy * sy, dz * sz)))
        m = Matrix.Rotation(rz, 3, 'Z') @ Matrix.Rotation(ry, 3, 'Y')
        pts = [m @ p + Vector((cx, cy, cz)) for p in pts]
        # order: 0(-x-y-z) 1(+x-y-z) 2(-x+y-z) 3(+x+y-z)
        #        4(-x-y+z) 5(+x-y+z) 6(-x+y+z) 7(+x+y+z)
        idx = [self.vert(p) for p in pts]
        for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
                  (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
            self.face([idx[i] for i in f], tint)

    # -- output ------------------------------------------------------------- #
    def build(self, material, collection, smooth=False, recalc=True):
        if not self.f:
            return None                      # nothing generated: skip the object
        me = bpy.data.meshes.new(self.name)
        me.from_pydata(self.v, [], self.f)
        me.validate(verbose=False)

        # per-face tint -> corner colour attribute
        col = me.color_attributes.new("tint", 'FLOAT_COLOR', 'CORNER')
        flat = []
        for poly, tint in zip(me.polygons, self.c[:len(me.polygons)]):
            for _ in range(poly.loop_total):
                flat.extend((tint[0], tint[1], tint[2], 1.0))
        if len(flat) == len(col.data) * 4:
            col.data.foreach_set("color", flat)

        ob = bpy.data.objects.new(self.name, me)
        collection.objects.link(ob)
        if material is not None:
            me.materials.append(material)
        if smooth:
            for p in me.polygons:
                p.use_smooth = True

        if recalc:
            bm = bmesh.new()
            bm.from_mesh(me)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            bm.to_mesh(me)
            bm.free()
        return ob


# --------------------------------------------------------------------------- #
#  2D helpers
# --------------------------------------------------------------------------- #
def area2(poly):
    a = 0.0
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return a * 0.5


def ccw(poly):
    return poly if area2(poly) >= 0 else list(reversed(poly))


def clip_poly(subject, clip):
    """Sutherland-Hodgman against a *convex* clip polygon."""
    clip = ccw(clip)

    def inside(p, a, b):
        return ((b[0] - a[0]) * (p[1] - a[1]) -
                (b[1] - a[1]) * (p[0] - a[0])) >= -1e-9

    def inter(p1, p2, a, b):
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = a
        x4, y4 = b
        d = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(d) < 1e-12:
            return p1
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / d
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))

    out = list(subject)
    for i in range(len(clip)):
        a, b = clip[i], clip[(i + 1) % len(clip)]
        if not out:
            return []
        src, out = out, []
        s = src[-1]
        for e in src:
            if inside(e, a, b):
                if not inside(s, a, b):
                    out.append(inter(s, e, a, b))
                out.append(e)
            elif inside(s, a, b):
                out.append(inter(s, e, a, b))
            s = e
    return out


class Frame:
    """Planar frame: p(u,v,w) = origin + u*U + v*V + w*N."""

    __slots__ = ("o", "U", "V", "N")

    def __init__(self, origin, u, v):
        self.o = Vector(origin)
        self.U = Vector(u).normalized()
        vv = Vector(v)
        vv = vv - self.U * vv.dot(self.U)
        self.V = vv.normalized()
        self.N = self.U.cross(self.V)

    @property
    def up(self):
        """normal pointing away from the model interior (roughly +Z)."""
        return self.N if self.N.z >= 0 else -self.N

    def p(self, u, v, w=0.0):
        return self.o + self.U * u + self.V * v + self.N * w



def strip_solid(mb, A, B, normal, thick, tint, cap=True):
    """Closed slab between two parallel polylines A[i]..B[i], extruded
    backwards along `normal` by `thick`.  Used for hip ribs, barge boards."""
    n = Vector(normal).normalized()
    nA, nB = len(A), len(B)
    if nA < 2 or nB != nA:
        return
    base = [Vector(p) for p in A]
    top = [Vector(p) for p in B]
    low_a = [p - n * thick for p in base]
    low_b = [p - n * thick for p in top]
    ia = [mb.vert(p) for p in base]
    ib = [mb.vert(p) for p in top]
    ja = [mb.vert(p) for p in low_a]
    jb = [mb.vert(p) for p in low_b]
    for i in range(nA - 1):
        mb.face((ia[i], ia[i + 1], ib[i + 1], ib[i]), tint)          # outer
        mb.face((ja[i], jb[i], jb[i + 1], ja[i + 1]), tint)          # inner
        mb.face((ia[i], ja[i], ja[i + 1], ia[i + 1]), tint)          # side A
        mb.face((ib[i], ib[i + 1], jb[i + 1], jb[i]), tint)          # side B
    if cap:
        mb.face((ia[0], ib[0], jb[0], ja[0]), tint)
        mb.face((ia[-1], ja[-1], jb[-1], ib[-1]), tint)


def revolve(profile, segments=32, axis='Z'):
    """profile: [(r, z), ...] -> (verts, faces) lathe around +Z."""
    verts, faces = [], []
    for (r, z) in profile:
        for i in range(segments):
            a = 2.0 * math.pi * i / segments
            verts.append((r * math.cos(a), r * math.sin(a), z))
    n = len(profile)
    for k in range(n - 1):
        for i in range(segments):
            j = (i + 1) % segments
            a = k * segments + i
            b = k * segments + j
            c = (k + 1) * segments + j
            d = (k + 1) * segments + i
            faces.append((a, b, c, d))
    return verts, faces


def ensure_tint(me, tint=(1.0, 1.0, 1.0)):
    """White 'tint' colour attribute so shaders that read it are not black."""
    if "tint" in [a.name for a in me.color_attributes]:
        return
    col = me.color_attributes.new("tint", 'FLOAT_COLOR', 'CORNER')
    n = len(me.loops)
    flat = []
    for _ in range(n):
        flat.extend((tint[0], tint[1], tint[2], 1.0))
    col.data.foreach_set("color", flat)


def lathe_object(name, profile, material, collection, segments=28,
                 location=(0, 0, 0), smooth=True):
    verts, faces = revolve(profile, segments)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    ensure_tint(me)
    ob = bpy.data.objects.new(name, me)
    ob.location = location
    collection.objects.link(ob)
    me.materials.append(material)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    return ob


# --------------------------------------------------------------------------- #
#  shaders
# --------------------------------------------------------------------------- #
def _set(node, name, value):
    if name in node.inputs:
        try:
            node.inputs[name].default_value = value
            return True
        except Exception:
            pass
    return False


def _mix_rgb(nt, a, b):
    n = nt.nodes.new("ShaderNodeMix")
    n.data_type = 'RGBA'
    n.blend_type = 'MIX'
    return n


def make_wood(name, base, dark, rough=0.62, grain=(8.0, 8.0, 60.0),
              plank=None, bump=0.45, tint_mul=0.35, sheen=0.0,
              mossy=0.0, spec=0.35):
    """Procedural weathered timber.

    base/dark : linear RGB of the lit / shadowed grain
    grain     : object-space frequency of (across, across, along) grain
    plank     : None, or (width, seam_darkness) to cut vertical plank seams
    tint_mul  : how strongly the per-face 'tint' attribute drives value
    mossy     : amount of green-grey lichen mottling
    """
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (900, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (620, 0)
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])

    tex = nt.nodes.new("ShaderNodeTexCoord")
    tex.location = (-1150, 0)

    mp = nt.nodes.new("ShaderNodeMapping")
    mp.location = (-960, 0)
    mp.inputs["Scale"].default_value = grain
    nt.links.new(tex.outputs["Object"], mp.inputs["Vector"])

    # long fibre grain
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.location = (-760, 120)
    wave.wave_type = 'BANDS'
    wave.bands_direction = 'Z'
    wave.wave_profile = 'SIN'
    wave.inputs["Scale"].default_value = 1.0
    wave.inputs["Distortion"].default_value = 14.0
    wave.inputs["Detail"].default_value = 3.0
    wave.inputs["Detail Scale"].default_value = 2.0
    nt.links.new(mp.outputs["Vector"], wave.inputs["Vector"])

    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.location = (-560, 120)
    ramp.color_ramp.elements[0].position = 0.28
    ramp.color_ramp.elements[1].position = 0.78
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])

    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = 'RGBA'
    mix.location = (-330, 60)
    mix.inputs[6].default_value = (base[0], base[1], base[2], 1.0)
    mix.inputs[7].default_value = (dark[0], dark[1], dark[2], 1.0)
    nt.links.new(ramp.outputs["Color"], mix.inputs[0])

    # large scale weathering / value drift
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.location = (-760, -170)
    nz.inputs["Scale"].default_value = 0.55
    nz.inputs["Detail"].default_value = 6.0
    nz.inputs["Roughness"].default_value = 0.62
    nt.links.new(tex.outputs["Object"], nz.inputs["Vector"])

    wobble = nt.nodes.new("ShaderNodeValToRGB")
    wobble.location = (-560, -170)
    wobble.color_ramp.elements[0].position = 0.34
    wobble.color_ramp.elements[0].color = (1 - tint_mul, 1 - tint_mul, 1 - tint_mul * 1.1, 1)
    wobble.color_ramp.elements[1].position = 0.78
    nt.links.new(nz.outputs["Fac"], wobble.inputs["Fac"])

    def mulcol(a_socket, b_socket, loc, fac=1.0):
        n = nt.nodes.new("ShaderNodeMix")
        n.data_type = 'RGBA'
        n.blend_type = 'MULTIPLY'
        n.location = loc
        n.inputs[0].default_value = fac
        if a_socket is not None:
            nt.links.new(a_socket, n.inputs[6])
        if b_socket is not None:
            nt.links.new(b_socket, n.inputs[7])
        return n

    chain = mulcol(mix.outputs[2], wobble.outputs["Color"], (-120, 60))

    # per-face tint -> value variation between identical boards / stones
    try:
        attr = nt.nodes.new("ShaderNodeVertexColor")
        attr.layer_name = "tint"
    except Exception:
        attr = nt.nodes.new("ShaderNodeAttribute")
        attr.attribute_name = "tint"
    attr.location = (-330, -300)
    chain = mulcol(chain.outputs[2], attr.outputs["Color"], (60, 60))

    # lichen / moss mottle
    lich = None
    if mossy > 0.0:
        lich = nt.nodes.new("ShaderNodeTexNoise")
        lich.location = (-760, -470)
        lich.inputs["Scale"].default_value = 7.0
        lich.inputs["Detail"].default_value = 5.0
        nt.links.new(tex.outputs["Object"], lich.inputs["Vector"])
        lichr = nt.nodes.new("ShaderNodeValToRGB")
        lichr.location = (-560, -470)
        lichr.color_ramp.elements[0].position = 0.50
        lichr.color_ramp.elements[0].color = (0.60, 0.68, 0.55, 1)
        lichr.color_ramp.elements[1].position = 0.68
        lichr.color_ramp.elements[1].color = (1, 1, 1, 1)
        nt.links.new(lich.outputs["Fac"], lichr.inputs["Fac"])
        chain = mulcol(chain.outputs[2], lichr.outputs["Color"], (220, 60), mossy)

    # vertical plank seams
    if plank is not None:
        width, seam = plank
        pw = nt.nodes.new("ShaderNodeTexWave")
        pw.location = (-760, 400)
        pw.wave_type = 'BANDS'
        pw.bands_direction = 'X'
        pw.wave_profile = 'SAW'
        pw.inputs["Scale"].default_value = 1.0
        pw.inputs["Distortion"].default_value = 0.0
        mpw = nt.nodes.new("ShaderNodeMapping")
        mpw.location = (-960, 400)
        mpw.inputs["Scale"].default_value = (1.0 / width, 1.0, 1.0)
        nt.links.new(tex.outputs["Object"], mpw.inputs["Vector"])
        nt.links.new(mpw.outputs["Vector"], pw.inputs["Vector"])
        sr = nt.nodes.new("ShaderNodeValToRGB")
        sr.location = (-560, 400)
        sr.color_ramp.elements[0].position = 0.88
        sr.color_ramp.elements[0].color = (1 - seam, 1 - seam, 1 - seam, 1)
        sr.color_ramp.elements[1].position = 0.965
        sr.color_ramp.elements[1].color = (1, 1, 1, 1)
        nt.links.new(pw.outputs["Fac"], sr.inputs["Fac"])
        chain = mulcol(chain.outputs[2], sr.outputs["Color"], (380, 60))

    nt.links.new(chain.outputs[2], bsdf.inputs["Base Color"])

    # roughness variation
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.location = (420, -200)
    rr.inputs["From Min"].default_value = 0.0
    rr.inputs["From Max"].default_value = 1.0
    rr.inputs["To Min"].default_value = rough - 0.12
    rr.inputs["To Max"].default_value = rough + 0.12
    nt.links.new(nz.outputs["Fac"], rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], bsdf.inputs["Roughness"])

    _set(bsdf, "Specular IOR Level", spec)
    _set(bsdf, "Sheen Weight", sheen)

    # micro relief: grain + plank seams
    bmp = nt.nodes.new("ShaderNodeBump")
    bmp.location = (420, -470)
    bmp.inputs["Strength"].default_value = bump
    bmp.inputs["Distance"].default_value = 0.02
    nt.links.new(nz.outputs["Fac"], bmp.inputs["Height"])

    if plank is not None:
        bump2 = nt.nodes.new("ShaderNodeBump")
        bump2.location = (600, -470)
        bump2.inputs["Strength"].default_value = 0.6
        bump2.inputs["Distance"].default_value = 0.012
        nt.links.new(sr.outputs["Color"], bump2.inputs["Height"])
        nt.links.new(bmp.outputs["Normal"], bump2.inputs["Normal"])
        nt.links.new(bump2.outputs["Normal"], bsdf.inputs["Normal"])
    else:
        nt.links.new(bmp.outputs["Normal"], bsdf.inputs["Normal"])

    return mat


def make_shingle(name, base, dark, rough=0.82, moss=0.35, tile=(4.0, 4.0, 14.0)):
    """Weathered shingle: strong per-tile tint + fibre bump + lichen."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    out.location = (900, 0)
    bsdf.location = (620, 0)
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])

    tex = nt.nodes.new("ShaderNodeTexCoord")
    tex.location = (-1200, 0)

    mp = nt.nodes.new("ShaderNodeMapping")
    mp.location = (-1000, 60)
    mp.inputs["Scale"].default_value = tile
    nt.links.new(tex.outputs["Object"], mp.inputs["Vector"])

    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.location = (-800, 140)
    wave.wave_type = 'BANDS'
    wave.bands_direction = 'Z'
    wave.wave_profile = 'SIN'
    wave.inputs["Distortion"].default_value = 22.0
    wave.inputs["Detail"].default_value = 4.0
    nt.links.new(mp.outputs["Vector"], wave.inputs["Vector"])

    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.location = (-600, 140)
    ramp.color_ramp.elements[0].position = 0.30
    ramp.color_ramp.elements[1].position = 0.72
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])

    grain = nt.nodes.new("ShaderNodeMix")
    grain.data_type = 'RGBA'
    grain.location = (-380, 140)
    grain.inputs[6].default_value = (base[0], base[1], base[2], 1.0)
    grain.inputs[7].default_value = (dark[0], dark[1], dark[2], 1.0)
    nt.links.new(ramp.outputs["Color"], grain.inputs[0])

    # per tile tint
    try:
        attr = nt.nodes.new("ShaderNodeVertexColor")
        attr.layer_name = "tint"
    except Exception:
        attr = nt.nodes.new("ShaderNodeAttribute")
        attr.attribute_name = "tint"
    attr.location = (-600, -140)

    tint_mul = nt.nodes.new("ShaderNodeMix")
    tint_mul.data_type = 'RGBA'
    tint_mul.blend_type = 'MULTIPLY'
    tint_mul.location = (-160, 120)
    tint_mul.inputs[0].default_value = 1.0
    nt.links.new(grain.outputs[2], tint_mul.inputs[6])
    nt.links.new(attr.outputs["Color"], tint_mul.inputs[7])

    # patchy lichen / weathering
    lich = nt.nodes.new("ShaderNodeTexNoise")
    lich.location = (-800, -420)
    lich.inputs["Scale"].default_value = 1.7
    lich.inputs["Detail"].default_value = 8.0
    lich.inputs["Roughness"].default_value = 0.7
    nt.links.new(tex.outputs["Object"], lich.inputs["Vector"])
    lr = nt.nodes.new("ShaderNodeValToRGB")
    lr.location = (-600, -420)
    lr.color_ramp.elements[0].position = 0.46
    lr.color_ramp.elements[0].color = (0.55, 0.58, 0.50, 1)
    lr.color_ramp.elements[1].position = 0.62
    lr.color_ramp.elements[1].color = (1, 1, 1, 1)
    nt.links.new(lich.outputs["Fac"], lr.inputs["Fac"])

    m2 = nt.nodes.new("ShaderNodeMix")
    m2.data_type = 'RGBA'
    m2.blend_type = 'MULTIPLY'
    m2.location = (80, 120)
    m2.inputs[0].default_value = moss
    nt.links.new(tint_mul.outputs[2], m2.inputs[6])
    nt.links.new(lr.outputs["Color"], m2.inputs[7])

    # broad patchy weathering (aged / freshly tarred areas)
    big = nt.nodes.new("ShaderNodeTexNoise")
    big.location = (-800, 340)
    big.inputs["Scale"].default_value = 0.22
    big.inputs["Detail"].default_value = 4.0
    big.inputs["Roughness"].default_value = 0.55
    nt.links.new(tex.outputs["Object"], big.inputs["Vector"])
    br = nt.nodes.new("ShaderNodeValToRGB")
    br.location = (-600, 340)
    br.color_ramp.elements[0].position = 0.38
    br.color_ramp.elements[0].color = (0.52, 0.53, 0.53, 1)
    br.color_ramp.elements[1].position = 0.62
    br.color_ramp.elements[1].color = (1.35, 1.28, 1.18, 1)
    nt.links.new(big.outputs["Fac"], br.inputs["Fac"])
    m3 = nt.nodes.new("ShaderNodeMix")
    m3.data_type = 'RGBA'
    m3.blend_type = 'MULTIPLY'
    m3.location = (250, 120)
    m3.inputs[0].default_value = 1.0
    nt.links.new(m2.outputs[2], m3.inputs[6])
    nt.links.new(br.outputs["Color"], m3.inputs[7])
    col = m3.outputs[2]
    nt.links.new(col, bsdf.inputs["Base Color"])

    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.location = (380, -180)
    rr.inputs["To Min"].default_value = rough - 0.10
    rr.inputs["To Max"].default_value = min(rough + 0.12, 1.0)
    nt.links.new(lich.outputs["Fac"], rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], bsdf.inputs["Roughness"])
    _set(bsdf, "Specular IOR Level", 0.25)

    bmp = nt.nodes.new("ShaderNodeBump")
    bmp.location = (380, -420)
    bmp.inputs["Strength"].default_value = 0.55
    bmp.inputs["Distance"].default_value = 0.012
    nt.links.new(wave.outputs["Fac"], bmp.inputs["Height"])
    b2 = nt.nodes.new("ShaderNodeBump")
    b2.location = (520, -420)
    b2.inputs["Strength"].default_value = 0.30
    b2.inputs["Distance"].default_value = 0.03
    nt.links.new(lich.outputs["Fac"], b2.inputs["Height"])
    nt.links.new(bmp.outputs["Normal"], b2.inputs["Normal"])
    nt.links.new(b2.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def make_stone(name="STONE_Rubble", base=(0.20, 0.195, 0.18)):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    out.location = (700, 0)
    bsdf.location = (450, 0)
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])

    tex = nt.nodes.new("ShaderNodeTexCoord")
    tex.location = (-900, 0)
    n1 = nt.nodes.new("ShaderNodeTexNoise")
    n1.location = (-700, 100)
    n1.inputs["Scale"].default_value = 4.0
    n1.inputs["Detail"].default_value = 10.0
    nt.links.new(tex.outputs["Object"], n1.inputs["Vector"])
    n2 = nt.nodes.new("ShaderNodeTexVoronoi")
    n2.location = (-700, -160)
    n2.feature = 'DISTANCE_TO_EDGE'
    n2.inputs["Scale"].default_value = 55.0
    nt.links.new(tex.outputs["Object"], n2.inputs["Vector"])

    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.location = (-480, 100)
    cr.color_ramp.elements[0].color = (base[0] * 0.55, base[1] * 0.55, base[2] * 0.55, 1)
    cr.color_ramp.elements[1].color = (base[0] * 1.5, base[1] * 1.5, base[2] * 1.45, 1)
    nt.links.new(n1.outputs["Fac"], cr.inputs["Fac"])

    try:
        attr = nt.nodes.new("ShaderNodeVertexColor")
        attr.layer_name = "tint"
    except Exception:
        attr = nt.nodes.new("ShaderNodeAttribute")
        attr.attribute_name = "tint"
    mul = nt.nodes.new("ShaderNodeMix")
    mul.data_type = 'RGBA'
    mul.blend_type = 'MULTIPLY'
    mul.location = (-200, 60)
    mul.inputs[0].default_value = 1.0
    nt.links.new(cr.outputs["Color"], mul.inputs[6])
    nt.links.new(attr.outputs["Color"], mul.inputs[7])
    nt.links.new(mul.outputs[2], bsdf.inputs["Base Color"])

    # moss in the joints
    n3 = nt.nodes.new("ShaderNodeTexNoise")
    n3.location = (-700, -420)
    n3.inputs["Scale"].default_value = 6.0
    nt.links.new(tex.outputs["Object"], n3.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeValToRGB")
    mr.location = (-480, -420)
    mr.color_ramp.elements[0].position = 0.5
    mr.color_ramp.elements[1].position = 0.66
    nt.links.new(n3.outputs["Fac"], mr.inputs["Fac"])
    mm = nt.nodes.new("ShaderNodeMix")
    mm.data_type = 'RGBA'
    mm.location = (150, 60)
    mm.inputs[0].default_value = 0.35
    nt.links.new(mul.outputs[2], mm.inputs[6])
    mm.inputs[7].default_value = (0.055, 0.075, 0.040, 1)
    nt.links.new(mr.outputs["Color"], mm.inputs[0])
    nt.links.new(mm.outputs[2], bsdf.inputs["Base Color"])

    _set(bsdf, "Roughness", 0.92)
    _set(bsdf, "Specular IOR Level", 0.3)
    bmp = nt.nodes.new("ShaderNodeBump")
    bmp.location = (150, -300)
    bmp.inputs["Strength"].default_value = 0.65
    bmp.inputs["Distance"].default_value = 0.03
    nt.links.new(n1.outputs["Fac"], bmp.inputs["Height"])
    b2 = nt.nodes.new("ShaderNodeBump")
    b2.location = (330, -300)
    b2.inputs["Strength"].default_value = 0.5
    nt.links.new(n2.outputs["Distance"], b2.inputs["Height"])
    nt.links.new(bmp.outputs["Normal"], b2.inputs["Normal"])
    nt.links.new(b2.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def _principled(mat):
    """Return the Principled BSDF of *mat* regardless of the UI language."""
    nt = mat.node_tree
    for n in nt.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            return n
    n = nt.nodes.new("ShaderNodeBsdfPrincipled")
    out = None
    for m in nt.nodes:
        if m.type == 'OUTPUT_MATERIAL':
            out = m
    if out is None:
        out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(n.outputs[0], out.inputs["Surface"])
    return n


def make_simple(name, color, rough=0.6, metal=0.0, spec=0.4):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    b = _principled(mat)
    b.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    _set(b, "Roughness", rough)
    _set(b, "Metallic", metal)
    _set(b, "Specular IOR Level", spec)
    return mat
