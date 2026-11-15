# -*- coding: utf-8 -*-
"""Geometry helpers + materials for the Horyu-ji five-storey pagoda."""
import bpy, math
from mathutils import Vector, Matrix

PI = math.pi
RAD = math.radians


# --------------------------------------------------------------------------- #
#  Mesh builder
# --------------------------------------------------------------------------- #
class MB:
    """Accumulates verts / faces / material ids, then bakes one mesh."""

    def __init__(self, mats):
        self.v = []
        self.f = []
        self.mi = []
        self.uv = []          # optional per-loop uv, list of (u,v) per face
        self.mats = list(mats)

    def _m(self, name):
        try:
            return self.mats.index(name)
        except ValueError:
            self.mats.append(name)
            return len(self.mats) - 1

    # ---- primitives -------------------------------------------------------
    def poly(self, pts, mat, uvs=None):
        i0 = len(self.v)
        for p in pts:
            self.v.append((p[0], p[1], p[2]))
        self.f.append(tuple(range(i0, i0 + len(pts))))
        self.mi.append(self._m(mat))
        if uvs is not None:
            self.uv.append(tuple(uvs))
        else:
            self.uv.append(None)

    def box(self, M, sx, sy, sz, mat, cx=0.0, cy=0.0, cz=0.0):
        """Axis-aligned box of size (sx,sy,sz) centred at local (cx,cy,cz), then
        transformed by 4x4 M."""
        hx, hy, hz = sx * .5, sy * .5, sz * .5
        c = [(cx - hx, cy - hy, cz - hz), (cx + hx, cy - hy, cz - hz),
             (cx + hx, cy + hy, cz - hz), (cx - hx, cy + hy, cz - hz),
             (cx - hx, cy - hy, cz + hz), (cx + hx, cy - hy, cz + hz),
             (cx + hx, cy + hy, cz + hz), (cx - hx, cy + hy, cz + hz)]
        p = [M @ Vector(x) for x in c]
        quads = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                 (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        i0 = len(self.v)
        for x in p:
            self.v.append((x[0], x[1], x[2]))
        for q in quads:
            self.f.append(tuple(i0 + k for k in q))
            self.mi.append(self._m(mat))
            self.uv.append(None)

    def cyl(self, M, r, h, mat, seg=16, cx=0.0, cy=0.0, cz=0.0, r2=None, caps=True):
        """Cylinder / cone along local Z."""
        r2 = r if r2 is None else r2
        i0 = len(self.v)
        for k in range(seg):
            a = 2 * PI * k / seg
            self.v.append((cx + r * math.cos(a), cy + r * math.sin(a), cz))
        for k in range(seg):
            a = 2 * PI * k / seg
            self.v.append((cx + r2 * math.cos(a), cy + r2 * math.sin(a), cz + h))
        for k in range(seg):
            k2 = (k + 1) % seg
            self.f.append((i0 + k, i0 + k2, i0 + seg + k2, i0 + seg + k))
            self.mi.append(self._m(mat))
            self.uv.append(None)
        if caps:
            self.f.append(tuple(i0 + k for k in range(seg - 1, -1, -1)))
            self.mi.append(self._m(mat))
            self.uv.append(None)
            self.f.append(tuple(i0 + seg + k for k in range(seg)))
            self.mi.append(self._m(mat))
            self.uv.append(None)

    def sphere(self, M, r, mat, seg=16, rings=8, cz=0.0):
        i0 = len(self.v)
        for i in range(rings + 1):
            th = PI * i / rings
            for k in range(seg):
                a = 2 * PI * k / seg
                q = M @ Vector((r * math.sin(th) * math.cos(a),
                                r * math.sin(th) * math.sin(a),
                                cz + r * math.cos(th)))
                self.v.append((q.x, q.y, q.z))
        for i in range(rings):
            for k in range(seg):
                k2 = (k + 1) % seg
                a = i0 + i * seg + k
                b = i0 + i * seg + k2
                c = i0 + (i + 1) * seg + k2
                d = i0 + (i + 1) * seg + k
                self.f.append((a, b, c, d))
                self.mi.append(self._m(mat))
                self.uv.append(None)

    def torus(self, M, R, r, mat, seg=24, rseg=8, cz=0.0):
        i0 = len(self.v)
        for i in range(seg):
            a = 2 * PI * i / seg
            for j in range(rseg):
                b = 2 * PI * j / rseg
                rr = R + r * math.cos(b)
                q = M @ Vector((rr * math.cos(a), rr * math.sin(a),
                                cz + r * math.sin(b)))
                self.v.append((q.x, q.y, q.z))
        for i in range(seg):
            i2 = (i + 1) % seg
            for j in range(rseg):
                j2 = (j + 1) % rseg
                self.f.append((i0 + i * rseg + j, i0 + i2 * rseg + j,
                               i0 + i2 * rseg + j2, i0 + i * rseg + j2))
                self.mi.append(self._m(mat))
                self.uv.append(None)

    def swept(self, pts, width, height, mat, side_axis=(1, 0, 0), profile=None):
        """Sweep a closed 2D profile (in (across, up) units, centred on origin)
        along a polyline."""
        sa = Vector(side_axis).normalized()
        if profile is None:
            profile = [(-.5, -.5), (.5, -.5), (.5, .5), (-.5, .5)]
        prof = [(a * width, b * height) for (a, b) in profile]
        npf = len(prof)
        secs = []
        n = len(pts)
        for i, p in enumerate(pts):
            p = Vector(p)
            if i == 0:
                t = (Vector(pts[1]) - p)
            elif i == n - 1:
                t = (p - Vector(pts[-2]))
            else:
                t = (Vector(pts[i + 1]) - Vector(pts[i - 1]))
            t.normalize()
            sd = sa - t * sa.dot(t)
            if sd.length < 1e-6:
                sd = Vector((1, 0, 0))
            sd.normalize()
            up = t.cross(sd).normalized()
            if up.z < 0:
                up = -up
            secs.append((p, sd, up))
        base = len(self.v)
        for (p, sd, up) in secs:
            for (a, b) in prof:
                q = p + sd * a + up * b
                self.v.append((q.x, q.y, q.z))
        for i in range(n - 1):
            for j in range(npf):
                j2 = (j + 1) % npf
                a0 = base + i * npf + j
                b0 = base + i * npf + j2
                c0 = base + (i + 1) * npf + j2
                d0 = base + (i + 1) * npf + j
                self.f.append((a0, b0, c0, d0))
                self.mi.append(self._m(mat))
                self.uv.append(None)
        self.f.append(tuple(base + j for j in range(npf - 1, -1, -1)))
        self.mi.append(self._m(mat)); self.uv.append(None)
        e = base + (n - 1) * npf
        self.f.append(tuple(e + j for j in range(npf)))
        self.mi.append(self._m(mat)); self.uv.append(None)

    # ---- output -----------------------------------------------------------
    def build(self, name, coll, smooth_angle=35.0):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.v, [], self.f)
        me.validate(verbose=False)
        if any(u is not None for u in self.uv):
            uvl = me.uv_layers.new(name="UVMap")
            k = 0
            for fi, face in enumerate(self.f):
                u = self.uv[fi]
                for j in range(len(face)):
                    if u is not None and j < len(u):
                        uvl.data[k + j].uv = u[j]
                    else:
                        uvl.data[k + j].uv = (0, 0)
                k += len(face)
        for m in self.mats:
            me.materials.append(bpy.data.materials[m])
        for i, p in enumerate(me.polygons):
            p.material_index = min(self.mi[i], len(self.mats) - 1)
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
        me.update()
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        if smooth_angle is not None:
            mod = ob.modifiers.new("Smooth by Angle", 'NODES')
            try:
                ng = bpy.data.node_groups.get("Smooth by Angle")
                if ng is None:
                    bpy.ops.object.select_all(action='DESELECT')
                    ob.select_set(True)
                    bpy.context.view_layer.objects.active = ob
                    bpy.ops.object.shade_auto_smooth(angle=RAD(smooth_angle))
                    ob.modifiers.remove(mod)
                else:
                    mod.node_group = ng
            except Exception:
                ob.modifiers.remove(mod)
        return ob


