import bpy, numpy as np, sys, os

paths = [
    (r"C:\Users\zkx88\.workbuddy\clipboard-images\clipboard-2026-11-12T09-13-11-371Z-5e3cddc1.jpg", "img1_front"),
    (r"D:\zkx88\微信\xwechat_files\wxid_lhj8cx303gh222_91af\temp\RWTemp\2026-11\9e20f478899dc29eb19741386f9343c8\61c22e2a1c8ec6d33ec0a2aa2b42aad1.jpg", "img3_snow"),
]

def lin2srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1/2.4) - 0.055)

for p, name in paths:
    if not os.path.exists(p):
        print("MISSING", p); continue
    img = bpy.data.images.load(p)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    px = px[::-1]  # top-down
    rgb = lin2srgb(px[:, :, :3])
    print(f"\n===== {name}  {w}x{h} =====")
    ny, nx = 9, 12
    for j in range(ny):
        row = []
        for i in range(nx):
            y0, y1 = int(h*j/ny), int(h*(j+1)/ny)
            x0, x1 = int(w*i/nx), int(w*(i+1)/nx)
            cell = rgb[y0:y1, x0:x1].reshape(-1, 3).mean(axis=0)
            r, g, b = (cell*255).astype(int)
            row.append(f"#{r:02X}{g:02X}{b:02X}")
        print(f"y{j} " + " ".join(row))
    bpy.data.images.remove(img)
