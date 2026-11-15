# -*- coding: utf-8 -*-
"""
太和殿 Blender 建模工具库
lib_taihe.py  —  材质、几何构建器、通用构件函数
"""
import bpy
import bmesh
import math
import random
import os
from mathutils import Vector, Matrix, Euler

TAU = math.pi * 2.0


# ----------------------------------------------------------------------------
# 场景 / 集合
# ----------------------------------------------------------------------------
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 1.0
    return sc


def new_coll(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent if parent else bpy.context.scene.collection).children.link(c)
    return c


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
        if n.type != 'OUTPUT_MATERIAL':
            nt.nodes.remove(n)
    out = nt.nodes['Material Output']
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (-200, 0)
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return m, nt, bsdf


def _noise(nt, scale=8.0, detail=6.0, rough=0.55, loc=(-900, 0), dim='3D'):
    n = nt.nodes.new('ShaderNodeTexNoise')
    n.noise_dimensions = dim
    n.inputs['Scale'].default_value = scale
    n.inputs['Detail'].default_value = detail
    if 'Roughness' in n.inputs:
        n.inputs['Roughness'].default_value = rough
    n.location = loc
    tc = nt.nodes.new('ShaderNodeTexCoord')
    tc.location = (-1100, 0)
    nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
    return n, tc


def _ramp(nt, stops, loc=(-650, 0)):
    r = nt.nodes.new('ShaderNodeValToRGB')
    r.location = loc
    el = r.color_ramp.elements
    while len(el) > 1:
        el.remove(el[-1])
    el[0].position = stops[0][0]
    el[0].color = (*stops[0][1], 1.0)
    for p, c in stops[1:]:
        e = el.new(p)
        e.color = (*c, 1.0)
    return r


def _mix(nt, fac, a, b, loc=(-400, 0)):
    m = nt.nodes.new('ShaderNodeMix')
    m.data_type = 'RGBA'
    m.blend_type = 'MIX'
    m.location = loc
    m.inputs['Factor'].default_value = fac
    nt.links.new(a, m.inputs[6])
    nt.links.new(b, m.inputs[7])
    return m


def mat_glazed_tile(name="MAT_琉璃瓦_黄"):
    """黄琉璃瓦：釉面高光 + 老化污渍 + 竖向流痕"""
    m, nt, b = _mat(name)
    b.inputs['Base Color'].default_value = (0.80, 0.40, 0.045, 1)
    b.inputs['Roughness'].default_value = 0.22
    b.inputs['Metallic'].default_value = 0.0
    if 'Coat Weight' in b.inputs:
        b.inputs['Coat Weight'].default_value = 0.45
        b.inputs['Coat Roughness'].default_value = 0.12
    n, tc = _noise(nt, 2.2, 8.0, 0.62, (-900, 250))
    # 竖向拉伸的流痕
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.location = (-1050, 250)
    mp.inputs['Scale'].default_value = (7.0, 7.0, 0.45)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], n.inputs['Vector'])
    r = _ramp(nt, [(0.35, (0.62, 0.26, 0.025)), (0.60, (0.82, 0.40, 0.048)),
                   (0.82, (0.92, 0.50, 0.075))], (-650, 250))
    nt.links.new(n.outputs['Fac'], r.inputs['Fac'])
    nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
    # 粗糙度变化
    n2, _ = _noise(nt, 6.0, 4.0, 0.5, (-900, -150))
    r2 = _ramp(nt, [(0.2, (0.16, 0.16, 0.16)), (0.8, (0.36, 0.36, 0.36))], (-650, -150))
    nt.links.new(n2.outputs['Fac'], r2.inputs['Fac'])
    nt.links.new(r2.outputs['Color'], b.inputs['Roughness'])
    # 凹凸
    n3, _ = _noise(nt, 55.0, 3.0, 0.5, (-900, -450))
    bmp = nt.nodes.new('ShaderNodeBump')
    bmp.location = (-400, -450)
    bmp.inputs['Strength'].default_value = 0.10
    nt.links.new(n3.outputs['Fac'], bmp.inputs['Height'])
    nt.links.new(bmp.outputs['Normal'], b.inputs['Normal'])
    return m


