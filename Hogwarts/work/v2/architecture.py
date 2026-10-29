"""Strumenti geometrici per ricostruzione esterna di Hogwarts (quote indicative)."""
import bpy, math, random
from mathutils import Vector
M={}; CURRENT=None

def material(name,c,rough=.8,metal=0):
 m=bpy.data.materials.new(name); m.diffuse_color=(*c,1); m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*c,1); p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metal
 return m

def init_materials():
 colors={'stone':(.40,.32,.225),'trim':(.57,.47,.33),'roof':(.065,.105,.105),'roofline':(.10,.145,.14),'window':(.009,.025,.025),'glass':(.16,.27,.25),'wood':(.095,.061,.034),'path':(.30,.285,.235),'grass':(.105,.145,.063),'rock':(.19,.20,.18),'water':(.035,.095,.11),'gold':(.32,.22,.075),'base':(.055,.069,.061)}
 for k,c in colors.items(): M[k]=material(k,c,.4 if k in ('roof','glass','water') else .85,.28 if k=='gold' else 0)
 # Materiale procedurale in coordinate globali, senza immagini esterne.
 for key,scale,strength in [('stone',5.2,.18),('trim',8,.10),('rock',.8,.38),('roof',10,.13)]:
  m=M[key]; n=m.node_tree.nodes; links=m.node_tree.links; p=n.get('Principled BSDF')
  noise=n.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=scale; noise.inputs['Detail'].default_value=2
  coord=n.new('ShaderNodeTexCoord'); links.new(coord.outputs['Object'],noise.inputs['Vector'])
  bump=n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=strength; bump.inputs['Distance'].default_value=.13
  links.new(noise.outputs['Fac'],bump.inputs['Height']); links.new(bump.outputs['Normal'],p.inputs['Normal'])
 return M

def collection(name):
 global CURRENT
 CURRENT=bpy.data.collections.new(name); bpy.context.scene.collection.children.link(CURRENT); return CURRENT

def xy(u,v): return ((u-.5)*600,(.55-v)*382)
def loc(u,v,z): return (*xy(u,v),z)

def mesh(name,verts,faces,mat='stone'):
 me=bpy.data.meshes.new(name); me.from_pydata(verts,[],faces); me.update(); o=bpy.data.objects.new(name,me); CURRENT.objects.link(o)
 if mat: me.materials.append(M[mat] if isinstance(mat,str) else mat)
 return o

def box(name,p,size,mat='stone',angle=0,bevel=0):
 x,y,z=p; a,b,c=[s/2 for s in size]; co=math.cos(angle); si=math.sin(angle)
 vs=[(x+dx*co-dy*si,y+dx*si+dy*co,z+dz) for dx,dy,dz in [(-a,-b,-c),(a,-b,-c),(a,b,-c),(-a,b,-c),(-a,-b,c),(a,-b,c),(a,b,c),(-a,b,c)]]
 o=mesh(name,vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)
 if bevel:
  mod=o.modifiers.new('Bordi di pietra','BEVEL'); mod.width=bevel; mod.segments=1
 return o

def prism(name,poly,z,h,mat='stone'):
 n=len(poly); return mesh(name,[(x,y,zz) for zz in (z,z+h) for x,y in poly],[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],mat)

def cone(name,p,r1,r2,h,mat='roof',n=48,phase=0):
 x,y,z=p; vs=[(x+r*math.cos(phase+i*2*math.pi/n),y+r*math.sin(phase+i*2*math.pi/n),zz) for zz,r in [(z,r1),(z+h,max(r2,.015))] for i in range(n)]
 o=mesh(name,vs,[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],mat)
 if n>16:
  for f in o.data.polygons[2:]: f.use_smooth=True
 return o

def beam(name,a,b,r,mat='trim',n=8):
 d=Vector(b)-Vector(a); o=cone(name,(0,0,0),r,r,d.length,mat,n); o.location=a; o.rotation_euler=d.to_track_quat('Z','Y').to_euler(); return o

def gable(name,p,length,width,height,mat='roof',angle=0):
 x,y,z=p; co=math.cos(angle); si=math.sin(angle)
 vs=[(-length/2,-width/2,0),(length/2,-width/2,0),(length/2,width/2,0),(-length/2,width/2,0),(-length/2,0,height),(length/2,0,height)]
 vs=[(x+u*co-v*si,y+u*si+v*co,z+w) for u,v,w in vs]
 return mesh(name,vs,[(0,3,2,1),(0,1,5,4),(3,4,5,2),(0,4,3),(1,2,5)],mat)

