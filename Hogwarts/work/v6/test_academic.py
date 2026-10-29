import bpy,sys,json,math
from pathlib import Path
R=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca');sys.path[:0]=[str(R/'work/v6'),str(R/'work/v2')]
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/Hogwarts-scala-rifinita.blend'))
import interior_kit as I
I.init();import academic_rooms
before=set(bpy.data.objects)
r=academic_rooms.apply();new=[o for o in bpy.data.objects if o not in before]
r['empty']=[o.name for o in new if o.type=='MESH' and not o.data.polygons]
r['nonfinite']=[o.name for o in new if o.type=='MESH' and any(not math.isfinite(c) for v in o.data.vertices for c in v.co)]
r['bbox_world']={c.name:([min((o.matrix_world@v.co)[k] for o in c.all_objects if o.type=='MESH' for v in o.data.vertices) for k in range(3)],[max((o.matrix_world@v.co)[k] for o in c.all_objects if o.type=='MESH' for v in o.data.vertices) for k in range(3)]) for c in [bpy.data.collections[n] for n in ['62 • Biblioteca','63 • Aula Pozioni','64 • Infermeria','65 • Aula Trasfigurazione']]}
(R/'work/v6/academic-check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
print('ACADEMIC_OK',json.dumps({k:v for k,v in r.items() if k not in ['rooms','bbox_world']},ensure_ascii=False),flush=True)
if '--preview' in sys.argv:
 s=bpy.context.scene;s.camera=bpy.data.objects['Camera | Biblioteca'];s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.adaptive_threshold=.05;s.cycles.use_denoising=True
 p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
 for dev in p.devices:dev.use=dev.type=='METAL'
 s.cycles.device='GPU';s.render.resolution_x=900;s.render.resolution_y=600;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.filepath=str(R/'work/v6/library-test.png');s.view_settings.exposure=.5
 bpy.ops.render.render(write_still=True)
