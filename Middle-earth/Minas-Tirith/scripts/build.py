"""Minas Tirith — a deterministic, editable first architectural interpretation.
Run: Blender --background --python scripts/build.py -- [--preview]
All dimensions are artistic model metres, not a canonical survey.
"""
import bpy, math, random, json, sys
from pathlib import Path
from mathutils import Vector, noise
RNG = random.Random(1437)
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs'
OUT.mkdir(exist_ok=True)
(ROOT / 'work').mkdir(exist_ok=True)
PREVIEW = '--preview' in sys.argv
bpy.ops.wm.read_factory_settings(use_empty=True)
S = bpy.context.scene
S.unit_settings.system = 'METRIC'
S.unit_settings.scale_length = 1
M = []

def mat(name, color, kind='stone', rough=.8):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough
    if kind in ('stone','rock','ground','roof'):
        tc=n.new('ShaderNodeTexCoord');tex=n.new('ShaderNodeTexNoise')
        tex.inputs['Scale'].default_value={'stone':.7,'rock':.13,'ground':.035,'roof':2}[kind]
        tex.inputs['Detail'].default_value=6;l.new(tc.outputs['Object'],tex.inputs['Vector'])
        ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*(v*.64 for v in color),1)
        ramp.color_ramp.elements[1].color=(*(min(1,v*1.13) for v in color),1)
        l.new(tex.outputs['Fac'],ramp.inputs['Fac']);l.new(ramp.outputs['Color'],p.inputs['Base Color'])
        bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.3;bump.inputs['Distance'].default_value=1.4 if kind=='rock' else .05
        l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
        if kind=='stone':
            brick=n.new('ShaderNodeTexBrick');brick.inputs['Scale'].default_value=1
            brick.inputs['Brick Width'].default_value=1.8;brick.inputs['Row Height'].default_value=.8
            brick.inputs['Mortar Size'].default_value=.025
            l.new(tc.outputs['UV'],brick.inputs['Vector'])
            b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=.35;b.inputs['Distance'].default_value=.08;b.invert=True
            l.new(brick.outputs['Fac'],b.inputs['Height']);l.new(bump.outputs['Normal'],b.inputs['Normal']);l.new(b.outputs['Normal'],p.inputs['Normal'])
    M.append(m);return len(M)-1
STONE=mat('Limestone | warm ivory',(.64,.61,.53))
WHITE=mat('Citadel | pale limestone',(.79,.78,.71))
TRIM=mat('Carved stone | highlights',(.73,.7,.61))
DARK=mat('Outer wall | dark stone',(.22,.24,.23))
ROCK=mat('Living rock | strata',(.30,.32,.29),'rock')
ROOF=mat('Weathered slate',(.18,.23,.26),'roof')
ROOF2=mat('Weathered grey roofs',(.29,.29,.26),'roof')
GLASS=mat('Recessed windows | blue black',(.025,.046,.055),'plain',.3)
WOOD=mat('Oak gates',(.13,.072,.033),'plain')
METAL=mat('Iron details',(.065,.075,.075),'plain',.4)
GRASS=mat('Pelennor | muted grass',(.21,.26,.15),'ground')
PAVING=mat('Roads and courtyards',(.43,.42,.36),'stone')
WATER=mat('Fountain water',(.09,.23,.25),'plain',.16)
TREE=mat('White Tree | old bark',(.74,.72,.62),'rock')
CLOTH=mat('Gondor | black banners',(.025,.036,.046),'plain')
GOLD=mat('Banner embroidery',(.67,.59,.38),'plain',.4)
BUSH=mat('Gardens | foliage',(.15,.23,.10),'ground')
COL=None

def coll(name):
    global COL
    COL=bpy.data.collections.new(name);S.collection.children.link(COL);return COL

