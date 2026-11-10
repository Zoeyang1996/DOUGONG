import bpy,math,json,bmesh
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parent;S=bpy.context.scene
wood=bpy.data.materials['木构_参考模型朱褐'];gold=bpy.data.materials['藻井_原木']
def box(n,p,d,c,m=wood):
 x,y,z=[v/2 for v in d];vs=[(a*x,b*y,e*z) for a,b,e in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]];fs=[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]
 me=bpy.data.meshes.new(n);me.from_pydata(vs,[],fs);me.update();ob=bpy.data.objects.new(n,me);c.objects.link(ob);ob.location=p;ob.data.materials.append(m);ob['参考依据']='照片4/9；文档image2/8/10，连续承托关系';return ob
fang=bpy.data.collections['02_阑额与柱头枋'];roof=bpy.data.collections['05_槫与椽架_可隐藏'];inside=bpy.data.collections['04_内槽铺作与梁架'];ceil=bpy.data.collections['06_前廊三藻井与平棊']
removed=[]
for ob in list(S.objects):
 if ob.name.startswith('山花内斜承') or (ob.name.startswith('前三椽栿_中三椽栿_后乳栿') and ob.name.endswith(('_11','_21'))):
  removed.append(ob.name);bpy.data.objects.remove(ob,do_unlink=True)
# Continuous bearing timber, kept visible when the rafters are hidden.
for y in [-6.97,6.97]:box('前后檐柱头枋',(0,y,4.61),(12.2,.25,.20),fang)
for x in [-5.9,5.9]:box('山面柱头枋',(x,0,4.61),(.25,14.35,.20),fang)
for y in [-2.24,3.79]:box('照壁补间承托枋',(0,y,6.53),(6.1,.26,.22),inside)
# Main beam below the king-post frame; preserve the lower beam's authentic span
# through the four higher inner columns and remove coplanar duplicate faces.
for ob in S.objects:
 if ob.name.startswith('中三椽栿_主梁'):
  for v in ob.data.vertices:
   # Local X is the longitudinal direction; extend the rear bearing to the rear inner column.
   if v.co.x>0:v.co.x+=.60
  ob.data.update()
# Distinguish rafters from purlins so inspection does not remove the load-bearing top frame.
raf=bpy.data.collections.new('07_椽子_默认隐藏便于看内部');S.collection.children.link(raf)
for ob in list(roof.objects):
 if ob.name.startswith('椽_'):
  roof.objects.unlink(ob);raf.objects.link(ob)
raf.hide_render=True;raf.hide_viewport=True;roof.hide_render=False
# Supplement the roof edge plan with return members, without inventing giant diagonal trusses.
for x in [-5.9,5.9]:
 for y in [-3.3,3.3]:box('山面丁栿承托',(x/2+math.copysign(1.41,x),y,6.12),(3.08,.25,.35),inside)
# Filled timber dome shell, board seams remain legible alongside the rib framework.
for name,cx,r,rise in [('当心间大藻井',0,.921,.898),('西次间小藻井',-3.56,.6295,.766),('东次间小藻井',3.56,.6295,.766)]:
 cy=-4.62;z=5.95
 for k in range(32):
  vs=[];faces=[]
  for j in range(11):
   t=j/10*1.50
   for a in [k*math.tau/32+.003,(k+1)*math.tau/32-.003]:vs.append((cx+r*math.cos(t)*math.cos(a),cy+r*math.cos(t)*math.sin(a),z+rise*math.sin(t)))
  for j in range(10):faces.append((2*j,2*j+1,2*j+3,2*j+2))
  me=bpy.data.meshes.new('穹窿板');me.from_pydata(vs,[],faces);me.update();ob=bpy.data.objects.new(name+'_穹窿木板_%02d'%k,me);ceil.objects.link(ob);ob.data.materials.append(gold)
  mod=ob.modifiers.new('木板厚度','SOLIDIFY');mod.thickness=.018
  ob['参考依据']='照片7穹窿围板、文档image7；板缝数量与厚度为推定'
# Move internal views into the front gallery rather than outside the eaves.
def point(ob,p):ob.rotation_euler=(Vector(p)-ob.location).to_track_quat('-Z','Y').to_euler()
C=bpy.data.objects['总览_东南向'];C.location=(22,-28,20);point(C,(0,0,4));C.data.ortho_scale=25;S.camera=C
S.cycles.samples=32
def render(fn):S.render.filepath=str(O/fn);bpy.ops.render.render(write_still=True)
render('07_修正后内部总览.png')
c=bpy.data.objects['前廊内部_仰视'];c.location=(0,-5.6,2.1);point(c,(0,-4.55,6));c.data.lens=15;S.camera=c;render('08_三藻井内部仰视.png')
S.camera=bpy.data.objects['东侧正投影'];render('09_修正后侧视.png')
S.camera=C
for screen in bpy.data.screens:
 for a in screen.areas:
  if a.type=='VIEW_3D':
   v=a.spaces.active;v.region_3d.view_distance=26;v.region_3d.view_location=(0,0,4);v.region_3d.view_rotation=C.rotation_euler.to_quaternion();v.region_3d.view_perspective='ORTHO';v.shading.color_type='MATERIAL';v.overlay.show_extras=False;v.overlay.show_floor=False
for ob in S.objects:
 if ob.type in ['CAMERA','LIGHT']:ob.hide_set(True)
S['状态']='按指定图片搭建的内部结构初版；待核项目见模型说明。'
bpy.data.texts['模型依据与待核项'].write('\n修正：拆分椽子集合（默认隐藏）、补充连续承托枋、去除重复中梁与无充分图像依据的山花长斜撑、增加藻井围板。未验证节点碰撞与结构受力。\n')
(O/'模型说明.txt').write_text(bpy.data.texts['模型依据与待核项'].as_string(),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(O/'保国寺大殿_内部结构_v01.blend'))
issues=[];count=0
for ob in S.objects:
 if ob.type!='MESH':continue
 count+=1;bm=bmesh.new();bm.from_mesh(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh())
 if any(not e.is_manifold for e in bm.edges):issues.append(ob.name)
 bm.free();ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()
(O/'validation.json').write_text(json.dumps({'mesh_objects':count,'non_manifold_evaluated':issues,'packed_images':sum(bool(i.packed_file) for i in bpy.data.images),'removed_duplicate_or_unsupported_objects':removed,'limits':'not an as-built survey; no structural calculation or exhaustive collision validation'},ensure_ascii=False,indent=2),encoding='utf-8')
(O/'构件清单.json').write_text(json.dumps([{'name':ob.name,'collection':ob.users_collection[0].name,'reference':ob.get('参考依据','推定，详见模型说明')} for ob in S.objects if ob.type=='MESH'],ensure_ascii=False,indent=2),encoding='utf-8')
print('REFINED',count,len(issues))
