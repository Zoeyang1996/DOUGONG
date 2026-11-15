# -*- coding: utf-8 -*-
"""保国寺大殿 · 建模核心库
网格累加器 / 程序化材质 / 文字工具
"""
import bpy, bmesh, math, os
from mathutils import Vector, Matrix

TAU = math.pi * 2.0
FONT_CALLI = "C:/Windows/Fonts/simkai.ttf"     # 楷体，用于匾额（含繁体字）
FONT_HEI = "C:/Windows/Fonts/simhei.ttf"


# ----------------------------------------------------------------------------
# 颜色
# ----------------------------------------------------------------------------
def s2l(c):
    out = []
    for v in c:
        if v > 1.0:
            v = v / 255.0
        out.append(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4)
    return tuple(out)


def hx(h):
    h = h.lstrip('#')
    return s2l(tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)))


# ----------------------------------------------------------------------------
# 网格累加器
# ----------------------------------------------------------------------------
class MeshAccum:
    """把大量基本体累加到一个网格里，最终生成单个可编辑对象。"""

    def __init__(self):
        self.v = []
        self.f = []

    # -- 底层 ----------------------------------------------------------------
    def add(self, verts, faces, M=None):
        o = len(self.v)
        if M is None:
            self.v.extend(verts)
        else:
            self.v.extend([M @ Vector(p) for p in verts])
        self.f.extend([tuple(i + o for i in fc) for fc in faces])

    # -- 盒体 ----------------------------------------------------------------
    def box(self, c, s, M=None):
        cx, cy, cz = (0.0, 0.0, 0.0) if M is not None else c
        hx_, hy_, hz_ = s[0] / 2.0, s[1] / 2.0, s[2] / 2.0
        v = [(cx - hx_, cy - hy_, cz - hz_), (cx + hx_, cy - hy_, cz - hz_),
             (cx + hx_, cy + hy_, cz - hz_), (cx - hx_, cy + hy_, cz - hz_),
             (cx - hx_, cy - hy_, cz + hz_), (cx + hx_, cy - hy_, cz + hz_),
             (cx + hx_, cy + hy_, cz + hz_), (cx - hx_, cy + hy_, cz + hz_)]
        f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        if M is None:
            self.add(v, f)
        else:
            off = Vector(c)
            self.v.extend([tuple(M @ Vector(p) + off) for p in v])
            o = len(self.v) - len(v)
            self.f.extend([tuple(i + o for i in fc) for fc in f])

    def box2(self, x0, x1, y0, y1, z0, z1, M=None):
        self.box(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2),
                 (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)), M)

    # -- 棱台（上下不同截面，用于斗、柱础、收分） -----------------------------
    def frustum(self, c, sb, st, h, M=None, z_off=0.0):
        cx, cy, cz = c
        bx, by = sb[0] / 2, sb[1] / 2
        tx, ty = st[0] / 2, st[1] / 2
        z0, z1 = cz - h / 2 + z_off, cz + h / 2 + z_off
        v = [(cx - bx, cy - by, z0), (cx + bx, cy - by, z0),
             (cx + bx, cy + by, z0), (cx - bx, cy + by, z0),
             (cx - tx, cy - ty, z1), (cx + tx, cy - ty, z1),
             (cx + tx, cy + ty, z1), (cx - tx, cy + ty, z1)]
        f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        self.add(v, f, M)

    # -- 圆柱 / 圆台 ---------------------------------------------------------
    def cyl(self, c, r, h, seg=20, M=None, rtop=None, caps=True, arc=None):
        """arc=(a0,a1) 可生成扇形柱（未封口）。给定 M 时先绕原点旋转再平移到 c"""
        rtop = r if rtop is None else rtop
        cx, cy, cz = (0.0, 0.0, 0.0) if M is not None else c
        a0, a1 = (0.0, TAU) if arc is None else arc
        v, f = [], []
        n = seg
        for k in range(n):
            a = a0 + (a1 - a0) * k / n
            ca, sa = math.cos(a), math.sin(a)
            v.append((cx + r * ca, cy + r * sa, cz - h / 2))
        for k in range(n):
            a = a0 + (a1 - a0) * k / n
            ca, sa = math.cos(a), math.sin(a)
            v.append((cx + rtop * ca, cy + rtop * sa, cz + h / 2))
        closed = arc is None
        for k in range(n if closed else n - 1):
            k2 = (k + 1) % n
            f.append((k, k2, n + k2, n + k))
        if closed and caps:
            f.append(tuple(range(n - 1, -1, -1)))
            f.append(tuple(range(n, 2 * n)))
        if M is not None:
            off = Vector(c)
            self.v.extend([tuple(M @ Vector(p) + off) for p in v])
            o = len(self.v) - len(v)
            self.f.extend([tuple(i + o for i in fc) for fc in f])
        else:
            self.add(v, f)

    # -- 放样环（管、脊、线脚） ----------------------------------------------
    def loft(self, rings, closed_profile=False, cap_ends=False):
        """rings: list of list of (x,y,z) —— 每环点数相同"""
        n = len(rings[0])
        base = len(self.v)
        for ring in rings:
            self.v.extend([tuple(p) for p in ring])
        m = n if closed_profile else n - 1
        for i in range(len(rings) - 1):
            a = base + i * n
            b = base + (i + 1) * n
            for k in range(m):
                k2 = (k + 1) % n
                self.f.append((a + k, a + k2, b + k2, b + k))
        if cap_ends:
            self.f.append(tuple(range(base + n - 1, base - 1, -1)))
            last = base + (len(rings) - 1) * n
            self.f.append(tuple(range(last, last + n)))

    # -- 网格面（高度场） -----------------------------------------------------
    def grid(self, nx, ny, fn, flip=False):
        """fn(i,j) -> (x,y,z)"""
        base = len(self.v)
        for j in range(ny + 1):
            for i in range(nx + 1):
                self.v.append(tuple(fn(i, j)))
        for j in range(ny):
            for i in range(nx):
                a = base + j * (nx + 1) + i
                b = a + 1
                c = a + nx + 2
                d = a + nx + 1
                self.f.append((a, d, c, b) if flip else (a, b, c, d))

    # -- 输出 ----------------------------------------------------------------
    def finish(self, name, mat, coll, bevel=0.0, smooth=False, seg=2, angle=40):
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(p) for p in self.v], [], self.f)
        me.validate(verbose=False)
        me.update()
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        if mat is not None:
            me.materials.append(mat)
        if smooth:
            for p in me.polygons:
                p.use_smooth = True
        if bevel > 0:
            md = ob.modifiers.new("倒角", 'BEVEL')
            md.width = bevel
            md.segments = seg
            md.limit_method = 'ANGLE'
            md.angle_limit = math.radians(angle)
            md.harden_normals = False
        return ob


