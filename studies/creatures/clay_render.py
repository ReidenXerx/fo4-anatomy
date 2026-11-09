"""Clay renders of NIFs (PyNifly import, grey material) from a few angles, to look at geometry.
    blender -b -P clay_render.py -- <out dir> <tag:nif> [<tag:nif> ...]
Each view: front, side, 3/4 low (crotch), close-up of the pelvis box."""
import math
import pathlib
import sys

import addon_utils
import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
OUT = pathlib.Path(args[0])
OUT.mkdir(parents=True, exist_ok=True)


def setup():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    addon_utils.enable('io_scene_nifly', default_set=True)
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light = 'STUDIO'
    sh.color_type = 'SINGLE'
    sh.single_color = (0.75, 0.68, 0.62)
    sh.show_cavity = True
    sh.cavity_type = 'BOTH'
    sh.show_shadows = True
    w = bpy.data.worlds.new('w')
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (0.2, 0.2, 0.22, 1)
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.exposure = 0.0
    sc.view_settings.view_transform = 'Standard'
    return sc


def light(name, loc, energy):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy, ld.size = energy, 40
    lo = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.location = loc
    lo.rotation_euler = (Vector((0, 0, 60)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()


def shoot(sc, name, target, yaw, pitch, scale):
    cd = bpy.data.cameras.new(name)
    cd.type, cd.ortho_scale, cd.clip_end = 'ORTHO', scale, 3000
    cam = bpy.data.objects.new(name, cd)
    sc.collection.objects.link(cam)
    y, p = math.radians(yaw), math.radians(pitch)
    cam.location = target + Vector((math.sin(y) * math.cos(p), math.cos(y) * math.cos(p), math.sin(p))) * 400
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    sc.render.resolution_x = sc.render.resolution_y = 900
    sc.render.filepath = str(OUT / f'{name}.png')
    bpy.ops.render.render(write_still=True)


for item in args[1:]:
    tag, path = item.split(':', 1) if ':' in item[2:] and not item[1] == ':' else ('x', item)
    if '|' in item:
        tag, path = item.split('|', 1)
    sc = setup()
    bpy.ops.import_scene.pynifly(filepath=path)
    clay = bpy.data.materials.new('clay')
    clay.use_nodes = True
    clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.55, 0.5, 0.47, 1)
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    for o in meshes:
        o.data.materials.clear()
        o.data.materials.append(clay)
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    mid = (lo + hi) / 2
    print(tag, 'bounds', tuple(round(v, 1) for v in lo), tuple(round(v, 1) for v in hi))
    light('key', (120, 260, 110), 60000)
    light('fill', (-220, 160, 60), 15000)
    light('back', (0, -250, 120), 40000)
    h = hi.z - lo.z
    shoot(sc, f'{tag}_front', mid, 0, 0, h * 1.05)
    shoot(sc, f'{tag}_side', mid, 90, 0, h * 1.05)
    pelvis = Vector((mid.x, mid.y, lo.z + h * 0.50))
    shoot(sc, f'{tag}_crotch', pelvis, 15, -10, h * 0.28)
    chest = Vector((mid.x, mid.y, lo.z + h * 0.72))
    shoot(sc, f'{tag}_chest', chest, 30, 0, h * 0.30)
    gz = Vector((mid.x, mid.y + 3, lo.z + h * 0.47))
    shoot(sc, f'{tag}_gside', gz, 70, 5, h * 0.10)
    shoot(sc, f'{tag}_gfront', gz, 0, -25, h * 0.10)
    shoot(sc, f'{tag}_gunder', gz + Vector((0, 0, -2)), 0, -65, h * 0.10)
print('clay done')
