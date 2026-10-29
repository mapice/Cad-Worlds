import bpy,sys,json,math
from pathlib import Path
ROOT=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca');sys.path.insert(0,str(ROOT/'work/v3'))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/Hogwarts-HBP.blend'))
import details
result=details.apply()
new=[o for o in bpy.data.objects if any(c.name.startswith(('30 •','31 •','32 •')) for c in o.users_collection)]
result['empty']=[o.name for o in new if o.type=='MESH' and not o.data.polygons]
result['nonfinite']=[o.name for o in new if o.type=='MESH' and any(not math.isfinite(v) for p in o.data.vertices for v in p.co)]
(ROOT/'work/v3/details-check.json').write_text(json.dumps(result,indent=2));print('DETAILS_TEST',json.dumps(result),flush=True)
# Piccola verifica visiva ravvicinata, senza modificare il modello originale.
from mathutils import Vector
scene=bpy.context.scene;cam=scene.camera;cam.location=(170,-310,185);cam.rotation_euler=(Vector((35,-106,103))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=135
scene.render.resolution_x=1100;scene.render.resolution_y=900;scene.cycles.samples=16;scene.cycles.adaptive_threshold=.08
scene.render.filepath=str(ROOT/'work/v3/details-test.png');bpy.ops.render.render(write_still=True)
