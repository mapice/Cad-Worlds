"""Rimuove solo residui di facciata rimasti senza muro dopo le unioni interne.
apply() opera sul file già caricato; non salva. Test CLI opzionale in work/v6.
"""
import bpy,bmesh,math,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import numpy as np

BATCH_NAMES=['Finestre | modanature esterne e davanzali','Vetrate | reticolo in piombo','Vetrate | trafori gotici']
BODY_COLLECTION='80 • Involucri esterni apribili'


def _bounds(points):
 return tuple(min(p[k] for p in points) for k in range(3)),tuple(max(p[k] for p in points) for k in range(3))


def _prefixes(body):
 n=body.name
 if n.startswith('Torre della Scalinata'):return ['Scalinata | finestra']
 if n.startswith('Astronomia | fusto'):return ['Astronomia | feritoia curva','Astronomia | finestra sud','Astronomia | finestra laterale','Astronomia | grande apertura']
 if n.startswith('Astronomia | tamburo'):return ['Astronomia | luci tamburo']
 if n.startswith('Centrale | corpo'):return ['Centrale | finestra']
 if n.startswith('Ingresso viadotto | corpo'):return ['Ingresso viadotto | finestra']
 return [n.split(' | muri')[0].split(' | muratura')[0].split(' | fusto')[0]]


def _body_tree(bodies):
 verts=[];faces=[];owners=[];meta=[]
 for ob in bodies:
  pts=[ob.matrix_world@v.co for v in ob.data.vertices]
  if not pts or not ob.data.polygons:continue
  k=len(verts);verts.extend(pts);faces.extend(tuple(k+i for i in p.vertices) for p in ob.data.polygons);owners.extend([ob.name]*len(ob.data.polygons));meta.append((ob.name,_prefixes(ob),*_bounds(pts)))
 return BVHTree.FromPolygons(verts,faces,all_triangles=False),owners,meta


def _sample_outer(frame,pane,count=16):
 """Otto punti sulla sagoma esterna della cornice, non dentro il foro."""
 nv=len(pane.data.vertices)//2
 # Le cornici corrette sono anelli di quattro contorni; i pannelli non toccati
 # restano sui corpi non aperti e non sono candidati a questa correzione.
 if len(frame.data.vertices)!=nv*4:return None
 points=[frame.matrix_world@v.co for v in frame.data.vertices[:nv]]
 other=[frame.matrix_world@v.co for v in frame.data.vertices[nv:2*nv]]
 poly=[(a+b)*.5 for a,b in zip(points,other)]
 cap=max(pane.data.polygons,key=lambda p:len(p.vertices));normal=(pane.matrix_world.to_3x3()@cap.normal).normalized()
 if abs(normal.z)>.2:return None
 center=sum(poly,Vector())/len(poly)
 lengths=[(poly[(i+1)%len(poly)]-p).length for i,p in enumerate(poly)];total=sum(lengths);samples=[]
 for j in range(count):
  s=(j+.37)*total/count
  for i,ln in enumerate(lengths):
   if s<=ln:
    p=poly[i].lerp(poly[(i+1)%len(poly)],s/max(ln,1e-9));radial=p-center;radial-=normal*radial.dot(normal)
    if radial.length:radial.normalize()
    samples.append(p+radial*.045);break
   s-=ln
 return normal,poly,samples


def _obb(poly,normal,margin=.6):
 tangent=Vector((-normal.y,normal.x,0)).normalized();up=Vector((0,0,1))
 u=[p.dot(tangent) for p in poly];v=[p.dot(normal) for p in poly];z=[p.z for p in poly]
 lo,hi=_bounds(poly)
 return {'t':tuple(tangent),'n':tuple(normal),'lo':[min(u)-margin,min(v)-margin,min(z)-margin],'hi':[max(u)+margin,max(v)+margin,max(z)+margin],'aabb_lo':[q-margin for q in lo],'aabb_hi':[q+margin for q in hi]}


