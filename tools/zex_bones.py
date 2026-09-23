"""Stage 2: the body's genital bones and weights, written by us (decisions A-6, A-9, A-13, A-14).

Outfit Studio 5.8.2's headless automation computes a weight copy and then silently drops it:
CopyBoneWeights leaves its result in an undo state that only a GUI mesh applies, and SaveProject
then deletes every bone that has no weight (0 of 14 bones arrived, measured twice). So the bones and
weights are written here, and every step is proven against something already in the file.

  bones    Our own genital bones (physics_design.REST), which live in the copy of the women's
           skeleton tools/skeleton.py builds (A-14: the skeleton women load has no genital bone
           at all, so ZeX's names left weighted vertices behind whenever the pelvis moved). Node
           transforms come from that skeleton, composed root to bone; the convention is proven by
           recomputing the bones already in the file from ZeX's skeleton (the body is bound to
           it), and the pelvis the new bones hang from must be the same in both. Skin-to-bone
           transforms use the file's own skin offset, proven by reproducing its stored BoneData.
  weights  JaneBod's genital weights, copied by proximity (inverse distance, the K nearest within
           R units) from the reference moved into our frame (tools/references.py), half of each
           onto the bone that plays that part here (ROLE); confined by the mask (tools/mask.py):
           free vertices take the full pattern, the blend band a fraction, protected vertices
           nothing. The bones collisions push (the inner lips, the anus) carry a layer fitted to
           Nahka's own openings instead (A-9, below at "Collision-grade weights"), the outer lips a
           soft layer (A-13). The rest of the vertex's weights make room proportionally; at most 4
           influences, as the vertex format allows.

Output: build/project/ShapeData/AnatomyBodyZeX (+ .osd) and SliderSets/AnatomyBodyZeX.osp.

    python tools/skeleton.py && python tools/zex_bones.py
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

import physics_design as pd  # noqa: E402  (our bones and the openings)

# JaneBod's genital bones (in the reference) and the part each plays here. JaneBod's pattern is for
# ANIMATIONS, which swing a bone several units; physics sways ours a fraction of that, so half of it
# (ROLE_SHARE, as the _CBP_ twins had) is enough for the vulva and the outer lips to move as one piece.
# JaneBod's inner lips and anus are not carried over: the fitted layers below replace them.
JBE_GENITAL = ['Vagina_00', 'Vagina_L_01', 'Vagina_L_02', 'Vagina_R_01', 'Vagina_R_02',
               'Anus_01', 'Anus_02', 'Anus_03', 'Anus_04']
ROLE = {'Vagina_00': 'AnatVulva', 'Vagina_L_01': 'AnatLipOuter_L', 'Vagina_R_01': 'AnatLipOuter_R'}
ROLE_SHARE = 0.5
# JaneBod's painting is lopsided (measured on ours: 1,501 vertices on the left outer lip, 1,020 on the
# right, the difference all in the light tail), so each vertex takes the mean of the pattern at its
# own place and, on the other side's bone, at its mirror image: both lips sway alike.
MIRROR = {'Vagina_00': 'Vagina_00', 'Vagina_L_01': 'Vagina_R_01', 'Vagina_R_01': 'Vagina_L_01'}
OUR_SKELETON = pathlib.Path(__file__).resolve().parent.parent / 'build/skeleton/female/skeleton.nif'

# Breast physics (owner, 2026-09-23: "something wrong with physics config and breasts ... fix").
# CBBE Body Physics hangs the breasts on CLOTH_Bone_Googles_00/01, Havok-cloth nodes that are in no
# skeleton, while the deployed ocbp.ini drives LBreast_skin/RBreast_skin, which ZeX parents under
# Chest and the body never weighted: OCBP moved nothing (measured: 0 vertices on LBreast_skin,
# 1,913 on each Googles bone). CBBE's own breast weight painting moves across unchanged, so at
# rest the mesh is identical and OCBP (and the hand collisions already configured) now reach it.
BREAST_MOVE = {'CLOTH_Bone_Googles_00': 'LBreast_skin', 'CLOTH_Bone_Googles_01': 'RBreast_skin'}
K, RADIUS = 4, 1.0          # the two genital meshes coincide within 0.77 units (research.md)

# Collision-grade weights (decision A-9). JaneBod's pattern swings with animations: at most 0.17 on a
# lip after the split, 0.07 on the anus (measured). A collision moves a bone only as far as it takes
# to clear the shaft (1.4-2.2 units, tools/ocbpc_sim.py), so weights like those would open the lips
# ~0.2 units: nothing to see. So the bones collisions push carry a layer FITTED to the openings Nahka
# drew:
#   for every vertex her VaginaPenetrate / AnusPenetrate moves, scaled from the shaft she drew for
#   to the partner's (physics_design.OPENINGS), find the non-negative weights whose bone pushes
#   (physics_design.expected_push: where each sphere is driven by a shaft in that opening) best
#   reproduce her displacement. Exact least squares over every subset of the opening's bones
#   (at most 4, so 15 subsets), the best non-negative one kept.
# What the bones cannot reproduce is reported as the fit residual, not hidden. Scaled by (1 - mask)
# like everything here: protected skin never moves.
LAYER_CAP = 0.9                             # the layer never takes more than this of a vertex
# The outer lips (labia majora) jiggle and react (A-13, owner poll 2026-09-23): a soft layer on the
# outer-lip bones, left of the midline to L, right to R, from the inner lips' edge out to the groin
# crease and from the perineum to the mons, full on the crests, fading to nothing at each border.
# The inner zone (|x| < 0.4) stays the inner-lip bones' alone: the fitted layer opens it.
OUTER_TWINS = ('AnatLipOuter_L', 'AnatLipOuter_R')
OUTER_W = 0.45


def _ramp(v, a, b):
    """0 at a, 1 at b (either direction), linear between."""
    t = (v - a) / (b - a)
    return 0.0 if t <= 0 else 1.0 if t >= 1 else t


def outer_lip_weights(p):
    x, y, z = p
    ax = abs(x)
    fx = min(_ramp(ax, 0.4, 1.0), _ramp(ax, 2.8, 1.8))
    fy = min(_ramp(y, -1.3, -0.5), _ramp(y, 5.5, 4.0))
    fz = _ramp(z, -53.5, -55.0)
    w = OUTER_W * fx * fy * fz
    if w <= 0.0:
        return {}
    return {OUTER_TWINS[0] if x < 0 else OUTER_TWINS[1]: w}
MAX_GENITAL = 0.95                          # the vertex keeps at least this much of its own
MOVE_MIN = 0.02                             # morph moves below this carry no layer
SMOOTH_ROUNDS = 3


def solve(cols, target):
    """Least squares over the columns (3-vectors), ridge 1e-9: weights, residual vector."""
    n = len(cols)
    a = [[sum(cols[i][k] * cols[j][k] for k in range(3)) + (1e-9 if i == j else 0.0) for j in range(n)]
         for i in range(n)]
    b = [sum(cols[i][k] * target[k] for k in range(3)) for i in range(n)]
    for i in range(n):                                  # Gauss-Jordan, n <= 4
        piv = max(range(i, n), key=lambda r: abs(a[r][i]))
        a[i], a[piv], b[i], b[piv] = a[piv], a[i], b[piv], b[i]
        for r in range(n):
            if r != i and a[i][i]:
                f = a[r][i] / a[i][i]
                a[r] = [a[r][c] - f * a[i][c] for c in range(n)]
                b[r] -= f * b[i]
    w = [b[i] / a[i][i] if a[i][i] else 0.0 for i in range(n)]
    fit = [sum(w[i] * cols[i][k] for i in range(n)) for k in range(3)]
    return w, [target[k] - fit[k] for k in range(3)]


def side(bone):
    """-1 for a bone on her left, +1 on her right, 0 on the midline (from its sphere's x)."""
    x = pd.sphere_centre(bone)[0]
    return 0 if abs(x) < 0.05 else (1 if x > 0 else -1)


def fit_layer(move, pushes, x=0.0):
    """move: the displacement wanted; pushes: {bone: push vector}. Best non-negative weights, using
    only bones on the vertex's own side (a lip must follow its own bones: fitting the right lip to a
    left bone reproduces the drawing for a centred shaft and nothing else), both near the midline."""
    here = 0 if abs(x) < 0.05 else (1 if x > 0 else -1)
    bones = [b for b in pushes if here == 0 or side(b) in (0, here)]
    best = ({}, math.sqrt(sum(c * c for c in move)))
    for mask_bits in range(1, 1 << len(bones)):
        chosen = [bones[i] for i in range(len(bones)) if mask_bits >> i & 1]
        w, res = solve([pushes[b] for b in chosen], move)
        if min(w) <= 0.0:
            continue
        err = math.sqrt(sum(c * c for c in res))
        if err < best[1] - 1e-9:
            best = (dict(zip(chosen, w)), err)
    weights, err = best
    total = sum(weights.values())
    if total > LAYER_CAP:                              # capped: measure what is actually delivered
        weights = {b: w * LAYER_CAP / total for b, w in weights.items()}
        got = [sum(w * pushes[b][k] for b, w in weights.items()) for k in range(3)]
        err = math.sqrt(sum((move[k] - got[k]) ** 2 for k in range(3)))
    return weights, err


def smooth(layers, positions, triangles, rounds=SMOOTH_ROUNDS):
    """Neighbouring vertices fitted independently can land on different bone subsets, and the jump
    shows as a stretched triangle when the bones move. A few rounds of averaging with the
    neighbours even it out. On WELDED vertices: the copies a UV seam splits share one position,
    must keep identical weights or the seam cracks open under a push, and have different
    neighbours on each side, so they are smoothed as one."""
    wid = nif.weld(positions)
    groups = collections.defaultdict(list)
    for j, g in enumerate(wid):
        groups[g].append(j)
    nbr = collections.defaultdict(set)
    for t in triangles:
        for a in t:
            for b in t:
                if wid[a] != wid[b]:
                    nbr[wid[a]].add(wid[b])
    cur = {}
    for j, v in layers.items():
        cur.setdefault(wid[j], v[0])
    for _ in range(rounds):
        nxt = {}
        for g in set(cur) | {n for g in cur for n in nbr[g]}:
            ns = nbr[g]
            if not ns:
                continue
            acc = collections.defaultdict(float)
            for n in ns:
                for b, w in cur.get(n, {}).items():
                    acc[b] += w / len(ns)
            mine = cur.get(g, {})
            mixed = {b: 0.5 * mine.get(b, 0.0) + 0.5 * acc.get(b, 0.0) for b in set(mine) | set(acc)}
            mixed = {b: w for b, w in mixed.items() if w > 1e-4}
            if mixed:
                nxt[g] = mixed
        cur = nxt
    out = {}
    for g, w in cur.items():
        total = sum(w.values())
        if total > LAYER_CAP:
            w = {b: x * LAYER_CAP / total for b, x in w.items()}
        for j in groups[g]:
            out[j] = w
    return out


def opening_layers(osd_data, positions):
    """{vertex: ({bone: weight}, residual, wanted, opening)} for both openings, from Nahka's sliders."""
    out = {}
    for name, o in pd.OPENINGS.items():
        if not o.get('physics'):
            continue
        morph = osd_data.get(ab.TARGET + o['morph'], {})
        scale = pd.SHAFT_RADIUS / o['drawn_for'] * o.get('gain', 1.0)
        pushes = {}
        for b in o['bones']:
            u, dist = pd.expected_push(b, name)
            pushes[b] = tuple(c * dist for c in u)
        for j, v in morph.items():
            want = tuple(c * scale for c in v)
            if math.sqrt(sum(c * c for c in want)) < MOVE_MIN:
                continue
            w, err = fit_layer(want, pushes, x=positions[j][0])
            if j in out:                                  # both sliders move it: keep the bigger move
                if sum(c * c for c in want) <= sum(c * c for c in out[j][2]):
                    continue
            out[j] = (w, err, want, name)
    return out


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
    """At most 4 influences, the vertex format's limit. Cutting a vertex's own influences blows the
    genital share up on renormalising, so:
      1. the vertex's own largest influence (its anchor, usually Pelvis_skin) always stays;
      2. the remaining slots go by weight;
      3. what was dropped is spread back by renormalising."""
    chosen = []
    if mine:
        chosen.append(max(mine.items(), key=lambda bw: bw[1]))
    rest = sorted([bw for bw in mine.items() if not chosen or bw[0] != chosen[0][0]] + list(genital.items()),
                  key=lambda bw: -bw[1])
    for b, w in rest:
        if len(chosen) >= 4:
            break
        if b not in {c for c, _ in chosen}:
            chosen.append((b, w))
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
    # our bones live in the women's skeleton (tools/skeleton.py); they hang from its pelvis, which must
    # be the pelvis this body is bound to
    if not OUR_SKELETON.exists():
        raise SystemExit(f'{OUR_SKELETON} is missing: run tools/skeleton.py first')
    ours = skeleton_world(OUR_SKELETON)
    pr_ours, pt_ours, _ = ours[pd.PARENT]
    pr_zex, pt_zex, _ = world[pd.PARENT]
    parent_gap = max(max(abs(a - b) for a, b in zip(pt_ours, pt_zex)),
                     max(abs(a - b) for a, b in zip(flat(pr_ours), flat(pr_zex))))
    absent = [b for b in pd.REST if b not in ours]
    print(f'   women\'s skeleton (ours): {pd.PARENT} differs from the bound one by {parent_gap:.2e}; '
          f'our bones present {len(pd.REST) - len(absent)}/{len(pd.REST)}')
    if parent_gap > 1e-4 or absent:
        raise SystemExit(f'our skeleton cannot carry this body: {pd.PARENT} moved {parent_gap}, bones absent {absent}')

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
    if max(abs(off[i] - pd.SKIN_OFFSET[i]) for i in range(3)) > 0.005:
        raise SystemExit(f'the skin offset {off} is not physics_design.SKIN_OFFSET {pd.SKIN_OFFSET}: '
                         f'our bones would sit elsewhere than designed')

    # ---- 3. weights: JaneBod's pattern, by proximity, inside the mask
    ref = nif.Nif(REFERENCE)
    rs = ref.shapes()[0]
    rbones, _ = ref.skin(rs)
    rpos = rs.positions()
    rgen = {}
    for v in range(rs.count):
        g = {rbones[s]: w for s, w in rs.skin_weights(v) if rbones[s] in JBE_GENITAL}
        if g:
            rgen[v] = g
    grid = ab.Grid(rpos, list(range(rs.count)))

    def jbe_at(p):
        """JaneBod's genital weights at a point: inverse distance over the K nearest within RADIUS."""
        g = collections.defaultdict(float)
        near = grid.nearest(p, K, limit=RADIUS)
        for v, w in (ab.idw(p, rpos, near) if near else []):
            for b, x in rgen.get(v, {}).items():
                g[b] += w * x
        return g
    mask = {int(v.get('i')): float(v.get('m')) for v in ET.parse(MASK).getroot().iter('V')}
    import osd as osd_mod
    pos_all = shape.positions()
    layers = opening_layers(osd_mod.read(ab.OUT / 'ShapeData' / ab.DATA_FOLDER / f'{ab.DATA_FOLDER}.osd'), pos_all)
    smoothed = smooth(layers, pos_all, shape.triangles())
    for name in [n for n, o in pd.OPENINGS.items() if o.get('physics')]:
        mine = {j: v for j, v in layers.items() if v[3] == name and mask.get(j, 0.0) < 1.0}
        wanted = sum(math.sqrt(sum(c * c for c in v[2])) for v in mine.values())
        missed = sum(v[1] for v in mine.values())
        print(f'   {name}: {len(mine)} vertices fitted to {pd.OPENINGS[name]["morph"]}; '
              f'displacement reproduced {100 * (1 - missed / wanted) if wanted else 0:.0f}% '
              f'(sum of residuals / sum of wanted moves)')
    pos = shape.positions()
    new_weights = {}
    for j in range(shape.count):
        m = mask.get(j, 0.0)
        if m >= 1.0:
            continue
        here, there = jbe_at(pos[j]), jbe_at((-pos[j][0], pos[j][1], pos[j][2]))
        s = 1.0 - m
        genital = {}
        for b in ROLE:
            x = 0.5 * (here.get(b, 0.0) + there.get(MIRROR[b], 0.0))
            if x > 0.0:
                genital[ROLE[b]] = s * x * ROLE_SHARE
        layer = dict(smoothed.get(j, {}))
        for b, x in outer_lip_weights(pos[j]).items():
            layer[b] = layer.get(b, 0.0) + x
        room = MAX_GENITAL - sum(genital.values())
        want = s * sum(layer.values())
        scale = s * (min(1.0, room / want) if want > room else 1.0) if want > 0 else 0.0
        for b, x in layer.items():
            genital[b] = genital.get(b, 0.0) + x * scale
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
    new_names = list(pd.REST) + list(BREAST_MOVE.values())
    defs = []
    for name in new_names:
        wr, wt, ws = ours[name] if name in pd.REST else world[name]
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
