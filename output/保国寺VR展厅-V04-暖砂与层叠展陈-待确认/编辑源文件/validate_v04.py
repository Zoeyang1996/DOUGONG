import bpy,json,hashlib,array,math,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
PANELS=json.loads((ROOT/'编辑源文件/墙面展陈内容.json').read_text())
source=json.loads((ROOT/'检查记录/V04修改记录.json').read_text())['source']
def structure():
 result={}
 for o in bpy.context.scene.objects:
  if o.type!='MESH' or not any(c.name.startswith(('01_','02_','07_','08_')) for c in o.users_collection):continue
  verts=array.array('f',[0])*(len(o.data.vertices)*3);o.data.vertices.foreach_get('co',verts)
  digest=hashlib.sha256(verts.tobytes()+str([tuple(p.vertices) for p in o.data.polygons]).encode()).hexdigest()
  result[o.name]={'mesh_hash':digest,'matrix':[round(x,6) for row in o.matrix_world for x in row]}
 return result
bpy.ops.wm.open_mainfile(filepath=source,load_ui=False);before=structure();before_text={o.name:o.data.body for o in bpy.context.scene.objects if o.type=='FONT'}
source_hash=hashlib.sha256(Path(source).read_bytes()).hexdigest()
assert source_hash==json.loads((ROOT/'检查记录/V04修改记录.json').read_text())['source_sha256']
path=ROOT/'模型/展厅V04_暖砂黄与层叠展陈_未烘焙_无摄像机.blend'
bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False);after=structure()
assert before==after,'建筑壳体或原有木构改变'
assert all(bpy.data.objects.get(n) and bpy.data.objects[n].type=='FONT' and bpy.data.objects[n].data.body==t for n,t in before_text.items()), '原有文字被修改'
assert len([o for o in bpy.data.objects if o.name.startswith('HangingSilk_Z')])==2
assert not [o for o in bpy.data.objects if o.type=='CAMERA'] and len(bpy.data.cameras)==0
assert all(s.camera is None for s in bpy.data.scenes)
assert not [o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith(tuple(f'P{i:02}_' for i in range(1,9)))], '残留原展台'
images=[i for i in bpy.data.images if i.source=='FILE'];assert len(images)==11 and all(i.packed_file for i in images)
fonts=[f for f in bpy.data.fonts if f.users>0 and f.filepath and not f.filepath.startswith('<')];assert all(f.packed_file for f in fonts)
coverage={i:sorted(set(p['id'].split('_')[1] for p in PANELS if p['zone']==i)) for i in range(1,9)}
assert all(v==['E','N','S','W'] for v in coverage.values())
assert len([o for o in bpy.context.scene.objects if o.name.startswith('Wall_') and o.type=='EMPTY'])==40
assert len([o for o in bpy.context.scene.objects if o.name.startswith('ColumnGroup_Zone')])==24

# The boards must not span any of the existing openings in plan.
openings=[('Y',.12,4.5,7.5),('Y',.12,28.5,31.5),('X',12,2,5),('X',12,18.5,21.5),('X',24,3,6),('X',24,10,13),('Y',7,3.5,6.5),('Y',7,17,20),('Y',17,3.5,6.5),('Y',17,17,20),('Y',10,29,32)]
door_hits=[]
for p in PANELS:
 axis='Y' if p['face'] in ('N','S') else 'X';c=p['center'];fixed=c[1 if axis=='Y' else 0];u=c[0 if axis=='Y' else 1]
 for a,f,lo,hi in openings:
  if a==axis and abs(f-fixed)<.6 and min(u+p['width']/2+.03,hi)-max(u-p['width']/2-.03,lo)>.001:door_hits.append(p['id'])
assert not door_hits,door_hits

# Same walking line used for V02, plus its quiet-corridor branch.
route=[(6,.35),(6,1.2),(3.4,1.2),(3.4,5.5),(5,6),(5,11),(6,13),(5,16),(5,18.2),(4.5,19),(6,19),(10.7,20),(12.5,20),(17.7,19.6),(18.5,17.8),(18.5,15.5),(13.7,15.2),(13.7,8.5),(22,8.5),(22,11.5),(25.5,11.5),(26.7,14.7),(30.5,14.7),(30.5,11),(30.5,9),(28.5,7),(28.5,4.2),(30,2),(30,.35)]
quiet=[(8.8,3.5),(12,3.5),(18.5,3.5),(22.5,4.5),(24,4.5),(27,4.5)]
obstacles=[]
for o in bpy.context.scene.objects:
 if o.type not in ('MESH','CURVE','FONT') or o.hide_render:continue
 vs=[o.matrix_world@Vector(v) for v in o.bound_box];lo=[min(v[i] for v in vs) for i in range(3)];hi=[max(v[i] for v in vs) for i in range(3)]
 if hi[2]>.05 and lo[2]<1.85:obstacles.append((o.name,lo,hi))
hits=[]
for path in (route,quiet,[(18.5,3.5),(18.5,7.8)]):
 for a,b in zip(path,path[1:]):
  count=max(1,math.ceil(math.dist(a,b)/.1))
  for j in range(count+1):
   point=[a[k]+(b[k]-a[k])*j/count for k in (0,1)]
   for name,lo,hi in obstacles:
    if all(lo[k]-.3<point[k]<hi[k]+.3 for k in (0,1)):hits.append({'object':name,'point':point})
# Conservative AABBs for rounded column bases can overestimate their real footprint;
# record actual results rather than silently skipping any colliding object.
report={'source_sha256_unchanged':True,'original_shell_and_timber_meshes_unchanged':len(before),'wall_groups':len(PANELS),'four_sides_of_all_8_zones':coverage,'door_overlap':door_hits,'plinth_remnants':0,'camera_objects':0,'camera_data':0,'packed_images':len(images),'packed_fonts':[f.name for f in fonts],'editable_text_objects':sum(o.type=='FONT' for o in bpy.context.scene.objects),'walk_test':{'radius_m':.3,'height_m':1.85,'sampling_m':.1,'hits':hits,'clear':not hits},'original_text_objects_preserved':len(before_text),'no_lighting_bake_in_V04':True,'new_silk_hangings':2}
chars={}
for o in bpy.context.scene.objects:
 if o.type=='FONT':
  f=o.data.font;chars.setdefault(f.name,{'path':f.filepath,'characters':set()})['characters'].update(o.data.body)
for v in chars.values():v['characters']=''.join(sorted(v['characters']))
(ROOT/'检查记录/字体字形检查输入.json').write_text(json.dumps(chars,ensure_ascii=False,indent=2))
(ROOT/'检查记录/重开与空间检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('VALIDATION',json.dumps(report,ensure_ascii=False),flush=True)
assert not hits,hits[:10]
