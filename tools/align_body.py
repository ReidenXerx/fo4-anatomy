"""Align Nahka's CBBEVaginaMorphs (physics variant) to today's CBBE Body Physics (decision A-4).

Nahka's body is CBBE plus a real slit and two canals, conformed in 2017. Today's CBBE has moved on:
the feet were reshaped (up to 0.6 units), FeetFeminine was added, and slider data around the hips
and buttocks drifts by up to 0.9 units (AppleCheeks). This tool keeps Nahka's topology and vertex
order, so her twelve genital sliders stay valid. It rebuilds everything else from today's CBBE:

  SHARED vertex (same UV, within 0.7 units of a CBBE vertex): CBBE's record byte for byte
      (position, UV, normal, tangent, weights), with weights re-pointed from CBBE's bone slots to
      the output's, plus CBBE's diff for every CBBE slider.
  NEW or CHANGED vertex (the vulva, the canals, the anus): Nahka's record and Nahka's diff, plus a
      correction so it meets the shared skin without a seam. The correction is the
      inverse-distance-weighted CBBE-minus-Nahka difference of its nearest shared vertices, so a
      slider moves the new geometry the way it moves the skin around it. FeetFeminine has no Nahka
      data, so there it is pure interpolation. A weight on a bone today's CBBE does not use
      (2017's cloth-bone physics hacks) is replaced the same way, from the neighbours' weights.

Output (build/project, never committed):
  ShapeData/AnatomyBody/AnatomyBody.nif + .osd, SliderSets/AnatomyBody.osp

    python tools/align_body.py            # extract inputs if needed, align, write, report
"""
import argparse
import collections
import math
import pathlib
import re
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape, quoteattr

import nif
import osd

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_DATA = pathlib.Path(r'D:\GOGGames\Fallout 4 GOTY\Data')
NAHKA_RAR = ROOT / 'inputs/CBBEVagMorphs.rar'
NAHKA_DIR = ROOT / 'build/nahka'
OUT = ROOT / 'build/project'

CBBE_SET = 'CBBE Body Physics'
NAHKA_SET = 'CBBEVaginaMorphsPhysics'
NAHKA_TARGET = 'CBBE2'

SET_NAME = 'Anatomy Body Physics'          # working name (A-5)
DATA_FOLDER = 'AnatomyBody'
TARGET = 'CBBE'
SHAPE = 'CBBE'

UV_DIGITS = 4
MATCH_RADIUS = 0.7
NEIGHBOURS = 8


# --------------------------------------------------------------------------
# inputs
# --------------------------------------------------------------------------

def extract_nahka():
    """build/nahka/Data/Tools/BodySlide/... from inputs/CBBEVagMorphs.rar (only the BodySlide files)."""
    marker = NAHKA_DIR / 'Data/Tools/BodySlide/SliderSets' / f'{NAHKA_SET}.osp'
    if marker.exists():
        return
    if not NAHKA_RAR.exists():
        raise SystemExit(f'missing {NAHKA_RAR}: the CBBEVagMorphs.rar Nahka published (Dropbox link on Nexus 98984)')
    NAHKA_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(['7z', 'x', '-y', '-sccUTF-8', f'-o{NAHKA_DIR}', str(NAHKA_RAR), r'Data\Tools\BodySlide\*', '-r'],
                   check=True, stdout=subprocess.DEVNULL)
    if not marker.exists():
        raise SystemExit(f'{NAHKA_RAR.name} did not contain {marker.relative_to(NAHKA_DIR)}')


def read_set(osp_path, set_name):
    """(set element, [(slider name, attributes, data name, osd file)]) for one <SliderSet>."""
    root = ET.parse(osp_path).getroot()
    for s in root.iter('SliderSet'):
        if s.get('name') == set_name:
            sliders = []
            for sl in s.iter('Slider'):
                d = sl.find('Data')
                file_part, _, data_name = (d.text or '').replace('/', '\\').rpartition('\\')
                sliders.append((sl.get('name'), dict(sl.attrib), d.get('name'), file_part))
            return s, sliders
    raise SystemExit(f'{osp_path}: no slider set {set_name!r}')


# --------------------------------------------------------------------------
# geometry
# --------------------------------------------------------------------------

