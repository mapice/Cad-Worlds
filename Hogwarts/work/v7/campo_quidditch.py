"""Campo di Quidditch con tribune, sei anelli e sentiero sulla collina."""
import bpy,math,random
import heapq
from mathutils import Vector
import kit_v7 as K
A=K.A
CX,CY=-485.,310.
RX,RY=102.,61.

def _route():
 # Ricerca di un sentiero che privilegi pendenze moderate e segua i colli.
 step=10.;x0,x1=-650,-100;y0,y1=70,390
 nx=int((x1-x0)/step)+1;ny=int((y1-y0)/step)+1
 heights={(i,j):K.ground(x0+i*step,y0+j*step) for i in range(nx) for j in range(ny)}
 start=(nx-3,10);end=(round((CX-x0)/step),round((CY-70-y0)/step))
 scores={start:0};previous={};queue=[(0,start)];directions=[(i,j) for i in [-1,0,1] for j in [-1,0,1] if i or j]
 while queue:
  cost,node=heapq.heappop(queue)
  if cost!=scores.get(node):continue
  if node==end:break
  for di,dj in directions:
   q=(node[0]+di,node[1]+dj)
   if q not in heights:continue
   dist=step*math.hypot(di,dj);slope=abs(heights[q]-heights[node])/dist
   new=cost+dist*(1+100*max(0,slope-.12)**2)
   if new<scores.get(q,float('inf')):scores[q]=new;previous[q]=node;heapq.heappush(queue,(new,q))
 nodes=[end]
 while nodes[-1]!=start:nodes.append(previous[nodes[-1]])
 nodes.reverse();controls=[(-120,175)]+[(x0+i*step,y0+j*step) for i,j in nodes[1:-1]]+[(CX,CY-70)]
 return controls

def _grade():
 # Solo la radura remota dello stadio: nessun vertice della rocca viene toccato.
 samples=[K.ground(CX+x,CY+y) for x,y in [(0,0),(-25,0),(25,0),(0,-20),(0,20)]]
 z=sum(samples)/len(samples);changed=0;max_delta=0
 o=bpy.data.objects['Colli e sponde | superficie continua']
 for v in o.data.vertices:
  p=o.matrix_world@v.co;r=math.hypot((p.x-CX)/RX,(p.y-CY)/RY)
  if r>=1.5:continue
  t=max(0,min(1,(r-1.13)/.37));w=1-t*t*(3-2*t)
  target=p.z*(1-w)+(z-.10)*w;max_delta=max(max_delta,abs(target-p.z))
  p.z=target;v.co=o.matrix_world.inverted()@p;changed+=1
 o.data.update();K.reset_ground()
 cleared=[];regrounded=[]
 for o in list(bpy.data.objects):
  if o.type=='MESH' and o.name.startswith(('Bosco |','Sottobosco esteso |')):
   p=o.matrix_world.translation
   if math.hypot((p.x-CX)/(RX+25),(p.y-CY)/(RY+20))<1:
    o.hide_render=True;o.hide_set(True);cleared.append(o.name)
   elif math.hypot((p.x-CX)/RX,(p.y-CY)/RY)<1.5:
    o.location.z=K.ground(p.x,p.y)-.18;regrounded.append(o.name)
 return z,{'terrain_vertices_graded':changed,'maximum_local_ground_adjustment':max_delta,'vegetation_cleared':len(cleared),'vegetation_regrounded':len(regrounded)}

def _ellipse_band(name,rx,ry,width,z,mat):
 vs=[];n=180
 for i in range(n):
  a=math.tau*i/n
  for off in [-width*.5,width*.5]:vs.append((CX+(rx+off)*math.cos(a),CY+(ry+off)*math.sin(a),z))
 o=A.mesh(name,vs,[(2*i,2*((i+1)%n),2*((i+1)%n)+1,2*i+1) for i in range(n)],mat);K.M.assign_uvs([o]);return o

