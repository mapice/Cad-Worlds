import bpy,json,hashlib,math
from pathlib import Path
R=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca');O=R/'outputs'
bpy.ops.wm.open_mainfile(filepath=str(R/'work/v7/Hogwarts-esterni-draft.blend'))
s=bpy.context.scene
build_guard=json.loads((R/'work/v7/build-check.json').read_text())
assert s.world.name=='Cielo | foschia degli esterni aggiornati','File di lavoro precedente alla correzione dello sfondo'
assert 'Camera | V7 Guferia dettaglio gufi' in bpy.data.objects,'File di lavoro precedente alle cornici aperte'
assert build_guard['modules']['guferia_rimessa']['owlery']['clear_window_probes']==90
assert len(bpy.data.objects)==11344+build_guard['new_objects'],'File e rapporto di costruzione non corrispondono'
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
for d in p.devices:d.use=d.type=='METAL'
s.cycles.device='GPU';s.cycles.samples=32;s.cycles.adaptive_threshold=.025;s.cycles.use_denoising=True
s.camera=bpy.data.objects['Camera | V7 castello e Lago Nero'];s.render.resolution_x=2200;s.render.resolution_y=1500;s.render.resolution_percentage=100;s.render.filepath=str(O/'Hogwarts-esterni-perfezionati.png')
bpy.context.preferences.filepaths.save_version=0
path=O/'Hogwarts-esterni-perfezionati.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True);print('V7_FINAL_SAVED',flush=True)
shots=[
 ('Camera | V7 Guferia e posatoi','Hogwarts-esterni-Guferia.png',1600,1150),
 ('Camera | V7 castello e Lago Nero','Hogwarts-esterni-perfezionati.png',2200,1500),
 ('Camera | V7 tenuta completa','Hogwarts-esterni-tenuta.png',2200,1550),
 ('Camera | V7 Capanna di Hagrid','Hogwarts-esterni-Hagrid.png',1700,1200),
 ('Esterni V7 | campo di Quidditch','Hogwarts-esterni-Quidditch.png',1800,1250),
 ('Camera | V7 Platano Picchiatore','Hogwarts-esterni-Platano.png',1600,1150),
 ('Camera | V7 fontana e cortile','Hogwarts-esterni-Fontana.png',1600,1150),
 ('Camera | V7 facciata dell’Orologio','Hogwarts-esterni-Orologio.png',1600,1200),
 ('Camera | V7 rimessa e barche','Hogwarts-esterni-Rimessa.png',1700,1200),
 ('Camera | V7 draghetti delle serre','Hogwarts-esterni-Serre.png',1600,1150),
 ('Camera | V7 scala e approdo conservati','Hogwarts-esterni-scala-conservata.png',1700,1250),
]
for name,file,w,h in shots:
 s.camera=bpy.data.objects[name];s.render.resolution_x=w;s.render.resolution_y=h;s.render.filepath=str(O/file)
 bpy.ops.render.render(write_still=True);print('FINAL_RENDER',file,flush=True)
build=json.loads((R/'work/v7/build-check.json').read_text())
result={'file':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_sha256':build['source_sha256'],'protected_objects':build['protected_objects'],'protected_changed':build['protected_changed'],'objects':len(bpy.data.objects),'mesh_objects':sum(o.type=='MESH' for o in bpy.data.objects),'faces':sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'),'view_layers':[l.name for l in s.view_layers],'missing_images':[i.name for i in bpy.data.images if i.source=='FILE' and not i.packed_file],'visible_empty':[o.name for o in bpy.data.objects if o.type=='MESH' and not o.hide_render and not o.data.polygons],'rendered':[file for _,file,_,_ in shots]}
assert not result['missing_images'] and not result['visible_empty'] and not result['protected_changed']
(R/'work/v7/final-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('V7_FINAL_DONE',flush=True)
