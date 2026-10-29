"""Scale e ballatoi interni; applicare dopo il kit e gli ambienti arredati.
Le aperture dei solai sono geometriche, non semplici superfici scure.
"""
import bpy,math
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt
import interior_kit as I

TAU=2*math.pi
GRAND_LEVELS=[60.4,66.9,73.4,80.,86.6,93.2,99.8,106.4,113.,119.6,126.2,134.4]
ASTRO_LEVELS=[55.4,68.4,81.4,94.4,107.4,120.4,133.4,146.4,154.4]
BELVEDERE_OUTER_RADIUS=1.0


def rot(p,a):
 x,y=p;return(x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a))

def inside(p,poly):
 x,y=p;b=False
 for i,(ax,ay) in enumerate(poly):
  bx,by=poly[(i+1)%len(poly)]
  if (ay>y)!=(by>y) and x<(bx-ax)*(y-ay)/(by-ay)+ax:b=not b
 return b

def floor_ring(name,center,z,outer,inner,holes=None,thickness=.24):
 cx,cy=center;holes=holes or [];n=128
 pts=[Vector((cx+outer*math.cos(TAU*j/n),cy+outer*math.sin(TAU*j/n))) for j in range(n)];loops=[list(range(n))]
 if inner:
  k=len(pts);pts.extend(Vector((cx+inner*math.cos(TAU*j/n),cy+inner*math.sin(TAU*j/n))) for j in range(n));loops.append(list(range(k,k+n)))
 for poly in holes:
  k=len(pts);pts.extend(Vector(v) for v in poly);loops.append(list(range(k,len(pts))))
 vv,ee,ff,*_=delaunay_2d_cdt(pts,[],loops,1,.0001,False)
 keep=[]
 for face in ff:
  c=sum((vv[i] for i in face),Vector((0,0)))/len(face);r=math.hypot(c.x-cx,c.y-cy)
  if r<=outer+1e-5 and r>=inner-1e-5 and not any(inside((c.x,c.y),poly) for poly in holes):keep.append(face)
 k=len(vv);verts=[(v.x,v.y,zz) for zz in (z-thickness,z) for v in vv];faces=[];edge_count={};directions={}
 for face in keep:
  faces.extend([tuple(i+k for i in face),tuple(reversed(face))])
  for a,b in zip(face,face[1:]+face[:1]):
   e=tuple(sorted((a,b)));edge_count[e]=edge_count.get(e,0)+1;directions[e]=(a,b)
 for e,num in edge_count.items():
  if num==1:
   a,b=directions[e];faces.append((a,b,b+k,a+k))
 ob=I.mesh(name,verts,faces,'path');ob['Quota piano']=z;ob['Foro centrale']=inner;return ob


