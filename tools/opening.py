"""The vaginal opening, a little longer toward the mons (the owner's look, 2026-09-24; A-25).

As built, the visible opening ran from about y 0.4 to 1.9 in skin space, the back half of the slit,
near the anus. The owner: "make it slightly bigger ... to cover more space close to the mons ...
slightly noticeable from the front". None of Nahka's sliders does only that: VaginaPenetrate opens
the entrance all round (gaping at 0.5), VaginaSpread parts the outer lips and shortens the hole.

So the opening uses Nahka's own VaginaPenetrate shape, weighted by a smooth step over y from the
hole's middle (1.0, weight 0) to its front half (2.0, weight 1): the front of the opening opens
forward and the back stays where it is.

  - BAKED (0.3 of that shape) is built INTO the base mesh, so every body has it, however it is
    built or morphed.
  - The slider "AnatomyOpening" ("Opening, front" in BodySlide) adds EXTRA on top (0.3 more at
    100%), default 0.

Why baked and not a slider default (it was one, briefly): a default applies wherever a preset does
not name the slider, and so does every tool that turns presets into run-time morphs the way
BodySlide would. Silhouette's generator did exactly that and would have doubled the opening on
every body (its verifier caught it, 2026-09-24). So would a player who builds with zeroed sliders
and applies a BodySlide-saved preset (which names the slider) through LooksMenu. Baked, and a
default of 0, nothing can apply it twice.

It is written for BOTH shapes, CBBE and AnatomyGenitals, as a function of position, so where the two
meet they move together. Proven here, from the positions before baking: the seam moves together;
folds beyond Nahka's own opening are slivers only; the baked mesh and the slider data read back.

    split_genitals.py calls add() on the set it has just written; a set already baked is refused.
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
BAKED = 0.3                    # of VaginaPenetrate at weight 1, built into the base: the owner's amount
EXTRA = 0.3                    # the slider at 100% adds this much more
DEFAULT = 0                    # percent: the base already carries the opening
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


def displacement(pen, y, amount):
    """The opening's move of one vertex: `amount` of its VaginaPenetrate diff, weighted by where it
    sat BEFORE any baking (y)."""
    w = weight(y)
    return tuple(c * amount * w for c in pen)


def half_step(x):
    """Spacing of half floats around x (compare_builds.half_step)."""
    a = abs(x)
    if a < 2 ** -14:
        return 2 ** -24
    return 2 ** (math.floor(math.log2(a)) - 10)


def normal(a, b, c):
    u = [b[k] - a[k] for k in range(3)]
    v = [c[k] - a[k] for k in range(3)]
    return (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])


def add(project):
    project = pathlib.Path(project)
    shape_dir = project / 'ShapeData' / FOLDER
    nif_path = shape_dir / f'{FOLDER}.nif'
    body = nif.Nif(nif_path)
    data = osd.read(shape_dir / f'{FOLDER}.osd')
    if any(k.endswith(SLIDER) for k in data):
        raise SystemExit(f'FAIL - {shape_dir} already carries {SLIDER}: its base is baked already. Run '
                         f'split_genitals for a fresh set instead of baking twice.')
    shapes = {s.name: s for s in body.shapes()}
    problems, positions, baked, extra = [], {}, {}, {}
    for name in SHAPES:
        ps = shapes[name].positions()
        positions[name] = ps
        b, e = {}, {}
        for i, d in data.get(name + SOURCE, {}).items():
            if weight(ps[i][1]) > 0.0:
                b[i] = displacement(d, ps[i][1], BAKED)
                e[i] = displacement(d, ps[i][1], EXTRA)
        baked[name], extra[name + SLIDER] = b, e
    # the seam: a genital vertex and the body vertex at the same place must move the same way
    by_pos = {}
    for i, p in enumerate(positions['CBBE']):
        by_pos.setdefault(tuple(round(c, 5) for c in p), []).append(i)
    seam = mismatched = 0
    for j, p in enumerate(positions['AnatomyGenitals']):
        for i in by_pos.get(tuple(round(c, 5) for c in p), []):
            seam += 1
            a = baked['CBBE'].get(i, (0.0, 0.0, 0.0))
            b = baked['AnatomyGenitals'].get(j, (0.0, 0.0, 0.0))
            if max(abs(a[k] - b[k]) for k in range(3)) > 1e-6:
                mismatched += 1
    if mismatched:
        problems.append(f'{mismatched} of {seam} seam vertices would move differently in the two shapes')
    # Folds. Nahka's own opening turns tiny triangles on the inner lip edge over as it rolls outward
    # (VaginaPenetrate at 0.3: 5, at 0.6: 16, at 1.0: 44, measured 2026-09-24). So the bar is: as built
    # and with the slider at 100%, every triangle ours turns over that hers at the same strength does
    # not must be a sliver (under SLIVER square units, about 0.4 mm2), too small to be seen.
    moved_tris, found = 0, {}
    for label, total in (('as built', BAKED), ('slider 100%', BAKED + EXTRA)):
        ours_only, big = 0, []
        for name in SHAPES:
            ps, pen = positions[name], data.get(name + SOURCE, {})
            ours = {i: displacement(d, ps[i][1], total) for i, d in pen.items() if weight(ps[i][1]) > 0.0}
            for a, b, c in shapes[name].triangles():
                if not (a in ours or b in ours or c in ours):
                    continue
                moved_tris += label == 'as built'
                n0 = normal(ps[a], ps[b], ps[c])

                def turned(field, scale):
                    q = [tuple(ps[v][k] + scale * field.get(v, (0.0, 0.0, 0.0))[k] for k in range(3)) for v in (a, b, c)]
                    n1 = normal(*q)
                    return sum(n0[k] * n1[k] for k in range(3)) <= 0

                if turned(ours, 1.0) and not turned(pen, total):
                    ours_only += 1
                    area = 0.5 * math.sqrt(sum(x * x for x in n0))
                    if area >= SLIVER:
                        big.append((name, round(area, 4)))
        found[label] = ours_only
        if big:
            problems.append(f'{label}: {len(big)} triangle(s) bigger than a sliver turn over where Nahka\'s '
                            f'own opening does not: {big[:4]}')
    # bake: the base mesh carries the opening
    for name in SHAPES:
        s, ps = shapes[name], positions[name]
        for i, d in baked[name].items():
            s.set_position(i, tuple(ps[i][k] + d[k] for k in range(3)))
    body.save(nif_path)
    # read back: a shape stored in half floats (both are, in CBBE's ShapeData) rounds each baked
    # coordinate to the nearest half, as BodySlide's own build does; nothing may be off by more
    check = {s.name: s for s in nif.Nif(nif_path).shapes()}
    worst_bake, off_bake = 0.0, 0
    for name in SHAPES:
        now, ps = check[name].positions(), positions[name]
        for i in range(len(ps)):
            want = tuple(ps[i][k] + baked[name].get(i, (0.0, 0.0, 0.0))[k] for k in range(3))
            for k in range(3):
                err = abs(now[i][k] - want[k])
                tol = 1e-5 if check[name].full else half_step(want[k]) / 2 * 1.01
                worst_bake = max(worst_bake, err)
                off_bake += err > tol
    if off_bake:
        problems.append(f'{off_bake} baked coordinate(s) read back off by more than their storage '
                        f'rounding (worst {worst_bake:.6f})')
    # the slider: the extra opening, on both shapes
    osd.write(shape_dir / f'{FOLDER}.osd', {**data, **extra})
    back = osd.read(shape_dir / f'{FOLDER}.osd')
    for k, blk in extra.items():
        want = {i: tuple(v) for i, v in blk.items() if tuple(v) != (0.0, 0.0, 0.0)}
        got = back.get(k, {})
        if set(got) != set(want) or any(max(abs(got[i][c] - want[i][c]) for c in range(3)) > 1e-6 for i in want):
            problems.append(f'{k} does not read back')
    osp_path = project / 'SliderSets' / f'{FOLDER}.osp'
    osp = osp_path.read_text(encoding='utf-8')
    osp = re.sub(rf'\s*<Slider name="{SLIDER}"[^>]*>.*?</Slider>', '', osp, flags=re.S)
    lines = ''.join(f'\n            <Data name="{name}{SLIDER}" target="{name}" local="true">'
                    f'{FOLDER}.osd\\{name}{SLIDER}</Data>' for name in SHAPES if extra[name + SLIDER])
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
    moved = ', '.join(f'{n} {len(baked[n])}' for n in SHAPES)
    biggest = max((math.sqrt(sum(c * c for c in d)) for n in SHAPES for d in baked[n].values()), default=0.0)
    print(f'4. opening baked into the base ({BAKED} of {SOURCE}, weighted): {moved} vertices, at most '
          f'{biggest:.2f} units; slider {SLIDER} adds up to {EXTRA} more (default {DEFAULT}%); '
          f'{seam - mismatched} of {seam} seam vertices move together; of {moved_tris} moved triangles, '
          f'{found["as built"]} as built and {found["slider 100%"]} at 100% turn over where Nahka\'s opening '
          f'does not (allowed only as slivers under {SLIVER})')
    if problems:
        raise SystemExit('FAIL - ' + '; '.join(problems))
    return baked


if __name__ == '__main__':
    print(__doc__)
    sys.exit(0)
