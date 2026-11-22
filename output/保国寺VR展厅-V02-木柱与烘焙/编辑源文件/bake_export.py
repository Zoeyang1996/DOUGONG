"""Cycles combined bake: real direct/indirect illumination, material color and emission.
The resulting sRGB appearance atlases are used by unlit Unity materials.
This is intentionally independent of Unity LightingData.asset / lightmap slots.
"""
import bpy,math,json,time
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sc=bpy.context.scene;START=time.time()
BAKED=ROOT/'贴图_烘焙';BAKED.mkdir(exist_ok=True)
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='METAL';pref.get_devices()
for d in pref.devices:d.use=d.type=='METAL'
sc.render.engine='CYCLES';sc.cycles.device='GPU';sc.cycles.samples=48;sc.cycles.use_adaptive_sampling=True;sc.cycles.adaptive_threshold=.025
sc.cycles.max_bounces=6;sc.cycles.diffuse_bounces=4
sc.render.bake.use_selected_to_active=False;sc.render.bake.use_clear=True;sc.render.bake.margin=4
sc.render.bake.use_pass_direct=True;sc.render.bake.use_pass_indirect=True;sc.render.bake.use_pass_color=True
sc.render.bake.use_pass_diffuse=True;sc.render.bake.use_pass_glossy=True;sc.render.bake.use_pass_transmission=False;sc.render.bake.use_pass_emit=True
runtime=bpy.data.collections.new('09_烘焙运行网格_按区域');sc.collection.children.link(runtime)
zones=json.loads((ROOT/'编辑源文件'/'空间参数.json').read_text())['zones']
def zonefor(o):
 if o.get('zone'):return int(o['zone'])
 p=o.parent
 while p:
  if '_Zone' in p.name:
   try:return int(p.name.split('_Zone')[1][:2])
   except:pass
  p=p.parent
 # Shared shell pieces belong to the containing zone, avoiding geometry duplication.
 pts=[o.matrix_world@Vector(c) for c in o.bound_box];x=sum(v.x for v in pts)/8;y=sum(v.y for v in pts)/8
 for z in zones:
  a,b,w,d=z['bounds_xywh']
  if a<=x<=a+w and b<=y<=b+d:return int(z['id'])
 return 1
texts=[o for o in sc.objects if o.type=='MESH' and o.get('文字内容')]
groups={i:[] for i in range(1,9)}
for o in list(sc.objects):
 if o.type=='MESH' and o not in texts:groups[zonefor(o)].append(o)
