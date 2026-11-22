import bpy
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for id in ['07_E_数字传承','07_E_小拱']:
 art=bpy.data.objects['Art_'+id]
 for o in art.children:
  if o.name.startswith('SpecimenDarkBacking'):o.scale.y*=.75/.99
  if o.name.startswith('SpecimenFineEdge'):o.scale.y*=.75/.99
  if o.name.startswith('SpecimenLightBar'):o.location.y-=.12
for o in bpy.context.scene.objects:
 if o.type=='FONT' and '共创' in o.data.body:
  print('TITLE',o.name,o.data.body,tuple(o.location))
  if o.data.body=='木构共创成果区':o.location.z+=.20
assert len(bpy.data.cameras)==0
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath,compress=True)
