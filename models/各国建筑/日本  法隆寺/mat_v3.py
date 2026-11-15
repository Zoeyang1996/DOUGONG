# -*- coding: utf-8 -*-
"""PBR material library for the Horyu-ji pagoda.

Real 2K texture sets (Poly Haven, CC0) live in ./tex :
    stained_pine_*              weathered pine  -> all timber
    plastered_wall_05_*         lime plaster     -> white walls
    gravel_embedded_concrete_*  gravel          -> courtyard
Everything else (roof tiles, cast bronze, foliage) is procedural.
"""
import bpy
import os
import math

TEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tex")


# --------------------------------------------------------------------------- #
#  helpers
# --------------------------------------------------------------------------- #
def _new(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return m, nt, bsdf, out


def _img(fn, non_color=False):
    p = os.path.join(TEX, fn)
    im = bpy.data.images.load(p, check_existing=True)
    if non_color:
        im.colorspace_settings.name = 'Non-Color'
    return im


def _math(nt, op, a=None, b=None, clamp=False):
    n = nt.nodes.new('ShaderNodeMath')
    n.operation = op
    n.use_clamp = clamp
    if a is not None:
        n.inputs[0].default_value = a
    if b is not None:
        n.inputs[1].default_value = b
    return n


def _ramp(nt, stops):
    r = nt.nodes.new('ShaderNodeValToRGB')
    el = r.color_ramp.elements
    while len(el) > 2:
        el.remove(el[-1])
    el[0].position, el[0].color = stops[0][0], tuple(stops[0][1]) + (1,)
    el[1].position, el[1].color = stops[-1][0], tuple(stops[-1][1]) + (1,)
    for s in stops[1:-1]:
        e = el.new(s[0])
        e.color = tuple(s[1]) + (1,)
    return r


# --------------------------------------------------------------------------- #
#  textured timber / plaster / gravel
# --------------------------------------------------------------------------- #
def pbr(name, prefix, scale=(1, 1, 1), rot=(0, 0, 0), tint=(1, 1, 1),
        rough_mul=1.0, metallic=0.0, nor=1.0, bump=0.0,
        grime=0.0, grime_col=(0.30, 0.27, 0.23), grime_scale=1.6,
        rough_floor=0.30):
    """Box-projected PBR set: diffuse * tint, roughness map, normal map."""
    m, nt, bsdf, out = _new(name)
    L = nt.links.new
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = scale
    mp.inputs['Rotation'].default_value = [math.radians(a) for a in rot]
    L(tc.outputs['Object'], mp.inputs['Vector'])
    vec = mp.outputs['Vector']

    def tex(fn, nc):
        t = nt.nodes.new('ShaderNodeTexImage')
        t.image = _img(fn, nc)
        t.projection = 'BOX'
        t.projection_blend = 0.32
        L(vec, t.inputs['Vector'])
        return t

    dif = tex(prefix + '_diff_2k.jpg', False)
    # ---- base colour
    col = dif.outputs['Color']
    if tint != (1, 1, 1):
        mix = nt.nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        mix.blend_type = 'MULTIPLY'
        mix.inputs['Factor'].default_value = 1.0
        L(col, mix.inputs[6])
        mix.inputs[7].default_value = tuple(tint) + (1,)
        col = mix.outputs[2]
    if grime > 0.0:
        nz = nt.nodes.new('ShaderNodeTexNoise')
        nz.inputs['Scale'].default_value = grime_scale
        nz.inputs['Detail'].default_value = 8.0
        nz.inputs['Roughness'].default_value = 0.62
        L(tc.outputs['Object'], nz.inputs['Vector'])
        gp = _ramp(nt, [(0.30, (1, 1, 1)), (0.62, grime_col)])
        L(nz.outputs['Fac'], gp.inputs['Fac'])
        gm = nt.nodes.new('ShaderNodeMix')
        gm.data_type = 'RGBA'
        gm.blend_type = 'MULTIPLY'
        gm.inputs['Factor'].default_value = grime
        L(col, gm.inputs[6])
        L(gp.outputs['Color'], gm.inputs[7])
        col = gm.outputs[2]
    L(col, bsdf.inputs['Base Color'])
    # ---- roughness
    rgh = tex(prefix + '_rough_2k.exr', True)
    rm = _math(nt, 'MULTIPLY', None, rough_mul, clamp=True)
    L(rgh.outputs['Color'], rm.inputs[0])
    L(rm.outputs[0], bsdf.inputs['Roughness'])
    bsdf.inputs['Metallic'].default_value = metallic
    # ---- normal
    nor_tex = tex(prefix + '_nor_gl_2k.exr', True)
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nm.inputs['Strength'].default_value = nor
    L(nor_tex.outputs['Color'], nm.inputs['Color'])
    if bump > 0.0:
        bp = nt.nodes.new('ShaderNodeBump')
        bp.inputs['Strength'].default_value = bump
        bp.inputs['Distance'].default_value = 0.02
        L(dif.outputs['Color'], bp.inputs['Height'])
        L(nm.outputs['Normal'], bp.inputs['Normal'])
        L(bp.outputs['Normal'], bsdf.inputs['Normal'])
    else:
        L(nm.outputs['Normal'], bsdf.inputs['Normal'])
    return m


# --------------------------------------------------------------------------- #
#  lime plaster (白壁) - procedural: no white plaster texture in the library
# --------------------------------------------------------------------------- #
def mat_lime(name, col=(0.680, 0.665, 0.620), mottle=0.055, rough=0.86,
             bump=0.10, streak=0.16, scale=1.0):
    m, nt, bsdf, out = _new(name)
    L = nt.links.new
    tc = nt.nodes.new('ShaderNodeTexCoord')

    # broad mottling (lime wash unevenness)
    n1 = nt.nodes.new('ShaderNodeTexNoise')
    n1.inputs['Scale'].default_value = 0.85 * scale
    n1.inputs['Detail'].default_value = 6.0
    n1.inputs['Roughness'].default_value = 0.55
    L(tc.outputs['Object'], n1.inputs['Vector'])
    r1 = _ramp(nt, [(0.30, tuple(c * (1.0 + mottle * 2.2) for c in col)),
                    (0.72, tuple(c * (1.0 - mottle * 1.6) for c in col))])
    L(n1.outputs['Fac'], r1.inputs['Fac'])

    # rain streaks running down the wall
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (3.4 * scale, 3.4 * scale, 0.22 * scale)
    L(tc.outputs['Object'], mp.inputs['Vector'])
    n2 = nt.nodes.new('ShaderNodeTexNoise')
    n2.inputs['Scale'].default_value = 2.4
    n2.inputs['Detail'].default_value = 8.0
    n2.inputs['Roughness'].default_value = 0.70
    L(mp.outputs['Vector'], n2.inputs['Vector'])
    r2 = _ramp(nt, [(0.36, (1, 1, 1)), (0.72, (0.62, 0.60, 0.56))])
    L(n2.outputs['Fac'], r2.inputs['Fac'])
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.blend_type = 'MULTIPLY'
    mix.inputs['Factor'].default_value = streak
    L(r1.outputs['Color'], mix.inputs[6])
    L(r2.outputs['Color'], mix.inputs[7])
    L(mix.outputs[2], bsdf.inputs['Base Color'])

    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Specular IOR Level'].default_value = 0.30

    # fine trowel grain
    n3 = nt.nodes.new('ShaderNodeTexNoise')
    n3.inputs['Scale'].default_value = 32.0 * scale
    n3.inputs['Detail'].default_value = 4.0
    L(tc.outputs['Object'], n3.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = bump
    bp.inputs['Distance'].default_value = 0.008
    L(n3.outputs['Fac'], bp.inputs['Height'])
    L(bp.outputs['Normal'], bsdf.inputs['Normal'])
    return m


# --------------------------------------------------------------------------- #
#  painted timber (丹塗り) - flat colour, faint grain, weathered micro-variation
# --------------------------------------------------------------------------- #
def mat_paint(name, col, rough=0.62, grain=0.30, tint2=None, scale=1.6):
    m, nt, bsdf, out = _new(name)
    L = nt.links.new
    tc = nt.nodes.new('ShaderNodeTexCoord')

    # stretched noise -> subtle grain along the member
    mpn = nt.nodes.new('ShaderNodeMapping')
    mpn.inputs['Scale'].default_value = (0.55 * scale, 0.06 * scale, 0.55 * scale)
    L(tc.outputs['Object'], mpn.inputs['Vector'])
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 3.2
    nz.inputs['Detail'].default_value = 9.0
    nz.inputs['Roughness'].default_value = 0.68
    L(mpn.outputs['Vector'], nz.inputs['Vector'])

    c2 = tint2 if tint2 else tuple(c * 0.62 for c in col)
    ramp = _ramp(nt, [(0.28, tuple(c * 1.30 for c in col)),
                      (0.55, tuple(col)),
                      (0.82, tuple(c2))])
    L(nz.outputs['Fac'], ramp.inputs['Fac'])

    # large-scale weathering blotches
    nz2 = nt.nodes.new('ShaderNodeTexNoise')
    nz2.inputs['Scale'].default_value = 0.55 * scale
    nz2.inputs['Detail'].default_value = 5.0
    L(tc.outputs['Object'], nz2.inputs['Vector'])
    gp = _ramp(nt, [(0.34, (1.0, 1.0, 1.0)),
                    (0.66, (0.52, 0.50, 0.48))])
    L(nz2.outputs['Fac'], gp.inputs['Fac'])
    gm = nt.nodes.new('ShaderNodeMix')
    gm.data_type = 'RGBA'
    gm.blend_type = 'MULTIPLY'
    gm.inputs['Factor'].default_value = grain
    L(ramp.outputs['Color'], gm.inputs[6])
    L(gp.outputs['Color'], gm.inputs[7])
    L(gm.outputs[2], bsdf.inputs['Base Color'])

    bsdf.inputs['Roughness'].default_value = rough
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 0.16
    bp.inputs['Distance'].default_value = 0.012
    L(nz.outputs['Fac'], bp.inputs['Height'])
    L(bp.outputs['Normal'], bsdf.inputs['Normal'])
    return m


# --------------------------------------------------------------------------- #
#  roof tiles (hongawara) - driven by the roof UVs  u = across, v = down slope
# --------------------------------------------------------------------------- #
def mat_tile(name="tile"):
    m, nt, bsdf, out = _new(name)
    L = nt.links.new
    uv = nt.nodes.new('ShaderNodeUVMap')
    uv.uv_map = "UVMap"
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    L(uv.outputs['UV'], sep.inputs['Vector'])
    U, V = sep.outputs['X'], sep.outputs['Y']

    # ---- one random value per (tile column, course)
    du = _math(nt, 'MULTIPLY', None, 1.0 / 0.315)
    L(U, du.inputs[0])
    dv = _math(nt, 'MULTIPLY', None, 1.0 / 0.30)
    L(V, dv.inputs[0])
    fu = _math(nt, 'FLOOR')
    L(du.outputs[0], fu.inputs[0])
    fv = _math(nt, 'FLOOR')
    L(dv.outputs[0], fv.inputs[0])
    comb = nt.nodes.new('ShaderNodeCombineXYZ')
    L(fu.outputs[0], comb.inputs['X'])
    L(fv.outputs[0], comb.inputs['Y'])
    wn = nt.nodes.new('ShaderNodeTexWhiteNoise')
    wn.noise_dimensions = '2D'
    L(comb.outputs['Vector'], wn.inputs['Vector'])
    tone = _ramp(nt, [(0.00, (0.076, 0.075, 0.073)),
                      (0.35, (0.112, 0.110, 0.106)),
                      (0.70, (0.158, 0.155, 0.148)),
                      (1.00, (0.092, 0.093, 0.094))])
    L(wn.outputs['Value'], tone.inputs['Fac'])

    # ---- dark joint at each course line
    fr = _math(nt, 'FRACT')
    L(dv.outputs[0], fr.inputs[0])
    joint = _ramp(nt, [(0.00, (0.30, 0.30, 0.30)), (0.10, (1, 1, 1)),
                       (0.92, (1, 1, 1)), (1.00, (0.42, 0.42, 0.42))])
    L(fr.outputs[0], joint.inputs['Fac'])
    jm = nt.nodes.new('ShaderNodeMix')
    jm.data_type = 'RGBA'
    jm.blend_type = 'MULTIPLY'
    jm.inputs['Factor'].default_value = 1.0
    L(tone.outputs['Color'], jm.inputs[6])
    L(joint.outputs['Color'], jm.inputs[7])
    col = jm.outputs[2]

    # ---- weathering / moss streaks running down the slope
    st = nt.nodes.new('ShaderNodeTexNoise')
    st.inputs['Scale'].default_value = 1.0
    st.inputs['Detail'].default_value = 8.0
    st.inputs['Roughness'].default_value = 0.65
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (2.6, 0.30, 1.0)
    L(uv.outputs['UV'], mp.inputs['Vector'])
    L(mp.outputs['Vector'], st.inputs['Vector'])
    wm = _ramp(nt, [(0.34, (0.62, 0.62, 0.60)), (0.55, (1.0, 1.0, 1.0)),
                    (0.80, (1.06, 1.04, 0.98))])
    L(st.outputs['Fac'], wm.inputs['Fac'])
    wmix = nt.nodes.new('ShaderNodeMix')
    wmix.data_type = 'RGBA'
    wmix.blend_type = 'MULTIPLY'
    wmix.inputs['Factor'].default_value = 0.55
    L(col, wmix.inputs[6])
    L(wm.outputs['Color'], wmix.inputs[7])
    L(wmix.outputs[2], bsdf.inputs['Base Color'])

    bsdf.inputs['Roughness'].default_value = 0.74
    bsdf.inputs['Specular IOR Level'].default_value = 0.12

    # ---- micro relief: ridges + course steps + grain
    fine = nt.nodes.new('ShaderNodeTexNoise')
    fine.inputs['Scale'].default_value = 26.0
    fine.inputs['Detail'].default_value = 10.0
    fine.inputs['Roughness'].default_value = 0.7
    L(uv.outputs['UV'], fine.inputs['Vector'])
    h = nt.nodes.new('ShaderNodeMix')
    h.data_type = 'FLOAT'
    h.inputs['Factor'].default_value = 0.45
    L(fine.outputs['Fac'], h.inputs[2])
    L(fr.outputs[0], h.inputs[3])
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 0.42
    bp.inputs['Distance'].default_value = 0.045
    L(h.outputs[0], bp.inputs['Height'])
    L(bp.outputs['Normal'], bsdf.inputs['Normal'])
    return m


def mat_tile_solid(name="tile_dark"):
    """Tiles for swept geometry (no UVs) - object space."""
    m, nt, bsdf, out = _new(name)
    L = nt.links.new
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 9.0
    nz.inputs['Detail'].default_value = 10.0
    nz.inputs['Roughness'].default_value = 0.6
    L(tc.outputs['Object'], nz.inputs['Vector'])
    rp = _ramp(nt, [(0.30, (0.030, 0.033, 0.039)),
                    (0.55, (0.062, 0.066, 0.072)),
                    (0.75, (0.096, 0.098, 0.104))])
    L(nz.outputs['Fac'], rp.inputs['Fac'])
    L(rp.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.72
    bsdf.inputs['Specular IOR Level'].default_value = 0.12
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 0.22
    bp.inputs['Distance'].default_value = 0.01
    L(nz.outputs['Fac'], bp.inputs['Height'])
    L(bp.outputs['Normal'], bsdf.inputs['Normal'])
    return m


# --------------------------------------------------------------------------- #
#  cut stone (platform, steps, plinths)
# --------------------------------------------------------------------------- #
def mat_stone(name="stone", base=(0.40, 0.395, 0.375), joint=0.85,
              course=0.55, brick=True):
    m, nt, bsdf, out = _new(name)
    L = nt.links.new
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 3.2
    nz.inputs['Detail'].default_value = 12.0
    nz.inputs['Roughness'].default_value = 0.68
    L(tc.outputs['Object'], nz.inputs['Vector'])
    rp = _ramp(nt, [(0.30, (base[0] * 0.62, base[1] * 0.62, base[2] * 0.62)),
                    (0.55, base),
                    (0.80, (base[0] * 1.30, base[1] * 1.28, base[2] * 1.22))])
    L(nz.outputs['Fac'], rp.inputs['Fac'])
    col = rp.outputs['Color']
    hgt = nz.outputs['Fac']
    if brick:
        br = nt.nodes.new('ShaderNodeTexBrick')
        br.offset = 0.5
        br.inputs['Scale'].default_value = course
        br.inputs['Mortar Size'].default_value = 0.014
        br.inputs['Mortar Smooth'].default_value = 0.35
        br.inputs['Brick Width'].default_value = 0.75
        br.inputs['Row Height'].default_value = 0.36
        br.inputs['Color1'].default_value = (0.92, 0.92, 0.90, 1)
        br.inputs['Color2'].default_value = (0.66, 0.66, 0.64, 1)
        br.inputs['Mortar'].default_value = (0.30, 0.29, 0.27, 1)
        L(tc.outputs['Object'], br.inputs['Vector'])
        dm = nt.nodes.new('ShaderNodeMix')
        dm.data_type = 'RGBA'
        dm.blend_type = 'MULTIPLY'
        dm.inputs['Factor'].default_value = joint
        L(col, dm.inputs[6])
        L(br.outputs['Color'], dm.inputs[7])
        col = dm.outputs[2]
        hc = nt.nodes.new('ShaderNodeMix')
        hc.data_type = 'FLOAT'
        hc.inputs['Factor'].default_value = 0.85
        L(hgt, hc.inputs[2])
        L(br.outputs['Fac'], hc.inputs[3])
        hgt = hc.outputs[0]
    L(col, bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.80
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 0.30
    bp.inputs['Distance'].default_value = 0.03
    L(hgt, bp.inputs['Height'])
    L(bp.outputs['Normal'], bsdf.inputs['Normal'])
    return m


# --------------------------------------------------------------------------- #
#  bronze / gilt bronze
# --------------------------------------------------------------------------- #
def mat_metal(name, c1, c2, metallic=0.9, rough=0.42, patina=0.0):
    m, nt, bsdf, out = _new(name)
    L = nt.links.new
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 9.0
    nz.inputs['Detail'].default_value = 10.0
    nz.inputs['Roughness'].default_value = 0.62
    L(tc.outputs['Object'], nz.inputs['Vector'])
    rp = _ramp(nt, [(0.30, c1), (0.55, c2),
                    (0.75, tuple(a * 0.72 + b * 0.28 for a, b in zip(c1, c2)))])
    L(nz.outputs['Fac'], rp.inputs['Fac'])
    col = rp.outputs['Color']
    if patina > 0:
        nz2 = nt.nodes.new('ShaderNodeTexNoise')
        nz2.inputs['Scale'].default_value = 2.4
        nz2.inputs['Detail'].default_value = 8.0
        L(tc.outputs['Object'], nz2.inputs['Vector'])
        pr = _ramp(nt, [(0.40, (0, 0, 0)), (0.72, (1, 1, 1))])
        L(nz2.outputs['Fac'], pr.inputs['Fac'])
        pm = nt.nodes.new('ShaderNodeMix')
        pm.data_type = 'RGBA'
        pm.blend_type = 'MIX'
        pm.inputs['Factor'].default_value = patina
        L(col, pm.inputs[6])
        pm.inputs[7].default_value = (0.10, 0.19, 0.15, 1)
        L(pr.outputs['Color'], pm.inputs['Factor'])
        col = pm.outputs[2]
    L(col, bsdf.inputs['Base Color'])
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = rough
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 0.22
    bp.inputs['Distance'].default_value = 0.008
    L(nz.outputs['Fac'], bp.inputs['Height'])
    L(bp.outputs['Normal'], bsdf.inputs['Normal'])
    return m


# --------------------------------------------------------------------------- #
#  ground gravel
# --------------------------------------------------------------------------- #
def mat_ground(name="gravel"):
    m, nt, bsdf, out = _new(name)
    L = nt.links.new
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (0.22, 0.22, 0.22)
    L(tc.outputs['Object'], mp.inputs['Vector'])
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = _img('gravel_embedded_concrete_diff_2k.jpg')
    t.projection = 'BOX'
    t.projection_blend = 0.3
    L(mp.outputs['Vector'], t.inputs['Vector'])
    tint = nt.nodes.new('ShaderNodeMix')
    tint.data_type = 'RGBA'
    tint.blend_type = 'MULTIPLY'
    tint.inputs['Factor'].default_value = 1.0
    L(t.outputs['Color'], tint.inputs[6])
    tint.inputs[7].default_value = (0.86, 0.83, 0.78, 1)
    # large scale patchiness
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 0.06
    nz.inputs['Detail'].default_value = 6.0
    L(tc.outputs['Object'], nz.inputs['Vector'])
    pr = _ramp(nt, [(0.32, (0.58, 0.57, 0.53)), (0.60, (1.06, 1.05, 1.0)),
                    (0.85, (0.78, 0.76, 0.70))])
    L(nz.outputs['Fac'], pr.inputs['Fac'])
    pm = nt.nodes.new('ShaderNodeMix')
    pm.data_type = 'RGBA'
    pm.blend_type = 'MULTIPLY'
    pm.inputs['Factor'].default_value = 0.85
    L(tint.outputs[2], pm.inputs[6])
    L(pr.outputs['Color'], pm.inputs[7])
    L(pm.outputs[2], bsdf.inputs['Base Color'])
    rgh = nt.nodes.new('ShaderNodeTexImage')
    rgh.image = _img('gravel_embedded_concrete_rough_2k.exr', True)
    rgh.projection = 'BOX'
    L(mp.outputs['Vector'], rgh.inputs['Vector'])
    L(rgh.outputs['Color'], bsdf.inputs['Roughness'])
    nrt = nt.nodes.new('ShaderNodeTexImage')
    nrt.image = _img('gravel_embedded_concrete_nor_gl_2k.exr', True)
    nrt.projection = 'BOX'
    L(mp.outputs['Vector'], nrt.inputs['Vector'])
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nm.inputs['Strength'].default_value = 0.9
    L(nrt.outputs['Color'], nm.inputs['Color'])
    L(nm.outputs['Normal'], bsdf.inputs['Normal'])
    return m


# --------------------------------------------------------------------------- #
#  foliage / bark
# --------------------------------------------------------------------------- #
def mat_foliage(name="foliage", c1=(0.045, 0.085, 0.028),
                c2=(0.13, 0.20, 0.055), scale=1.0):
    m, nt, bsdf, out = _new(name)
    L = nt.links.new
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 5.0 * scale
    nz.inputs['Detail'].default_value = 12.0
    nz.inputs['Roughness'].default_value = 0.7
    L(tc.outputs['Object'], nz.inputs['Vector'])
    rp = _ramp(nt, [(0.30, c1), (0.55, tuple((a + b) / 2 for a, b in zip(c1, c2))),
                    (0.78, c2)])
    L(nz.outputs['Fac'], rp.inputs['Fac'])
    L(rp.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.85
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 0.65
    bp.inputs['Distance'].default_value = 0.06
    L(nz.outputs['Fac'], bp.inputs['Height'])
    L(bp.outputs['Normal'], bsdf.inputs['Normal'])
    return m


# --------------------------------------------------------------------------- #
def build_materials():
    # ---- timber ----------------------------------------------------------
    # vertical grain for columns / posts
    pbr("wood_col", "stained_pine", scale=(2.4, 2.4, 0.30),
        tint=(0.78, 0.73, 0.67), rough_mul=1.0, nor=1.0,
        grime=0.45, grime_col=(0.42, 0.40, 0.36), grime_scale=1.1)
    # horizontal grain for beams
    pbr("wood_beam", "stained_pine", scale=(0.30, 2.4, 2.4),
        tint=(0.82, 0.76, 0.69), rough_mul=1.0, nor=1.0,
        grime=0.42, grime_col=(0.40, 0.38, 0.34), grime_scale=1.4)
    # thin members (rafters, brackets): coarser, darker
    pbr("wood_dark", "stained_pine", scale=(2.2, 0.42, 2.2),
        tint=(0.62, 0.55, 0.48), rough_mul=1.05, nor=1.0,
        grime=0.55, grime_col=(0.30, 0.28, 0.25), grime_scale=1.8)
    # freshly sanded / sunlit timber (doors, veranda deck)
    pbr("wood_light", "stained_pine", scale=(0.9, 0.9, 0.9),
        tint=(1.25, 1.16, 1.04), rough_mul=0.95, nor=1.0,
        grime=0.22, grime_col=(0.62, 0.58, 0.52), grime_scale=1.2)
    # deep shadow wood (soffits, recesses)
    pbr("wood_shadow", "stained_pine", scale=(1.1, 1.1, 1.1),
        tint=(0.20, 0.18, 0.16), rough_mul=1.1, nor=1.0)
    # 丹塗り : the red-ochre paint of the columns, beams and brackets
    mat_paint("vermilion", (0.106, 0.063, 0.043), rough=0.70, grain=0.38,
              tint2=(0.050, 0.030, 0.021), scale=1.0)
    mat_paint("vermilion_b", (0.078, 0.048, 0.034), rough=0.78, grain=0.34,
              tint2=(0.038, 0.024, 0.018), scale=1.6)
    # underside of the eaves: shaded timber with visible rafters
    mat_paint("soffit_wood", (0.046, 0.032, 0.023), rough=0.90, grain=0.30,
              tint2=(0.022, 0.016, 0.012), scale=2.2)
    # 軒丸瓦 - the pale tile mouths along the eave
    mat_paint("tile_edge", (0.225, 0.225, 0.216), rough=0.66, grain=0.24,
              tint2=(0.140, 0.140, 0.134), scale=3.0)
    # ---- plaster ---------------------------------------------------------
    mat_lime("plaster", (0.760, 0.740, 0.690), mottle=0.050, rough=0.86,
             bump=0.10, streak=0.18, scale=0.9)
    # 軒裏 : the white plaster soffits under the eaves (a hallmark of Horyuji)
    mat_lime("plaster_soffit", (0.520, 0.500, 0.452), mottle=0.070, rough=0.90,
             bump=0.12, streak=0.30, scale=1.3)
    # ---- roof ------------------------------------------------------------
    mat_tile("tile")
    mat_tile_solid("tile_dark")
    # ---- stone -----------------------------------------------------------
    mat_stone("stone", base=(0.44, 0.43, 0.41), joint=0.9, course=0.75)
    mat_stone("stone_step", base=(0.40, 0.385, 0.355), joint=0.55, course=1.4,
              brick=False)
    # ---- metal -----------------------------------------------------------
    mat_metal("bronze", (0.042, 0.055, 0.043), (0.088, 0.105, 0.082),
              metallic=0.85, rough=0.44, patina=0.55)
    mat_metal("bronze_l", (0.115, 0.115, 0.085), (0.205, 0.200, 0.150),
              metallic=0.90, rough=0.38, patina=0.35)
    mat_metal("gold", (0.62, 0.44, 0.13), (0.86, 0.66, 0.24),
              metallic=1.0, rough=0.24)
    # ---- environment -----------------------------------------------------
    mat_ground("gravel")
    mat_foliage("foliage", (0.022, 0.050, 0.014), (0.075, 0.135, 0.032))
    mat_foliage("foliage_dark", (0.012, 0.030, 0.010), (0.045, 0.085, 0.022))
    mat_foliage("bark", (0.075, 0.062, 0.048), (0.140, 0.118, 0.092), scale=3.0)
