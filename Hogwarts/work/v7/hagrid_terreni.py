"""Capanna cinematografica di Hagrid e Platano Picchiatore sul terreno attuale.
apply() non carica né salva file, non renderizza, non altera gli interni.
"""
import bpy, math, random, json, sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
import kit_v7 as K
A=K.A
TAU=math.tau

def _world(x,y,z,cx,cy,ang=.18):
 return (cx+x*math.cos(ang)-y*math.sin(ang),cy+x*math.sin(ang)+y*math.cos(ang),z)

def _foundation(name,cx,cy,r,top,phase,segments=8):
 xy=[(cx+r*math.cos(phase+i*TAU/segments),cy+r*math.sin(phase+i*TAU/segments)) for i in range(segments)]
 bottoms=[K.ground(x,y)-.24 for x,y in xy]
 verts=[(x,y,z) for (x,y),z in zip(xy,bottoms)]+[(x,y,top) for x,y in xy]
 faces=[tuple(range(segments-1,-1,-1)),tuple(range(segments,2*segments))]+[(i,(i+1)%segments,(i+1)%segments+segments,i+segments) for i in range(segments)]
 ob=A.mesh(name,verts,faces,'stone');K.M.assign_uvs([ob]);return ob,min(bottoms),max(bottoms)

def _roof(name,cx,cy,z,r,h,phase):
 ob=A.cone(name,(cx,cy,z),r,.07,h,'roof',8,phase)
 # Spigoli, bordi di gronda e corsi bassi segnano le falde in ardesia.
 trim=K.Batch(name+' | colmi e gronda',['roofline','v7_wood'])
 for i in range(8):
  a=phase+i*TAU/8;b=phase+(i+1)*TAU/8
  p=(cx+r*math.cos(a),cy+r*math.sin(a),z+.025)
  q=(cx+r*math.cos(b),cy+r*math.sin(b),z+.025)
  trim.tube(p,q,.07,n=7,mat=1)
  trim.tube(p,(cx,cy,z+h+.04),.045,n=6)
  for f in [.11,.23,.35,.47,.59,.71,.83]:
   rr=r*(1-f);pp=(cx+rr*math.cos(a),cy+rr*math.sin(a),z+h*f+.024);qq=(cx+rr*math.cos(b),cy+rr*math.sin(b),z+h*f+.024)
   trim.tube(pp,qq,.025,n=5)
 trim.finish();return ob

def _window(batch,cx,cy,z,r,a,w=1.25,h=1.4):
 n=Vector((math.cos(a),math.sin(a),0));t=Vector((-math.sin(a),math.cos(a),0));c=Vector((cx,cy,z))+n*(r+.025)
 angle=a+math.pi/2
 batch.box(c,(w,.09,h),2,angle)
 for side in [-1,1]:
  batch.tube(c+t*(side*w/2)+Vector((0,0,-h/2)),c+t*(side*w/2)+Vector((0,0,h/2)),.075,n=7,mat=0)
  batch.tube(c+t*(-w/2)+Vector((0,0,side*h/2)),c+t*(w/2)+Vector((0,0,side*h/2)),.075,n=7,mat=0)
 batch.tube(c+Vector((0,0,-h/2)),c+Vector((0,0,h/2)),.035,n=6,mat=1)
 batch.tube(c-t*w/2,c+t*w/2,.035,n=6,mat=1)
 # Pietra sporgente del davanzale.
 batch.box(c+Vector((0,0,-h/2-.14)),(w+.35,.35,.22),3,angle)

