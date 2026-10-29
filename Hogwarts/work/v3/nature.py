"""Vegetazione tridimensionale e dettagli di paesaggio per Hogwarts.
Applicare a una copia della scena HBP caricata. Nessuna risorsa esterna.
"""
import bpy,math,random,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca')
sys.path.insert(0,str(ROOT/'work/v2'))
import architecture as A

class Batch:
    def __init__(self,name,mats): self.name=name;self.mats=mats;self.v=[];self.f=[];self.mi=[]
    def face(self,pts,mi=0):
        k=len(self.v);self.v.extend(pts);self.f.append(tuple(range(k,k+len(pts))));self.mi.append(mi)
    def shape(self,vs,fs,mi=0):
        k=len(self.v);self.v.extend(vs);self.f.extend(tuple(k+j for j in f) for f in fs);self.mi.extend([mi]*len(fs))
    def make(self):
        if not self.f:return None
        ob=A.mesh(self.name,self.v,self.f,None)
        for m in self.mats: ob.data.materials.append(m)
        for p,mi in zip(ob.data.polygons,self.mi):p.material_index=mi
        return ob

def _mat(name,c,rough=.86):
    m=bpy.data.materials.get(name) or A.material(name,c,rough)
    m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
    p.inputs['Roughness'].default_value=rough
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=5;noise.inputs['Detail'].default_value=2
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.2;ramp.color_ramp.elements[0].color=(*[x*.6 for x in c],1)
    ramp.color_ramp.elements[1].position=.8;ramp.color_ramp.elements[1].color=(*[min(1,x*1.25) for x in c],1)
    coord=n.new('ShaderNodeTexCoord');l.new(coord.outputs['Object'],noise.inputs['Vector']);l.new(noise.outputs['Fac'],ramp.inputs['Fac']);l.new(ramp.outputs['Color'],p.inputs['Base Color'])
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.04;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
    return m

def tube(batch,a,b,r1,r2=None,n=7,mi=0):
    a=Vector(a);b=Vector(b);d=b-a
    if d.length<.001:return
    d.normalize();u=d.cross(Vector((0,0,1)))
    if u.length<.1:u=d.cross(Vector((0,1,0)))
    u.normalize();v=d.cross(u);r2=r1 if r2 is None else r2
    vs=[tuple(p+r*(u*math.cos(j*2*math.pi/n)+v*math.sin(j*2*math.pi/n))) for p,r in [(a,r1),(b,r2)] for j in range(n)]
    fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    batch.shape(vs,fs,mi)

def _leaf(batch,start,direction,length,width,mi=0):
    # Lamina curva, con nervatura centrale sollevata: due file di triangoli.
    p=Vector(start);d=Vector(direction).normalized();side=d.cross(Vector((0,0,1)))
    if side.length<.05:side=Vector((1,0,0))
    side.normalize();vs=[]
    for f,w in [(0,0),(.23,.75),(.58,1),(.82,.57),(1,0)]:
        mid=p+d*length*f+Vector((0,0,length*.19*math.sin(f*math.pi)))
        vs.extend([tuple(mid-side*width*w/2),tuple(mid+Vector((0,0,width*.10))),tuple(mid+side*width*w/2)])
    fs=[]
    for i in range(4):
        k=i*3;fs.extend([(k,k+3,k+4),(k,k+4,k+1),(k+1,k+4,k+5),(k+1,k+5,k+2)])
    batch.shape(vs,fs,mi)

def fir(x,y,z,h,phase,rng,bark,needles):
    tube(bark,(x,y,z-.15),(x+.04*h,y-.02*h,z+h*.98),h*.026,h*.005,8)
    # Otto palchi di rami diseguali, con lobi pendenti: niente silhouette a cono unico.
    tiers=8
    for tier in range(tiers):
        t=.16+tier*.098;zz=z+h*t;r=h*(.23*(1-t)+.026)*rng.uniform(.90,1.1);hh=h*.25
        n=15;ph=phase+tier*.75;vs=[]
        for level,rr,up in [(0,r,-h*.04),(1,r*.60,hh*.30),(2,r*.12,hh*.75)]:
            for j in range(n):
                a=ph+2*math.pi*j/n;sc=(1+.16*math.sin(j*4.6+tier))*(rng.uniform(.92,1.06))
                droop=-h*.025*(.5+.5*math.sin(j*2.4)) if level==0 else 0
                vs.append((x+rr*sc*math.cos(a),y+rr*sc*math.sin(a),zz+up+droop))
        fs=[]
        for lev in range(2):
            for j in range(n):
                k=lev*n+j;kk=lev*n+(j+1)%n;fs.extend([(k,kk,k+n),(kk,kk+n,k+n)])
        fs.append(tuple(range(2*n,3*n)))
        needles.shape(vs,fs,(tier+rng.randrange(3))%len(needles.mats))
        # Rami inferiori visibili e spruzzi aghiformi alle estremità.
        if tier<6:
            for j in range(5):
                aa=ph+j*2*math.pi/5;d=Vector((math.cos(aa),math.sin(aa),-.12));end=Vector((x,y,zz))+d*r*.98
                tube(bark,(x,y,zz+.13*h),end,h*.007,h*.0025,5)
                for k in range(3):
                    anchor=Vector((x,y,zz+.11*h))+(end-Vector((x,y,zz+.11*h)))*(.45+.17*k)
                    lateral=Vector((-math.sin(aa),math.cos(aa),.14))
                    for s in [-1,1]:
                        dd=(d*.5+lateral*s).normalized();ln=h*(.06+.025*(2-k))
                        # Tre aghi laminari compongono la punta del ramo.
                        for off in [-.25,0,.25]:
                            q=anchor+Vector((0,0,off*h*.017));p1=q+dd*ln;p2=q+d*(ln*.7)
                            needles.face([tuple(q),tuple(p1+Vector((0,0,ln*.07))),tuple(p2)],rng.randrange(len(needles.mats)))
    # Apice sottile separato dai palchi.
    p=(x+.04*h,y-.02*h,z+h)
    for j in range(7):
        a=phase+j*2*math.pi/7
        needles.face([(x+math.cos(a)*h*.045,y+math.sin(a)*h*.045,z+h*.85),(x+math.cos(a+.6)*h*.035,y+math.sin(a+.6)*h*.035,z+h*.87),p],j%len(needles.mats))