def mat_lacquer(name, color, rough=0.42, dirt=0.35, scale=1.6):
    """朱红大漆 / 彩画底色：细腻漆膜 + 斑驳老化"""
    m, nt, b = _mat(name)
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    if 'Coat Weight' in b.inputs:
        b.inputs['Coat Weight'].default_value = 0.30
        b.inputs['Coat Roughness'].default_value = 0.22
    n, tc = _noise(nt, scale, 9.0, 0.6, (-900, 200))
    r = _ramp(nt, [(0.36, (0.0, 0.0, 0.0)), (0.58, (0.45, 0.45, 0.45)),
                   (0.72, (1.0, 1.0, 1.0))], (-650, 200))
    nt.links.new(n.outputs['Fac'], r.inputs['Fac'])
    dark = tuple(c * 0.42 for c in color)
    mixc = nt.nodes.new('ShaderNodeMix')
    mixc.data_type = 'RGBA'
    mixc.location = (-380, 200)
    mixc.inputs['Factor'].default_value = dirt
    mixc.inputs[6].default_value = (*dark, 1)
    mixc.inputs[7].default_value = (*color, 1)
    nt.links.new(r.outputs['Color'], mixc.inputs['Factor'])
    nt.links.new(mixc.outputs[2], b.inputs['Base Color'])
    n2, _ = _noise(nt, 120.0, 3.0, 0.5, (-900, -350))
    bmp = nt.nodes.new('ShaderNodeBump')
    bmp.location = (-380, -350)
    bmp.inputs['Strength'].default_value = 0.06
    nt.links.new(n2.outputs['Fac'], bmp.inputs['Height'])
    nt.links.new(bmp.outputs['Normal'], b.inputs['Normal'])
    return m


def mat_marble(name="MAT_汉白玉"):
    """汉白玉：微暖白，杂以灰筋与雨痕"""
    m, nt, b = _mat(name)
    b.inputs['Base Color'].default_value = (0.74, 0.72, 0.665, 1)
    b.inputs['Roughness'].default_value = 0.55
    n, tc = _noise(nt, 3.0, 10.0, 0.62, (-900, 200))
    mpp = nt.nodes.new('ShaderNodeMapping')
    mpp.location = (-1050, 200)
    mpp.inputs['Scale'].default_value = (1.0, 1.0, 2.4)
    nt.links.new(tc.outputs['Object'], mpp.inputs['Vector'])
    nt.links.new(mpp.outputs['Vector'], n.inputs['Vector'])
    r = _ramp(nt, [(0.40, (0.60, 0.585, 0.545)), (0.55, (0.74, 0.725, 0.675)),
                   (0.70, (0.80, 0.785, 0.745))], (-650, 200))
    nt.links.new(n.outputs['Fac'], r.inputs['Fac'])
    nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
    n2, _ = _noise(nt, 40.0, 5.0, 0.6, (-900, -300))
    bmp = nt.nodes.new('ShaderNodeBump')
    bmp.location = (-380, -300)
    bmp.inputs['Strength'].default_value = 0.13
    nt.links.new(n2.outputs['Fac'], bmp.inputs['Height'])
    nt.links.new(bmp.outputs['Normal'], b.inputs['Normal'])
    return m


def mat_gold(name="MAT_沥粉贴金"):
    m, nt, b = _mat(name)
    b.inputs['Base Color'].default_value = (1.0, 0.70, 0.24, 1)
    b.inputs['Metallic'].default_value = 1.0
    b.inputs['Roughness'].default_value = 0.26
    n, _ = _noise(nt, 18.0, 4.0, 0.5, (-800, 0))
    r = _ramp(nt, [(0.3, (0.18, 0.18, 0.18)), (0.7, (0.40, 0.40, 0.40))], (-550, 0))
    nt.links.new(n.outputs['Fac'], r.inputs['Fac'])
    nt.links.new(r.outputs['Color'], b.inputs['Roughness'])
    return m


def mat_simple(name, color, rough=0.5, metal=0.0, coat=0.0):
    m, nt, b = _mat(name)
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if coat and 'Coat Weight' in b.inputs:
        b.inputs['Coat Weight'].default_value = coat
    return m


