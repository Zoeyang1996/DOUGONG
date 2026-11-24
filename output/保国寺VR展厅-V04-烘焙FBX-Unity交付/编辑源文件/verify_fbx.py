import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];ASSET=ROOT/'Assets/BaoguosiGalleryV04'
manifest=json.loads((ASSET/'MaterialManifest.json').read_text());expected={e['name']:e for e in manifest['materials']}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ASSET/'Models/Baoguosi_Gallery_V04_Baked.fbx'),use_image_search=True)
scene=bpy.context.scene;meshes=[o for o in scene.objects if o.type=='MESH']
assert len(meshes)==36
assert not [o for o in scene.objects if o.type in ('CAMERA','LIGHT')]
anchors=[o for o in scene.objects if o.name.startswith('VR_Teleport_Zone')];assert len(anchors)==8
images=[i for i in bpy.data.images if i.source=='FILE'];missing=[str(Path(bpy.path.abspath(i.filepath))) for i in images if not Path(bpy.path.abspath(i.filepath)).exists()]
assert not missing,missing
material_names={s.material.name for o in meshes for s in o.material_slots if s.material}
assert material_names==set(expected),(material_names-set(expected),set(expected)-material_names)
textures={Path(i.filepath).name for i in images};assert {e['texture'] for e in expected.values()}.issubset(textures)
points=[o.matrix_world@Vector(v) for o in meshes for v in o.bound_box];lo=[min(p[i] for p in points) for i in range(3)];hi=[max(p[i] for p in points) for i in range(3)];size=[hi[i]-lo[i] for i in range(3)]
assert abs(size[0]-36)<.5 and abs(size[1]-24)<.5 and 5<size[2]<12,size
for o in meshes:
 assert o.data.uv_layers or o.name.startswith('BGV04_Fine_') or o.name.startswith('SilkGlyph_'),o.name
 assert all(math.isfinite(v) for vertex in o.data.vertices for v in vertex.co),o.name
source=json.loads((ROOT/'检查记录/当前V04源文件清单.json').read_text());source_unchanged=hashlib.sha256(Path(source['source']).read_bytes()).hexdigest()==source['sha256'];assert source_unchanged
report={'fbx_reimported_in_Blender':True,'mesh_count':len(meshes),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes),'materials':len(material_names),'texture_files_found':len(textures),'missing_textures':missing,'camera_objects':0,'camera_data':len(bpy.data.cameras),'light_objects':0,'VR_anchors':len(anchors),'bounds_xyz_m':size,'source_unchanged':source_unchanged,'Unity_editor_executed':False,'PICO_device_tested':False}
(ROOT/'检查记录/FBX回读检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('FBX_VALIDATION',json.dumps(report,ensure_ascii=False),flush=True)
