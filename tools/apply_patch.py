"""Stage 1 from the PLAYER'S CBBE plus Nahka's patch (decision A-23): what the builder runs.

make_patch.py extracted only Nahka's own work. This puts it into the player's CBBE Body Physics:

  vertices   CBBE's, minus the ones her geometry replaces (so none lingers invisibly inside the
             canal), in CBBE's order; then hers. CBBE's records are untouched; hers take the CBBE
             skin's bone slots by NAME, and a vertex leaning on a bone that skin lacks (her 2017 cloth
             bones) is re-weighted from its CBBE neighbours, as align_body did.
  triangles  CBBE's, minus the ones her topology drops; then hers. The BSSubIndexTriShape segments
             are recounted, and hers extend the segment that held the body.
  sliders    CBBE's own data on CBBE's vertices; on hers, the blend of the player's CBBE diffs at
             her neighbours plus her own deviation (align_body's correction, with no CBBE data
             shipped); her genital sliders as she drew them.
  the rest   the player's CBBE file as it is: skeleton nodes, skin, bone data, shader, cloth.

The CBBE must be the one the patch was made against (vertex and triangle counts, vertex layout, and
a hash of every vertex it names); anything else is refused.

    python tools/apply_patch.py [--data <Data>] [--patch <nahka_patch.json.gz>] [--out <project dir>]
"""
import argparse
import collections
import gzip
import json
import pathlib
import struct

import align_body as ab
import make_patch
import nif
import osd


def load(path):
    return json.loads(gzip.decompress(pathlib.Path(path).read_bytes()))


