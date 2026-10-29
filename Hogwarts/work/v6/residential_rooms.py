"""Grifondoro, ufficio di Silente e osservatorio integrati nel castello.
apply() aggiunge arredi, solai separati, luci e camere, senza salvare il file.
"""
import bpy, math, random
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt
import interior_kit as I

TAU=2*math.pi


def _xy(r,a):return r*math.cos(a),r*math.sin(a)

def _disc_floor(name,r,z,mat='int_oak',inner=0,stair_slot=False):
    """Solaio a celle radiali; il settore SE della scala resta realmente vuoto."""
    n=144;rings=[inner,max(inner,.01),4.,6.8,r] if stair_slot else ([inner,r] if inner else [0.001,r])
    rings=sorted(set(q for q in rings if 0<=q<=r));verts=[]
    for zz in [z-.16,z]:
        for rr in rings:
            for j in range(n):verts.append((rr*math.cos(TAU*j/n),rr*math.sin(TAU*j/n),zz))
    stride=len(rings)*n;faces=[];edges={}
    for k in range(len(rings)-1):
        for j in range(n):
            mid=(j+.5)*360/n
            if stair_slot and 285<mid<345 and rings[k]>=4-1e-6 and rings[k+1]<=6.8+1e-6:continue
            a=k*n+j;b=k*n+(j+1)%n;c=(k+1)*n+(j+1)%n;d=(k+1)*n+j
            faces.extend([(a+stride,d+stride,c+stride,b+stride),(b,c,d,a)])
            for u,v in [(a,b),(b,c),(c,d),(d,a)]:
                key=tuple(sorted((u,v)));edges[key]=edges.get(key,0)+1
    for (a,b),num in edges.items():
        if num==1:faces.append((a,b,b+stride,a+stride))
    return I.mesh(name,verts,faces,mat)


def _ring(name,p,r,axis='Z',tube=.025,mat='int_brass',segments=48):
    x,y,z=p
    points=[]
    for j in range(segments+1):
        a=j*TAU/segments
        points.append((x+r*math.cos(a),y+r*math.sin(a),z) if axis=='Z' else ((x+r*math.cos(a),y,z+r*math.sin(a)) if axis=='Y' else (x,y+r*math.cos(a),z+r*math.sin(a))))
    for a,b in zip(points,points[1:]):I.beam(name,a,b,tube,mat,6)


def _cushion(name,p,size,mat='int_red',angle=0):
    return I.box(name,p,size,mat,angle,bevel=min(size)*.2)


def _sofa(name,p,width=2.7,angle=0):
    x,y,z=p;co=math.cos(angle);si=math.sin(angle)
    def q(u,v,w):return(x+u*co-v*si,y+u*si+v*co,z+w)
    for u in [-width/2+.17,width/2-.17]:
        for v in [-.37,.37]:I.box(name+' | piede',q(u,v,.12),(.14,.14,.24),'int_wood',angle)
    I.box(name+' | telaio',q(0,0,.28),(width,.98,.20),'int_wood',angle,bevel=.05)
    for i in range(3):
        u=(i-1)*width/3
        _cushion(name+' | seduta',q(u,-.06,.54),(width/3-.04,.87,.28),'int_red',angle)
        _cushion(name+' | schienale',q(u,.40,.94),(width/3-.05,.25,.80),'int_red',angle)
    for u in [-width/2,width/2]:_cushion(name+' | bracciolo',q(u,0,.72),(.24,1.02,.70),'int_red',angle)
    for u,mat in [(-width*.30,'int_gold'),(width*.28,'int_red')]:_cushion(name+' | cuscino',q(u,.15,.87),(.43,.18,.44),mat,angle+.1)


def _armchair(name,p,angle=0):
    x,y,z=p;co=math.cos(angle);si=math.sin(angle)
    def q(u,v,w):return(x+u*co-v*si,y+u*si+v*co,z+w)
    for u in [-.36,.36]:
        for v in [-.32,.32]:I.box(name+' | piede',q(u,v,.11),(.10,.10,.22),'int_wood',angle)
    _cushion(name+' | seduta',q(0,0,.45),(.78,.75,.32),'int_red',angle)
    _cushion(name+' | schienale',q(0,.32,.88),(.84,.22,.92),'int_red',angle)
    for u in [-.43,.43]:_cushion(name+' | braccio',q(u,0,.65),(.20,.83,.55),'int_red',angle)


