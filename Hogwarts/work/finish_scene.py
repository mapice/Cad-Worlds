import bpy
from pathlib import Path
p=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca/outputs')
bpy.ops.wm.open_mainfile(filepath=str(p/'Hogwarts.blend'))
# Evita sovrapposizione di superfici alla stessa quota tra ponte e piazzale.
bpy.data.objects['Piazzale d’ingresso'].location.z+=.25
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(p/'Hogwarts.blend'),compress=True)
bpy.context.scene.render.filepath=str(p/'Hogwarts-anteprima.png')
bpy.ops.render.render(write_still=True)
