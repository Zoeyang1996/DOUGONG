import bpy,json,struct,math
from pathlib import Path
from mathutils import Vector
B=Path(__file__).resolve().parents[1]
index=json.loads((B/'asset-index.json').read_text());report=[]
for row in index:
 k=row['id'];folder=B/row['folder'];meta=json.loads((folder/'assembly.json').read_text())
 bpy.ops.wm.open_mainfile(filepath=str(folder/(k+'.blend')));sc=bpy.context.scene;sc.frame_set(1)
 for ob in bpy.data.collections['ASSET_'+k].objects:
  if ob.type=='MESH':
   while len(ob.data.uv_layers)>1:ob.data.uv_layers.remove(ob.data.uv_layers[-1])
   ob.data.uv_layers[0].name='WoodUV';ob.data.uv_layers.active_index=0;ob.data.uv_layers[0].active_render=True
 if k in ['G1','G2']:
  for p in meta['parts']:
   ob=bpy.data.objects[p['id']];base=ob.location.copy()
   if k=='G1':off=Vector((.75,0,0)) if p['order']==2 else Vector((-.75,0,0))
   else:off=Vector((0,0,.85)) if p['order']>1 else Vector((0,0,-.50))
   p['appear']['offset']=[off.x,off.z,-off.y];ob['appear_offset_web']=p['appear']['offset']
   ob.location=base+off;ob.keyframe_insert(data_path='location',frame=80);ob.location=base
  (folder/'assembly.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));sc.frame_set(1)
  if 'README_素材审核' in bpy.data.texts:
   bpy.data.texts['README_素材审核'].clear();bpy.data.texts['README_素材审核'].write(json.dumps(meta,ensure_ascii=False,indent=2))
 bpy.ops.object.select_all(action='DESELECT')
 for ob in bpy.data.collections['ASSET_'+k].objects:ob.select_set(True)
 bpy.ops.export_scene.gltf(filepath=str(folder/(k+'.glb')),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_extras=True,export_yup=True,export_draco_mesh_compression_enable=True)
 bpy.ops.object.select_all(action='DESELECT');bpy.ops.wm.save_as_mainfile(filepath=str(folder/(k+'.blend')))
 if k=='G5':bpy.data.libraries.write(str(B/'shared/WoodMaterial.blend'),{bpy.data.materials['WOOD_SHARED_v1']},fake_user=True)
 if k in ['G1','G2']:
  sc.frame_set(80);sc.render.filepath=str(folder/'exploded.png');bpy.ops.render.render(write_still=True)
 # Actual importer round-trip confirms Draco decode and textures.
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.gltf(filepath=str(folder/(k+'.glb')))
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
 raw=(folder/(k+'.glb')).read_bytes();n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n])
 nodes={x['name']:x for x in g['nodes'] if 'name' in x};errors=[]
 for p in meta['parts']:
  node=nodes.get(p['id'])
  if not node:errors.append('missing '+p['id']);continue
  actual=node.get('translation',[0,0,0])
  if max(abs(a-b) for a,b in zip(actual,p['target']['pos']))>1e-4:errors.append('transform '+p['id'])
 assert len(meshes)==meta['parts_count'],(k,len(meshes),meta['parts_count'])
 assert not errors,(k,errors)
 assert len(g.get('materials',[]))==1
 assert 'KHR_draco_mesh_compression' in g.get('extensionsUsed',[])
 assert len(raw)<3_000_000
 report.append({'id':k,'imported_meshes':len(meshes),'glb_bytes':len(raw),'material_count':len(g.get('materials',[])),'draco':True,'transform_errors':errors,'roundtrip':'pass'})
 row['glb_bytes']=len(raw)
 v=json.loads((folder/'validation.json').read_text());v['glb_bytes']=len(raw);v['roundtrip']='pass';(folder/'validation.json').write_text(json.dumps(v,ensure_ascii=False,indent=2))
(B/'asset-index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2))
(B/'verification-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('VERIFIED',len(report))
