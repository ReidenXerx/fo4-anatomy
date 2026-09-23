"""Prove the stage-2 body (tools/zex_bones.py, decision A-6) is what it should be.

  1. Same geometry: vertex count, positions and triangles equal the aligned body's.
  2. Same sliders: every slider diff in the saved .osd equals the aligned body's.
  3. Bones: the 9 animated genital bones and the 5 _CBP_ twins are in the skin, bound where ZeX's
     skeleton puts them (a twin at its animated bone's position); the 2017 cloth bones, weightless, are reported.
  4. The skin outside the mask is untouched: every protected vertex (mask value 1) carries exactly
     the weights it had before.
  5. The genital weights landed on the genitals: which vertices carry them, how strongly, and their
     weighted centres next to their bones.

    python tools/verify_zex.py [--saved build/project/ShapeData/AnatomyBodyZeX]
"""
import argparse
import collections
import json
import math
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

import align_body as ab
import lab
import nif
import osd

ANIM = ['Vagina_00', 'Vagina_L_01', 'Vagina_L_02', 'Vagina_R_01', 'Vagina_R_02', 'Anus_01', 'Anus_02', 'Anus_03', 'Anus_04']
TWIN = {'Vagina_00': 'Vagina_CBP_00', 'Vagina_L_01': 'Vagina_CBP_L_01', 'Vagina_L_02': 'Vagina_CBP_L_02',
        'Vagina_R_01': 'Vagina_CBP_R_01', 'Vagina_R_02': 'Vagina_CBP_R_02'}
ZEX_AT = {'Vagina_00': (0, 4.00, -55.50), 'Vagina_L_01': (0, 2.45, -55.71), 'Vagina_R_01': (0, 2.45, -55.71),
          'Vagina_L_02': (-0.64, 1.09, -55.71), 'Vagina_R_02': (0.53, 1.07, -55.71),
          'Anus_01': (0, -2.98, -54.26), 'Anus_02': (0, -2.53, -54.49), 'Anus_03': (0.10, -2.76, -54.44),
          'Anus_04': (-0.10, -2.76, -54.44)}
CLOTH = ['CLOTH_Bone_LefTtools', 'CLOTH_Bone_RightTools', 'CLOTH_Bone_Tape', 'CLOTH_Bone_Pouch', 'CLOTH_Bone_Googles_03']


