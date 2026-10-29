"""Hogwarts — studio originale in Blender. Geometria in millimetri.
Eseguire con Blender --background --python build_hogwarts.py.
"""
import bpy, math, random, sys, json
from pathlib import Path
from mathutils import Vector
ROOT=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca')
OUT=ROOT/'outputs'
random.seed(17)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for col in list(bpy.data.collections):
 if col.name!='Collection': bpy.data.collections.remove(col)
if bpy.data.collections.get('Collection'): bpy.data.collections.remove(bpy.data.collections['Collection'])
scene=bpy.context.scene
scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=0.001; scene.unit_settings.length_unit='MILLIMETERS'
COL=None

def collection(name):
 global COL
 COL=bpy.data.collections.new(name); scene.collection.children.link(COL); return COL

def put(obj,name,mat=None):
 obj.name=name
 for c in list(obj.users_collection): c.objects.unlink(obj)
 COL.objects.link(obj)
 if mat: obj.data.materials.append(mat)
 return obj

def mat(name,color,rough=.65,metal=0):
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1); p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metal
 return m
stone=mat('Pietra • calcare miele',(.54,.42,.28))
trim=mat('Pietra • cornici chiare',(.74,.63,.44))
roof=mat('Tetti • ardesia verde blu',(.075,.14,.17),.48)
roof_edge=mat('Tetti • fasce di ardesia',(.115,.21,.24),.5)
window=mat('Finestre • vetro scuro',(.025,.065,.075),.3)
gold=mat('Metallo • ottone invecchiato',(.40,.26,.095),.32,.55)
rock_mats=[mat('Roccia • tono '+str(i+1),c) for i,c in enumerate([(.25,.29,.27),(.31,.34,.30),(.36,.38,.32),(.40,.40,.32),(.29,.32,.29)])]
grass=mat('Terreno • muschio',(.24,.29,.19))
pathmat=mat('Cortili • pietra levigata',(.49,.47,.37))
base_mat=mat('Basamento • verde scuro',(.065,.115,.115),.45)
water=mat('Lago • verde profondo',(.09,.22,.23),.22,.15)
wood=mat('Porte • rovere',(.17,.105,.06))

def bevel(o,width=.2,segments=2):
 mod=o.modifiers.new('Spigoli addolciti','BEVEL'); mod.width=width; mod.segments=segments
 mod=o.modifiers.new('Normali delle superfici','WEIGHTED_NORMAL')
 return o

def cube(name,loc,dim,ma=stone,b=.15):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=put(bpy.context.object,name,ma); o.dimensions=dim
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if b: bevel(o,b)
 return o

def mesh(name,verts,faces,ma):
 me=bpy.data.meshes.new(name); me.from_pydata(verts,[],faces); me.update(); o=bpy.data.objects.new(name,me); COL.objects.link(o)
 if ma: o.data.materials.append(ma)
 return o

def cyl(name,x,y,z,r,h,ma=stone,n=48,r2=None):
 bpy.ops.mesh.primitive_cone_add(vertices=n,radius1=r,radius2=r if r2 is None else r2,depth=h,location=(x,y,z+h/2))
 o=put(bpy.context.object,name,ma)
 for p in o.data.polygons: p.use_smooth=len(p.vertices)==4
 return o

def line(name,a,b,r,ma=trim,n=12):
 d=Vector(b)-Vector(a); o=cyl(name,0,0,0,r,d.length,ma,n)
 o.location=(Vector(a)+Vector(b))/2; o.rotation_euler=d.to_track_quat('Z','Y').to_euler(); return o

def gable(name,x,y,z,l,w,h,ma=roof):
 vs=[(x-l/2,y-w/2,z),(x+l/2,y-w/2,z),(x+l/2,y+w/2,z),(x-l/2,y+w/2,z),(x-l/2,y,z+h),(x+l/2,y,z+h)]
 return mesh(name,vs,[(0,3,2,1),(0,1,5,4),(3,4,5,2),(0,4,3),(1,2,5)],ma)

