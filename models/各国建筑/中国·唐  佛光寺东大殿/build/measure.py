import bpy, numpy as np, os

p = r"D:\zkx88\微信\xwechat_files\wxid_lhj8cx303gh222_91af\temp\RWTemp\2026-11\9e20f478899dc29eb19741386f9343c8\6b1145d9934279a1224436826e0aacfd.jpg"
img = bpy.data.images.load(p)
w, h = img.size
px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1]
def lin2srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c*12.92, 1.055*np.power(c, 1/2.4) - 0.055)
rgb = lin2srgb(px[:, :, :3])
print(f"SIZE {w}x{h}")

# vertical edges along chosen rows
luma = rgb @ np.array([0.299, 0.587, 0.114])
for row_frac in [0.60, 0.72, 0.80, 0.86]:
    y = int(h*row_frac)
    line = luma[y]
    d = np.abs(np.diff(line))
    idx = np.where(d > 0.055)[0]
    # group
    groups = []
    for i in idx:
        if groups and i - groups[-1][-1] <= 3: groups[-1].append(i)
        else: groups.append([i])
    print(f"row y={y} ({row_frac}): edges at x =", [int(np.mean(g)) for g in groups][:60])

# horizontal edges along chosen columns
for col_frac in [0.5, 0.25, 0.12]:
    x = int(w*col_frac)
    col = luma[:, x]
    d = np.abs(np.diff(col))
    idx = np.where(d > 0.05)[0]
    groups = []
    for i in idx:
        if groups and i - groups[-1][-1] <= 3: groups[-1].append(i)
        else: groups.append([i])
    print(f"col x={x} ({col_frac}): edges at y =", [int(np.mean(g)) for g in groups][:60])

# targeted color patches (x0,x1,y0,y1 in normalized coords)
patches = {
 "roof_tile_mid": (0.42,0.55,0.13,0.17),
 "roof_tile_low": (0.30,0.42,0.22,0.25),
 "bracket_wood":  (0.30,0.36,0.46,0.50),
 "door_wood":     (0.30,0.36,0.62,0.72),
 "door_wood2":    (0.62,0.68,0.62,0.72),
 "win_lattice":   (0.205,0.235,0.55,0.62),
 "wall_plaster":  (0.20,0.23,0.78,0.85),
 "platform":      (0.45,0.55,0.88,0.92),
 "stone_wall_low":(0.05,0.12,0.93,0.99),
 "pillar":        (0.288,0.296,0.60,0.72),
 "rafter_under":  (0.15,0.20,0.44,0.47),
}
print("\n--- patches ---")
for k,(x0,x1,y0,y1) in patches.items():
    patch = rgb[int(h*y0):int(h*y1), int(w*x0):int(w*x1)].reshape(-1,3)
    m = (patch.mean(axis=0)*255).astype(int)
    print(f"{k:16s} #{m[0]:02X}{m[1]:02X}{m[2]:02X}   lin={np.round(px[int(h*y0):int(h*y1), int(w*x0):int(w*x1),:3].reshape(-1,3).mean(axis=0),4)}")
