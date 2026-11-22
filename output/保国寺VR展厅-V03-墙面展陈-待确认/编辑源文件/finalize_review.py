"""Complete the load-path drawing and verify the saved, camera-free review model."""
import bpy,math,json,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
root=bpy.data.objects['Art_05_E_受力']
for o in list(root.children):bpy.data.objects.remove(o,do_unlink=True)
col=bpy.data.collections['10_构造图解与壁挂模型'];texts=bpy.data.collections['11_可编辑展陈文字']
ink=bpy.data.materials['M06_墨色导视'];green=bpy.data.materials['V03_图解墨绿'];red=bpy.data.materials['V03_朱砂注记']
font=next(f for f in bpy.data.fonts if f.name.startswith('Heiti TC Medium'))
f=min((3.05-.45)/2.1,.91/1.8)*.9
def path(name,pts,mat,closed=False):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=.009;c.bevel_resolution=1;c.resolution_u=1
 s=c.splines.new('POLY');s.points.add(len(pts)-1)
 for p,xy in zip(s.points,pts):p.co=(*xy,.10,1)
 s.use_cyclic_u=closed;c.materials.append(mat);o=bpy.data.objects.new(name,c);col.objects.link(o);o.parent=root
names=['屋顶','梁架','铺作','柱','柱础'];step=1.44/4
for i,label in enumerate(names):
 y=(.72-i*step)*f;w=(1.35-i*.08)*f;h=.25*f
 path('LoadBox_'+label,[(-w/2,y-h/2),(w/2,y-h/2),(w/2,y+h/2),(-w/2,y+h/2)],green,True)
 c=bpy.data.curves.new('LoadLabel_'+label,'FONT');c.font=font;c.body=label;c.size=.12*f;c.align_x='CENTER';c.align_y='TOP_BASELINE';c.extrude=.00035;c.resolution_u=2;c.materials.append(ink)
 o=bpy.data.objects.new('LoadLabel_'+label,c);texts.objects.link(o);o.parent=root;o.location=(0,y+.07*f,.12);o['展陈文字']=label;o['可直接编辑']=True
 if i<len(names)-1:
  a=y-.15*f;b=y-(step-.13)*f
  path('LoadArrow',[(0,a),(0,b)],red);path('LoadArrowHead',[(-.035,b+.06),(0,b),(.035,b+.06)],red)
assert not [o for o in bpy.data.objects if o.type=='CAMERA'] and len(bpy.data.cameras)==0
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath,compress=True)
report=json.loads((ROOT/'检查记录/建模结果.json').read_text());report['editable_text_objects']=sum(o.type=='FONT' for o in bpy.context.scene.objects);report['final_load_path']=['屋顶','梁架','铺作','柱','柱础'];(ROOT/'检查记录/建模结果.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
runpy.run_path(str(ROOT/'编辑源文件/validate_curation.py'))
