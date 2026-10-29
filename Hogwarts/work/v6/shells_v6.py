"""Involucri vuoti, aperture e organizzazione degli esterni per la vista degli interni."""
import bpy,math
from mathutils import Vector

TARGET_PREFIXES=[
 'Sala Grande | muratura','Sala d’ingresso | muri','Torre della Scalinata | fusto',
 'Quad | ala nord | muri','Quad | ala ovest | muri','Quad | ala sud | muri','Quad | ala est | muri',
 'Grifondoro | torre nordoccidentale | fusto','Quad | torre del ponte alto | fusto',
 'Silente | torretta 1 | fusto','Silente | torretta 2 | fusto','Silente | torretta 3 | fusto',
 'Galleria lunga | muri','Ala nord Durham | muri','Ala occidentale Durham | muri','Ala orientale Durham | muri',
 'Navata sud Durham | muri','Corpo sud Durham | muri','Corpo laterale occidentale | muri',
 'Ingresso viadotto | corpo laterale','Ingresso viadotto | corpo sopra portale',
 'Torre viadotto 1 | fusto','Torre viadotto 2 | fusto','Torre viadotto 3 | fusto','Torre viadotto 4 | fusto',
 'Centrale | corpo','Astronomia | fusto a D','Astronomia | tamburo belvedere','Infermeria | galleria | muri',
]
CUTTERS=[]

def mesh_cutter(name,vs,fs):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();ob=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(ob);CUTTERS.append(ob);return ob

def prism_cutter(name,poly,z0,z1):
 n=len(poly);return mesh_cutter(name,[(x,y,z) for z in [z0,z1] for x,y in poly],[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)])

def box_cutter(name,center,size,angle=0):
 x,y,z=center;l,w,h=size;co=math.cos(angle);si=math.sin(angle)
 poly=[(x+u*co-v*si,y+u*si+v*co) for u,v in [(-l/2,-w/2),(l/2,-w/2),(l/2,w/2),(-l/2,w/2)]]
 return prism_cutter(name,poly,z-h/2,z+h/2)

