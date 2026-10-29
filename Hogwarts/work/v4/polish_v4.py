import bpy,sys,math,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca');OUT=ROOT/'outputs';sys.path.insert(0,str(ROOT/'work/v3'))
DRAFT='--draft' in sys.argv
bpy.ops.wm.open_mainfile(filepath=str(OUT/'Hogwarts-Lago-Nero.blend'))
terrain=bpy.data.objects['Colli e sponde | superficie continua']
names=['Promontorio della Sala Grande | sommità','Promontorio delle serre | sommità','Scogliera della rimessa | superficie']
def tree_for(objects):
 vs=[];fs=[]
 for o in objects:
  k=len(vs);vs.extend(o.matrix_world@v.co for v in o.data.vertices);fs.extend(tuple(k+i for i in f.vertices) for f in o.data.polygons)
 return BVHTree.FromPolygons(vs,fs,all_triangles=False)
tops=[bpy.data.objects[n] for n in names];oldtree=tree_for(tops)
# Il nuovo reticolo deve passare sotto le scogliere esistenti, non ricampionarle
# quasi alla stessa quota con triangoli che possono spuntare dalla superficie.
changed=0
for v in terrain.data.vertices:
 if not(-65<v.co.x<220 and -225<v.co.y<195):continue
 hit=oldtree.ray_cast(Vector((v.co.x,v.co.y,600)),Vector((0,0,-1)),1000)
 if hit[0] is not None:
  v.co.z=min(v.co.z,-12);changed+=1
terrain.data.update();bpy.context.view_layer.update()
landtree=tree_for([terrain]+tops+[bpy.data.objects['Colline occidentali | superficie']])
col=bpy.data.collections.new('44 • Fondazioni e raccordi delle scogliere');bpy.context.scene.collection.children.link(col)
extensions=[];new=[]
for o in list(bpy.data.objects):
 if o.type!='MESH' or not o.name.startswith(('Viadotto | pila','Ponte di pietra alto | pila')):continue
 vs=[o.matrix_world@v.co for v in o.data.vertices];zmin=min(v.z for v in vs);bottom=[v for v in vs if abs(v.z-zmin)<.0005]
 if len(bottom)!=4:continue
 x=sum(v.x for v in bottom)/4;y=sum(v.y for v in bottom)/4
 hit=landtree.ray_cast(Vector((x,y,600)),Vector((0,0,-1)),1200)
 if hit[0] is None:continue
 ground=hit[0].z
 if zmin-ground<.5:continue
 bottom.sort(key=lambda v:math.atan2(v.y-y,v.x-x));lo=ground-.4
 points=[(v.x,v.y,z) for z in [lo,zmin] for v in bottom]
 faces=[(0,3,2,1),(4,5,6,7)]+[(i,(i+1)%4,(i+1)%4+4,i+4) for i in range(4)]
 me=bpy.data.meshes.new(o.name+' | fondazione');me.from_pydata(points,[],faces);me.update();ob=bpy.data.objects.new(o.name+' | fondazione',me);col.objects.link(ob);me.materials.append(bpy.data.materials['stone']);new.append(ob)
 extensions.append({'pier':o.name,'base_original':zmin,'ground':ground,'extension_bottom':lo,'height':zmin-lo})
import materials
materials.assign_uvs(new)
s=bpy.context.scene
s['Raccordo del terreno']='Nuova superficie tenuta sotto le vecchie scogliere; fondazioni dei piloni estese al fondale conservando archi e impalcato.'
# Controllo degli appoggi: la base inferiore delle estensioni entra nel terreno.
assert all(e['extension_bottom']<=e['ground'] for e in extensions)
report={'terrain_vertices_lowered':changed,'pier_extensions':extensions,'empty_meshes':[o.name for o in bpy.data.objects if o.type=='MESH' and not o.data.polygons]}
(ROOT/'work/v4/polish-check.json').write_text(json.dumps(report,indent=2))
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
for d in p.devices:d.use=d.type=='METAL'
s.cycles.device='GPU';s.cycles.samples=24 if DRAFT else 48;s.cycles.adaptive_threshold=.035 if DRAFT else .025
bpy.context.preferences.filepaths.save_version=0
s.camera=bpy.data.objects['Camera | Hogwarts dal Lago Nero'];s.render.resolution_x=2200;s.render.resolution_y=1450;s.render.filepath=str(OUT/'Hogwarts-Lago-Nero.png')
path=ROOT/'work/v4/Hogwarts-paesaggio-polished.blend' if DRAFT else OUT/'Hogwarts-Lago-Nero.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True);print('POLISHED_SAVED',report,flush=True)
if DRAFT:
 s.camera=bpy.data.objects['Camera | rimessa e sponde'];s.render.resolution_x=1200;s.render.resolution_y=840;s.render.filepath=str(ROOT/'work/v4/riva-polished-draft.png');bpy.ops.render.render(write_still=True)
else:
 for cam,name,w,h in [('Camera | Hogwarts dal Lago Nero','Hogwarts-Lago-Nero.png',2200,1450),('Camera | lago e colli dall’alto','Hogwarts-Lago-Nero-panorama.png',2200,1650),('Camera | rimessa e sponde','Hogwarts-Lago-Nero-riva.png',2000,1400)]:
  s.camera=bpy.data.objects[cam];s.render.resolution_x=w;s.render.resolution_y=h;s.render.filepath=str(OUT/name);bpy.ops.render.render(write_still=True);print('RENDERED',name,flush=True)
print('POLISHED_DONE',flush=True)