def mat_wood(name="MAT_木_老榆木", color=(0.145, 0.056, 0.035)):
    """隔扇木作：深褐红木 + 木纹"""
    m, nt, b = _mat(name)
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = 0.5
    tc = nt.nodes.new('ShaderNodeTexCoord')
    tc.location = (-1100, 0)
    w = nt.nodes.new('ShaderNodeTexWave')
    w.location = (-900, 0)
    w.wave_type = 'BANDS'
    w.bands_direction = 'Z'
    w.inputs['Scale'].default_value = 2.4
    w.inputs['Distortion'].default_value = 6.0
    w.inputs['Detail'].default_value = 3.0
    nt.links.new(tc.outputs['Object'], w.inputs['Vector'])
    r = _ramp(nt, [(0.30, tuple(c * 0.62 for c in color)),
                   (0.70, tuple(c * 1.15 for c in color))], (-650, 0))
    nt.links.new(w.outputs['Fac'], r.inputs['Fac'])
    nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
    return m


def mat_caihua_image(name="MAT_彩画_和玺", filepath=None):
    """以程序化生成的彩画贴图作为基色，UV 沿额枋长度展开"""
    m, nt, b = _mat(name)
    b.inputs['Roughness'].default_value = 0.44
    if 'Coat Weight' in b.inputs:
        b.inputs['Coat Weight'].default_value = 0.18
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.location = (-500, 100)
    tex.image = bpy.data.images.load(filepath)
    tex.extension = 'REPEAT'
    tex.interpolation = 'Smart'
    nt.links.new(tex.outputs['Color'], b.inputs['Base Color'])
    return m


