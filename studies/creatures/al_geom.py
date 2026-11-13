"""Immersive Aliens (Dudu 11-13): kassarawi's own "TentaTussy" (Tuss.fbx from her cleaned pack; credit kassarawi) on
the Zetan body (Actors\\Alien\\CharacterAssets\\Alien_Body.nif). Blender script: her mesh in its bind pose (metres,
front -y, root bone TusRoot at her avatar's crotch), turned to face the alien's front (+y), scaled K game units per
metre, its root put just inside the alien's crotch skin (ray straight up at x = 0). Rigid on Pelvis.
  rest    = the tentacles drawn back into the sheath (their length along the extension axis x REST_K, girth x0.85):
            a cone sticking out of a walking alien looks wrong, Unity animated them with bones
  Erection morph (AAF's name) = rest -> her extended bind pose
Writes a dc_build.py json: one shape 'AlienTenta' (verts, tris, nif-convention uv, normals, weights, morphs).
    blender -b --factory-startup --disable-autoexec -P al_geom.py -- <Tuss.fbx> <alien_body.nif> <out json>"""
import json
import sys

import bmesh
import bpy
import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402

fbx, body_nif, out = sys.argv[sys.argv.index('--') + 1:][:3]
K = 75.0                    # game units per metre of her avatar
REST_K = 0.18               # rest: tentacles at 18 % of their extended length
SINK = 0.6                  # root this far inside the skin (game units)

# ---------------------------------------------------------------- the alien's crotch
b = nif.Nif(body_nif)
bs = max(b.shapes(), key=lambda s: s.count)
BV = np.array(bs.positions())
BT = np.array(bs.triangles())


def ray_up(x, y, z0=-60.0):
    o = np.array([x, y, z0])
    d = np.array([0.0, 0.0, 1.0])
    V0, V1, V2 = BV[BT[:, 0]], BV[BT[:, 1]], BV[BT[:, 2]]
    E1, E2 = V1 - V0, V2 - V0
    p = np.cross(d, E2)
    det = (E1 * p).sum(1)
    ok = np.abs(det) > 1e-9
    inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
    s = o - V0
    u = (s * p).sum(1) * inv
    q = np.cross(s, E1)
    v = (q * d).sum(1) * inv
    t = (E2 * q).sum(1) * inv
    hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)
    return o + t[hit].min() * d if hit.any() else None


crotch = ray_up(0.0, 0.0)
print('alien crotch', crotch.round(2))

# ---------------------------------------------------------------- her mesh
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)
o = next(x for x in bpy.data.objects if x.type == 'MESH')
arm = next(x for x in bpy.data.objects if x.type == 'ARMATURE')
mw = np.array(o.matrix_world)
root = np.array(arm.matrix_world @ arm.pose.bones['TusRoot'].head)
bm = bmesh.new()
bm.from_mesh(o.data)
bmesh.ops.triangulate(bm, faces=bm.faces)
bm.verts.ensure_lookup_table()
uvl = bm.loops.layers.uv.active
P = np.array([v.co[:] for v in bm.verts]) @ mw[:3, :3].T + mw[:3, 3]
# vertex -> its tentacle share (weights to bones whose name holds 'Tent')
names = [g.name for g in o.vertex_groups]
tent = np.zeros(len(P))
for v in o.data.vertices:
    tot = sum(g.weight for g in v.groups) or 1.0
    tent[v.index] = sum(g.weight for g in v.groups if 'Tent' in names[g.group]) / tot
# UVs per vertex (split where a vertex carries two UVs)
verts, uvs, remap = [], [], {}
tris = []
for f in bm.faces:
    row = []
    for lp in f.loops:
        u, v = lp[uvl].uv
        key = (lp.vert.index, round(u, 5), round(v, 5))
        if key not in remap:
            remap[key] = len(verts)
            verts.append(lp.vert.index)
            uvs.append([float(u), float(1.0 - v)])            # nif v runs down
        row.append(remap[key])
    tris.append(row)
verts = np.array(verts)


def to_game(Q):
    """her metres -> alien skin space: turn 180 about z (her front -y -> +y), scale, root to the crotch"""
    rel = (Q - root) * np.array([-1.0, -1.0, 1.0]) * K
    return crotch + np.array([0.0, 0.0, SINK]) + rel


erect = to_game(P[verts])
# rest: pull each tentacle point back along the extension axis (her -y = game +y) toward the sheath mouth
mouth_y = float(np.percentile(erect[tent[verts] < 0.2][:, 1], 95))        # front of the sac/sheath
rest = erect.copy()
tv = tent[verts]
ext = np.maximum(rest[:, 1] - mouth_y, 0.0)
rest[:, 1] -= ext * (1 - REST_K) * tv
c = np.array([0.0, mouth_y, float(erect[tv > 0.5][:, 2].mean())])
rest[:, [0, 2]] = c[[0, 2]] + (rest[:, [0, 2]] - c[[0, 2]]) * (1 - 0.15 * tv)[:, None]


def normals(V, T):
    N = np.zeros_like(V)
    for a, b_, c_ in T:
        N[[a, b_, c_]] += np.cross(V[b_] - V[a], V[c_] - V[a])
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)


G = {'AlienTenta': {'verts': rest.round(5).tolist(), 'tris': tris, 'uv': uvs,
                    'normals': normals(rest, tris).round(5).tolist(),
                    'weights': {'Pelvis': [1.0] * len(rest)},
                    'morphs': {'Erection': (erect - rest).round(5).tolist()},
                    'mat': ['Materials\\Anatomy\\Creatures\\AlienTenta.bgsm',
                            'textures\\Anatomy\\Creatures\\AlienTenta_d.dds',
                            'textures\\Anatomy\\Creatures\\AlienTenta_n.dds', '']}}
json.dump(G, open(out, 'w'))
print('AL_GEOM', len(rest), 'verts', len(tris), 'tris | erect bbox', erect.min(0).round(1), erect.max(0).round(1),
      '| rest bbox', rest.min(0).round(1), rest.max(0).round(1))
