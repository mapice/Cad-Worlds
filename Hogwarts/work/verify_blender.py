"""Verifica in sola lettura di Hogwarts.blend: non salva o modifica il file."""
import bpy
import json
import math
from pathlib import Path
from mathutils import Vector


def finite(values):
    return all(math.isfinite(float(value)) for value in values)


scene = bpy.context.scene
objects = list(bpy.data.objects)
mesh_objects = [obj for obj in objects if obj.type == "MESH"]
empty_meshes = [obj.name for obj in mesh_objects if not len(obj.data.polygons)]
invalid_coordinates = []
for obj in objects:
    if not finite(value for row in obj.matrix_world for value in row):
        invalid_coordinates.append(obj.name + ": trasformazione")
    if obj.type == "MESH" and any(not finite(vertex.co) for vertex in obj.data.vertices):
        invalid_coordinates.append(obj.name + ": vertici")

external = []
for library in bpy.data.libraries:
    external.append({"type": "library", "name": library.name, "path": library.filepath})
for image in bpy.data.images:
    if image.source in {"FILE", "SEQUENCE", "MOVIE"} and not image.packed_file:
        external.append({"type": "image", "name": image.name, "path": image.filepath})
for font in bpy.data.fonts:
    if font.filepath and font.filepath != "<builtin>" and not font.packed_file:
        external.append({"type": "font", "name": font.name, "path": font.filepath})
for typename in ("cache_files", "volumes", "sounds", "movieclips"):
    for datablock in getattr(bpy.data, typename, []):
        path = getattr(datablock, "filepath", "")
        if path and not getattr(datablock, "packed_file", None):
            external.append({"type": typename, "name": datablock.name, "path": path})

castle_objects = [obj for obj in mesh_objects
                  if not any(col.name == "00 • Presentazione" for col in obj.users_collection)]
corners = [obj.matrix_world @ Vector(corner) for obj in castle_objects for corner in obj.bound_box]
bounds = None
if corners:
    bounds = {
        "minimum": [min(point[i] for point in corners) for i in range(3)],
        "maximum": [max(point[i] for point in corners) for i in range(3)],
    }
    bounds["size"] = [bounds["maximum"][i] - bounds["minimum"][i] for i in range(3)]
camera = scene.camera
camera_ok = (camera is not None and camera.type == "CAMERA"
             and camera.data.clip_end > camera.data.clip_start > 0)
report = {
    "file": bpy.data.filepath,
    "blender_version": bpy.app.version_string,
    "object_count": len(objects),
    "mesh_object_count": len(mesh_objects),
    "vertex_count": sum(len(obj.data.vertices) for obj in mesh_objects),
    "polygon_count": sum(len(obj.data.polygons) for obj in mesh_objects),
    "collections": {col.name: len(col.objects) for col in bpy.data.collections},
    "materials": [material.name for material in bpy.data.materials],
    "empty_meshes": empty_meshes,
    "invalid_coordinates": invalid_coordinates,
    "external_dependencies": external,
    "units": {"system": scene.unit_settings.system,
              "scale_length": scene.unit_settings.scale_length,
              "length_unit": scene.unit_settings.length_unit},
    "camera": {"valid": camera_ok, "name": camera.name if camera else None,
               "type": camera.data.type if camera else None,
               "ortho_scale": camera.data.ortho_scale if camera else None},
    "castle_bounds": bounds,
    "render_size": [scene.render.resolution_x, scene.render.resolution_y],
    "passed": bool(mesh_objects) and not empty_meshes and not invalid_coordinates
              and not external and camera_ok,
    "scope": "Integrità della scena; non certifica la stampa 3D.",
}
destination = Path(__file__).with_name("verification.json")
destination.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print("VERIFICATION", json.dumps({key: report[key] for key in
      ["passed", "mesh_object_count", "polygon_count", "empty_meshes",
       "invalid_coordinates", "external_dependencies", "units", "camera", "castle_bounds"]},
      ensure_ascii=False))
