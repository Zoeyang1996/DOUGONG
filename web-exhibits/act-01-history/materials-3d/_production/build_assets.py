import bpy, math, json, random, bmesh, struct, traceback
from mathutils import Vector
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
TEXT=BASE.parent/'materials-text-image'
ROOT=BASE.parents[2]
TEXTURES=BASE/'shared';TEXTURES.mkdir(exist_ok=True)
SPECS={
 'G1':('榫卯初见','G1_榫卯初见','原理示意',['S01'], '通用方榫与通卯；不是河姆渡梁头榫的器物复原。'),
 'G2':('走入生活','G2_走入生活','原理示意',['S01'], '顶开口燕尾节点与木销的教学构型，不指认某遗址已有这种完整组合。'),
 'G3':('斗拱之始','G3_斗拱之始','原理示意',['S04'], '一斗、横栱、两只小斗和短枋；不复原陶楼熊形栱，也不定名汉代一斗二升标准制度。'),
 'G4':('唐代铺作','G4_唐代铺作','形制示意',['S06','S13'], '以佛光寺研究为背景的简化出跳示意，非佛光寺测绘复原。粗壮栱材、长昂与横向枋表达空间关系。'),
 'G5':('保国寺宋构','G5_保国寺宋构','保国寺实例·待核',['L01','L02','S14'], '以保国寺前檐柱头铺作为目标；双杪双下昂与第一外跳偷心，瓜瓣栌斗为轮廓近似。尺寸、横栱层位、昂尾连接待核。'),
 'G6':('清式斗科','G6_清式斗科','形制示意',['S05','S12'], '单翘单昂五踩的教学简化，使用短昂嘴与水平昂身。不是太和殿某檐层平身科的测绘模型；保留素木以便比较。'),
 'K1':('斗','K_部件识名','术语示意',['S12'],'用大斗演示底部承托，不等于全部斗类。'),
 'K2':('拱（栱）','K_部件识名','术语示意',['S12'],'沿面宽方向横置的弓形构件示例。'),
 'K3':('升','K_部件识名','术语示意',['S12'],'清式三才升示例；属斗形构件，位于横栱端部。'),
 'K4':('昂','K_部件识名','术语示意',['S11','S12'],'斜昂轮廓示例；不把各时代所有昂一律解释成同样的杠杆。'),
 'K5':('翘','K_部件识名','术语示意',['S12'],'清式术语示例，朝出檐方向伸出，与横栱垂直；宋式对应华栱须按具体语境讲。')}

def make_texture():
 # Original seamless grain synthesized in Blender, saved as a reusable 1024 PNG.
 random.seed(41);N=1024
 im=bpy.data.images.new('wood_grain_original',width=N,height=N)
 pix=[]
 for y in range(N):
  for x in range(N):
   t=y/N;u=x/N
   grain=math.sin(2*math.pi*(t*39+.23*math.sin(2*math.pi*u*2)+.10*math.sin(2*math.pi*u*5)))
   fine=math.sin(2*math.pi*(t*131+.15*math.sin(2*math.pi*u*3)))
   f=.5+.11*grain+.035*fine+random.uniform(-.018,.018)
   pix.extend((.43+f*.22,.25+f*.16,.12+f*.11,1))
 im.pixels.foreach_set(pix);im.filepath_raw=str(TEXTURES/'wood_basecolor_1024.png');im.file_format='PNG';im.save();bpy.data.images.remove(im)

if not (TEXTURES/'wood_basecolor_1024.png').exists():make_texture()

def reset(key):
 global sc,asset,studio,parts,steps,mat,KEY
 KEY=key;bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene;sc.name=key+'_'+SPECS[key][0]
 sc.unit_settings.system='METRIC';sc['asset_type']=SPECS[key][2];sc['review_status']='待用户审稿；历史形制未完成专家校核'
 asset=bpy.data.collections.new('ASSET_'+key);studio=bpy.data.collections.new('STUDIO')
 sc.collection.children.link(asset);sc.collection.children.link(studio);parts=[];steps={}
 mat=bpy.data.materials.new('WOOD_SHARED_v1');mat.use_nodes=True;mat.diffuse_color=(.48,.28,.14,1)
 n=mat.node_tree.nodes;l=mat.node_tree.links;p=n.get('Principled BSDF');p.inputs['Roughness'].default_value=.56
 im=bpy.data.images.load(str(TEXTURES/'wood_basecolor_1024.png'));im.pack();tex=n.new('ShaderNodeTexImage');tex.image=im
 l.new(tex.outputs['Color'],p.inputs['Base Color'])
 def step(num,label,depends=[]):steps[num]={'label':label,'depends_on':depends}
 globals()['step']=step