def recalc(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()


# ----------------------------------------------------------------------------
# 材质
# ----------------------------------------------------------------------------
def _mat(name):
    m = bpy.data.materials.get(name)
    if m:
        bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    out.location = (420, 0)
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    b.location = (200, 0)
    nt.links.new(b.outputs[0], out.inputs[0])
    return m, nt, b


def _coord(nt, scale=1.0, loc=(0, 0)):
    tc = nt.nodes.new('ShaderNodeTexCoord')
    tc.location = (loc[0] - 400, loc[1])
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.location = (loc[0] - 220, loc[1])
    mp.inputs['Scale'].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    return mp.outputs['Vector']


def _set(b, key, val):
    if key in b.inputs:
        b.inputs[key].default_value = val


def mat_simple(name, hexcol, rough=0.6, metal=0.0, spec=0.5):
    m, nt, b = _mat(name)
    _set(b, "Base Color", (*hx(hexcol), 1))
    _set(b, "Roughness", rough)
    _set(b, "Metallic", metal)
    if "Specular IOR Level" in b.inputs:
        b.inputs["Specular IOR Level"].default_value = spec
    m.diffuse_color = (*hx(hexcol), 1)
    return m


def mat_surface(name, hex_a, hex_b, scale=6.0, rough=0.7, bump=0.15,
                bump_scale=60.0, detail=8.0, rough_var=0.0, mix=0.5,
                grime=None):
    """双色噪波混合的做旧表面"""
    m, nt, b = _mat(name)
    vec = _coord(nt, 1.0)
    n1 = nt.nodes.new('ShaderNodeTexNoise')
    n1.inputs['Scale'].default_value = scale
    n1.inputs['Detail'].default_value = detail
    n1.inputs['Roughness'].default_value = 0.55
    n1.location = (-60, 200)
    nt.links.new(vec, n1.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.location = (140, 200)
    ramp.color_ramp.elements[0].position = 0.30 + (0.5 - mix) * 0.3
    ramp.color_ramp.elements[1].position = 0.68 + (0.5 - mix) * 0.3
    ramp.color_ramp.elements[0].color = (*hx(hex_a), 1)
    ramp.color_ramp.elements[1].color = (*hx(hex_b), 1)
    nt.links.new(n1.outputs['Fac'], ramp.inputs['Fac'])
    gout = _grime(nt, ramp.outputs['Color'], 1.0, 4.6, 0.52)
    nt.links.new(gout, b.inputs['Base Color'])
    m.diffuse_color = (*hx(hex_b), 1)
    _set(b, "Roughness", rough)
    if rough_var > 0:
        r2 = nt.nodes.new('ShaderNodeMapRange')
        r2.inputs['To Min'].default_value = max(0.05, rough - rough_var)
        r2.inputs['To Max'].default_value = min(1.0, rough + rough_var)
        nt.links.new(n1.outputs['Fac'], r2.inputs['Value'])
        nt.links.new(r2.outputs['Result'], b.inputs['Roughness'])
    # 凹凸
    n2 = nt.nodes.new('ShaderNodeTexNoise')
    n2.inputs['Scale'].default_value = bump_scale
    n2.inputs['Detail'].default_value = 10
    n2.location = (-60, -180)
    nt.links.new(vec, n2.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = bump
    bp.inputs['Distance'].default_value = 0.02
    bp.location = (140, -180)
    nt.links.new(n2.outputs['Fac'], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m



def _grime(nt, color_socket, z0=1.0, z1=4.2, k=0.55):
    """按高度做旧：底部积尘、上部干净"""
    tc = nt.nodes.new('ShaderNodeTexCoord')
    tc.location = (-620, -420)
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    sep.location = (-440, -420)
    nt.links.new(tc.outputs['Object'], sep.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.location = (-260, -420)
    mr.inputs['From Min'].default_value = z0
    mr.inputs['From Max'].default_value = z1
    mr.inputs['To Min'].default_value = k
    mr.inputs['To Max'].default_value = 1.0
    mr.clamp = True
    nt.links.new(sep.outputs['Z'], mr.inputs['Value'])
    comb = nt.nodes.new('ShaderNodeCombineColor')
    comb.location = (-80, -420)
    for i in range(3):
        nt.links.new(mr.outputs['Result'], comb.inputs[i])
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.blend_type = 'MULTIPLY'
    mix.location = (60, -300)
    mix.inputs[0].default_value = 1.0
    ins = [s for s in mix.inputs if s.type == 'RGBA']
    outs = [s for s in mix.outputs if s.type == 'RGBA']
    nt.links.new(color_socket, ins[0])
    nt.links.new(comb.outputs[0], ins[1])
    return outs[0]


def mat_wood(name, hex_a, hex_b, axis='Z', scale=3.0, rough=0.55, bump=0.12):
    """木纹：沿轴向拉长的波纹 + 噪波"""
    m, nt, b = _mat(name)
    vec = _coord(nt, 1.0)
    mp2 = nt.nodes.new('ShaderNodeMapping')
    mp2.location = (-220, -20)
    sc = {'X': (0.25, 8.0, 8.0), 'Y': (8.0, 0.25, 8.0), 'Z': (8.0, 8.0, 0.25)}[axis]
    mp2.inputs['Scale'].default_value = sc
    nt.links.new(vec, mp2.inputs['Vector'])

    n1 = nt.nodes.new('ShaderNodeTexNoise')
    n1.inputs['Scale'].default_value = scale * 2.0
    n1.inputs['Detail'].default_value = 9
    n1.inputs['Roughness'].default_value = 0.6
    n1.location = (-40, 60)
    nt.links.new(mp2.outputs['Vector'], n1.inputs['Vector'])
    n1.inputs['Distortion'].default_value = 0.6

    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.location = (160, 60)
    ramp.color_ramp.elements[0].position = 0.34
    ramp.color_ramp.elements[1].position = 0.66
    ramp.color_ramp.elements[0].color = (*hx(hex_a), 1)
    ramp.color_ramp.elements[1].color = (*hx(hex_b), 1)
    nt.links.new(n1.outputs['Fac'], ramp.inputs['Fac'])
    gout = _grime(nt, ramp.outputs['Color'], 1.0, 4.6, 0.52)
    nt.links.new(gout, b.inputs['Base Color'])
    m.diffuse_color = (*hx(hex_b), 1)
    _set(b, "Roughness", rough)

    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = bump
    bp.inputs['Distance'].default_value = 0.01
    bp.location = (160, -160)
    nt.links.new(n1.outputs['Fac'], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


def mat_tile(name="MAT_青瓦"):
    """青瓦：冷灰、带苔痕与烟渍"""
    m, nt, b = _mat(name)
    vec = _coord(nt, 1.0)
    n1 = nt.nodes.new('ShaderNodeTexNoise')
    n1.inputs['Scale'].default_value = 42
    n1.inputs['Detail'].default_value = 9
    n1.location = (-120, 200)
    nt.links.new(vec, n1.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.location = (80, 200)
    ramp.color_ramp.elements[0].position = 0.32
    ramp.color_ramp.elements[1].position = 0.72
    ramp.color_ramp.elements[0].color = (*hx('#33362f'), 1)
    ramp.color_ramp.elements[1].color = (*hx('#4e514a'), 1)
    nt.links.new(n1.outputs['Fac'], ramp.inputs['Fac'])

    # 苔藓/水渍
    n2 = nt.nodes.new('ShaderNodeTexNoise')
    n2.inputs['Scale'].default_value = 5.0
    n2.inputs['Detail'].default_value = 6
    n2.location = (-120, -40)
    nt.links.new(vec, n2.inputs['Vector'])
    r2 = nt.nodes.new('ShaderNodeValToRGB')
    r2.location = (80, -40)
    r2.color_ramp.elements[0].position = 0.55
    r2.color_ramp.elements[1].position = 0.85
    r2.color_ramp.elements[0].color = (0, 0, 0, 1)
    r2.color_ramp.elements[1].color = (0.55, 0.55, 0.55, 1)
    nt.links.new(n2.outputs['Fac'], r2.inputs['Fac'])
    mixc = nt.nodes.new('ShaderNodeMix')
    mixc.data_type = 'RGBA'
    mixc.blend_type = 'MIX'
    ins = [s for s in mixc.inputs if s.type == 'RGBA']
    outs = [s for s in mixc.outputs if s.type == 'RGBA']
    ins[1].default_value = (*hx('#5d6247'), 1)
    mixc.location = (300, 120)
    nt.links.new(r2.outputs['Color'], mixc.inputs[0])
    nt.links.new(ramp.outputs['Color'], ins[0])
    nt.links.new(outs[0], b.inputs['Base Color'])
    m.diffuse_color = (*hx('#3d4244'), 1)
    _set(b, "Roughness", 0.55)

    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 0.25
    bp.inputs['Distance'].default_value = 0.015
    bp.location = (300, -180)
    nt.links.new(n1.outputs['Fac'], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


def mat_gold(name="MAT_鎏金"):
    m, nt, b = _mat(name)
    _set(b, "Base Color", (*hx('#c9a253'), 1))
    _set(b, "Metallic", 0.95)
    _set(b, "Roughness", 0.28)
    m.diffuse_color = (*hx('#c9a253'), 1)
    return m


def mat_paving(name="MAT_铺地"):
    """庭院条石铺装：用砖块纹理做缝"""
    m, nt, b = _mat(name)
    vec = _coord(nt, 1.0)
    br = nt.nodes.new('ShaderNodeTexBrick')
    br.location = (-120, 120)
    br.inputs['Scale'].default_value = 1.0
    br.inputs['Mortar Size'].default_value = 0.012
    br.inputs['Brick Width'].default_value = 1.55
    br.inputs['Row Height'].default_value = 0.95
    br.inputs['Color1'].default_value = (*hx('#8e8b80'), 1)
    br.inputs['Color2'].default_value = (*hx('#7d7a70'), 1)
    br.inputs['Mortar'].default_value = (*hx('#5c5a52'), 1)
    nt.links.new(vec, br.inputs['Vector'])
    nt.links.new(br.outputs['Color'], b.inputs['Base Color'])
    m.diffuse_color = (*hx('#8e8b80'), 1)
    _set(b, "Roughness", 0.82)
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 0.35
    bp.inputs['Distance'].default_value = 0.01
    bp.location = (120, -160)
    nt.links.new(br.outputs['Fac'], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m



def mat_slab(name="MAT_碑面"):
    """石碑面：米白石材 + 细密刻字纹理"""
    m, nt, b = _mat(name)
    vec = _coord(nt, 1.0)
    # 字迹：两个方向的波叠加成细格
    w1 = nt.nodes.new('ShaderNodeTexWave')
    w1.wave_type = 'BANDS'
    w1.bands_direction = 'X'
    w1.inputs['Scale'].default_value = 26.0
    w1.inputs['Distortion'].default_value = 0.6
    w1.inputs['Detail'].default_value = 2.0
    w1.location = (-260, 180)
    nt.links.new(vec, w1.inputs['Vector'])
    w2 = nt.nodes.new('ShaderNodeTexWave')
    w2.wave_type = 'BANDS'
    w2.bands_direction = 'Z'
    w2.inputs['Scale'].default_value = 34.0
    w2.inputs['Distortion'].default_value = 0.4
    w2.location = (-260, -40)
    nt.links.new(vec, w2.inputs['Vector'])
    mul = nt.nodes.new('ShaderNodeMath')
    mul.operation = 'MULTIPLY'
    mul.location = (-60, 80)
    nt.links.new(w1.outputs['Fac'], mul.inputs[0])
    nt.links.new(w2.outputs['Fac'], mul.inputs[1])
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 5.0
    nz.location = (-260, -240)
    nt.links.new(vec, nz.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.location = (140, 120)
    ramp.color_ramp.elements[0].position = 0.28
    ramp.color_ramp.elements[0].color = (*hx('#cfc9ba'), 1)
    ramp.color_ramp.elements[1].position = 0.72
    ramp.color_ramp.elements[1].color = (*hx('#e2ddcf'), 1)
    nt.links.new(nz.outputs['Fac'], ramp.inputs['Fac'])
    mixc = nt.nodes.new('ShaderNodeMix')
    mixc.data_type = 'RGBA'
    mixc.blend_type = 'MULTIPLY'
    mixc.location = (380, 60)
    ins = [s for s in mixc.inputs if s.type == 'RGBA']
    outs = [s for s in mixc.outputs if s.type == 'RGBA']
    nt.links.new(mul.outputs[0], mixc.inputs[0])
    nt.links.new(ramp.outputs['Color'], ins[0])
    ins[1].default_value = (*hx('#8c8577'), 1)
    nt.links.new(outs[0], b.inputs['Base Color'])
    _set(b, "Roughness", 0.74)
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 0.25
    bp.inputs['Distance'].default_value = 0.006
    bp.location = (380, -180)
    nt.links.new(mul.outputs[0], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    m.diffuse_color = (*hx('#dcd6c8'), 1)
    return m


# ----------------------------------------------------------------------------
# 文字
# ----------------------------------------------------------------------------
def make_text(body, size, mat, coll, name, font=FONT_CALLI, extrude=0.03,
              spacing=1.0, loc=(0, 0, 0), rot=(math.pi / 2, 0, 0), bevel=0.0):
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body
    if os.path.exists(font):
        cu.font = bpy.data.fonts.load(font, check_existing=True)
    cu.size = size
    cu.extrude = extrude
    cu.bevel_depth = bevel
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    cu.space_character = spacing
    cu.resolution_u = 6
    ob = bpy.data.objects.new(name, cu)
    coll.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = rot
    if mat:
        cu.materials.append(mat)
    return ob


# ----------------------------------------------------------------------------
# 场景工具
# ----------------------------------------------------------------------------
def new_coll(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    return c


def clean_scene():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for me in list(bpy.data.meshes):
        if me.users == 0:
            bpy.data.meshes.remove(me)


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)
