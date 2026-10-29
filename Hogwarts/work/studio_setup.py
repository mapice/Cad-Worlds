"""Allestimento di presentazione per il modello di Hogwarts.

Uso da Blender: import studio_setup; studio_setup.setup_scene()
La funzione non salva file e non avvia il rendering.
"""

import math

import bpy
from mathutils import Vector


COLLECTION_NAME = "00 • Presentazione"


def _point_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def _camera(collection, name, location, target, ortho_scale):
    data = bpy.data.cameras.new(name)
    data.type = "ORTHO"
    data.ortho_scale = ortho_scale
    data.clip_start = 0.1
    data.clip_end = 10000
    data.lens = 55
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.location = location
    _point_at(obj, target)
    obj.hide_select = True
    return obj


def _area(collection, name, location, target, power, size, color):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = power
    data.shape = "DISK"
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.location = location
    _point_at(obj, target)
    obj.hide_select = True
    return obj


def setup_scene():
    """Imposta luci, sfondo e due camere; restituisce la camera principale.

    Dimensioni attese: base 260 × 200, altezza massima 185 unità.
    L'allestimento usa esclusivamente la propria collezione.
    """
    scene = bpy.context.scene
    collection = bpy.data.collections.get(COLLECTION_NAME)
    if collection is None:
        collection = bpy.data.collections.new(COLLECTION_NAME)
        scene.collection.children.link(collection)
    else:
        for obj in list(collection.objects):
            bpy.data.objects.remove(obj, do_unlink=True)

    floor_mesh = bpy.data.meshes.new("Fondale • superficie")
    floor_mesh.from_pydata(
        [(-1800, -1800, -1), (1800, -1800, -1),
         (1800, 1800, -1), (-1800, 1800, -1)],
        [], [(0, 1, 2, 3)],
    )
    floor_mesh.update()
    floor = bpy.data.objects.new("Fondale • studio", floor_mesh)
    collection.objects.link(floor)
    floor.hide_select = True
    material = bpy.data.materials.get("Studio • avorio")
    if material is None:
        material = bpy.data.materials.new("Studio • avorio")
    material.use_nodes = True
    material.diffuse_color = (0.57, 0.55, 0.51, 1.0)
    principled = material.node_tree.nodes.get("Principled BSDF")
    principled.inputs["Base Color"].default_value = material.diffuse_color
    principled.inputs["Roughness"].default_value = 0.9
    floor.data.materials.append(material)

    target = (0, 0, 72)
    camera = _camera(
        collection, "Camera • principale", (340, -460, 300), target, 370
    )
    _camera(collection, "Camera • retro", (-340, 460, 300), target, 370)
    scene.camera = camera

    # Le potenze tengono conto delle grandi coordinate del modello in mm.
    _area(collection, "Luce • principale", (-220, -280, 450), (0, 0, 50),
          5000000, 280, (1.0, 0.87, 0.72))
    _area(collection, "Luce • riempimento", (310, -80, 280), (0, 0, 70),
          2300000, 260, (0.74, 0.86, 1.0))
    _area(collection, "Luce • contorno", (50, 300, 380), (0, 0, 80),
          4000000, 230, (1.0, 0.95, 0.84))

    world = bpy.data.worlds.get("Studio • ambiente")
    if world is None:
        world = bpy.data.worlds.new("Studio • ambiente")
    world.use_nodes = True
    world.node_tree.nodes.get("Background").inputs["Color"].default_value = (
        0.55, 0.61, 0.69, 1
    )
    world.node_tree.nodes.get("Background").inputs["Strength"].default_value = 0.35
    scene.world = world

    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.025
    scene.cycles.max_bounces = 6
    scene.cycles.diffuse_bounces = 3
    scene.cycles.glossy_bounces = 3
    scene.cycles.transparent_max_bounces = 4
    scene.render.resolution_x = 1800
    scene.render.resolution_y = 1500
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.film_transparent = False
    scene.render.use_file_extension = True
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1

    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 0.001
    scene.unit_settings.length_unit = "MILLIMETERS"

    # Vista libera già orientata come la camera, comoda per ruotare il modello.
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type != "VIEW_3D":
                continue
            space = area.spaces.active
            space.clip_start = 0.1
            space.clip_end = 10000
            space.shading.type = "MATERIAL"
            space.shading.use_scene_world = False
            space.shading.use_scene_lights = False
            space.overlay.show_floor = False
            space.overlay.show_axis_x = False
            space.overlay.show_axis_y = False
            if space.region_3d:
                space.region_3d.view_location = target
                space.region_3d.view_distance = 340
                space.region_3d.view_rotation = camera.rotation_euler.to_quaternion()
                space.region_3d.view_perspective = "ORTHO"
    return camera
