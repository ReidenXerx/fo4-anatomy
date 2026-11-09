"""Blender: where do our shapes land against the body after PyNifly import (skinning applied)?
    blender -b -P dc_where.py -- <review nif>"""
import sys

import addon_utils
import bpy
from mathutils import Vector

path = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable('io_scene_nifly', default_set=True)
bpy.ops.import_scene.pynifly(filepath=path)
dg = bpy.context.evaluated_depsgraph_get()
objs = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
body = objs['DeathclawFX:0']
be = body.evaluated_get(dg)
inv = be.matrix_world.inverted()
for name, o in objs.items():
    if name.startswith(('Deathclaw', 'Hots', 'Mouth', 'Eyes', 'tongue')):
        continue
    oe = o.evaluated_get(dg)
    me = oe.to_mesh()
    ws = [oe.matrix_world @ v.co for v in me.vertices]
    lo = Vector((min(p.x for p in ws), min(p.y for p in ws), min(p.z for p in ws)))
    hi = Vector((max(p.x for p in ws), max(p.y for p in ws), max(p.z for p in ws)))
    ds = []
    for p in ws[::7]:
        ok, loc, nrm, _ = be.closest_point_on_mesh(inv @ p)
        q = be.matrix_world @ loc
        n = (be.matrix_world.to_3x3() @ nrm).normalized()
        ds.append((p - q).dot(n))
    ds.sort()
    print(f'{name}: hide_render {o.hide_render} world bbox {tuple(round(c, 1) for c in lo)} {tuple(round(c, 1) for c in hi)}'
          f' matrix_world_t {tuple(round(c, 2) for c in o.matrix_world.translation)}'
          f' signed dist to body: min {ds[0]:.2f} median {ds[len(ds) // 2]:.2f} max {ds[-1]:.2f}')
bw = [be.matrix_world @ v.co for v in be.to_mesh().vertices]
print('body world z range', round(min(p.z for p in bw), 1), round(max(p.z for p in bw), 1),
      'matrix_world_t', tuple(round(c, 2) for c in body.matrix_world.translation))
