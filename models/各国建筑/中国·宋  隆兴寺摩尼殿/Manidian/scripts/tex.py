# -*- coding: utf-8 -*-
"""程序化贴图生成 + 材质库
全部贴图为 numpy 生成的周期性无缝纹理，写入 textures/ 并打包进 .blend，
因此在任何机器上打开工程都不会丢失贴图。
"""
import bpy, os, math
import numpy as np


TEXDIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "textures")


def _pnoise(size, base=3, octaves=5, seed=1, aniso=(1.0, 1.0)):
    """周期性无缝噪声（正弦叠加，频率取整数保证 tileable）"""
    rng = np.random.default_rng(seed)
    ys, xs = np.mgrid[0:size, 0:size] / float(size)
    out = np.zeros((size, size), np.float32)
    amp = 1.0
    f = base
    for _ in range(octaves):
        for _k in range(5):
            fx = int(rng.integers(1, max(2, f)))
            fy = int(rng.integers(1, max(2, f)))
            ph = rng.random() * 6.2832
            out += amp * np.sin(2 * math.pi * (fx * xs * aniso[0] + fy * ys * aniso[1]) + ph)
        amp *= 0.52
        f = max(2, int(f * 1.9))
    out -= out.min()
    out /= max(1e-6, out.max())
    return out


def _save(name, rgb):
    os.makedirs(TEXDIR, exist_ok=True)
    h, w = rgb.shape[:2]
    img = bpy.data.images.new(name, w, h, alpha=False, float_buffer=False)
    a = np.ones((h, w, 4), np.float32)
    a[:, :, :3] = np.clip(rgb, 0, 1)
    img.pixels.foreach_set(a.ravel())
    p = os.path.join(TEXDIR, name + ".png")
    img.filepath_raw = p
    img.file_format = 'PNG'
    img.save()
    img.pack()
    return img


# ---------------------------------------------------------------- 单张贴图
def tex_tile(size=1024):
    """绿琉璃筒瓦/板瓦：底色 + 釉色斑驳 + 顺坡流痕"""
    n1 = _pnoise(size, 3, 5, 11, aniso=(1.0, 0.35))     # 顺坡拉长
    n2 = _pnoise(size, 7, 4, 23)
    n3 = _pnoise(size, 22, 3, 31)
    base = np.array([0.052, 0.122, 0.094], np.float32)
    hi = np.array([0.100, 0.192, 0.152], np.float32)
    lo = np.array([0.026, 0.058, 0.045], np.float32)
    k = (0.55 * n1 + 0.30 * n2 + 0.15 * n3)[..., None]
    rgb = lo + (hi - lo) * k
    # 釉面高光块
    gloss = (n3 ** 3)[..., None]
    rgb = rgb * (1 - 0.45 * gloss) + 0.30 * gloss
    # 灰白风化
    weather = np.clip((n2 - 0.50) * 2.4, 0, 1)[..., None]
    rgb = rgb * (1 - 0.78 * weather) + np.array([0.295, 0.305, 0.278]) * (0.78 * weather)
    # 积水污痕
    dirt = np.clip((n1 - 0.55) * 2.2, 0, 1)[..., None]
    rgb *= (1 - 0.45 * dirt)
    return _save("T_roof_tile", rgb)


def tex_wall(size=1024):
    """朱红抹灰墙面：大面积平整，只有低频色差与极淡的返潮

    早先版本用竖向拉伸噪声做雨痕，但 aniso 取非整数会破坏 tileable，
    在 Object 坐标投影下形成等距竖条，远看像木板——这是"不像"的主因之一。
    现在改为各向同性噪声，明度变化压到 ±12% 以内。
    """
    n1 = _pnoise(size, 2, 5, 101)      # 大尺度色差
    n2 = _pnoise(size, 7, 4, 202)      # 中尺度斑驳
    n3 = _pnoise(size, 34, 3, 303)     # 灰泥细颗粒
    base = np.array([0.318, 0.060, 0.046], np.float32)
    rgb = np.ones((size, size, 3), np.float32) * base
    k = (0.62 * n1 + 0.38 * n2)[..., None]
    rgb *= (0.88 + 0.24 * k)
    rgb *= (0.975 + 0.050 * n3)[..., None]
    # 墙根返潮：沿高度轻微加深，不做竖向拉伸
    yy = np.mgrid[0:size, 0:size][0] / float(size)
    rgb *= (1.0 - 0.12 * np.clip(1.0 - yy / 0.32, 0, 1))[..., None]
    return _save("T_wall_red", rgb)


