# -*- coding: utf-8 -*-
"""
cf_lib.py —— 崇福寺弥陀殿 参数化建模基础库
Blender 5.0.1 / Python 3.11
包含：几何累加器(Geo)、网格生成、UV 投影、程序化贴图、材质、灯光相机工具
"""
import bpy
import bmesh
import os
import math
import numpy as np
from mathutils import Vector, Matrix, Euler

TAU = math.pi * 2.0
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(ROOT, "textures")
os.makedirs(TEX_DIR, exist_ok=True)


# ----------------------------------------------------------------------------
# 几何累加器：把大量构件合并到一个 mesh，兼顾性能与"按部件可编辑"
# ----------------------------------------------------------------------------
class Geo:
    def __init__(self):
        self.v = []          # vertices
        self.f = []          # faces (tuples)
        self.m = []          # material index per face
        self.uv = []         # optional per-face uv list (list of 2d tuples)

    # ---- 基础 ----
    def add(self, verts, faces, mat=0):
        off = len(self.v)
        self.v.extend([tuple(p) for p in verts])
        for fc in faces:
            self.f.append(tuple(off + i for i in fc))
            self.m.append(mat)

    def quad(self, a, b, c, d, mat=0):
        self.add([a, b, c, d], [(0, 1, 2, 3)], mat)

    def tri(self, a, b, c, mat=0):
        self.add([a, b, c], [(0, 1, 2)], mat)

    # ---- 盒体（可绕任意轴旋转）----
    def box(self, center, size, mat=0, rot=None, pivot=None):
        cx, cy, cz = center
        sx, sy, sz = size[0] / 2, size[1] / 2, size[2] / 2
        pts = [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
               (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)]
        if rot is not None:
            R = Euler(rot, 'XYZ').to_matrix()
            pts = [tuple(R @ Vector(p)) for p in pts]
        verts = [(cx + p[0], cy + p[1], cz + p[2]) for p in pts]
        faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                 (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        self.add(verts, faces, mat)

    # ---- 台锥/斗（上下不同尺寸），center 为整体几何中心 ----
    def frustum(self, center, bottom, top, height, mat=0, rot=None):
        cx, cy, cz = center
        bx, by = bottom[0] / 2, bottom[1] / 2
        tx, ty = top[0] / 2, top[1] / 2
        h = height
        pts = [(-bx, -by, -h / 2), (bx, -by, -h / 2), (bx, by, -h / 2), (-bx, by, -h / 2),
               (-tx, -ty, h / 2), (tx, -ty, h / 2), (tx, ty, h / 2), (-tx, ty, h / 2)]
        if rot is not None:
            R = Euler(rot, 'XYZ').to_matrix()
            pts = [tuple(R @ Vector(p)) for p in pts]
        verts = [(cx + p[0], cy + p[1], cz + p[2]) for p in pts]
        faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                 (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        self.add(verts, faces, mat)

    # ---- 圆柱（p0->p1）----
    def cyl(self, p0, p1, r, sides=12, mat=0, cap=True, r1=None):
        p0 = Vector(p0); p1 = Vector(p1)
        d = p1 - p0
        L = d.length
        if L < 1e-6:
            return
        z = d.normalized()
        ref = Vector((0, 0, 1)) if abs(z.z) < 0.9 else Vector((1, 0, 0))
        x = z.cross(ref).normalized()
        y = z.cross(x).normalized()
        r1 = r if r1 is None else r1
        ring0, ring1 = [], []
        for i in range(sides):
            a = TAU * i / sides
            ring0.append(p0 + x * (r * math.cos(a)) + y * (r * math.sin(a)))
            ring1.append(p1 + x * (r1 * math.cos(a)) + y * (r1 * math.sin(a)))
        verts = ring0 + ring1
        faces = []
        for i in range(sides):
            j = (i + 1) % sides
            faces.append((i, j, sides + j, sides + i))
        if cap:
            faces.append(tuple(range(sides - 1, -1, -1)))
            faces.append(tuple(range(sides, sides * 2)))
        self.add(verts, faces, mat)

    # ---- 沿折线扫掠矩形截面（脊、博风板、枋）----
    def sweep(self, pts, width, height, mat=0, up=Vector((0, 0, 1)), taper=None):
        pts = [Vector(p) for p in pts]
        n = len(pts)
        if n < 2:
            return
        rings = []
        for i, p in enumerate(pts):
            if i == 0:
                t = (pts[1] - pts[0])
            elif i == n - 1:
                t = (pts[-1] - pts[-2])
            else:
                t = (pts[i + 1] - pts[i - 1])
            t.normalize()
            s = t.cross(up)
            if s.length < 1e-6:
                s = Vector((1, 0, 0))
            s.normalize()
            u = s.cross(t).normalized()
            w = width[i] if isinstance(width, (list, tuple)) else width
            h = height[i] if isinstance(height, (list, tuple)) else height
            w *= (taper[i] if taper else 1.0)
            ring = [p + s * (-w / 2), p + s * (w / 2),
                    p + s * (w / 2) + u * h, p + s * (-w / 2) + u * h]
            rings.append(ring)
        verts = [v for ring in rings for v in ring]
        faces = []
        for i in range(n - 1):
            a = i * 4; b = (i + 1) * 4
            for k in range(4):
                k2 = (k + 1) % 4
                faces.append((a + k, a + k2, b + k2, b + k))
        faces.append((0, 3, 2, 1))
        b = (n - 1) * 4
        faces.append((b, b + 1, b + 2, b + 3))
        self.add(verts, faces, mat)

    # ---- 曲面片（网格）----
    def surface(self, grid, mat=0, flip=False):
        """grid: list[list[(x,y,z)]] 行优先，生成四边形面"""
        rows = len(grid); cols = len(grid[0])
        verts = [p for row in grid for p in row]
        faces = []
        for i in range(rows - 1):
            for j in range(cols - 1):
                a = i * cols + j
                b = a + 1
                c = a + cols + 1
                d = a + cols
                faces.append((a, b, c, d) if not flip else (d, c, b, a))
        self.add(verts, faces, mat)

    # ---- 生成对象 ----
    def build(self, name, coll, mats, smooth=False, box_uv=True, uv_scale=1.0,
              bevel=None, parent=None):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.v, [], self.f)
        me.validate(verbose=False)
        me.update()
        for m in mats:
            me.materials.append(m)
        if len(me.polygons) == len(self.m):
            me.polygons.foreach_set("material_index", self.m)
        if smooth:
            me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
        if box_uv:
            box_project_uv(me, uv_scale)
        obj = bpy.data.objects.new(name, me)
        coll.objects.link(obj)
        if bevel:
            md = obj.modifiers.new("Bevel", 'BEVEL')
            md.width = bevel
            md.segments = 2
            md.limit_method = 'ANGLE'
            md.angle_limit = math.radians(45)
        if parent:
            obj.parent = parent
        return obj


# ----------------------------------------------------------------------------
# UV
# ----------------------------------------------------------------------------
def box_project_uv(me, scale=1.0):
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv = me.uv_layers[0].data
    for poly in me.polygons:
        n = poly.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            if ax == 0:
                u, v = co.y, co.z
            elif ax == 1:
                u, v = co.x, co.z
            else:
                u, v = co.x, co.y
            uv[li].uv = (u * scale, v * scale)


# ----------------------------------------------------------------------------
# 程序化贴图（numpy -> bpy image -> png）
# ----------------------------------------------------------------------------
def tile_fbm(h, w, freq=4, octaves=5, seed=1, aniso=1.0):
    y = np.linspace(0, 1, h, endpoint=False)[:, None] * aniso
    x = np.linspace(0, 1, w, endpoint=False)[None, :]
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w))
    amp = 1.0
    f = freq
    for _ in range(octaves):
        for _k in range(3):
            fx = int(rng.integers(1, f + 1))
            fy = int(rng.integers(1, f + 1))
            ph = float(rng.random()) * TAU
            out += amp * np.sin(TAU * (fx * x + fy * y) + ph)
        amp *= 0.52
        f *= 2
    out -= out.min()
    if out.max() > 1e-9:
        out /= out.max()
    return out


