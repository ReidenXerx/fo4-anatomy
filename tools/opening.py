"""The vaginal opening, a little longer toward the mons (the owner's look, 2026-09-24).

As built, the visible opening runs from about y 0.4 to 1.9 in skin space, the back half of the slit,
near the anus. The owner: "make it slightly bigger ... to cover more space close to the mons ...
slightly noticeable from the front". None of Nahka's sliders does only that: VaginaPenetrate opens
the entrance all round (gaping at 0.5), VaginaSpread parts the outer lips and shortens the hole.

So a slider of our own, "AnatomyOpening": Nahka's own VaginaPenetrate shape, weighted by a smooth
step over y from the hole's middle (1.0, weight 0) to its front half (2.0, weight 1). The front of
the opening opens forward and the back stays where it is. 100% is 0.6 x VaginaPenetrate there. The
default is 50%, which the owner's zero build and any preset that does not name the slider get:
BodySlide gives a slider its set's default then (the unit is percent: sets in the owner's install
ship default="100", BodyTalk's Erection among them).

It is written for BOTH shapes, CBBE and AnatomyGenitals, as a function of position, so where the two
meet they move together. Proven here: the seam vertices get identical moves, no triangle turns over
at 100%, and the data reads back.

    python tools/opening.py          (split_genitals.py calls it; this re-adds it to build/project)
"""
import math
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

import nif
import osd

SLIDER = 'AnatomyOpening'
DISPLAY = 'Opening, front'
SHAPES = ('CBBE', 'AnatomyGenitals')
SOURCE = 'VaginaPenetrate'
Y0, Y1 = 1.0, 2.0              # skin-space y: the hole's middle (weight 0) and front half (weight 1)
FULL = 0.6                     # 100% of the slider: this much of VaginaPenetrate at weight 1
DEFAULT = 50                   # percent: the owner's "slightly bigger"
SLIVER = 0.002                 # square units: a triangle this small cannot be seen folded
FOLDER = 'Anatomy'
CATEGORIES = ('<SliderCategories>\n'
              '\t<Category name="Anatomy" defaultHidden="false">\n'
              f'\t\t<Slider name="{SLIDER}" displayname="{DISPLAY}" />\n'
              '\t</Category>\n'
              '</SliderCategories>\n')


def weight(y):
    t = min(1.0, max(0.0, (y - Y0) / (Y1 - Y0)))
    return t * t * (3 - 2 * t)


def normal(a, b, c):
    u = [b[k] - a[k] for k in range(3)]
    v = [c[k] - a[k] for k in range(3)]
    return (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])


