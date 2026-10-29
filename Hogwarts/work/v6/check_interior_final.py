import bpy,json,math,hashlib
from pathlib import Path
ROOT=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca');P=ROOT/'outputs/Hogwarts-interni.blend'
bpy.ops.wm.open_mainfile(filepath=str(P));bpy.context.view_layer.update();s=bpy.context.scene
expected={
'Sala Grande':('60 • Interno Sala Grande','Camera | Interno Sala Grande'),
'Atrio':('61 • Atrio di ingresso','Camera | Atrio e accesso alla scalinata'),
'Biblioteca':('62 • Biblioteca','Camera | Biblioteca'),
'Pozioni':('63 • Aula Pozioni','Camera | Aula Pozioni'),
'Infermeria':('64 • Infermeria','Camera | Infermeria'),
'Trasfigurazione':('65 • Aula Trasfigurazione','Camera | Aula Trasfigurazione'),
'Grifondoro':('66 • Sala comune Grifondoro','Interni | Sala comune Grifondoro'),
'Dormitorio':('67 • Dormitorio Grifondoro','Interni | Dormitorio Grifondoro'),
'Silente':('68 • Ufficio di Silente','Interni | Ufficio di Silente'),
'Osservatorio':('69 • Osservatorio astronomico','Interni | Osservatorio astronomico'),
'Grande scalinata':('70 • Grande scalinata','Interni | Grande scalinata dal ballatoio')}
rooms={}
for label,(coll,cam) in expected.items():
 c=bpy.data.collections.get(coll);o=bpy.data.objects.get(cam)
 rooms[label]={'collection':coll,'collection_present':c is not None,'mesh_objects':sum(q.type=='MESH' for q in c.all_objects) if c else 0,'camera':cam,'camera_present':o is not None and o.type=='CAMERA','camera_world_position':list(o.matrix_world.translation) if o else None}
complete=s.view_layers.get('Modello completo');opened=s.view_layers.get('Interni aperti')
render_objects=set()
def walk(lc,blocked=False):
 blocked=blocked or lc.exclude or lc.collection.hide_render
 if not blocked:
  for o in lc.collection.objects:
   if not o.hide_render:render_objects.add(o)
 for ch in lc.children:walk(ch,blocked)
if complete:walk(complete.layer_collection)
visible_meshes=[o for o in render_objects if o.type=='MESH']
unique_meshes={o.data.as_pointer():o.data for o in visible_meshes}
empty=[o.name for o in visible_meshes if not len(o.data.vertices) or not len(o.data.polygons)]
bad_mesh=set()
for me in unique_meshes.values():
 if any(not math.isfinite(q) for v in me.vertices for q in v.co):bad_mesh.add(me.as_pointer())
nonfinite=[o.name for o in visible_meshes if o.data.as_pointer() in bad_mesh or any(not math.isfinite(q) for row in o.matrix_world for q in row)]
no_material=[];unused_empty_slots={};bad_material_faces=[]
for o in visible_meshes:
 mats=list(o.data.materials);used={p.material_index for p in o.data.polygons}
 unused=[i for i,m in enumerate(mats) if m is None and i not in used]
 if unused:unused_empty_slots[o.name]=unused
 bad=[p.index for p in o.data.polygons if p.material_index>=len(mats) or mats[p.material_index] is None]
 if bad:
  no_material.append(o.name);bad_material_faces.append({'object':o.name,'bad_face_count':len(bad),'face_count':len(o.data.polygons),'used_indices':sorted(used),'slots':[m.name if m else None for m in mats]})
images=[]
for im in bpy.data.images:
 if im.source!='FILE':continue
 packed=im.packed_file
 used_by=[m.name for m in bpy.data.materials if m.use_nodes and any(n.type=='TEX_IMAGE' and n.image==im for n in m.node_tree.nodes)]
 data=bytes(packed.data) if packed else b''
 images.append({'name':im.name,'packed':packed is not None,'packed_bytes':len(data),'png_signature':data.startswith(b'\x89PNG\r\n\x1a\n'),'size':list(im.size),'material_users':used_by})
missing_external=[im['name'] for im in images if not im['packed']]
portrait_ok=any(i['packed'] and i['png_signature'] and i['material_users'] and min(i['size'])>0 for i in images)
collections={c.name:len(c.all_objects) for c in bpy.data.collections}
previous={}
for filename in ['build-check.json','polish-check.json','connectivity-check.json']:
 p=ROOT/'work/v6'/filename
 if p.exists():
  d=json.loads(p.read_text());previous[filename]={k:d[k] for k in ['objects','all_clear','ray_count','visible_empty','external_images'] if k in d}
