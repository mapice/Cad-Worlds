"""Finiture esterne localizzate: fontana, Orologio, doccioni della Sala Grande.

apply() non carica/salva il file, non renderizza e non modifica gli interni.
Le statue sono una ricostruzione stilizzata della fontana dei set cinematografici.
"""
import bpy, math, random, sys
from pathlib import Path
from mathutils import Vector, Matrix
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit_v7 as K

ROOT_NAME = '90 • Finiture esterne V7'

def _bounds(ob):
    pts=[ob.matrix_world@v.co for v in ob.data.vertices]
    return [min(p[k] for p in pts) for k in range(3)],[max(p[k] for p in pts) for k in range(3)]

def _part(parent, name):
    col=bpy.data.collections.new(name);parent.children.link(col);col['Esterni V7']=True;K.A.CURRENT=col
    return col

def _transform(batch, target, position, angle=0, scale=1):
    co,si=math.cos(angle),math.sin(angle)
    vs=[(position[0]+scale*(v[0]*co-v[1]*si),position[1]+scale*(v[0]*si+v[1]*co),position[2]+scale*v[2]) for v in batch.v]
    start=len(target.v);target.v.extend(vs);target.f.extend(tuple(start+i for i in face) for face in batch.f);target.mi.extend(batch.mi)

def _ribbon(batch, centers, widths, mat=0, thickness=.035):
    vs=[]
    for p,w in zip(centers,widths):
        for dz in (-thickness/2,thickness/2):
            vs.extend([(p[0]-w/2,p[1],p[2]+dz),(p[0]+w/2,p[1],p[2]+dz)])
    fs=[]
    for i in range(len(centers)-1):
        a=4*i;b=a+4
        fs.extend([(a,b,b+1,a+1),(a+2,a+3,b+3,b+2),(a,a+2,b+2,b),(a+1,b+1,b+3,a+3)])
    fs.extend([(0,1,3,2),(len(vs)-4,len(vs)-2,len(vs)-1,len(vs)-3)])
    batch.add(vs,fs,mat)

def _eagle():
    b=K.Batch('aquila', ['v7_sculpture','v7_crevice','trim'])
    # Massa del corpo e collo; ali ripiegate con penne effettivamente modellate.
    b.ellipsoid((0,0,.77),.35,.29,.50,n=14,rings=8,mat=0,irregular=.035)
    b.ellipsoid((0,-.115,1.13),.22,.22,.29,n=14,rings=7,mat=0,irregular=.025)
    b.ellipsoid((0,-.23,1.35),.24,.24,.23,n=16,rings=7,mat=0,irregular=.025)
    for side in (-1,1):
        b.ellipsoid((side*.28,.055,.76),.13,.27,.42,n=12,rings=7,mat=0,irregular=.04)
        for j in range(6):
            xx=side*(.27+.018*math.sin(j)); yy=-.1+j*.07
            # Penne lunghe a rilievo che convergono sotto il dorso.
            b.tube((xx,yy,1.01-j*.025),(xx*1.06,yy+.17,.35+j*.012),.042,.017,7,0)
        b.ellipsoid((side*.145,-.414,1.40),.045,.028,.035,n=10,rings=5,mat=1,irregular=0)
        b.tube((side*.105,-.15,.43),(side*.12,-.22,.17),.065,.048,8,0)
        for j in (-1,0,1):
            b.tube((side*.12,-.22,.17),(side*.12+j*.07,-.48,.10),.027,.015,7,0)
    # Coda e becco adunco.
    for j in (-1,0,1):
        _ribbon(b,[(j*.06,.13,.55),(j*.08,.34,.30),(j*.10,.53,.20)],[.10,.13,.045],0)
    b.tube((0,-.40,1.37),(0,-.59,1.31),.10,.065,10,2)
    b.tube((0,-.59,1.31),(0,-.57,1.20),.065,.012,9,2)
    # Serpente serrato dagli artigli e dal becco: curva continua, testa distinta.
    pts=[(-.27,-.50,.11),(-.42,-.39,.13),(-.45,-.15,.16),(-.26,-.07,.19),(.01,-.22,.20),(.23,-.46,.24),(.32,-.55,.43),(.29,-.55,.69),(.15,-.57,.92),(0,-.57,1.18),(-.13,-.58,1.28),(-.25,-.59,1.25)]
    for a,c in zip(pts,pts[1:]):b.tube(a,c,.045,.042,8,1)
    b.ellipsoid((-.28,-.59,1.25),.10,.065,.055,n=12,rings=5,mat=1,irregular=0)
    return b

