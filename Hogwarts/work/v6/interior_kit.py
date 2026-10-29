"""Oggetti e allestimenti per interni integrati nel modello Hogwarts."""
import bpy,math,random,sys
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca')
sys.path.insert(0,str(ROOT/'work/v2'))
import architecture as A
ROOMS=[]

def material(name,color,rough=.6,metal=0,emission=0):
 m=bpy.data.materials.get(name)
 if m:return m
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if emission:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
 else:
  n=m.node_tree.nodes;l=m.node_tree.links;tc=n.new('ShaderNodeTexCoord');no=n.new('ShaderNodeTexNoise');no.inputs['Scale'].default_value=18;no.inputs['Detail'].default_value=2;l.new(tc.outputs['Object'],no.inputs['Vector'])
  bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.17;bump.inputs['Distance'].default_value=.018;l.new(no.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
 return m

def init():
 for name in ['stone','trim','roof','roofline','window','glass','wood','path','grass','rock','water','gold']:
  if bpy.data.materials.get(name):A.M[name]=bpy.data.materials[name]
 palette={'int_wood':((.105,.047,.018),.5,0,0),'int_oak':((.22,.11,.038),.55,0,0),'int_red':((.23,.012,.015),.85,0,0),'int_gold':((.48,.29,.06),.34,.7,0),'int_brass':((.29,.18,.053),.30,.7,0),'int_paper':((.63,.54,.34),.85,0,0),'int_white':((.72,.69,.60),.9,0,0),'int_green':((.025,.105,.06),.8,0,0),'int_blue':((.025,.065,.16),.85,0,0),'int_iron':((.018,.022,.023),.45,.65,0),'int_flame':((1,.48,.10),.4,0,6),'int_wax':((.72,.55,.30),.65,0,0),'int_chalk':((.018,.037,.026),.95,0,0),'int_sky':((.014,.022,.065),.8,0,.3)}
 for name,(c,r,m,e) in palette.items():A.M[name]=material(name,c,r,m,e)
 for i,c in enumerate([(.18,.025,.014),(.025,.07,.045),(.025,.045,.12),(.23,.13,.035),(.07,.035,.08),(.12,.105,.07)]):A.M['book'+str(i)]=material('Libro | colore '+str(i),c,.8)
 return A.M

class Room:
 def __init__(self,name,origin,angle=0):
  self.name=name;self.origin=tuple(origin);self.angle=angle
  self.collection=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(self.collection)
  self.parts={};self.part('Arredi');self.cameras=[]
 def part(self,name):
  if name not in self.parts:
   c=bpy.data.collections.new(self.name+' • '+name);self.collection.children.link(c);self.parts[name]=c
  A.CURRENT=self.parts[name];return A.CURRENT
 def finish(self):
  bpy.context.view_layer.update()
  M=Matrix.Translation(Vector(self.origin))@Matrix.Rotation(self.angle,4,'Z')
  for ob in self.collection.all_objects:
   ob.matrix_world=M@ob.matrix_world;ob['Ambiente']=self.name;ob['Interno']=True
  ROOMS.append({'name':self.name,'origin':self.origin,'angle':self.angle,'collection':self.collection.name,'cameras':self.cameras})
  return ROOMS[-1]

box=A.box;cone=A.cone;beam=A.beam;mesh=A.mesh;arch=A.arch;panel=A.panel;gable=A.gable;window=A.window

class Batch:
 def __init__(self,name,mats):self.name=name;self.mats=mats;self.v=[];self.f=[];self.mi=[]
 def shape(self,v,f,mat=0):
  k=len(self.v);self.v.extend(v);self.f.extend(tuple(k+i for i in ff) for ff in f);self.mi.extend([mat]*len(f))
 def box(self,p,size,mat=0,angle=0):
  x,y,z=p;aa,bb,cc=[q/2 for q in size];co=math.cos(angle);si=math.sin(angle)
  v=[(x+u*co-v*si,y+u*si+v*co,z+w) for u,v,w in [(-aa,-bb,-cc),(aa,-bb,-cc),(aa,bb,-cc),(-aa,bb,-cc),(-aa,-bb,cc),(aa,-bb,cc),(aa,bb,cc),(-aa,bb,cc)]]
  self.shape(v,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)
 def finish(self):
  if not self.f:return None
  o=A.mesh(self.name,self.v,self.f,None)
  for key in self.mats:o.data.materials.append(A.M[key] if isinstance(key,str) else key)
  for p,i in zip(o.data.polygons,self.mi):p.material_index=i
  return o

def point(name,p,power=120,color=(1,.68,.35),radius=.6):
 d=bpy.data.lights.new(name,'POINT');d.energy=power;d.color=color;d.shadow_soft_size=radius;o=bpy.data.objects.new(name,d);A.CURRENT.objects.link(o);o.location=p;return o

def area(name,p,target,power=1200,size=5,color=(1,.78,.52)):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color;o=bpy.data.objects.new(name,d);A.CURRENT.objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o

def camera(room,name,p,target,lens=24):
 d=bpy.data.cameras.new(name);d.lens=lens;d.clip_start=.05;d.clip_end=15000;o=bpy.data.objects.new(name,d);A.CURRENT.objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();room.cameras.append(o.name);return o

def table(name,p,length=2,width=1,height=.85,mat='int_oak'):
 x,y,z=p;box(name+' | piano',(x,y,z+height),(length,width,.10),mat,bevel=.035)
 for dx in [-length/2+.18,length/2-.18]:
  for dy in [-width/2+.12,width/2-.12]:box(name+' | gamba',(x+dx,y+dy,z+height/2),(.13,.13,height),mat)
 beam(name+' | traversa',(x-length/2+.1,y,z+.25),(x+length/2-.1,y,z+.25),.065,mat,8)

def chair(name,p,mat='int_wood',angle=0):
 x,y,z=p;co=math.cos(angle);si=math.sin(angle)
 def q(u,v,w):return(x+u*co-v*si,y+u*si+v*co,z+w)
 box(name+' | seduta',q(0,0,.48),(.52,.52,.08),mat,angle)
 for u in [-.21,.21]:
  for v in [-.21,.21]:box(name+' | piede',q(u,v,.23),(.065,.065,.46),mat,angle)
 for u in [-.21,.21]:box(name+' | montante',q(u,.22,.77),(.065,.065,.64),mat,angle)
 box(name+' | schienale',q(0,.22,1.0),(.49,.065,.28),mat,angle)

def bookcase(name,p,width=3,height=4,depth=.55,angle=0,rows=5,seed=0):
 x,y,z=p;co=math.cos(angle);si=math.sin(angle);rng=random.Random(seed)
 def q(u,v,w):return(x+u*co-v*si,y+u*si+v*co,z+w)
 for u in [-width/2,width/2]:box(name+' | fianco',q(u,0,height/2),(.12,depth,height),'int_wood',angle)
 box(name+' | fondo',q(0,depth/2-.04,height/2),(width, .08,height),'int_wood',angle)
 books=Batch(name+' | libri',['book'+str(i) for i in range(6)]+['int_paper','int_gold'])
 for row in range(rows+1):
  zz=.12+row*(height-.24)/rows;box(name+' | ripiano',q(0,0,zz),(width+.2,depth+.06,.10),'int_wood',angle)
  if row==rows:continue
  u=-width/2+.15
  while u<width/2-.18:
   bw=rng.uniform(.055,.16);bh=rng.uniform(.28,min(.55,(height-.24)/rows-.12));dd=depth*.72
   books.box(q(u+bw/2,-.045,zz+.05+bh/2),(bw,dd,bh),rng.randrange(6),angle)
   books.box(q(u+bw/2,-.045,zz+.05+bh+.007),(bw*.77,dd*.85,.012),6,angle)
   for hh in [.10,bh-.07]:books.box(q(u+bw/2,-dd/2-.05,zz+.05+hh),(bw*.8,.012,.018),7,angle)
   u+=bw+.015
 books.finish()

def candle(name,p,h=.28):
 x,y,z=p;cone(name+' | cera',p,.035,.033,h,'int_wax',12);cone(name+' | fiamma',(x,y,z+h),.035,.002,.10,'int_flame',8)

def bottle(name,p,r=.12,h=.35,mat='glass'):
 x,y,z=p;cone(name+' | corpo',p,r,r*.85,h*.70,mat,16);cone(name+' | spalla',(x,y,z+h*.70),r*.85,r*.28,h*.15,mat,16);cone(name+' | collo',(x,y,z+h*.85),r*.28,r*.28,h*.15,mat,12);cone(name+' | tappo',(x,y,z+h),r*.32,r*.32,.04,'int_wood',12)

def portrait(name,p,width=1.2,height=1.8,angle=0,seed=0):
 x,y,z=p;co=math.cos(angle);si=math.sin(angle)
 def q(u,v,w):return(x+u*co-v*si,y+u*si+v*co,z+w)
 box(name+' | cornice',q(0,0,height/2),(width,.12,height),'int_gold',angle)
 box(name+' | tela',q(0,-.075,height/2),(width-.16,.035,height-.16),'book'+str(seed%6),angle)
 # Ritratto stilizzato in rilievo, non fotografia di una persona reale.
 box(name+' | busto',q(0,-.10,height*.36),(width*.46,.04,height*.34),'int_wood',angle)
 o=cone(name+' | volto',(0,0,0),width*.14,width*.14,.035,'int_paper',24);o.rotation_euler[0]=math.pi/2;o.rotation_euler[2]=angle;o.location=q(0,-.13,height*.67)

def torch(name,p,angle=0):
 x,y,z=p;beam(name+' | braccio',(x,y,z),(x,y-.35,z+.10),.04,'int_iron',8);cone(name+' | sostegno',(x,y-.35,z+.1),.09,.13,.24,'int_brass',12);candle(name,(x,y-.35,z+.34),.35);point(name+' | luce',(x,y-.50,z+.75),70,(1,.54,.22),.25)