def _papers(name,p,angle=0,count=3):
    x,y,z=p
    for i in range(count):I.box(name+' | pergamena',(x+i*.04,y+i*.035,z+i*.008),(.36,.26,.006),'int_paper',angle+i*.10)
    I.beam(name+' | penna',(x+.12,y-.05,z+.04),(x+.42,y+.07,z+.19),.012,'int_white',6)
    I.cone(name+' | calamaio',(x-.25,y+.11,z),.065,.055,.10,'int_iron',12)


def _loose_books(name,p,count=4,angle=0):
    x,y,z=p
    for i in range(count):
        a=angle+math.sin(i*1.7)*.13
        I.box(name+' | volume',(x+.02*i,y,z+.035+i*.075),(.34,.24,.065),'book'+str(i%6),a)
        I.box(name+' | pagine',(x+.02*i,y,z+.068+i*.075),(.30,.21,.012),'int_paper',a)


def _tapestry(name,p,width,height,angle=0):
    x,y,z=p;co=math.cos(angle);si=math.sin(angle)
    I.box(name+' | tessuto',(x,y,z+height/2),(width,.035,height),'int_red',angle)
    for u in [-width/2+.08,width/2-.08]:I.box(name+' | bordo',(x+u*co,y+u*si,z+height/2),(.08,.045,height),'int_gold',angle)
    for zz in [z+.1,z+height-.1]:I.box(name+' | bordo',(x,y,zz),(width,.045,.08),'int_gold',angle)
    I.beam(name+' | asta',(x-width*.58*co,y-width*.58*si,z+height+.12),(x+width*.58*co,y+width*.58*si,z+height+.12),.04,'int_brass',8)
    # Motivo araldico ornamentale, senza copiare un disegno di stemma.
    n=Vector((math.sin(angle),-math.cos(angle),0));t=Vector((co,si,0));center=Vector((x,y,z+height*.53))+n*.04
    vs=[tuple(center+t*u+Vector((0,0,v))) for u,v in [(0,.55),(.38,.12),(.28,-.38),(0,-.62),(-.28,-.38),(-.38,.12)]]
    I.mesh(name+' | medaglione',vs,[tuple(range(6))],'int_gold')


def _fireplace():
    # Fronte rivolto verso il centro della sala; nessuna scatola che chiuda il focolare.
    x,y=0,6.12
    I.box('Grifondoro | soglia del camino',(x,y-.35,.09),(3.2,1.15,.18),'stone',bevel=.03)
    for dx in [-1.27,1.27]:I.box('Grifondoro | piedritto camino',(dx,y,1.08),(.42,.70,2.05),'trim')
    I.arch('Grifondoro | volta del camino',(x,y,.18),2.12,2.17,.7,0,.35,'trim')
    I.box('Grifondoro | cappa',(x,y+.06,3.35),(3.1,.85,1.55),'stone')
    I.box('Grifondoro | mensola camino',(x,y-.08,2.75),(3.55,1.05,.16),'trim',bevel=.04)
    I.box('Grifondoro | fondo focolare',(0,y+.38,1.07),(2.15,.12,1.78),'int_fireblack')
    for dx,zz in [(-.45,.35),(.35,.36),(.05,.51)]:I.beam('Grifondoro | ceppo',(dx-.52,y-.10,zz),(dx+.52,y+.13,zz+.03),.13,'int_wood',9)
    for j in range(7):
        dx=-.65+j*.22;I.cone('Grifondoro | fiamma',(dx,y-.10,.48),.13,.008,.42+.20*math.sin(j*1.4),'int_flame',9)
    I.point('Grifondoro | bagliore del camino',(0,y-.75,1.15),180,(1,.39,.10),.55)
    I.portrait('Grifondoro | ritratto sopra il camino',(0,y-.40,3.0),1.3,1.5,0,0)


