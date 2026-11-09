"""Blender (background) + PyNifly: SynthGen2Body.nif with OUR synth penis (nick_geom.py json) in place of UAP's.
UAP's import supplies the armature (it alone carries the penis bones) and the penis shape's space; UAP's
Synt_Gen2_Penis is deleted and Body:0 gets the VANILLA weights back (UAP re-weighted its crotch), so the file holds
vanilla body data + our shapes.
    blender -b -P nick_build.py -- <geom.json> <uap SynthGen2Body.nif> <out.nif>"""
import json
import pathlib
import sys

import addon_utils
import bmesh
import bpy
from mathutils import Matrix, Vector

geom_path, src, dst = sys.argv[sys.argv.index('--') + 1:][:3]
G = json.load(open(geom_path))
JOINT_BGSM = 'Materials\\actors\\Synths\\Gen2a.BGSM'
JOINT_TEX = 'textures\\Actors\\Synths\\Gen2Synth_{}.dds'

bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable('io_scene_nifly', default_set=True)
bpy.ops.import_scene.pynifly(filepath=src, rename_bones=False)       # nif bone names = vertex group names
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
uap = next(o for o in meshes if o.name.startswith('Synt_Gen2_Penis'))
body = next(o for o in meshes if o.name.startswith('Body:0'))
arm = next(m.object for m in uap.modifiers if m.type == 'ARMATURE')
print('uap matrix', [list(r) for r in uap.matrix_world])
print('UAPKEYS', {k: (str(uap[k])[:80]) for k in uap.keys()})
# our coordinates are UAP's penis SHAPE space: check PyNifly kept the mesh in that space (local == nif positions)
lo = [min(v.co[i] for v in uap.data.vertices) for i in range(3)]
hi = [max(v.co[i] for v in uap.data.vertices) for i in range(3)]
want_lo, want_hi = G['_uap_penis_bbox']
err = max(abs(a - b) for a, b in zip(lo + hi, want_lo + want_hi))
print('uap local bbox', [round(x, 2) for x in lo + hi], 'nif bbox', [round(x, 2) for x in want_lo + want_hi], 'err', err)
if err > 0.01:
    raise SystemExit('UAP penis local space differs from its nif shape space')


def copy_props(src_o, dst_o, name):
    for k in src_o.keys():
        if k.startswith('FO4_SEG') or k in ('pynNodeName',):
            continue
        dst_o[k] = src_o[k]
    dst_o['pynNodeName'] = name
    dst_o['pynBlockName'] = 'BSTriShape'


def build(name, g, material):
    me = bpy.data.meshes.new(name)
    me.from_pydata([Vector(v) for v in g['verts']], [], [tuple(t) for t in g['tris']])
    me.update()
    uvl = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices:
            uvl.data[li].uv = g['uv'][me.loops[li].vertex_index]
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.parent = uap.parent
    o.matrix_world = uap.matrix_world.copy()
    copy_props(uap, o, name)
    groups = {}
    for b in sorted({b for w in g['weights'] for b in w}):
        if b not in arm.data.bones:
            raise SystemExit(f'bone {b} not in the armature')
        groups[b] = o.vertex_groups.new(name=b)
    for vi, w in enumerate(g['weights']):
        for b, x in w.items():
            if b not in groups:
                if b not in arm.data.bones:
                    raise SystemExit(f'bone {b} not in the armature')
                groups[b] = o.vertex_groups.new(name=b)
            groups[b].add([vi], x, 'REPLACE')
    a = o.modifiers.new('Armature', 'ARMATURE')
    a.object = arm
    # winding comes from nick_geom.py (open strips: a recalc could flip them)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.shade_smooth()
    me.materials.append(material)
    return o


plate_mat = body.data.materials[0].copy()                    # the synth body material: skin swaps apply
joint_mat = body.data.materials[0].copy()
joint_mat['BSLSP_Shader_Name'] = JOINT_BGSM
for k, kind in (('BSShaderTextureSet_Diffuse', 'd'), ('BSShaderTextureSet_Normal', 'n'),
                ('BSShaderTextureSet_Specular', 's')):
    joint_mat[k] = JOINT_TEX.format(kind)
