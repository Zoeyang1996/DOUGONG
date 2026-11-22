import bpy,bmesh,math,json,time,sys,traceback
from mathutils import Vector,Euler
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TEX=ROOT/'贴图';PREV=ROOT/'预览';MODEL=ROOT/'模型';CHECK=ROOT/'检查记录'
for p in [TEX,PREV,MODEL,CHECK]:p.mkdir(exist_ok=True)
PARAM=ROOT/'编辑源文件'/'空间参数.json'
params=json.loads(PARAM.read_text())
OUT=MODEL/'保国寺VR数字斗拱展厅_V01_无摄像机.blend'
FBX=MODEL/'保国寺VR数字斗拱展厅_V01_无摄像机.fbx'
START=time.time()
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.name='保国寺VR数字斗拱展厅'
sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=1
sc.render.engine='CYCLES';sc.cycles.samples=40;sc.cycles.use_denoising=True
sc.cycles.max_bounces=6;sc.cycles.diffuse_bounces=4;sc.cycles.glossy_bounces=3
sc.cycles.transparent_max_bounces=4
sc.render.resolution_x=1440;sc.render.resolution_y=900;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG'
sc.view_settings.view_transform='AgX';sc.view_settings.exposure=-.8
try:sc.view_settings.look='AgX - Medium High Contrast'
except:pass
sc.world=bpy.data.worlds.new('Gallery ambient');sc.world.use_nodes=True
sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.55,.62,.7,1)
sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.22
device='CPU'
try:
 pref=bpy.context.preferences.addons['cycles'].preferences
 pref.compute_device_type='METAL';pref.get_devices()
 for dev in pref.devices:dev.use=dev.type=='METAL'
 if any(d.type=='METAL' for d in pref.devices):sc.cycles.device='GPU';device='METAL'
except Exception as e:print('GPU selection fallback:',e)
print('RENDER_DEVICE',device,flush=True)

def rgba(c):
 if isinstance(c,str):c=tuple(int(c[i:i+2],16)/255 for i in [1,3,5])
 return tuple((v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4) for v in c)+(1,)
