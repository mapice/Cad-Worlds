exec(open('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca/work/v6/test_academic.py').read().split("if '--preview'")[0])
for name in ['Camera | Biblioteca','Camera | Aula Pozioni','Camera | Infermeria','Camera | Aula Trasfigurazione']:
 o=bpy.data.objects[name];print(name,'loc',tuple(o.location),'rotation',tuple(o.rotation_euler),'dir',tuple(o.matrix_world.to_quaternion()@__import__('mathutils').Vector((0,0,-1))))
