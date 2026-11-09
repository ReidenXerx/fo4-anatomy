"""Blender (background) + PyNifly: a VANILLA canine body nif + our genitals (canine_geom.py json) -> <out.nif>.
  <penis name>  : our penis (+ sheath lining), CaninePenis material, every vertex 100% <pelvis bone> (as UAP's)
  <sheath name> : our sheath, the material + UVs of the body piece nearest to it (each dog keeps its own fur),
                  100% <pelvis bone>
Morphs become '>Name' shape keys, so PyNifly writes <out>.tri next to the nif + the BODYTRI string itself.
    blender -b -P canine_build.py -- <geom.json> <vanilla.nif> <out.nif> <penis name> <sheath name> <pelvis bone>"""
import json
import pathlib
import sys

import addon_utils
import bpy
from mathutils import Vector

geom, src, dst, pen_name, sh_name, pelvis = sys.argv[sys.argv.index('--') + 1:][:6]
G = json.load(open(geom))
PEN_BGSM = 'Materials\\Anatomy\\Creatures\\CaninePenis.bgsm'
PEN_TEX = 'textures\\Anatomy\\Creatures\\CaninePenis_{}.dds'

bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable('io_scene_nifly', default_set=True)
bpy.ops.import_scene.pynifly(filepath=src, rename_bones=False)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
arm = next((a for a in arms if pelvis in a.data.bones), None)
if arm is None:
    raise SystemExit(f'no armature carries {pelvis}: {[list(a.data.bones.keys())[:8] for a in arms]}')
bodies = [o for o in meshes if o.data.materials and not any(k in o.name.lower() for k in
                                                                ('cap', 'eye', 'fur', 'teeth', 'tongue', 'dirt'))]  # alpha shells: no
ref = max(bodies, key=lambda o: len(o.data.vertices))
print('armature', arm.name, 'bodies', [o.name for o in bodies])


def copy_props(src_o, dst_o, name):
    for k in src_o.keys():
        if k.startswith('FO4_SEG') or k in ('pynNodeName',):
            continue
        dst_o[k] = src_o[k]
    dst_o['pynNodeName'] = name
    dst_o['pynBlockName'] = 'BSTriShape'                   # seg_fix.py retypes it with UAP's segment layout


def build(name, g):
    me = bpy.data.meshes.new(name)
    me.from_pydata([Vector(v) for v in g['verts']], [], [tuple(t) for t in g['tris']])
    me.update()
    uvl = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices:
            uvl.data[li].uv = g['uv'][me.loops[li].vertex_index]
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.parent = ref.parent
    o.matrix_world = ref.matrix_world.Identity(4)             # our geometry is in root space (UAP's shapes: t = 0)
    copy_props(ref, o, name)
    vg = o.vertex_groups.new(name=pelvis)
    vg.add(list(range(len(me.vertices))), 1.0, 'REPLACE')
    a = o.modifiers.new('Armature', 'ARMATURE')
    a.object = arm
    if g['morphs']:
        o.shape_key_add(name='Basis')
        for mname, d in g['morphs'].items():
            k = o.shape_key_add(name='>' + mname)
            for i, dv in enumerate(d):
                k.data[i].co = me.vertices[i].co + Vector(dv)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.shade_smooth()
    return o


if ref.matrix_world != ref.matrix_world.Identity(4):
    print('WARNING body world matrix not identity', [list(r) for r in ref.matrix_world])
pen = build(pen_name, G['penis'])
sh = build(sh_name, G['sheath'])
pm = ref.data.materials[0].copy()
pm['BSLSP_Shader_Name'] = PEN_BGSM
for k, kind in (('BSShaderTextureSet_Diffuse', 'd'), ('BSShaderTextureSet_Normal', 'n'),
                ('BSShaderTextureSet_Specular', 's')):
    pm[k] = PEN_TEX.format(kind)
pen.data.materials.append(pm)
# the sheath: material + UVs of the nearest body piece (by mean distance of its vertices)
c = sum((sh.matrix_world @ v.co for v in sh.data.vertices), Vector()) / len(sh.data.vertices)


def dist(o):
    ok, loc, _, _ = o.closest_point_on_mesh(o.matrix_world.inverted() @ c)
    return (o.matrix_world @ loc - c).length if ok else 1e9


near = min(bodies, key=dist)
print('sheath fur from', near.name, round(dist(near), 2), 'material', near.data.materials[0].get('BSLSP_Shader_Name'))
sh.data.materials.append(near.data.materials[0].copy())
# sheath UVs: each vertex takes the belly UV straight ABOVE it (ray up onto the fur piece), sampled at |x| >= 0.4 so a
# tube under the centre line never straddles the left/right UV islands (nearest-face transfer gave stretched stripes)
from mathutils.bvhtree import BVHTree  # noqa: E402
from mathutils.interpolate import poly_3d_calc  # noqa: E402

nm = near.data
nm.calc_loop_triangles()
bvh = BVHTree.FromPolygons([near.matrix_world @ v.co for v in nm.vertices], [p.vertices for p in nm.polygons])
nuv = nm.uv_layers.active.data


def project_uv(obj, samples):
    """each loop takes the fur UV straight ABOVE its vertex's sample point (x, y) on the nearest body piece"""
    suv = obj.data.uv_layers.active.data
    miss = 0
    for poly in obj.data.polygons:
        for li in poly.loop_indices:
            vi = obj.data.loops[li].vertex_index
            p = obj.matrix_world @ obj.data.vertices[vi].co
            sx, sy = samples[vi] if samples else (max(abs(p.x), 0.4), p.y)
            q = Vector((sx, sy, p.z - 30.0))
            loc, nrm, fi, _ = bvh.ray_cast(q, Vector((0, 0, 1)), 200.0)
            if fi is None:
                loc, nrm, fi, _ = bvh.find_nearest(Vector((sx, sy, p.z)))
                miss += 1
            fp = nm.polygons[fi]
            cos = [near.matrix_world @ nm.vertices[v].co for v in fp.vertices]
            w = poly_3d_calc(cos, loc)
            uv = Vector((0.0, 0.0))
            for wk, lk in zip(w, fp.loop_indices):
                uv += nuv[lk].uv * wk
            suv[li].uv = uv
    return miss


print('sheath uv by projection, fallbacks', project_uv(sh, G['sheath'].get('sample')))
# optional furred scrotum (bears): 7th argument = its shape name (UAP's balls name), same fur + projection
args7 = sys.argv[sys.argv.index('--') + 1:]
if len(args7) > 6 and 'sack' in G:
    sk = build(args7[6], G['sack'])
    sk.data.materials.append(near.data.materials[0].copy())
    if G['sack'].get('planar'):
        print('sack uv planar (json)')
    else:
        print('sack uv by projection, fallbacks', project_uv(sk, G['sack'].get('sample')))
pathlib.Path(dst).parent.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='DESELECT')
for o in [o for o in bpy.data.objects if o.type == 'MESH']:
    if o.name not in bpy.context.view_layer.objects:
        bpy.context.scene.collection.objects.link(o)
    o.select_set(True)
bpy.context.view_layer.objects.active = ref
bpy.ops.export_scene.pynifly(filepath=dst)
print('BUILT', dst, [o.name for o in bpy.data.objects if o.type == 'MESH'])