def _fountain(parent):
    col=_part(parent,'90 • Fontana delle quattro aquile')
    old=[o for o in bpy.data.objects if o.name.startswith('Fontana Orologio |')]
    for o in old:o.hide_render=True;o.hide_set(True)
    lo,hi=_bounds(bpy.data.objects['Fontana Orologio | vasca'])
    cx,cy=(lo[0]+hi[0])/2,(lo[1]+hi[1])/2
    z=_bounds(bpy.data.objects['Cortile Orologio | pavimentazione'])[1][2]+.03
    stone=K.Batch('Fontana Orologio V7 | vasca e bordi consumati',['stone','trim','v7_sculpture'])
    stone.box((cx,cy,z+.17),(8.6,8.6,.34),0)
    stone.box((cx,cy,z+.40),(7.7,7.7,.24),1)
    # Vasca quadrata con angoli smussati; il fondo resta una cavità visibile.
    outline=[(-3.65,-3.0),(-3.0,-3.65),(3.0,-3.65),(3.65,-3.0),(3.65,3.0),(3.0,3.65),(-3.0,3.65),(-3.65,3.0)]
    rng=random.Random(9081)
    for i,a in enumerate(outline):
        b=outline[(i+1)%len(outline)];aa=Vector(a);bb=Vector(b);length=(bb-aa).length;angle=math.atan2(b[1]-a[1],b[0]-a[0]);n=max(1,round(length/.85))
        for j in range(n):
            t=(j+.5)/n;p=aa.lerp(bb,t);h=.68+rng.uniform(-.035,.025)
            stone.box((cx+p.x,cy+p.y,z+.52+h/2),(length/n-.025,.53,h),0,angle)
            stone.box((cx+p.x,cy+p.y,z+.52+h+.09),(length/n-.03,.72,.18),1,angle)
    # Quattro piedistalli, senza l'alta colonna generica della versione iniziale.
    bird=_eagle();sculpt=K.Batch('Fontana Orologio V7 | quattro aquile e serpenti',['v7_sculpture','v7_crevice','trim'])
    for sx,sy in [(-1,-1),(-1,1),(1,-1),(1,1)]:
        x,y=cx+sx*2.85,cy+sy*2.85
        for zz,w,d,h,ma in [(z+.70,1.25,1.25,.26,1),(z+1.17,.85,.85,.68,0),(z+1.59,1.13,1.13,.18,1)]:
            stone.box((x,y,zz),(w,d,h),ma)
        yaw=math.atan2(-sx,sy) # il becco locale rivolto a -Y guarda verso la vasca
        _transform(bird,sculpt,(x,y,z+1.69),yaw,1.28)
    stone.finish();sculpt.finish()
    water=K.A.box('Fontana Orologio V7 | acqua bassa',(cx,cy,z+.58),(6.55,6.55,.045),'water')
    # Sedimenti e vegetazione nei giunti esterni, non sul passaggio del chiostro.
    moss=K.Batch('Fontana Orologio V7 | muschio nei giunti',['v7_leaf','v7_dirt'])
    for i in range(26):
        a=rng.uniform(0,math.tau);rr=rng.uniform(3.8,4.3);x=cx+rr*math.cos(a);y=cy+rr*math.sin(a)
        moss.ellipsoid((x,y,z+.36),rng.uniform(.06,.18),rng.uniform(.06,.15),.045,n=8,rings=3,mat=i%2,irregular=.2)
    moss.finish()
    K.camera('Camera | V7 fontana e cortile',(-112,-72,78.5),(cx,cy,73.0),32)
    return {'center':[cx,cy,z],'aquile':4,'serpenti':4,'old_hidden':[o.name for o in old],'collection':col.name}

