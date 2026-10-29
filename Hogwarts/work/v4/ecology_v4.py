"""Boschi per gruppi e rive irregolari per il paesaggio esteso di Hogwarts.
Si applica dopo terrain_v4.apply(); non salva né renderizza il progetto.
"""
import bpy, math, random
from mathutils import Vector
from mathutils.bvhtree import BVHTree

WATER_Z=.7

class Shape:
    def __init__(self):self.v=[];self.f=[];self.mi=[]
    def add(self,verts,faces,mat=0):
        k=len(self.v);self.v.extend(tuple(v) for v in verts)
        self.f.extend(tuple(k+i for i in f) for f in faces);self.mi.extend([mat]*len(faces))
    def tube(self,a,b,r0,r1=None,n=6,mat=0):
        a=Vector(a);b=Vector(b);d=b-a
        if d.length<1e-7:return
        d.normalize();u=d.cross(Vector((0,0,1)))
        if u.length<.05:u=d.cross(Vector((0,1,0)))
        u.normalize();v=d.cross(u);r1=r0 if r1 is None else r1
        verts=[p+r*(u*math.cos(j*2*math.pi/n)+v*math.sin(j*2*math.pi/n)) for p,r in [(a,r0),(b,r1)] for j in range(n)]
        faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
        self.add(verts,faces,mat)
    def ellipsoid(self,p,rx,ry,rz,phase=0,n=9,rings=5,mat=1,irregular=.09):
        p=Vector(p);verts=[]
        for k in range(rings+1):
            theta=.035+(math.pi-.07)*k/rings
            for j in range(n):
                a=phase+j*2*math.pi/n;f=1+irregular*math.sin(j*3.17+k*2.31+phase)
                verts.append(p+Vector((rx*f*math.sin(theta)*math.cos(a),ry*f*math.sin(theta)*math.sin(a),rz*math.cos(theta))))
        faces=[tuple(range(n-1,-1,-1)),tuple(range(rings*n,(rings+1)*n))]
        for k in range(rings):
            for j in range(n):
                a=k*n+j;b=k*n+(j+1)%n;faces.extend([(a,b,a+n),(b,b+n,a+n)])
        self.add(verts,faces,mat)
    def mesh(self,name,mats):
        me=bpy.data.meshes.new(name);me.from_pydata(self.v,[],self.f);me.update()
        for m in mats:me.materials.append(m)
        for p,idx in zip(me.polygons,self.mi):p.material_index=idx
        return me

def _collection(name):
    col=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(col);return col

def _material(name,base,rough=.9):
    m=bpy.data.materials.get(name)
    if m:return m
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*base,1)
    n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');p.inputs['Roughness'].default_value=rough
    ob=n.new('ShaderNodeObjectInfo');r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].color=(*(c*.72 for c in base),1);r.color_ramp.elements[1].color=(*(min(1,c*1.25) for c in base),1)
    l.new(ob.outputs['Random'],r.inputs[0]);l.new(r.outputs['Color'],p.inputs['Base Color'])
    return m

def _pine_mesh(name,variant,mats):
    rng=random.Random(100+variant);s=Shape();n=10 if variant<3 else 8;tiers=8 if variant<3 else 6
    leanx=rng.uniform(-.025,.025);leany=rng.uniform(-.02,.02)
    s.tube((0,0,-.018),(leanx,leany,1.0),.023,.003,7,0)
    for lev in range(tiers):
        t=.17+lev*.095 if tiers==8 else .20+lev*.13
        r=(.25*(1-t)+.015)*rng.uniform(.86,1.12);h=.20;ph=lev*1.16+variant
        verts=[]
        for ring,rr,zz in [(0,r,t-.025),(1,r*.80,t+.048),(2,r*.12,t+h)]:
            for j in range(n):
                a=ph+j*2*math.pi/n;f=1+.20*math.sin(j*2.91+lev)+rng.uniform(-.05,.05)
                verts.append((leanx*t+rr*f*math.cos(a),leany*t+rr*f*math.sin(a),zz+(.014*math.sin(j*2.07+lev) if ring<2 else 0)))
        fs=[]
        for k in range(2):
            for j in range(n):
                a=k*n+j;b=k*n+(j+1)%n;fs.extend([(a,b,a+n),(b,b+n,a+n)])
        fs.append(tuple(range(2*n,3*n)));s.add(verts,fs,1+lev%3)
        if lev<5:
            for j in range(4):
                a=ph+j*math.pi/2;tip=(leanx*t+r*.94*math.cos(a),leany*t+r*.94*math.sin(a),t+.01)
                s.tube((leanx*t,leany*t,t+.09),tip,.0055,.0015,5,0)
    return s.mesh(name,mats)

