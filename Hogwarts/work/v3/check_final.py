import bpy,json,math,hashlib,os
from pathlib import Path
R=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca');P=R/'outputs/Hogwarts-HBP-dettagliato.blend'
bpy.ops.wm.open_mainfile(filepath=str(P))
standard={'stone','trim','roof','roofline','window','glass','wood','path','grass','rock','water','gold','base'}
rep={'file':str(P),'file_sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'blender_version':bpy.app.version_string,'scope':'Riapertura, integrità geometrica, assegnazione materiali e risorse, UV sui materiali standard, presenza dettagli/vegetazione/camere. Nessun salvataggio né rendering. Non certifica fedeltà architettonica o stampabilità.','objects':len(bpy.data.objects),'mesh_objects':0,'faces':0,'empty_meshes':[],'nonfinite_mesh_or_transform':[],'missing_materials':[],'standard_meshes_without_uv':[],'missing_external_resources':[],'cameras':[],'collections':[]}
for o in bpy.data.objects:
 if o.type=='CAMERA':rep['cameras'].append(o.name)
 if o.type!='MESH':continue
 rep['mesh_objects']+=1;rep['faces']+=len(o.data.polygons)
 if not o.data.polygons:rep['empty_meshes'].append(o.name)
 if not all(math.isfinite(c) for row in o.matrix_world for c in row) or not all(math.isfinite(c) for v in o.data.vertices for c in v.co):rep['nonfinite_mesh_or_transform'].append(o.name)
 if not o.data.materials or any(m is None for m in o.data.materials):rep['missing_materials'].append(o.name)
 if any(m and m.name in standard for m in o.data.materials) and not o.data.uv_layers:rep['standard_meshes_without_uv'].append(o.name)
for image in bpy.data.images:
 if image.source not in {'FILE','MOVIE'} or image.packed_file or image.packed_files:continue
 if image.filepath and not Path(bpy.path.abspath(image.filepath)).exists():rep['missing_external_resources'].append({'image':image.name,'path':image.filepath})
for lib in bpy.data.libraries:
 if not Path(bpy.path.abspath(lib.filepath)).exists():rep['missing_external_resources'].append({'library':lib.name,'path':lib.filepath})
for c in bpy.data.collections:rep['collections'].append({'name':c.name,'objects':len(c.objects),'mesh_objects':sum(o.type=='MESH' for o in c.objects)})
rep['detail_collections']=[c for c in rep['collections'] if 'Dettagli' in c['name'] or c['name'].startswith(('30 ','31 '))]
rep['vegetation_collections']=[c for c in rep['collections'] if c['name'].startswith(('32 ','33 ','34 ')) or 'Erbologia' in c['name'] or 'conifere' in c['name']]
rep['six_cameras_present']=len(rep['cameras'])==6
rep['ok']=not any(rep[k] for k in ['empty_meshes','nonfinite_mesh_or_transform','missing_materials','standard_meshes_without_uv','missing_external_resources']) and rep['six_cameras_present'] and bool(rep['detail_collections']) and bool(rep['vegetation_collections'])
(R/'work/v3/verification-final.json').write_text(json.dumps(rep,indent=2,ensure_ascii=False))
print('FINAL_VERIFICATION',json.dumps({k:rep[k] for k in ['ok','objects','mesh_objects','faces','empty_meshes','nonfinite_mesh_or_transform','missing_materials','standard_meshes_without_uv','missing_external_resources','cameras']},ensure_ascii=False),flush=True)
