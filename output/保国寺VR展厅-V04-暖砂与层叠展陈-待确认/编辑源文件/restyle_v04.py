"""Restyle the user's V03 in place in memory; save a separate, unbaked V04.
Warm sandstone / aged paper / dark oak. Native geometry, not edited photographs.
"""
import bpy,bmesh,math,json,hashlib,array
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[1];sc=bpy.context.scene;SOURCE=bpy.data.filepath
def srgb(h):
 vals=[int(h[i:i+2],16)/255 for i in (1,3,5)]
 return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in vals)+(1,)
def basic(name,color,rough=.7,metal=0,emit=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=srgb(color);bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal;m.diffuse_color=srgb(color)
 if emit:bs.inputs['Emission Color'].default_value=srgb(color);bs.inputs['Emission Strength'].default_value=emit
 return m
def setflat(name,color,rough=None):
 m=bpy.data.materials.get(name)
 if not m:return
 bs=m.node_tree.nodes.get('Principled BSDF')
 if bs:
  bs.inputs['Base Color'].default_value=srgb(color)
  if rough is not None:bs.inputs['Roughness'].default_value=rough
 m.diffuse_color=srgb(color)
def tint_pbr(prefix,color):
 m=next(m for m in bpy.data.materials if m.name.startswith(prefix))
 for n in m.node_tree.nodes:
  if n.type=='MIX_RGB' and n.blend_type=='MULTIPLY':n.inputs[2].default_value=color
 return m
def multiply_surface(m,factors):
 if not m.use_nodes:return
 bs=m.node_tree.nodes.get('Principled BSDF')
 if not bs:return
 links=m.node_tree.links;slot=bs.inputs['Base Color']
 if slot.is_linked:
  old=slot.links[0].from_socket;mix=m.node_tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(*factors,1);links.new(old,mix.inputs[1]);links.new(mix.outputs[0],slot)
 else:
  col=slot.default_value[:];slot.default_value=tuple(col[i]*factors[i] for i in range(3))+(1,)

oak=tint_pbr('M01',(.145,.095,.053,1))
wall=tint_pbr('M02',(.86,.60,.33,1))
floor=tint_pbr('M03',(.60,.57,.48,1))
wall['V04色调']='暖砂黄矿物墙；保留实拍表面细节'
oak['V04色调']='深色木构，保留实拍木纹'
setflat('M04_浅矿物台面','#b5a17a',.78)
setflat('M07_深灰缝与内缩踢脚','#38372f',.86)
setflat('M11_展墙底衬','#bba16f',.92)
setflat('V03_暖白展陈纸','#dcc494',.93)
setflat('V03_挂轴绫边','#a98e61',.93)
setflat('V03_图解墨绿','#3e4a36',.85)
for m in bpy.data.materials:
 if m.name.startswith(('旧木','雕花檐枋')):multiply_surface(m,(.49,.40,.29))
 if m.name.startswith('泛黄宣纸'):multiply_surface(m,(.85,.70,.46))
paper=bpy.data.materials['V03_暖白展陈纸'];bronze=bpy.data.materials['M05_暗古铜收口'];ink=bpy.data.materials['M06_墨色导视']
ochre=basic('V04_夯土赭金','#b89a62',.92)
ochre_light=basic('V04_浅砂岩层','#cdb384',.91)
deep=basic('V04_展龛深褐底','#493b28',.84)
led=basic('V04_隐藏暖光','#ffd397',.45,emit=3.0)
warmmetal=basic('V04_旧金属细边','#866238',.48,.55)
master=bpy.data.objects['Baoguosi_VR_Gallery_36x24m']
cols={}
for key,name in [('layers','15_层叠檐线叙事墙'),('cases','16_木构展龛与工具挂墙'),('silk','17_半透宣纸纱幅'),('light','18_新增间接照明')]:
 c=bpy.data.collections.new(name);sc.collection.children.link(c);cols[key]=c
def empty(name,parent=None,key='layers'):
 o=bpy.data.objects.new(name,None);cols[key].objects.link(o);o.parent=parent;o.empty_display_size=.2;return o
def box(name,loc,dim,mat,parent=None,key='layers',bevel=.004):
 bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
 for v in bm.verts:
  for i in range(3):v.co[i]*=dim[i]
 if bevel:bmesh.ops.bevel(bm,geom=list(bm.edges),offset=min(bevel,min(dim)*.22),segments=2,affect='EDGES')
 me=bpy.data.meshes.new(name+'_Mesh');bm.to_mesh(me);bm.free();me.materials.append(mat)
 uv=me.uv_layers.new(name='UVMap')
 for p in me.polygons:
  normal=max(range(3),key=lambda i:abs(p.normal[i]));axes=sorted([i for i in range(3) if i!=normal],key=lambda i:dim[i],reverse=True)
  for li in p.loop_indices:
   v=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(v[axes[0]]/2,v[axes[1]]/2)
 o=bpy.data.objects.new(name,me);cols[key].objects.link(o);o.parent=parent;o.location=loc;return o
def curve(name,points,parent,mat=warmmetal,r=.006,key='layers',closed=False):
 data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.resolution_u=1;data.bevel_depth=r;data.bevel_resolution=1
 sp=data.splines.new('POLY');sp.points.add(len(points)-1)
 for p,c in zip(sp.points,points):p.co=(*c,1)
 sp.use_cyclic_u=closed;data.materials.append(mat);ob=bpy.data.objects.new(name,data);cols[key].objects.link(ob);ob.parent=parent;return ob
def profile(name,points,parent,mat,depth):
 # Thin extruded silhouette. All contours stay outside the article-reading area.
 n=len(points);verts=[(x,y,depth+z) for z in (0,.018) for x,y in points]
 faces=[tuple(reversed(range(n))),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 me=bpy.data.meshes.new(name+'_Mesh');me.from_pydata(verts,[],faces);me.materials.append(mat);me.update();uv=me.uv_layers.new(name='UVMap')
 for poly in me.polygons:
  for li in poly.loop_indices:
   v=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(v.x/2,v.y/2)
 o=bpy.data.objects.new(name,me);cols['layers'].objects.link(o);o.parent=parent;return o
def strip_rect(name,parent,w,h,z,mat=led):
 curve(name,[(-w/2,-h/2,z),(w/2,-h/2,z),(w/2,h/2,z),(-w/2,h/2,z)],parent,mat,.009,closed=True)
def area(name,eye,target,power,size,color=(1,.82,.57)):
 data=bpy.data.lights.new(name,'AREA');data.shape='DISK';data.size=size;data.energy=power;data.color=color
 ob=bpy.data.objects.new(name,data);cols['light'].objects.link(ob);ob.location=eye;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();return ob
panels=json.loads((ROOT/'编辑源文件/墙面展陈内容.json').read_text());lookup={p['id']:p for p in panels}
for p in panels:
 root=bpy.data.objects['Wall_'+p['id']]
 root['V04展陈色调']='暖砂、旧纸与深木'

def clear_surround(root):
 for o in list(root.children):
  if o.type=='MESH' and o.name.startswith(('PaperPanel','ShadowReveal','FineTimberEdge','BronzeEdge')):bpy.data.objects.remove(o,do_unlink=True)

layered_ids=['05_W_主展墙','02_E_沿革长卷','06_N_整殿']
for id in layered_ids:
 p=lookup[id];root=bpy.data.objects['Wall_'+id];w=p['width'];h=p['height'];clear_surround(root)
 box('NarrativeDarkReveal',(0,.01,-.026),(w+.26,h+.55,.11),oak,root)
 box('NarrativeSandField',(0,0,.025),(w+.10,h+.46,.055),paper,root)
 for xx in [-w/2-.09,w/2+.09]:box('NarrativeTimberUpright',(xx,0,.075),(.075,h+.55,.16),oak,root)
 for sign in (-1,1):
  for layer,mat in enumerate((oak,ochre,ochre_light)):
   n=40;top=[]
   for i in range(n+1):
    u=-w/2+.02+i*(w-.04)/n;t=i/n
    v=h/2+.22-layer*.063+.040*math.sin(t*math.pi*6+.25*layer)+.015*math.sin(t*math.pi*14)
    top.append((u,sign*v))
   base=sign*(h/2+.265)
   pts=[(-w/2+.02,base),(w/2-.02,base)]+list(reversed(top))
   profile('LayeredEaveBand_'+id+'_'+str(sign)+'_'+str(layer),pts,root,mat,.096-layer*.018)
 strip_rect('NarrativeWarmEdge',root,w+.23,h+.50,.012)
 # The central slim post divides image from article, not the reading surface.
 box('NarrativeDivider',(w*.115,-.06,.075),(.025,h-.58,.018),warmmetal,root)
 bpy.context.view_layer.update()
 target=root.matrix_world@Vector((0,0,0));eye=root.matrix_world@Vector((0,h/2+.25,.85))
 area('NarrativeWallWash_'+id,eye,target,70,max(1,w*.32))

# Shadow-box presentation for the three components, assembled/exploded study models,
# and a few small interpretive panels. Everything remains mounted on the walls.
case_ids=['03_N_斗','03_N_栱','03_N_昂','04_N_整朵','04_N_分解','05_N_铺作','07_E_数字传承','07_E_小拱']
for id in case_ids:
 p=lookup[id];root=bpy.data.objects['Wall_'+id];w=p['width'];h=p['height'];clear_surround(root)
 box('CaseOuterWalnut',(0,0,-.01),(w+.17,h+.16,.115),oak,root,'cases')
 box('CaseParchmentInset',(0,0,.033),(w-.025,h-.025,.035),paper,root,'cases')
 for xx in [-w/2-.025,w/2+.025]:box('CaseDeepSide',(xx,0,.115),(.075,h+.17,.22),oak,root,'cases')
 for yy in [-h/2-.04,h/2+.04]:box('CaseHeadAndFoot',(0,yy,.115),(w+.16,.075,.22),oak,root,'cases')
 art=bpy.data.objects.get('Art_'+id)
 if art:
  aw=w*.53 if w>=3.7 else w-.45;ah=h-.92 if w>=3.7 else (.67 if h<2.3 else .91)
  box('SpecimenDarkBacking',(0,0,.035),(aw+.03,ah+.08,.035),deep,art,'cases')
  for xx in [-aw/2,aw/2]:box('SpecimenFineEdge',(xx,0,.09),(.016,ah+.08,.075),warmmetal,art,'cases')
  box('SpecimenLightBar',(0,ah/2+.025,.11),(aw-.08,.016,.016),led,art,'cases')
  if id=='04_N_分解':
   for xx in [-aw*.33,aw*.33]:curve('ExplodedSupportSpine',[(xx,-ah*.46,.145),(xx,ah*.46,.145)],art,warmmetal,.005,'cases')
 strip_rect('CaseWarmReveal',root,w+.13,h+.13,.02)

# A real shallow tool display replaces the former flat tool symbol, retaining its article.
tool=bpy.data.objects['Art_04_S_工匠工具']
for o in list(tool.children):bpy.data.objects.remove(o,do_unlink=True)
box('ToolPegboard',(0,0,.10),(1.83,1.40,.055),ochre_light,tool,'cases')
for i in range(6):
 for j in range(4):
  x=-.72+i*.285;y=-.49+j*.31
  curve('PegHole',[(x+.013*math.cos(k*math.tau/16),y+.013*math.sin(k*math.tau/16),.132) for k in range(16)],tool,deep,.005,'cases',True)
box('WoodMalletHandle',(-.38,-.05,.21),(.052,.89,.052),oak,tool,'cases',.007)
box('WoodMalletHead',(-.38,.34,.24),(.52,.18,.14),oak,tool,'cases',.012)
box('TrySquareLong',(.34,.02,.22),(.045,.87,.035),warmmetal,tool,'cases')
box('TrySquareShort',(.51,-.39,.22),(.38,.045,.035),warmmetal,tool,'cases')
for k in range(7):curve('TrySquareMark',[(.317,-.32+k*.105,.243),(.349,-.32+k*.105,.243)],tool,ink,.003,'cases')
box('ToolCaseLED',(0,.69,.19),(1.7,.018,.018),led,tool,'cases')

# Small shelf-light strips lend the reused bookcases the feel of gallery cabinetry.
for group in [o for o in sc.objects if o.type=='EMPTY' and o.name.startswith('CornerBookcase_Z')]:
 for z in (1.16,1.72,2.28,2.91):box('LibraryShelfLight',(0,-.232,z-.055),(1.88,.018,.012),led,group,'cases',.002)

def sheer_material(name,color,opacity):
 m=bpy.data.materials.new(name);m.use_nodes=True;nodes=m.node_tree.nodes;nodes.clear();links=m.node_tree.links
 out=nodes.new('ShaderNodeOutputMaterial');transparent=nodes.new('ShaderNodeBsdfTransparent');bs=nodes.new('ShaderNodeBsdfPrincipled');bs.inputs['Base Color'].default_value=srgb(color);bs.inputs['Roughness'].default_value=.95
 noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=180;noise.inputs['Detail'].default_value=2
 bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.14;bump.inputs['Distance'].default_value=.002;links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs[0],bs.inputs['Normal'])
 mix=nodes.new('ShaderNodeMixShader');mix.inputs[0].default_value=opacity;links.new(transparent.outputs[0],mix.inputs[1]);links.new(bs.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],out.inputs['Surface']);m.diffuse_color=srgb(color);return m