def _turf(z):
 mats=[]
 for i,c in enumerate([(.075,.17,.035),(.12,.23,.055)]):
  key='v7_turf'+str(i);A.M[key]=K.I.material('Quidditch | prato '+str(i),c,.98);mats.append(key)
 b=K.Batch('Quidditch | prato a fasce',mats)
 for j in range(22):
  x0=-86+j*172/22;x1=-86+(j+1)*172/22
  # Ogni fascia segue il bordo ovale con più campioni.
  xs=[x0+(x1-x0)*k/4 for k in range(5)]
  vs=[(CX+x,CY+side*44*math.sqrt(max(0,1-(x/86)**2)),z+.03) for side in [-1,1] for x in xs]
  b.add(vs,[tuple(range(5))+tuple(range(9,4,-1))],j%2)
 b.finish();_ellipse_band('Quidditch | limite di gioco',84,42,.23,z+.065,'v7_linen')
 _ellipse_band('Quidditch | cammino esterno',105,63,4.0,z+.015,'path')
 A.box('Quidditch | linea centrale',(CX,CY,z+.065),(.18,83,.012),'v7_linen')
 ring=K.Batch('Quidditch | cerchio di metà campo',['v7_linen']);ring.ring((CX,CY,z+.07),6,.085,n=72);ring.finish()

def _goals(z):
 b=K.Batch('Quidditch | sei pali e anelli',['v7_wood','int_brass','stone'])
 for side in [-1,1]:
  for j,(y,h) in enumerate([(-12,11),(0,17),(12,14)]):
   x=CX+side*(72 if j==1 else 69);yy=CY+y
   b.box((x,yy,z+.28),(1.25,1.25,.56),2)
   b.tube((x,yy,z+.3),(x,yy,z+h),.20,.13,n=12,mat=0)
   b.ring((x,yy,z+h),2.25,.16,axis='X',mat=1,n=56,sides=9)
 b.finish()