# ----------------------------------------------------------------------------
# 几何构建器
# ----------------------------------------------------------------------------
class MB:
    """把大量小构件合并进一个网格，减少物体数量"""

    def __init__(self, name="MB"):
        self.name = name
        self.v = []
        self.f = []
        self.mi = []

    # --- 基础 ---
    def add(self, verts, faces, mi=0, mtx=None):
        base = len(self.v)
        if mtx is not None:
            for p in verts:
                self.v.append(tuple(mtx @ Vector(p)))
        else:
            for p in verts:
                self.v.append(tuple(p))
        for fc in faces:
            self.f.append(tuple(base + i for i in fc))
            self.mi.append(mi)

    def box(self, center, size, mi=0, rz=0.0, rx=0.0, ry=0.0):
        cx, cy, cz = center
        sx, sy, sz = (size[0] / 2.0, size[1] / 2.0, size[2] / 2.0)
        vs = [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
              (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)]
        fs = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
              (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        mtx = Matrix.Translation(Vector(center)) @ Euler((rx, ry, rz)).to_matrix().to_4x4()
        self.add(vs, fs, mi, mtx)

    def box2(self, p0, p1, mi=0):
        """由两个对角点定义轴对齐盒"""
        c = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, (p0[2] + p1[2]) / 2)
        s = (abs(p1[0] - p0[0]), abs(p1[1] - p0[1]), abs(p1[2] - p0[2]))
        self.box(c, s, mi)

    def beam(self, p0, p1, w, h, mi=0, up=(0, 0, 1)):
        """从 p0 到 p1 的方料（沿任意方向）"""
        p0 = Vector(p0)
        p1 = Vector(p1)
        d = (p1 - p0)
        L = d.length
        if L < 1e-6:
            return
        z = Vector(up).normalized()
        x = d.normalized()
        if abs(x.dot(z)) > 0.999:
            z = Vector((0, 1, 0))
            x = d.normalized()
        y = z.cross(x).normalized()
        z = x.cross(y).normalized()
        mtx = Matrix(((x.x, y.x, z.x, p0.x), (x.y, y.y, z.y, p0.y),
                      (x.z, y.z, z.z, p0.z), (0, 0, 0, 1)))
        vs = [(0, -w / 2, -h / 2), (L, -w / 2, -h / 2), (L, w / 2, -h / 2), (0, w / 2, -h / 2),
              (0, -w / 2, h / 2), (L, -w / 2, h / 2), (L, w / 2, h / 2), (0, w / 2, h / 2)]
        fs = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
              (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        self.add(vs, fs, mi, mtx)

    def cyl(self, p0, p1, r, seg=16, mi=0, r2=None, cap=True):
        p0 = Vector(p0)
        p1 = Vector(p1)
        d = p1 - p0
        L = d.length
        if L < 1e-6:
            return
        if r2 is None:
            r2 = r
        z = d.normalized()
        ref = Vector((0, 0, 1))
        if abs(z.dot(ref)) > 0.99:
            ref = Vector((1, 0, 0))
        x = ref.cross(z).normalized()
        y = z.cross(x).normalized()
        base = len(self.v)
        for i in range(seg):
            a = TAU * i / seg
            c, s = math.cos(a), math.sin(a)
            self.v.append(tuple(p0 + x * (c * r) + y * (s * r)))
        for i in range(seg):
            a = TAU * i / seg
            c, s = math.cos(a), math.sin(a)
            self.v.append(tuple(p1 + x * (c * r2) + y * (s * r2)))
        for i in range(seg):
            j = (i + 1) % seg
            self.f.append((base + i, base + j, base + seg + j, base + seg + i))
            self.mi.append(mi)
        if cap:
            self.f.append(tuple(base + i for i in range(seg - 1, -1, -1)))
            self.mi.append(mi)
            self.f.append(tuple(base + seg + i for i in range(seg)))
            self.mi.append(mi)

    def sphere(self, c, r, seg=14, ring=8, mi=0, scale=(1, 1, 1)):
        base = len(self.v)
        for j in range(ring + 1):
            phi = math.pi * j / ring
            for i in range(seg):
                th = TAU * i / seg
                self.v.append((c[0] + r * math.sin(phi) * math.cos(th) * scale[0],
                               c[1] + r * math.sin(phi) * math.sin(th) * scale[1],
                               c[2] + r * math.cos(phi) * scale[2]))
        for j in range(ring):
            for i in range(seg):
                a = base + j * seg + i
                b = base + j * seg + (i + 1) % seg
                cc = base + (j + 1) * seg + (i + 1) % seg
                d = base + (j + 1) * seg + i
                self.f.append((a, b, cc, d))
                self.mi.append(mi)

    def loft(self, rings, mi=0, close_top=False, close_bottom=False, closed_ring=True):
        """rings: list of list of 3D points (same count)"""
        n = len(rings[0])
        base = len(self.v)
        for rg in rings:
            for p in rg:
                self.v.append(tuple(p))
        for k in range(len(rings) - 1):
            a0 = base + k * n
            b0 = base + (k + 1) * n
            rng = range(n) if closed_ring else range(n - 1)
            for i in rng:
                j = (i + 1) % n
                self.f.append((a0 + i, a0 + j, b0 + j, b0 + i))
                self.mi.append(mi)
        if close_bottom:
            self.f.append(tuple(base + (n - 1 - i) for i in range(n)))
            self.mi.append(mi)
        if close_top:
            o = base + (len(rings) - 1) * n
            self.f.append(tuple(o + i for i in range(n)))
            self.mi.append(mi)

    # --- 输出 ---
    def build(self, name, coll, mats, smooth=False, auto_smooth=35.0):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.v, [], self.f)
        me.validate(verbose=False)
        me.update()
        for m in mats:
            me.materials.append(m)
        if self.mi:
            for i, p in enumerate(me.polygons):
                if i < len(self.mi):
                    p.material_index = min(self.mi[i], len(mats) - 1)
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        if smooth:
            for p in me.polygons:
                p.use_smooth = True
        return ob

    def empty(self):
        return len(self.v) == 0


def clean_mesh(ob, merge=0.0008, recalc=True):
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    if merge:
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=merge)
    if recalc:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()


def add_bevel(ob, width=0.012, segments=2, angle=40):
    md = ob.modifiers.new("Bevel", 'BEVEL')
    md.width = width
    md.segments = segments
    md.limit_method = 'ANGLE'
    md.angle_limit = math.radians(angle)
    md.harden_normals = False