def move(o,c):
 for old in list(o.users_collection):old.objects.unlink(o)
 c.objects.link(o)

def reg(o,cn,event,cat):
 o.name=f'{KEY.lower()}_{cat}_{len(parts)+1:02d}';move(o,asset);o.data.materials.clear();o.data.materials.append(mat)
 o['id']=o.name;o['name_cn']=cn;o['group']=KEY;o['order']=event;o['asset_type']=SPECS[KEY][2];o['status']='待核';o['source']=';'.join(SPECS[KEY][3])
 be=o.modifiers.new('小倒角','BEVEL');be.width=.006;be.segments=3
 o.modifiers.new('面法线','WEIGHTED_NORMAL');parts.append(o);return o

def uvmap(o):
 me=o.data;uv=me.uv_layers.new(name='WoodUV') if not me.uv_layers else me.uv_layers[0]
 while len(me.uv_layers)>1:me.uv_layers.remove(me.uv_layers[-1])
 uv.name='WoodUV';me.uv_layers.active_index=0;uv.active_render=True
 # Direction follows local timber longitudinal X for shaped timbers.
 for p in me.polygons:
  axis=max(range(3),key=lambda i:abs(p.normal[i]))
  for li in p.loop_indices:
   v=me.vertices[me.loops[li].vertex_index].co
   a,b=(v.x,v.z) if axis==1 else ((v.x,v.y) if axis==2 else (v.y,v.z))
   uv.data[li].uv=(a*.48,b*.48)

def mesh(cn,verts,faces,event,cat):
 me=bpy.data.meshes.new(cn);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(cn,me);sc.collection.objects.link(o)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free();uvmap(o)
 return reg(o,cn,event,cat)

def box(cn,loc,size,e,cat='timber'):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);uvmap(o);return reg(o,cn,e,cat)

def profile(cn,pts,width,loc,e,cat='gong',axis='X'):
 n=len(pts);verts=[(x,w*width/2,z) for w in [-1,1] for x,z in pts];faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 o=mesh(cn,verts,faces,e,cat);o.location=loc
 if axis=='Y':o.rotation_euler.z=math.pi/2
 return o

def gong(cn,L,loc,e,axis='X',h=.18,w=.12,style='song'):
 half=L/2
 # Smooth-cut underside, firm bearing ledges; different tips for Qing.
 tail=.91 if style=='qing' else .84
 pts=[(-half,h),(half,h),(half,.64*h),(half*tail,.64*h),(half*.77,.40*h),(half*.62,.18*h),(half*.35,0),(-half*.35,0),(-half*.62,.18*h),(-half*.77,.40*h),(-half*tail,.64*h),(-half,.64*h)]
 return profile(cn,pts,w,loc,e,'gong',axis)

def cut(o,cutter):
 bpy.context.view_layer.objects.active=o
 m=o.modifiers.new('可见承口','BOOLEAN');m.object=cutter;m.operation='DIFFERENCE'
 while list(o.modifiers).index(m)>0:bpy.ops.object.modifier_move_up(modifier=m.name)
 bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(cutter,do_unlink=True);uvmap(o)

def cutter_box(loc,sz):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=sz;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return o

def dou(cn,loc,e,w=.24,h=.14,cross=False,lobed=False,slot=.125):
 if lobed:
  N=64;rings=[(.72,0),(1,h*.45),(1,h)]
  verts=[((w/2+.025*math.cos(8*2*math.pi*i/N))*r*math.cos(2*math.pi*i/N),(w/2+.025*math.cos(8*2*math.pi*i/N))*r*math.sin(2*math.pi*i/N),z) for r,z in rings for i in range(N)]
 else:
  N=4;verts=[(x*s*w/2,y*s*w/2,z) for s,z in [(.68,0),(1,h*.4),(1,h)] for x,y in [(-1,-1),(1,-1),(1,1),(-1,1)]]
 faces=[tuple(reversed(range(N))),tuple(range(2*N,3*N))]+[(r*N+i,r*N+(i+1)%N,(r+1)*N+(i+1)%N,(r+1)*N+i) for r in range(2) for i in range(N)]
 o=mesh(cn,verts,faces,e,'dou');o.location=loc;x,y,z=loc;depth=min(.045,h*.32)
 for axis in (['X','Y'] if cross else ['X']):
  sz=(w*1.5,slot,depth*2) if axis=='X' else (slot,w*1.5,depth*2)
  cut(o,cutter_box((x,y,z+h),sz))
 return o

