"""Blender (background) + PyNifly: the VANILLA behemoth lower body without its loincloth (a separate piece of the
same shape; the skin under it is closed). Faces whose three corners are all loincloth positions (json list) are
deleted, loose vertices removed; ONLY that shape is exported (transplant.py replaces it in the vanilla nif).
    blender -b -P bh_cut.py -- <vanilla nif> <shape> <cloth positions.json> <out.nif>"""
import json
import pathlib
import sys

import addon_utils
import bmesh
import bpy

src, shape, cloth_json, dst = sys.argv[sys.argv.index('--') + 1:][:4]
cloth = {tuple(round(c, 2) for c in p) for p in json.load(open(cloth_json))}
bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable('io_scene_nifly', default_set=True)
bpy.ops.import_scene.pynifly(filepath=src, rename_bones=False)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
o = next(m for m in meshes if m.name.startswith(shape))
bm = bmesh.new()
bm.from_mesh(o.data)
key = {v: tuple(round(c, 2) for c in v.co) in cloth for v in bm.verts}
dead = [f for f in bm.faces if all(key[v] for v in f.verts)]
n0 = len(bm.verts)
bmesh.ops.delete(bm, geom=dead, context='FACES_ONLY')
loose = [v for v in bm.verts if not v.link_faces]
bmesh.ops.delete(bm, geom=loose, context='VERTS')
print('CUT', o.name, 'faces', len(dead), 'verts', n0, '->', len(bm.verts))
bm.to_mesh(o.data)
bm.free()
for m in meshes:
    if m is not o:
        bpy.data.objects.remove(m, do_unlink=True)
pathlib.Path(dst).parent.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='DESELECT')
o.select_set(True)
bpy.context.view_layer.objects.active = o
bpy.ops.export_scene.pynifly(filepath=dst)
print('BUILT', dst)