class Mesh:
    def __init__(self):self.v=[];self.f=[];self.mi=[]
    def add(self,v,f,m):
        k=len(self.v);self.v.extend(v);self.f.extend([tuple(k+i for i in q) for q in f]);self.mi.extend([m]*len(f))
    def box(self,p,d,m=STONE,a=0):
        x,y,z=p;w,h,t=(n/2 for n in d);c=math.cos(a);s=math.sin(a)
        self.add([(x+u*c-v*s,y+u*s+v*c,z+b) for u,v,b in [(-w,-h,-t),(w,-h,-t),(w,h,-t),(-w,h,-t),(-w,-h,t),(w,-h,t),(w,h,t),(-w,h,t)]],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],m)
    def cyl(self,p,r,h,m=STONE,n=16,r2=None):
        if r2 is None:r2=r
        x,y,z=p;v=[(x+rr*math.cos(i*math.tau/n),y+rr*math.sin(i*math.tau/n),z+zz) for rr,zz in [(r,0),(r2,h)] for i in range(n)]
        f=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        self.add(v,f,m)
    def beam(self,p,q,r,m=STONE,r2=None,n=7):
        p=Vector(p);q=Vector(q);d=(q-p).normalized();axis=Vector((0,0,1)) if abs(d.z)<.9 else Vector((1,0,0));u=d.cross(axis).normalized();v=d.cross(u)
        vv=[tuple(c+rr*(math.cos(i*math.tau/n)*u+math.sin(i*math.tau/n)*v)) for c,rr in [(p,r),(q,r if r2 is None else r2)] for i in range(n)]
        self.add(vv,[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],m)
    def sector(self,r0,r1,a0,a1,z0,z1,m=STONE,steps=None):
        n=steps or max(2,int(abs(a1-a0)*r1/2));v=[]
        for j in range(n+1):
            a=a0+(a1-a0)*j/n
            for r,z in [(r0,z0),(r1,z0),(r1,z1),(r0,z1)]:v.append((r*math.sin(a),-r*math.cos(a),z))
        f=[(3,2,1,0),(n*4,n*4+1,n*4+2,n*4+3)]
        for j in range(n):
            k=j*4
            for s in range(4):t=(s+1)%4;f.append((k+s,k+t,k+4+t,k+4+s))
        self.add(v,f,m)
    def finish(self,name):
        me=bpy.data.meshes.new(name);me.from_pydata(self.v,[],self.f);me.update()
        for m in M:me.materials.append(m)
        for i,p in enumerate(me.polygons):p.material_index=self.mi[i]
        uv=me.uv_layers.new(name='Metre-scale masonry')
        for p in me.polygons:
            no=p.normal;axis=max(range(3),key=lambda k:abs(no[k]));axes=[k for k in range(3) if k!=axis]
            for li in p.loop_indices:
                co=me.vertices[me.loops[li].vertex_index].co
                if abs(no.z)<.5 and 'Circle ' in name and ('wall' in name or 'battlements' in name):
                    uv.data[li].uv=(math.atan2(co.x,-co.y)*math.hypot(co.x,co.y),co.z)
                else:uv.data[li].uv=(co[axes[0]],co[axes[1]])
        ob=bpy.data.objects.new(name,me);COL.objects.link(ob);return ob

def pos(r,a,z=0):return (r*math.sin(a),-r*math.cos(a),z)
def local(x,y,z,p,a):return (p[0]+x*math.cos(a)-y*math.sin(a),p[1]+x*math.sin(a)+y*math.cos(a),p[2]+z)