def cylinder(cn,loc,r,depth,e,axis='Z',lobed=False):
 N=64;v=[]
 for z in [-depth/2,depth/2]:
  for i in range(N):
   a=2*math.pi*i/N;rr=r*(1+.065*math.cos(8*a)) if lobed else r;v.append((rr*math.cos(a),rr*math.sin(a),z))
 f=[tuple(reversed(range(N))),tuple(range(N,2*N))]+[(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)]
 o=mesh(cn,v,f,e,'column' if axis=='Z' else 'beam');o.location=loc
 uv=o.data.uv_layers[0]
 for face in o.data.polygons:
  if abs(face.normal.z)<.5:
   for li in face.loop_indices:
    co=o.data.vertices[o.data.loops[li].vertex_index].co
    uv.data[li].uv=(co.z*.48,math.atan2(co.y,co.x)/math.tau*.8)

 if axis=='X':o.rotation_euler.y=math.pi/2
 return o

def ang(cn,head,tail,z,e,width=.13,slope=.40,qing=False):
 if qing:pts=[(head-.13,z-.11),(head-.08,z+.09),(tail,z+.09),(tail,z-.08),(head+.14,z-.08)]
 else:pts=[(head-.14,z-.07),(head-.05,z+.14),(tail,z+.14+(tail-head)*slope),(tail,z-.04+(tail-head)*slope),(head+.16,z-.035)]
 return profile(cn,pts,width,(0,0,0),e,'ang','Y')

# G1 and G2 contain visible, actually cut sockets, with feasible insertion axes.
def g1():
 step(1,'卯件就位');step(2,'榫件沿轴向插合',[1])
 a=box('卯件',(0,0,0),(.55,.72,.62),1,'mortise')
 cut(a,cutter_box((0,0,0),(.8,.245,.245)))
 rings=[(-.25,.11,.11),(.30,.11,.11),(.30,.24,.26),(1.10,.24,.26)]
 verts=[(x,sy*y,sz*z) for x,y,z in rings for sy,sz in [(-1,-1),(1,-1),(1,1),(-1,1)]]
 faces=[(3,2,1,0),(12,13,14,15)]+[(r*4+i,r*4+(i+1)%4,(r+1)*4+(i+1)%4,(r+1)*4+i) for r in range(3) for i in range(4)]
 b=mesh('榫件_整木凸榫与肩部',verts,faces,2,'tenon')
 b['insertion_axis']='-X';b['offset_override']=[1.0,0,0]

def g2():
 step(1,'柱件就位');step(2,'梁头从顶开口下落插合',[1]);step(3,'木销从上方插入',[2]);step(4,'楼板示意件落位',[2,3])
 col=box('柱件_顶开口燕尾卯',(0,0,0),(.55,.55,1.7),1,'post')
 # Dovetail socket in XY, open at the top; counterpart slides vertically.
 poly=[(.08,-.17),(.31,-.10),(.31,.10),(.08,.17)]
 verts=[(x,y,z) for z in [.40,.90] for x,y in poly];faces=[(3,2,1,0),(4,5,6,7)]+[(i,(i+1)%4,(i+1)%4+4,i+4) for i in range(4)]
 me=bpy.data.meshes.new('socket');me.from_pydata(verts,[],faces);me.update();c=bpy.data.objects.new('socket',me);sc.collection.objects.link(c);cut(col,c)
 beam=box('梁件_燕尾榫头',(.77,0,.60),(1.0,.24,.38),2,'beam')
 verts=[(x,y,z) for z in [.415,.785] for x,y in [( .09,-.162),(.32,-.094),(.32,.094),(.09,.162)]]
 me=bpy.data.meshes.new('tongue');me.from_pydata(verts,[],faces);me.update();c=bpy.data.objects.new('tongue',me);sc.collection.objects.link(c)
 bpy.context.view_layer.objects.active=beam;m=beam.modifiers.new('燕尾榫连为整木','BOOLEAN');m.operation='UNION';m.object=c;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(c,do_unlink=True);uvmap(beam)
 bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.035,depth=.55,location=(.19,0,.68));cut(col,bpy.context.object)
 bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.035,depth=.55,location=(.19,0,.68));cut(beam,bpy.context.object)
 cylinder('木销',(.19,0,.66),.030,.43,3)
 box('楼板局部_空间示意',(.85,0,.83),(.65,.72,.07),4,'board')