def arch_outline(w,h,steps=10):
 # Lancetta ogivale con due archi di cerchio.
 r=w; spring=h-math.sqrt(3)*w/2
 pts=[(-w/2,0),(w/2,0),(w/2,spring)]
 for i in range(1,steps+1):
  a=math.pi/3*i/steps; pts.append((-w/2+r*math.cos(a),spring+r*math.sin(a)))
 for i in range(1,steps+1):
  a=2*math.pi/3+math.pi/3*i/steps; pts.append((w/2+r*math.cos(a),spring+r*math.sin(a)))
 return pts

def panel(name,cx,cy,z,w,h,ang=0,depth=.28,ma=window):
 pts=arch_outline(w,h); n=len(pts); vs=[]
 for d in [-depth/2,depth/2]:
  for u,v in pts: vs.append((cx+u*math.cos(ang)-d*math.sin(ang),cy+u*math.sin(ang)+d*math.cos(ang),z+v))
 faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 return mesh(name,vs,faces,ma)

def lancet(name,cx,cy,z,w,h,ang=0,mull=True):
 panel(name+' • cornice',cx,cy,z-.35,w+.9,h+.8,ang,.45,trim)
 # In front of frame, towards local negative Y.
 dx=.28*math.sin(ang); dy=-.28*math.cos(ang)
 panel(name+' • vetro',cx+dx,cy+dy,z,w,h,ang,.16,window)
 if mull:
  line(name+' • montante',(cx+dx*1.3,cy+dy*1.3,z),(cx+dx*1.3,cy+dy*1.3,z+h*.72),.14,trim,8)
  for zz in [z+h*.35]:
   line(name+' • traverso',(cx+dx-w*.46*math.cos(ang),cy+dy-w*.46*math.sin(ang),zz),(cx+dx+w*.46*math.cos(ang),cy+dy+w*.46*math.sin(ang),zz),.13,trim,8)

def spire(name,x,y,z,r,h):
 cyl(name+' • gronda',x,y,z-.5,r*1.08,1.1,roof_edge)
 cyl(name+' • cono',x,y,z,r,h,roof,64,r2=.25)
 for t in [.18,.36,.54,.72]:
  rr=r*(1-t)+.25*t
  cyl(name+' • corso',x,y,z+h*t-.12,rr+.23,.6,roof_edge,64,r2=max(.2,rr+.23-.6*r/h))
 cyl(name+' • puntale',x,y,z+h-.1,.3,2,gold,12,r2=.09)

def tower(name,x,y,r,h,rz,base=33,levels=3,turrets=False):
 cyl(name+' • fusto',x,y,base,r,h,stone)
 for dz,rr,hh in [(0,r+.9,1.8),(h*.32,r+.4,.8),(h*.66,r+.4,.8),(h-2,r+.8,1.5)]:
  cyl(name+' • marcapiano',x,y,base+dz,rr,hh,trim)
 for lev in range(levels):
  zz=base+8+lev*(h-18)/max(1,levels-1)
  for j in range(8):
   a=2*math.pi*j/8
   # local outside normal is -Y; tangent has angle a+pi/2.
   lancet(name+' • finestra',x+(r+.10)*math.cos(a),y+(r+.10)*math.sin(a),zz,2.7,7.8,a+math.pi/2,mull=False)
 spire(name+' • copertura',x,y,base+h,r+1.9,rz)
 if turrets:
  for a in [-math.pi/2,.2,2.9]:
   xx=x+(r-1.4)*math.cos(a); yy=y+(r-1.4)*math.sin(a)
   z=base+h-21
   cyl(name+' • mensola torretta',xx,yy,z-9,1.6,9,trim,24,r2=4.6)
   cyl(name+' • torretta',xx,yy,z,4.5,27,stone,32)
   cyl(name+' • fascia torretta',xx,yy,z+24,4.85,1,trim,32)
   spire(name+' • guglia torretta',xx,yy,z+27,5.3,19)
   lancet(name+' • luce torretta',xx,yy-4.6,z+13,2.0,6,0,False)

