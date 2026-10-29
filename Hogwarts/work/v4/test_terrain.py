import bpy,sys,json,math,time
from pathlib import Path
R=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca');sys.path.insert(0,str(R/'work/v4'))
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/Hogwarts-HBP-dettagliato.blend'))
import terrain_v4
t=time.time();r=terrain_v4.apply();r['elapsed']=time.time()-t
new=bpy.data.collections['40 • Paesaggio esteso'].objects
r['empty_meshes']=[o.name for o in new if o.type=='MESH' and not o.data.polygons]
r['nonfinite']=[o.name for o in new if any(not math.isfinite(c) for v in o.data.vertices for c in v.co)]
(R/'work/v4/terrain-check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
print('TERRAIN_TEST',json.dumps(r,ensure_ascii=False),flush=True)