# ----------------------------------------------------------------------------
# 彩画贴图（程序化生成）
# ----------------------------------------------------------------------------
def make_caihua_image(path, w=2048, h=256, style="hexi", seed=3):
    """
    生成"金龙和玺"彩画带：
    两端箍头(金/青) — 藻头(旋子花) — 枋心(金龙/绿地)
    贴图沿 U 方向为额枋长度方向。
    """
    import numpy as np
    rng = np.random.default_rng(seed)
    img = np.zeros((h, w, 3), dtype=np.float32)

    QING = np.array([0.075, 0.215, 0.315])   # 石青
    LV = np.array([0.075, 0.245, 0.185])     # 石绿
    JIN = np.array([0.72, 0.50, 0.17])       # 金
    BAI = np.array([0.80, 0.77, 0.68])       # 白粉
    HONG = np.array([0.40, 0.09, 0.07])      # 银朱
    ground_a, ground_b = (QING, LV) if style == "hexi" else (LV, QING)

    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u = xx / w
    v = yy / h

    # 交替青绿：每 1/4 段换色
    seg = (u * 4.0).astype(np.int32) % 2
    img[:] = np.where(seg[..., None] == 0, ground_a, ground_b)

    def rect(u0, u1, v0, v1, col):
        m = (u >= u0) & (u <= u1) & (v >= v0) & (v <= v1)
        img[m] = col

    def hline(v0, v1, col, u0=0.0, u1=1.0):
        rect(u0, u1, v0, v1, col)

    # 枋心（中央大段）+ 藻头（两侧）
    # 上下边框
    hline(0.02, 0.055, JIN)
    hline(0.945, 0.98, JIN)
    hline(0.065, 0.075, BAI)
    hline(0.925, 0.935, BAI)

    # 箍头（两端竖向金带）
    for u0 in (0.0, 0.955):
        rect(u0, u0 + 0.045, 0.0, 1.0, JIN)
        rect(u0 + 0.010, u0 + 0.035, 0.0, 1.0, ground_b * 0.8)
        for vv in np.linspace(0.08, 0.92, 6):
            rect(u0 + 0.013, u0 + 0.032, vv, vv + 0.012, JIN)
    # 副箍头细线
    for u0 in (0.055, 0.900):
        rect(u0, u0 + 0.008, 0.06, 0.94, JIN)

    # 藻头旋子花：两处，圆环 + 花瓣
    for uc in (0.175, 0.815):
        R = 0.085
        du = (u - uc) / R
        dv = (v - 0.5) / (R * 3.4)
        rr = np.sqrt(du ** 2 + dv ** 2)
        ring = (rr > 0.72) & (rr < 0.82)
        img[ring] = JIN
        ring2 = (rr > 0.40) & (rr < 0.46)
        img[ring2] = BAI
        core = rr < 0.16
        img[core] = JIN
        # 花瓣
        ang = np.arctan2(dv, du)
        petal = (np.abs(np.cos(ang * 6.0)) > 0.86) & (rr > 0.44) & (rr < 0.74)
        img[petal] = JIN

    # 枋心：金色行龙（用简化的龙形曲线表示）+ 云纹
    cx0, cx1 = 0.30, 0.70
    m_in = (u > cx0) & (u < cx1)
    img[m_in] *= 0.55
    # 龙身：正弦波主体
    t = (u - cx0) / (cx1 - cx0)
    for k, (amp, ph, th) in enumerate([(0.16, 0.0, 0.030), (0.11, 1.1, 0.020)]):
        yc = 0.5 + amp * np.sin(t * math.pi * 3.2 + ph)
        band = (np.abs(v - yc) < th) & m_in
        img[band] = JIN * (0.95 - 0.15 * k)
    # 龙头
    head = ((u - 0.315) ** 2 / 0.0009 + (v - 0.44) ** 2 / 0.006) < 1.0
    img[head & m_in] = JIN
    # 云纹（小弧）
    for i in range(14):
        ccx = rng.uniform(cx0 + 0.02, cx1 - 0.02)
        ccy = rng.uniform(0.15, 0.85)
        dx = (u - ccx) / 0.018
        dy = (v - ccy) / 0.055
        ar = np.sqrt(dx ** 2 + dy ** 2)
        img[(np.abs(ar - 1.0) < 0.22) & m_in] = JIN * 0.9

    # 白色沥粉描边（沿上下边框内侧）
    hline(0.10, 0.115, BAI)
    hline(0.885, 0.90, BAI)

    # 老化：整体污渍、褪色
    noise = rng.normal(0, 0.035, (h, w, 1)).astype(np.float32)
    from math import sin
    grad = (0.94 + 0.10 * np.sin(np.linspace(0, 9, w)))[None, :, None]
    img = np.clip(img * grad + noise, 0.0, 1.0)

    im = bpy.data.images.new("TEX_彩画", w, h, alpha=False)
    img = img.astype(np.float32)
    flat = np.concatenate([img[::-1], np.ones((h, w, 1), dtype=np.float32)], axis=2).ravel()
    flat = np.ascontiguousarray(flat, dtype=np.float32)
    im.pixels.foreach_set(flat)
    im.filepath_raw = path
    im.file_format = 'PNG'
    im.save()
    bpy.data.images.remove(im)
    return path


