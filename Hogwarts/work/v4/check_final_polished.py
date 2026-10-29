import bpy,sys,json,hashlib,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca')
FILE=ROOT/'outputs/Hogwarts-Lago-Nero.blend'
sys.path.insert(0,str(ROOT/'work/v4'))
bpy.ops.wm.open_mainfile(filepath=str(FILE))
import ecology_v4
build=json.loads((ROOT/'work/v4/build-check.json').read_text())
polish=json.loads((ROOT/'work/v4/polish-check.json').read_text())
meshes=[o for o in bpy.data.objects if o.type=='MESH']
empty=[];nonfinite=[];missing_material=[]
for o in meshes:
 if not o.data.vertices or not o.data.polygons:empty.append(o.name)
 if any(not math.isfinite(q) for v in o.data.vertices for q in v.co) or any(not math.isfinite(q) for row in o.matrix_world for q in row):nonfinite.append(o.name)
 if not o.data.materials or any(m is None for m in o.data.materials):missing_material.append(o.name)
external_images=[{'name':i.name,'filepath':i.filepath} for i in bpy.data.images if i.source=='FILE' and not i.packed_file]
libraries=[l.filepath for l in bpy.data.libraries]
external_fonts=[f.filepath for f in bpy.data.fonts if f.filepath not in ('','<builtin>') and not getattr(f,'packed_file',None)]
new_visibility={}
for n in ['Colli e sponde | superficie continua','Lago Nero | superficie estesa']:
 o=bpy.data.objects.get(n)
 new_visibility[n]={'exists':o is not None,'hide_render':bool(o.hide_render) if o else None,'hidden_viewport':bool(o.hide_get()) if o else None,'faces':len(o.data.polygons) if o else None}
old_hidden={}
for n in ['Lago Nero | acqua','Colline occidentali | pareti rocciose','Studio | piano','Bosco sulle colline','Conifere | tronchi e rami','Conifere | palchi e aghi','Rocce | detriti di riva']:
 o=bpy.data.objects.get(n);old_hidden[n]={'exists':o is not None,'hide_render':bool(o.hide_render) if o else None,'hidden_viewport':bool(o.hide_get()) if o else None}
forest=bpy.data.collections.get('41 • Boschi e radure')
trees=[o for o in forest.objects if o.type=='MESH'] if forest else []
protected=[{'name':o.name,'xy':list(o.location[:2])} for o in trees if ecology_v4._protected(o.location.x,o.location.y)]
# Presenza reale delle macro-architetture, senza ripetere l'audit di ogni finestra.
parts={
 'sala_grande':'01 • Sala Grande e ingresso',
 'scalinata_silente':'02 • Torre della Scalinata e ufficio di Silente',
 'quadrilatero':'03 • Quadrilatero, infermeria e Grifondoro',
 'cortile_viadotto':'04 • Cortile del viadotto',
 'tre_ponti':'05 • Tre ponti sulla gola',
 'durham':'05 • Ala Durham, galleria lunga e chiostri',
 'serre':'06 • Serre di Erbologia e conservatorio',
 'ingresso_viadotto':'07 • Ingresso del viadotto e quattro torri',
 'astronomia':'10 • Torre di Astronomia (HBP)',
 'orologio':'11 • Torre dell’Orologio',
 'rimessa':'16 • Rimessa delle barche e scalinata',
}
architecture={}
for label,n in parts.items():
 c=bpy.data.collections.get(n);objs=[o for o in c.all_objects if o.type=='MESH' and not o.hide_render] if c else []
 architecture[label]={'collection':n,'visible_mesh_objects':len(objs),'faces':sum(len(o.data.polygons) for o in objs)}
missing_parts=[k for k,v in architecture.items() if v['visible_mesh_objects']==0 or v['faces']==0]
# Controllo della continuità delle fondazioni aggiunte al file finale.
land_names=['Colli e sponde | superficie continua','Colline occidentali | superficie','Promontorio della Sala Grande | sommità','Promontorio delle serre | sommità','Scogliera della rimessa | superficie']
landtrees=[]
for name in land_names:
 ob=bpy.data.objects.get(name)
 if ob:
  verts=[ob.matrix_world@v.co for v in ob.data.vertices]
  landtrees.append((name,BVHTree.FromPolygons(verts,[tuple(p.vertices) for p in ob.data.polygons])))
