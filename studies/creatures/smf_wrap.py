"""Female super mutant v4 (ilhamitaa24 11-12: "use my model as a base and re texture it ... like the game model"):
the game mutant body, subdivided once, WRAPPED onto her sculpt - so the result is her surface, on the game skeleton,
with the game's UVs (the real mutant skin texture) and skin weights.
Each vertex goes into her space through the bone frame of every segment it is skinned to (game joint pair -> her
joint pair: origin, axis, forward/left basis, uniform scale = segment-length ratio; that also undoes her T-pose
arms), snaps onto her surface (rays both ways along the mapped normal; a hit must FACE the same way, so the inside
of a hanging loincloth flap or a gap is never taken), and comes back the same way; the segments blend by the skin
weights. Kept as the game's: head + neck, forearms + hands (her bracers), calves + feet (her boots); her shoulder
pads are masked. The displacement is then smoothed over the mesh (straps are thin; the transitions soften).
Front = +y game / -y hers, left = -x game / +x hers.
    blender -b --factory-startup --disable-autoexec -P smf_wrap.py -- <her glb> <out mesh json> [subdiv levels]"""
import json
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:]
GLB, OUT = args[0], args[1]
LEVELS = int(args[2]) if len(args) > 2 else 1
VAN = r'D:\F4Output\creatures\sm\vanilla\supermutantbody.nif'

# ---------------------------------------------------------------- the game body (+ subdivision, UVs, weights kept)
n = nif.Nif(VAN)
sh = n.shape('SupermutantBodyNew:0')
names, xf = n.skin(sh)
GB = {nm: -np.linalg.solve(np.array(r).reshape(3, 3), np.array(t)) / sc for nm, (r, t, sc) in zip(names, xf)}
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('game')
me.from_pydata([tuple(p) for p in sh.positions()], [], [tuple(t) for t in sh.triangles()])
me.update()
uvl = me.uv_layers.new(name='UVMap')
for poly in me.polygons:
    for li in poly.loop_indices:
        u, v = sh.uv(me.loops[li].vertex_index)
        uvl.data[li].uv = (u, 1.0 - v)
go = bpy.data.objects.new('game', me)
bpy.context.scene.collection.objects.link(go)
for nm in names:
    go.vertex_groups.new(name=nm)
for i in range(sh.count):
    for slot, w in sh.skin_weights(i):
        go.vertex_groups[slot].add([i], w, 'ADD')
if LEVELS:
    md = go.modifiers.new('sub', 'SUBSURF')
    md.subdivision_type = 'SIMPLE'
    md.levels = LEVELS
    bpy.context.view_layer.objects.active = go
    bpy.ops.object.modifier_apply(modifier='sub')
me = go.data
NV = len(me.vertices)
V = np.array([v.co[:] for v in me.vertices])
N = np.array([v.normal[:] for v in me.vertices])
W = np.zeros((NV, len(names)))
for v in me.vertices:
    for g in v.groups:
        W[v.index, g.group] = g.weight
W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
print('game body', sh.count, '->', NV, 'vertices after', LEVELS, 'subdivision(s)')

# ---------------------------------------------------------------- her sculpt (BVH) + rig
bpy.ops.import_scene.gltf(filepath=GLB)
her = bpy.data.objects['model']
dg = bpy.context.evaluated_depsgraph_get()
bvh = BVHTree.FromObject(her, dg)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE' and o.name != 'game')
HB = {b.name: np.array(arm.matrix_world @ b.head) for b in arm.pose.bones}
print('her BVH ready')

SEGS = [  # name, game joints, her joints, game bones (skin slots) of this segment
    ('torso', ('Pelvis', 'Neck_skin'), ('Hips', 'Neck'),
     ('Pelvis', 'Pelvis_skin', 'SPINE1', 'Spine1_skin', 'SPINE2', 'Spine2_skin', 'Chest', 'Chest_skin', 'Belly_skin',
      'UpperBelly_skin', 'L_RibHelper', 'R_RibHelper', 'LBreast_skin', 'RBreast_skin', 'LButtFat_skin',
      'RButtFat_skin', 'LArm_Collarbone', 'LArm_Collarbone_skin', 'RArm_Collarbone', 'RArm_Collarbone_skin')),
    ('upperarmL', ('LArm_UpperArm', 'LArm_ForeArm1_skin'), ('LeftArm', 'LeftForeArm'),
     ('LArm_UpperArm', 'LArm_UpperArm_skin', 'LArm_UpperTwist1_skin', 'LArm_UpperTwist2_skin', 'LArm_UpperFat_skin')),
    ('upperarmR', ('RArm_UpperArm', 'RArm_ForeArm1_skin'), ('RightArm', 'RightForeArm'),
     ('RArm_UpperArm', 'RArm_UpperArm_skin', 'RArm_UpperTwist1_skin', 'RArm_UpperTwist2_skin', 'RArm_UpperFat_skin')),
    ('thighL', ('LLeg_Thigh', 'LLeg_Calf_skin'), ('LeftUpLeg', 'LeftLeg'), ('LLeg_Thigh', 'LLeg_Thigh_skin')),
    ('thighR', ('RLeg_Thigh', 'RLeg_Calf_skin'), ('RightUpLeg', 'RightLeg'), ('RLeg_Thigh', 'RLeg_Thigh_skin')),
]


def basis(a0, a1, fwd):
    ax = a1 - a0
    L = np.linalg.norm(ax)
    ax = ax / L
    f = fwd - (fwd @ ax) * ax
    f /= np.linalg.norm(f)
    return np.stack([f, np.cross(ax, f), ax]), L          # rows: forward, left-ish, axis


