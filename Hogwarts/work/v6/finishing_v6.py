"""Rifiniture di materiali e solai degli ambienti interni."""
import bpy,math
from pathlib import Path
from mathutils import Vector
ROOT=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca')

def apply():
 import shells_v6 as S
 # La vecchia cornice piena a quota202.7 coincideva col pavimento nuovo.
 # Si conserva l'anello esterno e si elimina il disco sotto il pavimento.
 for o in list(bpy.data.objects):
  if not o.name.startswith('Astronomia | cornice belvedere') or o.type!='MESH':continue
  lo,hi=S.bounds(o)
  if lo[2]<202.7<hi[2]+.02 and lo[2]>200:
   poly=[(20.8+4.57*math.cos(i*math.tau/64),11.988+4.57*math.sin(i*math.tau/64)) for i in range(64)]
   S.subtract(o,S.prism_cutter('TEMP | cornice osservatorio anulare',poly,201,204))
 for c in list(S.CUTTERS):bpy.data.objects.remove(c,do_unlink=True)
 S.CUTTERS.clear()
 upper=bpy.data.objects.get('Ingresso viadotto | galleria alta')
 if upper:
  for v in upper.data.vertices:v.co.z-=.04
 # Una camera che guarda le carte e l'armillare, con il telescopio di lato.
 cam=bpy.data.objects['Interni | Osservatorio astronomico'];cam.location=(23.8,10.988,204.6);target=Vector((19.8,14.988,204.1));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=22
 # Le tele dipinte sostituiscono soltanto i segnaposto geometrici.
 image=bpy.data.images.load(str(ROOT/'outputs/risorse-interni/ritratti-dipinti.png'),check_existing=True);image.pack();image.filepath='//risorse-interni/ritratti-dipinti.png'
 m=bpy.data.materials.get('Interni | ritratti dipinti') or bpy.data.materials.new('Interni | ritratti dipinti');m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;n.clear()
 out=n.new('ShaderNodeOutputMaterial');p=n.new('ShaderNodeBsdfPrincipled');p.inputs['Roughness'].default_value=.78;p.inputs['Specular IOR Level'].default_value=.23;tex=n.new('ShaderNodeTexImage');tex.image=image;tex.interpolation='Linear';l.new(tex.outputs['Color'],p.inputs['Base Color']);l.new(p.outputs[0],out.inputs['Surface'])
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.10;bump.inputs['Distance'].default_value=.003;l.new(tex.outputs['Color'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
 canvases=[o for o in bpy.data.objects if o.type=='MESH' and o.get('Interno') and ' | tela' in o.name];hidden=[]
 for index,o in enumerate(canvases):
  vs=[v.co for v in o.data.vertices];normal=o.data.polygons[2].normal.normalized();tangent=Vector((-normal.y,normal.x,0)).normalized();coords=[v.dot(tangent) for v in vs];umin,umax=min(coords),max(coords);zmin,zmax=min(v.z for v in vs),max(v.z for v in vs)
  uv=o.data.uv_layers.get('Ritratto') or o.data.uv_layers.new(name='Ritratto');o.data.uv_layers.active=uv
  for layer in o.data.uv_layers:layer.active_render=(layer==uv)
  col=index%3;row=(index//3)%2
  for face in o.data.polygons:
   for li in face.loop_indices:
    v=vs[o.data.loops[li].vertex_index];u=(v.dot(tangent)-umin)/max(.001,umax-umin);vv=(v.z-zmin)/max(.001,zmax-zmin)
    uv.data[li].uv=((col+.012+.976*u)/3,(1-row+.012+.976*vv)/2)
  o.data.materials.clear();o.data.materials.append(m)
  for part in ['busto','volto']:
   old=bpy.data.objects.get(o.name.replace(' | tela',' | '+part))
   if old:old.hide_render=True;old.hide_set(True);hidden.append(old.name)
 # UV delle cornici ricostruite, che non erano ancora presenti nel primo passaggio.
 import materials
 missing=[o for o in bpy.data.objects if o.type=='MESH' and o.data.polygons and not o.data.uv_layers]
 materials.assign_uvs(missing)
 # I collegamenti fra le ali restano visibili anche nella modalità aperta.
 openlayer=bpy.context.scene.view_layers['Interni aperti']
 for lc in openlayer.layer_collection.children:
  if lc.collection.name in ['05 • Tre ponti sulla gola','14 • Collegamento dell’infermeria','04 • Cortile del viadotto']:lc.exclude=False
 bpy.context.scene['Ritratti']='Tele originali generate con imagegen, incorporate nel file; non riproduzioni dei personaggi dei film.'
 return {'painted_portraits':len(canvases),'geometric_placeholders_hidden':len(hidden),'uv_meshes_completed':len(missing),'packed_portrait_image':image.name,'observatory_floor_fixed':True}