def common_room():
    room=I.Room('66 • Sala comune Grifondoro',(-43.2,-26.74,93.2))
    room.part('Pavimenti');_disc_floor('Grifondoro | parquet circolare',7.4,0,'int_oak')
    I.cone('Grifondoro | tappeto tondo',(0,0,.012),2.72,2.72,.025,'int_red',96)
    # Bordo e motivo centrale del tappeto restano completamente calpestabili.
    _ring('Grifondoro | bordo tappeto',(0,0,.045),2.53,tube=.03,mat='int_gold',segments=64)
    _ring('Grifondoro | motivo tappeto',(0,0,.045),1.2,tube=.022,mat='int_gold',segments=48)
    room.part('Arredi');_fireplace()
    _sofa('Grifondoro | divano davanti al fuoco',(0,3.9,0),2.75,math.pi)
    _sofa('Grifondoro | divano laterale',(-4.45,1.65,0),2.45,-math.pi/2)
    _armchair('Grifondoro | poltrona',(4.15,2.0,0),math.pi*.68)
    _armchair('Grifondoro | poltrona di lettura',(-3.5,-3.0,0),-.7)
    I.table('Grifondoro | tavolino del camino',(0,5.02,0),1.55,.66,.43)
    _loose_books('Grifondoro | letture sul tavolo',(-.40,5.0,.49),3)
    I.table('Grifondoro | tavolo di studio',(3.75,-.10,0),1.5,.8,.78,mat='int_wood')
    _papers('Grifondoro | compiti',(3.60,-.1,.84),.25,3)
    I.chair('Grifondoro | sedia di studio',(4.2,-.92,0),'int_wood',math.pi)
    for i,a in enumerate([math.pi,math.radians(218)]):
        x,y=_xy(6.65,a);I.bookcase('Grifondoro | libreria '+str(i+1),(x,y,.06),2.5,3.4,.50,a-math.pi/2,5,41+i)
    for i,a in enumerate([math.radians(20),math.radians(55),math.radians(128),math.radians(250)]):
        x,y=_xy(7.04,a);I.portrait('Grifondoro | ritratto '+str(i+1),(x,y,2.2),.95,1.35,a-math.pi/2,i+1)
    for i,a in enumerate([math.radians(152),math.radians(285)]):
        x,y=_xy(7.05,a);_tapestry('Grifondoro | arazzo '+str(i+1),(x,y,1.0),1.65,3.8,a-math.pi/2)
    room.part('Soffitti');_disc_floor('Grifondoro | soffitto ligneo',7.38,6.4,'int_wood',stair_slot=True)
    # Travi sopra il lato nord, lontane dal vano scala SE.
    for x in [-4,0,4]:
        span=math.sqrt(7.15**2-x*x)
        # La trave orientale si interrompe prima del vano scala SE.
        if x>0:I.box('Grifondoro | trave soffitto',(x,span/2+.2,6.16),(.22,span-.4,.30),'int_oak')
        else:I.box('Grifondoro | trave soffitto',(x,0,6.16),(.22,span*2,.30),'int_oak')
    room.part('Luci');I.area('Grifondoro | luce ambiente',(0,1.2,5.5),(0,0,0),950,5,(1,.72,.43));I.area('Grifondoro | luce lato ingresso',(3.5,-3.6,4.1),(-2,2,1),420,3,(1,.80,.58))
    room.part('Camere');I.camera(room,'Interni | Sala comune Grifondoro',(-4.5,-4.6,2.15),(0,3.25,1.85),21)
    return room.finish()


def _curtain(name,p,width,height,angle=0):
    x,y,z=p;n=20;vs=[]
    for j in range(4):
        zz=z+height*j/3
        for i in range(n+1):
            u=-width/2+width*i/n;v=.045*math.cos(i*math.pi*.7)*(1-.12*j)
            vs.append((x+u*math.cos(angle)-v*math.sin(angle),y+u*math.sin(angle)+v*math.cos(angle),zz))
    fs=[]
    for j in range(3):
        for i in range(n):a=j*(n+1)+i;fs.append((a,a+1,a+n+2,a+n+1))
    return I.mesh(name,vs,fs,'int_red')


