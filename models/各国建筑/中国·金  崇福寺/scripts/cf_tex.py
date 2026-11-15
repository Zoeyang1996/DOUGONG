# -*- coding: utf-8 -*-
"""
cf_tex.py —— 全部贴图的程序化生成（砖、木、石、瓦、琉璃、铜、灰泥）
生成结果写入 textures/*.png 并打包进 .blend
"""
import numpy as np
import math
from cf_lib import (tile_fbm, grain, save_png, normal_from_height, mix, TEX_DIR)


def clamp01(a):
    return np.clip(a, 0.0, 1.0)


# ---------------------------------------------------------------------------
def tex_wall_red(S=1536):
    base = np.array([0.600, 0.258, 0.183], dtype=np.float32)   # 朱红灰泥
    n1 = tile_fbm(S, S, freq=3, octaves=5, seed=11)
    n2 = tile_fbm(S, S, freq=9, octaves=4, seed=12, aniso=0.18)  # 竖向雨痕
    n3 = tile_fbm(S, S, freq=48, octaves=3, seed=13)
    n4 = grain(S, S, seed=14, s=2)

    col = np.ones((S, S, 3), dtype=np.float32) * base
    # 大面积色差（新旧灰泥补配）
    col = mix(col, base * np.array([1.10, 0.94, 0.90]), (n1 - 0.35) * 1.1)
    # 竖向雨痕变深
    streak = clamp01((n2 - 0.52) * 2.4)
    col = mix(col, np.array([0.545, 0.225, 0.165]), streak * 0.55)
    # 细微灰泥颗粒
    col *= (0.94 + 0.12 * n3)[:, :, None] * (0.96 + 0.08 * n4)[:, :, None]
    # 底部返潮发灰
    yy = np.linspace(0, 1, S)[:, None]
    damp = clamp01((yy - 0.72) * 3.2) * 0.55
    col = mix(col, np.array([0.470, 0.230, 0.185]), damp)

    h = 0.45 * n3 + 0.35 * n4 + 0.2 * n1
    return save_png("wall_red", clamp01(col)), save_png("wall_red_n", normal_from_height(h, 2.6))


def tex_plaster_white(S=1024):
    base = np.array([0.800, 0.780, 0.725], dtype=np.float32)
    n1 = tile_fbm(S, S, freq=4, octaves=5, seed=21)
    n2 = tile_fbm(S, S, freq=10, octaves=4, seed=22, aniso=0.25)
    n3 = grain(S, S, seed=23, s=3)
    col = np.ones((S, S, 3), dtype=np.float32) * base
    col = mix(col, np.array([0.72, 0.70, 0.64]), (n1 - 0.4) * 0.8)
    col = mix(col, np.array([0.55, 0.54, 0.49]), clamp01((n2 - 0.6) * 3) * 0.35)
    col *= (0.95 + 0.09 * n3)[:, :, None]
    yy = np.linspace(0, 1, S)[:, None]
    col = mix(col, np.array([0.48, 0.47, 0.43]), clamp01((yy - 0.8) * 3.5) * 0.5)
    h = 0.5 * n3 + 0.5 * n1
    return save_png("plaster_white", clamp01(col)), save_png("plaster_white_n", normal_from_height(h, 2.0))


def tex_wood(name, base, S=1024, seed=31, dark=0.72, contrast=0.16, rough_v=0.0):
    """竖向木纹"""
    b = np.array(base, dtype=np.float32)
    n1 = tile_fbm(S, S, freq=2, octaves=5, seed=seed, aniso=0.06)
    n2 = tile_fbm(S, S, freq=14, octaves=4, seed=seed + 1, aniso=0.05)
    n3 = grain(S, S, seed=seed + 2, s=3)
    col = np.ones((S, S, 3), dtype=np.float32) * b
    col = mix(col, b * dark, clamp01((n1 - 0.3) * 1.2) * 0.85)
    col = mix(col, b * (dark + 0.22), clamp01((n2 - 0.55) * 2.2) * 0.5)
    col *= (0.94 + contrast * n3)[:, :, None]
    # 木节
    rng = np.random.default_rng(seed)
    for _ in range(6):
        cx, cy = rng.integers(0, S, 2)
        yy, xx = np.mgrid[0:S, 0:S]
        d = np.sqrt(((xx - cx) / (S * 0.03)) ** 2 + ((yy - cy) / (S * 0.06)) ** 2)
        knot = clamp01(1 - d)
        col = mix(col, b * 0.55, knot * 0.8)
    h = 0.6 * n2 + 0.4 * n3
    return (save_png(name, clamp01(col)),
            save_png(name + "_n", normal_from_height(h, 3.2)))


