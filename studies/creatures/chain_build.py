"""Blender (background) + PyNifly: export ONLY our shapes (json: {name: verts, uv, weights, tris}) in the shape space
of a reference shape of a UAP nif, on UAP's armature (it carries the genital bones). The result is the transplant
SOURCE (transplant.py puts our shapes onto the vanilla body; nothing else of this export ships).
    blender -b -P chain_build.py -- <geom.json> <uap.nif> <ref shape> <out.nif>"""
import json
import pathlib
import sys

import addon_utils
import bpy
from mathutils import Vector

geom, src, ref_name, dst = sys.argv[sys.argv.index('--') + 1:][:4]
G = json.load(open(geom))
bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable('io_scene_nifly', default_set=True)
bpy.ops.import_scene.pynifly(filepath=src, rename_bones=False)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
ref = next(o for o in meshes if o.name.startswith(ref_name))
arm = next(m.object for m in ref.modifiers if m.type == 'ARMATURE')
lo = [min(v.co[i] for v in ref.data.vertices) for i in range(3)]
hi = [max(v.co[i] for v in ref.data.vertices) for i in range(3)]
wl, wh = G['_uap_penis_bbox']
err = max(abs(a - b) for a, b in zip(lo + hi, wl + wh))
print('ref local bbox err', err)
if err > 0.01:
    raise SystemExit('reference shape local space differs from its nif shape space')
needed = sorted({b for k, g in G.items() if not k.startswith('_') for w in g['weights'] for b in w})
missing = [b for b in needed if b not in arm.data.bones]
if missing:
    raise SystemExit(f'bones missing in the reference armature: {missing}')
# every armature gets the reference armature's copy of the needed bones (PyNifly may export through another one)
for other in [a for a in bpy.data.objects if a.type == 'ARMATURE' and a is not arm]:
    src_m = {b: (arm.data.bones[b].matrix_local.copy(), arm.data.bones[b].length,
                 arm.data.bones[b].parent.name if arm.data.bones[b].parent else None) for b in needed}
    bpy.context.view_layer.objects.active = other
    bpy.ops.object.mode_set(mode='EDIT')
    eb = other.data.edit_bones
    for b in needed:
        mat, length, par = src_m[b]
        e = eb.get(b) or eb.new(b)
        e.length = length
        e.matrix = mat
        if par and par in eb:
            e.parent = eb[par]
    bpy.ops.object.mode_set(mode='OBJECT')
ours = []
for name, g in G.items():
    if name.startswith('_'):
        continue
    me = bpy.data.meshes.new(name)
    me.from_pydata([Vector(v) for v in g['verts']], [], [tuple(t) for t in g['tris']])
    me.update()
    uvl = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices:
            uvl.data[li].uv = g['uv'][me.loops[li].vertex_index]
    o = bpy.data.objects.new(name + '_new', me)
    bpy.context.scene.collection.objects.link(o)
    o.parent = ref.parent
    o.matrix_world = ref.matrix_world.copy()
    for k in ref.keys():
        if not k.startswith('FO4_SEG') and k != 'pynNodeName':
            o[k] = ref[k]
    o['pynBlockName'] = 'BSTriShape'
    groups = {b: o.vertex_groups.new(name=b) for b in sorted({b for w in g['weights'] for b in w})}
    for vi, w in enumerate(g['weights']):
        for b, x in w.items():
            groups[b].add([vi], x, 'REPLACE')
    a = o.modifiers.new('Armature', 'ARMATURE')
    a.object = arm
    me.materials.append(ref.data.materials[0].copy())
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.shade_smooth()
    ours.append((o, name))
for o in [o for o in bpy.data.objects if o.type == 'MESH' and o not in [x for x, _ in ours]]:
    bpy.data.objects.remove(o, do_unlink=True)
for o, name in ours:
    o.name = name
    o.data.name = name
    o['pynNodeName'] = name
pathlib.Path(dst).parent.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='DESELECT')
for o, _ in ours:
    o.select_set(True)
bpy.context.view_layer.objects.active = ours[0][0]
bpy.ops.export_scene.pynifly(filepath=dst)
print('BUILT', dst, [n for _, n in ours])