def material(name,color,rough=.6,metal=0,texture=None,emit=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;ln=m.node_tree.links
 bs=n.get('Principled BSDF');bs.inputs['Base Color'].default_value=rgba(color)
 bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
 m.diffuse_color=rgba(color)
 if emit:
  bs.inputs['Emission Color'].default_value=rgba(color);bs.inputs['Emission Strength'].default_value=emit
 if texture:
  for suffix,socket in [('BaseColor','Base Color'),('Roughness','Roughness'),('NormalGL',None)]:
   tx=n.new('ShaderNodeTexImage');tx.name=texture+'_'+suffix
   tx.image=bpy.data.images.load(str(TEX/f'{texture}_{suffix}.png'),check_existing=True)
   if suffix!='BaseColor':tx.image.colorspace_settings.name='Non-Color'
   if socket:ln.new(tx.outputs['Color'],bs.inputs[socket])
   else:
    normal=n.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.25
    ln.new(tx.outputs['Color'],normal.inputs['Color']);ln.new(normal.outputs['Normal'],bs.inputs['Normal'])
 return m
mat={
 'oak':material('M01_烟熏橡木_PBR','#493526',texture='SmokedOak'),
 'wall':material('M02_暖灰矿物墙_PBR','#b5aa97',texture='WarmPlaster'),
 'floor':material('M03_哑光灰石_PBR','#7d807a',texture='GreyStone'),
 'lightstone':material('M04_浅矿物台面','#c3baa9',.68),
 'bronze':material('M05_暗古铜收口','#8a714c',.43,.65),
 'ink':material('M06_墨色导视','#1c241d',.74),
 'seam':material('M07_深灰缝与内缩踢脚','#444540',.8),
 'paper':material('M08_半透织物屏风','#d9cfb9',.82),
 'diffuse':material('M09_天窗漫射面','#f7edd3',.7,emit=.65),
 'glow':material('M10_暖光灯槽','#ffcf8b',.5,emit=4),
 'clay':material('M11_展墙底衬','#ded2b8',.9),
}
# Thin fabric uses a translucent BSDF; it does not require alpha blending in exported materials.
bs=mat['paper'].node_tree.nodes.get('Principled BSDF')
bs.inputs['Subsurface Weight'].default_value=.06

cats={};roots={};mesh_cache={};obstacles=[];roof=[];outer_cut=[];text_manifest=[];portal_manifest=[]
master=bpy.data.objects.new('Baoguosi_VR_Gallery_36x24m',None);sc.collection.objects.link(master)
master['units']='meters';master['design_revision']='Spatial design V01 approved 2026-11-22'
master['contains_game_logic']=False;master['camera_free_delivery']=True
cat_names={'Shell':'01_建筑壳体','Timber':'02_顶面与木构','Fixtures':'03_展台与固定家具','Text':'04_墙面主题与导视','Lighting':'05_室内灯光','VR':'06_VR交互预留','Ceiling':'07_顶面遮罩_可单独隐藏'}
def category(key):
 if key not in cats:
  col=bpy.data.collections.new(cat_names[key]);sc.collection.children.link(col);cats[key]=col
  ob=bpy.data.objects.new(key,None);col.objects.link(ob);ob.parent=master;roots[key]=ob
 return cats[key]
def parent(key,zone=None):
 category(key)
 if not zone:return roots[key]
 code=(key,zone)
 if code not in roots:
  e=bpy.data.objects.new(f'{key}_Zone{zone:02}',None);cats[key].objects.link(e);e.parent=roots[key];roots[code]=e
 return roots[code]
def uv_project(me):
 uv=me.uv_layers.new(name='UVMap')
 for poly in me.polygons:
  dominant=max(range(3),key=lambda k:abs(poly.normal[k]))
  axes=[i for i in range(3) if i!=dominant]
  ext=[max(me.vertices[v].co[a] for v in poly.vertices)-min(me.vertices[v].co[a] for v in poly.vertices) for a in axes]
  if ext[1]>ext[0]:axes=axes[::-1]
  for loopidx in poly.loop_indices:
   v=me.vertices[me.loops[loopidx].vertex_index].co
   uv.data[loopidx].uv=(v[axes[0]]/2,v[axes[1]]/2)
def box(name,loc,dim,material_key='oak',key='Fixtures',zone=None,bevel=.008,collide=False,cut=False,ceiling=False):
 cache=(tuple(round(v,5) for v in dim),material_key,round(bevel,5))
 if cache not in mesh_cache:
  bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
  for v in bm.verts:v.co.x*=dim[0];v.co.y*=dim[1];v.co.z*=dim[2]
  if bevel>0:
   bmesh.ops.bevel(bm,geom=list(bm.edges),offset=min(bevel,min(dim)*.22),segments=2,affect='EDGES')
  bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
  me=bpy.data.meshes.new(name+'_mesh');bm.to_mesh(me);bm.free();me.update();uv_project(me)
  me.materials.append(mat[material_key]);mesh_cache[cache]=me
 ob=bpy.data.objects.new(name,mesh_cache[cache]);category(key).objects.link(ob);ob.parent=parent(key,zone);ob.location=loc
 if collide:obstacles.append((name,[loc[i]-dim[i]/2 for i in range(3)],[loc[i]+dim[i]/2 for i in range(3)]))
 if cut:outer_cut.append(ob)
 if ceiling:roof.append(ob)
 return ob
def wall_segment(name,a,b,height=5.9,cut=False,zone=None):
 x1,y1=a;x2,y2=b;length=math.hypot(x2-x1,y2-y1)
 if abs(x2-x1)>.001:dim=(length,.18,height)
 else:dim=(.18,length,height)
 ob=box(name,((x1+x2)/2,(y1+y2)/2,height/2),dim,'wall','Shell',zone,.006,True,cut)
 # a dark plinth and subtle timber cornice meet the wall without coplanar faces
 box(name+'_skirting',((x1+x2)/2,(y1+y2)/2,.11),(dim[0]+.012,dim[1]+.012,.22),'lightstone','Shell',zone,.005,cut=cut)
 box(name+'_cornice',((x1+x2)/2,(y1+y2)/2,5.12),(dim[0]+.045,dim[1]+.045,.15),'oak','Timber',zone,.012,cut=cut)
 return ob
def opening(name,axis,c,fixed,width=3,height=3.2,top=5.9):
 # The wall is segmented around the opening. No cutter meshes are retained.
 thick=.22
 if axis=='X':
  box(name+'_lintel_wall',(c,fixed,(height+top)/2),(width,.18,top-height),'wall','Shell',bevel=.005,collide=True)
  for s in [-1,1]:box(name+f'_jamb_{s}',(c+s*(width/2+.01),fixed,height/2),(.15,thick,height),'oak','Timber',bevel=.012,collide=True)
  box(name+'_head',(c,fixed,height+.07),(width+.18,thick,.16),'oak','Timber',bevel=.012)
 else:
  box(name+'_lintel_wall',(fixed,c,(height+top)/2),(.18,width,top-height),'wall','Shell',bevel=.005,collide=True)
  for s in [-1,1]:box(name+f'_jamb_{s}',(fixed,c+s*(width/2+.01),height/2),(thick,.15,height),'oak','Timber',bevel=.012,collide=True)
  box(name+'_head',(fixed,c,height+.07),(thick,width+.18,.16),'oak','Timber',bevel=.012)
 portal_manifest.append({'id':name,'axis':axis,'center':c,'fixed_coordinate':fixed,'nominal_width':width,'clear_width':round(width-.13,3),'clear_height':height})
def area(name,loc,target,power,size=3,color=(1,.9,.75),zone=None):
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.color=color;data.shape='DISK';data.size=size
 ob=bpy.data.objects.new(name,data);category('Lighting').objects.link(ob);ob.parent=parent('Lighting',zone);ob.location=loc
 ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();return ob
font=bpy.data.fonts.load('/System/Library/Fonts/Supplemental/Songti.ttc')
font_ui=bpy.data.fonts.load('/System/Library/Fonts/STHeiti Light.ttc')
def text(name,body,loc,size=.46,face='S',zone=None,kind='ink',max_width=None):
 cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.font=font if size>.3 else font_ui;cu.size=size
 cu.align_x='CENTER';cu.align_y='CENTER';cu.extrude=.003;cu.bevel_depth=.0005;cu.bevel_resolution=0;cu.resolution_u=4
 ob=bpy.data.objects.new(name,cu);category('Text').objects.link(ob);ob.parent=parent('Text',zone);ob.location=loc
 ob.rotation_euler=(math.pi/2,0,{'S':0,'N':math.pi,'E':math.pi/2,'W':-math.pi/2}[face]);cu.materials.append(mat[kind]);bpy.context.view_layer.update()
 if max_width:
  width=max(ob.dimensions.x,ob.dimensions.y)
  if width>max_width:ob.scale*=max_width/width
 ob['文字内容']=body;ob['zone']=zone or 0
 bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.convert(target='MESH');ob.select_set(False)
 text_manifest.append({'object':name,'text':body,'zone':zone,'position_m':list(loc),'face':face})
 return ob

# 01 / floors - one level, no thresholds or entrance steps.
box('Floor_GroutBed',(18,12,-.15),(36,24,.19),'seam','Shell',bevel=0)
tile=1.2
for i in range(30):
 for j in range(20):
  box(f'FloorTile_{i:02}_{j:02}',((i+.5)*tile,(j+.5)*tile,-.027),(tile-.008,tile-.008,.054),'floor','Shell',bevel=.002)

# 02 / perimeter: exact outer footprint 36 x 24m.
for no,(a,b) in enumerate([(0,4.5),(7.5,28.5),(31.5,36)]):
 box(f'Outer_S_{no}',((a+b)/2,.12,2.95),(b-a,.24,5.9),'wall','Shell',bevel=.004,collide=True,cut=True)
 box(f'Outer_S_{no}_base',((a+b)/2,.12,.11),(b-a,.27,.22),'lightstone','Shell',bevel=.004,cut=True)
for name,loc,dim,cut in [('Outer_W',(.12,12,2.95),(.24,24,5.9),True),('Outer_E',(35.88,12,2.95),(.24,24,5.9),False),('Outer_N',(18,23.88,2.95),(36,.24,5.9),False)]:
 box(name,loc,dim,'wall','Shell',bevel=.004,collide=True,cut=cut)
 box(name+'_base',(loc[0],loc[1],.11),(dim[0]+.024,dim[1]+.024,.22),'lightstone','Shell',bevel=.004,cut=cut)
opening('Entrance','X',6,.12,top=5.9);opening('Exit','X',30,.12,top=5.9)

# Internal solid wall segments and full-height header pieces around every portal.
for fixed,intervals in [(12,[(0,2),(5,18.5),(21.5,24)]),(24,[(0,3),(6,10),(13,24)])]:
 for no,(a,b) in enumerate(intervals):wall_segment(f'Wall_X{fixed}_{no}',(fixed,a),(fixed,b))
for x,y in [(12,3.5),(12,20),(24,4.5),(24,11.5)]:opening(f'Portal_X{x}_Y{y}','Y',y,x)
for fixed in [7,17]:
 for no,(a,b) in enumerate([(0,3.5),(6.5,12),(12,17),(20,24)]):wall_segment(f'Wall_Y{fixed}_{no}',(a,fixed),(b,fixed))
 for x in [5,18.5]:opening(f'Portal_Y{fixed}_X{x}','X',x,fixed)
for no,(a,b) in enumerate([(24,29),(32,36)]):wall_segment(f'Wall_Y10_{no}',(a,10),(b,10))
opening('Portal_Y10_X30.5','X',30.5,10)

# 03 / tall main hall clerestory enclosure: above the ordinary gallery roof.
for n,loc,dim in [
 ('Main_Upper_W',(12,12,6.78),(.18,10,1.76)),('Main_Upper_E',(24,12,6.78),(.18,10,1.76)),
 ('Main_Upper_S',(18,7,6.78),(12,.18,1.76)),('Main_Upper_N',(18,17,6.78),(12,.18,1.76))]:
 box(n,loc,dim,'wall','Shell',bevel=.004)
for x in [12.12,23.88]:
 box('Clerestory_Long_'+str(x),(x,12,6.65),(.045,8.8,.65),'diffuse','Timber',bevel=.004)
for y in [7.12,16.88]:
 box('Clerestory_Short_'+str(y),(18,y,6.65),(10.6,.045,.65),'diffuse','Timber',bevel=.004)

# 04 / ceiling fields, timber rhythm, wall-side uprights and perimeter light slots.
for z in params['zones']:
 zone=int(z['id']);x,y,w,d=z['bounds_xywh'];high=zone==5;bottom=7.2 if high else 5.4
 top=bottom+.38
 box(f'Zone{zone:02}_CeilingBacking',(x+w/2,y+d/2,top+.12),(w-.05,d-.05,.14),'wall','Ceiling',zone,ceiling=True)
 for xx in [x+.24,x+w-.24]:
  box(f'Z{zone:02}_PerimeterBeam_X{xx}',(xx,y+d/2,bottom+.13),(.22,d-.3,.26),'oak','Timber',zone,.015)
 for yy in [y+.24,y+d-.24]:
  box(f'Z{zone:02}_PerimeterBeam_Y{yy}',(x+w/2,yy,bottom+.13),(w-.3,.22,.26),'oak','Timber',zone,.015)
 # cross beams at 3m rhythm. These are overhead only, not posts through exhibits.
 for k in range(1,int(w/3)):
  xx=x+3*k;box(f'Z{zone:02}_CrossBeam_{k}',(xx,y+d/2,bottom+.16),(.18,d-.45,.32),'oak','Timber',zone,.012)
 for k in range(1,int(d/3)+1):
  yy=y+3*k
  if yy<y+d-.4:box(f'Z{zone:02}_TieBeam_{k}',(x+w/2,yy,bottom+.27),(w-.45,.13,.18),'oak','Timber',zone,.01)
 # diffuse ceiling in three large strips, no heavy transparent layers
 for k in range(3):
  box(f'Z{zone:02}_Diffuser_{k}',(x+(k+.5)*w/3,y+d/2,top+.015),(w/3-.25,d-.56,.035),'diffuse' if high else 'clay','Ceiling',zone,.003,ceiling=True)
 for xx in [x+.32,x+w-.32]:
  box(f'Z{zone:02}_Cove_X{xx}',(xx,y+d/2,5.03 if not high else 6.96),(.035,d-.8,.025),'glow','Timber',zone,.002)
 for xx in [x+w*.28,x+w*.72]:
  for yy in [y+d*.3,y+d*.72]:
   area(f'Z{zone:02}_Ambient_{xx}_{yy}',(xx,yy,bottom-.12),(xx,yy,0),540 if not high else 1050,3.5 if not high else 4.5,(1,.94,.84),zone)

# 05 / wall timber members and construction detail. Each is mounted against a wall.
for x in [1,6,11,13,18,23,25,30,35]:
 box(f'North_WallPost_{x}',(x,23.70,2.62),(.16,.13,5.24),'oak','Timber',bevel=.012)
for y in [1,6,11,16,21,23]:
 for x in [.30,35.70]:box(f'Side_WallPost_{x}_{y}',(x,y,2.62),(.13,.16,5.24),'oak','Timber',bevel=.012)
for x in [.32,35.68]:box('Side_Rail_'+str(x),(x,12,4.80),(.17,23.4,.15),'oak','Timber',bevel=.01)
box('North_Rail',(18,23.66,4.80),(35.4,.18,.15),'oak','Timber',bevel=.01)

def north_panel(name,x,y,z,w,h,zone):
 # Wall-mounted backing, boxed bottom shelf, fine bronze edge; geometry is offset from wall.
 box(name+'_back',(x,y,z),(w,.07,h),'clay','Fixtures',zone,.008)
 for xx in [x-w/2,x+w/2]:box(name+'_edge_'+str(xx),(xx,y-.045,z),(.014,.014,h),'bronze','Fixtures',zone,.002)
 box(name+'_shelf',(x,y-.17,z-h/2-.03),(w,.38,.07),'lightstone','Fixtures',zone,.009)
 box(name+'_lamp',(x,y-.06,z+h/2-.04),(w-.16,.018,.018),'glow','Fixtures',zone,.002)
 area(name+'_wash',(x,y-.42,z+h/2-.12),(x,y-.02,z),100,1.6,(1,.85,.66),zone)

# Gallery 02 wall panels on west wall with a quiet large heading above.
for idx,yy in enumerate([9.4,12.1,14.8]):
 box(f'HistoryPanel_{idx}',(.285,yy,1.85),(.06,1.7,1.45),'clay','Fixtures',2,.012)
 for zz in [1.09,2.60]:box(f'HistoryRail_{idx}_{zz}',(.335,yy,zz),(.08,1.75,.035),'bronze','Fixtures',2,.003)
 box(f'HistoryShelf_{idx}',(.51,yy,.90),(.6,1.8,.1),'oak','Fixtures',2,.012)
 area(f'HistoryWallWash_{idx}',(1.0,yy,3.0),(.28,yy,1.5),100,1.1,(1,.86,.7),2)
 text(f'HistoryTheme_{idx}',['保国寺','榫卯','铺作'][idx],(.33,yy,1.95),.30,'E',2,'ink',1.2)

# Component gallery shallow cabinet/wall and quiet framed silhouettes for later interpretation.
for idx,xx in enumerate([2.5,6,9.5]):
 north_panel(f'ComponentPanel_{idx}',xx,23.64,1.95,2.2,1.55,3)
 text(f'ComponentWord_{idx}',['斗','栱','昂'][idx],(xx,23.585,2.0),.55,'S',3,'ink',1.4)

# 06 / plinth family: stone tops, timber sides and inset feet. All tops remain empty.
for p in params['empty_plinths']:
 no=p['id'];x,y=p['x'],p['y'];w,d,h=p['size'];zone=5 if no=='P01' else 3 if no in ['P02','P03','P04'] else 4 if no in ['P05','P06'] else 6 if no=='P07' else 7
 if no in ['P05','P06','P08']:
  box(no+'_StoneTop',(x+w/2,y+d/2,h-.05),(w,d,.10),'lightstone','Fixtures',zone,.018,True)
  box(no+'_Apron',(x+w/2,y+d/2,h-.16),(w-.12,d-.12,.15),'oak','Fixtures',zone,.012)
  for xx in [x+.12,x+w-.12]:
   for yy in [y+.12,y+d-.12]:
    box(no+f'_Leg_{xx}_{yy}',(xx,yy,(h-.2)/2),(.13,.13,h-.2),'oak','Fixtures',zone,.012,True)
  box(no+'_Stretcher',(x+w/2,y+d/2,.16),(w-.3,.075,.10),'oak','Fixtures',zone,.008)
 else:
  box(no+'_InsetFoot',(x+w/2,y+d/2,.035),(w-.16,d-.16,.07),'seam','Fixtures',zone,.006,True)
  box(no+'_TimberBody',(x+w/2,y+d/2,h/2),(w-.05,d-.05,h-.075),'oak','Fixtures',zone,.012,True)
  box(no+'_MineralTop',(x+w/2,y+d/2,h-.024),(w,d,.048),'lightstone','Fixtures',zone,.012,True)
  # restrained thin bronze datum around the top edge
  box(no+'_InlayFront',(x+w/2,y-.002,h-.065),(w-.12,.007,.008),'bronze','Fixtures',zone,.001)
 anchor=bpy.data.objects.new(no+'_ExhibitAnchor_EMPTY',None);category('VR').objects.link(anchor);anchor.parent=parent('VR',zone);anchor.location=(x+w/2,y+d/2,h+.01);anchor.empty_display_size=.15
 anchor['用途']=p['name']+'；当前台面留空';anchor['展品最大占地建议_m']=[w-.4,d-.4]

# 07 / workbench back panels with joinery-inspired framing; generous space before the tables.
for idx,xx in enumerate([15.2,21.2]):north_panel(f'WorkshopWall_{idx}',xx,23.63,2.18,4.65,1.65,4)

# Arrival screen - simple timber lattice, raised topic plate; no ornamental doorway blocking passage.
for i in range(18):box(f'ArrivalScreen_Slat_{i}',(5+.09+i*.16,2.5,1.75),(.045,.12,3.5),'oak','Fixtures',1,.006,True)
for z in [.14,3.4]:box('ArrivalScreen_Frame_'+str(z),(6.47,2.5,z),(3.1,.16,.12),'oak','Fixtures',1,.009)
box('Arrival_TopicPlate',(6.47,2.405,2.08),(2.68,.055,.90),'lightstone','Fixtures',1,.012)
text('Arrival_FourCharacters','入木见构',(6.47,2.366,2.08),.47,'S',1,'ink',2.35)

# Displaced fabric screens in component gallery boundary, kept away from openings and main route.
for i,(xx,yy) in enumerate([(1.15,18.5),(10.95,22.4)]):
 box(f'Screen_{i}_Paper',(xx,yy,1.9),(1.45,.035,3.45),'paper','Fixtures',3,.004)
 for xxx in [xx-.76,xx+.76]:box(f'Screen_{i}_Frame_{xxx}',(xxx,yy,1.9),(.055,.085,3.62),'oak','Fixtures',3,.006,True)
 for zz in [.12,3.68]:box(f'Screen_{i}_Rail_{zz}',(xx,yy,zz),(1.58,.085,.055),'oak','Fixtures',3,.005)

# Quiet corridor bench and finished end-gallery wall recesses.
box('QuietBench_Base',(18,1.65,.18),(7.8,.52,.36),'oak','Fixtures',8,.018,True)
box('QuietBench_Seat',(18,1.65,.41),(8,.68,.1),'lightstone','Fixtures',8,.018,True)
for idx,yy in enumerate([3,6.5]):
 box(f'EndWallPanel_{idx}',(35.61,yy,1.72),(.07,2.5,1.4),'clay','Fixtures',7,.012)
 box(f'EndWallShelf_{idx}',(35.48,yy,.96),(.35,2.52,.075),'lightstone','Fixtures',7,.01)
 area(f'EndWallWash_{idx}',(35.1,yy,2.7),(35.67,yy,1.7),100,1.4,(1,.86,.7),7)

# 08 / room titles. All Chinese typography is converted to geometry, so fonts are not required on another machine.
text('Title01_Entrance','保国寺数字斗拱展厅',(9.18,6.872,3.45),.43,'S',1,'ink',5.0)
text('Sub01_Entrance','观木构 · 识榫卯 · 习营造',(9.18,6.867,2.85),.19,'S',1,'bronze',4.5)
text('Title02_History','保国寺营造图谱',(.274,12,3.65),.43,'E',2,'ink',7)
text('Title03_Component','斗拱构件识读区',(6,23.584,3.55),.49,'S',3,'ink',7.8)
text('Title04_Workshop','斗拱铺作搭建区',(18,23.578,3.62),.52,'S',4,'ink',8)
text('Sub04_Workshop','识构 · 试合 · 成一朵铺作',(18,23.575,3.08),.20,'S',4,'bronze',6)
text('Title05_Main','保国寺宋殿木构',(18,16.872,4.25),.56,'S',5,'ink',8)
text('Sub05_Main','以榫卯相接 · 见木构之美',(18,16.868,3.63),.22,'S',5,'bronze',6)
text('Title06_Challenge','大殿拼搭挑战区',(35.704,19,3.75),.54,'W',6,'ink',8)
text('Sub06_Challenge','120秒 · 让木构归位',(35.700,19,3.10),.23,'W',6,'bronze',6)
text('Title07_Results','木构共创成果区',(35.556,5.1,3.35),.43,'W',7,'ink',6)
text('Title08_Quiet','听木 · 静观',(14.8,6.872,2.9),.35,'S',8,'ink',4)
text('Wayfinding_Exit','出口',(30,.264,3.62),.30,'N',7,'ink',1.2)

# Add a restrained main-hall rear bench on the west wall, outside the 2.4m walking band.
box('Main_WestBench',(12.38,12,.22),(.48,5.5,.44),'lightstone','Fixtures',5,.018,True)
for zone,loc in [(1,(3.4,4.8,.02)),(2,(5,12,.02)),(3,(6,19,.02)),(4,(18.5,19.0,.02)),(5,(14,9,.02)),(6,(27,13,.02)),(7,(29,4,.02)),(8,(18.5,4,.02))]:
 ob=bpy.data.objects.new(f'VR_Teleport_Zone{zone:02}',None);category('VR').objects.link(ob);ob.parent=parent('VR',zone);ob.location=loc;ob.empty_display_type='CIRCLE';ob.empty_display_size=.35
 ob['用途']='仅定位锚点，Unity中绑定瞬移/交互；不是已实现的游戏逻辑'

# 09 / route clearance audit against wall, screen and exhibit bounding boxes.
route=[(6,.35),(6,1.2),(3.4,1.2),(3.4,5.5),(5,6),(5,11),(6,13),(5,16),(5,18.2),(4.5,19),(6,19),(10.7,20),(12.5,20),(17.7,19.6),(18.5,17.8),(18.5,15.5),(13.7,15.2),(13.7,8.5),(22,8.5),(22,11.5),(25.5,11.5),(26.7,14.7),(30.5,14.7),(30.5,11),(30.5,9),(28.5,7),(28.5,4.2),(30,2),(30,.35)]
hits=[]
for a,b in zip(route,route[1:]):
 count=max(1,int(math.dist(a,b)/.10))
 for i in range(count+1):
  q=[a[k]+(b[k]-a[k])*i/count for k in [0,1]]
  for n,lo,hi in obstacles:
   if hi[2]<.05 or lo[2]>1.85:continue
   if all(lo[k]-.30<q[k]<hi[k]+.30 for k in [0,1]):hits.append({'object':n,'point':[round(v,2) for v in q]})
route_report={'tested_capsule_radius_m':.30,'tested_body_height_m':1.85,'sampling_step_m':.10,'hits':hits,'clear':not hits}
(CHECK/'动线净空检查.json').write_text(json.dumps(route_report,ensure_ascii=False,indent=2))
print('ROUTE_CLEAR',not hits,'HITS',len(hits),flush=True)

# 10 / render from temporary perspective cameras. Remove all cameras and their data before saving/exporting.
def camera(loc,target,lens):
 data=bpy.data.cameras.new('TEMP_PreviewCamera');data.lens=lens;data.clip_start=.03;data.clip_end=150
 ob=bpy.data.objects.new('TEMP_PreviewCamera',data);sc.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();sc.camera=ob;return ob
view_specs=[
 ('01_主展厅_真实模型预览',(13.65,8.35,1.75),(18.9,14.1,3.05),19),
 ('02_铺作搭建区_真实模型预览',(13.6,18.1,1.75),(18.5,22.6,2.7),20),
 ('03_入口转折_真实模型预览',(2.7,1.2,1.7),(8.0,5.8,2.6),20),
 ('04_大殿挑战区_真实模型预览',(25.3,11.35,1.75),(31.4,18.8,2.8),20)]
viewport=None
for idx,(name,loc,target,lens) in enumerate(view_specs):
 cam=camera(loc,target,lens)
 if idx==0:viewport=(cam.location.copy(),cam.rotation_euler.copy())
 sc.render.filepath=str(PREV/(name+'.png'))
 print('RENDER_BEGIN',name,flush=True)
 try:bpy.ops.render.render(write_still=True)
 except Exception:
  sc.cycles.device='CPU';device='CPU';bpy.ops.render.render(write_still=True)
 print('RENDER_DONE',name,flush=True)
 bpy.data.objects.remove(cam,do_unlink=True)
 sc.camera=None

# Cutaway preview only: removed roof panels / two outer walls, restore visibility afterwards.
hidden=list(set(roof+outer_cut))
for ob in hidden:ob.hide_render=True
cam=camera((42,-28,43),(18,12,1),38)
sc.render.resolution_x=1680;sc.render.resolution_y=1120;sc.cycles.samples=32
sc.render.filepath=str(PREV/'05_去顶空间总览_真实模型预览.png')
print('RENDER_BEGIN','cutaway',flush=True);bpy.ops.render.render(write_still=True)
bpy.data.objects.remove(cam,do_unlink=True)
for ob in hidden:ob.hide_render=False
for obj in list(bpy.data.objects):
 if obj.type=='CAMERA':bpy.data.objects.remove(obj,do_unlink=True)
for s in bpy.data.scenes:s.camera=None
for data in list(bpy.data.cameras):bpy.data.cameras.remove(data)

# Store an interior perspective viewport rather than a camera.
if viewport:
 eye,rot=viewport;distance=2.0
 for screen in bpy.data.screens:
  for a in screen.areas:
   if a.type=='VIEW_3D':
    a.spaces.active.lens=22;a.spaces.active.clip_start=.03;a.spaces.active.clip_end=150
    r=a.spaces.active.region_3d;r.view_perspective='PERSP';r.view_rotation=rot.to_quaternion();r.view_distance=distance
    r.view_location=eye+rot.to_matrix()@Vector((0,0,-distance))
    a.spaces.active.shading.type='MATERIAL'
    a.spaces.active.overlay.show_extras=False
bpy.ops.object.select_all(action='DESELECT');bpy.context.view_layer.objects.active=None
for im in bpy.data.images:
 if im.source=='FILE':im.pack();im.filepath='//../贴图/'+Path(im.filepath).name
# Converted text has no external font dependency. Remove unused font datablocks.
for f in list(bpy.data.fonts):
 if f.users==0 and f.name!='Bfont':bpy.data.fonts.remove(f)
sc['交付说明']='无摄像机；1 Blender单位=1m；台面留空；所有导视文字已转网格；游戏逻辑待Unity接入。'
sc['外轮廓_m']=[36,24];sc['墙面文字数量']=len(text_manifest)
sc.render.filepath='//../预览/'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT))

