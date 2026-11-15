# -*- coding: utf-8 -*-
"""网格构建基础库：批量几何合并、扫掠、参数曲面"""
import bpy, bmesh, math
from mathutils import Vector, Matrix, Euler


# ---------------------------------------------------------------- 场景
def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.length_unit = 'METERS'


def ensure_coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


# ---------------------------------------------------------------- 构建器
class MB:
    """把大量小几何合并进一个网格，保持对象数量可控且仍可编辑"""

    def __init__(self):
        self.v = []
        self.f = []
        self.sm = []      # 每面是否平滑

    # -- 顶点/面
    def addv(self, co):
        self.v.append((float(co[0]), float(co[1]), float(co[2])))
        return len(self.v) - 1

    def addf(self, idx, smooth=False):
        if len(set(idx)) < 3:
            return
        self.f.append(tuple(idx))
        self.sm.append(smooth)

    # -- 六面体（8 点：0-3 底，4-7 顶，逆时针）
    def hexa(self, p, smooth=False):
        b = [self.addv(x) for x in p]
        self.addf((b[0], b[3], b[2], b[1]), smooth)
        self.addf((b[4], b[5], b[6], b[7]), smooth)
        for i in range(4):
            j = (i + 1) % 4
            self.addf((b[i], b[j], b[j + 4], b[i + 4]), smooth)
        return b

    def cuboid(self, c, s, rot=(0, 0, 0), top=(1.0, 1.0), bot=(1.0, 1.0),
               smooth=False):
        hx, hy, hz = s[0] / 2, s[1] / 2, s[2] / 2
        pts = []
        for sz in (-1, 1):
            tx, ty = (bot if sz < 0 else top)
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                pts.append(Vector((sx * hx * tx, sy * hy * ty, sz * hz)))
        M = Euler(rot, 'XYZ').to_matrix()
        pts = [M @ p + Vector(c) for p in pts]
        return self.hexa(pts, smooth)

    def box_minmax(self, x0, x1, y0, y1, z0, z1, smooth=False):
        c = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
        s = (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))
        return self.cuboid(c, s, smooth=smooth)

    # -- 参数网格：grid[i][j] = Vector
    def grid(self, pts, smooth=True, flip=False, uclose=False, vclose=False):
        n = len(pts)
        m = len(pts[0])
        idx = [[self.addv(pts[i][j]) for j in range(m)] for i in range(n)]
        for i in range(n - 1 + (1 if uclose else 0)):
            i2 = (i + 1) % n
            for j in range(m - 1 + (1 if vclose else 0)):
                j2 = (j + 1) % m
                q = (idx[i][j], idx[i][j2], idx[i2][j2], idx[i2][j])
                self.addf(q[::-1] if flip else q, smooth)
        return idx

    # -- 沿路径扫掠一个二维截面 profile=[(u,v)...]（u=侧向，v=法向）
    def sweep(self, path, profile, up=Vector((0, 0, 1)), smooth=False,
              close=False, scale=None):
        n = len(path)
        rings = []
        for i, p in enumerate(path):
            if i == 0:
                t = (Vector(path[1]) - Vector(path[0]))
            elif i == n - 1:
                t = (Vector(path[-1]) - Vector(path[-2]))
            else:
                t = (Vector(path[i + 1]) - Vector(path[i - 1]))
            t.normalize()
            side = t.cross(up)
            if side.length < 1e-6:
                side = t.cross(Vector((1, 0, 0)))
            side.normalize()
            nrm = side.cross(t).normalized()
            s = 1.0 if scale is None else scale[i]
            rings.append([Vector(p) + side * (u * s) + nrm * (v * s)
                          for (u, v) in profile])
        m = len(profile)
        idx = [[self.addv(q) for q in r] for r in rings]
        for i in range(n - 1):
            for j in range(m - 1):
                q = (idx[i][j], idx[i][j + 1], idx[i + 1][j + 1], idx[i + 1][j])
                self.addf(q[::-1], smooth)
        if close:
            for i in range(n - 1):
                q = (idx[i][m - 1], idx[i][0], idx[i + 1][0], idx[i + 1][m - 1])
                self.addf(q[::-1], smooth)
        # 端盖
        self.addf(tuple(idx[0][::-1]), smooth)
        self.addf(tuple(idx[-1]), smooth)
        return idx

    def revolve(self, profile, center=(0, 0, 0), seg=24, axis='Z', smooth=True,
                closed=False):
        """绕轴旋转 profile=[(r,z)...]"""
        rings = []
        for k in range(seg):
            a = 2 * math.pi * k / seg
            ca, sa = math.cos(a), math.sin(a)
            r = []
            for (rr, zz) in profile:
                if axis == 'Z':
                    r.append(Vector((center[0] + rr * ca, center[1] + rr * sa,
                                     center[2] + zz)))
                else:
                    r.append(Vector((center[0] + zz, center[1] + rr * ca,
                                     center[2] + rr * sa)))
            rings.append(r)
        m = len(profile)
        idx = [[self.addv(q) for q in r] for r in rings]
        for k in range(seg):
            k2 = (k + 1) % seg
            for j in range(m - 1 + (1 if closed else 0)):
                j2 = (j + 1) % m
                self.addf((idx[k][j], idx[k][j2], idx[k2][j2], idx[k2][j]), smooth)
        return idx

    def cyl_dir(self, c, r, h, d, seg=10, r2=None):
        """沿任意方向的圆柱/圆台（用于檐头瓦当）"""
        d = Vector(d).normalized()
        up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
        u = d.cross(up).normalized()
        v = d.cross(u).normalized()
        r2 = r if r2 is None else r2
        c = Vector(c)
        rings = []
        for k, (rr, off) in enumerate(((r, 0.0), (r2, h))):
            ring = []
            for i in range(seg):
                a = 2 * math.pi * i / seg
                ring.append(c + d * off + u * (rr * math.cos(a)) + v * (rr * math.sin(a)))
            rings.append([self.addv(q) for q in ring])
        for i in range(seg):
            j = (i + 1) % seg
            self.addf((rings[0][i], rings[0][j], rings[1][j], rings[1][i]), True)
        self.addf(tuple(rings[0][::-1]), True)
        self.addf(tuple(rings[1]), True)

    # -- 输出
    def build(self, name, mat, coll, smooth_all=None, auto_smooth=38.0):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.v, [], self.f)
        me.update()
        if mat:
            me.materials.append(mat)
        if smooth_all is None:
            for i, p in enumerate(me.polygons):
                if i < len(self.sm):
                    p.use_smooth = self.sm[i]
        else:
            for p in me.polygons:
                p.use_smooth = smooth_all
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        me.validate(verbose=False)
        if auto_smooth:
            try:
                for o in bpy.context.selected_objects:
                    o.select_set(False)
                bpy.context.view_layer.objects.active = ob
                ob.select_set(True)
                bpy.ops.object.shade_smooth_by_angle(angle=math.radians(auto_smooth))
                ob.select_set(False)
            except Exception as e:
                print("[smooth] %s: %s" % (name, e))
        return ob