def arch_points(w,h):
 sp=h-.866*w; pts=[(-w/2,0),(w/2,0),(w/2,sp)]
 for i in range(1,9):
  a=math.pi/3*i/8; pts.append((-w/2+w*math.cos(a),sp+w*math.sin(a)))
 for i in range(1,9):
  a=2*math.pi/3+math.pi/3*i/8; pts.append((w/2+w*math.cos(a),sp+w*math.sin(a)))
 return pts

def panel(name,p,w,h,angle=0,mat='window',depth=.12):
 x,y,z=p; pts=arch_points(w,h); n=len(pts); co=math.cos(angle); si=math.sin(angle)
 vs=[(x+u*co-d*si,y+u*si+d*co,z+v) for d in [-depth/2,depth/2] for u,v in pts]
 return mesh(name,vs,[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],mat)

def window(name,p,w,h,angle=0,mull=False):
 x,y,z=p
 panel(name+' | cornice',(x,y,z-.17),w+.42,h+.4,angle,'trim',.16)
 dx=.13*math.sin(angle); dy=-.13*math.cos(angle)
 panel(name+' | vetro',(x+dx,y+dy,z),w,h,angle,'window',.08)
 if mull:
  beam(name+' | montante',(x+1.5*dx,y+1.5*dy,z),(x+1.5*dx,y+1.5*dy,z+h*.79),.065,'trim')
  for f in [.30,.60]: beam(name+' | traversa',(x+1.5*dx-w/2*math.cos(angle),y+1.5*dy-w/2*math.sin(angle),z+h*f),(x+1.5*dx+w/2*math.cos(angle),y+1.5*dy+w/2*math.sin(angle),z+h*f),.055,'trim')

def round_windows(name,p,r,levels,count=16,w=1.15,h=2.5,step=9):
 x,y,z=p
 for lev in range(levels):
  for j in range(count):
   a=j*2*math.pi/count
   window(name,(x+(r+.04)*math.cos(a),y+(r+.04)*math.sin(a),z+lev*step),w,h,a+math.pi/2)

def spire(name,p,r,h,n=48,dormers=0):
 x,y,z=p; cone(name+' | gronda',(x,y,z),r+.55,r+.35,.8,'trim',n)
 cone(name+' | ardesia',(x,y,z+.7),r+.3,.08,h-.7,'roof',n)
 beam(name+' | puntale',(x,y,z+h),(x,y,z+h+3.4),.12,'gold')
 if dormers:
  for lev in range(2):
   frac=.24+lev*.26
   for i in range(dormers):
    a=i*2*math.pi/dormers+(lev%2)*math.pi/dormers; rr=(r+.3)*(1-frac)
    xx=x+rr*math.cos(a); yy=y+rr*math.sin(a); zz=z+h*frac
    panel(name+' | abbaino',(xx,yy,zz),.9,1.8,a+math.pi/2,'window',.20)
    gable(name+' | cuffia abbaino',(xx,yy,zz+1.8),1.8,1.6,1.4,'roofline',a)

def turret(name,p,r,h,roofh,windows=True):
 x,y,z=p; cone(name+' | fusto',p,r,r,h,'stone',32)
 for zz in [z+1,z+h-1.4]: cone(name+' | fascia',(x,y,zz),r+.35,r+.35,.65,'trim',32)
 if windows: round_windows(name+' | feritoie',(x,y,z+h*.45),r,1,8,1,2.6)
 spire(name+' | tetto',(x,y,z+h),r+.7,roofh,32)

