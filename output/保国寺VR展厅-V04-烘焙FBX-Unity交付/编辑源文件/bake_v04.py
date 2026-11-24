"""Bake the user's latest V04, retaining vector lettering and alpha cloth.
Cycles COMBINED appearance bake, not Unity LightingData.asset.
"""
import bpy, bmesh, math, json, time, hashlib, sys
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
ASSET=ROOT/'Assets/BaoguosiGalleryV04'
TEX=ASSET/'Textures';MODEL=ASSET/'Models'
for p in (TEX,MODEL,ROOT/'Blender备份',ROOT/'检查记录',ROOT/'预览'):p.mkdir(parents=True,exist_ok=True)
sc=bpy.context.scene;START=time.time();SOURCE=bpy.data.filepath
SOURCE_SHA=hashlib.sha256(Path(SOURCE).read_bytes()).hexdigest()
for o in list(bpy.data.objects):
 if o.type=='CAMERA':bpy.data.objects.remove(o,do_unlink=True)
for s in bpy.data.scenes:s.camera=None
for c in list(bpy.data.cameras):bpy.data.cameras.remove(c)

pref=bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type='METAL';pref.get_devices()
for d in pref.devices:d.use=d.type=='METAL'
sc.render.engine='CYCLES';sc.cycles.device='GPU';sc.cycles.samples=32
sc.cycles.use_adaptive_sampling=True;sc.cycles.adaptive_threshold=.025
sc.cycles.max_bounces=6;sc.cycles.diffuse_bounces=4;sc.cycles.transparent_max_bounces=8
sc.render.bake.use_selected_to_active=False;sc.render.bake.use_clear=True;sc.render.bake.margin=8
sc.render.bake.use_pass_direct=True;sc.render.bake.use_pass_indirect=True;sc.render.bake.use_pass_color=True
sc.render.bake.use_pass_diffuse=True;sc.render.bake.use_pass_glossy=True
sc.render.bake.use_pass_transmission=False;sc.render.bake.use_pass_emit=True
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGB';sc.render.image_settings.color_depth='8'
bpy.context.preferences.filepaths.save_version=0

ZONES=[(1,(0,0,12,7)),(2,(0,7,12,10)),(3,(0,17,12,7)),(4,(12,17,12,7)),(5,(12,7,12,10)),(6,(24,10,12,14)),(7,(24,0,12,10)),(8,(12,0,12,7))]
def zonefor(o):
 p=o
 while p:
  if p.get('zone'):return int(p['zone'])
  if '_Zone' in p.name:
   try:return int(p.name.split('_Zone')[1][:2])
   except ValueError:pass
  p=p.parent
 points=[o.matrix_world@Vector(v) for v in o.bound_box]
 x=sum(v.x for v in points)/8;y=sum(v.y for v in points)/8
 for i,(a,b,w,h) in ZONES:
  if a<=x<=a+w and b<=y<=b+h:return i
 return 1
def flat_material(m):
 return m.name.startswith(('M05_','M06_','V03_图解墨绿','V03_朱砂注记','V03_淡墨说明'))
def is_sheer(o):
 return any(s.material and s.material.name.startswith(('V04_暖宣纱','V04_纱上淡墨')) for s in o.material_slots)
def is_fine(o):
 return o.type=='FONT' or bool(o.get('文字内容')) or (o.type=='CURVE' and all(s.material and flat_material(s.material) for s in o.material_slots))
classification={}
for o in list(sc.objects):
 if o.type not in ('MESH','CURVE','FONT'):continue
 if o.hide_render:continue
 category='Sheer' if is_sheer(o) else 'Fine' if is_fine(o) else 'Photo' if o.name.startswith('Photo_') else 'Exhibits' if any(c.name.startswith(('09_','10_','12_','13_','15_','16_','17_')) for c in o.users_collection) else 'Architecture'
 classification[o.name]=(category,zonefor(o))