def tex_stone(name, base, S=1024, seed=41, speck=0.10, dirt=0.25):
    b = np.array(base, dtype=np.float32)
    n1 = tile_fbm(S, S, freq=3, octaves=5, seed=seed)
    n2 = grain(S, S, seed=seed + 1, s=1)
    n3 = tile_fbm(S, S, freq=26, octaves=3, seed=seed + 2)
    col = np.ones((S, S, 3), dtype=np.float32) * b
    col = mix(col, b * 0.80, clamp01((n1 - 0.45) * 1.6) * 0.7)
    col = mix(col, b * 1.10, clamp01((n3 - 0.6) * 2.0) * 0.4)
    col *= (1.0 - speck + speck * 2 * n2)[:, :, None]
    yy = np.linspace(0, 1, S)[:, None]
    col = mix(col, b * 0.62, clamp01((yy - 0.75) * 3.0) * dirt)
    h = 0.5 * n2 + 0.5 * n3
    return save_png(name, clamp01(col)), save_png(name + "_n", normal_from_height(h, 1.8))


def tex_brick_ground(S=2048):
    """青砖地面：错缝铺砌，1 张贴图 = 3.6m x 3.6m"""
    b = np.array([0.335, 0.330, 0.310], dtype=np.float32)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32) / S
    rows, cols = 12, 6                     # 12 行 x 6 列（0.3 x 0.6 m）
    ry = yy * rows
    row = np.floor(ry)
    offset = (row % 2) * 0.5
    rx = (xx + offset / cols) * cols
    col_i = np.floor(rx)
    fy = ry - row
    fx = rx - col_i
    mortar = (np.minimum(np.minimum(fy, 1 - fy) * 0.6, np.minimum(fx, 1 - fx) * 0.25) < 0.012)
    rng = np.random.default_rng(7)
    tone = rng.random((rows + 1, cols + 1))
    ti = np.clip(row.astype(int), 0, rows - 1)
    tj = (col_i.astype(int) % cols)
    tone_map = tone[ti, tj]
    n1 = tile_fbm(S, S, freq=6, octaves=5, seed=8)
    n2 = grain(S, S, seed=9, s=2)
    col = b * (0.88 + 0.24 * tone_map)[:, :, None]
    col *= (0.93 + 0.14 * n2)[:, :, None]
    col = mix(col, np.array([0.62, 0.60, 0.55]), (n1 - 0.5) * 0.35 + 0.2)
    col = mix(col, np.array([0.72, 0.70, 0.64]), mortar.astype(np.float32) * 0.9)
    # 污渍
    n3 = tile_fbm(S, S, freq=2, octaves=4, seed=10)
    col = mix(col, np.array([0.38, 0.365, 0.34]), clamp01((n3 - 0.62) * 2.2) * 0.35)
    h = mortar.astype(np.float32) * 0.8 + 0.2 * n2
    return save_png("brick_ground", clamp01(col)), save_png("brick_ground_n", normal_from_height(h, 4.0))


def tex_roof_tile(S=1024):
    """屋面底瓦（板瓦搭接面）：暗哑灰瓦，苔痕与雨渍"""
    base = np.array([0.238, 0.238, 0.222], dtype=np.float32)
    n1 = tile_fbm(S, S, freq=4, octaves=5, seed=51)
    n2 = grain(S, S, seed=52, s=2)
    n3 = tile_fbm(S, S, freq=26, octaves=3, seed=53, aniso=0.35)
    col = np.ones((S, S, 3), dtype=np.float32) * base
    col = mix(col, np.array([0.072, 0.080, 0.072]), clamp01((n1 - 0.45) * 1.5) * 0.60)
    col = mix(col, np.array([0.165, 0.172, 0.152]), clamp01((n3 - 0.60) * 2.2) * 0.32)
    col *= (0.90 + 0.18 * n2)[:, :, None]
    h = 0.65 * n3 + 0.35 * n2
    return save_png("roof_tile", clamp01(col)), save_png("roof_tile_n", normal_from_height(h, 1.6))


def tex_glaze(name, base, S=1024, seed=61):
    """琉璃：饱和、带釉面斑驳与开片"""
    b = np.array(base, dtype=np.float32)
    n1 = tile_fbm(S, S, freq=5, octaves=5, seed=seed)
    n2 = grain(S, S, seed=seed + 1, s=2)
    col = np.ones((S, S, 3), dtype=np.float32) * b
    col = mix(col, b * 1.35 + 0.10, clamp01((n1 - 0.55) * 2.2) * 0.5)
    col = mix(col, b * 0.62, clamp01((n1 - 0.3) * -1.6 + 0.35) * 0.35)
    # 开片：细密折线
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32) / S
    crack = (np.abs(np.sin((xx * 37 + yy * 21 + n1 * 9) * math.pi)) < 0.02)
    col = mix(col, b * 0.55, crack.astype(np.float32) * 0.45)
    col *= (0.95 + 0.10 * n2)[:, :, None]
    h = 0.6 * n1 + 0.4 * n2
    return save_png(name, clamp01(col)), save_png(name + "_n", normal_from_height(h, 2.0))


