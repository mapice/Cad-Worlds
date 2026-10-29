"""Strumenti condivisi per aggiunte esterne; nessun caricamento o salvataggio."""
import bpy, math, sys
from pathlib import Path
from mathutils import Vector
R=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca')
for rel in ['work/v2','work/v3','work/v4','work/v6']:
 sys.path.insert(0,str(R/rel))
import architecture as A
import interior_kit as I
import ecology_v4 as E
import materials as M
_ground=None

def init():
 I.init()
 for key,col,rough,metal in [
 ('v7_wood',(.13,.067,.027),.75,0),('v7_iron',(.035,.043,.04),.5,.65),
 ('v7_red',(.34,.025,.018),.9,0),('v7_blue',(.035,.09,.23),.9,0),
 ('v7_green',(.028,.15,.08),.9,0),('v7_yellow',(.5,.32,.055),.9,0),
 ('v7_linen',(.62,.53,.35),.93,0),('v7_dirt',(.12,.09,.045),1,0),
 ('v7_leaf',(.07,.16,.042),.92,0),('v7_pumpkin',(.55,.16,.02),.65,0)]:
  A.M[key]=I.material('Esterni | '+key,col,rough,metal)
 return A.M

def collection(name):
 c=bpy.data.collections.get(name)
 if c:raise RuntimeError('Collezione già presente: '+name)
 c=A.collection(name);c['Esterni V7']=True;return c

def ground(x,y):
 global _ground
 if _ground is None:_ground=E._terrain_sampler()[0]
 hit=_ground(x,y)
 if hit is None:raise RuntimeError('Terreno non trovato: '+str((x,y)))
 return hit[0]

def reset_ground():
 global _ground
 _ground=None

class Batch(E.Shape):
 def __init__(self,name,mats):super().__init__();self.name=name;self.mats=mats
 def box(self,p,size,mat=0,angle=0):
  x,y,z=p;a,b,c=[q*.5 for q in size];co=math.cos(angle);si=math.sin(angle)
  vs=[(x+u*co-v*si,y+u*si+v*co,z+w) for u,v,w in [(-a,-b,-c),(a,-b,-c),(a,b,-c),(-a,b,-c),(-a,-b,c),(a,-b,c),(a,b,c),(-a,b,c)]]
  self.add(vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)
 def ring(self,p,r,tube=.1,axis='Z',mat=0,n=48,sides=7):
  vs=[]
  for i in range(n):
   a=math.tau*i/n
   for j in range(sides):
    b=math.tau*j/sides;q=((r+tube*math.cos(b))*math.cos(a),(r+tube*math.cos(b))*math.sin(a),tube*math.sin(b))
    if axis=='X':q=(q[2],q[0],q[1])
    elif axis=='Y':q=(q[0],q[2],q[1])
    vs.append(tuple(p[k]+q[k] for k in range(3)))
  fs=[(i*sides+j,((i+1)%n)*sides+j,((i+1)%n)*sides+(j+1)%sides,i*sides+(j+1)%sides) for i in range(n) for j in range(sides)]
  self.add(vs,fs,mat)
 def finish(self):
  if not self.f:return None
  me=self.mesh(self.name,[A.M[m] if isinstance(m,str) else m for m in self.mats]);o=bpy.data.objects.new(self.name,me);A.CURRENT.objects.link(o);o['Esterni V7']=True
  M.assign_uvs([o]);return o

def camera(name,p,target,lens=45,ortho=None):
 d=bpy.data.cameras.new(name);d.lens=lens;d.clip_start=.1;d.clip_end=15000
 if ortho:d.type='ORTHO';d.ortho_scale=ortho
 o=bpy.data.objects.new(name,d);A.CURRENT.objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o

def path(name,points,width=2,mat='path',lift=.055):
 vs=[]
 for i,(x,y) in enumerate(points):
  a=Vector(points[max(0,i-1)]);b=Vector(points[min(len(points)-1,i+1)]);t=(b-a).normalized();n=Vector((-t.y,t.x))
  for side in (-1,1):
   xx=x+side*n.x*width*.5;yy=y+side*n.y*width*.5;vs.append((xx,yy,ground(xx,yy)+lift))
 fs=[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(points)-1)]
 o=A.mesh(name,vs,fs,mat);o['Esterni V7']=True;M.assign_uvs([o]);return o

def smooth_path(controls,step=2):
 # Catmull–Rom con estremità bloccate, per sentieri aderenti al suolo.
 out=[];p=[Vector(controls[0])]+[Vector(q) for q in controls]+[Vector(controls[-1])]
 for i in range(1,len(p)-2):
  a,b,c,d=p[i-1:i+3];n=max(2,round((c-b).length/step))
  for j in range(n):
   t=j/n;q=.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t);out.append(tuple(q))
 out.append(tuple(controls[-1]));return out
