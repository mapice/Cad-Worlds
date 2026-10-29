"""Corridoi, pianerottoli e passaggi reali fra i principali ambienti."""
import bpy,math
from mathutils import Vector
import interior_kit as I
A=I.A
ROUTES=[]

def floor_ring(name,left,right,bottom,top,width,z):
 outer=[(left-width/2,bottom-width/2),(right+width/2,bottom-width/2),(right+width/2,top+width/2),(left-width/2,top+width/2)]
 inner=[(left+width/2,bottom+width/2),(right-width/2,bottom+width/2),(right-width/2,top-width/2),(left+width/2,top-width/2)]
 vs=[(x,y,zz) for zz in [z-.28,z] for poly in [outer,inner] for x,y in poly];fs=[]
 for i in range(4):
  j=(i+1)%4;fs.extend([(i,j,8+j,8+i),(4+j,4+i,12+i,12+j),(8+i,8+j,12+j,12+i),(4+i,4+j,j,i)])
 return I.mesh(name,vs,fs,'path')

def floor_strip(name,a,b,z,width=2.4):
 dx=b[0]-a[0];dy=b[1]-a[1];L=math.hypot(dx,dy)
 if L<.05:return None
 return I.box(name,((a[0]+b[0])/2,(a[1]+b[1])/2,z-.15),(L,width,.3),'path',math.atan2(dy,dx))

def flight(name,a,b,width=2.4,rail=True):
 a=Vector(a);b=Vector(b)
 if a.z>b.z:a,b=b,a
 d=Vector((b.x-a.x,b.y-a.y,0));L=d.length
 if L<.1:return
 d.normalize();n=Vector((-d.y,d.x,0));h=b.z-a.z
 if h<.05:return floor_strip(name,a,b,a.z,width)
 N=math.ceil(h/.18);rise=h/N;run=L/N
 poly=[(0,a.z-.55),(L,b.z-.55),(L,b.z)]
 for j in range(N-1,-1,-1):poly.extend([(j*run,a.z+(j+1)*rise),(j*run,a.z+j*rise)])
 vs=[tuple(Vector((a.x,a.y,zz))+d*u+n*side*width/2) for side in [-1,1] for u,zz in poly];nn=len(poly)
 fs=[tuple(range(nn-1,-1,-1)),tuple(range(nn,2*nn))]+[(j,(j+1)%nn,(j+1)%nn+nn,j+nn) for j in range(nn)]
 o=I.mesh(name+' | gradini e base',vs,fs,'stone')
 if rail:
  for side in [-1,1]:
   p=a+n*side*(width/2-.06)+Vector((0,0,1.02));q=b+n*side*(width/2-.06)+Vector((0,0,1.02));I.beam(name+' | corrimano',p,q,.055,'int_wood',8)
   for j in range(0,N+1,3):
    t=j/N;zz=a.z+h*t;v=Vector((a.x,a.y,zz))+d*L*t+n*side*(width/2-.06);I.beam(name+' | balaustro',v,v+Vector((0,0,1.02)),.035,'int_wood',8)
 return o

def wall_with_door(name,a,b,z,h=6.1,thick=.28,door_at=None,door_width=2.1,door_height=3.2):
 aa=Vector((a[0],a[1],z));bb=Vector((b[0],b[1],z));d=bb-aa;L=d.length;d.normalize();ang=math.atan2(d.y,d.x)
 if door_at is None:door_at=L/2
 lo=max(0,door_at-door_width/2);hi=min(L,door_at+door_width/2)
 for p,q in [(0,lo),(hi,L)]:
  if q-p>.02:I.box(name+' | spalla',tuple(aa+d*((p+q)/2)+Vector((0,0,h/2))),(q-p,thick,h),'stone',ang)
 center=aa+d*door_at
 I.arch(name+' | arco del varco',tuple(center),door_width,door_height,thick,ang,h-door_height,'stone')
 for s in [-1,1]:I.beam(name+' | stipite',center+d*s*(door_width/2+.07),center+d*s*(door_width/2+.07)+Vector((0,0,door_height-door_width/2)),.10,'trim',8)