def g3():
 for n,label in [(1,'大斗'),(2,'横栱'),(3,'两端小斗'),(4,'短枋')]:step(n,label,[n-1] if n>1 else [])
 dou('大斗',(0,0,0),1,w=.42,h=.23,slot=.17)
 gong('横栱',1.25,(0,0,.19),2,h=.20,w=.16)
 for x in [-.48,.48]:dou('两端小斗',(x,0,.36),3,w=.24,h=.16,slot=.17)
 box('短枋',(0,0,.55),(1.50,.16,.15),4)

# Independently authored configurations: not a single mesh rescaled across eras.
def tang():
 step(1,'柱头承托');step(2,'第一层栱',[1]);step(3,'第一跳承斗',[2]);step(4,'第二杪与横栱',[3]);step(5,'第二跳承斗',[4]);step(6,'第一下昂',[5]);step(7,'昂头承托',[6]);step(8,'第二下昂',[7]);step(9,'上层横栱与承斗',[8]);step(10,'联系枋与槫局部',[9])
 cylinder('柱头局部',(0,0,-.45),.30,.90,1);dou('大斗',(0,0,0),1,w=.60,h=.30,cross=True,slot=.19)
 gong('第一华栱',1.30,(0,0,.25),2,'Y',h=.27,w=.18);gong('泥道栱',1.12,(0,0,.25),2,h=.27,w=.18)
 for y in [-.46,0,.46]:dou('第一层承斗',(0,y,.49),3,w=.29,h=.18,cross=True,slot=.19)
 gong('第二华栱',2.20,(0,0,.63),4,'Y',h=.27,w=.18);gong('柱心横栱',1.55,(0,0,.63),4,h=.27,w=.18)
 for y in [-.92,0,.92]:dou('第二层承斗',(0,y,.87),5,w=.29,h=.18,cross=True,slot=.19)
 ang('第一下昂_批竹轮廓示意',-1.38,1.62,1.14,6,width=.19,slope=21/47)
 for y in [-.92,0,.92]:gong('横向承栱',1.18,(0,y,1.01),6,h=.25,w=.18)
 dou('第一昂头承斗',(0,-1.38,1.24),7,w=.29,h=.18,cross=True,slot=.19)
 ang('第二下昂_长尾',-1.84,1.86,1.48,8,width=.195,slope=21/47)
 dou('第二昂头承斗',(0,-1.84,1.58),9,w=.29,h=.18,cross=True,slot=.19)
 for y,z in [(-1.84,1.73),(0,1.73),(.92,1.73)]:
  gong('上层承栱',1.20,(0,y,z),9,h=.25,w=.18)
  for x in [-.45,.45]:dou('上层小斗',(x,y,z+.23),9,w=.26,h=.17,slot=.19)
  box('横向联系枋_截段',(0,y,z+.46),(2.1,.18,.20),10)
 cylinder('檐槫_局部',(0,-1.84,2.42),.13,2.25,10,axis='X')

