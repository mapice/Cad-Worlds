import bpy,sys
from pathlib import Path
ROOT=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca');sys.path.insert(0,str(ROOT/'work/v4'))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/v4/Hogwarts-paesaggio-draft.blend'))
import environment_v4
environment_v4.setup()
s=bpy.context.scene
# Materiali corretti, stessa vista di prova: nessun salvataggio del modello.
s.camera=bpy.data.objects.get('Camera | Hogwarts dal Lago Nero.001') or bpy.data.objects['Camera | Hogwarts dal Lago Nero']
s.cycles.samples=16;s.cycles.adaptive_threshold=.05;s.render.resolution_x=1000;s.render.resolution_y=700;s.render.filepath=str(ROOT/'work/v4/colore-draft.png')
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
for d in p.devices:d.use=d.type=='METAL'
s.cycles.device='GPU'
bpy.ops.render.render(write_still=True)
