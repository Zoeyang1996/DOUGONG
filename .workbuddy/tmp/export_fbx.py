import bpy, json, os, sys, time

# ---------------------------------------------------------------
# 保国寺斗拱资产 · 批量导出 FBX（v2：支持多场景拆分 + 稳健选择）
# 用法: blender -b --python export_fbx.py -- <manifest.json> <out_dir> <report.json>
# ---------------------------------------------------------------

argv = sys.argv[sys.argv.index("--") + 1:]
manifest_path, out_dir, report_path = argv[0], argv[1], argv[2]

with open(manifest_path, encoding="utf-8") as f:
    manifest = json.load(f)

os.makedirs(out_dir, exist_ok=True)

EXCLUDE_SET_KEYS = ["摄影棚", "参考图", "灯光相机", "背景", "展台", "地台"]
EXCLUDE_OBJ_KEYS = [
    "摄影棚", "背景板", "背景", "地台", "展台", "相机", "灯光",
    "地面", "地板", "底板", "大地",
    "floor", "Floor", "FLOOR", "Ground", "ground", "Grass",
]


def unhide_all(lc):
    lc.exclude = False
    lc.hide_viewport = False
    for ch in lc.children:
        unhide_all(ch)


def is_excluded_obj(o):
    if any(k in o.name for k in EXCLUDE_OBJ_KEYS):
        return True
    for c in o.users_collection:
        if any(k in c.name for k in EXCLUDE_SET_KEYS):
            return True
    return False


report = []

for item in manifest:
    src, name = item["src"], item["name"]
    dst = os.path.join(out_dir, name + ".fbx")
    t0 = time.time()
    rec = {"src": src, "name": name, "out": dst, "ok": False}

    try:
        bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
    except Exception as e:
        rec["error"] = "open failed: %s" % e
        report.append(rec)
        continue

    # --- 多场景：只保留目标场景 ---
    if item.get("scene"):
        tgt = bpy.data.scenes.get(item["scene"])
        if tgt is None:
            rec["error"] = "scene not found: %s" % item["scene"]
            report.append(rec)
            continue
        for s in list(bpy.data.scenes):
            if s is not tgt:
                bpy.data.scenes.remove(s)
        try:
            bpy.context.window.scene = tgt
        except Exception:
            pass

    # --- 退出编辑模式，全部可见 ---
    try:
        if bpy.context.object and bpy.context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
    except Exception:
        pass

    for sc in bpy.data.scenes:
        for vl in sc.view_layers:
            unhide_all(vl.layer_collection)
    for c in bpy.data.collections:
        c.hide_viewport = False
        c.hide_render = False
    for o in bpy.data.objects:
        try:
            o.hide_set(False)
        except Exception:
            pass
        o.hide_viewport = False
        o.hide_render = False

    # --- 剔除摄影棚/参考图 ---
    removed = []
    for o in list(bpy.data.objects):
        if o.type in {"MESH", "EMPTY", "LIGHT", "CAMERA"} and is_excluded_obj(o):
            removed.append(o.name)
            bpy.data.objects.remove(o, do_unlink=True)

    # --- 选择所有 MESH + EMPTY 祖先 ---
    vl = bpy.context.view_layer
    for o in list(vl.objects):
        try:
            o.select_set(False)
        except Exception:
            pass

    meshes = [o for o in bpy.data.objects if o.type == "MESH" and o.name in vl.objects]
    tris = 0
    sel = []
    for o in meshes:
        try:
            o.select_set(True)
            sel.append(o)
        except Exception:
            continue
        p = o.parent
        while p:
            if p.type == "EMPTY" and p.name in vl.objects:
                try:
                    p.select_set(True)
                except Exception:
                    pass
            p = p.parent
        try:
            o.data.calc_loop_triangles()
            tris += len(o.data.loop_triangles)
        except Exception:
            pass

    if not sel:
        rec["error"] = "no mesh selectable"
        report.append(rec)
        continue

    vl.objects.active = sel[0]
    rec["objects_total"] = len(bpy.data.objects)
    rec["mesh_total"] = len(bpy.data.objects and [o for o in bpy.data.objects if o.type == "MESH"])

    kw = dict(
        filepath=dst,
        check_existing=False,
        use_selection=True,
        use_visible=False,
        use_active_collection=False,
        object_types={"MESH", "EMPTY"},
        apply_scale_options="FBX_SCALE_ALL",
        apply_unit_scale=True,
        use_space_transform=True,
        bake_space_transform=False,
        axis_forward="-Z",
        axis_up="Y",
        use_mesh_modifiers=True,
        use_mesh_modifiers_render=False,
        mesh_smooth_type="FACE",
        use_custom_props=True,
        add_leaf_bones=False,
        bake_anim=False,
        path_mode="COPY",
        embed_textures=True,
        use_triangles=False,
        use_subsurf=False,
        use_metadata=True,
        use_tspace=False,
    )
    try:
        bpy.ops.export_scene.fbx(**kw)
        rec["ok"] = True
    except TypeError as e:
        rec["error"] = "TypeError: %s" % e
        try:
            bpy.ops.export_scene.fbx(
                filepath=dst, use_selection=True, object_types={"MESH", "EMPTY"},
                apply_scale_options="FBX_SCALE_ALL", use_mesh_modifiers=True,
                add_leaf_bones=False, bake_anim=False, path_mode="COPY",
                axis_forward="-Z", axis_up="Y")
            rec["ok"] = True
            rec["note"] = "fallback args"
        except Exception as e2:
            rec["error"] += " | fallback: %s" % e2
    except Exception as e:
        rec["error"] = "%s" % e

    rec.update({
        "meshes": len(sel),
        "triangles": tris,
        "removed": removed[:10],
        "removed_count": len(removed),
        "size_mb": round(os.path.getsize(dst) / 1048576, 2) if os.path.exists(dst) else 0,
        "sec": round(time.time() - t0, 1),
    })
    report.append(rec)
    print("DONE %-38s mesh=%-5d tri=%-7d %6.2fMB %5.1fs %s" % (
        name, len(sel), tris, rec["size_mb"], rec["sec"], "" if rec["ok"] else "FAIL:" + str(rec.get("error"))))

with open(report_path, "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
print("REPORT", report_path)
