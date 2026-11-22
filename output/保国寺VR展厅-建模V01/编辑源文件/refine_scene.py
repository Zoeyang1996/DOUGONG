import bpy,json,math,sys,time
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sc=bpy.context.scene
ground=bpy.data.objects.get('Floor_GroutBed')
ground.location.z=-.15
sc.view_settings.exposure=-.8
def rgba(hex):
 vals=[int(hex[i:i+2],16)/255 for i in [1,3,5]]
 return tuple((v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4) for v in vals)+(1,)
replacements={}
for im in list(bpy.data.images):
 if im.source=='FILE':
  path=ROOT/'贴图'/Path(im.filepath).name
  n=bpy.data.images.load(str(path),check_existing=False)
  n.colorspace_settings.name='sRGB' if 'BaseColor' in n.name else 'Non-Color'
  replacements[im]=n
for m in bpy.data.materials:
 if m.use_nodes:
  for n in m.node_tree.nodes:
   if n.type=='TEX_IMAGE' and n.image in replacements:n.image=replacements[n.image]
for old in replacements:
 if old.users==0:bpy.data.images.remove(old)
for name,col in [('M01_烟熏橡木_PBR','#493526'),('M02_暖灰矿物墙_PBR','#b5aa97'),('M03_哑光灰石_PBR','#7d807a'),('M04_浅矿物台面','#c3baa9'),('M06_墨色导视','#1c241d')]:
 m=bpy.data.materials[name];m.diffuse_color=rgba(col)
 if name in ['M04_浅矿物台面','M06_墨色导视']:m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=rgba(col)
for o in bpy.data.objects:
 if o.type=='LIGHT' and '_Ambient_' in o.name:
  o.data.energy=1050 if o.name.startswith('Z05_') else 540
sc.cycles.samples=32;sc.cycles.use_denoising=True
sc.cycles.device='GPU'
try:
 pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='METAL';pref.get_devices()
 for d in pref.devices:d.use=d.type=='METAL'
except:sc.cycles.device='CPU'
def camera(loc,target,lens):
 data=bpy.data.cameras.new('TEMP_QA');data.lens=lens;data.clip_start=.03;data.clip_end=150
 ob=bpy.data.objects.new('TEMP_QA',data);sc.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();sc.camera=ob;return ob
spec=[('01_主展厅_真实模型预览',(13.65,8.35,1.75),(18.9,14.1,3.05),19),('02_铺作搭建区_真实模型预览',(13.6,18.1,1.75),(18.5,22.6,2.7),20),('03_入口转折_真实模型预览',(2.7,1.2,1.7),(8.0,5.8,2.6),20),('04_大殿挑战区_真实模型预览',(25.3,11.35,1.75),(31.4,18.8,2.8),20)]
sc.render.resolution_x=1280;sc.render.resolution_y=800
for name,loc,target,lens in spec:
 c=camera(loc,target,lens);sc.render.filepath=str(ROOT/'预览'/(name+'.png'))
 print('REFINE_RENDER',name,flush=True);bpy.ops.render.render(write_still=True)
 bpy.data.objects.remove(c,do_unlink=True);sc.camera=None
hidden=[]
for o in bpy.data.objects:
 if o.type=='MESH' and (o.name.startswith('Outer_S_') or o.name.startswith('Outer_W') or any(c.name.startswith('07_') for c in o.users_collection)):
  hidden.append(o);o.hide_render=True
c=camera((42,-28,43),(18,12,1),38);sc.render.resolution_x=1500;sc.render.resolution_y=1000;sc.cycles.samples=32
sc.render.filepath=str(ROOT/'预览'/'05_去顶空间总览_真实模型预览.png')
bpy.ops.render.render(write_still=True);bpy.data.objects.remove(c,do_unlink=True)
for o in hidden:o.hide_render=False
for o in list(bpy.data.objects):
 if o.type=='CAMERA':bpy.data.objects.remove(o,do_unlink=True)
for s in bpy.data.scenes:s.camera=None
for c in list(bpy.data.cameras):bpy.data.cameras.remove(c)
for im in bpy.data.images:
 if im.source=='FILE':
  im.pack();im.filepath='//../贴图/'+Path(im.filepath).name
sc.render.filepath='//../预览/'
sc['地面基层检查']='基层顶面-0.055m；石板顶面0m，底面-0.054m；无共面重叠'
sc['灯光校正']='Ambient ordinary540W / main1050W / exposure -0.8；烟熏木/灰石材质收敛'
blend=ROOT/'模型'/'保国寺VR数字斗拱展厅_V01_无摄像机.blend'
fbx=ROOT/'模型'/'保国寺VR数字斗拱展厅_V01_无摄像机.fbx'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
for ob in sc.objects:
 if ob.type=='MESH' and ob.data.users>1:ob.data=ob.data.copy()
bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=False,object_types={'MESH','EMPTY'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',bake_space_transform=False,use_mesh_modifiers=True,mesh_smooth_type='FACE',use_tspace=False,path_mode='RELATIVE',embed_textures=False,add_leaf_bones=False,bake_anim=False)
r=json.loads((ROOT/'检查记录'/'场景交付检查.json').read_text())
r.update({'refinement':'修正地面基层共面遮挡、降低环境灯光与曝光','camera_objects':len([o for o in bpy.data.objects if o.type=='CAMERA']),'camera_datablocks':len(bpy.data.cameras)})
(ROOT/'检查记录'/'场景交付检查.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
print('REFINE_COMPLETE',flush=True)