def mask_values(path):
    root = ET.parse(path).getroot()
    return {int(v.get('i')): float(v.get('m')) for v in root.iter('V')}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--saved', type=pathlib.Path, default=ab.OUT / 'ShapeData/AnatomyBodyZeX')
    args = ap.parse_args()
    problems = []
    before_nif = nif.Nif(ab.OUT / 'ShapeData' / ab.DATA_FOLDER / f'{ab.DATA_FOLDER}.nif')
    after_nif = nif.Nif(args.saved / 'AnatomyBodyZeX.nif')
    b, a = before_nif.shape(ab.SHAPE), after_nif.shape(ab.SHAPE)

    # 1. geometry
    same_pos = b.count == a.count and all(p == q for p, q in zip(b.positions(), a.positions()))
    same_tri = b.triangles() == a.triangles()
    print(f'1. vertices {b.count} -> {a.count}; positions identical {same_pos}; triangles identical {same_tri}')
    if not (same_pos and same_tri):
        problems.append('geometry changed')

    # 2. sliders
    bo = osd.read(ab.OUT / 'ShapeData' / ab.DATA_FOLDER / f'{ab.DATA_FOLDER}.osd')
    osd_files = list(args.saved.glob('*.osd'))
    ao = osd.read(osd_files[0]) if osd_files else {}
    zero = (0.0, 0.0, 0.0)
    diff_sliders = []
    for name, d in bo.items():
        e = ao.get(name)
        if e is None:
            diff_sliders.append(f'{name} missing')
            continue
        worst = max((max(abs(x - y) for x, y in zip(d.get(i, zero), e.get(i, zero))) for i in set(d) | set(e)), default=0.0)
        if worst > 1e-6:
            diff_sliders.append(f'{name} {worst:.2g}')
    print(f'2. slider data: {len(bo)} before, {len(ao)} after; differing: {diff_sliders[:8] or "none"}')
    if diff_sliders:
        problems.append(f'slider data changed: {diff_sliders[:8]}')

    # 3. bones
    bones, xf = after_nif.skin(a)
    origin = {n: nif.bone_origin(xf[i]) for i, n in enumerate(bones)}
    want = ANIM + list(TWIN.values()) + ['LBreast_skin', 'RBreast_skin']
    missing = [n for n in want if n not in bones]
    leftover = [n for n in CLOTH if n in bones]
    print(f'3. bones {len(bones)}; genital present {len(want) - len(missing)}/{len(want)}; missing {missing or "none"}; '
          f'2017 cloth bones left {leftover or "none"}')
    for n in ANIM:
        if n in origin:
            d = math.dist(origin[n], ZEX_AT[n])
            t = TWIN.get(n)
            dt = math.dist(origin[t], origin[n]) if t in origin else None
            print(f'   {n:12} bound at ({origin[n][0]:6.2f},{origin[n][1]:6.2f},{origin[n][2]:7.2f}), {d:.3f} from ZeX'
                  + (f'; twin {t} {dt:.3f} away' if dt is not None else ''))
            if d > 0.05 or (dt is not None and dt > 0.01):
                problems.append(f'{n} (or its twin) is not bound where ZeX puts it')
    if missing:
        problems.append(f'genital bones missing: {missing}')

    # 4. untouched outside the mask -- apart from the breast move, which must be exact
    import zex_bones
    move = zex_bones.BREAST_MOVE
    m = mask_values(ab.OUT / 'Masks/AnatomyGenitalRegion.xml')
    bb, _ = before_nif.skin(b)
    changed = 0
    for i, v in m.items():
        if v < 1.0:
            continue
        wb = sorted((move.get(bb[s], bb[s]), round(w, 4)) for s, w in b.skin_weights(i))
        wa = sorted((bones[s], round(w, 4)) for s, w in a.skin_weights(i))
        if wb != wa:
            changed += 1
    protected = sum(1 for v in m.values() if v >= 1.0)
    print(f'4. protected vertices {protected}; weights changed on {changed} (breast move applied before comparing)')
    if changed:
        problems.append(f'{changed} protected vertices changed weight')
    left_on_cloth = sum(1 for i in range(a.count) for s, w in a.skin_weights(i) if bones[s] in move)
    before_cloth = collections.Counter(move[bb[s]] for i in range(b.count) for s, w in b.skin_weights(i) if bb[s] in move)
    after_breast = collections.Counter(bones[s] for i in range(a.count) for s, w in a.skin_weights(i)
                                       if bones[s] in move.values())
    print(f'   breasts: weights left on the Havok cloth bones {left_on_cloth}; carried before {dict(before_cloth)}, '
          f'now on the OCBP bones {dict(after_breast)}')
    if left_on_cloth or before_cloth != after_breast:
        problems.append('breast weights did not move exactly onto LBreast_skin/RBreast_skin')

    # 5. where the genital weights went
    pos = a.positions()
    per = collections.defaultdict(list)
    for i in range(a.count):
        for s, w in a.skin_weights(i):
            if bones[s] in want:
                per[bones[s]].append((w, i))
    print('5. genital weights:')
    for n in want:
        ws = per.get(n, [])
        if not ws:
            import zex_bones as zbw
            if n in ANIM and not zbw.ANIM_WEIGHTS:
                print(f'   {n:16} no vertex (by design: animated genital bones carry no weight, A-12)')
            else:
                print(f'   {n:16} NO vertex')
                problems.append(f'{n} carries no weight')
            continue
        c = tuple(sum(pos[i][k] * w for w, i in ws) / sum(w for w, _ in ws) for k in range(3))
        far = math.dist(c, origin.get(n, c))
        print(f'   {n:16} {len(ws):5} vertices, max {max(w for w, _ in ws):.2f}, weighted centre '
              f'({c[0]:6.2f},{c[1]:6.2f},{c[2]:7.2f}), {far:.2f} from its bone')
        # a genital bone sits inside what it carries; a breast bone is a pivot above the bust
        if far > 3.0 and n not in move.values():
            problems.append(f'{n} weights centre {far:.1f} units from the bone')
    four = sum(1 for i in range(a.count) if len(a.skin_weights(i)) == 4)
    print(f'   vertices using all 4 influence slots: {four}')

    if problems:
        print('\nFAIL - ' + '\n       '.join(problems))
        sys.exit(1)
    print('\nPASS - geometry and sliders unchanged, 14 genital bones bound where ZeX puts them, '
          'CBBE skin untouched outside the mask.')


if __name__ == '__main__':
    main()
