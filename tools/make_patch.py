"""Nahka's genitals as a PATCH against CBBE: only her own work, nothing of CBBE's (decision A-23).

Her CBBEVaginaMorphsPhysics files are a whole 2017 CBBE body with her genitals in it. Her page lets
anyone use her work ("up for adoption ... no need to ask me for permission"), but the CBBE inside is
CBBE's, whose rule 3 asks permission for "uploading a modified body mesh outside of sliders". So the
release ships only what she added, expressed against the player's own CBBE, and the builder
(apply_patch.py) rebuilds stage 1 from their files. The patch holds:

  cbbe       the CBBE shape it was made against: vertex/triangle counts, vertex layout, and a hash of
             every CBBE vertex it names (rounded position + UV). A different CBBE is refused, never guessed.
  replaced   CBBE vertices her geometry replaces (dropped from the output)
  remove     CBBE triangles her topology does not keep (as CBBE vertex triples)
  vertices   her new vertex records, bone slots as indices into `bones` (her names)
  triangles  her new triangles; a reference >= 0 is a CBBE vertex, < 0 is new vertex -1-ref
  near       per new vertex, the shared CBBE vertices and weights align_body blends them from
             (inverse distance, the NEIGHBOURS nearest, in positions where shared = CBBE's)
  deviation  per CBBE slider, per new vertex: HER diff minus the blend of her diffs at those
             neighbours. The builder adds the blend of the PLAYER'S CBBE diffs, which is exactly
             align_body's "Nahka's diff plus the CBBE-minus-Nahka correction", with no CBBE data shipped.
  genital    her own sliders (Vagina*, Anus*...): diffs on new vertices and on CBBE vertices
  sets       her genital sliders' .osp attributes

    python tools/make_patch.py     -> build/patch/nahka_patch.json.gz
"""
import collections
import gzip
import hashlib
import json
import math
import pathlib
import struct

import align_body as ab
import nif
import osd

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'build/patch/nahka_patch.json.gz'


def fingerprint(shape, indices):
    h = hashlib.sha1()
    pos = shape.positions()
    for i in sorted(indices):
        h.update(struct.pack('<I', i))
        h.update(struct.pack('<3i', *(round(c * 1000) for c in pos[i])))
        h.update(struct.pack('<2i', *(round(c * 10000) for c in shape.uv(i))))
    return h.hexdigest()


