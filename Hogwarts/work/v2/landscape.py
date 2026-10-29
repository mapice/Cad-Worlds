import math,random,bpy
from mathutils import Vector
from mathutils.geometry import tessellate_polygon, delaunay_2d_cdt
import architecture as A
random.seed(27)

def cliff(name,uv,height):
 # Contorno densificato e quattro strati rocciosi, senza chiudere la gola.
 points=[]
 for i,p in enumerate(uv):
  q=uv[(i+1)%len(uv)];dist=math.dist(A.xy(*p),A.xy(*q));steps=max(1,int(dist/4))
  for j in range(steps):
   t=j/steps;points.append(A.xy(p[0]+(q[0]-p[0])*t,p[1]+(q[1]-p[1])*t))
 n=len(points);cx=sum(x for x,y in points)/n;cy=sum(y for x,y in points)/n;vs=[]
 for k,(frac,zz) in enumerate([(1.09,2),(1.055,height*.30),(1.025,height*.68),(1,height)]):
  for i,(x,y) in enumerate(points):
   jitter=random.uniform(-1.5,1.5) if k in(1,2) else 0
   dx=x-cx;dy=y-cy;dd=max(1,math.hypot(dx,dy))
   vs.append((cx+dx*frac+jitter*dx/dd,cy+dy*frac+jitter*dy/dd,zz+(random.uniform(-2,2) if k in(1,2) else 0)))
 fs=[]
 for k in range(3):
  for i in range(n):
   j=(i+1)%n;a=k*n+i;b=k*n+j;c=(k+1)*n+j;d=(k+1)*n+i;fs.extend([(a,b,d),(b,c,d)])
 o=A.mesh(name+' | pareti rocciose',vs,fs,'rock')
 # Plateau concavo triangolato.
 pv=[Vector((x,y,height)) for x,y in points];idx={(round(p.x,6),round(p.y,6)):i for i,p in enumerate(pv)}
 tf=[tuple((v if isinstance(v,int) else idx[(round(v.x,6),round(v.y,6))]) for v in tri) for tri in tessellate_polygon([pv])]
 A.mesh(name+' | sommità',pv,tf,'grass')
 return o

def inside(u,v,poly):
 b=False
 for i,(a,c) in enumerate(poly):
  d,e=poly[(i+1)%len(poly)]
  if (c>v)!=(e>v) and u<(d-a)*(v-c)/(e-c)+a:b=not b
 return b

def smooth(t):
 t=max(0,min(1,t));return t*t*(3-2*t)

def west_height(u,v):
 h=48+7*math.sin(u*19)*math.cos(v*14)+5*math.sin(u*34+v*11)
 valley=math.exp(-((u-.235)/.058)**4-((v-.713)/.043)**2)
 h=h*(1-valley)+(29+3*math.sin(u*30))*valley
 # Pianori con raccordi morbidi, senza gradoni circolari.
 dx=max(.292-u,0,u-.410)*600;dy=max(.645-v,0,v-.781)*382
 d=math.hypot(dx,dy);w=1-smooth(d/16)
 h=h*(1-w)+69.6*w
 for uu,vv,level,core,outer in [(.145,.713,69.8,9,31),(.182,.354,89.8,9,48)]:
  dd=math.hypot((u-uu)*600,(v-vv)*382);ww=1-smooth((dd-core)/(outer-core));h=h*(1-ww)+level*ww
 if .30<u<.51 and v<.27:
  dd=min((u-.30)*600,(.51-u)*600,(.27-v)*382);ww=smooth(dd/10);h=h*(1-ww)+55*ww
 return h

