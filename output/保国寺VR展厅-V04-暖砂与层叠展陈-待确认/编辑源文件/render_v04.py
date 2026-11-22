import bpy,math,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sc=bpy.context.scene
try:
 p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
 for d in p.devices:d.use=d.type=='METAL'
 sc.cycles.device='GPU'
except:sc.cycles.device='CPU'
sc.render.engine='CYCLES';sc.cycles.samples=32;sc.cycles.use_denoising=True
sc.render.resolution_x=1440;sc.render.resolution_y=900;sc.render.resolution_percentage=100
spec=[
 ('01_主展厅_墙面展陈',(18.1,12.5,1.75),(12.28,12.5,2.1),24),
 ('02_铺作工坊_壁挂与分解',(17.9,18.35,1.75),(18,23.5,2.15),19),
 ('03_构件展廊_斗栱昂',(6,18.25,1.75),(6,23.5,2.4),16),
 ('04_寻源展廊_沿革',(5.3,9.0,1.75),(11.72,12.0,2.2),20),
 ('05_整殿挑战区_墙面长幅',(30.5,14.4,1.75),(30.5,23.4,2.3),22),
 ('06_序厅_图文导览',(3.5,4.7,1.75),(9.0,6.5,2.05),23),
 ('07_静廊_挂轴与书架',(17.8,5.6,1.75),(18.9,.45,2.00),20),
 ('08_静廊_半透悬幅',(18.5,1.5,1.7),(18.5,6.5,2.6),20),
 ('09_成果尾厅_数字与传承',(29.2,2.35,1.75),(35.4,6.1,2.10),22),
]
if '--tail' in sys.argv:spec=[s for s in spec if s[0][:2] in ('02','09')]
if '--layers' in sys.argv:spec=[s for s in spec if s[0][:2] in ('01','04','05')]
if '--first' in sys.argv:spec=spec[:2]
if '--refined' in sys.argv:spec=[s for s in spec if s[0][:2] in ('02','03','04','06')]
for name,eye,target,lens in spec:
 data=bpy.data.cameras.new('TEMP_V04_PERSPECTIVE_PREVIEW');data.type='PERSP';data.lens=lens;data.clip_start=.03;data.clip_end=160
 ob=bpy.data.objects.new('TEMP_V04_PERSPECTIVE_PREVIEW',data);sc.collection.objects.link(ob);ob.location=eye;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();sc.camera=ob
 sc.render.filepath=str(ROOT/'预览'/(name+'.png'));print('PREVIEW_START',name,flush=True);bpy.ops.render.render(write_still=True)
 bpy.data.objects.remove(ob,do_unlink=True);sc.camera=None;bpy.data.cameras.remove(data)
print('PREVIEWS_FINISHED',flush=True)