def _bed(name,p,angle):
    x,y,z=p;co=math.cos(angle);si=math.sin(angle)
    def q(u,v,w):return(x+u*co-v*si,y+u*si+v*co,z+w)
    I.box(name+' | struttura',q(0,0,.36),(1.42,2.28,.25),'int_wood',angle,bevel=.04)
    I.box(name+' | materasso',q(0,0,.55),(1.30,2.16,.22),'int_white',angle,bevel=.06)
    I.box(name+' | coperta',q(0,-.28,.70),(1.34,1.55,.12),'int_red',angle,bevel=.04)
    _cushion(name+' | cuscino',q(0,.75,.76),(1.04,.43,.20),'int_white',angle)
    I.box(name+' | testiera',q(0,1.08,.94),(1.45,.15,1.1),'int_wood',angle)
    for u in [-.71,.71]:
        for v in [-1.14,1.14]:
            I.beam(name+' | colonna baldacchino',q(u,v,.1),q(u,v,2.72),.065,'int_wood',12)
            I.cone(name+' | pomo',q(u,v,2.7),.10,.02,.19,'int_gold',12)
    I.box(name+' | cielo baldacchino',q(0,0,2.72),(1.58,2.46,.12),'int_red',angle,bevel=.03)
    _curtain(name+' | cortina testiera',q(0,1.14,.50),1.42,2.16,angle)
    for side in [-1,1]:_curtain(name+' | cortina laterale',q(side*.72,.70,.45),.80,2.20,angle+math.pi/2)
    # Baule ai piedi, con due fasce metalliche e serratura.
    c=q(0,-1.62,.28);I.box(name+' | baule',c,(1.20,.55,.50),'int_oak',angle,bevel=.035)
    for u in [-.42,.42]:I.box(name+' | fascia baule',q(u,-1.62,.54),(.055,.57,.025),'int_brass',angle)
    I.box(name+' | serratura',q(0,-1.91,.32),(.10,.03,.14),'int_brass',angle)
    side=q(1.13,.65,0);I.table(name+' | comodino',side,.5,.5,.60)
    I.candle(name+' | candela comodino',(side[0],side[1],side[2]+.67),.22)
    _loose_books(name+' | libri sul comodino',(side[0]-.12,side[1]-.05,side[2]+.65),2,angle)


def dormitory():
    room=I.Room('67 • Dormitorio Grifondoro',(-43.2,-26.74,99.8))
    room.part('Pavimenti');_disc_floor('Dormitorio | pavimento con vano scala',7.4,0,'int_oak',stair_slot=True)
    room.part('Arredi')
    for i,deg in enumerate([25,85,145,205,260],1):
        a=math.radians(deg);x,y=_xy(4.85,a);_bed('Dormitorio | letto '+str(i),(x,y,0),a-math.pi/2)
    I.cone('Dormitorio | tappeto',(0,0,.012),2.5,2.5,.025,'int_red',96)
    for i,a in enumerate([math.radians(50),math.radians(115),math.radians(180),math.radians(235)]):
        x,y=_xy(7.02,a);_tapestry('Dormitorio | drappo '+str(i),(x,y,2.9),.90,1.8,a-math.pi/2)
    room.part('Soffitti');_disc_floor('Dormitorio | soffitto',7.35,6.15,'int_wood')
    for x in [-3.4,0,3.4]:
        span=math.sqrt(7.1**2-x*x);I.box('Dormitorio | trave',(x,0,5.98),(.2,span*2,.24),'int_oak')
    room.part('Luci');I.area('Dormitorio | luce calda',(0,0,5.1),(0,0,0),1050,5,(1,.75,.48));I.area('Dormitorio | luce laterale',(-3,3.7,3.9),(0,0,1),330,3,(1,.82,.62))
    room.part('Camere');I.camera(room,'Interni | Dormitorio Grifondoro',(-4.3,-4.7,2.05),(.5,2.3,1.35),20)
    return room.finish()