def building(name,p,length,width,height,roofh,angle=0,levels=3,bays=None):
 x,y,z=p; box(name+' | muri',(x,y,z+height/2),(length,width,height),'stone',angle)
 gable(name+' | timpani',(x,y,z+height),length,width,roofh,'stone',angle)
 gable(name+' | tetto',(x,y,z+height+.15),length+1,width+1,roofh,'roof',angle)
 co=math.cos(angle); si=math.sin(angle); bays=bays or max(3,int(length/5.5))
 for side in [-1,1]:
  for i in range(bays):
   u=-length/2+3+(length-6)*i/max(1,bays-1); v=side*(width/2+.08)
   xx=x+u*co-v*si; yy=y+u*si+v*co
   for lv in range(levels): window(name+' | finestra',(xx,yy,z+4+lv*(height-7)/max(1,levels)),1.5,3,angle if side==-1 else angle+math.pi)
  box(name+' | cornice',(x-side*(width/2+.25)*si,y+side*(width/2+.25)*co,z+height-.4),(length+1,.7,.8),'trim',angle)
 # piccoli abbaini su entrambe le falde
 for i in range(1,bays,2):
  u=-length/2+length*i/bays
  for side in [-1,1]:
   v=side*width*.30; xx=x+u*co-v*si; yy=y+u*si+v*co; zz=z+height+roofh*.40
   window(name+' | abbaino',(xx,yy,zz),1.3,2.3,angle if side==-1 else angle+math.pi)
   gable(name+' | tetto abbaino',(xx,yy,zz+2.3),2.5,2.2,2,'roof',angle+math.pi/2)

def wall(name,a,b,z,height,thickness=1,mat='stone',merlons=False):
 dx=b[0]-a[0];dy=b[1]-a[1];L=math.hypot(dx,dy); angle=math.atan2(dy,dx)
 box(name,((a[0]+b[0])/2,(a[1]+b[1])/2,z+height/2),(L,thickness,height),mat,angle)
 if merlons:
  for i in range(int(L/2.5)+1):
   t=i/max(1,int(L/2.5)); box(name+' | merlo',(a[0]+dx*t,a[1]+dy*t,z+height+.55),(1.3,thickness+0.2,1.1),'trim',angle)

def arch(name,p,w,height,depth,angle=0,cap=1,mat='stone'):
 # Arco semicircolare sopra una luce realmente aperta.
 x,y,z=p; n=16; co=math.cos(angle); si=math.sin(angle); spring=height-w/2; vs=[]
 for d in [-depth/2,depth/2]:
  for i in range(n+1):
   a=math.pi-i*math.pi/n; u=w/2*math.cos(a); v=spring+w/2*math.sin(a)
   for zz in [v,height+cap]: vs.append((x+u*co-d*si,y+u*si+d*co,z+zz))
 stride=2*(n+1);fs=[]
 for i in range(n):
  a=2*i;b=a+2;fs.extend([(a,b,b+1,a+1),(a+stride,a+1+stride,b+1+stride,b+stride),(a,a+stride,b+stride,b),(a+1,b+1,b+1+stride,a+1+stride)])
 fs.extend([(0,1,1+stride,stride),(2*n,2*n+stride,2*n+1+stride,2*n+1)])
 return mesh(name,vs,fs,mat)

def arcade(name,a,b,z,height=8,bay=5,width=3,roofh=3):
 dx=b[0]-a[0];dy=b[1]-a[1];L=math.hypot(dx,dy);angle=math.atan2(dy,dx);count=max(1,round(L/bay));bay=L/count
 for i in range(count+1):
  t=i/count;box(name+' | pilastro',(a[0]+dx*t,a[1]+dy*t,z+height/2),(.8,width,height),'stone',angle)
 for i in range(count):
  t=(i+.5)/count;arch(name+' | arcata',(a[0]+dx*t,a[1]+dy*t,z),bay-.8,height,width,angle,.8)
 if roofh: gable(name+' | tetto',((a[0]+b[0])/2,(a[1]+b[1])/2,z+height+.8),L+1,width+1,roofh,'roof',angle)

def bridge(name,a,b,z,bottom,width=5,bays=8):
 dx=b[0]-a[0];dy=b[1]-a[1];L=math.hypot(dx,dy);ang=math.atan2(dy,dx);bay=L/bays;h=z-bottom
 for i in range(bays+1):
  t=i/bays;box(name+' | pila',(a[0]+dx*t,a[1]+dy*t,bottom+h/2),(1.4,width,h),'stone',ang)
 for i in range(bays):
  t=(i+.5)/bays;arch(name+' | volta',(a[0]+dx*t,a[1]+dy*t,bottom),bay-1.4,h-1.2,width,ang,1.2)
 c=((a[0]+b[0])/2,(a[1]+b[1])/2)
 box(name+' | pavimento',(*c,z+.5),(L+1,width+1,1),'path',ang)
 for side in [-1,1]:
  off=(width/2+.35)*side
  aa=(a[0]-off*math.sin(ang),a[1]+off*math.cos(ang));bb=(b[0]-off*math.sin(ang),b[1]+off*math.cos(ang))
  wall(name+' | parapetto',aa,bb,z+1,1.5,.5,'stone')
