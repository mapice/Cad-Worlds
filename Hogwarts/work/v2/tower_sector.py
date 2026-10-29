"""Torri orientali: Astronomia HBP, campanili Durham e torre centrale.
Ricostruzione esterna proporzionata, con aperture reali nei belvederi.
Responsabilità limitata a queste quattro torri; nessuna luce o terreno.
"""
import math
import architecture as A


def _square_band(name,x,y,z,w,d,height=.7,material='trim'):
    return A.box(name,(x,y,z+height/2),(w,d,height),material)


def _small_square_windows(name,x,y,z,w,d,rows=3,step=10,ww=1.25,hh=5,bays=2):
    for side in range(4):
        angle=side*math.pi/2
        tangent=(math.cos(angle),math.sin(angle))
        normal=(math.sin(angle),-math.cos(angle))
        span=w if side in (0,2) else d
        rad=d/2 if side in (0,2) else w/2
        for j in range(bays):
            u=(j-(bays-1)/2)*span*.36
            for lv in range(rows):
                xx=x+u*tangent[0]+(rad+.09)*normal[0]
                yy=y+u*tangent[1]+(rad+.09)*normal[1]
                A.window(name,(xx,yy,z+lv*step),ww,hh,angle,mull=hh>7)


def _open_square_tier(name,x,y,z,w,d,height,openings=2,shaft=1.15,pier_material='trim'):
    """Pilastri e archi sui quattro lati; il centro resta realmente vuoto."""
    # Quattro pilastri d'angolo, condivisi dai prospetti.
    for sx in (-1,1):
        for sy in (-1,1):
            A.box(name+' | pilastro angolare',(x+sx*(w/2-shaft/2),y+sy*(d/2-shaft/2),z+height/2),(shaft,shaft,height),'stone')
    for side in range(4):
        a=side*math.pi/2; tx,ty=math.cos(a),math.sin(a); nx,ny=math.sin(a),-math.cos(a)
        span=w if side%2==0 else d; rad=(d if side%2==0 else w)/2-shaft/2
        usable=span-shaft; pitch=usable/openings
        # Piantoni intermedi, sottili modanature verticali e archi.
        for j in range(1,openings):
            u=-usable/2+j*pitch
            A.box(name+' | colonnina',(x+u*tx+rad*nx,y+u*ty+rad*ny,z+height/2),(shaft,shaft,height),pier_material)
        for j in range(openings):
            u=-usable/2+(j+.5)*pitch
            A.arch(name+' | arco aperto',(x+u*tx+rad*nx,y+u*ty+rad*ny,z),pitch-shaft,height-.6,shaft,a,.6,'stone')
            # Ogni apertura viene leggibilmente divisa da una sottilissima colonnina.
            if openings==1 and span>13:
                A.beam(name+' | bifora',(x+u*tx+rad*nx,y+u*ty+rad*ny,z),(x+u*tx+rad*nx,y+u*ty+rad*ny,z+height*.77),.16,'trim')


def _cornice_teeth(name,x,y,z,w,d,count=8):
    for side in range(4):
        a=side*math.pi/2; tx,ty=math.cos(a),math.sin(a); nx,ny=math.sin(a),-math.cos(a)
        span=w if side%2==0 else d; rad=(d if side%2==0 else w)/2
        for j in range(count):
            u=-span/2+.8+(span-1.6)*j/max(count-1,1)
            A.box(name+' | mensola',(x+u*tx+(rad+.12)*nx,y+u*ty+(rad+.12)*ny,z),(.5,.75,1.2),'trim',a)


def _square_pinnacle(name,x,y,z,height=14,r=.85):
    A.box(name+' | piede',(x,y,z+1),(2.4*r,2.4*r,2),'trim')
    A.cone(name+' | fusto',(x,y,z+2),r,r,height*.45,'stone',8,math.pi/8)
    A.cone(name+' | capitello',(x,y,z+2+height*.45),r*1.3,r*1.3,.7,'trim',8,math.pi/8)
    A.spire(name+' | cuspide',(x,y,z+2.7+height*.45),r*1.3,height*.55,8)