def grain(h, w, seed=3, s=1.0):
    rng = np.random.default_rng(seed)
    a = rng.normal(0, 1, (h // max(1, int(2 * s)), w // max(1, int(2 * s))))
    # 双线性放大
    out = np.array(a, dtype=np.float32)
    while out.shape[0] < h:
        out = np.repeat(out, 2, axis=0)
        out = np.repeat(out, 2, axis=1)
    out = out[:h, :w]
    out = out - out.min()
    out = out / max(1e-6, out.max())
    return out


def save_png(name, rgb):
    """rgb: HxWx3 float 0..1，行 0 视为图像顶部"""
    h, w, _ = rgb.shape
    img = bpy.data.images.get(name)
    if img:
        bpy.data.images.remove(img)
    img = bpy.data.images.new(name, w, h, alpha=False)
    arr = np.asarray(rgb, dtype=np.float32)
    rgba = np.ones((h, w, 4), dtype=np.float32)
    rgba[:, :, :3] = arr[::-1]           # Blender 像素自下而上
    img.pixels.foreach_set(rgba.ravel())
    img.file_format = 'PNG'
    path = os.path.join(TEX_DIR, name + ".png")
    img.filepath_raw = path
    img.save()
    img.pack()
    return img


def normal_from_height(height, strength=2.0):
    # 高度 -> 法线（Sobel 近似）
    dx = np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)
    dy = np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)
    nx = -dx * strength
    ny = -dy * strength
    nz = np.ones_like(height)
    L = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx /= L; ny /= L; nz /= L
    out = np.stack([nx * 0.5 + 0.5, ny * 0.5 + 0.5, nz * 0.5 + 0.5], axis=-1)
    return out