def arch(b,p,w,h,depth,thick,m=TRIM,a=0,fill=False):
    # Semicircular voussoirs and jambs; true open centre unless fill=True.
    r=w/2;spring=h-r;n=14
    for side in (-1,1):b.box(local(side*(r+thick/2),0,spring/2,p,a),(thick,depth,spring),m,a)
    vv=[]
    for i in range(n+1):
        t=math.pi*i/n
        for rr,y in [(r,-depth/2),(r+thick,-depth/2),(r+thick,depth/2),(r,depth/2)]:vv.append(local(rr*math.cos(t),y,spring+rr*math.sin(t),p,a))
    ff=[]
    for i in range(n):
        k=4*i
        for j in range(4):ff.append((k+j,k+(j+1)%4,k+4+(j+1)%4,k+4+j))
    ff.extend([(3,2,1,0),(n*4,n*4+1,n*4+2,n*4+3)]);b.add(vv,ff,m)
    if fill:
        outline=[(-r,0,0),(r,0,0)]+[(r*math.cos(t),0,spring+r*math.sin(t)) for t in [math.pi*i/n for i in range(n+1)]]
        b.add([local(x,y,z,p,a) for x,y,z in outline],[tuple(range(len(outline)))],GLASS)

def roof(b,p,w,d,h,m=ROOF,a=0):
    v=[(-w/2,-d/2,0),(w/2,-d/2,0),(w/2,d/2,0),(-w/2,d/2,0),(-w/2,0,h),(w/2,0,h)]
    b.add([local(*v0,p,a) for v0 in v],[(0,1,5,4),(3,4,5,2),(0,4,3),(1,2,5),(0,3,2,1)],m)

def building(name,p,w,d,h,a=0,palace=False):
    b=Mesh();st=WHITE if palace else STONE
    b.box(local(0,0,h/2,p,a),(w,d,h),st,a)
    b.box(local(0,0,.35,p,a),(w+.6,d+.6,.7),TRIM,a)
    for z in [h*.5,h-.35]:b.box(local(0,0,z,p,a),(w+.3,d+.3,.35),TRIM,a)
    roof(b,local(0,0,h,p,a),w+.8,d+.8,d*RNG.uniform(.29,.58),ROOF if RNG.random()<.72 else ROOF2,a)
    if RNG.random()<.22 and not palace:
        b.box(local(0,-d/2-1,h*.55,p,a),(w*.65,2,.3),TRIM,a)
        for bx in [-w*.28,0,w*.28]:b.box(local(bx,-d/2-1.8,h*.55+.7,p,a),(.17,.17,1.4),TRIM,a)
        b.box(local(0,-d/2-1.8,h*.55+1.4,p,a),(w*.65,.2,.2),TRIM,a)
    for side in (-1,1):
        for z in [2.8,h*.67]:
            for x in [-w*.3,0,w*.3]:
                arch(b,local(x,side*(d/2+.06),z,p,a),.9,1.7,.12,.16,TRIM,a,True)
    arch(b,local(0,-d/2-.12,0,p,a),1.55,2.9,.2,.22,TRIM,a,True)
    for x in (-w/2,w/2):b.box(local(x,0,h*.5,p,a),(.35,d+.5,h),TRIM,a)
    if RNG.random()<.55:b.box(local(w*.29,d*.2,h+d*.36,p,a),(.8,.8,2.4),STONE,a)
    o=b.finish(name);o['role']='building';return o

def turret(b,p,r,h,stone=STONE,spire=False):
    b.cyl(p,r*1.16,1,stone);b.cyl((p[0],p[1],p[2]+1),r,h-1,stone)
    for dz in [h*.35,h*.7,h-.7]:b.cyl((p[0],p[1],p[2]+dz),r*1.08,.5,TRIM)
    for a in [i*math.tau/8 for i in range(8)]:
        x=p[0]+r*math.sin(a);y=p[1]-r*math.cos(a)
        arch(b,(x,y,p[2]+h*.52),max(.5,r*.35),max(1.5,h*.17),.15,.16,TRIM,a,True)
    if spire:
        b.cyl((p[0],p[1],p[2]+h),r*1.2,r*2.5,ROOF,16,0)
    else:
        b.cyl((p[0],p[1],p[2]+h),r*1.2,.7,TRIM)
        for a in [i*math.tau/12 for i in range(12)]:b.box((p[0]+r*1.03*math.sin(a),p[1]-r*1.03*math.cos(a),p[2]+h+1.2),(r*.36,r*.38,1.3),stone,a)