def masked(t, seg):
    """what a segment's wrap must not take (her space): the shoulder pads; for the torso, her T-posed arms (the
    game's armpit/shoulder skin snapped onto them = 'wings' in w3)"""
    if t[2] > 1.49 and abs(t[0]) > 0.12:
        return True
    return seg == 'torso' and t[2] > 1.30 and abs(t[0] - HB['Hips'][0]) > 0.245


RANGE = 0.12                       # her units searched along the normal (her torso is ~1.3x the game's at s_rad)
_rg, _lg = basis(GB['Pelvis'], GB['Neck_skin'], np.array([0.0, 1.0, 0.0]))
_rh, _lh = basis(HB['Hips'], HB['Neck'], np.array([0.0, -1.0, 0.0]))
S_RAD = _lg / _lh                  # the torso's length ratio sets her girth everywhere
targets = np.zeros_like(V)
wsum = np.zeros(NV)
segw = np.zeros(NV)                # weight of the wrapped segments, hit or not
stats = {}
SKIP = {'upperarmL', 'upperarmR'}    # her arms: T-posed under shoulder pads/bracers - partial, erratic hits
for name, (g0, g1), (h0, h1), bones in SEGS:
    if name in SKIP:
        continue
    Rg, Lg = basis(GB[g0], GB[g1], np.array([0.0, 1.0, 0.0]))
    Rh, Lh = basis(HB[h0], HB[h1], np.array([0.0, -1.0, 0.0]))
    s_ax = Lg / Lh                                          # along the segment: the game's joint spacing
    s_rad = S_RAD                                           # across: one factor for her whole body (proportions)
    SC = np.array([s_rad, s_rad, s_ax])
    slots = [names.index(b) for b in bones if b in names]
    w = W[:, slots].sum(1)
    segw += w
    hit = miss = 0
    for i in np.where(w > 0.01)[0]:
        c = Rg @ (V[i] - GB[g0]) / SC                      # game -> local -> her
        q = HB[h0] + Rh.T @ c
        nq = Rh.T @ (Rg @ N[i])
        best = None
        for d in (nq, -nq):
            o, left = q - d * 0.002, RANGE
            for _ in range(6):                     # past rejected surfaces (a fold, gear facing the other way)
                r = bvh.ray_cast(Vector(o), Vector(d), left)
                if r[0] is None:
                    break
                hp = np.array(r[0])
                ok_ = np.dot(np.array(r[1]), nq) > 0.3 and not masked(hp, name)
                if ok_:
                    dist = np.linalg.norm(hp - q)
                    if best is None or dist < best[0]:
                        best = (dist, hp)
                    break
                step = np.linalg.norm(hp - o) + 1e-4
                o, left = hp + d * 1e-4, left - step
                if left <= 0:
                    break
        if best is None:
            miss += 1
            continue
        hit += 1
        p = GB[g0] + Rg.T @ ((Rh @ (best[1] - HB[h0])) * SC)   # her -> local -> game
        targets[i] += w[i] * p
        wsum[i] += w[i]
    stats[name] = (round(float(s_ax), 1), hit, miss)
    if name == 'torso':
        ch = (V[:, 2] > -40) & (V[:, 2] < -18) & (V[:, 1] > 6) & (w > 0.01)
        print('chest verts', int(ch.sum()), 'hit', int((ch & (wsum > 0)).sum()))
print('segments (scale, hits, misses)', stats)

# blend: the share of a vertex's weight that found her surface moves there; the rest (head, forearms, calves,
# masked/missed points) stays the game's. Then smooth the displacement over the mesh.
disp = np.zeros_like(V)
has = wsum > 1e-6
disp[has] = targets[has] / wsum[has, None] - V[has]           # where her surface was found (hit share)
edges = np.array([e.vertices[:] for e in me.edges])
# misses (rays that found no facing surface) are FILLED from their neighbours (hits held fixed, kept parts held at
# 0): leaving them at 0 and smoothing flattened the breasts in w2
known = has | (segw < 1e-6)
for _ in range(200):
    acc = np.zeros_like(disp)
    cnt = np.zeros(NV)
    np.add.at(acc, edges[:, 0], disp[edges[:, 1]])
    np.add.at(acc, edges[:, 1], disp[edges[:, 0]])
    np.add.at(cnt, edges[:, 0], 1)
    np.add.at(cnt, edges[:, 1], 1)
    upd = acc / np.maximum(cnt, 1)[:, None]
    disp[~known] = upd[~known]
disp *= np.minimum(segw, 1.0)[:, None]                         # fade into the kept parts (head, forearms, calves)
for _ in range(int(args[3]) if len(args) > 3 else 2):
    acc = np.zeros_like(disp)
    cnt = np.zeros(NV)
    np.add.at(acc, edges[:, 0], disp[edges[:, 1]])
    np.add.at(acc, edges[:, 1], disp[edges[:, 0]])
    np.add.at(cnt, edges[:, 0], 1)
    np.add.at(cnt, edges[:, 1], 1)
    disp = 0.5 * disp + 0.5 * acc / np.maximum(cnt, 1)[:, None]
P = V + disp
print('moved', int((np.linalg.norm(disp, axis=1) > 0.05).sum()), 'of', NV, '| max', np.linalg.norm(disp, axis=1).max().round(2))
tris = [list(p.vertices) for p in me.polygons]
json.dump({'positions': P.round(4).tolist(), 'tris': [t if len(t) == 3 else [t[0], t[1], t[2]] for t in tris]
           + [[t[0], t[2], t[3]] for t in tris if len(t) == 4],
           'vanilla': V.round(4).tolist()}, open(OUT, 'w'))
print('WRAP DONE ->', OUT)
