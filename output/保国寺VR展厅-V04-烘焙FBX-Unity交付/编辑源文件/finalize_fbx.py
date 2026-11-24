"""Finalize standard FBX materials, compact the hierarchy, verify resources."""
import bpy,bmesh,json,hashlib
from pathlib import Path
from bpy_extras.node_shader_utils import PrincipledBSDFWrapper
ROOT=Path(__file__).resolve().parents[1];ASSET=ROOT/'Assets/BaoguosiGalleryV04';sc=bpy.context.scene
zones={1:(0,0,12,7),2:(0,7,12,10),3:(0,17,12,7),4:(12,17,12,7),5:(12,7,12,10),6:(24,10,12,14),7:(24,0,12,10),8:(12,0,12,7)}
def tris(o):return sum(max(0,len(p.vertices)-2) for p in o.data.polygons)
text_optimization=[]
for o in sc.objects:
 if o.type!='MESH' or not o.name.startswith('BGV04_Fine_Zone'):continue
 before=tris(o);zone=int(o.name[-2:]);x,y,w,h=zones[zone];bm=bmesh.new();bm.from_mesh(o.data);bm.normal_update();remove=[]
 for f in bm.faces:
  c=o.matrix_world@f.calc_center_median();normal=o.matrix_world.to_3x3()@f.normal
  # These meshes are lettering and ink strokes mounted on the four walls.
  # Retain the exact visible front outline; remove hidden backs and thickness.
  side=min([(abs(c.x-x),(1,0,0)),(abs(c.x-x-w),(-1,0,0)),(abs(c.y-y),(0,1,0)),(abs(c.y-y-h),(0,-1,0))],key=lambda item:item[0])[1]
  if sum(normal[i]*side[i] for i in range(3))<=.001:remove.append(f)
 bmesh.ops.delete(bm,geom=remove,context='FACES');unused=[v for v in bm.verts if not v.link_faces]
 if unused:bmesh.ops.delete(bm,geom=unused,context='VERTS')
 bm.to_mesh(o.data);bm.free();o.data.update();text_optimization.append({'object':o.name,'before':before,'after':tris(o)})
manifest=json.loads((ASSET/'MaterialManifest.json').read_text())
for entry in manifest['materials']:
 m=bpy.data.materials[entry['name']];nodes=m.node_tree.nodes;links=m.node_tree.links
 bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');tx=next(n for n in nodes if n.type=='TEX_IMAGE');out=nodes.get('Material Output')
 links.new(tx.outputs['Color'],bs.inputs['Base Color']);links.new(tx.outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=1
 if entry['transparent']:links.new(tx.outputs['Alpha'],bs.inputs['Alpha']);m.surface_render_method='DITHERED'
 links.new(bs.outputs[0],out.inputs['Surface'])
 wrapper=PrincipledBSDFWrapper(m,is_readonly=True)
 assert wrapper.base_color_texture and wrapper.base_color_texture.image,'FBX cannot discover '+m.name
master=bpy.data.objects['Baoguosi_VR_Gallery_36x24m']
keep=[o for o in sc.objects if o.type=='MESH' or o.name.startswith('VR_Teleport_Zone')]
for o in keep:
 matrix=o.matrix_world.copy();o.parent=master;o.matrix_world=matrix
 if o.type=='MESH':
  if not o.data.uv_layers:o.data.uv_layers.new(name='UVMap')
  original=o.data.attributes.get('OriginalGenerated')
  if original:o.data.attributes.remove(original)
for o in list(bpy.data.objects):
 if o.type=='EMPTY' and o!=master and o not in keep:bpy.data.objects.remove(o,do_unlink=True)
for o in list(bpy.data.objects):
 if o.type in ('CAMERA','LIGHT'):bpy.data.objects.remove(o,do_unlink=True)
for scene in bpy.data.scenes:scene.camera=None
for c in list(bpy.data.cameras):bpy.data.cameras.remove(c)
for s in bpy.data.screens:
 for a in s.areas:
  if a.type=='VIEW_3D':a.spaces.active.shading.type='MATERIAL';a.spaces.active.shading.use_scene_lights=True;a.spaces.active.shading.use_scene_world=True
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Blender备份/展厅V04_烘焙展示_无摄像机.blend'),compress=True)
bpy.ops.export_scene.fbx(filepath=str(ASSET/'Models/Baoguosi_Gallery_V04_Baked.fbx'),use_selection=False,object_types={'MESH','EMPTY'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',bake_space_transform=False,use_mesh_modifiers=True,mesh_smooth_type='FACE',use_tspace=False,path_mode='RELATIVE',embed_textures=False,add_leaf_bones=False,bake_anim=False,use_custom_props=True)
report=json.loads((ROOT/'检查记录/烘焙导出完成.json').read_text());report['final_material_texture_links_verified']=len(manifest['materials']);report['empty_nodes']=sum(o.type=='EMPTY' for o in sc.objects);report['teleport_anchors']=sum(o.name.startswith('VR_Teleport_Zone') for o in sc.objects);report['final_fbx_bytes']=(ASSET/'Models/Baoguosi_Gallery_V04_Baked.fbx').stat().st_size
report['text_hidden_faces_removed']=text_optimization;report['final_triangles']=sum(tris(o) for o in sc.objects if o.type=='MESH')
(ROOT/'检查记录/烘焙导出完成.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('FINALIZE_COMPLETE',json.dumps(report,ensure_ascii=False),flush=True)
