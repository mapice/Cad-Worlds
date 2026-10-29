import bpy,sys,math,json
from pathlib import Path
R=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca')
sys.path.insert(0,str(R/'work/v3'))
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/Hogwarts-HBP.blend'))
before=set(bpy.data.objects);from nature import apply
report=apply();added=set(bpy.data.objects)-before
report['objects_added']=len(added);report['faces_added']=sum(len(o.data.polygons) for o in added if o.type=='MESH')
report['empty_meshes']=[o.name for o in added if o.type=='MESH' and not o.data.polygons]
report['nonfinite']=[o.name for o in added if o.type=='MESH' and any(not math.isfinite(c) for v in o.data.vertices for c in v.co)]
(R/'work/v3/nature-test.json').write_text(json.dumps(report,indent=2));print('NATURE_TEST',json.dumps(report),flush=True)
