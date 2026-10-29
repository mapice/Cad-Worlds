import bpy,sys,json,time
from pathlib import Path
R=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca');sys.path.insert(0,str(R/'work/v6'))
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/Hogwarts-scala-rifinita.blend'))
import shells_v6
t=time.time();r=shells_v6.apply();r['elapsed']=time.time()-t;r['empty']=[o.name for o in bpy.data.objects if o.type=='MESH' and not o.data.polygons]
(R/'work/v6/shell-check.json').write_text(json.dumps(r,indent=2));print('SHELL_CHECK',len(r['hollow_bodies']),len(r['window_groups']),r['portals'],r['elapsed'],r['empty'],flush=True)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(R/'work/v6/Hogwarts-involucri.blend'),compress=True)
