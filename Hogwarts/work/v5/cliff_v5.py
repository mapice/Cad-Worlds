"""Sperone della scalinata: rilievo continuo e vincolato ai nuovi pianerottoli.
Applicare dopo stair_v5.apply() sulla scena del Lago Nero. Nessun salvataggio.
"""
import bpy, math
import numpy as np
from mathutils import Vector, noise
from mathutils.bvhtree import BVHTree
from mathutils.geometry import delaunay_2d_cdt

COLLECTION='46 • Sperone roccioso della scalinata'
# Il contorno copre la vecchia impronta, ma il margine basso entra nel talus e
# nell'acqua: non viene chiuso con una parete verticale da basamento.
OUTLINE=[(59,-125),(72,-104),(94,-93),(116,-89),(142,-96),(169,-112),
         (188,-125),(200,-144),(185,-158),(163,-160),(143,-148),
         (122,-157),(99,-163),(75,-161),(59,-148)]


def _smooth(t):
 t=max(0,min(1,float(t)));return t*t*(3-2*t)

def _inside(x,y,poly):
 b=False
 for i,(ax,ay) in enumerate(poly):
  bx,by=poly[(i+1)%len(poly)]
  if (ay>y)!=(by>y) and x<(bx-ax)*(y-ay)/(by-ay)+ax:b=not b
 return b

def _edge_distance(x,y):
 ds=[]
 for i,a in enumerate(OUTLINE):
  b=OUTLINE[(i+1)%len(OUTLINE)];dx=b[0]-a[0];dy=b[1]-a[1]
  t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy)))
  ds.append(math.hypot(x-a[0]-dx*t,y-a[1]-dy*t))
 return min(ds)

def _world_tree(ob):
 return BVHTree.FromPolygons([ob.matrix_world@v.co for v in ob.data.vertices],[tuple(p.vertices) for p in ob.data.polygons],all_triangles=False)


