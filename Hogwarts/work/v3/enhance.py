"""Terza revisione: dettagli e materiali del modello HBP studiato."""
import bpy,bmesh,sys,math,json,time,hashlib
from mathutils import Vector,noise
from pathlib import Path
ROOT=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca')
SRC=ROOT/'outputs/Hogwarts-HBP.blend'
OUT=ROOT/'outputs'
sys.path[:0]=[str(ROOT/'work/v3'),str(ROOT/'work/v2')]
DRAFT='--draft' in sys.argv or '--prepare' in sys.argv
start=time.time()
bpy.ops.wm.open_mainfile(filepath=str(SRC))
print('SOURCE_LOADED',flush=True)
# La revisione conserva ogni posizione dei corpi principali.
architecture_positions={o.name:[list(v) for v in o.matrix_world] for o in bpy.data.objects if o.type=='MESH' and any(k in o.name for k in ['Sala Grande | muratura','Torre della Scalinata | fusto','Astronomia | fusto','Centrale | corpo','Orologio | ala laterale'])}
rock_report=[]
for o in list(bpy.data.objects):
 if o.type!='MESH' or not ('pareti rocciose' in o.name) or not any(k in o.name for k in ['Promontorio','Colline occidentali']):continue
 bm=bmesh.new();bm.from_mesh(o.data)
 bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=4,use_grid_fill=True)
 bm.normal_update()
 zmin=min(v.co.z for v in bm.verts);zmax=max(v.co.z for v in bm.verts);dz=max(.1,zmax-zmin)
 for v in bm.verts:
  t=(v.co.z-zmin)/dz;envelope=math.sin(math.pi*t)**1.4
  n=v.normal.copy();n.z=0
  if n.length<1e-8:continue
  n.normalize()
  p=v.co.copy()
  broad=noise.noise(Vector((p.x*.12,p.y*.12,p.z*.075)))
  crack=noise.noise(Vector((p.x*.65,p.y*.65,p.z*.30)))
  layers=math.sin(p.z*1.6+broad*2)*.24
  v.co+=n*(broad*2.4+crack*.65+layers)*envelope
 bm.to_mesh(o.data);bm.free();o.data.update()
 for f in o.data.polygons:f.use_smooth=False
 rock_report.append({'name':o.name,'vertices':len(o.data.vertices),'faces':len(o.data.polygons)})
print('CLIFFS_REFINED',rock_report,flush=True)
# Smussature contenute sulle sole masse murarie maggiori.
beveled=0
for o in list(bpy.data.objects):
 if o.type!='MESH' or not o.data.materials:continue
 if o.data.materials[0].name not in ('stone','trim'):continue
 if not any(k in o.name.lower() for k in ['muratura','corpo','fusto','ala laterale','muri','pilastro angolare']):continue
 if max(o.dimensions)<10 or min(o.dimensions)<2:continue
 if any(m.type=='BEVEL' for m in o.modifiers):continue
 m=o.modifiers.new('Usura lieve degli spigoli','BEVEL');m.width=.07;m.segments=2;m.limit_method='ANGLE';m.angle_limit=.55
 beveled+=1
print('BEVELLED',beveled,flush=True)
import details
print('DETAILS_START',flush=True)
r1=details.apply();print('DETAILS_DONE',r1,flush=True)
import nature
print('NATURE_START',flush=True)
r2=nature.apply();print('NATURE_DONE',r2,flush=True)
import materials
print('MATERIALS_START',flush=True)
r3=materials.apply();print('MATERIALS_DONE',r3,flush=True)
scene=bpy.context.scene
# Illuminazione diurna con ombre più definite per leggere rilievi e giunti.
for name,power,size in [('Luce | sole morbido',8800000,220),('Luce | cielo',2800000,420),('Luce | bordo',7000000,300)]:
 o=bpy.data.objects.get(name)
 if o:o.data.energy=power;o.data.size=size
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.30
scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.0
# Altre due camere ravvicinate; tutte le viste precedenti restano disponibili.
presentation=bpy.data.collections.get('00 • Presentazione e camere')
def make_camera(name,position,target,scale):
 d=bpy.data.cameras.new(name);d.type='ORTHO';d.ortho_scale=scale;d.clip_start=.05;d.clip_end=5000
 o=bpy.data.objects.new(name,d);presentation.objects.link(o);o.location=position;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();o.hide_select=True;return o