# Site: a subdued landscape, with a modelled rocky mountain behind the city.
coll('01 | Pelennor and mountain')
b=Mesh();b.box((0,0,-7),(12000,12000,10),GRASS);b.finish('Pelennor fields')
b=Mesh();nx=200;ny=140
for j in range(ny+1):
    y=65+j*3
    for i in range(nx+1):
        x=-360+i*3.6
        edge=max(0,min(1,(y-65)/48))
        profile=235*math.exp(-((x+60)/185)**2-((y-215)/250)**2)+100*math.exp(-((x-195)/100)**2-((y-205)/190)**2)
        detail=noise.fractal(Vector((x*.016,y*.016,2)),1,2,5)*22
        rim=max(0,min(1,(360-abs(x))/65))*max(0,min(1,(485-y)/85))
        z=max(-2.3,edge*rim*(profile+detail)-2.2)
        b.v.append((x,y,z))
for j in range(ny):
    for i in range(nx):
        k=j*(nx+1)+i;b.f.extend([(k,k+1,k+nx+2),(k,k+nx+2,k+nx+1)]);b.mi.extend([ROCK,ROCK])
o=b.finish('Mount Mindolluin | interpreted foothill')
for poly in o.data.polygons:poly.use_smooth=True
# Approach road, a little irregular rather than a perfectly straight runway.
b=Mesh();pts=[(0,-230,.05),(0,-251,-1.8),(0,-280,-1.8),(20,-330,-1.8),(45,-395,-1.8),(95,-485,-1.8),(120,-600,-1.8)]
verts=[]
for i,p in enumerate(pts):
    v=Vector(pts[min(i+1,len(pts)-1)])-Vector(pts[max(i-1,0)]);n=Vector((-v.y,v.x,0)).normalized()*5
    verts.extend([tuple(Vector(p)-n),tuple(Vector(p)+n)])
b.add(verts,[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(pts)-1)],PAVING)
b.finish('Road from the Pelennor')

RADII=[240,204,169,136,105,77,50]
HEIGHTS=[0,26,52,78,104,130,156]
SPAN=math.radians(128)
GATES=[0,1.25,-1.30,1.20,-1.25,1.22,-1.28]
ramps=[]
for i in range(6):
    ga=GATES[i+1];sign=1 if ga>0 else -1;start=ga-sign*.82
    samples=[]
    for j in range(61):
        t=j/60;u=min(t/.88,1);a=start+(ga-start)*u
        r=(RADII[i]-8)*(1-u)+(RADII[i+1]+6)*u if t<=.88 else RADII[i+1]+6-12*(t-.88)/.12
        z=HEIGHTS[i]+26*u+.16
        samples.append((*pos(r,a)[:2],z))
    ramps.append(samples)

def near_ramp(x,y,extra=0):
    return any((x-p[0])**2+(y-p[1])**2<(5+extra)**2 for path in ramps for p in path[::2])

def rock_width(y):
    if y < -187 or y>100:return 0
    return 3+(y+187)/287*32

