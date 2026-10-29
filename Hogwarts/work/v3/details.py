"""Dettagli architettonici aggiunti al modello HBP esistente.
Non altera volumi o disposizione; non salva né avvia rendering.
"""
import bpy, math, sys
from pathlib import Path
from mathutils import Vector
ROOT=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca')
sys.path.insert(0,str(ROOT/'work/v2'))
import architecture as A
UP=Vector((0,0,1))

class Batch:
    def __init__(self,name,mat): self.name=name;self.mat=mat;self.v=[];self.f=[]
    def geom(self,vs,fs):
        k=len(self.v);self.v.extend([tuple(p) for p in vs]);self.f.extend([tuple(k+i for i in f) for f in fs])
    def beam(self,a,b,r,n=6):
        a,b=Vector(a),Vector(b);d=b-a
        if d.length<.0001:return
        d.normalize();ref=UP if abs(d.z)<.95 else Vector((0,1,0));u=d.cross(ref).normalized();v=d.cross(u).normalized()
        pts=[p+r*(math.cos(i*2*math.pi/n)*u+math.sin(i*2*math.pi/n)*v) for p in (a,b) for i in range(n)]
        self.geom(pts,[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)])
    def box(self,p,t,n,w,dep,h):
        p,t,n=Vector(p),Vector(t),Vector(n);a=w/2;b=dep/2;c=h/2
        self.geom([p+u*t+v*n+z*UP for u,v,z in [(-a,-b,-c),(a,-b,-c),(a,b,-c),(-a,b,-c),(-a,-b,c),(a,-b,c),(a,b,c),(-a,b,c)]],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
    def finish(self):
        if not self.f:return None
        obj=A.mesh(self.name,self.v,self.f,self.mat)
        # Proiezione metrica per materiale, anche quando il modulo materiali è già passato.
        uv=obj.data.uv_layers.new(name='Dettagli • metri')
        for poly in obj.data.polygons:
            no=poly.normal
            t=Vector((1,0,0)) if abs(no.z)>.8 else Vector((-no.y,no.x,0)).normalized()
            v=no.cross(t).normalized()
            for li in poly.loop_indices:
                co=obj.data.vertices[obj.data.loops[li].vertex_index].co
                uv.data[li].uv=(co.dot(t),co.dot(v))
        obj['Dettaglio aggiunto']='Geometria di finitura; disposizione del castello invariata'
        return obj

def _setup():
    keys=['stone','trim','roof','roofline','window','glass','wood','path','grass','rock','water','gold','base']
    A.M={k:bpy.data.materials[k] for k in keys if bpy.data.materials.get(k)}
    if 'Ferro brunito • dettagli' not in bpy.data.materials:
        m=A.material('Ferro brunito • dettagli',(.025,.032,.031),.36,.72)
        p=m.node_tree.nodes.get('Principled BSDF');noise=m.node_tree.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=11
        bump=m.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.15;bump.inputs['Distance'].default_value=.025
        m.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);m.node_tree.links.new(bump.outputs['Normal'],p.inputs['Normal'])
    A.M['iron']=bpy.data.materials['Ferro brunito • dettagli']
    if 'Piombo • vetrate' not in bpy.data.materials:A.material('Piombo • vetrate',(.09,.105,.10),.42,.48)
    if 'Terracotta • comignoli' not in bpy.data.materials:A.material('Terracotta • comignoli',(.18,.075,.034),.78)
    A.M['lead']=bpy.data.materials['Piombo • vetrate'];A.M['clay']=bpy.data.materials['Terracotta • comignoli']
    if 'Vetro ambrato • lanterne' not in bpy.data.materials:
        m=A.material('Vetro ambrato • lanterne',(.37,.15,.025),.3)
        p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(1,.40,.065,1);p.inputs['Emission Strength'].default_value=.7
    A.M['warm']=bpy.data.materials['Vetro ambrato • lanterne']


def _panel_frame(obj):
    vs=[obj.matrix_world@v.co for v in obj.data.vertices]
    if len(vs)<10:return None
    a,b=vs[0],vs[1];t=b-a
    if t.length<.4 or abs(t.z)>.01:return None
    w=t.length;t.normalize();n=t.cross(UP).normalized();p=(a+b)*.5;h=max(v.z for v in vs)-min(v.z for v in vs)
    if h<1:return None
    return p,t,n,w,h

def _top(w,h,u):
    # Profilo ogivale identico alla finestra originale.
    u=abs(u);return h-.8660254038*w+math.sqrt(max(0,w*w-(u+w/2)**2))

