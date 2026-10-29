"""Lago e colli continui per la scena HBP; conserva le sommità della rocca.
apply() non carica, salva o renderizza file. Coordinate e quote in metri indicativi.
"""
import bpy, math, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

WATER_Z=.7
BOUNDS=(-5000.,5200.,-5200.,5400.)
LAKE_CONTROL=[(300,630),(410,690),(470,720),(570,695),(630,745),(705,710),(710,650),(790,630),(830,610),(900,440),(825,360),(835,290),(770,215),(810,145),(805,60),(860,-30),(860,-130),(800,-360),(680,-650),(560,-705),(540,-765),(460,-820),(350,-850),(270,-800),(195,-825),(100,-805),(-40,-740),(-135,-570),(-205,-510),(-165,-445),(-190,-390),(-115,-335),(-90,-250),(-45,-185),(-10,-188),(40,-185),(90,-177),(155,-168),(193,-142),(201,-100),(167,-62),(193,-10),(202,30),(190,92),(147,151),(116,167),(160,234),(197,330),(235,420)]
WEST_UV=[(.045,.66),(.095,.85),(.25,.96),(.399,.948),(.41,.80),(.41,.64),(.465,.56),(.468,.45),(.49,.30),(.505,.10),(.455,.015),(.38,.018),(.30,.16),(.17,.32),(.10,.48)]
WEST_POLY=[((u-.5)*600,(.55-v)*382) for u,v in WEST_UV]
TOP_NAMES=['Colline occidentali | superficie','Promontorio della Sala Grande | sommità','Promontorio delle serre | sommità','Scogliera della rimessa | superficie']
_sampler=None


def _smooth(v):
    a=np.clip(v,0.,1.);return a*a*(3-2*a)


def _catmull(points,sub=7):
    out=[];n=len(points)
    for i in range(n):
        p0=np.array(points[(i-1)%n],float);p1=np.array(points[i],float);p2=np.array(points[(i+1)%n],float);p3=np.array(points[(i+2)%n],float)
        for j in range(sub):
            t=j/sub;t2=t*t;t3=t2*t
            p=.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t2+(-p0+3*p1-3*p2+p3)*t3)
            out.append(tuple(p))
    return np.array(out)
def _rough_coast(poly):
    tangent=np.roll(poly,-1,axis=0)-np.roll(poly,1,axis=0)
    normal=np.column_stack([-tangent[:,1],tangent[:,0]])
    normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-8)
    x=poly[:,0];y=poly[:,1]
    # Irregolarità spaziale dolce, non una corona di denti radiali.
    jitter=8*np.sin(x*.027+y*.011)+4*np.sin(x*.061-y*.037)
    protection=_smooth((np.hypot(x-70,y+30)-210)/150)
    return poly+normal*(jitter*protection)[:,None]
LAKE_POLY=_rough_coast(_catmull(LAKE_CONTROL))


def _distance(points,poly,return_nearest=False):
    """Distanza con segno: positiva a terra, negativa nel poligono."""
    pts=np.asarray(points,float).reshape((-1,2));poly=np.asarray(poly,float)
    aa=poly;bb=np.roll(poly,-1,axis=0);d=bb-aa;dd=np.maximum(np.sum(d*d,axis=1),1e-10)
    result=np.empty(len(pts));nearest=np.empty((len(pts),2));edge_ids=np.empty(len(pts),int)
    for start in range(0,len(pts),1200):
        p=pts[start:start+1200];px=p[:,None,0];py=p[:,None,1]
        t=np.clip(((px-aa[None,:,0])*d[None,:,0]+(py-aa[None,:,1])*d[None,:,1])/dd[None,:],0,1)
        qx=aa[None,:,0]+t*d[None,:,0];qy=aa[None,:,1]+t*d[None,:,1]
        distances=(px-qx)**2+(py-qy)**2;which=np.argmin(distances,axis=1)
        dist=np.sqrt(distances[np.arange(len(p)),which])
        crossing=((aa[None,:,1]>py)!=(bb[None,:,1]>py)) & (px<d[None,:,0]*(py-aa[None,:,1])/(d[None,:,1]+1e-25)+aa[None,:,0])
        inside=np.count_nonzero(crossing,axis=1)%2==1
        result[start:start+len(p)]=np.where(inside,-dist,dist)
        nearest[start:start+len(p),0]=qx[np.arange(len(p)),which];nearest[start:start+len(p),1]=qy[np.arange(len(p)),which]
        edge_ids[start:start+len(p)]=which
    if return_nearest:return result,nearest,edge_ids
    return result


