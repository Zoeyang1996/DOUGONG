import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
def inspect():
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
 points=[o.matrix_world@Vector(v) for o in meshes for v in o.bound_box]
 return {'mesh_count':len(meshes),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes),'camera_objects':sum(o.type=='CAMERA' for o in bpy.data.objects),'camera_datablocks':len(bpy.data.cameras),'light_objects':sum(o.type=='LIGHT' for o in bpy.context.scene.objects),'bounds_m':[[round(min(v[i] for v in points),4),round(max(v[i] for v in points),4)] for i in range(3)],'empty_meshes':[o.name for o in meshes if len(o.data.polygons)==0],'anchors':[o.name for o in bpy.context.scene.objects if o.name.endswith('_ExhibitAnchor_EMPTY')],'teleports':[o.name for o in bpy.context.scene.objects if o.name.startswith('VR_Teleport_')],'external_missing':[i.filepath for i in bpy.data.images if i.source=='FILE' and not i.packed_file and not Path(bpy.path.abspath(i.filepath)).is_file()]}
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'模型/展厅V02_可编辑PBR_无摄像机.blend'),load_ui=False)
pbr=inspect();pbr['shaft_count']=sum(o.name.startswith('TimberColumn_') and o.name.endswith('_Shaft') for o in bpy.data.objects);pbr['packed_real_maps']=sum(i.source=='FILE' and bool(i.packed_file) for i in bpy.data.images)
pbr['column_groups']=sum(o.name.startswith('ColumnGroup_Zone') for o in bpy.data.objects)
assert pbr['column_groups']==24
for entry in json.loads((ROOT/'检查记录/新增木柱与动线.json').read_text())['columns']:
 shaft=bpy.data.objects[entry['id']+'_Shaft']
 assert all(abs(shaft.matrix_world.translation[i]-entry['xy_m'][i])<1e-4 for i in (0,1))
assert pbr['shaft_count']==24 and pbr['packed_real_maps']==9 and pbr['camera_objects']==pbr['camera_datablocks']==0 and not pbr['external_missing']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'模型/展厅V02_烘焙展示_无摄像机.blend'),load_ui=False)
baked=inspect();baked['runtime_zones']=sum(o.name.startswith('Gallery_Baked_Zone') for o in bpy.data.objects);baked['packed_atlases']=sum(i.source=='FILE' and bool(i.packed_file) for i in bpy.data.images)
baked['UV_bounds']={}
for o in bpy.context.scene.objects:
 if o.type=='MESH' and o.name.startswith('Gallery_Baked_Zone'):
  assert len(o.data.uv_layers)==1
  coords=[c.uv[:] for c in o.data.uv_layers[0].data];lo=[min(p[i] for p in coords) for i in (0,1)];hi=[max(p[i] for p in coords) for i in (0,1)]
  baked['UV_bounds'][o.name]={'min':lo,'max':hi};assert min(lo)>-.0001 and max(hi)<1.0001
assert baked['runtime_zones']==8 and baked['packed_atlases']==8 and baked['camera_objects']==baked['camera_datablocks']==baked['light_objects']==0 and not baked['external_missing']
assert len(baked['anchors'])==8 and len(baked['teleports'])==8
assert pbr['triangles']==baked['triangles']
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT/'模型/Baoguosi_Gallery_V02_Baked.fbx'),use_anim=False)
fbx=inspect();fbx['baked_materials']=[m.name for m in bpy.data.materials if m.name.startswith('BG_')]
assert fbx['mesh_count']==baked['mesh_count'] and fbx['camera_objects']==fbx['light_objects']==0 and not fbx['external_missing'] and not fbx['empty_meshes']
for i in range(3):
 for j in range(2):assert abs(fbx['bounds_m'][i][j]-baked['bounds_m'][i][j])<.01
assert all(any(m.startswith(f'BG_Baked_Zone{i:02}') for m in fbx['baked_materials']) for i in range(1,9))
report={'passed':True,'PBR_reopened':pbr,'baked_reopened':baked,'FBX_reimported':fbx,'Unity_runtime_tested':False,'PICO_tested':False}
(ROOT/'检查记录/独立重开与FBX回导检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
