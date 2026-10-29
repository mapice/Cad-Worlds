"""Acqua, materiali del terreno e luce naturale per il paesaggio esteso."""
import bpy,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def basic(name,col,rough):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*col,1)
 nt=m.node_tree;nt.nodes.clear();n=nt.nodes;l=nt.links
 p=n.new('ShaderNodeBsdfPrincipled');p.inputs['Base Color'].default_value=(*col,1);p.inputs['Roughness'].default_value=rough
 out=n.new('ShaderNodeOutputMaterial');l.new(p.outputs[0],out.inputs['Surface'])
 tc=n.new('ShaderNodeTexCoord');tc.location=(-1000,0);p.location=(800,0);out.location=(1100,0)
 return m,n,l,p,tc

def ramp(n,l,fac,stops,label):
 r=n.new('ShaderNodeValToRGB');r.label=label
 for i,(v,c) in enumerate(stops):
  e=r.color_ramp.elements[i] if i<2 else r.color_ramp.elements.new(v);e.position=v;e.color=(*c,1)
 l.new(fac,r.inputs['Fac']);return r.outputs['Color']

def noise_node(n,l,coord,scale,detail=4):
 q=n.new('ShaderNodeTexNoise');q.inputs['Scale'].default_value=scale;q.inputs['Detail'].default_value=detail;q.inputs['Roughness'].default_value=.68;l.new(coord,q.inputs['Vector']);return q

def mix(n,l,a,b,factor=1,mode='MIX'):
 q=n.new('ShaderNodeMixRGB');q.blend_type=mode
 if isinstance(factor,(float,int)):q.inputs[0].default_value=factor
 else:l.new(factor,q.inputs[0])
 for value,s in [(a,q.inputs[1]),(b,q.inputs[2])]:
  if isinstance(value,tuple):s.default_value=(*value,1)
  else:l.new(value,s)
 return q.outputs[0]

def math_node(n,l,op,a,b):
 q=n.new('ShaderNodeMath');q.operation=op
 for v,s in [(a,q.inputs[0]),(b,q.inputs[1])]:
  if isinstance(v,(int,float)):s.default_value=v
  else:l.new(v,s)
 return q.outputs[0]