def hall(name,x,y,z,l,w,h,rh,windows=9):
 cube(name+' • corpo',(x,y,z+h/2),(l,w,h))
 gable(name+' • timpani',x,y,z+h,l,w,rh,stone)
 gable(name+' • tetto',x,y,z+h-.15,l+2.8,w+3,rh+1.3)
 for side in [-1,1]:
  yy=y+side*(w/2+.20); ang=0 if side==-1 else math.pi
  cube(name+' • cornicione',(x,yy,z+h-1),(l+1.6,1,1.5),trim)
  for j in range(windows):
   xx=x-l/2+6+(l-12)*j/max(windows-1,1)
   lancet(name+' • vetrata',xx,yy,z+10,3.8,h-14,ang)
  for j in range(windows+1):
   xx=x-l/2+2+(l-4)*j/windows
   cube(name+' • contrafforte',(xx,y+side*(w/2+1.1),z+(h-3)/2),(1.5,2.5,h-3),stone)
   cube(name+' • capitello',(xx,y+side*(w/2+1.2),z+h-4),(2,2.9,1.2),trim)
 # Coperture scandite da sottili nervature.
 for j in range(1,windows):
  xx=x-l/2+l*j/windows
  for side in [-1,1]:
   line(name+' • nervatura tetto',(xx,y+side*(w/2+1.5),z+h+.3),(xx,y,z+h+rh+1.4),.17,roof_edge)
 line(name+' • colmo',(x-l/2-1.5,y,z+h+rh+1.4),(x+l/2+1.5,y,z+h+rh+1.4),.4,roof_edge)
 # Pinnacoli sui due timpani.
 for xx in [x-l/2,x+l/2]:
  cyl(name+' • pinnacolo',xx,y,z+h+rh,.6,4,trim,12,r2=.1)

def roman_arch(name,x,y,z,w,h,thick,depth,ma=stone):
 # Elemento pieno sopra una luce semicircolare, senza booleane.
 spring=h-w/2; n=20; vs=[]
 for yy in [y-depth/2,y+depth/2]:
  for i in range(n+1):
   a=math.pi-math.pi*i/n
   xx=x+w/2*math.cos(a); zz=z+spring+w/2*math.sin(a)
   vs.extend([(xx,yy,zz),(xx,yy,z+h+thick)])
 faces=[]; stride=2*(n+1)
 for i in range(n):
  a=2*i; b=a+2
  faces.extend([(a,b,b+1,a+1),(a+stride,a+1+stride,b+1+stride,b+stride),(a,a+stride,b+stride,b),(a+1,b+1,b+1+stride,a+1+stride)])
 faces.extend([(0,1,1+stride,stride),(2*n,2*n+stride,2*n+1+stride,2*n+1)])
 return mesh(name,vs,faces,ma)

# BASAMENTO E RILIEVO
collection('01 • Basamento e scogliera')
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=1,depth=4,location=(0,0,2)); o=put(bpy.context.object,'Base ovale',base_mat); o.scale=(130,98,1); bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); bevel(o,.8,3)
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=1,depth=.8,location=(0,0,4.15)); o=put(bpy.context.object,'Bordo superiore',trim); o.scale=(128,96,1); bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=1,depth=.65,location=(0,0,4.65)); o=put(bpy.context.object,'Superficie del lago',water); o.scale=(126,94,1); bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
# Terrazza superiore irregolare: triangoli sui lati, superficie superiore piana.
n=38; vs=[]; phases=[random.uniform(.94,1.05) for _ in range(n)]
for ring,(sx,sy,zz) in enumerate([(1.05,1.05,5),(.99,.99,16),(.91,.91,33)]):
 for i in range(n):
  a=2*math.pi*i/n; p=phases[i]
  vs.append((-17+109*sx*p*math.cos(a),15+75*sy*p*math.sin(a),zz+(random.uniform(-4,4) if ring==1 else 0)))
