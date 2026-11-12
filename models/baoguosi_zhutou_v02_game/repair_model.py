"""Repair the user's edited v01 in Blender; never overwrite the source."""
import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent
WEB=OUT.parent.parent/'web-exhibits/act-03-assembly/assets'
s=bpy.context.scene;s.frame_set(1)
parts=[o for o in s.objects if o.type=='MESH' and '名称' in o]
for o in parts:
 o.animation_data_clear()
 for m in list(o.modifiers):o.modifiers.remove(m)
 o.data=o.data.copy();o.data.transform(o.matrix_world);o.matrix_world.identity()
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()

def volume(o):
 bm=bmesh.new();bm.from_mesh(o.data);v=abs(bm.calc_volume(signed=True));bm.free();return v

def bounds(o):
 vs=[v.co for v in o.data.vertices]
 return [min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]

def overlap(a,b):
 aa,ab=bounds(a);ba,bb=bounds(b)
 return all(min(ab[i],bb[i])-max(aa[i],ba[i])>1e-5 for i in range(3))

def duplicate(o):
 c=o.copy();c.data=o.data.copy();s.collection.objects.link(c);return c

def remove(o):
 mesh=o.data;bpy.data.objects.remove(o,do_unlink=True)
 if mesh.users==0:bpy.data.meshes.remove(mesh)

def boolean(a,b,operation):
 bpy.context.view_layer.objects.active=a
 m=a.modifiers.new('搭接布尔_'+operation,'BOOLEAN');m.operation=operation;m.solver='MANIFOLD';m.object=b
 bpy.ops.object.modifier_apply(modifier=m.name)

def intersect_volume(a,b):
 if not overlap(a,b):return 0
 c=duplicate(a);boolean(c,b,'INTERSECT');v=volume(c);remove(c);return v

def clip(o,z,upper,axis=2):
 c=duplicate(o)
 loc=[0,0,0];loc[axis]=z+(10 if upper else -10)
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
 cube=bpy.context.object;cube.scale=(20,20,20);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 boolean(c,cube,'INTERSECT');remove(cube);return c

before=[];ops=[];initial={o.name:volume(o) for o in parts}
for i,a in enumerate(parts):
 for b in parts[i+1:]:
  v=intersect_volume(a,b)
  if v>1e-8:before.append({'a':a.name,'b':b.name,'volume':v})
print('BEFORE',len(before),'overlaps',flush=True)
for pair in before:
 a=bpy.data.objects[pair['a']];b=bpy.data.objects[pair['b']]
 if intersect_volume(a,b)<1e-8:continue
 timber=lambda o:o.name.startswith(('gong_','ang_','timber_','fang_'))
 if timber(a) and timber(b):
  intersection=duplicate(a);boolean(intersection,b,'INTERSECT');lo,hi=bounds(intersection);remove(intersection)
  axis=0 if (a.name.startswith('ang_') and b.name.startswith('timber_')) or (b.name.startswith('ang_') and a.name.startswith('timber_')) else 2
  z=(lo[axis]+hi[axis])/2
  # Complementary half-laps keep both spanning members continuous.
  ca=clip(a,z+.00005,False,axis);cb=clip(b,z-.00005,True,axis)
  boolean(a,cb,'DIFFERENCE');boolean(b,ca,'DIFFERENCE');remove(ca);remove(cb)
  method='互补半搭接'
 else:
  # Carve a seat in the block; retain the bearing timber's silhouette.
  victim,keep=(a,b) if a.name.startswith('dou_') else (b,a)
  if not victim.name.startswith('dou_'):
   victim,keep=sorted([a,b],key=lambda o:initial[o.name],reverse=True)
  boolean(victim,keep,'DIFFERENCE');method='承口避让'
 ops.append({**pair,'method':method})
# Clean numeric remnants after interacting multi-way joints.
residual_repairs=[]
for pass_index in range(2):
 for i,a in enumerate(parts):
  for b in parts[i+1:]:
   v=intersect_volume(a,b)
   if v>1e-8:
    victim,keep=(b,a) if a.name.startswith('ang_') else (a,b)
    boolean(victim,keep,'DIFFERENCE');residual_repairs.append({'a':a.name,'b':b.name,'volume':v})
