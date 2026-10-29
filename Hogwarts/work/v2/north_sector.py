"""Ala settentrionale HBP: geometria esterna ricostruita dalla pianta EE2109.
Chiamare build() dopo architecture.init_materials(). Non salva né genera immagini.
"""
import math
import architecture as A


def _facade_ribs(name, p, length, width, height, angle=0, count=10, z=55):
    x,y=p; co=math.cos(angle); si=math.sin(angle)
    for side in (-1,1):
        for i in range(count+1):
            u=-length/2+length*i/count; v=side*(width/2+.45)
            xx=x+u*co-v*si; yy=y+u*si+v*co
            A.box(name+' | contrafforte',(xx,yy,z+(height-2)/2),(1.05,1.7,height-2),'stone',angle)
            A.box(name+' | cappello',(xx,yy,z+height-2),(1.45,2,1),'trim',angle)
    for h in (height*.34,height*.68):
        for side in (-1,1):
            v=side*(width/2+.15)
            A.box(name+' | fascia', (x-v*si,y+v*co,z+h), (length,.45,.45),'trim',angle)


def _greenhouse(name,u,v,length,width,angle=0):
    x,y=A.xy(u,v); z=55.4; wallh=4.1; roofh=3.6
    co=math.cos(angle); si=math.sin(angle)
    def p(a,b,c): return (x+a*co-b*si,y+a*si+b*co,z+c)
    A.box(name+' | zoccolo',p(0,0,.45),(length+.9,width+.9,.9),'trim',angle)
    A.box(name+' | pareti vetrate',p(0,0,.9+wallh/2),(length,width,wallh),'glass',angle)
    A.gable(name+' | tetto vetrato',p(0,0,.9+wallh),length,width,roofh,'glass',angle)
    n=max(5,round(length/4.4))
    for i in range(n+1):
        aa=-length/2+length*i/n
        for side in (-1,1):
            b=side*width/2
            A.beam(name+' | montante',p(aa,b,.9),p(aa,b,.9+wallh),.105,'roof',6)
            A.beam(name+' | centina',p(aa,b,.9+wallh),p(aa,0,.9+wallh+roofh),.105,'roof',6)
    A.beam(name+' | colmo',p(-length/2,0,.9+wallh+roofh),p(length/2,0,.9+wallh+roofh),.13,'roof',8)
    for side in (-1,1):
        for h in (.9,.9+wallh*.50,.9+wallh):
            A.beam(name+' | traverso',p(-length/2,side*width/2,h),p(length/2,side*width/2,h),.085,'roof',6)
        # Barre intermedie sulle due falde, oltre alle centine trasversali.
        A.beam(name+' | barra falda',p(-length/2,side*width*.25,.9+wallh+roofh*.5),p(length/2,side*width*.25,.9+wallh+roofh*.5),.08,'roof',6)
    for end in (-1,1):
        A.beam(name+' | stipite frontone',p(end*length/2,0,.9),p(end*length/2,0,.9+wallh+roofh),.12,'roof',6)
        A.beam(name+' | frontone',p(end*length/2,-width/2,.9+wallh),p(end*length/2,width/2,.9+wallh),.10,'roof',6)


def _dome(name,u,v):
    x,y=A.xy(u,v); z=55.4; r=6.0; h=5.5; n=24
    A.cone(name+' | basamento',(x,y,z),r+.5,r+.5,.9,'trim',8,math.pi/8)
    A.cone(name+' | tamburo vetrato',(x,y,z+.9),r,r,5.2,'glass',24)
    for i in range(12):
        a=2*math.pi*i/12
        A.beam(name+' | pilastrino',(x+r*math.cos(a),y+r*math.sin(a),z+.9),(x+r*math.cos(a),y+r*math.sin(a),z+6.1),.12,'roof',6)
    vz=z+6.1; rings=8; verts=[]
    for j in range(rings+1):
        a=(math.pi/2)*j/rings
        rr=max(.025,r*math.cos(a)); zz=vz+h*math.sin(a)
        for i in range(n):
            t=2*math.pi*i/n; verts.append((x+rr*math.cos(t),y+rr*math.sin(t),zz))
    faces=[]
    for j in range(rings):
        for i in range(n):
            a=j*n+i;b=j*n+(i+1)%n;faces.append((a,b,b+n,a+n))
    faces.append(tuple(range(rings*n,(rings+1)*n)))
    A.mesh(name+' | cupola',verts,faces,'glass')
    for i in range(12):
        t=2*math.pi*i/12
        for j in range(rings):
            a=j*math.pi/2/rings;b=(j+1)*math.pi/2/rings
            A.beam(name+' | nervatura',(x+r*math.cos(a)*math.cos(t),y+r*math.cos(a)*math.sin(t),vz+h*math.sin(a)),(x+r*math.cos(b)*math.cos(t),y+r*math.cos(b)*math.sin(t),vz+h*math.sin(b)),.09,'roof',6)
    A.cone(name+' | lanterna',(x,y,vz+h-.15),.6,.6,1,'roof',12)
    A.cone(name+' | puntale',(x,y,vz+h+.8),.45,.02,1.6,'gold',12)


