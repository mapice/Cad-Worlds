import bpy,sys,math,json,time,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca');OUT=ROOT/'outputs'
sys.path[:0]=[str(ROOT/'work/v6'),str(ROOT/'work/v3'),str(ROOT/'work/v2')]
DRAFT='--draft' in sys.argv;start=time.time()
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/v6/Hogwarts-involucri.blend'))
# Le sole parti ornamentali completamente assorbite dai vani non hanno più superfici.
absorbed=[]
for o in list(bpy.data.objects):
 if o.type=='MESH' and not o.data.polygons and o.hide_render:absorbed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
import interior_kit as I
I.init()
modules={}
for modname in ['great_hall','academic_rooms','residential_rooms','circulation_v6','connectors_v6']:
 print('BUILDING',modname,flush=True);mod=__import__(modname);modules[modname]=mod.apply();print('BUILT',modname,len(bpy.data.objects),flush=True)
# Ultimi varchi verificabili fra piani, torri e ponti.
import shells_v6 as S
bodycoll=bpy.data.collections['80 • Involucri esterni apribili'];bodies=list(bodycoll.objects)
extra=[('Uscita sul ponte alto',(29,-27.5,86),(11,4,4.5),.607),('Infermeria porta corridoio',(-33.65,-61.9,83.4),(3.2,2.1,4.2),0)]
for level in [80,93.2,99.8]:extra.append(('Scala–corridoio '+str(level),(19.2,-84,level+2),(5,15,4.2),0))
for name,center,size,ang in extra:
 c=S.box_cutter('VARCO | '+name,center,size,ang);lo,hi=S.bounds(c)
 for o in bodies:
  a,b=S.bounds(o)
  if all(b[k]>=lo[k] and a[k]<=hi[k] for k in range(3)):S.subtract(o,c)
# Le cornici del belvedere sono fasce annulari: non devono otturare la chiocciola.
poly=[(20.8+1.15*math.cos(i*math.tau/48),11.988+1.15*math.sin(i*math.tau/48)) for i in range(48)]
c=S.prism_cutter('VARCO | chiocciola belvedere',poly,158.8,204)
for o in list(bpy.data.objects):
 if o.type=='MESH' and (o.name.startswith('Astronomia | cornice belvedere') or o.name=='Astronomia | pavimento osservatorio'):S.subtract(o,c)
# Elimina la sovrapposizione fra il solaio dell'ufficio e il ballatoio superiore.
top=bpy.data.objects.get('Scalinata | ballatoio 11')
if top:
 for a in [3.55,3.87,4.19]:
  x=21.6+16.5*math.cos(a);y=-97.028+16.5*math.sin(a)
  p=[(x+2.75*math.cos(i*math.tau/48),y+2.75*math.sin(i*math.tau/48)) for i in range(48)]
  S.subtract(top,S.prism_cutter('VARCO | impronta ufficio',p,134.0,134.7))
for c in list(S.CUTTERS):bpy.data.objects.remove(c,do_unlink=True)
S.CUTTERS.clear()
# UV per tutti i nuovi arredi e le superfici ricavate dalle cavità.
import materials
new_meshes=[o for o in bpy.data.objects if o.type=='MESH' and (o.get('Interno') or o in bodies)]
materials.assign_uvs(new_meshes)
# Sviluppo continuo delle pareti della torre principale e delle torri cilindriche.
for ob in bodies:
 if not any(k in ob.name for k in ['Torre della Scalinata','Grifondoro','Silente','Torre viadotto']):continue
 if not ob.data.polygons:continue
 verts=[v.co for v in ob.data.vertices];cx=(min(v.x for v in verts)+max(v.x for v in verts))/2;cy=(min(v.y for v in verts)+max(v.y for v in verts))/2
 radius=max(math.hypot(v.x-cx,v.y-cy) for v in verts);uv=ob.data.uv_layers.active
 for face in ob.data.polygons:
  if abs(face.normal.z)>.2:continue
  angles=[math.atan2(verts[ob.data.loops[li].vertex_index].y-cy,verts[ob.data.loops[li].vertex_index].x-cx) for li in face.loop_indices]
  if max(angles)-min(angles)>math.pi:angles=[a+math.tau if a<0 else a for a in angles]
  for li,a in zip(face.loop_indices,angles):uv.data[li].uv=(a*radius,verts[ob.data.loops[li].vertex_index].z)
# Collezione di appoggio visibile soltanto nella vista aperta.
s=bpy.context.scene
cutcoll=bpy.data.collections.new('79 • Presentazione degli interni aperti');s.collection.children.link(cutcoll);I.A.CURRENT=cutcoll
I.A.M['int_display']=I.material('Interni | fondale neutro',(.33,.36,.34),.85)
I.box('Interni aperti | piano', (8,-45,52.3),(330,310,.25),'int_display')
camdata=bpy.data.cameras.new('Camera | disposizione degli interni');camdata.type='ORTHO';camdata.ortho_scale=315;camdata.clip_end=15000
cutcam=bpy.data.objects.new('Camera | disposizione degli interni',camdata);cutcoll.objects.link(cutcam);cutcam.location=(280,-340,285);cutcam.rotation_euler=(Vector((5,-45,102))-cutcam.location).to_track_quat('-Z','Y').to_euler()
I.area('Interni aperti | luce ampia',(50,-80,240),(0,-40,80),24000,95,(1,.9,.76))
# Due modalità salvate: esterno completo, oppure interni esposti.
complete=s.view_layers[0];complete.name='Modello completo'
openlayer=s.view_layers.new('Interni aperti')
def traverse(lc):
 yield lc
 for child in lc.children:yield from traverse(child)
