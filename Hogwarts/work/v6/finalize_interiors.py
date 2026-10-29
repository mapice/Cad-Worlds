import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector
R=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca');O=R/'outputs'
bpy.ops.wm.open_mainfile(filepath=str(R/'work/v6/Hogwarts-interni-finale-base.blend'))
s=bpy.context.scene
# La sezione comprende tutta la loggia più alta senza tagliarla nel fotogramma.
cutcam=bpy.data.objects['Camera | disposizione degli interni'];cutcam.data.ortho_scale=350;cutcam.rotation_euler=(Vector((5,-45,110))-cutcam.location).to_track_quat('-Z','Y').to_euler()
for l in s.view_layers:l.use=(l.name=='Modello completo')
bpy.context.window.view_layer=s.view_layers['Modello completo']
s.camera=bpy.data.objects['Camera | Interno Sala Grande'];s.render.resolution_x=2000;s.render.resolution_y=1350;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.filepath=str(O/'Hogwarts-interni-Sala-Grande.png')
s.cycles.samples=40;s.cycles.adaptive_threshold=.025;s.cycles.use_denoising=True;s.cycles.max_bounces=8;s.cycles.transparent_max_bounces=16
p=bpy.context.preferences.addons['cycles'].preferences
try:
 p.compute_device_type='METAL';p.get_devices()
 for d in p.devices:d.use=d.type=='METAL'
 s.cycles.device='GPU'
except:s.cycles.device='CPU'
# Tutte le risorse raster referenziate sono incorporate nel progetto.
for image in bpy.data.images:
 if image.source=='FILE' and not image.packed_file:image.pack()
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Hogwarts-interni.blend'),compress=True);print('FINAL_INTERIORS_SAVED',flush=True)
shots=[
 ('Camera | Interno Sala Grande','Sala-Grande'),
 ('Interni | Grande scalinata dal ballatoio','Scalinata'),
 ('Camera | Biblioteca','Biblioteca'),
 ('Camera | Aula Pozioni','Pozioni'),
 ('Interni | Sala comune Grifondoro','Grifondoro'),
 ('Interni | Dormitorio Grifondoro','Dormitorio'),
 ('Interni | Ufficio di Silente','Silente'),
 ('Camera | Infermeria','Infermeria'),
 ('Camera | Aula Trasfigurazione','Trasfigurazione'),
 ('Interni | Osservatorio astronomico','Osservatorio'),
 ('Camera | Atrio e accesso alla scalinata','Atrio'),
]
for idx,(cam,label) in enumerate(shots):
 s.camera=bpy.data.objects[cam];s.render.resolution_x=2000 if idx==0 else 1600;s.render.resolution_y=1350 if idx==0 else 1100;s.render.filepath=str(O/f'Hogwarts-interni-{label}.png')
 bpy.ops.render.render(write_still=True);print('RENDERED',label,flush=True)
for l in s.view_layers:l.use=(l.name=='Interni aperti')
bpy.context.window.view_layer=s.view_layers['Interni aperti'];s.camera=cutcam;s.render.resolution_x=2200;s.render.resolution_y=1650;s.render.filepath=str(O/'Hogwarts-interni-sezione.png');bpy.ops.render.render(write_still=True,layer='Interni aperti');print('CUTAWAY_RENDERED',flush=True)
result={'file':'Hogwarts-interni.blend','sha256':hashlib.sha256((O/'Hogwarts-interni.blend').read_bytes()).hexdigest(),'objects':len(bpy.data.objects),'mesh_objects':sum(o.type=='MESH' for o in bpy.data.objects),'cameras':len([o for o in bpy.data.objects if o.type=='CAMERA']),'view_layers':[l.name for l in s.view_layers],'missing_external_images':[im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file],'packed_images':[im.name for im in bpy.data.images if im.packed_file],'visible_empty_meshes':[o.name for o in bpy.data.objects if o.type=='MESH' and not o.hide_render and not o.data.polygons],'rendered_rooms':[label for _,label in shots]}
(R/'work/v6/final-check.json').write_text(json.dumps(result,indent=2));print('FINAL_DONE',result,flush=True)
