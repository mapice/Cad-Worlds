import bpy,sys
from pathlib import Path
R=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca');sys.path.insert(0,str(R/'work/v7'))
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/Hogwarts-interni.blend'))
import hagrid_terreni
hagrid_terreni.apply()
s=bpy.context.scene
for l in s.view_layers:l.use=l.name=='Modello completo'
bpy.context.window.view_layer=s.view_layers['Modello completo'];s.cycles.samples=20;s.cycles.adaptive_threshold=.04;s.cycles.use_denoising=True;s.render.resolution_x=1200;s.render.resolution_y=850;s.render.resolution_percentage=100
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
for d in p.devices:d.use=d.type=='METAL'
s.cycles.device='GPU'
for name,label in [('Camera | V7 Capanna di Hagrid','hagrid'),('Camera | V7 Platano Picchiatore','platano')]:
 s.camera=bpy.data.objects[name];s.render.filepath=str(R/f'work/v7/qa/{label}.png');bpy.ops.render.render(write_still=True);print('PREVIEW',label,flush=True)