def _union_floor(name,centers,r,z):
    n=96;vs=[Vector((x+r*math.cos(TAU*j/n),y+r*math.sin(TAU*j/n))) for x,y in centers for j in range(n)]
    rings=[list(range(k*n,(k+1)*n)) for k in range(len(centers))]
    vv,ee,ff,*_=delaunay_2d_cdt(vs,[],rings,1,1e-5,False)
    keep=[]
    for f in ff:
        c=sum((vv[i] for i in f),Vector((0,0)))/len(f)
        if any((c.x-x)**2+(c.y-y)**2<=r*r+1e-5 for x,y in centers):keep.append(f)
    n=len(vv);verts=[(p.x,p.y,zz) for zz in [z-.16,z] for p in vv];faces=[];edges={}
    for f in keep:
        faces.extend([tuple(i+n for i in f),tuple(reversed(f))])
        for a,b in zip(f,f[1:]+f[:1]):
            key=tuple(sorted((a,b)));edges[key]=edges.get(key,0)+1
    for (a,b),num in edges.items():
        if num==1:faces.append((a,b,b+n,a+n))
    return I.mesh(name,verts,faces,'path')


def _dome_ceiling(name,p,r):
    x,y,z=p;n=40;nr=8;vs=[]
    for k in range(nr+1):
        rr=r*(1-k/nr);zz=z+1.0*math.sin(k/nr*math.pi/2)
        for j in range(n):vs.append((x+rr*math.cos(TAU*j/n),y+rr*math.sin(TAU*j/n),zz))
    fs=[]
    for k in range(nr):
        for j in range(n):a=k*n+j;b=k*n+(j+1)%n;fs.append((a,b,b+n,a+n))
    I.mesh(name,vs,fs,'stone')
    for j in range(8):
        a=TAU*j/8;last=(x+r*math.cos(a),y+r*math.sin(a),z-.02)
        for k in range(1,9):
            rr=r*(1-k/8);q=(x+rr*math.cos(a),y+rr*math.sin(a),z+math.sin(k/8*math.pi/2)-.02)
            I.beam(name+' | nervatura',last,q,.045,'trim',7);last=q


def _memory_cabinet(name,p,angle=0):
    x,y,z=p;co=math.cos(angle);si=math.sin(angle)
    def q(u,v,w):return(x+u*co-v*si,y+u*si+v*co,z+w)
    for u in [-.55,.55]:I.box(name+' | fianco',q(u,0,1.35),(.09,.38,2.7),'int_wood',angle)
    I.box(name+' | fondo',q(0,.17,1.35),(1.12,.06,2.7),'int_wood',angle)
    batch=I.Batch(name+' | fiale',['glass','int_memory','int_paper','int_brass'])
    for row in range(6):
        zz=.17+row*.40;I.box(name+' | ripiano',q(0,0,zz),(1.17,.40,.055),'int_wood',angle)
        for j in range(7):
            u=-.44+j*.145;cx,cy,cz=q(u,-.025,zz+.03);n=10;vs=[]
            for rr,hh in [(.046,0),(.046,.22),(.022,.27),(.022,.31)]:
                for k in range(n):vs.append((cx+rr*math.cos(TAU*k/n),cy+rr*math.sin(TAU*k/n),cz+hh))
            fs=[tuple(range(n-1,-1,-1)),tuple(range(3*n,4*n))]+[(k*n+i,k*n+(i+1)%n,(k+1)*n+(i+1)%n,(k+1)*n+i) for k in range(3) for i in range(n)]
            batch.shape(vs,fs,0)
            batch.box(q(u,-.025,zz+.12),(.035,.035,.16),1,angle)
            batch.box(q(u,-.077,zz+.14),(.065,.005,.095),2,angle)
            batch.box(q(u,-.025,zz+.35),(.06,.06,.035),3,angle)
    batch.finish()