def _terrain_path(name,controls,width):
 # La griglia campiona anche il centro della carreggiata: una semplice
 # striscia a due bordi può intersecare un dosso fra i due margini.
 trail=K.smooth_path(controls,.22);columns=max(7,math.ceil(width/.22)+1)
 verts=[]
 for i,(x,y) in enumerate(trail):
  a=Vector(trail[max(0,i-1)]);b=Vector(trail[min(len(trail)-1,i+1)]);t=(b-a).normalized();n=Vector((-t.y,t.x))
  for j in range(columns):
   xx=x+n.x*width*(j/(columns-1)-.5);yy=y+n.y*width*(j/(columns-1)-.5)
   verts.append([xx,yy,K.ground(xx,yy)+.075])
 faces=[]
 for i in range(len(trail)-1):
  for j in range(columns-1):
   a=i*columns+j;b=a+1;c=a+columns;d=c+1
   faces.extend([(a,b,d),(a,d,c)])
 # Sonde interne e sui margini di ogni triangolo, non soltanto sull'asse.
 bary=[(1/3,1/3,1/3),(.5,.5,0),(.5,0,.5),(0,.5,.5)]
 probes=[]
 for face in faces:
  for weights in bary:
   x=sum(verts[k][0]*w for k,w in zip(face,weights));y=sum(verts[k][1]*w for k,w in zip(face,weights))
   probes.append((face,weights,K.ground(x,y)))
 max_lift=0.
 for iteration in range(3):
  lift=[0.]*len(verts)
  for face,weights,gz in probes:
   clearance=sum(verts[k][2]*w for k,w in zip(face,weights))-gz
   if clearance<.035:
    for k in face:lift[k]=max(lift[k],.045-clearance)
  if not any(lift):break
  max_lift=max(max_lift,max(lift))
  for p,dz in zip(verts,lift):p[2]+=dz
 minimum=min(sum(verts[k][2]*w for k,w in zip(face,weights))-gz for face,weights,gz in probes)
 if minimum<.025:raise RuntimeError('Il terreno attraversa ancora il sentiero '+name)
 ob=A.mesh(name,verts,faces,'v7_dirt');K.M.assign_uvs([ob]);ob['Esterni V7']=True
 ob['Verifica tutta la larghezza']=len(probes);ob['Distacco minimo dal terreno']=minimum
 return trail,{'vertices':len(verts),'triangles':len(faces),'transverse_samples':columns,'surface_probes':len(probes),'minimum_clearance':minimum,'maximum_local_lift':max_lift}

