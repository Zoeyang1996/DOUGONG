import bpy,math,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sc=bpy.context.scene
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='METAL';pref.get_devices()
for d in pref.devices:d.use=d.type=='METAL'
sc.cycles.device='GPU';sc.cycles.samples=32;sc.cycles.use_denoising=True
sc.render.resolution_x=1440;sc.render.resolution_y=900;sc.render.resolution_percentage=100
spec=[('01_木构主展厅',(18.1,8.1,1.75),(18.1,14.7,3.15),18),('02_斗拱铺作搭建区',(13.6,18.1,1.75),(18.5,22.6,2.7),20),('03_大殿拼搭挑战区',(25.3,11.35,1.75),(31.4,18.8,2.8),20)]
if '--main' in sys.argv:spec=spec[:1]
for name,eye,target,lens in spec:
 data=bpy.data.cameras.new('TEMP_PREVIEW');data.lens=lens;data.clip_start=.03
 ob=bpy.data.objects.new('TEMP_PREVIEW',data);sc.collection.objects.link(ob);ob.location=eye;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();sc.camera=ob
 sc.render.filepath=str(ROOT/'预览'/(name+'.png'));print('RENDER',name,flush=True);bpy.ops.render.render(write_still=True)
 bpy.data.objects.remove(ob,do_unlink=True);sc.camera=None;bpy.data.cameras.remove(data)
print('PREVIEWS_COMPLETE',flush=True)
