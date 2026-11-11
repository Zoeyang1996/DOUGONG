import bpy,json
from pathlib import Path
root=Path('/Users/yangzhe/Desktop/浙江工商/DOUGONG')
rows=[]
for p in sorted((root/'models/保国寺铺作/保国寺铺作').glob('柱头*.blend')):
 bpy.ops.wm.open_mainfile(filepath=str(p))
 rows.append({'file':str(p),'objects':[{'name':o.name,'type':o.type,'vertices':len(o.data.vertices) if o.type=='MESH' else 0,'dimensions':list(o.dimensions),'location':list(o.location)} for o in bpy.context.scene.objects]})
(root/'web-exhibits/act-01-history/materials-3d/_production/existing_models.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
