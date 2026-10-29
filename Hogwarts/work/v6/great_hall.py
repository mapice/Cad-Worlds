"""Sala Grande e atrio: arredi e strutture interne nel modello HBP.
Gli involucri e i passaggi verso gli altri edifici sono gestiti dall'integratore.
"""
import bpy,math,random
from mathutils import Vector,Matrix
import interior_kit as I

HALL_ORIGIN=(15,-142.104,60.4)
HALL_ANGLE=math.atan2(.072*382,.066*600)
ATRIUM_ORIGIN=(28.8,-121.476,60.4)


def _lathe(batch,p,profile,n=16,mat=0):
 x,y,z=p;vs=[]
 for r,h in profile:
  for j in range(n):
   a=j*math.tau/n;vs.append((x+r*math.cos(a),y+r*math.sin(a),z+h))
 fs=[tuple(range(n-1,-1,-1))]
 for k in range(len(profile)-1):
  for j in range(n):a=k*n+j;b=k*n+(j+1)%n;fs.append((a,b,b+n,a+n))
 fs.append(tuple(range((len(profile)-1)*n,len(profile)*n)))
 batch.shape(vs,fs,mat)


def _sphere(batch,p,r,mat=0,n=12,rings=6,scale=(1,1,1)):
 x,y,z=p;vs=[]
 for k in range(rings+1):
  a=math.pi*k/rings;rr=r*math.sin(a)
  for j in range(n):
   b=j*math.tau/n;vs.append((x+scale[0]*rr*math.cos(b),y+scale[1]*rr*math.sin(b),z+scale[2]*r*math.cos(a)))
 fs=[]
 for k in range(rings):
  for j in range(n):a=k*n+j;b=k*n+(j+1)%n;fs.append((a,b,b+n,a+n))
 batch.shape(vs,fs,mat)


def _beam_batch(batch,a,b,r,mat=0,n=8):
 a=Vector(a);b=Vector(b);d=(b-a).normalized();u=d.cross(Vector((0,0,1)))
 if u.length<.01:u=d.cross(Vector((0,1,0)))
 u.normalize();v=d.cross(u)
 vs=[tuple(p+r*(math.cos(j*math.tau/n)*u+math.sin(j*math.tau/n)*v)) for p in [a,b] for j in range(n)]
 fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 batch.shape(vs,fs,mat)


def _banner(name,x,y,z,width,height,mat,angle=0):
 co=math.cos(angle);si=math.sin(angle)
 def p(u,v,w):return(x+u*co-v*si,y+u*si+v*co,z+w)
 verts=[];N=9
 for j in range(N):
  u=-width/2+width*j/(N-1);wave=.10*math.sin(j*1.6)
  verts.extend([p(u,wave,0),p(u,wave,-height+.2*(abs(u)/(width/2)))])
 I.mesh(name+' | drappo',verts,[(2*j,2*j+2,2*j+3,2*j+1) for j in range(N-1)],mat)
 I.beam(name+' | asta',p(-width*.63,0,.08),p(width*.63,0,.08),.055,'int_brass')
 # Bordo e stemma geometrico discreto, senza inventare insegne araldiche dettagliate.
 for u in [-width*.47,width*.47]:I.beam(name+' | bordo dorato',p(u,.11,-.08),p(u,.11,-height+.12),.025,'int_gold')
 badge=[p(-width*.20,-.14,-height*.32),p(width*.20,-.14,-height*.32),p(width*.16,-.14,-height*.55),p(0,-.14,-height*.65),p(-width*.16,-.14,-height*.55)]
 I.mesh(name+' | scudo semplice',badge,[(0,1,2,3,4)],'int_gold')


