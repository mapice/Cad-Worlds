"""Settore occidentale HBP: Orologio, ponte coperto e civettaia.
Disposizione letta dalla pianta EE2109; dettagli esterni ricostruiti dalle foto.
Nessun salvataggio né allestimento: richiamare build() nella scena principale.
"""
import math
import random
from mathutils import Vector
import architecture as A


def clock_dial(name,p,r):
    # Quadrante verticale nel piano YZ, rivolto a ovest.
    x,y,z=p
    for suffix,rr,depth,ma,xx in [('cornice',r+.45,.45,'trim',x),('anello',r+.15,.18,'gold',x-.25),('quadrante',r,.10,'roof',x-.38)]:
        ob=A.cone(name+' | '+suffix,(0,0,0),rr,rr,depth,ma,64)
        ob.rotation_euler[1]=-math.pi/2
        ob.location=(xx,y,z)
    front=x-.53
    for i in range(12):
        a=2*math.pi*i/12
        A.beam(name+' | indice',(front,y+r*.79*math.sin(a),z+r*.79*math.cos(a)),(front,y+r*.93*math.sin(a),z+r*.93*math.cos(a)),max(.055,r*.018),'gold',6)
    A.beam(name+' | lancetta minuti',(front-.07,y,z),(front-.07,y-r*.63,z+r*.26),max(.07,r*.025),'gold',6)
    A.beam(name+' | lancetta ore',(front-.12,y,z),(front-.12,y+r*.24,z+r*.43),max(.09,r*.032),'gold',6)
    ob=A.cone(name+' | perno',(0,0,0),r*.09,r*.09,.15,'gold',12)
    ob.rotation_euler[1]=-math.pi/2;ob.location=(front-.16,y,z)


def clock_tower():
    A.collection('11 • Torre dell’Orologio')
    x,y=A.xy(.382,.7105);base=70;length=.101*382;width=.036*600
    front=x-width/2
    gap=9.6
    # Corpi laterali e vera apertura al piano terra, senza pannello nero chiuso.
    wing=(length-gap)/2
    for side in [-1,1]:
        yy=y+side*(gap/2+wing/2)
        A.box('Orologio | ala laterale',(x,yy,base+21.5),(width,wing,43))
        for lv,zz in enumerate([76,85,96,106]):
            for i in range(3):
                wy=y+side*(7.5+i*4.2)
                A.window('Orologio | luce facciata',(front-.08,wy,zz),1.4,3.6,-math.pi/2,True)
                A.window('Orologio | luce retro',(x+width/2+.08,wy,zz),1.4,3.6,math.pi/2,True)
    A.arch('Orologio | passaggio voltato',(x,y,base),gap,24,width,math.pi/2,19)
    # Cornici discontinue a quota bassa, continue sopra il passaggio.
    for zz in [95.5,111.7]:
        A.box('Orologio | fascia orizzontale',(x,y,zz),(width+.7,length+1,.7),'trim')
    # Due falde longitudinali e frontone del grande orologio.
    A.gable('Orologio | timpani',(x,y,113),length,width,23,'stone',math.pi/2)
    A.gable('Orologio | copertura a due falde',(x,y,113.25),length+1.2,width+1.6,23.5,'roof',math.pi/2)
    A.gable('Orologio | frontone',(front+.9,y,112.2),4.8,15.5,29.4,'stone')
    A.gable('Orologio | tetto del frontone',(front+.7,y,112.6),5.4,16.3,29.6,'roof')
    # Il quadrante principale sporge dal prospetto, con cornice leggibile.
    clock_dial('Orologio grande',(front-.45,y,103.2),6.7)
    clock_dial('Orologio superiore',(front-1.9,y,124.7),2.15)
    # Montanti verticali e mensole di coronamento.
    for side in [-1,1]:
        for frac in [.12,.37,.67,.93]:
            yy=y+side*length*.5*frac
            A.box('Orologio | contrafforte',(front-.48,yy,90.4),(1.1,1,40.8),'stone')
            A.box('Orologio | cappello contrafforte',(front-.7,yy,111.7),(1.65,1.45,.7),'trim')
    for i in range(18):
        yy=y-length/2+1+i*(length-2)/17
        for xx in [front-.2,x+width/2+.2]:
            A.box('Orologio | mensola',(xx,yy,110.8),(.9,.5,1.2),'trim')
    # Abbaini su entrambi i versanti.
    for side in [-1,1]:
        for j in range(7):
            yy=y-length/2+3+j*(length-6)/6;xx=x+side*width*.28
            zz=113.4+23.5*.44
            A.window('Orologio | abbaino',(xx,yy,zz),1.35,2.8,-math.pi/2 if side==-1 else math.pi/2)
            A.gable('Orologio | cuffia abbaino',(xx,yy,zz+2.8),3.1,2.8,3,'roof')
    # Sottili guglie sui due timpani e sulla punta del frontone.
    for yy in [y-length/2,y+length/2]:
        A.turret('Orologio | guglia di colmo',(x,yy,131),1.25,7,13,False)
    A.turret('Orologio | guglia del frontone',(front+.7,y,138.5),.9,5,10,False)
    # Due torri minute sul lato anteriore del corpo, subordinate al frontone.
    for yy in [y-length*.44,y+length*.44]:
        A.cone('Orologio | torretta laterale',(front+1,yy,107),1.2,1.2,12,'stone',16)
        A.spire('Orologio | tetto torretta',(front+1,yy,119),1.8,10,16)
    # Occhi e finestre dei timpani nord/sud.
    for side in [-1,1]:
        for xx in [x-5,x,x+5]:
            A.window('Orologio | finestre del timpano',(xx,y+side*(length/2+.08),104),1.7,5,0 if side==-1 else math.pi,True)
    return x,y


