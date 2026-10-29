import bpy,math,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca')
FILE=ROOT/'work/v6/Hogwarts-interni-pronto.blend'
bpy.ops.wm.open_mainfile(filepath=str(FILE))
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
objects=[]
shells=bpy.data.collections.get('80 • Involucri esterni apribili')
if shells:objects.extend(o for o in shells.all_objects if o.type=='MESH' and len(o.data.polygons) and not o.hide_render)
part=bpy.data.collections.get('73 • Corridoi, aule e accessi • Porte e divisori delle aule')
if part:
 objects.extend(o for o in part.all_objects if o.type=='MESH' and any(s in o.name for s in ['parete','testata','ingresso est']) and not o.hide_render)
# Rimuovi duplicati conservando l'identità degli oggetti.
objects=list({o.as_pointer():o for o in objects}.values())
trees=[]
for o in objects:
 ev=o.evaluated_get(deps);me=ev.to_mesh();vs=[ev.matrix_world@v.co for v in me.vertices];fs=[tuple(p.vertices) for p in me.polygons]
 if vs and fs:trees.append((o.name,BVHTree.FromPolygons(vs,fs,all_triangles=False)))
 ev.to_mesh_clear()

tests=[]
def add(name,a,b,floor,notes=''):
 tests.append({'name':name,'a':a,'b':b,'floor':floor,'notes':notes})
# La Sala Grande e l'atrio si sovrappongono; si passa nella porzione interna comune,
# non prolungando oltre la facciata est una retta che uscirebbe dal fabbricato.
add('Sala Grande–Atrio',(27.0,-132.0),(28.8,-121.0),60.4,'Attraversamento nella zona di sovrapposizione delle cavità, verso il centro dell’atrio.')
add('Atrio–Scalinata',(28.8,-116.0),(28.8,-106.0),60.4)
for z in [73.4,80,93.2,99.8]:
 add('Scalinata–Quad y quota '+str(z),(19.2,-89.0),(19.2,-79.0),z)
 add('Scalinata–Quad raccordo x quota '+str(z),(19.2,-84.0),(14.6,-84.0),z)
add('Pozioni laterale',(14.6,-52.334),(18.0,-52.334),73.4)
add('Trasfigurazione est',(5.1,-32.6),(9.2,-32.6),73.4)
add('Infermeria dal corridoio',(-32.3,-61.9),(-35.1,-61.9),81.4)
add('Infermeria dal ponte',(-47.8,-61.9),(-40.8,-61.9),81.4)
add('Biblioteca ingresso sud',(75.6,31.4),(75.6,39.3),55.4)
add('Biblioteca laterale',(58.0,62.03),(65.0,62.03),55.4)
add('Navata–Gate',(75.6,-2.0),(75.6,5.0),60.4)
add('Navata–Centrale',(75.6,14.4),(75.6,22.5),55.4)

out=[];all_hits=[]
for t in tests:
 a=Vector((*t['a'],t['floor']+1.6));b=Vector((*t['b'],t['floor']+1.6));d=b-a;length=d.length;d.normalize();normal=Vector((-d.y,d.x,0));rays=[]
 for off in [-.65,0,.65]:
  aa=a+normal*off;bb=b+normal*off;hits=[]
  for name,tree in trees:
   hit=tree.ray_cast(aa,d,length)
   if hit[0] is not None and .01<hit[3]<length-.01:
    hits.append({'object':name,'point':list(hit[0]),'distance':float(hit[3]),'offset':off})
  rays.append({'offset':off,'from':list(aa),'to':list(bb),'hits':hits})
  for h in hits:all_hits.append({'test':t['name'],**h})
 out.append({**t,'rays':rays,'clear':not any(r['hits'] for r in rays)})
r={'source':str(FILE),'scope':'Sole pareti strutturali della collezione80 e partizioni nuove; esclusi arredi, terreno, cornici/pali esterni e scale che il coordinatore sta rifinendo. Segmenti a pavimento+1.6m, con fasce laterali±0.65m.','structural_objects':[o.name for o in objects],'tests':out,'ray_count':len(tests)*3,'obstructions':all_hits,'all_clear':not all_hits}
(ROOT/'work/v6/connectivity-check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
print('CONNECTIVITY',len(trees),'structures',r['ray_count'],'rays','clear',r['all_clear'],flush=True)
for h in all_hits:print('HIT',json.dumps(h,ensure_ascii=False),flush=True)
