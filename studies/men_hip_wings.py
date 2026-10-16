"""The men's hip "wings" (2026-10-16): flat skin sheets fanning out of a man's hip creases in AAF Cowgirl (Douglas Leonard,
Diamond City, on release Engine 1.2.25 too, so not strands). Is it skinning tear, as the women's A-30 fin was?

Poses the skeleton MEN load (Data's skeleton.nif, read through gamedata), skins the installed men's body by linear
blend skinning (tools/pose_check.skin_all) and reports the worst edge growth around the hips, with the bones of the
worst vertices; then the same with the women's A-30 hip fold applied to the men's weights (tools/hip_fold.soften),
to see whether that cure applies.

    python studies/men_hip_wings.py [--body <MaleBody.nif>]
"""
import argparse
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'tools'))
import gamedata  # noqa: E402
import hip_fold  # noqa: E402
import nif  # noqa: E402
import pose_check as pc  # noqa: E402
import zex_bones as zb  # noqa: E402

DATA = pathlib.Path(r'D:/SteamFreeGames/Fallout 4 AE/Data')
SKELETON = 'Meshes/Actors/Character/CharacterAssets/skeleton.nif'
BODY = DATA / 'Meshes/Actors/Character/CharacterAssets/MaleBody.nif'
SHAPE = 'BaseMaleBody:0'
HIPS = (16.0, -60.0, -35.0)            # |x| <=, z in: pelvis and upper thighs (the body's own space)

POSES = {
    'cowgirl: lying back, thighs spread 30': {'COM': ((1, 0, 0), 90, (0, 0, -30)), 'LLeg_Thigh': ((0, 1, 0), 30),
                                              'RLeg_Thigh': ((0, 1, 0), -30)},
    'cowgirl: lying back, knees up 60, spread 35': {'COM': ((1, 0, 0), 90, (0, 0, -30)),
                                                    'LLeg_Thigh': ((1, 0, 0), 60), 'RLeg_Thigh': ((1, 0, 0), 60)},
    'thighs spread 45': {'LLeg_Thigh': ((0, 1, 0), 45), 'RLeg_Thigh': ((0, 1, 0), -45)},
    'thighs spread 60': {'LLeg_Thigh': ((0, 1, 0), 60), 'RLeg_Thigh': ((0, 1, 0), -60)},
    'thighs flexed 90': {'LLeg_Thigh': ((1, 0, 0), 90), 'RLeg_Thigh': ((1, 0, 0), 90)},
}


def posed_world(sk, pose):
    """pose_check.posed_world on the men's skeleton"""
    parent = {}
    for i, n in sk.nodes.items():
        for kid in n['kids']:
            parent[kid] = i
    local = {}
    for i, n in sk.nodes.items():
        r, t = zb.rows(n['r']), list(n['t'])
        if n['name'] in pose:
            axis, deg, *move = pose[n['name']]
            r = zb.mul(r, pc.rot(axis, deg))
            if move:
                t = [t[k] + move[0][k] for k in range(3)]
        local[i] = (r, t, n['s'])
    world = {}

    def w(i):
        if i not in world:
            world[i] = zb.compose(w(parent[i]), local[i]) if i in parent else local[i]
        return world[i]
    return {sk.nodes[i]['name']: w(i) for i in sk.nodes if sk.nodes[i]['name']}


class Weighted:
    """a shape whose skin weights are replaced (hip_fold's output), positions as they were"""
    def __init__(self, shape, weights):
        self.shape, self.weights, self.count = shape, weights, shape.count

    def positions(self):
        return self.shape.positions()

    def skin_weights(self, j):
        return self.weights[j]


def measure(shape, bones, xf, rest, edges, world):
    posed = pc.skin_all(shape, bones, xf, world)
    worst = []
    for a, b in edges:
        l0 = math.dist(rest[a], rest[b])
        if l0 >= 0.05:
            worst.append((math.dist(posed[a], posed[b]) / l0, a, b))
    worst.sort(reverse=True)
    return worst, sum(1 for w in worst if w[0] > 3)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--body', type=pathlib.Path, default=BODY)
    a = ap.parse_args()
    raw = gamedata.Game(DATA).read(SKELETON)
    tmp = pathlib.Path(__file__).resolve().parent / '_men_skeleton.nif'
    tmp.write_bytes(raw)
    sk = nif.Nif(tmp)
    body = nif.Nif(a.body)
    shape = body.shape(SHAPE)
    bones, xf = body.skin(shape)
    rest = shape.positions()
    region = {j for j, p in enumerate(rest) if abs(p[0]) <= HIPS[0] and HIPS[1] <= p[2] <= HIPS[2]}
    edges = set()
    for t in shape.triangles():
        for x, y in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            if x in region or y in region:
                edges.add((min(x, y), max(x, y)))
    base = pc.skin_all(shape, bones, xf, posed_world(sk, {}))
    drift = max(math.dist(base[j], rest[j]) for j in region)
    print(f'{a.body.name}: {len(region)} hip vertices, {len(edges)} edges; rest drift {drift:.3f} (pose_check.OFF '
          f'is the women\'s; large drift = the men\'s skeleton binds elsewhere); missing bones {sorted(pc.MISSING)}')
    # our four anus bones are made by the engine at run time ([Bones]) under the pelvis, so offline they would stay
    # behind (pose_check's A-14 stretch, x75 lying back): their share goes to Pelvis_Rear_skin, which they follow
    names = list(bones)
    idx = {n: i for i, n in enumerate(names)}
    dicts = []
    for j in range(shape.count):
        d = {}
        for sl, w in shape.skin_weights(j):
            n = 'Pelvis_Rear_skin' if names[sl].startswith('AnatAnus') else names[sl]
            d[n] = d.get(n, 0.0) + w
        dicts.append(d)
    triangles = shape.triangles()
    shape = Weighted(shape, [[(idx[n], w) for n, w in d.items()] for d in dicts])
    pc.MISSING.clear()
    # the women's cure on the men's weights
    try:
        soft = hip_fold.soften(rest, triangles, dicts)
        softened = Weighted(shape.shape, [[(idx[n], w) for n, w in d.items()] for d in soft])
    except Exception as e:   # hip_fold's API is the women's: say why it does not fit
        softened = None
        print('hip_fold.soften on the men\'s weights:', repr(e))
    for name, pose in POSES.items():
        world = posed_world(sk, pose)
        worst, over3 = measure(shape, bones, xf, rest, edges, world)
        side = [w for w in worst if abs(rest[w[1]][0]) > 3 or abs(rest[w[2]][0]) > 3]
        line = f'{name}: worst x{worst[0][0]:.1f}, edges > 3x: {over3}; hip creases (|x|>3) worst x{side[0][0]:.1f}'
        if softened:
            w2, o2 = measure(softened, bones, xf, rest, edges, world)
            line += f'   | hip fold: worst x{w2[0][0]:.1f}, > 3x: {o2}'
        print(line)
        for ratio, x, y in worst[:1] + side[:1]:
            for v in (x, y):
                ws = sorted(((bones[sl], round(w, 2)) for sl, w in shape.skin_weights(v)), key=lambda t: -t[1])
                print(f'    v{v} ({rest[v][0]:5.1f},{rest[v][1]:5.1f},{rest[v][2]:6.1f}): {ws}')


if __name__ == '__main__':
    main()