def lake_signed_distance(x,y):return float(_distance([(x,y)],LAKE_POLY)[0])


def _old_west_height(x,y):
    # Stessa funzione della superficie precedente, per la fascia esterna di raccordo.
    u=x/600+.5;v=.55-y/382
    h=48+7*np.sin(u*19)*np.cos(v*14)+5*np.sin(u*34+v*11)
    valley=np.exp(-((u-.235)/.058)**4-((v-.713)/.043)**2)
    h=h*(1-valley)+(29+3*np.sin(u*30))*valley
    dx=np.maximum(np.maximum(.292-u,u-.410),0)*600;dy=np.maximum(np.maximum(.645-v,v-.781),0)*382
    d=np.hypot(dx,dy);w=1-_smooth(d/16);h=h*(1-w)+69.6*w
    for uu,vv,level,core,outer in [(.145,.713,69.8,9,31),(.182,.354,89.8,9,48)]:
        dd=np.hypot((u-uu)*600,(v-vv)*382);ww=1-_smooth((dd-core)/(outer-core));h=h*(1-ww)+level*ww
    mask=(u>.30)&(u<.51)&(v<.27)
    dd=np.minimum(np.minimum((u-.30)*600,(.51-u)*600),(.27-v)*382);ww=_smooth(dd/10)
    return np.where(mask,h*(1-ww)+55*ww,h)