def _lead_segment(batch,p,t,n,w,h,u0,v0,u1,v1,r=.022):
    # La losanga è retta: un solo segmento ritagliato, non decine di cilindretti.
    def valid(s):
        u=u0+(u1-u0)*s;v=v0+(v1-v0)*s
        return abs(u)<w/2-.04 and .06<v<_top(w,h,u)-.07
    N=32;ts=[i/N for i in range(N+1) if valid(i/N)]
    if not ts:return
    lo=max(0,ts[0]-1/N);hi=ts[0]
    for _ in range(12):
        mid=(lo+hi)/2
        if valid(mid):hi=mid
        else:lo=mid
    start=hi;lo=ts[-1];hi=min(1,ts[-1]+1/N)
    for _ in range(12):
        mid=(lo+hi)/2
        if valid(mid):lo=mid
        else:hi=mid
    end=lo
    def point(s):return p+t*(u0+(u1-u0)*s)+UP*(v0+(v1-v0)*s)+n*.035
    if end-start>.0001:batch.beam(point(start),point(end),r,5)


def windows():
    A.collection('30 • Dettagli delle finestre')
    trim=Batch('Finestre | modanature esterne e davanzali','trim')
    lead=Batch('Vetrate | reticolo in piombo','lead')
    tracery=Batch('Vetrate | trafori gotici','trim')
    source=[o for o in list(bpy.data.objects) if o.type=='MESH' and ' | vetro' in o.name and _panel_frame(o)]
    counts={'finestre_rifinite':0,'vetrate_con_piombo':0}
    for ob in source:
        p,t,n,w,h=_panel_frame(ob)
        # Abbaini e finestre minuscole restano sottili; bordi dimensionalmente coerenti.
        radius=max(.045,min(.095,w*.045));depth=max(.11,min(.24,w*.065))
        pts=A.arch_points(w+.15,h+.20)
        out=[p+n*depth+t*u+UP*(v-.07) for u,v in pts]
        for a,b in zip(out,out[1:]+out[:1]):trim.beam(a,b,radius,6)
        trim.box(p+n*(depth*.6)-UP*.17,t,n,w+.55,.52,.28)
        # Un secondo listello introduce una vera ombra nella strombatura.
        if w>1.8 and h>4:
            pts=A.arch_points(w+.35,h+.34);out=[p+n*(depth-.10)+t*u+UP*(v-.12) for u,v in pts]
            for a,b in zip(out,out[1:]+out[:1]):trim.beam(a,b,radius*.65,6)
        counts['finestre_rifinite']+=1
        if w<1.7 or h<5:continue
        counts['vetrate_con_piombo']+=1
        # Piccole lastre a losanga, più fini delle esistenti traverse portanti.
        pitch=.85 if w<4 else 1.0
        for sign in [-1,1]:
            for k in range(-int(w/pitch)-2,int((h+w)/pitch)+2):
                c=k*pitch
                _lead_segment(lead,p,t,n,w,h,-w/2,c+sign*(-w/2),w/2,c+sign*(w/2),.021 if w<4 else .028)
        if w>5 and h>12:
            spring=h-w*.90
            for u in [-w*.24,0,w*.24]:
                hh=_top(w,h,u)-.6
                tracery.beam(p+t*u+UP*.15+n*.11,p+t*u+UP*hh+n*.11,.10,8)
            # Rosone a quattro foglie nel tratto superiore.
            cz=h-w*.55;r=w*.14
            for j in range(4):
                aa=j*math.pi/2;c=p+t*(r*.70*math.cos(aa))+UP*(cz+r*.70*math.sin(aa))+n*.14
                for i in range(20):
                    a=i*2*math.pi/20;b=(i+1)*2*math.pi/20
                    tracery.beam(c+t*(r*.57*math.cos(a))+UP*(r*.57*math.sin(a)),c+t*(r*.57*math.cos(b))+UP*(r*.57*math.sin(b)),.065,6)
    for b in [trim,lead,tracery]:b.finish()
    return counts


def _ring(batch,p,t,n,r,tube=.05):
    p=Vector(p);t=Vector(t)
    for i in range(28):
        a=i*2*math.pi/28;b=(i+1)*2*math.pi/28
        batch.beam(p+t*(r*math.cos(a))+UP*(r*math.sin(a)),p+t*(r*math.cos(b))+UP*(r*math.sin(b)),tube,7)


