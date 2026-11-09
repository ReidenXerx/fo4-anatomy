"""Feral ghoul genitals (owner-approved creature job, 11-09), built in Blender (background) with PyNifly.
  M  <src> <dst>: the vanilla feral body + OUR rotted, torn-off stump: 'FeralStump' (skin, the body's own material,
     UVs taken from the body surface it grows from) and 'FeralStumpWound' (the torn end, our wound material).
  F  <src> <dst>: the vanilla feral body with breasts sagging under the wasted muscle and a vulva, sculpted into the
     body's own surface (local subdivision + displacement along the normal), so skin and seams stay the body's.
Anchors come from raycasts on each mesh, so every feral variant gets them in its own place.
    blender -b -P feral_build.py -- <report.json> M|F <src.nif> <dst.nif> [M|F <src> <dst> ...]"""
import json
import math
import pathlib
import sys

import addon_utils
import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

args = sys.argv[sys.argv.index('--') + 1:]
REPORT = pathlib.Path(args[0])
JOBS = [args[i:i + 3] for i in range(1, len(args), 3)]
WOUND_BGSM = 'Materials\\Anatomy\\Creatures\\FeralStumpWound.bgsm'
WOUND_TEX = 'textures\\Anatomy\\Creatures\\FeralStumpWound_{}.dds'
VULVA_BGSM = 'Materials\\Anatomy\\Creatures\\FeralVulvaInner.bgsm'      # same length as the wound names (byte copy)
VULVA_TEX = 'textures\\Anatomy\\Creatures\\FeralVulvaInner_{}.dds'


def fresh(src):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    addon_utils.enable('io_scene_nifly', default_set=True)
    bpy.ops.import_scene.pynifly(filepath=src)
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    skip = ('hair', 'flash', 'fx', 'streak')
    body = max((o for o in meshes if o.data.materials and not any(k in o.name.lower() for k in skip)),
               key=lambda o: len(o.data.vertices))
    return body, meshes