building_counts=[]
for level,(r,z) in enumerate(zip(RADII,HEIGHTS)):
    coll(f'{10+level:02d} | Circle {level+1} | walls and streets')
    # Solid terrace with a clean top. Retaining face below the next circle is masonry.
    b=Mesh();b.sector(.01,r-3,-SPAN,SPAN,-2,z-.05,PAVING);b.finish(f'Circle {level+1} | terrace')
    b=Mesh();ga=GATES[level];half=5.5/r;st=DARK if level==0 else STONE
    intervals=[(-SPAN,ga-half),(ga+half,SPAN)]
    if level==6:
        intervals=[(a0,min(a1,-.48)) for a0,a1 in intervals if a0<-.48]+[(max(a0,.48),a1) for a0,a1 in intervals if a1>.48]
    for a0,a1 in intervals:
        b.sector(r-3,r,a0,a1,z-26 if level else -2,z+8,st)
        b.sector(r-3.5,r+.5,a0,a1,z+6.8,z+7.4,TRIM)
        b.sector(r-3.4,r+.4,a0,a1,z+.6,z+1.2,TRIM)
    n=int(2*SPAN*r/2.5)
    for j in range(n+1):
        a=-SPAN+2*SPAN*j/n
        if abs(a-ga)<half+.004 or (level==6 and abs(a)<.49):continue
        b.box(pos(r-1,a,z+8.7),(1.45,2.2,1.5),st,a)
    b.finish(f'Circle {level+1} | curtain wall and battlements')
    b=Mesh();n=max(8,int(r/12))
    for j in range(n+1):
        a=-SPAN+2*SPAN*j/n
        if abs(a-ga)<.085 or (level==6 and abs(a)<.49):continue
        turret(b,pos(r-.7,a,z),2.8 if level==0 else 2.2,12,st)
        # Vertical buttress ties the parapet tower to the exposed retaining wall.
        if level:b.box(pos(r-.7,a,z-12),(3.2,3.8,25),st,a)
    b.finish(f'Circle {level+1} | wall towers')
    b=Mesh();p=pos(r-1.5,ga,z)
    arch(b,p,10,9,5,1.4,TRIM,ga)
    # An upper lintel above the open arch.
    b.box(local(0,0,11.1,p,ga),(13,5,2.4),st,ga)
    for side in (-1,1):turret(b,local(side*8,0,0,p,ga),3.8,17,st)
    if level==0:
        # Two open door leaves, rotated inward.
        for side in (-1,1):
            hinge=local(side*4.9,1,0,p,ga);ang=ga+side*.98
            b.box(local(-side*2.3,0,3.5,hinge,ang),(4.6,.45,7),WOOD,ang)
            for zz in [1.3,3.7,6]:b.box(local(-side*2.3,-.26,zz,hinge,ang),(4.5,.12,.24),METAL,ang)
    b.box(local(0,0,-.15,p,ga),(10,9,.3),PAVING,ga)
    b.finish(f'Circle {level+1} | gate')
    if level==6:break
    coll(f'{20+level:02d} | Circle {level+1} | houses')
    count=0
    rows=[r-19] if level>=3 else [r-16,r-28]
    for row,rr in enumerate(rows):
        n=int(2*SPAN*rr/10.4)
        for j in range(n):
            a=-SPAN+2*SPAN*(j+.5)/n+RNG.uniform(-.006,.006)
            x,y,_=pos(rr,a)
            if y>78 or abs(x)<rock_width(y)+6:continue
            if abs(a-ga)<.07 or near_ramp(x,y,6):continue
            w=RNG.uniform(6.3,8.9);d=RNG.uniform(6.5,8.6);h=RNG.uniform(7,14)
            building(f'L{level+1} | house {count+1:03d}',(x,y,z),w,d,h,a)
            count+=1
    # Taller civic buildings terminate the curved streets near the mountain.
    b=Mesh()
    for sign in (-1,1):
        a=sign*1.85;rr=r-17;x,y,_=pos(rr,a)
        if y<78 and not near_ramp(x,y,8):
            turret(b,(x,y,z),3.2,25,STONE,True)
    b.finish(f'L{level+1} | slender civic towers')
    building_counts.append(count)

