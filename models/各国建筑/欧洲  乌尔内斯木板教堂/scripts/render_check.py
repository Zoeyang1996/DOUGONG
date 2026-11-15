# -*- coding: utf-8 -*-
"""Re-render cameras from the saved .blend without rebuilding geometry."""
import bpy, sys, os

ROOT = r"D:/技能大赛/各国建筑/乌尔内斯木板教堂"
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "Urnes_Stave_Church.blend"))
sc = bpy.context.scene

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
views = args[0].split(",") if args else ["front", "hero"]
samples = int(args[1]) if len(args) > 1 else 40
scale = int(args[2]) if len(args) > 2 else 100
tag = args[3] if len(args) > 3 else "chk"

SIZES = {"front": (1000, 1330), "hero": (1400, 1050),
         "side": (1200, 900), "detail": (900, 1000)}

sc.cycles.samples = samples
sc.render.resolution_percentage = scale
for v in views:
    cam = bpy.data.objects.get({"front": "CAM_01_West_Front",
                                "hero": "CAM_02_Three_Quarter",
                                "side": "CAM_03_South_East",
                                "detail": "CAM_04_Tower_Detail"}[v])
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = SIZES[v]
    sc.render.filepath = os.path.join(ROOT, "renders", "chk_%s_%s.png" % (tag, v))
    bpy.ops.render.render(write_still=True)
    print("CHK rendered", v)
