import bpy,sys,math,json,time
from pathlib import Path
from mathutils import Vector
ROOT=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca')
sys.path.insert(0,str(ROOT/'work/v2'))
import architecture as A
start=time.time()
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):bpy.data.collections.remove(c)
A.init_materials()
for module in ['landscape','south_sector','north_sector','tower_sector','west_sector']:
 print('BUILDING',module,flush=True);__import__(module).build();print('BUILT',module,len(bpy.data.objects),flush=True)
scene=bpy.context.scene
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1;scene.unit_settings.length_unit='METERS'
scene['Riferimento']='Hogwarts, modellino cinematografico HBP / Studio Tour; pianta EE2109'
scene['Perimetro']='Ricostruzione esterna dei principali settori e collegamenti; quote indicative, nessun interno completo'
scene['Disposizione']='Centri e orientamenti tracciati dalla pianta di lavorazione; dettagli ricostruiti da fotografie'
scene['Fonte pianta']='https://hogwarts4d.home.blog/2021/08/23/blueprint-appreciation-post/'
scene['Fonti fotografie']='https://www.wbstudiotour.co.uk/the-experience/explore-the-tour/art-department/'
scene['Edizione']='Seconda ricostruzione: pianta estesa HBP, non Hogwarts Legacy o Doni della Morte'
A.collection('00 • Presentazione e camere')
# Fondale neutro, esterno al modello.
floor=A.material('Studio | avorio grigio',(.40,.42,.39),.9)
A.box('Studio | piano',(-30,0,-2.2),(3000,3000,2),floor)
def aim(obj,p):obj.rotation_euler=(Vector(p)-obj.location).to_track_quat('-Z','Y').to_euler()
def camera(name,p,target,scale):
 d=bpy.data.cameras.new(name);d.type='ORTHO';d.ortho_scale=scale;d.clip_end=5000;d.clip_start=.1
 o=bpy.data.objects.new(name,d);A.CURRENT.objects.link(o);o.location=p;aim(o,target);o.hide_select=True;return o
hero=camera('Camera | insieme da sud-est',(730,-950,820),(-45,0,88),575)
back=camera('Camera | cortile Orologio e retro',(-800,-350,690),(-45,0,80),570)
close=camera('Camera | corpo principale',(470,-650,520),(22,-28,95),395)
plan=camera('Camera | pianta',(0,0,1100),(-45,0,0),570)
scene.camera=hero
for name,p,target,power,size,color in [('Luce | sole morbido',(-300,-500,900),(0,0,60),10000000,380,(1,.88,.72)),('Luce | cielo',(520,-120,600),(0,0,80),5000000,450,(.72,.86,1)),('Luce | bordo',(50,650,850),(0,0,100),11000000,350,(1,.96,.87))]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color;o=bpy.data.objects.new(name,d);A.CURRENT.objects.link(o);o.location=p;aim(o,target);o.hide_select=True
world=bpy.data.worlds.new('Cielo | neutro');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.48,.56,.63,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.25;scene.world=world
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.cycles.use_adaptive_sampling=True;scene.cycles.adaptive_threshold=.025
scene.cycles.max_bounces=6;scene.render.resolution_x=2000;scene.render.resolution_y=1600;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.view_settings.view_transform='AgX';scene.view_settings.exposure=0
scene.render.film_transparent=False
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   s=area.spaces.active;s.clip_end=5000;s.clip_start=.1;s.shading.type='MATERIAL';s.overlay.show_floor=False;s.overlay.show_axis_x=False;s.overlay.show_axis_y=False
   if s.region_3d:s.region_3d.view_location=(10,-35,90);s.region_3d.view_distance=440;s.region_3d.view_rotation=close.rotation_euler.to_quaternion();s.region_3d.view_perspective='ORTHO'
# Mantieni il file orientato sul castello; le luci e i fondali non selezionabili.
for o in bpy.data.objects:o.select_set(False)
bpy.context.preferences.filepaths.save_version=0
text=bpy.data.texts.new('LEGGIMI | Ricostruzione HBP')
text.write('HOGWARTS — RICOSTRUZIONE ESTERNA HBP\n\nSeconda versione basata sulla disposizione della pianta di lavorazione EE2109 del Principe Mezzosangue e sulle fotografie del modellino Studio Tour.\n\nIl complesso comprende il Quad abitato, Sala Grande, torre della Scalinata e ufficio di Silente, torre Orologio e cortile, ponte coperto e infermeria, Astronomia asimmetrica, cortile Durham, galleria lunga, campanili gemelli, torre centrale, ingresso e viadotto sulla gola, ponte alto, ponte sospeso, nove serre e cupola, civettaia, cerchio di pietre, rimessa barche e scalinata al lago.\n\nLe collezioni separano i settori. Quattro camere mostrano insieme, retro, corpo principale e pianta. Materiali procedurali incorporati.\n\nLimiti: non è un rilievo metrico certificato; quote e parte dei dettagli sono ricostruite. Sono rappresentati gli esterni, non tutti gli interni del castello. Finestre in gran parte applicate ai muri; logge, ponti e chiostri hanno aperture geometriche. Modello per Blender, non preparato come unico solido per stampa 3D.\n\nFonte pianta: https://hogwarts4d.home.blog/2021/08/23/blueprint-appreciation-post/\nFonte ufficiale modellino: https://www.wbstudiotour.co.uk/the-experience/explore-the-tour/art-department/\n')
report={'objects':len(bpy.data.objects),'meshes':sum(o.type=='MESH' for o in bpy.data.objects),'faces':sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'),'collections':list(bpy.data.collections.keys()),'empty_meshes':[o.name for o in bpy.data.objects if o.type=='MESH' and not o.data.polygons],'nonfinite':[o.name for o in bpy.data.objects if o.type=='MESH' and any(not math.isfinite(v) for p in o.data.vertices for v in p.co)]}
(ROOT/'work/v2/initial-check.json').write_text(json.dumps(report,indent=2))
print('GEOMETRY',report['objects'],report['faces'],'seconds',time.time()-start,flush=True)
scene.render.filepath=str(ROOT/'outputs/Hogwarts-HBP-insieme.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/Hogwarts-HBP.blend'),compress=True)
print('SAVED',flush=True)
bpy.ops.render.render(write_still=True)
print('HERO_RENDERED',flush=True)
# Vista posteriore complementare: la completezza si verifica anche dietro.
scene.camera=back;scene.render.filepath=str(ROOT/'outputs/Hogwarts-HBP-retro.png');scene.render.resolution_x=1400;scene.render.resolution_y=1100
bpy.ops.render.render(write_still=True)
print('BACK_RENDERED',flush=True)
scene.camera=close;scene.render.filepath=str(ROOT/'outputs/Hogwarts-HBP-dettaglio.png');scene.render.resolution_x=1700;scene.render.resolution_y=1400
bpy.ops.render.render(write_still=True)
print('DETAIL_RENDERED',flush=True)