def _hagrid():
 col=K.collection('84 • Capanna e orto di Hagrid');rng=random.Random(8401)
 cx,cy=-275.,-80.;angle=.18;phase=math.pi/8+angle
 ax,ay,_=_world(6.1,-2.7,0,cx,cy,angle)
 points=[(cx+5*math.cos(t*TAU/16),cy+5*math.sin(t*TAU/16)) for t in range(16)]+[(ax+3.3*math.cos(t*TAU/16),ay+3.3*math.sin(t*TAU/16)) for t in range(16)]
 z=max(K.ground(x,y) for x,y in points)+.17
 foundation=[]
 for name,x,y,r in [('principale',cx,cy,4.9),('annesso',ax,ay,3.35)]:
  _,lo,hi=_foundation('Hagrid | fondazione '+name,x,y,r,z,phase);foundation.append({'name':name,'bottom_min':lo,'ground_max':hi,'floor':z})
 A.cone('Hagrid | corpo ottagonale in pietra',(cx,cy,z),4.7,4.65,4.6,'stone',8,phase)
 A.cone('Hagrid | annesso in pietra',(ax,ay,z),3.2,3.17,3.2,'stone',8,phase)
 # Coperture distinte, inclinate come i due corpi del set cinematografico.
 _roof('Hagrid | tetto alto in ardesia',cx,cy,z+4.6,5.25,5.2,phase)
 _roof('Hagrid | tetto basso in ardesia',ax,ay,z+3.2,3.6,3.5,phase)
 stone=K.Batch('Hagrid | pietre angolari e camino',['trim','stone'])
 for x,y,r,levels in [(cx,cy,4.70,8),(ax,ay,3.20,5)]:
  for j in range(8):
   a=phase+j*TAU/8
   for lev in range(levels):
    stone.box((x+r*math.cos(a),y+r*math.sin(a),z+.30+lev*.53),(.37,.37,.44),lev%2,a)
 # Camino al raccordo fra le due falde con canna e comignolo scuro.
 chx,chy,_=_world(3.5,1.1,0,cx,cy,angle)
 stone.box((chx,chy,z+6.8),(.95,1.05,6.5),1,angle)
 stone.box((chx,chy,z+10.1),(1.18,1.28,.28),0,angle)
 stone.finish()
 iron=K.Batch('Hagrid | ferramenta e puntali',['v7_iron','v7_wood','window','trim'])
 for x,y,zz,hh in [(cx,cy,z+9.8,1.4),(ax,ay,z+6.7,1.0)]:
  iron.tube((x,y,zz),(x,y,zz+hh),.045,.015,n=8)
  iron.ring((x,y,zz+.45),.13,.025,axis='Y',n=20)
 iron.box((chx,chy,z+10.23),(.72,.82,.04),2,angle)
 for a in [angle+math.pi,angle-math.pi/2]:_window(iron,cx,cy,z+2.30,4.7*math.cos(math.pi/8),a)
 _window(iron,ax,ay,z+1.9,3.2*math.cos(math.pi/8),angle+math.pi/2,1.0,1.1)
 # Porta verso il terreno più basso a est: tavole indipendenti e vere pedate.
 front_angle=angle;n=Vector((math.cos(front_angle),math.sin(front_angle),0));t=Vector((-n.y,n.x,0));door=Vector((ax,ay,z))+n*(3.2*math.cos(math.pi/8)+.08)
 iron.box(door+Vector((0,0,1.15)),(1.65,.18,2.35),2,front_angle+math.pi/2)
 for j in range(6):
  p=door+t*((j-2.5)*.25)+n*.12+Vector((0,0,1.15));iron.box(p,(.235,.14,2.25),1,front_angle+math.pi/2)
 for hh in [.4,1.65]:iron.box(door+n*.21+Vector((0,0,hh)),(1.25,.06,.085),0,front_angle+math.pi/2)
 iron.ring(door+t*.43+n*.25+Vector((0,0,1.05)),.12,.025,'X',n=20)
 for side in [-1,1]:iron.box(door+t*(side*.94)+Vector((0,0,1.20)),(.23,.43,2.48),3,front_angle+math.pi/2)
 iron.box(door+Vector((0,0,2.47)),(2.1,.43,.26),3,front_angle+math.pi/2)
 # Piccola lanterna sospesa accanto all'ingresso.
 lp=door+t*1.35+n*.25+Vector((0,0,1.98))
 iron.tube(lp+Vector((0,0,.40)),lp+Vector((0,0,.66)),.045,n=6)
 iron.box(lp,(.28,.28,.45),0);iron.box(lp+n*.155,(.20,.04,.28),3)
 iron.finish()
 # Gradini con fondazione sotto ogni pedata; ultimo livello esattamente alla soglia.
 steps=K.Batch('Hagrid | gradini e pianerottolo',['path','v7_wood'])
 end=door+n*3.5;ground_end=K.ground(end.x,end.y);height=z-ground_end
 count=max(4,math.ceil(max(.5,height)/.20));run=max(2.6,count*.32)
 for j in range(count):
  dist=run*(1-(j+.5)/count);p=door+n*dist;top=ground_end+(z-ground_end)*(j+1)/count
  low=min(K.ground(p.x,p.y)-.10,top-.18)
  steps.box((p.x,p.y,(top+low)/2),(2.25,run/count+.025,top-low),0,front_angle+math.pi/2)
 steps.finish();pathend=door+n*(run+.5)
 # Percorso serpeggiante dal cerchio esistente, con bordi di terra.
 controls=[(-220.5,-62.3),(-229,-57),(-239,-67),(-233,-79),(-246,-90),(-259,-91),(pathend.x,pathend.y)]
 trail,pathcheck=_terrain_path('Hagrid | sentiero dal cerchio di pietre',controls,2.0)
 ed=K.Batch('Hagrid | alzate rustiche del sentiero',['v7_wood','stone'])
 for i in range(5,len(trail)-5,9):
  x,y=trail[i];p=Vector(trail[i-5]);q=Vector(trail[i+5]);d=(q-p).normalized();rise=K.ground(*trail[i+5])-K.ground(*trail[i-5])
  if abs(rise)>.65:
   a=(x-d.y*.92,y+d.x*.92,K.ground(x-d.y*.92,y+d.x*.92)+.10);b=(x+d.y*.92,y-d.x*.92,K.ground(x+d.y*.92,y-d.x*.92)+.10);ed.tube(a,b,.11,n=7)
 ed.finish()
 # Orto di zucche segue il pendio; niente piattaforma sospesa.
 gx,gy=-278.,-96.;patch=K.Batch('Hagrid | zolle e filari',['v7_dirt'])
 for row in range(5):
  for j in range(9):
   x=gx-6+j*1.45;y=gy-3.8+row*1.8;zz=K.ground(x,y)+.04
   patch.ellipsoid((x,y,zz),.85,.62,.12,n=8,rings=3,mat=0,irregular=.12)
 patch.finish()
 pumpkins=K.Batch('Hagrid | zucche costolute e foglie',['v7_pumpkin','v7_leaf','v7_wood'])
 for j in range(31):
  x=gx+rng.uniform(-5.8,5.8);y=gy+rng.uniform(-3.2,3.2);base=K.ground(x,y);r=rng.uniform(.32,.77)
  for k in range(9):
   a=k*TAU/9;p=(x+.28*r*math.cos(a),y+.28*r*math.sin(a),base+r*.65)
   pumpkins.ellipsoid(p,r*.64,r*.64,r*.73,n=8,rings=5,mat=0,irregular=.04)
  pumpkins.tube((x,y,base+r*1.18),(x+.10,y,base+r*1.52),r*.12,r*.065,n=6,mat=2)
  for k in range(3):
   a=rng.random()*TAU;rr=r*.95
   pumpkins.ellipsoid((x+rr*math.cos(a),y+rr*math.sin(a),base+.12),.48,.31,.07,a,n=7,rings=3,mat=1)
 pumpkins.finish()
 # Staccionata sbrecciata con apertura sul lato della capanna.
 fence=K.Batch('Hagrid | staccionata rustica',['v7_wood','v7_iron'])
 fencepoints=[(gx-7.6,gy+5),(gx-7.6,gy-5),(gx+7.6,gy-5),(gx+7.6,gy+5),(gx+3,gy+5)]
 for a,b in zip(fencepoints,fencepoints[1:]):
  nseg=max(1,round(math.dist(a,b)/1.9));prev=None
  for j in range(nseg+1):
   t0=j/nseg;x=a[0]+t0*(b[0]-a[0]);y=a[1]+t0*(b[1]-a[1]);zz=K.ground(x,y)
   p=(x,y,zz);fence.tube(p,(x+rng.uniform(-.08,.08),y+rng.uniform(-.07,.07),zz+1.3+rng.uniform(-.1,.1)),.085,.06,n=6)
   if prev:
    for h in [.4,.95]:fence.tube((prev[0],prev[1],prev[2]+h),(x,y,zz+h),.055,n=6)
   prev=p
 fence.finish()
 # Catasta, ceppo con accetta, barile, spaventapasseri e utensili.
 props=K.Batch('Hagrid | legna e utensili',['v7_wood','v7_iron','v7_linen','v7_blue','v7_iron'])
 lx,ly=cx-5.2,cy-2.2;gz=K.ground(lx,ly)
 for lev in range(4):
  for j in range(5-lev):
   yy=ly+(j-(4-lev)/2)*.34;zz=gz+.19+lev*.30
   props.tube((lx-.7,yy,zz),(lx+.7,yy,zz),.19,.17,n=10)
 props.tube((lx-1.5,ly-1,gz),(lx-1.5,ly-1,gz+.65),.5,.46,n=10)
 props.tube((lx-1.5,ly-1,gz+.65),(lx-1.05,ly-1,gz+1.3),.035,n=6)
 props.box((lx-1.47,ly-1,gz+.73),(.30,.09,.35),1,.5)
 bx,by=ax+2.8,ay+2.2;bz=K.ground(bx,by)
 props.tube((bx,by,bz),(bx,by,bz+1.05),.45,.46,n=12)
 for h in [.15,.8]:props.ring((bx,by,bz+h),.46,.035,n=30,mat=1)
 sx,sy=gx-4,gy+1.3;sz=K.ground(sx,sy)
 props.tube((sx,sy,sz),(sx,sy,sz+2.8),.065,n=7)
 props.tube((sx-1,sy,sz+2.2),(sx+1,sy,sz+2.15),.05,n=7)
 props.ellipsoid((sx,sy,sz+2.77),.22,.18,.28,n=10,rings=5,mat=2)
 props.box((sx,sy,sz+2.1),(.7,.3,.95),3)
 for side in [-1,1]:props.tube((sx+side*.25,sy,sz+2.35),(sx+side*.85,sy,sz+2.2),.13,.10,n=8,mat=3)
 props.tube((sx,sy,sz+2.95),(sx,sy,sz+3.1),.37,.19,n=12)
 props.finish()
 # Appoggi d'ingresso e pavimenti controllati sulla quota effettiva del terreno.
 camera=K.camera('Camera | V7 Capanna di Hagrid',(-236,-122,z+18),(-274,-87,z+3.7),39)
 clear=[(cx,cy,8.5),(ax,ay,5.0),(gx,gy,10.0)]
 return {'center':[cx,cy,z],'annex':[ax,ay,z],'garden':[gx,gy],'foundation':foundation,'door':list(door),'steps':count,'path_points':len(trail),'path_surface_check':pathcheck,'path_end':list(pathend),'camera':camera.name,'clear_zones':clear,'trail':trail}

