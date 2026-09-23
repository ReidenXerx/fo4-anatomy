"""Prove the aligned body project is what align_body.py claims (decision A-4). Reads the WRITTEN files.

  1. Every shared vertex holds CBBE's record exactly: position, UV, normal, tangent, and the same
     weights on the same bones by name.
  2. Every CBBE slider moves every shared vertex exactly as CBBE's slider data does.
  3. No vertex leans on a bone today's CBBE does not use (the 2017 cloth-bone hacks).
  4. The openings are CBBE's three (neck, wrists) plus the vulva: nothing torn open anywhere else.
  5. The genital sliders move only the genital region.

It must FAIL on a broken project; `--plant` corrupts one thing in a copy to prove each check can.

    python tools/verify_body.py
    python tools/verify_body.py --plant weight|position|slider|bone
"""
import argparse
import json
import math
import pathlib
import shutil
import struct
import sys
import tempfile

import align_body as ab
import nif
import osd


def check(project, data_root, problems):
    m = json.loads((project / 'mapping.json').read_text())
    mapping = {int(j): i for j, i in m['output_to_cbbe'].items()}
    bs = data_root / 'Tools/BodySlide'
    cset, csliders = ab.read_set(bs / 'SliderSets/CBBE.osp', ab.CBBE_SET)
    cbbe = nif.Nif(bs / 'ShapeData' / cset.findtext('DataFolder') / cset.findtext('SourceFile'))
    cosd = osd.read(bs / 'ShapeData' / cset.findtext('DataFolder') / csliders[0][3])
    out = nif.Nif(project / 'ShapeData' / ab.DATA_FOLDER / f'{ab.DATA_FOLDER}.nif')
    oosd = osd.read(project / 'ShapeData' / ab.DATA_FOLDER / f'{ab.DATA_FOLDER}.osd')
    cs, os_ = cbbe.shape(ab.SHAPE), out.shape(ab.SHAPE)
    cb, _ = cbbe.skin(cs)
    ob, _ = out.skin(os_)

    # 1. records
    bad_rec = bad_w = 0
    for j, i in mapping.items():
        a, b = cs.record(i), os_.record(j)
        if a[:cs.skin_at] != b[:os_.skin_at]:
            bad_rec += 1
        wa = sorted((cb[s], round(w, 6)) for s, w in cs.skin_weights(i))
        wb = sorted((ob[s], round(w, 6)) for s, w in os_.skin_weights(j))
        if wa != wb:
            bad_w += 1
    print(f'1. shared vertices: {len(mapping)}; records differing from CBBE {bad_rec}; weights differing {bad_w}')
    if bad_rec or bad_w:
        problems.append(f'{bad_rec} shared records and {bad_w} shared weight sets are not CBBE\'s')

    # 2. slider data on shared vertices
    zero = (0.0, 0.0, 0.0)
    wrong = {}
    for name, _, dname, _ in csliders:
        cd, od = cosd.get(dname, {}), oosd.get(ab.TARGET + name)
        if od is None:
            wrong[name] = 'missing'
            continue
        n = sum(1 for j, i in mapping.items() if cd.get(i, zero) != od.get(j, zero))
        if n:
            wrong[name] = n
    print(f'2. CBBE sliders: {len(csliders)}; differing on shared vertices: {wrong or "none"}')
    if wrong:
        problems.append(f'CBBE sliders that do not move shared vertices exactly as CBBE: {wrong}')

    # 3. bones
    used = {ob[s] for j in range(os_.count) for s, _ in os_.skin_weights(j)}
    foreign = sorted(used - set(cb) - set(b for b in ob if b and b.startswith(('Vagina', 'Anus', 'Penis'))))
    print(f'3. bones carrying weight: {len(used)}; not in CBBE Body Physics: {foreign or "none"}')
    if foreign:
        problems.append(f'weights on bones CBBE does not use: {foreign}')

    # 4. openings
    loops = nif.openings(os_.positions(), os_.triangles())
    print(f'4. openings: {len(loops)}')
    unexpected = []
    for n, c, span in loops:
        where = ('neck' if c[2] > -15 and abs(c[0]) < 3 else 'wrist' if abs(abs(c[0]) - 36.2) < 1 and abs(c[2] + 35.9) < 1
                 else 'vulva' if abs(c[0]) < 1 and -57 < c[2] < -53 and -1 < c[1] < 6 else None)
        print(f'   {where or "UNEXPECTED":10} {n:4} vertices at ({c[0]:.2f}, {c[1]:.2f}, {c[2]:.2f})')
        if where is None:
            unexpected.append(c)
    if unexpected:
        problems.append(f'{len(unexpected)} openings where the body should be closed')

    # 6. cloth physics: today's CBBE blob, not Nahka's 2017 one
    cb, ob = cbbe.extra_block('BSClothExtraData'), out.extra_block('BSClothExtraData')
    same = bool(cb and ob and cbbe.b[cb[0] + 4:cb[0] + cb[1]] == out.b[ob[0] + 4:ob[0] + ob[1]])
    print(f'6. cloth physics (BSClothExtraData) identical to today\'s CBBE: {same}')
    if cb and not same:
        problems.append('cloth physics data is not today\'s CBBE')

    # 5. genital sliders stay in the crotch
    pos = os_.positions()
    stray = {}
    for g in m['genital_sliders']:
        d = oosd.get(ab.TARGET + g, {})
        far = [j for j, v in d.items() if any(abs(x) > 1e-4 for x in v)
               and not (abs(pos[j][0]) < 12 and -75 < pos[j][2] < -40)]
        if far:
            stray[g] = len(far)
    print(f'5. genital sliders moving vertices outside the crotch: {stray or "none"}')
    if stray:
        problems.append(f'genital sliders move vertices outside the crotch: {stray}')


def plant(project, kind):
    """Copy the project and corrupt ONE thing, so each check is proven able to fail."""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='anatomy-plant-'))
    shutil.copytree(project, tmp, dirs_exist_ok=True)
    m = json.loads((tmp / 'mapping.json').read_text())
    j = int(next(iter(m['output_to_cbbe'])))
    path = tmp / 'ShapeData' / ab.DATA_FOLDER / f'{ab.DATA_FOLDER}.nif'
    n = nif.Nif(path)
    s = n.shape(ab.SHAPE)
    if kind == 'position':
        p = s.position(j)
        s.set_position(j, (p[0] + 0.5, p[1], p[2]))
    elif kind in ('weight', 'bone'):
        bones, _ = n.skin(s)
        target = bones.index('CLOTH_Bone_LefTtools') if kind == 'bone' else 0
        s.set_skin_weights(j, [(target, 1.0)])
    n.save(path)
    if kind == 'slider':
        opath = tmp / 'ShapeData' / ab.DATA_FOLDER / f'{ab.DATA_FOLDER}.osd'
        d = osd.read(opath)
        d[ab.TARGET + 'Breasts'][j] = (9.0, 9.0, 9.0)
        osd.write(opath, d)
    return tmp


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--project', type=pathlib.Path, default=ab.OUT)
    ap.add_argument('--data', type=pathlib.Path, default=ab.DEFAULT_DATA)
    ap.add_argument('--plant', choices=('weight', 'position', 'slider', 'bone'))
    args = ap.parse_args()
    project = plant(args.project, args.plant) if args.plant else args.project
    problems = []
    check(project, args.data, problems)
    if problems:
        print('\nFAIL - ' + '\n       '.join(problems))
        sys.exit(1)
    print('\nPASS - shared skin is CBBE exactly, sliders agree, no stray bones, no stray openings.')


if __name__ == '__main__':
    main()