def apply():
    rng=random.Random(509)
    for key in ['stone','trim','roof','roofline','window','glass','wood','path','grass','rock','water','gold','base']:
        if bpy.data.materials.get(key):A.M[key]=bpy.data.materials[key]
    leaf=[_mat('Fogliame | abete scuro',(.018,.056,.025)),_mat('Fogliame | abete verde',(.030,.078,.036)),_mat('Fogliame | germogli',(.055,.105,.040))]
    bushm=[_mat('Fogliame | arbusti',(.054,.10,.027)),_mat('Fogliame | foglie chiare',(.09,.145,.048))]
    barkmat=_mat('Corteccia | bruno scuro',(.065,.036,.018));potmat=_mat('Vasi | terracotta',(.24,.083,.040));soilmat=_mat('Terra | umida',(.030,.018,.011));mossmat=_mat('Muschio | velluto',(.040,.080,.026))
    bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
    terrain=bpy.data.objects.get('Colline occidentali | superficie');bv=BVHTree.FromObject(terrain,dg) if terrain else None
    def ground(x,y,fallback=0):
        if bv:
            hit=bv.ray_cast(Vector((x,y,300)),Vector((0,0,-1)))
            if hit[0] is not None:return hit[0].z
        return fallback
    A.collection('32 • Bosco di conifere dettagliate')
    bark=Batch('Conifere | tronchi e rami',[barkmat]);needles=Batch('Conifere | palchi e aghi',leaf)
    original=bpy.data.objects.get('Bosco sulle colline');positions=[]
    if original:
        v=original.data.vertices
        for i in range(0,len(v),8):
            if i+7>=len(v):break
            ring=[original.matrix_world@v[i+j].co for j in range(7)];tip=original.matrix_world@v[i+7].co
            x=sum(p.x for p in ring)/7;y=sum(p.y for p in ring)/7
            h=(tip.z-sum(p.z for p in ring)/7)/.82;z=ground(x,y,tip.z-h)
            positions.append((x,y,z,h))
        original.hide_render=True;original.hide_set(True)
    for x,y,z,h in positions:fir(x,y,z,h*rng.uniform(1.05,1.28),rng.random()*6.28,rng,bark,needles)
    bark.make();needles.make()
    A.collection('33 • Sottobosco, muschio e rocce')
    bushes=Batch('Sottobosco | fogliame',bushm);stems=Batch('Sottobosco | ramoscelli',[barkmat]);moss=Batch('Sottobosco | muschio a terra',[mossmat])
    for x,y,z,h in positions[::2]:
        xx=x+rng.uniform(-2.8,2.8);yy=y+rng.uniform(-2.8,2.8);zz=ground(xx,yy,z)
        for j in range(8):
            a=rng.random()*6.28;rr=rng.uniform(.15,.65);base=(xx+rr*math.cos(a),yy+rr*math.sin(a),zz-.05);top=(base[0]+rng.uniform(-.25,.25),base[1]+rng.uniform(-.25,.25),zz+rng.uniform(.5,1.3))
            tube(stems,base,top,.025,.008,5)
            for k in range(3):_leaf(bushes,Vector(base).lerp(Vector(top),.35+.25*k),(math.cos(a+k*1.4),math.sin(a+k*1.4),.2),rng.uniform(.35,.75),.20,k%2)
        radius=rng.uniform(.55,1.25);poly=[]
        for j in range(13):
            a=j*2*math.pi/13;r=radius*rng.uniform(.7,1.2);px=xx+r*math.cos(a);py=yy+r*math.sin(a);poly.append((px,py,ground(px,py,zz)+.018))
        center=(xx,yy,ground(xx,yy,zz)+.02)
        for j in range(13):moss.face([center,poly[j],poly[(j+1)%13]])
    bushes.make();stems.make();moss.make()
    # Piccoli massi radicati lungo il piede delle scogliere, non disseminati sui ponti.
    rocks=Batch('Rocce | detriti di riva',[A.M['rock']]);rock_count=0
    for ob in list(bpy.data.objects):
        if ob.type!='MESH' or not ob.name.startswith('Promontorio') or 'pareti rocciose' not in ob.name:continue
        low=[ob.matrix_world@v.co for v in ob.data.vertices if v.co.z<2.01]
        for idx in range(1,len(low),6):
            p=low[idx];r=rng.uniform(.8,2.1);hh=rng.uniform(1.0,2.7);n=7;vs=[]
            for zz,rr in [(.15,r*.8),(.15+hh*.40,r),(.15+hh,r*.40)]:
                for j in range(n):
                    a=j*2*math.pi/n;sc=rng.uniform(.8,1.2);vs.append((p.x+rr*sc*math.cos(a),p.y+rr*sc*math.sin(a),zz))
            fs=[tuple(range(2*n,3*n))]
            for k in range(2):
                for j in range(n):a=k*n+j;b=k*n+(j+1)%n;fs.extend([(a,b,a+n),(b,b+n,a+n)])
            rocks.shape(vs,fs);rock_count+=1
    rocks.make()
    A.collection('34 • Erbologia, vasi e piante nelle serre')
    pots=Batch('Erbologia | vasi di terracotta',[potmat]);soil=Batch('Erbologia | terreno nei vasi',[soilmat]);stalks=Batch('Erbologia | steli',[barkmat]);plants=[];pot_count=0
    greenhouse_specs=[(.578,.220,36.6,7.258,0),(.578,.250,36.6,7.258,0),(.672,.220,36.6,7.258,0),(.672,.250,36.6,7.258,0),(.679,.313,32.852,7.8,math.pi/2),(.699,.313,32.852,7.8,math.pi/2),(.679,.407,32.852,7.8,math.pi/2),(.699,.407,32.852,7.8,math.pi/2),(.568,.276,27.6,4.584,0)]
    for gi,(u,v,length,width,angle) in enumerate(greenhouse_specs,1):
        leaves=Batch('Serra '+str(gi)+' | piante di Erbologia',bushm+leaf[:1]);cx,cy=A.xy(u,v);co=math.cos(angle);si=math.sin(angle)
        for row in [-1,1]:
            for j in range(7):
                px=-length/2+3+(length-6)*j/6;py=row*width*.28;x=cx+px*co-py*si;y=cy+px*si+py*co;z=56.3;r=rng.uniform(.32,.48);h=rng.uniform(.5,.7);n=10
                vs=[(x+rr*math.cos(k*2*math.pi/n),y+rr*math.sin(k*2*math.pi/n),zz) for rr,zz in [(r*.65,z),(r,z+h)]]
                pots.shape(vs,[(k,(k+1)%n,(k+1)%n+n,k+n) for k in range(n)])
                rim=[]
                for rr in [r,r*.84]:rim.extend([(x+rr*math.cos(k*2*math.pi/n),y+rr*math.sin(k*2*math.pi/n),z+h) for k in range(n)])
                pots.shape(rim,[(k,(k+1)%n,(k+1)%n+n,k+n) for k in range(n)])
                soil.face([(x+r*.82*math.cos(k*2*math.pi/n),y+r*.82*math.sin(k*2*math.pi/n),z+h-.07) for k in range(n)])
                ph=rng.uniform(1.3,2.8);tube(stalks,(x,y,z+h-.1),(x,y,z+h+ph),.04,.015,6)
                for k in range(9):
                    aa=k*2.399+gi;frac=.15+.075*k
                    _leaf(leaves,(x,y,z+h+ph*frac),(math.cos(aa),math.sin(aa),.2 if k<5 else .5),rng.uniform(.5,1.25),rng.uniform(.16,.34),k%3)
                pot_count+=1
        plants.append(leaves.make())
    # Conservatorio: felci e foglie larghe sotto la cupola.
    dome=Batch('Conservatorio | piante tropicali',bushm+leaf[:1]);cx,cy=A.xy(.625,.198)
    for j in range(10):
        a=j*2*math.pi/10;rr=3.6;x=cx+rr*math.cos(a);y=cy+rr*math.sin(a);z=56.3;h=rng.uniform(2.7,4.0)
        tube(stalks,(x,y,z),(x,y,z+h),.09,.035,7)
        for k in range(10):
            aa=k*2.399+j;_leaf(dome,(x,y,z+h*(.25+k*.065)),(math.cos(aa),math.sin(aa),.15),rng.uniform(1.0,1.75),rng.uniform(.3,.55),k%3)
    dome.make();pots.make();soil.make();stalks.make()
    report={'conifere':len(positions),'massi_riva':rock_count,'vasi_serre':pot_count,'serre_con_piante':len(plants),'conservatori_con_piante':1,'resources_external':0}
    bpy.context.scene['Vegetazione V3']=str(report)
    return report
