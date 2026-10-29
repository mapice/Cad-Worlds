import bpy,sys,math,json
from pathlib import Path
P=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca')
sys.path.insert(0,str(P/'work/v4'))
bpy.ops.wm.open_mainfile(filepath=str(P/'outputs/Hogwarts-HBP-dettagliato.blend'))
col=bpy.data.collections.new('40 • Paesaggio esteso');bpy.context.scene.collection.children.link(col)
vs=[];fs=[];nx=101;ny=87
coasts=[(226,-195),(212,97),(-120,-435),(-55,-710),(570,-777),(820,120),(847,-200),(904,420),(700,702),(330,618)]
for j in range(ny):
 y=-1000+j*25
 for i in range(nx):
  x=-1200+i*25;h=75+35*math.sin(x*.002)*math.cos(y*.003)
  for a,b in coasts:
   d=math.hypot(x-a,y-b)
   if d<60:h=min(h,1.1+max(0,d-35)*.9)
  vs.append((x,y,h))
for j in range(ny-1):
 for i in range(nx-1):
  a=j*nx+i;fs.extend([(a,a+1,a+nx),(a+1,a+nx+1,a+nx)])
me=bpy.data.meshes.new('Campione terreno');me.from_pydata(vs,[],fs);me.materials.append(bpy.data.materials['grass']);me.update();ob=bpy.data.objects.new('Campione | superficie',me);col.objects.link(ob)
import ecology_v4
report=ecology_v4.apply()
collections=[bpy.data.collections[n] for n in ['41 • Boschi e radure','42 • Rive e sottobosco']]
new=[o for c in collections for o in c.objects]
report['empty']=[o.name for o in new if o.type=='MESH' and not o.data.polygons]
report['nonfinite']=[o.name for o in new if o.type=='MESH' and any(not math.isfinite(q) for v in o.data.vertices for q in v.co)]
report['protected_tree_points']=[o.name for o in collections[0].objects if ecology_v4._protected(o.location.x,o.location.y)]
(P/'work/v4/ecology-test.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
print('ECOLOGY_TEST',report,flush=True)
