"""Scala esterna rifinita verso la rimessa: gradini, pianerottoli e parapetti.
apply() opera su una scena già caricata e non salva né renderizza.
Le quote sono quelle del modello; non costituiscono un progetto esecutivo.
"""
import math
import bpy,bmesh
from mathutils import Vector

ROUTE_XYZ=[
 (83.4,-125.678,60.24),
 (87.01,-131.24,60.24),
 (74.0,-143.0,55.0),
 (98.4,-144.778,48.0),
 (112.2,-133.7,41.0),
 (102.6,-108.87,32.0),
 (119.4,-101.612,26.0),
 (139.8,-112.69,18.0),
 (154.8,-126.442,10.0),
 (171.0,-127.3,4.12),
]
CLEAR_WIDTH=2.7
WALL_THICKNESS=.28
OUTER_WIDTH=3.36
WALL_HEIGHT=1.05
SUPPORT_DEPTH=.85
COLLECTION='45 • Scalinata in pietra rifinita'


def _unit(a,b):
 d=Vector((b[0]-a[0],b[1]-a[1],0));return d.normalized(),d.length

_DIRECTIONS=[];_LENGTHS=[]
for _a,_b in zip(ROUTE_XYZ,ROUTE_XYZ[1:]):
 _d,_length=_unit(_a,_b);_DIRECTIONS.append(_d);_LENGTHS.append(_length)
_NORMALS=[Vector((-d.y,d.x,0)) for d in _DIRECTIONS]
_MITERS=[];_SETBACK=[]
for i,p in enumerate(ROUTE_XYZ):
 if i==0:_MITERS.append(_NORMALS[0]);_SETBACK.append(1.2)
 elif i==len(ROUTE_XYZ)-1:_MITERS.append(_NORMALS[-1]);_SETBACK.append(1.2)
 else:
  n=(_NORMALS[i-1]+_NORMALS[i]).normalized();den=max(.15,n.dot(_NORMALS[i]));_MITERS.append(n/den)
  angle=math.acos(max(-1,min(1,_DIRECTIONS[i-1].dot(_DIRECTIONS[i]))))
  _SETBACK.append(max(1.2,OUTER_WIDTH*.5*math.tan(angle/2)+.4))


def _profile(i):
 """Intervalli di pianerottolo e rampa, con tutte le quantità in metri."""
 a,b=ROUTE_XYZ[i:i+2];L=_LENGTHS[i];drop=a[2]-b[2]
 if abs(drop)<1e-8:return {'index':i,'length':L,'steps':0,'riser':0,'tread':0,'flights':0,'pieces':[{'kind':'landing','s0':0.,'s1':L,'z0':a[2],'z1':b[2],'steps':0}]}
 count=math.ceil(drop/.185);flights=math.ceil(count/16);inner=1.35
 start,end=_SETBACK[i],_SETBACK[i+1]
 available=(L-start-end-(flights-1)*inner)/count
 if available<.32:
  flights=math.ceil(count/18);available=(L-start-end-(flights-1)*inner)/count
 if available<.30:raise ValueError('Tratto troppo corto per scala proporzionata: '+str(i))
 tread=min(.42,available);extra=L-count*tread-(flights-1)*inner-start-end
 start+=extra/2;end+=extra/2;riser=drop/count
 sizes=[count//flights+(j<count%flights) for j in range(flights)]
 pieces=[];s=0.;z=a[2]
 pieces.append({'kind':'landing','s0':s,'s1':start,'z0':z,'z1':z,'steps':0});s=start
 for j,n in enumerate(sizes):
  dz=n*riser
  pieces.append({'kind':'flight','s0':s,'s1':s+n*tread,'z0':z,'z1':z-dz,'steps':n});s+=n*tread;z-=dz
  flat=inner if j<flights-1 else end
  pieces.append({'kind':'landing','s0':s,'s1':s+flat,'z0':z,'z1':z,'steps':0});s+=flat
 pieces[-1]['s1']=L;pieces[-1]['z0']=b[2];pieces[-1]['z1']=b[2]
 return {'index':i,'length':L,'steps':count,'riser':riser,'tread':tread,'flights':flights,'pieces':pieces}

PROFILES=[_profile(i) for i in range(len(_LENGTHS))]


def _surface(i,s):
 profile=PROFILES[i];s=max(0,min(profile['length'],s))
 for piece in profile['pieces']:
  if s<=piece['s1']+1e-8:
   if piece['kind']=='landing':return piece['z0'],piece['z0']-SUPPORT_DEPTH
   t=max(0,min(1,(s-piece['s0'])/(piece['s1']-piece['s0'])))
   # Ogni pedata è al livello successivo; il riser all'inizio collega la precedente.
   step=min(piece['steps'],int((s-piece['s0'])/profile['tread']+1e-7)+1)
   height=piece['z0']-step*profile['riser']
   lower=piece['z0']+(piece['z1']-piece['z0'])*t-SUPPORT_DEPTH
   return height,lower
 return ROUTE_XYZ[i+1][2],ROUTE_XYZ[i+1][2]-SUPPORT_DEPTH


def sample_path(x,y):
 """Ritorna distanza XY, quota del calpestio, sostegno e punto vicino.

 Dizionario con distance, height, support_z, point=(x,y,z), segment, s,
 clear_width e outer_width. Non modifica Blender; utilizzabile prima di apply().
 """
 best=None
 for i,(a,b) in enumerate(zip(ROUTE_XYZ,ROUTE_XYZ[1:])):
  d=_DIRECTIONS[i];s=max(0,min(_LENGTHS[i],(x-a[0])*d.x+(y-a[1])*d.y));xx=a[0]+d.x*s;yy=a[1]+d.y*s;dist=math.hypot(x-xx,y-yy)
  if best is None or dist<best['distance']-1e-8:
   z,support=_surface(i,s)
   best={'distance':dist,'height':z,'support_z':support,'point':(xx,yy,z),'segment':i,'s':s,'clear_width':CLEAR_WIDTH,'outer_width':OUTER_WIDTH}
 return best


class Batch:
 def __init__(self,name,materials):self.name=name;self.materials=materials;self.vertices=[];self.faces=[];self.indices=[]
 def face(self,points,mat=0):
  clean=[]
  for p in points:
   v=Vector(p)
   if not clean or (v-clean[-1]).length>1e-8:clean.append(v)
  if len(clean)>2 and (clean[0]-clean[-1]).length<1e-8:clean.pop()
  if len(clean)<3:return
  area=Vector((0,0,0))
  for i in range(1,len(clean)-1):area+=(clean[i]-clean[0]).cross(clean[i+1]-clean[0])
  if area.length<1e-9:return
  k=len(self.vertices);self.vertices.extend(tuple(v) for v in clean);self.faces.append(tuple(range(k,k+len(clean))));self.indices.append(mat)
 def make(self,col):
  me=bpy.data.meshes.new(self.name);me.from_pydata(self.vertices,[],self.faces);me.update();ob=bpy.data.objects.new(self.name,me);col.objects.link(ob)
  for name in self.materials:me.materials.append(bpy.data.materials[name])
  for p,mi in zip(me.polygons,self.indices):p.material_index=mi
  bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-4);bm.to_mesh(me);bm.free();me.update()
  return ob


