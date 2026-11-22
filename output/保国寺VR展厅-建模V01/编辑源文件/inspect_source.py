import bpy,json
from pathlib import Path
p=Path('/Users/yangzhe/Desktop/浙江工商/DOUGONG/output/保国寺VR展厅-建模V01/检查记录/原场景检查.json')
p.write_text(json.dumps({'source':bpy.data.filepath,'objects':len(bpy.data.objects),'meshes':len([o for o in bpy.data.objects if o.type=='MESH']),'cameras':[o.name for o in bpy.data.objects if o.type=='CAMERA'],'materials':[m.name for m in bpy.data.materials],'images':[{ 'name':i.name,'path':i.filepath,'packed':bool(i.packed_file)} for i in bpy.data.images]},ensure_ascii=False,indent=2),encoding='utf-8')
print(p.read_text())