coll('30 | Roads between the circles')
for i,pts in enumerate(ramps):
    b=Mesh();vv=[]
    for j,p in enumerate(pts):
        t=Vector(pts[min(j+1,len(pts)-1)])-Vector(pts[max(j-1,0)]);n=Vector((-t.y,t.x,0)).normalized()*3.1
        vv.extend([tuple(Vector(p)-n),tuple(Vector(p)+n),tuple(Vector(p)-n-Vector((0,0,.8))),tuple(Vector(p)+n-Vector((0,0,.8)))])
    ff=[]
    for j in range(len(pts)-1):
        k=j*4;ff.extend([(k,k+4,k+5,k+1),(k+2,k+3,k+7,k+6),(k,k+2,k+6,k+4),(k+1,k+5,k+7,k+3)])
        for side in (0,1):
            pa=Vector(vv[k+side])+Vector((0,0,.8));pb=Vector(vv[k+4+side])+Vector((0,0,.8));b.beam(pa,pb,.25,TRIM,n=5)
            if j%3==0:b.beam(vv[k+side],pa,.13,TRIM,n=5)
        if j%5==0 and pts[j][2]>HEIGHTS[i]+2:
            for side in (0,1):
                q=vv[k+side];b.box((q[0],q[1],(q[2]+HEIGHTS[i])*.5),(.85,.85,q[2]-HEIGHTS[i]),STONE)
    b.add(vv,ff,PAVING);o=b.finish(f'Ramp {i+1} to {i+2} | curved ascent');o['role']='ramp'

coll('40 | Great rock and summit promenade')
b=Mesh();nx=110;nz=55
# Triangulated sides with tapering vertical strata, and a flat walkable crown.
for side in (-1,1):
    vv=[]
    for j in range(nz+1):
        t=j/nz;z=-1+t*157
        for i in range(nx+1):
            y=-187+i*287/nx;width=rock_width(y)
            jitter=(math.sin(i*.8+j*.11)*1.3+math.sin(i*1.73-j*.08)*.75+noise.noise_vector(Vector((i*.23,j*.14,side)))[0]*.5)*math.sin(math.pi*i/nx)
            x=side*(width+(1-t)*5+(jitter if j not in (0,nz) else 0))
            vv.append((x,y,z))
    ff=[]
    for j in range(nz):
        for i in range(nx):
            k=j*(nx+1)+i;qs=[(k,k+nx+1,k+1),(k+1,k+nx+1,k+nx+2)]
            ff.extend(qs if side>0 else [tuple(reversed(q)) for q in qs])
    b.add(vv,ff,ROCK)
# Close sharp nose and rear, preserving the recognizable long vertical keel.
for y in [-187,100]:
    w=rock_width(y);b.add([(-w-5,y,-1),(w+5,y,-1),(w,y,156),(-w,y,156)],[(0,1,2,3)],ROCK)
poly=[]
for side,seq in [(-1,range(nx+1)),(1,reversed(range(nx+1)))]:
    for i in seq:
        y=-187+i*287/nx;poly.append((side*rock_width(y),y,156))
b.add(poly,[tuple(range(len(poly)))],PAVING)
o=b.finish('Great rock | the stone prow')
for poly in o.data.polygons:
    if poly.material_index==ROCK:poly.use_smooth=True
# Crown paving and low crenellated parapets.
b=Mesh()
for side in (-1,1):
    for i in range(60):
        y=-184+i*3.65;w=rock_width(y);x=side*(w-.45)
        b.box((x,y,157.2),(.9,3.7,2.4),STONE)
        if i%2==0:b.box((x,y,159),(.95,1.6,1.2),TRIM)
b.finish('Prow | summit parapets')

coll('50 | Citadel and Tower of Ecthelion')
# Long ceremonial hall, aisles, buttresses and a thin, tapering white tower.
building('Citadel | Hall of the Kings',(0,40,156),27,51,25,0,True)
b=Mesh()
for side in (-1,1):
    for y in [19,29,39,49,59]:
        b.box((side*15,y,167),(2,2.4,22),WHITE)
        b.cyl((side*15,y,178),1.5,7,WHITE,8,.65)
        b.cyl((side*15,y,185),.85,4,WHITE,8,0)
        arch(b,(side*13.65,y,161),3.3,13,.3,.45,TRIM,math.pi/2,True)