class Sampler:
    def __init__(self):
        dg=bpy.context.evaluated_depsgraph_get();self.tops=[];self.rims=[]
        for name in TOP_NAMES:
            ob=bpy.data.objects.get(name)
            if ob:
                verts=[ob.matrix_world@v.co for v in ob.data.vertices];faces=[tuple(p.vertices) for p in ob.data.polygons]
                tree=BVHTree.FromPolygons(verts,faces,all_triangles=False)
                self.tops.append((name,tree,(min(v.x for v in verts),max(v.x for v in verts),min(v.y for v in verts),max(v.y for v in verts))))
                if name!='Colline occidentali | superficie':
                    edges={}
                    for face in faces:
                        for j,a in enumerate(face):
                            edge=tuple(sorted((a,face[(j+1)%len(face)])));edges[edge]=edges.get(edge,0)+1
                    adjacency={}
                    for (a,b),count in edges.items():
                        if count==1:adjacency.setdefault(a,[]).append(b);adjacency.setdefault(b,[]).append(a)
                    if adjacency:
                        start=next(iter(adjacency));loop=[start];prev=None;current=start
                        for _ in range(len(adjacency)+2):
                            candidates=[q for q in adjacency[current] if q!=prev]
                            if not candidates:break
                            nxt=candidates[0]
                            if nxt==start:break
                            loop.append(nxt);prev,current=current,nxt
                        rim=np.array([(verts[i].x,verts[i].y) for i in loop]);levels=np.array([verts[i].z for i in loop])
                        self.rims.append((name,rim,levels))
        if not self.tops:raise RuntimeError('Superfici esistenti non trovate: caricare il modello dettagliato HBP')

    def old_top(self,x,y):
        best=None;source=None
        for name,tree,bb in self.tops:
            if not(bb[0]-.01<=x<=bb[1]+.01 and bb[2]-.01<=y<=bb[3]+.01):continue
            hit=tree.ray_cast(Vector((x,y,600)),Vector((0,0,-1)))
            if hit[0] is not None and (best is None or hit[0].z>best):best=hit[0].z;source=name
        return best,source

    def sample(self,points,include_old=True):
        p=np.asarray(points,float).reshape((-1,2));x=p[:,0];y=p[:,1]
        signed=_distance(p,LAKE_POLY);landdist=np.maximum(signed,0)
        # Le creste sono indipendenti dal bacino: una sequenza di dorsali, non un catino regolare.
        hills=np.zeros(len(p))
        for cx,cy,amp,sx,sy in [(-430,280,145,270,280),(-650,670,220,360,270),(-560,-300,115,310,300),(-850,80,150,270,400),(160,870,210,360,250),(660,1010,195,330,250),(1130,390,205,250,410),(1080,-430,165,250,340),(400,-1180,130,430,250),(-180,-1080,105,320,260),(-1200,2300,210,900,550),(350,2600,230,1000,650),(1700,2200,195,600,800),(2400,700,170,720,650),(-2200,-1300,175,850,750),(600,-2600,165,1100,650)]:
            hills=np.maximum(hills,amp*np.exp(-(((x-cx)/sx)**2+((y-cy)/sy)**2)*.75))
        rolling=10*np.sin(x*.009+y*.003)*np.cos(y*.007)+4*np.sin(x*.027-y*.019)+2.2*np.sin(x*.073+y*.046)
        shore_weight=_smooth(landdist/110)
        natural=WATER_Z+np.minimum(65,landdist*.20)+(hills+rolling)*shore_weight
        depth=48*(1-np.exp(-np.maximum(-signed,0)/150))+.10*np.sin(x*.08+y*.13)
        h=np.where(signed<0,WATER_Z-np.maximum(.12,depth),natural)
        # Continuità intorno alla vecchia patch occidentale: la parete da basamento scompare.
        dwest,near,_=_distance(p,WEST_POLY,True)
        transition=np.minimum(240,180+45*_smooth((near[:,1]+50)/150)+25*_smooth((-near[:,0]-80)/160))
        blend=(1-_smooth(np.maximum(dwest,0)/transition))*(dwest>=0)*_smooth(landdist/32)
        edgeh=_old_west_height(near[:,0],near[:,1])-.24
        h=h*(1-blend)+edgeh*blend
        # In questa zona i corpi esistenti definiscono la rocca; il vuoto resta gola.
        # La maschera non interessa né la nuova sponda opposta né i colli occidentali.
        interior=(x>-64)&(x<215)&(y>-215)&(y<190)
        edge=np.minimum.reduce([x+64,215-x,y+215,190-y])
        core=_smooth(edge/26)*interior
        gorge=-4.5-1.1*np.sin(x*.045+y*.035)
        h=h*(1-core)+np.minimum(h,gorge)*core
        # Piedi irregolari delle falesie, fuori dalle loro impronte e sotto le quote dei cammini.
        talus=np.zeros(len(p))
        bridge_clear=np.ones(len(p))
        for aa,bb,halfwidth in [((61.2,-83.658),(75.6,-17.954),6.0),((23.4,-31.706),(46.2,-16.044),4.2),((0.,-24.448),(0.,8.022),3.6)]:
            dx=bb[0]-aa[0];dy=bb[1]-aa[1];t=np.clip(((x-aa[0])*dx+(y-aa[1])*dy)/(dx*dx+dy*dy),0,1)
            d=np.hypot(x-aa[0]-dx*t,y-aa[1]-dy*t)
            bridge_clear=np.minimum(bridge_clear,_smooth((d-halfwidth)/8))
        local=(x>-100)&(x<255)&(y>-230)&(y<190)
        ids=np.flatnonzero(local)
        if len(ids):
            for name,rim,levels in self.rims:
                dist,nearest,edgeid=_distance(p[ids],rim,True)
                aa=rim[edgeid];bb=rim[(edgeid+1)%len(rim)];dv=bb-aa
                tt=np.clip(np.sum((nearest-aa)*dv,axis=1)/np.maximum(np.sum(dv*dv,axis=1),1e-8),0,1)
                edge_z=levels[edgeid]*(1-tt)+levels[(edgeid+1)%len(levels)]*tt
                lx=x[ids];ly=y[ids]
                width=29+7*np.sin(lx*.074+ly*.031)+3*np.sin(lx*.19-ly*.08)
                height=np.minimum(18,np.maximum(1.2,edge_z*.28))*(.86+.14*np.sin(lx*.09+ly*.057))
                profile=(1-_smooth(np.maximum(dist,0)/width))**1.6
                if 'Sala Grande' in name:
                    sector=np.maximum(1-_smooth((ly+120)/40),_smooth((lx-35)/45))
                elif 'serre' in name:
                    sector=np.maximum(1-_smooth((ly+10)/40),_smooth((lx-95)/45))
                else:sector=np.ones(len(ids))
                weight=profile*sector*bridge_clear[ids]*(dist>=0)
                target=WATER_Z-.45+height*weight
                active=(dist>=0)&(dist<width)&(weight>.01)&(target>h[ids])
                h[ids]=np.where(active,np.maximum(h[ids],target),h[ids])
                talus[ids]=np.maximum(talus[ids],np.where(active,weight,0))
        self.last_talus_strength=talus
        if include_old:
            for i,(xx,yy) in enumerate(p):
                if not(-300<xx<230 and -240<yy<230):continue
                old,source=self.old_top(xx,yy)
                if old is not None:
                    # Sotto le superfici originali: nessun piano coincidente o edificio spostato.
                    h[i]=old-.24
        # Il muro basso e il vialetto settentrionale devono avere una spalla di terreno.
        # Sono raccordi a terra, non i tre ponti: le loro due impronte vengono preservate.
        for aa,bb in [((-11.4,194.438),(16.2,147.452)),((16.8,144.396),(30.,160.44))]:
            dx=bb[0]-aa[0];dy=bb[1]-aa[1];tt=np.clip(((x-aa[0])*dx+(y-aa[1])*dy)/(dx*dx+dy*dy),0,1)
            dd=np.hypot(x-aa[0]-dx*tt,y-aa[1]-dy*tt)
            w=1-_smooth((dd-4.2)/12)
            h=h*(1-w)+np.maximum(h,54.76)*w
        return h