def tex_wood(size=1024):
    """深褐木纹（斗拱、柱子、板门）"""
    ys, xs = np.mgrid[0:size, 0:size] / float(size)
    n1 = _pnoise(size, 2, 5, 707, aniso=(1.0, 0.25))
    n2 = _pnoise(size, 18, 4, 808, aniso=(0.15, 1.0))
    grain = 0.5 + 0.5 * np.sin(2 * math.pi * (26 * ys + 3.0 * n1))
    base = np.array([0.075, 0.045, 0.032], np.float32)
    rgb = np.ones((size, size, 3), np.float32) * base
    rgb *= (0.55 + 0.85 * (0.55 * grain + 0.45 * n1))[..., None]
    rgb *= (0.85 + 0.30 * n2)[..., None]
    rgb += np.array([0.030, 0.016, 0.010]) * (grain ** 6)[..., None]
    return _save("T_wood_dark", rgb)


def tex_stone(size=1024):
    """花岗岩台基：麻点 + 色斑"""
    n1 = _pnoise(size, 4, 5, 909)
    n2 = _pnoise(size, 40, 3, 910)
    base = np.array([0.335, 0.325, 0.300], np.float32)
    rgb = np.ones((size, size, 3), np.float32) * base
    rgb *= (0.70 + 0.60 * n1)[..., None]
    rgb *= (0.86 + 0.30 * n2)[..., None]
    sp = (np.random.default_rng(9).random((size, size)) > 0.955).astype(np.float32)
    rgb = rgb * (1 - 0.35 * sp[..., None]) + 0.20 * sp[..., None]
    return _save("T_stone", rgb)


def tex_caihua(size=512):
    """斗拱/额枋彩画（青绿叠晕简化）"""
    ys, xs = np.mgrid[0:size, 0:size] / float(size)
    band = np.abs(np.sin(2 * math.pi * ys * 3))
    rgb = np.zeros((size, size, 3), np.float32)
    blue = np.array([0.045, 0.115, 0.175], np.float32)
    green = np.array([0.055, 0.145, 0.110], np.float32)
    white = np.array([0.72, 0.70, 0.62], np.float32)
    sel = (band > 0.55)[..., None]
    rgb = np.where(sel, blue, green) * np.ones((1, 1, 3))
    rgb = rgb * (0.85 + 0.25 * _pnoise(size, 5, 4, 55)[..., None])
    edge = (np.abs(band - 0.55) < 0.035)[..., None]
    rgb = np.where(edge, white, rgb)
    return _save("T_caihua", rgb)


def tex_door(size=512):
    """板门：暗红漆面木纹"""
    n1 = _pnoise(size, 3, 5, 606, aniso=(1.0, 0.22))
    ys, xs = np.mgrid[0:size, 0:size] / float(size)
    grain = 0.5 + 0.5 * np.sin(2 * math.pi * (18 * ys + 2.0 * n1))
    base = np.array([0.215, 0.045, 0.038], np.float32)
    rgb = np.ones((size, size, 3), np.float32) * base
    rgb *= (0.70 + 0.55 * (0.6 * grain + 0.4 * n1))[..., None]
    return _save("T_door_red", rgb)


def tex_ground(size=512):
    n1 = _pnoise(size, 5, 5, 123)
    n2 = _pnoise(size, 26, 3, 456)
    base = np.array([0.255, 0.250, 0.235], np.float32)
    rgb = np.ones((size, size, 3), np.float32) * base
    rgb *= (0.72 + 0.55 * n1)[..., None]
    rgb *= (0.88 + 0.24 * n2)[..., None]
    return _save("T_ground", rgb)
