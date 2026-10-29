"""Due rampe diagonali e vista umana della grande scalinata.
Applicare una volta alla scena interna pronta; non salva né renderizza.
"""
import bpy,bmesh,math,sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import interior_kit as I
import circulation_v6 as C
sys.path.insert(0,str(I.ROOT/'work/v3'))
import materials

CENTER=Vector((21.6,-97.028,0))
COLLECTION='70 • Grande scalinata • Rampe diagonali'


def _world(p):return Vector(p)+CENTER

def _strip(a,b,width):
 d=Vector(b)-Vector(a);d.z=0;d.normalize();n=Vector((-d.y,d.x,0))*width/2
 return [(a.x-n.x,a.y-n.y),(b.x-n.x,b.y-n.y),(b.x+n.x,b.y+n.y),(a.x+n.x,a.y+n.y)]


def _cut_floor(ob,a,b,width,z):
 poly=_strip(a,b,width);vs=[(x,y,zz) for zz in (z-.75,z+.75) for x,y in poly]
 fs=[(0,3,2,1),(4,5,6,7)]+[(i,(i+1)%4,(i+1)%4+4,i+4) for i in range(4)]
 me=bpy.data.meshes.new('TEMP varco diagonale');me.from_pydata(vs,[],fs);me.update()
 cut=bpy.data.objects.new('TEMP varco diagonale',me);bpy.context.scene.collection.objects.link(cut)
 bpy.context.view_layer.update();bpy.context.view_layer.objects.active=ob
 original=ob.data.copy()
 mod=ob.modifiers.new('Varco di arrivo scala diagonale','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;mod.use_self=True
 try:
  bpy.ops.object.modifier_apply(modifier=mod.name)
  if not ob.data.polygons:ob.data=original;raise RuntimeError('Taglio ha svuotato il ballatoio '+ob.name)
 finally:
  bpy.data.objects.remove(cut,do_unlink=True)
 if original.users==0:bpy.data.meshes.remove(original)


def _point_in_gate(p,spec):
 a,b,w,z0,z1=spec
 if not z0-.03<=p.z<=z1+.03:return False
 d=b-a;L=math.hypot(d.x,d.y);u=((p.x-a.x)*d.x+(p.y-a.y)*d.y)/L
 side=abs(-(p.x-a.x)*d.y+(p.y-a.y)*d.x)/L
 return -.12<=u<=L+.12 and side<=w/2+.08


def _open_guards(ob,specs):
 """Rimuove interi piccoli segmenti chiusi; conserva le rampe e i loro lunghi corrimano."""
 me=ob.data;n=len(me.vertices);parent=list(range(n))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 def union(a,b):
  a=find(a);b=find(b)
  if a!=b:parent[b]=a
 for f in me.polygons:
  vs=list(f.vertices)
  for i in vs[1:]:union(vs[0],i)
 groups={}
 for i in range(n):groups.setdefault(find(i),[]).append(i)
 removed=[];components=0
 for ids in groups.values():
  pts=[ob.matrix_world@me.vertices[i].co for i in ids]
  span=max((max(p[k] for p in pts)-min(p[k] for p in pts)) for k in range(3))
  if span>3.5:continue
  if any(_point_in_gate(p,spec) for p in pts for spec in specs):removed.extend(ids);components+=1
 if removed:
  bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.verts[i] for i in removed],context='VERTS');bm.to_mesh(me);bm.free();me.update()
 return components


def _tree(ob):return BVHTree.FromPolygons([ob.matrix_world@v.co for v in ob.data.vertices],[tuple(f.vertices) for f in ob.data.polygons],all_triangles=False)


