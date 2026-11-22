import bpy,bmesh,math,json,time
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sc=bpy.context.scene
SOURCE=bpy.data.filepath
def rgb(h):
 a=[int(h[i:i+2],16)/255 for i in (1,3,5)]
 return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in a)+(1,)
def gpu():
 p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
 for d in p.devices:d.use=d.type=='METAL'
 sc.cycles.device='GPU' if any(d.type=='METAL' for d in p.devices) else 'CPU'
gpu();sc.render.engine='CYCLES';sc.cycles.samples=32;sc.cycles.use_denoising=True
sc.cycles.max_bounces=6;sc.cycles.diffuse_bounces=4
sc.view_settings.view_transform='AgX';sc.view_settings.exposure=-.8
try:sc.view_settings.look='AgX - Medium High Contrast'
except:pass
materials={}
for prefix,asset,tint,nstrength in [('M01','oak_veneer_01',(.24,.19,.15,1),.24),('M02','painted_plaster_wall',(.79,.75,.66,1),.12),('M03','granite_tile',(.72,.74,.73,1),.2)]:
 m=next(m for m in bpy.data.materials if m.name.startswith(prefix));materials[prefix]=m
 m.use_nodes=True;n=m.node_tree.nodes;n.clear();l=m.node_tree.links
 out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');l.new(bs.outputs['BSDF'],out.inputs['Surface'])
 uv=n.new('ShaderNodeUVMap');uv.uv_map='UVMap'
 # The oak photograph has vertical grain: align it with the original long-axis U mapping.
 vector=uv.outputs['UV']
 if prefix=='M01':
  sep=n.new('ShaderNodeSeparateXYZ');cmb=n.new('ShaderNodeCombineXYZ');l.new(vector,sep.inputs[0]);l.new(sep.outputs['Y'],cmb.inputs['X']);l.new(sep.outputs['X'],cmb.inputs['Y']);vector=cmb.outputs[0]
 for kind in ['Diffuse','Rough','nor_gl']:
  tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ROOT/'贴图_PBR'/f'{asset}_{kind}_2k.jpg'),check_existing=True)
  tex.image.colorspace_settings.name='sRGB' if kind=='Diffuse' else 'Non-Color';l.new(vector,tex.inputs['Vector'])
  if kind=='Diffuse':
   mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=tint
   l.new(tex.outputs['Color'],mix.inputs[1]);l.new(mix.outputs[0],bs.inputs['Base Color'])
  elif kind=='Rough':
   rem=n.new('ShaderNodeMapRange');rem.inputs['From Min'].default_value=0;rem.inputs['From Max'].default_value=1
   rem.inputs['To Min'].default_value=.48 if prefix=='M01' else .65;rem.inputs['To Max'].default_value=.86
   l.new(tex.outputs['Color'],rem.inputs['Value']);l.new(rem.outputs[0],bs.inputs['Roughness'])
  else:
   normal=n.new('ShaderNodeNormalMap');normal.uv_map='UVMap';normal.inputs['Strength'].default_value=nstrength
   l.new(tex.outputs['Color'],normal.inputs['Color']);l.new(normal.outputs['Normal'],bs.inputs['Normal'])
 m['texture_source']='https://polyhaven.com/a/'+asset;m['license']='CC0'
 # Neutral dielectric reflectance avoids a polished/plastic wood appearance.
 bs.inputs['Specular IOR Level'].default_value=.3

master=bpy.data.objects.get('Baoguosi_VR_Gallery_36x24m')
col=bpy.data.collections.new('08_新增木柱_柱础与托木');sc.collection.children.link(col)
parent=bpy.data.objects.new('Freestanding_Timber_Columns_V02',None);col.objects.link(parent);parent.parent=master
stone=next(m for m in bpy.data.materials if m.name.startswith('M04'))
def meshob(name,verts,faces,mat):
 me=bpy.data.meshes.new(name+'_Mesh');me.from_pydata(verts,[],faces);me.update();me.materials.append(mat)
 o=bpy.data.objects.new(name,me);col.objects.link(o);o.parent=parent
 uv=me.uv_layers.new(name='UVMap')
 for p in me.polygons:
  dominant=max(range(3),key=lambda i:abs(p.normal[i]));axes=[i for i in range(3) if i!=dominant]
  if dominant!=2:axes=[2,next(i for i in axes if i!=2)]
  for li in p.loop_indices:
   v=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(v[axes[0]]/2,v[axes[1]]/2)
 return o
