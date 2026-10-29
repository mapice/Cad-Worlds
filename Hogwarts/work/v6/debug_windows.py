import bpy,sys
from pathlib import Path
R=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca');sys.path.insert(0,str(R/'work/v6'))
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/Hogwarts-scala-rifinita.blend'))
import shells_v6 as S
for name,prefix in [('Sala Grande | muratura','Sala Grande | vetrata'),('Astronomia | fusto a D','Astronomia | feritoia curva')]:
 o=bpy.data.objects[name]
 for m in list(o.modifiers):o.modifiers.remove(m)
 pts=[o.matrix_world@v.co for v in o.data.vertices];z0=min(v.z for v in pts);z1=max(v.z for v in pts);base=[v for v in pts if abs(v.z-z0)<.001];poly=S.offset([(v.x,v.y) for v in base],.78)
 c=S.prism_cutter('cav',poly,z0+.22,z1+1);S.subtract(o,c)
 panes=[p for p in bpy.data.objects if p.name.startswith(prefix) and ' | vetro' in p.name]
 for idx,p in enumerate(panes[:3]):
  cut=S.compound_windows('w',[p]);S.subtract(o,cut);print(name,idx,p.name,len(o.data.polygons),flush=True)