def terrain_material(name='Paesaggio | prato, brughiera e roccia',slope=True):
 m,n,l,p,tc=basic(name,(.115,.155,.065),.94)
 large=noise_node(n,l,tc.outputs['Object'],.004,5)
 small=noise_node(n,l,tc.outputs['Object'],.048,4)
 grain=noise_node(n,l,tc.outputs['Object'],3.5,3)
 heather=ramp(n,l,large.outputs['Fac'],[(.20,(.035,.065,.024)),(.38,(.085,.125,.035)),(.57,(.17,.19,.065)),(.74,(.22,.205,.11)),(.9,(.16,.175,.12))],'Prati, felci e brughiera')
 variation=ramp(n,l,small.outputs['Fac'],[(.18,(.55,.62,.46)),(.82,(1.12,1.08,.9))],'Chiazze del suolo')
 color=mix(n,l,heather,variation,.48,'MULTIPLY')
 geom=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');l.new(geom.outputs['Normal'],sep.inputs[0])
 if slope:
  steeps=n.new('ShaderNodeMapRange');steeps.clamp=True;l.new(sep.outputs['Z'],steeps.inputs['Value']);steeps.inputs['From Min'].default_value=.55;steeps.inputs['From Max'].default_value=.87;steeps.inputs['To Min'].default_value=1;steeps.inputs['To Max'].default_value=0
  rock=ramp(n,l,small.outputs['Fac'],[(.20,(.075,.085,.078)),(.8,(.25,.26,.235))],'Roccia affiorante')
  color=mix(n,l,color,rock,steeps.outputs['Result'])
 # Lieve variazione sulle rive basse, dove il terreno incontra l'acqua.
 pos=n.new('ShaderNodeSeparateXYZ');l.new(geom.outputs['Position'],pos.inputs[0])
 shore=n.new('ShaderNodeMapRange');shore.clamp=True;l.new(pos.outputs['Z'],shore.inputs['Value']);shore.inputs['From Min'].default_value=.7;shore.inputs['From Max'].default_value=5;shore.inputs['To Min'].default_value=.88;shore.inputs['To Max'].default_value=0
 sand=ramp(n,l,small.outputs['Fac'],[(.15,(.065,.063,.042)),(.85,(.21,.20,.125))],'Riva bagnata e ghiaia')
 color=mix(n,l,color,sand,shore.outputs['Result'])
 if slope:
  debris=n.new('ShaderNodeAttribute');debris.attribute_name='Pietrisco';debris.label='Pietrisco al piede delle falesie'
  color=mix(n,l,color,rock,debris.outputs['Fac'])
 # Prospettiva atmosferica sui rilievi lontani; nessun volume costoso.
 cam=n.new('ShaderNodeCameraData');fog=n.new('ShaderNodeMapRange');fog.clamp=True;l.new(cam.outputs['View Distance'],fog.inputs['Value']);fog.inputs['From Min'].default_value=1500;fog.inputs['From Max'].default_value=5000;fog.inputs['To Min'].default_value=0;fog.inputs['To Max'].default_value=.12
 color=mix(n,l,color,(.30,.39,.46),fog.outputs['Result']);l.new(color,p.inputs['Base Color'])
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.33;bump.inputs['Distance'].default_value=.09;l.new(grain.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
 return m

def water_material():
 m,n,l,p,tc=basic('Lago Nero | acqua profonda e rive',(.012,.045,.055),.23)
 depth=n.new('ShaderNodeAttribute');depth.attribute_name='Profondita';depth.label='Profondità del fondale'
 norm=math_node(n,l,'DIVIDE',depth.outputs['Fac'],38)
 co=ramp(n,l,norm,[(0,(.10,.145,.10)),(.08,(.045,.12,.10)),(.28,(.012,.075,.078)),(.65,(.008,.036,.052)),(1,(.005,.020,.033))],'Bassi fondali e acqua scura')
 l.new(co,p.inputs['Base Color']);p.inputs['IOR'].default_value=1.333;p.inputs['Transmission Weight'].default_value=.22;p.inputs['Specular IOR Level'].default_value=.5;p.inputs['Coat Weight'].default_value=.2;p.inputs['Coat Roughness'].default_value=.12
 vec=n.new('ShaderNodeVectorMath');vec.operation='MULTIPLY';vec.inputs[1].default_value=(.42,1.7,1);l.new(tc.outputs['Object'],vec.inputs[0])
 long=noise_node(n,l,vec.outputs['Vector'],.42,4);fine=noise_node(n,l,tc.outputs['Object'],5.5,2)
 b1=n.new('ShaderNodeBump');b1.inputs['Strength'].default_value=.35;b1.inputs['Distance'].default_value=.07;l.new(long.outputs['Fac'],b1.inputs['Height'])
 b2=n.new('ShaderNodeBump');b2.inputs['Strength'].default_value=.16;b2.inputs['Distance'].default_value=.009;l.new(fine.outputs['Fac'],b2.inputs['Height']);l.new(b1.outputs['Normal'],b2.inputs['Normal']);l.new(b2.outputs['Normal'],p.inputs['Normal'])
 return m

def setup():
 c=bpy.data.collections.get('40 • Paesaggio esteso')
 surfaces=[o for o in c.objects if o.type=='MESH' and 'acqua' not in o.name.lower() and o.name!='Lago Nero | superficie estesa'] if c else []
 # Conserva un prato coerente anche sulle sommità originali.
 terrain_material('grass',False)
 mainmat=terrain_material()
 for o in surfaces:
  if 'fondo' not in o.name.lower():
   o.data.materials.clear();o.data.materials.append(mainmat)
   for face in o.data.polygons:face.material_index=0
 water=bpy.data.objects.get('Lago Nero | superficie estesa')
 if water:
  vertices=[];faces=[]
  for o in surfaces:
   offset=len(vertices);vertices += [o.matrix_world@v.co for v in o.data.vertices];faces += [tuple(offset+i for i in f.vertices) for f in o.data.polygons]
  tree=BVHTree.FromPolygons(vertices,faces,all_triangles=False) if faces else None
  attr=water.data.attributes.get('Profondita') or water.data.attributes.new('Profondita','FLOAT','POINT')
  for v,a in zip(water.data.vertices,attr.data):
   p=water.matrix_world@v.co;hit=tree.ray_cast(Vector((p.x,p.y,1500)),Vector((0,0,-1)),3000) if tree else (None,)
   a.value=max(0,.7-hit[0].z) if hit[0] is not None else 40
  water.data.materials.clear();water.data.materials.append(water_material())
 # Luce esterna, senza il pavimento e le lampade del vecchio studio.
 for o in bpy.data.objects:
  if o.type=='LIGHT' or o.name=='Studio | piano':o.hide_render=True;o.hide_set(True)
 scene=bpy.context.scene
 world=bpy.data.worlds.new('Cielo del Lago Nero');world.use_nodes=True;nd=world.node_tree.nodes;nd.clear();lk=world.node_tree.links
 sky=nd.new('ShaderNodeTexSky');sky.sky_type='MULTIPLE_SCATTERING';sky.sun_disc=False;sky.sun_elevation=.42;sky.sun_rotation=2.7;sky.altitude=.15;sky.air_density=1.1;sky.ozone_density=1.0
 bg=nd.new('ShaderNodeBackground');bg.inputs['Strength'].default_value=.22;out=nd.new('ShaderNodeOutputWorld');floor=nd.new('ShaderNodeMixRGB');floor.blend_type='LIGHTEN';floor.inputs[0].default_value=1;floor.inputs[2].default_value=(.22,.30,.36,1);lk.new(sky.outputs['Color'],floor.inputs[1]);lk.new(floor.outputs[0],bg.inputs['Color']);lk.new(bg.outputs[0],out.inputs['Surface']);scene.world=world
 coll=bpy.data.collections.new('43 • Cielo e viste del paesaggio');scene.collection.children.link(coll)
 d=bpy.data.lights.new('Sole | luce sul castello','SUN');d.energy=2.2;d.angle=.10;d.color=(1,.91,.78)
 sun=bpy.data.objects.new('Sole | luce sul castello',d);coll.objects.link(sun);sun.rotation_euler=(math.radians(35),math.radians(-30),math.radians(-35))
 def camera(name,where,target,lens=42,ortho=None):
  d=bpy.data.cameras.new(name);d.clip_start=.1;d.clip_end=12000;d.lens=lens
  if ortho:d.type='ORTHO';d.ortho_scale=ortho
  o=bpy.data.objects.new(name,d);coll.objects.link(o);o.location=where;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
 hero=camera('Camera | Hogwarts dal Lago Nero',(520,-760,190),(20,-10,116),43)
 wide=camera('Camera | lago e colli dall’alto',(1450,-1800,2100),(245,-70,25),ortho=2050)
 shore=camera('Camera | rimessa e sponde',(365,-370,125),(120,-95,45),48)
 scene.camera=hero;scene.view_settings.view_transform='AgX';scene.view_settings.exposure=-.15
 return {'terrain_surfaces':[o.name for o in surfaces],'water_vertices':len(water.data.vertices) if water else 0,'cameras':[hero.name,wide.name,shore.name]}