def _trim_batch(ob,boxes):
 if not ob or ob.type!='MESH' or not ob.data.polygons:return {'object':ob.name if ob else None,'faces_removed':0}
 verts=np.array([tuple(ob.matrix_world@v.co) for v in ob.data.vertices]);remove=np.zeros(len(verts),dtype=bool)
 for bb in boxes:
  lo=np.array(bb['aabb_lo']);hi=np.array(bb['aabb_hi']);mask=np.all((verts>=lo)&(verts<=hi),axis=1)
  ids=np.flatnonzero(mask)
  if not len(ids):continue
  ps=verts[ids];uv=np.column_stack((ps@np.array(bb['t']),ps@np.array(bb['n']),ps[:,2]));inside=np.all((uv>=np.array(bb['lo']))&(uv<=np.array(bb['hi'])),axis=1);remove[ids[inside]]=True
 affected=[p.index for p in ob.data.polygons if all(remove[i] for i in p.vertices)]
 if not affected:return {'object':ob.name,'faces_removed':0}
 before=len(ob.data.polygons);bm=bmesh.new();bm.from_mesh(ob.data);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.faces[i] for i in affected],context='FACES')
 loose=[v for v in bm.verts if not v.link_faces]
 if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
 bm.to_mesh(ob.data);bm.free();ob.data.update()
 return {'object':ob.name,'faces_removed':before-len(ob.data.polygons),'faces_remaining':len(ob.data.polygons)}


def _pixel_ray(camera,x,y,width=1000,height=700):
 deps=bpy.context.evaluated_depsgraph_get();P=camera.calc_matrix_camera(deps,x=width,y=height,scale_x=1,scale_y=1).inverted()
 q=P@Vector((2*x/width-1,1-2*y/height,-1,1));local=Vector(q[:3])/q.w
 if camera.data.type=='ORTHO':origin=camera.matrix_world@local;direction=camera.matrix_world.to_3x3()@Vector((0,0,-1))
 else:origin=camera.matrix_world.translation;direction=camera.matrix_world.to_3x3()@local.normalized()
 direction.normalize();hit=bpy.context.scene.ray_cast(deps,origin,direction,distance=600)
 return {'camera':camera.name,'pixel':[x,y],'object':hit[4].name if hit[0] else None,'face':hit[3] if hit[0] else None,'location':list(hit[1]) if hit[0] else None}


def _pipe_cleanup():
 ob=bpy.data.objects.get('Tetti | grondaie e pluviali')
 if not ob or ob.type!='MESH':return {'object':None,'faces_removed':0,'components_removed':0}
 # Il cilindro interno della torre è stato sottratto dalle vecchie ali del Quad.
 # Tubi completamente dentro quel vuoto non hanno più una facciata da servire.
 pts=[ob.matrix_world@v.co for v in ob.data.vertices]
 inside=[(p.x+43.2)**2+(p.y+26.74)**2<7.67**2 and 73.20<p.z<130.0 for p in pts]
 # Componenti connesse: identifica il tubo verticale, non la scala nuova.
 bm=bmesh.new();bm.from_mesh(ob.data);bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table();seen=set();remove_faces=set();component_meta=[]
 for v in bm.verts:
  if v.index in seen:continue
  stack=[v];vs=[];seen.add(v.index)
  while stack:
   a=stack.pop();vs.append(a)
   for e in a.link_edges:
    b=e.other_vert(a)
    if b.index not in seen:seen.add(b.index);stack.append(b)
  if not vs or not all(inside[a.index] for a in vs):continue
  component_faces=set(f for a in vs for f in a.link_faces)
  xyz=[pts[a.index] for a in vs];lo,hi=_bounds(xyz)
  # Componenti verticali e raccordi dello stesso tubo; coperture esterne lunghe
  # attraversanti la torre vengono ritagliate solo per le facce dentro la cavità.
  remove_faces.update(component_faces);component_meta.append({'min':lo,'max':hi,'vertices':len(vs),'faces':len(component_faces)})
 for f in bm.faces:
  if all(inside[v.index] for v in f.verts):remove_faces.add(f)
 removed=len(remove_faces)
 if remove_faces:bmesh.ops.delete(bm,geom=list(remove_faces),context='FACES')
 loose=[v for v in bm.verts if not v.link_faces]
 if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
 bm.to_mesh(ob.data);bm.free();ob.data.update()
 return {'object':ob.name,'faces_removed':removed,'components_removed':len(component_meta),'components':component_meta}



