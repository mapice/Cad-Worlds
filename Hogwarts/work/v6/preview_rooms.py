import bpy,json
from pathlib import Path
R=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca');(R/'work/v6/qa').mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'work/v6/Hogwarts-interni-pronto.blend'))
s=bpy.context.scene;s.cycles.samples=16;s.cycles.adaptive_threshold=.055;s.render.resolution_x=1000;s.render.resolution_y=700
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
for d in p.devices:d.use=d.type=='METAL'
s.cycles.device='GPU'
for name,file in [('Camera | Biblioteca','biblioteca'),('Camera | Aula Pozioni','pozioni'),('Camera | Infermeria','infermeria'),('Camera | Aula Trasfigurazione','trasfigurazione'),('Interni | Sala comune Grifondoro','grifondoro'),('Interni | Dormitorio Grifondoro','dormitorio'),('Interni | Ufficio di Silente','silente'),('Interni | Osservatorio astronomico','osservatorio')]:
 s.camera=bpy.data.objects[name];s.render.filepath=str(R/'work/v6/qa'/f'{file}.png');bpy.ops.render.render(write_still=True);print('QA_RENDERED',file,flush=True)
