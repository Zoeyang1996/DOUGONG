"""Preserve the original bronze secondary headings and re-export final delivery."""
import bpy,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sc=bpy.context.scene
def rgb(h):
 a=[int(h[i:i+2],16)/255 for i in (1,3,5)]
 return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in a)+(1,)
m=bpy.data.materials.get('BG_Bronze')
if not m:
 m=bpy.data.materials.new('BG_Bronze');m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=rgb('#8a714c');bs.inputs['Emission Color'].default_value=rgb('#8a714c');bs.inputs['Emission Strength'].default_value=1;bs.inputs['Specular IOR Level'].default_value=0
for o in sc.objects:
 if o.type=='MESH' and o.name.startswith('Sub') and o.get('文字内容'):o.data.materials.clear();o.data.materials.append(m)
# Packed source photographs can remain as zero-user images after Blender purges
# their old source materials on reopen. Keep only the eight referenced atlases.
for image in list(bpy.data.images):
 if image.source=='FILE' and not image.name.startswith('Baked_Zone'):bpy.data.images.remove(image,do_unlink=True)
eye=Vector((18.1,8.1,1.75));target=Vector((18.1,14.7,3.15));rot=(target-eye).to_track_quat('-Z','Y')
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   space=area.spaces.active;space.lens=18;space.clip_start=.03;space.clip_end=200
   region=space.region_3d;region.view_perspective='PERSP';region.view_rotation=rot;region.view_distance=6.75;region.view_location=eye+rot@Vector((0,0,-6.75))
   space.shading.type='MATERIAL';space.shading.use_scene_lights=True;space.shading.use_scene_world=True
assert not [o for o in bpy.data.objects if o.type in ('LIGHT','CAMERA')]
assert len(bpy.data.cameras)==0
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'模型/展厅V02_烘焙展示_无摄像机.blend'))
bpy.ops.export_scene.fbx(filepath=str(ROOT/'模型/Baoguosi_Gallery_V02_Baked.fbx'),use_selection=False,object_types={'MESH','EMPTY'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',bake_space_transform=False,use_mesh_modifiers=True,mesh_smooth_type='FACE',use_tspace=False,path_mode='RELATIVE',embed_textures=False,add_leaf_bones=False,bake_anim=False)
data=bpy.data.cameras.new('TEMP_FINAL_CHECK');data.lens=18;data.clip_start=.03
cam=bpy.data.objects.new('TEMP_FINAL_CHECK',data);sc.collection.objects.link(cam);cam.location=(18.1,8.1,1.75);cam.rotation_euler=(Vector((18.1,14.7,3.15))-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam
sc.render.resolution_x=1440;sc.render.resolution_y=900;sc.render.resolution_percentage=100
sc.render.filepath=str(ROOT/'预览/04_关闭灯光后的烘焙显示验证.png');bpy.ops.render.render(write_still=True)
bpy.data.objects.remove(cam,do_unlink=True);sc.camera=None;bpy.data.cameras.remove(data)
print('FINAL_DISPLAY_EXPORT_COMPLETE',flush=True)