def _branch(batch,points,radii,mat=0,sides=16):
 # Una sola superficie continua segue una curva Catmull–Rom, evitando
 # gomiti fra cilindri e nodi sferici separati. Stessi punti della posa.
 p=[Vector(points[0])]+[Vector(q) for q in points]+[Vector(points[-1])]
 samples=[];rs=[]
 for i in range(1,len(p)-2):
  a,b,c,d=p[i-1:i+3];count=max(8,math.ceil((c-b).length/.38))
  for j in range(count):
   t=j/count;v=.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)
   samples.append(v);rs.append(radii[i-1]*(1-t)+radii[i]*t)
 samples.append(Vector(points[-1]));rs.append(radii[-1])
 vs=[];previous=None
 for i,(p,r) in enumerate(zip(samples,rs)):
  tangent=(samples[min(len(samples)-1,i+1)]-samples[max(0,i-1)]).normalized()
  if previous is None:
   ref=Vector((0,0,1)) if abs(tangent.z)<.92 else Vector((0,1,0));u=tangent.cross(ref).normalized()
  else:
   u=(previous-tangent*previous.dot(tangent)).normalized()
  v=tangent.cross(u).normalized();previous=u
  for j in range(sides):
   a=j*TAU/sides;shape=1+.035*math.sin(3*a+i*.09)+.018*math.sin(5*a-i*.055)
   vs.append(tuple(p+r*shape*(u*math.cos(a)+v*math.sin(a))))
 fs=[tuple(range(sides-1,-1,-1)),tuple(range((len(samples)-1)*sides,len(samples)*sides))]
 fs.extend((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j) for i in range(len(samples)-1) for j in range(sides))
 batch.add(vs,fs,mat)