def _hall_furniture(room):
 room.part('Tavolate e panche')
 timber=I.Batch('Sala Grande | quattro tavolate',['int_oak','int_wood'])
 rows=[-5.10,-1.78,1.78,5.10]
 center=2.;length=30.;top=.86
 for row,y in enumerate(rows):
  # Cinque assi sul piano, otto cavalletti sotto ogni tavolata.
  for j in range(5):timber.box((center,y+(j-2)*.205,top),(length,.199,.10),0)
  for x in [-12,-8,-4,0,4,8,12,16]:
   for yy in [y-.37,y+.37]:timber.box((x,yy,.40),(.16,.16,.80),1)
   timber.box((x,y,.25),(.12,.92,.14),1)
  timber.box((center,y,.35),(length-.4,.12,.15),1)
  for side in [-1,1]:
   yy=y+side*.91
   for j in [-1,1]:timber.box((center,yy+j*.095,.48),(length,.18,.09),0)
   for x in [-12,-8,-4,0,4,8,12,16]:
    timber.box((x,yy,.23),(.14,.31,.46),1)
    timber.box((x,yy,.08),(.38,.46,.11),1)
 timber.finish()
 # Servizio tavola: piatti incavati, calici, coltelli e tovaglioli.
 ceramics=I.Batch('Sala Grande | piatti e scodelle',['int_white'])
 gold=I.Batch('Sala Grande | calici e stoviglie',['int_brass','int_gold','int_iron'])
 napkins=I.Batch('Sala Grande | tovaglioli',['int_white'])
 bread=I.material('Banchetto | crosta del pane',(.24,.105,.027),.83);I.A.M['int_bread']=bread
 fruit=I.material('Banchetto | frutta rossa',(.25,.018,.012),.47);I.A.M['int_fruit']=fruit
 food=I.Batch('Sala Grande | pani e frutta',['int_bread','int_fruit','int_green'])
 for row,y in enumerate(rows):
  for j in range(20):
   x=-12.2+j*1.45
   for side in [-1,1]:
    yy=y+side*.32
    _lathe(ceramics,(x,yy,.916),[(.045,0),(.12,.006),(.153,.030),(.158,.048),(.146,.054),(.118,.023)],20)
    _lathe(gold,(x+.25,yy-side*.11,.92),[(.06,0),(.07,.018),(.022,.033),(.018,.13),(.075,.185),(.080,.26),(.078,.28),(.065,.28),(.052,.205),(.02,.185)],14,0)
    gold.box((x-.22,yy,.93),(.025,.19,.012),2)
    gold.box((x-.22,yy-side*.13,.94),(.042,.10,.025),0)
    napkins.box((x+.38,yy,.93),(.19,.21,.025),0,side*.08)
  for j,x in enumerate([-10,-5,0,5,10,15]):
   _lathe(gold,(x,y,.92),[(.15,0),(.21,.035),(.25,.08),(.22,.10)],18,1)
   _sphere(food,(x,y,1.10),.20,j%2,14,6,(1.3,.8,.6))
   if j%2:
    for k in range(4):_sphere(food,(x+.12*math.cos(k*1.5),y+.12*math.sin(k*1.5),1.18),.07,1,10,5)
 ceramics.finish();gold.finish();napkins.finish();food.finish()
 # Professori al lato opposto all'ingresso +X.
 room.part('Pedana dei professori')
 I.box('Professori | pedana',(-20.6,0,.18),(6.3,13.8,.36),'path')
 for j in range(2):I.box('Professori | gradino',(-17.05-j*.45,0,.09+j*.09),(.48,12.8,.18+j*.18),'trim')
 # Tavolo trasversale costruito per elementi, sedie rivolte verso +X.
 I.box('Professori | tavolo',(-21.0,0,1.27),(1.0,11.7,.13),'int_oak',bevel=.04)
 for y in [-5.4,-2.7,0,2.7,5.4]:
  I.box('Professori | cavalletto',(-21.0,y,.79),(.72,.20,.85),'int_wood')
 for y in [-5.2+1.04*j for j in range(11)]:
  I.chair('Professori | sedia',(-22.35,y,.36),'int_wood',math.pi/2)
  I.bottle('Professori | caraffa',(-20.8,y,1.35),.13,.36,'int_brass')
  I.candle('Professori | candela',(-21.10,y+.42,1.35),.36)
 # Schienale del preside più alto e intagliato.
 I.box('Preside | schienale alto',(-22.60,0,1.67),(.11,.74,1.52),'int_wood')
 I.panel('Preside | pinnacolo dello schienale',(-22.66,0,1.15),.72,1.35,math.pi/2,'int_gold',.06)
 # Leggio davanti alla pedana, lascia libero l'asse d'ingresso e l'aisle principale.
 I.cone('Leggio | base',(-18.25,-4.8,.36),.43,.31,.12,'int_brass',24)
 I.cone('Leggio | colonna',(-18.25,-4.8,.48),.10,.085,.98,'int_brass',16)
 top=I.box('Leggio | piano inclinato',(-18.25,-4.8,1.49),(.72,.58,.07),'int_wood')
 book=I.box('Leggio | libro aperto',(-18.25,-4.8,1.55),(.57,.45,.055),'int_paper')
 pivot=Vector((-18.25,-4.8,1.49));rot=Matrix.Rotation(-.18,3,'Y')
 for ob in [top,book]:
  for vertex in ob.data.vertices:vertex.co=pivot+rot@(vertex.co-pivot)
 return {'long_tables':4,'student_settings':160,'professors_chairs':11}