# Cavità cilindriche effettivamente usate da shells_v6; solo dettagli di
# facciata dentro questi vuoti vengono ritagliati. Gli arredi restano intatti.
CAVITIES=[('Scalinata',21.6,-97.028,16.02,60.22,147.0),
          ('Grifondoro',-43.2,-26.74,7.72,73.22,131.0)]
for _i,(_a,_z) in enumerate([(3.55,128),(3.87,134),(4.19,129)],1):
 CAVITIES.append(('Silente'+str(_i),21.6+16.5*math.cos(_a),-97.028+16.5*math.sin(_a),2.78,_z+.22,_z+14.0))

def _inside_cavity(p,c):
 _,x,y,r,z0,z1=c
 return z0+.002<p.z<z1-.002 and (p.x-x)**2+(p.y-y)**2<(r+.015)**2

def _cylinder(c):
 name,x,y,r,z0,z1=c;n=96;r+=.015
 vs=[(x+r*math.cos(i*math.tau/n),y+r*math.sin(i*math.tau/n),z) for z in [z0,z1] for i in range(n)]
 fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 me=bpy.data.meshes.new('TEMP pulizia '+name);me.from_pydata(vs,[],fs);me.update();ob=bpy.data.objects.new('TEMP pulizia '+name,me);bpy.context.scene.collection.objects.link(ob);return ob