chips=[]
for o in parts:
 bm=bmesh.new();bm.from_mesh(o.data);seen=set();islands=[]
 for vert in bm.verts:
  if vert in seen:continue
  island=[];todo=[vert];seen.add(vert)
  while todo:
   v=todo.pop();island.append(v)
   for e in v.link_edges:
    w=e.other_vert(v)
    if w not in seen:seen.add(w);todo.append(w)
  islands.append(island)
 if len(islands)>1:
  islands.sort(key=lambda group:max(max(v.co[i] for v in group)-min(v.co[i] for v in group) for i in range(3)),reverse=True)
  for island in islands[1:]:
   span=max(max(v.co[i] for v in island)-min(v.co[i] for v in island) for i in range(3))
   if span<.13:
    chips.append({'id':o.name,'fragment_span_m':span});bmesh.ops.delete(bm,geom=island,context='VERTS')
 bm.to_mesh(o.data);bm.free();o.data.update()
remaining=[];checks=[]
for i,a in enumerate(parts):
 for b in parts[i+1:]:
  v=intersect_volume(a,b)
  if v>1e-8:remaining.append({'a':a.name,'b':b.name,'volume':v})
 bm=bmesh.new();bm.from_mesh(a.data)
 seen=set();islands=0
 for vert in bm.verts:
  if vert in seen:continue
  islands+=1;stack=[vert];seen.add(vert)
  while stack:
   cur=stack.pop()
   for edge in cur.link_edges:
    other=edge.other_vert(cur)
    if other not in seen:seen.add(other);stack.append(other)
 checks.append({'id':a.name,'volume_before':initial[a.name],'volume_after':volume(a),'retained_ratio':volume(a)/initial[a.name],'non_manifold_edges':sum(not e.is_manifold for e in bm.edges),'islands':islands})
 bm.free()
 a['修正']='游戏几何搭接：互补半搭接与承口避让，非测绘榫卯复原'
report={'source':'baoguosi_zhutou_v01/保国寺主铺作_v01_形制草模.blend','parts':len(parts),'overlaps_before':before,'repairs':ops,'overlaps_after':remaining,'tolerance_m3':1e-8,'mesh_checks':checks,'residual_repairs':residual_repairs,'removed_cutoff_chips':chips,'scope':'游戏展示几何修正，不代表历史榫卯或加工尺寸。'}
(OUT/'repair-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('AFTER',len(remaining),'overlaps','ISLANDS',[(r['id'],r['islands']) for r in checks if r['islands']>1],flush=True)
for a in parts:
 bevel=a.modifiers.new('修正切口微倒角','BEVEL');bevel.width=.001;bevel.segments=2
 bevel.use_clamp_overlap=True
 a.modifiers.new('修正法线','WEIGHTED_NORMAL')
s['status']='游戏布尔修正版 v02；保留用户编辑的 v01 外形与构件；非测绘榫卯复原'
# Remove obsolete exploded animation markers; scene always opens assembled.
s.frame_end=1
for marker in list(s.timeline_markers):s.timeline_markers.remove(marker)
for o in parts:o.hide_set(False);o.hide_render=False
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0]
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'保国寺柱头铺作_v02_游戏搭接修正版.blend'))
# Web materials use warm solid wood; original procedural materials stay in the blend.
colors={'gong':(.43,.235,.105,1),'dou':(.57,.36,.18,1),'ang':(.30,.135,.055,1),'other':(.40,.26,.14,1)}
for o in parts:
 category=next((x for x in ('gong','dou','ang') if o.name.startswith(x)),'other')
 m=bpy.data.materials.get('Web_'+category)
 if not m:
  m=bpy.data.materials.new('Web_'+category);m.diffuse_color=colors[category];m.use_nodes=True
  node=m.node_tree.nodes.get('Principled BSDF');node.inputs['Base Color'].default_value=colors[category];node.inputs['Roughness'].default_value=.66
 o.data.materials.clear();o.data.materials.append(m)
bpy.ops.export_scene.gltf(filepath=str(WEB/'baoguosi-zhutou-v02.glb'),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_extras=True,export_yup=True)
# Render the actual repaired asset, not the older reference screenshot.
s.render.engine='CYCLES';s.cycles.samples=24;s.render.resolution_x=900;s.render.resolution_y=900;s.render.resolution_percentage=100
s.render.film_transparent=True
for o in s.objects:
 if o.type=='MESH' and o not in parts:o.hide_render=True
s.camera.location=(5.5,-7,4.1);s.camera.rotation_euler=(Vector((0,.25,.7))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.ortho_scale=5.3
s.render.filepath=str(WEB/'assembled-reference.png');bpy.ops.render.render(write_still=True)
print('REPAIR_EXPORT_COMPLETE',flush=True)
