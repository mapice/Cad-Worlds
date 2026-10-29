import bpy,json,hashlib,math
from pathlib import Path
ROOT=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca');OUT=ROOT/'outputs'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/v4/Hogwarts-paesaggio-draft.blend'))
s=bpy.context.scene;s.cycles.samples=48;s.cycles.adaptive_threshold=.025;s.cycles.max_bounces=7;s.cycles.transparent_max_bounces=16
p=bpy.context.preferences.addons['cycles'].preferences
try:
 p.compute_device_type='METAL';p.get_devices()
 for d in p.devices:d.use=d.type=='METAL'
 s.cycles.device='GPU'
except:s.cycles.device='CPU'
s.camera=bpy.data.objects['Camera | Hogwarts dal Lago Nero'];s.render.resolution_x=2400;s.render.resolution_y=1600;s.render.filepath=str(OUT/'Hogwarts-Lago-Nero.png')
s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Hogwarts-Lago-Nero.blend'),compress=True)
print('FINAL_SAVED',flush=True)
for camera,name,w,h in [('Camera | Hogwarts dal Lago Nero','Hogwarts-Lago-Nero.png',2400,1600),('Camera | lago e colli dall’alto','Hogwarts-Lago-Nero-panorama.png',2400,1800),('Camera | rimessa e sponde','Hogwarts-Lago-Nero-riva.png',2000,1400)]:
 s.camera=bpy.data.objects[camera];s.render.resolution_x=w;s.render.resolution_y=h;s.render.filepath=str(OUT/name)
 try:bpy.ops.render.render(write_still=True)
 except RuntimeError:s.cycles.device='CPU';bpy.ops.render.render(write_still=True)
 print('RENDERED',name,flush=True)
report={'file':'Hogwarts-Lago-Nero.blend','sha256':hashlib.sha256((OUT/'Hogwarts-Lago-Nero.blend').read_bytes()).hexdigest(),'objects':len(bpy.data.objects),'mesh_objects':sum(o.type=='MESH' for o in bpy.data.objects),'faces_including_instances':sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'),'external_images':[i.name for i in bpy.data.images if i.source=='FILE' and not i.packed_file],'empty_meshes':[o.name for o in bpy.data.objects if o.type=='MESH' and not o.data.polygons]}
(ROOT/'work/v4/final-check.json').write_text(json.dumps(report,indent=2));print('FINAL_DONE',flush=True)