structural_names=json.loads((ROOT/'work/v6/connectivity-check.json').read_text()).get('structural_objects',[])
structural_missing=[n for n in structural_names if bpy.data.objects.get(n) is None]
report={
'file':str(P),'sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'blender_version':bpy.app.version_string,
'scope':'Riapertura senza modifica né rendering: presenza degli11ambienti e camere, livelli di vista, geometrie visibili finite/nonvuote, materiali e immagini incorporate. Nessuna nuova campagna di sonde dei passaggi; confrontato il rapporto strutturale precedente.',
'pending_later_change':None,
'objects':len(bpy.data.objects),'collections':len(bpy.data.collections),'mesh_objects':sum(o.type=='MESH' for o in bpy.data.objects),'visible_mesh_objects':len(visible_meshes),'unique_visible_meshes':len(unique_meshes),'faces_including_instances':sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'),'materials':len(bpy.data.materials),
'view_layers':[l.name for l in s.view_layers],'required_view_layers_present':complete is not None and opened is not None,'default_camera':s.camera.name if s.camera else None,'default_camera_is_great_hall':bool(s.camera and s.camera.name=='Camera | Interno Sala Grande'),
'rooms':rooms,'iconic_rooms_count':len(rooms),'rooms_and_cameras_present':all(r['collection_present'] and r['camera_present'] and r['mesh_objects']>0 for r in rooms.values()),
'visible_empty_meshes':empty,'visible_nonfinite_meshes_or_transforms':nonfinite,'visible_missing_materials':no_material,'faces_using_missing_materials':bad_material_faces,'unused_empty_material_slots':unused_empty_slots,
'file_images':images,'missing_external_images':missing_external,'packed_png_portrait_used_by_material':portrait_ok,
'architectural_groups':{n:collections.get(n) for n in ['80 • Involucri esterni apribili','81 • Tetti esterni nascondibili','70 • Grande scalinata','71 • Scala di Grifondoro','72 • Collegamenti dell’Astronomia','73 • Corridoi, aule e accessi','74 • Ingresso del viadotto e percorso biblioteca','75 • Scala verso il ponte alto']},
'previous_checks':previous,'previous_structural_objects_missing':structural_missing}
# Piccolo controllo aggiuntivo, soltanto sul portale atrio–scalinata aggiornato.
from mathutils import Vector
from mathutils.bvhtree import BVHTree
portal_objects=[]
for cname in ['80 • Involucri esterni apribili','61 • Atrio • Soglia e spallette raccordate']:
 cc=bpy.data.collections.get(cname)
 if cc:portal_objects.extend(o for o in cc.all_objects if o.type=='MESH' and not o.hide_render and o.data.polygons)
portal_objects.extend(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Scalinata | fascia di pietra') and not o.hide_render and o.data.polygons)
portal_objects=list({o.as_pointer():o for o in portal_objects}.values());trees=[];dg=bpy.context.evaluated_depsgraph_get()
for o in portal_objects:
 ev=o.evaluated_get(dg);me=ev.to_mesh();verts=[ev.matrix_world@v.co for v in me.vertices];faces=[tuple(f.vertices) for f in me.polygons]
 if verts and faces:trees.append((o.name,BVHTree.FromPolygons(verts,faces)))
 ev.to_mesh_clear()
portal_rays=[];portal_hits=[]
for off in [-.65,0,.65]:
 a=Vector((28.8+off,-116.0,62.0));direction=Vector((0,1,0));hits=[]
 for name,tree in trees:
  hit=tree.ray_cast(a,direction,10)
  if hit[0] is not None and .01<hit[3]<9.99:hits.append({'object':name,'point':list(hit[0]),'distance':float(hit[3])})
 portal_rays.append({'offset':off,'from':list(a),'to':[28.8+off,-106.0,62.0],'hits':hits});portal_hits.extend(hits)
report['atrium_stair_portal_after_fix']={'height':62.0,'ray_count':3,'rays':portal_rays,'clear':not portal_hits}
report['status']='PASS' if report['required_view_layers_present'] and report['default_camera_is_great_hall'] and report['rooms_and_cameras_present'] and not(empty or nonfinite or no_material or missing_external or structural_missing) and portrait_ok and not portal_hits else 'CHECK_REQUIRED'
(ROOT/'work/v6/verification-final.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('VERIFY_FINAL',json.dumps({k:report[k] for k in ['status','objects','collections','mesh_objects','visible_mesh_objects','faces_including_instances','default_camera','iconic_rooms_count','visible_empty_meshes','visible_nonfinite_meshes_or_transforms','visible_missing_materials','missing_external_images','packed_png_portrait_used_by_material','previous_structural_objects_missing']},ensure_ascii=False),flush=True)
print('ATRIUM_PORTAL',json.dumps(report['atrium_stair_portal_after_fix'],ensure_ascii=False),flush=True)
print('BAD_MATERIAL_FACES',json.dumps(bad_material_faces,ensure_ascii=False),flush=True)
print('UNUSED_EMPTY_SLOT_OBJECTS',len(unused_empty_slots),flush=True)
print('IMAGES',json.dumps(images,ensure_ascii=False),flush=True)
