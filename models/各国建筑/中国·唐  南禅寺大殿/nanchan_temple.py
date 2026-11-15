# -*- coding: utf-8 -*-
"""
================================================================================
 南禅寺大殿 · Blender 程序化建模脚本
 Nanchan Temple Main Hall - Procedural Model
================================================================================
 对象：山西五台 南禅寺大殿（唐建中三年 782 年），中国现存最早的木构建筑
 形制：面阔三间 11.75m × 进深四椽 9.90m，单檐歇山（九脊顶），
       柱头铺作五铺作双抄偷心造，无补间铺作，殿内无柱（彻上明造），
       四椽栿通檐用二柱，举折缓、出檐深、侧脚明显。

 适用：Blender 3.3 LTS / 3.6 / 4.0 / 4.1 / 4.2 / 4.3
 运行：
   A. 图形界面：Scripting 工作区 → New → 粘贴本文件 → Run Script (Alt+P)
   B. 命令行  ：blender -b -P nanchan_temple.py
   C. 导入模块：import nanchan_temple as nt; nt.build()

 生成层级：
   南禅寺大殿_Nanchan_Hall
     ├─ 00_台基_Platform
     ├─ 01_柱网_Columns
     ├─ 02_额枋_Architrave
     ├─ 03_墙体门窗_Wall_Door
     ├─ 04_斗拱_Bracket
     ├─ 05_梁架_Frame
     ├─ 06_椽望_Rafter
     ├─ 07_屋面_Roof
     ├─ 08_脊饰_Ridge
     └─ 09_环境_Environment
================================================================================
"""

import bpy
import math
from mathutils import Vector, Matrix

# =============================================================================
# 一、基本参数（单位：米，参照南禅寺大殿实测数据）
# =============================================================================

BAY_MID   = 4.75                     # 明间面阔
BAY_SIDE  = 3.50                     # 次间面阔
WIDTH     = BAY_MID + 2 * BAY_SIDE   # 通面阔 11.75
DEPTH     = 9.90                     # 通进深（四椽）
COL_H     = 3.45                     # 檐柱高
COL_R     = 0.235                    # 檐柱半径（柱径约 0.47）
PLAT_H    = 1.05                     # 台基高
CEIL_Z    = PLAT_H + COL_H           # 柱头标高 4.50

COL_X     = [-WIDTH / 2, -BAY_MID / 2, BAY_MID / 2, WIDTH / 2]
COL_Y     = [-DEPTH / 2, DEPTH / 2]

SIDE_FOOT = 0.016                    # 侧脚：柱头向内收 1.6%
WALL_T    = 0.40                     # 墙体厚

# ---- 斗拱用材（材高 0.22m，分 = 材高/15） ----
CAI       = 0.22
FEN       = CAI / 15.0
DG_TOP    = 87 * FEN                 # 五铺作总高 ≈ 1.276
LIAO_BOT  = CEIL_Z + DG_TOP          # 撩檐槫底皮
LIAO_D    = 0.22                     # 撩檐槫径
Y_PURLIN  = DEPTH / 2 + 60 * FEN     # 撩檐槫水平位置（出跳两跳 = 60分）

# ---- 屋面 ----
OVER      = 1.75                     # 自柱中线出檐
WE        = WIDTH / 2 + OVER         # 屋面半宽 7.825
DE        = DEPTH / 2 + OVER         # 屋面半深 6.900
RISE      = 4.45                     # 举高（檐口至正脊）
P_EXP     = 1.5                      # 举折曲线指数（>1 檐部平缓、近脊陡峻）
XG        = WIDTH / 2 * (1 - SIDE_FOOT) + 0.12   # 山花平面：退至角柱缝之外（收山大）
YG        = 2.55                     # 山花底边半宽

# 檐口标高：由"撩檐槫上皮 + 椽望厚"反推，保证屋面与斗拱精确衔接
_T = 1.0 - Y_PURLIN / DE
HE        = (LIAO_BOT + LIAO_D + 0.26) - RISE * (_T ** P_EXP)
RIDGE_Z   = HE + RISE                # 正脊标高
H_G       = HE + RISE * ((1.0 - YG / DE) ** P_EXP)   # 山花底边标高

LIFT      = 0.34                     # 翼角起翘量
LIFT_N    = 8                        # 起翘影响范围指数

# =============================================================================
# 二、集合与材质
# =============================================================================

COLL = {}
MAT  = {}

COLL_DEF = [
    ("platform", "00_台基_Platform"),
    ("columns",  "01_柱网_Columns"),
    ("arch",     "02_额枋_Architrave"),
    ("wall",     "03_墙体门窗_Wall_Door"),
    ("dougong",  "04_斗拱_Bracket"),
    ("frame",    "05_梁架_Frame"),
    ("rafter",   "06_椽望_Rafter"),
    ("roof",     "07_屋面_Roof"),
    ("ridge",    "08_脊饰_Ridge"),
    ("env",      "09_环境_Environment"),
]


def get_coll(key):
    return COLL[key]


def setup_collections():
    COLL.clear()
    root = bpy.data.collections.new("南禅寺大殿_Nanchan_Hall")
    bpy.context.scene.collection.children.link(root)
    for key, name in COLL_DEF:
        c = bpy.data.collections.new(name)
        root.children.link(c)
        COLL[key] = c
    return root


def srgb(r, g, b, a=1.0):
    """sRGB(0-255) → 线性色"""
    def f(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b), a)


def _set_in(bsdf, names, value):
    for n in names:
        if n in bsdf.inputs:
            bsdf.inputs[n].default_value = value
            return True
    return False


