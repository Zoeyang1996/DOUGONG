import bpy, json, os, sys
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
items_path, report_path = argv[0], argv[1]

with open(items_path, encoding="utf-8") as f:
    items = json.load(f)

report = []
for it in items:
    p = it["path"]
    name = os.path.basename(p)
    rec = {"name": name, "path": p, "ok": False}
    if not os.path.exists(p):
        rec["error"] = "missing"
        report.append(rec)
        continue

    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        bpy.ops.import_scene.fbx(filepath=p)
    except Exception as e:
        rec["error"] = str(e)
        report.append(rec)
        continue

    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    tris = 0
    mn = Vector((1e9, 1e9, 1e9))
    mx = Vector((-1e9, -1e9, -1e9))
    for o in meshes:
        try:
            o.data.calc_loop_triangles()
            tris += len(o.data.loop_triangles)
        except Exception:
            pass
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            for i in range(3):
                mn[i] = min(mn[i], w[i])
                mx[i] = max(mx[i], w[i])

    size = [round(mx[i] - mn[i], 3) for i in range(3)] if meshes else [0, 0, 0]
    mats = len(bpy.data.materials)
    # 前 6 个对象名（验证中文名是否保留）
    names = [o.name for o in meshes[:6]]
    rec.update({
        "ok": len(meshes) > 0,
        "meshes": len(meshes),
        "triangles": tris,
        "materials": mats,
        "bbox_m": size,
        "sample_names": names,
        "size_mb": round(os.path.getsize(p) / 1048576, 2),
    })
    report.append(rec)
    print("VERIFY %-34s mesh=%-5d tri=%-7d bbox=%s" % (name, len(meshes), tris, size))

with open(report_path, "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
print("REPORT", report_path)
