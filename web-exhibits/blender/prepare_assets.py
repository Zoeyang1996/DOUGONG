import bpy,json
from pathlib import Path
O=Path(__file__).resolve().parent;ROOT=O.parent.parent;DEST=O.parent/'shared/models'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/baoguosi_zhutou_v01/保国寺主铺作_v01_形制草模.blend'))
bpy.context.scene.frame_set(1);bpy.ops.object.select_all(action='DESELECT')
for ob in bpy.context.scene.objects:
 if ob.type=='MESH' and '名称' in ob:
  ob.hide_set(False);ob.select_set(True)
  for mat in ob.data.materials:
   if mat:
    mat.use_nodes=True
    shader=mat.node_tree.nodes.get('Principled BSDF')
    if shader:shader.inputs['Base Color'].default_value=mat.diffuse_color;shader.inputs['Roughness'].default_value=.83
bpy.ops.export_scene.gltf(filepath=str(DEST/'baoguosi-bracket.glb'),use_selection=True,export_animations=False,export_extras=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
m=bpy.data.materials.new('暖木');m.diffuse_color=(.48,.23,.09,1);m.use_nodes=True;m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=m.diffuse_color
def cube(name,p,d):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);ob=bpy.context.object;ob.name=name;ob.dimensions=d;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);ob.data.materials.append(m);return ob
body=cube('卯口木',(0,0,0),(1.4,.6,.55));cut=cube('临时槽',(.4,0,.2),(.35,.3,.6))
bpy.context.view_layer.objects.active=body;mod=body.modifiers.new('实际卯槽','BOOLEAN');mod.object=cut;mod.operation='DIFFERENCE';bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
head=cube('榫头',(.4,0,.65),(.34,.29,.5));stem=cube('榫身',(.4,0,1.12),(.6,.6,.5))
for ob in [body,head,stem]:ob['status']='现代原理演示几何；非河姆渡出土器物复原'
bpy.ops.wm.save_as_mainfile(filepath=str(O/'榫卯原理演示.blend'))
bpy.ops.export_scene.gltf(filepath=str(DEST/'mortise-demo.glb'),export_animations=False,export_extras=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
m=bpy.data.materials.new('游戏木');m.diffuse_color=(.48,.23,.09,1);m.use_nodes=True;m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=m.diffuse_color
defs=[('栌斗',(0,0,.15),(.7,.7,.3)),('华栱',(0,0,.43),(.25,1.35,.24)),('横栱',(0,0,.68),(1.5,.25,.24)),('承斗左',(-.56,0,.9),(.28,.32,.22)),('承斗右',(.56,0,.9),(.28,.32,.22)),('上层枋',(0,0,1.15),(1.9,.3,.24)),('内承斗',(0,-.5,.7),(.3,.3,.3)),('外承斗',(0,.5,.7),(.3,.3,.3)),('纵向上栱',(0,0,1.4),(.26,1.8,.22)),('顶枋',(0,0,1.63),(2.15,.25,.22))]
for i,(n,p,d) in enumerate(defs):
 ob=cube('part_%02d'%i,p,d);ob['label']=n;ob['status']='交互占位件；非某种真实铺作的定型模型'
bpy.ops.wm.save_as_mainfile(filepath=str(O/'拼装交互占位件.blend'))
bpy.ops.export_scene.gltf(filepath=str(DEST/'assembly-demo.glb'),export_animations=False,export_extras=True)
(DEST/'model-status.json').write_text(json.dumps({'mortise-demo.glb':'已建真实卯槽，原理演示；非出土器物','baoguosi-bracket.glb':'已有形制草模网页导出，榫卯和尺寸待核','assembly-demo.glb':'十件交互占位模型，三关使用6/8/10件；不可作为真实铺作科普定稿'},ensure_ascii=False,indent=2),encoding='utf-8')
print('ASSETS_READY')