foundation_checks=[]
for e in polish['pier_extensions']:
 pier=bpy.data.objects.get(e['pier']);foundation=bpy.data.objects.get(e['pier']+' | fondazione')
 result={'pier':e['pier'],'foundation':e['pier']+' | fondazione','exists':pier is not None and foundation is not None}
 if result['exists']:
  pv=[pier.matrix_world@v.co for v in pier.data.vertices];fv=[foundation.matrix_world@v.co for v in foundation.data.vertices]
  base=min(v.z for v in pv);top=max(v.z for v in fv);bottom=min(v.z for v in fv)
  x=sum(v.x for v in fv)/len(fv);y=sum(v.y for v in fv)/len(fv);ground=None;source=None
  for name,tree in landtrees:
   h=tree.ray_cast(Vector((x,y,800)),Vector((0,0,-1)),1600)
   if h[0] is not None and (ground is None or h[0].z>ground):ground=h[0].z;source=name
  original_foot=[v for v in pv if abs(v.z-base)<.0001];new_top=[v for v in fv if abs(v.z-top)<.0001]
  xy_error=max(min(math.hypot(v.x-q.x,v.y-q.y) for q in original_foot) for v in new_top)
  result.update({'original_base_z':base,'foundation_top_z':top,'foundation_bottom_z':bottom,'terrain_z_at_center':ground,'terrain_source':source,'top_gap':abs(top-base),'footprint_max_xy_difference':xy_error,'coincident_top':abs(top-base)<=.0001 and xy_error<=.0001,'reaches_ground':ground is not None and bottom<=ground+.0001,'penetration_at_center':ground-bottom if ground is not None else None,'visible':not foundation.hide_render and not foundation.hide_get(),'reported_ground_difference':abs(ground-e['ground']) if ground is not None else None})
 foundation_checks.append(result)
foundations_ok=len(foundation_checks)==9 and all(r.get('exists') and r.get('coincident_top') and r.get('reaches_ground') and r.get('visible') for r in foundation_checks)
count=len(bpy.data.objects);facecount=sum(len(o.data.polygons) for o in meshes)
from_build=build.get('architecture_transforms_changed',None)
checks={'scene_objects_match_build':count==build['objects']+len(polish['pier_extensions']),'faces_match_build':facecount==build['mesh_faces_evaluated_sum']+sum(len(bpy.data.objects[e['pier']+' | fondazione'].data.polygons) for e in polish['pier_extensions']),'build_reports_architecture_transforms_unchanged':from_build==[],'new_terrain_and_water_visible':all(v['exists'] and not v['hide_render'] and not v['hidden_viewport'] for v in new_visibility.values()),'old_borders_and_old_forest_hidden':all(v['exists'] and v['hide_render'] and v['hidden_viewport'] for v in old_hidden.values()),'trees_outside_protected_areas':not protected,'architecture_present':not missing_parts,'all_nine_pier_extensions_continuous_and_grounded':foundations_ok,'geometry_finite_and_nonempty':not empty and not nonfinite,'materials_present':not missing_material,'no_external_dependencies':not external_images and not libraries and not external_fonts}
report={'file':str(FILE),'file_sha256':hashlib.sha256(FILE.read_bytes()).hexdigest(),'blender_version':bpy.app.version_string,'scope':'Riapertura del file finale senza modifica o rendering. Controllo di risorse, integrità, visibilità paesaggio, aree protette degli alberi e presenza macro-architetture. Il controllo delle trasformazioni architettoniche proviene dal confronto eseguito durante la generazione e viene confrontato qui con i conteggi del file salvato. Non è una certificazione di fedeltà del paesaggio cinematografico.','scene_objects':count,'mesh_objects':len(meshes),'mesh_faces_evaluated_sum':facecount,'empty_meshes':empty,'nonfinite_geometry_or_transforms':nonfinite,'missing_material_assignments':missing_material,'external_images':external_images,'linked_libraries':libraries,'external_fonts':external_fonts,'new_visibility':new_visibility,'old_hidden':old_hidden,'trees':len(trees),'trees_in_protected_zones':protected,'architecture':architecture,'missing_architecture_parts':missing_parts,'architecture_transforms_changed_from_build':from_build,'terrain_vertices_lowered_from_polish':polish['terrain_vertices_lowered'],'foundation_checks':foundation_checks,'foundation_check_method':'Sommità e impronta confrontate con le quattro estremità inferiori del pilone originale. Fondale misurato con raycast al centro di ciascuna fondazione, sulle superfici del terreno usate dal generatore. Il vecchio corpo e la fondazione sono valutati insieme.','checks':checks,'passed':all(checks.values())}
(ROOT/'work/v4/verification-final.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
print('FINAL_VERIFICATION',json.dumps({'passed':report['passed'],'objects':count,'mesh_objects':len(meshes),'faces':facecount,'trees':len(trees),'foundations':len(foundation_checks),'checks':checks,'sha256':report['file_sha256']},ensure_ascii=False),flush=True)