def _text_mesh(name,body,p,size,mat):
    curve=bpy.data.curves.new(name,'FONT');curve.body=body;curve.align_x='CENTER';curve.align_y='CENTER';curve.size=size;curve.extrude=.022;curve.bevel_depth=.008;curve.bevel_resolution=1
    obj=bpy.data.objects.new(name,curve);K.A.CURRENT.objects.link(obj)
    obj.location=p;obj.rotation_euler=Matrix(((0,0,-1),(-1,0,0),(0,1,0))).to_euler()
    curve.materials.append(K.A.M[mat]);bpy.context.view_layer.update()
    mesh=bpy.data.meshes.new_from_object(obj.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    matrix=obj.matrix_world.copy();bpy.data.objects.remove(obj,do_unlink=True)
    result=bpy.data.objects.new(name,mesh);K.A.CURRENT.objects.link(result);result.matrix_world=matrix
    bpy.data.curves.remove(curve)
    return result

def _clock(parent):
    col=_part(parent,'91 • Orologio e pendolo')
    x,y=K.A.xy(.382,.7105);front=x-.036*600/2
    old=[]
    for ob in bpy.data.objects:
        if ob.name.startswith('Orologio grande |') and any(s in ob.name for s in ['indice','lancetta','perno']):
            old.append(ob.name);ob.hide_render=True;ob.hide_set(True)
    # Il vecchio disco passava dietro i contrafforti di 10 cm: la facciata
    # compariva come strisce dentro il quadrante. Spostamento solo verso l'esterno.
    for name in ['Orologio grande | cornice','Orologio grande | anello','Orologio grande | quadrante']:
        bpy.data.objects[name].location.x-=.36
    bpy.context.view_layer.update()
    lo,hi=_bounds(bpy.data.objects['Orologio grande | quadrante'])
    face=lo[0]-.16;y=(lo[1]+hi[1])/2;z=(lo[2]+hi[2])/2;r=(hi[2]-lo[2])/2
    metal=K.Batch('Orologio V7 | minuteria e lancette traforate',['gold','v7_iron','trim'])
    for rr in (r*.56,r*.98):metal.ring((face,y,z),rr,.055,'X',0,96,7)
    for i in range(60):
        a=math.tau*i/60;rr=.91*r;inner=rr-(.34 if i%5==0 else .16)
        metal.tube((face,y+inner*math.sin(a),z+inner*math.cos(a)),(face,y+rr*math.sin(a),z+rr*math.cos(a)),.048 if i%5==0 else .025,None,6,0)
    roman=['XII','I','II','III','IV','V','VI','VII','VIII','IX','X','XI']
    for i,label in enumerate(roman):
        a=math.tau*i/12
        _text_mesh('Orologio V7 | numero '+label,label,(face-.055,y-r*.735*math.sin(a),z+r*.735*math.cos(a)),.80,'gold')
    for length,angle,width in [(r*.68,-1.03,.15),(r*.43,.60,.21)]:
        # Lancette con spalla a losanga, punta affusolata e contrappeso.
        direction=Vector((0,math.sin(angle),math.cos(angle)));base=Vector((face-.13,y,z));side=Vector((0,math.cos(angle),-math.sin(angle)))
        pts=[base-direction*.62,base+side*width,base+direction*(length*.58)+side*(width*.65),base+direction*length,base+direction*(length*.58)-side*(width*.65),base-side*width]
        v=[p+Vector((d,0,0)) for d in (-.045,.045) for p in pts];n=len(pts)
        metal.add(v,[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)],0)
    metal.ellipsoid((face-.24,y,z),.12,.33,.33,n=16,rings=7,mat=0,irregular=0)
    # Un pendolo statico sospeso nell'apertura; il peso rimane oltre6m sopra il passaggio.
    pendx=front+4.8
    metal.tube((pendx,y,92.2),(pendx,y,79.7),.11,.15,12,0)
    metal.tube((pendx,y-3.4,92.2),(pendx,y+3.4,92.2),.18,.18,10,1)
    metal.ellipsoid((pendx,y,79.4),.35,1.72,1.72,n=28,rings=12,mat=0,irregular=0)
    metal.ring((pendx-.35,y,79.4),1.45,.075,'X',1,64,8)
    for a in [i*math.tau/8 for i in range(8)]:metal.tube((pendx-.37,y+.35*math.sin(a),79.4+.35*math.cos(a)),(pendx-.37,y+1.34*math.sin(a),79.4+1.34*math.cos(a)),.034,None,6,1)
    metal.finish();K.camera('Camera | V7 facciata dell’Orologio',(-230,-95,116),(front+3,y,109),40)
    return {'dial_center':[face,y,z],'roman_numerals':12,'minute_marks':60,'pendulum_lowest_z':77.68,'dial_outward_clearance_correction':.36,'old_hidden':old,'collection':col.name}