def _door(planks,metal,p,t,n,w,h,arched=True):
    p,t,n=Vector(p),Vector(t),Vector(n);cols=max(5,round(w/.43));pw=w/cols
    for i in range(cols):
        u=-w/2+(i+.5)*pw
        hh=min(_top(w,h,u-pw/2+.02),_top(w,h,u+pw/2-.02)) if arched else h
        planks.box(p+t*u+UP*hh/2+n*.045,t,n,pw-.025,.13,hh)
    metal.box(p+UP*h*.5+n*.15,t,n,.065,.045,h)
    for level in [.22,.67]:
        z=h*level
        for s in [-1,1]:
            uu=s*w*.25
            metal.box(p+t*uu+UP*z+n*.15,t,n,w*.43,.095,.16)
            # Tre borchie per ferramenta.
            for j in [-1,0,1]:
                q=p+t*(uu+j*w*.13)+UP*z+n*.23;metal.beam(q-n*.04,q+n*.06,.09,10)
    for u in [-w*.16,w*.16]:
        q=p+t*u+UP*h*.39+n*.23;_ring(metal,q,t,n,min(.26,w*.07),.055)
        metal.beam(q+UP*.25-n*.06,q+UP*.25+n*.05,.11,10)


def doors_and_lanterns():
    A.collection('31 • Portali, ferramenta e lanterne')
    planks=Batch('Portali | assi di rovere','wood');iron=Batch('Portali | cerniere e battenti','iron');metal=Batch('Lanterne | ferro brunito','iron');glass=Batch('Lanterne | vetri ambrati','warm');shields=Batch('Ingresso | stemmi scolpiti','trim')
    orig=bpy.data.objects.get('Portale della Sala Grande')
    lantern_positions=[]
    if orig:
        dat=_panel_frame(orig)
        if dat:
            p,t,n,w,h=dat;_door(planks,iron,p+n*.12,t,n,w-.1,h-.1)
            for s in [-1,1]:lantern_positions.append((p+t*s*(w/2+1.0)+UP*h*.45+n*.30,t,n))
    x,y=A.xy(.6265,.571);front=y-.050*382/2-.12
    # Battenti aperti lungo le spalle: il passaggio centrale resta libero.
    for s in [-1,1]:
        hinge=Vector((x+s*4.7,front+.35,60.25));t=Vector((-s*.12,.9928,0));n=t.cross(UP).normalized()
        _door(planks,iron,hinge+t*2.1,t,n,4.2,16,False)
        lantern_positions.append((Vector((x+s*6.2,front-.35,66.4)),Vector((1,0,0)),Vector((0,-1,0))))
        # Scudo liscio a quarti; nessun testo o marchio inventato.
        c=Vector((x+s*10,front-.32,88.5));T=Vector((1,0,0));N=Vector((0,-1,0))
        poly=[(-1.25,1.8),(1.25,1.8),(1.18,-.8),(0,-2),(-1.18,-.8)]
        vs=[c+T*u+UP*v+N*d for d in [0,.3] for u,v in poly]
        shields.geom(vs,[(4,3,2,1,0),(5,6,7,8,9)]+[(i,(i+1)%5,(i+1)%5+5,i+5) for i in range(5)])
        iron.box(c+N*.34,T,N,.085,.035,2.8);iron.box(c+UP*.2+N*.34,T,N,2.0,.035,.085)
    x,y=A.xy(.382,.7105);front=x-.036*600/2
    for s in [-1,1]:lantern_positions.append((Vector((front-.35,y+s*5.8,77.2)),Vector((0,1,0)),Vector((-1,0,0))))
    # Lampade appese a bracci di ferro, con gabbia e cappello piramidale.
    for p,t,n in lantern_positions:
        metal.beam(p-n*.25,p+n*.65,.09,8);q=p+n*.60-UP*.55
        glass.box(q,t,n,.48,.48,.72)
        for u in [-.3,.3]:
            for v in [-.3,.3]:metal.beam(q+t*u+n*v-UP*.45,q+t*u+n*v+UP*.45,.045,6)
        for zz in [-.45,.45]:metal.box(q+UP*zz,t,n,.70,.70,.08)
        vs=[q+t*u+n*v+UP*.49 for u,v in [(-.42,-.42),(.42,-.42),(.42,.42),(-.42,.42)]]+[q+UP*.95]
        metal.geom(vs,[(0,1,4),(1,2,4),(2,3,4),(3,0,4)])
        _ring(metal,p+n*.60-UP*.02,t,n,.13,.04)
    for b in [planks,iron,metal,glass,shields]:b.finish()
    return {'porte_rifinite':3,'lanterne':len(lantern_positions),'stemmi':2}


