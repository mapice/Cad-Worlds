import bpy,sys,json,hashlib
from pathlib import Path
R=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca')
sys.path.insert(0,str(R/'work/v4'))
import ecology_v4 as E
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/Hogwarts-interni.blend'))
s=bpy.context.scene
for vl in s.view_layers:vl.use=vl.name=='Modello completo'
bpy.context.window.view_layer=s.view_layers['Modello completo']
ground,names=E._terrain_sampler()
samples=[]
for x in range(-600,1,50):
 for y in range(-200,501,50):
  hit=ground(x,y)
  if hit:samples.append([x,y,round(hit[0],2),round(hit[1].z,3),hit[2]])
report={'cameras':[{'name':o.name,'position':list(o.location)} for o in bpy.data.objects if o.type=='CAMERA'],'terrain':samples,'ground_meshes':names,'source_sha256':hashlib.sha256((R/'outputs/Hogwarts-interni.blend').read_bytes()).hexdigest()}
(R/'work/v7/baseline.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
s.camera=bpy.data.objects['Camera | Hogwarts dal Lago Nero'];s.render.resolution_x=1400;s.render.resolution_y=950;s.render.resolution_percentage=100;s.cycles.samples=20;s.cycles.use_denoising=True
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
for d in p.devices:d.use=d.type=='METAL'
s.cycles.device='GPU';s.render.filepath=str(R/'work/v7/baseline.png');bpy.ops.render.render(write_still=True)
print('BASELINE_READY',flush=True)
