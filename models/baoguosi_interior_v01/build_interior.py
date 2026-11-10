import bpy, math, json, bmesh
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parent;ROOT=O.parent.parent
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
S=bpy.context.scene;S.name='保国寺大殿_内部构架';S.unit_settings.system='METRIC'
cols={};inventory=[]
def collection(n):
 c=bpy.data.collections.new(n);S.collection.children.link(c);cols[n]=c;return c
base=collection('00_台基柱础与佛坛');pillars=collection('01_十六柱柱网');fang=collection('02_阑额与柱头枋');brackets=collection('03_外槽铺作');inside=collection('04_内槽铺作与梁架');roof=collection('05_槫与椽架_可隐藏');ceil=collection('06_前廊三藻井与平棊');refs=collection('90_原始参考图');studio=collection('99_灯光相机')
def material(n,c):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=.7;return m
wood=material('木构_参考模型朱褐',(.29,.085,.041));edge=material('斗与栱_浅朱褐',(.43,.17,.075));dark=material('椽与额枋_深木',(.18,.065,.033));stone=material('石构_暖灰',(.37,.35,.30));floor=material('展示台基',(.23,.24,.24));gold=material('藻井_原木',(.47,.26,.11))
def reg(o,n,c,m,source):
 o.name=n
 for k in list(o.users_collection):k.objects.unlink(o)
 c.objects.link(o);o.data.materials.append(m);o['参考依据']=source;o['精度']='图像比例重建；未提供的断面、隐藏节点待核';inventory.append(o)
 return o
def box(n,p,d,c=fang,m=wood,source='文档image8、image10；照片4'):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.dimensions=d;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);reg(o,n,c,m,source)
 be=o.modifiers.new('边缘小倒角','BEVEL');be.width=.012;be.segments=2;return o
def cylinder(n,a,b,r,c,m,source='文档image8、image10',verts=24):
 a=Vector(a);b=Vector(b);bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=(b-a).length,location=(a+b)/2);o=bpy.context.object;o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return reg(o,n,c,m,source)
def beam(n,a,b,w,h,c=inside,m=wood):
 a=Vector(a);b=Vector(b);o=box(n,(a+b)/2,(w,h,(b-a).length),c,m);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def profile(n,poly,width,origin,angle,c,m=wood,source='照片4；文档image10'):
 vs=[(x,y,z) for y in [-width/2,width/2] for x,z in poly];N=len(poly);fs=[tuple(reversed(range(N))),tuple(range(N,2*N))]+[(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)]
 me=bpy.data.meshes.new(n);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(n,me);c.objects.link(o);o.data.materials.append(m);o.location=origin;o.rotation_euler.z=angle;o['参考依据']=source;o['精度']='轮廓按图重建，榫卯未测绘';inventory.append(o);return o
def moon(n,a,b,z,h=.5,c=inside):
 dx=b[0]-a[0];dy=b[1]-a[1];L=math.hypot(dx,dy)
 ps=[(-L/2,0),(-L/2+.15,-h*.3),(-L*.34,-h*.52),(L*.34,-h*.52),(L/2-.15,-h*.3),(L/2,0),(L/2,h*.3),(L*.32,h*.48),(-L*.32,h*.48),(-L/2,h*.3)]
 return profile(n,ps,.32,((a[0]+b[0])/2,(a[1]+b[1])/2,z),math.atan2(dy,dx),c)
