import bpy,sys,json,hashlib,math
from pathlib import Path
ROOT=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca')
FILE=ROOT/'outputs/Hogwarts-Lago-Nero.blend'
sys.path.insert(0,str(ROOT/'work/v4'))
bpy.ops.wm.open_mainfile(filepath=str(FILE))
import ecology_v4
build=json.loads((ROOT/'work/v4/build-check.json').read_text())
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
count=len(bpy.data.objects);facecount=sum(len(o.data.polygons) for o in meshes)
from_build=build.get('architecture_transforms_changed',None)
checks={'scene_objects_match_build':count==build['objects'],'faces_match_build':facecount==build['mesh_faces_evaluated_sum'],'build_reports_architecture_transforms_unchanged':from_build==[],'new_terrain_and_water_visible':all(v['exists'] and not v['hide_render'] and not v['hidden_viewport'] for v in new_visibility.values()),'old_borders_and_old_forest_hidden':all(v['exists'] and v['hide_render'] and v['hidden_viewport'] for v in old_hidden.values()),'trees_outside_protected_areas':not protected,'architecture_present':not missing_parts,'geometry_finite_and_nonempty':not empty and not nonfinite,'materials_present':not missing_material,'no_external_dependencies':not external_images and not libraries and not external_fonts}
report={'file':str(FILE),'file_sha256':hashlib.sha256(FILE.read_bytes()).hexdigest(),'blender_version':bpy.app.version_string,'scope':'Riapertura del file finale senza modifica o rendering. Controllo di risorse, integrità, visibilità paesaggio, aree protette degli alberi e presenza macro-architetture. Il controllo delle trasformazioni architettoniche proviene dal confronto eseguito durante la generazione e viene confrontato qui con i conteggi del file salvato. Non è una certificazione di fedeltà del paesaggio cinematografico.','scene_objects':count,'mesh_objects':len(meshes),'mesh_faces_evaluated_sum':facecount,'empty_meshes':empty,'nonfinite_geometry_or_transforms':nonfinite,'missing_material_assignments':missing_material,'external_images':external_images,'linked_libraries':libraries,'external_fonts':external_fonts,'new_visibility':new_visibility,'old_hidden':old_hidden,'trees':len(trees),'trees_in_protected_zones':protected,'architecture':architecture,'missing_architecture_parts':missing_parts,'architecture_transforms_changed_from_build':from_build,'checks':checks,'passed':all(checks.values())}
(ROOT/'work/v4/verification-final.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
print('FINAL_VERIFICATION',json.dumps({'passed':report['passed'],'objects':count,'mesh_objects':len(meshes),'faces':facecount,'trees':len(trees),'checks':checks,'sha256':report['file_sha256']},ensure_ascii=False),flush=True)