silk=sheer_material('V04_暖宣纱_真实半透','#d4b77d',.32)
printed=sheer_material('V04_纱上淡墨','#695235',.67)
for o in sc.objects:
 if o.type=='MESH' and o.name.startswith('Screen_') and '_Paper' in o.name:o.data.materials.clear();o.data.materials.append(silk)
font=next(f for f in bpy.data.fonts if f.name.startswith('Songti SC Black'))
for i,(x,chars) in enumerate([(16.35,'木作'),(20.60,'营造')]):
 root=empty(f'HangingSilk_Z08_{i:02}',bpy.data.objects['Exhibits_Zone08'],'silk');root.location=(x,5.75,3.0);root.rotation_euler=(math.pi/2,0,0)
 w=.72;h=3.70;nx=10;ny=28;verts=[];faces=[]
 for j in range(ny+1):
  yy=-h/2+j*h/ny
  for k in range(nx+1):
   xx=-w/2+k*w/nx;zz=.018*math.sin(k/nx*math.tau+j/ny*1.8)+.008*math.sin(j/ny*math.tau*2)
   verts.append((xx,yy,zz))
 for j in range(ny):
  for k in range(nx):
   a=j*(nx+1)+k;faces.append((a,a+1,a+nx+2,a+nx+1))
 me=bpy.data.meshes.new('SheerFabricMesh');me.from_pydata(verts,[],faces);me.materials.append(silk);me.update()
 ob=bpy.data.objects.new('SheerHangingLeaf',me);cols['silk'].objects.link(ob);ob.parent=root
 for p in me.polygons:p.use_smooth=True
 for sign in (-1,1):box('SilkWeightRod',(0,sign*h/2,0),(w+.075,.025,.03),warmmetal,root,'silk',.003)
 for u in (-w*.38,w*.38):curve('SilkSuspension',[(u,h/2,0),(u,2.30,0)],root,warmmetal,.003,'silk')
 for j,ch in enumerate(chars):
  cu=bpy.data.curves.new('SilkGlyph','FONT');cu.body=ch;cu.font=font;cu.size=.39;cu.align_x='CENTER';cu.align_y='CENTER';cu.resolution_u=2;cu.materials.append(printed)
  text=bpy.data.objects.new('SilkGlyph_'+ch,cu);cols['silk'].objects.link(text);text.parent=root;text.location=(0,.58-j*.73,.04);text['展陈文字']=ch