def tree(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


def front_hit(t, x, z, y0=60.0):
    hit = t.ray_cast(Vector((x, y0, z)), Vector((0, -1, 0)), 200)
    return hit if hit[0] is not None else None


def anchors(body):
    t = tree(body)
    gap = None
    for k in range(0, 400):                                   # top of the gap between the legs, at x = 0
        z = 75.0 - k * 0.1
        if front_hit(t, 0.0, z) is None:
            gap = z
            break
    top = max((body.matrix_world @ v.co).z for v in body.data.vertices)
    best = None
    lo_z = gap + 0.50 * (top - gap)                           # the chest band, above the feral's belly bulge
    for k in range(0, int(0.25 * (top - gap) / 0.1)):         # pectoral: where it sticks out most in that band
        z = lo_z + k * 0.1
        h = front_hit(t, 5.5, z)
        if h and (best is None or h[0].y > best[1]):
            best = (z, h[0].y)
    return t, gap, best[0] if best else None


def copy_props(src, dst, name):
    for k in src.keys():
        if k.startswith('FO4_SEG') or k in ('pynNodeName',):
            continue
        dst[k] = src[k]
    dst['pynNodeName'] = name
    dst['pynBlockName'] = 'BSTriShape'


def skin_like(body, obj):
    """Parent, armature modifier, vertex groups (by nearest body face) and UVs from the body."""
    obj.parent = body.parent
    arm = next((m.object for m in body.modifiers if m.type == 'ARMATURE'), None)
    for g in body.vertex_groups:
        if not g.name.startswith('FO4 '):
            obj.vertex_groups.new(name=g.name)
    bpy.context.view_layer.objects.active = obj
    dt = obj.modifiers.new('dt', 'DATA_TRANSFER')
    dt.object = body
    dt.use_vert_data = True
    dt.data_types_verts = {'VGROUP_WEIGHTS'}
    dt.vert_mapping = 'POLYINTERP_NEAREST'
    dt.layers_vgroup_select_src = 'ALL'
    dt.layers_vgroup_select_dst = 'NAME'
    bpy.ops.object.modifier_apply(modifier='dt')
    # drop empty groups, keep at most what the body uses
    for g in list(obj.vertex_groups):
        if not any(g.index in [e.group for e in v.groups if e.weight > 1e-4] for v in obj.data.vertices):
            obj.vertex_groups.remove(g)
    if arm:
        a = obj.modifiers.new('Armature', 'ARMATURE')
        a.object = arm


def uv_from_body(body, obj):
    if not obj.data.uv_layers:
        obj.data.uv_layers.new(name='UVMap')
    bpy.context.view_layer.objects.active = obj
    dt = obj.modifiers.new('uv', 'DATA_TRANSFER')
    dt.object = body
    dt.use_loop_data = True
    dt.data_types_loops = {'UV'}
    dt.loop_mapping = 'POLYINTERP_NEAREST'
    bpy.ops.object.modifier_apply(modifier='uv')


def noise1(i, seed):
    v = math.sin(i * 12.9898 + seed * 78.233) * 43758.5453
    return v - math.floor(v)


def stump(body, t, gap):
    """A short, slightly drooping tube out of the pubis with a ragged, torn end; returns (shaft, wound)."""
    z0 = gap + 3.2
    h = front_hit(t, 0.0, z0)
    base, nrm = h[0], h[1]
    axis = (nrm.normalized() * 0.85 + Vector((0, 0, -0.55))).normalized()
    side = axis.cross(Vector((1, 0, 0))).normalized()
    up = side.cross(axis).normalized()
    seg, rings, length = 16, 7, 3.1
    sbm, wbm = bmesh.new(), bmesh.new()
    ring_vs = []
    for r in range(rings + 1):
        f = r / rings
        rad = (1.05 - 0.18 * f) * (1.0 + 0.06 * math.sin(r * 2.1))
        row = []
        for s in range(seg):
            a = 2 * math.pi * s / seg
            d = -0.6 + f * length
            jag = 0.0
            if r == rings:                                     # the torn end: ragged, uneven lengths
                jag = (noise1(s, 3) - 0.5) * 0.7
            p = base + axis * (d + jag) + (math.cos(a) * side + math.sin(a) * up) * rad
            row.append(sbm.verts.new(p))
        ring_vs.append(row)
    for r in range(rings):
        for s in range(seg):
            a, b = ring_vs[r][s], ring_vs[r][(s + 1) % seg]
            c, d = ring_vs[r + 1][(s + 1) % seg], ring_vs[r + 1][s]
            sbm.faces.new((a, b, c, d))
    # wound: the torn end, a sunken, lumpy cap of raw meat (own material)
    end = [v.co.copy() for v in ring_vs[-1]]
    centre = sum(end, Vector()) / len(end) - axis * 0.35
    outer = [wbm.verts.new(p) for p in end]
    mid = [wbm.verts.new(centre.lerp(p, 0.55) + axis * ((noise1(i, 7) - 0.5) * 0.3)) for i, p in enumerate(end)]
    c = wbm.verts.new(centre)
    for s in range(seg):
        n = (s + 1) % seg
        wbm.faces.new((outer[s], outer[n], mid[n], mid[s]))
        wbm.faces.new((mid[s], mid[n], c))
    bmesh.ops.recalc_face_normals(sbm, faces=sbm.faces)
    bmesh.ops.recalc_face_normals(wbm, faces=wbm.faces)
    objs = []
    for name, bm in (('FeralStump', sbm), ('FeralStumpWound', wbm)):
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(o)
        copy_props(body, o, name)
        objs.append(o)
    shaft, wound = objs
    uv_from_body(body, shaft)
    # wound UVs: a disc projection onto its own texture
    wound.data.uv_layers.new(name='UVMap')
    uvl = wound.data.uv_layers['UVMap'].data
    for poly in wound.data.polygons:
        for li in poly.loop_indices:
            v = wound.data.vertices[wound.data.loops[li].vertex_index].co - centre
            uvl[li].uv = (0.5 + v.dot(side) / 2.6, 0.5 + v.dot(up) / 2.6)
    for o in (shaft, wound):
        skin_like(body, o)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.shade_smooth()
    shaft.data.materials.append(body.data.materials[0].copy())
    wound.data.materials.append(wound_material(body))
    return dict(stump_base=tuple(round(v, 2) for v in base), axis=tuple(round(v, 3) for v in axis))


def sculpt(body, region, fn, rounds):
    """Subdivide the body's faces touching region(co) `rounds` times (each round splits a triangle into four, so the
    density is even inside), then displace every vertex by fn(co) along its normal. Weights, UVs and segments
    interpolate with the subdivision."""
    me = body.data
    bm = bmesh.new()
    bm.from_mesh(me)
    faces = []
    for _ in range(rounds):
        faces = [f for f in bm.faces if region(f.calc_center_median()) or any(region(v.co) for v in f.verts)]
        edges = list({e for f in faces for e in f.edges})
        if not edges:
            break
        bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1, use_grid_fill=True, smooth=0.0)
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bm.normal_update()
    moved = 0
    for v in bm.verts:
        d = fn(v.co)
        if d:
            v.co += v.normal * d
            moved += 1
    bm.to_mesh(me)
    bm.free()
    me.update()
    return moved, len(faces)


