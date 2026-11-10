import bpy, json, bmesh
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent
s=bpy.context.scene
o=bpy.data.objects['timber_shuatou_01']
for v in o.data.vertices:v.co.y *= .17/.15
o.data.update()
issues=[];count=0
for o in s.objects:
    if '名称' not in o:continue
    count+=1
    bm=bmesh.new();bm.from_mesh(o.data)
    if any(not e.is_manifold for e in bm.edges):issues.append(o.name)
    bm.free()
(OUT/'validation.json').write_text(json.dumps({'parts':count,'non_manifold_meshes':issues,'historical_accuracy':'unverified schematic','reference_images_packed':sum(bool(i.packed_file) for i in bpy.data.images)},indent=2))
c=s.camera
def point(target):c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler()
c.location=(5.5,-7,4.1);point((0,.25,.85));c.data.ortho_scale=5.6;s.frame_set(1)
s.render.filepath=str(OUT/'01_assembled.png');bpy.ops.render.render(write_still=True)
s.frame_set(90);point((0,.25,1.55));c.data.ortho_scale=7.1
s.render.filepath=str(OUT/'02_exploded.png');bpy.ops.render.render(write_still=True)
s.frame_set(1);c.location=(7,0,2.1);point((0,.3,.8));c.data.ortho_scale=5.4
s.render.filepath=str(OUT/'03_side.png');bpy.ops.render.render(write_still=True)
c.location=(5.5,-7,4.1);point((0,.25,.85));c.data.ortho_scale=5.6
s.render.filepath=str(OUT/'01_assembled.png')
# The current Console becomes the primary modelling viewport before saving.
a=bpy.context.area
if a and a.type=='CONSOLE':a.type='VIEW_3D'
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':
            v=a.spaces.active;v.region_3d.view_distance=6.5;v.region_3d.view_location=(0,.3,.8)
            v.region_3d.view_rotation=c.rotation_euler.to_quaternion();v.region_3d.view_perspective='ORTHO'
            v.shading.type='SOLID';v.shading.color_type='MATERIAL';v.shading.show_cavity=True;v.overlay.show_floor=False
bpy.context.view_layer.objects.active=None
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'保国寺主铺作_v01_形制草模.blend'))
(OUT/'READY').write_text('Saved and validated; all render previews generated.')
