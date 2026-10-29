import bpy,sys,json
from pathlib import Path
R=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca');sys.path.insert(0,str(R/'work/v6'))
bpy.ops.wm.open_mainfile(filepath=str(R/'work/v6/Hogwarts-interni-rifinito.blend'))
import cutaway_v6
r=cutaway_v6.apply();(R/'work/v6/cutaway-check.json').write_text(json.dumps(r,indent=2))
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(R/'work/v6/Hogwarts-interni-finale-base.blend'),compress=True)
s=bpy.context.scene
for l in s.view_layers:l.use=(l.name=='Interni aperti')
bpy.context.window.view_layer=s.view_layers['Interni aperti'];s.camera=bpy.data.objects['Camera | disposizione degli interni'];s.cycles.samples=20;s.cycles.adaptive_threshold=.04;s.render.resolution_x=1400;s.render.resolution_y=1050;s.render.filepath=str(R/'work/v6/qa/interni-sezione.png')
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
for d in p.devices:d.use=d.type=='METAL'
s.cycles.device='GPU';bpy.ops.render.render(write_still=True,layer='Interni aperti')