def terrain_surface(name,poly,height_func,step=4.5,material='grass'):
 boundary=[]
 for i,p in enumerate(poly):
  q=poly[(i+1)%len(poly)];n=max(1,int(math.dist(A.xy(*p),A.xy(*q))/step))
  for j in range(n):boundary.append(A.xy(p[0]+(q[0]-p[0])*j/n,p[1]+(q[1]-p[1])*j/n))
 area=sum(boundary[i][0]*boundary[(i+1)%len(boundary)][1]-boundary[(i+1)%len(boundary)][0]*boundary[i][1] for i in range(len(boundary)))
 if area<0:boundary.reverse()
 vertices=[Vector(p) for p in boundary];bn=len(boundary)
 xmin=min(x for x,y in boundary);xmax=max(x for x,y in boundary);ymin=min(y for x,y in boundary);ymax=max(y for x,y in boundary)
 for i in range(int((xmax-xmin)/step)):
  for j in range(int((ymax-ymin)/step)):
   x=xmin+(i+.5)*step;y=ymin+(j+.5)*step;u=x/600+.5;v=.55-y/382
   if inside(u,v,poly):vertices.append(Vector((x,y)))
 vv,ee,ff,*_=delaunay_2d_cdt(vertices,[],[list(range(bn))],1,0.001,False)
 vs=[(v.x,v.y,height_func(v.x/600+.5,.55-v.y/382)) for v in vv]
 o=A.mesh(name+' | superficie',vs,ff,material)
 for f in o.data.polygons:f.use_smooth=True
 edges={}
 for f in ff:
  for k in range(len(f)):
   edge=tuple(sorted((f[k],f[(k+1)%len(f)])));edges[edge]=edges.get(edge,0)+1
 # Bordi fedeli al contorno, senza il dente del reticolo quadrato.
 sv=[];sf=[];lookup={}
 def vert(i,low):
  key=(i,low)
  if key not in lookup:
   x,y,z=vs[i];lookup[key]=len(sv);sv.append((x,y,.1 if low else z))
  return lookup[key]
 for (a,b),count in edges.items():
  if count==1:sf.append((vert(a,False),vert(b,False),vert(b,True),vert(a,True)))
 side=A.mesh(name+' | pareti rocciose',sv,sf,'rock')
 for f in side.data.polygons:f.use_smooth=True
 return o

def terrain_west():
 poly=[(.045,.66),(.095,.85),(.25,.96),(.399,.948),(.41,.80),(.41,.64),(.465,.56),(.468,.45),(.49,.30),(.505,.10),(.455,.015),(.38,.018),(.30,.16),(.17,.32),(.10,.48)]
 terrain_surface('Colline occidentali',poly,west_height,4.5)
 verts=[];fs=[]
 for i in range(190):
  u=random.uniform(.08,.43);v=random.uniform(.08,.91)
  if not inside(u,v,poly):continue
  if (.285<u<.415 and .625<v<.79) or abs(v-.713)<.055 or (.30<u<.51 and v<.27):continue
  if math.hypot((u-.182)*600,(v-.354)*382)<18:continue
  x,y=A.xy(u,v);z=west_height(u,v);H=random.uniform(5,10);r=H*.24;n=7
  k=len(verts);verts += [(x+r*math.cos(j*2*math.pi/n),y+r*math.sin(j*2*math.pi/n),z+H*.18) for j in range(n)]+[(x,y,z+H)]
  fs +=[(k+j,k+(j+1)%n,k+n) for j in range(n)]
 A.mesh('Bosco sulle colline',verts,fs,'grass')


def staircase(name,uvs):
 for i,(u,v,z) in enumerate(uvs[:-1]):
  U,V,Z=uvs[i+1];a=A.xy(u,v);b=A.xy(U,V);dx=b[0]-a[0];dy=b[1]-a[1];L=math.hypot(dx,dy);ang=math.atan2(dy,dx);cnt=max(3,int(abs(Z-z)/.65))
  # Sostegno inclinato continuo, più pedate, con parapetti a gradoni.
  w=3.4;nx=-math.sin(ang)*w/2;ny=math.cos(ang)*w/2
  verts=[(a[0]+nx,a[1]+ny,z-1),(a[0]-nx,a[1]-ny,z-1),(b[0]-nx,b[1]-ny,Z-1),(b[0]+nx,b[1]+ny,Z-1),(a[0]+nx,a[1]+ny,z-3),(a[0]-nx,a[1]-ny,z-3),(b[0]-nx,b[1]-ny,Z-3),(b[0]+nx,b[1]+ny,Z-3)]
  A.mesh(name+' | rampa',verts,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],'stone')
  for j in range(cnt):
   t=(j+.5)/cnt;zz=z+(Z-z)*t
   A.box(name+' | gradino',(a[0]+dx*t,a[1]+dy*t,zz-.35),(L/cnt+.08,3.7,.7),'trim',ang)
   for s in [-1,1]:A.box(name+' | parapetto',(a[0]+dx*t+s*nx*1.05,a[1]+dy*t+s*ny*1.05,zz+.7),(L/cnt+.08,.35,1.5),'stone',ang)
  A.box(name+' | pianerottolo',(*b,Z-.3),(4.2,4.2,.6),'path')