# Preserve pre-join Generated texture coordinates used by the corner furniture.
# UV-based PBR materials continue to use their original UVMap throughout the bake.
generated_mats=set()
for m in bpy.data.materials:
 if not m.use_nodes:continue
 for n in list(m.node_tree.nodes):
  if n.type!='TEX_COORD':continue
  links=list(n.outputs['Generated'].links)
  if links:
   attr=m.node_tree.nodes.new('ShaderNodeAttribute');attr.attribute_name='OriginalGenerated'
   for link in links:m.node_tree.links.new(attr.outputs['Vector'],link.to_socket)
   generated_mats.add(m.name)

for o in list(sc.objects):
 if o.name not in classification:continue
 if o.type in ('CURVE','FONT'):
  bpy.ops.object.select_all(action='DESELECT');o.hide_set(False);o.hide_select=False;o.select_set(True);bpy.context.view_layer.objects.active=o
  bpy.ops.object.convert(target='MESH')
 if o.data.users>1:o.data=o.data.copy()
 if classification[o.name][0] in ('Architecture','Exhibits'):
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 if any(s.material and s.material.name in generated_mats for s in o.material_slots):
  coords=[v.co.copy() for v in o.data.vertices]
  if coords:
   lo=Vector(tuple(min(v[i] for v in coords) for i in range(3)));hi=Vector(tuple(max(v[i] for v in coords) for i in range(3)))
   attr=o.data.attributes.new('OriginalGenerated','FLOAT_VECTOR','POINT')
   for item,v in zip(attr.data,coords):item.vector=tuple((v[i]-lo[i])/max(hi[i]-lo[i],.000001) for i in range(3))

runtime=bpy.data.collections.new('19_Unity烘焙运行网格');sc.collection.children.link(runtime)
def join_group(name,objects):
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.hide_viewport=False;o.hide_set(False);o.hide_select=False;o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0]
 if len(objects)>1:bpy.ops.object.join()
 o=bpy.context.object;o.name=name;mw=o.matrix_world.copy();o.parent=None;o.matrix_world=mw
 for c in list(o.users_collection):c.objects.unlink(o)
 runtime.objects.link(o);bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
 return o

tasks=[];fine=[];sheer=[]
for category in ('Architecture','Exhibits','Fine'):
 for zone in range(1,9):
  obs=[o for o in list(sc.objects) if o.name in classification and classification[o.name]==(category,zone)]
  if not obs:continue
  o=join_group(f'BGV04_{category}_Zone{zone:02}',obs);o['BGV04_Category']=category;o['BGV04_Zone']=zone
  if category=='Fine':fine.append(o);continue
  uv=o.data.uv_layers.new(name='BakeUV');o.data.uv_layers.active=uv;uv.active_render=True
  bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
  bpy.ops.uv.smart_project(angle_limit=math.radians(70),island_margin=.003,area_weight=.7,correct_aspect=True,scale_to_bounds=True)
  bpy.ops.object.mode_set(mode='OBJECT')
  tasks.append((o,f'{category}_Z{zone:02}',2048))
for o in list(sc.objects):
 if o.name not in classification:continue
 category,zone=classification[o.name]
 if category=='Photo':
  # Preserve the exact rectangular photograph UVs, not a smart-projected mosaic.
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
  uv=o.data.uv_layers.get('UVMap');o.data.uv_layers.active=uv;uv.active_render=True
  tasks.append((o,f'Photo_{len([t for t in tasks if t[1].startswith("Photo_")])+1:02}',1024))
 elif category=='Sheer':sheer.append(o)

