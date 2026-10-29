import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca')
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/Hogwarts-Lago-Nero.blend'))
candidates=[]
for o in bpy.data.objects:
 if o.type!='MESH' or o.hide_render:continue
 if o.name in ['Colli e sponde | superficie continua','Colline occidentali | superficie','Scogliera della rimessa | superficie'] or o.name.startswith('Promontorio'):
  vs=[o.matrix_world@v.co for v in o.data.vertices];fs=[tuple(f.vertices) for f in o.data.polygons];candidates.append((o.name,BVHTree.FromPolygons(vs,fs)))
report=[]
for o in sorted([o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Viadotto | pila')],key=lambda o:o.name):
 vs=[o.matrix_world@v.co for v in o.data.vertices];x=sum(p.x for p in vs)/len(vs);y=sum(p.y for p in vs)/len(vs);base=min(p.z for p in vs)
 highest=None;source=None
 for name,bvh in candidates:
  hit=bvh.ray_cast(Vector((x,y,800)),Vector((0,0,-1)),1600)
  if hit[0] is not None and (highest is None or hit[0].z>highest):highest=hit[0].z;source=name
 gap=base-highest if highest is not None else None
 report.append({'name':o.name,'center':[x,y],'base_z':base,'ground_z':highest,'ground_source':source,'gap':gap,'gap_over_0_5':gap is None or gap>.5})
result={'piers':report,'unsupported':[r for r in report if r['gap_over_0_5']],'scope':'Raycast verticale al centro di ciascun pilone del viadotto; incluse superficie continua e scogliere originali visibili. Nessuna modifica.'}
(ROOT/'work/v4/piers-check.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
print('PIERS_CHECK',json.dumps(result,ensure_ascii=False),flush=True)