def clock_courtyard():
    A.collection('12 • Cortile dell’Orologio')
    west,north=A.xy(.299,.671);east,south=A.xy(.365,.756)
    cx=(west+east)/2;cy=(north+south)/2
    A.box('Cortile Orologio | pavimentazione',(cx,cy,70),(east-west,north-south,.8),'path')
    # Tre lati porticati; lascia aperto il varco all'imbocco del ponte.
    A.arcade('Chiostro Orologio nord',(west,north),(east,north),70.4,7.4,4.5,3.4,3)
    A.arcade('Chiostro Orologio sud',(west,south),(east,south),70.4,7.4,4.5,3.4,3)
    py=A.xy(.30,.713)[1]
    A.arcade('Chiostro Orologio ovest sud',(west,south),(west,py-3.4),70.4,7.4,4.5,3.4,3)
    A.arcade('Chiostro Orologio ovest nord',(west,py+3.4),(west,north),70.4,7.4,4.5,3.4,3)
    # Torre d'angolo più torrette secondarie come il gruppo HBP.
    for i,(xx,yy) in enumerate([(west,north),(west,south),(west+4.5,south)]):
        A.turret('Cortile Orologio | torretta '+str(i+1),(xx,yy,70.4),2.0,12+(i==0)*2,8,False)
    for zz,rr,hh,ma in [(70.45,3.6,.55,'trim'),(71,3.0,1,'stone'),(72,2.6,.12,'water')]:
        A.cone('Fontana Orologio | vasca',(cx,cy,zz),rr,rr,hh,ma,32)
    A.cone('Fontana Orologio | colonna',(cx,cy,72.1),.7,.6,4.1,'trim',16)
    A.cone('Fontana Orologio | coppa',(cx,cy,75.5),1.4,2.0,.8,'trim',24)
    for a in [0,math.pi/2,math.pi,3*math.pi/2]:
        A.beam('Fontana Orologio | becco',(cx+.6*math.cos(a),cy+.6*math.sin(a),75),(cx+1.3*math.cos(a),cy+1.3*math.sin(a),74.5),.16,'trim')
    # Lastricato: fasce sobrie, lontane dai piani coincidenti.
    for t in [.25,.5,.75]:
        A.box('Cortile Orologio | fuga',(west+(east-west)*t,cy,70.42),(.09,north-south-5,.02),'trim')
        A.box('Cortile Orologio | fuga',(cx,south+(north-south)*t,70.42),(east-west-5,.09,.02),'trim')


