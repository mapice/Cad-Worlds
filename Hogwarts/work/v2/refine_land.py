from pathlib import Path
p=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca/work/v2/landscape.py')
s=p.read_text().replace('from mathutils.geometry import tessellate_polygon','from mathutils.geometry import tessellate_polygon, delaunay_2d_cdt')
a=s.index('def west_height(');b=s.index('\ndef staircase(',a)
s=s[:a]+'''def smooth(t):
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

''' + s[b:]
a=s.index(' # Costoni di appoggio lungo la scalinata');b=s.index('\n\n\ndef build',a)
s=s[:a]+''' # Penisola rocciosa continua sotto le rampe, collegata alla scogliera.
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
''' + s[b:]
s=s.replace('(.518,.174),(.612,.159)','(.518,.174),(.534,.140),(.555,.115),(.572,.144),(.612,.159)')
p.write_text(s)
p=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca/work/v2/south_sector.py');s=p.read_text().replace('(x,y,z-1.2),(L+3,W+3,2.4)','(x,y,z-1.05),(L+3,W+3,2.4)').replace("t,q,z-3,3,7,'stone'","t,q,z-3,3.3,7,'stone'");p.write_text(s)
p=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca/work/v2/build.py');s=p.read_text().replace('16000000,380','10000000,380').replace('8500000,450','5000000,450').replace('17000000,350','11000000,350').replace("default_value=.35;scene.world","default_value=.25;scene.world").replace('scene.cycles.samples=32','scene.cycles.samples=48').replace('scene.cycles.adaptive_threshold=.04','scene.cycles.adaptive_threshold=.025').replace('resolution_x=1600','resolution_x=2000').replace('resolution_y=1300','resolution_y=1600').replace("print('BACK_RENDERED',flush=True)","print('BACK_RENDERED',flush=True)\nscene.camera=close;scene.render.filepath=str(ROOT/'outputs/Hogwarts-HBP-dettaglio.png');scene.render.resolution_x=1700;scene.render.resolution_y=1400\nbpy.ops.render.render(write_still=True)\nprint('DETAIL_RENDERED',flush=True)");p.write_text(s)
