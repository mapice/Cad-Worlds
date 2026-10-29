"""Biblioteca, Pozioni, infermeria e Trasfigurazione: arredi integrati.
Gli involucri e i collegamenti esterni sono gestiti dal coordinatore.
"""
import bpy,math,random
from mathutils import Vector
import interior_kit as I
A=I.A


def _tube(batch,a,b,r,mat=0,n=8):
 a=Vector(a);b=Vector(b);d=b-a
 if d.length<1e-8:return
 d.normalize();u=d.cross(Vector((0,0,1)))
 if u.length<.01:u=d.cross(Vector((0,1,0)))
 u.normalize();v=d.cross(u)
 vs=[tuple(p+r*(u*math.cos(j*math.tau/n)+v*math.sin(j*math.tau/n))) for p in [a,b] for j in range(n)]
 batch.shape(vs,[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],mat)


def _lathe(batch,center,profile,mat=0,n=20,cap_start=True,cap_end=True):
 x,y,z=center;vs=[(x+r*math.cos(j*math.tau/n),y+r*math.sin(j*math.tau/n),z+h) for r,h in profile for j in range(n)]
 fs=[]
 for k in range(len(profile)-1):
  for j in range(n):a=k*n+j;b=k*n+(j+1)%n;fs.append((a,b,b+n,a+n))
 if cap_start:fs.append(tuple(range(n-1,-1,-1)))
 if cap_end:fs.append(tuple(range((len(profile)-1)*n,len(profile)*n)))
 batch.shape(vs,fs,mat)


def _text(name,body,p,size=.25,angle=0,mat='int_gold'):
 d=bpy.data.curves.new(name,'FONT');d.body=body;d.size=size;d.align_x='CENTER';d.extrude=.001
 o=bpy.data.objects.new(name,d);A.CURRENT.objects.link(o);o.location=p;o.rotation_euler=(math.pi/2,0,angle);d.materials.append(A.M[mat]);return o


def _finish(room,size,height,entries):
 data=room.finish();co=math.cos(room.angle);si=math.sin(room.angle);x,y,z=room.origin
 data.update({'size_local':size,'clear_height':height,'entries':[{'position':(x+p[0]*co-p[1]*si,y+p[0]*si+p[1]*co,z+p[2]),'local':p} for p in entries]})
 return data


def _stairs(name,x0,x1,y,height,z0=0,width=1.8):
 n=math.ceil(height/.18);r=height/n;run=abs(x1-x0)/n;sgn=1 if x1>x0 else -1
 wood=I.Batch(name+' | pedate e montanti',['int_wood','int_oak'])
 for j in range(n):
  xx=x0+sgn*run*(j+.5);zz=z0+(j+1)*r
  wood.box((xx,y,zz-.07),(run+.04,width,.14),1)
 for side in [-1,1]:
  yy=y+side*(width/2-.08)
  _tube(wood,(x0,yy,z0+.02),(x1,yy,z0+height-.08),.16,0,8)
  _tube(wood,(x0,yy,z0+1.04),(x1,yy,z0+height+1.04),.07,0,8)
  for j in range(0,n+1,3):
   t=j/n;xx=x0+(x1-x0)*t;zz=z0+height*t
   _tube(wood,(xx,yy,zz),(xx,yy,zz+1.05),.055,0,8)
 wood.finish()


