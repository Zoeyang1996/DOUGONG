import bpy,bmesh,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sc=bpy.context.scene
source=json.loads((ROOT/'检查记录/当前V04源文件清单.json').read_text())
cleats=[o['bounds'] for o in source['objects'] if o['type']=='MESH' and o['name'].startswith('WallMountCleat')]
removed=0
for o in sc.objects:
 if o.type=='MESH' and o.name.startswith('BGV04_Exhibits_'):
  bm=bmesh.new();bm.from_mesh(o.data);delete=[]
  for f in bm.faces:
   points=[o.matrix_world@v.co for v in f.verts]
   if any(all(all(lo[i]-0.00002<=p[i]<=hi[i]+0.00002 for i in range(3)) for p in points) for lo,hi in cleats):delete.append(f)
  removed+=len(delete)
  if delete:bmesh.ops.delete(bm,geom=delete,context='FACES')
  unused=[v for v in bm.verts if not v.link_faces]
  if unused:bmesh.ops.delete(bm,geom=unused,context='VERTS')
  bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
for im in bpy.data.images:
 if im.source=='FILE':
  path=str(ROOT/'Assets/BaoguosiGalleryV04/Textures'/Path(im.filepath).name)
  if im.packed_file:im.unpack(method='REMOVE')
  im.filepath=path;im.reload();im.pack();im.filepath='//../Assets/BaoguosiGalleryV04/Textures/'+Path(path).name
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath,compress=True)
bpy.ops.export_scene.fbx(filepath=str(ROOT/'Assets/BaoguosiGalleryV04/Models/Baoguosi_Gallery_V04_Baked.fbx'),use_selection=False,object_types={'MESH','EMPTY'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',bake_space_transform=False,use_mesh_modifiers=True,mesh_smooth_type='FACE',use_tspace=False,path_mode='RELATIVE',embed_textures=False,add_leaf_bones=False,bake_anim=False,use_custom_props=True)
(ROOT/'检查记录/隐蔽安装条清理.json').write_text(json.dumps({'source_mount_cleats':len(cleats),'faces_removed':removed,'reason':'删除嵌入隔墙的背面安装条，消除墙面交叠产生的黑条；保留正面展板与木框。'},ensure_ascii=False,indent=2))
print('ATLAS_REFRESH_COMPLETE',removed,flush=True)