for x in [-10,10]:turret(b,(x,14,156),2.5,33,WHITE,True)
b.finish('Citadel | buttresses and lancets')
b=Mesh();p=(0,-7,156)
for zz,r,h in [(0,6.8,6),(6,5.6,35),(41,4.8,19),(60,3.4,14),(74,2.2,12)]:
    b.cyl((p[0],p[1],p[2]+zz),r,h,WHITE,12,r*.91)
    b.cyl((p[0],p[1],p[2]+zz+h-.7),r*1.13,.7,TRIM,12)
    for a in [i*math.tau/8 for i in range(8)]:
        x=r*.94*math.sin(a);y=-7-r*.94*math.cos(a)
        b.beam((x,y,156+zz),(x*.93,-7+(y+7)*.93,156+zz+h),.32,TRIM)
        if h>10:arch(b,(x,y,156+zz+3),max(.6,r*.32),h*.58,.15,.17,TRIM,a,True)
b.cyl((0,-7,242),2.2,13,WHITE,12,0)
for a in [i*math.tau/4+math.pi/4 for i in range(4)]:
    x=5.2*math.sin(a);y=-7-5.2*math.cos(a);b.cyl((x,y,187),.9,14,WHITE,8,.5);b.cyl((x,y,201),.65,6,WHITE,8,0)
b.finish('Tower of Ecthelion | tapering white spire')
# Fountain court extends along the top of the rock.
coll('51 | Court of the Fountain and White Tree')
b=Mesh();b.cyl((0,-57,156.06),12,.35,TRIM,64)
b.cyl((0,-57,156.4),8,.45,PAVING,48)
b.cyl((0,-57,156.9),5.6,.15,GRASS,48)
b.cyl((0,-88,156.1),7.5,.6,TRIM,48)
b.cyl((0,-88,156.7),6.7,.35,WATER,48)
# Basin ring uses annular sectors in local coordinates.
for i in range(64):
    a=i*math.tau/64;aa=(i+1)*math.tau/64
    b.beam((7*math.cos(a),-88+7*math.sin(a),157.1),(7*math.cos(aa),-88+7*math.sin(aa),157.1),.45,WHITE,n=6)
b.cyl((0,-88,157),1,2.3,TRIM,16)
b.cyl((0,-88,159),2.6,.5,TRIM,32,2.9)
b.finish('Court | circular paving and fountain')
b=Mesh()
def branch(p,v,length,r,depth):
    q=Vector(p)+Vector(v).normalized()*length;b.beam(p,q,r,TREE,r*.56,8)
    if depth:
        for k in range(3 if depth==3 else 2):
            a=RNG.uniform(0,math.tau);vv=Vector((math.cos(a)*.8,math.sin(a)*.8,RNG.uniform(.35,.9)))+Vector(v)*.4
            branch(q,vv,length*RNG.uniform(.55,.75),r*.53,depth-1)
branch((0,-57,157),(.08,.06,1),6,1.15,4)
o=b.finish('White Tree of Gondor | bare branching crown')
for poly in o.data.polygons:poly.use_smooth=True
# Colonnades framing the ceremony court.
b=Mesh()
for side in (-1,1):
    for i in range(9):
        y=-32+i*5;x=side*27
        b.cyl((x,y,156),.7,6.2,WHITE,10)
        if i<8:arch(b,(x,y+2.5,158.6),3.6,3.6,1,.4,TRIM,math.pi/2)
    b.box((side*27,-12,163),(2,43,.6),TRIM)