def box(name,loc,dims,mat):
 bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
 for v in bm.verts:
  for k in range(3):v.co[k]*=dims[k]
 bmesh.ops.bevel(bm,geom=list(bm.edges),offset=.008,segments=2,affect='EDGES')
 me=bpy.data.meshes.new('temp');bm.to_mesh(me);bm.free()
 o=meshob(name,[v.co[:] for v in me.vertices],[tuple(p.vertices) for p in me.polygons],mat);bpy.data.meshes.remove(me);o.location=loc;return o
def turned(name,x,y,rings,mat,flute=False):
 n=32;verts=[];faces=[]
 for z,r in rings:
  for i in range(n):
   a=i*2*math.pi/n;rr=r*(1+.025*math.cos(a*8)) if flute else r
   verts.append((rr*math.cos(a),rr*math.sin(a),z))
 for j in range(len(rings)-1):
  for i in range(n):faces.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
 faces.extend([tuple(range(n-1,-1,-1)),tuple((len(rings)-1)*n+i for i in range(n))])
 o=meshob(name,verts,faces,mat);o.location=(x,y,0)
 uv=o.data.uv_layers.active
 for p in o.data.polygons:
  if len(p.vertices)==4:
   j=p.index//n;i=p.index%n
   for li,u,z in zip(p.loop_indices,[i/n,(i+1)/n,(i+1)/n,i/n],[rings[j][0],rings[j][0],rings[j+1][0],rings[j+1][0]]):uv.data[li].uv=(z/2,u*math.pi*.44/2)
  p.use_smooth=len(p.vertices)==4
 return o
positions={1:[(2,3.6),(9.5,5.5)],2:[(2.2,9),(9.8,9),(2.2,15),(9.8,15)],3:[(3,22.3),(9,22.3)],4:[(13.1,18),(22.8,18),(13.1,22.7),(22.8,22.7)],5:[(14.5,9.3),(21.3,9.3),(14.5,16.1),(21.3,16.1)],6:[(26,16),(34.7,16),(26,22.2),(34.7,22.2)],7:[(25.5,2.2),(33.6,2.2)],8:[(14,5.5),(22,5.5)]}
manifest=[]
for zone,points in positions.items():
 h=7.2 if zone==5 else 5.4
 for i,(x,y) in enumerate(points,1):
  code=f'TimberColumn_Z{zone:02}_{i:02}'
  turned(code+'_StoneBase',x,y,[(0,.32),(.04,.32),(.07,.29),(.14,.29),(.18,.24),(.23,.23)],stone)
  shaft=turned(code+'_Shaft',x,y,[(.23,.225),(.4,.222),(h-1,.202),(h-.49,.198)],materials['M01'],True)
  shaft['zone']=zone;shaft['role']='可编辑独立木柱；现代展厅木构意象，不作为历史测绘复原'
  box(code+'_Capital',(x,y,h-.43),(.5,.5,.16),materials['M01'])
  # Stepped cantilever corbels meet the ring beam; kept above head clearance.
  for axis in range(2):
   for tier,(length,z,thick) in enumerate([(.66,h-.30,.13),(.98,h-.17,.13),(1.18,h-.055,.10)]):
    dims=(length,.22,thick) if axis==0 else (.22,length,thick)
    box(code+f'_Corbel_{axis}_{tier}',(x,y,z),dims,materials['M01'])
  group=bpy.data.objects.new(f'ColumnGroup_Zone{zone:02}_{i:02}',None);col.objects.link(group);group.parent=parent;group.location=(x,y,0);group.empty_display_size=.3
  bpy.context.view_layer.update()
  for part in list(col.objects):
   if part.type=='MESH' and part.name.startswith(code+'_'):
    world=part.matrix_world.copy();part.parent=group;part.matrix_world=world
  manifest.append({'id':code,'zone':zone,'xy_m':[x,y],'top_m':h,'base_diameter_m':.64,'shaft_diameter_m':.45})
 # A coherent overhead ring links the columns, rather than leaving floating capitals.
 if zone in (2,4,5,6):
  xs=sorted(set(p[0] for p in points));ys=sorted(set(p[1] for p in points))
  for y in ys:box(f'ColumnRing_Z{zone:02}_X_{y}',((xs[0]+xs[-1])/2,y,h+.12),(xs[-1]-xs[0]+.6,.25,.24),materials['M01'])
  for x in xs:box(f'ColumnRing_Z{zone:02}_Y_{x}',(x,(ys[0]+ys[-1])/2,h+.12),(.25,ys[-1]-ys[0]+.6,.24),materials['M01'])
 else:
  # Short ties connect isolated column heads to the existing ceiling lattice.
  for i,(x,y) in enumerate(points):box(f'ColumnTie_Z{zone:02}_{i}',(x,y,h+.1),(1.3,.24,.2),materials['M01'])

