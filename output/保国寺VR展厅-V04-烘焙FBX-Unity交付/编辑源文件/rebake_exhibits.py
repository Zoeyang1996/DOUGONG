"""Correct inward polygon normals that Cycles' two-sided render had hidden."""
import bpy,bmesh,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sc=bpy.context.scene;TEX=ROOT/'Assets/BaoguosiGalleryV04/Textures'
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='METAL';pref.get_devices()
for d in pref.devices:d.use=d.type=='METAL'
sc.render.engine='CYCLES';sc.cycles.device='GPU';sc.cycles.samples=32;sc.render.bake.use_clear=True
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGB';sc.render.image_settings.color_depth='8'
objects=[o for o in sc.objects if o.type=='MESH' and o.name.startswith('BGV04_Exhibits_')]
for o in objects:
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
records=[]
for o in sorted(objects,key=lambda o:o.name):
 key='Exhibits_Z'+o.name[-2:];bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 uv=o.data.uv_layers['BakeUV'];o.data.uv_layers.active=uv;uv.active_render=True
 image=bpy.data.images.new('FIX_'+key,width=2048,height=2048,alpha=False,float_buffer=True);image.colorspace_settings.name='Linear Rec.709'
 mats=set(s.material for s in o.material_slots if s.material)
 for m in mats:
  for n in m.node_tree.nodes:n.select=False
  n=m.node_tree.nodes.new('ShaderNodeTexImage');n.name='CORRECTED_NORMALS_BAKE';n.image=image;n.select=True;m.node_tree.nodes.active=n
 start=time.time();print('NORMAL_BAKE_START',key,flush=True);bpy.ops.object.bake(type='COMBINED');image.save_render(str(TEX/(key+'.png')),scene=sc)
 for m in mats:m.node_tree.nodes.remove(m.node_tree.nodes['CORRECTED_NORMALS_BAKE'])
 bpy.data.images.remove(image);records.append({'atlas':key,'seconds':round(time.time()-start,1),'outward_normals':True});(ROOT/'检查记录/展陈朝向修正烘焙.json').write_text(json.dumps(records,ensure_ascii=False,indent=2));print('NORMAL_BAKE_DONE',records[-1],flush=True)
print('NORMAL_REBAKE_FINISHED',flush=True)
