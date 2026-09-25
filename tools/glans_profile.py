"""The glans's profile for the fork's contact mouth (physics_design.GLANS_PROFILE, the fork's Glans.h).

Builds BodyTalk4's erect penis (the owner's MaleBody.nif, its .tri), shapes it the way the fork does at run time
(A-31: Penis_01..04 x shaft about their own origins, Penis_05 x head), and prints the flesh's widest radius
along the axis in units of the tip sphere's radius R = 1.8 x head, from the Penis_05 bone (along < 0 behind it).
Then compares the mouth's old reading (the collider spheres, straight between bones, minus [Mouth] skin) with
the mesh.

Needs fo4-silhouette's tools (mesh.py builds a body from its .tri) and the game's Data folder.
"""
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'fo4-silhouette' / 'tools' / 'pool'))
sys.path.insert(0, str(HERE.parents[1] / 'fo4-silhouette' / 'tools'))
sys.path.insert(0, str(HERE))
import mesh  # noqa: E402
import nif   # noqa: E402

DATA = pathlib.Path(r'D:\GOGGames\Fallout 4 GOTY\Data')
NAMES = ('Penis_01', 'Penis_02', 'Penis_03', 'Penis_04', 'Penis_05')
SHAFT_R, HEAD_R, SKIN = 2.0, 1.8, 0.2       # physics_design COLLIDERS and MOUTH skin


def main():
    b = mesh.Body(DATA, 'male')
    er = b.build({'Erection': 1.0})
    moved = [i for i in range(len(b.ref)) if math.dist(er[i], b.ref[i]) > 0.3]
    tip = max(moved, key=lambda i: er[i][1])
    root_pts = sorted(moved, key=lambda i: math.dist(er[i], b.ref[i]))[:20]
    root = [sum(er[i][k] for i in root_pts) / len(root_pts) for k in range(3)]
    ax = [er[tip][k] - root[k] for k in range(3)]
    L = math.sqrt(sum(c * c for c in ax))
    ax = [c / L for c in ax]
    n = nif.Nif(DATA / 'Meshes' / 'Actors' / 'Character' / 'CharacterAssets' / 'MaleBody.nif')
    s = [x for x in n.shapes() if x.count == len(b.ref)][0]
    bones, bxf = n.skin(s)
    O = {nm: nif.bone_origin(bxf[bones.index(nm)]) for nm in NAMES}
    H = {nm: sum((O[nm][j] - root[j]) * ax[j] for j in range(3)) for nm in NAMES}
    print('bones along the axis:', {k: round(v, 2) for k, v in H.items()})

    def shaped(sh, hd):
        out = []
        for i, p in enumerate(er):
            q = list(p)
            for sl, w in s.skin_weights(i):
                nm = bones[sl]
                if nm in O:
                    sc = hd if nm == 'Penis_05' else sh
                    q = [q[k] + w * (sc - 1.0) * (p[k] - O[nm][k]) for k in range(3)]
            out.append(q)
        return out

    def widest(v, step):
        bins = {}
        for i in moved:
            d = [v[i][k] - root[k] for k in range(3)]
            h = sum(d[k] * ax[k] for k in range(3))
            r = math.sqrt(max(0.0, sum(c * c for c in d) - h * h))
            bins[round(h / step)] = max(bins.get(round(h / step), 0.0), r)
        return {k * step: r for k, r in sorted(bins.items())}

    def spheres(h, sh, hd):
        pts = [(H[nm], HEAD_R * hd if nm == 'Penis_05' else SHAFT_R * sh) for nm in NAMES]
        for (h0, r0), (h1, r1) in zip(pts, pts[1:]):
            if h0 <= h <= h1:
                return r0 + (r1 - r0) * (h - h0) / (h1 - h0) - SKIN
        dT = h - pts[-1][0]
        rT = pts[-1][1]
        return math.sqrt(max(0.0, rT * rT - dT * dT)) - SKIN if dT < rT else 0.0

    for hd in (1.2, 1.3, 1.4):
        v = shaped(0.85, hd)
        R = HEAD_R * hd
        prof = widest(v, 0.25)
        print(f'head x{hd} (R {R:.2f}), along:radius in R: ' + ' '.join(
            f'{(h - H["Penis_05"]) / R:+.2f}:{r / R:.2f}' for h, r in prof.items() if (h - H['Penis_05']) / R >= -1.4))
        worst = max(((r - spheres(h, 0.85, hd), h) for h, r in widest(v, 0.5).items() if h > H['Penis_04']),
                    default=(0.0, 0.0))
        print(f'  the spheres read it {worst[0]:.2f} too thin at {(worst[1] - H["Penis_05"]) / R:+.2f} R')


if __name__ == '__main__':
    main()
