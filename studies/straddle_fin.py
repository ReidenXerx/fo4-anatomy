"""Her hip fin in a straddle (2026-10-16): big flat skin "wings" along her thighs in AAF Cowgirl, seen behind and below.
The A-30 hip fold (tools/hip_fold.py) measured legs up and spread 45; a straddle raises AND spreads the thighs much
further. Poses the women's skeleton (tools/pose_check) in straddles and reports the worst edge growth over the hips,
where the worst vertices sit and which bones carry them.

    python studies/straddle_fin.py [--body <FemaleBody.nif>]
"""
import argparse
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'tools'))
import align_body as ab  # noqa: E402
import nif  # noqa: E402
import pose_check as pc  # noqa: E402

BODY = pathlib.Path(r'D:/SteamFreeGames/Fallout 4 AE/Data/Meshes/Actors/Character/CharacterAssets/FemaleBody.nif')
HIPS = (18.0, -62.0, -35.0)   # |x| <=, z in


def unit(v):
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v)


def straddle(up, out):
    """both thighs raised `up` and spread `out` degrees, as one turn about a tilted axis per side"""
    deg = math.degrees(math.acos(math.cos(math.radians(up)) * math.cos(math.radians(out))))
    left = unit((math.sin(math.radians(up)), math.sin(math.radians(out)), 0.0))
    right = unit((math.sin(math.radians(up)), -math.sin(math.radians(out)), 0.0))
    return {'LLeg_Thigh': (left, deg), 'RLeg_Thigh': (right, deg)}


POSES = {
    'legs up 100 (A-30 measured 4.2)': {'LLeg_Thigh': ((1, 0, 0), 100), 'RLeg_Thigh': ((1, 0, 0), 100)},
    'straddle: up 60, out 45': straddle(60, 45),
    'straddle: up 80, out 60': straddle(80, 60),
    'straddle: up 90, out 75': straddle(90, 75),
    'straddle (negative up): up -80, out 60': straddle(-80, 60),
}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--body', type=pathlib.Path, default=BODY)
    a = ap.parse_args()
    body = nif.Nif(a.body)
    shape = body.shape(ab.SHAPE)
    bones, xf = body.skin(shape)
    rest = shape.positions()
    region = {j for j, p in enumerate(rest) if abs(p[0]) <= HIPS[0] and HIPS[1] <= p[2] <= HIPS[2]}
    edges = set()
    for t in shape.triangles():
        for x, y in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            if x in region or y in region:
                edges.add((min(x, y), max(x, y)))
    print(f'{a.body.name}: {len(region)} hip vertices, {len(edges)} edges; bones the women\'s skeleton lacks: ', end='')
    pc.skin_all(shape, bones, xf, pc.posed_world({}))
    print(sorted(pc.MISSING) or 'none')
    for name, pose in POSES.items():
        posed = pc.skin_all(shape, bones, xf, pc.posed_world(pose))
        worst = []
        for x, y in edges:
            l0 = math.dist(rest[x], rest[y])
            if l0 >= 0.05:
                worst.append((math.dist(posed[x], posed[y]) / l0, math.dist(posed[x], posed[y]) - l0, x, y))
        worst.sort(reverse=True)
        print(f'{name}: worst x{worst[0][0]:.1f} (+{worst[0][1]:.1f} units); > 3x: {sum(w[0] > 3 for w in worst)}; '
              f'> +3 units: {sum(w[1] > 3 for w in worst)}')
        for ratio, grow, x, y in worst[:2]:
            ws = sorted(((bones[sl], round(w, 2)) for sl, w in shape.skin_weights(x)), key=lambda t: -t[1])
            print(f'    v{x} ({rest[x][0]:5.1f},{rest[x][1]:5.1f},{rest[x][2]:6.1f}) x{ratio:.1f}: {ws}')


if __name__ == '__main__':
    main()