faces=[tuple(range(n-1,-1,-1)),tuple(range(2*n,3*n))]
for ring in range(2):
 for i in range(n):
  a=ring*n+i; b=ring*n+(i+1)%n; c=b+n; d=a+n
  faces.extend([(a,b,d),(b,c,d)])
o=mesh('Scogliera • roccia sfaccettata',vs,faces,None)
for m in rock_mats: o.data.materials.append(m)
o.data.materials.append(grass)
for p in o.data.polygons: p.material_index=5 if p.index==1 else random.randrange(5)
# Costoni verticali addossati alla scogliera.
for i in range(28):
 a=2*math.pi*i/28; xx=-17+103*math.cos(a); yy=15+70*math.sin(a)
 cyl('Costone roccioso',xx,yy,5,random.uniform(3,6),random.uniform(12,24),random.choice(rock_mats),5,r2=random.uniform(1,3))

collection('02 • Sala Grande')
hall('Sala Grande',-55,-24,33,88,29,34,24,9)
# Grande vetrata sul fronte occidentale e rosone sul timpano.
lancet('Vetrata del timpano',-99.2,-24,43,11,22,-math.pi/2)
# Piccola lanterna sul colmo.
cube('Lanterna centrale',(-55,-24,90),(7,6,5),stone)
spire('Tetto lanterna',-55,-24,92.5,5,11)

collection('03 • Torre principale')
tower('Torre principale',7,15,18,90,43,33,4,True)
# Contrafforti radiali della grande torre.
for i in range(10):
 a=i*2*math.pi/10; xx=7+18.3*math.cos(a); yy=15+18.3*math.sin(a)
 ob=cube('Torre • contrafforte',(xx,yy,57),(2.2,3,48),stone); ob.rotation_euler[2]=a

collection('04 • Cortile e chiostro')
cube('Cortile • pavimentazione',(-61,29,33.25),(63,52,.8),pathmat)
# Percorsi incisi nel cortile: croce e vasca centrale.
for xx in [-77,-61,-45]: cube('Cortile • lastricato',(xx,29,33.73),(.25,42,.06),trim,0)
for yy in [14,29,44]: cube('Cortile • lastricato',(-61,yy,33.73),(53,.25,.06),trim,0)
cyl('Fontana • base',-61,29,33.8,5.3,.8,trim,32)
cyl('Fontana • vasca',-61,29,34.6,4.1,1.6,stone,32)
cyl('Fontana • acqua',-61,29,36.22,3.5,.08,water,32)
cyl('Fontana • colonna',-61,29,36,1,4,trim,16)
cyl('Fontana • coppa',-61,29,39.4,2.6,.9,trim,24,r2=3)
# Tre gallerie attorno a un cortile realmente aperto.
def gallery(name,x,y,length,rotate=False):
 before=set(bpy.data.objects)
 count=round(length/8); bay=length/count; depth=7; z=34
 for i in range(count+1): cube(name+' • pilastro',(x-length/2+i*bay,y,z+6),(1.7,depth,12),stone)
 for i in range(count): roman_arch(name+' • arcata',x-length/2+(i+.5)*bay,y,z,bay-1.7,12,1.3,depth)
 cube(name+' • architrave',(x,y,47.8),(length+1,depth+1,2),trim)
 gable(name+' • tetto',x,y,48.8,length+2,depth+2,6.5)
 if rotate:
  # ruota tutto il modulo di 90 gradi intorno al suo centro
  for ob in set(bpy.data.objects)-before:
   for v in ob.data.vertices if ob.type=='MESH' else []:
    pass
   # Usare trasformazione globale: vertici mesh con coordinate globali e primitive locali.
   from mathutils import Matrix
   M=Matrix.Translation((x,y,0))@Matrix.Rotation(math.pi/2,4,'Z')@Matrix.Translation((-x,-y,0))
   ob.matrix_world=M@ob.matrix_world
gallery('Chiostro nord',-60,54,62)
gallery('Chiostro ovest',-90,29,43,True)
gallery('Chiostro est',-30,34,33,True)

