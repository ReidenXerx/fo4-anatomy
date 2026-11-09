"""Dismemberment-safe segments after a PyNifly export (feral crash 11-09: BGSDismembermentManager::PostprocessCut null
on a female Bloated Glowing One; PyNifly had rewritten segment data of shapes it never needed to touch, e.g.
Boils003 sub-segment user index 2 -> 1, and our new genital shapes were plain BSTriShapes).
  - every shape the vanilla mesh also has, with the same vertices (by index) and triangle count: its triangles AND
    segment data are put back byte for byte from vanilla (vertex order is vanilla's, checked);
  - shapes we sculpted (more triangles): PyNifly's segments kept, checked to cover every triangle exactly once;
  - our new shapes: retyped BSTriShape -> BSSubIndexTriShape with UAP's own minimal layout (all triangles in one
    segment: 'single' = 1 segment as UAP's feral penis; 'torso4' = 4 segments, all in the 4th, as UAP's synth penis).
    python -I seg_fix.py <vanilla.nif> <ours.nif> single|torso4"""
import struct
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
van_p, ours_p, pattern = sys.argv[1:4]
v, m = nif.Nif(van_p), nif.Nif(ours_p)
vs = {s.name: s for s in v.shapes()}


def tail_start(f, s):
    """file offset where the triangles start (after the vertex data)"""
    return s.data_at + s.count * s.stride


def seg_coverage(f, s):
    """(covered triangle count, ok) from the segment table: segments + sub-segments tile [0, ntri) exactly"""
    o = tail_start(f, s) + 6 * s.triangle_count
    nprim, nseg, total = struct.unpack_from('<3I', f.b, o)
    o += 12
    spans = []
    for _ in range(nseg):
        start, cnt, par, nsub = struct.unpack_from('<4I', f.b, o)
        o += 16 + 16 * nsub
        spans.append((start // 3, cnt))
    spans = sorted(x for x in spans if x[1])
    pos, ok = 0, True
    for st, cnt in spans:
        ok &= st == pos
        pos = st + cnt
    return pos, ok and pos == s.triangle_count and nprim == s.triangle_count


replace = {}
notes = []
for s in m.shapes():
    o_blk, sz = m.offsets[s.index]
    kind = m.types[s.index]
    if s.name in vs:
        w = vs[s.name]
        same_v = s.count == w.count and np.abs(np.array(s.positions()) - np.array(w.positions())).max() < 1e-4
        if same_v and s.triangle_count == w.triangle_count and kind == v.types[w.index]:
            mine = bytes(m.b[tail_start(m, s):o_blk + sz])
            wo, wsz = v.offsets[w.index]
            theirs = bytes(v.b[tail_start(v, w):wo + wsz])
            if mine != theirs:
                replace[s.index] = bytes(m.b[o_blk:tail_start(m, s)]) + theirs
                notes.append(f'{s.name}: triangles+segments restored from vanilla ({len(mine)}->{len(theirs)} bytes)')
            else:
                notes.append(f'{s.name}: identical to vanilla')
        elif kind == 'BSSubIndexTriShape':
            cov, ok = seg_coverage(m, s)
            notes.append(f'{s.name}: SCULPTED {w.triangle_count}->{s.triangle_count} tris, segments cover {cov} '
                         f'{"OK" if ok else "BROKEN"}')
            if not ok:
                raise SystemExit(f'{ours_p}: {s.name} segment table does not tile its triangles')
        else:
            notes.append(f'{s.name}: changed {kind} (left as is)')
        continue
    # a shape of ours
    if kind == 'BSSubIndexTriShape':
        notes.append(f'{s.name}: ours, already sub-index')
        continue
    n = s.triangle_count
    if pattern == 'single':
        seg = struct.pack('<3I', n, 1, 1) + struct.pack('<4I', 0, n, 0xFFFFFFFF, 0)
    else:
        seg = struct.pack('<3I', n, 4, 4) + b''.join(struct.pack('<4I', 0, 0, 0xFFFFFFFF, 0) for _ in range(3)) \
            + struct.pack('<4I', 0, n, 0xFFFFFFFF, 0)
    blk = bytes(m.b[o_blk:o_blk + sz])
    if o_blk + sz != tail_start(m, s) + 6 * n:
        raise SystemExit(f'{s.name}: unexpected bytes after the triangles of a BSTriShape')
    replace[s.index] = blk + seg
    if 'BSSubIndexTriShape' not in m.type_names:                  # an export of only our shapes: add the type
        m.type_names.append('BSSubIndexTriShape')
    m.type_index[s.index] =(m.type_index[s.index] & 0x8000) | m.type_names.index('BSSubIndexTriShape')
    notes.append(f'{s.name}: ours, BSTriShape -> BSSubIndexTriShape ({pattern}, {n} tris)')
if 'BSSubIndexTriShape' not in m.type_names:
    raise SystemExit('no BSSubIndexTriShape type in the file')
data = m.with_edits(replace=replace)
open(ours_p, 'wb').write(data)
chk = nif.Nif(ours_p)
for s in chk.shapes():
    if s.name in vs and s.count == vs[s.name].count:
        continue                                   # vanilla's own layout (some vanilla caps do not tile, e.g. radstag)
    if chk.types[s.index] == 'BSSubIndexTriShape':
        cov, ok = seg_coverage(chk, s)
        if not ok:
            raise SystemExit(f'after fix: {s.name} segments broken')
print(pathlib_name := ours_p.replace('\\', '/').split('/')[-1], '|', '; '.join(notes))