X=[-5.9,-2.82,2.82,5.9];Y=[-6.97,-2.24,3.79,6.97]
box('台基_参考平面边界',(0,0,-.3),(14.6,16.8,.6),base,floor,'文档image4，台基厚度示意')
for k in range(5):box('南侧台阶_'+str(k),(0,-8.8+k*.22,-.55+k*.11),(3.2,1.3-k*.18,.12),base,stone)
for i in range(4):
 for j in range(4):
  x,y=X[i],Y[j];inner=i in [1,2] and j in [1,2];h=(7.05 if j==1 else 7.10) if inner else 4.7
  cylinder(f'柱础_{i}{j}',(x,y,0),(x,y,.19),.46 if inner else .36,base,stone,'文档image2、image3；柱础简化',48)
  if inner:
   # Reuse the previously made real mortise geometry, not the earlier display spacing.
   src=ROOT/'models/baoguosi_guoleng_v01/保国寺四根瓜棱柱_v01.blend'
   with bpy.data.libraries.load(str(src),link=False) as (data,target):target.objects=[n for n in data.objects if n.startswith('A_前左')]
   for ob in target.objects:
    if ob:
     pillars.objects.link(ob);ob.animation_data_clear();ob.name=f'内柱_{i}{j}_'+ob.name;ob.location=(x,y,.19);ob.scale=(1,1,(h-.19)/3.8);ob['参考依据']='本次照片8、文档image5；拼合榫卯沿用上版示意';inventory.append(ob)
  else:
   # Whole timber with a gently eight-lobed section, not eight intersecting sticks.
   N=96;vs=[]
   for z,scale in [(.19,1),(h,.96)]:
    for k in range(N):
     t=k*math.tau/N;r=(.255+.016*math.cos(t*8))*scale;vs.append((x+r*math.cos(t),y+r*math.sin(t),z))
   fs=[tuple(reversed(range(N))),tuple(range(N,2*N))]+[(k,(k+1)%N,(k+1)%N+N,k+N) for k in range(N)]
   me=bpy.data.meshes.new('瓜棱柱');me.from_pydata(vs,[],fs);me.update();ob=bpy.data.objects.new(f'檐柱_{i}{j}',me);pillars.objects.link(ob);ob.data.materials.append(wood);ob['参考依据']='文档image5：外围存在不同瓜棱范围，本版统一轮廓待细分';inventory.append(ob)
for j in range(4):
 for i in range(3):
  z=4.36 if j in [0,3] else 5.7
  moon(f'横向阑额_{i}{j}',(X[i],Y[j]),(X[i+1],Y[j]),z,.35,fang)
for i in [0,3]:
 for j in range(3):moon(f'山面阑额_{i}{j}',(X[i],Y[j]),(X[i],Y[j+1]),4.36,.36,fang)
for i in [1,2]:
 for j in range(3):moon(f'前三椽栿_中三椽栿_后乳栿_{i}{j}',(X[i],Y[j]),(X[i],Y[j+1]),[5.58,7.60,5.65][j],[.5,.72,.44][j],inside)
for y in Y[1:3]:
 for z in [6.12,6.53]:beam('内柱横向联系枋',(-3.12,y,z),(3.12,y,z),.23,.29,inside)
for z,d in [(.10,(5.9,3.8,.2)),(.30,(5.6,3.6,.22)),(.50,(5.9,3.8,.18))]:box('佛坛_须弥座轮廓',(0,2.65,z),d,base,stone,'文档image4；照片3，细部未复原')
def point(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
def cam(n,loc,p,scale):
 d=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,d);studio.objects.link(o);o.location=loc;point(o,p);d.type='ORTHO';d.ortho_scale=scale;S.camera=o;return o
C=cam('总览_东南向',(22,-28,20),(0,0,4),24)
S.render.engine='CYCLES';S.cycles.samples=24;S.cycles.use_denoising=True;S.render.resolution_x=1600;S.render.resolution_y=1300;S.render.resolution_percentage=100
S.world.color=(.22,.22,.22)
S.world.use_nodes=True;S.world.node_tree.nodes['Background'].inputs[0].default_value=(.25,.28,.32,1);S.world.node_tree.nodes['Background'].inputs[1].default_value=.7
for p,power,size in [((0,-10,20),4200,12),((-13,-4,12),3500,10),((7,12,19),5000,10)]:
 d=bpy.data.lights.new('柔光','AREA');d.energy=power;d.size=size;o=bpy.data.objects.new('柔光',d);studio.objects.link(o);o.location=p;point(o,(0,0,4))
def save_view():
 for scr in bpy.data.screens:
  for a in scr.areas:
   if a.type=='VIEW_3D':
    v=a.spaces.active;v.region_3d.view_distance=26;v.region_3d.view_location=(0,0,4);v.region_3d.view_rotation=C.rotation_euler.to_quaternion();v.region_3d.view_perspective='ORTHO';v.clip_end=500;v.shading.color_type='MATERIAL';v.shading.show_cavity=True;v.overlay.show_extras=False
 bpy.ops.object.select_all(action='DESELECT')
def snap(name):
 S.render.filepath=str(O/name);bpy.ops.render.render(write_still=True)