collection('05 • Torre dell’orologio')
x,y=-84,61; z=33; h=55
cube('Orologio • corpo',(x,y,z+h/2),(22,22,h),stone)
for zz in [z+2,z+20,z+42,z+h-1]: cube('Orologio • cornice',(x,y,zz),(23.5,23.5,1.3),trim)
# Copertura piramidale ruotata, quattro torrette angolari.
o=cyl('Orologio • tetto',x,y,z+h,18,22,roof,4,r2=.4); o.rotation_euler[2]=math.pi/4
for dx in [-10,10]:
 for dy in [-10,10]: tower('Orologio • torretta',x+dx,y+dy,3.1,16,12,z+h-10,1)
for side in [-1,1]:
 for dx in [-6,0,6]: lancet('Orologio • finestra',x+dx,y+side*11.2,z+18,2.7,12,0 if side==-1 else math.pi,False)
# Quadrante sulla facciata visibile.
cy=y-11.55; cz=z+45
ob=cyl('Orologio • cornice circolare',0,0,0,5.6,.8,trim,64); ob.rotation_euler[0]=math.pi/2; ob.location=(x,cy,cz)
ob=cyl('Orologio • quadrante',0,0,0,4.9,.25,roof,64); ob.rotation_euler[0]=math.pi/2; ob.location=(x,cy-.6,cz)
for i in range(12):
 a=i*math.pi/6; line('Orologio • indice',(x+3.8*math.sin(a),cy-.8,cz+3.8*math.cos(a)),(x+4.4*math.sin(a),cy-.8,cz+4.4*math.cos(a)),.13,gold,8)
line('Orologio • lancetta lunga',(x,cy-1,cz),(x+2.6,cy-1,cz+2.6),.18,gold)
line('Orologio • lancetta corta',(x,cy-1.1,cz),(x-2,cy-1.1,cz+1),.22,gold)

collection('06 • Torri e ali orientali')
hall('Ala est',49,31,33,48,18,28,15,5)
hall('Ala posteriore',5,65,33,67,18,32,17,7)
tower('Torre di astronomia',65,55,11,72,33,33,3,True)
tower('Torre ottagonale',62,6,11.5,46,24,33,2)
tower('Torre sul cortile',-24,61,8,48,25,33,2)
tower('Torre sud',-4,-27,9,45,26,33,2)
tower('Torre occidentale',-107,-15,7,39,22,33,2)
tower('Torre secondaria',36,63,7,42,24,33,2)
# Comignoli delle ali, con cuffie separate.
for x,y,zz in [(-14,64,85),(18,64,85),(40,31,79),(73,31,79)]:
 cube('Comignolo',(x,y,zz),(2.6,3.4,12),stone)
 cube('Comignolo • cuffia',(x,y,zz+6),(3.6,4.4,1.2),trim)

collection('07 • Ingresso e ponte ad archi')
# Piazzale e collegamento alla Sala Grande.
cube('Piazzale d’ingresso',(-25,-48,33.65),(39,27,1.2),pathmat)
cube('Passaggio al portale',(-25,-42,40),(15,9,13),stone)
gable('Tetto del passaggio',-25,-42,46.5,17,11,8)
# Ponte lungo X, gli archi si aprono sul prospetto rivolto alla camera.
start=-30; length=126; count=7; bay=length/count; yy=-63; bottom=5; deck=32.7
for i in range(count+1):
 xx=start+i*bay
 cube('Ponte • pila',(xx,yy,(bottom+deck)/2),(3.1,12,deck-bottom),stone,.2)
 cube('Ponte • piede',(xx,yy,6.4),(4.8,14,2.8),trim,.2)
for i in range(count):
 xx=start+(i+.5)*bay
 roman_arch('Ponte • volta',xx,yy,bottom,bay-3.1,deck-bottom-2.2,2.2,12)
 # Conci radiali sulle due facce.
 rr=(bay-3.1)/2; spring=bottom+deck-bottom-2.2-rr
 for side in [-1,1]:
  for j in range(11):
   a=math.pi*j/10
   ob=cube('Ponte • concio',(xx+(rr+.4)*math.cos(a),yy+side*6.1,spring+(rr+.4)*math.sin(a)),(.75,.4,1.6),trim,.05)
   ob.rotation_euler[1]=a-math.pi/2
