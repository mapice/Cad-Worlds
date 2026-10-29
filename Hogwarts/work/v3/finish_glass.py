import bpy,sys,json,hashlib
from pathlib import Path
ROOT=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca');OUT=ROOT/'outputs'
sys.path.insert(0,str(ROOT/'work/v3'))
bpy.ops.wm.open_mainfile(filepath=str(OUT/'Hogwarts-HBP-dettagliato.blend'))
before=(len(bpy.data.objects),sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'))
import materials
materials.glass_material('glass')
s=bpy.context.scene;s.cycles.transparent_max_bounces=16;s.cycles.transmission_bounces=8
s.camera=bpy.data.objects['Camera | insieme da sud-est'];s.render.resolution_x=2200;s.render.resolution_y=1700;s.render.filepath=str(OUT/'Hogwarts-dettagliato-insieme.png')
bpy.context.preferences.filepaths.save_version=0
assert before==(len(bpy.data.objects),sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Hogwarts-HBP-dettagliato.blend'),compress=True)
sha=hashlib.sha256((OUT/'Hogwarts-HBP-dettagliato.blend').read_bytes()).hexdigest()
(ROOT/'work/v3/glass-final-check.json').write_text(json.dumps({'file':'Hogwarts-HBP-dettagliato.blend','sha256':sha,'geometry_unchanged':True,'objects':before[0],'faces':before[1],'only_material_changed':'glass','external_images':len([i for i in bpy.data.images if i.source=='FILE' and not i.packed_file])},indent=2))
print('GLASS_FINAL_SAVED',sha,flush=True)
for cam,name,w,h in [('Camera | insieme da sud-est','Hogwarts-dettagliato-insieme.png',2200,1700),('Camera | serre e campanili','Hogwarts-dettagliato-serre.png',1800,1400)]:
 s.camera=bpy.data.objects[cam];s.render.resolution_x=w;s.render.resolution_y=h;s.render.filepath=str(OUT/name)
 bpy.ops.render.render(write_still=True);print('RENDERED',name,flush=True)
print('GLASS_FINAL_DONE',flush=True)
