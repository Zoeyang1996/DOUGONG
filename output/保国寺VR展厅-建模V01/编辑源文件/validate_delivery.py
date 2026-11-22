import bpy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
model=ROOT/'模型'/'保国寺VR数字斗拱展厅_V01_无摄像机.blend'
fbx=ROOT/'模型'/'保国寺VR数字斗拱展厅_V01_无摄像机.fbx'
bpy.ops.wm.open_mainfile(filepath=str(model),load_ui=False)
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
blend={
 'camera_objects':[o.name for o in bpy.data.objects if o.type=='CAMERA'],
 'camera_datablocks':len(bpy.data.cameras),
 'scene_camera_references':[s.name for s in bpy.data.scenes if s.camera],
 'mesh_count':len(meshes),
 'empty_meshes':[o.name for o in meshes if not o.data.polygons],
 'packed_textures':all(bool(i.packed_file) for i in bpy.data.images if i.source=='FILE'),
 'external_missing_textures':[i.filepath for i in bpy.data.images if i.source=='FILE' and not i.packed_file and not Path(bpy.path.abspath(i.filepath)).exists()],
 'zero_scale_objects':[o.name for o in bpy.data.objects if any(abs(v)<1e-6 for v in o.scale)],
 'text_mesh_count':len([o for o in meshes if o.get('文字内容')]),
 'floor_tile_count':len([o for o in meshes if o.name.startswith('FloorTile_')]),
 'empty_exhibit_anchors':len([o for o in bpy.data.objects if o.name.endswith('_ExhibitAnchor_EMPTY')]),
 'teleport_anchors':len([o for o in bpy.data.objects if o.name.startswith('VR_Teleport_')])}
assert not blend['camera_objects'] and blend['camera_datablocks']==0 and not blend['scene_camera_references']
assert not blend['empty_meshes'] and not blend['zero_scale_objects'] and blend['packed_textures']
assert blend['empty_exhibit_anchors']==8 and blend['teleport_anchors']==8
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(fbx),use_anim=False)
fbxcheck={'mesh_count':len([o for o in bpy.data.objects if o.type=='MESH']),
 'camera_count':len([o for o in bpy.data.objects if o.type=='CAMERA']),
 'light_count':len([o for o in bpy.data.objects if o.type=='LIGHT']),
 'mesh_count_matches_blend':len([o for o in bpy.data.objects if o.type=='MESH'])==blend['mesh_count'],
 'missing_texture_files':[bpy.path.abspath(i.filepath) for i in bpy.data.images if i.source=='FILE' and not Path(bpy.path.abspath(i.filepath)).exists()]}
assert fbxcheck['mesh_count_matches_blend'] and fbxcheck['camera_count']==0 and fbxcheck['light_count']==0
assert not fbxcheck['missing_texture_files'],fbxcheck['missing_texture_files']
report={'blend_reopened':blend,'fbx_reimported':fbxcheck,'passed':True}
(ROOT/'检查记录'/'独立重开与FBX回导检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