def apply():
 if bpy.data.collections.get(COLLECTION):raise RuntimeError('Rampe diagonali già applicate')
 I.init();root=bpy.data.collections['70 • Grande scalinata'];col=bpy.data.collections.new(COLLECTION);root.children.link(col);I.A.CURRENT=col
 # La seconda diagonale evita le rampe perimetrali già esistenti sul lato nord/ovest.
 specs=[((-8,-6,73.4),(8,6,80.),3,1.4),((6,-8,99.8),(-6.8,6.6,106.4),7,1.0)]
 gates=[];floors=[];ramps=[]
 for local_a,local_b,index,landing_length in specs:
  a=_world(local_a);b=_world(local_b);d=b-a;d.z=0;d.normalize()
  # Il varco termina sul bordo del pianerottolo di arrivo, non oltre.
  _cut_floor(bpy.data.objects['Scalinata | ballatoio '+str(index)],b-d*4.5,b,3.3,b.z)
  floors.append(bpy.data.objects['Scalinata | ballatoio '+str(index)])
  gates.extend([(a-d*.65,a+d*4.2,3.3,a.z-.35,a.z+1.5),(b-d*4.3,b+d*.15,3.3,b.z-.35,b.z+1.5)])
  ramps.append((a,b,d,landing_length,index))
 guard_changes={}
 for name in ['Scalinata | corrimano continui','Scalinata | balaustri']:
  ob=bpy.data.objects.get(name)
  if ob:guard_changes[name]=_open_guards(ob,gates)
 body=C.Geo('Scalinata | rampe diagonali in pietra','stone');rail=C.Geo('Scalinata | corrimano diagonali','int_oak');posts=C.Geo('Scalinata | balaustri diagonali','int_wood');count=0
 for a,b,d,landing_length,index in ramps:
  count+=C.straight_flight(body,rail,posts,a,b,2.4,.18)
  lower=a-d*1.15;upper=b+d*landing_length
  body.band(lower,a,2.4,-.23,.015);body.band(b,upper,2.4,-.23,.015)
  n=Vector((-d.y,d.x,0))
  # Corrimano proseguiti sui pianerottoli, lasciando aperti i due fronti del percorso.
  for p,q in [(lower,a),(b,upper)]:
   for side in (-1,1):
    offset=n*(1.2-.055)*side
    rail.tube(p+offset+Vector((0,0,1.05)),q+offset+Vector((0,0,1.05)),.07,8)
    posts.tube(p+offset+Vector((0,0,.04)),p+offset+Vector((0,0,1.05)),.045,7)
 new=[body.finish(),rail.finish(),posts.finish()]
 camera_data=bpy.data.cameras.new('Interni | Grande scalinata dal ballatoio');camera_data.lens=20;camera_data.clip_start=.05;camera_data.clip_end=15000
 camera=bpy.data.objects.new(camera_data.name,camera_data);col.objects.link(camera);camera.location=(10.6,-96.028,75.1);target=Vector((24.6,-95.028,84));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
 for o in col.objects:o['Interno']=True;o['Ambiente']='70 • Grande scalinata'
 for ob in bpy.data.objects:
  if ob.type=='LIGHT' and ob.name.startswith('Scalinata | luce morbida piano') and ob.data.type=='AREA':ob.data.energy=900
  elif ob.type=='LIGHT' and ob.name.startswith('Scalinata | torcia al piano') and ob.data.type=='POINT':ob.data.energy=130
 materials.assign_uvs(new+floors)
 bpy.context.view_layer.update()
 # Aperture reali nel solaio per tutta la larghezza delle ultime pedate.
 errors=[];probes=0
 for a,b,d,landing_length,index in ramps:
  floor=_tree(bpy.data.objects['Scalinata | ballatoio '+str(index)]);n=Vector((-d.y,d.x,0))
  for dist in [.12,.45,.9,1.5,2.2,3.5]:
   for off in [-1.15,0,1.15]:
    p=b-d*dist+n*off;hit=floor.ray_cast(Vector((p.x,p.y,b.z+1)),Vector((0,0,-1)),2);probes+=1
    if hit[0] is not None:errors.append({'floor':index,'distance':dist,'side':off,'z':hit[0].z})
  p=b+d*min(.6,landing_length*.5);hit=floor.ray_cast(Vector((p.x,p.y,b.z+1)),Vector((0,0,-1)),2)
  if hit[0] is None:errors.append({'landing_missing':index})
 faces=sum(len(o.data.polygons) for o in new)
 if errors or faces>6000:raise RuntimeError(str({'opening_errors':errors,'faces':faces}))
 bpy.context.scene['Grande scalinata | diagonali']='Due rampe fisse trasversali con varchi nei ballatoi; vista dal ballatoio e illuminazione interna aumentata.'
 return {'camera':camera.name,'new_faces':faces,'new_objects':len(col.objects),'steps':count,'floor_openings_checked':probes,'opening_errors':errors,'guard_components_removed':guard_changes,'ramps_world':[{'a':tuple(a),'b':tuple(b)} for a,b,_,_,_ in ramps]}