def height_at(x,y):
    if _sampler is None:raise RuntimeError('Chiamare apply() prima di height_at')
    return float(_sampler.sample([(x,y)])[0])


def _axis(a,b,c,d,outer=20,inner=4):
    left=np.arange(a,b,outer);mid=np.arange(b,c,inner);right=np.arange(c,d+outer*.01,outer)
    return np.unique(np.concatenate([left,mid,right,[d]]))


def _mesh(name,verts,faces,collection,mat):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    ob=bpy.data.objects.new(name,me);collection.objects.link(ob);me.materials.append(mat)
    uv=me.uv_layers.new(name='Metriche')
    for poly in me.polygons:
        poly.use_smooth=True
        for li in poly.loop_indices:
            p=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(p.x,p.y)
    return ob


def apply():
    global _sampler
    if bpy.data.collections.get('40 • Paesaggio esteso'):raise RuntimeError('Paesaggio v4 già presente; applicare una sola volta alla scena di partenza')
    bpy.context.view_layer.update();_sampler=Sampler()
    col=bpy.data.collections.new('40 • Paesaggio esteso');bpy.context.scene.collection.children.link(col)
    for name in ['Lago Nero | acqua','Colline occidentali | pareti rocciose','Studio | piano']:
        ob=bpy.data.objects.get(name)
        if ob:ob.hide_render=True;ob.hide_set(True)
    xs=np.unique(np.concatenate([np.arange(-5000,-1300,170),_axis(-1300,-330,240,1500),np.arange(1500,5200,170),[5200]]))
    ys=np.unique(np.concatenate([np.arange(-5200,-1400,170),_axis(-1400,-240,260,1500),np.arange(1500,5400,170),[5400]]))
    gx,gy=np.meshgrid(xs,ys);pts=np.column_stack([gx.ravel(),gy.ravel()]);heights=_sampler.sample(pts);talus_mask=_sampler.last_talus_strength.copy()
    verts=np.column_stack([pts,heights]).tolist();nx=len(xs);ny=len(ys);faces=[]
    for j in range(ny-1):
        for i in range(nx-1):
            a=j*nx+i;b=a+1;c=a+nx+1;d=a+nx
            if (i+j)%2:faces.extend([(a,b,d),(b,c,d)])
            else:faces.extend([(a,b,c),(a,c,d)])
    terrain=_mesh('Colli e sponde | superficie continua',verts,faces,col,bpy.data.materials['grass'])
    terrain.data.materials.append(bpy.data.materials['rock'])
    for face in terrain.data.polygons:
        # I versanti ripidi rimangono rocciosi, i prati si posano sui pendii dolci.
        if face.normal.z<.72 or max(talus_mask[i] for i in face.vertices)>.10:face.material_index=1
    # Attributi utilizzabili per materiali e distribuzione naturale della vegetazione.
    attr=terrain.data.attributes.new('Quota',type='FLOAT',domain='POINT');attr.data.foreach_set('value',heights)
    attr=terrain.data.attributes.new('Pietrisco',type='FLOAT',domain='POINT');attr.data.foreach_set('value',talus_mask)
    # Il lago è una superficie leggera, non un prisma con pareti verticali ai bordi.
    wx=np.linspace(-1320,1520,113);wy=np.linspace(-1420,1520,117);xx,yy=np.meshgrid(wx,wy)
    pp=np.column_stack([xx.ravel(),yy.ravel()])
    waves=.038*np.sin(pp[:,0]*.173+pp[:,1]*.117)+.022*np.sin(pp[:,0]*.291-pp[:,1]*.083)
    wverts=np.column_stack([pp,np.full(len(pp),WATER_Z)+waves]).tolist();wnx=len(wx);wfaces=[]
    for j in range(len(wy)-1):
        for i in range(len(wx)-1):
            a=j*wnx+i;wfaces.append((a,a+1,a+wnx+1,a+wnx))
    water=_mesh('Lago Nero | superficie estesa',wverts,wfaces,col,bpy.data.materials['water'])
    depth=np.maximum(0,WATER_Z-_sampler.sample(pp))
    attribute=water.data.attributes.new('Profondita',type='FLOAT',domain='POINT');attribute.data.foreach_set('value',depth)
    water['quota_media']=WATER_Z;water['ondulazione_massima_m']=.06
    terrain['Nota']='Paesaggio interpretato: lago esteso, quote vincolate alle sommità preesistenti, colline e coste ricostruite.'
    bpy.context.view_layer.update()
    samples={}
    probes={'civettaia':(-190.8,74.9),'cerchio_pietre':(-213,-62.3),'cortile_orologio':(-101,-62),'serre':(100,125),'quad':(-10,-60),'fondo_gola_viadotto':(72,-60),'molo':(175.8,-136),'lago_centrale':(430,-170),'colli_ovest':(-650,650),'sponda_est':(1100,300),'nord':(200,900),'raccordo_muro_nord':(1.8,171.9),'vialetto_nord':(25,154),'piede_sud_falesia':(25,-190),'piede_est_falesia':(180,20),'dorsale_lontana':(350,2600),'margine_lontano':(5000,5000)}
    for name,(x,y) in probes.items():
        old,origin=_sampler.old_top(x,y)
        samples[name]={'xy':[x,y],'nuovo_terreno':height_at(x,y),'sommità_precedente':old,'fonte_sommità':origin,'distanza_riva':lake_signed_distance(x,y)}
    result={'terrain_object':terrain.name,'water_object':water.name,'terrain_vertices':len(verts),'terrain_faces':len(faces),'water_vertices':len(wverts),'water_faces':len(wfaces),'bounds':list(BOUNDS),'water_level':WATER_Z,'samples':samples,'external_resources':0}
    bpy.context.scene['Paesaggio V4']='Lago e colli estesi con coste continue; quote originali del castello conservate. Paesaggio interpretato, non rilievo topografico.'
    return result
