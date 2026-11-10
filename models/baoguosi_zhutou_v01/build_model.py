"""Baoguosi column-top bracket: editable, explicitly schematic study v01.
Run with Blender --background --factory-startup --python this_file.
"""
import bpy, math, json
from pathlib import Path
from mathutils import Vector, Quaternion

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name == 'Collection': bpy.data.collections.remove(c)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'METERS'
scene['status'] = '形制研究初稿 / 非测绘复原 / 隐蔽榫卯未建'
scene['axes'] = 'X=沿檐方向; Y负向=檐外; Y正向=殿内; Z=向上'
scene['module'] = '示意模数: 材宽0.12m, 材高0.18m, 每跳0.36m; 均待测绘校核'

def collection(name):
    c=bpy.data.collections.new(name); scene.collection.children.link(c); return c
layers=[collection(n) for n in ['00_柱头与栌斗','01_第一杪_外跳偷心','02_第二杪','03_第一下昂','04_第二下昂','05_耍头与上层横栱','06_承托与槫_局部示意']]
stage=collection('90_摄影棚_非建筑构件')
refs=collection('91_参考图_已打包')
parts=[]

def wood(name,base):
    m=bpy.data.materials.new(name);m.diffuse_color=(*base,1);m.use_nodes=True
    n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');p.inputs['Roughness'].default_value=.48
    tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=3;tex.inputs['Detail'].default_value=2
    co=n.new('ShaderNodeTexCoord');v=n.new('ShaderNodeVectorMath');v.operation='MULTIPLY';v.inputs[1].default_value=(2,35,35)
    l.new(co.outputs['Generated'],v.inputs[0]);l.new(v.outputs[0],tex.inputs['Vector'])
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.18;ramp.color_ramp.elements[1].position=.82
    ramp.color_ramp.elements[0].color=(*(x*.75 for x in base),1);ramp.color_ramp.elements[1].color=(*(min(x*1.14,1) for x in base),1)
    l.new(tex.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color'])
    return m
mat_gong=wood('木材_栱_暖褐',(.38,.205,.087))
mat_dou=wood('木材_斗_浅褐',(.52,.325,.15))
mat_ang=wood('木材_昂_深褐',(.26,.115,.047))
mat_context=wood('木材_关联梁枋',(.34,.23,.135))

def register(o,name,cn,layer,mat,kind='构件'):
    o.name=name
    for c in list(o.users_collection):c.objects.unlink(o)
    layers[layer].objects.link(o);o.data.materials.append(mat)
    o['名称']=cn;o['层']=layer;o['类型']=kind;o['精度']='示意比例，非测绘尺寸';o['榫卯']='未复原隐藏节点'
    bevel=o.modifiers.new('小倒角_可调整','BEVEL');bevel.width=.004;bevel.segments=3
    o.modifiers.new('法线','WEIGHTED_NORMAL')
    parts.append(o);return o

def mesh(name,verts,faces,cn,layer,mat):
    me=bpy.data.meshes.new(name+'_mesh');me.from_pydata(verts,[],faces);me.update()
    ob=bpy.data.objects.new(name,me);scene.collection.objects.link(ob)
    return register(ob,name,cn,layer,mat)

def box(name,loc,size,cn,layer,mat=mat_context):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return register(o,name,cn,layer,mat)

def profile(name,points,width,center,axis,cn,layer,mat):
    # Extruded shaped timber. Local longitudinal coordinate is X.
    verts=[(x,s*width/2,z) for s in [-1,1] for x,z in points];n=len(points)
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    o=mesh(name,verts,faces,cn,layer,mat);o.location=center
    if axis=='Y':o.rotation_euler.z=math.pi/2
    return o

def gong(name,length,y,z,cn,layer,axis='X',x=0):
    # Flat bearing top, scooped underside with rolled/stepped ends.
    h=.18;L=length/2
    pts=[(-L,h), (L,h),(L,.115),(L*.88,.115),(L*.83,.08),(L*.69,.08),(L*.63,.025),(L*.38,0),(-L*.38,0),(-L*.63,.025),(-L*.69,.08),(-L*.83,.08),(-L*.88,.115),(-L,.115)]
    return profile(name,pts,.12,(x,y,z),axis,cn,layer,mat_gong)

def dou(name,x,y,z,cn,layer,scale=1,cross=False):
    # Three ring flared body, with actual open bearing channel(s).
    w=.23*scale;h=.14*scale
    rings=[(w*.68,0),(w,.055*scale),(w,h)]
    verts=[(sx*a/2,sy*a/2,zz) for a,zz in rings for sx,sy in [(-1,-1),(1,-1),(1,1),(-1,1)]]
    faces=[(3,2,1,0),(8,9,10,11)]
    for j in range(2):
        for k in range(4):faces.append((j*4+k,j*4+(k+1)%4,(j+1)*4+(k+1)%4,(j+1)*4+k))
    o=mesh(name,verts,faces,cn,layer,mat_dou);o.location=(x,y,z)
    # Notches are illustrative visible seats only, not historically verified joinery.
    for axis in (['X','Y'] if cross else ['X']):
        bpy.ops.mesh.primitive_cube_add(size=1,location=(x,y,z+h-.014*scale))
        cut=bpy.context.object;cut.dimensions=(w*1.2,.125*scale,.06*scale) if axis=='X' else (.125*scale,w*1.2,.06*scale)
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        mod=o.modifiers.new('示意承口','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut
        bpy.context.view_layer.objects.active=o
        bpy.ops.object.modifier_move_up(modifier=mod.name);bpy.ops.object.modifier_move_up(modifier=mod.name)
        bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
    o['承口']='可见承口为示意；槽深槽宽待核'
    return o

# Short eight-lobed column context (not a reconstructed full column).
verts=[];N=96
for z in [-1.05,0]:
    for i in range(N):
        a=i*2*math.pi/N;r=.285+.023*math.cos(8*a);verts.append((r*math.cos(a),r*math.sin(a),z))
faces=[tuple(reversed(range(N))),tuple(range(N,2*N))]+[(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)]
column=mesh('context_gualeng_column',verts,faces,'瓜棱柱头局部_外形示意',0,mat_context)
column['说明']='仅显示柱头上下关系，非完整拼合柱模型'
# Lobed capital body responds to column outline; upper seat remains schematic.
cap=dou('dou_ludou_01',0,0,0,'栌斗_形制待细化',0,scale=2.4,cross=True)
cap['待核']='瓜瓣栌斗外轮廓未复原；本版暂用简化承托体'

# First level: transverse nidagoong at wall line; no transverse arm at outer first jump.
gong('gong_nidaogong_01',.90,0,.29,'泥道栱',1)
gong('gong_huagong_tiao1_01',.95,0,.29,'华栱_第一杪',1,'Y')
for y in [-.36,0,.36]:dou('dou_jiaohu_t1_'+str(round(y,2)),0,y,.455,'交互斗_第一跳承托',1,cross=True)
for x in [-.34,.34]:dou('dou_sandou_nidao_'+str(x),x,0,.455,'散斗_泥道栱端',1)

# Second projecting arm. First exterior jump remains touxin (no lateral gong).
gong('gong_huagong_tiao2_01',1.67,0,.565,'华栱_第二杪',2,'Y')
gong('gong_mangong_center_01',1.24,0,.565,'慢栱_柱心横向',2)
for y in [-.72,.72]:
    dou('dou_jiaohu_t2_'+str(y),0,y,.735,'交互斗_第二跳',2,cross=True)
for x in [-.49,0,.49]:dou('dou_sandou_center2_'+str(x),x,0,.735,'散斗_柱心层',2)

# Long ang: low exterior head, high interior tail. Absolute profile follows reference only schematically.
def ang(name,head,tail,z,cn,layer):
    slope=.35
    pts=[(head-.17,z-.04),(head-.07,z+.155),(tail,z+.155+(tail-head)*slope),(tail,z-.035+(tail-head)*slope),(head+.18,z+.035)]
    return profile(name,pts,.15,(0,0,0),'Y',cn,layer,mat_ang)

ang('ang_xiaang_01',-1.08,1.90,.92,'下昂_第一昂_昂尾关系待核',3)
for y in [-.72,0,.72]:
    gong('gong_guazigong_l3_'+str(y),.92,y,.845,'瓜子栱_横向',3)
    for x in [-.34,.34]:dou('dou_sandou_l3_'+str(y)+'_'+str(x),x,y,1.015,'散斗',3)
dou('dou_ang_head_01',0,-1.08,1.045,'昂头承斗_示意',3,cross=True)

ang('ang_xiaang_02',-1.44,2.12,1.20,'下昂_第二昂_昂尾关系待核',4)
for y in [-1.08,-.72,0,.72]:
    gong('gong_mangong_l4_'+str(y),1.20,y,1.125,'慢栱_横向',4)
    for x in [-.47,.47]:dou('dou_sandou_l4_'+str(y)+'_'+str(x),x,y,1.295,'散斗',4)
dou('dou_ang_head_02',0,-1.44,1.33,'昂头承斗_示意',4,cross=True)

# Upper termination; a single forward shuato profile and lateral bearing arms.
profile('timber_shuatou_01',[(-1.63,0),(-1.57,.16),(.72,.16),(.72,0),(-1.37,0),(-1.48,-.06)],.17,(0,0,1.44),'Y','耍头_轮廓示意',5,mat_gong)
for y in [-1.44,-.72,0,.72]:
    gong('gong_linggong_'+str(y),.94,y,1.44,'令栱_上层横向承托',5)
    for x in [-.35,.35]:dou('dou_sandou_top_'+str(y)+'_'+str(x),x,y,1.61,'散斗_上层',5)

# Context beams intentionally cropped. Inner tail support is unfinished and explicitly labelled.
for y,z in [(-1.44,1.805),(0,1.805),(.72,1.805)]:
    box('fang_context_'+str(y),(0,y,z),(1.85,.16,.17),'承托枋_截段示意',6)
for y,z in [(-1.44,1.99),(.72,1.99)]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=.105,depth=1.90,location=(0,y,z),rotation=(0,math.pi/2,0))
    register(bpy.context.object,'tuan_context_'+str(y),'槫_空间位置示意',6,mat_context)

# Annotated inventory and exploded-view animation. Frame 90 is explanatory, not erection order.
for o in parts:
    start=o.location.copy();o['原位']=list(start)
    o.keyframe_insert(data_path='location',frame=1)
    o.location.z += o['层']*.26
    o.keyframe_insert(data_path='location',frame=90)
    o.location=start;o.keyframe_insert(data_path='location',frame=150)
scene.frame_end=150;scene.frame_set(1)
for f,n in [(1,'组合状态'),(90,'分层展开_非施工顺序'),(150,'回到组合')]:scene.timeline_markers.new(n,frame=f)

# Packed references accessible in Image Editor, also present as hidden image empties.
sources=['research/斗拱可视化资料/保国寺铺作.jpg','research/保国寺实地调研照片/37f6b9701sd1af240159492ef45c6f44.jpg','research/保国寺实地调研照片/cc7a4f051r19a9534ca0ee41238d5bc8.jpg']
for i,p in enumerate(sources):
    im=bpy.data.images.load(str(ROOT/p));im.pack()
    o=bpy.data.objects.new('参考_'+Path(p).stem,None);o.empty_display_type='IMAGE';o.data=im;o.empty_display_size=3
    refs.objects.link(o);o.location=(4+i*3,0,1)
refs.hide_viewport=True;refs.hide_render=True

readme='''保国寺前檐柱头铺作 / V01 形制研究模型
本模型是依据现有侧向示意图与现场模型照片制作的第一轮空间草模，不是测绘复原或最终科普事实底稿。
研究目标：双杪、双下昂、四跳，以及第一外跳偷心的可视表达。
尺寸：暂定材宽0.12m、材高0.18m、每跳0.36m，全部属于工作模数。
坐标：X沿檐，-Y向檐外，+Y向殿内，Z向上。原点为栌斗底面中心。
帧1/150：组合；帧90：分层展开。展开仅解释层级，不能作为真实施工装配顺序。
构件独立命名、分集合，可直接编辑。参考图已经打包到本工程。
待核重点：栌斗的瓜瓣外形；横向栱的实际层位与数量；昂斜率及两椽跨范围；昂尾与内柱铺作、下平槫的实际承托关系；耍头及衬枋头做法。
当前上层梁枋、槫仅为位置占位，未构成完整梁架系统。个别交接采用叠压/穿插占位，隐藏榫卯尚未建模。不能据此演示受力或制作加工件。
摄影棚、灯光、地台属于展示辅助，可关闭90集合。
'''
bpy.data.texts.new('请先阅读_README').write(readme)
(OUT/'模型说明.txt').write_text(readme,encoding='utf-8')

# Museum-style studio presentation.
def move_stage(o):
    for c in list(o.users_collection):c.objects.unlink(o)
    stage.objects.link(o)
def simplemat(name,color):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=.75;return m
dark=simplemat('展台_炭灰',(.028,.038,.043))
bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=1.65,depth=.10,location=(0,.15,-1.12));o=bpy.context.object;o.name='展台';move_stage(o);o.data.materials.append(dark)
be=o.modifiers.new('边缘倒角','BEVEL');be.width=.035;be.segments=3
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-1.18));o=bpy.context.object;move_stage(o);o.data.materials.append(simplemat('背景',(.052,.065,.074)))
world=bpy.data.worlds.new('Studio World');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.21,.25,.30,1);world.node_tree.nodes['Background'].inputs[1].default_value=.35
def point(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size,color in [('主光',(1,-4,7),1400,5,(1,.85,.67)),('补光',(-4,-1,3),1000,4,(.66,.79,1)),('轮廓光',(2,5,6),1700,3,(1,.89,.70))]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color
    o=bpy.data.objects.new(name,data);stage.objects.link(o);o.location=loc;point(o,(0,.2,.8))
camera_data=bpy.data.cameras.new('Camera');camera=bpy.data.objects.new('Camera',camera_data);stage.objects.link(camera)
camera.location=(5.5,-7,4.1);point(camera,(0,.25,.85));camera_data.type='ORTHO';camera_data.ortho_scale=5.6;scene.camera=camera
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=1400;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'

# Useful opening viewport: model only, all components unselected.
bpy.ops.object.select_all(action='DESELECT')
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            s=area.spaces.active;s.region_3d.view_distance=6.5;s.region_3d.view_location=(0,.3,.8)
            s.region_3d.view_rotation=camera.rotation_euler.to_quaternion();s.region_3d.view_perspective='ORTHO'
            s.shading.type='MATERIAL';s.shading.type='SOLID';s.shading.color_type='MATERIAL';s.shading.light='STUDIO';s.shading.show_shadows=True;s.shading.show_cavity=True
            s.overlay.show_floor=False;s.clip_end=100
# Hide studio from viewport, keep render enabled.
for o in stage.objects:o.hide_set(True)
scene['parts_count']=len(parts)
inventory=[{'id':o.name,'name':o['名称'],'layer':o['层'],'location':list(o.location),'status':o['精度']} for o in parts]
(OUT/'parts_manifest.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'保国寺主铺作_v01_形制草模.blend'))
scene.render.filepath=str(OUT/'01_assembled.png');bpy.ops.render.render(write_still=True)
scene.frame_set(90);camera_data.ortho_scale=7.1;point(camera,(0,.25,1.55));scene.render.filepath=str(OUT/'02_exploded.png');bpy.ops.render.render(write_still=True)
scene.frame_set(1);camera.location=(7,0,2.1);point(camera,(0,.3,.8));camera_data.ortho_scale=5.4;scene.render.filepath=str(OUT/'03_side.png');bpy.ops.render.render(write_still=True)
print('MODEL_COMPLETE',len(parts))