# Keep the gallery heading clear of the deeper wall-case lintels.
if bpy.data.objects.get('Title07_Results'):bpy.data.objects['Title07_Results'].location.z=3.70
if bpy.data.objects.get('Sub04_Workshop'):
 ob=bpy.data.objects['Sub04_Workshop'];ob.scale*=.8;ob.location.z=3.72

# Preserve portable resources and keep the review file strictly camera-free.
for o in list(bpy.data.objects):
 if o.type=='CAMERA':bpy.data.objects.remove(o,do_unlink=True)
for s in bpy.data.scenes:s.camera=None
for c in list(bpy.data.cameras):bpy.data.cameras.remove(c)
for image in bpy.data.images:
 if image.source=='FILE' and not image.packed_file:image.pack()
for f in bpy.data.fonts:
 if f.users>0 and f.filepath and not f.filepath.startswith('<') and not f.packed_file:f.pack()
sc.view_settings.view_transform='AgX';sc.view_settings.exposure=-.95
sc.render.engine='CYCLES';sc.cycles.samples=32;sc.cycles.use_denoising=True;sc.cycles.max_bounces=6;sc.cycles.transparent_max_bounces=8
try:
 pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='METAL';pref.get_devices()
 for d in pref.devices:d.use=d.type=='METAL'
 sc.cycles.device='GPU'
except:sc.cycles.device='CPU'
sc['V04状态']='暖砂黄墙面与多样展陈审核稿，尚未进行本版灯光烘焙'
sc['V04来源']=SOURCE;sc['V04保留']='原空间、24根木柱、40组墙面内容、中央留空、零摄像机'
sc['V04展陈方式']='层叠檐线叙事墙 / 木构浅展龛 / 工具壁挂 / 间接光书架 / 半透悬幅'
bpy.context.preferences.filepaths.save_version=0
file=ROOT/'模型/展厅V04_暖砂黄与层叠展陈_未烘焙_无摄像机.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(file),compress=True)
report={'source':SOURCE,'source_sha256':hashlib.sha256(Path(SOURCE).read_bytes()).hexdigest(),'model':str(file),'palette':{'wall':'暖砂黄矿物墙','timber':'深木色','paper':'旧宣纸米金','floor':'暖灰石'},'layered_narrative_walls':layered_ids,'wall_shadow_boxes':case_ids,'tool_wall':True,'sheer_hangings':2,'existing_screens_made_translucent':2,'wall_articles_preserved':40,'cameras':0,'baked':False}
(ROOT/'检查记录/V04修改记录.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('V04_BUILD_COMPLETE',report,flush=True)
