import bpy
from mathutils import Vector
ob = bpy.data.objects.get("屋面（瓦面+望板）")
me = ob.data
print("verts", len(me.vertices), "polys", len(me.polygons))
groups = {}
for p in me.polygons:
    n = p.normal
    if abs(n.x) > 0.85 and abs(n.y) < 0.3:
        c = p.center
        key = (round(c.x, 1), p.material_index)
        groups.setdefault(key, []).append((c.y, c.z, p.area))
for key in sorted(groups):
    lst = groups[key]
    ys = [a for a, b, c in lst]
    zs = [b for a, b, c in lst]
    ar = sum(c for a, b, c in lst)
    print("x=%7.2f mat=%d n=%4d  y[%7.2f,%7.2f] z[%7.2f,%7.2f] area=%8.2f" %
          (key[0], key[1], len(lst), min(ys), max(ys), min(zs), max(zs), ar))
