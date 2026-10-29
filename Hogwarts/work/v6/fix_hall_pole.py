"""Pulizia locale di pluviali e finestre obsolete dentro SalaGrande e vano scala.
apply() non salva, non renderizza e non modifica gli arredi degli interni.
"""
import bpy,bmesh,math,json,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
import facade_cleanup as F

ANGLE=math.atan2(.072*382,.066*600)
CO=math.cos(ANGLE);SI=math.sin(ANGLE)

def _inside_hall(p):
 dx=p.x-15;dy=p.y+142.104;u=CO*dx+SI*dy;v=-SI*dx+CO*dy
 return abs(u)<24.10 and abs(v)<7.60 and 60.22<p.z<94.05

def _inside_stairs(p):return (p.x-21.6)**2+(p.y+97.028)**2<15.97**2 and 60.22<p.z<146.5

def _inside(p):return _inside_hall(p) or _inside_stairs(p)

def _bounds(points):return [min(v[k] for v in points) for k in range(3)],[max(v[k] for v in points) for k in range(3)]

def _pipes():
 o=bpy.data.objects.get('Tetti | grondaie e pluviali')
 if not o:return {'object':None,'faces_removed':0}
 points=[o.matrix_world@v.co for v in o.data.vertices];inside=[_inside(p) for p in points]
 bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table();seen=set();discard=set();components=[]
 for v in bm.verts:
  if v.index in seen:continue
  todo=[v];seen.add(v.index);part=[]
  while todo:
   a=todo.pop();part.append(a)
   for e in a.link_edges:
    b=e.other_vert(a)
    if b.index not in seen:seen.add(b.index);todo.append(b)
  if part and all(inside[a.index] for a in part):
   faces=set(f for a in part for f in a.link_faces);discard.update(faces);ps=[points[a.index] for a in part];lo,hi=_bounds(ps)
   components.append({'bounds_min':lo,'bounds_max':hi,'vertices':len(part),'faces':len(faces),'region':'Sala Grande' if all(_inside_hall(p) for p in ps) else 'Torre della Scalinata'})
 # Segmenti di gronda eventualmente attraversanti il bordo: si eliminano solo
 # le facce interamente dentro uno dei due vuoti, lasciando intatta la parte esterna.
 for face in bm.faces:
  if all(inside[v.index] for v in face.verts):discard.add(face)
 count=len(discard)
 if discard:bmesh.ops.delete(bm,geom=list(discard),context='FACES')
 loose=[v for v in bm.verts if not v.link_faces]
 if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
 bm.to_mesh(o.data);bm.free();o.data.update()
 return {'object':o.name,'faces_removed':count,'components':components}


def _windows():
 hidden=[];boxes=[]
 for pane in list(bpy.data.objects):
  if pane.type!='MESH' or pane.get('Interno') or pane.hide_render or ' | vetro' not in pane.name:continue
  frame=bpy.data.objects.get(pane.name.replace(' | vetro',' | cornice'))
  if not frame or frame.type!='MESH' or not pane.data.polygons:continue
  pts=[pane.matrix_world@v.co for v in pane.data.vertices];fr=[frame.matrix_world@v.co for v in frame.data.vertices]
  # Tutto il telaio deve essere interno: nessuna finestra rimasta sulla facciata
  # esterna viene nascosta. Funziona sia con vecchi pannelli sia con anelli aperti.
  allpoints=pts+fr
  hall=all(_inside_hall(p) for p in allpoints);stairs=all(_inside_stairs(p) for p in allpoints)
  if not(hall or stairs):continue
  nv=len(pane.data.vertices)//2;poly=fr[:nv]
  cap=max(pane.data.polygons,key=lambda p:len(p.vertices));normal=(pane.matrix_world.to_3x3()@cap.normal).normalized()
  box=F._obb(poly,normal,.6);boxes.append(box)
  for ob in [pane,frame]:ob.hide_render=True;ob.hide_set(True);ob['Dettaglio esterno obsoleto']=True
  lo,hi=_bounds(fr);hidden.append({'pane':pane.name,'frame':frame.name,'region':'Sala Grande' if hall else 'Torre della Scalinata','bounds_min':lo,'bounds_max':hi})
 batches=[F._trim_batch(bpy.data.objects.get(name),boxes) for name in F.BATCH_NAMES]
 return {'hidden':hidden,'batches':batches}


def _ray_proof():
 result={}
 specs=[('Camera | Interno Sala Grande',2000,1350,[(1330,220),(1330,600),(1330,900)]),('Interni | Grande scalinata dal ballatoio',1600,1100,[(300,880),(320,805),(310,945),(458,950),(485,800),(512,650),(530,550),(582,320),(605,200)])]
 for name,w,h,pixels in specs:
  cam=bpy.data.objects.get(name)
  if cam:result[name]=[F._pixel_ray(cam,x,y,w,h) for x,y in pixels]
 return result


def apply():
 bpy.context.view_layer.update();before=_ray_proof();pipes=_pipes();windows=_windows();bpy.context.view_layer.update();after=_ray_proof()
 # Verifica puntuale: lo stesso raggio del palo nellaSalaGrande non deve
 # incontrare più il batch del pluviale rimosso.
 hallafter=after.get('Camera | Interno Sala Grande',[])
 if any(r['object']=='Tetti | grondaie e pluviali' for r in hallafter):raise RuntimeError('Residuo del palo SalaGrande ancora presente')
 empty=[o.name for o in bpy.data.objects if o.type=='MESH' and not o.data.polygons and not o.hide_render]
 report={'pipes':pipes,'windows':windows,'rays_before':before,'rays_after':after,'empty_visible_meshes':empty}
 bpy.context.scene['Pulizia finale SalaGrande e Scalinata']='Rimossi soltanto pluviali e finestre esterne rimasti interamente nei vuoti interni.'
 return report


if __name__=='__main__':
 R=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca')
 bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/Hogwarts-interni.blend'));r=apply()
 (R/'work/v6/hall-pole-check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
 print('POLE_CHECK',json.dumps(r,ensure_ascii=False),flush=True)