def mx(x=0, y=0, z=0, rz=0.0):
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(rz, 4, 'Z')


# --------------------------------------------------------------------------- #
#  Materials
# --------------------------------------------------------------------------- #
def _new(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
    out = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeOutputMaterial')
    return m, nt, bsdf, out


def _ramp(nt, stops, loc=(0, 0)):
    r = nt.nodes.new('ShaderNodeValToRGB')
    el = r.color_ramp.elements
    while len(el) > 2:
        el.remove(el[-1])
    el[0].position = stops[0][0]
    el[0].color = tuple(stops[0][1]) + (1,)
    el[1].position = stops[-1][0]
    el[1].color = tuple(stops[-1][1]) + (1,)
    for s in stops[1:-1]:
        e = el.new(s[0])
        e.color = tuple(s[1]) + (1,)
    r.location = loc
    return r


def _mixrgb(nt, a, b, fac, blend='MIX'):
    m = nt.nodes.new('ShaderNodeMix')
    m.data_type = 'RGBA'
    m.blend_type = blend
    m.location = (-150, 200)
    return m


def mat_wood(name, c1, c2, rough=0.62, grain=1.0, bump=0.22, axis='Z'):
    m, nt, bsdf, out = _new(name)
    L = nt.links
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (14 * grain if axis == 'X' else 1.4 * grain,
                                        14 * grain if axis == 'Y' else 1.4 * grain,
                                        0.55 * grain)
    L.new(tc.outputs['Object'], mp.inputs['Vector'])
    wv = nt.nodes.new('ShaderNodeTexWave')
    wv.wave_type = 'BANDS'
    wv.bands_direction = 'Z'
    wv.inputs['Scale'].default_value = 1.0
    wv.inputs['Distortion'].default_value = 7.0
    wv.inputs['Detail'].default_value = 3.0
    wv.inputs['Detail Scale'].default_value = 1.6
    L.new(mp.outputs['Vector'], wv.inputs['Vector'])
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 3.5
    nz.inputs['Detail'].default_value = 8.0
    nz.inputs['Roughness'].default_value = 0.6
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    mix = nt.nodes.new('ShaderNodeMix')          # grain over base colour
    mix.data_type = 'RGBA'
    L.new(wv.outputs['Fac'], mix.inputs['Factor'])
    mix.inputs[6].default_value = c1 + (1,)
    mix.inputs[7].default_value = c2 + (1,)
    # large scale weathering
    wmix = nt.nodes.new('ShaderNodeMix')
    wmix.data_type = 'RGBA'
    wmix.blend_type = 'MULTIPLY'
    wmix.inputs['Factor'].default_value = 0.35
    L.new(nz.outputs['Fac'], wmix.inputs['Factor'])
    L.new(mix.outputs[2], wmix.inputs[6])
    wmix.inputs[7].default_value = (0.55, 0.50, 0.45, 1)
    L.new(wmix.outputs[2], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Specular IOR Level'].default_value = 0.32
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = bump
    bp.inputs['Distance'].default_value = 0.02
    L.new(wv.outputs['Fac'], bp.inputs['Height'])
    L.new(bp.outputs['Normal'], bsdf.inputs['Normal'])
    return m


def mat_plaster(name, base=(0.83, 0.80, 0.73), rough=0.9):
    m, nt, bsdf, out = _new(name)
    L = nt.links
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 26.0
    nz.inputs['Detail'].default_value = 9.0
    nz.inputs['Roughness'].default_value = 0.62
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    rp = _ramp(nt, [(0.35, (0.62, 0.61, 0.57)), (0.62, base), (0.85, (0.90, 0.88, 0.82))])
    L.new(nz.outputs['Fac'], rp.inputs['Fac'])
    L.new(rp.outputs['Color'], bsdf.inputs['Base Color'])
    # dirt in crevices
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    pv = _ramp(nt, [(0.35, (0.30, 0.30, 0.30)), (0.55, (1, 1, 1))])
    L.new(geo.outputs['Pointiness'], pv.inputs['Fac'])
    dm = nt.nodes.new('ShaderNodeMix')
    dm.data_type = 'RGBA'
    dm.blend_type = 'MULTIPLY'
    dm.inputs['Factor'].default_value = 0.45
    L.new(rp.outputs['Color'], dm.inputs[6])
    L.new(pv.outputs['Color'], dm.inputs[7])
    L.new(dm.outputs[2], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = rough
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 0.10
    bp.inputs['Distance'].default_value = 0.01
    L.new(nz.outputs['Fac'], bp.inputs['Height'])
    L.new(bp.outputs['Normal'], bsdf.inputs['Normal'])
    return m


def mat_tile(name):
    m, nt, bsdf, out = _new(name)
    L = nt.links.new
    uv = nt.nodes.new('ShaderNodeUVMap')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    L(uv.outputs['UV'], sep.inputs['Vector'])
    # rounded tile ridges running down the slope (bands across U)
    wv = nt.nodes.new('ShaderNodeTexWave')
    wv.wave_type = 'BANDS'
    wv.bands_direction = 'X'
    wv.wave_profile = 'SIN'
    wv.inputs['Scale'].default_value = 3.55
    wv.inputs['Distortion'].default_value = 0.0
    L(uv.outputs['UV'], wv.inputs['Vector'])
    # per-tile tone variation
    comb = nt.nodes.new('ShaderNodeCombineXYZ')
    L(sep.outputs['X'], comb.inputs['X'])
    wn = nt.nodes.new('ShaderNodeTexWhiteNoise')
    wn.noise_dimensions = '2D'
    mp = nt.nodes.new('ShaderNodeMath')
    mp.operation = 'MULTIPLY'
    mp.inputs[1].default_value = 1.0 / 0.30
    L(sep.outputs['X'], mp.inputs[0])
    L(sep.outputs['Y'], comb.inputs['X'])
    L(comb.outputs['Vector'], wn.inputs['Vector'])
    wc = _ramp(nt, [(0.0, (0.058, 0.064, 0.072)), (0.5, (0.082, 0.090, 0.100)),
                    (1.0, (0.048, 0.054, 0.062))])
    L(wn.outputs['Value'], wc.inputs['Fac'])
    # horizontal courses of flat tiles
    wv2 = nt.nodes.new('ShaderNodeTexWave')
    wv2.wave_type = 'BANDS'
    wv2.bands_direction = 'Y'
    wv2.wave_profile = 'SAW'
    wv2.inputs['Scale'].default_value = 3.15
    wv2.inputs['Distortion'].default_value = 0.0
    L(uv.outputs['UV'], wv2.inputs['Vector'])
    cr = _ramp(nt, [(0.0, (0.55, 0.58, 0.62)), (0.07, (1.0, 1.0, 1.0)),
                    (0.93, (1.0, 1.0, 1.0)), (1.0, (0.55, 0.58, 0.62))])
    L(wv2.outputs['Fac'], cr.inputs['Fac'])
    # streaks / moss
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 7.0
    nz.inputs['Detail'].default_value = 8.0
    L(uv.outputs['UV'], nz.inputs['Vector'])
    dm = nt.nodes.new('ShaderNodeMix')
    dm.data_type = 'RGBA'
    dm.blend_type = 'MULTIPLY'
    dm.inputs['Factor'].default_value = 0.5
    L(wc.outputs['Color'], dm.inputs[6])
    nr = _ramp(nt, [(0.3, (1, 1, 1)), (0.62, (0.62, 0.64, 0.62)), (0.8, (0.80, 0.80, 0.78))])
    L(nz.outputs['Fac'], nr.inputs['Fac'])
    L(nr.outputs['Color'], dm.inputs[7])
    L(dm.outputs[2], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.60
    bsdf.inputs['Specular IOR Level'].default_value = 0.30
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 0.55
    bp.inputs['Distance'].default_value = 0.06
    L(wv.outputs['Fac'], bp.inputs['Height'])
    L(bp.outputs['Normal'], bsdf.inputs['Normal'])
    return m


def mat_stone(name, c1=(0.34, 0.33, 0.31), c2=(0.52, 0.51, 0.48), scale=6.0,
              brick=False):
    m, nt, bsdf, out = _new(name)
    L = nt.links
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = scale
    nz.inputs['Detail'].default_value = 10.0
    nz.inputs['Roughness'].default_value = 0.65
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    rp = _ramp(nt, [(0.30, c1), (0.55, [(a + b) * .5 for a, b in zip(c1, c2)]),
                    (0.78, c2)])
    L.new(nz.outputs['Fac'], rp.inputs['Fac'])
    col = rp.outputs['Color']
    hgt = nz.outputs['Fac']
    if brick:
        br = nt.nodes.new('ShaderNodeTexBrick')
        br.inputs['Scale'].default_value = 0.55
        br.inputs['Mortar Size'].default_value = 0.012
        br.inputs['Mortar Smooth'].default_value = 0.3
        br.inputs['Color1'].default_value = (0.62, 0.62, 0.62, 1)
        br.inputs['Color2'].default_value = (0.44, 0.44, 0.44, 1)
        br.inputs['Mortar'].default_value = (0.20, 0.20, 0.19, 1)
        L.new(tc.outputs['Object'], br.inputs['Vector'])
        dm = nt.nodes.new('ShaderNodeMix')
        dm.data_type = 'RGBA'
        dm.blend_type = 'MULTIPLY'
        dm.inputs['Factor'].default_value = 1.0
        L.new(col, dm.inputs[6])
        L.new(br.outputs['Color'], dm.inputs[7])
        col = dm.outputs[2]
        hc = nt.nodes.new('ShaderNodeMix')
        hc.data_type = 'FLOAT'
        hc.inputs['Factor'].default_value = 0.8
        L.new(hgt, hc.inputs[2])
        L.new(br.outputs['Fac'], hc.inputs[3])
        hgt = hc.outputs[0]
    bsdf.inputs['Base Color'].default_value = (0.4, 0.4, 0.4, 1)
    L.new(col, bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.78
    bsdf.inputs['Specular IOR Level'].default_value = 0.3
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 0.32
    bp.inputs['Distance'].default_value = 0.03
    L.new(hgt, bp.inputs['Height'])
    L.new(bp.outputs['Normal'], bsdf.inputs['Normal'])
    return m


def mat_metal(name, c1=(0.10, 0.115, 0.10), c2=(0.055, 0.16, 0.125),
              metallic=0.9, rough=0.42):
    m, nt, bsdf, out = _new(name)
    L = nt.links
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 12.0
    nz.inputs['Detail'].default_value = 10.0
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    rp = _ramp(nt, [(0.32, c1), (0.55, c2), (0.72, [(a * .7 + b * .3) for a, b in zip(c1, c2)])])
    L.new(nz.outputs['Fac'], rp.inputs['Fac'])
    L.new(rp.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = rough
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 0.25
    bp.inputs['Distance'].default_value = 0.01
    L.new(nz.outputs['Fac'], bp.inputs['Height'])
    L.new(bp.outputs['Normal'], bsdf.inputs['Normal'])
    return m


def mat_ground(name):
    m, nt, bsdf, out = _new(name)
    L = nt.links.new
    tc = nt.nodes.new('ShaderNodeTexCoord')
    # large patches of dirt / moss
    nz0 = nt.nodes.new('ShaderNodeTexNoise')
    nz0.inputs['Scale'].default_value = 0.09
    nz0.inputs['Detail'].default_value = 5.0
    L(tc.outputs['Object'], nz0.inputs['Vector'])
    big = _ramp(nt, [(0.30, (0.17, 0.155, 0.13)), (0.50, (0.27, 0.25, 0.215)),
                     (0.72, (0.36, 0.335, 0.29)), (0.90, (0.30, 0.28, 0.24))])
    L(nz0.outputs['Fac'], big.inputs['Fac'])
    # gravel grains
    vor = nt.nodes.new('ShaderNodeTexVoronoi')
    vor.feature = 'F1'
    vor.inputs['Scale'].default_value = 210.0
    L(tc.outputs['Object'], vor.inputs['Vector'])
    gr = _ramp(nt, [(0.0, (0.14, 0.135, 0.125)), (0.28, (0.36, 0.345, 0.31)),
                    (0.85, (0.62, 0.60, 0.55))])
    L(vor.outputs['Distance'], gr.inputs['Fac'])
    dm = nt.nodes.new('ShaderNodeMix')
    dm.data_type = 'RGBA'
    dm.blend_type = 'OVERLAY'
    dm.inputs['Factor'].default_value = 0.72
    L(big.outputs['Color'], dm.inputs[6])
    L(gr.outputs['Color'], dm.inputs[7])
    L(dm.outputs[2], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.93
    bsdf.inputs['Specular IOR Level'].default_value = 0.15
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 0.55
    bp.inputs['Distance'].default_value = 0.02
    L(vor.outputs['Distance'], bp.inputs['Height'])
    L(bp.outputs['Normal'], bsdf.inputs['Normal'])
    return m


def build_materials():
    mat_wood("wood_shadow", (0.020, 0.014, 0.010), (0.042, 0.030, 0.021),
             rough=0.72, grain=1.0, bump=0.20)
    mat_wood("wood_dark", (0.070, 0.046, 0.033), (0.130, 0.085, 0.060),
             rough=0.62, grain=1.0, bump=0.30)
    mat_wood("wood_beam", (0.095, 0.062, 0.044), (0.160, 0.108, 0.076),
             rough=0.60, grain=0.7, bump=0.24)
    mat_wood("wood_red", (0.080, 0.048, 0.034), (0.135, 0.088, 0.062),
             rough=0.68, grain=0.8, bump=0.22)
    mat_wood("wood_light", (0.185, 0.135, 0.090), (0.255, 0.190, 0.128),
             rough=0.60, grain=0.9, bump=0.20)
    mat_plaster("plaster")
    mat_tile("tile")
    mat_stone("stone", c1=(0.20, 0.195, 0.18), c2=(0.36, 0.35, 0.33),
              brick=True, scale=0.0)
    mat_stone("stone_step", c1=(0.22, 0.215, 0.20), c2=(0.40, 0.39, 0.36),
              scale=8.0)
    mat_metal("bronze", c1=(0.042, 0.070, 0.058), c2=(0.070, 0.100, 0.084),
              metallic=0.75, rough=0.48)
    mat_metal("gold", c1=(0.55, 0.38, 0.10), c2=(0.75, 0.56, 0.18),
              metallic=1.0, rough=0.25)
    mat_ground("gravel")
