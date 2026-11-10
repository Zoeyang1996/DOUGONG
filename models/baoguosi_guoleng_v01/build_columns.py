import bpy, math, json, bmesh
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parent
R=O.parent.parent
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
S=bpy.context.scene;S.name='01_四根内柱_组合与展开'
parts=[]
def mat(name,col):
 m=bpy.data.materials.new(name);m.diffuse_color=(*col,1);m.use_nodes=True
 n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');p.inputs['Roughness'].default_value=.65
 t=n.new('ShaderNodeTexNoise');t.inputs['Scale'].default_value=5
 c=n.new('ShaderNodeTexCoord');v=n.new('ShaderNodeVectorMath');v.operation='MULTIPLY';v.inputs[1].default_value=(9,9,.45)
 l.new(c.outputs['Generated'],v.inputs[0]);l.new(v.outputs[0],t.inputs['Vector'])
 ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*(x*.6 for x in col),1);ramp.color_ramp.elements[1].color=(*(min(1,x*1.25) for x in col),1)
 l.new(t.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color']);return m
wood=mat('主拼木_暖木色',(.36,.16,.065));cover=mat('补缝瓜瓣_浅木色',(.55,.30,.13));keymat=mat('暗榫_深色硬木',(.20,.075,.025));stone=mat('展示底座_非复原柱础',(.22,.24,.25))
def coll(name):
 c=bpy.data.collections.new(name);S.collection.children.link(c);return c
def mesh(name,poly,z0,z1,c,material):
 n=len(poly);verts=[(x,y,z) for z in [z0,z1] for x,y in poly]
 faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new(name,me);c.objects.link(ob);ob.data.materials.append(material);return ob
def clip(poly,fun):
 out=[]
 for p,q in zip(poly,poly[1:]+poly[:1]):
  a,b=fun(p),fun(q)
  if a>=0:out.append(p)
  if (a>=0)!=(b>=0):
   t=a/(a-b);out.append((p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])))
 return out
def rotate(p,a):return (p[0]*math.cos(a)-p[1]*math.sin(a),p[0]*math.sin(a)+p[1]*math.cos(a))
def finish(ob,role,vec,origin):
 ob['构件类型']=role;ob['尺寸依据']='工作尺寸，待测绘';ob['节点依据']='展品照片形态示意；暗榫层数和深度待核'
 mod=ob.modifiers.new('边缘微倒角','BEVEL');mod.width=.001;mod.segments=2
 ob.modifiers.new('加权法线','WEIGHTED_NORMAL')
 ob.location=origin;ob.keyframe_insert(data_path='location',frame=1)
 ob.location=Vector(origin)+Vector(vec);ob.keyframe_insert(data_path='location',frame=90)
 ob.location=origin;ob.keyframe_insert(data_path='location',frame=160);parts.append(ob)
def column(tag,origin,h,levels):
 c=coll(tag);logs=[]
 poly=[(.12+.18*math.cos(i*math.tau/128),.12+.18*math.sin(i*math.tau/128)) for i in range(128)]
 for f in [lambda p:p[0]-.001,lambda p:p[1]-.001,lambda p:p[0]+p[1]-.055]:poly=clip(poly,f)
 for k in range(4):
  a=k*math.pi/2;ob=mesh(tag+'_主拼木_'+str(k+1),[rotate(p,a) for p in poly],0,h,c,wood);logs.append(ob)
 # Four real recessed bow-tie sockets per tier, with separately editable keys.
 bow=[(-.08,-.036),(0,-.019),(.08,-.036),(.08,.036),(0,.019),(-.08,.036)]
 for j,z in enumerate(levels):
  for k in range(4):
   a=k*math.pi/2;pp=[rotate((x,y+.12),a) for x,y in bow]
   cutter=mesh('临时卯槽',pp,z-.035,z+.036,c,keymat)
   for ob in logs:
    bpy.context.view_layer.objects.active=ob
    mod=ob.modifiers.new('实切暗榫卯槽','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
    bpy.ops.object.modifier_apply(modifier=mod.name)
   bpy.data.objects.remove(cutter,do_unlink=True)
   pp=[rotate((x*.975,y*.975+.12),a) for x,y in bow]
   ob=mesh(tag+f'_暗榫_{j+1}_{k+1}',pp,z-.034,min(h,z+.034),c,keymat)
   dx,dy=rotate((0,.18),a);finish(ob,'双燕尾形暗榫（照片形态解释）',(dx,dy,.22),origin)
 for k,ob in enumerate(logs):
  dx,dy=rotate((.32,.32),k*math.pi/2);finish(ob,'修整接合面的主拼木',(dx,dy,0),origin)
 # Concave backs fit the two adjacent timbers; no intersecting full cylinders.
 ys=[-.09+i*.18/48 for i in range(49)]
 outer=[(.20+math.sqrt(.15**2-y*y),y) for y in ys]
 inner=[(.12+math.sqrt(.18**2-(abs(y)-.12)**2)+.0015,y) for y in reversed(ys)]
 for k in range(4):
  a=k*math.pi/2;ob=mesh(tag+'_补缝瓜瓣_'+str(k+1),[rotate(p,a) for p in outer+inner],0,h,c,cover)
  dx,dy=rotate((.68,0),a);finish(ob,'弧背补缝木条（固定方式待核）',(dx,dy,0),origin)
def camera(name,loc,target,scale):
 data=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,data);S.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=scale;S.camera=ob;return ob