b.finish('Citadel | open arcades')
# Hanging cloth banners, with a stylised white tree emblem made of geometry.
coll('52 | Banners of Gondor')
b=Mesh()
for side in (-1,1):
    x=side*18;y=-28
    b.beam((x,y,156),(x,y,168),.12,METAL)
    b.beam((x,y,167),(x+side*3.5,y,167),.1,METAL)
    verts=[]
    for j in range(9):
        for i in range(6):verts.append((x+side*(.3+i*.58),y+math.sin(i*.9+j*.7)*.24,167-j*.55))
    faces=[(j*6+i,j*6+i+1,(j+1)*6+i+1,(j+1)*6+i) for j in range(8) for i in range(5)];b.add(verts,faces,CLOTH)
    xx=x+side*1.7
    b.beam((xx,y-.3,163.3),(xx,y-.3,165.7),.065,WHITE)
    for dz in [0,.6,1.2]:
        for sg in [-1,1]:b.beam((xx,y-.3,163.8+dz),(xx+sg*.65,y-.3,164.3+dz),.05,WHITE)
b.finish('Court | black standards and White Tree emblems')

coll('90 | Cameras and light')
def camera(name,p,target,lens=50,ortho=None):
    d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);COL.objects.link(o);o.location=p
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=6000
    if ortho:d.type='ORTHO';d.ortho_scale=ortho
    return o
hero=camera('Camera | city from the southeast',(510,-735,380),(0,-5,103),51)
camera('Camera | front and seven circles',(0,-910,330),(0,0,102),51)
camera('Camera | White Tree court',(180,-310,295),(0,-35,193),48)
camera('Camera | plan',(0,-5,1100),(0,0,0),ortho=600)
camera('Camera | main gate',(72,-340,55),(0,-180,42),44)
S.camera=hero
sun_d=bpy.data.lights.new('Late afternoon sun','SUN');sun_d.energy=3.6;sun_d.angle=.09
sun=bpy.data.objects.new('Late afternoon sun',sun_d);COL.objects.link(sun);sun.rotation_euler=Vector((-.65,-.8,1.3)).to_track_quat('Z','Y').to_euler();sun_d.color=(1,.92,.80)
world=bpy.data.worlds.new('Clear pale sky');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.56,.68,.82,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.65;S.world=world
S.render.engine='CYCLES';S.cycles.samples=24 if PREVIEW else 48;S.cycles.use_denoising=True;S.cycles.use_adaptive_sampling=True;S.cycles.adaptive_threshold=.035
S.cycles.max_bounces=5
try:
    pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='METAL';pref.get_devices()
    for d in pref.devices:d.use=d.type=='METAL'
    S.cycles.device='GPU'
except Exception:S.cycles.device='CPU'
S.render.resolution_x=1300 if PREVIEW else 2200;S.render.resolution_y=1050 if PREVIEW else 1700;S.render.resolution_percentage=100
S.render.image_settings.file_format='PNG';S.render.film_transparent=False
S.view_settings.view_transform='AgX'
S['Project']='Minas Tirith — first architectural interpretation';S['Seed']=1437;S['Circles']=7;S['Not a canonical plan']=True
S['Building counts']=str(building_counts)
S['Known limits']='Exteriors only; interpreted dimensions; ramps and gates require navigation refinement; not print-ready.'
# Open comfortably in material view, looking through the main camera.
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.clip_end=6000;area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL'
bpy.context.preferences.filepaths.save_version=0
S.render.filepath=str(OUT/'Minas-Tirith-overview.png')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Minas-Tirith.blend'),compress=True)
report={'circles':len(RADII),'houses_per_circle':building_counts,'houses':sum(building_counts),'objects':len(bpy.data.objects),'mesh_objects':sum(o.type=='MESH' for o in bpy.data.objects),'faces':sum(len(m.polygons) for m in bpy.data.meshes),'ramp_count':len(ramps),'seed':1437,'scope':'First exterior interpretation; not an official plan or a finished navigable city.'}
(ROOT/'work'/'build.json').write_text(json.dumps(report,indent=2))
print('MODEL_SAVED',json.dumps(report),flush=True)
if '--no-render' not in sys.argv:
    bpy.ops.render.render(write_still=True)
    print('OVERVIEW_RENDERED',flush=True)
