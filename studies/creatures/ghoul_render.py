"""Blender (background) offline renders of the ghoul skins, BEFORE and AFTER, from ghoul_render_prep.py's OBJs and
maps.  blender -b --factory-startup -P ghoul_render.py -- D:/F4Output/ghoulskin/render"""
import math
import pathlib
import sys

import bpy
from mathutils import Vector

R = pathlib.Path(sys.argv[sys.argv.index('--') + 1])
SHOTS = R / 'shots'
SHOTS.mkdir(parents=True, exist_ok=True)
TEX = {'F': {'body': 'F_body', 'genitals': 'F_genitals', 'hands': 'F_hands', 'head': 'F_face', 'rear': 'F_rear_head'},
       'M': {'body': 'M_body', 'rear': 'M_body', 'hands': 'M_hands', 'head': 'M_face'}}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE', 'CYCLES'):
        try:
            sc.render.engine = eng
            break
        except TypeError:
            continue
    sc.render.film_transparent = False
    world = bpy.data.worlds.new('w')
    sc.world = world
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (0.16, 0.16, 0.17, 1)
    world.node_tree.nodes['Background'].inputs[1].default_value = 1.0
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.exposure = 2.2
    return sc


def material(name, when):
    m = bpy.data.materials.new(f'{name}_{when}')
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']

    def img(kind, colour):
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = bpy.data.images.load(str(R / when / f'{name}_{kind}.png'))
        n.image.colorspace_settings.name = 'sRGB' if colour else 'Non-Color'
        return n
    d = img('d', True)
    nt.links.new(d.outputs['Color'], bsdf.inputs['Base Color'])
    n = img('n', False)
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(n.outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    s = img('s', False)
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(s.outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
    spec_in = bsdf.inputs.get('Specular IOR Level') or bsdf.inputs.get('Specular')
    nt.links.new(sep.outputs['Red'], spec_in)
    return m


def load(sex, when):
    objs = []
    for key, tex in TEX[sex].items():
        bpy.ops.wm.obj_import(filepath=str(R / 'obj' / f'{sex}_{key}.obj'), forward_axis='Y', up_axis='Z')
        o = bpy.context.selected_objects[0]
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.0005)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.shade_smooth()
        o.data.materials.clear()
        o.data.materials.append(material(tex, when))
        objs.append(o)
    return objs


def bounds(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def light(name, loc, energy, size=30):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy = energy
    ld.size = size
    lo = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.location = loc
    d = Vector((0, 0, -40)) - Vector(loc)
    lo.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def shoot(sc, name, target, yaw_deg, dist, scale, res):
    cd = bpy.data.cameras.new(name)
    cd.type = 'ORTHO'
    cd.ortho_scale = scale
    cd.clip_end = 2000
    cam = bpy.data.objects.new(name, cd)
    sc.collection.objects.link(cam)
    yaw = math.radians(yaw_deg)
    cam.location = target + Vector((math.sin(yaw) * dist, math.cos(yaw) * dist, 0))
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = str(SHOTS / f'{name}.png')
    bpy.ops.render.render(write_still=True)


for sex in ('F', 'M'):
    for when in ('before', 'after'):
        sc = reset()
        objs = load(sex, when)
        lo, hi = bounds(objs)
        mid = (lo + hi) / 2
        light('key', (120, 160, 60), 60000)
        light('fill', (-160, 120, 0), 20000)
        light('rim', (0, -200, 80), 40000)
        light('rimf', (0, 220, -40), 15000)
        head_top = hi.z
        head_c = Vector((0, mid.y, head_top - 14))
        shoot(sc, f'{sex}_{when}_front', mid, 0, 300, (hi.z - lo.z) * 1.05, (900, 1200))
        shoot(sc, f'{sex}_{when}_back', mid, 180, 300, (hi.z - lo.z) * 1.05, (900, 1200))
        shoot(sc, f'{sex}_{when}_face', head_c, 20, 300, 34, (1000, 1000))
        shoot(sc, f'{sex}_{when}_neckback', head_c + Vector((0, 0, -4)), 150, 300, 40, (1000, 1000))
        shoot(sc, f'{sex}_{when}_torso', Vector((0, mid.y, head_top - 45)), 15, 300, 50, (1000, 1000))
        shoot(sc, f'{sex}_{when}_crotch', Vector((0, mid.y, -50)), 10, 300, 26, (1000, 1000))
print('renders done')