near=make_camera('Camera | pietra, finestre e ardesia',(305,-430,295),(27,-82,126),215)
green=make_camera('Camera | serre e campanili',(355,255,235),(82,81,93),165)
# Appunti incorporati nel progetto.
scene['Edizione']='Terza revisione: materiali, dettagli e vegetazione sulla pianta HBP studiata'
scene['Materiali']='Materiali procedurali incorporati: conci e giunti, ardesia, legno, terreno, rocce e acqua. Nessuna immagine da scaricare.'
scene['Dettagli']='Cornici e reticoli, ferramenta, coperture, vegetazione e serre; disposizione dei principali edifici conservata.'
text=bpy.data.texts.new('LEGGIMI | Materiali e dettagli')
text.write('HOGWARTS — VERSIONE CON MATERIALI E DETTAGLI\n\nQuesta revisione mantiene la disposizione del modello HBP studiato. Aggiunge materiali procedurali incorporati, dettaglio architettonico e vegetazione.\n\nLe collezioni dei dettagli sono separate, così si possono nascondere o modificare. I materiali si modificano nell’editor Shader; le coordinate delle texture sono incluse nelle mesh. Nessuna texture esterna è richiesta.\n\nLe nuove camere mostrano pietra/finestre/tetti e serre/campanili. Il file conserva anche le viste d’insieme e posteriori.\n\nRestano i limiti della ricostruzione: esterni interpretati, altezze indicative, interni non ricostruiti integralmente; non è un modello qualificato per stampa 3D.\n')
# Verifiche concrete sul risultato geometrico e sulle dipendenze.
empty=[o.name for o in bpy.data.objects if o.type=='MESH' and not o.data.polygons]
invalid=[o.name for o in bpy.data.objects if o.type=='MESH' and any(not math.isfinite(c) for v in o.data.vertices for c in v.co)]
changed=[n for n,m in architecture_positions.items() if n not in bpy.data.objects or [list(v) for v in bpy.data.objects[n].matrix_world]!=m]
report={'objects':len(bpy.data.objects),'mesh_objects':sum(o.type=='MESH' for o in bpy.data.objects),'faces':sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'),'materials':len(bpy.data.materials),'empty_meshes':empty,'nonfinite_meshes':invalid,'changed_principal_transforms':changed,'rock_detail':rock_report,'beveled_masses':beveled,'details':r1,'nature':r2,'materials_report':r3}
(ROOT/'work/v3/build-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str))
if empty or invalid or changed:raise RuntimeError('Controllo geometrico finale fallito')
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=64;scene.cycles.use_denoising=True;scene.cycles.adaptive_threshold=.018;scene.cycles.max_bounces=7
scene.render.resolution_x=2200;scene.render.resolution_y=1700;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.camera=bpy.data.objects['Camera | insieme da sud-est'];scene.render.filepath=str(OUT/'Hogwarts-dettagliato-insieme.png')
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   s=area.spaces.active;s.shading.type='MATERIAL';s.shading.use_scene_world=False;s.shading.use_scene_lights=False
   if s.region_3d:s.region_3d.view_location=(10,-30,100);s.region_3d.view_distance=470;s.region_3d.view_rotation=scene.camera.rotation_euler.to_quaternion()
bpy.context.preferences.filepaths.save_version=0
for o in bpy.context.selected_objects:o.select_set(False)
if DRAFT:
 scene.camera=near;scene.cycles.samples=32;scene.cycles.adaptive_threshold=.04;scene.render.resolution_x=1400;scene.render.resolution_y=1100;scene.render.filepath=str(ROOT/'work/v3/ravvicinata-draft.png')
 bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'work/v3/Hogwarts-draft.blend'),compress=True)
else:
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Hogwarts-HBP-dettagliato.blend'),compress=True)
print('FINAL_SAVED',len(bpy.data.objects),'elapsed',time.time()-start,flush=True)
if '--prepare' in sys.argv:sys.exit(0)
bpy.ops.render.render(write_still=True);print('HERO_RENDERED',flush=True)
if DRAFT:sys.exit(0)
scene.camera=near;scene.render.resolution_x=2100;scene.render.resolution_y=1600;scene.render.filepath=str(OUT/'Hogwarts-dettagliato-ravvicinata.png')
bpy.ops.render.render(write_still=True);print('NEAR_RENDERED',flush=True)
scene.camera=green;scene.render.resolution_x=1800;scene.render.resolution_y=1400;scene.render.filepath=str(OUT/'Hogwarts-dettagliato-serre.png')
bpy.ops.render.render(write_still=True);print('GREENHOUSES_RENDERED',flush=True)
