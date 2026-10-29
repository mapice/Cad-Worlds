"""Elimina la superficie coplanare del ballatoio sotto il pavimento di Silente."""
import bpy, bmesh, math
from mathutils import Vector

def apply():
    floor = bpy.data.objects['Silente | pavimento continuo']
    gallery = bpy.data.objects['Scalinata | ballatoio 11']
    verts = []
    for v in floor.data.vertices:
        p = floor.matrix_world @ v.co
        verts.append((p.x, p.y, 133.8 if p.z < 134.32 else 134.8))
    mesh = bpy.data.meshes.new('Cutter temporaneo | raccordo pavimento Silente')
    mesh.from_pydata(verts, [], [tuple(p.vertices) for p in floor.data.polygons])
    bm = bmesh.new(); bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh); bm.free()
    cutter = bpy.data.objects.new(mesh.name, mesh)
    bpy.context.scene.collection.objects.link(cutter)
    mod = gallery.modifiers.new('Raccordo pavimento Silente', 'BOOLEAN')
    mod.operation = 'DIFFERENCE'; mod.solver = 'EXACT'; mod.object = cutter
    bpy.context.view_layer.objects.active = gallery
    gallery.hide_set(False)
    before = len(gallery.data.polygons)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter, do_unlink=True)
    bpy.data.meshes.remove(mesh)
    assert gallery.data.polygons, 'Il raccordo ha svuotato il ballatoio'
    bpy.context.view_layer.update()
    centers = [(21.6 + 16.5*math.cos(a), -97.028 + 16.5*math.sin(a)) for a in [3.55, 3.87, 4.19]]
    samples = []
    def height(obj, x, y):
        inverse = obj.matrix_world.inverted()
        ok, pos, _, _ = obj.ray_cast(inverse @ Vector((x, y, 134.7)), inverse.to_3x3() @ Vector((0,0,-1)), distance=1.2)
        return (obj.matrix_world @ pos).z if ok else None
    for x in [3.9 + k*.23 for k in range(54)]:
        for y in [-114 + k*.23 for k in range(58)]:
            if not any((x-a)**2+(y-b)**2 < 2.65**2 for a,b in centers):
                continue
            if not 11.5**2 < (x-21.6)**2+(y+97.028)**2 < 15.0**2:
                continue
            fh, gh = height(floor,x,y), height(gallery,x,y)
            assert fh is not None and abs(fh-134.4)<.01, ('Pavimento mancante',x,y,fh)
            assert gh is None or abs(gh-134.4)>.01, ('Superfici ancora sovrapposte',x,y,gh)
            samples.append((x,y))
    assert samples, 'Nessun campione del raccordo'
    gallery['Raccordo ufficio Silente'] = 'Il pavimento continuo delle tre stanze sostituisce la porzione sovrapposta del ballatoio.'
    return {'gallery_faces_before':before, 'gallery_faces_after':len(gallery.data.polygons), 'overlap_probes_clear':len(samples)}

if __name__ == '__main__':
    import json
    from pathlib import Path
    root=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca')
    bpy.ops.wm.open_mainfile(filepath=str(root/'outputs/Hogwarts-interni.blend'))
    result=apply()
    (root/'work/v6/silente-floor-check.json').write_text(json.dumps(result,indent=2))
    print('SILENTE_FLOOR_CHECK',result,flush=True)