def _hall_architecture(room):
 room.part('Pavimento')
 I.box('Sala Grande | pavimento interno',(0,0,-.10),(48.2,15.2,.20),'path')
 # Cornice perimetrale e striscia cerimoniale nel corridoio centrale.
 for y in [-7.30,7.30]:I.box('Sala Grande | fascia pavimento',(0,y,.012),(47.8,.22,.024),'trim')
 for x in [-23.8,23.8]:I.box('Sala Grande | fascia terminale',(x,0,.012),(.22,14.8,.024),'trim')
 room.part('Pilastri e rivestimenti')
 for side in [-1,1]:
  yy=side*7.55
  I.box('Sala Grande | zoccolo interno',(0,yy,1.25),(48.2,.20,2.5),'stone')
  I.box('Sala Grande | cornice del basamento',(0,yy-side*.07,2.55),(48.2,.32,.16),'trim')
  for x in [-23.8,-19.05,-14.30,-9.55,-4.8,0,4.8,9.55,14.30,19.05,23.8]:
   I.box('Sala Grande | pilastro interno',(x,yy,14.6),(.55,.42,29.2),'stone')
   for zz in [.4,6.2,22.6,28.8]:I.box('Sala Grande | collarino pilastro',(x,yy-side*.05,zz),(.78,.60,.22),'trim')
   # Mensole sotto le travi, come supporti della grande struttura lignea.
   I.cone('Sala Grande | mensola lignea',(x,yy-side*.18,23.0),.42,.25,1.2,'int_wood',8)
 # Stendardi sulle spalle, non davanti alle grandi finestre.
 for j,(x,mat) in enumerate([(-14.3,'int_red'),(-4.8,'int_green'),(4.8,'int_blue'),(14.3,'int_gold')]):
  _banner('Sala Grande | stendardo '+str(j+1),x,7.20,10.4,1.25,4.3,mat)
 # Travi a martello e archi lignei della copertura.
 room.part('Struttura lignea')
 beam=I.Batch('Sala Grande | travi e capriate',['int_wood','int_oak'])
 for x in [-22,-15,-8,-1,6,13,20]:
  for side in [-1,1]:
   _beam_batch(beam,(x,side*7.25,22.8),(x,side*4.6,27.2),.22,0)
   _beam_batch(beam,(x,side*7.2,26.0),(x,side*4.5,26.0),.21,1)
   _beam_batch(beam,(x,side*5.1,26),(x,side*5.1,30.1),.17,0)
  points=[]
  for j in range(25):
   y=-7.3+14.6*j/24;z=25.4+8.0*(1-(abs(y)/7.3)**1.7);points.append((x,y,z))
  for a,b in zip(points,points[1:]):_beam_batch(beam,a,b,.21,1)
 for y in [-6.9,-4.3,0,4.3,6.9]:
  z=25.4+8*(1-(abs(y)/7.3)**1.7)
  _beam_batch(beam,(-24,y,z),(24,y,z),.16,0)
 beam.finish()
 room.part('Soffitto — nascondibile')
 # Calotta incantata separata, sopra gli elementi strutturali.
 verts=[];N=28
 for x in [-24.25,24.25]:
  for j in range(N+1):
   y=-7.65+15.3*j/N;z=29.7+5.2*math.sin(math.pi*j/N)**.74;verts.append((x,y,z))
 I.mesh('Sala Grande | cielo incantato',verts,[(j,j+1,j+1+N+1,j+N+1) for j in range(N)],'int_sky')
 stars=I.Batch('Sala Grande | stelle incantate',['int_flame'])
 rng=random.Random(610)
 for j in range(135):
  x=rng.uniform(-23.3,23.3);y=rng.uniform(-7.3,7.3);z=29.7+5.2*math.sin(math.pi*(y+7.65)/15.3)**.74-.05
  _sphere(stars,(x,y,z),rng.uniform(.018,.050),0,6,3)
 stars.finish()
 # Candele sospese in un volume più basso, visibili dal livello dei tavoli.
 room.part('Candele sospese')
 wax=I.Batch('Sala Grande | candele galleggianti',['int_wax','int_flame'])
 for j in range(86):
  x=rng.uniform(-18,17);y=rng.uniform(-6.2,6.2);z=rng.uniform(6.8,10.9);h=rng.uniform(.22,.48)
  _lathe(wax,(x,y,z),[(.035,0),(.035,h)],10,0)
  _lathe(wax,(x,y,z+h),[(.025,0),(.040,.045),(.005,.14)],8,1)
 wax.finish()
 room.part('Luci e camere')
 for x in [-14,0,14]:I.area('Sala Grande | luce delle candele',(x,0,9.4),(x,0,0),3400,10,(1,.74,.47))
 for x in [-17,-2,13]:
  I.area('Sala Grande | luce delle vetrate',(x,-6.9,15),(x,2,5),2600,8,(.72,.84,1))
  I.area('Sala Grande | rimbalzo delle vetrate',(x,6.9,14),(x,-2,4),1600,8,(1,.82,.58))
 I.area('Sala Grande | luce della pedana',(-20,0,9),(-20,0,1),2400,6,(1,.76,.48))
 I.camera(room,'Camera | Interno Sala Grande',(21,0,2.2),(-17,0,4.5),22)
 I.camera(room,'Camera | Sala Grande dall’alto',(17,-6.3,16),(-13,0,2),23)


