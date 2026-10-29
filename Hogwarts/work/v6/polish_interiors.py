import bpy,sys,json,time
from pathlib import Path
R=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca');sys.path[:0]=[str(R/'work/v6'),str(R/'work/v3')]
bpy.ops.wm.open_mainfile(filepath=str(R/'work/v6/Hogwarts-interni-pronto.blend'))
import interior_kit as I
I.init()
import facade_cleanup,grand_stair_patch,finishing_v6
r1=facade_cleanup.apply();print('FACADE_CLEANUP',r1,flush=True)
r2=grand_stair_patch.apply();print('GRAND_STAIR_PATCH',r2,flush=True)
r3=finishing_v6.apply();print('FINISHING',r3,flush=True)
for ob in bpy.data.objects:
 if ob.type=='MESH' and ob.get('Interno') and any(m and m.name=='int_red' for m in ob.data.materials):
  for mod in ob.modifiers:
   if mod.type=='BEVEL':mod.segments=3
# Tutti i soffitti, anche quelli con il nome al plurale, si aprono nella vista dedicata.
layer=bpy.context.scene.view_layers['Interni aperti']
def visit(lc):
 yield lc
 for ch in lc.children:yield from visit(ch)
for lc in visit(layer.layer_collection):
 if 'soffitt' in lc.collection.name.lower():lc.exclude=True
for o in bpy.data.objects:
 if o.type=='LIGHT' and o.name.startswith('Interni aperti | luce'):o.data.energy=120000
s=bpy.context.scene;s.camera=bpy.data.objects['Camera | Interno Sala Grande'];bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(R/'work/v6/Hogwarts-interni-rifinito.blend'),compress=True)
report={'cleanup':r1,'stairs':r2,'finishing':r3,'objects':len(bpy.data.objects),'visible_empty':[o.name for o in bpy.data.objects if o.type=='MESH' and not o.hide_render and not o.data.polygons],'external_images':[i.name for i in bpy.data.images if i.source=='FILE' and not i.packed_file]}
(R/'work/v6/polish-check.json').write_text(json.dumps(report,indent=2,ensure_ascii=False,default=str));print('POLISHED_SAVED',flush=True)
s.cycles.samples=20;s.cycles.adaptive_threshold=.045;s.render.resolution_x=1000;s.render.resolution_y=750
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
for d in p.devices:d.use=d.type=='METAL'
s.cycles.device='GPU'
for cam,file in [('Interni | Grande scalinata dal ballatoio','scalinata-rifinita'),('Interni | Sala comune Grifondoro','grifondoro-rifinito'),('Interni | Ufficio di Silente','silente-rifinito'),('Interni | Osservatorio astronomico','osservatorio-rifinito')]:
 s.camera=bpy.data.objects[cam];s.render.filepath=str(R/'work/v6/qa'/f'{file}.png');bpy.ops.render.render(write_still=True);print('QA_RENDERED',file,flush=True)
# Una vista in sezione, con collegamenti e piani esposti.
for l in s.view_layers:l.use=(l.name=='Interni aperti')
bpy.context.window.view_layer=s.view_layers['Interni aperti'];s.camera=bpy.data.objects['Camera | disposizione degli interni'];s.render.filepath=str(R/'work/v6/qa/interni-aperti.png');bpy.ops.render.render(write_still=True,layer='Interni aperti');print('CUTAWAY_RENDERED',flush=True)
