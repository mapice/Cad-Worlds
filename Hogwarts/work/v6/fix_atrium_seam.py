"""Correzione locale della soglia e delle spallette atrio–scalinata.
Non salva il modello e non modifica arredi, camera o altri ambienti.
"""
import bpy,math,sys
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt
from mathutils.bvhtree import BVHTree
import interior_kit as I
sys.path.insert(0,str(I.ROOT/'work/v3'))
import materials

COLLECTION='61 • Atrio • Soglia e spallette raccordate'


def _inside(p,poly):
 x,y=p;v=False
 for i,(ax,ay) in enumerate(poly):
  bx,by=poly[(i+1)%len(poly)]
  if (ay>y)!=(by>y) and x<(bx-ax)*(y-ay)/(by-ay)+ax:v=not v
 return v


def _outline(ob):
 pts=[ob.matrix_world@v.co for v in ob.data.vertices];z=max(p.z for p in pts)
 xy=list({(round(p.x,6),round(p.y,6)) for p in pts if abs(p.z-z)<.001})
 cx=sum(p[0] for p in xy)/len(xy);cy=sum(p[1] for p in xy)/len(xy)
 xy.sort(key=lambda p:math.atan2(p[1]-cy,p[0]-cx));return xy


def _union_floor(polys,z):
 points=[];loops=[]
 for poly in polys:
  k=len(points);points.extend(Vector(p) for p in poly);loops.append(list(range(k,len(points))))
 vv,ee,ff,*_=delaunay_2d_cdt(points,[],loops,1,.0001,False);keep=[]
 for f in ff:
  c=sum((vv[i] for i in f),Vector((0,0)))/len(f)
  if any(_inside(c,p) for p in polys):keep.append(f)
 n=len(vv);vs=[(p.x,p.y,h) for h in (z-.28,z) for p in vv];fs=[];edges={};directions={}
 for f in keep:
  fs.extend([tuple(i+n for i in f),tuple(reversed(f))])
  for a,b in zip(f,f[1:]+f[:1]):
   e=tuple(sorted((a,b)));edges[e]=edges.get(e,0)+1;directions[e]=(a,b)
 for e,count in edges.items():
  if count==1:
   a,b=directions[e];fs.append((a,b,b+n,a+n))
 return I.mesh('Atrio–scalinata | pavimento e soglia continui',vs,fs,'path')


def _cutter(poly,z0,z1):
 n=len(poly);me=bpy.data.meshes.new('TEMP giunzione');me.from_pydata([(x,y,z) for z in (z0,z1) for x,y in poly],[],[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]);me.update()
 ob=bpy.data.objects.new('TEMP giunzione',me);bpy.context.scene.collection.objects.link(ob);return ob


