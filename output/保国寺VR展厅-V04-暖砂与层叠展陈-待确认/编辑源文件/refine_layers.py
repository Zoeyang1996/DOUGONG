import bpy
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for o in bpy.context.scene.objects:
 if o.type=='MESH' and o.name.startswith('LayeredEaveBand_'):
  layer=int(o.name.rsplit('_',1)[1]);delta=(.096-layer*.018)-(.060+layer*.018)
  for v in o.data.vertices:v.co.z+=delta
  uv=o.data.uv_layers.new(name='UVMap')
  for p in o.data.polygons:
   for li in p.loop_indices:
    v=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(v.x/2,v.y/2)
for o in bpy.context.scene.objects:
 if o.type=='FONT' and '识构' in o.data.body:print('CAPTION',o.name,o.data.body,tuple(o.matrix_world.translation))
assert not bpy.data.cameras
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath,compress=True)
