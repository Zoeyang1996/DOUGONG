import bpy,bmesh,math,json,sys,random,hashlib,textwrap
from pathlib import Path
from mathutils import Vector,Matrix,Euler
sys.path.insert(0,str(Path(__file__).parent))
from curation import PANELS,SOURCES
ROOT=Path(__file__).resolve().parents[1];sc=bpy.context.scene;random.seed(26)
SOURCE=bpy.data.filepath
ZEN='/Users/yangzhe/Downloads/榫卯修改/国风室内场景/禅意木构室内场景.blend'
BRACKET='/Users/yangzhe/Desktop/浙江工商/DOUGONG/models/baoguosi_zhutou_v02_game/保国寺柱头铺作_v02_游戏搭接修正版.blend'
def rgba(h):
 a=[int(h[i:i+2],16)/255 for i in (1,3,5)]
 return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in a)+(1,)
def mat(name,color,rough=.7,metal=0,emit=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=rgba(color);bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal;m.diffuse_color=rgba(color)
 if emit:bs.inputs['Emission Color'].default_value=rgba(color);bs.inputs['Emission Strength'].default_value=emit
 return m
oak=bpy.data.materials['M01_烟熏橡木_PBR'];ink=bpy.data.materials['M06_墨色导视'];bronze=bpy.data.materials['M05_暗古铜收口']
paper=mat('V03_暖白展陈纸','#e7e0cd',.91)
muted=mat('V03_正文暖墨','#30382f',.95)
line_mat=mat('V03_图解墨绿','#465647',.78)
red=mat('V03_朱砂注记','#8c4936',.82)
woodflat=mat('V03_教学图浅木','#947147',.62)
linen=mat('V03_挂轴绫边','#8b8266',.92)
leafmat=mat('V03_枝叶墨绿','#354c37',.8)
branchmat=mat('V03_枝条深褐','#4f3c29',.8)
for m in [paper,linen]:
 n=m.node_tree.nodes;l=m.node_tree.links;bs=n.get('Principled BSDF');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=145;noise.inputs['Detail'].default_value=2
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.1;bump.inputs['Distance'].default_value=.006;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],bs.inputs['Normal'])
master=bpy.data.objects.get('Baoguosi_VR_Gallery_36x24m')
COLS={}
for key,name in [('panels','09_墙面展陈板与框架'),('diagrams','10_构造图解与壁挂模型'),('text','11_可编辑展陈文字'),('decor','12_角落书架与器物'),('lights','13_展陈壁灯与预览照明'),('photos','14_现场摄影图版')]:
 c=bpy.data.collections.new(name);sc.collection.children.link(c);COLS[key]=c
zones={}
def empty(name,col='panels',parent=None):
 o=bpy.data.objects.new(name,None);COLS[col].objects.link(o);o.parent=parent;o.empty_display_size=.2;return o
for i in range(1,9):zones[i]=empty(f'Exhibits_Zone{i:02}',parent=master)
def mesh(name,verts,faces,material,parent=None,col='diagrams'):
 me=bpy.data.meshes.new(name+'_Mesh');me.from_pydata(verts,[],faces);me.update()
 if material:me.materials.append(material)
 o=bpy.data.objects.new(name,me);COLS[col].objects.link(o);o.parent=parent;return o
def box(name,loc,dim,material,parent=None,col='panels',bevel=.004):
 bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
 for v in bm.verts:
  for k in range(3):v.co[k]*=dim[k]
 if bevel:bmesh.ops.bevel(bm,geom=list(bm.edges),offset=min(bevel,min(dim)*.2),segments=2,affect='EDGES')
 me=bpy.data.meshes.new(name+'_Mesh');bm.to_mesh(me);bm.free();me.materials.append(material)
 # Long-axis grain mapping for the retained real PBR wood material.
 uv=me.uv_layers.new(name='UVMap')
 for p in me.polygons:
  axes=sorted([i for i in range(3) if i!=max(range(3),key=lambda k:abs(p.normal[k]))],key=lambda i:dim[i],reverse=True)
  for li in p.loop_indices:
   v=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(v[axes[0]]/2,v[axes[1]]/2)
 o=bpy.data.objects.new(name,me);COLS[col].objects.link(o);o.parent=parent;o.location=loc;return o