def _difference(ob,cut):
 bpy.context.view_layer.objects.active=ob
 mod=ob.modifiers.new('Ritaglio dettaglio interno obsoleto','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;mod.use_self=True
 bpy.ops.object.modifier_apply(modifier=mod.name)

def _box_vertex_mask(ob,boxes):
 vs=np.array([tuple(ob.matrix_world@v.co) for v in ob.data.vertices]);mask=np.zeros(len(vs),dtype=bool)
 for bb in boxes:
  good=np.all((vs>=np.array(bb['aabb_lo']))&(vs<=np.array(bb['aabb_hi'])),axis=1);ids=np.flatnonzero(good)
  if not len(ids):continue
  ps=vs[ids];q=np.column_stack((ps@np.array(bb['t']),ps@np.array(bb['n']),ps[:,2]));valid=np.all((q>=np.array(bb['lo']))&(q<=np.array(bb['hi'])),axis=1);mask[ids[valid]]=True
 return mask

def _partial_clip(windows):
 candidates=[]
 for pane,frame,box in windows:
  pts=[frame.matrix_world@v.co for v in frame.data.vertices]
  cavities=[c for c in CAVITIES if any(_inside_cavity(v,c) for v in pts)]
  if cavities:candidates.append((pane,frame,box,cavities))
 if not candidates:return {'windows':[],'batches':[]}
 all_names={c[0] for _,_,_,cs in candidates for c in cs};cutters={c[0]:_cylinder(c) for c in CAVITIES if c[0] in all_names};report=[]
 for pane,frame,bb,cs in candidates:
  changes=[]
  for ob in [pane,frame]:
   backup=ob.data.copy();before=len(ob.data.polygons)
   for c in cs:
    if ob.data.polygons:_difference(ob,cutters[c[0]])
   if not ob.data.polygons:
    dead=ob.data;ob.data=backup;ob.hide_render=True;ob.hide_set(True);ob['Dettaglio esterno obsoleto']=True
    if dead.users==0:bpy.data.meshes.remove(dead)
    changes.append({'object':ob.name,'hidden':True,'faces_before':before})
   else:
    changes.append({'object':ob.name,'hidden':False,'faces_before':before,'faces_after':len(ob.data.polygons)})
    if backup.users==0:bpy.data.meshes.remove(backup)
  report.append({'pane':pane.name,'cavities':[c[0] for c in cs],'changes':changes})
 # Dal batch vengono estratti soltanto i componenti compresi nelle finestre
 # parzialmente obsolete. Il ritaglio non può toccare altri dettagli di facciata.
 batch_report=[];boxes=[bb for _,_,bb,_ in candidates]
 for name in BATCH_NAMES:
  ob=bpy.data.objects.get(name)
  if not ob or ob.type!='MESH':continue
  mask=_box_vertex_mask(ob,boxes);selected=[p for p in ob.data.polygons if all(mask[i] for i in p.vertices)]
  if not selected:batch_report.append({'object':name,'faces_selected':0});continue
  selected_ids={p.index for p in selected};ids=sorted({i for p in selected for i in p.vertices});remap={old:new for new,old in enumerate(ids)}
  tempme=bpy.data.meshes.new('TEMP frammenti '+name);tempme.from_pydata([tuple(ob.matrix_world@ob.data.vertices[i].co) for i in ids],[],[tuple(remap[i] for i in p.vertices) for p in selected]);tempme.update()
  for mat in ob.data.materials:tempme.materials.append(mat)
  for p,old in zip(tempme.polygons,selected):p.material_index=old.material_index;p.use_smooth=old.use_smooth
  temp=bpy.data.objects.new('TEMP frammenti '+name,tempme);bpy.context.scene.collection.objects.link(temp)
  before=len(temp.data.polygons)
  for cut in cutters.values():
   if temp.data.polygons:_difference(temp,cut)
  keep=[p for p in ob.data.polygons if p.index not in selected_ids];vs=[tuple(v.co) for v in ob.data.vertices];fs=[tuple(p.vertices) for p in keep];mi=[p.material_index for p in keep];sm=[p.use_smooth for p in keep]
  offset=len(vs);inv=ob.matrix_world.inverted();vs.extend(tuple(inv@(temp.matrix_world@v.co)) for v in temp.data.vertices);fs.extend(tuple(offset+i for i in p.vertices) for p in temp.data.polygons);mi.extend(p.material_index for p in temp.data.polygons);sm.extend(p.use_smooth for p in temp.data.polygons)
  out=bpy.data.meshes.new(ob.data.name+' facciate sostenute');out.from_pydata(vs,[],fs);out.update()
  for mat in ob.data.materials:out.materials.append(mat)
  for p,m,smooth in zip(out.polygons,mi,sm):p.material_index=m;p.use_smooth=smooth
  ob.data=out
  batch_report.append({'object':name,'faces_selected':before,'faces_returned':len(temp.data.polygons)})
  dead=temp.data;bpy.data.objects.remove(temp,do_unlink=True)
  if dead.users==0:bpy.data.meshes.remove(dead)
 for cut in cutters.values():
  dead=cut.data;bpy.data.objects.remove(cut,do_unlink=True)
  if dead.users==0:bpy.data.meshes.remove(dead)
 # Coordinate metriche sui frammenti ricostruiti; nessuna risorsa esterna.
 import sys
 sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v3'))
 import materials
 materials.assign_uvs([bpy.data.objects[n] for n in BATCH_NAMES if bpy.data.objects.get(n)]+[o for p,f,_,_ in candidates for o in [p,f] if not o.hide_render])
 return {'windows':report,'batches':batch_report}

def apply():
 col=bpy.data.collections.get(BODY_COLLECTION)
 if col is None:raise RuntimeError('Collezione degli involucri non trovata')
 bodies=[o for o in col.all_objects if o.type=='MESH' and o.data.polygons]
 bpy.context.view_layer.update();tree,owners,meta=_body_tree(bodies)
 cam=bpy.data.objects.get('Interni | Sala comune Grifondoro')
 ray_before=[_pixel_ray(cam,797,y) for y in [160,300,440,505]] if cam else []
 hidden=[];tested=0;kept=[];boxes=[];retained_windows=[]
 for pane in list(bpy.data.objects):
  if pane.type!='MESH' or pane.get('Interno') or ' | vetro' not in pane.name or pane.hide_render:continue
  frame=bpy.data.objects.get(pane.name.replace(' | vetro',' | cornice'))
  if not frame or frame.type!='MESH':continue
  data=_sample_outer(frame,pane)
  if not data:continue
  normal,poly,samples=data;c=sum(poly,Vector())/len(poly)
  relevant=[n for n,prefs,lo,hi in meta if any(pane.name.startswith(p) for p in prefs) and all(lo[k]-1.6<=c[k]<=hi[k]+1.6 for k in range(3))]
  if not relevant:continue
  tested+=1;supported=[]
  for j,p in enumerate(samples):
   hits=[]
   for sign in [-1,1]:
    h=tree.ray_cast(p+normal*(sign*.002),normal*sign,1.5)
    if h[0] is not None and h[3]<=.30:hits.append({'distance':h[3],'body':owners[h[2]] if h[2]<len(owners) else None})
   if hits:supported.append(j)
  if supported:
   kept.append({'pane':pane.name,'supported':len(supported)});retained_windows.append((pane,frame,_obb(poly,normal,.6)));continue
  for o in [pane,frame]:o.hide_render=True;o.hide_set(True);o['Dettaglio esterno obsoleto']=True
  box=_obb(poly,normal,.6);box['pane']=pane.name;boxes.append(box)
  hidden.append({'pane':pane.name,'frame':frame.name,'center':list(c),'bodies':relevant,'support_points':0})
 batches=[_trim_batch(bpy.data.objects.get(name),boxes) for name in BATCH_NAMES]
 partial=_partial_clip(retained_windows)
 pipe=_pipe_cleanup()
 bpy.context.view_layer.update()
 ray_after=[_pixel_ray(cam,797,y) for y in [160,300,440,505]] if cam else []
 result={'support_tolerance_m':.30,'windows_tested':tested,'unsupported_windows_hidden':len(hidden),'windows_retained':len(kept),'hidden':hidden,'retained_support_counts':kept,'batches':batches,'partial_clipping':partial,'pipe':pipe,'grifondoro_ray_before':ray_before,'grifondoro_ray_after':ray_after}
 bpy.context.scene['Pulizia facciate interne']='Finestre esterne senza muro e pluviale obsoleto della torre Grifondoro rimossi dopo unione dei vuoti.'
 return result


def _test():
 import sys
 R=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca')
 bpy.ops.wm.open_mainfile(filepath=str(R/'work/v6/Hogwarts-interni-pronto.blend'))
 result=apply();(R/'work/v6/facade-cleanup-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('FACADE_CLEANUP',result['windows_tested'],result['unsupported_windows_hidden'],result['batches'],result['pipe'],result['grifondoro_ray_before'],result['grifondoro_ray_after'],flush=True)
 if '--render' not in sys.argv:return
 s=bpy.context.scene;s.cycles.samples=16;s.cycles.adaptive_threshold=.05;s.render.resolution_x=900;s.render.resolution_y=630;s.render.resolution_percentage=100
 p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
 for d in p.devices:d.use=d.type=='METAL'
 s.cycles.device='GPU'
 for camera,file in [('Interni | Ufficio di Silente','silente'),('Interni | Sala comune Grifondoro','grifondoro')]:
  s.camera=bpy.data.objects[camera];s.render.filepath=str(R/'work/v6/qa'/('pulito-'+file+'.png'));bpy.ops.render.render(write_still=True);print('CLEANUP_RENDERED',file,flush=True)

if __name__=='__main__':_test()
