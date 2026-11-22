"""Blender (background): a rigged penis mesh from an FBX -> JSON for servitron_male.py --mesh (2026-11-22, Ilham's penis
for Anatomy Servitron; Dudu's approval via Watcher). Run with --factory-startup --disable-autoexec (the FBX is untrusted).

    blender --background --factory-startup --disable-autoexec --python tools/fbx_penis_export.py -- <in.fbx> <object> <out.json>

Writes, in the armature's rest pose and world space (the FBX's own units):
  verts: [[x, y, z, nx, ny, nz, u, v, {group: weight}]] - one per (vertex, UV, normal) corner combination, as FO4 needs
  tris:  [[a, b, c]]
  bones: {name: [head xyz, tail xyz]}
"""
import json
import sys

import bpy

args = sys.argv[sys.argv.index('--') + 1:]
src, name, out = args
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=src)
ob = bpy.data.objects[name]
arm = ob.parent if ob.parent and ob.parent.type == 'ARMATURE' else None
if arm:
    arm.data.pose_position = 'REST'
bpy.context.view_layer.update()
deps = bpy.context.evaluated_depsgraph_get()
ev = ob.evaluated_get(deps)
me = ev.to_mesh()
me.calc_loop_triangles()
mw = ob.matrix_world
nm = mw.to_3x3().inverted().transposed()
uvl = me.uv_layers.active.data
groups = {g.index: g.name for g in ob.vertex_groups}
key, verts, tris = {}, [], []
for lt in me.loop_triangles:
    tri = []
    for li, vi in zip(lt.loops, lt.vertices):
        v = me.vertices[vi]
        p = mw @ v.co
        n = (nm @ me.corner_normals[li].vector).normalized()
        u, w = uvl[li].uv
        k = (vi, round(u, 5), round(w, 5), round(n.x, 3), round(n.y, 3), round(n.z, 3))
        if k not in key:
            key[k] = len(verts)
            wts = {groups[g.group]: round(g.weight, 5) for g in v.groups if g.weight > 0 and g.group in groups}
            verts.append([p.x, p.y, p.z, n.x, n.y, n.z, u, w, wts])
        tri.append(key[k])
    tris.append(tri)
bones = {}
if arm:
    for b in arm.data.bones:
        bones[b.name] = [list(arm.matrix_world @ b.head_local), list(arm.matrix_world @ b.tail_local)]
json.dump(dict(verts=verts, tris=tris, bones=bones, material=[m.name for m in ob.data.materials if m]), open(out, 'w'))
print(f'EXPORTED {name}: {len(verts)} verts, {len(tris)} tris, {len(bones)} bones -> {out}')