def _viaduct_gate():
    A.collection('07 • Ingresso del viadotto e quattro torri')
    u,v=.6265,.571; x,y=A.xy(u,v); base=60; length=.097*600; width=.050*382; h=34
    A.box('Ingresso viadotto | fondazione',(x,y,57.4),(length+1,width+1,4.8),'stone')
    # Portale passante: due spalle e una vera volta, senza piano scuro incollato.
    opening=9.8; leg=(length-opening)/2
    for side in (-1,1):
        A.box('Ingresso viadotto | corpo laterale',(x+side*(opening+leg)/2,y,base+h/2),(leg,width,h),'stone')
    A.arch('Ingresso viadotto | portale passante',(x,y,base),opening,20,width,0,1,'trim')
    A.box('Ingresso viadotto | corpo sopra portale',(x,y,base+27.5),(opening,width,13),'stone')
    A.gable('Ingresso viadotto | timpani',(x,y,base+h),length,width,16,'stone')
    A.gable('Ingresso viadotto | grande tetto',(x,y,base+h+.12),length+1,width+1,16,'roof')
    for side in (-1,1):
        yy=y+side*(width/2+.10); ang=0 if side==-1 else math.pi
        for dx in (-23,-16,-8,8,16,23):
            for zz in (base+5,base+18):
                A.window('Ingresso viadotto | finestra',(x+dx,yy,zz),2.15,7.3,ang,True)
        A.box('Ingresso viadotto | marcapiano',(x,yy,base+15),(length+1,.65,.8),'trim')
        A.box('Ingresso viadotto | cornicione',(x,yy,base+h-.5),(length+1,.8,1),'trim')
    # Frontone centrale, oculo e pinnacoli sopra la porta.
    front=y-width/2-.36
    A.gable('Ingresso viadotto | frontone',(x,front,base+h),.8,13,13,'stone',math.pi/2)
    A.gable('Ingresso viadotto | cappello frontone',(x,front,base+h+12.8),1.3,1.6,1.2,'roof',math.pi/2)
    for r,depth,mat in [(2.7,.35,'trim'),(2.2,.12,'window')]:
        o=A.cone('Ingresso viadotto | rosone',(0,0,0),r,r,depth,mat,40)
        o.rotation_euler[0]=math.pi/2;o.location=(x,front-.45 if mat=='trim' else front-.68,base+39)
    for i in range(8):
        a=i*math.pi/4
        A.beam('Ingresso viadotto | raggio rosone',(x,front-.85,base+39),(x+2.1*math.cos(a),front-.85,base+39+2.1*math.sin(a)),.09,'trim',6)
    for side in (-1,1): A.turret('Ingresso viadotto | pinnacolo', (x+side*7,front,base+h-1),1,6,5,False)
    for i,(uu,vv) in enumerate([(.578,.546),(.675,.546),(.578,.596),(.675,.596)],1):
        xx,yy=A.xy(uu,vv)
        A.cone('Torre viadotto '+str(i)+' | zoccolo',(xx,yy,55),6.2,5,7,'stone')
        A.cone('Torre viadotto '+str(i)+' | fusto',(xx,yy,base),5,5,50,'stone')
        for zz in (base+1,base+18,base+35,base+48): A.cone('Torre viadotto | fascia',(xx,yy,zz),5.3,5.3,.7,'trim')
        A.round_windows('Torre viadotto | finestra',(xx,yy,base+8),5,3,8,1.1,3.7,13)
        A.spire('Torre viadotto | guglia',(xx,yy,base+50),5.9,24,48,4)