def _willow():
 col=K.collection('85 • Platano Picchiatore');cx,cy=-302.,-44.;z=K.ground(cx,cy);rng=random.Random(8503)
 A.M['v7_bark']=K.I.material('Esterni | corteccia Platano',(.12,.085,.052),.98)
 bark=K.Batch('Platano | tronco cavo radici e grandi braccia',['v7_bark'])
 # Il tronco parte sopra un'apertura reale delimitata da due grandi contrafforti.
 rootpaths=[]
 for i in range(8):
  a=i*TAU/8+.2;ex=cx+7.6*math.cos(a);ey=cy+7.6*math.sin(a);ez=K.ground(ex,ey)
  root=[(cx+1.3*math.cos(a),cy+1.3*math.sin(a),z+2.3),(cx+3.4*math.cos(a+.08),cy+3.4*math.sin(a+.08),K.ground(cx+3.4*math.cos(a+.08),cy+3.4*math.sin(a+.08))+.48),(ex,ey,ez+.10)]
  _branch(bark,root,[.86,.48,.06]);rootpaths.append(root)
 trunk=[(cx,cy,z+2.1),(cx-.7,cy+.2,z+5),(cx+.2,cy+.4,z+8.3),(cx-1.0,cy+.1,z+11.7),(cx-.3,cy+.1,z+15)]
 _branch(bark,trunk,[2.12,1.9,1.6,1.23,.55])
 # Noduli e vecchi monconi spezzano la silhouette, senza volto umano.
 for p,rx,ry,rz in [((cx+1.3,cy-.4,z+5.4),.85,.65,1.0),((cx-1.7,cy+.5,z+8.3),.55,.68,.85),((cx+.5,cy-1.25,z+10.3),.55,.55,.6)]:bark.ellipsoid(p,rx,ry,rz,n=12,rings=6,mat=0,irregular=.15)
 arms=[
  [(cx-.6,cy,z+7.3),(cx-5,cy-.8,z+10.4),(cx-10,cy-1.6,z+8.4),(cx-13,cy-2,z+10.8)],
  [(cx-.3,cy+.1,z+9.2),(cx+4,cy-.5,z+12),(cx+9.4,cy-2,z+13.3),(cx+13,cy-3,z+11.1)],
  [(cx-.3,cy+.6,z+11.8),(cx-3,cy+5,z+14),(cx-4,cy+9,z+18.6)],
  [(cx-.1,cy+.3,z+14),(cx+2.4,cy+2,z+18),(cx+5,cy+2.7,z+20.4)],
  [(cx-.5,cy-.1,z+10),(cx+1.2,cy-5,z+13.6),(cx-.2,cy-9,z+16.1)],
 ]
 tips=[];fine_twigs=0
 for i,arm in enumerate(arms):
  _branch(bark,arm,[1.20,.83,.49,.17] if len(arm)==4 else [.95,.56,.16])
  for j in range(3):
   base=Vector(arm[-2]).lerp(Vector(arm[-1]),.25+j*.23);a=(i*.93+j*1.57)
   p=base+Vector((2.1*math.cos(a),2.1*math.sin(a),1.5+j*.7));q=p+Vector((1.2*math.cos(a+.4),1.2*math.sin(a+.4),1.8))
   _branch(bark,[tuple(base),tuple(p),tuple(q)],[.23,.12,.025]);tips.append(tuple(q))
   for sign in [-1,1]:
    end=q+Vector((sign*.85*math.sin(a),-sign*.85*math.cos(a),.75));mid=p.lerp(end,.55)+Vector((sign*.18,-sign*.1,.16))
    _branch(bark,[tuple(p),tuple(mid),tuple(end)],[.065,.038,.006],sides=12);fine_twigs+=1
    for k in range(2):
     start=mid.lerp(end,.25+k*.35);tip=start+Vector((sign*(.55+.20*k)*math.sin(a+.6),-sign*.55*math.cos(a+.6),.50+.18*k));bend=start.lerp(tip,.53)+Vector((.08*sign,.03,.06))
     _branch(bark,[tuple(start),tuple(bend),tuple(tip)],[.026,.016,.0035],sides=12);fine_twigs+=1
 barkob=bark.finish()
 for f in barkob.data.polygons:f.use_smooth=True
 # L'ingresso oscuro è arretrato fra le radici: nessun disco sul davanti del tronco.
 dark=K.Batch('Platano | cavità fra le radici',['window'])
 dark.ellipsoid((cx,cy+.25,z+.97),.9,.7,1.3,n=14,rings=8,mat=0,irregular=.05);dark.finish()
 leaves=K.Batch('Platano | chioma rada',['v7_leaf','v7_green'])
 for i,p in enumerate(tips):
  if i%3==0:continue
  leaves.ellipsoid((p[0],p[1],p[2]-.15),1.6,1.1,.75,phase=i,n=9,rings=4,mat=i%2,irregular=.3)
 leafob=leaves.finish()
 for f in leafob.data.polygons:f.use_smooth=True
 # Un sentiero discreto arriva al bordo della radura.
 trail,pathcheck=_terrain_path('Platano | traccia verso la radura',[(-279,-76),(-288,-68),(-294,-58),(-296,-50)],1.2)
 camera=K.camera('Camera | V7 Platano Picchiatore',(-268,-75,z+16),(cx,cy,z+11.5),32)
 return {'center':[cx,cy,z],'arms':len(arms),'roots':len(rootpaths),'fine_twigs':fine_twigs,'continuous_sections':16,'path_surface_check':pathcheck,'camera':camera.name,'clear_zones':[(cx,cy,17)],'trail':trail}