# ---------------------------------------------------------------- 工具
def lerp(a, b, t):
    return a + (b - a) * t


def clamp(v, a, b):
    return max(a, min(b, v))


def smoothstep(t):
    t = clamp(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def rect_ring(hw, hd, n_side=40):
    """矩形轮廓采样点（逆时针），用于檐口走线"""
    pts = []
    for i in range(n_side):
        pts.append((-hw + 2 * hw * i / n_side, -hd))
    for i in range(n_side):
        pts.append((hw, -hd + 2 * hd * i / n_side))
    for i in range(n_side):
        pts.append((hw - 2 * hw * i / n_side, hd))
    for i in range(n_side):
        pts.append((-hw, hd - 2 * hd * i / n_side))
    return pts


def add_solidify(ob, t=0.11):
    m = ob.modifiers.new('Solidify', 'SOLIDIFY')
    m.thickness = t
    m.offset = -1.0
    m.use_even_offset = False
    m.use_rim = True
    m.use_quality_normals = False
    return m


def add_bevel(ob, width=0.02, seg=1, angle=50):
    m = ob.modifiers.new('Bevel', 'BEVEL')
    m.width = width
    m.segments = seg
    m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(angle)
    return m


def fix_normals(ob):
    """闭合实体统一朝外法向（避免背面全黑）"""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return ob
