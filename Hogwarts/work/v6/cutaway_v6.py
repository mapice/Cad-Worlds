import bpy,bmesh
from mathutils import Vector

def apply():
 col=bpy.data.collections['79 • Presentazione degli interni aperti']
 cam=bpy.data.objects['Camera | disposizione degli interni'];direction=Vector((cam.location.x-5,cam.location.y+45,0)).normalized();created=[]
 for ob in list(bpy.data.collections['80 • Involucri esterni apribili'].objects):
  if ob.type!='MESH' or not ob.data.polygons:continue
  world=[ob.matrix_world@v.co for v in ob.data.vertices];cx=(min(v.x for v in world)+max(v.x for v in world))/2;cy=(min(v.y for v in world)+max(v.y for v in world))/2
  bm=bmesh.new();bm.from_mesh(ob.data)
  remove=[]
  for face in bm.faces:
   q=ob.matrix_world@face.calc_center_median()
   if Vector((q.x-cx,q.y-cy,0)).dot(direction)>.03:remove.append(face)
  bmesh.ops.delete(bm,geom=remove,context='FACES')
  if not bm.faces:bm.free();continue
  me=bpy.data.meshes.new(ob.data.name+' | sezione');bm.to_mesh(me);bm.free();me.update()
  for mat in ob.data.materials:me.materials.append(mat)
  copy=bpy.data.objects.new('Sezione | '+ob.name,me);col.objects.link(copy);copy.matrix_world=ob.matrix_world.copy();copy.hide_select=True;copy['Solo vista aperta']=True;created.append(copy.name)
 # La loggia dell'osservatorio dà una chiusura leggibile all'arrivo della chiocciola.
 for ob in list(bpy.data.objects):
  if ob.type!='MESH' or not ob.name.startswith(('Astronomia | osservatorio |','Astronomia | loggia inferiore |')):continue
  copy=ob.copy();copy.data=ob.data;copy.name='Sezione | '+ob.name;col.objects.link(copy);copy.hide_select=True;copy['Solo vista aperta']=True;created.append(copy.name)
 return {'section_objects':len(created),'names':created}