def covered_bridge():
    A.collection('13 • Ponte coperto in legno')
    start=A.xy(.174,.713);end=A.xy(.300,.713)
    n=15;L=end[0]-start[0]
    # Profilo leggermente irregolare, come il ponte scenografico.
    nodes=[]
    for i in range(n+1):
        t=i/n;nodes.append((start[0]+L*t,start[1]+.8*math.sin(t*math.pi*2),70-.75*math.sin(t*math.pi)))
    for i in range(n):
        a=nodes[i];b=nodes[i+1];dx=b[0]-a[0];dy=b[1]-a[1];seg=math.hypot(dx,dy);ang=math.atan2(dy,dx)
        mx=(a[0]+b[0])/2;my=(a[1]+b[1])/2;mz=(a[2]+b[2])/2
        A.box('Ponte coperto | tavolato',(mx,my,mz-.25),(seg+.1,5.1,.5),'wood',ang)
        A.gable('Ponte coperto | tetto',(mx,my,mz+6.6),seg+.24,6.2,2.3,'roof',ang)
        for side in [-1,1]:
            for h in [1.1,2.5,6.4]:
                A.beam('Ponte coperto | corrente',(a[0],a[1]+side*2.45,a[2]+h),(b[0],b[1]+side*2.45,b[2]+h),.16,'wood',6)
            A.beam('Ponte coperto | croce',(a[0],a[1]+side*2.45,a[2]+.5),(b[0],b[1]+side*2.45,b[2]+5.7),.14,'wood',6)
            A.beam('Ponte coperto | croce',(a[0],a[1]+side*2.45,a[2]+5.7),(b[0],b[1]+side*2.45,b[2]+.5),.14,'wood',6)
        # Assi visibili trasversali del piano, non superfici sovrapposte.
        for j in range(5):
            tt=j/5
            A.box('Ponte coperto | giunto tavole',(a[0]+dx*tt,a[1]+dy*tt,mz+.025),(.045,4.9,.04),'roofline',ang)
    for i,(x,y,z) in enumerate(nodes):
        for side in [-1,1]:
            A.beam('Ponte coperto | montante',(x,y+side*2.45,z-.5),(x,y+side*2.45,z+6.6),.23,'wood',6)
        A.beam('Ponte coperto | traversa superiore',(x,y-2.6,z+6.5),(x,y+2.6,z+6.5),.22,'wood',6)
        if i%3==0 and i not in (0,n):
            foot=25+5*math.sin(i/n*math.pi)
            for side in [-1,1]:
                A.beam('Ponte coperto | sostegno',(x-1.5,y+side*3.5,foot),(x,y+side*2.2,z-.4),.55,'wood',8)
                A.beam('Ponte coperto | saetta',(x-5,y+side*2.4,z-14),(x,y+side*2.4,z-.4),.4,'wood',8)
                A.beam('Ponte coperto | saetta',(x+5,y+side*2.4,z-14),(x,y+side*2.4,z-.4),.4,'wood',8)
            A.beam('Ponte coperto | controvento sostegno',(x-1.5,y-3.5,foot+4),(x,y+2.4,z-4),.37,'wood',8)
    # Piccolo corpo di accesso in pietra presso il cerchio di pietre.
    x,y,z=nodes[0]
    for side in [-1,1]:A.box('Ponte coperto | ingresso in pietra',(x,y+side*3.2,z+3),(3.2,1.1,6),'stone')
    A.arch('Ponte coperto | arco d’accesso',(x,y,z),5.3,7,3.2,math.pi/2,1.5)
    A.gable('Ponte coperto | copertura accesso',(x,y,z+8.5),4.4,7.7,4,'roof')


def hospital_bridge():
    A.collection('14 • Collegamento dell’infermeria')
    a=A.xy(.399,.710);b=A.xy(.430,.710);cx=(a[0]+b[0])/2;cy=(a[1]+b[1])/2;length=b[0]-a[0]
    # Solo le arcate inferiori e la galleria coperta, indipendente dal Quad.
    A.bridge('Infermeria | ponte in pietra',a,b,80,50,5.6,3)
    A.building('Infermeria | galleria',(cx,cy,81),length,6.3,6.5,4.1,0,1,5)


def owlery_and_stones():
    A.collection('15 • Civettaia e cerchio di pietre')
    x,y=A.xy(.182,.354);base=90
    A.cone('Civettaia | basamento',(x,y,base),8.2,8.2,1.4,'stone',48)
    A.cone('Civettaia | fusto',(x,y,base+1.4),7,6.6,23.6,'stone',48)
    for zz in [base+4,base+17,base+24]:A.cone('Civettaia | cornice',(x,y,zz),7.25,7.25,.65,'trim',48)
    A.round_windows('Civettaia | nicchie alte',(x,y,base+12),6.9,1,10,1.65,6.1)
    A.round_windows('Civettaia | feritoie basse',(x,y,base+5.7),7,1,8,.85,2.7)
    A.spire('Civettaia | copertura',(x,y,base+25),8.2,18,48,5)
    # Piattaforma e scalinata breve, da unire al pendio creato dal modello principale.
    A.box('Civettaia | pianerottolo',(x,y-7.4,base+.3),(7,5.5,.6),'path')
    for j in range(10):A.box('Civettaia | gradino',(x,y-10-j*.85,base-.35-j*.5),(5,.85,.7),'stone')
    cx,cy=A.xy(.145,.713)
    rng=random.Random(91)
    # Cerchio irregolare di monoliti; nessuna simmetria da tempietto.
    for i in range(9):
        a=2*math.pi*i/9+.09*rng.random();rr=7.7+rng.uniform(-.9,.9)
        xx=cx+rr*math.cos(a);yy=cy+rr*math.sin(a);h=rng.uniform(3.1,5.9)
        ob=A.cone('Cerchio di pietre | monolite',(xx,yy,70),rng.uniform(.8,1.2),rng.uniform(.55,.9),h,'rock',5,phase=a)
    # Sentiero corto dall'anello all'imbocco del ponte.
    sx,sy=A.xy(.174,.713)
    A.box('Cerchio di pietre | sentiero',((cx+sx)/2,cy,70.05),(sx-cx+2,4,.18),'path')


def build():
    clock_tower()
    clock_courtyard()
    covered_bridge()
    hospital_bridge()
    owlery_and_stones()