cube('Ponte • impalcato',(start+length/2,yy,deck+.65),(length+4,14,1.3),pathmat)
for side in [-1,1]:
 cube('Ponte • parapetto',(start+length/2,yy+side*6.8,deck+3),(length+4,1,4),stone)
 cube('Ponte • copertina',(start+length/2,yy+side*6.8,deck+5.1),(length+4,1.4,.5),trim)
# Portale all’estremità di ingresso.
for xx in [90,102]: tower('Ingresso • torre',xx,yy,3.9,22,10,deck+1.3,1)
roman_arch('Ingresso • arco',96,yy,deck+1.3,8.3,17,3,6)
# Sostegno e scalinata che termina sul basamento.
cube('Ingresso • terrazza',(107,yy,18.7),(17,17,27.4),rock_mats[1])
for i in range(12):
 # scala compatta verso il retro del basamento
 zz=deck+1.3-(i+1)*2.25
 cube('Scalinata • gradino',(109,yy+10+i*2.15,(zz+5)/2),(10,2.3,zz-5),trim,.08)
# Alberi bassi e stilizzati, senza coprire l'architettura.
collection('08 • Vegetazione')
for i,(x,y,zz) in enumerate([(-112,29,24),(-103,47,27),(-54,78,28),(85,31,24),(84,47,25),(77,-23,19),(24,78,29),(-76,-50,26)]):
 cyl('Abete • tronco',x,y,zz,.6,8,wood,8)
 for dz,r,h in [(3,4,8),(7,3.2,7),(11,2.2,6)]: cyl('Abete • chioma',x,y,zz+dz,r,h,grass,9,r2=.1)
# Informazioni nel file .blend.
scene['Titolo']='Hogwarts — castello ispirato alla saga'
scene['Descrizione']='Composizione originale semplificata. Esterni modellati; nessun interno. Oggetti e materiali separati per la modifica.'
scene['Unita']='millimetri; 1 unità Blender = 1 mm'
scene['Uso']='Modello visuale modificabile; non certificato per stampa 3D.'
scene['Riferimento']='https://www.wbstudiotour.co.uk/the-experience/explore-the-tour/art-department/'
# Allestimento, sviluppato separatamente.
sys.path.insert(0,str(ROOT/'work'))
from studio_setup import setup_scene
setup_scene()
# Selezione iniziale pulita, nessun oggetto attivo.
bpy.ops.object.select_all(action='DESELECT')
scene.render.filepath=str(OUT/'Hogwarts-anteprima.png')
scene.render.image_settings.file_format='PNG'
# Testo guida incorporato.
txt=bpy.data.texts.new('LEGGIMI • Hogwarts')
txt.write('HOGWARTS — MODELLO BLENDER\n\nVersione originale e semplificata, ispirata al castello cinematografico.\n\nLe collezioni 01–08 contengono terreno, edifici, tetti, finestre e ponte.\nLa collezione 00 contiene solo presentazione, luci e camere.\nGli elementi sono separati e modificabili. I tetti sono pieni; non ci sono interni.\nUnità: millimetri. Base circa 260 × 196 mm.\n\nTastierino 0: vista della camera. Home: inquadra la geometria visibile.\nF12: genera immagine. Le due camere consentono viste opposte.\n\nModello per visualizzazione e modifica; non preparato come unico solido per stampa 3D.\nRiferimento visivo: Warner Bros. Studio Tour, Art Department.\nhttps://www.wbstudiotour.co.uk/the-experience/explore-the-tour/art-department/\n')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Hogwarts.blend'))
print('MODEL_SAVED',len(bpy.data.objects),'objects',flush=True)
bpy.ops.render.render(write_still=True)
print('RENDER_FINISHED',flush=True)
