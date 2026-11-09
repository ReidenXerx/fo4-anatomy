"""After feral_all.py: every original shape that should be untouched (male files: all; female files: all but the body
and its glow shells) keeps its vertex positions, UVs, triangle count and transform; new shapes are listed.
    python -I feral_verify.py"""
import pathlib
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402

ROOT = pathlib.Path(r'D:\F4Output\creatures\feral')
OUT = ROOT / 'out3/Data/meshes/actors/feralghoul/characterassets'
bad = 0
for dst in sorted(OUT.glob('*.nif')):
    src = ROOT / 'vanilla' / (dst.stem.removesuffix('_F') + '.nif')
    s, d = nif.Nif(src), nif.Nif(dst)
    ss = {x.name: x for x in s.shapes()}
    notes = []
    for x in d.shapes():
        if x.name not in ss:
            notes.append(f'+{x.name}({x.count}v)')
            continue
        y = ss[x.name]
        if x.count != y.count:
            notes.append(f'~{x.name} {y.count}->{x.count}v')
            continue
        dp = np.abs(np.array(x.positions()) - np.array(y.positions())).max()
        du = np.abs(np.array([x.uv(i) for i in range(x.count)]) - np.array([y.uv(i) for i in range(y.count)])).max()
        if dp > 1e-3 or du > 1e-3 or x.triangle_count != y.triangle_count:
            notes.append(f'!{x.name} dpos {dp:.4f} duv {du:.4f} tris {y.triangle_count}->{x.triangle_count}')
            bad += 1
    missing = [n for n in ss if n not in {x.name for x in d.shapes()}]
    if missing:
        notes.append(f'MISSING {missing}')
        bad += 1
    print(f'{dst.name}: {" ".join(notes) or "unchanged"}')
print('problems', bad)
