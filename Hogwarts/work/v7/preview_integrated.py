import bpy
from pathlib import Path
R=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca')
bpy.ops.wm.open_mainfile(filepath=str(R/'work/v7/Hogwarts-esterni-draft.blend'))
s=bpy.context.scene;s.cycles.samples=20;s.cycles.adaptive_threshold=.04;s.cycles.use_denoising=True;s.render.resolution_x=1200;s.render.resolution_y=850;s.render.resolution_percentage=100
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
for d in p.devices:d.use=d.type=='METAL'
s.cycles.device='GPU'
shots=[('Camera | V7 castello e Lago Nero','castello'),('Camera | V7 tenuta completa','tenuta'),('Camera | V7 Guferia e posatoi','guferia'),('Camera | V7 rimessa e barche','rimessa'),('Camera | V7 draghetti delle serre','serre'),('Camera | V7 Platano Picchiatore','platano-rifinito'),('Camera | V7 Capanna di Hagrid','hagrid-rifinita')]
for name,label in shots:
 if name not in bpy.data.objects:
  print('MISSING_CAMERA',name,flush=True);continue
 s.camera=bpy.data.objects[name];s.render.filepath=str(R/f'work/v7/qa/{label}.png');bpy.ops.render.render(write_still=True);print('PREVIEW',label,flush=True)