def setup():
 S.unit_settings.system='METRIC';S.render.engine='CYCLES';S.cycles.samples=32
 S.render.resolution_x=1400;S.render.resolution_y=1100;S.render.resolution_percentage=100
 S.world=bpy.data.worlds.new(S.name);S.world.use_nodes=True;S.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.14,.17,1)
 S.world.node_tree.nodes['Background'].inputs[1].default_value=.5
 S.frame_end=160
 for frame,name in [(1,'组合'),(90,'拆解示意_非施工顺序'),(160,'复位')]:S.timeline_markers.new(name,frame=frame)
 for loc,power,size in [((1,-4,7),1600,5),((-4,-1,4),1100,4),((2,5,6),1900,3)]:
  d=bpy.data.lights.new('柔光','AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new('柔光',d);S.collection.objects.link(o);o.location=loc;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
 S['精度声明']='依据现场展品的构造研究模型；非测绘复原。四柱高度统一3.8m、外径约0.70m、柱距及榫层均为可改工作参数。'
def render(name):
 S.render.filepath=str(O/name);bpy.ops.render.render(write_still=True)
setup()
for tag,org in [('A_前左',(-1.3,-1.15,0)),('B_前右',(1.3,-1.15,0)),('C_后左',(-1.3,1.15,0)),('D_后右',(1.3,1.15,0))]:column(tag,org,3.8,[.40,1.35,2.30,3.25])
camera('四柱总览',(7,-10,7),(0,0,1.8),7.3);S.frame_set(1)
main=S
S=bpy.data.scenes.new('02_榫卯剖段_组合与展开');bpy.context.window.scene=S;setup();column('构造剖段',(0,0,0),.75,[.25,.75]);camera('节点特写',(1.4,-2,2.5),(0,0,.35),1.65);S.frame_set(1)
for fn in ['7e71f48e1i525dcfc8e646dc6b2e3cb8.jpg','中国南方最强木结构建筑，宁波保国寺_14_寻山探古universe_来自小红书网页版.jpg']:
 im=bpy.data.images.load(str(R/'research'/'保国寺实地调研照片'/fn));im.pack();im.use_fake_user=True
notes='''保国寺四根瓜棱内柱 / V01 构造研究模型
使用：场景01为四柱组；场景02为榫卯短剖段。帧1组合，90展开，160复位。
每柱：4主拼木+4弧背补条+16暗榫；剖段另有8暗榫。主木已实切卯槽。
照片明确：四木拼合、暗榫连接、木条补贴成瓜棱。蝴蝶形榫依据展品端面制作。
推定：榫厚、沿柱高的层数间距、微小配合余量；补条如何固定未得到可靠依据，未虚构附加榫钉。
四柱统一高3.8m、约0.70m外径，展示柱距2.6×2.3m，均非实测；A-D为展示编号，无实际柱位对应。
暂未复原侧脚、生起、收分、上下端梁枋/柱础节点；两端平切，不表示原物端部做法。短剖段为切开解释，原柱暗榫不外露。
照片展示模型并非全尺寸原柱。请勿把端面可见暗榫理解为柱头实际外露榫。
研究补充：陈勇平等《宁波保国寺大殿瓜棱柱内部构造初探》，林业科学2011，47(4):135–140。
https://html.rhhz.net/linyekexue/html/20110421.htm
该研究识别D4/D5/E4/E5为拼合柱，提示接合面经过修整；本文未对图10逐尺寸复原。
论文关于后期维修形成拼合柱的推断，与本地资料“宋代原始拼柱”的说法有分歧，本模型不作年代断言。
'''
(O/'模型说明.txt').write_text(notes,encoding='utf-8');bpy.data.texts.new('请先阅读_模型依据与操作').write(notes)
issues=[]
for ob in parts:
 bm=bmesh.new();bm.from_mesh(ob.data)
 if any(not e.is_manifold for e in bm.edges):issues.append(ob.name)
 bm.free()
(O/'validation.json').write_text(json.dumps({'components':len(parts),'non_manifold':issues,'packed_references':2,'full_columns':4,'historical_status':'schematic_not_survey'},ensure_ascii=False,indent=2),encoding='utf-8')
render('02_榫卯剖面.png');S.frame_set(90);S.camera.data.ortho_scale=2.9;render('03_榫卯展开.png');S.frame_set(1);S.camera.data.ortho_scale=1.65
S=main;bpy.context.window.scene=S;S.frame_set(1);render('01_四柱组合.png')
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   v=area.spaces.active;v.region_3d.view_distance=8;v.region_3d.view_location=(0,0,1.8);v.region_3d.view_rotation=S.camera.rotation_euler.to_quaternion();v.shading.color_type='MATERIAL';v.shading.show_cavity=True
bpy.ops.wm.save_as_mainfile(filepath=str(O/'保国寺四根瓜棱柱_v01.blend'))
print('MODEL_READY',len(parts),issues)