def line(name,points,parent,material=line_mat,width=.008,closed=False):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=1;cu.bevel_depth=width;cu.bevel_resolution=1
 sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
 for p,c in zip(sp.points,points):p.co=(*c,1)
 sp.use_cyclic_u=closed;cu.materials.append(material);o=bpy.data.objects.new(name,cu);COLS['diagrams'].objects.link(o);o.parent=parent;return o
def rect(name,x,y,w,h,p,material=line_mat,width=.008):return line(name,[(x-w/2,y-h/2,.09),(x+w/2,y-h/2,.09),(x+w/2,y+h/2,.09),(x-w/2,y+h/2,.09)],p,material,width,True)
font=bpy.data.fonts.load(str(ROOT/'素材/字体/展陈标题.ttf'))
font_fallback=bpy.data.fonts.load(str(ROOT/'素材/字体/展陈标题补字.ttf'))
sans=bpy.data.fonts.load(str(ROOT/'素材/字体/展陈正文.ttf'))
for f in (font,font_fallback,sans):
 if hasattr(f,'pack'):f.pack()
def text(name,body,loc,size,p,material=ink,maxw=None,maxh=None,center=False,title=False):
 cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.font=(font_fallback if any(c in body for c in '栱〇') else font) if title else sans;cu.size=size;cu.align_x='CENTER' if center else 'LEFT';cu.align_y='TOP_BASELINE';cu.space_line=1.28;cu.extrude=.00035;cu.resolution_u=2;cu.materials.append(material)
 o=bpy.data.objects.new(name,cu);COLS['text'].objects.link(o);o.parent=p;o.location=loc;o['展陈文字']=body;o['可直接编辑']=True
 bpy.context.view_layer.update()
 bounds=o.bound_box;w=max(v[0] for v in bounds)-min(v[0] for v in bounds);h=max(v[1] for v in bounds)-min(v[1] for v in bounds)
 scale=min(1,maxw/w if maxw and w else 1,maxh/h if maxh and h else 1);o.scale*=scale
 return o
def para(s,width,size):
 n=max(8,int(width/size))
 return '\n'.join('\n'.join(textwrap.wrap(p,width=n,break_long_words=True,break_on_hyphens=False)) for p in s.split('\n'))
def circle(name,cx,cy,r,p,material=line_mat,width=.008):
 return line(name,[(cx+r*math.cos(a*math.tau/48),cy+r*math.sin(a*math.tau/48),.10) for a in range(48)],p,material,width,True)
def arrow(name,a,b,p,material=red,width=.011):
 line(name,[(*a,.105),(*b,.105)],p,material,width)
 d=(Vector(a)-Vector(b)).normalized();v=Vector((-d.y,d.x));h=.09
 pts=[Vector(b)+d*h+v*h*.45,Vector(b),Vector(b)+d*h-v*h*.45]
 line(name+'_head',[(*q,.105) for q in pts],p,material,width)
