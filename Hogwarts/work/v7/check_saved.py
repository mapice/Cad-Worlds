import bpy,hashlib,json,math
from pathlib import Path
from array import array
R=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca');O=R/'outputs'
def fp(o):
 h=hashlib.sha256();h.update(str([list(row) for row in o.matrix_world]).encode());h.update(str((o.hide_render,o.hide_get())).encode())
 if o.type=='MESH':
  for collection,prop,kind,count in [(o.data.vertices,'co','f',len(o.data.vertices)*3),(o.data.loops,'vertex_index','i',len(o.data.loops)),(o.data.polygons,'loop_total','i',len(o.data.polygons))]:
   a=array(kind,[0])*count;collection.foreach_get(prop,a);h.update(a.tobytes())
  h.update(str([m.name if m else None for m in o.data.materials]).encode())
 return h.hexdigest()
def protected():
 out={}
 for col in bpy.data.collections:
  p=col.name.split(' • ')[0]
  if p in ['45','46'] or p.isdigit() and 60<=int(p)<=81:
   for o in col.all_objects:out[o.name]=fp(o)
 return out
target=O/'Hogwarts-esterni-perfezionati.blend'
bpy.ops.wm.open_mainfile(filepath=str(target));new=protected();s=bpy.context.scene
assert s.world.name=='Cielo | foschia degli esterni aggiornati'
assert s.camera.name=='Camera | V7 castello e Lago Nero'
empty=[o.name for o in bpy.data.objects if o.type=='MESH' and not o.hide_render and not o.data.polygons]
missing=[i.name for i in bpy.data.images if i.source=='FILE' and not i.packed_file]
rooms=[c.name for c in bpy.data.collections if any(c.name.startswith(str(i)+' •') for i in range(60,71))]
layers=[l.name for l in s.view_layers]
exterior_visible_in_open=[lc.collection.name for lc in s.view_layers['Interni aperti'].layer_collection.children if lc.collection.name.split(' • ')[0].isdigit() and 83<=int(lc.collection.name.split(' • ')[0])<=93 and not lc.exclude]
assert not empty and not missing and not exterior_visible_in_open
bpy.ops.wm.open_mainfile(filepath=str(O/'Hogwarts-interni.blend'));old=protected();changed=[n for n,h in old.items() if new.get(n)!=h]
assert not changed and len(old)==4339
result={'status':'PASS','file':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'source_sha256':hashlib.sha256((O/'Hogwarts-interni.blend').read_bytes()).hexdigest(),'protected_objects_compared':len(old),'protected_changed':changed,'missing_images':missing,'visible_empty_meshes':empty,'view_layers':layers,'exterior_visible_in_open_layer':exterior_visible_in_open}
(R/'work/v7/verification-saved.json').write_text(json.dumps(result,indent=2));print('SAVED_FILE_VERIFIED',json.dumps(result),flush=True)