print('body material props', {k: body.data.materials[0][k] for k in body.data.materials[0].keys()
                              if 'Shader_Name' in k or 'TextureSet_Diffuse' in k})
ours = [build('Synt_Gen2_Penis_new', G['Synt_Gen2_Penis'], plate_mat),
        build('Synt_Gen2_PenisJoints', G['Synt_Gen2_PenisJoints'], joint_mat)]
# Body:0: vanilla weights back (same vertex order + positions as vanilla, checked)
bp = G['_body_positions']
if len(body.data.vertices) != len(bp):
    raise SystemExit(f'Body:0 has {len(body.data.vertices)} verts, vanilla {len(bp)}')
derr = max((Vector(bp[i]) - v.co).length for i, v in enumerate(body.data.vertices))
print('Body:0 vs vanilla positions max', derr)
if derr > 1e-3:
    raise SystemExit('Body:0 vertex order differs from vanilla')
for g in list(body.vertex_groups):
    if not g.name.startswith('FO4 '):
        g.remove(list(range(len(body.data.vertices))))
for g in [g for g in body.vertex_groups if g.name.startswith('Penis') or g.name.startswith('Belly_01')]:
    body.vertex_groups.remove(g)
for vi, ws in enumerate(G['_body_weights']):
    for b, x in ws:
        g = body.vertex_groups.get(b) or body.vertex_groups.new(name=b)
        g.add([vi], x, 'REPLACE')
bpy.data.objects.remove(uap, do_unlink=True)
ours[0].name = 'Synt_Gen2_Penis'
ours[0]['pynNodeName'] = 'Synt_Gen2_Penis'
ours[0].data.name = 'Synt_Gen2_Penis'
# PyNifly builds one armature per distinct bind pose: UAP's penis bind (= the ZeX skeleton, checked) sits in `arm`,
# UAP's Body:0 bind (its Penis_01/02 off by ~0.65, no Penis_03..05) in another, and the exporter resolves bones through
# that other one -> Penis_03..05 silently dropped. Body:0 no longer uses penis bones, so every armature gets the
# correct chain (same armature-space matrices as `arm`).
PEN = ['Penis_00', 'Penis_01', 'Penis_02', 'Penis_03', 'Penis_04', 'Penis_05', 'Penis_Balls_01']
for other in [a for a in bpy.data.objects if a.type == 'ARMATURE' and a is not arm]:
    if (other.matrix_world.translation - arm.matrix_world.translation).length > 1e-4:
        raise SystemExit(f'armature {other.name} placed differently from {arm.name}')
    src_m = {b: (arm.data.bones[b].matrix_local.copy(), arm.data.bones[b].length,
                 arm.data.bones[b].parent.name if arm.data.bones[b].parent else None) for b in PEN}
    bpy.ops.object.mode_set(mode='OBJECT') if bpy.context.object and bpy.context.object.mode != 'OBJECT' else None
    bpy.context.view_layer.objects.active = other
    bpy.ops.object.mode_set(mode='EDIT')
    eb = other.data.edit_bones
    for b in PEN:
        mat, length, par = src_m[b]
        e = eb.get(b) or eb.new(b)
        e.length = length
        e.matrix = mat
        if par and par in eb:
            e.parent = eb[par]
        e.use_deform = True
    bpy.ops.object.mode_set(mode='OBJECT')
    print('FIXED ARMATURE', other.name, [(b, tuple(round(x, 2) for x in other.data.bones[b].head_local)) for b in PEN])
for o in ours:
    cnt = {g.name: 0 for g in o.vertex_groups}
    for v in o.data.vertices:
        for e in v.groups:
            cnt[o.vertex_groups[e.group].name] += 1
    print('GROUPS', o.name, cnt)
print('ARMBONES', [b.name for b in arm.data.bones if 'Penis' in b.name], [(b.name, b.use_deform) for b in arm.data.bones
                                                                           if 'Penis' in b.name and not b.use_deform])
keep = [o for o in bpy.data.objects if o.type == 'MESH']
pathlib.Path(dst).parent.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='DESELECT')
for o in keep:
    if o.name not in bpy.context.view_layer.objects:
        bpy.context.scene.collection.objects.link(o)
    o.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.export_scene.pynifly(filepath=dst)
print('BUILT', dst, [o.name for o in keep])