def apply():
 import stair_v5
 if bpy.data.collections.get(COLLECTION):raise RuntimeError('Sperone V5 già presente: applicare una sola volta')
 route=[tuple(float(q) for q in p) for p in stair_v5.ROUTE_XYZ]
 terrain=bpy.data.objects.get('Colli e sponde | superficie continua')
 groundtree=_world_tree(terrain) if terrain else None
 deck=bpy.data.objects.get('Scalinata V5 | gradini e sostegno continuo')
 decktree=_world_tree(deck) if deck else None
 def ground(x,y):
  hit=groundtree.ray_cast(Vector((x,y,600)),Vector((0,0,-1)),1500) if groundtree else (None,)
  return hit[0].z if hit[0] is not None else .1
 # Guide lungo il percorso: campi di quota lisci lontano dalla scala,
 # vincoli stretti solo nella sede dei gradini e pianerottoli.
 control=[]
 for a,b in zip(route,route[1:]):
  L=math.hypot(b[0]-a[0],b[1]-a[1]);N=max(2,int(L/1.8))
  for j in range(N):
   t=j/N;x=a[0]+(b[0]-a[0])*t;y=a[1]+(b[1]-a[1])*t
   info=stair_v5.sample_path(x,y);control.append((x,y,float(info['support_z'])+.07))
 info=stair_v5.sample_path(route[-1][0],route[-1][1]);control.append((*route[-1][:2],float(info['support_z'])+.07))
 cp=np.array(control,float)
 def height(x,y):
  dx=cp[:,0]-x;dy=cp[:,1]-y;d2=dx*dx+dy*dy
  # Media locale continua: nessuna selezione brusca del singolo segmento.
  weights=np.exp(-d2/(19.5**2))+.002*np.exp(-d2/(50**2))
  body=float(np.sum(weights*cp[:,2])/max(1e-12,np.sum(weights)))
  ed=_edge_distance(x,y);fade=_smooth(ed/12.0)
  bed=max(-.15,min(12,ground(x,y)-.18))
  h=bed+max(0,body-bed)*fade
  rough=(noise.noise(Vector((x*.13,y*.13,.4)))*6.6+
         noise.noise(Vector((x*.39,y*.39,1.7)))*1.3+
         .8*math.sin(body*.48+x*.12+y*.09))
  h+=rough*fade
  inf=stair_v5.sample_path(x,y);d=float(inf['distance']);support=float(inf['support_z'])+.07
  # La sede è più ampia dei parapetti. Niente roccia sopra il piano di passaggio.
  if d<=2.06:h=support
  elif d<6.6:
   f=1-_smooth((d-2.06)/(6.6-2.06));h=h*(1-f)+support*f
  # Non riempire la rimessa: il nuovo sperone passa sotto il fabbricato.
  dx=max(165.5-x,0,x-187.0);dy=max(-143.0-y,0,y+130.6)
  protect=1-_smooth(math.hypot(dx,dy)/3.0)
  if protect>0:h=h*(1-protect)+min(h,3.72)*protect
  # Il ventre della scala prevale anche negli angoli miterati dei pianerottoli.
  if decktree:
   hit=decktree.ray_cast(Vector((x,y,-40)),Vector((0,0,1)),150)
   if hit[0] is not None:h=hit[0].z+.045
  # Fronte della rimessa: il passaggio delle barche resta sotto l'acqua.
  # Margine pieno di 2 m contro l'interpolazione dei triangoli, poi raccordo di 4 m.
  bx=max(160.0-x,0.0,x-192.0);by=max(-167.0-y,0.0,y+143.0)
  water_clearance=1-_smooth(math.hypot(bx,by)/4.0)
  if water_clearance>0:h=h*(1-water_clearance)+min(h,.25)*water_clearance
  return h

 # Contorno densificato; triangolazione aderente alle due guide della scala.
 points=[]
 for i,a in enumerate(OUTLINE):
  b=OUTLINE[(i+1)%len(OUTLINE)];N=max(1,round(math.dist(a,b)/1.5))
  for j in range(N):points.append((a[0]+(b[0]-a[0])*j/N,a[1]+(b[1]-a[1])*j/N))
 area=sum(points[i][0]*points[(i+1)%len(points)][1]-points[(i+1)%len(points)][0]*points[i][1] for i in range(len(points)))
 if area<0:points.reverse()
 boundary_count=len(points);edges=[]
 # Reticolo non allineato perfettamente alle linee della geologia.
 for i in range(134):
  for j in range(72):
   x=58.6+i*1.06+.12*math.sin(j*2.1);y=-164+j*1.06+.12*math.sin(i*1.7)
   if not _inside(x,y,OUTLINE) or _edge_distance(x,y)<.6:continue
   info=stair_v5.sample_path(x,y)
   if float(info['distance'])<2.35:continue
   points.append((x,y))
 for a,b in zip(route,route[1:]):
  dx=b[0]-a[0];dy=b[1]-a[1];L=math.hypot(dx,dy);nx=-dy/L;ny=dx/L
  N=max(2,math.ceil(L/.72));last=[None]*5
  for j in range(N+1):
   t=j/N;cx=a[0]+dx*t;cy=a[1]+dy*t
   for q,off in enumerate([-2.05,-1.02,0,1.02,2.05]):
    x=cx+off*nx;y=cy+off*ny
    if not _inside(x,y,OUTLINE):continue
    k=len(points);points.append((x,y))
    if last[q] is not None:edges.append((last[q],k))
    last[q]=k
 if deck:
  extra={}
  for v in deck.data.vertices:
   q=deck.matrix_world@v.co
   if _inside(q.x,q.y,OUTLINE):extra[(round(q.x,4),round(q.y,4))]=(q.x,q.y)
  points.extend(extra.values())
 vv,ee,ff,*_=delaunay_2d_cdt([Vector(p) for p in points],edges,[list(range(boundary_count))],1,.0003,False)
 verts=[(p.x,p.y,height(p.x,p.y)) for p in vv]
 me=bpy.data.meshes.new('Roccia della scalinata | rilievo continuo');me.from_pydata(verts,[],ff);me.update()
 col=bpy.data.collections.new(COLLECTION);bpy.context.scene.collection.children.link(col)
 ob=bpy.data.objects.new('Sperone della scalinata | roccia modellata',me);col.objects.link(ob);me.materials.append(bpy.data.materials['rock'])
 for f in me.polygons:f.use_smooth=True
 uv=me.uv_layers.new(name='Metriche')
 for f in me.polygons:
  for li in f.loop_indices:
   v=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(v.x,v.y)
 # Le parti sostituite rimangono nel file nascoste, per confronto.
 hidden=[]
 for name in ['Scogliera della rimessa | superficie','Scogliera della rimessa | pareti rocciose']:
  old=bpy.data.objects.get(name)
  if old:old.hide_render=True;old.hide_set(True);hidden.append(name)
 bpy.context.view_layer.update();tree=_world_tree(ob)
 probes=[]
 for a,b in zip(route,route[1:]):
  for t in [.08,.25,.5,.75,.92]:
   x=a[0]+(b[0]-a[0])*t;y=a[1]+(b[1]-a[1])*t;inf=stair_v5.sample_path(x,y)
   hit=tree.ray_cast(Vector((x,y,300)),Vector((0,0,-1)),600)
   z=hit[0].z if hit[0] is not None else None
   probes.append({'xy':[x,y],'walkway':float(inf['height']),'support_bottom':float(inf['support_z']),'rock':z,'delta_support':None if z is None else z-float(inf['support_z'])})
 boat_probes=[]
 for x in [166.0,169.8,175.0,180.8,186.0]:
  for y in [-145.0,-147.0,-150.0,-155.0,-162.0]:
   hit=tree.ray_cast(Vector((x,y,300)),Vector((0,0,-1)),600)
   z=hit[0].z if hit[0] is not None else None
   boat_probes.append({'xy':[x,y],'rock':z,'clear':z is None or z<=.251})
 if len(me.polygons)>50000:raise RuntimeError('Sperone troppo dettagliato')
 nonfinite=any(not math.isfinite(c) for v in me.vertices for c in v.co)
 if nonfinite:raise RuntimeError('Coordinate non finite nello sperone')
 report={'vertices':len(me.vertices),'faces':len(me.polygons),'hidden_previous':hidden,'path_probes':probes,'boat_probes':boat_probes,'boat_corridor_obstructions':[p for p in boat_probes if not p['clear']],'rock_above_walkway':[p for p in probes if p['rock'] is not None and p['rock']>p['walkway']-.10],'missing_support':[p for p in probes if p['rock'] is None or p['delta_support']<-.16]}
 bpy.context.scene['Sperone V5']='Roccia continua con creste minute e sede vincolata sotto la nuova scalinata; rocca principale e molo invariati.'
 return report