class Grid:
    """Nearest-neighbour lookup over a fixed point set."""

    def __init__(self, points, ids, cell=1.0):
        self.cell, self.points = cell, points
        self.cells = collections.defaultdict(list)
        for i in ids:
            self.cells[self.key(points[i])].append(i)

    def key(self, p):
        return tuple(int(math.floor(c / self.cell)) for c in p)

    def nearest(self, p, k):
        cx, cy, cz = self.key(p)
        r = 1
        while True:
            found = []
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    for dz in range(-r, r + 1):
                        found.extend(self.cells.get((cx + dx, cy + dy, cz + dz), ()))
            if len(found) >= k or r > 40:
                found.sort(key=lambda i: math.dist(self.points[i], p))
                # a point further than r cells may still be closer than the k-th found; widen once
                if len(found) >= k and math.dist(self.points[found[k - 1]], p) <= r * self.cell:
                    return found[:k]
                if r > 40:
                    return found[:k]
            r += 1


def match(cs, ns):
    """{Nahka vertex: CBBE vertex}.

    First pass: same UV (rounded) and the nearest unused position within MATCH_RADIUS. That is
    not enough where CBBE has several vertices with the same UV close together (the feet: 225 on
    the left foot) and the feet moved by up to 0.6 units since 2017. The nearest position then
    picks the wrong twin, and 304 triangles of the left foot came out as non-CBBE triangles.

    Second pass: TOPOLOGY decides between twins. A pairing is scored by how many of the Nahka
    vertex's triangles map onto CBBE triangles; a swap with the twin's current owner is kept when
    it raises the total. Repeated until nothing improves."""
    cv, nv = cs.positions(), ns.positions()
    by_uv = collections.defaultdict(list)
    for i in range(cs.count):
        u = cs.uv(i)
        by_uv[(round(u[0], UV_DIGITS), round(u[1], UV_DIGITS))].append(i)
    mapping, used, twins = {}, set(), {}
    for j in range(ns.count):
        u = ns.uv(j)
        same = [i for i in by_uv.get((round(u[0], UV_DIGITS), round(u[1], UV_DIGITS)), ())
                if math.dist(cv[i], nv[j]) < MATCH_RADIUS]
        twins[j] = same
        free = [i for i in same if i not in used]
        best = min(free, key=lambda i: math.dist(cv[i], nv[j]), default=None)
        if best is not None:
            mapping[j] = best
            used.add(best)

    ctris = {frozenset(t) for t in cs.triangles()}
    ntris = ns.triangles()
    around = collections.defaultdict(list)
    for t in ntris:
        for v in t:
            around[v].append(t)
    owner = {i: j for j, i in mapping.items()}

    def score(j):
        s = 0
        for t in around[j]:
            if all(v in mapping for v in t):
                s += frozenset(mapping[v] for v in t) in ctris
        return s

    for _ in range(50):
        wrong = {v for t in ntris if all(x in mapping for x in t)
                 and frozenset(mapping[x] for x in t) not in ctris for v in t}
        improved = False
        for j in sorted(wrong):
            cur = mapping[j]
            for i in twins[j]:
                if i == cur:
                    continue
                other = owner.get(i)
                before = score(j) + (score(other) if other is not None else 0)
                mapping[j] = i
                if other is not None:
                    mapping[other] = cur
                after = score(j) + (score(other) if other is not None else 0)
                if after > before:
                    owner[i] = j
                    if other is not None:
                        owner[cur] = other
                    else:
                        del owner[cur]
                    cur = i
                    improved = True
                else:
                    mapping[j] = cur
                    if other is not None:
                        mapping[other] = i
        if not improved:
            break
    return mapping