def female(body, t, gap, nip_z):
    out = {}
    nx = 5.6

    def breast(co):
        a = 0.0
        for sx in (-1, 1):
            dx = co.x - sx * nx
            dz = co.z - (nip_z - 0.6)
            sz = 3.9 if dz > 0 else 2.6                      # sag: fuller below the nipple line
            g = math.exp(-(dx / 3.4) ** 2 - (dz / sz) ** 2)
            nip = 0.22 * math.exp(-((co.x - sx * nx) / 0.45) ** 2 - ((co.z - nip_z + 0.9) / 0.45) ** 2)
            a += 1.7 * g + nip
        return a if co.y > 0 else 0.0

    reg = lambda c: c.y > 0 and abs(c.x) < 12 and nip_z - 9 < c.z < nip_z + 7         # noqa: E731
    out['breasts'] = sculpt(body, reg, breast, 2)
    # glowing variants wrap the body in effect shells (flash / streak): they get the same breasts, or the breasts
    # would poke through the glow
    shells = [o for o in bpy.data.objects if o.type == 'MESH' and o is not body and
              any(k in o.name.lower() for k in ('flash', 'fx', 'streak')) and len(o.data.vertices) > 1500]
    out['shells'] = [(o.name, sculpt(o, reg, breast, 2)[0]) for o in shells]
    out['vulva'] = vulva_patch(body, t, gap)
    return out


def vulva_sculpt(body, gap):
    """The vulva sculpted INTO the body (no overlay shape: a shape lying on the skin z-fights in game). Each vertex
    is placed on an arc round the crotch (angle about a point inside the pelvis): s = 0 under the crotch (perineum)
    -> 1 at the lower pubis; labia rise either side of a slit that cuts inward."""
    centre = Vector((0.0, 1.0, gap + 1.2))
    a0, a1 = math.radians(-115), math.radians(-30)
    half_w = 2.2

    def arc_s(co):
        d = co - centre
        a = math.atan2(d.z, d.y)                              # y forward, z up
        return (a - a0) / (a1 - a0)

    def region(co):
        s = arc_s(co)
        return abs(co.x) < half_w + 0.6 and -0.15 < s < 1.15 and (co - centre).length < 9

    def fn(co):
        s = arc_s(co)
        if not (0.0 < s < 1.0) or abs(co.x) > half_w:
            return 0.0
        env_v = math.sin(math.pi * min(max((s - 0.10) / 0.82, 0), 1)) ** 0.8
        env_u = max(0.0, 1 - (abs(co.x) / half_w) ** 2) ** 1.5
        lab = 0.40 * math.exp(-((abs(co.x) - 0.78) / 0.42) ** 2)
        slit = 0.30 * math.exp(-(co.x / 0.14) ** 2)
        return (lab - slit) * env_v * env_u

    return sculpt(body, region, fn, 3)