def _offset(i,s,dist,z):
 a=ROUTE_XYZ[i];d=_DIRECTIONS[i]
 if abs(s)<1e-7:n=_MITERS[i]
 elif abs(s-_LENGTHS[i])<1e-7:n=_MITERS[i+1]
 else:n=_NORMALS[i]
 return Vector((a[0]+d.x*s+n.x*dist,a[1]+d.y*s+n.y*dist,z))


def _smooth_z(piece,s):
 t=(s-piece['s0'])/max(1e-8,piece['s1']-piece['s0']);return piece['z0']+(piece['z1']-piece['z0'])*t


def _solid_between(batch,i,s0,s1,z0,z1,off0,off1,low0,low1,mat=0,cap_start=True,cap_end=True):
 # Sezione rettangolare estrusa, capi miterati quando coincidono con nodi della pianta.
 a=_offset(i,s0,off0,low0);b=_offset(i,s0,off1,low0);c=_offset(i,s1,off1,low1);d=_offset(i,s1,off0,low1)
 A=_offset(i,s0,off0,z0);B=_offset(i,s0,off1,z0);C=_offset(i,s1,off1,z1);D=_offset(i,s1,off0,z1)
 for f in [(a,b,c,d),(A,D,C,B),(b,B,C,c),(d,D,A,a)]:batch.face(f,mat)
 if cap_start:batch.face((a,A,B,b),mat)
 if cap_end:batch.face((c,C,D,d),mat)


def _deck(i,batch):
 p=PROFILES[i];stations=[]
 def add(s,z,b):
  if stations and all(abs(a-bb)<1e-8 for a,bb in zip(stations[-1],(s,z,b))):return
  stations.append((s,z,b))
 for pc in p['pieces']:
  if pc['kind']=='landing':
   add(pc['s0'],pc['z0'],pc['z0']-SUPPORT_DEPTH);add(pc['s1'],pc['z1'],pc['z1']-SUPPORT_DEPTH)
  else:
   n=pc['steps'];r=p['riser'];t=p['tread']
   add(pc['s0'],pc['z0'],pc['z0']-SUPPORT_DEPTH)
   for j in range(n):
    s0=pc['s0']+j*t;s1=pc['s0']+(j+1)*t;z=pc['z0']-(j+1)*r
    add(s0,z,_smooth_z(pc,s0)-SUPPORT_DEPTH);add(s1,z,_smooth_z(pc,s1)-SUPPORT_DEPTH)
 half=OUTER_WIDTH/2
 for si,(a,b) in enumerate(zip(stations,stations[1:])):
  s0,z0,base0=a;s1,z1,base1=b
  l0=_offset(i,s0,-half,z0);r0=_offset(i,s0,half,z0);l1=_offset(i,s1,-half,z1);r1=_offset(i,s1,half,z1)
  bl0=_offset(i,s0,-half,base0);br0=_offset(i,s0,half,base0);bl1=_offset(i,s1,-half,base1);br1=_offset(i,s1,half,base1)
  batch.face((l0,l1,r1,r0),1 if abs(z1-z0)<1e-8 else 0)
  batch.face((bl0,br0,br1,bl1),0)
  extra_l=[];extra_r=[]
  if si+2<len(stations):
   sn,zn,_=stations[si+2]
   if abs(sn-s1)<1e-8 and zn<z1-1e-8:
    extra_l=[_offset(i,s1,-half,zn)];extra_r=[_offset(i,s1,half,zn)]
  batch.face([bl0,bl1]+extra_l+[l1,l0],0);batch.face([r0,r1]+extra_r+[br1,br0],0)
 if i==0:
  s,z,base=stations[0];batch.face((_offset(i,s,-half,base),_offset(i,s,-half,z),_offset(i,s,half,z),_offset(i,s,half,base)),0)
 if i==len(PROFILES)-1:
  s,z,base=stations[-1];batch.face((_offset(i,s,-half,base),_offset(i,s,half,base),_offset(i,s,half,z),_offset(i,s,-half,z)),0)