def _belltower(name,u,v):
    x,y=A.xy(u,v); z=55; w=d=14.4
    A.collection(name)
    A.box(name+' | basamento',(x,y,z+1.2),(w+2,d+2,2.4),'trim')
    A.box(name+' | corpo inferiore',(x,y,z+22.5),(w,d,45),'stone')
    for zz in (z+3,z+14,z+27,z+43):
        _square_band(name+' | marcapiano',x,y,zz,w+.8,d+.8,.7)
    _small_square_windows(name+' | finestre inferiori',x,y,z+5,w,d,3,12,1.6,7,2)
    # Contrafforti d'angolo; geometria distinta dal cilindro delle torri medievali.
    for sx in (-1,1):
        for sy in (-1,1):
            A.box(name+' | contrafforte',(x+sx*(w/2-.45),y+sy*(d/2-.45),z+23),(1.5,1.5,46),'trim')
            A.box(name+' | plinto contrafforte',(x+sx*(w/2-.45),y+sy*(d/2-.45),z+2),(2,2,4),'stone')
    # Due registri campanari: basi murarie e spalle robuste racchiudono
    # le aperture. Evita l'aspetto a gabbia dei primi archi troppo sottili.
    _square_band(name+' | pavimento campane',x,y,z+44.7,w+.7,d+.7,1)
    _square_band(name+' | basamento registro inferiore',x,y,z+45.7,w,d,2.1,'stone')
    _open_square_tier(name+' | campanile inferiore',x,y,z+47.8,w,d,7.5,2,2.1,'stone')
    _square_band(name+' | architrave inferiore',x,y,z+55.3,w+1,d+1,1.1)
    _square_band(name+' | basamento registro superiore',x,y,z+56.4,w,d,2.0,'stone')
    _open_square_tier(name+' | campanile superiore',x,y,z+58.4,w,d,8.5,2,2.1,'stone')
    # Lesene continue sugli angoli, con modanature discrete anziché
    # una griglia interamente chiara. Non modificano la sagoma superiore.
    for sx in (-1,1):
        for sy in (-1,1):
            A.box(name+' | spalla campanaria',(x+sx*(w/2-1.05),y+sy*(d/2-1.05),z+56.3),(2.25,2.25,21.2),'stone')
            A.box(name+' | listello angolare',(x+sx*(w/2-.28),y+sy*(d/2-.28),z+56.3),(.32,.32,21.2),'trim')
    _square_band(name+' | coronamento',x,y,z+66.9,w+1.5,d+1.5,1.1)
    _cornice_teeth(name,x,y,z+66.3,w,d,8)
    # Vere campane semplici, visibili attraverso le aperture.
    A.cone(name+' | campana',(x,y,z+60),1.8,1.0,3.2,'gold',24)
    A.cone(name+' | labbro campana',(x,y,z+59.8),2.05,1.8,.5,'gold',24)
    A.beam(name+' | sostegno campana',(x-5.5,y,z+64),(x+5.5,y,z+64),.35,'wood')
    # Versione POA–HBP: cuspide ottagonale alta, non tetto conico basso dei primi film.
    A.cone(name+' | tamburo ottagonale',(x,y,z+68),8.2,8.0,3,'stone',8,math.pi/8)
    A.spire(name+' | grande cuspide',(x,y,z+71),8.2,40,8,dormers=4)
    for sx in (-1,1):
        for sy in (-1,1): _square_pinnacle(name+' | pinnacolo',x+sx*6.7,y+sy*6.7,z+67.8,13,1.05)
    # Cuspidi minori sui lati e ghimberghe sulla zona di transizione.
    for side in range(4):
        a=side*math.pi/2; nx,ny=math.sin(a),-math.cos(a)
        A.gable(name+' | frontoncino',(x+nx*7.15,y+ny*7.15,z+68.8),3.8,2.7,5,'stone',a+math.pi/2)
        A.window(name+' | luce frontoncino',(x+nx*7.6,y+ny*7.6,z+69.4),1.3,3.5,a)


def _central_tower():
    name='13 • Torre centrale Durham (HBP)'; A.collection(name)
    x,y=A.xy(.626,.484); z=55; w,d=20.4,20.6
    A.box('Centrale | corpo',(x,y,z+25),(w,d,50),'stone')
    A.box('Centrale | zoccolo',(x,y,z+1.1),(w+1.5,d+1.5,2.2),'trim')
    for zz in (z+15,z+29,z+43,z+49): _square_band('Centrale | marcapiano',x,y,zz,w+1,d+1,.8)
    # Tre registri, coerenti con la torre accorciata per HBP.
    _small_square_windows('Centrale | finestra',x,y,z+6,w,d,3,13,1.8,5.6,3)
    for sx in (-1,1):
        for sy in (-1,1):
            A.box('Centrale | contrafforte',(x+sx*(w/2-.65),y+sy*(d/2-.65),z+25),(2,2,50),'trim')
    _open_square_tier('Centrale | loggiato',x,y,z+50,w,d,10.8,3,1.5)
    _square_band('Centrale | cornice sommitale',x,y,z+60.8,w+1.5,d+1.5,1.2)
    _cornice_teeth('Centrale',x,y,z+60.5,w,d,11)
    A.cone('Centrale | tamburo',(x,y,z+62),11.2,10.8,2.2,'stone',8,math.pi/8)
    A.spire('Centrale | guglia ottagonale',(x,y,z+64.2),11.0,33.8,8,dormers=6)
    for sx in (-1,1):
        for sy in (-1,1): _square_pinnacle('Centrale | pinnacolo',x+sx*9.2,y+sy*9.3,z+61.7,15,1.1)
    for side in range(4):
        a=side*math.pi/2; nx,ny=math.sin(a),-math.cos(a)
        A.gable('Centrale | ghimberga',(x+nx*10.0,y+ny*10.1,z+63),4.4,3.1,6,'stone',a+math.pi/2)
        A.window('Centrale | finestra ghimberga',(x+nx*10.7,y+ny*10.8,z+63.6),1.6,4,a)


