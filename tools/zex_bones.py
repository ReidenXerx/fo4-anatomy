"""Stage 2 (decision A-6): ZeX's genital bones and JaneBod Extended's weight pattern, written by us.

Outfit Studio 5.8.2's headless automation computes a weight copy and then silently drops it:
CopyBoneWeights leaves its result in an undo state that only a GUI mesh applies, and SaveProject
then deletes every bone that has no weight (0 of 14 bones arrived, measured twice). So the bones and
weights are written here, and every step is proven against something already in the file.

  bones    Nine animated ZeX genital bones (Vagina_00, Vagina_L/R_01-02, Anus_01-04) plus the five
           vagina _CBP_ twins OCBP physics moves. Node transforms come from the installed ZeX
           skeleton, composed root to bone. The convention is proven by recomputing the 63 bones
           already in the file. Skin-to-bone transforms use the file's own skin offset, proven by
           reproducing the file's stored BoneData.
  weights  JaneBod's genital weights, copied by proximity (inverse distance, the K nearest within
           R units) from the reference moved into our frame (tools/references.py). They are
           confined by the mask (tools/mask.py): free vertices take the full pattern, the blend
           band a fraction, protected vertices nothing. A vagina weight is split between the
           animated bone and its twin (TWIN_SHARE); the rest of the vertex's weights make room
           proportionally; at most 4 influences, as the vertex format allows.

Output: build/project/ShapeData/AnatomyBodyZeX (+ .osd) and SliderSets/AnatomyBodyZeX.osp.

    python tools/zex_bones.py
"""
import collections
import json
import math
import pathlib
import shutil
import sys
import xml.etree.ElementTree as ET

import align_body as ab
import nif

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKELETON = ab.DEFAULT_DATA / 'Meshes/Actors/Character/CharacterAssets/skeleton.nif'
REFERENCE = ROOT / 'build/references/AnatomyRefJBE.nif'
MASK = ab.OUT / 'Masks/AnatomyGenitalRegion.xml'
STAGE1 = ab.OUT / 'ShapeData' / ab.DATA_FOLDER / f'{ab.DATA_FOLDER}.nif'
OUT_FOLDER = 'AnatomyBodyZeX'
SET_NAME = 'Anatomy Body ZeX'

ANIM = ['Vagina_00', 'Vagina_L_01', 'Vagina_L_02', 'Vagina_R_01', 'Vagina_R_02',
        'Anus_01', 'Anus_02', 'Anus_03', 'Anus_04']
TWIN = {'Vagina_00': 'Vagina_CBP_00', 'Vagina_L_01': 'Vagina_CBP_L_01', 'Vagina_L_02': 'Vagina_CBP_L_02',
        'Vagina_R_01': 'Vagina_CBP_R_01', 'Vagina_R_02': 'Vagina_CBP_R_02'}
TWIN_SHARE = 0.5            # of each vagina weight, to the physics twin (tuned in game)

# Breast physics (owner, 2026-09-23: "something wrong with physics config and breasts ... fix").
# CBBE Body Physics hangs the breasts on CLOTH_Bone_Googles_00/01, Havok-cloth nodes that are in no
# skeleton, while the deployed ocbp.ini drives LBreast_skin/RBreast_skin, which ZeX parents under
# Chest and the body never weighted: OCBP moved nothing (measured: 0 vertices on LBreast_skin,
# 1,913 on each Googles bone). CBBE's own breast weight painting moves across unchanged, so at
# rest the mesh is identical and OCBP (and the hand collisions already configured) now reach it.
BREAST_MOVE = {'CLOTH_Bone_Googles_00': 'LBreast_skin', 'CLOTH_Bone_Googles_01': 'RBreast_skin'}
K, RADIUS = 4, 1.0          # the two genital meshes coincide within 0.77 units (research.md)


# --------------------------------------------------------------------------
# transforms (NIF stores 3x3 rotations row by row; v' = s * (M v) + t)
# --------------------------------------------------------------------------

def rows(r9):
    return [list(r9[0:3]), list(r9[3:6]), list(r9[6:9])]


def mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def apply(m, v):
    return [sum(m[i][k] * v[k] for k in range(3)) for i in range(3)]


def transpose(m):
    return [[m[j][i] for j in range(3)] for i in range(3)]


