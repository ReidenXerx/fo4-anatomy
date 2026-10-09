"""Copy the rig's skin weights onto already BUILT Servitron abdomens (a BodySlide build keeps every vertex, its order and
the bone list; a rig change that only reweights, like the rigid rings of 2026-10-09, need not wait for a rebuild).
Each built shape is matched to the ShapeData shape of the same name and vertex count; its weights are written in
place (nif.py: fixed-size vertex bytes), slots mapped by bone name. A shape whose bones the source has more of is left.

    python studies/servitron_weights_onto_built.py <ShapeData folder(s) ...> --built <built .nif ...> [--apply]
"""
import argparse
import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'tools'))
import nif  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('sources', nargs='+', type=pathlib.Path)
    ap.add_argument('--built', nargs='+', type=pathlib.Path, required=True)
    ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()
    src = {}
    for folder in a.sources:
        for p in folder.rglob('*.nif'):
            n = nif.Nif(p)
            for s in n.shapes():
                src.setdefault((s.name, s.count), (n, s))
    for b in a.built:
        n = nif.Nif(b)
        changed, notes = 0, []
        for s in n.shapes():
            hit = src.get((s.name, s.count))
            if hit is None:
                continue
            sn, ss = hit
            if ss.triangles() != s.triangles():
                notes.append(f'{s.name}: triangles differ, left')
                continue
            sb, bb = sn.skin(ss)[0], n.skin(s)[0]
            slot = {x: k for k, x in enumerate(bb)}
            missing = sorted({sb[sl] for v in range(ss.count) for sl, w in ss.skin_weights(v) if w > 0} - set(slot))
            if missing:
                notes.append(f'{s.name}: bones {missing[:4]} not in the built shape, left')
                continue
            for v in range(s.count):
                so = ss.data_at + v * ss.stride + ss.skin_at
                w = bytes(sn.b[so:so + 8])
                sl = struct.unpack_from('<4B', sn.b, so + 8)
                ws = struct.unpack_from('<4e', sn.b, so)
                raw = w + bytes(slot[sb[sl[k]]] if ws[k] > 0 else 0 for k in range(4))
                bo = s.data_at + v * s.stride + s.skin_at
                if bytes(n.b[bo:bo + 12]) != raw:
                    n.b[bo:bo + 12] = raw
                    changed += 1
        print(f'{b.name}: {changed} vertices reweighted' + (f'; {"; ".join(notes)}' if notes else ''))
        if a.apply and changed:
            with open(b, 'r+b') as f:                    # in place: a Vortex hard link stays one file
                f.write(bytes(n.b))
                f.truncate()


if __name__ == '__main__':
    main()