plan={'source':SOURCE,'source_sha256':SOURCE_SHA,'samples':32,'bake_type':'Cycles Combined appearance, direct+indirect+color+glossy+emission','not_unity_native_lightmaps':True,'generated_materials_preserved':sorted(generated_mats),'tasks':[{'object':o.name,'id':key,'size':size,'polygons':len(o.data.polygons)} for o,key,size in tasks],'fine_text_meshes':[o.name for o in fine],'transparent_meshes':[o.name for o in sheer]}
(ROOT/'检查记录/烘焙计划.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'检查记录/烘焙准备检查点.blend'),compress=True)

records=[];baked=[]
for index,(o,key,size) in enumerate(tasks):
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 uv=o.data.uv_layers.get('BakeUV') or o.data.uv_layers.get('UVMap');o.data.uv_layers.active=uv;uv.active_render=True
 image=bpy.data.images.new('RAW_'+key,width=size,height=size,alpha=False,float_buffer=True)
 image.colorspace_settings.name='Linear Rec.709'
 mats=set(s.material for s in o.material_slots if s.material)
 for m in mats:
  for n in m.node_tree.nodes:n.select=False
  target=m.node_tree.nodes.get('BGV04_BAKE_TARGET') or m.node_tree.nodes.new('ShaderNodeTexImage')
  target.name='BGV04_BAKE_TARGET';target.image=image;target.select=True;m.node_tree.nodes.active=target
 t=time.time();print('BAKE_START',index+1,len(tasks),key,size,flush=True)
 bpy.ops.object.bake(type='COMBINED')
 file=TEX/(key+'.png');image.save_render(str(file),scene=sc)
 for m in mats:
  node=m.node_tree.nodes.get('BGV04_BAKE_TARGET')
  if node:m.node_tree.nodes.remove(node)
 bpy.data.images.remove(image)
 rec={'id':key,'object':o.name,'resolution':size,'seconds':round(time.time()-t,1),'file':file.name,'passes':['Color','Direct','Indirect','Glossy','Emission']}
 records.append(rec);baked.append((o,key,file));(ROOT/'检查记录/烘焙进度.json').write_text(json.dumps(records,ensure_ascii=False,indent=2));print('BAKE_DONE',json.dumps(rec,ensure_ascii=False),flush=True)

manifest=[]
def display_material(name,file,transparent=False):
 m=bpy.data.materials.new(name);m.use_nodes=True;nodes=m.node_tree.nodes;links=m.node_tree.links;bs=nodes.get('Principled BSDF')
 tx=nodes.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(str(file),check_existing=True);tx.image.colorspace_settings.name='sRGB'
 uv=nodes.new('ShaderNodeUVMap');uv.uv_map='UVMap';links.new(uv.outputs[0],tx.inputs['Vector']);links.new(tx.outputs['Color'],bs.inputs['Base Color'])
 bs.inputs['Roughness'].default_value=1;bs.inputs['Specular IOR Level'].default_value=0
 # No live lighting remains in the display scene: emission is the baked look.
 # Direct Principled->Output is also required by Blender's FBX shader wrapper.
 links.new(tx.outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=1
 output=nodes.get('Material Output')
 if transparent:
  links.new(tx.outputs['Alpha'],bs.inputs['Alpha'])
  m.surface_render_method='DITHERED'
 links.new(bs.outputs['BSDF'],output.inputs['Surface'])
 manifest.append({'name':name,'texture':file.name,'transparent':transparent,'double_sided':transparent})
 return m

for o,key,file in baked:
 if o.data.uv_layers.get('BakeUV'):
  for uv in list(o.data.uv_layers):
   if uv.name!='BakeUV':o.data.uv_layers.remove(uv)
  o.data.uv_layers[0].name='UVMap'
 o.data.materials.clear();o.data.materials.append(display_material('BGV04_'+key,file))
 for p in o.data.polygons:p.material_index=0

# Preserve vector lettering as geometry. Constant texture swatches keep stock
# Built-in and URP Unlit materials consistent, including gamma/linear projects.
flat_map={}
def swatch(old,transparent=False):
 if old.name in flat_map:return flat_map[old.name]
 nodes=old.node_tree.nodes;bs=next((n for n in nodes if n.type=='BSDF_PRINCIPLED'),None)
 color=tuple(bs.inputs['Base Color'].default_value) if bs else tuple(old.diffuse_color)
 alpha=.32 if old.name.startswith('V04_暖宣纱') else .67 if old.name.startswith('V04_纱上淡墨') else 1
 key='Swatch_'+str(len(flat_map)+1).zfill(2);file=TEX/(key+'.png')
 image=bpy.data.images.new('RAW_'+key,width=8,height=8,alpha=transparent,float_buffer=True);image.colorspace_settings.name='Linear Rec.709';image.pixels=list(color[:3]+(alpha,))*64
 sc.render.image_settings.color_mode='RGBA' if transparent else 'RGB';image.save_render(str(file),scene=sc);sc.render.image_settings.color_mode='RGB';bpy.data.images.remove(image)
 mat=display_material('BGV04_'+key,file,transparent);flat_map[old.name]=mat;return mat
for o in fine+sheer:
 for slot in o.material_slots:
  if slot.material:slot.material=swatch(slot.material,o in sheer)

# Only now remove the live lights: all Cycles bakes have finished using the
# unchanged original PBR materials and the original 55 lights for illumination.
for o in list(bpy.data.objects):
 if o.type in ('LIGHT','CAMERA'):bpy.data.objects.remove(o,do_unlink=True)
for s in bpy.data.scenes:s.camera=None
for c in list(bpy.data.cameras):bpy.data.cameras.remove(c)
for m in list(bpy.data.materials):
 if not m.name.startswith('BGV04_') and m.users==0:bpy.data.materials.remove(m)
for im in list(bpy.data.images):
 if im.users==0:bpy.data.images.remove(im)
for im in bpy.data.images:
 if im.source=='FILE':im.pack();im.filepath='//../Assets/BaoguosiGalleryV04/Textures/'+Path(im.filepath).name
sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=0
sc.render.engine='BLENDER_EEVEE';sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
sc['交付方案']='Cycles彩色静态光影烘焙；Unity使用Unlit；不依赖实时灯光；不是Unity原生Lightmap资产'
sc['烘焙采样']=32;sc['摄像机数量']=0;sc['灯光数量']=0
bpy.ops.object.select_all(action='DESELECT');bpy.context.view_layer.objects.active=None
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Blender备份/展厅V04_烘焙展示_无摄像机.blend'),compress=True)
fbx=MODEL/'Baoguosi_Gallery_V04_Baked.fbx'
bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=False,object_types={'MESH','EMPTY'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',bake_space_transform=False,use_mesh_modifiers=True,mesh_smooth_type='FACE',use_tspace=False,path_mode='RELATIVE',embed_textures=False,add_leaf_bones=False,bake_anim=False,use_custom_props=True)
(ASSET/'MaterialManifest.json').write_text(json.dumps({'materials':manifest,'texture_color_space':'sRGB appearance with AgX/exposure baked once','camera_count':0,'light_count':0,'units':'metres'},ensure_ascii=False,indent=2))
report={'source':SOURCE,'source_sha256':SOURCE_SHA,'source_unchanged':hashlib.sha256(Path(SOURCE).read_bytes()).hexdigest()==SOURCE_SHA,'bake_count':len(records),'records':records,'seconds':round(time.time()-START,1),'meshes':sum(o.type=='MESH' for o in sc.objects),'triangles':sum(sum(max(0,len(p.vertices)-2) for p in o.data.polygons) for o in sc.objects if o.type=='MESH'),'materials':len(manifest),'camera_objects':sum(o.type=='CAMERA' for o in bpy.data.objects),'camera_data':len(bpy.data.cameras),'lights':sum(o.type=='LIGHT' for o in sc.objects),'appearance_bake':True,'native_Unity_lightmap':False,'textures':len(list(TEX.glob('*.png'))),'fbx_bytes':fbx.stat().st_size}
(ROOT/'检查记录/烘焙导出完成.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('BAKE_EXPORT_COMPLETE',json.dumps(report,ensure_ascii=False),flush=True)