def _armor(name,x,y,z,facing=0):
 before=set(bpy.data.objects)
 # Armatura su basamento: sagoma leggibile e dettagli costruttivi, non personaggio.
 I.box(name+' | plinto',(x,y,z+.12),(.72,.72,.24),'stone')
 for side in [-1,1]:
  I.cone(name+' | gambale',(x+side*.17,y,z+.30),.09,.075,.55,'int_iron',10)
  I.box(name+' | sabatone',(x+side*.17,y-.08,z+.27),(.19,.34,.15),'int_iron')
  I.cone(name+' | coscia',(x+side*.15,y,z+.83),.12,.10,.45,'int_iron',10)
 I.cone(name+' | corazza',(x,y,z+1.12),.25,.30,.48,'int_iron',12)
 I.cone(name+' | collo',(x,y,z+1.61),.11,.11,.12,'int_brass',12)
 I.cone(name+' | elmo',(x,y,z+1.73),.18,.12,.29,'int_iron',16)
 I.box(name+' | visiera',(x,y-.16,z+1.86),(.23,.035,.05),'int_gold')
 for side in [-1,1]:
  I.cone(name+' | spallaccio',(x+side*.33,y,z+1.40),.16,.11,.23,'int_iron',12)
  I.beam(name+' | braccio',(x+side*.35,y,z+1.39),(x+side*.39,y-.05,z+.96),.085,'int_iron',10)
 I.beam(name+' | asta',(x+.45,y-.08,z+.30),(x+.45,y-.08,z+2.35),.035,'int_wood',8)
 I.mesh(name+' | punta',[(x+.36,y-.08,z+2.30),(x+.54,y-.08,z+2.30),(x+.45,y-.08,z+2.62)],[(0,1,2)],'int_iron')
 if y<0:
  tr=Matrix.Translation((x,y,z))@Matrix.Rotation(math.pi,4,'Z')@Matrix.Translation((-x,-y,-z))
  for ob in set(bpy.data.objects)-before:ob.matrix_world=tr@ob.matrix_world