def mix(c1, c2, t):
    c1 = np.array(c1, dtype=np.float32)
    c2 = np.array(c2, dtype=np.float32)
    if t.ndim == 2:
        t = t[:, :, None]
    return c1 * (1 - t) + c2 * t


# ----------------------------------------------------------------------------
# 材质
# ----------------------------------------------------------------------------
def pbr(name, img=None, normal=None, color=(0.8, 0.8, 0.8), rough=0.6,
        metallic=0.0, uv_scale=1.0, bump=0.0, rough_img=None, tint=None,
        spec=0.5, ior=1.45):
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (600, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (300, 0)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = spec
    if "IOR" in bsdf.inputs:
        bsdf.inputs["IOR"].default_value = ior

    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-900, 0)
    mp = nt.nodes.new("ShaderNodeMapping"); mp.location = (-720, 0)
    mp.inputs["Scale"].default_value = (uv_scale, uv_scale, uv_scale)
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])

    def img_node(image, y, non_color=False):
        n = nt.nodes.new("ShaderNodeTexImage")
        n.location = (-460, y)
        n.image = image
        n.interpolation = 'Cubic'
        if non_color:
            image.colorspace_settings.name = 'Non-Color'
        nt.links.new(mp.outputs["Vector"], n.inputs["Vector"])
        return n

    if img is not None:
        tex = img_node(img, 120)
        if tint is not None:
            mul = nt.nodes.new("ShaderNodeMixRGB"); mul.location = (-180, 120)
            mul.blend_type = 'MULTIPLY'
            mul.inputs["Fac"].default_value = 1.0
            mul.inputs["Color2"].default_value = (*tint, 1)
            nt.links.new(tex.outputs["Color"], mul.inputs["Color1"])
            nt.links.new(mul.outputs["Color"], bsdf.inputs["Base Color"])
        else:
            nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        bsdf.inputs["Base Color"].default_value = (*color, 1)

    if normal is not None:
        ntex = img_node(normal, -200, non_color=True)
        nmap = nt.nodes.new("ShaderNodeNormalMap"); nmap.location = (-160, -200)
        nmap.inputs["Strength"].default_value = bump if bump > 0 else 1.0
        nt.links.new(ntex.outputs["Color"], nmap.inputs["Color"])
        nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])

    if rough_img is not None:
        rt = img_node(rough_img, -40, non_color=True)
        nt.links.new(rt.outputs["Color"], bsdf.inputs["Roughness"])
    return mat


def flat(name, color, rough=0.7, metallic=0.0, spec=0.4):
    return pbr(name, color=color, rough=rough, metallic=metallic, spec=spec)


# ----------------------------------------------------------------------------
# 场景工具
# ----------------------------------------------------------------------------
def new_coll(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    return c


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.images):
        for b in list(block):
            try:
                block.remove(b)
            except Exception:
                pass


def sun_setup(direction, energy=4.0, color=(1.0, 0.93, 0.82), angle=0.6):
    light = bpy.data.lights.new("Sun", 'SUN')
    light.energy = energy
    light.color = color
    light.angle = math.radians(angle)
    obj = bpy.data.objects.new("Sun", light)
    bpy.context.scene.collection.objects.link(obj)
    d = Vector(direction).normalized()
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return obj


def camera(name, loc, target, lens=50.0, sensor=36.0):
    cam = bpy.data.cameras.new(name)
    cam.lens = lens
    cam.sensor_width = sensor
    obj = bpy.data.objects.new(name, cam)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = loc
    d = Vector(target) - Vector(loc)
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return obj


def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)