def flat(m):
    return tuple(x for row in m for x in row)


def compose(parent, child):
    """world of a child = parent (x) local."""
    pr, pt, ps = parent
    cr, ct, cs = child
    return mul(pr, cr), [pt[i] + ps * apply(pr, ct)[i] for i in range(3)], ps * cs


def pick_four(mine, genital):
    """At most 4 influences, the vertex format's limit. A plain top-4 cut starved the physics twins
    (ties went to the animated bone: Vagina_CBP_L_01 kept 190 vertices against Vagina_L_01's 908),
    and cutting a vertex's own influences blows the genital share up on renormalising. So:
      1. the vertex's own largest influence (its anchor, usually Pelvis_skin) always stays;
      2. the remaining slots go by weight, and an animated bone brings its twin along whenever a
         slot is free, so a genital pair is split only when a single slot is left;
      3. what was dropped is spread back by renormalising."""
    chosen = []
    if mine:
        anchor = max(mine.items(), key=lambda bw: bw[1])
        chosen.append(anchor)
    partner = {**TWIN, **{v: k for k, v in TWIN.items()}}
    rest = sorted([bw for bw in mine.items() if not chosen or bw[0] != chosen[0][0]] + list(genital.items()),
                  key=lambda bw: -bw[1])
    taken = {b for b, _ in chosen}
    for b, w in rest:
        if len(chosen) >= 4:
            break
        if b in taken:
            continue
        p = partner.get(b)
        if p and p in genital and p not in taken and len(chosen) == 3:
            # one slot for a pair: the owner asked for physics first (A-1), so the twin gets it
            # (measured before this rule: 718 of 908 L_01 vertices kept the animated half alone)
            twin = b if b in TWIN.values() else p
            chosen.append((twin, genital[twin]))
            taken.update((b, p))
            continue
        chosen.append((b, w))
        taken.add(b)
        if p and p in genital and p not in taken and len(chosen) < 4:
            chosen.append((p, genital[p]))
            taken.add(p)
    norm = sum(w for _, w in chosen)
    return [(b, w / norm) for b, w in chosen]


def skeleton_world(path):
    sk = nif.Nif(path)
    parent = {}
    for i, n in sk.nodes.items():
        for kid in n['kids']:
            parent[kid] = i
    local = {i: (rows(n['r']), list(n['t']), n['s']) for i, n in sk.nodes.items()}
    world = {}

    def w(i):
        if i not in world:
            world[i] = compose(w(parent[i]), local[i]) if i in parent else local[i]
        return world[i]
    return {sk.nodes[i]['name']: w(i) for i in sk.nodes if sk.nodes[i]['name']}