def subtract(ob,cutter):
 bpy.context.view_layer.objects.active=ob
 mod=ob.modifiers.new('Spazio interno e aperture','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter;mod.use_self=True
 bpy.ops.object.modifier_apply(modifier=mod.name)

def offset(poly,inset):
 area=sum(poly[i][0]*poly[(i+1)%len(poly)][1]-poly[(i+1)%len(poly)][0]*poly[i][1] for i in range(len(poly)))
 if area<0:poly=list(reversed(poly))
 out=[];n=len(poly)
 for i,p in enumerate(poly):
  a=Vector(poly[(i-1)%n]);b=Vector(p);c=Vector(poly[(i+1)%n]);u=(b-a).normalized();v=(c-b).normalized()
  n1=Vector((-u.y,u.x));n2=Vector((-v.y,v.x));avg=n1+n2
  if avg.length<1e-8:avg=n1
  avg.normalize();den=max(.12,avg.dot(n1));q=b+avg*inset/den;out.append((q.x,q.y))
 return out

def bounds(o):
 pts=[o.matrix_world@v.co for v in o.data.vertices]
 return tuple(min(v[i] for v in pts) for i in range(3)),tuple(max(v[i] for v in pts) for i in range(3))

def compound_windows(name,panes):
 vs=[];fs=[]
 for ob in panes:
  me=ob.data;caps=sorted(me.polygons,key=lambda p:len(p.vertices),reverse=True)
  if not caps:continue
  cap=caps[0];poly=[ob.matrix_world@me.vertices[i].co for i in cap.vertices]
  normal=(ob.matrix_world.to_3x3()@cap.normal).normalized();n=len(poly);k=len(vs)
  vs.extend(tuple(p+normal*d) for d in [-1.9,1.9] for p in poly)
  fs.extend([tuple(k+i for i in range(n-1,-1,-1)),tuple(k+i for i in range(n,2*n))]);fs.extend((k+i,k+(i+1)%n,k+(i+1)%n+n,k+i+n) for i in range(n))
 return mesh_cutter(name,vs,fs) if fs else None

def open_roof_bases():
 count=0
 for ob in bpy.data.objects:
  if ob.type!='MESH' or (len(ob.data.vertices)!=6 and ob.name!='Astronomia | copertura asimmetrica'):continue
  if not any(k in ob.name for k in ['Sala Grande','Sala d’ingresso','Quad | ala','Galleria lunga','Ala nord Durham','Ala occidentale Durham','Ala orientale Durham','Navata sud Durham','Corpo sud Durham','Infermeria | galleria','Astronomia | copertura asimmetrica']):continue
  if not any(k in ob.name for k in ['tetto','timpani','copertura asimmetrica']):continue
  vs=[tuple(v.co) for v in ob.data.vertices];faces=[tuple(p.vertices) for p in ob.data.polygons if p.normal.z>-.9]
  if len(faces)==len(ob.data.polygons):continue
  mats=list(ob.data.materials);me=bpy.data.meshes.new(ob.data.name+' aperto sotto');me.from_pydata(vs,[],faces);me.update();ob.data=me
  for m in mats:me.materials.append(m)
  count+=1
 return count

def apply():
 bodies=[o for o in bpy.data.objects if o.type=='MESH' and any(o.name.startswith(p) for p in TARGET_PREFIXES)]
 panes=[o for o in bpy.data.objects if o.type=='MESH' and ' | vetro' in o.name and not o.get('Interno')]
 decor=[o for o in bpy.data.objects if o.type=='MESH' and o not in bodies and any(k in o.name.lower() for k in ['fascia','marcapiano','zoccolo','basamento','cornice belvedere','piattaforma addossata','mensola belvedere','silente | mensola']) and max(o.dimensions.x,o.dimensions.y)>3.5]
 cavity_meta=[];window_meta=[]
 boxes={o.name:bounds(o) for o in bodies+decor}
 cavities=[]
 for o in bodies:
  for mod in list(o.modifiers):
   if mod.type in ['BEVEL','WEIGHTED_NORMAL']:o.modifiers.remove(mod)
  points=[o.matrix_world@v.co for v in o.data.vertices];z0=min(p.z for p in points);z1=max(p.z for p in points)
  base=[p for p in points if abs(p.z-z0)<.001]
  if len(base)<3:continue
  wall=.62 if 'Silente' in o.name else .78
  inner=offset([(p.x,p.y) for p in base],wall)
  cut=prism_cutter('CAVITA | '+o.name,inner,z0+.22,z1+1.0);cavities.append((o,cut))
  cavity_meta.append({'name':o.name,'floor':z0+.22,'ceiling_open':z1,'wall':wall})
 # Unione dei vuoti: quando due corpi si sovrappongono, non resta un muro
 # appartenente all'edificio vicino all'interno della stanza.
 for owner,cut in cavities:
  cl,cu=bounds(cut)
  for o in bodies+decor:
   if not o.data.polygons:continue
   lo,hi=boxes[o.name]
   if all(hi[k]>=cl[k] and lo[k]<=cu[k] for k in range(3)):
    subtract(o,cut)
    if not o.data.polygons:
     if o in bodies:raise RuntimeError('Cavità vuota inattesa: '+o.name+' / '+owner.name)
     o.hide_render=True;o.hide_set(True)
 for o in bodies:
  lo,hi=boxes[o.name]
  if o.name.startswith('Torre della Scalinata'):prefixes=['Scalinata | finestra']
  elif o.name.startswith('Astronomia | fusto'):prefixes=['Astronomia | feritoia curva','Astronomia | finestra sud','Astronomia | finestra laterale','Astronomia | grande apertura']
  elif o.name.startswith('Astronomia | tamburo'):prefixes=['Astronomia | luci tamburo']
  elif o.name.startswith('Centrale | corpo'):prefixes=['Centrale | finestra']
  elif o.name.startswith('Ingresso viadotto | corpo'):prefixes=['Ingresso viadotto | finestra']
  else:prefixes=[o.name.split(' | muri')[0].split(' | muratura')[0].split(' | fusto')[0]]
  near=[]
  for pane in panes:
   if not any(pane.name.startswith(pre) for pre in prefixes):continue
   pp=[pane.matrix_world@v.co for v in pane.data.vertices];c=sum(pp,Vector())/len(pp)
   if all(lo[k]-.9<=c[k]<=hi[k]+.9 for k in range(3)):near.append(pane)
  if near:
   backup=o.data.copy();cut=compound_windows('FINESTRE | '+o.name,near)
   subtract(o,cut)
   if not o.data.polygons:
    bad=o.data;o.data=backup
    if bad.users==0:bpy.data.meshes.remove(bad)
    for pane in near:
     cut=compound_windows('FINESTRA | '+o.name,[pane]);subtract(o,cut)
     if not o.data.polygons:raise RuntimeError('Finestra cancella involucro: '+o.name+' / '+pane.name)
   elif backup.users==0:bpy.data.meshes.remove(backup)
   for pane in near:
    if bpy.data.materials.get('glass'):pane.data.materials.clear();pane.data.materials.append(bpy.data.materials['glass'])
   window_meta.append({'body':o.name,'openings':len(near)})
 # Passaggi tra i volumi sovrapposti. Ogni volume riceve la stessa sottrazione.
 portals=[
  ('Sala Grande–atrio',(35.0,-128.7,63.2),(9,5.2,6.0),.607),
  ('Atrio–Scalinata',(28.8,-111.0,63.2),(4.2,11,6),0),
  ('Scalinata–Quad',(19.2,-84.0,75.4),(4.0,15,4.4),0),
  ('Quad nord–Gryffindor',(-39,-30,95.3),(10,5,4.2),-.70),
  ('Quad nord–dormitorio',(-39,-30,101.9),(10,5,4.2),-.70),
  ('Quad est–ponte alto',(23.0,-31.5,86.0),(6,9,4.6),0),
  ('Ponte alto–torre ingresso',(46.2,-16.0,86.0),(6.0,8.0,4.6),.6),
  ('Ingresso alto–galleria',(59,-9,86.1),(28,4.0,4.8),0),
  ('Biblioteca–centrale',(75.6,34.8,57.8),(4.5,9,5.0),0),
  ('Centrale–navata',(75.6,17.5,57.8),(4.5,10,5.0),0),
  ('Navata–ingresso nord',(75.6,1.5,62.4),(4.5,8,5.0),0),
  ('Durham–biblioteca',(60.8,63.0,57.8),(8.0,4.0,5.0),0),
  ('Durham–Astronomia',(31.2,43,57.8),(4.2,15,5.0),0),
  ('Infermeria–ponte',(-43.2,-61.9,83.6),(12,4.2,4.8),0),
  ('Astronomia–belvedere',(21.0,18.0,161.6),(4.0,16.0,4.8),0),
 ]
 # Ufficio: collegamenti tra le tre stanze circolari e l'ultimo ballatoio.
 centers=[(21.6+16.5*math.cos(a),-97.028+16.5*math.sin(a)) for a in [3.55,3.87,4.19]]
 for a,b in zip(centers,centers[1:]):portals.append(('Silente | camere',((a[0]+b[0])/2,(a[1]+b[1])/2,136.5),(math.dist(a,b)+3,1.65,4.5),math.atan2(b[1]-a[1],b[0]-a[0])))
 portals.append(('Silente–ballatoio',(14.2,-106.0,136.5),(10,2.2,4.5),.55))
 for name,center,size,angle in portals:
  cut=box_cutter('PORTA | '+name,center,size,angle);clo,chi=bounds(cut)
  for body in bodies:
   lo,hi=boxes[body.name]
   if all(hi[k]>=clo[k] and lo[k]<=chi[k] for k in range(3)):subtract(body,cut)
 # Foro della scala nel vecchio solaio dell'osservatorio.
 old_floor=bpy.data.objects.get('Astronomia | pavimento osservatorio')
 if old_floor:
  poly=[(20.8+1.15*math.cos(i*math.tau/48),11.988+1.15*math.sin(i*math.tau/48)) for i in range(48)]
  subtract(old_floor,prism_cutter('Scala osservatorio | varco',poly,201.0,204.0))
 roof_count=open_roof_bases()
 for o in CUTTERS:bpy.data.objects.remove(o,do_unlink=True)
 CUTTERS.clear()
 # Gli involucri sono isolabili con un solo interruttore nell'Outliner.
 shells=bpy.data.collections.new('80 • Involucri esterni apribili');bpy.context.scene.collection.children.link(shells)
 for o in bodies:
  for c in list(o.users_collection):c.objects.unlink(o)
  shells.objects.link(o);o['Involucro apribile']=True
 roofs=bpy.data.collections.new('81 • Tetti esterni nascondibili');bpy.context.scene.collection.children.link(roofs)
 roof_objects=[]
 for o in list(bpy.data.objects):
  if o.type!='MESH' or o.get('Interno'):continue
  if not any(k in o.name.lower() for k in [' | tetto',' | copertura',' | ardesia',' | grande guglia',' | grande cuspide',' | guglia ottagonale',' | colmo']):continue
  if any(k in o.name for k in ['Serra','Ponte coperto','Rimessa']):continue
  for c in list(o.users_collection):c.objects.unlink(o)
  roofs.objects.link(o);roof_objects.append(o.name)
 return {'hollow_bodies':cavity_meta,'window_groups':window_meta,'portals':len(portals),'roof_bases_opened':roof_count,'roof_objects':len(roof_objects),'decor_hollowed':len(decor)}
