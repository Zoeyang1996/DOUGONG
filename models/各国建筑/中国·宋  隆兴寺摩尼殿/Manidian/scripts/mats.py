# -*- coding: utf-8 -*-
"""材质库：Principled BSDF + 程序化贴图（对象坐标盒式投影，免 UV）"""
import bpy
import tex


def _tex_node(nt, img, scale=1.0, loc=(-900, 0), coord='Object'):
    tc = nt.nodes.new('ShaderNodeTexCoord')
    tc.location = (loc[0] - 400, loc[1])
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.location = (loc[0] - 220, loc[1])
    mp.inputs['Scale'].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs[coord], mp.inputs['Vector'])
    tx = nt.nodes.new('ShaderNodeTexImage')
    tx.image = img
    tx.location = loc
    tx.extension = 'REPEAT'
    tx.interpolation = 'Smart'
    nt.links.new(mp.outputs['Vector'], tx.inputs['Vector'])
    return tx


def make_mat(name, img, scale=1.0, rough=0.7, metallic=0.0, tint=None,
             tint_strength=1.0, bump=0.12, spec=0.4, coord='Object'):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    out.location = (400, 0)
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (100, 0)
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    if img is not None:
        tx = _tex_node(nt, img, scale, coord=coord)
        src = tx.outputs['Color']
        if tint:
            mix = nt.nodes.new('ShaderNodeMix')
            mix.data_type = 'RGBA'
            mix.blend_type = 'MULTIPLY'
            mix.location = (-500, 100)
            mix.inputs['Factor'].default_value = tint_strength
            nt.links.new(src, mix.inputs[6])
            mix.inputs[7].default_value = (*tint, 1)
            src = mix.outputs[2]
        nt.links.new(src, bsdf.inputs['Base Color'])
        if bump > 0:
            bp = nt.nodes.new('ShaderNodeBump')
            bp.location = (-200, -320)
            bp.inputs['Strength'].default_value = bump
            bp.inputs['Distance'].default_value = 0.06
            nt.links.new(tx.outputs['Color'], bp.inputs['Height'])
            nt.links.new(bp.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metallic
    if 'Specular IOR Level' in bsdf.inputs:
        bsdf.inputs['Specular IOR Level'].default_value = spec
    return m


def plain(name, color, rough=0.6, metallic=0.0, spec=0.5, emit=None):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = [n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'][0]
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metallic
    if 'Specular IOR Level' in b.inputs:
        b.inputs['Specular IOR Level'].default_value = spec
    if emit is not None:
        ec, es = emit
        if 'Emission Color' in b.inputs:
            b.inputs['Emission Color'].default_value = (*ec, 1)
            b.inputs['Emission Strength'].default_value = es
    return m


class Mats:
    def __init__(self):
        print("[tex] 生成贴图 ...")
        self.img_tile = tex.tex_tile()
        self.img_wall = tex.tex_wall()
        self.img_wood = tex.tex_wood()
        self.img_stone = tex.tex_stone()
        self.img_caihua = tex.tex_caihua()
        self.img_door = tex.tex_door()
        self.img_ground = tex.tex_ground()

        self.tile = make_mat("琉璃绿瓦", self.img_tile, 0.55, rough=0.62,
                             tint=(0.74, 0.80, 0.76), bump=0.14, spec=0.18)
        self.tile_dark = make_mat("琉璃瓦_脊件", self.img_tile, 0.9, rough=0.54,
                                  tint=(0.56, 0.64, 0.57), bump=0.16, spec=0.26)
        self.wall = make_mat("朱红墙面", self.img_wall, 0.16, rough=0.90,
                             tint=(0.72, 0.60, 0.58), bump=0.06)
        self.wood = make_mat("木构_斗拱朱漆", self.img_wood, 1.6, rough=0.62,
                             tint=(2.70, 2.05, 1.72), bump=0.20)
        # 额枋/撩檐枋：照片里是未上漆的老木本色，比朱柱浅得多，是立面上最醒目的一条
        self.wood_beam = make_mat("木_额枋原木", self.img_wood, 0.30, rough=0.86,
                                  tint=(5.20, 4.55, 3.80), bump=0.34)
        self.wood_red = make_mat("木构_红柱", self.img_door, 1.2, rough=0.52,
                                 tint=(0.90, 0.78, 0.76), bump=0.22)
        self.door = make_mat("板门_暗红", self.img_door, 1.5, rough=0.48,
                             tint=(1.02, 0.80, 0.76), bump=0.28)
        self.carve = make_mat("雕饰木_悬鱼", self.img_door, 2.4, rough=0.48,
                              tint=(2.05, 1.80, 1.62), bump=0.25)
        self.lattice = make_mat("直棂窗_木", self.img_wood, 2.2, rough=0.55,
                                bump=0.2)
        self.stone = make_mat("石台基", self.img_stone, 0.35, rough=0.9,
                              tint=(1.08, 1.00, 0.88), bump=0.15)
        self.stone_dark = make_mat("石_深", self.img_stone, 0.4, rough=0.88,
                                   tint=(0.62, 0.585, 0.520), bump=0.12)
        self.caihua = make_mat("彩画", self.img_caihua, 0.7, rough=0.55,
                               bump=0.05)
        self.ground = make_mat("地面砖石", self.img_ground, 0.18, rough=0.92,
                               tint=(1.10, 1.02, 0.90), bump=0.12)
        self.gold = plain("鎏金", (0.72, 0.52, 0.16), rough=0.28, metallic=0.95)
        self.bronze = plain("铜件_门钉铺首", (0.34, 0.235, 0.098),
                            rough=0.46, metallic=0.88)
        self.gable = plain("山花板", (0.104, 0.029, 0.022), rough=0.86)
        self.boxue = plain("博缝板", (0.188, 0.182, 0.168), rough=0.90)
        self.carve_red = plain("悬鱼_朱漆", (0.160, 0.042, 0.030), rough=0.66)
        self.beast = plain("脊兽_灰陶", (0.150, 0.150, 0.140), rough=0.80)
        self.panel = plain("拱眼壁_暗", (0.088, 0.037, 0.030), rough=0.88)
        self.plaque = plain("匾额底", (0.020, 0.013, 0.010), rough=0.86, spec=0.14)
        self.water = plain("水面", (0.035, 0.055, 0.045), rough=0.05, spec=0.9)
        self.foliage = plain("树冠", (0.075, 0.115, 0.045), rough=0.85)
        self.bark = plain("树干", (0.09, 0.065, 0.045), rough=0.9)
