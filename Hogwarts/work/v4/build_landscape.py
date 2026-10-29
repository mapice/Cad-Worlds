import bpy,sys,json,math,time
from pathlib import Path
ROOT=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca');OUT=ROOT/'outputs'
sys.path[:0]=[str(ROOT/'work/v4'),str(ROOT/'work/v3'),str(ROOT/'work/v2')]
DRAFT='--draft' in sys.argv
start=time.time();bpy.ops.wm.open_mainfile(filepath=str(OUT/'Hogwarts-HBP-dettagliato.blend'))
# Una fotografia delle trasformazioni delle architetture, prima del paesaggio.
protected={o.name:[list(r) for r in o.matrix_world] for o in bpy.data.objects if o.type=='MESH' and any(m and m.name in ['stone','trim','roof','roofline','window','glass','wood','iron'] for m in o.data.materials)}
import terrain_v4,ecology_v4,environment_v4
r1=terrain_v4.apply();print('TERRAIN_DONE',r1,flush=True)
r2=ecology_v4.apply();print('ECOLOGY_DONE',r2,flush=True)
r3=environment_v4.setup();print('ENVIRONMENT_DONE',r3,flush=True)
s=bpy.context.scene
s['Paesaggio esteso']='Bacino del Lago Nero, sponde opposte, colli continui e boschi per gruppi. Paesaggio interpretato raccordato alla pianta HBP.'
s['Perimetro paesaggio']='Rilievi e coste oltre il modellino ricostruiti per continuità visiva; non una carta geografica ufficiale.'
text=bpy.data.texts.new('LEGGIMI | Lago e colli')
text.write('HOGWARTS — LAGO NERO E COLLI\n\nIl file conserva il castello HBP dettagliato e amplia il paesaggio: bacino più lungo, sponda opposta, rilievi continui, boschi per gruppi, radure, rive con massi e pochi canneti.\n\nLe nuove collezioni 40–43 contengono paesaggio, vegetazione e viste. Le vecchie superfici e alberature sostituite sono nascoste, per conservarne la possibilità di confronto.\n\nIl livello del lago resta a quota0.7 del modello; edifici, ponti, molo e scalinata conservano posizione e quota. Cielo e sole sostituiscono l’allestimento di studio.\n\nCamere: Hogwarts dal Lago Nero; lago e colli dall’alto; rimessa e sponde.\n\nMateriali incorporati e modificabili, senza immagini esterne. Quote e paesaggio lontano sono interpretati: non una geografia ufficiale o un rilievo del Loch Shiel.\n')
changed=[name for name,m in protected.items() if name not in bpy.data.objects or [list(r) for r in bpy.data.objects[name].matrix_world]!=m]
empty=[o.name for o in bpy.data.objects if o.type=='MESH' and not o.data.polygons]
finite=[o.name for o in bpy.data.objects if o.type=='MESH' and any(not math.isfinite(c) for v in o.data.vertices for c in v.co)]
report={'terrain':r1,'ecology':r2,'environment':r3,'architecture_transforms_changed':changed,'empty_meshes':empty,'nonfinite_meshes':finite,'objects':len(bpy.data.objects),'mesh_faces_evaluated_sum':sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH')}
(ROOT/'work/v4/build-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str))
if changed or empty or finite:raise RuntimeError('Controllo geometrico del paesaggio fallito')
s.render.engine='CYCLES';s.cycles.samples=24 if DRAFT else 48;s.cycles.use_denoising=True;s.cycles.use_adaptive_sampling=True;s.cycles.adaptive_threshold=.04 if DRAFT else .025;s.cycles.max_bounces=7;s.cycles.transparent_max_bounces=16;s.cycles.transmission_bounces=8
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
 prefs.compute_device_type='METAL';prefs.get_devices()
 for d in prefs.devices:d.use=d.type=='METAL'
 s.cycles.device='GPU';print('DEVICE_METAL',flush=True)
except Exception as e:s.cycles.device='CPU';print('DEVICE_CPU',str(e),flush=True)
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.resolution_percentage=100
s.camera=bpy.data.objects['Camera | Hogwarts dal Lago Nero']
s.render.resolution_x=1200 if DRAFT else 2200;s.render.resolution_y=800 if DRAFT else 1450
s.render.filepath=str(ROOT/'work/v4/lago-draft.png') if DRAFT else str(OUT/'Hogwarts-Lago-Nero.png')
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   a=area.spaces.active;a.clip_end=15000;a.shading.type='MATERIAL';a.shading.use_scene_world=True;a.shading.use_scene_lights=True
   if a.region_3d:a.region_3d.view_location=(80,-40,90);a.region_3d.view_distance=1250;a.region_3d.view_rotation=s.camera.rotation_euler.to_quaternion();a.region_3d.view_perspective='PERSP'
bpy.context.preferences.filepaths.save_version=0
path=ROOT/'work/v4/Hogwarts-paesaggio-draft.blend' if DRAFT else OUT/'Hogwarts-Lago-Nero.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True);print('SAVED',str(path),'seconds',time.time()-start,flush=True)
try:bpy.ops.render.render(write_still=True)
except Exception as e:
 print('GPU_FALLBACK_CPU',str(e),flush=True);s.cycles.device='CPU';bpy.ops.render.render(write_still=True)
print('HERO_RENDERED',flush=True)
s.camera=bpy.data.objects['Camera | lago e colli dall’alto'];s.render.resolution_x=1200 if DRAFT else 2200;s.render.resolution_y=900 if DRAFT else 1650
s.render.filepath=str(ROOT/'work/v4/panorama-draft.png') if DRAFT else str(OUT/'Hogwarts-Lago-Nero-panorama.png')
bpy.ops.render.render(write_still=True);print('AERIAL_RENDERED',flush=True)

if not DRAFT:
 s.camera=bpy.data.objects['Camera | rimessa e sponde'];s.render.resolution_x=2000;s.render.resolution_y=1400;s.render.filepath=str(OUT/'Hogwarts-Lago-Nero-riva.png')
 bpy.ops.render.render(write_still=True);print('SHORE_RENDERED',flush=True)
