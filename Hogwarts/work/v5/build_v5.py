import bpy,sys,math,json,hashlib,time
from pathlib import Path
from mathutils import Vector
ROOT=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca');OUT=ROOT/'outputs'
sys.path[:0]=[str(ROOT/'work/v5'),str(ROOT/'work/v3'),str(ROOT/'work/v2')]
DRAFT='--draft' in sys.argv
bpy.ops.wm.open_mainfile(filepath=str(OUT/'Hogwarts-Lago-Nero.blend'))
protected={o.name:[list(r) for r in o.matrix_world] for o in bpy.data.objects if o.type=='MESH' and any(k in o.name for k in ['Sala Grande | muratura','Torre della Scalinata | fusto','Rimessa | molo di pietra','Rimessa | muro','Viadotto | pila','Orologio | ala laterale'])}
import stair_v5,cliff_v5
r1=stair_v5.apply();print('STAIRS_DONE',r1,flush=True)
r2=cliff_v5.apply();print('ROCK_DONE',r2,flush=True)
# Le aggiunte hanno materiali e coordinate incorporati.
import materials
collections=[c for c in bpy.data.collections if c.name.startswith(('45 •','46 •'))]
new=[o for c in collections for o in c.objects if o.type=='MESH']
materials.assign_uvs(new)
changed=[n for n,m in protected.items() if n not in bpy.data.objects or [list(r) for r in bpy.data.objects[n].matrix_world]!=m]
empty=[o.name for o in new if not o.data.polygons]
nonfinite=[o.name for o in new if any(not math.isfinite(q) for v in o.data.vertices for q in v.co)]
if changed or empty or nonfinite:raise RuntimeError(str({'changed':changed,'empty':empty,'nonfinite':nonfinite}))
s=bpy.context.scene
col=bpy.data.collections.new('47 • Viste della scalinata');s.collection.children.link(col)
def camera(name,p,target,scale):
 d=bpy.data.cameras.new(name);d.type='ORTHO';d.ortho_scale=scale;d.clip_start=.1;d.clip_end=12000
 o=bpy.data.objects.new(name,d);col.objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
near=camera('Camera | scalinata superiore',(155,-235,104),(86,-136,51),65)
context=camera('Camera | scalinata e rimessa',(270,-270,118),(124,-127,37),175)
s.camera=near
s['Revisione scalinata']='Gradini proporzionati, pianerottoli e parapetti continui; raccordo superiore fuori dalla rocca; sperone locale ricostruito.'
text=bpy.data.texts.new('LEGGIMI | Scala e roccia')
text.write('SCALINATA DELLA RIMESSA — REVISIONE\n\nLa scala originale aveva alzate di circa0.67m e il primo tratto entrava nella rocca. Questa revisione sostituisce il percorso con un breve raccordo piano di uscita, rampe con alzate più proporzionate, pianerottoli e parapetti continui. Lo sperone locale è ricostruito per sostenerla senza il vecchio blocco prismatico.\n\nLe collezioni45–47 contengono scala, roccia e camere ravvicinate. I componenti vecchi sono nascosti. Castello, lago e rimessa rimangono nel medesimo file.\n\nQuote e particolari restano interpretati, come nel resto del modello.\n')
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D' and area.spaces.active.region_3d:
   a=area.spaces.active;a.clip_end=15000;a.region_3d.view_location=(106,-132,38);a.region_3d.view_distance=175;a.region_3d.view_rotation=context.rotation_euler.to_quaternion();a.region_3d.view_perspective='ORTHO'
s.render.engine='CYCLES';s.cycles.samples=24 if DRAFT else 48;s.cycles.adaptive_threshold=.04 if DRAFT else .025;s.cycles.use_denoising=True
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
for d in p.devices:d.use=d.type=='METAL'
s.cycles.device='GPU'
s.render.image_settings.file_format='PNG';s.render.resolution_percentage=100
s.render.resolution_x=1200 if DRAFT else 2000;s.render.resolution_y=900 if DRAFT else 1500
s.render.filepath=str(ROOT/'work/v5/scala-draft.png') if DRAFT else str(OUT/'Hogwarts-scala-rifinita.png')
bpy.context.preferences.filepaths.save_version=0
path=ROOT/'work/v5/Hogwarts-scala-draft.blend' if DRAFT else OUT/'Hogwarts-scala-rifinita.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
report={'stairs':r1,'rock':r2,'protected_transforms_changed':changed,'empty_meshes':empty,'nonfinite_meshes':nonfinite,'new_objects':len(new),'new_faces':sum(len(o.data.polygons) for o in new),'file':str(path)}
(ROOT/'work/v5/build-check.json').write_text(json.dumps(report,indent=2,default=str));print('SAVED',report,flush=True)
bpy.ops.render.render(write_still=True);print('DETAIL_RENDERED',flush=True)
s.camera=context;s.render.resolution_x=1200 if DRAFT else 2000;s.render.resolution_y=900 if DRAFT else 1500;s.render.filepath=str(ROOT/'work/v5/contesto-draft.png') if DRAFT else str(OUT/'Hogwarts-scala-contesto.png')
bpy.ops.render.render(write_still=True);print('CONTEXT_RENDERED',flush=True)