def make_mat(name, color, rough, metal=0.0, spec=0.5, noise=None, tint=None):
    """创建 PBR 材质；noise=(scale, strength) 附加程序化凹凸"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = None
    for n in nt.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            bsdf = n
            break
    if bsdf is None:
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        out = None
        for n in nt.nodes:
            if n.type == 'OUTPUT_MATERIAL':
                out = n
                break
        if out:
            nt.links.new(bsdf.outputs[0], out.inputs[0])

    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    _set_in(bsdf, ["Specular IOR Level", "Specular"], spec)

    # 颜色微扰：大尺度噪声混合深色，模拟木构/石材的风化斑驳
    # （不同 Blender 版本 Mix 节点命名不同，故整体做兼容保护，失败则退回纯色）
    if tint is not None:
        try:
            scale, amount = tint
            tex = nt.nodes.new("ShaderNodeTexNoise")
            tex.inputs["Scale"].default_value = scale
            tex.inputs["Detail"].default_value = 8.0
            tex.location = (-760, 240)
            ramp = nt.nodes.new("ShaderNodeValToRGB")
            ramp.color_ramp.elements[0].position = 0.36
            ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
            ramp.color_ramp.elements[1].position = 0.72
            ramp.color_ramp.elements[1].color = (amount, amount, amount, 1.0)
            ramp.location = (-540, 240)

            mix = nt.nodes.new("ShaderNodeMixRGB")
            c_in, c_out, c_fac = "Color1", "Color", "Fac"
            c2 = "Color2"
            if not hasattr(mix, "blend_type"):
                raise RuntimeError("legacy MixRGB unavailable")
            mix.blend_type = 'MIX'
            mix.inputs[c_in].default_value = color
            mix.inputs[c2].default_value = (color[0] * 0.52, color[1] * 0.48,
                                            color[2] * 0.44, 1.0)
            mix.location = (-300, 240)
            nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
            nt.links.new(ramp.outputs["Color"], mix.inputs[c_fac])
            nt.links.new(mix.outputs[c_out], bsdf.inputs["Base Color"])
        except Exception:
            pass

    if noise is not None:
        scale, strength = noise
        tex = nt.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = scale
        tex.inputs["Detail"].default_value = 8.0
        tex.location = (-760, -220)
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = strength
        bump.location = (-330, -220)
        nt.links.new(tex.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    return m


def build_materials():
    MAT.clear()
    # 木材：柱、梁、斗拱 —— 风化灰褐
    MAT["wood"]  = make_mat("MAT_木_风化灰褐", srgb(122, 104, 86), 0.72, spec=0.32,
                            noise=(48, 0.22), tint=(2.6, 0.45))
    # 木材：门窗、板壁 —— 唐风赭红
    MAT["wood2"] = make_mat("MAT_木_赭红门窗", srgb(146, 84, 58), 0.62, spec=0.36,
                            noise=(36, 0.16), tint=(3.0, 0.35))
    # 木材：椽、望板 —— 室内原木色
    MAT["wood3"] = make_mat("MAT_木_椽望", srgb(134, 108, 82), 0.78, spec=0.28,
                            noise=(60, 0.25))
    # 瓦：青灰布瓦
    MAT["tile"]  = make_mat("MAT_瓦_青灰", srgb(112, 116, 120), 0.78, spec=0.12,
                            noise=(120, 0.12), tint=(4.0, 0.30))
    # 瓦沟（板瓦搭接处的暗部，用于强化瓦垄的立体感）
    MAT["tile_dark"] = make_mat("MAT_瓦_瓦沟", srgb(72, 76, 80), 0.86, spec=0.14,
                                noise=(140, 0.18))
    # 石材：台基、踏道
    MAT["stone"] = make_mat("MAT_石_灰岩", srgb(176, 170, 158), 0.84, spec=0.36,
                            noise=(28, 0.16), tint=(2.2, 0.35))
    # 灰泥：墙面
    MAT["plaster"] = make_mat("MAT_灰泥_白灰墙", srgb(212, 204, 188), 0.90, spec=0.26,
                              noise=(22, 0.10), tint=(1.8, 0.20))
    # 山花板（木板填塞，唐代歇山多见于博风板内）
    MAT["gable"] = make_mat("MAT_木_山花板", srgb(112, 98, 84), 0.86, spec=0.22,
                            noise=(70, 0.30), tint=(3.4, 0.40))
    # 脊饰：与瓦同色略深
    MAT["ridge"] = make_mat("MAT_脊_青灰", srgb(104, 106, 106), 0.66, spec=0.38,
                            noise=(90, 0.14))
    # 金属：门钉、铺首
    MAT["metal"] = make_mat("MAT_铜_门钉", srgb(122, 98, 62), 0.42, metal=0.85, spec=0.5)
    # 殿内暗部
    MAT["dark"]  = make_mat("MAT_室内暗部", srgb(58, 50, 44), 0.95, spec=0.15)
    # 地面
    MAT["ground"] = make_mat("MAT_地面_素土", srgb(168, 161, 148), 0.95, spec=0.25,
                             noise=(6, 0.08))


# =============================================================================
# 三、网格构建器
# =============================================================================

class MB:
    """轻量网格累加器：把大量构件合并为一个可编辑对象"""

    def __init__(self, M=None):
        self.v = []
        self.f = []
        self.M = M if M is not None else Matrix.Identity(4)

    def _o(self, p):
        return self.M @ Vector((p[0], p[1], p[2]))

    # ---- 长方体 ----
    def box(self, center, size, rotz=0.0):
        cx, cy, cz = center
        hx, hy, hz = size[0] / 2.0, size[1] / 2.0, size[2] / 2.0
        b = len(self.v)
        ca, sa = math.cos(rotz), math.sin(rotz)
        for dz in (-hz, hz):
            for ux, uy in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)):
                self.v.append(self._o((cx + ux * ca - uy * sa,
                                       cy + ux * sa + uy * ca,
                                       cz + dz)))
        self._hexa(b)

    # ---- 棱台（斗、收分墙体） ----
    def frustum(self, base_center, wb, db, wt, dt, h):
        cx, cy, cz = base_center
        b = len(self.v)
        for hw, hd, z in ((wb / 2, db / 2, cz), (wt / 2, dt / 2, cz + h)):
            for ux, uy in ((-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)):
                self.v.append(self._o((cx + ux, cy + uy, z)))
        self._hexa(b)

    def _hexa(self, b):
        self.f += [
            (b + 0, b + 3, b + 2, b + 1),
            (b + 4, b + 5, b + 6, b + 7),
            (b + 0, b + 1, b + 5, b + 4),
            (b + 1, b + 2, b + 6, b + 5),
            (b + 2, b + 3, b + 7, b + 6),
            (b + 3, b + 0, b + 4, b + 7),
        ]

    # ---- 圆柱 / 棱柱 ----
    def tube(self, p0, p1, r0, r1=None, sides=16, cap=True):
        if r1 is None:
            r1 = r0
        P0, P1 = Vector(p0), Vector(p1)
        d = P1 - P0
        if d.length < 1e-9:
            return
        n = d.normalized()
        ref = Vector((0, 0, 1)) if abs(n.z) < 0.95 else Vector((1, 0, 0))
        u = n.cross(ref).normalized()
        w = n.cross(u)
        b = len(self.v)
        for P, r in ((P0, r0), (P1, r1)):
            for i in range(sides):
                a = 2 * math.pi * i / sides
                self.v.append(self._o(P + u * (math.cos(a) * r) + w * (math.sin(a) * r)))
        for i in range(sides):
            j = (i + 1) % sides
            self.f.append((b + i, b + j, b + sides + j, b + sides + i))
        if cap:
            self.f.append(tuple(b + k for k in range(sides - 1, -1, -1)))
            self.f.append(tuple(b + sides + k for k in range(sides)))

    # ---- 方料 / 梁枋（沿任意方向） ----
    def beam(self, p0, p1, w, h, up=(0, 0, 1), ext0=0.0, ext1=0.0):
        P0, P1 = Vector(p0), Vector(p1)
        d = P1 - P0
        L = d.length
        if L < 1e-9:
            return
        n = d / L
        upv = Vector(up)
        if abs(n.dot(upv)) > 0.995:
            upv = Vector((0, 1, 0))
        side = n.cross(upv).normalized()
        up2 = n.cross(side)
        P0 = P0 - n * ext0
        P1 = P1 + n * ext1
        b = len(self.v)
        for P in (P0, P1):
            for a, c in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                self.v.append(self._o(P + side * (a * w / 2) + up2 * (c * h / 2)))
        self._hexa(b)

    # ---- 通用曲面网格 ----
    def grid(self, fn, nu, nv, flip=False):
        base = len(self.v)
        stride = nv + 1
        for i in range(nu + 1):
            u = i / nu
            for j in range(nv + 1):
                self.v.append(self._o(fn(u, j / nv)))
        for i in range(nu):
            for j in range(nv):
                a = base + i * stride + j
                b = a + stride
                q = (a, b, b + 1, a + 1)
                self.f.append(q[::-1] if flip else q)

    # ---- 多边形挤出面（鸱尾等） ----
    def poly_prism(self, pts, thick, plane='XZ', origin=(0, 0, 0), flip=False):
        ox, oy, oz = origin
        n = len(pts)
        b = len(self.v)
        for s in (-1, 1):
            for p in pts:
                if plane == 'XZ':
                    self.v.append(self._o((ox + p[0], oy + s * thick / 2, oz + p[1])))
                else:
                    self.v.append(self._o((ox + s * thick / 2, oy + p[0], oz + p[1])))
        for i in range(n):
            j = (i + 1) % n
            self.f.append((b + i, b + j, b + n + j, b + n + i))
        self.f.append(tuple(b + i for i in range(n - 1, -1, -1)))
        self.f.append(tuple(b + n + i for i in range(n)))
        if flip:
            self.f = [tuple(reversed(x)) for x in self.f]

    # ---- 输出 ----
    def build(self, name, coll_key, mat, smooth=False):
        if not self.f:
            return None
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(v) for v in self.v], [], self.f)
        me.validate(verbose=False)
        me.update()
        ob = bpy.data.objects.new(name, me)
        get_coll(coll_key).objects.link(ob)
        if mat is not None:
            ob.data.materials.append(mat)
        if smooth:
            for p in me.polygons:
                p.use_smooth = True
        return ob


def add_bevel(ob, width=0.015, segments=2, angle=40):
    """为木构件添加轻微倒角，提升转折处的高光表现（保留为可编辑修改器）"""
    if ob is None:
        return
    m = ob.modifiers.new("Bevel", 'BEVEL')
    m.width = width
    m.segments = segments
    m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(angle)


# =============================================================================
# 四、屋面数学
# =============================================================================

def corner_lift(x, y):
    return LIFT * ((abs(x) / WE) ** LIFT_N) * ((abs(y) / DE) ** LIFT_N)


def roof_z(x, y):
    """屋面高度场：主坡（前后檐） / 撒头面（两山收山以内）

    平面划分（以 +x / +y 象限为例）：
        戗脊线：y = den(u)，u = (|x|-XG)/(WE-XG)，den 由 YG 线性增到 DE
        |y| <  den  → 撒头面（两山撇山），高度只随 u 变化
        |y| >= den  → 前后坡角部
    该划分保证两块曲面沿戗脊严格等值，且 x<=XG 时退化为纯主坡。
    """
    ax, ay = abs(x), abs(y)
    u = max(0.0, (ax - XG) / (WE - XG))
    den = YG + u * (DE - YG)
    if ax > XG and ay < den:
        t = (1.0 - YG / DE) * (1.0 - u)
    else:
        t = 1.0 - ay / DE
    return HE + RISE * (max(t, 0.0) ** P_EXP) + corner_lift(x, y)


def hip_z(u):
    """撒头面高度（仅随 u 变化，保证与戗脊完全吻合）"""
    t = (1.0 - YG / DE) * (1.0 - u)
    return HE + RISE * (max(t, 0.0) ** P_EXP)


def eave_z(x, y):
    """檐口高度（所有檐口点 t=0，仅受翼角起翘影响）"""
    return HE + corner_lift(x, y)


def roof_normal(x, y, eps=0.06):
    dx = (roof_z(x + eps, y) - roof_z(x - eps, y)) / (2 * eps)
    dy = (roof_z(x, y + eps) - roof_z(x, y - eps)) / (2 * eps)
    return Vector((-dx, -dy, 1.0)).normalized()


def roof_patch_defs(dz=0.0, lod=1.0):
    """把歇山屋面拆成 10 块可用参数曲面描述的片：
       前坡中央 / 后坡中央（各 1）
       四角回落段（各 1）
       两山撒头面（各 1，含前后两半）
       返回 [(fn, nu, nv, flip), ...]
    """
    NU = max(8, int(44 * lod))
    NV = max(8, int(52 * lod))
    NC = max(4, int(18 * lod))
    NCV = max(4, int(16 * lod))
    NH = max(4, int(18 * lod))
    NHV = max(4, int(34 * lod))
    out = []

    def front(u, v):
        x = (u * 2 - 1) * XG
        y = v * DE
        return (x, y, roof_z(x, y) + dz)

    def back(u, v):
        x = (u * 2 - 1) * XG
        y = -v * DE
        return (x, y, roof_z(x, y) + dz)

    out.append((front, NU, NV, False))
    out.append((back, NU, NV, True))

    for sx in (-1, 1):
        for sy in (-1, 1):
            def corner(u, v, sx=sx, sy=sy):
                x = sx * (XG + u * (WE - XG))
                den = YG + u * (DE - YG)
                y = sy * (den + v * (DE - den))
                return (x, y, roof_z(x, y) + dz)
            out.append((corner, NC, NCV, sx * sy < 0))

    for sx in (-1, 1):
        def hip(u, v, sx=sx):
            x = sx * (XG + u * (WE - XG))
            den = YG + u * (DE - YG)
            y = (v * 2 - 1) * den            # v:0..1 → y: -den..+den
            return (x, y, hip_z(u) + corner_lift(x, y) + dz)
        out.append((hip, NH, 2 * NHV, sx < 0))

    return out



# =============================================================================
# 五、台基
# =============================================================================

PLAT_LX = WIDTH + 2 * 0.95
PLAT_LY = DEPTH + 2 * 0.85


def build_platform():
    mb = MB()
    # 圭角（下枭）
    mb.box((0, 0, 0.09), (PLAT_LX, PLAT_LY, 0.18))
    # 台基身（略有收分）
    mb.frustum((0, 0, 0.18), PLAT_LX - 0.02, PLAT_LY - 0.02,
               PLAT_LX - 0.14, PLAT_LY - 0.14, PLAT_H - 0.30)
    # 阶条石（上枋，压阑）
    mb.box((0, 0, PLAT_H - 0.06), (PLAT_LX, PLAT_LY, 0.12))
    mb.build("台基_主体", 'platform', MAT["stone"])

    # 台面（略低于阶条石 1cm，形成一圈边框）
    mb2 = MB()
    mb2.box((0, 0, PLAT_H - 0.012), (PLAT_LX - 0.62, PLAT_LY - 0.62, 0.05))
    mb2.build("台基_台面", 'platform', MAT["stone"])

    # 踏道（正面 6 级）
    mb3 = MB()
    n_step = 6
    sw, sd = 3.90, 0.31
    for i in range(n_step):
        zt = PLAT_H - (i + 1) * (PLAT_H / (n_step + 0.4))
        if zt <= 0.02:
            continue
        y0 = -PLAT_LY / 2 - i * sd
        mb3.box((0, y0 - sd / 2, zt / 2), (sw, sd, zt))
    # 垂带石
    for sx in (-1, 1):
        p0 = (sx * (sw / 2 + 0.10), -PLAT_LY / 2 + 0.05, PLAT_H - 0.06)
        p1 = (sx * (sw / 2 + 0.10), -PLAT_LY / 2 - n_step * sd - 0.05, 0.06)
        mb3.beam(p0, p1, 0.30, 0.26, up=(0, 0, 1), ext0=0.1, ext1=0.1)
    mb3.build("台基_踏道", 'platform', MAT["stone"])


# =============================================================================
# 六、柱网（含侧脚）
# =============================================================================

def col_top(x, y):
    """柱头中心（侧脚：向建筑中心倾斜）"""
    return Vector((x * (1 - SIDE_FOOT), y * (1 - SIDE_FOOT), CEIL_Z))


def build_columns():
    mb = MB()
    detail = MB()
    for i, x in enumerate(COL_X):
        for j, y in enumerate(COL_Y):
            p0 = Vector((x, y, PLAT_H))
            p1 = col_top(x, y)
            mb.tube(p0, p1, COL_R, COL_R * 0.88, sides=20)
            # 柱础（覆盆）
            detail.frustum((x, y, PLAT_H - 0.01), COL_R * 2.5, COL_R * 2.5,
                           COL_R * 2.15, COL_R * 2.15, 0.10)
            detail.tube((x, y, PLAT_H + 0.09), (x, y, PLAT_H + 0.13),
                        COL_R * 2.15, COL_R * 1.02, sides=20)
    ob = mb.build("柱网_檐柱x8", 'columns', MAT["wood"], smooth=True)
    add_bevel(ob, 0.01, 2)
    detail.build("柱网_柱础", 'columns', MAT["stone"], smooth=False)


# =============================================================================
# 七、额枋（阑额）
# =============================================================================

ARCH_H = 0.34
ARCH_T = 0.20


def build_architrave():
    mb = MB()
    z0 = CEIL_Z - ARCH_H
    half = WIDTH / 2 * (1 - SIDE_FOOT)
    hd = DEPTH / 2 * (1 - SIDE_FOOT)
    xs = [x * (1 - SIDE_FOOT) for x in COL_X]
    # 前后檐：分间架设
    for y in (-hd, hd):
        for k in range(3):
            x0, x1 = xs[k], xs[k + 1]
            mb.beam((x0, y, z0 + ARCH_H / 2), (x1, y, z0 + ARCH_H / 2),
                    ARCH_T, ARCH_H, up=(0, 0, 1), ext0=0.1, ext1=0.1)
    # 两山：整根
    for x in (-half, half):
        mb.beam((x, -hd, z0 + ARCH_H / 2), (x, hd, z0 + ARCH_H / 2),
                ARCH_T, ARCH_H, up=(0, 0, 1), ext0=0.1, ext1=0.1)
    ob = mb.build("额枋_阑额", 'arch', MAT["wood"])
    add_bevel(ob, 0.012, 2)


# =============================================================================
# 八、墙体与门窗
# =============================================================================

FLOOR_Z = PLAT_H
WALL_TOP = CEIL_Z - ARCH_H          # 墙顶 / 阑额下皮


def _wood_panel(mb, x0, x1, z0, z1, y, t=0.09, mat=None):
    mb.box(((x0 + x1) / 2, y, (z0 + z1) / 2), (abs(x1 - x0), t, abs(z1 - z0)))


def build_walls():
    """两山、后檐为白灰墙；前檐为板门 + 直棂窗"""
    hd = DEPTH / 2
    hw = WIDTH / 2
    fy = -hd + WALL_T / 2 + 0.02      # 前檐墙内皮基准
    by = hd - WALL_T / 2

    # ---------- 后檐墙 ----------
    mb = MB()
    mb.box((0, by, (FLOOR_Z + 0.44 + WALL_TOP) / 2),
           (WIDTH - 0.9, WALL_T, WALL_TOP - FLOOR_Z - 0.44))
    mb.build("墙体_后檐墙", 'wall', MAT["plaster"])

    mb_b = MB()
    mb_b.box((0, by - 0.02, FLOOR_Z + 0.22), (WIDTH - 0.9, WALL_T + 0.05, 0.44))
    mb_b.build("墙体_后檐下碱", 'wall', MAT["stone"])

    # ---------- 两山墙 ----------
    mb2 = MB()
    for sx in (-1, 1):
        mb2.box((sx * (hw - WALL_T / 2), 0, (FLOOR_Z + 0.44 + WALL_TOP) / 2),
                (WALL_T, DEPTH - 0.9, WALL_TOP - FLOOR_Z - 0.44))
    mb2.build("墙体_两山墙", 'wall', MAT["plaster"])

    mb2b = MB()
    for sx in (-1, 1):
        mb2b.box((sx * (hw - WALL_T / 2 + 0.02), 0, FLOOR_Z + 0.22),
                 (WALL_T + 0.05, DEPTH - 0.9, 0.44))
    mb2b.build("墙体_两山下碱", 'wall', MAT["stone"])

    # ---------- 前檐：明间板门 ----------
    yf = fy - WALL_T / 2
    mb3 = MB()
    dw = BAY_MID - 0.55          # 门洞宽
    dh = 2.90                    # 门洞高
    zt = FLOOR_Z + dh
    # 门洞两侧填塞的墙垛
    for sx in (-1, 1):
        x_in = sx * dw / 2
        x_out = sx * BAY_MID / 2
        mb3.box(((x_in + x_out) / 2, yf, (FLOOR_Z + WALL_TOP) / 2),
                (abs(x_out - x_in), WALL_T, WALL_TOP - FLOOR_Z))
    # 门额以上的墙
    mb3.box((0, yf, (zt + WALL_TOP) / 2), (dw, WALL_T, WALL_TOP - zt))
    mb3.build("墙体_明间墙垛", 'wall', MAT["plaster"])

    # 门框
    mb4 = MB()
    fr = 0.16
    yd = yf - WALL_T / 2 - 0.02
    for sx in (-1, 1):
        mb4.box((sx * (dw / 2 - fr / 2), yd, FLOOR_Z + dh / 2), (fr, 0.20, dh))
    mb4.box((0, yd, zt - fr / 2), (dw, 0.20, fr))            # 门额
    mb4.box((0, yd - 0.02, FLOOR_Z + 0.09), (dw, 0.24, 0.18))  # 门槛
    # 门簪
    for sx in (-0.55, 0, 0.55):
        mb4.box((sx, yd - 0.11, zt - fr / 2), (0.14, 0.10, 0.14))
    mb4.build("门窗_板门门框", 'wall', MAT["wood2"])

    # 门扇 ×2
    mb5 = MB()
    leaf_w = (dw - 0.14) / 2
    for sx in (-1, 1):
        cx = sx * (leaf_w / 2 + 0.02)
        mb5.box((cx, yd - 0.11, FLOOR_Z + 0.18 + (dh - 0.28) / 2),
                (leaf_w, 0.11, dh - 0.28))
        # 门钉 5×5
        for a in range(5):
            for b in range(5):
                px = cx - leaf_w / 2 + 0.16 + a * (leaf_w - 0.32) / 4
                pz = FLOOR_Z + 0.42 + b * 0.30
                mb5.tube((px, yd - 0.17, pz), (px, yd - 0.145, pz), 0.036, 0.030, sides=8)
    mb5.build("门窗_板门扇", 'wall', MAT["wood2"], smooth=True)

    # ---------- 前檐：次间 直棂窗 ----------
    mb6 = MB()
    mb7 = MB()
    mb8 = MB()
    for sx in (-1, 1):
        xc = sx * (BAY_MID / 2 + BAY_SIDE / 2)     # 次间中心
        ww = BAY_SIDE - 1.90                        # 窗宽
        z0w, z1w = FLOOR_Z + 1.02, FLOOR_Z + 2.58
        # 槛墙（板壁）
        mb6.box((xc, yf, (FLOOR_Z + z0w) / 2), (ww + 0.5, WALL_T, z0w - FLOOR_Z))
        # 窗上板壁
        mb6.box((xc, yf, (z1w + WALL_TOP) / 2), (ww + 0.5, WALL_T, WALL_TOP - z1w))
        # 窗两侧板壁
        for s2 in (-1, 1):
            x_ed = xc + s2 * (ww / 2 + 0.14)
            x_bay = xc + s2 * (BAY_SIDE / 2)
            mb6.box(((x_ed + x_bay) / 2, yf, (z0w + z1w) / 2),
                    (abs(x_bay - x_ed), WALL_T, z1w - z0w))
        # 窗框
        yw = yf - WALL_T / 2 - 0.01
        fw = 0.09
        mb7.box((xc, yw, z0w + fw / 2), (ww + 2 * fw, 0.16, fw))
        mb7.box((xc, yw, z1w - fw / 2), (ww + 2 * fw, 0.16, fw))
        for s2 in (-1, 1):
            mb7.box((xc + s2 * ww / 2, yw, (z0w + z1w) / 2), (fw, 0.16, z1w - z0w))
        # 直棂（竖向棂条）
        n_bar = 11
        for k in range(n_bar):
            px = xc - ww / 2 + (k + 0.5) * ww / n_bar
            mb7.box((px, yw, (z0w + z1w) / 2), (0.055, 0.10, z1w - z0w - 2 * fw))
        # 窗下槛
        mb7.box((xc, yw, z0w - 0.05), (ww + 0.3, 0.22, 0.12))
        # 窗后室内暗衬（避免视线穿透）
        mb8.box((xc, yf + 0.30, (z0w + z1w) / 2), (ww + 0.1, 0.04, z1w - z0w))
    mb6.build("墙体_次间墙板", 'wall', MAT["plaster"])
    mb7.build("门窗_直棂窗", 'wall', MAT["wood2"])
    mb8.build("门窗_窗内暗衬", 'wall', MAT["dark"])


# =============================================================================
# 九、斗拱（五铺作双抄偷心造）
# =============================================================================

def dougong_parts(mb):
    """局部坐标：X=檐面切向，Y=外法向，Z=柱头上皮"""
    F = FEN
    # 栌斗
    mb.frustum((0, 0, 0), 26 * F, 26 * F, 32 * F, 32 * F, 20 * F)
    # 泥道拱（横，第一层）
    mb.box((0, 0, 20 * F + 7.5 * F), (62 * F, 10 * F, 15 * F))
    # 华拱一跳（出 30 分）
    mb.box((0, 4 * F, 20 * F + 10.5 * F), (10 * F, 52 * F, 21 * F))
    # 交互斗（一跳端）
    mb.frustum((0, 30 * F, 41 * F), 16 * F, 16 * F, 18 * F, 18 * F, 10 * F)
    # 华拱二跳
    mb.box((0, 45 * F, 41 * F + 10.5 * F), (10 * F, 30 * F, 21 * F))
    # 散斗（泥道拱两端）
    for s in (-1, 1):
        mb.frustum((s * 26 * F, 0, 35 * F), 14 * F, 14 * F, 16 * F, 16 * F, 10 * F)
    # 慢拱（横，第二层）
    mb.box((0, 0, 45 * F + 7.5 * F), (92 * F, 10 * F, 15 * F))
    # 交互斗（二跳端）
    mb.frustum((0, 60 * F, 62 * F), 16 * F, 16 * F, 18 * F, 18 * F, 10 * F)
    # 令拱（承撩檐槫）
    mb.box((0, 60 * F, 62 * F + 17.5 * F), (72 * F, 10 * F, 15 * F))
    # 耍头
    mb.box((0, 30 * F, 62 * F + 12.5 * F), (10 * F, 62 * F, 15 * F))
    # 令拱上散斗 ×3
    for s in (-1, 0, 1):
        mb.frustum((s * 30 * F, 60 * F, 77 * F), 14 * F, 14 * F, 16 * F, 16 * F, 10 * F)
    # 柱头方（慢拱上皮）
    mb.box((0, 0, 60 * F + 7.5 * F), (92 * F, 10 * F, 15 * F))


def frame_matrix(loc, X, Y, Z):
    return Matrix(((X.x, Y.x, Z.x, loc[0]),
                   (X.y, Y.y, Z.y, loc[1]),
                   (X.z, Y.z, Z.z, loc[2]),
                   (0.0, 0.0, 0.0, 1.0)))


def build_dougong():
    Z = Vector((0, 0, 1))
    faces = []   # (位置, 外法向)
    for x in COL_X:
        faces.append((Vector((x, -DEPTH / 2, 0)), Vector((0, -1, 0)), "前檐"))
        faces.append((Vector((x, DEPTH / 2, 0)), Vector((0, 1, 0)), "后檐"))
    for y in COL_Y:
        faces.append((Vector((-WIDTH / 2, y, 0)), Vector((-1, 0, 0)), "西山"))
        faces.append((Vector((WIDTH / 2, y, 0)), Vector((1, 0, 0)), "东山"))

    # 同一柱位多向铺作合并为一个对象
    groups = {}
    for pos, nrm, tag in faces:
        key = (round(pos.x, 3), round(pos.y, 3))
        groups.setdefault(key, []).append((pos, nrm, tag))

    corner_extra = MB()
    idx = 0
    for key, lst in groups.items():
        mb = MB()
        pos0 = lst[0][0]
        head = Vector((pos0.x * (1 - SIDE_FOOT), pos0.y * (1 - SIDE_FOOT), CEIL_Z))
        for pos, nrm, tag in lst:
            X = nrm.cross(Z)
            if X.length < 1e-6:
                continue
            X.normalize()
            mb.M = frame_matrix(head, X, nrm, Z)
            dougong_parts(mb)
        idx += 1
        name = "斗拱_柱头铺作_%02d" % idx
        ob = mb.build(name, 'dougong', MAT["wood"])
        add_bevel(ob, 0.008, 1, 50)

        # 转角铺作附加 45° 角华拱
        if len(lst) > 1:
            cx, cy = head.x, head.y
            tx, ty = (1 if cx > 0 else -1), (1 if cy > 0 else -1)
            p0 = Vector((cx, cy, CEIL_Z + 30 * FEN))
            p1 = Vector((cx + tx * 0.95, cy + ty * 0.95, CEIL_Z + 30 * FEN))
            corner_extra.beam(p0, p1, 0.16, 0.30, up=(0, 0, 1))
            corner_extra.beam(p0, p1, 0.14, 0.28, up=(0, 0, 1))
    corner_extra.build("斗拱_转角角华拱", 'dougong', MAT["wood"])

    # 撩檐槫 + 柱头方（通长）
    mb2 = MB()
    zc = LIAO_BOT + LIAO_D / 2
    for y in (-Y_PURLIN, Y_PURLIN):
        mb2.tube((-WE + 0.2, y, zc), (WE - 0.2, y, zc), LIAO_D / 2, LIAO_D / 2, sides=14)
    for x in (-Y_PURLIN, Y_PURLIN):
        mb2.tube((x, -DE + 0.2, zc), (x, DE - 0.2, zc), LIAO_D / 2, LIAO_D / 2, sides=14)
    mb2.build("斗拱_撩檐槫", 'dougong', MAT["wood"], smooth=True)

    # 罗汉枋（柱头方通长）
    mb3 = MB()
    for y in (-Y_PURLIN, Y_PURLIN):
        mb3.box((0, y, LIAO_BOT - 0.40), (WIDTH + 0.2, 0.14, 0.22))
    for x in (-Y_PURLIN, Y_PURLIN):
        mb3.box((x, 0, LIAO_BOT - 0.40), (0.14, DEPTH + 0.2, 0.22))
    mb3.build("斗拱_罗汉枋", 'dougong', MAT["wood"])


# =============================================================================
# 十、梁架（四椽栿通檐用二柱 · 彻上明造）
# =============================================================================

def build_frame():
    mb = MB()
    z_col = CEIL_Z + 0.30                # 栌斗上皮
    beam_h, beam_w = 0.72, 0.52
    z_beam = z_col + beam_h / 2          # 四椽栿中心
    hd = DEPTH / 2 * (1 - SIDE_FOOT)

    xs = [x * (1 - SIDE_FOOT) for x in COL_X]
    for x in xs:
        # 四椽栿
        mb.beam((x, -hd, z_beam), (x, hd, z_beam), beam_w, beam_h)
    # 平梁（二椽）
    z_pl = z_col + beam_h + 0.28
    for x in xs:
        mb.beam((x, -DEPTH / 4, z_pl), (x, DEPTH / 4, z_pl), 0.40, 0.46)

    # 槫（檩）：檐槫 / 上平槫 / 脊槫
    z_eave = LIAO_BOT - 0.10
    z_up = roof_z(0, DEPTH / 4) - 0.34
    z_ridge = RIDGE_Z - 0.36
    purlins = [
        (0.0, z_ridge, 0.30),
        (DEPTH / 4, z_up, 0.28), (-DEPTH / 4, z_up, 0.28),
    ]
    for y, z, d in purlins:
        mb.tube((-WIDTH / 2 - 0.1, y, z), (WIDTH / 2 + 0.1, y, z), d / 2, d / 2, sides=12)

    # 蜀柱 / 叉手 / 托脚
    for x in xs:
        # 平梁→上平槫 的蜀柱
        for sy in (-1, 1):
            y = sy * DEPTH / 4
            h1 = z_up - z_pl
            if h1 > 0.1:
                mb.box((x, y, z_pl - 0.02 + h1 / 2), (0.26, 0.26, h1))
        # 脊瓜柱
        h2 = z_ridge - z_pl
        if h2 > 0.1:
            mb.box((x, 0, z_pl + h2 / 2), (0.30, 0.30, h2))
        # 叉手（平梁端→脊槫）
        for sy in (-1, 1):
            mb.beam((x, sy * DEPTH / 4, z_pl + 0.2),
                    (x, sy * 0.16, z_ridge - 0.30), 0.16, 0.22)
        # 托脚（四椽栿→上平槫）
        for sy in (-1, 1):
            mb.beam((x, sy * (hd - 0.55), z_beam + 0.32),
                    (x, sy * DEPTH / 4, z_up - 0.16), 0.15, 0.20)

    # 丁栿（山面承托歇山撒头）
    for sx in (-1, 1):
        x = sx * (WIDTH / 2 - 0.55)
        for yy in (-DEPTH / 6, DEPTH / 6):
            mb.beam((x, yy - 1.0, z_beam + 0.1), (x, yy + 1.0, z_beam + 0.1), 0.34, 0.40)

    ob = mb.build("梁架_四椽栿与平梁", 'frame', MAT["wood3"])
    add_bevel(ob, 0.01, 2)


# =============================================================================
# 十一、椽、望板
# =============================================================================

def build_rafters():
    """檐椽 / 飞椽：沿举折曲面分段铺设，避免弦线穿出屋面"""
    mb = MB()
    y_in = Y_PURLIN + 0.02
    step = 0.30
    SEG = 4                     # 每根椽沿曲面的分段数
    DROP = 0.17                 # 椽背距瓦面（椽径 + 望板 + 苫背）

    def curved_beam(p_uv, s0, s1, drop, w=0.13, h=0.15, seg=SEG):
        """p_uv(t) → 世界点 (t 为 0..1 参数)"""
        prev = None
        for k in range(seg + 1):
            t = s0 + (s1 - s0) * k / seg
            x, y = p_uv(t)
            p = (x, y, roof_z(x, y) - drop)
            if prev is not None:
                mb.beam(prev, p, w, h, up=(0, 0, 1), ext0=0.01, ext1=0.01)
            prev = p

    # ---- 前后檐檐椽 ----
    n = int((WE - 0.25) * 2 / step)
    for i in range(n + 1):
        x = -WE + 0.25 + i * step
        for sy in (-1, 1):
            curved_beam(lambda t, x=x, sy=sy: (x, sy * (y_in + (DE - 0.16 - y_in) * t)),
                        0.0, 1.0, DROP)
            # 飞椽（檐口段，抬高于檐椽之上）
            curved_beam(lambda t, x=x, sy=sy: (x, sy * (DE - 0.60 + 0.46 * t)),
                        0.0, 1.0, DROP - 0.13, w=0.11, h=0.11, seg=2)

    # ---- 两山檐椽（自山花外侧的踩步金起挑，不进入山花以内） ----
    x_in = XG + 0.05
    n2 = int((DE - 0.6) * 2 / step)
    for i in range(n2 + 1):
        y = -DE + 0.3 + i * step
        for sx in (-1, 1):
            curved_beam(lambda t, y=y, sx=sx: (sx * (x_in + (WE - 0.16 - x_in) * t), y),
                        0.0, 1.0, DROP)
            curved_beam(lambda t, y=y, sx=sx: (sx * (WE - 0.60 + 0.46 * t), y),
                        0.0, 1.0, DROP - 0.13, w=0.11, h=0.11, seg=2)

    ob = mb.build("椽望_檐椽飞椽", 'rafter', MAT["wood3"])
    add_bevel(ob, 0.006, 1, 50)


# =============================================================================
# 十二、屋面（歇山曲面）
# =============================================================================

def build_roof_surface():
    mb = MB()

    # ---- 屋面基层（瓦面） ----
    for fn, nu, nv, flip in roof_patch_defs(dz=0.0, lod=1.0):
        mb.grid(fn, nu, nv, flip=flip)

    # ---- 山花（垂直三角面，两山，木构山花板） ----
    mb_g = MB()
    N = 26
    for sx in (-1, 1):
        b = len(mb_g.v)
        for j in range(N + 1):
            y = -YG + 2 * YG * j / N
            zt = roof_z(sx * XG, y)
            mb_g.v.append(mb_g._o((sx * XG, y, H_G)))
            mb_g.v.append(mb_g._o((sx * XG, y, zt)))
        for j in range(N):
            a = b + j * 2
            q = (a, a + 2, a + 3, a + 1)
            mb_g.f.append(q if sx > 0 else q[::-1])

    # ---- 檐口封边（表现瓦口厚度） ----
    b = len(mb.v)
    seg = 36
    loop = []
    for i in range(seg + 1):                     # 前檐
        loop.append((-WE + 2 * WE * i / seg, DE))
    for i in range(1, seg + 1):                  # 东山
        loop.append((WE, DE - 2 * DE * i / seg))
    for i in range(1, seg + 1):                  # 后檐
        loop.append((WE - 2 * WE * i / seg, -DE))
    for i in range(1, seg + 1):                  # 西山
        loop.append((-WE, -DE + 2 * DE * i / seg))
    for x, y in loop:
        mb.v.append(mb._o((x, y, eave_z(x, y) + 0.012)))
        mb.v.append(mb._o((x, y, eave_z(x, y) - 0.075)))
    m = len(loop)
    for i in range(m):
        j = (i + 1) % m
        mb.f.append((b + 2 * i, b + 2 * j, b + 2 * j + 1, b + 2 * i + 1))

    mb.build("屋面_瓦基层", 'roof', MAT["tile_dark"])
    mb_g.build("屋面_山花板", 'roof', MAT["gable"])

    # ---- 望板（屋面板，位于瓦面之下，檐口可见其端头） ----
    mb2 = MB()
    for fn, nu, nv, flip in roof_patch_defs(dz=-0.15, lod=0.70):
        mb2.grid(fn, nu, nv, flip=not flip)
    mb2.build("屋面_望板层", 'rafter', MAT["wood3"])

    build_tile_ridges()


# =============================================================================
# 十三、筒瓦垄 + 瓦当
# =============================================================================

TILE_R = 0.085
TILE_GAP = 0.225


def _tile_row(mb, pts):
    n = len(pts)
    if n < 2:
        return
    rings = []
    for i, p in enumerate(pts):
        if i == 0:
            t = pts[1] - pts[0]
        elif i == n - 1:
            t = pts[-1] - pts[-2]
        else:
            t = pts[i + 1] - pts[i - 1]
        if t.length < 1e-9:
            continue
        t.normalize()
        s = t.cross(Vector((0, 0, 1)))
        if s.length < 1e-6:
            s = Vector((1, 0, 0))
        s.normalize()
        u2 = t.cross(s)
        if u2.z < 0:
            u2 = -u2
            s = -s
        ring = []
        for k in range(5):
            a = math.pi * k / 4
            ring.append(p + u2 * (TILE_R * (0.30 + 0.70 * math.sin(a)) + 0.012)
                        + s * (TILE_R * 1.05 * math.cos(a)))
        rings.append(ring)
    base = len(mb.v)
    for ring in rings:
        for q in ring:
            mb.v.append(mb._o(q))
    for i in range(len(rings) - 1):
        for k in range(4):
            a = base + i * 5 + k
            b = a + 5
            mb.f.append((a, b, b + 1, a + 1))


def build_tile_ridges():
    mb = MB()
    mbd = MB()          # 瓦当 / 滴水（平直着色，边缘清晰）
    nst = 18

    # ---- 前后坡瓦垄 ----
    nx = int((WE - 0.20) * 2 / TILE_GAP)
    for i in range(nx + 1):
        x = -WE + 0.20 + i * TILE_GAP
        if abs(x) <= XG:
            y_start, y_end = 0.26, DE - 0.30      # 脊下 → 檐口
        else:
            den = YG + (abs(x) - XG) / (WE - XG) * (DE - YG)
            y_start, y_end = den + 0.10, DE - 0.30  # 戗脊 → 檐口（角部）
        if y_end - y_start < 0.15:
            continue
        for sy in (-1, 1):
            pts = []
            for k in range(nst + 1):
                y = sy * (y_start + (y_end - y_start) * k / nst)
                pts.append(Vector((x, y, roof_z(x, y))))
            _tile_row(mb, pts)
            # 瓦当（扁圆瓦头）
            p = pts[-1]
            mbd.tube((p.x, p.y - sy * 0.012, p.z + TILE_R * 0.42),
                     (p.x, p.y + sy * 0.028, p.z + TILE_R * 0.42),
                     TILE_R * 1.06, TILE_R * 1.02, sides=12)
            # 滴水（两垄之间下垂的板瓦头）
            if i < nx:
                qx = x + TILE_GAP / 2
                qy = sy * (DE - 0.30)
                mbd.box((qx, qy, eave_z(qx, qy) - 0.045), (TILE_GAP * 0.78, 0.045, 0.11))

    # ---- 两山撒头瓦垄（沿戗脊方向，自山花底边生出） ----
    for sx in (-1, 1):
        nv = 12
        for i in range(nv + 1):
            v = -0.92 + 1.84 * i / nv
            pts = []
            for k in range(nst + 1):
                u = 0.05 + 0.91 * k / nst
                x = sx * (XG + u * (WE - XG))
                den = YG + u * (DE - YG)
                y = v * den
                pts.append(Vector((x, y, hip_z(u) + corner_lift(x, y))))
            _tile_row(mb, pts)
            p = pts[-1]
            mbd.tube((p.x - sx * 0.012, p.y, p.z + TILE_R * 0.42),
                     (p.x + sx * 0.028, p.y, p.z + TILE_R * 0.42),
                     TILE_R * 1.06, TILE_R * 1.02, sides=12)

    mb.build("屋面_筒瓦垄", 'roof', MAT["tile"], smooth=True)
    mbd.build("屋面_瓦当滴水", 'roof', MAT["tile"])


# =============================================================================
# 十四、脊饰（正脊、垂脊、戗脊、鸱尾）
# =============================================================================

def build_ridges():
    mb = MB()

    # ---- 正脊 ----
    mb.box((0, 0, RIDGE_Z + 0.16), (2 * XG + 0.30, 0.42, 0.34))
    mb.box((0, 0, RIDGE_Z + 0.40), (2 * XG + 0.22, 0.34, 0.16))
    # 脊上叠瓦状起伏
    n = int((2 * XG) / 0.34)
    for i in range(n):
        x = -XG + 0.17 + i * 0.34
        mb.box((x, 0, RIDGE_Z + 0.50), (0.20, 0.30, 0.08))

    # ---- 垂脊（山花上缘，随举折曲线） ----
    for sx in (-1, 1):
        for sy in (-1, 1):
            pts = []
            for k in range(9):
                y = sy * YG * k / 8
                pts.append(Vector((sx * (XG + 0.10), y, roof_z(sx * XG, y) + 0.06)))
            for k in range(len(pts) - 1):
                mb.beam(pts[k], pts[k + 1], 0.24, 0.22, up=(0, 0, 1),
                        ext0=0.02, ext1=0.02)

    # ---- 戗脊（山花底角 → 檐角） ----
    for sx in (-1, 1):
        for sy in (-1, 1):
            pts = []
            for k in range(7):
                u = k / 6.0
                x = sx * (XG + u * (WE - XG))
                den = YG + u * (DE - YG)
                y = sy * den
                pts.append(Vector((x, y, hip_z(u) + corner_lift(x, y) + 0.06)))
            for k in range(len(pts) - 1):
                mb.beam(pts[k], pts[k + 1], 0.22, 0.20, up=(0, 0, 1),
                        ext0=0.02, ext1=0.02)

    mb.build("脊_正脊垂脊戗脊", 'ridge', MAT["ridge"])

    # ---- 博风板 + 悬鱼（山花边缘的木构护板，唐构特征） ----
    mb_b = MB()
    for sx in (-1, 1):
        pts = []
        for k in range(17):
            y = -YG + 2 * YG * k / 16
            pts.append(Vector((sx * (XG + 0.05), y, roof_z(sx * XG, y) + 0.02)))
        for k in range(len(pts) - 1):
            mb_b.beam(pts[k], pts[k + 1], 0.09, 0.26, up=(0, 0, 1),
                      ext0=0.02, ext1=0.02)
        # 山花板下缘的压边（收头）
        mb_b.box((sx * (XG + 0.04), 0, H_G - 0.03), (0.10, 2 * YG, 0.10))
    mb_b.build("脊_博风板", 'ridge', MAT["wood2"])

    # ---- 鸱尾（唐代鱼尾形吻兽） ----
    outline = [
        (0.00, 0.00), (0.06, 0.32), (0.18, 0.64), (0.34, 0.92),
        (0.54, 1.12), (0.78, 1.26), (0.99, 1.30), (1.13, 1.20),
        (1.08, 1.02), (0.94, 0.92), (0.83, 0.74), (0.74, 0.52),
        (0.60, 0.30), (0.42, 0.12), (0.24, 0.00),
    ]
    mb2 = MB()
    for sx in (-1, 1):
        pts = [(sx * (-p[0]), p[1]) for p in outline]
        mb2.poly_prism(pts, 0.30, plane='XZ',
                       origin=(sx * (XG + 0.05), 0.0, RIDGE_Z + 0.24))
        # 吻座
        mb2.box((sx * (XG + 0.04), 0, RIDGE_Z + 0.13), (0.46, 0.50, 0.26))
    ob = mb2.build("脊_鸱尾", 'ridge', MAT["ridge"])
    add_bevel(ob, 0.012, 2)

    # ---- 风铎（檐角悬铃） ----
    mb3 = MB()
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (WE - 0.30), sy * (DE - 0.30)
            z = roof_z(x, y) - 0.30
            mb3.tube((x, y, z), (x, y, z - 0.18), 0.012, 0.012, sides=6)
            mb3.tube((x, y, z - 0.18), (x, y, z - 0.34), 0.055, 0.075, sides=10)
            mb3.tube((x, y, z - 0.34), (x, y, z - 0.40), 0.075, 0.02, sides=10)
    mb3.build("脊_风铎", 'ridge', MAT["metal"], smooth=True)


# =============================================================================
# 十五、环境（相机 / 灯光 / 地面）
# =============================================================================

def build_env():
    coll = get_coll('env')

    # 地面
    me = bpy.data.meshes.new("地面")
    s = 26.0
    me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
    me.update()
    ob = bpy.data.objects.new("地面_环境", me)
    coll.objects.link(ob)
    ob.data.materials.append(MAT["ground"])
    ob.location = (0, 0, -0.02)

    # 相机（西南 3/4 视角，自动对准殿身中部）
    cam_data = bpy.data.cameras.new("相机")
    cam_data.lens = 50
    cam = bpy.data.objects.new("相机_Camera", cam_data)
    coll.objects.link(cam)
    eye = (13.5, -21.5, 8.2)
    tgt = (0.0, 0.0, 5.0)
    cam.location = eye
    dx, dy, dz = tgt[0] - eye[0], tgt[1] - eye[1], tgt[2] - eye[2]
    horiz = math.hypot(dx, dy)
    cam.rotation_euler = (math.pi / 2 + math.atan2(dz, horiz), 0.0,
                          math.atan2(-dx, dy))
    bpy.context.scene.camera = cam
    sc = bpy.context.scene
    sc.render.resolution_x = 1600
    sc.render.resolution_y = 1000

    # 太阳光
    sun_data = bpy.data.lights.new("太阳", type='SUN')
    sun_data.energy = 3.6
    sun_data.angle = math.radians(2.5)
    sun = bpy.data.objects.new("灯光_太阳", sun_data)
    coll.objects.link(sun)
    sun.rotation_euler = (math.radians(56), 0.0, math.radians(-46))

    # 世界环境光
    w = bpy.context.scene.world
    if w is None:
        w = bpy.data.worlds.new("World")
        bpy.context.scene.world = w
    w.use_nodes = True
    for n in w.node_tree.nodes:
        if n.type == 'BACKGROUND':
            n.inputs[0].default_value = srgb(168, 170, 172)
            n.inputs[1].default_value = 0.12
            break


# =============================================================================
# 十六、主流程
# =============================================================================

def reset_scene():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras,
                  bpy.data.lights, bpy.data.collections):
        try:
            for b in list(block):
                if b.users == 0:
                    block.remove(b)
        except Exception:
            pass


def build():
    reset_scene()
    setup_collections()
    build_materials()

    build_platform()
    build_columns()
    build_architrave()
    build_walls()
    build_dougong()
    build_frame()
    build_rafters()
    build_roof_surface()
    build_ridges()
    build_env()

    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.length_unit = 'METERS'
    try:
        sc.render.engine = 'BLENDER_EEVEE_NEXT'
    except Exception:
        try:
            sc.render.engine = 'BLENDER_EEVEE'
        except Exception:
            pass

    bpy.context.view_layer.update()

    n_obj = sum(len(c.objects) for c in COLL.values())
    n_tri = sum(len(o.data.polygons) for c in COLL.values()
                for o in c.objects if o.type == 'MESH')
    print("=" * 62)
    print(" 南禅寺大殿 程序化建模完成")
    print("   对象数 : %d" % n_obj)
    print("   面    数 : %d" % n_tri)
    print("   通面阔 : %.2f m   通进深 : %.2f m" % (WIDTH, DEPTH))
    print("   台基高 : %.2f m   柱高   : %.2f m" % (PLAT_H, COL_H))
    print("   檐口高 : %.2f m   正脊高 : %.2f m" % (HE, RIDGE_Z))
    print("=" * 62)
    return True


if __name__ == "__main__":
    build()