def library():
 room=I.Room('62 • Biblioteca',(75.6,63.03,55.4),math.pi/2)
 room.part('Pavimento')
 I.box('Biblioteca | lastre di pietra',(0,0,-.10),(54,25.8,.20),'path')
 room.part('Scaffali e libri')
 # Due registri di librerie, con il passaggio laterale per il chiostro.
 xs=[-21,-13,-5,3,11,19]
 for side in [-1,1]:
  angle=0 if side==1 else math.pi
  for i,x in enumerate(xs):
   I.bookcase('Biblioteca | scaffale basso', (x,side*12.05,.1),5.9,5.6,.72,angle,7,i+(side+1)*10)
   I.bookcase('Biblioteca | scaffale alto', (x,side*12.05,6.3),5.9,4.9,.66,angle,6,30+i+(side+1)*10)
 # Scaffali bassi trasversali interrotti prima dell'asse centrale.
 for x in [-14,-2,10]:
  for side in [-1,1]:
   for face in [-1,1]:
    I.bookcase('Biblioteca | pluteo bifacciale', (x+face*.33,side*8.1,.1),4.2,3.3,.65,face*math.pi/2,5,70+int(x)+side+face*10)
 for side in [-1,1]:
  I.bookcase('Biblioteca | volumi riservati',(25.6,side*6.2,.1),10.5,5.3,.65,-math.pi/2,7,150+side)
 room.part('Gallerie e scale')
 structure=I.Batch('Biblioteca | gallerie e balaustre',['int_wood','int_oak','int_gold'])
 for side in [-1,1]:
  structure.box((0,side*10.7,6.10),(51,3.5,.24),1)
  # Mensole e pilastri d'appoggio.
  for x in [-24,-18,-12,-6,0,6,12,18,24]:
   structure.box((x,side*9.05,3.1),(.25,.25,6.2),0)
   _tube(structure,(x,side*9.05,5.0),(x,side*10.3,6.0),.14,0)
  join=-11.9
  for level in [6.35,7.18]:
   _tube(structure,(-25.5,side*8.9,level),(join-1.0,side*8.9,level),.075,0)
   _tube(structure,(join+1.0,side*8.9,level),(25.5,side*8.9,level),.075,0)
  for j in range(65):
   x=-25.2+j*.7875
   # Varco sul ballatoio, in corrispondenza del raccordo della scala.
   join=-11.9
   if abs(x-join)<1.15:continue
   _tube(structure,(x,side*8.9,6.25),(x,side*8.9,7.2),.042,0)
  join=-11.9
  structure.box((join,side*7.65,6.10),(1.8,2.6,.24),1)
  _stairs('Biblioteca | scala al ballatoio',-24,-12.8,side*7.25,6.2,width=1.8)
 structure.finish()
 room.part('Tavoli di lettura')
 details=I.Batch('Biblioteca | volumi aperti e fogli',['int_paper','book0','book1','book2','int_gold'])
 for x in [-17,-6,5,16]:
  for side in [-1,1]:
   y=side*4.5;I.table('Biblioteca | tavolo di lettura',(x,y,.05),5.8,1.4,.83)
   for dx in [-1.6,1.6]:
    for sy in [-1,1]:I.chair('Biblioteca | sedia',(x+dx,y+sy*1.08,.05),angle=0 if sy==1 else math.pi)
   for dx in [-1.7,.2,1.5]:
    details.box((x+dx,y,.93),(.48,.33,.07),1+(int(x+dx)%3),angle=.13)
    details.box((x+dx,y,.975),(.43,.30,.015),0,angle=.13)
   I.cone('Biblioteca | base candeliere',(x,y,.92),.14,.10,.08,'int_brass',16)
   I.beam('Biblioteca | stelo candeliere',(x,y,1),(x,y,1.65),.035,'int_brass')
   for dy in [-.27,0,.27]:
    I.beam('Biblioteca | braccio candeliere',(x,y,1.45),(x,y+dy,1.57),.028,'int_brass')
    I.candle('Biblioteca | candela',(x,y+dy,1.57),.23)
 details.finish()
 # Zona riservata con porta aperta sull'asse, griglia ai lati.
 room.part('Reparto riservato')
 gate=I.Batch('Biblioteca | cancellata del reparto riservato',['int_iron','int_brass'])
 for side in [-1,1]:
  for j in range(24):
   y=side*(1.25+j*.44);_tube(gate,(22.7,y,.1),(22.7,y,3.6),.038,0)
  for z in [.4,2.8,3.6]:_tube(gate,(22.7,side*1.25,z),(22.7,side*11.5,z),.065,0)
  # Le due ante sono aperte parallelamente alla navata.
  for j in range(6):_tube(gate,(22.7+j*.26,side*1.25,.1),(22.7+j*.26,side*1.25,3.4),.035,0)
 gate.finish()
 _text('Biblioteca | titolo reparto','REPARTO RISERVATO',(22.64,0,3.95),.32,-math.pi/2)
 room.part('Soffitto — nascondibile')
 I.box('Biblioteca | soffitto a cassettoni',(0,0,11.94),(54,25.8,.25),'int_wood')
 roof=I.Batch('Biblioteca | travi e cassettoni',['int_oak','int_gold','book2','book0'])
 for x in range(-25,26,5):
  roof.box((x,0,11.65),(.32,25.5,.55),0)
 for y in [-12,-8,-4,0,4,8,12]:roof.box((0,y,11.68),(53,.24,.5),0)
 for x in range(-22,23,5):
  for y in [-10,-6,-2,2,6,10]:
   roof.box((x,y,11.78),(3.8,2.9,.09),2 if ((x+y)//5)%2 else 3)
   roof.box((x,y,11.69),(.12,2.7,.06),1);roof.box((x,y,11.69),(3.6,.12,.06),1)
 roof.finish()
 room.part('Luci e camere')
 for x in [-19,-6,7,20]:I.area('Biblioteca | luce calda',(x,0,10.5),(x,0,1),2200,8,(1,.78,.5))
 for side in [-1,1]:
  for x in [-17,1,18]:I.area('Biblioteca | luce dalle finestre',(x,side*12,7),(x,0,2),2200,6,(.72,.85,1))
 I.camera(room,'Camera | Biblioteca',(-24,0,2.0),(18,0,4.2),21)
 I.camera(room,'Camera | Biblioteca dal ballatoio',(-19,8.2,7.4),(10,-5,3.2),24)
 return _finish(room,(54,25.8),12,[(-27,0,0),(-1,12.9,0)])


def potions():
 room=I.Room('63 • Aula Pozioni',(20.4,-52.334,73.4),math.pi/2)
 room.part('Pavimento')
 I.box('Pozioni | pavimento',(0,0,-.10),(23,8.4,.2),'path')
 # Piccoli materiali per liquidi e vetri del laboratorio.
 for key,c in [('potion_amber',(.20,.09,.016)),('potion_green',(.018,.16,.065)),('potion_blue',(.02,.09,.18)),('potion_purple',(.12,.025,.16))]:
  A.M[key]=I.material(key,c,.22);p=A.M[key].node_tree.nodes.get('Principled BSDF');p.inputs['Transmission Weight'].default_value=.12;p.inputs['IOR'].default_value=1.45
 room.part('Banchi e strumenti')
 items=I.Batch('Pozioni | vetri, calderoni e strumenti',['int_iron','int_brass','int_paper','potion_amber','potion_green','potion_blue','potion_purple','int_wood'])
 rng=random.Random(612)
 stations=[(x,y) for x in [-5,1,7] for y in [-2.25,2.25] if not(x==1 and y>0)]
 for idx,(x,y) in enumerate(stations):
  I.table('Pozioni | banco',(x,y,.03),3.5,1.35,.88,'int_wood')
  for dx in [-1.1,1.1]:I.chair('Pozioni | sgabello',(x+dx,y-1.05,.03),'int_wood',math.pi)
  z=.98
  # Profilo esterno e interno: l'imboccatura è aperta e il fondo è concavo.
  profile=[(.29,0),(.43,.10),(.53,.48),(.55,.64),(.47,.64),(.45,.48),(.31,.18)]
  _lathe(items,(x-.4,y,z),profile,0,24,True,True)
  for side in [-1,1]:
   pts=[(x-.4+side*.60,y+.14*math.cos(a),z+.43+.14*math.sin(a)) for a in [j*math.tau/12 for j in range(13)]]
   for a,b in zip(pts,pts[1:]):_tube(items,a,b,.025,1,6)
  if idx%2==0:_lathe(items,(x-.4,y,z+.48),[(.43,0),(.43,.018)],4,24,True,True)
  for j in range(3):
   xx=x+.65+j*.35;hh=rng.uniform(.23,.42);rr=.07+rng.random()*.03
   _lathe(items,(xx,y+.15,z),[(rr,0),(rr,hh*.70),(rr*.33,hh*.83),(rr*.33,hh)],3+(j+idx)%4,12)
   _lathe(items,(xx,y+.15,z+hh),[(rr*.4,0),(rr*.4,.035)],7,10)
  # Mortaio a ciotola e pestello obliquo.
  _lathe(items,(x+1.15,y-.32,z),[(.18,0),(.24,.14),(.23,.23),(.17,.23),(.13,.10)],1,16)
  _tube(items,(x+1.08,y-.30,z+.14),(x+1.34,y-.23,z+.47),.05,7,8)
  # Bilancia a due piatti, davanti ai flaconi.
  xx=x-1.3;yy=y+.35
  _tube(items,(xx,yy,z),(xx,yy,z+.64),.025,1);_tube(items,(xx-.34,yy,z+.61),(xx+.34,yy,z+.61),.025,1)
  for side in [-1,1]:
   _tube(items,(xx+side*.30,yy,z+.61),(xx+side*.30,yy,z+.28),.009,1,6)
   _lathe(items,(xx+side*.30,yy,z+.24),[(.035,0),(.15,.035),(.14,.055),(.02,.025)],1,12)
  items.box((x+.85,y-.34,z+.04),(.38,.29,.07),7,.1);items.box((x+.85,y-.34,z+.085),(.34,.26,.02),2,.1)
 # Scaffali bassi con bottiglie lungo pareti e parete docente.
 for side in [-1,1]:
  for x in [-9,-2.7,5.7]:
   if side==1 and abs(x+2.7)<.1:continue
   y=side*3.80
   for zz in [1.1,2.0,2.9,3.8]:
    I.box('Pozioni | ripiano',(x,y,zz),(4.3,.5,.12),'int_wood')
    for j in range(12):
     xx=x-1.9+j*.34;h=.2+rng.random()*.32;r=.065+rng.random()*.04
     _lathe(items,(xx,y,zz+.07),[(r,0),(r,h*.68),(r*.28,h*.8),(r*.28,h)],3+rng.randrange(4),10)
     _lathe(items,(xx,y,zz+.07+h),[(r*.35,0),(r*.35,.04)],7,8)
 I.table('Pozioni | cattedra',(9.4,0,.03),2.2,1.5,.92,'int_wood')
 items.finish()
 I.box('Pozioni | lavagna',(10.8,0,2.25),(.10,3.0,1.8),'int_chalk')
 _text('Pozioni | titolo','POZIONI',(10.72,0,2.8),.32,-math.pi/2,'int_paper')
 room.part('Volte e pilastri')
 ribs=I.Batch('Pozioni | archi e nervature',['stone','trim'])
 for x in [-10,-5,0,5,10]:
  for side in [-1,1]:
   if x==0 and side==1:continue  # ingresso laterale libero verso il corridoio
   _tube(ribs,(x,side*4.02,0),(x,side*4.02,3.6),.22,0,12)
  pts=[(x,4.0*math.cos(j*math.pi/24),3.6+2.2*math.sin(j*math.pi/24)) for j in range(25)]
  for a,b in zip(pts,pts[1:]):_tube(ribs,a,b,.16,1,8)
 ribs.finish()
 room.part('Soffitto — nascondibile')
 verts=[];faces=[];N=24
 for x in [-11.5,11.5]:
  for j in range(N+1):
   a=j*math.pi/N;verts.append((x,4.2*math.cos(a),3.6+2.45*math.sin(a)))
 for j in range(N):faces.append((j,j+1,j+1+N+1,j+N+1))
 I.mesh('Pozioni | volta',verts,faces,'stone')
 room.part('Luci e camere')
 for x in [-7,0,7]:I.area('Pozioni | luce dei banchi',(x,0,5.25),(x,0,.8),550,3.6,(1,.72,.35))
 I.area('Pozioni | luce diurna',(-3,-3.5,4.1),(2,1,1.3),650,3,(.64,.82,1))
 for x in [-9,9]:I.torch('Pozioni | torcia',(x,3.6,2.2))
 I.camera(room,'Camera | Aula Pozioni',(-10.2,0,1.8),(8.6,0,1.6),22)
 return _finish(room,(23,8.4),6.1,[(-11.5,0,0),(0,4.2,0)])


def _bed(frame,x,y,side):
 # Letti trasversali rispetto alla navata, testata verso il muro.
 z=.05;w=1.12;length=2.12
 frame.box((x,y,z+.40),(w,length,.12),0)
 for dx in [-w/2+.04,w/2-.04]:
  for dy in [-length/2+.06,length/2-.06]:_tube(frame,(x+dx,y+dy,z),(x+dx,y+dy,z+(.95 if dy*side>0 else .72)),.035,0,8)
 for edge,height in [(side*(length/2-.06),.94),(-side*(length/2-.06),.70)]:
  _tube(frame,(x-w/2+.04,y+edge,z+height),(x+w/2-.04,y+edge,z+height),.035,0,8)
  for dx in [-.32,-.16,0,.16,.32]:_tube(frame,(x+dx,y+edge,z+.43),(x+dx,y+edge,z+height-.02),.018,0,6)
 I.box('Infermeria | materasso',(x,y,.57),(1.07,2.04,.22),'int_white',bevel=.10)
 I.box('Infermeria | guanciale',(x,y+side*.73,.76),(.82,.48,.16),'int_white',bevel=.10)
 # Coperta che scende leggermente sui bordi, con lievi pieghe.
 vs=[];fs=[];nx=9;ny=10
 for i in range(nx):
  u=-.62+i*1.24/(nx-1)
  for j in range(ny):
   v=-.95+j*1.45/(ny-1)
   zz=.704-.22*max(0,(abs(u)-.49)/.13)+.012*math.sin(i*2.5+j*1.7)
   vs.append((x+u,y-side*v,zz))
 for i in range(nx-1):
  for j in range(ny-1):a=i*ny+j;fs.append((a,a+1,a+ny+1,a+ny))
 o=I.mesh('Infermeria | coperta in lino',vs,fs,'int_white')
 for f in o.data.polygons:f.use_smooth=True


def infirmary():
 room=I.Room('64 • Infermeria',(-38.5,-61.9,81.4),math.pi/2)
 room.part('Pavimento');I.box('Infermeria | lastre',(0,0,-.1),(44,9.4,.2),'path')
 room.part('Letti e arredi')
 A.M['int_bedmetal']=I.material('Letti | ferro chiaro',(.40,.43,.40),.43,.55)
 frame=I.Batch('Infermeria | telai dei letti',['int_bedmetal'])
 for x in [-18,-13.5,-9,-4.5,4.5,9,13.5,18]:
  for side in [-1,1]:
   _bed(frame,x,side*3.05,side)
   I.table('Infermeria | comodino',(x+1.2,side*3.3,.05),.55,.50,.58,'int_oak')
   I.cone('Infermeria | brocca',(x+1.2,side*3.3,.67),.10,.075,.24,'int_white',16)
   I.cone('Infermeria | catino',(x+1.2,side*3.3,.65),.16,.20,.07,'int_white',20)
 frame.finish()
 # Paraventi pieghevoli in lino, disposti fra gruppi di letti.
 screens=I.Batch('Infermeria | paraventi',['int_bedmetal','int_white'])
 for x,y in [(-11.2,-2.7),(11.2,2.7)]:
  for j in range(3):
   xx=x+(j-1)*.62;angle=(-1 if j%2 else 1)*.22
   screens.box((xx,y,1.05),(.62,.045,1.35),1,angle)
   for dx in [-.31,.31]:_tube(screens,(xx+dx*math.cos(angle),y+dx*math.sin(angle),.1),(xx+dx*math.cos(angle),y+dx*math.sin(angle),1.78),.025,0)
 screens.finish()
 # Armadi medicinali con ripiani e flaconi, non librerie generiche.
 A.M['int_medicine']=I.material('Infermeria | vetro ambrato',(.18,.095,.025),.20)
 meds=I.Batch('Infermeria | armadi e medicinali',['int_wood','glass','int_medicine','int_white'])
 for side in [-1,1]:
  xx=20.4;yy=side*3.0
  for dy in [-1.1,1.1]:meds.box((xx,yy+dy,1.30),(.58,.10,2.5),0)
  meds.box((xx+.25,yy,1.30),(.08,2.2,2.5),0)
  for row,zz in enumerate([.18,.78,1.38,1.98,2.55]):
   meds.box((xx,yy,zz),(.62,2.35,.08),0)
   if row==4:continue
   for j in range(7):
    by=yy-.9+j*.3;h=.22+.06*((row+j)%3);r=.075
    _lathe(meds,(xx-.02,by,zz+.05),[(r,0),(r,h*.7),(r*.4,h*.82),(r*.4,h)],1+(row+j)%3,12)
    _lathe(meds,(xx-.02,by,zz+.05+h),[(r*.48,0),(r*.48,.04)],0,8)
 meds.finish()
 I.table('Infermeria | scrittoio',(19.5,0,.05),2.0,1.05,.82)
 room.part('Volte e pilastri')
 ribs=I.Batch('Infermeria | nervature gotiche',['trim'])
 bays=[-21,-15,-9,-3,3,9,15,21]
 for x in bays:
  for side in [-1,1]:_tube(ribs,(x,side*4.45,.05),(x,side*4.45,4.3),.13,0,10)
  pts=[(x,4.45*math.cos(j*math.pi/28),4.3+2.65*math.sin(j*math.pi/28)) for j in range(29)]
  for a,b in zip(pts,pts[1:]):_tube(ribs,a,b,.11,0,8)
 for x0,x1 in zip(bays,bays[1:]):
  for side in [-1,1]:
   pts=[(x0+(x1-x0)*t,side*4.45*(1-2*t),4.3+2.65*math.sin(math.pi*t)) for t in [j/20 for j in range(21)]]
   for a,b in zip(pts,pts[1:]):_tube(ribs,a,b,.065,0,6)
 ribs.finish()
 room.part('Soffitto — nascondibile')
 vs=[];fs=[];N=28
 for x in [-22,22]:
  for j in range(N+1):
   a=j*math.pi/N;vs.append((x,4.70*math.cos(a),4.3+2.85*math.sin(a)))
 for j in range(N):fs.append((j,j+1,j+1+N+1,j+N+1))
 I.mesh('Infermeria | volta chiara',vs,fs,'int_white')
 room.part('Luci e camere')
 for x in [-17,-6,6,17]:I.area('Infermeria | luce diffusa',(x,0,6.3),(x,0,0),750,5,(1,.91,.76))
 for side in [-1,1]:
  for x in [-15,0,15]:I.area('Infermeria | luce delle finestre',(x,side*4.4,4.8),(x,0,1),950,3.5,(.80,.90,1))
 I.camera(room,'Camera | Infermeria',(-20,0,1.65),(17,0,2.0),23)
 return _finish(room,(44,9.4),7.2,[(-22,0,0),(0,4.7,0),(0,-4.7,0)])


def transfiguration():
 room=I.Room('65 • Aula Trasfigurazione',(-5,-32.6,73.4),0)
 room.part('Pavimento');I.box('Trasfigurazione | pavimento',(0,0,-.10),(23,8.5,.2),'path')
 room.part('Arredi')
 for x in [-3,1,5,8]:
  for y in [-2.4,2.4]:
   I.table('Trasfigurazione | banco',(x,y,.04),.78,1.65,.78,'int_oak')
   for dy in [-.43,.43]:I.chair('Trasfigurazione | sedia',(x+.82,y+dy,.04),'int_wood',-math.pi/2)
   for dy in [-.4,.4]:
    I.box('Trasfigurazione | libro',(x,y+dy,.88),(.35,.27,.07),'book1',.13)
 I.table('Trasfigurazione | cattedra',(-8.3,0,.04),1.3,2.6,.9,'int_wood')
 I.chair('Trasfigurazione | sedia docente',(-9.5,0,.04),'int_wood',math.pi/2)
 # Lavagna e diagrammi, orientati verso gli studenti.
 I.box('Trasfigurazione | cornice lavagna',(-10.9,0,2.55),(.22,5.3,2.7),'int_wood')
 I.box('Trasfigurazione | lavagna',(-10.75,0,2.55),(.07,4.95,2.37),'int_chalk')
 _text('Trasfigurazione | titolo','TRASFIGURAZIONE',(-10.69,0,3.33),.30,math.pi/2,'int_paper')
 chalk=I.Batch('Trasfigurazione | segni di gesso',['int_paper'])
 for cy,r in [(-1.35,.46),(1.25,.62)]:
  pts=[(-10.70,cy+r*math.cos(j*math.tau/32),2.35+r*math.sin(j*math.tau/32)) for j in range(33)]
  for a,b in zip(pts,pts[1:]):_tube(chalk,a,b,.012,0,5)
 for a,b in [((-10.70,-.6,2.35),(-10.70,.4,2.35)),((-10.70,.15,2.6),(-10.70,.4,2.35)),((-10.70,.15,2.1),(-10.70,.4,2.35))]:_tube(chalk,a,b,.018,0,5)
 chalk.finish()
 for y in [-3.6,3.6]:I.bookcase('Trasfigurazione | armadio',(-7.1,y,.04),2.2,3.5,.55,0 if y>0 else math.pi,5,int(y*10)+80)
 I.cone('Trasfigurazione | supporto dimostrazione',(-8.3,0,1.0),.24,.18,.32,'int_brass',20)
 # Oggetti di studio: coppa, cubo e sfera sfaccettata.
 I.cone('Trasfigurazione | coppa',(-8.3,0,1.32),.12,.28,.36,'int_brass',24)
 I.box('Trasfigurazione | cubo di studio',(-8.3,.8,1.18),(.35,.35,.35),'int_wood')
 I.cone('Trasfigurazione | prisma di studio',(-8.3,-.8,1.0),.22,.22,.42,'int_brass',6)
 room.part('Architettura interna')
 ribs=I.Batch('Trasfigurazione | archi',['stone','trim'])
 for x in [-10,-5,0,5,10]:
  for side in [-1,1]:_tube(ribs,(x,side*4.08,0),(x,side*4.08,3.8),.14,0,10)
  pts=[(x,4.08*math.cos(j*math.pi/20),3.8+2.0*math.sin(j*math.pi/20)) for j in range(21)]
  for a,b in zip(pts,pts[1:]):_tube(ribs,a,b,.12,1,8)
 ribs.finish()
 room.part('Soffitto — nascondibile')
 I.box('Trasfigurazione | soffitto',(0,0,6.05),(23,8.5,.15),'stone')
 for x in [-9,-3,3,9]:I.box('Trasfigurazione | trave',(x,0,5.82),(.25,8.5,.35),'int_wood')
 room.part('Luci e camere')
 for x in [-7,0,7]:I.area('Trasfigurazione | luce alta',(x,0,5.5),(x,0,1),700,4,(1,.82,.58))
 I.area('Trasfigurazione | luce della finestra',(0,-3.8,4.6),(0,0,1),850,4,(.78,.9,1))
 I.camera(room,'Camera | Aula Trasfigurazione',(10.2,0,1.75),(-8,0,2.1),22)
 return _finish(room,(23,8.5),6.1,[(11.5,0,0)])


def apply():
 before=set(bpy.data.objects);rooms=[library(),potions(),infirmary(),transfiguration()]
 new=[o for o in bpy.data.objects if o not in before]
 stats={'rooms':rooms,'objects':len(new),'mesh_objects':sum(o.type=='MESH' for o in new),'faces':sum(len(o.data.polygons) for o in new if o.type=='MESH'),'lights':sum(o.type=='LIGHT' for o in new),'cameras':[o.name for o in new if o.type=='CAMERA']}
 if stats['faces']>350000 or stats['objects']>2000:raise RuntimeError('Limite del modulo aule superato: '+str((stats['objects'],stats['faces'])))
 return stats