def tex_bronze(S=1024):
    base = np.array([0.235, 0.215, 0.165], dtype=np.float32)
    n1 = tile_fbm(S, S, freq=5, octaves=5, seed=71)
    n2 = grain(S, S, seed=72, s=2)
    col = np.ones((S, S, 3), dtype=np.float32) * base
    col = mix(col, np.array([0.20, 0.30, 0.24]), clamp01((n1 - 0.5) * 2.0) * 0.65)  # 铜绿
    col = mix(col, np.array([0.10, 0.09, 0.07]), clamp01((n1 - 0.35) * -1.8 + 0.4) * 0.45)
    col *= (0.9 + 0.2 * n2)[:, :, None]
    h = 0.7 * n1 + 0.3 * n2
    return save_png("bronze", clamp01(col)), save_png("bronze_n", normal_from_height(h, 2.0))


def tex_bark(S=512):
    base = np.array([0.29, 0.24, 0.19], dtype=np.float32)
    n1 = tile_fbm(S, S, freq=8, octaves=5, seed=81, aniso=0.08)
    n2 = grain(S, S, seed=82, s=2)
    col = base[None, None, :] * (0.75 + 0.5 * n1)[:, :, None]
    col *= (0.9 + 0.2 * n2)[:, :, None]
    h = n1 * 0.7 + n2 * 0.3
    return save_png("bark", clamp01(col)), save_png("bark_n", normal_from_height(h, 5.0))


def tex_door_panel(S=1024):
    """裙板浮雕：回纹边框 + 卷草暗纹"""
    base = np.array([0.545, 0.215, 0.155], dtype=np.float32)
    col = np.ones((S, S, 3), dtype=np.float32) * base
    n1 = tile_fbm(S, S, freq=4, octaves=4, seed=91, aniso=0.1)
    n2 = grain(S, S, seed=92, s=2)
    col *= (0.93 + 0.12 * n2)[:, :, None]
    col = mix(col, base * 0.8, clamp01((n1 - 0.5) * 1.5) * 0.4)
    # 边框凹槽
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32) / S
    e = 0.10
    inner = (xx > e) & (xx < 1 - e) & (yy > e) & (yy < 1 - e)
    frame = (~inner) & (xx > 0.04) & (xx < 0.96) & (yy > 0.04) & (yy < 0.96)
    col = mix(col, base * 0.62, frame.astype(np.float32) * 0.75)
    # 中央卷草浮雕（用错位正弦近似）
    r = np.sqrt((xx - 0.5) ** 2 * 1.4 + (yy - 0.5) ** 2)
    orn = (np.sin(r * 60) * 0.5 + 0.5) * np.exp(-((r - 0.26) ** 2) / 0.012)
    col = mix(col, base * 1.18, orn * 0.6 * inner)
    h = 0.45 * n2 + 0.25 * n1 + 0.3 * orn * inner - 0.25 * frame
    return save_png("door_panel", clamp01(col)), save_png("door_panel_n", normal_from_height(h, 3.0))


def tex_plaque(S=1024):
    base = np.array([0.105, 0.115, 0.125], dtype=np.float32)
    n1 = tile_fbm(S, S, freq=6, octaves=4, seed=101)
    col = base[None, None, :] * (0.85 + 0.3 * n1)[:, :, None]
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32) / S
    edge = (xx < 0.055) | (xx > 0.945) | (yy < 0.035) | (yy > 0.965)
    col = mix(col, np.array([0.52, 0.37, 0.14]), edge.astype(np.float32) * 0.95)
    return save_png("plaque", clamp01(col)), None


def build_all():
    T = {}
    T["wall_red"], T["wall_red_n"] = tex_wall_red()
    T["plaster_white"], T["plaster_white_n"] = tex_plaster_white()
    T["wood_dark"], T["wood_dark_n"] = tex_wood("wood_dark", (0.345, 0.215, 0.145), seed=31, dark=0.66, contrast=0.18)
    T["wood_red"], T["wood_red_n"] = tex_wood("wood_red", (0.545, 0.245, 0.175), seed=35, dark=0.74, contrast=0.14)
    T["wood_beam"], T["wood_beam_n"] = tex_wood("wood_beam", (0.395, 0.245, 0.170), seed=39, dark=0.70, contrast=0.20)
    T["stone"], T["stone_n"] = tex_stone("stone", (0.392, 0.378, 0.348), seed=41, speck=0.13)
    T["stone_dark"], T["stone_dark_n"] = tex_stone("stone_dark", (0.390, 0.378, 0.350), seed=45, speck=0.14, dirt=0.35)
    T["brick"], T["brick_n"] = tex_brick_ground()
    T["roof_tile"], T["roof_tile_n"] = tex_roof_tile()
    T["glaze_green"], T["glaze_green_n"] = tex_glaze("glaze_green", (0.082, 0.186, 0.122))
    T["glaze_gold"], T["glaze_gold_n"] = tex_glaze("glaze_gold", (0.72, 0.55, 0.20), seed=65)
    T["bronze"], T["bronze_n"] = tex_bronze()
    T["bark"], T["bark_n"] = tex_bark()
    T["door_panel"], T["door_panel_n"] = tex_door_panel()
    T["plaque"], _ = tex_plaque()
    print("[tex] generated", len([k for k in T if T[k]]), "images ->", TEX_DIR)
    return T