def _d_plan(x,y,r,back,steps=40):
    # Lato sud rettilineo e abside semicircolare a nord.
    pts=[(x-r,back),(x+r,back),(x+r,y)]
    for i in range(1,steps+1):
        a=math.pi*i/steps; pts.append((x+r*math.cos(a),y+r*math.sin(a)))
    return pts


def _d_roof(name,x,y,z,r,back,height):
    poly=_d_plan(x,y,r,back)
    # Il vertice spostato produce la caratteristica copertura asimmetrica.
    center=(x,y+1.6); n=len(poly)
    upper=[(center[0]+(xx-center[0])*.055,center[1]+(yy-center[1])*.055,z+height) for xx,yy in poly]
    vs=[(xx,yy,z) for xx,yy in poly]+upper
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    o=A.mesh(name,vs,faces,'roof')
    for f in o.data.polygons[4:]: f.use_smooth=True
    return o


def _open_round_tier(name,x,y,z,r,height,n=8,shaft=.43):
    # Arcate vere fra colonnine; tetto separato, nessun cilindro pieno dietro.
    for i in range(n):
        a=2*math.pi*i/n
        A.cone(name+' | colonna',(x+r*math.cos(a),y+r*math.sin(a),z),shaft,shaft,height,'trim',12)
        b=2*math.pi*(i+1)/n
        p1=(x+r*math.cos(a),y+r*math.sin(a)); p2=(x+r*math.cos(b),y+r*math.sin(b))
        cx=(p1[0]+p2[0])/2;cy=(p1[1]+p2[1])/2
        span=math.dist(p1,p2)-2*shaft; ang=math.atan2(p2[1]-p1[1],p2[0]-p1[0])
        A.arch(name+' | arco',(cx,cy,z),span,height,.65,ang,.6,'stone')
        # Parapetto basso con due colonnine e corrimano.
        A.beam(name+' | corrimano',(p1[0],p1[1],z+2.9),(p2[0],p2[1],z+2.9),.14,'trim')
        for t in (.33,.67):
            A.beam(name+' | balaustro',(p1[0]*(1-t)+p2[0]*t,p1[1]*(1-t)+p2[1]*t,z+.6),(p1[0]*(1-t)+p2[0]*t,p1[1]*(1-t)+p2[1]*t,z+2.9),.11,'trim')


