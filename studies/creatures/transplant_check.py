"""After a transplant: every vanilla block is byte-identical except the root and the blocks of replaced shapes (shape,
skin instance, bone data); our shapes' positions/UVs equal the export's; every BSSubIndexTriShape's segments tile.
    python -I transplant_check.py <vanilla dir> <export dir> <out dir> [--strip _F]"""
import pathlib
import struct
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import nif  # noqa: E402
from transplant import _shape_refs_at  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def seg_ok(m, s):
    o = s.data_at + s.count * s.stride + 6 * s.triangle_count
    nprim, nseg, total = struct.unpack_from('<3I', m.b, o)
    o += 12
    spans = []
    for _ in range(nseg):
        start, cnt, par, nsub = struct.unpack_from('<4I', m.b, o)
        o += 16 + 16 * nsub
        if cnt:
            spans.append((start // 3, cnt))
    pos = 0
    for st, cnt in sorted(spans):
        if st != pos:
            return False
        pos = st + cnt
    return pos == s.triangle_count == nprim


van, exp, out = (pathlib.Path(a) for a in sys.argv[1:4])
strip = '_F'
bad = 0
for f in sorted(out.glob('*.nif')):
    base = f.stem.removesuffix(strip)
    vp = next((p for p in van.glob('*.nif') if p.stem.lower() == base.lower()), None)
    V, O, E = nif.Nif(vp), nif.Nif(f), nif.Nif(exp / f.name)
    vs = {s.name: s for s in V.shapes()}
    os_ = {s.name: s for s in O.shapes()}
    allowed = {0}
    for s in O.shapes():
        if s.name in vs and s.count != vs[s.name].count:
            sk = struct.unpack_from('<i', O.b, _shape_refs_at(O, s.index))[0]
            allowed |= {s.index, sk, struct.unpack_from('<i', O.b, O.offsets[sk][0] + 4)[0]}
    diff = [i for i in range(len(V.offsets)) if i not in allowed and
            bytes(V.b[V.offsets[i][0]:sum(V.offsets[i])]) != bytes(O.b[O.offsets[i][0]:sum(O.offsets[i])])]
    notes = []
    if diff:
        notes.append(f'VANILLA BLOCKS CHANGED {[(i, V.types[i]) for i in diff[:6]]}')
        bad += 1
    for s in E.shapes():
        if s.name not in os_:
            continue
        if s.name in vs and s.count == vs[s.name].count:
            continue                                              # untouched: vanilla's own (checked above)
        o = os_[s.name]
        dp = np.abs(np.array(o.positions()) - np.array(s.positions())).max()
        du = np.abs(np.array([o.uv(i) for i in range(o.count)]) - np.array([s.uv(i) for i in range(s.count)])).max()
        ok = dp < 1e-4 and du < 1e-4 and o.triangle_count == s.triangle_count
        if O.types[o.index] == 'BSSubIndexTriShape':
            ok &= seg_ok(O, o)
        if not ok:
            notes.append(f'{s.name}: dpos {dp} duv {du} or segments broken')
            bad += 1
    missing = [n for n in vs if n not in os_]
    if missing:
        notes.append(f'MISSING {missing}')
        bad += 1
    print(f'{f.name}: {"OK" if not notes else " ".join(notes)}')
print('problems', bad)
