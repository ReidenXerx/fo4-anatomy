"""Prove a BodySlide BUILD of the anatomy body equals today's CBBE build of the same preset on every
shared vertex: the mesh an outfit was fitted against, and the .tri morphs Silhouette and LooksMenu
move it with. The strongest check there is, because it runs BodySlide itself.

    python tools/lab.py build CBBELab "CBBE Curvy" D:/F4Output/AnatomyLab/out/cbbe --game-is-free
    python tools/lab.py build AnatomyLab "CBBE Curvy" D:/F4Output/AnatomyLab/out/anatomy --game-is-free
    python tools/compare_builds.py D:/F4Output/AnatomyLab/out/cbbe D:/F4Output/AnatomyLab/out/anatomy

Positions are half floats in a built FO4 body, so "equal" means within half-float rounding of the
larger coordinate (0.0625 above |64|).
"""
import argparse
import json
import math
import pathlib
import struct
import sys

import align_body as ab
import nif

BODY = 'meshes/actors/character/characterassets/FemaleBody'


def half_step(x):
    """Spacing of half floats around x: the rounding a built body carries."""
    a = abs(x)
    if a < 2 ** -14:
        return 2 ** -24
    return 2 ** (math.floor(math.log2(a)) - 10)


def read_tri(path):
    """{shape: {morph: {vertex: (dx, dy, dz)}}} from a BodySlide .tri (PIRT)."""
    b = pathlib.Path(path).read_bytes()
    if b[:4] != b'PIRT':
        raise ValueError(f'{path}: not a BodySlide .tri')
    o, out = 4, {}
    (nshapes,) = struct.unpack_from('<H', b, o)
    o += 2
    for _ in range(nshapes):
        n = b[o]
        shape = b[o + 1:o + 1 + n].decode('latin1')
        o += 1 + n
        (nmorphs,) = struct.unpack_from('<H', b, o)
        o += 2
        morphs = {}
        for _ in range(nmorphs):
            n = b[o]
            name = b[o + 1:o + 1 + n].decode('latin1')
            o += 1 + n
            (mult,) = struct.unpack_from('<f', b, o)
            o += 4
            (count,) = struct.unpack_from('<H', b, o)
            o += 2
            d = {}
            for k in range(count):
                idx, x, y, z = struct.unpack_from('<H3h', b, o + k * 8)
                d[idx] = (x * mult, y * mult, z * mult)
            o += count * 8
            morphs[name] = d
        out[shape] = morphs
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('cbbe', type=pathlib.Path)
    ap.add_argument('anatomy', type=pathlib.Path)
    ap.add_argument('--project', type=pathlib.Path, default=ab.OUT)
    args = ap.parse_args()
    mapping = {int(j): i for j, i in json.loads((args.project / 'mapping.json').read_text())['output_to_cbbe'].items()}

    def find(root, ext):
        hits = [p for p in root.rglob('*' + ext) if p.stem.lower() == 'femalebody']
        if not hits:
            raise SystemExit(f'no FemaleBody{ext} under {root}')
        return hits[0]

    c = nif.Nif(find(args.cbbe, '.nif')).shape(ab.SHAPE)
    a = nif.Nif(find(args.anatomy, '.nif')).shape(ab.SHAPE)
    cv, av = c.positions(), a.positions()
    # The one intended difference: the front of the vaginal opening, which opening.py bakes into the
    # base (the slit's front rim is partly CBBE's own vertices). Those must sit exactly where the bake
    # puts them, from CBBE's own position; every other shared vertex must be CBBE's.
    import opening
    import osd
    pen = (osd.read(args.project / f'ShapeData/{opening.FOLDER}/{opening.FOLDER}.osd')
           .get(ab.SHAPE + opening.SOURCE, {}))
    designed = {}
    for j, i in mapping.items():
        if j in pen and opening.weight(cv[i][1]) > 0.0:
            designed[j] = opening.displacement(pen[j], cv[i][1], opening.BAKED)
    off, by_design, design_worst = [], 0, 0.0
    for j, i in mapping.items():
        want = tuple(cv[i][k] + designed.get(j, (0.0, 0.0, 0.0))[k] for k in range(3))
        d = max(abs(p - q) for p, q in zip(want, av[j]))
        tol = max(half_step(x) for x in cv[i]) * (2.02 if j in designed else 1.01)
        if d > tol:
            off.append((d, j, i))
        elif j in designed and max(abs(x) for x in designed[j]) > tol:
            by_design += 1
            design_worst = max(design_worst, max(abs(x) for x in designed[j]))
    print(f'mesh: {len(mapping)} shared vertices; beyond half-float rounding: {len(off)}'
          + (f' (worst {max(off)[0]:.4f})' if off else '')
          + f'; moved by design (the opening baked into the base), each where the bake puts it: '
            f'{by_design} (up to {design_worst:.3f})')

    ct, at = read_tri(find(args.cbbe, '.tri')), read_tri(find(args.anatomy, '.tri'))
    cm, am = ct.get(ab.SHAPE, {}), at.get(ab.SHAPE, {})
    missing = sorted(set(cm) - set(am))
    worst, bad = 0.0, {}
    for m in sorted(set(cm) & set(am)):
        for j, i in mapping.items():
            p, q = cm[m].get(i, (0, 0, 0)), am[m].get(j, (0, 0, 0))
            d = max(abs(x - y) for x, y in zip(p, q))
            worst = max(worst, d)
            if d > 0.01:
                bad[m] = bad.get(m, 0) + 1
    print(f'.tri: CBBE {len(cm)} morphs, anatomy {len(am)}; missing from anatomy: {missing or "none"}; '
          f'extra: {sorted(set(am) - set(cm))}')
    print(f'      shared vertices moved differently (> 0.01): {bad or "none"}; worst {worst:.4f}')
    if off or missing or bad:
        print('\nFAIL')
        sys.exit(1)
    print('\nPASS - the anatomy build is today\'s CBBE build on every shared vertex, mesh and morphs.')


if __name__ == '__main__':
    main()
