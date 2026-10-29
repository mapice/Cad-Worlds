import sys,bpy,json
from pathlib import Path
from mathutils import Vector
ROOT=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca')
sys.path.insert(0,str(ROOT/'work/v3'))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/Hogwarts-HBP.blend'))
import materials
print('MATERIALS_APPLY',materials.apply(),flush=True)
scene=bpy.context.scene
cam=scene.camera
cam.location=(135,-250,150)
cam.rotation_euler=(Vector((21,-97,112))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.ortho_scale=84
scene.render.resolution_x=900;scene.render.resolution_y=740;scene.render.resolution_percentage=100
scene.cycles.samples=32;scene.cycles.adaptive_threshold=.035
scene.render.filepath=str(ROOT/'work/v3/material-test.png')
bpy.ops.render.render(write_still=True)
print('MATERIAL_TEST_RENDERED',flush=True)
