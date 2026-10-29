import bpy,bmesh,sys,json,math
from pathlib import Path
ROOT=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca');sys.path[:0]=[str(ROOT/'work/v5'),str(ROOT/'work/v3')]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/Hogwarts-Lago-Nero.blend'))
import stair_v5 as S
r=S.apply();r['profiles']=[{k:v for k,v in p.items() if k!='pieces'} for p in S.PROFILES]
objs=list(bpy.data.collections[S.COLLECTION].objects)
r['empty']=[o.name for o in objs if not o.data.polygons]
r['nonfinite']=[o.name for o in objs if any(not math.isfinite(c) for v in o.data.vertices for c in v.co)]
r['zero_area_faces']={o.name:sum(p.area<1e-9 for p in o.data.polygons) for o in objs}
r['mesh_edges']={}
for ob in objs:
 bm=bmesh.new();bm.from_mesh(ob.data);r['mesh_edges'][ob.name]={'boundary':sum(e.is_boundary for e in bm.edges),'nonmanifold':sum(not e.is_manifold for e in bm.edges)};bm.free()
r['node_samples']=[S.sample_path(x,y) for x,y,z in S.ROUTE_XYZ]
(ROOT/'work/v5/stair-check.json').write_text(json.dumps(r,indent=2))
print('STAIR_V5',json.dumps({k:v for k,v in r.items() if k not in ['profiles','node_samples']}),flush=True)