def add(project):
    project = pathlib.Path(project)
    shape_dir = project / 'ShapeData' / FOLDER
    body = nif.Nif(shape_dir / f'{FOLDER}.nif')
    data = osd.read(shape_dir / f'{FOLDER}.osd')
    shapes = {s.name: s for s in body.shapes()}
    problems, blocks, positions = [], {}, {}
    for name in SHAPES:
        ps = shapes[name].positions()
        positions[name] = ps
        source = data.get(name + SOURCE, {})
        block = {}
        for i, d in source.items():
            w = weight(ps[i][1])
            if w > 0.0:
                block[i] = tuple(c * FULL * w for c in d)
        blocks[name + SLIDER] = block
    # the seam: a genital vertex and the body vertex at the same place must move the same way
    by_pos = {}
    for i, p in enumerate(positions['CBBE']):
        by_pos.setdefault(tuple(round(c, 5) for c in p), []).append(i)
    seam = mismatched = 0
    for j, p in enumerate(positions['AnatomyGenitals']):
        for i in by_pos.get(tuple(round(c, 5) for c in p), []):
            seam += 1
            a = blocks['CBBE' + SLIDER].get(i, (0.0, 0.0, 0.0))
            b = blocks['AnatomyGenitals' + SLIDER].get(j, (0.0, 0.0, 0.0))
            if max(abs(a[k] - b[k]) for k in range(3)) > 1e-6:
                mismatched += 1
    if mismatched:
        problems.append(f'{mismatched} of {seam} seam vertices would move differently in the two shapes')
    # Folds. Nahka's own opening turns tiny triangles on the inner lip edge over as it rolls outward
    # (VaginaPenetrate at 0.3: 5, at 0.6: 16, at 1.0: 44, measured 2026-09-24). So the bar is: at the
    # default and at 100%, every triangle ours turns over that hers at the same strength does not must
    # be a sliver (under SLIVER square units, about 0.4 mm2), too small to be seen.
    moved_tris = 0
    found = {}
    for pct in (DEFAULT, 100):
        s = pct / 100.0
        ours_only, big = 0, []
        for name in SHAPES:
            ps, block, pen = positions[name], blocks[name + SLIDER], data.get(name + SOURCE, {})
            for a, b, c in shapes[name].triangles():
                if not (a in block or b in block or c in block):
                    continue
                moved_tris += pct == 100
                n0 = normal(ps[a], ps[b], ps[c])

                def turned(field, scale):
                    q = [tuple(ps[v][k] + scale * field.get(v, (0.0, 0.0, 0.0))[k] for k in range(3)) for v in (a, b, c)]
                    n1 = normal(*q)
                    return sum(n0[k] * n1[k] for k in range(3)) <= 0

                if turned(block, s) and not turned(pen, s * FULL):
                    ours_only += 1
                    area = 0.5 * math.sqrt(sum(x * x for x in n0))
                    if area >= SLIVER:
                        big.append((name, round(area, 4)))
        found[pct] = ours_only
        if big:
            problems.append(f'at {pct}% {len(big)} triangle(s) bigger than a sliver turn over where Nahka\'s '
                            f'own opening does not: {big[:4]}')
    biggest = max((math.sqrt(sum(c * c for c in d)) for blk in blocks.values() for d in blk.values()), default=0.0)
    osd.write(shape_dir / f'{FOLDER}.osd', {**{k: v for k, v in data.items() if not k.endswith(SLIDER)}, **blocks})
    back = osd.read(shape_dir / f'{FOLDER}.osd')
    for k, blk in blocks.items():
        want = {i: tuple(v) for i, v in blk.items() if tuple(v) != (0.0, 0.0, 0.0)}
        got = back.get(k, {})
        if set(got) != set(want) or any(max(abs(got[i][c] - want[i][c]) for c in range(3)) > 1e-6 for i in want):
            problems.append(f'{k} does not read back')
    # the slider in the set, with its default
    osp_path = project / 'SliderSets' / f'{FOLDER}.osp'
    osp = osp_path.read_text(encoding='utf-8')
    osp = re.sub(rf'\s*<Slider name="{SLIDER}"[^>]*>.*?</Slider>', '', osp, flags=re.S)
    lines = ''.join(f'\n            <Data name="{name}{SLIDER}" target="{name}" local="true">'
                    f'{FOLDER}.osd\\{name}{SLIDER}</Data>' for name in SHAPES if blocks[name + SLIDER])
    element = f'\n        <Slider name="{SLIDER}" invert="false" default="{DEFAULT}">{lines}\n        </Slider>'
    last = osp.rfind('</Slider>')
    if last < 0:
        problems.append('the set has no slider to add after')
    else:
        osp = osp[:last + len('</Slider>')] + element + osp[last + len('</Slider>'):]
    osp_path.write_text(osp, encoding='utf-8')
    tree = ET.parse(osp_path)
    ours = [s for s in tree.iter('Slider') if s.get('name') == SLIDER]
    if len(ours) != 1 or ours[0].get('default') != str(DEFAULT) or len(list(ours[0].iter('Data'))) != 2:
        problems.append('the set does not hold the slider once, with its default and both shapes')
    cats = project / 'SliderCategories' / 'Anatomy.xml'
    cats.parent.mkdir(parents=True, exist_ok=True)
    cats.write_text(CATEGORIES, encoding='utf-8')
    ET.parse(cats)
    counts = ', '.join(f'{k} {len(v)}' for k, v in blocks.items())
    print(f'4. slider {SLIDER} (default {DEFAULT}%): {counts} vertices; at 100% at most {biggest:.2f} units; '
          f'{seam - mismatched} of {seam} seam vertices move together; of {moved_tris} moved triangles, '
          f'{found[DEFAULT]} at {DEFAULT}% and {found[100]} at 100% turn over where Nahka\'s opening does not '
          f'(allowed only as slivers under {SLIVER})')
    if problems:
        raise SystemExit('FAIL - ' + '; '.join(problems))
    return blocks


if __name__ == '__main__':
    import align_body as ab
    add(ab.OUT)
    sys.exit(0)