def song():
 for n,label in [(1,'瓜棱柱头与八瓣栌斗'),(2,'泥道栱与第一杪'),(3,'第一跳承斗_不设外跳横栱'),(4,'第二杪与柱心横栱'),(5,'第二跳承斗'),(6,'第一下昂与横栱'),(7,'上承小斗'),(8,'第二下昂与横栱'),(9,'第二昂头及横栱端承斗'),(10,'耍头与令栱'),(11,'上承小斗'),(12,'枋槫局部')]:step(n,label,[n-1] if n>1 else [])
 cylinder('瓜棱柱头',(0,0,-.40),.26,.80,1,lobed=True);dou('八瓣栌斗_轮廓近似',(0,0,0),1,w=.53,h=.27,cross=True,lobed=True,slot=.14)
 gong('泥道栱',.88,(0,0,.225),2);gong('第一杪华栱',.94,(0,0,.225),2,'Y')
 for y in [-.35,0,.35]:dou('第一跳交互斗',(0,y,.385),3,cross=True)
 for x in [-.32,.32]:dou('泥道栱散斗',(x,0,.385),3)
 gong('第二杪华栱',1.64,(0,0,.49),4,'Y');gong('柱心慢栱',1.22,(0,0,.49),4)
 for y in [-.70,0,.70]:dou('第二跳交互斗',(0,y,.65),5,cross=True)
 ang('第一下昂_长尾',-1.05,1.80,.88,6,width=.14,slope=.35)
 for y in [-.70,0,.70]:gong('横向瓜子栱',.88,(0,y,.755),6)
 for y in [-.70,0,.70]:
  for x in [-.32,.32]:dou('横栱端散斗',(x,y,.915),7)
 dou('第一昂头承斗',(0,-1.05,.99),7,cross=True)
 ang('第二下昂_长尾',-1.40,2.00,1.15,8,width=.145,slope=.35)
 for y in [-1.05,-.70,0,.70]:gong('横向慢栱',1.16,(0,y,1.02),8)
 for y in [-1.05,-.70,0,.70]:
  for x in [-.44,.44]:dou('上层散斗',(x,y,1.18),9)
 dou('第二昂头承斗',(0,-1.40,1.26),9,cross=True)
 profile('耍头_轮廓示意',[(-1.58,0),(-1.53,.16),(.75,.16),(.75,0),(-1.32,0),(-1.45,-.05)],.165,(0,0,1.37),10,'shuatou','Y')
 for y in [-1.40,0,.70]:
  gong('令栱_上层承托',.94,(0,y,1.37),10)
  for x in [-.35,.35]:dou('上承散斗',(x,y,1.53),11)
  box('承托枋_局部',(0,y,1.72),(1.65,.13,.16),12)
 cylinder('撩檐槫_局部',(0,-1.40,1.90),.105,1.80,12,axis='X')

def qing():
 for n,label in [(1,'平板枋与坐斗'),(2,'头翘与正心瓜栱'),(3,'十八斗及升'),(4,'头昂与正心万栱'),(5,'昂头十八斗'),(6,'厢栱与三才升'),(7,'蚂蚱头与挑檐枋'),(8,'挑檐桁局部')]:step(n,label,[n-1] if n>1 else [])
 box('平板枋_柱间截段',(0,0,-.12),(1.80,.35,.24),1);dou('坐斗',(0,0,0),1,w=.38,h=.20,cross=True,slot=.105)
 gong('头翘',.86,(0,0,.16),2,'Y',h=.15,w=.095,style='qing');gong('正心瓜栱',.72,(0,0,.16),2,h=.15,w=.095,style='qing')
 for y in [-.30,0,.30]:dou('十八斗',(0,y,.29),3,w=.18,h=.115,cross=True,slot=.10)
 for x in [-.27,.27]:dou('槽升',(x,0,.29),3,w=.15,h=.115,slot=.10)
 ang('头昂_水平昂身与下垂昂嘴',-.60,.64,.43,4,width=.10,qing=True)
 gong('正心万栱',1.00,(0,0,.375),4,h=.15,w=.095,style='qing')
 for y in [-.60,.60]:dou('昂头十八斗',(0,y,.50),5,w=.18,h=.115,cross=True,slot=.10)
 for y in [-.60,.60]:
  gong('厢栱',.84,(0,y,.58),6,h=.15,w=.095,style='qing')
  for x in [-.31,.31]:dou('三才升',(x,y,.71),6,w=.15,h=.115,slot=.10)
 profile('蚂蚱头_简化',[(-.78,0),(-.70,.13),(.70,.13),(.78,.02),(.61,0),(-.61,0)],.115,(0,0,.61),7,'head','Y')
 for y in [-.60,0,.60]:box('挑檐枋或正心枋_截段',(0,y,.88),(1.35,.10,.13),7)
 cylinder('挑檐桁_局部',(0,-.60,1.04),.09,1.45,8,axis='X')

