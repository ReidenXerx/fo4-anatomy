"""Blender (background) + PyNifly: our shapes from a dc_geom.py json, skinned on the VANILLA deathclaw armature, ONLY
our shapes exported (the vanilla body is just the armature + material source; transplant.py puts our shapes into
UAP's file). Per-vertex UVs, weights per bone, welded normals as custom normals, morphs as '>Name' shape keys.
    blender -b -P dc_build.py -- <geom.json> <vanilla body.nif> <out.nif>"""
import json
import pathlib
import sys

import addon_utils
import bpy
from mathutils import Vector

geom, src, dst = sys.argv[sys.argv.index('--') + 1:][:3]
G = json.load(open(geom))
bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable('io_scene_nifly', default_set=True)
bpy.ops.import_scene.pynifly(filepath=src, rename_bones=False)
vanilla = [o for o in bpy.data.objects if o.type == 'MESH']
arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
ref = max(vanilla, key=lambda o: len(o.data.vertices))
need = {b for g in G.values() if isinstance(g, dict) and 'weights' in g for b in g['weights']}
arm = next((a for a in arms if need <= set(a.data.bones.keys())), None)
if arm is None:
    raise SystemExit(f'no armature carries {need}: {[sorted(a.data.bones.keys())[:10] for a in arms]}')
print('armature', arm.name, 'ref', ref.name)
mat = ref.data.materials[0]
built = []
for name, g in G.items():
    if name.startswith('_'):
        continue
    me = bpy.data.meshes.new(name)
    me.from_pydata([Vector(v) for v in g['verts']], [], [tuple(t) for t in g['tris']])
    me.update()
    uvl = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices:
            u_, v_ = g['uv'][me.loops[li].vertex_index]
            uvl.data[li].uv = (u_, 1.0 - v_)                  # json = nif convention; PyNifly flips v on export
    if g.get('colors'):                                       # per-vertex grey, 0..1 (the body's own colours
        ca = me.color_attributes.new(name='VERTEX_COLOR', type='FLOAT_COLOR', domain='POINT')   # are its shading)
        for i, c in enumerate(g['colors']):
            ca.data[i].color = (c, c, c, 1.0)
        me.color_attributes.active_color = ca
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.parent = ref.parent
    o.matrix_world = ref.matrix_world.Identity(4)
    for k in ref.keys():
        if not k.startswith('FO4_SEG') and k != 'pynNodeName':
            o[k] = ref[k]
    o['pynNodeName'] = name
    o['pynBlockName'] = 'BSTriShape'
    for bone, ws in g['weights'].items():
        vg = o.vertex_groups.new(name=bone)
        for i, w in enumerate(ws):
            if w > 1e-4:
                vg.add([i], w, 'REPLACE')
    a = o.modifiers.new('Armature', 'ARMATURE')
    a.object = arm
    mm = mat.copy()
    if g.get('mat'):                                          # [bgsm, d, n, s]: our own material on this shape
        mm['BSLSP_Shader_Name'] = g['mat'][0]
        for k, t in zip(('BSShaderTextureSet_Diffuse', 'BSShaderTextureSet_Normal', 'BSShaderTextureSet_Specular'),
                        g['mat'][1:]):
            mm[k] = t
    me.materials.append(mm)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.shade_smooth()
    me.normals_split_custom_set_from_vertices([Vector(n) for n in g['normals']])
    if g['morphs']:
        o.shape_key_add(name='Basis')
        for mname, d in g['morphs'].items():
            k = o.shape_key_add(name='>' + mname)
            for i, dv in enumerate(d):
                k.data[i].co = me.vertices[i].co + Vector(dv)
    built.append(o)
for o in vanilla:
    bpy.data.objects.remove(o, do_unlink=True)
pathlib.Path(dst).parent.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='DESELECT')
for o in built:
    o.select_set(True)
bpy.context.view_layer.objects.active = built[0]
bpy.ops.export_scene.pynifly(filepath=dst)
print('BUILT', dst, [o.name for o in built])