def apply():
 room=I.Room('73 • Corridoi, aule e accessi',(0,0,0))
 for level in [73.4,80,93.2,99.8]:
  room.part('Piano '+str(level))
  floor_ring('Quad | corridoio continuo '+str(level),-32.3,14.6,-88.5,-39.2,2.4,level-.04)
  # Raccordo al vano della grande scalinata.
  floor_strip('Quad | raccordo scala '+str(level),(14.6,-84),(23,-84),level-.03,2.4)
  # Collegamento nordoccidentale alla torre di Grifondoro.
  if level in [93.2,99.8]:
   floor_strip('Grifondoro | corridoio nord',(-32.3,-39.2),(-37,-34),level-.02,2.4)
   floor_strip('Grifondoro | soglia',(-37,-34),(-38.25,-31.7),level-.02,2.4)
  # Lanterne e ritratti, senza chiudere il corridoio.
  for x in [-27,-13,1,11]:
   I.portrait('Quad | ritratto sul corridoio',(x,-40.08,level+1.6),1.0,1.6,math.pi,int(x)%6)
  for x,y in [(-28,-39),(-30,-82),(13,-52),(7,-88)]:I.point('Quad | luce soffusa',(x,y,level+3.6),140,(1,.74,.45),1.2)
 # Pareti di separazione dei vani: porte sulla stessa quota dei corridoi.
 room.part('Porte e divisori delle aule')
 wall_with_door('Pozioni | parete corridoio',(16.0,-64.0),(16.0,-40.6),73.4,6.1,.28,11.666,2.0,3.2)
 wall_with_door('Pozioni | parete sud',(16.0,-64.0),(24.6,-64.0),73.4,6.1,.28,4.4,2.1,3.2)
 I.box('Pozioni | parete nord',(20.3,-40.6,76.45),(8.6,.28,6.1),'stone')
 floor_strip('Pozioni | soglia laterale',(14.6,-52.334),(17,-52.334),73.38,2.0)
 wall_with_door('Trasfigurazione | ingresso est',(6.7,-37),(6.7,-28.3),73.4,6.1,.28,4.4,2.0,3.2)
 I.box('Trasfigurazione | parete sud',(-5,-37.05,76.45),(23.4,.28,6.1),'stone')
 I.box('Trasfigurazione | parete ovest',(-16.7,-32.6,76.45),(.28,8.9,6.1),'stone')
 floor_strip('Trasfigurazione | raccordo',(9,-39.2),(9,-32.6),73.38,2.2)
 floor_strip('Trasfigurazione | soglia',(9,-32.6),(6.5,-32.6),73.38,2.2)
 wall_with_door('Infermeria | parete corridoio',(-33.65,-84.1),(-33.65,-39.7),81.4,7.2,.28,22.2,2.1,3.3)
 wall_with_door('Infermeria | testata sud',(-43.3,-84.1),(-33.65,-84.1),81.4,7.2,.28,4.8,2.1,3.3)
 I.box('Infermeria | testata nord',(-38.5,-39.7,85),(9.65,.28,7.2),'stone')
 floor_strip('Infermeria | corridoio rialzato',(-32.3,-84.5),(-32.3,-42),81.36,2.4)
 flight('Infermeria | raccordo sud',(-32.3,-88.5,80),(-32.3,-84.5,81.4),2.4)
 flight('Infermeria | raccordo nord',(-32.3,-38,80),(-32.3,-42,81.4),2.4)
 floor_strip('Infermeria | soglia',(-32.3,-61.9),(-34.0,-61.9),81.38,2.2)
 room.finish()

 room=I.Room('74 • Ingresso del viadotto e percorso biblioteca',(0,0,0))
 room.part('Piano pubblico e galleria alta')
 I.box('Ingresso viadotto | pavimento interno',(75.9,-8.0,60.25),(56.0,17.0,.3),'path')
 I.box('Ingresso viadotto | galleria alta',(75.9,-8.0,83.85),(56.0,16.8,.3),'path')
 # Scala a due rampe per livello nell'ala occidentale, con veri varchi nei solai.
 # I livelli intermedi sono pianerottoli stretti, non dischi che tagliano le rampe.
 xs=[52.5,56.4];y0=-13.8;y1=-2.6;levels=[60.4,66.3,72.2,78.1,84.0]
 for i,(za,zb) in enumerate(zip(levels,levels[1:])):
  mid=(za+zb)/2
  flight('Ingresso viadotto | scala ovest', (xs[0],y0,za),(xs[0],y1,mid),2.4)
  floor_strip('Ingresso viadotto | pianerottolo',(xs[0]-1.2,y1),(xs[1]+1.2,y1),mid,2.5)
  flight('Ingresso viadotto | scala est',(xs[1],y1,mid),(xs[1],y0,zb),2.4)
  floor_strip('Ingresso viadotto | arrivo',(xs[0]-1.2,y0),(xs[1]+1.2,y0),zb,2.5)
 # Foro nella galleria alta sopra le rampe in arrivo.
 import shells_v6 as S
 slab=bpy.data.objects['Ingresso viadotto | galleria alta']
 cut=S.box_cutter('TEMP foro scala ingresso',(54.45,-8.2,84),(7.2,10.4,2),0);S.subtract(slab,cut);S.CUTTERS.remove(cut);bpy.data.objects.remove(cut,do_unlink=True)
 for x in [53,75,98]:
  I.area('Ingresso viadotto | luce',(x,-8,89),(x,-8,84),500,4,(1,.8,.55))
  I.area('Ingresso viadotto | luce bassa',(x,-8,68),(x,-8,61),500,4,(1,.8,.55))
 room.part('Discesa verso la biblioteca')
 floor_strip('Navata | pavimento',(75.6,1.5),(75.6,36.1),55.36,6.0)
 flight('Navata | scala verso biblioteca',(75.6,14.5,55.4),(75.6,2.0,60.4),3.2)
 I.box('Centrale | vestibolo interno',(75.6,25.2,55.2),(18.5,18.5,.3),'path')
 for yy in [8,23,32]:I.area('Navata | luce',(75.6,yy,64),(75.6,yy,56),600,4,(1,.78,.5))
 # Galleria laterale al cortile Durham e soglia della biblioteca.
 floor_strip('Durham | corridoio orientale',(57.0,38),(57.0,94),55.46,3.6)
 floor_strip('Biblioteca | accesso dal chiostro',(50.4,62.03),(63.0,62.03),55.45,2.4)
 for yy in [44,62,80]:I.point('Durham | luce',(57,yy,60),170,(1,.75,.46),1)
 room.finish()

 room=I.Room('75 • Scala verso il ponte alto',(24,-31.324,73.4))
 room.part('Scala e pianerottoli')
 N=math.ceil(10.6/.18);r=2.25;w=1.35;turns=1.45
 # Gradini a settore: angolo e livello crescono insieme.
 for j in range(N):
  a=j/N*math.tau*turns;b=(j+1)/N*math.tau*turns;z=(j+1)/N*10.6
  poly=[(rr*math.cos(t),rr*math.sin(t)) for rr,t in [(r-w/2,a),(r+w/2,a),(r+w/2,b),(r-w/2,b)]]
  A.prism('Ponte alto | pedata a chiocciola',poly,z-.24,.24,'stone')
  p=( (r+w/2)*math.cos(b),(r+w/2)*math.sin(b),z)
  I.beam('Ponte alto | balaustro',p,(p[0],p[1],z+1.0),.035,'int_wood',6)
 angle=math.tau*turns
 floor_strip('Ponte alto | uscita',(r*math.cos(angle),r*math.sin(angle)),(0,0),10.6,2.4)
 floor_strip('Ponte alto | passerella alla porta',(0,0),(6.0,4.0),10.6,2.6)
 I.point('Ponte alto | luce interna',(0,0,13.0),400,(1,.76,.45),1.0)
 room.finish()
 return {'groups':['73 • Corridoi, aule e accessi','74 • Ingresso del viadotto e percorso biblioteca','75 • Scala verso il ponte alto'],'quad_levels':[73.4,80,93.2,99.8],'infirmary_floor':81.4,'library_floor':55.4,'gate_floors':[60.4,84.0]}
