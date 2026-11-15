"""材质库：土朱木构 / 青灰瓦 / 白灰墙 / 石台基

原则：构件尺度大，颜色以大面均匀为主，纹理只做"高频细节 + 极低频色差"，
避免出现明显条带或斑块。
"""
import bpy, math


def srgb(hexstr):
    h = hexstr.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]

    def f(u):
        return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4
    return (f(c[0]), f(c[1]), f(c[2]), 1.0)


def shade(color, k):
    return (min(1, color[0] * k), min(1, color[1] * k), min(1, color[2] * k), 1.0)


def _new(name):
    m = bpy.data.materials.get(name)
    if m:
        bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            nt.nodes.remove(n)
    out = nt.nodes.get("Material Output")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.location = (300, 0)
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    return m, nt, b


def _coord(nt):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    tc.location = (-1100, 0)
    return tc


def _ramp(nt, stops, loc=(0, 0)):
    r = nt.nodes.new("ShaderNodeValToRGB")
    r.location = loc
    el = r.color_ramp.elements
    while len(el) > 1:
        el.remove(el[-1])
    el[0].position = stops[0][0]
    el[0].color = stops[0][1]
    for p, c in stops[1:]:
        e = el.new(p)
        e.color = c
    return r


def _noise(nt, tc, scale, detail, rough=0.55, loc=(-850, 0)):
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.location = loc
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = rough
    nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
    return n


def _bump(nt, src, strength, dist, loc=(-360, -320)):
    bp = nt.nodes.new("ShaderNodeBump")
    bp.location = loc
    bp.inputs["Strength"].default_value = strength
    bp.inputs["Distance"].default_value = dist
    nt.links.new(src, bp.inputs["Height"])
    return bp



def _mix(nt, a_socket, b_color, fac_socket, loc=(0, 0)):
    mx = nt.nodes.new("ShaderNodeMix")
    mx.data_type = 'RGBA'
    mx.blend_type = 'MIX'
    mx.location = loc
    nt.links.new(fac_socket, mx.inputs[0])
    nt.links.new(a_socket, mx.inputs[6])
    mx.inputs[7].default_value = b_color
    return mx


def _grime(nt, tc, base_z=-0.2, top_z=3.2, strength=0.55):
    """近地风化：越靠下越脏"""
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    sep.location = (-860, -560)
    nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.location = (-660, -560)
    mr.inputs["From Min"].default_value = base_z
    mr.inputs["From Max"].default_value = top_z
    mr.inputs["To Min"].default_value = strength
    mr.inputs["To Max"].default_value = 0.0
    mr.clamp = True
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    return mr.outputs["Result"]


def wood(name, color, rough=0.72, var=0.10, fiber=34.0, bump=0.12):
    """木构：无条带，仅极低频色差 + 细木纤维凹凸"""
    m, nt, b = _new(name)
    tc = _coord(nt)
    nz = _noise(nt, tc, 0.45, 3, 0.5, (-850, 160))
    ramp = _ramp(nt, [(0.36, shade(color, 1 - var)), (0.52, color), (0.70, shade(color, 1 + var * 0.7))],
                 (-560, 160))
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    gf = _grime(nt, tc, -0.3, 2.6, 0.5)
    mx = _mix(nt, ramp.outputs["Color"], shade(color, 0.62), gf, (-300, 180))
    nt.links.new(mx.outputs[2], b.inputs["Base Color"])

    fib = nt.nodes.new("ShaderNodeTexWave")
    fib.location = (-850, -220)
    fib.wave_type = 'BANDS'
    fib.bands_direction = 'X'
    fib.inputs["Scale"].default_value = fiber
    fib.inputs["Distortion"].default_value = 6.0
    fib.inputs["Detail"].default_value = 2.0
    nt.links.new(tc.outputs["Object"], fib.inputs["Vector"])
    bp = _bump(nt, fib.outputs["Fac"], bump, 0.003)
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])

    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = 0.30
    return m


def plaster(name, color, rough=0.9, var=0.06):
    m, nt, b = _new(name)
    tc = _coord(nt)
    nz = _noise(nt, tc, 1.6, 6, 0.55, (-850, 160))
    ramp = _ramp(nt, [(0.36, shade(color, 1 - var)), (0.54, color), (0.72, shade(color, 1 + var))],
                 (-560, 160))
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    gf = _grime(nt, tc, -0.3, 3.4, 0.45)
    mx = _mix(nt, ramp.outputs["Color"], shade(color, 0.60), gf, (-300, 180))
    nt.links.new(mx.outputs[2], b.inputs["Base Color"])

    fine = _noise(nt, tc, 190.0, 4, 0.6, (-850, -240))
    bp = _bump(nt, fine.outputs["Fac"], 0.14, 0.003)
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = 0.16
    return m


