import bpy,sys,time
from pathlib import Path
R=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca');sys.path.insert(0,str(R/'work/v6'))
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/Hogwarts-scala-rifinita.blend'))
import shells_v6 as S
for name in ['Sala Grande | muratura','Quad | ala est | muri','Astronomia | fusto a D','Silente | torretta 2 | fusto']:
 o=bpy.data.objects[name]
 for m in list(o.modifiers):o.modifiers.remove(m)
 pts=[o.matrix_world@v.co for v in o.data.vertices];z0=min(v.z for v in pts);z1=max(v.z for v in pts);base=[v for v in pts if abs(v.z-z0)<.001];poly=S.offset([(v.x,v.y) for v in base],.62 if 'Silente' in name else .78)
 print('BEFORE',name,len(pts),len(base),z0,z1,poly[:3],flush=True)
 c=S.prism_cutter('test',poly,z0+.22,z1+1);S.subtract(o,c)
 print('AFTER',name,len(o.data.vertices),len(o.data.polygons),flush=True)