save_view();bpy.ops.wm.save_as_mainfile(filepath=str(O/'stage01_柱网.blend'));snap('01_柱网与联系梁.png')
# Bracket arms have curved/scooped profiles and separate bearing blocks.
def gong(n,L,p,angle,c=brackets):
 ps=[(-L/2,.10),(-L/2+.08,-.04),(-L*.29,-.08),(-L*.19,-.17),(L*.19,-.17),(L*.29,-.08),(L/2-.08,-.04),(L/2,.10)]
 return profile(n,ps,.16,p,angle,c,edge,'照片4与6，按位置区别外槽与内槽；断面为图像推定')
def puzuo(n,x,y,z,angle=0,c=brackets,layers=4):
 def pos(u,v,h):return (x+u*math.cos(angle)-v*math.sin(angle),y+u*math.sin(angle)+v*math.cos(angle),z+h)
 box(n+'_栌斗',pos(0,0,.13),(.48,.48,.26),c,edge)
 for k in range(layers):
  reach=.27*(k+1);h=.32+k*.22
  gong(n+f'_横栱{k}',1.05+(.15 if k==layers-1 else 0),pos(0,reach,h),angle,c)
  gong(n+f'_华栱{k}',reach*2+.3,pos(0,0,h-.05),angle+math.pi/2,c)
  for u in [-.42,.42]:box(n+f'_散斗{k}',pos(u,reach,h+.18),(.18,.18,.16),c,edge)
 if c==brackets:
  for k in [0,1]:
   a=pos(0,1.1+k*.20,.46+k*.25);b=pos(0,-1.9,.46+k*.25+.95);beam(n+'_下昂'+str(k),a,b,.13,.20,c,dark)
 else:
  gong(n+'_内转丁头栱',1.15,pos(0,-.30,1.02),angle+math.pi/2,c)
 return z+.32+(layers-1)*.22+.26
for j in [0,3]:
 for i,x in enumerate(X):puzuo(f'前后檐柱头_{i}{j}',x,Y[j],4.7,math.pi if j==0 else 0)
 for i in range(3):
  count=2 if i==1 else 1
  for k in range(count):puzuo(f'前后檐补间_{i}{j}{k}',X[i]+(X[i+1]-X[i])*(k+1)/(count+1),Y[j],4.7,math.pi if j==0 else 0,layers=4)
for i in [0,3]:
 for j in [1,2]:puzuo(f'山面柱头_{i}{j}',X[i],Y[j],4.7,math.pi/2 if i==0 else -math.pi/2)
 for j in range(3):
  for t in [.5]:puzuo(f'山面补间_{i}{j}',X[i],Y[j]+(Y[j+1]-Y[j])*t,4.7,math.pi/2 if i==0 else -math.pi/2)
for i in [0,3]:
 for j in [0,3]:
  a=math.atan2(Y[j],X[i])-math.pi/2;puzuo(f'转角斜出_{i}{j}',X[i],Y[j],4.7,a,layers=4)
for i in [1,2]:
 for j in [1,2]:puzuo(f'内柱柱头_{i}{j}',X[i],Y[j],7.05 if j==1 else 7.10,math.pi if j==1 else 0,inside,3)
for y,z in [(Y[1],6.55),(Y[2],6.55)]:
 for x in [-1.4,1.4]:puzuo('照壁上补间',x,y,z,0,inside,2)
# Two primary transverse frames, flat beam, king post and paired fork braces.
for x in [-2.82,2.82]:
 moon('中三椽栿_主梁',(x,-3.3),(x,3.3),8.04,.65)
 for y in [-1.65,1.65]:
  box('蜀柱',(x,y,8.85),(.24,.24,1.12),inside);puzuo('蜀柱柱头',x,y,9.25,0,inside,1)
 moon('平梁',(x,-1.83),(x,1.83),9.62,.42)
 box('脊蜀柱',(x,0,10.18),(.25,.25,.84),inside)
 beam('叉手_南',(x,-1.6,9.68),(x,0,10.63),.14,.16)
 beam('叉手_北',(x,1.6,9.68),(x,0,10.63),.14,.16)
for y,z in [(-6.97,6.02),(6.97,6.02)]:
 for x0,x1 in zip(X,X[1:]):beam('檐口承托枋',(x0-.3,y,z),(x1+.3,y,z),.22,.22,roof)
