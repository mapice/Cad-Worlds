"""Reopen the saved model, check its structure, and render inspection views."""
import bpy
import hashlib
import json
import math
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs'
FILE = OUT / 'Minas-Tirith.blend'
bpy.ops.wm.open_mainfile(filepath=str(FILE))
s = bpy.context.scene
depsgraph = bpy.context.evaluated_depsgraph_get()
errors = []
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    if not o.data.polygons:
        errors.append('Empty mesh: ' + o.name)
    if any(not math.isfinite(c) for v in o.data.vertices for c in v.co):
        errors.append('Non-finite coordinates: ' + o.name)
missing = [i.filepath for i in bpy.data.images if i.source == 'FILE' and not i.packed_file and not Path(bpy.path.abspath(i.filepath)).exists()]
errors.extend('Missing image: ' + p for p in missing)
walls = [o.name for o in bpy.data.objects if 'curtain wall and battlements' in o.name]
ramps = [o.name for o in bpy.data.objects if o.get('role') == 'ramp']
assert len(walls) == 7, walls
assert len(ramps) == 6, ramps

# Probe each gate at pedestrian height along its radial centreline.
gate_probes = []
for level, (r, z, a) in enumerate(zip([240,204,169,136,105,77,50], [0,26,52,78,104,130,156], [0,1.25,-1.30,1.20,-1.25,1.22,-1.28])):
    radial = Vector((math.sin(a), -math.cos(a), 0))
    origin = radial * (r + 3) + Vector((0,0,z+3))
    hit, loc, norm, index, obj, matrix = s.ray_cast(depsgraph, origin, -radial, distance=9)
    result = {'circle': level+1, 'clear': not hit, 'obstacle': obj.name if hit else None}
    gate_probes.append(result)
    if hit:
        errors.append('Gate centreline blocked: ' + str(result))

report = {
    'file': FILE.name,
    'sha256': hashlib.sha256(FILE.read_bytes()).hexdigest(),
    'blender': bpy.app.version_string,
    'circles': len(walls),
    'ramps': len(ramps),
    'buildings': sum(o.get('role') == 'building' for o in bpy.data.objects),
    'objects': len(bpy.data.objects),
    'faces': sum(len(m.polygons) for m in bpy.data.meshes),
    'gate_centreline_probes': gate_probes,
    'errors': errors,
    'scope': 'Basic file integrity and seven gate centreline probes only. Does not certify full walkability, canonical accuracy, watertight solids, or print readiness.',
}
report['status'] = 'PASS' if not errors else 'FAIL'
(OUT/'verification.json').write_text(json.dumps(report,indent=2))
print('VERIFICATION', json.dumps(report), flush=True)
assert not errors, errors

pref=bpy.context.preferences.addons['cycles'].preferences
try:
    pref.compute_device_type='METAL';pref.get_devices()
    for d in pref.devices:d.use=d.type=='METAL'
    s.cycles.device='GPU'
except Exception:
    s.cycles.device='CPU'
s.cycles.samples=48
shots=[
    ('Camera | city from the southeast','Minas-Tirith-overview.png',2200,1700),
    ('Camera | front and seven circles','Minas-Tirith-front.png',1900,1600),
    ('Camera | White Tree court','Minas-Tirith-citadel.png',1900,1500),
    ('Camera | plan','Minas-Tirith-plan.png',1700,1700),
    ('Camera | main gate','Minas-Tirith-gate.png',1700,1250),
]
for name,file,w,h in shots:
    s.camera=bpy.data.objects[name]
    s.render.resolution_x=w;s.render.resolution_y=h
    s.render.filepath=str(OUT/file)
    bpy.ops.render.render(write_still=True)
    print('RENDERED',file,flush=True)