def _scots_mesh(name,variant,mats):
    rng=random.Random(701+variant);s=Shape();lean=.05 if variant%2 else -.045
    s.tube((0,0,-.025),(lean,0,.93),.027,.007,8,0)
    # Chioma larga e diseguale, distinta dalle conifere piramidali.
    for j in range(7):
        a=j*2.399+variant;level=.52+j*.055;r=.12+rng.random()*.09
        tip=Vector((lean*.6+r*math.cos(a),r*math.sin(a),level+.08))
        s.tube((lean*level,0,level-.13),tip,.009,.003,6,0)
        s.ellipsoid(tip,.14+rng.random()*.06,.14,.14+j*.005,a,8,3,1+j%3,.16)
    s.ellipsoid((lean,0,.93),.13,.12,.12,0,8,3,2,.15)
    return s.mesh(name,mats)

def _rock_mesh(name,variant,mat):
    rng=random.Random(821+variant);s=Shape();n=7;verts=[]
    for z,r in [(-.14,.65),(.18,1),(.75,.73),(1.0,.28)]:
        for j in range(n):
            a=j*2*math.pi/n;f=rng.uniform(.77,1.18);verts.append((r*f*math.cos(a),r*f*math.sin(a),z+rng.uniform(-.07,.07)))
    fs=[tuple(range(n-1,-1,-1)),tuple(range(3*n,4*n))]
    for k in range(3):
        for j in range(n):
            a=k*n+j;b=k*n+(j+1)%n;fs.extend([(a,b,a+n),(b,b+n,a+n)])
    s.add(verts,fs);return s.mesh(name,[mat])

def _bush_mesh(name,variant,mats):
    rng=random.Random(912+variant);s=Shape()
    for j in range(5):
        a=j*2.4;rr=rng.uniform(.1,.32);p=(rr*math.cos(a),rr*math.sin(a),.30+rng.random()*.24)
        s.tube((0,0,-.04),p,.022,.007,5,0)
        s.ellipsoid(p,.25,.23,.28,a,7,3,1+j%3,.19)
    return s.mesh(name,mats)

def _terrain_sampler():
    candidates=[];col=bpy.data.collections.get('40 • Paesaggio esteso')
    if col:
        for o in col.all_objects:
            if o.type!='MESH' or o.hide_render:continue
            if any(t in o.name.lower() for t in ['acqua','water']):continue
            if any(m and m.name=='water' for m in o.data.materials):continue
            if len(o.data.polygons)>10:candidates.append(o)
    for o in bpy.data.objects:
        if o.type!='MESH' or o.hide_render:continue
        if 'sommità' in o.name or o.name in ['Colline occidentali | superficie','Scogliera della rimessa | superficie']:
            if o not in candidates:candidates.append(o)
    bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();bv=[]
    for o in candidates:
        ev=o.evaluated_get(dg);me=ev.to_mesh();matrix=o.matrix_world
        verts=[matrix@v.co for v in me.vertices];faces=[tuple(p.vertices) for p in me.polygons]
        bv.append((o.name,BVHTree.FromPolygons(verts,faces,all_triangles=False)));ev.to_mesh_clear()
    if not bv:raise RuntimeError('Nessuna superficie di terreno disponibile per appoggiare la vegetazione')
    def ground(x,y):
        best=None
        for name,tree in bv:
            point,normal,_,_=tree.ray_cast(Vector((x,y,1300)),Vector((0,0,-1)),3000)
            if point is not None and (best is None or point.z>best[0]):best=(point.z,normal,name)
        return best
    return ground,[name for name,_ in bv]

def _distance_segment(x,y,a,b):
    dx=b[0]-a[0];dy=b[1]-a[1];d=dx*dx+dy*dy
    t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/d)) if d else 0
    return math.hypot(x-a[0]-t*dx,y-a[1]-t*dy)

def _protected(x,y):
    if -75<x<215 and -205<y<195:return True
    if -143<x<-45 and -110<y<-15:return True
    if -143<x<27 and 90<y<235:return True
    if math.hypot(x+213,y+62)<23 or math.hypot(x+191,y-75)<23:return True
    if _distance_segment(x,y,(-209,-62),(-112,-62))<14:return True
    if _distance_segment(x,y,(-191,75),(-120,175))<10:return True
    return False