for x in [-5.9,5.9]:beam('山面承托枋',(x,-7.2,6.02),(x,7.2,6.02),.22,.22,roof)
P=[(-8.15,5.65),(-6.6,6.645),(-4.95,7.365),(-3.3,8.284),(-1.65,9.882),(0,10.689),(1.65,9.882),(3.3,8.284),(4.95,7.365),(6.6,6.645),(8.15,5.65)]
for j,(y,z) in enumerate(P):
 length=6.2 if abs(y)<3.4 else 12.7
 cylinder('槫_%02d_标高中%.3f'%(j,z),(-length/2,y,z),(length/2,y,z),.14,roof,dark,'文档image8：6.645/7.365/8.284/9.882/10.689；进深位置按图推定',32)
 # Cantilever framing at intermediate slopes, visible from inside.
 if 0<abs(y)<6.61:
  for x in [-2.82,2.82]:
   if abs(y)>3.3:beam('槫下承托短柱',(x,y,6.02),(x,y,z-.14),.18,.18,inside)
for side in [-1,1]:
 for y in [-3.3,-1.65,0,1.65,3.3]:
  z=dict(P)[y];beam('山花内斜承',(side*2.82,y,z-.12),(side*5.9,y,6.05),.19,.22,roof)
for k in range(35):
 x=-6.3+k*.37
 for j in range(len(P)-1):
  y,z=P[j];yy,zz=P[j+1]
  if abs(x)>3.05 and min(abs(y),abs(yy))<3.3:continue
  cylinder('椽_%02d_%02d'%(k,j),(x,y,z+.16),(x,yy,zz+.16),.045,roof,dark,'照片5、文档image2；椽距示意',8)
save_view();bpy.ops.wm.save_as_mainfile(filepath=str(O/'stage02_梁架.blend'));snap('02_铺作与梁架.png')
# Three caissons and two flat interstitial ceilings in the southern front gallery.
def ring(n,cx,cy,z,r,count,c=ceil,m=gold):
 for k in range(count):
  a=k*math.tau/count;b=(k+1)*math.tau/count;beam(n,(cx+r*math.cos(a),cy+r*math.sin(a),z),(cx+r*math.cos(b),cy+r*math.sin(b),z),.07,.09,c,m)
def caisson(n,x,y,r,rise):
 z=5.65
 ring(n+'_下八角井',x,y,z,r+ .23,8)
 ring(n+'_上八角井',x,y,z+.25,r+.09,8)
 for k in range(8):
  a=k*math.tau/8;px=x+(r+.20)*math.cos(a);py=y+(r+.20)*math.sin(a)
  gong(n+'_井口栱',.48,(px,py,z-.15),a+math.pi/2,ceil);box(n+'_井口斗',(px,py,z-.01),(.15,.15,.13),ceil,gold)
 for j in range(9):
  t=j/9*math.pi/2;ring(n+'_穹窿环',x,y,z+.3+rise*math.sin(t),max(.07,r*math.cos(t)),32)
 for k in range(16):
  a=k*math.tau/16
  for j in range(12):
   t=j/12*math.pi/2;tt=(j+1)/12*math.pi/2
   beam(n+'_弯椽',(x+r*math.cos(t)*math.cos(a),y+r*math.cos(t)*math.sin(a),z+.3+rise*math.sin(t)),(x+r*math.cos(tt)*math.cos(a),y+r*math.cos(tt)*math.sin(a),z+.3+rise*math.sin(tt)),.045,.055,ceil,gold)
 cylinder(n+'_顶心',(x,y,z+.3+rise-.04),(x,y,z+.3+rise+.08),.10,ceil,gold,'文档image7；照片7',24)
for name,x,r,h in [('当心间大藻井',0,.921,.898),('西次间小藻井',-3.56,.6295,.766),('东次间小藻井',3.56,.6295,.766)]:caisson(name,x,-4.62,r,h)
for x in [-1.93,1.93]:
 for y in [-5.87,-3.37]:beam('平棊边框',(x-.72,y,5.65),(x+.72,y,5.65),.12,.15,ceil,gold)
 for xx in [x-.72,x+.72]:beam('平棊边框',(xx,-5.87,5.65),(xx,-3.37,5.65),.12,.15,ceil,gold)
 for k in range(9):beam('平棊格栅',(x-.65+k*.16,-5.8,5.66),(x-.65+k*.16,-3.44,5.66),.035,.045,ceil,gold)
 for k in range(15):beam('平棊格栅',(x-.65,-5.8+k*.16,5.68),(x+.65,-5.8+k*.16,5.68),.035,.045,ceil,gold)