def build():
    A.collection('05 • Ala Durham, galleria lunga e chiostri')
    # Asse della navata lungo nord/sud; le tre torri appartengono all'altro modulo.
    p=A.loc(.626,.385,55)
    A.building('Galleria lunga',p,.15*382,28,35,20,math.pi/2,3,11)
    _facade_ribs('Galleria lunga',p[:2],.15*382,28,35,math.pi/2,11)
    # Ali che delimitano il cortile, senza riempirne la superficie aperta.
    A.building('Ala nord Durham',A.loc(.550,.317,55),60,10,26,11,0,2,10)
    A.building('Ala occidentale Durham',A.loc(.503,.391,55),57,9,26,11,math.pi/2,2,10)
    A.building('Ala orientale Durham',A.loc(.595,.388,55),44,6.5,24,9,math.pi/2,3,8)
    _facade_ribs('Ala nord Durham',A.xy(.550,.317),60,10,26,0,10)
    _facade_ribs('Ala occidentale Durham',A.xy(.503,.391),57,9,26,math.pi/2,9)
    # Terrazza e chiostri autenticamente aperti, quattro lati con interruzione verso Astronomia.
    c=A.xy(.553,.394)
    A.box('Cortile Durham | lastricato',(*c,55.25),(.068*600,.104*382,.5),'path')
    for name,a,b in [
        ('Chiostro Durham nord',(.522,.351),(.584,.351)),
        ('Chiostro Durham ovest',(.522,.351),(.522,.437)),
        ('Chiostro Durham est',(.584,.351),(.584,.437)),
        ('Chiostro Durham sud ovest',(.522,.437),(.531,.437)),
        ('Chiostro Durham sud est',(.575,.437),(.584,.437)),
    ]:
        A.arcade(name,A.xy(*a),A.xy(*b),55.55,8.5,4.6,3.7,3.1)
    for uu in (.536,.553,.570):
        aa=A.xy(uu,.366);bb=A.xy(uu,.427)
        A.wall('Cortile Durham | giunto lastre',aa,bb,55.51,.025,.08,'trim')
    for vv in (.375,.395,.415):
        aa=A.xy(.531,vv);bb=A.xy(.575,vv)
        A.wall('Cortile Durham | giunto lastre',aa,bb,55.51,.025,.08,'trim')
    # Collegamenti corti al transetto e alla base delle torri; lascia libero il cortile.
    A.building('Navata sud Durham',A.loc(.626,.523,55),.046*382,21,30,16,math.pi/2,2,3)
    A.building('Corpo sud Durham',A.loc(.603,.515,55),21,9,24,10,0,2,4)
    A.building('Corpo laterale occidentale',A.loc(.507,.483,55),15,10,22,9,math.pi/2,2,3)
    # Piccola torre circolare sulla linea occidentale, senza richiamare il DADA rimosso in HBP.
    A.turret('Torre del percorso settentrionale',A.loc(.543,.178,55),4,22,14)

    A.collection('06 • Serre di Erbologia e conservatorio')
    # Lastricati di servizio fra i padiglioni, a quota di terreno.
    A.box('Serre | terrazza nord',A.loc(.625,.246,55.05),(.171*600,.102*382,.35),'path')
    A.box('Serre | terrazza orientale',A.loc(.689,.368,55.16),(.047*600,.203*382,.35),'path')
    k=0
    for u,v in [(.578,.220),(.578,.250),(.672,.220),(.672,.250)]:
        k+=1;_greenhouse('Serra '+str(k),u,v,.061*600,.019*382)
    for u,v in [(.679,.313),(.699,.313),(.679,.407),(.699,.407)]:
        k+=1;_greenhouse('Serra '+str(k),u,v,.086*382,.013*600,math.pi/2)
    _greenhouse('Serra 9 addossata',.568,.276,.046*600,.012*382)
    _dome('Conservatorio a cupola',.625,.198)
    # Cordoli bassi: il bordo orientale segue il precipizio.
    for a,b in [((.543,.198),(.610,.198)),((.640,.198),(.714,.198)),((.714,.198),(.714,.532)),((.714,.532),(.687,.532))]:
        A.wall('Serre | muretto perimetrale',A.xy(*a),A.xy(*b),55,2,.6,'stone')
    _viaduct_gate()

    A.collection('08 • Mura dei campi settentrionali')
    points=[(.533,.185),(.481,.041),(.465,.020),(.390,.033),(.335,.145),(.316,.170)]
    for a,b in zip(points,points[1:]):
        A.wall('Campo settentrionale | cinta',A.xy(*a),A.xy(*b),55,5.5,1.8,'stone',True)
    # Torri poligonali lungo l'antica cinta e porta aperta verso il prato.
    for i,(u,v) in enumerate([(.481,.041),(.465,.020),(.390,.033),(.335,.145)],1):
        A.cone('Cinta | torre '+str(i),A.loc(u,v,55),4.0,4.0,8,'stone',8,math.pi/8)
        A.cone('Cinta | cornice torre '+str(i),A.loc(u,v,62.12),4.5,4.5,1,'trim',8,math.pi/8)
        for j in range(8):
            ang=j*math.pi/4;xx,yy=A.xy(u,v)
            A.box('Cinta | merlo torre',(xx+3.7*math.cos(ang),yy+3.7*math.sin(ang),63.7),(1.5,1.2,1.5),'trim',ang)
    A.building('Campo settentrionale | corpo di guardia',A.loc(.316,.173,55),15,10,10,5,.65,1,3)
    # Area del campo, muro sottile orientale e cammino di accesso alle serre.
    A.wall('Campo settentrionale | muro basso',A.xy(.481,.041),A.xy(.527,.164),55,2,1,'stone')
    A.wall('Campo settentrionale | strada',A.xy(.528,.172),A.xy(.550,.130),55.03,.12,4.2,'path')
    return {'settore':'nord','serre':9,'conservatori':1,'torri_ingresso':4,'chiostro':'aperto'}