def _astronomy():
    name='10 • Torre di Astronomia (HBP)'; A.collection(name)
    x,y=A.xy(.552,.457); base=55; r=13; back=A.xy(.552,.516)[1]
    poly=_d_plan(x,y,r,back)
    A.prism('Astronomia | fusto a D',poly,base,105,'stone')
    for zz,expand,hh in [(base,1.0,2),(base+28,.35,.6),(base+64,.4,.7),(base+100,.7,1),(base+104,1.0,1.2)]:
        A.prism('Astronomia | fascia',_d_plan(x,y,r+expand,back-expand),zz,hh,'trim')
    # File piccole e fitte sulla curva; il fusto rimane imponente.
    for lv in range(7):
        zz=base+7+lv*12.7
        for j in range(11):
            a=.10+(math.pi-.20)*j/10
            xx=x+(r+.06)*math.cos(a); yy=y+(r+.06)*math.sin(a)
            A.window('Astronomia | feritoia curva',(xx,yy,zz),1.05,3.0,a+math.pi/2)
    # Faccia rettilinea a sud e lunghi fianchi.
    for lv in range(7):
        zz=base+7+lv*12.7
        for dx in (-8,-3,3,8): A.window('Astronomia | finestra sud',(x+dx,back-.08,zz),1.1,3.5,0)
        for side in (-1,1):
            for dy in (back+6,back+14):
                A.window('Astronomia | finestra laterale',(x+side*(r+.08),dy,zz),1.15,3.5,math.pi/2 if side==1 else -math.pi/2)
    # Contrafforti rettangolari alti contro la faccia piatta, con coronamento a mensola.
    for dx in (-11.8,11.8):
        A.box('Astronomia | contrafforte sud',(x+dx,back-.9,base+46),(2.1,2.5,92),'stone')
        A.box('Astronomia | cappello contrafforte',(x+dx,back-1.0,base+92),(2.7,3.1,1.0),'trim')
    # Mensole della grande gronda a semicerchio.
    for j in range(24):
        a=math.pi*j/23
        A.box('Astronomia | mensola',(x+(r+.1)*math.cos(a),y+(r+.1)*math.sin(a),base+103),(.65,1.05,1.6),'trim',a+math.pi/2)
    _d_roof('Astronomia | copertura asimmetrica',x,y,base+105.5,r+1,back-.7,55)
    A.beam('Astronomia | puntale centrale',(x,y+1.6,base+160.5),(x,y+1.6,base+167.5),.18,'gold')
    # Abbaini solo nel semicono visibile.
    for lv,frac in enumerate((.22,.43,.64)):
        for j in range(6):
            a=.17+(math.pi-.34)*j/5; rr=(r+1)*(1-frac)
            xx=x+rr*math.cos(a); yy=y+1.6*frac+rr*math.sin(a); zz=base+105.5+55*frac
            A.window('Astronomia | abbaino',(xx,yy,zz),1.15,2.1,a+math.pi/2)
            A.gable('Astronomia | copertura abbaino',(xx,yy,zz+2.1),2.4,1.9,1.8,'roofline',a)
    # Belvedere aggettante sul fronte sud-ovest: due logge aperte e cuspide più alta.
    bx=x-10.4; by=back-1.0; br=5.3
    A.cone('Astronomia | mensola belvedere',(bx,by,142),1.4,br,17,'stone',32)
    A.cone('Astronomia | tamburo belvedere',(bx,by,159),br,br,31,'stone',32)
    A.round_windows('Astronomia | luci tamburo',(bx,by,169),br,2,10,1.3,4.2,9)
    for zz in (160,187.8,201.8,219.0): A.cone('Astronomia | cornice belvedere',(bx,by,zz),br+.6,br+.6,.9,'trim',32)
    _open_round_tier('Astronomia | loggia inferiore',bx,by,188.7,br,12.4,8,.42)
    _open_round_tier('Astronomia | osservatorio',bx,by,202.7,br,15.6,8,.42)
    A.cone('Astronomia | pavimento osservatorio',(bx,by,202.0),br+.5,br+.5,.6,'stone',32)
    A.spire('Astronomia | cuspide belvedere',(bx,by,219.9),br+1.0,21.7,8)
    # Un telescopio piccolo nella loggia superiore, leggibile dai lati.
    A.beam('Astronomia | colonna telescopio',(bx,by,203),(bx,by,209),.4,'gold')
    A.beam('Astronomia | telescopio',(bx-2.5,by-3.2,210.8),(bx+2.0,by+2.5,208.2),.62,'gold',16)
    # Due torrette laterali strettissime, con altezze diverse.
    for suffix,tx,ty,zz,hh,roofh,rr in [
        ('est',x+r-1.0,y-4,151,49,26,2.5),
        ('posteriore',x-7,y+9,156,51,26,2.3),
    ]:
        A.cone('Astronomia | sostegno '+suffix,(tx,ty,zz-9),.8,rr,9,'stone',24)
        A.turret('Astronomia | torretta '+suffix,(tx,ty,zz),rr,hh,roofh,True)
    # Ballatoio sul tetto piatto del corpo addossato, con parapetto sul bordo.
    A.box('Astronomia | piattaforma addossata',(x,back+8,base+99),(24,17,1.3),'path')
    for side in (-1,1):
        A.wall('Astronomia | parapetto ballatoio',(x+side*12,back),(x+side*12,back+17),base+99.6,2.2,.7,'stone')
    A.wall('Astronomia | parapetto sud',(x-12,back),(x+12,back),base+99.6,2.2,.7,'stone')
    # Grande occhio/portale del telescopio sul lato piano, sotto il belvedere.
    # Incorniciato scuro: apertura suggerita nella massa, logge superiori realmente aperte.
    A.window('Astronomia | grande apertura telescopio',(x+3,back-.13,base+84),5.5,11.5,0,True)


def build():
    before=len(A.bpy.data.objects)
    _astronomy()
    _belltower('11 • Campanile occidentale',.604,.288)
    _belltower('12 • Campanile orientale',.649,.288)
    _central_tower()
    return {'objects_added':len(A.bpy.data.objects)-before,'groups':4,'highest_point':245.0}