for x in [-4.82,4.82]:beam('藻井横列边框',(x,-5.87,5.60),(x,-3.37,5.60),.13,.18,ceil)
for y in [-5.87,-3.37]:beam('藻井横列通枋',(-4.82,y,5.60),(4.82,y,5.60),.13,.18,ceil)
for p in sorted((ROOT/'research/baoguosi_ model').glob('*.jpg'))+sorted((O/'references').glob('image*.png')):
 im=bpy.data.images.load(str(p),check_existing=True);im.pack();im.use_fake_user=True
refs.hide_render=True;refs.hide_viewport=True
S['坐标']='X沿面阔；-Y南/前檐；+Y北/后檐；Z向上'
S['资料范围']='仅依据用户指定 baoguosi_ model 文件夹：9照片+文档12插图。'
S['尺寸等级']='标注优先：槫高和藻井尺寸；柱网、层高、构件断面按图推定；非测绘复原。'
S['待核']='外围瓜棱类型逐柱差异、侧脚、生起、节点暗榫、各铺作精细差异、椽架转角搭接；本版不作结构验算。'
notes='''保国寺大殿内部结构 V01
严格以 research/baoguosi_ model 内9张照片、DOCX内12张插图为形态依据。原图已打包，可在图像编辑器中选择。
坐标：-Y南前檐，+Y北后檐，X面阔；地坪Z=0。
尺寸：内柱横距5.64m、槫中标高6.645/7.365/8.284/9.882/10.689m取自文档image8；大藻井口1.842m，小藻井口1.259m，穹窿高度按image7标注。
柱网X=-5.90/-2.82/2.82/5.90，Y=-6.97/-2.24/3.79/6.97，由image4比例推算，存在图像和制图误差；未沿用项目旧文档的总体尺寸。
前廊三藻井+两平棊；佛坛和露明梁架依照片3与image4/image10定位。照片9用于复核平面构架；照片4用于内槽层次，照片6用于外槽形态。
本版为可编辑图像重建：柱高、梁枋断面、铺作跳距、侧脚生起、隐藏节点、椽架转角仍待测绘校核；外围柱的全/半/四分之三瓜棱未逐柱细分。四内柱的拼合榫卯沿用上版展示解释几何，不代表新获得原物节点尺寸。
对象按构件独立、按构造分集合。隐藏05集合可直接观察内部梁架和藻井。相机包含总览、前廊内部、东侧正投影和俯视。
模型未加入清代外围副阶、屋瓦遮挡、佛像和装饰壁画；本次对象是照片所示宋构核心内部。
'''
bpy.data.texts.new('模型依据与待核项').write(notes);(O/'模型说明.txt').write_text(notes,encoding='utf-8')
(O/'构件清单.json').write_text(json.dumps([{'name':o.name,'collection':o.users_collection[0].name,'reference':o.get('参考依据','上版瓜棱柱示意')} for o in inventory],ensure_ascii=False,indent=2),encoding='utf-8')
snap('03_内部结构总览.png')
roof.hide_render=True
C.location=(17,-23,15);point(C,(0,-.3,4.4));C.data.ortho_scale=22;snap('04_去椽架观察内部.png')
view=cam('前廊内部_仰视',(0,-11,2.2),(0,-1.2,6.4),15);view.data.type='PERSP';view.data.lens=22;snap('05_前廊藻井仰视.png')
side=cam('东侧正投影',(25,0,5.3),(0,0,5.3),19);snap('06_东侧梁架.png')
top=cam('柱网俯视',(0,0,30),(0,0,0),21)
roof.hide_render=False;S.camera=C;C.location=(22,-28,20);point(C,(0,0,4));C.data.ortho_scale=24
save_view();bpy.ops.wm.save_as_mainfile(filepath=str(O/'保国寺大殿_内部结构_v01.blend'))
issues=[]
for ob in inventory:
 if ob.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(ob.data)
 if any(not e.is_manifold for e in bm.edges):issues.append(ob.name)
 bm.free()
(O/'validation.json').write_text(json.dumps({'objects':len(inventory),'non_manifold':issues,'packed_references':sum(bool(i.packed_file) for i in bpy.data.images),'reference_only_reconstruction':True},ensure_ascii=False,indent=2),encoding='utf-8')
print('READY',len(inventory),len(issues))