for lc in traverse(complete.layer_collection):
 if lc.collection==cutcoll:lc.exclude=True
for lc in openlayer.layer_collection.children:
 name=lc.collection.name
 if not any(name.startswith(str(i)+' •') for i in range(60,80)):lc.exclude=True
 else:
  for child in traverse(lc):
   if 'Soffitto' in child.collection.name:child.exclude=True
openlayer.use=False;complete.use=True;bpy.context.window.view_layer=complete
s['Interni']='Sala Grande, atrio, scalinata, Grifondoro, dormitorio, ufficio Silente, biblioteca, Pozioni, Trasfigurazione, infermeria e osservatorio, collegati con corridoi e scale.'
s['Distribuzione degli interni']='Ispirata ai set, adattata all’involucro HBP: non una pianta ufficiale degli interni cinematografici.'
s['Modalità']='View Layer: Modello completo / Interni aperti. Collezioni80 e81 isolano involucri e tetti; soffitti e piani sono separati negli ambienti.'
text=bpy.data.texts.new('LEGGIMI | Interni di Hogwarts')
text.write('INTERNI DI HOGWARTS\n\nAmbientazioni iconiche arredate e collegate: SalaGrande, atrio, grande scalinata, sala comune e dormitorio di Grifondoro, ufficioSilente in tre stanze, biblioteca con ballatoi, Pozioni, Trasfigurazione, infermeria e osservatorio.\n\nLe camere interne sono nominate per ambiente. Il menu View Layer permette di scegliere Modello completo oppure Interni aperti. Nella seconda modalità gli esterni e i soffitti sono esclusi. Le collezioni80 e81 permettono anche di nascondere involucri e tetti manualmente.\n\nI passaggi fra volumi sono aperti e i solai delle scale hanno fori. Le scale sono statiche. Pavimenti, soffitti e arredi sono separati.\n\nLa ricostruzione visiva richiama i set; distribuzione e proporzioni sono adattate all’esterno del modello, non rappresentano una planimetria ufficiale completa.\n\nMateriali incorporati, nessuna immagine esterna.\n')
s.render.engine='CYCLES';s.cycles.samples=24 if DRAFT else 48;s.cycles.adaptive_threshold=.04 if DRAFT else .025;s.cycles.use_denoising=True;s.cycles.max_bounces=8;s.cycles.transmission_bounces=8;s.cycles.transparent_max_bounces=16
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
for d in p.devices:d.use=d.type=='METAL'
s.cycles.device='GPU'
s.camera=bpy.data.objects['Camera | Interno Sala Grande'];s.render.resolution_x=1200 if DRAFT else 2200;s.render.resolution_y=800 if DRAFT else 1450;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
s.render.filepath=str(ROOT/'work/v6/sala-grande-draft.png') if DRAFT else str(OUT/'Hogwarts-interni-Sala-Grande.png')
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   a=area.spaces.active;a.clip_end=15000;a.shading.type='MATERIAL';a.shading.use_scene_world=True;a.shading.use_scene_lights=True
   if a.region_3d:a.region_3d.view_perspective='CAMERA'
bpy.context.preferences.filepaths.save_version=0
path=ROOT/'work/v6/Hogwarts-interni-draft.blend' if DRAFT else OUT/'Hogwarts-interni.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
report={'modules':modules,'rooms':I.ROOMS,'absorbed_hidden_decoration':absorbed,'objects':len(bpy.data.objects),'mesh_objects':sum(o.type=='MESH' for o in bpy.data.objects),'faces':sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'),'visible_empty':[o.name for o in bpy.data.objects if o.type=='MESH' and not o.hide_render and not o.data.polygons],'external_images':[i.name for i in bpy.data.images if i.source=='FILE' and not i.packed_file],'cameras':[o.name for o in bpy.data.objects if o.type=='CAMERA']}
(ROOT/'work/v6/build-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str));print('INTERIORS_SAVED',report['objects'],report['faces'],report['visible_empty'],flush=True)
if report['visible_empty']:raise RuntimeError('Mesh visibile vuota')
bpy.ops.render.render(write_still=True);print('GREAT_HALL_RENDERED',flush=True)
s.camera=bpy.data.objects['Interni | Grande scalinata'];s.render.filepath=str(ROOT/'work/v6/scalinata-draft.png') if DRAFT else str(OUT/'Hogwarts-interni-Scalinata.png');bpy.ops.render.render(write_still=True);print('STAIRS_RENDERED',flush=True)