def _tower(z,i,a):
 x=CX+RX*math.cos(a);y=CY+RY*math.sin(a);ang=a+math.pi/2
 co,si=math.cos(ang),math.sin(ang)
 def q(u,v,w):return (x+u*co-v*si,y+u*si+v*co,z+w)
 h=21+(i%4==0)*5;half=4.6
 colors=['v7_red','v7_yellow','v7_blue','v7_green'];house=colors[(i//4)%4]
 b=K.Batch('Quidditch | torre tribuna %02d'%i,['v7_wood',house,'v7_linen','v7_iron','stone'])
 for u in [-half,half]:
  for v in [-half,half]:
   b.box(q(u,v,.3),(1.2,1.2,.6),4,ang)
   b.tube(q(u,v,.6),q(u,v,h+5),.19,.15,n=8,mat=0)
 for level in [4.5,10,15,h]:
  for v in [-half,half]:
   b.tube(q(-half,v,level),q(half,v,level),.13,n=7)
  for u in [-half,half]:b.tube(q(u,-half,level),q(u,half,level),.13,n=7)
 # Croci strutturali e scala esterna a due rampe per raggiungere la tribuna.
 for u in [-half,half]:
  for z0,z1 in [(1,10),(10,h)]:
   b.tube(q(u,-half,z0),q(u,half,z1),.105,n=7)
   b.tube(q(u,half,z0),q(u,-half,z1),.105,n=7)
 for side in [-1,1]:
  z0=0 if side==-1 else h*.5
  for k in range(32):
   zz=z0+(k+1)*h/64;v=-4.5+k*9/32 if side==-1 else 4.5-k*9/32
   b.box(q(-half-.65,v,zz),(1.25,.30,.14),0,ang)
  b.tube(q(-half-1.3,-4.5,z0+1),q(-half-1.3,4.5,z0+h*.5+1),.045,n=5)
 b.box(q(0,0,h-.12),(9.5,9.5,.24),0,ang)
 # Retro e fianchi con scacchi di stoffa: il fronte rivolto al campo resta aperto.
 for side in ['back','left','right']:
  for row in range(4):
   for col in range(4):
    u=-half+half/4+col*half/2;w=h-8+row*2
    mat=1 if (row+col)%2==0 else 2
    if side=='back':b.box(q(u,-half,w),(half/2,.045,2.0),mat,ang)
    else:b.box(q(-half if side=='left' else half,u,w),(.045,half/2,2.0),mat,ang)
 # Tre gradoni, sedute e parapetto della loggia.
 for row in range(3):
  b.box(q(0,-2.9+row*1.9,h+.15+row*.45),(8.1,1.5,.3+row*.9),0,ang)
  b.box(q(0,-2.9+row*1.9,h+.6+row*.45),(8.1,.36,.12),2,ang)
 for u in [-4,-3,-2,-1,0,1,2,3,4]:b.tube(q(u,half,h),q(u,half,h+1.1),.055,n=6)
 b.tube(q(-half,half,h+1.1),q(half,half,h+1.1),.085,n=7)
 # Tetto a padiglione con falde a fasce alternate e piccolo stendardo mosso.
 corners=[q(-5.15,-5.15,h+5),q(5.15,-5.15,h+5),q(5.15,5.15,h+5),q(-5.15,5.15,h+5)];peak=q(0,0,h+10)
 for k in range(4):
  p0,p1=Vector(corners[k]),Vector(corners[(k+1)%4])
  for j in range(4):b.add([p0.lerp(p1,j/4),p0.lerp(p1,(j+1)/4),peak],[(0,1,2)],1 if j%2 else 2)
 b.tube(q(0,0,h+9.8),q(0,0,h+13.3),.045,n=6)
 b.add([q(0,0,h+13.2),q(2.4,.2,h+12.9),q(2.1,-.08,h+11.7),q(0,0,h+12)],[(0,1,2,3)],1)
 b.finish()

def apply():
 K.init();col=K.collection('83 • Campo di Quidditch');z,report=_grade();_turf(z);_goals(z)
 for i in range(16):_tower(z,i,math.tau*i/16+math.pi/16)
 fence=K.Batch('Quidditch | recinto e accessi',['v7_wood','v7_linen'])
 for i in range(120):
  a=math.tau*i/120;b=math.tau*(i+1)/120
  if abs(a-4.71)<.10:continue
  pa=(CX+96*math.cos(a),CY+55*math.sin(a));pb=(CX+96*math.cos(b),CY+55*math.sin(b))
  fence.tube((*pa,z),(*pa,z+2.4),.09,n=7)
  for h in [.7,1.8]:fence.tube((*pa,z+h),(*pb,z+h),.06,n=6)
 fence.finish()
 controls=_route()
 path=K.path('Quidditch | sentiero dalla Guferia',K.smooth_path(controls,2),2.6,'path')
 path_cleared=0
 for ob in bpy.data.objects:
  if ob.type!='MESH' or ob.hide_render or not ob.name.startswith(('Bosco |','Sottobosco esteso |')):continue
  p=ob.matrix_world.translation
  if any(K.E._distance_segment(p.x,p.y,a,b)<3.8 for a,b in zip(controls,controls[1:])):
   ob.hide_render=True;ob.hide_set(True);path_cleared+=1
 # Cippi e lanterne del sentiero, senza invadere la carreggiata.
 poles=K.Batch('Quidditch | cippi del percorso',['stone','trim','v7_iron'])
 for x,y in K.smooth_path(controls,20)[1:-1]:
  yy=y-2;zz=K.ground(x,yy);poles.box((x,yy,zz+.5),(.45,.45,1),0);poles.box((x,yy,zz+1.05),(.6,.6,.12),1)
 poles.finish()
 K.camera('Esterni V7 | campo di Quidditch',(CX+170,CY-210,z+160),(CX,CY,z+10),43)
 K.camera('Esterni V7 | tribune e anelli',(CX+20,CY-106,z+26),(CX+40,CY,z+13),31)
 report.update({'center':[CX,CY,z],'towers':16,'goal_rings':6,'path_controls':controls,'path_vegetation_cleared':path_cleared,'objects':len(col.objects),'faces':sum(len(o.data.polygons) for o in col.objects if o.type=='MESH')})
 return report
