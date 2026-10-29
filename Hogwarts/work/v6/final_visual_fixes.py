"""Apply the two final visual cleanups and refresh only affected views."""
import bpy, json, sys, hashlib
from pathlib import Path

R = Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca')
O = R / 'outputs'
sys.path.insert(0, str(R / 'work/v6'))
bpy.ops.wm.open_mainfile(filepath=str(O / 'Hogwarts-interni.blend'))
import fix_hall_pole, fix_atrium_seam, fix_silente_floor
changes = {'hall': fix_hall_pole.apply(), 'atrium': fix_atrium_seam.apply(), 'silente': fix_silente_floor.apply()}
import cutaway_v6
for ob in list(bpy.data.objects):
    if ob.get('Solo vista aperta'):
        bpy.data.objects.remove(ob, do_unlink=True)
changes['section'] = cutaway_v6.apply()
guide = bpy.data.texts.get('LEGGIMI | Interni di Hogwarts') or bpy.data.texts.new('LEGGIMI | Interni di Hogwarts')
guide.clear()
guide.write((O / 'Hogwarts-interni-GUIDA.txt').read_text())
s = bpy.context.scene
for layer in s.view_layers:
    layer.use = layer.name == 'Modello completo'
bpy.context.window.view_layer = s.view_layers['Modello completo']
s.camera = bpy.data.objects['Camera | Interno Sala Grande']
s.render.resolution_x = 2000
s.render.resolution_y = 1350
s.render.resolution_percentage = 100
s.render.filepath = str(O / 'Hogwarts-interni-Sala-Grande.png')
s.cycles.samples = 40
s.cycles.adaptive_threshold = .025
s.cycles.use_denoising = True
p = bpy.context.preferences.addons['cycles'].preferences
try:
    p.compute_device_type = 'METAL'
    p.get_devices()
    for device in p.devices:
        device.use = device.type == 'METAL'
    s.cycles.device = 'GPU'
except Exception:
    s.cycles.device = 'CPU'
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(O / 'Hogwarts-interni.blend'), compress=True)
print('VISUAL_FIXES_SAVED', changes, flush=True)
shots = [
    ('Camera | Interno Sala Grande', 'Sala-Grande'),
    ('Interni | Grande scalinata dal ballatoio', 'Scalinata'),
    ('Camera | Atrio e accesso alla scalinata', 'Atrio'),
    ('Interni | Ufficio di Silente', 'Silente'),
]
for i, (camera, label) in enumerate(shots):
    s.camera = bpy.data.objects[camera]
    s.render.resolution_x = 2000 if i == 0 else 1600
    s.render.resolution_y = 1350 if i == 0 else 1100
    s.render.filepath = str(O / f'Hogwarts-interni-{label}.png')
    bpy.ops.render.render(write_still=True)
    print('UPDATED_RENDER', label, flush=True)
for layer in s.view_layers:
    layer.use = layer.name == 'Interni aperti'
bpy.context.window.view_layer = s.view_layers['Interni aperti']
s.camera = bpy.data.objects['Camera | disposizione degli interni']
s.render.resolution_x = 2200
s.render.resolution_y = 1650
s.render.filepath = str(O / 'Hogwarts-interni-sezione.png')
bpy.ops.render.render(write_still=True, layer='Interni aperti')
result_path = R / 'work/v6/final-check.json'
result = json.loads(result_path.read_text())
result.update(
    sha256=hashlib.sha256((O / 'Hogwarts-interni.blend').read_bytes()).hexdigest(),
    objects=len(bpy.data.objects),
    mesh_objects=sum(o.type == 'MESH' for o in bpy.data.objects),
    visual_corrections=changes,
    visible_empty_meshes=[o.name for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render and not o.data.polygons],
)
result_path.write_text(json.dumps(result, indent=2, default=str))
print('VISUAL_FIXES_DONE', flush=True)