def boathouse():
 A.collection('16 • Rimessa delle barche e scalinata')
 x,y=A.xy(.793,.906);z=4
 A.box('Rimessa | molo di pietra',(x,y,2),(26,22,4),'stone')
 # Due ampie aperture sul lato lago (sud), senza parete dietro.
 for xx in [x-9.5,x,x+9.5]:A.box('Rimessa | piedritto',(xx,y-5.5,z+4.5),(1.3,1.6,9),'stone')
 for xx in [x-4.75,x+4.75]:A.arch('Rimessa | apertura barche',(xx,y-5.5,z),8.2,9,1.6,0,1.3)
 A.box('Rimessa | muro posteriore',(x,y+5.5,z+5.1),(20,1.5,10.2),'stone')
 for xx in [x-9.5,x+9.5]:A.box('Rimessa | muro laterale',(xx,y,z+5.1),(1.3,11,10.2),'stone')
 A.gable('Rimessa | tetto',(x,y,z+10.2),21.7,13,10,'roof')
 A.turret('Rimessa | torretta ottagonale',(x+5.5,y+5.6,z),3.1,14,10,True)
 for xx in [x-6,x+5]:
  # Piccola barca a remi, scafo aperto con falchetta e sedute.
  vv=[(xx-1.4,y-14,2.2),(xx+1.4,y-14,2.2),(xx+1.6,y-10,2.2),(xx,y-7.4,2.2),(xx-1.6,y-10,2.2),(xx,y-11,.8)]
  A.mesh('Barca | scafo',vv,[(0,1,5),(1,2,5),(2,3,5),(3,4,5),(4,0,5)],'wood')
  for j in range(5):A.beam('Barca | falchetta',vv[j],vv[(j+1)%5],.12,'wood')
  for yy in [y-12.4,y-10.6]:A.box('Barca | sedile',(xx,yy,2.2),(2.6,.5,.25),'wood')
 route=[(.639,.879,60),(.617,.909,56),(.664,.929,48),(.687,.900,41),(.671,.835,32),(.699,.816,26),(.733,.845,18),(.758,.881,10),(.785,.891,4)]
 staircase('Discesa al lago',route)
 # Penisola rocciosa continua sotto le rampe, collegata alla scogliera.
 coast=[(.612,.873),(.636,.821),(.691,.793),(.735,.815),(.778,.859),(.811,.887),(.823,.928),(.782,.949),(.744,.914),(.707,.932),(.672,.950),(.631,.952),(.607,.920)]
 def coast_height(u,v):
  x,y=A.xy(u,v);best=1e9;hh=0
  for aa,bb in zip(route,route[1:]):
   ax,ay=A.xy(aa[0],aa[1]);bx,by=A.xy(bb[0],bb[1]);dx=bx-ax;dy=by-ay
   t=max(0,min(1,((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy)))
   dist=math.hypot(x-ax-dx*t,y-ay-dy*t)
   if dist<best:best=dist;hh=aa[2]+(bb[2]-aa[2])*t
  return max(.6,hh-2.1-best*.45)
 terrain_surface('Scogliera della rimessa',coast,coast_height,2.5,'rock')



def build():
 A.collection('17 • Scogliere, gole e lago')
 south=[(.421,.604),(.495,.601),(.552,.623),(.563,.738),(.608,.766),(.647,.816),(.657,.872),(.602,.928),(.565,.979),(.487,.993),(.461,.954),(.478,.848),(.421,.826),(.413,.771),(.414,.651)]
 north=[(.483,.535),(.491,.296),(.518,.174),(.534,.140),(.555,.115),(.572,.144),(.612,.159),(.720,.179),(.723,.437),(.787,.491),(.748,.628),(.673,.652),(.575,.637),(.557,.548)]
 cliff('Promontorio della Sala Grande',south,60)
 cliff('Promontorio delle serre',north,55)
 terrain_west()
 # Acqua sul lato est/sud; le gole restano leggibili fino in profondità.
 lake=[(.40,.60),(.50,.50),(.63,.42),(.81,.43),(.88,.60),(.89,.94),(.82,1.02),(.48,1.03),(.43,.91)]
 A.prism('Lago Nero | acqua',[A.xy(*p) for p in lake],-.8,1.5,'water')
 # Sostegno del piccolo blocco d'arrivo del ponte sospeso.
 A.collection('18 • Raccordi e passaggi secondari')
 A.building('Ala del ponte sospeso',A.loc(.521,.523,55),31,9,25,11,0,2,6)
 A.box('Ingresso viadotto | fondazione',A.loc(.6265,.571,57.5),(62,25,5),'stone')
 boathouse()
