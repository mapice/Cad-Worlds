import bpy,json,hashlib,math
from pathlib import Path
ROOT=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca');OUT=ROOT/'outputs'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/v3/Hogwarts-draft.blend'))
s=bpy.context.scene;s.cycles.samples=64;s.cycles.adaptive_threshold=.018;s.cycles.max_bounces=7
s.cycles.transmission_bounces=7;s.cycles.transparent_max_bounces=8
s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA'
s.camera=bpy.data.objects['Camera | insieme da sud-est'];s.render.resolution_x=2200;s.render.resolution_y=1700;s.render.filepath=str(OUT/'Hogwarts-dettagliato-insieme.png')
# Salva il file pronto sulla vista generale, non su un dettaglio tagliato.
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D' and area.spaces.active.region_3d:
   a=area.spaces.active;a.region_3d.view_location=(-40,0,85);a.region_3d.view_distance=590;a.region_3d.view_rotation=s.camera.rotation_euler.to_quaternion();a.region_3d.view_perspective='ORTHO'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Hogwarts-HBP-dettagliato.blend'),compress=True)
print('FINAL_SAVED',flush=True)
for cam,name,w,h in [
 ('Camera | insieme da sud-est','Hogwarts-dettagliato-insieme.png',2200,1700),
 ('Camera | pietra, finestre e ardesia','Hogwarts-dettagliato-ravvicinata.png',2100,1600),
 ('Camera | serre e campanili','Hogwarts-dettagliato-serre.png',1800,1400)]:
 s.camera=bpy.data.objects[cam];s.render.resolution_x=w;s.render.resolution_y=h;s.render.filepath=str(OUT/name)
 bpy.ops.render.render(write_still=True);print('RENDERED',name,flush=True)
print('ALL_RENDERED',flush=True)