def make(data=None):
    ab.extract_nahka()
    bs = (data or ab.DEFAULT_DATA) / 'Tools/BodySlide'
    nbs = ab.NAHKA_DIR / 'Data/Tools/BodySlide'
    cset, csliders = ab.read_set(bs / 'SliderSets/CBBE.osp', ab.CBBE_SET)
    nset, nsliders = ab.read_set(nbs / f'SliderSets/{ab.NAHKA_SET}.osp', ab.NAHKA_SET)
    cbbe_nif = nif.Nif(bs / 'ShapeData' / cset.findtext('DataFolder') / cset.findtext('SourceFile'))
    nahka_nif = nif.Nif(nbs / 'ShapeData' / nset.findtext('DataFolder') / nset.findtext('SourceFile'))
    nosd = osd.read(nbs / 'ShapeData' / nset.findtext('DataFolder') / nsliders[0][3])
    cs, ns = cbbe_nif.shape(ab.SHAPE), nahka_nif.shape(ab.SHAPE)
    mapping = ab.match(cs, ns)                                  # Nahka index -> CBBE index
    shared = sorted(mapping)
    new = [j for j in range(ns.count) if j not in mapping]
    newi = {j: k for k, j in enumerate(new)}
    ctris = cs.triangles()
    ckey = {frozenset(t): t for t in ctris}
    kept, ntris = set(), []
    for t in ns.triangles():
        if all(v in mapping for v in t):
            m = frozenset(mapping[v] for v in t)
            if m in ckey:
                kept.add(m)
                continue
        ntris.append([mapping[v] if v in mapping else -1 - newi[v] for v in t])
    remove = [list(t) for t in ctris if frozenset(t) not in kept]
    used = {mapping[j] for j in shared}
    replaced = [i for i in range(cs.count) if i not in used]

    nbones, _ = nahka_nif.skin(ns)
    records = []
    for j in new:
        rec = bytearray(ns.record(j))
        records.append(rec.hex())
    # neighbours exactly as align_body computes them: positions where shared vertices sit on CBBE's
    cpos = cs.positions()
    npos = ns.positions()
    pos_now = [cpos[mapping[j]] if j in mapping else npos[j] for j in range(ns.count)]
    grid = ab.Grid(pos_now, shared)
    near = {j: ab.idw(pos_now[j], pos_now, grid.nearest(pos_now[j], ab.NEIGHBOURS)) for j in new}
    zero = (0.0, 0.0, 0.0)
    deviation = {}
    for name, attrs, dname, _ in csliders:
        nd = nosd.get(ab.NAHKA_TARGET + name, {})
        rows = {}
        for j in new:
            blend = [0.0, 0.0, 0.0]
            for k, w in near[j]:
                d = nd.get(k, zero)
                for c in range(3):
                    blend[c] += w * d[c]
            dev = [nd.get(j, zero)[c] - blend[c] for c in range(3)]
            if any(abs(x) > 1e-7 for x in dev):
                rows[newi[j]] = dev
        if rows:
            deviation[name] = rows
    genital_sets = [(n, a, d, f) for n, a, d, f in nsliders if n not in {c[0] for c in csliders}]
    genital = {}
    for name, attrs, dname, _ in genital_sets:
        diffs = nosd.get(dname, {})
        genital[name] = {'new': {newi[j]: list(v) for j, v in diffs.items() if j in newi},
                         'cbbe': {mapping[j]: list(v) for j, v in diffs.items() if j in mapping}}
    named = sorted(used | {i for t in remove for i in t})
    patch = {
        'format': 1,
        'cbbe': {'set': ab.CBBE_SET, 'shape': ab.SHAPE, 'vertices': cs.count, 'triangles': len(ctris),
                 'desc': cs.desc, 'hash': fingerprint(cs, named), 'named': len(named)},
        'replaced': replaced,
        'remove': remove,
        'bones': nbones,
        'vertices': records,
        'triangles': ntris,
        'near': [[[mapping[k], w] for k, w in near[j]] for j in new],
        'deviation': deviation,
        'genital': genital,
        'sets': [[n, dict(a)] for n, a, d, f in genital_sets],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(patch, separators=(',', ':')).encode()
    OUT.write_bytes(gzip.compress(raw, 9))
    print(f'patch: {len(new)} new vertices, {len(ntris)} new triangles, {len(remove)} CBBE triangles removed, '
          f'{len(replaced)} CBBE vertices replaced; {len(deviation)} CBBE sliders deviate on her vertices, '
          f'{len(genital)} genital sliders; {len(raw) // 1024} KB json, {OUT.stat().st_size // 1024} KB gz -> {OUT}')
    return patch


TEX = OUT.parent / 'tex'
CROP_ALIGN = 64                       # crop edges on a 64-texel grid: every mip reduction down to 64x stays aligned
CROP_MARGIN = 64                      # beyond the padded island, so no reduced block ever mixes in blank texels
RING_SIZES = (512, 1024, 2048, 4096)


def textures():
    """Her three maps cut to the genital island (PNG, lossless), and her crotch-skin means per texture
    size (the colour match needs her skin there, which is NOT part of the island): build/patch/tex/."""
    from PIL import Image
    import genital_texture as gt
    TEX.mkdir(parents=True, exist_ok=True)
    full = 4096
    mask, island, ring, _ = gt.islands(full)
    box = mask.getbbox()
    x0 = max(0, (box[0] - CROP_MARGIN) // CROP_ALIGN * CROP_ALIGN)
    y0 = max(0, (box[1] - CROP_MARGIN) // CROP_ALIGN * CROP_ALIGN)
    x1 = min(full, -(-(box[2] + CROP_MARGIN) // CROP_ALIGN) * CROP_ALIGN)
    y1 = min(full, -(-(box[3] + CROP_MARGIN) // CROP_ALIGN) * CROP_ALIGN)
    rings = {}
    for _, _, nahka_name, kind in gt.MAPS:
        img = Image.open(gt.NAHKA / nahka_name).convert('RGB')
        if img.size != (full, full):
            raise SystemExit(f'{nahka_name}: {img.size}, expected {full}x{full}')
        img.crop((x0, y0, x1, y1)).save(TEX / f'{pathlib.Path(nahka_name).stem}.png', optimize=True)
        if kind != 'normal':
            for size in RING_SIZES:
                small = img.reduce(full // size) if size != full else img
                _, _, r, _ = gt.islands(size)
                means, _ = gt.ring_means(small, r, kind == 'colour')
                rings.setdefault(nahka_name, {})[str(size)] = means
    (TEX / 'crops.json').write_text(json.dumps({'size': full, 'box': [x0, y0, x1, y1], 'ring': rings}, indent=1))
    kb = sum(p.stat().st_size for p in TEX.iterdir()) // 1024
    print(f'textures: her island cut to {x1 - x0}x{y1 - y0} at ({x0},{y0}) of {full}; crotch-skin means for '
          f'{list(RING_SIZES)}; {kb} KB -> {TEX}')


if __name__ == '__main__':
    make()
    textures()