def roofs():
    A.collection('32 • Gronde, colmi e comignoli')
    gutter=Batch('Tetti | grondaie e pluviali','iron');ridge=Batch('Tetti | copertine di colmo','roofline');brackets=Batch('Tetti | staffe delle gronde','iron');chimneys=Batch('Comignoli | muratura','stone');caps=Batch('Comignoli | cappelli','trim');pots=Batch('Comignoli | terminali in cotto','clay')
    candidates=[]
    for ob in list(bpy.data.objects):
        if ob.type!='MESH' or len(ob.data.vertices)!=6 or not ob.data.materials:continue
        if ob.data.materials[0].name!='roof':continue
        vs=[ob.matrix_world@v.co for v in ob.data.vertices]
        if abs(vs[4].z-vs[5].z)>.01:continue
        L=(vs[1]-vs[0]).length;W=(vs[3]-vs[0]).length;H=vs[4].z-vs[0].z
        if L<13 or W<5 or H<3:continue
        candidates.append((ob,vs,L,W,H))
    for ob,vs,L,W,H in candidates:
        t=(vs[1]-vs[0]).normalized();n=(vs[3]-vs[0]).normalized();z=vs[0].z
        # Semi-canale aperto e staffe ripetute lungo entrambe le gronde.
        for ia,ib,side in [(0,1,-1),(3,2,1)]:
            a=vs[ia]+n*side*.15+UP*.05;b=vs[ib]+n*side*.15+UP*.05
            segs=max(2,int(L/3));r=.17;verts=[];faces=[]
            for j in range(segs+1):
                p=a+(b-a)*j/segs
                for k in range(9):
                    theta=math.pi+math.pi*k/8;verts.append(p+n*r*math.cos(theta)+UP*r*math.sin(theta))
            for j in range(segs):
                for k in range(8):q=j*9+k;faces.append((q,q+1,q+10,q+9))
            gutter.geom(verts,faces)
            for j in range(segs+1):
                p=a+(b-a)*j/segs;brackets.beam(p-n*.25,p+n*.25,.035,6)
            base=73 if ob.name.startswith('Quad') else 70 if 'Orologio' in ob.name or 'Infermeria' in ob.name else 60 if any(v in ob.name for v in ['Sala Grande','ingresso','viadotto','Ingresso']) else 55
            if z-base>10:
                # Un pluviale per fronte, all'estremità meno ingombrante.
                p=a+t*.65+n*side*.10;mid=p-UP*.8-n*side*.30;end=Vector((mid.x,mid.y,base+.8))
                gutter.beam(p,mid,.11,10);gutter.beam(mid,end,.11,10);gutter.beam(end,end+n*side*.55-UP*.3,.11,10)
        # Coppi/lastre angolari segmentati sul colmo con spessore reale.
        rr=vs[4]+UP*.12;d=vs[5]-vs[4];N=max(2,int(L/.85));slope=H/(W/2)
        for i in range(N):
            c=rr+d*(i+.5)/N;hl=L/N*.48;cross=[(-.40,-.40*slope+.08),(0,.11),(.40,-.40*slope+.08),(.40,-.40*slope-.015),(0,.015),(-.40,-.40*slope-.015)]
            ridge.geom([c+t*along+n*uu+UP*zz for along in [-hl,hl] for uu,zz in cross],[(5,4,3,2,1,0),(6,7,8,9,10,11)]+[(j,(j+1)%6,(j+1)%6+6,j+6) for j in range(6)])
        # Piccoli gruppi di camini su quattro ali, lasciando libere le guglie.
        if any(k in ob.name for k in ['Quad | ala nord','Quad | ala ovest','Ala occidentale Durham','Galleria lunga']):
            for frac in [.22,.77]:
                q=vs[4]+d*frac-UP*1.1
                chimneys.box(q+UP*2.3,t,n,1.45,1.7,4.6)
                caps.box(q+UP*4.65,t,n,1.9,2.05,.45)
                for off in [-.40,.40]:
                    pp=q+t*off+UP*4.87;pots.beam(pp,pp+UP*1.25,.25,12);caps.beam(pp+UP*1.15,pp+UP*1.35,.31,12)
    for b in [gutter,ridge,brackets,chimneys,caps,pots]:b.finish()
    return {'coperture_rifinite':len(candidates)}


def apply():
    _setup();before=set(bpy.data.objects)
    results={};results.update(windows());results.update(doors_and_lanterns());results.update(roofs())
    new=[o for o in bpy.data.objects if o not in before]
    results['oggetti_aggiunti']=len(new);results['facce_aggiunte']=sum(len(o.data.polygons) for o in new if o.type=='MESH')
    bpy.context.scene['Dettagli V3']='Modanature profonde e davanzali, vetrate a piombo, assi/ferramenta, porte aperte, lanterne, gronde, pluviali, colmi e comignoli. Gruppi geometrici separati.'
    return results
