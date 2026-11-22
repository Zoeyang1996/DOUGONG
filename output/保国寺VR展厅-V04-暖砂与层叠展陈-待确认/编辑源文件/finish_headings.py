import bpy
if bpy.data.objects.get('Title07_Results'):bpy.data.objects['Title07_Results'].location.z=3.70
if bpy.data.objects.get('Sub04_Workshop'):
 o=bpy.data.objects['Sub04_Workshop'];o.scale*=.8;o.location.z=3.72
assert len(bpy.data.cameras)==0
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath,compress=True)