def idw(p, points, ids):
    """Inverse-square-distance weights of `ids` for point p (an exact hit takes everything)."""
    out = []
    for i in ids:
        d = math.dist(points[i], p)
        if d < 1e-9:
            return [(i, 1.0)]
        out.append((i, 1.0 / (d * d)))
    total = sum(w for _, w in out)
    return [(i, w / total) for i, w in out]


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--data', type=pathlib.Path, default=DEFAULT_DATA)
    ap.add_argument('--out', type=pathlib.Path, default=OUT)
    args = ap.parse_args()

    extract_nahka()
    bs = args.data / 'Tools/BodySlide'
    nbs = NAHKA_DIR / 'Data/Tools/BodySlide'
    cset, csliders = read_set(bs / 'SliderSets/CBBE.osp', CBBE_SET)
    nset, nsliders = read_set(nbs / f'SliderSets/{NAHKA_SET}.osp', NAHKA_SET)
    cbbe_nif = nif.Nif(bs / 'ShapeData' / cset.findtext('DataFolder') / cset.findtext('SourceFile'))
    nahka_nif = nif.Nif(nbs / 'ShapeData' / nset.findtext('DataFolder') / nset.findtext('SourceFile'))
    cosd = osd.read(bs / 'ShapeData' / cset.findtext('DataFolder') / csliders[0][3])
    nosd = osd.read(nbs / 'ShapeData' / nset.findtext('DataFolder') / nsliders[0][3])
    cs, ns = cbbe_nif.shape(SHAPE), nahka_nif.shape(SHAPE)
    if cs.desc != ns.desc:
        raise SystemExit(f'vertex layouts differ ({cs.desc:#x} vs {ns.desc:#x}): records cannot be copied')
    print(f'CBBE     {cset.get("name")!r}: {cs.count} vertices, {len(csliders)} sliders')
    print(f'Nahka    {nset.get("name")!r}: {ns.count} vertices, {len(nsliders)} sliders')

    # ---- vertex correspondence, checked against the triangles
    mapping = match(cs, ns)
    shared, new = sorted(mapping), [j for j in range(ns.count) if j not in mapping]
    ctris = {frozenset(t) for t in cs.triangles()}
    cedges = {frozenset(e) for t in cs.triangles() for e in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0]))}
    npos = ns.positions()
    new_grid = Grid(npos, new)
    whole = agree = seam = 0
    for t in ns.triangles():
        if all(v in mapping for v in t):
            whole += 1
            m = [mapping[v] for v in t]
            if frozenset(m) in ctris:
                agree += 1
                continue
            # Nahka re-triangulated the skin around her cut: a flipped diagonal (two of three edges
            # are CBBE's) next to her new geometry. Measured: 8, all at the top of the vulva.
            flip = sum(frozenset(p) in cedges for p in ((m[0], m[1]), (m[1], m[2]), (m[2], m[0]))) == 2
            centre = tuple(sum(npos[v][a] for v in t) / 3 for a in range(3))
            if flip and math.dist(centre, npos[new_grid.nearest(centre, 1)[0]]) < 1.0:
                seam += 1
    print(f'shared   {len(shared)} vertices (UV + position); new or changed {len(new)}; '
          f'CBBE vertices replaced {cs.count - len(mapping)}')
    print(f'         triangles made only of shared vertices: {whole}; CBBE triangles {agree}; '
          f'Nahka\'s own at the edge of her geometry {seam}')
    if agree + seam != whole:
        raise SystemExit(f'{whole - agree - seam} shared triangles away from the new geometry are not CBBE '
                         f'triangles: the correspondence is wrong')

    # ---- bones: the output keeps Nahka's slot table; CBBE slots are re-pointed by name
    cbones, _ = cbbe_nif.skin(cs)
    nbones, _ = nahka_nif.skin(ns)
    missing = [b for b in cbones if b not in nbones]
    if missing:
        raise SystemExit(f'CBBE bones missing from Nahka\'s skin: {missing}')
    slot = {i: nbones.index(b) for i, b in enumerate(cbones)}
    foreign = {k for k, b in enumerate(nbones) if b not in cbones}

    out = nahka_nif                      # edited in place, saved under the new name
    cv, nv = cs.positions(), ns.positions()
    for j, i in mapping.items():
        rec = bytearray(cs.record(i))
        idx = struct.unpack_from('<4B', rec, cs.skin_at + 8)
        wts = struct.unpack_from('<4e', rec, cs.skin_at)
        struct.pack_into('<4B', rec, cs.skin_at + 8, *(slot[s] if w > 0 else 0 for s, w in zip(idx, wts)))
        ns.set_record(j, bytes(rec))

    nv_now = ns.positions()                            # shared vertices now sit exactly on CBBE's
    grid = Grid(nv_now, shared)
    near = {j: idw(nv_now[j], nv_now, grid.nearest(nv_now[j], NEIGHBOURS)) for j in new}

    reweighted = 0
    for j in new:
        ws = ns.skin_weights(j)
        if not any(s in foreign for s, _ in ws):
            continue
        acc = collections.defaultdict(float)
        for k, w in near[j]:
            for s, v in ns.skin_weights(k):
                acc[s] += w * v
        ns.set_skin_weights(j, sorted(acc.items(), key=lambda sv: -sv[1])[:4])
        reweighted += 1
    left = sum(1 for j in range(ns.count) for s, _ in ns.skin_weights(j) if s in foreign)
    print(f'weights  {len(mapping)} copied from CBBE; {reweighted} new vertices re-weighted from their neighbours '
          f'(they leaned on 2017 cloth bones); vertices still on those bones: {left}')

    # ---- slider data
    data = {}
    worst = {}
    for name, attrs, dname, _ in csliders:
        cd = cosd.get(dname, {})
        nd = nosd.get(NAHKA_TARGET + name, {})
        diffs = {j: cd[i] for j, i in mapping.items() if i in cd}
        zero = (0.0, 0.0, 0.0)
        for j in new:
            base = nd.get(j, zero)
            corr = [0.0, 0.0, 0.0]
            for k, w in near[j]:
                a, b = cd.get(mapping[k], zero), nd.get(k, zero)
                for c in range(3):
                    corr[c] += w * (a[c] - b[c])
            v = tuple(base[c] + corr[c] for c in range(3))
            if v != zero:
                diffs[j] = v
            worst[name] = max(worst.get(name, 0.0), math.sqrt(sum(x * x for x in corr)))
        data[TARGET + name] = diffs
    genital = [(n, a, d, f) for n, a, d, f in nsliders if n not in {c[0] for c in csliders}]
    for name, attrs, dname, _ in genital:
        data[TARGET + name] = dict(nosd.get(dname, {}))
    big = sorted(((w, n) for n, w in worst.items() if w > 0.05), reverse=True)
    print(f'sliders  {len(csliders)} from CBBE (shared vertices exact), {len(genital)} genital from Nahka: '
          f'{", ".join(n for n, *_ in genital)}')
    print(f'         seam corrections on new vertices above 0.05 units: '
          + (', '.join(f'{n} {w:.2f}' for w, n in big[:8]) or 'none'))

    # ---- write the project
    shape_dir = args.out / 'ShapeData' / DATA_FOLDER
    shape_dir.mkdir(parents=True, exist_ok=True)
    (args.out / 'SliderSets').mkdir(parents=True, exist_ok=True)
    out.save(shape_dir / f'{DATA_FOLDER}.nif')
    osd.write(shape_dir / f'{DATA_FOLDER}.osd', data)
    write_osp(args.out / 'SliderSets' / f'{DATA_FOLDER}.osp', cset, csliders, genital)
    import json
    (args.out / 'mapping.json').write_text(json.dumps({'output_to_cbbe': {str(j): i for j, i in mapping.items()},
                                                       'cbbe_slider_data': {n: d for n, _, d, _ in csliders},
                                                       'genital_sliders': [n for n, *_ in genital]}))
    print(f'wrote    {shape_dir / (DATA_FOLDER + ".nif")}, .osd, and SliderSets/{DATA_FOLDER}.osp')


