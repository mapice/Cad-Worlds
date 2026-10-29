"""Materiali procedurali incorporati e coordinate metriche per Hogwarts.
apply(): aggiorna i materiali esistenti e assegna le UV.
assign_uvs(objects=None): utile anche dopo l'aggiunta di nuovi dettagli.
Nessuna risorsa esterna, nessun salvataggio del file.
"""
import bpy, math
from mathutils import Vector


def assign_uvs(objects=None):
    count=0
    for ob in list(objects) if objects is not None else list(bpy.context.scene.objects):
        if ob.type!='MESH' or not ob.data.polygons: continue
        me=ob.data
        uv=me.uv_layers.get('Metriche') or me.uv_layers.new(name='Metriche')
        me.uv_layers.active=uv
        for lyr in me.uv_layers: lyr.active_render=(lyr==uv)
        pts=[v.co.copy() for v in me.vertices]
        zs=[v.z for v in pts];zmin=min(zs);zmax=max(zs)
        # Primitive circolari originali: due anelli, due calotte e pannelli laterali.
        caps=[p for p in me.polygons if len(p.vertices)>=12]
        cylindrical=(len(caps)==2 and len(me.vertices)%2==0 and len(me.vertices)>=24 and len(me.polygons)==len(me.vertices)//2+2)
        if cylindrical:
            n=len(me.vertices)//2
            bottom=pts[:n];top=pts[n:]
            cx=sum(v.x for v in bottom)/n;cy=sum(v.y for v in bottom)/n
            r0=sum(math.hypot(v.x-cx,v.y-cy) for v in bottom)/n
            r1=sum(math.hypot(v.x-cx,v.y-cy) for v in top)/n
            valid=max(abs(v.z-bottom[0].z) for v in bottom)<1e-3 and max(abs(v.z-top[0].z) for v in top)<1e-3
            cylindrical=valid and max(r0,r1)>1e-4
            circular=max(abs(math.hypot(v.x-cx,v.y-cy)-r0) for v in bottom)<max(.001,r0*.02)
            perimeter=[0.0]
            for j in range(n):perimeter.append(perimeter[-1]+(bottom[(j+1)%n]-bottom[j]).length)
        for face in me.polygons:
            loops=list(face.loop_indices)
            verts=[pts[me.loops[i].vertex_index] for i in loops]
            if cylindrical and len(face.vertices)==4:
                angles=[math.atan2(v.y-cy,v.x-cx) for v in verts]
                if max(angles)-min(angles)>math.pi: angles=[a+2*math.pi if a<0 else a for a in angles]
                radius=max(r0,r1)
                slant=math.sqrt((zmax-zmin)**2+(r1-r0)**2)/max(.001,zmax-zmin)
                if circular:
                    for li,v,ang in zip(loops,verts,angles): uv.data[li].uv=(ang*radius,(v.z-zmin)*slant)
                else:
                    # Profili a D e prismi irregolari: sviluppo metrico del perimetro.
                    indices=[me.loops[li].vertex_index%n for li in loops]
                    seam=max(indices)-min(indices)>n/2
                    for li,v,j in zip(loops,verts,indices):
                        u=perimeter[j]+(perimeter[-1] if seam and j<n/2 else 0)
                        uv.data[li].uv=(u,(v.z-zmin)*slant)
            else:
                normal=face.normal.normalized()
                if abs(normal.z)>.97:
                    tangent=Vector((1,0,0));vertical=Vector((0,1,0))
                else:
                    tangent=Vector((-normal.y,normal.x,0)).normalized()
                    vertical=normal.cross(tangent).normalized()
                    if vertical.z<0:tangent=-tangent;vertical=-vertical
                for li,v in zip(loops,verts):uv.data[li].uv=(v.dot(tangent),v.dot(vertical))
        count+=1
    return count


class Graph:
    def __init__(self,name,color,rough=.8,metal=0):
        self.mat=bpy.data.materials.get(name) or bpy.data.materials.new(name)
        self.mat.use_nodes=True;self.mat.diffuse_color=(*color,1)
        self.n=self.mat.node_tree.nodes;self.l=self.mat.node_tree.links;self.n.clear()
        self.out=self.add('ShaderNodeOutputMaterial','Uscita',(950,0))
        self.bs=self.add('ShaderNodeBsdfPrincipled','Superficie',(700,0))
        self.bs.inputs['Base Color'].default_value=(*color,1)
        self.bs.inputs['Roughness'].default_value=rough;self.bs.inputs['Metallic'].default_value=metal
        self.bs.inputs['Specular IOR Level'].default_value=.3
        self.l.new(self.bs.outputs['BSDF'],self.out.inputs['Surface'])
        self.coord=self.add('ShaderNodeTexCoord','Coordinate metriche',(-1100,0))
        self.uv=self.coord.outputs['UV'];self.pos=self.coord.outputs['Object']
    def add(self,typ,label,pos=(0,0)):
        n=self.n.new(typ);n.label=label;n.name=label;n.location=pos;return n
    def link(self,a,b):self.l.new(a,b)
    def noise(self,label,vec=None,scale=1,detail=3,rough=.7,pos=(-650,100)):
        n=self.add('ShaderNodeTexNoise',label,pos);n.noise_dimensions='3D';n.inputs['Scale'].default_value=scale;n.inputs['Detail'].default_value=detail;n.inputs['Roughness'].default_value=rough
        self.link(vec or self.uv,n.inputs['Vector']);return n
    def vector_scale(self,vec,values,label,pos=(-900,0)):
        n=self.add('ShaderNodeVectorMath',label,pos);n.operation='MULTIPLY';n.inputs[1].default_value=values;self.link(vec,n.inputs[0]);return n.outputs['Vector']
    def ramp(self,fac,colors,label,pos=(-200,100)):
        n=self.add('ShaderNodeValToRGB',label,pos)
        ramp=n.color_ramp
        while len(ramp.elements)>2:ramp.elements.remove(ramp.elements[-1])
        for i,(where,c) in enumerate(colors):
            e=ramp.elements[i] if i<2 else ramp.elements.new(where)
            e.position=where;e.color=(*c,1)
        self.link(fac,n.inputs['Fac']);return n.outputs['Color']
    def mix(self,a,b,fac=1,blend='MULTIPLY',label='Variazione',pos=(100,100)):
        n=self.add('ShaderNodeMixRGB',label,pos);n.blend_type=blend;n.inputs[0].default_value=fac
        for val,sock in [(a,n.inputs[1]),(b,n.inputs[2])]:
            if isinstance(val,(tuple,list)):sock.default_value=(*val,1) if len(val)==3 else val
            else:self.link(val,sock)
        return n.outputs['Color']
    def bump(self,height,distance=.05,strength=.5,invert=False,normal=None,label='Rilievo',pos=(420,-150)):
        n=self.add('ShaderNodeBump',label,pos);n.inputs['Distance'].default_value=distance;n.inputs['Strength'].default_value=strength;n.invert=invert
        self.link(height,n.inputs['Height'])
        if normal is not None:self.link(normal,n.inputs['Normal'])
        return n.outputs['Normal']
    def brick(self,label,w,h,mortar,c1,c2,mc,vec=None,pos=(-650,450)):
        n=self.add('ShaderNodeTexBrick',label,pos);self.link(vec or self.uv,n.inputs['Vector'])
        n.inputs['Scale'].default_value=1;n.inputs['Brick Width'].default_value=w;n.inputs['Row Height'].default_value=h
        n.inputs['Mortar Size'].default_value=mortar;n.inputs['Mortar Smooth'].default_value=.12
        n.inputs['Color1'].default_value=(*c1,1);n.inputs['Color2'].default_value=(*c2,1);n.inputs['Mortar'].default_value=(*mc,1)
        n.offset=.5;n.offset_frequency=2;n.squash=1.15;n.squash_frequency=5
        return n


def stone_material():
    g=Graph('stone',(.26,.23,.175),.84)
    # Pietra irregolare leggermente deformata; giunti non perfettamente rettilinei.
    warp=g.noise('Irregolarità dei conci',scale=1.7,detail=2,pos=(-1000,500))
    scaled=g.vector_scale(warp.outputs['Color'],(.045,.025,.01),'Deformazione dei giunti',(-820,520))
    add=g.add('ShaderNodeVectorMath','Coordinate dei conci',(-650,650));add.operation='ADD';g.link(g.uv,add.inputs[0]);g.link(scaled,add.inputs[1])
    br=g.brick('Calcare a corsi sfalsati',1.22,.56,.018,(.29,.255,.19),(.205,.185,.145),(.105,.10,.079),add.outputs['Vector'],(-420,550))
    macro=g.noise('Differenze naturali della pietra',scale=.23,detail=4,pos=(-600,240))
    mottled=g.ramp(macro.outputs['Fac'],[(.15,(.53,.55,.50)),(.8,(1.12,1.07,.96))],'Patina minerale',(-340,240))
    color=g.mix(br.outputs['Color'],mottled,1,label='Calcare variegato',pos=(-80,430))
    dripvec=g.vector_scale(g.uv,(.95,.075,1),'Colature verticali',(-920,-150))
    drips=g.noise('Umidità e dilavamento',dripvec,1.1,3,pos=(-680,-150))
    stain=g.ramp(drips.outputs['Fac'],[(.40,(1,1,1)),(.71,(.65,.67,.57)),(.87,(.42,.46,.36))],'Depositi e muschio discreto',(-400,-90))
    color=g.mix(color,stain,.46,label='Usura superficiale',pos=(170,300));g.link(color,g.bs.inputs['Base Color'])
    fine=g.noise('Porosità del calcare',scale=15,detail=3,pos=(-200,-450))
    pores=g.bump(fine.outputs['Fac'],.033,.55,label='Pori',pos=(60,-360))
    norm=g.bump(br.outputs['Fac'],.075,.75,True,pores,'Giunti incavati',(400,-160));g.link(norm,g.bs.inputs['Normal'])
    rough=g.ramp(macro.outputs['Fac'],[(.2,(.68,.68,.68)),(.8,(.94,.94,.94))],'Rugosità della pietra',(130,50));g.link(rough,g.bs.inputs['Roughness'])


def trim_material():
    g=Graph('trim',(.36,.32,.25),.78)
    no=g.noise('Granulosità della pietra lavorata',scale=1.9,detail=4)
    co=g.ramp(no.outputs['Fac'],[(.15,(.27,.245,.19)),(.85,(.43,.39,.31))],'Toni delle cornici')
    g.link(co,g.bs.inputs['Base Color']);fine=g.noise('Grana fine',scale=24,pos=(-600,-250))
    g.link(g.bump(fine.outputs['Fac'],.025,.45),g.bs.inputs['Normal'])


def roof_material(name='roof'):
    g=Graph(name,(.055,.065,.065),.7)
    br=g.brick('Scandole di ardesia',.48,.34,.010,(.042,.055,.061),(.083,.096,.096),(.018,.024,.027))
    no=g.noise('Variazioni tra le lastre',scale=.65,detail=3,pos=(-600,170))
    tint=g.ramp(no.outputs['Fac'],[(.15,(.53,.59,.61)),(.83,(1.2,1.15,1.05))],'Ardesia fredda e patina',(-350,170))
    co=g.mix(br.outputs['Color'],tint,1,label='Colore dell’ardesia',pos=(-70,380))
    stainvec=g.vector_scale(g.uv,(.40,.1,1),'Depositi nelle falde',(-1000,-200))
    moss=g.noise('Licheni e depositi',stainvec,1,4,pos=(-720,-200))
    patch=g.ramp(moss.outputs['Fac'],[(.52,(0,0,0)),(.76,(.34,.34,.34)),(.92,(.8,.8,.8))],'Maschera licheni',(-470,-150))
    mix=g.add('ShaderNodeMixRGB','Licheni sulle lastre',(180,260));g.link(patch,mix.inputs[0]);g.link(co,mix.inputs[1]);mix.inputs[2].default_value=(.075,.087,.052,1)
    g.link(mix.outputs[0],g.bs.inputs['Base Color'])
    no2=g.noise('Sfaldature dell’ardesia',scale=32,detail=2,pos=(-220,-350))
    small=g.bump(no2.outputs['Fac'],.018,.38,label='Sfaldatura fine',pos=(0,-330))
    joint=g.bump(br.outputs['Fac'],.044,.8,True,small,'Sovrapposizione e fuga',(380,-120));g.link(joint,g.bs.inputs['Normal'])
    g.link(g.ramp(no.outputs['Fac'],[(.2,(.52,.52,.52)),(.8,(.82,.82,.82))],'Rugosità delle lastre',(160,50)),g.bs.inputs['Roughness'])


def wood_material():
    g=Graph('wood',(.11,.065,.031),.83)
    vec=g.vector_scale(g.uv,(2.4,.055,1),'Venatura longitudinale')
    no=g.noise('Fibre del legno',vec,3.2,5,pos=(-650,150))
    co=g.ramp(no.outputs['Fac'],[(.17,(.037,.023,.012)),(.52,(.115,.069,.032)),(.85,(.22,.15,.077))],'Rovere invecchiato')
    g.link(co,g.bs.inputs['Base Color']);g.link(g.bump(no.outputs['Fac'],.035,.55,label='Fibre in rilievo'),g.bs.inputs['Normal'])


def path_material():
    g=Graph('path',(.23,.22,.19),.9)
    br=g.brick('Lastre del lastricato',1.5,1.0,.025,(.26,.255,.214),(.18,.185,.164),(.075,.079,.061))
    n=g.noise('Usura delle lastre',scale=3.4,detail=4,pos=(-600,130))
    col=g.ramp(n.outputs['Fac'],[(.16,(.63,.65,.58)),(.8,(1.1,1.07,.96))],'Polvere e scolorimento')
    g.link(g.mix(br.outputs['Color'],col,1),g.bs.inputs['Base Color'])
    bump=g.bump(n.outputs['Fac'],.04,.5,label='Superficie consumata',pos=(0,-200))
    g.link(g.bump(br.outputs['Fac'],.06,.75,True,bump,'Giunti delle lastre'),g.bs.inputs['Normal'])


def rock_material():
    g=Graph('rock',(.14,.145,.123),.95)
    no=g.noise('Massa e fratture della roccia',g.pos,.28,5,pos=(-720,350))
    co=g.ramp(no.outputs['Fac'],[(.18,(.075,.082,.076)),(.48,(.16,.17,.147)),(.82,(.285,.29,.235))],'Strati minerali',(-430,370))
    vec=g.vector_scale(g.pos,(.06,.06,.8),'Stratificazione geologica',(-930,-40))
    strata=g.noise('Vene e strati sedimentari',vec,.8,3,pos=(-670,20))
    sc=g.ramp(strata.outputs['Fac'],[(.24,(.40,.45,.43)),(.76,(1.0,1.04,.97))],'Variazione degli strati',(-380,80))
    g.link(g.mix(co,sc,.72,pos=(0,260)),g.bs.inputs['Base Color'])
    fine=g.noise('Grana della roccia',g.pos,6.5,3,pos=(-450,-250))
    nb=g.bump(fine.outputs['Fac'],.07,.7,label='Grana e schegge',pos=(-120,-250))
    g.link(g.bump(no.outputs['Fac'],.6,.7,False,nb,'Fratture profonde',(350,-100)),g.bs.inputs['Normal'])


def grass_material():
    g=Graph('grass',(.10,.14,.055),.95)
    no=g.noise('Prato e muschio a macchie',g.pos,.18,5,pos=(-650,250))
    co=g.ramp(no.outputs['Fac'],[(.18,(.044,.069,.022)),(.44,(.105,.14,.05)),(.69,(.20,.21,.085)),(.86,(.115,.097,.05))],'Erba, muschio e terra',(-350,240))
    g.link(co,g.bs.inputs['Base Color'])
    fine=g.noise('Tessitura del suolo',g.pos,19,2,pos=(-600,-100))
    g.link(g.bump(fine.outputs['Fac'],.045,.8),g.bs.inputs['Normal'])


def glass_material(name='glass'):
    if name=='glass':
        # Il modello usa involucri chiusi: una trasmissione diretta evita che
        # siano interpretati come enormi blocchi pieni di vetro rifrangente.
        g=Graph(name,(.90,.96,.93),.10)
        g.n.remove(g.bs)
        transparent=g.add('ShaderNodeBsdfTransparent','Trasmissione della lastra',(-70,150))
        transparent.inputs['Color'].default_value=(.975,.990,.980,1)
        glazing=g.add('ShaderNodeBsdfGlass','Riflesso del vetro antico',(170,-70))
        glazing.inputs['Color'].default_value=(.90,.96,.93,1)
        glazing.inputs['Roughness'].default_value=.10
        glazing.inputs['IOR'].default_value=1.46
        fresnel=g.add('ShaderNodeFresnel','Riflessione radente',(-80,390))
        fresnel.inputs['IOR'].default_value=1.46
        no=g.noise('Ondulazione leggera delle lastre',scale=2.2,detail=2,pos=(-650,-120))
        norm=g.bump(no.outputs['Fac'],.004,.24,label='Imperfezioni del vetro',pos=(-350,-110))
        g.link(norm,glazing.inputs['Normal']);g.link(norm,fresnel.inputs['Normal'])
        mix=g.add('ShaderNodeMixShader','Vetro sottile con riflessi',(650,120))
        g.link(fresnel.outputs['Fac'],mix.inputs[0])
        g.link(transparent.outputs[0],mix.inputs[1]);g.link(glazing.outputs[0],mix.inputs[2])
        g.link(mix.outputs[0],g.out.inputs['Surface'])
        g.mat.diffuse_color=(.66,.79,.72,.25)
        g.mat['Descrizione']='Vetro sottile chiaro, trasmissione diretta e riflessi Fresnel; adatto agli involucri vetrati chiusi del modello'
        return
    g=Graph(name,(.09,.145,.135),.19 if name=='glass' else .24)
    g.bs.inputs['IOR'].default_value=1.46
    g.bs.inputs['Transmission Weight'].default_value=.52 if name=='glass' else .13
    g.bs.inputs['Specular IOR Level'].default_value=.5
    g.bs.inputs['Coat Weight'].default_value=.3
    g.bs.inputs['Coat Roughness'].default_value=.18
    no=g.noise('Vetro antico ondulato',scale=2.2,detail=2,pos=(-650,200))
    if name=='window':
        co=g.ramp(no.outputs['Fac'],[(.2,(.012,.026,.022)),(.8,(.042,.07,.06))],'Toni dei vetri scuri')
        g.link(co,g.bs.inputs['Base Color'])
    norm=g.bump(no.outputs['Fac'],.012,.45,label='Ondulazione del vetro');g.link(norm,g.bs.inputs['Normal'])


def water_material():
    g=Graph('water',(.018,.053,.063),.19,.08)
    g.bs.inputs['IOR'].default_value=1.333;g.bs.inputs['Specular IOR Level'].default_value=.5
    g.bs.inputs['Coat Weight'].default_value=.4;g.bs.inputs['Coat Roughness'].default_value=.12
    vec=g.vector_scale(g.pos,(.7,2.8,1),'Increspature del vento')
    no=g.noise('Ondine del lago',vec,1.4,3,pos=(-600,150))
    macro=g.noise('Toni del lago',g.pos,.035,2,pos=(-600,-120))
    co=g.ramp(macro.outputs['Fac'],[(.15,(.008,.026,.032)),(.85,(.027,.085,.091))],'Acqua profonda')
    g.link(co,g.bs.inputs['Base Color']);g.link(g.bump(no.outputs['Fac'],.07,.5),g.bs.inputs['Normal'])


def metal_material():
    g=Graph('gold',(.20,.13,.047),.46,.82)
    no=g.noise('Metallo ossidato',scale=4,detail=3)
    co=g.ramp(no.outputs['Fac'],[(.15,(.055,.080,.065)),(.52,(.25,.16,.057)),(.85,(.40,.29,.115))],'Ottone e patina')
    g.link(co,g.bs.inputs['Base Color']);g.link(g.bump(no.outputs['Fac'],.012,.25),g.bs.inputs['Normal'])


def apply():
    uv_count=assign_uvs()
    stone_material();trim_material();roof_material('roof');roof_material('roofline')
    wood_material();path_material();rock_material();grass_material();glass_material('glass');glass_material('window');water_material();metal_material()
    base=bpy.data.materials.get('base')
    if base and base.use_nodes:
        p=base.node_tree.nodes.get('Principled BSDF')
        if p:p.inputs['Roughness'].default_value=.8
    for name in ['stone','trim','roof','roofline','wood','path','rock','grass','glass','window','water','gold']:
        bpy.data.materials[name]['Descrizione']='Materiale procedurale incorporato, coordinate metriche; nessuna immagine esterna'
    return {'uv_meshes':uv_count,'materials_updated':12,'external_images':0}
