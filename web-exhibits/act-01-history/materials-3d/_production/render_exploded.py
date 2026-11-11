import bpy,json
from pathlib import Path
from mathutils import Vector
B=Path(__file__).resolve().parents[1]
for row in json.loads((B/'asset-index.json').read_text())[:6]:
 k=row['id'];f=B/row['folder'];bpy.ops.wm.open_mainfile(filepath=str(f/(k+'.blend')))
 sc=bpy.context.scene;sc.frame_set(80);cam=sc.camera;inv=cam.matrix_world.inverted();deps=bpy.context.evaluated_depsgraph_get()
 pts=[]
 for o in bpy.data.collections['ASSET_'+k].objects:
  if o.type=='MESH':
   e=o.evaluated_get(deps);pts.extend(inv@(e.matrix_world@Vector(p)) for p in e.bound_box)
 xmin=min(p.x for p in pts);xmax=max(p.x for p in pts);ymin=min(p.y for p in pts);ymax=max(p.y for p in pts)
 cam.location+=cam.matrix_world.to_3x3()@Vector(((xmin+xmax)/2,(ymin+ymax)/2,0))
 cam.data.ortho_scale=max(xmax-xmin,(ymax-ymin)*sc.render.resolution_x/sc.render.resolution_y)*1.18
 sc.render.filepath=str(f/'exploded.png');bpy.ops.render.render(write_still=True)
 print('EXPLODED_DONE',k,flush=True)
