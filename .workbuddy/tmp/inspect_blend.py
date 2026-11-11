import bpy, json, os, sys

# 跳过命令行参数
argv = sys.argv[sys.argv.index("--") + 1:]
files = [a for a in argv if not a.startswith("--")]
out_path = os.path.join(os.path.dirname(files[0]), "__never__")  # placeholder
report = []

for f in files:
    try:
        bpy.ops.wm.open_mainfile(filepath=f)
    except Exception as e:
        report.append({"file": f, "error": str(e)})
        continue

    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    tris = 0
    for o in meshes:
        me = o.data
        try:
            o.data.calc_loop_triangles()
            tris += len(me.loop_triangles)
        except Exception:
            pass

    collections = []
    for c in bpy.data.collections:
        n = len([o for o in c.all_objects if o.type == 'MESH'])
        collections.append({"name": c.name, "meshes": n})

    lights = [o.name for o in bpy.data.objects if o.type == 'LIGHT']
    cams = [o.name for o in bpy.data.objects if o.type == 'CAMERA']

    # 顶层面对象（不在任何 collection 里的）
    top_meshes = [o.name for o in meshes if o.name not in
                  {x.name for c in bpy.data.collections for x in c.all_objects}]

    # 材质探测
    mats = []
    for m in bpy.data.materials:
        has_img = False
        if m.use_nodes and m.node_tree:
            for n in m.node_tree.nodes:
                if n.type == 'TEX_IMAGE' and n.image:
                    has_img = True
                    break
        mats.append({"name": m.name, "image": has_img})

    # 是否有动画
    has_anim = len(bpy.data.actions) > 0
    frames = [s.frame_start for s in bpy.data.scenes] + [s.frame_end for s in bpy.data.scenes]

    report.append({
        "file": f,
        "ok": True,
        "objects_total": len(bpy.data.objects),
        "meshes": len(meshes),
        "triangles": tris,
        "lights": len(lights),
        "cameras": len(cams),
        "light_names": lights[:6],
        "collections": sorted(collections, key=lambda x: -x["meshes"]),
        "top_level_meshes": top_meshes[:12],
        "top_level_count": len(top_meshes),
        "materials": len(mats),
        "materials_with_image": sum(1 for m in mats if m["image"]),
        "material_sample": [m["name"] for m in mats[:8]],
        "has_actions": has_anim,
        "frames": sorted(set(frames))[:6],
        "obj_name_sample": [o.name for o in meshes[:10]],
    })

out = os.environ.get("INSPECT_OUT", "inspect.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump(report, fh, ensure_ascii=False, indent=2)
print("WROTE", out)