def _pensieve(p):
    x,y,z=p;I.cone('Silente | piedistallo Pensatoio',p,.46,.34,.86,'stone',32)
    profiles=[(.35,0),(.66,.28),(.62,.31),(.48,.08)];n=48;vs=[]
    for r,h in profiles:
        for j in range(n):vs.append((x+r*math.cos(TAU*j/n),y+r*math.sin(TAU*j/n),z+.86+h))
    fs=[]
    for k in range(len(profiles)-1):
        for j in range(n):a=k*n+j;b=k*n+(j+1)%n;fs.append((a,b,b+n,a+n))
    fs.append(tuple(range((len(profiles)-1)*n,len(profiles)*n)))
    I.mesh('Silente | vasca del Pensatoio',vs,fs,'trim')
    I.cone('Silente | superficie dei ricordi',(x,y,z+.995),.48,.48,.015,'int_memory',48)
    _ring('Silente | anello Pensatoio',(x,y,z+1.145),.64,tube=.015,mat='int_gold',segments=48)


def dumbledore():
    room=I.Room('68 • Ufficio di Silente',(0,0,0))
    centers=[(21.6+16.5*math.cos(a),-97.028+16.5*math.sin(a)) for a in [3.55,3.87,4.19]];z=134.4
    room.part('Pavimenti');_union_floor('Silente | pavimento continuo',centers,2.75,z)
    room.part('Arredi')
    x,y=centers[0]
    I.table('Silente | console d’ingresso',(x-1.1,y+.6,z),1.15,.45,.78,'int_wood')
    I.cone('Silente | base cappello',(x-1.1,y+.6,z+.85),.33,.25,.05,'int_wood',32)
    I.cone('Silente | cappello parlante',(x-1.1,y+.6,z+.90),.26,.08,.5,'int_oak',24)
    o=I.cone('Silente | punta piegata cappello',(0,0,0),.10,.015,.33,'int_oak',16);o.location=(x-1.1,y+.6,z+1.35);o.rotation_euler[1]=-.35
    for i,a in enumerate([math.radians(95),math.radians(150),math.radians(205),math.radians(250)]):
        xx=x+2.42*math.cos(a);yy=y+2.42*math.sin(a);I.portrait('Silente | preside precedente',(xx,yy,z+2.05),.65,1.0,a-math.pi/2,i)
    x,y=centers[1]
    I.table('Silente | scrivania',(x-.10,y+.25,z),1.50,.72,.82,'int_wood');I.chair('Silente | seggio',(x-.10,y+1.0,z),'int_wood',0)
    _papers('Silente | scritti sulla scrivania',(x-.45,y+.20,z+.88),.05,4);_loose_books('Silente | libri di consultazione',(x+.34,y+.22,z+.90),3,.15)
    I.candle('Silente | candela della scrivania',(x+.51,y+.44,z+.88),.28)
    I.table('Silente | strumenti',(x-1.65,y-.75,z),.65,.55,.85,'int_oak')
    I.cone('Silente | strumento sferico',(x-1.65,y-.75,z+.90),.17,.10,.24,'int_brass',24)
    _ring('Silente | armilla',(x-1.65,y-.75,z+1.18),.25,'Y',.014,'int_brass',28)
    _ring('Silente | armilla',(x-1.65,y-.75,z+1.18),.25,'X',.014,'int_brass',28)
    I.portrait('Silente | ritratto nello studio',(x-2.40,y,z+2.25),.7,1.2,math.pi/2,4)
    x,y=centers[2];_pensieve((x+.45,y-.45,z))
    _memory_cabinet('Silente | armadio delle memorie',(x+1.95,y+.70,z),math.radians(-60))
    for i,a in enumerate([math.radians(215),math.radians(265)]):
        xx=x+2.25*math.cos(a);yy=y+2.25*math.sin(a);I.bookcase('Silente | libreria circolare '+str(i+1),(xx,yy,z),1.2,2.8,.34,a-math.pi/2,6,76+i)
    room.part('Soffitti')
    for i,(x,y) in enumerate(centers):_dome_ceiling('Silente | volta '+str(i+1),(x,y,z+5.85+i*.025),2.73)
    room.part('Luci')
    for i,(x,y) in enumerate(centers):I.area('Silente | luce stanza '+str(i+1),(x,y,z+5.1),(x,y,z+.5),340,2.5,(1,.77,.48))
    x,y=centers[1];I.area('Silente | luce scrivania',(x+1.8,y-1.4,z+3.5),(x-.1,y+.3,z+1),180,1.6,(.73,.84,1))
    room.part('Camere');x,y=centers[1]
    I.camera(room,'Interni | Ufficio di Silente',(x+1.95,y-1.15,z+1.65),(x-.45,y+.45,z+1.25),20)
    center=(sum(p[0] for p in centers)/3,sum(p[1] for p in centers)/3)
    cam=I.camera(room,'Interni aperti | Tre stanze di Silente',(center[0]+9,center[1]-10,z+14),(center[0],center[1],z+1),35)
    cam.data.type='ORTHO';cam.data.ortho_scale=15.8
    return room.finish()