def _atrium():
 room=I.Room('61 • Atrio di ingresso',ATRIUM_ORIGIN,math.pi/2)
 room.part('Pavimento e colonne')
 I.box('Atrio | pavimento interno',(6.5,0,-.10),(10.0,11.2,.20),'path')
 # Raccordo trapezoidale esattamente sul bordo obliquo del pavimento della sala.
 def edge_u(v):return (7.6+math.sin(HALL_ANGLE)*(13.8-v))/math.cos(HALL_ANGLE)-20.628-.035
 I.A.prism('Atrio | raccordo di pavimento',[(edge_u(-2.1),-2.1),(1.5,-2.1),(1.5,2.1),(edge_u(2.1),2.1)],-.188,.20,'path')
 for side in [-1,1]:
  for x in [2,6.2,10.5]:
   # Portale SalaGrande a xlocale~−7.3,y−5.6 resta libero.
   I.box('Atrio | pilastro',(x,side*5.45,10.9),(.70,.44,21.8),'stone')
   for zz in [.35,4.2,18.0,21.5]:I.box('Atrio | capitello',(x,side*5.35,zz),(.88,.62,.26),'trim')
  I.box('Atrio | zoccolo',(6.5,side*5.52,1.15),(9.8,.13,2.3),'stone')
 room.part('Armature e stendardi')
 for i,(x,y) in enumerate([(3.0,-4.5),(8.0,-4.5),(9.8,4.5)]):_armor('Atrio | armatura '+str(i+1),x,y,0)
 for i,(x,mat) in enumerate([(3.0,'int_red'),(6.3,'int_green'),(9.5,'int_blue')]):_banner('Atrio | stendardo '+str(i+1),x,5.08,8.8,1.1,3.7,mat)
 # Contatori delle case: quattro clessidre vetrate con grani colorati.
 room.part('Contatori delle case')
 colors=['int_red','int_green','int_blue','int_gold'];beads=I.Batch('Atrio | gemme dei punti',colors)
 I.box('Atrio | base dei contatori',(6.1,4.65,.20),(6.0,1.0,.4),'int_wood')
 for i,mat in enumerate(colors):
  x=4.0+i*1.4;y=4.65
  for zz in [.42,3.6]:I.cone('Atrio | cornice clessidra',(x,y,zz),.46,.46,.14,'int_brass',24)
  I.cone('Atrio | vetro superiore',(x,y,2.02),.09,.36,1.55,'glass',24)
  I.cone('Atrio | vetro inferiore',(x,y,.58),.36,.09,1.45,'glass',24)
  for side in [-1,1]:I.beam('Atrio | montante clessidra',(x+side*.42,y,.55),(x+side*.42,y,3.65),.042,'int_brass',8)
  for row in range(9+i):
   for j in range(6):
    a=j*math.tau/6+.3*row;r=.22*(1-row/(15+i))
    _sphere(beads,(x+r*math.cos(a),y+r*math.sin(a),.70+.07*row),.037,i,6,4)
 beads.finish()
 # Quadri e torce sulle fasce alte: evitano i due accessi.
 room.part('Decorazioni')
 for i,x in enumerate([3.0,6.3,9.5]):
  I.portrait('Atrio | ritratto', (x,5.18,4.3),1.45,2.2,0,i+1)
  I.torch('Atrio | torcia',(x,-5.1,3.5))
 room.part('Soffitto — nascondibile')
 # Volta semplice in pietra e costoloni; non aggiunge muri ciechi.
 vs=[];N=20
 for x in [1.5,11.45]:
  for j in range(N+1):
   y=-5.5+11*j/N;zz=18.0+3.7*math.sin(math.pi*j/N);vs.append((x,y,zz))
 I.mesh('Atrio | volta interna',vs,[(j,j+1,j+1+N+1,j+N+1) for j in range(N)],'stone')
 for x in [2,6.2,10.5]:
  pts=[(x,-5.4+10.8*j/16,18+3.7*math.sin(math.pi*j/16)-.1) for j in range(17)]
  for a,b in zip(pts,pts[1:]):I.beam('Atrio | costolone',a,b,.13,'trim',10)
 room.part('Luci e camere')
 for x in [3.0,6.5,10.0]:I.area('Atrio | luce calda',(x,0,7.5),(x,0,0),1300,5,(1,.76,.49))
 I.area('Atrio | luce d’ingresso',(2.0,-4.5,5),(7,0,2),950,4,(.78,.86,1))
 I.camera(room,'Camera | Atrio e accesso alla scalinata',(2.4,0,1.9),(10.2,0,3.2),22)
 result=room.finish()
 result['portals']=[{'label':'verso Sala Grande','local':[1.5,0,0],'width':4.2,'height':4.4},{'label':'verso Torre della Scalinata','local':[11.5,0,0],'width':3.2,'height':4.5}]
 return result


def apply():
 before=set(bpy.data.objects)
 room=I.Room('60 • Interno Sala Grande',HALL_ORIGIN,HALL_ANGLE)
 stats=_hall_furniture(room);_hall_architecture(room);hall=room.finish()
 hall['portals']=[{'label':'ingresso dalla Sala d’ingresso','local':[24.1,0,0],'width':3.2,'height':4.8}]
 atrium=_atrium()
 added=[o for o in bpy.data.objects if o not in before]
 return {'rooms':[hall,atrium],'stats':stats,'objects_added':len(added),'faces_added':sum(len(o.data.polygons) for o in added if o.type=='MESH'),'local_bounds':{'Sala Grande':[-24.3,24.3,-7.85,7.85,-.20,35.5],'Atrio':[-3.4,11.5,-5.7,5.7,-.20,22.0]},'clear_routes':{'Sala Grande':'asse y0 libero fra le tavolate; ingresso+X, professori−X','Atrio':'ambiente arredato u1.5..11.5; raccordo centrale obliquo u−3.3..1.5; uscita torre(+11.5,0)'}}