# FBX: export only static meshes + semantic empty anchors, exclude lights and cameras.
for ob in sc.objects:
 if ob.type=='MESH' and ob.data.users>1:ob.data=ob.data.copy()
bpy.ops.export_scene.fbx(filepath=str(FBX),use_selection=False,object_types={'MESH','EMPTY'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',bake_space_transform=False,use_mesh_modifiers=True,mesh_smooth_type='FACE',use_tspace=False,path_mode='RELATIVE',embed_textures=False,add_leaf_bones=False,bake_anim=False)

tris=0
for ob in sc.objects:
 if ob.type=='MESH':ob.data.calc_loop_triangles();tris+=len(ob.data.loop_triangles)
report={'blend':str(OUT),'fbx':str(FBX),'camera_objects':len([o for o in bpy.data.objects if o.type=='CAMERA']),'camera_datablocks':len(bpy.data.cameras),'mesh_objects':len([o for o in sc.objects if o.type=='MESH']),'triangles_instances_counted':tris,'unique_meshes':len(bpy.data.meshes),'lights':len([o for o in sc.objects if o.type=='LIGHT']),'textures':len([i for i in bpy.data.images if i.source=='FILE']),'all_file_textures_packed':all(i.packed_file for i in bpy.data.images if i.source=='FILE'),'route_clear':not hits,'render_device':device,'duration_seconds':round(time.time()-START,1),'footprint_m':[36,24],'note':'这是VR场景资产，不是Unity已接好逻辑的可运行游戏。'}
(CHECK/'场景交付检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'编辑源文件'/'墙面文字清单.json').write_text(json.dumps(text_manifest,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'编辑源文件'/'门洞参数.json').write_text(json.dumps(portal_manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('DELIVERY_REPORT',json.dumps(report,ensure_ascii=False),flush=True)
assert report['camera_objects']==0 and report['camera_datablocks']==0
print('BUILD_COMPLETE',flush=True)
