import bpy,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sc=bpy.context.scene
assert not [o for o in sc.objects if o.type in ('CAMERA','LIGHT')]
assert len(bpy.data.cameras)==0
sc.render.engine='BLENDER_EEVEE';sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
sc.render.resolution_x=1440;sc.render.resolution_y=900;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGB'
views=[('01_主展墙_关闭全部灯光验证',(18.1,12.5,1.75),(12.28,12.5,2.1),24),('02_斗拱工坊_关闭全部灯光验证',(17.9,18.35,1.75),(18,23.5,2.15),19),('03_半透悬幅_关闭全部灯光验证',(18.5,1.5,1.7),(18.5,6.5,2.6),20),('04_序厅与动线_关闭全部灯光验证',(3.5,4.7,1.75),(9,6.5,2.05),23)]
import sys
if '--quiet' in sys.argv:views=[v for v in views if v[0].startswith('03')]
for name,eye,target,lens in views:
 data=bpy.data.cameras.new('TEMP_BAKED_CHECK');data.type='PERSP';data.lens=lens;data.clip_start=.03;data.clip_end=160
 camera=bpy.data.objects.new('TEMP_BAKED_CHECK',data);sc.collection.objects.link(camera);camera.location=eye;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();sc.camera=camera
 sc.render.filepath=str(ROOT/'预览'/(name+'.png'));print('BAKED_PREVIEW_START',name,flush=True);bpy.ops.render.render(write_still=True)
 bpy.data.objects.remove(camera,do_unlink=True);sc.camera=None;bpy.data.cameras.remove(data)
assert not bpy.data.cameras
print('BAKED_PREVIEWS_DONE',flush=True)
