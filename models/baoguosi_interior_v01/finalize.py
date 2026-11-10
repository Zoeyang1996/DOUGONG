import bpy
from pathlib import Path
O=Path(__file__).resolve().parent;S=bpy.context.scene
for o in list(S.objects):
 if o.name.startswith('蜀柱柱头_内转丁头栱'):bpy.data.objects.remove(o,do_unlink=True)
 elif o.name.startswith('照壁上补间_内转丁头栱'):o.location.z-=.48
S.camera=bpy.data.objects['总览_东南向'];S.render.filepath=str(O/'07_修正后内部总览.png');bpy.ops.render.render(write_still=True)
S.camera=bpy.data.objects['东侧正投影'];S.render.filepath=str(O/'09_修正后侧视.png');bpy.ops.render.render(write_still=True)
S.camera=bpy.data.objects['总览_东南向'];bpy.ops.wm.save_as_mainfile(filepath=str(O/'保国寺大殿_内部结构_v01.blend'))