def _dragon():
    b=K.Batch('doccione',['v7_sculpture','v7_crevice','trim'])
    # Un piccolo doccione zoomorfo allungato, con bocca di scarico realmente scura.
    b.ellipsoid((0,0,.22),.26,.55,.28,n=12,rings=6,mat=0,irregular=.035)
    b.ellipsoid((0,-.52,.32),.27,.26,.26,n=12,rings=6,mat=0,irregular=.025)
    b.ellipsoid((0,-.75,.23),.20,.18,.16,n=12,rings=6,mat=0,irregular=.025)
    b.ellipsoid((0,-.90,.22),.105,.022,.074,n=12,rings=6,mat=1,irregular=0)
    for side in (-1,1):
        b.tube((side*.15,-.43,.50),(side*.23,-.38,.78),.08,.012,9,0)
        b.ellipsoid((side*.21,-.65,.41),.043,.04,.035,n=8,rings=4,mat=1,irregular=0)
        b.tube((side*.20,.14,.25),(side*.37,-.02,.06),.09,.07,8,0)
        for j in range(3):b.tube((side*.37,-.02,.06),(side*.39+(j-1)*.05,-.20,.03),.032,.014,6,0)
        for j in range(3):
            b.tube((side*.16,.12,.38),(side*(.45+.13*j),.36+.12*j,.62+.06*j),.045,.018,7,0)
        vertices=[(side*.16,.10,.38),(side*.45,.36,.62),(side*.58,.48,.68),(side*.71,.60,.74),(side*.33,.53,.22)]
        b.add(vertices,[(0,1,2),(0,2,3),(0,3,4)],0)
    tail=[(0,.43,.25),(.10,.70,.26),(.30,.85,.40),(.43,.81,.55)]
    for a,c in zip(tail,tail[1:]):b.tube(a,c,.08,.045,8,0)
    return b

def _hall(parent):
    col=_part(parent,'92 • Pietre scolpite della Sala Grande')
    x,y=K.A.xy(.525,.922);angle=math.atan2(.072*382,.066*600);co,si=math.cos(angle),math.sin(angle)
    def point(u,v,z):return (x+u*co-v*si,y+u*si+v*co,z)
    sculpt=K.Batch('Sala Grande V7 | doccioni e mensole scolpite',['v7_sculpture','v7_crevice','trim'])
    caps=K.Batch('Sala Grande V7 | corone dei pinnacoli',['trim','stone'])
    dragon=_dragon();count=0
    for side in (-1,1):
        for u in (-19.12,-9.56,0.0,9.56):
            # Queste coordinate corrispondono ai contrafforti già presenti, non ai vani interni.
            p=point(u,side*9.54,92.0);yaw=angle+(math.pi if side>0 else 0)
            _transform(dragon,sculpt,p,yaw,1.55)
            caps.box(point(u,side*9.15,91.65),(1.4,2.1,.4),0,angle)
            count+=1
        for i in range(11):
            u=-25+1.1+i*47.8/10;p=point(u,side*9.15,92.25)
            caps.ring(p,.49,.09,'Z',0,24,6)
            for j in range(4):
                a=math.tau*j/4
                stem=(p[0]+.36*math.cos(a),p[1]+.36*math.sin(a),p[2]+1.0)
                tip=(p[0]+.60*math.cos(a),p[1]+.60*math.sin(a),p[2]+1.28)
                caps.tube(stem,tip,.07,.025,6,0)
    sculpt.finish();caps.finish()
    K.camera('Camera | V7 doccioni della Sala Grande',(-24,-199,110),(7,-151,94),60)
    return {'doccioni':count,'pinnacoli_rifiniti':22,'collection':col.name}

def apply():
    K.init()
    K.A.M['v7_sculpture']=K.I.material('Esterni | pietra antica scolpita',(.25,.265,.22),.92)
    K.A.M['v7_crevice']=K.I.material('Esterni | incavi nelle sculture',(.095,.11,.078),.98)
    before=set(bpy.data.objects);root=K.collection(ROOT_NAME)
    report={'fontana':_fountain(root),'orologio':_clock(root),'sala_grande':_hall(root)}
    new=[o for o in bpy.data.objects if o not in before]
    K.M.assign_uvs([o for o in new if o.type=='MESH'])
    for o in new:o['Esterni V7']=True
    report.update(objects=len(new),mesh_objects=sum(o.type=='MESH' for o in new),faces=sum(len(o.data.polygons) for o in new if o.type=='MESH'),empty=[o.name for o in new if o.type=='MESH' and not o.data.polygons],cameras=[o.name for o in new if o.type=='CAMERA'])
    assert not report['empty'],report['empty']
    return report

if __name__=='__main__':
    import json
    R=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca')
    bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/Hogwarts-interni.blend'))
    result=apply();(R/'work/v7/dettagli-castello-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print('DETTAGLI_CASTELLO_READY',result,flush=True)
