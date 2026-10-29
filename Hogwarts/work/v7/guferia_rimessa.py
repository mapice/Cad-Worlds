"""Guferia, rimessa e piccoli coronamenti delle serre. Applicare al finale V6.
Non salva e non renderizza; scala della rimessa, roccia V5 e interni invariati.
"""
import bpy,bmesh,math,random,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import kit_v7 as K
A=K.A
X,Y=-190.8,74.872

def _hide(o,hidden):
 if o and not o.hide_render:o.hide_render=True;o.hide_set(True);hidden.append(o.name)

def _diff(ob,cutter,modified):
 # I pannelli ogivali ereditati hanno orientamento opposto a un solido cutter.
 # Ricalcolare le normali assicura che DIFFERENCE sottragga il volume interno.
 bm=bmesh.new();bm.from_mesh(cutter.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(cutter.data);bm.free();cutter.data.update()
 bpy.context.view_layer.update();bpy.context.view_layer.objects.active=ob;ob.hide_set(False)
 m=ob.modifiers.new('V7 | apertura funzionale','BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=cutter
 bpy.ops.object.modifier_move_to_index(modifier=m.name,index=0)
 bpy.ops.object.modifier_apply(modifier=m.name)
 if not ob.data.polygons:raise RuntimeError('Oggetto svuotato: '+ob.name)
 if ob.name not in modified:modified.append(ob.name)

def _remove_cutter(o):
 me=o.data;bpy.data.objects.remove(o,do_unlink=True)
 if me.users==0:bpy.data.meshes.remove(me)

def _trim_lead(modified):
 for name in ['Vetrate | reticolo in piombo','Vetrate | trafori gotici']:
  o=bpy.data.objects.get(name)
  if not o:continue
  bm=bmesh.new();bm.from_mesh(o.data)
  discard=[f for f in bm.faces if all(101.7<(o.matrix_world@v.co).z<109.0 and math.hypot((o.matrix_world@v.co).x-X,(o.matrix_world@v.co).y-Y)<8.6 for v in f.verts)]
  if discard:
   bmesh.ops.delete(bm,geom=discard,context='FACES');bm.to_mesh(o.data);o.data.update();modified.append(name)
  bm.free()

def _owl(batch,p,angle,scale=1):
 co,si=math.cos(angle),math.sin(angle)
 def q(u,v,w):return (p[0]+scale*(u*co-v*si),p[1]+scale*(u*si+v*co),p[2]+scale*w)
 batch.ellipsoid(q(0,0,.36),.24*scale,.19*scale,.34*scale,n=12,rings=7,mat=0)
 batch.ellipsoid(q(0,-.012,.75),.235*scale,.19*scale,.22*scale,n=12,rings=6,mat=1)
 for side in [-1,1]:
  batch.ellipsoid(q(side*.20,0,.35),.095*scale,.15*scale,.27*scale,n=9,rings=5,mat=0)
  batch.ellipsoid(q(side*.10,-.174,.78),.082*scale,.035*scale,.092*scale,n=10,rings=5,mat=2)
  batch.ellipsoid(q(side*.10,-.206,.78),.038*scale,.015*scale,.048*scale,n=9,rings=4,mat=3)
  batch.tube(q(side*.16,.01,.87),q(side*.19,.015,1.04),.065*scale,.005*scale,n=7,mat=0)
  for j in range(3):batch.tube(q(side*.11+(j-1)*.04,-.03,.07),q(side*.11+(j-1)*.045,-.18,.025),.012*scale,n=5,mat=3)
 batch.add([q(-.055,-.20,.70),q(.055,-.20,.70),q(0,-.29,.60)],[(0,1,2)],3)
 # Ventre piumato: file di piccole incisioni geometriche, leggibili da vicino.
 for row in range(3):
  for col in range(3):
   u=(col-1)*.075;w=.25+row*.10
   batch.tube(q(u-.025,-.181,w+.03),q(u,-.196,w),.008*scale,n=5,mat=1)
   batch.tube(q(u,-.196,w),q(u+.025,-.181,w+.03),.008*scale,n=5,mat=1)

def _owlery_stairs(hidden):
 for o in list(bpy.data.objects):
  if o.name.startswith('Civettaia | gradino'):_hide(o,hidden)
 start=Vector((X,Y-10.18));end=Vector((-177.,70.));d=end-start;length=d.length;t=d.normalized();n=Vector((-t.y,t.x));count=110
 samples=[]
 for j in range(count+1):
  p=start+d*(j/count);hs=[K.ground(*(p+n*q)) for q in [-1.15,0,1.15]];samples.append((p,max(hs),min(hs)))
 # Quote monotone: i gradini seguono l'inviluppo del pendio senza penetrarlo.
 envelope=[0]*(count+1);level=-1e9
 for j in range(count,-1,-1):level=max(level,samples[j][1]+.13);envelope[j]=level
 top=max(90.6,envelope[0]);step=.175
 heights=[top-step*math.floor(max(0,(top-z))/step) for z in envelope]
 b=K.Batch('Guferia | scala di accesso e appoggi',['stone','trim']);r=K.Batch('Guferia | corrimano della scala',['v7_iron']);segments=[]
 j=0
 while j<count:
  k=j+1
  while k<count and abs(heights[k]-heights[j])<.001:k+=1
  p=(samples[j][0]+samples[k][0])*.5;run=(k-j)*length/count+.012;z=heights[j]
  bottom=min(h[2] for h in samples[j:k+1])-.2;hh=max(.25,z-bottom)
  b.box((p.x,p.y,z-hh*.5),(run,2.5,hh),0,math.atan2(t.y,t.x))
  b.box((p.x,p.y,z+.025),(run,2.6,.05),1,math.atan2(t.y,t.x));segments.append((j,k,z));j=k
 # Ultimo raccordo corto, aderente al sentiero.
 for side in [-1,1]:
  prev=None
  for j in range(0,count+1,10):
   p=samples[j][0]+n*(side*1.27);z=heights[j]
   r.tube((p.x,p.y,z),(p.x,p.y,z+1.05),.045,n=7)
   if prev:r.tube(prev,(p.x,p.y,z+1.05),.04,n=7)
   prev=(p.x,p.y,z+1.05)
 b.finish();r.finish()
 controls=[tuple(end),(-165,83),(-182,112),(-151,125),(-166,146),(-138,164),(-120,175)]
 pathpts=K.smooth_path(controls,.9);path=K.path('Guferia | sentiero fino al nodo settentrionale',pathpts,2.5,'path',.065)
 # La quota finale del gradino considera il lato alto del pendio trasversale.
 # Nei primi8m raccordare entrambi i bordi alla stessa soglia evita un salto
 # centrale, senza abbassare il terreno o lasciare il cammino sospeso.
 ramp=K.Batch('Guferia | sostegno del raccordo al sentiero',['stone']);ramp_top=[];ramp_bottom=[];distance=0.;ramp_end=0
 endpoint_z=segments[-1][2]+.025
 for i,p in enumerate(pathpts):
  if i:distance+=math.dist(pathpts[i-1],p)
  if distance>8.0:break
  t=distance/8.0;w=1-t*t*(3-2*t)
  for side in [0,1]:
   v=path.data.vertices[2*i+side];old=v.co.copy();v.co.z=old.z*(1-w)+endpoint_z*w
   ramp_top.append(tuple(v.co));ramp_bottom.append((old.x,old.y,old.z-.20))
  ramp_end=i
 if ramp_end:
  nverts=len(ramp_top);vs=ramp_top+ramp_bottom;fs=[]
  for i in range(ramp_end):
   a=2*i;fs.extend([(a,a+2,a+2+nverts,a+nverts),(a+1,a+1+nverts,a+3+nverts,a+3)])
  fs.extend([(0,nverts,nverts+1,1),(nverts-2,nverts-1,2*nverts-1,2*nverts-2)])
  ramp.add(vs,fs);ramp.finish()
 path.data.update();K.M.assign_uvs([path])
 # Assenza di alberi nel percorso: si nascondono soltanto istanze vicine.
 cleared=[]
 for o in bpy.data.objects:
  if o.name.startswith(('Bosco |','Sottobosco esteso |')) and not o.hide_render:
   p=o.matrix_world.translation
   if min((p.x-x)**2+(p.y-y)**2 for x,y in pathpts)<3.6**2:_hide(o,cleared)
 # Tutti i campioni della scala risultano sotto al piano di calpestio.
 gaps=[heights[j]-samples[j][1] for j in range(count+1)]
 if min(gaps)<.10:raise RuntimeError('Il terreno supera un gradino Guferia')
 return {'treads':len(segments),'riser':step,'clear_width':2.5,'support_probes':len(gaps),'minimum_ground_clearance':min(gaps),'path_points':len(pathpts),'path_vegetation_hidden':cleared,'hidden_original_steps':10,'stair_path_join_delta':max(abs(path.data.vertices[j].co.z-endpoint_z) for j in [0,1]),'ramp_length':8.0}

def _owlery(modified,hidden):
 col=K.collection('86 • Guferia e percorso sulla collina')
 targets=[bpy.data.objects[n] for n in ['Civettaia | fusto','Civettaia | basamento']]+[o for o in bpy.data.objects if o.name.startswith('Civettaia | cornice')]
 hollow=A.cone('TEMP | vano Guferia',(X,Y,90.6),5.65,5.65,25,'stone',96)
 for o in targets:_diff(o,hollow,modified)
 _remove_cutter(hollow)
 body=bpy.data.objects['Civettaia | fusto'];window_rays=[];open_frames=[]
 for i in range(10):
  a=math.tau*i/10;nx,ny=math.cos(a),math.sin(a)
  cut=A.panel('TEMP | nicchia aperta Guferia',(X+6.6*nx,Y+6.6*ny,102.0),1.65,6.1,a+math.pi/2,None,4.5)
  for o in targets:
   if o.name!='Civettaia | basamento':_diff(o,cut,modified)
  frame_name='Civettaia | nicchie alte | cornice'+('' if i==0 else '.%03d'%i)
  frame=bpy.data.objects[frame_name]
  # Le cornici originali sono prismi pieni: aprire anche loro, non solo il fusto.
  bm=bmesh.new();bm.from_mesh(frame.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(frame.data);bm.free();frame.data.update()
  _diff(frame,cut,modified);open_frames.append(frame)
  _remove_cutter(cut)
  for tangential in [-.5,0,.5]:
   for height in [102.55,104.3,105.8]:
    window_rays.append(((X+8.8*nx-tangential*ny,Y+8.8*ny+tangential*nx,height),(-nx,-ny,0)))
 for o in list(bpy.data.objects):
  if o.name.startswith('Civettaia | nicchie alte') and ('vetro' in o.name or 'montante' in o.name or 'traversa' in o.name):_hide(o,hidden)
 _trim_lead(modified)
 door=A.panel('TEMP | ingresso Guferia',(X,Y-6.8,90.6),2.4,4.6,0,None,4.2)
 for o in targets:
  if o.name in ['Civettaia | fusto','Civettaia | basamento']:_diff(o,door,modified)
 _remove_cutter(door)
 # Due stipiti e arco leggero seguono il taglio reale.
 for sx in [-1,1]:A.box('Guferia | stipite ingresso',(X+sx*1.35,Y-7.0,92.15),(.28,.38,3.1),'trim')
 # Pavimento anulare in quota e scala interna per raggiungere i posatoi.
 b=K.Batch('Guferia | ballatoio e scala interna',['v7_wood','v7_iron'])
 n=96;vs=[]
 for z in [101.58,101.78]:
  for rr in [4.25,5.65]:
   vs.extend((X+rr*math.cos(j*math.tau/n),Y+rr*math.sin(j*math.tau/n),z) for j in range(n))
 fs=[]
 for j in range(n):
  k=(j+1)%n;fs.extend([(j,k,k+n,j+n),(j+2*n,j+3*n,k+3*n,k+2*n),(j,j+2*n,k+2*n,k),(j+n,k+n,k+3*n,j+3*n)])
 b.add(vs,fs,0)
 for j in range(64):
  a=-math.pi/2+j*math.tau*2.5/64;aa=a+.23;z=90.6+(j+1)*11.18/64
  verts=[(X+rr*math.cos(angle),Y+rr*math.sin(angle),zz) for zz in [z-.12,z] for rr,angle in [(2.4,a),(4.2,a),(4.2,aa),(2.4,aa)]]
  b.add(verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],0)
 b.finish()
 roost=K.Batch('Guferia | posatoi e nicchie di legno',['v7_wood','v7_linen'])
 owls=K.Batch('Guferia | gufi sui posatoi',['v7_wood','v7_linen','v7_yellow','v7_iron'])
 for i in range(10):
  a=math.tau*i/10;nx,ny=math.cos(a),math.sin(a);t=Vector((-ny,nx,0));p=Vector((X+5.3*nx,Y+5.3*ny,102.35))
  roost.tube(p-t*.85,p+t*.85,.085,n=9)
  for lev in [0,1]:
   q=Vector((X+5.15*nx,Y+5.15*ny,109.1+lev*1.5));roost.box(q,(1.35,.9,.12),0,a+math.pi/2)
   roost.box(q+Vector((0,0,.55)),(1.35,.9,.12),0,a+math.pi/2)
   for s in [-1,1]:roost.box(q+t*(s*.64)+Vector((0,0,.27)),(.08,.9,.55),0,a+math.pi/2)
  if i in [0,2,4,6,7,8]:_owl(owls,(p.x,p.y,p.z+.09),a+math.pi/2,.95+(i%3)*.10)
 roost.finish();owls.finish()
 stairs=_owlery_stairs(hidden)
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();blocked=[]
 # Verifica congiunta in coordinate globali: fusto, fasce, cornici e ogni
 # modanatura o reticolo visibile nella regione delle dieci aperture.
 candidates=[o for o in bpy.data.objects if o.type=='MESH' and not o.hide_render and (
  o.name.startswith(('Civettaia | fusto','Civettaia | cornice','Civettaia | nicchie alte')) or
  o.name in ['Finestre | modanature esterne e davanzali','Vetrate | reticolo in piombo','Vetrate | trafori gotici'])]
 verts=[];faces=[];owners=[]
 for ob in candidates:
  ev=ob.evaluated_get(dg);me=ev.to_mesh();world=[ob.matrix_world@v.co for v in me.vertices]
  for f in me.polygons:
   ps=[world[j] for j in f.vertices]
   if max(p.z for p in ps)<101.4 or min(p.z for p in ps)>109.0 or all(math.hypot(p.x-X,p.y-Y)>9.4 for p in ps):continue
   idx=len(verts);verts.extend(ps);faces.append(tuple(range(idx,idx+len(ps))));owners.append(ob.name)
  ev.to_mesh_clear()
 tree=BVHTree.FromPolygons(verts,faces)
 for p,d in window_rays:
  hit=tree.ray_cast(Vector(p),Vector(d),3.6)
  if hit[0] is not None:blocked.append({'origin':tuple(p),'object':owners[hit[2]],'hit':tuple(hit[0])})
 if blocked:raise RuntimeError('Aperture Guferia ostruite: '+str(blocked))
 K.M.assign_uvs(targets+open_frames)
 full_camera=K.camera('Camera | V7 Guferia e posatoi',(-258,0,134),(X,Y,110),44)
 K.camera('Camera | V7 Guferia dettaglio gufi',(-229,31,113),(X,Y,105),66)
 from bpy_extras.object_utils import world_to_camera_view
 bpy.context.view_layer.update();scene=bpy.context.scene;oldres=(scene.render.resolution_x,scene.render.resolution_y);scene.render.resolution_x=1200;scene.render.resolution_y=850
 points=[world_to_camera_view(scene,full_camera,ob.matrix_world@v.co) for ob in bpy.data.objects if ob.type=='MESH' and not ob.hide_render and (ob.name.startswith('Civettaia |') or ob.name=='Guferia | scala di accesso e appoggi') for v in ob.data.vertices]
 bounds=[min(p.x for p in points),max(p.x for p in points),min(p.y for p in points),max(p.y for p in points)]
 scene.render.resolution_x,scene.render.resolution_y=oldres
 if min(bounds[0],bounds[2])<.025 or max(bounds[1],bounds[3])>.975:raise RuntimeError('Guferia tagliata dalla camera: '+str(bounds))
 return {'open_arches':10,'open_frame_rings':10,'owls':6,'clear_window_probes':len(window_rays),'probe_objects':[o.name for o in candidates],'full_camera_bounds':bounds,'stairs':stairs,'objects':len(col.objects)}

def _hull(ob,cx,y0,modified):
 widths=[1.0,1.25,1.4,1.52,1.55,1.5,1.35,1.14,.84,.48,.04];ny=len(widths);ns=13;vs=[]
 for inner in [False,True]:
  for j,ww in enumerate(widths):
   yy=y0+6.6*j/(ny-1);bottom=.82+.45*(j/(ny-1))**4
   for k in range(ns):
    a=math.pi*k/(ns-1);x=cx+ww*math.cos(a)*( .95 if inner else 1);z=2.2-(2.2-bottom)*math.sin(a)+(.09*math.sin(a) if inner else 0)
    vs.append((x,yy,z))
 fs=[];mi=[];offset=ny*ns
 for layer in [0,offset]:
  for j in range(ny-1):
   for k in range(ns-1):
    a=layer+j*ns+k;f=(a,a+ns,a+ns+1,a+1);fs.append(tuple(reversed(f)) if layer else f);mi.append(0 if k%3 else 1)
 for j in range(ny-1):
  for k in [0,ns-1]:a=j*ns+k;fs.append((a,a+offset,a+ns+offset,a+ns));mi.append(0)
 for j in [0,ny-1]:
  for k in range(ns-1):a=j*ns+k;fs.append((a,a+1,a+1+offset,a+offset));mi.append(0)
 me=bpy.data.meshes.new(ob.data.name+' | fasciame curvo');me.from_pydata(vs,[],fs);me.materials.append(A.M['v7_wood']);me.materials.append(A.M['int_oak'])
 for f,i in zip(me.polygons,mi):f.material_index=i;f.use_smooth=True
 ob.data=me;modified.append(ob.name);K.M.assign_uvs([ob])

def _boathouse(modified,hidden):
 col=K.collection('87 • Rimessa, approdi e banderuola');x,y=175.8,-135.992
 molo=bpy.data.objects['Rimessa | molo di pietra']
 for cx in [x-6,x+5]:
  cut=A.box('TEMP | canale di approdo',(cx,y-8.1,1.6),(4.6,16.2,5.2),None)
  _diff(molo,cut,modified);_remove_cutter(cut)
 K.M.assign_uvs([molo])
 # Le barche rimangono le due esistenti: fasciame curvo, non doppioni sovrapposti.
 boats=sorted([o for o in bpy.data.objects if o.name.startswith('Barca | scafo')],key=lambda o:o.name)
 for ob,cx in zip(boats,[x-6,x+5]):_hull(ob,cx,y-14,modified)
 for ob in list(bpy.data.objects):
  if ob.name.startswith('Barca | falchetta'):_hide(ob,hidden)
 details=K.Batch('Rimessa | fasciame, remi e cime',['v7_wood','int_oak','v7_iron','v7_linen'])
 wood=K.Batch('Rimessa | passerelle e bitte',['v7_wood','v7_iron','stone'])
 widths=[1.0,1.25,1.4,1.52,1.55,1.5,1.35,1.14,.84,.48,.04]
 for cx in [x-6,x+5]:
  for side in [-1,1]:
   for j in range(10):details.tube((cx+side*widths[j],y-14+j*.66,2.22),(cx+side*widths[j+1],y-14+(j+1)*.66,2.22),.085,n=9)
  for j in [1,3,5,7]:
   yy=y-14+j*.66;ww=widths[j]
   points=[(cx+ww*.94*math.cos(math.pi*k/12),yy,2.2-1.28*math.sin(math.pi*k/12)+.12) for k in range(13)]
   for a,b in zip(points,points[1:]):details.tube(a,b,.045,n=7,mat=1)
  for side in [-1,1]:
   a=Vector((cx-side*.9,y-12.4,2.55));b=Vector((cx+side*1.1,y-9.0,2.55));details.tube(a,b,.045,n=8,mat=1)
   d=(b-a).normalized();n=Vector((-d.y,d.x,0));p=b+d*.48
   details.add([b-n*.06,b+n*.06,p+n*.18,p+d*.38+n*.11,p+d*.38-n*.11,p-n*.18],[(0,1,2,3,4,5)],1)
  # La cima si lega a una bitta laterale, lasciando il canale centrale libero.
  bx=cx+2.8;by=y-9;wood.tube((bx,by,4.05),(bx,by,4.85),.13,n=12,mat=1);wood.tube((bx-.28,by,4.68),(bx+.28,by,4.68),.10,n=9,mat=1)
  rope=[(cx+.9,y-12.2,2.28),(cx+1.5,y-11.2,2.35),(bx-.5,by-.7,3.5),(bx,by,4.6)]
  for a,b in zip(rope,rope[1:]):details.tube(a,b,.026,n=7,mat=3)
  details.ring((bx,by,4.62),.17,.028,mat=3,n=28)
  for j in range(14):wood.box((bx,by-2.6+j*.42,4.065),(1.0,.36,.13),0)
 # Cerchi di cima e anelli d'ormeggio sui due angoli esterni del molo.
 for bx in [x-11.5,x+11.5]:
  for yy in [y-9,y-4]:
   wood.box((bx,yy,4.14),(.55,.55,.28),2);details.ring((bx,yy,4.38),.23,.055,axis='Y',mat=2,n=28)
  for rr in [.34,.43,.52]:details.ring((bx,y-2,4.1),rr,.03,mat=3,n=36)
 details.finish();wood.finish()
 vane=K.Batch('Rimessa | banderuola strega e gatto',['v7_iron'])
 zz=26.8;vane.tube((x,y,24.2),(x,y,zz+2),.045,n=10)
 vane.tube((x-2.2,y,zz),(x+2.1,y,zz),.055,n=8)
 # Sagoma metallica ritagliata nel piano del colmo: cappello, mantello e scopa.
 poly=[(-.70,.22),(-.32,.8),(-.45,1.15),(-.20,1.28),(-.15,1.9),(.2,1.3),(.47,1.22),(.18,1.14),(.38,.90),(.30,.60),(.78,.15),(.35,.05),(.0,.15)]
 vs=[(x+u,y+dep,zz+w) for dep in [-.025,.025] for u,w in poly];n=len(poly)
 vane.add(vs,[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)])
 for j in range(7):vane.tube((x-1.1,y,zz-.03),(x-2.1,y,zz-.25+j*.08),.025,n=5)
 # Gatto seduto dietro la strega, con orecchie e coda curva.
 vane.ellipsoid((x+1.15,y,zz+.31),.23,.045,.33,n=12,rings=6,mat=0)
 vane.ellipsoid((x+1.14,y,zz+.69),.18,.045,.17,n=12,rings=5,mat=0)
 for sx in [-1,1]:vane.tube((x+1.14+sx*.12,y,zz+.77),(x+1.14+sx*.14,y,zz+.98),.06,.005,n=6)
 tail=[(x+1.30,y,zz+.10),(x+1.65,y,zz+.18),(x+1.76,y,zz+.44),(x+1.65,y,zz+.62)]
 for a,b in zip(tail,tail[1:]):vane.tube(a,b,.045,n=7)
 vane.finish();K.camera('Camera | V7 rimessa e barche',(219,-194,42),(x,y-5,8),47)
 # I due raggi seguono l'acqua attraverso la parte asportata del molo.
 bpy.context.view_layer.update();tree=BVHTree.FromObject(molo,bpy.context.evaluated_depsgraph_get());blocked=[]
 for cx in [x-6,x+5]:
  for dx in [-1,0,1]:
   if tree.ray_cast(Vector((cx+dx,y-15,1.2)),Vector((0,1,0)),13)[0] is not None:blocked.append(cx+dx)
 if blocked:raise RuntimeError('Canali della rimessa ostruiti')
 return {'boats_refined':len(boats),'water_channels':2,'clear_boat_channel_probes':6,'objects':len(col.objects)}

def _dragon(b,p,angle,scale=1):
 co,si=math.cos(angle),math.sin(angle)
 def q(u,v,w):return (p[0]+scale*(u*co-v*si),p[1]+scale*(u*si+v*co),p[2]+scale*w)
 b.ellipsoid(q(0,0,.35),.5*scale,.19*scale,.25*scale,n=12,rings=6)
 b.tube(q(.27,0,.45),q(.48,0,.83),.16*scale,.10*scale,n=9)
 b.ellipsoid(q(.53,0,.90),.22*scale,.14*scale,.15*scale,n=10,rings=5)
 b.tube(q(.62,0,.88),q(.85,0,.83),.10*scale,.07*scale,n=8)
 for s in [-1,1]:
  b.tube(q(.45,s*.09,.98),q(.33,s*.14,1.20),.045*scale,.005*scale,n=6)
  b.add([q(-.08,s*.10,.52),q(-.24,s*.92,1.2),q(.18,s*.68,.77),q(.34,s*.22,.65)],[(0,1,2,3)])
  for u in [-.2,.25]:b.tube(q(u,s*.14,.3),q(u+.10,s*.32,.05),.065*scale,.04*scale,n=7)
 tail=[q(-.3,0,.35),q(-.7,0,.35),q(-.95,.14,.50),q(-.99,.19,.78),q(-.80,.17,.88)]
 for a,c in zip(tail,tail[1:]):b.tube(a,c,.045*scale,n=7)

def _greenhouses():
 col=K.collection('88 • Coronamenti e attrezzi delle serre');dragons=K.Batch('Serre | draghetti dei colmi',['v7_iron'])
 count=0
 for o in list(bpy.data.objects):
  if o.type!='MESH' or not o.name.startswith('Serra ') or ' | colmo' not in o.name:continue
  pts=[o.matrix_world@v.co for v in o.data.vertices];lo=[min(p[k] for p in pts) for k in range(3)];hi=[max(p[k] for p in pts) for k in range(3)]
  longx=hi[0]-lo[0]>hi[1]-lo[1];cx=(lo[0]+hi[0])/2;cy=(lo[1]+hi[1])/2;ang=0 if longx else math.pi/2
  for side in [-1,1]:
   px=(hi[0]-1.4 if side>0 else lo[0]+1.4) if longx else cx
   py=cy if longx else (hi[1]-1.4 if side>0 else lo[1]+1.4)
   _dragon(dragons,(px,py,hi[2]),ang+(math.pi if side<0 else 0),1.05);count+=1
 dragons.finish();props=K.Batch('Serre | banchi, attrezzi e annaffiatoi',['v7_wood','v7_iron','v7_linen','v7_dirt'])
 for y in [118.,128.]:
  x=75.;z=55.4
  props.box((x,y,z+1.0),(3.2,1.0,.16),0)
  for sx in [-1,1]:
   for sy in [-1,1]:props.box((x+sx*1.35,y+sy*.35,z+.48),(.13,.13,.96),0)
  # Sacchi da terriccio, cassetta e annaffiatoio; i vasi originali restano invariati.
  for sx in [-.8,0]:props.ellipsoid((x+sx,y,z+1.35),.32,.25,.28,n=10,rings=5,mat=2)
  props.tube((x+.9,y,z+1.1),(x+.9,y,z+1.7),.24,n=16,mat=1)
  props.tube((x+1.05,y,z+1.25),(x+1.62,y,z+1.65),.055,.025,n=8,mat=1)
  props.ring((x+.78,y,z+1.46),.23,.035,axis='Y',mat=1,n=24)
  for j in range(3):
   xx=x-1.0+j*.35;props.tube((xx,y+.35,z+1.13),(xx+.1,y-.4,z+1.13),.018,n=6,mat=0)
   props.box((xx+.1,y-.45,z+1.13),(.13,.2,.025),1)
 props.finish();K.camera('Camera | V7 draghetti delle serre',(128,161,84),(75,119,61),46)
 return {'ridge_dragons':count,'outdoor_worktables':2,'objects':len(col.objects)}

def apply():
 K.init();modified=[];hidden=[];before=set(bpy.data.objects)
 owl=_owlery(modified,hidden);boat=_boathouse(modified,hidden);green=_greenhouses()
 new=[o for o in bpy.data.objects if o not in before];empty=[o.name for o in new if o.type=='MESH' and not o.data.polygons]
 if empty:raise RuntimeError('Nuove mesh vuote: '+str(empty))
 return {'owlery':owl,'boathouse':boat,'greenhouses':green,'modified_objects':modified,'hidden_objects':hidden,'new_objects':len(new),'new_faces':sum(len(o.data.polygons) for o in new if o.type=='MESH'),'empty_meshes':empty}

if __name__=='__main__':
 import json
 bpy.ops.wm.open_mainfile(filepath=str(K.R/'outputs/Hogwarts-interni.blend'))
 report=apply();(K.R/'work/v7/guferia-rimessa-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('GUFERIA_RIMESSA_CHECK',json.dumps(report,ensure_ascii=False),flush=True)