def _hide_trees(zones,paths):
 hidden=[];collection=bpy.data.collections.get('41 • Boschi e radure')
 if collection is None:return hidden
 for ob in collection.all_objects:
  if ob.type!='MESH' or ob.hide_render:continue
  x,y=ob.matrix_world.translation.xy
  near=any((x-cx)**2+(y-cy)**2<r*r for cx,cy,r in zones)
  if not near:
   near=any((x-p[0])**2+(y-p[1])**2<3.5**2 for path in paths for p in path[::3])
  if near:ob.hide_render=True;ob.hide_set(True);ob['Radura Hagrid V7']=True;hidden.append(ob.name)
 return hidden

def apply():
 K.init();before=set(bpy.data.objects);h=_hagrid();w=_willow()
 hidden=_hide_trees(h.pop('clear_zones')+w.pop('clear_zones'),[h.pop('trail'),w.pop('trail')])
 added=[o for o in bpy.data.objects if o not in before]
 for o in added:o['Esterni V7']=True
 mesh=[o for o in added if o.type=='MESH'];K.M.assign_uvs(mesh)
 bad=[o.name for o in mesh if not o.data.polygons or any(not math.isfinite(q) for v in o.data.vertices for q in v.co)]
 if bad:raise RuntimeError('Geometria non valida: '+str(bad))
 bpy.context.view_layer.update()
 report={'hagrid':h,'willow':w,'objects':len(added),'mesh_objects':len(mesh),'faces':sum(len(o.data.polygons) for o in mesh),'hidden_trees':hidden,'empty_or_nonfinite':bad}
 return report

if __name__=='__main__':
 root=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca')
 bpy.ops.wm.open_mainfile(filepath=str(root/'outputs/Hogwarts-interni.blend'))
 result=apply();(root/'work/v7/hagrid-terreni-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('HAGRID_CHECK',json.dumps(result,ensure_ascii=False),flush=True)