def make_tile_image(path, w=512, h=512):
    """瓦面细节贴图：竖向瓦垄 + 釉面斑驳"""
    import numpy as np
    rng = np.random.default_rng(7)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    base = 0.5 + 0.5 * np.cos(xx / w * math.tau * 8.0)
    base = 0.78 + 0.22 * base
    noise = rng.normal(0, 0.05, (h, w)).astype(np.float32)
    g = np.clip(base + noise, 0, 1)
    img = np.stack([g * 0.98, g * 0.62, g * 0.30], axis=2)
    im = bpy.data.images.new("TEX_瓦", w, h, alpha=False)
    flat = np.concatenate([img[::-1], np.ones((h, w, 1), dtype=np.float32)], axis=2).ravel()
    im.pixels.foreach_set(flat)
    im.filepath_raw = path
    im.file_format = 'PNG'
    im.save()
    bpy.data.images.remove(im)
    return path


# ----------------------------------------------------------------------------
# 屋顶曲面
# ----------------------------------------------------------------------------
def hip_roof_mesh(hx, hy, ridge_hx, ridge_hy, z_eave, z_ridge,
                  p=1.75, nx=14, ny=10, nt=26, lift=0.55, lift_t=2.4,
                  lift_scale=5.0, flare=0.012):
    """
    生成庑殿顶曲面（含举折凹曲、翼角起翘、推山）。
    返回 (verts, faces)。曲面为单层，需 Solidify 加厚。
    hx, hy          檐口半宽 / 半深
    ridge_hx/hy     正脊半长 / 半深
    z_eave/z_ridge  檐口高 / 脊高
    p               举折指数（越大越"上陡下缓"）
    """
    verts = []
    faces = []
    # 每条边采样数
    NX, NY = nx, ny
    per = 2 * (NX + NY)
    rings = []
    for k in range(nt + 1):
        t = k / nt
        a = ridge_hx + (hx - ridge_hx) * t
        b = ridge_hy + (hy - ridge_hy) * t
        u = 1.0 - t
        z = z_eave + (z_ridge - z_eave) * (0.55 * u + 0.45 * u ** 1.9)
        pts = []
        # 周长参数 s∈[0,1)
        # 上边 (+Y) 从左到右
        for i in range(NX):
            s = i / per
            pts.append(((-a + 2 * a * i / NX), b, s))
        for i in range(NY):
            pts.append((a, (b - 2 * b * i / NY), None))
        for i in range(NX):
            pts.append(((a - 2 * a * i / NX), -b, None))
        for i in range(NY):
            pts.append((-a, (-b + 2 * b * i / NY), None))
        ring = []
        n = len(pts)
        for i, (x, y, _s) in enumerate(pts):
            # 角部权重：与最近檐角的平面距离（米）
            d = min(math.hypot(x - sx * a, y - sy * b)
                    for sx in (-1, 1) for sy in (-1, 1))
            w = max(0.0, 1.0 - d / lift_scale)
            w = w ** 2
            zz = z + lift * (w ** 1.5) * (t ** lift_t)
            sc = 1.0 + flare * (w ** 2) * (t ** 2)
            ring.append((x * sc, y * sc, zz))
        rings.append(ring)

    n = per
    for rg in rings:
        verts.extend(rg)
    for k in range(nt):
        a0 = k * n
        b0 = (k + 1) * n
        for i in range(n):
            j = (i + 1) % n
            faces.append((a0 + i, a0 + j, b0 + j, b0 + i))
    # 顶盖（脊下封闭）
    faces.append(tuple(range(n - 1, -1, -1)))
    return verts, faces