def vulva_patch(body, t, gap):
    """'FeralVulva': a fine patch that hugs the crotch surface from the underside round to the pubis (raycast onto
    the body along an arc), then rises into labia either side of a slit. Its edge sits on the skin; UVs and weights
    come from the body, so it wears the body's own skin."""
    nu, nv = 32, 44
    half_w = 1.9
    centre = Vector((0.0, 1.0, gap + 1.2))                    # inside the pelvis, behind the crotch
    a0, a1 = math.radians(-115), math.radians(-30)            # from under the crotch round to the lower pubis
    bm = bmesh.new()
    blend = bm.verts.layers.float.new('blend')                # 1 = take the body's normal (patch edge), 0 = own
    grid = []
    for j in range(nv + 1):
        a = a0 + (a1 - a0) * j / nv
        d = Vector((0.0, math.cos(a), math.sin(a)))           # y forward, z up: -90 deg = straight down
        row = []
        for i in range(nu + 1):
            u = -half_w + 2 * half_w * i / nu
            origin = centre + d * 25.0 + Vector((u, 0, 0))
            hit = t.ray_cast(origin, -d, 60)
            if hit[0] is None:
                row.append(None)
                continue
            p, n = hit[0], hit[1]
            s = j / nv                                         # 0 at the back (perineum), 1 at the pubis
            # elliptical footprint: r = 0 at the centre, 1 on the rim; nothing outside
            r = math.sqrt((u / half_w) ** 2 + ((s - 0.5) / 0.5) ** 2)
            if r > 1.0:
                row.append(None)
                continue
            edge = 1.0 - r

            def ss(a, b, x):
                k = min(max((x - a) / (b - a), 0.0), 1.0)
                return k * k * (3 - 2 * k)
            env = ss(0.08, 0.55, edge)
            # run 6 (11-09): 0.40 labia + a 0.15 slit read as plain skin in game -> fuller labia, wider slit
            lab = 0.72 * math.exp(-((abs(u) - 0.80) / 0.42) ** 2)
            slit = 0.70 * math.exp(-(u / 0.24) ** 2)
            # the patch floats 0.10 above the skin inside (no z-fighting, the body never pokes through) and its rim
            # dives 0.08 UNDER the skin, so no plate edge can show
            base = -0.08 + 0.18 * ss(0.0, 0.35, edge)
            rise = base + (lab - slit * (lab / 0.72)) * env
            v = bm.verts.new(p + n.normalized() * rise)
            v[blend] = 1.0 - env
            row.append(v)
        grid.append(row)
    for j in range(nv):
        for i in range(nu):
            q = (grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i])
            if all(q):
                bm.faces.new(q)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new('FeralVulva')
    weights = [v[blend] for v in bm.verts]
    bm.to_mesh(me)
    n_faces = len(bm.faces)
    bm.free()
    o = bpy.data.objects.new('FeralVulva', me)
    bpy.context.scene.collection.objects.link(o)
    # outward normals: away from the pelvis centre
    me.update()
    if sum((p.center - centre).dot(p.normal) for p in me.polygons) < 0:
        for p in me.polygons:
            p.flip()
    copy_props(body, o, 'FeralVulva')
    uv_from_body(body, o)
    # the patch edge takes the body's own (faceted) normals, so no plate outline shows where it meets the skin
    g = o.vertex_groups.new(name='_blend')
    for i, w in enumerate(weights):
        g.add([i], w, 'REPLACE')
    bpy.context.view_layer.objects.active = o
    dt = o.modifiers.new('nrm', 'DATA_TRANSFER')
    dt.object = body
    dt.use_loop_data = True
    dt.data_types_loops = {'CUSTOM_NORMAL'}
    dt.loop_mapping = 'POLYINTERP_NEAREST'
    dt.vertex_group = '_blend'
    bpy.ops.object.modifier_apply(modifier='nrm')
    if '_blend' in o.vertex_groups:
        o.vertex_groups.remove(o.vertex_groups['_blend'])
    skin_like(body, o)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.shade_smooth()
    # the body's own material and UVs: it follows every material swap (withered, charred, UAP's colour skins)
    o.data.materials.append(body.data.materials[0].copy())
    inner = vulva_inner(body, t, centre, a0, a1, half_w)
    return dict(faces=n_faces, inner_faces=inner)


