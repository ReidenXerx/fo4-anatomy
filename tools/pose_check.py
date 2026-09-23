"""Bend the skeleton, skin the body the way the engine does, and find what tears (no game needed).

The owner's own look (2026-09-23, Photo118-130) showed a long thin rod of the genital mesh in
doggy and standing poses, far longer than any physics bone can move (OCBPC's cap). Something in
the weights follows a LIMB. This poses the ZeX skeleton (a local rotation on the named bones; their
children follow), skins every vertex by linear blend skinning with the body's own bind data, and
reports the genital-region vertices that move away from their neighbours: the worst edge growth,
and for each offender the bones that carry it.

    python tools/pose_check.py [--body <FemaleBody.nif>]
"""
import argparse
import math
import pathlib

import align_body as ab
import nif
import zex_bones as zb

DEFAULT_BODY = ab.DEFAULT_DATA / 'Meshes/Actors/Character/CharacterAssets/FemaleBody.nif'
OFF = (0.0, 0.882, -120.844)                     # skin = skeleton world + OFF (zex_bones step 2)
REGION = (4.0, -7.0, 7.0, -60.0, -48.0)          # |x| <=, y in, z in: the crotch


def rot(axis, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    x, y, z = axis
    return [[c + x * x * (1 - c), x * y * (1 - c) - z * s, x * z * (1 - c) + y * s],
            [y * x * (1 - c) + z * s, c + y * y * (1 - c), y * z * (1 - c) - x * s],
            [z * x * (1 - c) - y * s, z * y * (1 - c) + x * s, c + z * z * (1 - c)]]


def posed_world(pose):
    """Skeleton world transforms with extra local rotations {bone: (axis, degrees[, move])} applied
    (move: added to the local translation), on the skeleton WOMEN load (ours, tools/skeleton.py;
    A-14). Posing ZeX's instead hid the missing-bone stretch: ZeX has the bones hers lacked."""
    import skeleton
    sk = nif.Nif(skeleton.OUT)
    parent = {}
    for i, n in sk.nodes.items():
        for kid in n['kids']:
            parent[kid] = i
    local = {}
    for i, n in sk.nodes.items():
        r, t = zb.rows(n['r']), list(n['t'])
        if n['name'] in pose:
            axis, deg, *move = pose[n['name']]
            r = zb.mul(r, rot(axis, deg))
            if move:
                t = [t[k] + move[0][k] for k in range(3)]
        local[i] = (r, t, n['s'])
    world = {}

    def w(i):
        if i not in world:
            world[i] = zb.compose(w(parent[i]), local[i]) if i in parent else local[i]
        return world[i]
    return {sk.nodes[i]['name']: w(i) for i in sk.nodes if sk.nodes[i]['name']}


MISSING = set()


def skin_all(shape, bones, skin_xf, world):
    """Linear blend skinning: v' = sum w * World_b * (skin-to-bone_b * v). A bone the skeleton lacks
    keeps the body file's own node, at its bind place under the actor's root: its share of the
    vertex stays where the vertex rests, whatever the pelvis does (the A-14 stretch). Named in MISSING."""
    pos = shape.positions()
    out = []
    for j in range(shape.count):
        acc = [0.0, 0.0, 0.0]
        for sl, w in shape.skin_weights(j):
            name = bones[sl]
            if name not in world:
                if w > 0 and not name.startswith('CLOTH_'):   # Havok cloth makes its own bones
                    MISSING.add(name)
                    for i in range(3):
                        acc[i] += w * pos[j][i]
                continue
            r, t, s = skin_xf[sl]
            rr = zb.rows(r)
            vb = [sum(rr[i][k] * pos[j][k] for k in range(3)) * s + t[i] for i in range(3)]
            wr, wt, ws = world[name]
            vw = [ws * sum(wr[i][k] * vb[k] for k in range(3)) + wt[i] for i in range(3)]
            for i in range(3):
                acc[i] += w * (vw[i] + OFF[i])
        out.append(acc)
    return out


POSES = {
    'rest (sanity)': {},
    'thighs flexed 90 (doggy)': {'LLeg_Thigh': ((1, 0, 0), 90), 'RLeg_Thigh': ((1, 0, 0), 90)},
    'thighs flexed -90': {'LLeg_Thigh': ((1, 0, 0), -90), 'RLeg_Thigh': ((1, 0, 0), -90)},
    'thighs spread 45': {'LLeg_Thigh': ((0, 1, 0), 45), 'RLeg_Thigh': ((0, 1, 0), -45)},
    'thighs spread -45': {'LLeg_Thigh': ((0, 1, 0), -45), 'RLeg_Thigh': ((0, 1, 0), 45)},
    'thighs twist 45': {'LLeg_Thigh': ((0, 0, 1), 45), 'RLeg_Thigh': ((0, 0, 1), -45)},
    'spine bent 60': {'SPINE1': ((1, 0, 0), 60)},
    'spine bent -60': {'SPINE1': ((1, 0, 0), -60)},
    # the body moving against the actor's root, as every sex scene does: this is what strands a
    # share weighted to a bone the skeleton lacks (the fin, A-14)
    'kneeling (COM down 15)': {'COM': ((1, 0, 0), 0, (0, 0, -15))},
    'lying back (COM pitched 90, down 30)': {'COM': ((1, 0, 0), 90, (0, 0, -30))},
}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--body', type=pathlib.Path, default=DEFAULT_BODY)
    args = ap.parse_args()
    body = nif.Nif(args.body)
    shape = body.shape(ab.SHAPE)
    bones, skin_xf = body.skin(shape)
    rest = shape.positions()
    tris = shape.triangles()
    region = {j for j, p in enumerate(rest) if abs(p[0]) <= REGION[0] and REGION[1] <= p[1] <= REGION[2]
              and REGION[3] <= p[2] <= REGION[4]}
    edges = set()
    for t in tris:
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            if a in region or b in region:
                edges.add((min(a, b), max(a, b)))
    base = skin_all(shape, bones, skin_xf, posed_world({}))
    drift = max(math.dist(base[j], rest[j]) for j in region)
    print(f'{args.body.name}: {len(region)} crotch vertices, {len(edges)} edges; rest-pose skinning drift {drift:.4f} '
          f'(must be ~0: the bind data and skeleton agree)')
    print(f'weighted bones the women\'s skeleton lacks (their share stays behind when she moves): '
          f'{sorted(MISSING) or "none"}')
    for name, pose in POSES.items():
        if not pose:
            continue
        posed = skin_all(shape, bones, skin_xf, posed_world(pose))
        worst = []
        for a, b in edges:
            l0 = math.dist(rest[a], rest[b])
            if l0 < 0.05:
                continue
            worst.append((math.dist(posed[a], posed[b]) / l0, math.dist(posed[a], posed[b]) - l0, a, b))
        worst.sort(reverse=True)
        print(f'\n{name}: worst edge growth x{worst[0][0]:.1f} (+{worst[0][1]:.2f} units); '
              f'edges grown > 3x: {sum(1 for w in worst if w[0] > 3)}; > +2 units: {sum(1 for w in worst if w[1] > 2)}')
        for ratio, grow, a, b in worst[:4]:
            for v in (a, b):
                ws = sorted(((bones[sl], round(w, 2)) for sl, w in shape.skin_weights(v)), key=lambda t: -t[1])
                print(f'   v{v} ({rest[v][0]:5.2f},{rest[v][1]:5.2f},{rest[v][2]:6.2f}) -> moved '
                      f'{math.dist(posed[v], rest[v]):5.2f}: {ws}')
            print(f'     edge x{ratio:.1f} (+{grow:.2f})')


if __name__ == '__main__':
    main()