def tile_mat(name, color, rough=0.55, var=0.13):
    m, nt, b = _new(name)
    tc = _coord(nt)
    nz = _noise(nt, tc, 2.2, 8, 0.62, (-850, 160))
    ramp = _ramp(nt, [(0.36, shade(color, 1 - var)), (0.54, color), (0.72, shade(color, 1 + var))],
                 (-560, 160))
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])

    grain = _noise(nt, tc, 260.0, 3, 0.5, (-850, -240))
    bp = _bump(nt, grain.outputs["Fac"], 0.12, 0.003)
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = 0.36
    return m


def stone(name, color, rough=0.84, var=0.10):
    m, nt, b = _new(name)
    tc = _coord(nt)
    nz = _noise(nt, tc, 1.2, 8, 0.6, (-850, 160))
    ramp = _ramp(nt, [(0.38, shade(color, 1 - var)), (0.55, color), (0.72, shade(color, 1 + var))],
                 (-560, 160))
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.location = (-850, -240)
    vor.inputs["Scale"].default_value = 70.0
    nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
    bp = _bump(nt, vor.outputs["Distance"], 0.15, 0.004)
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = 0.24
    return m


def paving(name, color, mortar, rough=0.88, bw=1.6, rh=0.95):
    """地面/台面铺石"""
    m, nt, b = _new(name)
    tc = _coord(nt)
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.location = (-800, 120)
    br.offset = 0.5
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Mortar Size"].default_value = 0.035
    br.inputs["Brick Width"].default_value = bw
    br.inputs["Row Height"].default_value = rh
    br.inputs["Color1"].default_value = shade(color, 1.06)
    br.inputs["Color2"].default_value = shade(color, 0.90)
    br.inputs["Mortar"].default_value = mortar
    nt.links.new(tc.outputs["Object"], br.inputs["Vector"])
    nz = _noise(nt, tc, 3.0, 6, 0.6, (-800, -180))
    mixv = nt.nodes.new("ShaderNodeMix")
    mixv.data_type = 'RGBA'
    mixv.blend_type = 'MULTIPLY'
    mixv.inputs[0].default_value = 0.55
    mixv.location = (-520, 60)
    nt.links.new(br.outputs["Color"], mixv.inputs[6])
    cr = _ramp(nt, [(0.35, (0.82, 0.82, 0.82, 1)), (0.65, (1.05, 1.05, 1.05, 1))], (-800, -400))
    nt.links.new(nz.outputs["Fac"], cr.inputs["Fac"])
    nt.links.new(cr.outputs["Color"], mixv.inputs[7])
    nt.links.new(mixv.outputs[2], b.inputs["Base Color"])
    bp = _bump(nt, br.outputs["Fac"], 0.30, 0.02)
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = 0.2
    return m


def metal(name, color, rough=0.42, metalval=0.9):
    m, nt, b = _new(name)
    b.inputs["Base Color"].default_value = color
    b.inputs["Metallic"].default_value = metalval
    b.inputs["Roughness"].default_value = rough
    return m


def build_all():
    M = {}
    M["wood_red"] = wood("M_wuta_red", srgb("#84503A"), 0.72, 0.12, 30.0, 0.14)
    M["wood_dark"] = wood("M_wuta_dark", srgb("#6B4029"), 0.76, 0.13, 34.0, 0.16)
    M["wood_door"] = wood("M_door", srgb("#8A5036"), 0.68, 0.11, 18.0, 0.16)
    M["plaster"] = plaster("M_plaster", srgb("#B4A78C"), 0.90, 0.05)
    M["wall_red"] = plaster("M_wall_red", srgb("#8E4E38"), 0.88, 0.07)
    M["tile"] = tile_mat("M_tile", srgb("#585C61"), 0.60, 0.16)
    M["tile_gap"] = tile_mat("M_tile_gap", srgb("#41454A"), 0.72, 0.18)
    M["tile_ridge"] = tile_mat("M_tile_ridge", srgb("#393C41"), 0.62, 0.14)
    M["stone"] = stone("M_stone", srgb("#9E9483"), 0.84, 0.10)
    M["stone_dark"] = stone("M_stone_dark", srgb("#9B9282"), 0.86, 0.10)
    M["iron"] = metal("M_iron", srgb("#332F29"), 0.44, 0.88)
    M["stud"] = metal("M_stud", srgb("#6B5B44"), 0.42, 0.75)
    M["gold"] = metal("M_gold", srgb("#BF9349"), 0.34, 1.0)
    M["bronze"] = metal("M_bronze", srgb("#6A5838"), 0.45, 0.85)
    M["plaque"] = wood("M_plaque", srgb("#3B2C1E"), 0.55, 0.10, 12.0, 0.10)
    M["ground"] = paving("M_ground", srgb("#9C9585"), srgb("#7E7768"), 0.9, 1.7, 1.0)
    M["pave"] = paving("M_pave", srgb("#B0A897"), srgb("#958D7C"), 0.9, 1.2, 0.72)
    return M