def vulva_inner(body, t, centre, a0, a1, half_w):
    """'FeralVulvaInner': a narrow strip of dark, raw flesh (the stump's wound material) lying just above the slit
    floor: the labia rise over its edges, so it shows only inside the slit."""
    nu, nv, w = 6, 36, 0.42
    bm = bmesh.new()
    grid = []
    for j in range(nv + 1):
        s = 0.12 + 0.76 * j / nv
        a = a0 + (a1 - a0) * s
        d = Vector((0.0, math.cos(a), math.sin(a)))
        row = []
        for i in range(nu + 1):
            u = -w + 2 * w * i / nu
            hit = t.ray_cast(centre + d * 25.0 + Vector((u, 0, 0)), -d, 60)
            row.append(bm.verts.new(hit[0] + hit[1].normalized() * 0.12) if hit[0] is not None else None)
        grid.append(row)
    for j in range(nv):
        for i in range(nu):
            q = (grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i])
            if all(q):
                bm.faces.new(q)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new('FeralVulvaInner')
    coords = {v: (0.5 + (i / nu - 0.5) * 0.35, 0.15 + 0.7 * j / nv) for j, row in enumerate(grid)
              for i, v in enumerate(row) if v is not None}
    bm.verts.index_update()
    vuv = {v.index: coords[v] for v in bm.verts}
    bm.to_mesh(me)
    n = len(bm.faces)
    bm.free()
    o = bpy.data.objects.new('FeralVulvaInner', me)
    bpy.context.scene.collection.objects.link(o)
    me.update()
    if sum((p.center - centre).dot(p.normal) for p in me.polygons) < 0:
        for p in me.polygons:
            p.flip()
    copy_props(body, o, 'FeralVulvaInner')
    layer = me.uv_layers.new(name='UVMap')
    for li, loop in enumerate(me.loops):
        layer.data[li].uv = vuv[loop.vertex_index]
    skin_like(body, o)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.shade_smooth()
    o.data.materials.append(wound_material(body, VULVA_BGSM, VULVA_TEX))      # pink mucosa, not the dark wound
    return n


def wound_material(body, bgsm=None, tex=None):
    wm = body.data.materials[0].copy()
    wm['BSLSP_Shader_Name'] = bgsm or WOUND_BGSM
    for k, kind in (('BSShaderTextureSet_Diffuse', 'd'), ('BSShaderTextureSet_Normal', 'n'),
                    ('BSShaderTextureSet_Specular', 's')):
        wm[k] = (tex or WOUND_TEX).format(kind)
    return wm


def export(dst, meshes):
    pathlib.Path(dst).parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes:
        if o.name not in bpy.context.view_layer.objects:      # PyNifly leaves some FX shapes out of the layer
            bpy.context.scene.collection.objects.link(o)
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.export_scene.pynifly(filepath=dst)


report = {}
import traceback


VARIANT = ['']


def job(kind, src, dst):
    VARIANT[0] = pathlib.Path(dst).stem.removesuffix('_F')
    body, meshes = fresh(src)
    t, gap, nip_z = anchors(body)
    info = dict(gap=round(gap, 2) if gap else None, nipple_z=round(nip_z, 2) if nip_z else None)
    if gap is None:
        info['error'] = 'no leg gap found'
    elif kind == 'M':
        info.update(stump(body, t, gap))
        meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    else:
        info.update(female(body, t, gap, nip_z))
        meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    export(dst, meshes)
    return info


for kind, src, dst in JOBS:
    try:
        info = job(kind, src, dst)
    except Exception:                                                   # noqa: BLE001
        info = {'error': traceback.format_exc()[-600:]}
    report[dst] = info
    print('BUILT', kind, dst, {k: v for k, v in info.items() if k != 'error'}, 'ERROR' if 'error' in info else '')
    REPORT.write_text(json.dumps(report, indent=1))
