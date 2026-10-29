import bpy,sys,json,math,time
from pathlib import Path
from mathutils import Vector
ROOT=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca');sys.path[:0]=[str(ROOT/'work/v6'),str(ROOT/'work/v3')]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/v6/Hogwarts-interni-draft.blend'))
import shells_v6 as S
report={'frames':0,'foundation':False}
# La fondazione del Quad penetrava nel vano della torre principale.
foundation=bpy.data.objects.get('Quad | fondazione')
if foundation:
 poly=[(21.6+16.0*math.cos(i*math.tau/96),-97.028+16.0*math.sin(i*math.tau/96)) for i in range(96)]
 c=S.prism_cutter('TEMP | vano nella fondazione',poly,60.22,148);S.subtract(foundation,c);report['foundation']=True
# Le antiche cornici erano pannelli pieni: diventano cornici realmente forate.
for pane in list(bpy.data.objects):
 if pane.type!='MESH' or pane.get('Interno') or ' | vetro' not in pane.name or not pane.data.materials or pane.data.materials[0].name!='glass':continue
 frame=bpy.data.objects.get(pane.name.replace(' | vetro',' | cornice'))
 if not frame or frame.type!='MESH' or not frame.data.polygons:continue
 # Ricostruzione diretta dell'anello, senza centinaia di operazioni globali.
 outer=[frame.matrix_world@v.co for v in frame.data.vertices]
 inner=[pane.matrix_world@v.co for v in pane.data.vertices]
 n=len(outer)//2
 if len(outer)!=2*n or len(inner)!=2*n:continue
 normal=(frame.matrix_world.to_3x3()@frame.data.polygons[0].normal).normalized()
 levels=[sum(v.dot(normal) for v in outer[j*n:(j+1)*n])/n for j in [0,1]]
 inv=frame.matrix_world.inverted()
 points=[tuple(inv@v) for v in outer]
 for level in levels:
  points.extend(tuple(inv@(v+normal*(level-v.dot(normal)))) for v in inner[:n])
 faces=[]
 for i in range(n):
  j=(i+1)%n
  faces.extend([(i,j,n+j,n+i),(2*n+j,2*n+i,3*n+i,3*n+j),(n+i,n+j,3*n+j,3*n+i),(j,i,2*n+i,2*n+j)])
 me=bpy.data.meshes.new(frame.data.name+' anello aperto');me.from_pydata(points,[],faces);me.update()
 for mat in frame.data.materials:me.materials.append(mat)
 frame.data=me;report['frames']+=1

# Raccordo del piano superiore di Silente: il passaggio supera il bordo del ballatoio.
# Gli arredi restano dove sono, con il solaio principale già ritagliato.
for c in list(S.CUTTERS):bpy.data.objects.remove(c,do_unlink=True)
S.CUTTERS.clear()
# Quattrocento millimetri di piano appoggiato alla fondazione e scala oltre il suo margine.
# Le nuove pedate della navata iniziano oltre y4.5, dove finisce la fondazione.
old=[o for o in list(bpy.data.objects) if o.name.startswith('Navata | scala verso biblioteca')]
for o in old:bpy.data.objects.remove(o,do_unlink=True)
import interior_kit as I,connectors_v6 as C
I.init();I.A.CURRENT=bpy.data.collections['74 • Ingresso del viadotto e percorso biblioteca • Discesa verso la biblioteca']
C.flight('Navata | scala verso biblioteca',(75.6,14.5,55.4),(75.6,5.0,60.4),3.2)
I.box('Navata | soglia alta',(75.6,3.25,60.15),(3.2,3.5,.5),'path')
# Capi luce della scala sono già incorporati.
import materials
materials.assign_uvs([o for o in bpy.data.objects if o.type=='MESH' and (o.name.startswith('Navata | scala verso biblioteca') or o.name=='Navata | soglia alta')])
# Identificazione delle eventuali superfici ancora troppo vicine alle camere.
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();hits=[]
for cam in [o for o in bpy.data.objects if o.type=='CAMERA' and (o.name.startswith('Interni |') or o.name.startswith('Camera | Interno'))]:
 direction=cam.matrix_world.to_quaternion()@Vector((0,0,-1));r=bpy.context.scene.ray_cast(deps,cam.location,direction,distance=500)
 hits.append({'camera':cam.name,'hit':r[4].name if r[0] else None,'distance':float((r[1]-cam.location).length) if r[0] else None})
report['camera_first_hits']=hits
(ROOT/'work/v6/obstruction-check.json').write_text(json.dumps(report,indent=2))
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'work/v6/Hogwarts-interni-pronto.blend'),compress=True);print('FIXED',report['frames'],hits,flush=True)
s=bpy.context.scene;s.cycles.samples=20;s.cycles.adaptive_threshold=.04;s.render.resolution_x=1200;s.render.resolution_y=800
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
for d in p.devices:d.use=d.type=='METAL'
s.cycles.device='GPU'
for cam,file in [('Camera | Interno Sala Grande','sala-grande-corretta.png'),('Interni | Grande scalinata','scalinata-corretta.png')]:
 s.camera=bpy.data.objects[cam];s.render.filepath=str(ROOT/'work/v6'/file);bpy.ops.render.render(write_still=True);print('RENDERED',file,flush=True)