def observatory():
    room=I.Room('69 • Osservatorio astronomico',(20.8,11.988,202.7))
    room.part('Pavimenti');_disc_floor('Osservatorio | pavimento anulare',4.55,0,'path',inner=1.15)
    room.part('Arredi');I.table('Osservatorio | tavolo delle mappe',(-2.45,1.25,0),1.55,.85,.82,'int_wood')
    I.box('Osservatorio | carta stellare',(-2.45,1.25,.885),(1.32,.68,.012),'int_sky')
    stars=I.Batch('Osservatorio | stelle sulla carta',['int_gold','int_white'])
    rng=random.Random(42)
    for i in range(45):stars.box((-2.45+rng.uniform(-.60,.60),1.25+rng.uniform(-.29,.29),.897),(.014,.014,.006),i%2)
    stars.finish();_papers('Osservatorio | appunti',(-2.8,1.28,.90),.1,2)
    _loose_books('Osservatorio | atlanti',(-2.1,1.30,.9),3,.05)
    # Armillare compatto; il telescopio esterno già esistente non viene duplicato.
    I.cone('Osservatorio | base astrolabio',(2.3,1.2,0),.40,.25,.85,'int_wood',24)
    for axis in ['X','Y','Z']:_ring('Osservatorio | sfera armillare',(2.3,1.2,1.40),.52,axis,.022,'int_brass',40)
    I.beam('Osservatorio | asse sfera',(2.3,1.2,.85),(2.3,1.2,2.0),.03,'int_brass',8)
    I.table('Osservatorio | leggio',(-2.1,-1.7,0),.65,.55,.95,'int_oak');_loose_books('Osservatorio | quaderni',(-2.10,-1.70,1.02),2,.15)
    room.part('Luci');I.area('Osservatorio | luce diffusa',(0,0,4.6),(0,0,0),260,3.5,(.72,.84,1));I.point('Osservatorio | lanterna',(-2.7,1.3,1.4),55,(1,.65,.27),.5)
    room.part('Camere');I.camera(room,'Interni | Osservatorio astronomico',(3.0,-2.6,1.65),(-1.0,1.3,1.1),21)
    return room.finish()


def apply():
    I.init();I.A.M['int_fireblack']=I.material('Interni | fondo focolare',(.012,.008,.004),.98)
    I.A.M['int_memory']=I.material('Interni | ricordi luminosi',(.025,.18,.23),.28,0,.5)
    before=set(bpy.data.objects)
    rooms=[common_room(),dormitory(),dumbledore(),observatory()]
    new=[o for o in bpy.data.objects if o not in before]
    faces=sum(len(o.data.polygons) for o in new if o.type=='MESH')
    if len(new)>1600 or faces>250000:raise RuntimeError('Modulo residenziale oltre il limite concordato')
    return {'rooms':rooms,'objects_added':len(new),'faces_added':faces,'dormitory_beds':5,'dumbledore_chambers':3,'observatory_has_new_telescope':False,'dormitory_stair_opening':'SE -75..-15 gradi, r4..6.8','observatory_stair_opening':'centro r1.15'}