class Geo(I.Batch):
 def __init__(self,name,mat):super().__init__(name,[mat])
 def tube(self,a,b,r,n=8):
  a=Vector(a);b=Vector(b);d=b-a
  if d.length<1e-7:return
  d.normalize();u=d.cross(Vector((0,0,1)))
  if u.length<.01:u=d.cross(Vector((0,1,0)))
  u.normalize();v=d.cross(u)
  pts=[tuple(p+r*(u*math.cos(TAU*j/n)+v*math.sin(TAU*j/n))) for p in (a,b) for j in range(n)]
  fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
  self.shape(pts,fs)
 def band(self,a,b,width,zlow,zhigh):
  # Striscia inclinata a quota variabile, definita da due punti XYZ.
  a=Vector(a);b=Vector(b);d=b-a;L=math.hypot(d.x,d.y)
  if L<1e-8:return
  nx=-d.y/L*width/2;ny=d.x/L*width/2
  pts=[(p.x+side*nx,p.y+side*ny,p.z+zz) for zz in (zlow,zhigh) for p,side in [(a,-1),(b,-1),(b,1),(a,1)]]
  self.shape(pts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
 def sector(self,c,r0,r1,a0,a1,z,h,sub=2):
  x,y=c;n=sub+1;points=[]
  for zz in (z-h,z):
   for rr in (r0,r1):
    for j in range(n):
     a=a0+(a1-a0)*j/sub;points.append((x+rr*math.cos(a),y+rr*math.sin(a),zz))
  fs=[];stride=2*n
  for j in range(sub):
   fs.extend([(j,n+j,n+j+1,j+1),(stride+j,stride+j+1,stride+n+j+1,stride+n+j),(j,j+1,stride+j+1,stride+j),(n+j,n+j+stride,n+j+1+stride,n+j+1)])
  fs += [(0,stride,stride+n,n),(n-1,2*n-1,2*n-1+stride,n-1+stride)]
  if a1>a0:fs=[tuple(reversed(f)) for f in fs]
  self.shape(points,fs)


def rail_ring(rail,posts,c,r,z,skip=None,height=1.03,n=112):
 for j in range(n):
  a=TAU*j/n;b=TAU*(j+1)/n;m=(a+b)/2
  if skip and skip(m):continue
  p=(c[0]+r*math.cos(a),c[1]+r*math.sin(a),z+height);q=(c[0]+r*math.cos(b),c[1]+r*math.sin(b),z+height)
  rail.tube(p,q,.065,8)
  if j%3==0:posts.tube((p[0],p[1],z+.05),p,.045,7)


def straight_flight(body,rail,posts,a,b,width=2.4,riser=.18):
 a=Vector(a);b=Vector(b);d=b-a;L=math.hypot(d.x,d.y);count=max(1,math.ceil(abs(d.z)/riser));rise=d.z/count;dx=d.x/L;dy=d.y/L;ang=math.atan2(dy,dx)
 for j in range(count):
  t=(j+.5)/count;z=a.z+(j+1)*rise
  body.box((a.x+d.x*t,a.y+d.y*t,z-.14),(L/count,width,.28),0,ang)
 body.band(a,b,width,-.48,-.18)
 for side in (-1,1):
  nx=-dy*(width/2-.055)*side;ny=dx*(width/2-.055)*side
  p=a+Vector((nx,ny,1.05));q=b+Vector((nx,ny,1.05));rail.tube(p,q,.07,8)
  N=max(2,math.ceil(L/1.25))
  for j in range(N+1):
   t=j/N;v=a+d*t+Vector((nx,ny,.06));posts.tube(v,v+Vector((0,0,.99)),.045,7)
 return count


def spiral(body,rail,posts,c,z0,z1,r0,r1,start_angle,turns):
 count=math.ceil((z1-z0)/.18);rise=(z1-z0)/count;step=turns*TAU/count
 for j in range(count):
  a=start_angle+j*step;b=a+step;top=z0+(j+1)*rise
  body.sector(c,r0,r1,a,b,top,.18 if r1<2 else .27,2)
 for r in [r0+.045,r1-.045]:
  last=None
  for j in range(count+1):
   a=start_angle+j*step;z=z0+j*rise
   p=(c[0]+r*math.cos(a),c[1]+r*math.sin(a),z+1.03)
   if last:rail.tube(last,p,.05 if r1<2 else .065,7)
   if j%2==0:posts.tube((p[0],p[1],z+.04),p,.03 if r1<2 else .045,7)
   last=p
 return {'steps':count,'riser':rise,'turns':turns,'end_angle':start_angle+turns*TAU,'pitch':(z1-z0)/turns}


def torch_at(name,p,a,power=60):
 x,y,z=p;n=Vector((-math.cos(a),-math.sin(a),0));q=Vector((x,y,z))+n*.35
 I.beam(name+' | braccio',(x,y,z),q,.04,'int_iron',8)
 I.cone(name+' | coppa',(q.x,q.y,q.z),.08,.14,.20,'int_brass',10)
 I.candle(name+' | candela',(q.x,q.y,q.z+.20),.30)
 I.point(name+' | luce',(q.x+n.x*.2,q.y+n.y*.2,q.z+.60),power,(1,.66,.32),.35)


def grand_staircase():
 room=I.Room('70 • Grande scalinata',(21.6,-97.028,0))
 room.part('Pavimenti');holes_by_floor=[]
 for i,z in enumerate(GRAND_LEVELS):
  holes=[]
  if i:
   angle=(i-1)*math.pi/2
   holes=[[rot(p,angle) for p in [(-9.9,-11.65),(8.6,-11.65),(8.6,-8.35),(-9.9,-8.35)]]]
  floor_ring('Scalinata | ballatoio '+str(i),(0,0),z,15.1,8.7 if i else 0,holes,.25)
  holes_by_floor.append(holes)
 room.part('Rampe');body=Geo('Scalinata | rampe collegate','stone');rails=Geo('Scalinata | corrimano continui','int_oak');posts=Geo('Scalinata | balaustri','int_wood');steps=0
 for i,(z0,z1) in enumerate(zip(GRAND_LEVELS,GRAND_LEVELS[1:])):
  angle=i*math.pi/2;a=rot((-8.6,-10),angle);b=rot((8.6,-10),angle)
  steps+=straight_flight(body,rails,posts,(*a,z0),(*b,z1),2.4)
  # Le fasce piane di1.4m sono già parte del solaio; nessuna faccia sovrapposta.
 for i,z in enumerate(GRAND_LEVELS):
  if not i:continue
  hole=holes_by_floor[i][0]
  rail_ring(rails,posts,(0,0),8.75,z,lambda a,h=hole:inside((8.75*math.cos(a),8.75*math.sin(a)),h),1.03,112)
  # Tre lati protetti del vano in arrivo; il lato dell'uscita resta aperto.
  angle=(i-1)*math.pi/2
  for aa,bb in [((-10.05,-11.82),(8.6,-11.82)),((-10.05,-8.18),(8.6,-8.18)),((-10.05,-11.82),(-10.05,-8.18))]:
   L=math.dist(aa,bb);n=max(1,math.ceil(L/.5))
   for j in range(n):
    t0=j/n;t1=(j+1)/n;p=(aa[0]+(bb[0]-aa[0])*t0,aa[1]+(bb[1]-aa[1])*t0);q=(aa[0]+(bb[0]-aa[0])*t1,aa[1]+(bb[1]-aa[1])*t1);mid=((p[0]+q[0])/2,(p[1]+q[1])/2)
    if not 8.85<math.hypot(*mid)<14.95:continue
    p=rot(p,angle);q=rot(q,angle);rails.tube((*p,z+1.03),(*q,z+1.03),.065,7)
    if j%3==0:posts.tube((*p,z+.04),(*p,z+1.03),.045,7)
 body.finish();rails.finish();posts.finish()
 # Passaggio sul ballatoio superiore verso la seconda stanza di Silente.
 room.part('Collegamento Silente');a=Vector((14-21.6,-106+97.028,134.4));b=Vector((10.85-21.6,-106.65+97.028,134.4));walk=Geo('Silente | breve passaggio di accesso','path');walk.band(a,b,1.25,-.22,.015);walk.finish()
 room.part('Ritratti e luci')
 for i,z in enumerate(GRAND_LEVELS):
  for j,a in enumerate([math.pi/4,3*math.pi/4,5*math.pi/4]):
   x=15.15*math.cos(a);y=15.15*math.sin(a);I.portrait('Scalinata | ritratto al piano '+str(i),(x,y,z+1.7),1.05,1.65,a-math.pi/2,i+j)
  for a in [math.pi/2,3*math.pi/2]:torch_at('Scalinata | torcia al piano '+str(i),(14.8*math.cos(a),14.8*math.sin(a),z+2),a,90)
  I.area('Scalinata | luce morbida piano '+str(i),(0,0,z+4.5),(4,3,z+.4),450,7,(1,.79,.55))
 room.part('Camere');I.camera(room,'Interni | Grande scalinata',(0,-.5,62.3),(6,7,82),18)
 result=room.finish();result.update({'steps':steps,'levels':GRAND_LEVELS,'incoming_floor_openings':len(GRAND_LEVELS)-1,'dumbledore_link_world':[(14,-106,134.4),(10.85,-106.65,134.4)]});return result


def curved_run(body,rail,posts,c,r0,r1,a0,a1,z0,z1,count):
 rise=(z1-z0)/count
 for j in range(count):
  a=a0+(a1-a0)*j/count;b=a0+(a1-a0)*(j+1)/count
  body.sector(c,r0,r1,a,b,z0+(j+1)*rise,.27,2)
 for r in [r0+.035,r1-.035]:
  last=None
  for j in range(count+1):
   a=a0+(a1-a0)*j/count;z=z0+j*rise;p=(c[0]+r*math.cos(a),c[1]+r*math.sin(a),z+1.01)
   if last:rail.tube(last,p,.045,7)
   if j%2==0:posts.tube((p[0],p[1],z+.03),p,.03,7)
   last=p
 return rise


def gryffindor_stairs():
 room=I.Room('71 • Scala di Grifondoro',(-43.2,-26.74,93.2));room.part('Rampe')
 body=Geo('Grifondoro | due rampe curve','int_oak');rail=Geo('Grifondoro | corrimano scala','int_wood');posts=Geo('Grifondoro | balaustri scala','int_wood')
 zmid=6.6*17/36
 lower=curved_run(body,rail,posts,(0,0),4.1,5.15,math.radians(-21),math.radians(-75),0,zmid,17)
 curved_run(body,rail,posts,(0,0),5.45,6.5,math.radians(-75),math.radians(-15),zmid,6.6,19)
 # Pianerottolo di ritorno, compreso nel settore libero e sotto il solaio superiore.
 body.sector((0,0),4.1,6.5,math.radians(-87),math.radians(-73.5),zmid+.012,.22,5)
 # Il piccolo sbocco superiore supera il bordo angolare del foro; è lontano dai letti.
 body.sector((0,0),5.45,6.5,math.radians(-17),math.radians(-3),6.612,.22,5)
 for r in [4.1,6.5]:
  for j in range(5):
   aa=math.radians(-87+13.5*j/5);bb=math.radians(-87+13.5*(j+1)/5)
   rail.tube((r*math.cos(aa),r*math.sin(aa),zmid+1.01),(r*math.cos(bb),r*math.sin(bb),zmid+1.01),.045,7)
 # Due appoggi sotto il pianerottolo, fuori dall'area centrale della sala.
 for r in [4.25,6.35]:
  x=r*math.cos(math.radians(-82));y=r*math.sin(math.radians(-82));posts.tube((x,y,0),(x,y,zmid-.12),.09,10)
 body.finish();rail.finish();posts.finish()
 room.part('Luci');I.area('Grifondoro | luce del vano scala',(5,-3,5.9),(4,-3,1),180,2,(1,.78,.52))
 room.part('Camere');I.camera(room,'Interni | Scala di Grifondoro',(3,-6.25,1.6),(3.9,-4.3,4.1),20)
 result=room.finish();result.update({'steps':36,'riser':lower,'levels':[93.2,99.8],'radial_range':[4.1,6.5],'upper_exit_angles':[-17,-3]});return result


def astronomy_stairs():
 room=I.Room('72 • Collegamenti dell’Astronomia',(0,0,0));c=(31.2,30);bc=(20.8,11.988)
 room.part('Ballatoi');phase=math.radians(240)-(154.4-55.4)/13*TAU
 floor_angles=[]
 for i,z in enumerate(ASTRO_LEVELS):
  angle=phase+(z-55.4)/13*TAU;floor_angles.append(angle)
  floor_ring('Astronomia | ballatoio '+str(i),c,z,11.7,5.20 if i else 0,thickness=.25)
 room.part('Rampe');body=Geo('Astronomia | chiocciola ampia','stone');rails=Geo('Astronomia | corrimano e bordi','int_iron');posts=Geo('Astronomia | montanti','int_iron');main_steps=0
 for i,(z0,z1) in enumerate(zip(ASTRO_LEVELS,ASTRO_LEVELS[1:])):
  result=spiral(body,rails,posts,c,z0,z1,3.4,4.8,floor_angles[i],(z1-z0)/13);main_steps+=result['steps']
 for z,a in zip(ASTRO_LEVELS,floor_angles):
  p=(c[0]+4.45*math.cos(a),c[1]+4.45*math.sin(a),z);q=(c[0]+5.85*math.cos(a),c[1]+5.85*math.sin(a),z)
  body.band(p,q,1.45,-.25,.025)
  def skip(theta,aa=a):return abs(math.atan2(math.sin(theta-aa),math.cos(theta-aa)))<.20
  rail_ring(rails,posts,c,5.24,z,skip,1.03,96)
 body.finish();rails.finish();posts.finish()
 # Raccordo verso il tamburo: due pianerottoli e una breve rampa vera.
 room.part('Passaggio belvedere');bridge=Geo('Astronomia | rampa verso belvedere','stone');br=Geo('Astronomia | corrimano passerella','int_iron');bp=Geo('Astronomia | montanti passerella','int_iron')
 delta=Vector((bc[0]-c[0],bc[1]-c[1],0)).normalized();start=Vector((c[0],c[1],154.4))+delta*6.8;end=Vector((bc[0],bc[1],159.4))-delta*3.5
 bridge_steps=straight_flight(bridge,br,bp,start,end,1.65)
 # Tratti orizzontali agli estremi per raggiungere entrambi i ballatoi.
 bridge.band(Vector((c[0],c[1],154.4))+delta*5.4,start,1.65,-.25,.02)
 bridge.band(end,Vector((bc[0],bc[1],159.4))-delta*1.6,1.65,-.25,.02)
 bridge.finish();br.finish();bp.finish()
 room.part('Scala del belvedere');sb=Geo('Belvedere | gradini della chiocciola','int_oak');sr=Geo('Belvedere | corrimano','int_brass');sp=Geo('Belvedere | montanti','int_wood')
 count=math.ceil((202.7-159.4)/.18);turns=count/13;start_angle=-turns*TAU
 small=spiral(sb,sr,sp,bc,159.4,202.7,.30,BELVEDERE_OUTER_RADIUS,start_angle,turns)
 # Ingresso e uscita coprono soltanto il necessario varco radiale.
 angle=start_angle;p=(bc[0]+.88*math.cos(angle),bc[1]+.88*math.sin(angle),159.4);q=(bc[0]+1.8*math.cos(angle),bc[1]+1.8*math.sin(angle),159.4);sb.band(p,q,.78,-.20,.02)
 sb.band((bc[0]+.85,bc[1],202.7),(bc[0]+1.8,bc[1],202.7),.80,-.20,.02)
 # Pianerottolo inferiore anulare per raggiungere l'attacco della scala.
 floor_ring('Belvedere | ballatoio inferiore',bc,159.4,4.55,1.18,thickness=.22)
 I.cone('Belvedere | colonna centrale',(bc[0],bc[1],159.4),.31,.31,43.3,'int_wood',32)
 sb.finish();sr.finish();sp.finish()
 room.part('Luci')
 for i,z in enumerate(ASTRO_LEVELS):I.area('Astronomia | luce ballatoio '+str(i),(c[0]+1,c[1]+1,z+5),(c[0]+4,c[1],z+1),360,4,(.72,.83,1))
 for i in range(6):I.point('Belvedere | luce scala '+str(i),(bc[0]+1.35,bc[1]+.2,161+i*7.6),55,(1,.76,.46),.4)
 room.part('Camere');I.camera(room,'Interni | Chiocciola dell’Astronomia',(c[0]-.5,c[1]-.5,57.3),(c[0]+3.5,c[1]+2,78),18)
 result=room.finish();result.update({'main_steps':main_steps,'main_levels':ASTRO_LEVELS,'bridge_steps':bridge_steps,'bridge_endpoints':[tuple(start),tuple(end)],'belvedere_steps':small['steps'],'belvedere_pitch':small['pitch'],'belvedere_outer_radius':BELVEDERE_OUTER_RADIUS,'observatory_hole_required':1.15,'observatory_exit_world':[(bc[0]+.85,bc[1],202.7),(bc[0]+1.8,bc[1],202.7)]});return result


def apply():
 I.init();before=set(bpy.data.objects)
 rooms=[grand_staircase(),gryffindor_stairs(),astronomy_stairs()]
 new=[o for o in bpy.data.objects if o not in before];faces=sum(len(o.data.polygons) for o in new if o.type=='MESH')
 empty=[o.name for o in new if o.type=='MESH' and not o.data.polygons]
 nonfinite=[o.name for o in new if o.type=='MESH' and any(not math.isfinite(v) for p in o.data.vertices for v in p.co)]
 if empty or nonfinite or len(new)>800 or faces>150000:raise RuntimeError(str({'empty':empty,'nonfinite':nonfinite,'objects':len(new),'faces':faces}))
 return {'rooms':rooms,'objects_added':len(new),'faces_added':faces,'empty':empty,'nonfinite':nonfinite}