route=[(6,.35),(6,1.2),(3.4,1.2),(3.4,5.5),(5,6),(5,11),(6,13),(5,16),(5,18.2),(4.5,19),(6,19),(10.7,20),(12.5,20),(17.7,19.6),(18.5,17.8),(18.5,15.5),(13.7,15.2),(13.7,8.5),(22,8.5),(22,11.5),(25.5,11.5),(26.7,14.7),(30.5,14.7),(30.5,11),(30.5,9),(28.5,7),(28.5,4.2),(30,2),(30,.35)]
quiet=[(8.8,3.5),(12,3.5),(18.5,3.5),(22.5,4.5),(24,4.5),(27,4.5)]
def distseg(p,a,b):
 v=Vector(b)-Vector(a);t=max(0,min(1,(Vector(p)-Vector(a)).dot(v)/v.length_squared));return (Vector(p)-Vector(a)-v*t).length
clearances=[{'id':m['id'],'nearest_route_center_m':round(min(distseg(m['xy_m'],a,b) for path in [route,quiet] for a,b in zip(path,path[1:])),3)} for m in manifest]
assert min(c['nearest_route_center_m'] for c in clearances)>.62,clearances
(ROOT/'检查记录'/'新增木柱与动线.json').write_text(json.dumps({'column_count':len(manifest),'columns':manifest,'route_clearance':clearances,'capsule_radius_m':.30,'column_base_radius_m':.32,'passed':True},ensure_ascii=False,indent=2))
# Move a pre-existing teleport point out of the new main-hall column base.
o=bpy.data.objects.get('VR_Teleport_Zone05')
if o:o.location=(15,8.4,.02)
# Remove orphaned procedural images from the delivery while retaining all user geometry.
for im in list(bpy.data.images):
 if im.users==0 and im.source=='FILE':bpy.data.images.remove(im)
for im in bpy.data.images:
 if im.source=='FILE':im.pack();im.filepath='//../贴图_PBR/'+Path(im.filepath).name
for o in list(bpy.data.objects):
 if o.type=='CAMERA':bpy.data.objects.remove(o,do_unlink=True)
for s in bpy.data.scenes:s.camera=None
for c in list(bpy.data.cameras):bpy.data.cameras.remove(c)
eye=Vector((18.1,8.1,1.75));target=Vector((18.1,14.7,3.15));rot=(target-eye).to_track_quat('-Z','Y')
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   space=area.spaces.active;space.lens=18;space.clip_start=.03;space.clip_end=200
   region=space.region_3d;region.view_perspective='PERSP';region.view_rotation=rot;region.view_distance=6.75;region.view_location=eye+rot@Vector((0,0,-6.75))
   space.shading.type='MATERIAL';space.shading.use_scene_lights=True;space.shading.use_scene_world=True
sc['V02说明']='24根木柱、石柱础、简化托木与连系梁；Poly Haven CC0实拍PBR；不含摄像机'
sc['V02源文件']=SOURCE
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'模型'/'展厅V02_可编辑PBR_无摄像机.blend'))
report={'source':SOURCE,'mesh_count':sum(o.type=='MESH' for o in sc.objects),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in sc.objects if o.type=='MESH'),'cameras':len(bpy.data.cameras),'columns':len(manifest),'real_PBR_maps':len([i for i in bpy.data.images if i.source=='FILE'])}
(ROOT/'检查记录'/'PBR场景检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('PREPARE_COMPLETE',report,flush=True)