def build(data, patch, out):
    bs = data / 'Tools/BodySlide'
    cset, csliders = ab.read_set(bs / 'SliderSets/CBBE.osp', ab.CBBE_SET)
    folder = bs / 'ShapeData' / cset.findtext('DataFolder')
    cbbe = nif.Nif(folder / cset.findtext('SourceFile'))
    cosd = osd.read(folder / csliders[0][3])
    cs = cbbe.shape(ab.SHAPE)
    ctris = cs.triangles()
    meta = patch['cbbe']
    got = dict(vertices=cs.count, triangles=len(ctris), desc=cs.desc)
    want = {k: meta[k] for k in got}
    if got != want:
        raise SystemExit(f'this CBBE is not the one the patch was made against: {got} vs {want}')
    named = sorted({i for i in range(cs.count) if i not in set(patch['replaced'])} |
                   {i for t in patch['remove'] for i in t})
    if make_patch.fingerprint(cs, named) != meta['hash']:
        raise SystemExit('this CBBE\'s vertices differ from the ones the patch was made against (hash)')

    # ---- vertices
    replaced = set(patch['replaced'])
    kept_v = [i for i in range(cs.count) if i not in replaced]
    out_of = {i: k for k, i in enumerate(kept_v)}                  # CBBE index -> output index
    base = len(kept_v)
    stride = cs.stride
    cbones, _ = cbbe.skin(cs)
    slot_of = {b: k for k, b in enumerate(cbones)}
    pbones = patch['bones']
    records, reweighted = [], 0
    for k, hexrec in enumerate(patch['vertices']):
        rec = bytearray(bytes.fromhex(hexrec))
        if len(rec) != stride:
            raise SystemExit(f'patch vertex {k}: record size {len(rec)}, CBBE uses {stride}')
        w = struct.unpack_from('<4e', rec, cs.skin_at)
        s = struct.unpack_from('<4B', rec, cs.skin_at + 8)
        pairs = [(pbones[s[q]], float(w[q])) for q in range(4) if w[q] > 0]
        if all(b in slot_of for b, _ in pairs):
            struct.pack_into('<4B', rec, cs.skin_at + 8,
                             *[slot_of[pbones[s[q]]] if w[q] > 0 else 0 for q in range(4)])
        else:                                                        # her 2017 cloth bones: from neighbours
            acc = collections.defaultdict(float)
            for ci, wt in patch['near'][k]:
                for sl, v in cs.skin_weights(ci):
                    acc[sl] += wt * v
            top = sorted(acc.items(), key=lambda sv: -sv[1])[:4]
            total = sum(v for _, v in top)
            top = [(sl, v / total) for sl, v in top] + [(0, 0.0)] * (4 - len(top))
            struct.pack_into('<4e', rec, cs.skin_at, *(v for _, v in top))
            struct.pack_into('<4B', rec, cs.skin_at + 8, *(sl for sl, _ in top))
            reweighted += 1
        records.append(bytes(rec))
    vdata = b''.join(cs.record(i) for i in kept_v) + b''.join(records)

    # ---- triangles
    drop = {frozenset(t) for t in patch['remove']}
    kept_t = [t for t in ctris if frozenset(t) not in drop]
    if len(kept_t) != len(ctris) - len(drop):
        raise SystemExit('a triangle the patch removes is not in this CBBE')

    def ref(r):
        return out_of[r] if r >= 0 else base + (-1 - r)
    tris = [tuple(out_of[i] for i in t) for t in kept_t] + [tuple(ref(r) for r in t) for t in patch['triangles']]

    # ---- the shape block: CBBE's, with the new vertex and triangle lists and recounted segments
    o, size = cbbe.offsets[cs.index]
    c = nif.Cursor(cbbe.b, o)
    cbbe._av(c)
    c.take('4f')
    c.take('i'), c.take('i'), c.take('i')
    c.take('Q')
    counts_at = c.o
    seg_at = cs.data_at + cs.count * stride + 6 * cs.triangle_count
    seg = bytes(cbbe.b[seg_at:o + size])
    tri_bytes = b''.join(struct.pack('<3H', *t) for t in tris)
    if cbbe.types[cs.index] == 'BSSubIndexTriShape':
        keep_flags = [frozenset(t) not in drop for t in ctris]
        before = [0] * (len(ctris) + 1)
        for k2, f in enumerate(keep_flags):
            before[k2 + 1] = before[k2] + (1 if f else 0)
        sc = nif.Cursor(seg, 0)
        sc.take('I')
        nseg, total = sc.take('I'), sc.take('I')
        body = bytearray(struct.pack('<III', len(tris), nseg, total))
        rows = []
        for _ in range(nseg):
            start, count, parent, nsub = sc.take('I'), sc.take('I'), sc.take('I'), sc.take('I')
            lo, hi = start // 3, start // 3 + count
            subs = []
            for _ in range(nsub):
                ss, scn, sp, su = sc.take('I'), sc.take('I'), sc.take('I'), sc.take('I')
                subs.append([before[ss // 3] * 3, before[ss // 3 + scn] - before[ss // 3], sp, su])
            rows.append([before[lo] * 3, before[hi] - before[lo], parent, subs])
        last = max(k2 for k2, r in enumerate(rows) if r[1] > 0)    # hers extend the body's segment
        rows[last][1] += len(patch['triangles'])
        for start, count, parent, subs in rows:
            body += struct.pack('<IIII', start, count, parent, len(subs))
            for s4 in subs:
                body += struct.pack('<IIII', *s4)
        seg = bytes(body) + seg[sc.o:]
        if sum(r[1] for r in rows) != len(tris):
            raise SystemExit('segments do not cover the triangles')
    counts = struct.pack('<IHI', len(tris), len(kept_v) + len(records), len(vdata) + len(tri_bytes))
    if len(kept_v) + len(records) > 0xFFFF:
        raise SystemExit('more than 65,535 vertices')
    shape_blk = bytes(cbbe.b[o:counts_at]) + counts + vdata + tri_bytes + seg

    # ---- sliders
    near = patch['near']
    data_out = {}
    zero = (0.0, 0.0, 0.0)
    for name, attrs, dname, _ in csliders:
        cd = cosd.get(dname, {})
        dev = patch['deviation'].get(name, {})
        diffs = {out_of[i]: d for i, d in cd.items() if i in out_of}
        for k in range(len(records)):
            v = [0.0, 0.0, 0.0]
            for ci, wt in near[k]:
                d = cd.get(ci, zero)
                for q in range(3):
                    v[q] += wt * d[q]
            dv = dev.get(str(k))
            if dv:
                v = [v[q] + dv[q] for q in range(3)]
            if any(x != 0.0 for x in v):
                diffs[base + k] = tuple(v)
        data_out[ab.TARGET + name] = diffs
    genital = []
    for name, attrs in patch['sets']:
        g = patch['genital'][name]
        diffs = {base + int(k): tuple(v) for k, v in g['new'].items()}
        diffs.update({out_of[int(i)]: tuple(v) for i, v in g['cbbe'].items()})
        data_out[ab.TARGET + name] = diffs
        genital.append((name, attrs, ab.TARGET + name, ''))

    # ---- write stage 1 where align_body used to
    shape_dir = out / 'ShapeData' / ab.DATA_FOLDER
    shape_dir.mkdir(parents=True, exist_ok=True)
    (out / 'SliderSets').mkdir(parents=True, exist_ok=True)
    (shape_dir / f'{ab.DATA_FOLDER}.nif').write_bytes(cbbe.with_edits(replace={cs.index: shape_blk}))
    osd.write(shape_dir / f'{ab.DATA_FOLDER}.osd', data_out)
    ab.write_osp(out / 'SliderSets' / f'{ab.DATA_FOLDER}.osp', cset, csliders, genital)
    (out / 'mapping.json').write_text(json.dumps({
        'output_to_cbbe': {str(k): i for i, k in out_of.items()},
        'cbbe_slider_data': {n: d for n, _, d, _ in csliders},
        'genital_sliders': [n for n, _ in patch['sets']]}))
    print(f'stage 1 from this CBBE + the patch: {len(kept_v)} CBBE vertices + {len(records)} hers '
          f'({reweighted} re-weighted from neighbours), {len(tris)} triangles; {len(csliders)} CBBE sliders, '
          f'{len(genital)} genital -> {shape_dir}')
    return shape_dir / f'{ab.DATA_FOLDER}.nif'


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--data', type=pathlib.Path, default=ab.DEFAULT_DATA)
    ap.add_argument('--patch', type=pathlib.Path, default=make_patch.OUT)
    ap.add_argument('--out', type=pathlib.Path, default=ab.OUT)
    args = ap.parse_args()
    build(args.data, load(args.patch), args.out)


if __name__ == '__main__':
    main()