def term(key):
 step(1,SPECS[key][0]+'独立观察')
 if key=='K1':dou('斗_大斗示例',(0,0,0),1,w=.60,h=.32,cross=True,slot=.18)
 elif key=='K2':gong('拱_横向栱示例',1.30,(0,0,0),1,h=.25,w=.18)
 elif key=='K3':dou('升_三才升示例',(0,0,0),1,w=.30,h=.20,slot=.13)
 elif key=='K4':ang('昂_斜昂示意',-.65,.85,.0,1,width=.18,slope=.40)
 elif key=='K5':gong('翘_向檐外出挑',1.30,(0,0,0),1,'Y',h=.25,w=.18,style='qing')

BUILD={'G1':g1,'G2':g2,'G3':g3,'G4':tang,'G5':song,'G6':qing}

def setup_scene():
 # All models are recentered at a shared display origin with the exact same camera.
 bpy.context.view_layer.update()
 points=[o.matrix_world@Vector(v) for o in parts for v in o.bound_box]
 mn=Vector([min(p[i] for p in points) for i in range(3)]);mx=Vector([max(p[i] for p in points) for i in range(3)]);center=(mn+mx)/2
 physical_extent=list(mx-mn);scale=3.15/max(mx-mn)
 for o in parts:
  # Bake world placement to mesh, then give each part its own centroid/pivot.
  world=o.matrix_world.copy()
  for v in o.data.vertices:v.co=(world@v.co-center)*scale
  o.matrix_world.identity()
  mid=sum((v.co for v in o.data.vertices),Vector())/len(o.data.vertices)
  for v in o.data.vertices:v.co-=mid
  o.location=mid
  for m in o.modifiers:
   if m.type=='BEVEL':m.width*=scale
  o['display_scale']=scale
 sc['presentation']='轮廓归一，非同比例；单位米为工作单位，不代表实测尺寸'
 sc['source_extent_m']=physical_extent
 root=bpy.data.objects.new(KEY+'_ROOT',None);asset.objects.link(root);root['asset_type']=SPECS[KEY][2];root['note']=SPECS[KEY][4]
 for o in parts:o.parent=root
 # Exact fixed camera and paper studio, no decorative plinth.
 world=bpy.data.worlds.new('Paper Studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.80,.76,.66,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45;sc.world=world
 camd=bpy.data.cameras.new('FixedCamera');cam=bpy.data.objects.new('FixedCamera',camd);studio.objects.link(cam);cam.location=(6,-8,5);cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();camd.type='ORTHO';camd.ortho_scale=5.3;sc.camera=cam
 for name,loc,power,size in [('Key',(1,-4,7),850,5),('Fill',(-4,-2,3),500,5),('Rim',(2,5,4),700,4)]:
  ld=bpy.data.lights.new(name,'AREA');lo=bpy.data.objects.new(name,ld);studio.objects.link(lo);lo.location=loc;lo.rotation_euler=(-lo.location).to_track_quat('-Z','Y').to_euler();ld.energy=power;ld.size=size
 sc.render.engine='CYCLES';sc.cycles.samples=24;sc.cycles.use_denoising=True;sc.render.resolution_x=1280;sc.render.resolution_y=1120;sc.render.resolution_percentage=100;sc.render.film_transparent=False;sc.render.image_settings.file_format='PNG';sc.view_settings.view_transform='AgX'
 return root,scale

def export(key):
 out=BASE/(key+'_'+SPECS[key][0].replace('（','').replace('）',''));out.mkdir(exist_ok=True)
 root,scale=setup_scene();meta=[];random.seed(12)
 for o in parts:
  p=o.location.copy();q=o.rotation_quaternion.copy() if o.rotation_mode=='QUATERNION' else o.rotation_euler.to_quaternion()
  off=Vector((random.uniform(-.45,.45),random.uniform(-.2,.2),1.2+.04*o['order']))
  if key=='G1':off=Vector((.75,0,0)) if o['order']==2 else Vector((-.75,0,0))
  elif key=='G2':off=Vector((0,0,.85)) if o['order']>1 else Vector((0,0,-.50))
  # All serialized positions use glTF / web Y-up, quaternion XYZW.
  toweb=lambda v:[round(v[0],6),round(v[2],6),round(-v[1],6)]
  meta.append({'id':o.name,'name_cn':o['name_cn'],'group':key,'order':o['order'],'assembly_event':steps[o['order']]['label'],'depends_on':steps[o['order']]['depends_on'],'appear':{'offset':toweb(off),'rot':[0,0,0]},'target':{'pos':toweb(p),'quat':[0,0,0,1]},'type':SPECS[key][2],'source':SPECS[key][3],'status':'待核','note':SPECS[key][4]})
  o['appear_offset_web']=toweb(off);o['target_pos_web']=toweb(p);o['target_quat_web']=[0,0,0,1]
  o.keyframe_insert(data_path='location',frame=1);o.location=p+off*(1 if key in ['G1','G2'] else .55);o.keyframe_insert(data_path='location',frame=80);o.location=p;o.keyframe_insert(data_path='location',frame=140)
 sc.frame_end=140;sc.frame_set(1)
 for f,label in [(1,'组合审核'),(80,'分离观察_非施工顺序'),(140,'回到组合')]:sc.timeline_markers.new(label,frame=f)
 data={'schema_version':1,'id':key,'title':SPECS[key][0],'asset_type':SPECS[key][2],'status':'待核','coordinates':'glTF Y-up; Blender Z-up; conversion [x,z,-y]','presentation':'轮廓归一，非同比例','display_scale':scale,'parts_count':len(parts),'assembly_events':len(steps),'events':steps,'parts':meta,'notes':[SPECS[key][4],'order是教学落位顺序草案，非已经校核的历史施工顺序；专家核校前禁止称真实施工动画。','根节点原点为中心；模型底部不强制为0。后续退场只移动ROOT。']}
 (out/'assembly.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
 bm_errors=[]
 for o in parts:
  bm=bmesh.new();bm.from_mesh(o.data)
  if any(not e.is_manifold for e in bm.edges):bm_errors.append(o.name)
  bm.free()
 bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0]
 export_args=dict(filepath=str(out/(key+'.glb')),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_extras=True,export_materials='EXPORT',export_yup=True)
 try:bpy.ops.export_scene.gltf(**export_args,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6)
 except Exception as e:
  (out/'compression-note.txt').write_text(str(e));bpy.ops.export_scene.gltf(**export_args)
 bpy.ops.object.select_all(action='DESELECT')
 # Clean modelling view when the saved file is opened.
 for screen in bpy.data.screens:
  for area in screen.areas:
   if area.type=='VIEW_3D':
    s=area.spaces.active;s.region_3d.view_rotation=sc.camera.rotation_euler.to_quaternion();s.region_3d.view_distance=6;s.region_3d.view_location=(0,0,0);s.region_3d.view_perspective='ORTHO';s.shading.color_type='MATERIAL';s.shading.show_cavity=True;s.overlay.show_floor=False
 for o in studio.objects:o.hide_set(True)
 bpy.data.texts.new('README_素材审核').write(json.dumps(data,ensure_ascii=False,indent=2))
 sc.render.filepath=str(out/'render.png');bpy.ops.wm.save_as_mainfile(filepath=str(out/(key+'.blend')));bpy.ops.render.render(write_still=True)
 if key.startswith('G'):
  sc.frame_set(80);sc.render.filepath=str(out/'exploded.png');bpy.ops.render.render(write_still=True);sc.frame_set(1)
 status={'id':key,'mesh_count':len(parts),'non_manifold_base_meshes':bm_errors,'glb_bytes':(out/(key+'.glb')).stat().st_size,'shared_materials':1,'image_size':[1024,1024],'historical_status':'待核','render':'render.png'}
 (out/'validation.json').write_text(json.dumps(status,ensure_ascii=False,indent=2))
 # Copy original rendered evidence-free image into each story folder.
 import shutil
 dest=TEXT/SPECS[key][1]/'renders';dest.mkdir(exist_ok=True)
 shutil.copy2(out/'render.png',dest/(key+'_模型渲染.png'))
 return {'id':key,'folder':str(out.relative_to(BASE)),**status}

results=[]
for key in SPECS:
 try:
  reset(key)
  if key.startswith('K'):term(key)
  else:BUILD[key]()
  results.append(export(key))
  (BASE/'build-progress.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
  print('ASSET_DONE',key,flush=True)
 except Exception:
  (BASE/(key+'_ERROR.txt')).write_text(traceback.format_exc());raise
(BASE/'asset-index.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print('ALL_ASSETS_COMPLETE',flush=True)