def _parapets(i,walls,caps):
 for piece in PROFILES[i]['pieces']:
  s0,s1=piece['s0'],piece['s1'];z0,z1=piece['z0'],piece['z1']
  for sign in [-1,1]:
   inner=sign*CLEAR_WIDTH/2;outer=sign*(CLEAR_WIDTH/2+WALL_THICKNESS)
   lo,hi=sorted((inner,outer))
   _solid_between(walls,i,s0,s1,z0+WALL_HEIGHT,z1+WALL_HEIGHT,lo,hi,z0-.28,z1-.28,cap_start=(i==0 and s0==0),cap_end=(i==len(PROFILES)-1 and abs(s1-_LENGTHS[i])<1e-7))
   # Copertina continua attraverso rampe, pianerottoli e svolte.
   # I profili ai nodi sono miterati e saldati, senza tasselli in sovrapposizione.
   _solid_between(caps,i,s0,s1,z0+WALL_HEIGHT+.12,z1+WALL_HEIGHT+.12,lo-.045,hi+.045,z0+WALL_HEIGHT-.01,z1+WALL_HEIGHT-.01,cap_start=(i==0 and s0==0),cap_end=(i==len(PROFILES)-1 and abs(s1-_LENGTHS[i])<1e-7))


def apply():
 if bpy.data.collections.get(COLLECTION):raise RuntimeError('Scala v5 già presente; applicare alla scena di partenza una sola volta')
 hidden=[]
 for o in bpy.data.objects:
  if o.name.startswith('Discesa al lago'):
   o.hide_render=True;o.hide_set(True);hidden.append(o.name)
 col=bpy.data.collections.new(COLLECTION);bpy.context.scene.collection.children.link(col)
 deck=Batch('Scalinata V5 | gradini e sostegno continuo',['stone','path']);walls=Batch('Scalinata V5 | parapetti continui',['stone']);caps=Batch('Scalinata V5 | copertine di pietra',['trim'])
 for i in range(len(PROFILES)):_deck(i,deck);_parapets(i,walls,caps)
 objects=[b.make(col) for b in [deck,walls,caps]]
 # Addolcimento minimo per evitare bordi taglienti da blocchi ideali.
 for o in objects:
  bevel=o.modifiers.new('Spigoli smussati della pietra','BEVEL');bevel.width=.014 if o==objects[0] else .025;bevel.segments=2;bevel.limit_method='ANGLE';bevel.angle_limit=.45
 try:
  import materials
  materials.assign_uvs(objects)
 except ImportError:
  # Mappatura metrica per faccia, indipendente dalla presenza del modulo v3.
  for ob in objects:
   me=ob.data;uv=me.uv_layers.new(name='Metriche')
   for f in me.polygons:
    n=f.normal.normalized()
    t=Vector((1,0,0)) if abs(n.z)>.97 else Vector((-n.y,n.x,0)).normalized();v=Vector((0,1,0)) if abs(n.z)>.97 else n.cross(t).normalized()
    for li in f.loop_indices:
     p=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(p.dot(t),p.dot(v))
 result={'objects':len(objects),'faces':sum(len(o.data.polygons) for o in objects),'steps':sum(p['steps'] for p in PROFILES),'flights':sum(p['flights'] for p in PROFILES),'riser_min':min(p['riser'] for p in PROFILES if p['steps']),'riser_max':max(p['riser'] for p in PROFILES if p['steps']),'tread_min':min(p['tread'] for p in PROFILES if p['steps']),'tread_max':max(p['tread'] for p in PROFILES if p['steps']),'clear_width':CLEAR_WIDTH,'outer_width':OUTER_WIDTH,'hidden_original_objects':len(hidden),'start':ROUTE_XYZ[0],'end':ROUTE_XYZ[-1]}
 bpy.context.scene['Scalinata V5']='Gradini proporzionati, rampe con pianerottoli, parapetti continui miterati; sostegno chiuso sotto le pedate.'
 return result