def _subtract(ob,cutter):
 bpy.context.view_layer.update();bpy.context.view_layer.objects.active=ob
 m=ob.modifiers.new('Raccordo locale degli spazi interni','BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=cutter;m.use_self=True
 bpy.ops.object.modifier_apply(modifier=m.name)
 if not ob.data.polygons:raise RuntimeError('Parete svuotata inaspettatamente: '+ob.name)


def apply():
 if bpy.data.collections.get(COLLECTION):raise RuntimeError('Giunzione atrio già corretta')
 I.init();root=bpy.data.collections['61 • Atrio di ingresso'];col=bpy.data.collections.new(COLLECTION);root.children.link(col);I.A.CURRENT=col
 old_atrium=bpy.data.objects['Atrio | pavimento interno'];old_stair=bpy.data.objects['Scalinata | ballatoio 0']
 # Un solo pavimento elimina sia la sovrapposizione sia il triangolo mancante
 # fra bordo rettilineo dell'atrio e bordo circolare della torre.
 polys=[_outline(old_atrium),_outline(old_stair),[(26.0,-113.2),(31.6,-113.2),(31.6,-107.6),(26.0,-107.6)]]
 floor=_union_floor(polys,60.4)
 for ob in (old_atrium,old_stair):ob.hide_render=True;ob.hide_set(True)
 # Le facce nere erano pareti interpenetrate: ciascun volume deve essere
 # vuoto anche nella porzione occupata dall'ambiente adiacente.
 targets=[o for o in bpy.data.objects if o.type=='MESH' and (o.name=='Torre della Scalinata | fusto' or o.name.startswith('Scalinata | fascia di pietra'))]
 atrium_space=_cutter([(23.15,-120.0),(34.45,-120.0),(34.45,-109.65),(23.15,-109.65)],60.05,84.6)
 changed=[]
 for ob in targets:
  pts=[ob.matrix_world@v.co for v in ob.data.vertices]
  if min(p.z for p in pts)<84.6 and max(p.z for p in pts)>60.05:_subtract(ob,atrium_space);changed.append(ob.name)
 bpy.data.objects.remove(atrium_space,do_unlink=True)
 atrium_wall=bpy.data.objects['Sala d’ingresso | muri']
 circle=[(21.6+15.5*math.cos(i*math.tau/128),-97.028+15.5*math.sin(i*math.tau/128)) for i in range(128)]
 tower_space=_cutter(circle,60.05,84.6);_subtract(atrium_wall,tower_space);bpy.data.objects.remove(tower_space,do_unlink=True);changed.append(atrium_wall.name)
 throat=_cutter([(26.0,-113.3),(31.6,-113.3),(31.6,-107.6),(26.0,-107.6)],60.05,66.3)
 for ob in targets+[atrium_wall]:
  pts=[ob.matrix_world@v.co for v in ob.data.vertices]
  if min(p.z for p in pts)<66.3 and max(p.z for p in pts)>60.05:_subtract(ob,throat)
 bpy.data.objects.remove(throat,do_unlink=True)
 # Spallette semplici: il vano conserva oltre4m di larghezza e quasi6m di altezza.
 jambs=[]
 for x in (26.4,31.2):jambs.append(I.box('Atrio | spalletta del varco',(x,-111.0,63.35),(.4,2.8,5.9),'trim',bevel=.025))
 jambs.append(I.box('Atrio | architrave del varco',(28.8,-111.0,66.45),(5.6,2.8,.30),'trim',bevel=.025))
 hidden_decor=[]
 for ob in bpy.data.objects:
  if ob.type!='MESH' or not ob.name.startswith('Scalinata | finestra'):continue
  pts=[ob.matrix_world@v.co for v in ob.data.vertices]
  if pts and all(23.15<p.x<34.45 and -120<p.y<-109.65 and 60.05<p.z<84.6 for p in pts):ob.hide_render=True;ob.hide_set(True);hidden_decor.append(ob.name)
 for ob in col.objects:ob['Interno']=True;ob['Ambiente']='61 • Atrio di ingresso'
 materials.assign_uvs([floor]+jambs+[bpy.data.objects[n] for n in changed])
 bpy.context.view_layer.update()
 tree=BVHTree.FromPolygons([floor.matrix_world@v.co for v in floor.data.vertices],[tuple(f.vertices) for f in floor.data.polygons])
 missing=[]
 for x in [26.7,27.5,28.8,30.0,30.9]:
  for y in [-113,-112,-111,-110,-109,-108]:
   hit=tree.ray_cast(Vector((x,y,61)),Vector((0,0,-1)),2)
   if hit[0] is None or abs(hit[0].z-60.4)>.01:missing.append((x,y))
 if missing:raise RuntimeError('Soglia non continua: '+str(missing))
 return {'floor_probes':30,'missing_floor':missing,'walls_cleaned':changed,'old_floors_hidden':[old_atrium.name,old_stair.name],'hidden_decor':hidden_decor,'new_objects':len(col.objects),'new_faces':sum(len(o.data.polygons) for o in col.objects if o.type=='MESH'),'clear_width':4.4,'clear_height':5.9}