def write_osp(path, cset, csliders, genital):
    L = ['<?xml version="1.0" encoding="UTF-8"?>', '<SliderSetInfo version="1">',
         f'    <SliderSet name={quoteattr(SET_NAME)}>',
         f'        <DataFolder>{DATA_FOLDER}</DataFolder>',
         f'        <SourceFile>{DATA_FOLDER}.nif</SourceFile>',
         f'        <OutputPath>{escape(cset.findtext("OutputPath"))}</OutputPath>',
         f'        <OutputFile GenWeights="false">{escape(cset.findtext("OutputFile"))}</OutputFile>',
         f'        <Shape target="{TARGET}">{SHAPE}</Shape>']
    for name, attrs, _, _ in list(csliders) + list(genital):
        a = ' '.join(f'{k}={quoteattr(v)}' for k, v in attrs.items())
        L.append(f'        <Slider {a}>')
        L.append(f'            <Data name={quoteattr(TARGET + name)} target="{TARGET}" local="true">'
                 f'{escape(DATA_FOLDER + ".osd")}\\{escape(TARGET + name)}</Data>')
        L.append('        </Slider>')
    L += ['    </SliderSet>', '</SliderSetInfo>', '']
    pathlib.Path(path).write_text('\n'.join(L), encoding='utf-8')


if __name__ == '__main__':
    main()
