import sys,bpy
from pathlib import Path
from mathutils import Vector
ROOT=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca')
sys.path.insert(0,str(ROOT/'work/v3'))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/Hogwarts-HBP-dettagliato.blend'))
import materials
materials.glass_material('glass')
s=bpy.context.scene;c=bpy.data.objects['Camera | serre e campanili'];s.camera=c
# Stessa direzione della camera consegnata, centrata sul gruppo settentrionale.
target=Vector((75,121,60));direction=c.rotation_euler.to_quaternion()@Vector((0,0,1))
c.location=target+direction*500;c.rotation_euler=(target-c.location).to_track_quat('-Z','Y').to_euler();c.data.ortho_scale=120
s.render.resolution_x=1000;s.render.resolution_y=720;s.render.resolution_percentage=100
s.cycles.samples=24;s.cycles.adaptive_threshold=.06;s.cycles.max_bounces=7;s.cycles.transmission_bounces=7;s.cycles.transparent_max_bounces=12
s.render.filepath=str(ROOT/'work/v3/glass-test.png')
bpy.ops.render.render(write_still=True)
print('GLASS_TEST_OK',flush=True)