def _instance(name,me,col,loc,scale,angle):
    ob=bpy.data.objects.new(name,me);col.objects.link(ob);ob.location=loc;ob.scale=scale;ob.rotation_euler[2]=angle;return ob

def apply():
    rng=random.Random(260526)
    hidden=[]
    for o in list(bpy.data.objects):
        if o.name in ['Bosco sulle colline','Conifere | tronchi e rami','Conifere | palchi e aghi','Rocce | detriti di riva'] or o.name.startswith('Sottobosco |'):
            o.hide_render=True;o.hide_set(True);hidden.append(o.name)
    ground,ground_names=_terrain_sampler()
    bark=_material('Paesaggio | corteccia',(.065,.037,.020))
    green=[_material('Paesaggio | aghi ombrosi',(.014,.039,.022)),_material('Paesaggio | aghi verdi',(.027,.063,.031)),_material('Paesaggio | aghi giovani',(.055,.093,.041))]
    mats=[bark]+green
    prototypes=[_pine_mesh('Abete | variante '+str(i+1),i,mats) for i in range(4)]+[_scots_mesh('Pino silvestre | variante '+str(i+1),i,mats) for i in range(2)]
    forest=_collection('41 • Boschi e radure')
    # Centri di macchie boschive, con una parte larga e nuclei più fitti.
    centers=[(-335,-20,58,45),(-395,150,70,50),(-560,40,90,50),(-620,300,75,50),(-760,440,75,40),(-500,470,65,45),(-300,370,75,45),(-230,610,80,50),(-50,530,65,40),(140,520,70,40),(320,700,75,45),(480,800,65,35),(620,870,65,30),(970,390,55,55),(1030,120,65,50),(1020,-150,55,45),(900,-420,70,55),(810,-650,65,45),(-300,-280,45,35),(-420,-340,65,40)]
    placements=[];spatial={};cell=5;target=840;attempts=0
    weights=[c[3] for c in centers]
    while len(placements)<target and attempts<target*24:
        attempts+=1;cx,cy,spread,_=rng.choices(centers,weights=weights,k=1)[0]
        x=rng.gauss(cx,spread*.58);y=rng.gauss(cy,spread*.58)
        if _protected(x,y) or x<-1100 or x>1200 or y<-900 or y>1050:continue
        hit=ground(x,y)
        if hit is None:continue
        z,n,_=hit
        if z<3 or z>360 or n.z<math.cos(math.radians(34)):continue
        # Radure sinuose in mezzo ai gruppi e rare aperture presso le rive.
        clearing=math.sin(x*.013+y*.006)+math.cos(y*.017-x*.004)
        if clearing>1.55 and rng.random()<.85:continue
        k=(int(x//cell),int(y//cell));too_close=False
        for ix in range(k[0]-1,k[0]+2):
            for iy in range(k[1]-1,k[1]+2):
                for px,py in spatial.get((ix,iy),[]):
                    if (x-px)**2+(y-py)**2<18:too_close=True;break
        if too_close:continue
        dist=math.hypot(x,y);h=rng.uniform(10,19) if dist<420 else rng.uniform(14,27)
        # La parte alta dei colli resta in prevalenza brulla.
        if z>190 and rng.random()<(z-190)/200:continue
        variant=rng.choices(range(6),weights=[3,3,2,3,1,1])[0];me=prototypes[variant]
        ob=_instance('Bosco | '+('abete' if variant<4 else 'pino'),me,forest,(x,y,z-.18),(h*rng.uniform(.88,1.08),h*rng.uniform(.88,1.08),h),rng.random()*math.tau)
        placements.append((x,y,z,h));spatial.setdefault(k,[]).append((x,y))
    shores=_collection('42 • Rive e sottobosco')
    bushm=[bark,_material('Paesaggio | arbusti scuri',(.043,.080,.026)),_material('Paesaggio | arbusti verdi',(.075,.117,.036)),_material('Paesaggio | erica',(.111,.100,.067))]
    bushes=[_bush_mesh('Arbusto | variante '+str(i+1),i,bushm) for i in range(2)]
    shrub_count=0
    for x,y,z,h in placements[::7]:
        if shrub_count>=105:break
        xx=x+rng.uniform(-4,4);yy=y+rng.uniform(-4,4)
        if _protected(xx,yy):continue
        hit=ground(xx,yy)
        if hit and hit[0]>1.4 and hit[1].z>.75:
            size=rng.uniform(1.3,3.2);_instance('Sottobosco esteso | arbusto',rng.choice(bushes),shores,(xx,yy,hit[0]-.08),(size,size,size*rng.uniform(.7,1.1)),rng.random()*math.tau);shrub_count+=1
    rockmat=bpy.data.materials.get('rock') or _material('Paesaggio | roccia',(.20,.23,.20))
    rocks=[_rock_mesh('Masso | variante '+str(i+1),i,rockmat) for i in range(4)]
    # Gruppi localizzati, mai una fila periodica attorno alle scogliere.
    candidates=[]
    for cx,cy in [(226,-195),(201,-57),(212,97),(160,215),(-72,-236),(-120,-360),(-70,-710),(476,-811),(710,-610),(847,-200),(856,165),(904,420),(700,702),(330,618)]:
        for j in range(80):
            x=cx+rng.gauss(0,32);y=cy+rng.gauss(0,32)
            if _protected(x,y):continue
            hit=ground(x,y)
            if hit and .1<hit[0]<9 and hit[1].z>.45:candidates.append((x,y,hit[0],hit[1]))
    rng.shuffle(candidates);rock_count=0;rock_xy=[]
    for x,y,z,n in candidates:
        if rock_count>=120:break
        if any((x-a)**2+(y-b)**2<9 for a,b in rock_xy):continue
        size=rng.uniform(1.1,4.0);_instance('Riva | masso isolato',rng.choice(rocks),shores,(x,y,z-.22),(size*rng.uniform(.8,1.2),size*rng.uniform(.8,1.2),size*rng.uniform(.50,.95)),rng.random()*math.tau);rock_count+=1;rock_xy.append((x,y))
    # Canneti soltanto in due o tre insenature dolci: geometria riunita in un oggetto.
    reedmat=_material('Paesaggio | canne',(.115,.143,.046));reedtops=_material('Paesaggio | spighe',(.13,.077,.030));reed=Shape();tufts=0
    for cx,cy in [(-120,-435),(-55,-710),(570,-777),(820,120)]:
        local=0
        for _ in range(250):
            if local>=16:break
            x=cx+rng.gauss(0,35);y=cy+rng.gauss(0,35);hit=ground(x,y)
            if hit is None or not .30<hit[0]<2.3 or hit[1].z<.88:continue
            z=hit[0];local+=1;tufts+=1
            for j in range(rng.randint(7,11)):
                xx=x+rng.uniform(-.65,.65);yy=y+rng.uniform(-.65,.65);stem_hit=ground(xx,yy);stem_z=stem_hit[0] if stem_hit else z;h=rng.uniform(1.2,2.2);lean=Vector((rng.uniform(-.20,.20),rng.uniform(-.20,.20),0));a=Vector((xx,yy,stem_z-.06));b=a+lean+Vector((0,0,h))
                reed.tube(a,b,.035,.018,4,0)
                if j%2==0:reed.tube(b-Vector((0,0,.23)),b+Vector((0,0,.08)),.075,.06,5,1)
                for off in [.4,.65]:
                    p=a.lerp(b,off);dd=Vector((math.cos(j*2.4),math.sin(j*2.4),.3));q=p+dd*rng.uniform(.5,.9)
                    reed.add([p,q+Vector((0,0,.12)),q+Vector((.04,.02,0))],[(0,1,2)],0)
    if reed.f:
        ob=bpy.data.objects.new('Rive | canneti delle anse',reed.mesh('Canne riunite',[reedmat,reedtops]));shores.objects.link(ob)
    new=list(forest.objects)+list(shores.objects)
    evaluated=sum(len(o.data.polygons) for o in new if o.type=='MESH')
    if len(new)>1400 or evaluated>1000000:raise RuntimeError('Vegetazione oltre il limite concordato')
    result={'trees':len(placements),'tree_variants':len(prototypes),'shrubs':shrub_count,'shore_rocks':rock_count,'reed_tufts':tufts,'new_objects':len(new),'evaluated_faces':evaluated,'hidden_previous':hidden,'ground_objects':ground_names,'all_grounded_by_raycast':True}
    bpy.context.scene['Paesaggio | boschi']='Boschi per macchie e radure, alberi a mesh condivisa; rive con massi discontinui e pochi canneti.'
    return result
