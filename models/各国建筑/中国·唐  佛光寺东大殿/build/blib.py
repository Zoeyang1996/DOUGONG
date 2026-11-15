"""几何基础库：网格构建、扫掠、材质组"""
import bpy, bmesh, math
from mathutils import Vector, Matrix, Euler

TAU = math.pi * 2


def V(*a):
    if len(a) == 1:
        return Vector(a[0])
    return Vector(a)


def clamp(x, a=0.0, b=1.0):
    return a if x < a else (b if x > b else x)


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def rotz(a):
    return Matrix.Rotation(a, 3, 'Z')


class MB:
    """累积顶点/面的网格缓冲"""

    def __init__(self):
        self.v = []
        self.f = []

    def add(self, verts, faces):
        o = len(self.v)
        self.v.extend([tuple(x) for x in verts])
        self.f.extend([tuple(i + o for i in fc) for fc in faces])
        return o

    def count(self):
        return len(self.v)


class Builder:
    """按材质分组累积几何，最后每组生成一个物体"""

    def __init__(self):
        self.groups = {}

    def g(self, mat):
        if mat not in self.groups:
            self.groups[mat] = MB()
        return self.groups[mat]

    # ---------- 基本体 ----------
    def abox(self, mat, x0, x1, y0, y1, z0, z1):
        x0, x1 = min(x0, x1), max(x0, x1)
        y0, y1 = min(y0, y1), max(y0, y1)
        z0, z1 = min(z0, z1), max(z0, z1)
        v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        self.g(mat).add(v, f)

    def obox(self, mat, center, size, rot=None):
        cx, cy, cz = center
        sx, sy, sz = size
        pts = [(-sx / 2, -sy / 2, -sz / 2), (sx / 2, -sy / 2, -sz / 2),
               (sx / 2, sy / 2, -sz / 2), (-sx / 2, sy / 2, -sz / 2),
               (-sx / 2, -sy / 2, sz / 2), (sx / 2, -sy / 2, sz / 2),
               (sx / 2, sy / 2, sz / 2), (-sx / 2, sy / 2, sz / 2)]
        M = rot if rot is not None else Matrix.Identity(3)
        v = [Vector(center) + M @ Vector(p) for p in pts]
        f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        self.g(mat).add(v, f)

    def beam(self, mat, p0, p1, w, h, rot=None):
        """两点之间的矩形梁（沿 p0->p1），w 为侧向宽，h 为竖向高"""
        p0, p1 = Vector(p0), Vector(p1)
        d = p1 - p0
        L = d.length
        if L < 1e-6:
            return
        z = Vector((0, 0, 1))
        t = d.normalized()
        side = t.cross(z)
        if side.length < 1e-5:
            side = Vector((1, 0, 0))
        side.normalize()
        up = side.cross(t).normalized()
        if rot is not None:
            side = rot @ side
            up = rot @ up
        cen = (p0 + p1) / 2
        vt = [cen + side * w / 2 + up * h / 2, cen - side * w / 2 + up * h / 2,
              cen - side * w / 2 - up * h / 2, cen + side * w / 2 - up * h / 2]
        t2 = (p1 - p0).normalized() * (d.length / 2)
        v = [vt[0] - t2, vt[1] - t2, vt[2] - t2, vt[3] - t2,
             vt[0] + t2, vt[1] + t2, vt[2] + t2, vt[3] + t2]
        f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        self.g(mat).add(v, f)

    def cyl(self, mat, p0, p1, r, n=14, r1=None, caps=True):
        p0, p1 = Vector(p0), Vector(p1)
        d = p1 - p0
        L = d.length
        if L < 1e-6:
            return
        t = d.normalized()
        z = Vector((0, 0, 1)) if abs(t.z) < 0.95 else Vector((1, 0, 0))
        a = t.cross(z).normalized()
        b = t.cross(a).normalized()
        r1 = r if r1 is None else r1
        verts, faces = [], []
        for i in range(n):
            th = TAU * i / n
            ca, sa = math.cos(th), math.sin(th)
            verts.append(p0 + (a * ca + b * sa) * r)
        for i in range(n):
            th = TAU * i / n
            ca, sa = math.cos(th), math.sin(th)
            verts.append(p1 + (a * ca + b * sa) * r1)
        for i in range(n):
            j = (i + 1) % n
            faces.append((i, j, n + j, n + i))
        if caps:
            faces.append(tuple(range(n - 1, -1, -1)))
            faces.append(tuple(range(n, 2 * n)))
        self.g(mat).add(verts, faces)

    def sweep(self, mat, path, profile, closed=False, cap_start=False, cap_end=False):
        """沿 path 扫掠 2D 剖面 profile=[(u,v)...]（u 横向, v 竖向）"""
        n = len(path)
        m = len(profile)
        verts, faces = [], []
        for i, p in enumerate(path):
            p = Vector(p)
            if i == 0:
                t = Vector(path[1]) - p
            elif i == n - 1:
                t = p - Vector(path[-2])
            else:
                t = Vector(path[i + 1]) - Vector(path[i - 1])
            t = t.normalized()
            side = t.cross(Vector((0, 0, 1)))
            if side.length < 1e-5:
                side = Vector((1, 0, 0))
            side.normalize()
            up = side.cross(t).normalized()
            for (u, v) in profile:
                verts.append(p + side * u + up * v)
        rng = m if closed else m - 1
        for i in range(n - 1):
            for j in range(rng):
                j2 = (j + 1) % m
                faces.append((i * m + j, i * m + j2, (i + 1) * m + j2, (i + 1) * m + j))
        if cap_start:
            faces.append(tuple(range(m - 1, -1, -1)))
        if cap_end:
            faces.append(tuple(range((n - 1) * m, n * m)))
        self.g(mat).add(verts, faces)

    def quad_grid(self, mat, pts, nu, nv):
        """pts 为 (nu x nv) 的二维列表，生成四边形网格"""
        verts = [pts[i][j] for i in range(nu) for j in range(nv)]
        faces = []
        for i in range(nu - 1):
            for j in range(nv - 1):
                a = i * nv + j
                b = (i + 1) * nv + j
                c = (i + 1) * nv + j + 1
                d = i * nv + j + 1
                faces.append((a, b, c, d))
        self.g(mat).add(verts, faces)

    def poly(self, mat, verts, faces):
        self.g(mat).add(verts, faces)

    def sphere(self, mat, center, r, seg=12, rings=8):
        c = Vector(center)
        verts, faces = [], []
        for i in range(rings + 1):
            phi = math.pi * i / rings
            for j in range(seg):
                th = TAU * j / seg
                verts.append(c + Vector((r * math.sin(phi) * math.cos(th),
                                         r * math.sin(phi) * math.sin(th),
                                         r * math.cos(phi))))
        for i in range(rings):
            for j in range(seg):
                j2 = (j + 1) % seg
                a = i * seg + j
                b = i * seg + j2
                cc = (i + 1) * seg + j2
                d = (i + 1) * seg + j
                faces.append((a, b, cc, d))
        self.g(mat).add(verts, faces)

    # ---------- 输出 ----------
    def build(self, coll, mats, smooth_angle=math.radians(31), bevel=None, name_prefix=""):
        objs = []
        for matname, mb in self.groups.items():
            if not mb.v:
                continue
            me = bpy.data.meshes.new(f"{name_prefix}{matname}")
            me.from_pydata(mb.v, [], mb.f)
            me.validate(verbose=False)
            me.update()
            ob = bpy.data.objects.new(f"{name_prefix}{matname}", me)
            coll.objects.link(ob)
            if matname in mats:
                me.materials.append(mats[matname])
            if smooth_angle:
                for p in me.polygons:
                    p.use_smooth = True
                mod = ob.modifiers.new("SmoothByAngle", 'NODES') if False else None
            objs.append(ob)
        return objs


def shade_auto(ob, angle_deg=31):
    bpy.context.view_layer.objects.active = ob
    for p in ob.data.polygons:
        p.use_smooth = True
    try:
        bpy.ops.object.shade_auto_smooth(angle=math.radians(angle_deg))
    except Exception:
        pass