baked=[];report=[]
for zone,objects in groups.items():
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:
  # Tiles and repeated joinery share mesh data in the editable file. Make the
  # runtime inputs independent before joining a subset of those instances.
  if o.data.users>1:o.data=o.data.copy()
  o.hide_viewport=False;o.hide_set(False);o.hide_select=False;o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();o=bpy.context.object;o.name=f'Gallery_Baked_Zone{zone:02}'
 mw=o.matrix_world.copy();o.parent=None;o.matrix_world=mw
 for c in list(o.users_collection):c.objects.unlink(o)
 runtime.objects.link(o)
 bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
 uv=o.data.uv_layers.new(name='BakeUV');o.data.uv_layers.active=uv;uv.active_render=True
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
 bpy.ops.uv.smart_project(angle_limit=math.radians(70),island_margin=.0015,area_weight=.7,correct_aspect=True,scale_to_bounds=True)
 bpy.ops.object.mode_set(mode='OBJECT')
 # 4K in the main hall and assembly challenge; 2K in the six smaller zones.
 size=4096 if zone in (5,6) else 2048
 image=bpy.data.images.new(f'RAW_LIGHT_BAKE_Z{zone:02}',width=size,height=size,alpha=False,float_buffer=True)
 image.colorspace_settings.name='Linear Rec.709'
 mats=set(s.material for s in o.material_slots if s.material)
 for m in mats:
  nodes=m.node_tree.nodes
  for n in nodes:n.select=False
  target=nodes.get('LIGHT_BAKE_TARGET') or nodes.new('ShaderNodeTexImage');target.name='LIGHT_BAKE_TARGET';target.image=image;target.select=True;nodes.active=target
 print('BAKE_START',zone,size,len(o.data.polygons),flush=True);t=time.time()
 bpy.ops.object.bake(type='COMBINED')
 # Save the scene's AgX/exposure look once into an sRGB PNG. The unlit display
 # scene uses Standard/exposure 0, preventing a second Blender tone-map pass.
 file=BAKED/f'Baked_Zone{zone:02}.png';sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGB';sc.render.image_settings.color_depth='8'
 image.save_render(str(file),scene=sc)
 for m in mats:
  n=m.node_tree.nodes.get('LIGHT_BAKE_TARGET')
  if n:m.node_tree.nodes.remove(n)
 bpy.data.images.remove(image)
 baked.append((o,zone,file))
 rec={'zone':zone,'resolution':[size,size],'polygons':len(o.data.polygons),'seconds':round(time.time()-t,1),'file':file.name,'passes':['Diffuse Color','Direct','Indirect','Glossy','Emission'],'glossy':True,'margin_px':4,'uv_island_margin':.0015}
 report.append(rec);(ROOT/'检查记录'/'烘焙进度.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('BAKE_DONE',rec,flush=True)

# Only replace surface shaders after every zone is baked: prevents already-baked
# surfaces from emitting their illumination into the subsequent bake.
def bakedmat(zone,file):
 m=bpy.data.materials.new(f'BG_Baked_Zone{zone:02}');m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links
 bs=n.get('Principled BSDF');bs.inputs['Roughness'].default_value=1;bs.inputs['Specular IOR Level'].default_value=0
 tx=n.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(str(file),check_existing=True);tx.image.colorspace_settings.name='sRGB'
 uv=n.new('ShaderNodeUVMap');uv.uv_map='UVMap';l.new(uv.outputs[0],tx.inputs['Vector']);l.new(tx.outputs['Color'],bs.inputs['Base Color']);l.new(tx.outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=1
 return m
for o,zone,file in baked:
 # FBX and Unity use UV0. Delete the old repeating material UV after baking.
 for uv in list(o.data.uv_layers):
  if uv.name!='BakeUV':o.data.uv_layers.remove(uv)
 o.data.uv_layers[0].name='UVMap';o.data.materials.clear();o.data.materials.append(bakedmat(zone,file))
 for p in o.data.polygons:p.material_index=0
for o in texts:
 old=o.data.materials[0];bsold=old.node_tree.nodes.get('Principled BSDF');color=bsold.inputs['Base Color'].default_value[:]
 textmat='BG_Bronze' if old.name.startswith('M05') else 'BG_Ink'
 m=bpy.data.materials.get(textmat)
 if not m:
  m=bpy.data.materials.new(textmat);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=color;bs.inputs['Emission Color'].default_value=color;bs.inputs['Emission Strength'].default_value=1;bs.inputs['Specular IOR Level'].default_value=0
 o.data.materials.clear();o.data.materials.append(m)
for o in list(bpy.data.objects):
 if o.type in ('LIGHT','CAMERA'):bpy.data.objects.remove(o,do_unlink=True)
for s in bpy.data.scenes:s.camera=None
for c in list(bpy.data.cameras):bpy.data.cameras.remove(c)
for m in list(bpy.data.materials):
 if not m.name.startswith('BG_'):bpy.data.materials.remove(m,do_unlink=True)
for i in list(bpy.data.images):
 if i.users==0:bpy.data.images.remove(i)
for im in bpy.data.images:
 if im.source=='FILE':im.pack();im.filepath='//../贴图_烘焙/'+Path(im.filepath).name
sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=0
sc.render.engine='BLENDER_EEVEE';sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
sc['烘焙方案']='Cycles Combined彩色静态光影贴图；Unity使用Unlit；不是Unity LightingData.asset'
sc['烘焙采样']=48;sc['合并说明']='按8个展区合并运行网格；墙面文字保持独立；编辑请用PBR源文件'
sc.render.filepath='//../预览/'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'模型'/'展厅V02_烘焙展示_无摄像机.blend'))
bpy.ops.export_scene.fbx(filepath=str(ROOT/'模型'/'Baoguosi_Gallery_V02_Baked.fbx'),use_selection=False,object_types={'MESH','EMPTY'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',bake_space_transform=False,use_mesh_modifiers=True,mesh_smooth_type='FACE',use_tspace=False,path_mode='RELATIVE',embed_textures=False,add_leaf_bones=False,bake_anim=False)
# Independent no-light render demonstrates that the illumination lives in the textures.
data=bpy.data.cameras.new('TEMP_BAKED_CHECK');data.lens=18;data.clip_start=.03
cam=bpy.data.objects.new('TEMP_BAKED_CHECK',data);sc.collection.objects.link(cam);cam.location=(18.1,8.1,1.75);cam.rotation_euler=(Vector((18.1,14.7,3.15))-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam
sc.render.resolution_x=1440;sc.render.resolution_y=900;sc.render.resolution_percentage=100;sc.render.filepath=str(ROOT/'预览'/'04_关闭灯光后的烘焙显示验证.png');bpy.ops.render.render(write_still=True)
bpy.data.objects.remove(cam,do_unlink=True);sc.camera=None;bpy.data.cameras.remove(data)
report={'atlases':report,'seconds_total':round(time.time()-START,1),'mesh_count':sum(o.type=='MESH' for o in sc.objects),'camera_count':len(bpy.data.cameras),'light_objects_in_baked_scene':sum(o.type=='LIGHT' for o in sc.objects),'native_Unity_lightmap':False,'appearance_bake':True}
(ROOT/'检查记录'/'烘焙交付检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('BAKE_EXPORT_COMPLETE',report,flush=True)
