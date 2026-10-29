import bpy,sys,json
from pathlib import Path
R=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca');sys.path.insert(0,str(R/'work/v7'))
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/Hogwarts-interni.blend'))
import campo_quidditch,dettagli_castello
report={'quidditch':campo_quidditch.apply(),'castle':dettagli_castello.apply()}
(R/'work/v7/first-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str))
s=bpy.context.scene
for l in s.view_layers:l.use=l.name=='Modello completo'
bpy.context.window.view_layer=s.view_layers['Modello completo']
s.cycles.samples=20;s.cycles.adaptive_threshold=.04;s.cycles.use_denoising=True;s.render.resolution_x=1200;s.render.resolution_y=850;s.render.resolution_percentage=100
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
for d in p.devices:d.use=d.type=='METAL'
s.cycles.device='GPU'
(R/'work/v7/qa').mkdir(exist_ok=True)
for name,label in [('Esterni V7 | campo di Quidditch','quidditch'),('Camera | V7 fontana e cortile','fontana'),('Camera | V7 facciata dell’Orologio','orologio')]:
 s.camera=bpy.data.objects[name];s.render.filepath=str(R/f'work/v7/qa/{label}.png');bpy.ops.render.render(write_still=True);print('PREVIEW',label,flush=True)