def main():
    body = nif.Nif(STAGE1)
    shape = body.shape(ab.SHAPE)
    bones, skin_xf = body.skin(shape)
    ref_by_slot = []
    o, _ = body.offsets[shape.skin]
    c = nif.Cursor(body.b, o)
    c.take('i'), c.take('i')
    ref_by_slot = [c.take('i') for _ in range(c.take('I'))]

    # ---- 1. the skeleton's world transforms reproduce the file's bone nodes
    world = skeleton_world(SKELETON)
    worst_t = worst_r = 0.0
    checked = 0
    for slot, name in enumerate(bones):
        if name not in world:
            continue
        node = body.nodes[ref_by_slot[slot]]
        wr, wt, _ = world[name]
        worst_t = max(worst_t, max(abs(a - b) for a, b in zip(wt, node['t'])))
        worst_r = max(worst_r, max(abs(a - b) for a, b in zip(flat(wr), node['r'])))
        checked += 1
    print(f'1. ZeX skeleton world transforms vs the file\'s {checked} bone nodes: worst translation {worst_t:.4f}, '
          f'rotation {worst_r:.5f}')
    if worst_t > 0.01 or worst_r > 1e-3:
        raise SystemExit('the skeleton does not reproduce the file\'s bone nodes: convention wrong')

    # ---- 2. the skin offset: skin-to-bone = inverse(node) after moving skin space by -offset
    # Only bones the skeleton knows: the cloth bones (CLOTH_Bone_*) are not in ZeX, and their nodes
    # in the file carry transforms of their own (measured: including them spreads the offset by 5).
    in_skel = [slot for slot, name in enumerate(bones) if name in world]
    offs = []
    for slot in in_skel:
        node = body.nodes[ref_by_slot[slot]]
        origin_skin = nif.bone_origin(skin_xf[slot])
        offs.append([origin_skin[i] - node['t'][i] for i in range(3)])
    off = [sum(x[i] for x in offs) / len(offs) for i in range(3)]
    spread = max(max(abs(x[i] - off[i]) for i in range(3)) for x in offs)

    def skin_to_bone(node_rot, node_t):
        # v_skin = v_world + off and v_world = R v_bone + t  =>  v_bone = R^T (v_skin - off - t)
        rt = transpose(node_rot)
        return rt, [-v for v in apply(rt, [off[i] + node_t[i] for i in range(3)])]

    # CBBE was bound to a pose that differs from ZeX's rest pose at the extremities (measured: toes
    # off by up to 2.85). The genital bones hang off Pelvis, so what must reproduce exactly is the
    # pelvis and the bones around it; elsewhere the differences are reported, not fatal.
    errors = {}
    for slot in in_skel:
        node = body.nodes[ref_by_slot[slot]]
        r, t = skin_to_bone(rows(node['r']), node['t'])
        sr, st, _ = skin_xf[slot]
        errors[bones[slot]] = max(max(abs(a - b) for a, b in zip(flat(r), sr)),
                                  max(abs(a - b) for a, b in zip(t, st)))
    core = [b for b in ('Pelvis', 'Pelvis_skin', 'Pelvis_Rear_skin', 'SPINE1', 'Spine1_skin', 'LLeg_Thigh',
                        'RLeg_Thigh', 'LLeg_Thigh_skin', 'RLeg_Thigh_skin', 'LButtFat_skin', 'RButtFat_skin') if b in errors]
    off_bones = sorted(((e, b) for b, e in errors.items() if e > 0.01), reverse=True)
    print(f'2. skin offset {tuple(round(x, 3) for x in off)} over {len(in_skel)} skeleton bones (spread {spread:.4f}); '
          f'pelvis-area bones reproduced to {max(errors[b] for b in core):.5f} ({len(core)} checked); '
          f'bones bound to a different pose: {[(b, round(e, 2)) for e, b in off_bones]}')
    if spread > 0.01 or max(errors[b] for b in core) > 0.01:
        raise SystemExit('cannot reproduce the pelvis-area skin transforms: offset or convention wrong')

    # ---- 3. weights: JaneBod's pattern, by proximity, inside the mask
    ref = nif.Nif(REFERENCE)
    rs = ref.shapes()[0]
    rbones, _ = ref.skin(rs)
    rpos = rs.positions()
    rgen = {}
    for v in range(rs.count):
        g = {rbones[s]: w for s, w in rs.skin_weights(v) if rbones[s] in ANIM}
        if g:
            rgen[v] = g
    grid = ab.Grid(rpos, list(range(rs.count)))
    mask = {int(v.get('i')): float(v.get('m')) for v in ET.parse(MASK).getroot().iter('V')}
    pos = shape.positions()
    new_weights = {}
    for j in range(shape.count):
        m = mask.get(j, 0.0)
        if m >= 1.0:
            continue
        near = grid.nearest(pos[j], K, limit=RADIUS)
        if not near:
            continue
        idw = ab.idw(pos[j], rpos, near)
        g = collections.defaultdict(float)
        for v, w in idw:
            for b, x in rgen.get(v, {}).items():
                g[b] += w * x
        if not g:
            continue
        s = 1.0 - m
        genital = {}
        for b, x in g.items():
            if b in TWIN:
                genital[b] = s * x * (1 - TWIN_SHARE)
                genital[TWIN[b]] = s * x * TWIN_SHARE
            else:
                genital[b] = s * x
        total = sum(genital.values())
        if total < 1e-4:
            continue
        mine = {bones[sl]: w * (1.0 - total) for sl, w in shape.skin_weights(j)}
        new_weights[j] = pick_four(mine, genital)
    touched_protected = [j for j in new_weights if mask.get(j, 0.0) >= 1.0]
    print(f'3. JaneBod genital-weighted reference vertices {len(rgen)}; our vertices given genital weight '
          f'{len(new_weights)} (protected among them: {len(touched_protected)})')

    # breasts: the same weights, on the bones OCBP drives. Only the bone slot changes (index bytes),
    # never the weight bytes, so every moved weight stays bit-identical.
    breast = {}                                   # vertex -> [(new bone, weight)] for the spheres
    moved = collections.Counter()
    for j in range(shape.count):
        ws = [(bones[sl], w) for sl, w in shape.skin_weights(j)]
        if any(b in BREAST_MOVE for b, _ in ws):
            if j in new_weights:
                raise SystemExit(f'vertex {j} carries both genital and breast weight: regions overlap')
            breast[j] = [(BREAST_MOVE.get(b, b), w) for b, w in ws]
            moved.update(BREAST_MOVE[b] for b, _ in ws if b in BREAST_MOVE)
    print(f'   breast weights moved off the Havok cloth bones: {dict(moved)}')

    # ---- 4. the bones, with bone-space bounding spheres of what they now carry
    new_names = ANIM + [TWIN[b] for b in ANIM if b in TWIN] + list(BREAST_MOVE.values())
    defs = []
    for name in new_names:
        wr, wt, ws = world[name]
        sr, st = skin_to_bone(wr, wt)
        carried = [apply(sr, pos[j]) for j, ws_ in list(new_weights.items()) + list(breast.items())
                   for b, w in ws_ if b == name and w > 0]
        carried = [[p[i] + st[i] for i in range(3)] for p in carried]
        if carried:
            ctr = [sum(p[i] for p in carried) / len(carried) for i in range(3)]
            rad = max(math.dist(ctr, p) for p in carried)
        else:
            ctr, rad = [0.0, 0.0, 0.0], 0.0
        defs.append(dict(name=name, node_rot=flat(wr), node_t=tuple(wt), sphere=(*ctr, rad),
                         skin_rot=flat(sr), skin_t=tuple(st), scale=1.0))
        print(f'   {name:16} at ({wt[0]:6.2f},{wt[1]:6.2f},{wt[2]:7.2f}) in skeleton space; carries {len(carried):4} '
              f'vertices; sphere r {rad:.2f}')

    # ---- 5. write: bones first (structure), then the weights in place
    out_dir = ab.OUT / 'ShapeData' / OUT_FOLDER
    out_dir.mkdir(parents=True, exist_ok=True)
    out_nif = out_dir / f'{OUT_FOLDER}.nif'
    out_nif.write_bytes(body.with_bones(shape, defs))
    done = nif.Nif(out_nif)
    ds = done.shape(ab.SHAPE)
    dbones, _ = done.skin(ds)
    slot = {b: i for i, b in enumerate(dbones)}
    for j, ws_ in new_weights.items():
        ds.set_skin_weights(j, [(slot[b], w) for b, w in ws_])
    remap = {slot[old]: slot[new] for old, new in BREAST_MOVE.items()}
    for j in breast:
        ds.remap_skin_slots(j, remap)
    done.save(out_nif)
    shutil.copy2(ab.OUT / 'ShapeData' / ab.DATA_FOLDER / f'{ab.DATA_FOLDER}.osd', out_dir / f'{OUT_FOLDER}.osd')
    osp = (ab.OUT / 'SliderSets' / f'{ab.DATA_FOLDER}.osp').read_text(encoding='utf-8')
    osp = (osp.replace(f'name="{ab.SET_NAME}"', f'name="{SET_NAME}"')
              .replace(f'<DataFolder>{ab.DATA_FOLDER}</DataFolder>', f'<DataFolder>{OUT_FOLDER}</DataFolder>')
              .replace(f'<SourceFile>{ab.DATA_FOLDER}.nif</SourceFile>', f'<SourceFile>{OUT_FOLDER}.nif</SourceFile>')
              .replace(f'{ab.DATA_FOLDER}.osd\\', f'{OUT_FOLDER}.osd\\'))
    (ab.OUT / 'SliderSets' / f'{OUT_FOLDER}.osp').write_text(osp, encoding='utf-8')
    print(f'4. wrote {out_nif} ({len(done.offsets)} blocks, {len(dbones)} bones), .osd, SliderSets/{OUT_FOLDER}.osp')


if __name__ == '__main__':
    main()
