import bpy,sys,json,math,hashlib,importlib
from pathlib import Path
from array import array
R=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca');O=R/'outputs';sys.path.insert(0,str(R/'work/v7'))
SOURCE=O/'Hogwarts-interni.blend'
EXPECTED='ed36965cc8ceadd7318b108d01f40ed2b4f4a564bf47dd28376aab0169b402b3'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED,'La base è cambiata: controllarla prima di proseguire'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))

def fingerprint(o):
 h=hashlib.sha256()
 h.update(str([list(row) for row in o.matrix_world]).encode());h.update(str((o.hide_render,o.hide_get())).encode())
 if o.type=='MESH':
  coords=array('f',[0.])*len(o.data.vertices)*3;o.data.vertices.foreach_get('co',coords);h.update(coords.tobytes())
  loops=array('i',[0])*len(o.data.loops);o.data.loops.foreach_get('vertex_index',loops);h.update(loops.tobytes())
  sizes=array('i',[0])*len(o.data.polygons);o.data.polygons.foreach_get('loop_total',sizes);h.update(sizes.tobytes())
  h.update(str([m.name if m else None for m in o.data.materials]).encode())
 return h.hexdigest()

protected={}
for c in bpy.data.collections:
 prefix=c.name.split(' • ')[0]
 if prefix in ('45','46') or (prefix.isdigit() and 60<=int(prefix)<=81):
  for o in c.all_objects:protected[o.name]=fingerprint(o)
initial=set(bpy.data.objects.keys());reports={}
for name in ['campo_quidditch','hagrid_terreni','guferia_rimessa','dettagli_castello']:
 mod=importlib.import_module(name);reports[name]=mod.apply();print('APPLIED',name,flush=True)
import kit_v7 as K
K.init();K.collection('93 • Viste degli esterni aggiornati')
hero=K.camera('Camera | V7 castello e Lago Nero',(470,-650,280),(0,-25,101),50)
K.camera('Camera | V7 tenuta completa',(-790,-870,680),(-180,70,110),38)
K.camera('Camera | V7 scala e approdo conservati',(270,-270,118),(124,-127,37),45,ortho=175)
s=bpy.context.scene
bpy.data.objects['Camera | V7 rimessa e barche'].data.lens=39
# Il cielo fisico mantiene l'illuminazione. Solo lo sfondo visibile in camera
# usa foschia uniforme, evitando il semispazio scuro sotto l'orizzonte del cielo.
s.world=s.world.copy();s.world.name='Cielo | foschia degli esterni aggiornati'
nt=s.world.node_tree;out=next(n for n in nt.nodes if n.type=='OUTPUT_WORLD')
original=out.inputs['Surface'].links[0].from_socket
lp=nt.nodes.new('ShaderNodeLightPath');bg=nt.nodes.new('ShaderNodeBackground');bg.inputs['Color'].default_value=(.55,.68,.80,1);bg.inputs['Strength'].default_value=.70
bg.label='Foschia visibile sullo sfondo';mix=nt.nodes.new('ShaderNodeMixShader');nt.links.new(lp.outputs['Is Camera Ray'],mix.inputs[0]);nt.links.new(original,mix.inputs[1]);nt.links.new(bg.outputs['Background'],mix.inputs[2]);nt.links.new(mix.outputs[0],out.inputs['Surface'])
for layer in s.view_layers:layer.use=layer.name=='Modello completo'
bpy.context.window.view_layer=s.view_layers['Modello completo']
def recurse(lc):
 yield lc
 for child in lc.children:yield from recurse(child)
for lc in recurse(s.view_layers['Interni aperti'].layer_collection):
 p=lc.collection.name.split(' • ')[0]
 if p.isdigit() and 82<=int(p)<=99:lc.exclude=True
bpy.context.view_layer.update()
changed=[name for name,fp in protected.items() if name not in bpy.data.objects or fingerprint(bpy.data.objects[name])!=fp]
if changed:raise RuntimeError('Geometrie protette modificate: '+str(changed))
new=[o for o in bpy.data.objects if o.name not in initial]
empty=[o.name for o in new if o.type=='MESH' and not o.data.polygons and not o.hide_render]
nonfinite=[o.name for o in new if o.type=='MESH' and any(not math.isfinite(c) for v in o.data.vertices for c in v.co)]
if empty or nonfinite:raise RuntimeError(str({'empty':empty,'nonfinite':nonfinite}))
for im in bpy.data.images:
 if im.source=='FILE' and not im.packed_file:im.pack()
s.camera=hero;s.render.engine='CYCLES';s.cycles.samples=40;s.cycles.adaptive_threshold=.025;s.cycles.use_denoising=True;s.cycles.max_bounces=8;s.cycles.transparent_max_bounces=16
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
for d in p.devices:d.use=d.type=='METAL'
s.cycles.device='GPU';s.render.resolution_percentage=100;s.render.resolution_x=2200;s.render.resolution_y=1500;s.render.image_settings.file_format='PNG';s.render.filepath=str(O/'Hogwarts-esterni-perfezionati.png')
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D' and area.spaces.active.region_3d:
   area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.clip_end=15000
s['Versione corrente']='28 ottobre 2026: esterni V7 costruiti sul file finale degli interni; scala, roccia e interni preservati con confronto della geometria.'
guide=O/'Hogwarts-esterni-GUIDA.txt'
if guide.exists():
 txt=bpy.data.texts.get('LEGGIMI | Esterni aggiornati') or bpy.data.texts.new('LEGGIMI | Esterni aggiornati');txt.clear();txt.write(guide.read_text())
bpy.context.preferences.filepaths.save_version=0
dest=R/'work/v7/Hogwarts-esterni-draft.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(dest),compress=True)
result={'source':str(SOURCE),'source_sha256':EXPECTED,'protected_objects':len(protected),'protected_changed':changed,'new_objects':len(new),'new_mesh_faces':sum(len(o.data.polygons) for o in new if o.type=='MESH'),'new_empty_meshes':empty,'new_nonfinite_meshes':nonfinite,'modules':reports,'cameras':[o.name for o in new if o.type=='CAMERA']}
(R/'work/v7/build-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str));print('DRAFT_SAVED',len(new),'PROTECTED',len(protected),flush=True)
