#!/usr/bin/env python3
"""生成参考版所需材质：做旧竹纸、胡桃木桌面、书口纸叠。

用法：python3 tools/make_textures.py
输出：assets/paper/paper.jpg、desk.jpg、edges.png
"""

import os
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "assets", "paper"))
os.makedirs(OUT, exist_ok=True)

rng = np.random.default_rng(20261116)


def value_noise(h, w, scale):
    """低频随机场，双三次放大后作为纹理起伏。"""
    small = rng.normal(0, 1, (max(2, h // scale), max(2, w // scale)))
    span = float(small.max() - small.min()) + 1e-6
    img = Image.fromarray(((small - small.min()) / span * 255).astype(np.uint8))
    img = img.resize((w, h), Image.BICUBIC)
    return np.asarray(img, dtype=np.float32) / 255.0


def paper(w=1240, h=1720):
    base = np.zeros((h, w, 3), dtype=np.float32)
    base[..., 0] = 206
    base[..., 1] = 176
    base[..., 2] = 124

    # 1. 多尺度起伏：纸浆不匀
    lum = np.zeros((h, w), dtype=np.float32)
    for scale, weight in ((220, 0.85), (110, 0.5), (48, 0.32), (18, 0.18), (7, 0.08)):
        lum += (value_noise(h, w, scale) - 0.5) * weight
    base += (lum * 42)[..., None]

    # 2. 纤维：短促的横竖细丝
    fib = np.zeros((h, w), dtype=np.float32)
    for _ in range(3200):
        y = rng.integers(0, h)
        x = rng.integers(0, w)
        ln = int(rng.integers(8, 80))
        horiz = rng.random() < 0.62
        v = rng.uniform(-1, 1) * 14
        if horiz:
            fib[y, x:x + ln] += v
        else:
            fib[y:y + ln, x] += v
    fib = np.asarray(
        Image.fromarray(((fib + 14) / 28 * 255).clip(0, 255).astype(np.uint8)).filter(
            ImageFilter.GaussianBlur(0.55)
        ),
        dtype=np.float32,
    ) / 255.0
    base += ((fib - 0.5) * 20)[..., None]

    # 3. 帘纹：竹纸抄纸留下的细密竖纹
    laid = (np.sin(np.arange(w) * np.pi / 4.8) * 1.2).astype(np.float32)
    base += laid[None, :, None]

    # 4. 霉斑与虫蛀：小点深褐，边缘虚
    ys, xs = np.ogrid[0:h, 0:w]
    for _ in range(220):
        cx, cy = rng.integers(0, w), rng.integers(0, h)
        r = rng.uniform(0.9, 13)
        a = rng.uniform(0.10, 0.62)
        d = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
        mask = np.clip(1 - d / r, 0, 1) ** 1.5 * a
        tint = np.array([96, 64, 32], dtype=np.float32)
        base = base * (1 - mask[..., None]) + tint * mask[..., None]

    # 5. 水渍：大片淡黄晕圈（用噪声扭曲半径，避免看出是圆）
    warp_r = (value_noise(h, w, 90) - 0.5) * 0.35 + (value_noise(h, w, 30) - 0.5) * 0.12
    for _ in range(4):
        cx, cy = rng.integers(0, w), rng.integers(0, h)
        r = rng.uniform(0.12, 0.3) * min(w, h)
        d = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2) / r + warp_r
        ring = np.exp(-((d - 0.96) ** 2) / 0.0012) * 0.1 + np.clip(1 - d, 0, 1) ** 2 * 0.04
        base *= 1 - ring[..., None] * 0.16

    # 5b. 中尺度色斑：抄纸厚薄不匀
    mottle = (value_noise(h, w, 150) - 0.5) * 0.06 + (value_noise(h, w, 60) - 0.5) * 0.05
    base *= (1 + mottle)[..., None]

    # 5c. 细颗粒：纸面粗糙
    grain = rng.normal(0, 1, (h, w, 1)).astype(np.float32)
    base += grain * 3.4

    # 6. 边框做旧：边缘不规则地压暗发褐
    ex = np.minimum(np.arange(w), np.arange(w)[::-1]).astype(np.float32)
    ey = np.minimum(np.arange(h), np.arange(h)[::-1]).astype(np.float32)
    dist = np.minimum(ex[None, :], ey[:, None])
    jitter = (value_noise(h, w, 46) - 0.5) * 44 + (value_noise(h, w, 14) - 0.5) * 12
    t = np.clip((dist + jitter) / 118.0, 0, 1)
    t = t * t * (3 - 2 * t)  # smoothstep
    brown = np.array([92, 62, 30], dtype=np.float32)
    mix = (1 - t) ** 1.25 * 0.62
    base = base * (1 - mix[..., None]) + (base * 0.55 + brown * 0.45) * mix[..., None]

    # 7. 轻微整体色偏 + 柔化
    base[..., 0] *= 1.015
    base[..., 2] *= 0.965
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(0.4)
    )
    img.save(os.path.join(OUT, "paper.jpg"), quality=92, subsampling=0)
    print("paper.jpg", img.size)


def desk(w=1800, h=1200):
    """胡桃木桌面：宽幅年轮带 + 深色条纹 + 大面积明暗。"""
    yy = np.arange(h, dtype=np.float32)[:, None]
    xx = np.arange(w, dtype=np.float32)[None, :]

    # 相位被大尺度噪声扭曲，形成宽而松的木纹带
    warp = (
        (value_noise(h, w, 620) - 0.5) * 260
        + (value_noise(h, w, 240) - 0.5) * 110
        + (value_noise(h, w, 70) - 0.5) * 24
    )
    pitch = 128 + (value_noise(h, w, 400) - 0.5) * 60
    rings = np.sin((yy + warp) * 2 * np.pi / pitch)
    rings = np.sign(rings) * np.abs(rings) ** 2.2  # 压平，只留下宽缓的明暗
    presence = np.clip(value_noise(h, w, 340) * 1.9 - 0.55, 0, 1)
    grain = rings * presence * 0.75

    # 深色条纹：沿 x 拉长的细长暗痕
    for _ in range(9):
        cy = rng.integers(0, h)
        thick = rng.uniform(1.2, 4.5)
        amp = rng.uniform(0.25, 0.7)
        bend = (value_noise(1, w, 80) - 0.5) * 34
        d = np.abs(yy - (cy + bend))
        grain -= np.exp(-(d ** 2) / (2 * thick ** 2)) * amp

    # 横向纤维：模糊后的大尺度起伏
    streak = value_noise(h, w, 5)
    streak = np.asarray(
        Image.fromarray((streak * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(9)),
        dtype=np.float32,
    ) / 255.0
    grain += (streak - 0.5) * 1.1

    # 细密木孔
    pores = np.zeros((h, w), dtype=np.float32)
    for _ in range(5200):
        py = rng.integers(0, h)
        px = rng.integers(0, w)
        ln = int(rng.integers(6, 40))
        pores[py, px:px + ln] -= rng.uniform(0.15, 0.6)
    pores = np.asarray(
        Image.fromarray(((pores + 1) * 127).clip(0, 255).astype(np.uint8)).filter(
            ImageFilter.GaussianBlur(0.6)
        ),
        dtype=np.float32,
    ) / 255.0 - 0.5
    grain += pores * 0.4

    dark = np.array([34, 20, 13], dtype=np.float32)
    light = np.array([124, 82, 54], dtype=np.float32)
    t = np.clip(0.52 + grain * 0.3, 0, 1)[..., None]
    img = dark * (1 - t) + light * t

    # 刨光高光
    sheen = 0.09 * np.exp(-((yy - h * 0.24) ** 2) / (2 * (h * 0.3) ** 2))
    img += sheen[..., None] * 85

    # 四周暗角
    gx = (xx / w - 0.5) * 2
    gy = (yy / h - 0.5) * 2
    vig = np.clip(1 - 0.62 * (gx ** 2 + gy ** 2), 0.14, 1)
    img *= vig[..., None]

    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(1.6)
    )
    out.save(os.path.join(OUT, "desk.jpg"), quality=86, subsampling=0)
    print("desk.jpg", out.size)


def edges(w=260, h=1400):
    """书口：一叠纸的侧边，用细横线表现层叠。"""
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[..., :3] = np.array([196, 172, 130], dtype=np.uint8)
    arr[..., 3] = 255
    rng2 = np.random.default_rng(7)
    for y in range(h):
        if y % 3 == 0:
            arr[y, :, :3] = (arr[y, :, :3] * 0.86).astype(np.uint8)
    noise = rng2.normal(0, 7, (h, w, 1))
    arr[..., :3] = np.clip(arr[..., :3] + noise, 0, 255).astype(np.uint8)
    Image.fromarray(arr).filter(ImageFilter.GaussianBlur(0.3)).save(
        os.path.join(OUT, "edges.png")
    )
    print("edges.png", (w, h))


if __name__ == "__main__":
    paper()
    desk()
    edges()