def polygon(name,pts,p,material=woodflat,depth=.035):
 n=len(pts);v=[(x,y,.10+z) for z in (0,depth) for x,y in pts];f=[tuple(reversed(range(n))),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 return mesh(name,v,f,material,p)

# Respect the user's edit. Clear remaining plinth fragments and obsolete empty boards.
removed=[]
for o in list(sc.objects):
 if o.type=='MESH' and (o.name.startswith(tuple(f'P{i:02}_' for i in range(1,9))) or o.name.startswith(('HistoryPanel_','HistoryRail_','HistoryShelf_','HistoryTheme_','ComponentPanel_','ComponentWord_','WorkshopWall_','EndWallPanel_','EndWallShelf_'))):
  removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
for o in sc.objects:
 if o.name.endswith('_ExhibitAnchor_EMPTY'):o['用途']='原展台位置已清空；仅保留数字交互定位'
for name,z in [('Title01_Entrance',3.85),('Sub01_Entrance',3.32),('Title04_Workshop',4.18),('Sub04_Workshop',3.70),('Title06_Challenge',4.16),('Sub06_Challenge',3.62),('Title08_Quiet',3.58)]:
 o=bpy.data.objects.get(name)
 if o:o.location.z=z
for zone,xx,zz,width,title in [(3,6,3.95,9.2,'Title03_Component'),(4,18,4.18,8.7,'Title04_Workshop')]:
 box(f'HeaderPlate_Z{zone:02}',(xx,23.45,zz),(width,.065,.74),paper,zones[zone])
 ob=bpy.data.objects.get(title)
 if ob:ob.location.y=23.40;ob.location.z=zz

# Load only the user's actual decorative assets: no room, floor, old cameras or lights.
with bpy.data.libraries.load(ZEN,link=False) as (a,b):
 b.objects=[n for n in a.objects if n.startswith(('书架立柱','书架层板','书函与藏书','书架下柜','柜门格心','青釉地瓶','壁灯挂件','暖色壁灯罩'))]
zen=[o for o in b.objects if o]
booksrc=[o for o in zen if o.name.startswith(('书架','书函','柜门格心'))]
vasesrc=[o for o in zen if o.name.startswith('青釉地瓶')]
lampsrc=[o for o in zen if o.name in ('壁灯挂件','暖色壁灯罩')]
def copy_asset(objects,source_origin,location,angle,groupname,zone,col='decor'):
 group=empty(groupname,col,zones[zone]);group.location=location;group.rotation_euler.z=angle
 for o in objects:
  n=o.copy();n.animation_data_clear();n.name=groupname+'_'+o.name;COLS[col].objects.link(n);n.parent=group
  # Source decorations use applied dimensions with no parents.
  n.location=Vector(o.location)-Vector(source_origin);n.rotation_euler=o.rotation_euler;n.scale=o.scale.copy();n.hide_render=False;n.hide_viewport=False
 return group
for zone,loc,angle in [(2,(1.85,7.62,0),math.pi),(8,(21.55,.65,0),math.pi),(7,(34.05,9.18,0),0)]:
 copy_asset(booksrc,(2.96,3.29,0),loc,angle,f'CornerBookcase_Z{zone:02}',zone)
decor_positions=[(1,(1.05,.95,0)),(2,(1.10,16.35,0)),(3,(.92,23.05,0)),(5,(12.92,16.22,0)),(6,(35.10,23.02,0)),(7,(35.05,.93,0))]
for index,(zone,loc) in enumerate(decor_positions):
 group=copy_asset(vasesrc,(-4.49,3.0,.065),loc,0,f'CeladonBranches_Z{zone:02}',zone)
 # Reuse the celadon vessel; add restrained, individually modeled stems and leaves.
 for j in range(3):
  angle=(index*.7+j*2.2);dx=.22*math.cos(angle);dy=.22*math.sin(angle);height=1.55+.18*j
  cu=bpy.data.curves.new('竹枝','CURVE');cu.dimensions='3D';cu.resolution_u=2;cu.bevel_depth=.008;cu.bevel_resolution=1
  sp=cu.splines.new('BEZIER');sp.bezier_points.add(3)
  for k,p in enumerate(sp.bezier_points):p.co=(dx*k/3,dy*k/3,.75+(height-.75)*k/3);p.handle_left_type='AUTO';p.handle_right_type='AUTO'
  cu.materials.append(branchmat);stem=bpy.data.objects.new(f'枝条_{index}_{j}',cu);COLS['decor'].objects.link(stem);stem.parent=group
  for k in range(3):
   t=.55+.19*k;x=dx*t;y=dy*t;z=.75+(height-.75)*t
   aa=angle+(-1 if k%2 else 1)*.8;v=Vector((math.cos(aa),math.sin(aa),.60));cross=Vector((-v.y,v.x,.14));base=Vector((x,y,z));tip=base+v*.24
   pts=[base,base+v*.10+cross*.052,tip,base+v*.10-cross*.052]
   leaf=mesh(f'竹叶_{index}_{j}_{k}',[tuple(p) for p in pts],[(0,1,2),(0,2,3)],leafmat,group,col='decor')

def area(name,eye,target,power,size,color=(1,.86,.68),parent=None):
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color
 ob=bpy.data.objects.new(name,data);COLS['lights'].objects.link(ob);ob.location=eye;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();return ob
lamp_specs=[(1,(.52,1.0,3.8),'E'),(2,(11.65,8.0,3.9),'W'),(3,(.5,23.0,3.85),'E'),(4,(23.60,18.0,3.95),'W'),(5,(12.30,8.0,4.15),'E'),(5,(23.70,16.4,4.05),'W'),(6,(25.2,23.45,4.20),'S'),(6,(34.8,23.45,4.20),'S'),(7,(35.48,8.7,3.85),'W'),(8,(13.8,.47,3.8),'N')]
angles={'W':0,'S':math.pi/2,'N':-math.pi/2,'E':math.pi}
for k,(zone,pos,face) in enumerate(lamp_specs):
 g=copy_asset(lampsrc,(4.68,-3.13,2.67),pos,angles[face],f'WarmLantern_{k:02}',zone,'lights')
 normal={'E':Vector((1,0,0)),'W':Vector((-1,0,0)),'S':Vector((0,-1,0)),'N':Vector((0,1,0))}[face]
 eye=Vector(pos)+normal*.28+Vector((0,0,-.18));area(f'WallAccent_{k:02}',eye,eye+normal*.45+Vector((0,0,-1)),22,.45)

# Keep prototypes outside the scene and copy their evaluated geometry as shallow wall reliefs.
with bpy.data.libraries.load(BRACKET,link=False) as (a,b):
 b.objects=[n for n in a.objects if n.startswith(('dou_','gong_','ang_','timber_','fang_'))]
brackets=[o for o in b.objects if o and o.type=='MESH']
protos=[]
for o in brackets:protos.append((o.name,o.data,o.matrix_world.copy(),int(o.get('层',0))))
def bracket_art(p,w,h,exploded=False):
 verts=[]
 for name,data,m,layer in protos:
  for v in data.vertices:
   q=m@v.co;verts.append(Vector((q.x,q.y,q.z+(layer*.14 if exploded else 0))))
 lo=Vector(tuple(min(v[i] for v in verts) for i in range(3)));hi=Vector(tuple(max(v[i] for v in verts) for i in range(3)));center=(lo+hi)/2
 scale=min(w/(hi.x-lo.x),h/(hi.z-lo.z))*.88
 depthscale=min(.10,.34/(hi.y-lo.y))
 mapping=Matrix(((scale,0,0,0),(0,0,scale,0),(0,-depthscale,0,.30),(0,0,0,1)))
 for name,data,m,layer in protos:
  me=data.copy();translation=Matrix.Translation(-center+Vector((0,0,layer*.14 if exploded else 0)));me.transform(mapping@translation@m)
  o=bpy.data.objects.new(('Exploded_' if exploded else 'Assembled_')+name,me);COLS['diagrams'].objects.link(o);o.parent=p;o['用途']='项目现有教学模型壁挂展示，非测绘复原'
  bevel=o.modifiers.new('微倒角','BEVEL');bevel.width=.0015;bevel.segments=2

def diagram(kind,p,w,h):
 # All drawings are real vector/mesh objects, editable and independent of raster text.
 if kind in ('bracket','exploded'):
  bracket_art(p,w,h,kind=='exploded');return
 if kind=='timer':
  circle('计时环',0,0,min(w,h)*.40,p,bronze,.018);text('120秒','120',(0,.12,.12),min(w,h)*.28,p,red,center=True,title=True);return
 if kind in ('dou','gong','ang'):
  if kind=='dou':pts=[(-.35,-.24),(.35,-.24),(.48,.05),(.48,.25),(.12,.25),(.12,.06),(-.12,.06),(-.12,.25),(-.48,.25),(-.48,.05)]
  elif kind=='gong':pts=[(-.75,.17),(.75,.17),(.75,.02),(.55,.02),(.43,-.17),(.23,-.23),(-.23,-.23),(-.43,-.17),(-.55,.02),(-.75,.02)]
  else:pts=[(-.8,-.25),(-.65,-.30),(.8,.19),(.8,.32),(-.6,-.12),(-.8,-.10)]
  factor=min(w/1.8,h/.9)*.83;polygon(kind,[(x*factor,y*factor) for x,y in pts],p);return
 if kind in ('plan','survey'):
  ww=min(w*.75,h*1.25);hh=min(h*.80,w*.66);rect('柱网边界',0,0,ww,hh,p,bronze)
  for i in range(4):
   x=-ww/2+i*ww/3;y=-hh/2+i*hh/3
   line('轴线X',[(x,-hh/2,.10),(x,hh/2,.10)],p,linen,.003)
   line('轴线Y',[(-ww/2,y,.10),(ww/2,y,.10)],p,linen,.003)
   for j in range(4):circle('柱位',x,-hh/2+j*hh/3,.028,p,red,.009)
  return
 if kind=='joinery':
  f=min(w/2.4,h/1.1)*.85
  polygon('榫头',[(-1.05,-.24),(-.4,-.24),(-.4,-.1),(-.13,-.1),(-.13,.1),(-.4,.1),(-.4,.24),(-1.05,.24)],p,woodflat)
  # The open slot is physically empty; the drawing does not imply a measured joint.
  for x,y,ww,hh in [(.65,.20,.72,.18),(.65,-.20,.72,.18),(.94,0,.14,.4)]:box('卯眼木件',(x,y,.13),(ww,hh,.06),woodflat,p,'diagrams')
  arrow('合向',(-.05,0),(.22,0),p)
  for o in list(p.children):
   o.scale*=f;o.location.x*=f;o.location.y*=f
  return
 if kind in ('roof','load','stack'):
  f=min(w/2.1,h/1.8)*.90
  if kind=='roof':
   pts=[(-1,-.10),(-.80,-.03),(-.52,.13),(0,.53),(.52,.13),(.80,-.03),(1,-.10)]
   line('歇山意向屋面',[(x*f,y*f,.12) for x,y in pts],p,bronze,.018)
   for x in [-.68,0,.68]:line('柱线',[(x*f,-.53*f,.12),(x*f,-.05*f,.12)],p,line_mat,.015)
   line('梁线',[(-.78*f,-.04*f,.12),(.78*f,-.04*f,.12)],p,line_mat,.015)
  else:
   names=['屋架','铺作','梁枋','柱网'] if kind=='stack' else ['屋顶','梁架','铺作','柱','柱础']
   step=1.44/(len(names)-1)
   for i,label in enumerate(names):
    yy=(.72-i*step)*f;ww=(1.35-i*.08)*f;rect(label,0,yy,ww,.25*f,p,line_mat,.009)
    text(label,label,(0,yy+.07*f,.12),.12*f,p,ink,center=True)
    if i<len(names)-1:arrow('传力',(0,yy-.15*f),(0,yy-(step-.13)*f),p,red,.009)
  return
 if kind=='timeline':
  horizontal=w>2.5;positions=[(-w*.36,0),(0,0),(w*.36,0)] if horizontal else [(0,h*.28),(0,0),(0,-h*.28)]
  line('沿革',[(x,y,.10) for x,y in positions],p,bronze,.012)
  for (x,y),title,sub in zip(positions,['1013','清代','今日'],['宋代核心','增修下檐','数字解读']):
   circle('纪年节点',x,y,.06,p,red,.015)
   dx=.13 if not horizontal else 0;dy=.12 if not horizontal else .22
   text('纪年',title,(x+dx,y+dy,.12),.17,p,ink,center=horizontal,title=True)
   if horizontal:text('沿革短题',sub,(x,y-.20,.12),.11,p,muted,center=True)
  return
 if kind in ('flow','route'):
  labels=['识构','对位','归位'] if kind=='flow' else ['寻源','识材','解构']
  for i,label in enumerate(labels):
   x=(i-1)*w*.32;rect(label,x,0,w*.25,min(h*.5,.48),p,bronze,.012);text(label,label,(x,.08,.12),min(.19,w*.09),p,ink,center=True,title=True)
   if i<2:arrow('体验路径',(x+w*.14,0),(x+w*.18,0),p)
  return
 if kind=='book':
  ww=min(w*.42,h*.60);hh=min(h*.72,w*.55)
  for side in [-1,1]:
   rect('书页',side*ww/2,0,ww,hh,p,bronze,.012)
   for k in range(4):line('书页行线',[(side*ww/2-ww*.32,(.24-k*.16)*hh,.12),(side*ww/2+ww*.32,(.24-k*.16)*hh,.12)],p,linen,.005)
  line('书脊',[(0,-hh/2,.12),(0,hh/2,.12)],p,red,.011);return
 if kind=='tools':
  line('曲尺',[(-w*.32,h*.25,.13),(-w*.32,-h*.25,.13),(w*.20,-h*.25,.13)],p,bronze,.033)
  line('木槌柄',[(w*.12,-h*.14,.13),(w*.12,h*.23,.13)],p,woodflat,.024)
  box('木槌头',(w*.12,h*.26,.13),(w*.38,h*.16,.08),woodflat,p,'diagrams')
  for k in range(6):line('尺刻',[(w*(-.27+k*.065),-h*.25,.14),(w*(-.27+k*.065),-h*.17,.14)],p,red,.005)
  return
 if kind=='vr':
  ww=min(w*.72,h*1.25);hh=min(h*.50,ww*.52);rect('头显',0,.10,ww,hh,p,line_mat,.016)
  line('头带',[(-ww/2,0,.12),(-ww*.64,.16,.12),(-ww*.60,hh*.8,.12),(ww*.6,hh*.8,.12),(ww*.64,.16,.12),(ww/2,0,.12)],p,bronze,.012)
  for side in [-1,1]:circle('手势点',side*ww*.67,-hh*.75,.09,p,red,.016)
  return
 if kind=='dialogue':
  rect('提问',-.16,.14,w*.6,h*.35,p,line_mat,.014);rect('回答',.16,-.19,w*.60,h*.35,p,bronze,.014)
  text('问号','？',(-.16,.24,.12),.23,p,red,center=True,title=True);text('木','木',(.16,-.08,.12),.19,p,ink,center=True,title=True);return

photo_mats={}
def photograph(file,parent,w,h):
 if file not in photo_mats:
  image=bpy.data.images.load(str(ROOT/'素材'/file),check_existing=True);m=mat('V03_现场图版_'+file,'#ffffff',.9)
  bs=m.node_tree.nodes.get('Principled BSDF');tx=m.node_tree.nodes.new('ShaderNodeTexImage');tx.image=image;m.node_tree.links.new(tx.outputs['Color'],bs.inputs['Base Color']);m.node_tree.links.new(tx.outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=.12
  photo_mats[file]=(m,image)
 m,image=photo_mats[file];iw,ih=image.size;factor=min(w/iw,h/ih);ww=iw*factor;hh=ih*factor
 o=mesh('Photo_'+file,[(-ww/2,-hh/2,.09),(ww/2,-hh/2,.09),(ww/2,hh/2,.09),(-ww/2,hh/2,.09)],[(0,1,2,3)],m,parent,'photos')
 uv=o.data.uv_layers.new(name='UVMap')
 for li,xy in zip(o.data.polygons[0].loop_indices,[(0,0),(1,0),(1,1),(0,1)]):uv.data[li].uv=xy
 rect('摄影图框',0,0,ww+.05,hh+.05,parent,bronze,.007)
 text('图版说明','现场展陈模型 · 摄影记录',(-ww/2,-hh/2-.13,.11),.075,parent,muted,maxw=ww)

faceangle={'S':0,'N':math.pi,'E':math.pi/2,'W':-math.pi/2}
roots=[]
for item in PANELS:
 name=item['id'];w=item['width'];h=item['height'];root=empty('Wall_'+name,parent=zones[item['zone']]);root.location=item['center'];root.rotation_euler=(math.pi/2,0,faceangle[item['face']]);root['展区']=item['zone'];root['墙面朝向']=item['face'];root['标题']=item['title'];roots.append(root)
 if item['art'] in ('scroll','scrollwide'):
  box('挂轴绫边',(0,0,0),(w,h,.032),linen,root)
  box('宣纸挂轴',(0,0,.025),(w-.13,h-.12,.015),paper,root)
  for yy in [-h/2,h/2]:box('挂轴木杆',(0,yy,.08),(w+.14,.055,.06),oak,root)
  if item['art']=='scrollwide':
   text('横披',item['title'],(0,h*.34,.10),.38,root,ink,maxw=w*.8,center=True,title=True)
   columns=item['body'].split('\n')
   for j,col in enumerate(columns):
    for k,char in enumerate(col):text('竖排诗句',char,((len(columns)-1)/2*.7-j*.7,.40-k*.30,.11),.25,root,muted,center=True,title=True)
  else:
   for k,ch in enumerate(item['title']):text('竖排题签',ch,(w*.15,h*.33-k*.36,.10),.31,root,ink,center=True,title=True)
   for j,col in enumerate(item['body'].split('\n')):
    for k,ch in enumerate(col):text('题签短句',ch,(-w*.20-j*.18,h*.17-k*.20,.10),.15,root,muted,center=True,title=True)
  continue
 box('ShadowReveal',(0,0,-.024),(w+.05,h+.05,.040),ink,root)
 for xx in [-w/2+.08,w/2-.08]:box('WallMountCleat',(xx,0,-.18),(.055,h-.16,.38),oak,root)
 box('PaperPanel',(0,0,.012),(w,h,.048),paper,root)
 for xx in [-w/2,w/2]:box('FineTimberEdge',(xx,0,.039),(.035,h+.035,.06),oak,root)
 for yy in [-h/2,h/2]:box('BronzeEdge',(0,yy,.044),(w,.014,.02),bronze,root)
 text('ArticleTitle',item['title'],(-w/2+.19,h/2-.27,.075),.235 if w>=3.7 else .18,root,ink,maxw=w-.38,title=True)
 line('题下短线',[(-w/2+.2,h/2-.43,.075),(-w/2+min(1.15,w*.5),h/2-.43,.075)],root,bronze,.005)
 if w>=3.7:
  art=empty('Art_'+name,'diagrams',root);art.location=(-w*.175,-.12,0)
  aw=w*.53;ah=h-.92
  if item['art']=='photo':photograph(item['image'],art,aw,ah-.1)
  else:diagram(item['art'],art,aw,ah)
  bx=w*.14;bw=w*.36-.15;bh=h-.88;size=.15 if w>=6 else .125
  text('ArticleBody',para(item['body'],bw,size),(bx,h/2-.68,.075),size,root,muted,maxw=bw,maxh=bh)
 else:
  art=empty('Art_'+name,'diagrams',root);art.location=(0,.32,0);ah=.67 if h<2.3 else .91
  diagram(item['art'],art,w-.45,ah)
  bw=w-.38;size=.115
  bodytop=-.18 if h<2.3 else -.28
  text('ArticleBody',para(item['body'],bw,size),(-w/2+.19,bodytop,.075),size,root,muted,maxw=bw,maxh=h/2+bodytop-.15)

# Remove unlinked prototypes, never the copies linked to the display collections.
for o in zen+brackets:
 if o.users==0:bpy.data.objects.remove(o)
for o in list(bpy.data.objects):
 if o.type=='CAMERA':bpy.data.objects.remove(o,do_unlink=True)
for s in bpy.data.scenes:s.camera=None
for c in list(bpy.data.cameras):bpy.data.cameras.remove(c)
for f in bpy.data.fonts:
 if f.filepath and not f.filepath.startswith('<') and hasattr(f,'pack'):
  try:f.pack()
  except RuntimeError:pass
for im in bpy.data.images:
 if im.source=='FILE':
  im.pack();im.filepath='//../素材/'+Path(im.filepath).name
sc['V03状态']='墙面展陈与靠墙陈设审核稿；尚未进行本版光照烘焙'
sc['V03依据']=SOURCE;sc['V03墙面展陈组数']=len(PANELS);sc['V03移除展台碎件']=len(removed)
sc['V03边界']='保留V02建筑壳体、柱网与通道；展陈文字仍为可编辑FONT；教学图示非测绘图'
sc.render.engine='CYCLES';sc.cycles.samples=40;sc.cycles.use_denoising=True;sc.cycles.max_bounces=6
try:
 pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='METAL';pref.get_devices()
 for d in pref.devices:d.use=d.type=='METAL'
 sc.cycles.device='GPU'
except:sc.cycles.device='CPU'
sc.view_settings.view_transform='AgX';sc.view_settings.exposure=-.8
eye=Vector((18.1,12.5,1.75));target=Vector((12.28,12.5,2.1));rot=(target-eye).to_track_quat('-Z','Y')
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   space=area.spaces.active;space.lens=24;space.clip_start=.03;space.clip_end=200;space.shading.type='MATERIAL';space.shading.use_scene_lights=True;space.shading.use_scene_world=True
   region=space.region_3d;region.view_perspective='PERSP';region.view_rotation=rot;region.view_distance=6;region.view_location=eye+rot@Vector((0,0,-6))
bpy.ops.object.select_all(action='DESELECT');bpy.context.view_layer.objects.active=None
bpy.context.preferences.filepaths.save_version=0
out=ROOT/'模型/展厅V03_墙面展陈与角落陈设_未烘焙_无摄像机.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
(ROOT/'编辑源文件/墙面展陈内容.json').write_text(json.dumps(PANELS,ensure_ascii=False,indent=2))
(ROOT/'编辑源文件/内容与素材依据.json').write_text(json.dumps(SOURCES,ensure_ascii=False,indent=2))
report={'source':SOURCE,'new_blend':str(out),'panel_groups':len(PANELS),'zones':sorted(set(p['zone'] for p in PANELS)),'removed_objects':removed,'camera_objects':sum(o.type=='CAMERA' for o in bpy.data.objects),'camera_data':len(bpy.data.cameras),'editable_text_objects':sum(o.type=='FONT' for o in sc.objects),'packed_fonts':[{'name':f.name,'packed':bool(f.packed_file)} for f in bpy.data.fonts if f.filepath and not f.filepath.startswith('<')],'images':[{'name':i.name,'packed':bool(i.packed_file)} for i in bpy.data.images if i.source=='FILE'],'baked_this_revision':False,'decor_bookcases':3,'decor_celadon_groups':6,'wall_lanterns':10,'diagram_model':'existing bracket teaching model; not a measured reconstruction'}
(ROOT/'检查记录/建模结果.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('CURATION_BUILD_COMPLETE',report,flush=True)
