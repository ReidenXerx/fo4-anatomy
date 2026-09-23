"""The two weight references for Outfit Studio's CopyBoneWeights (decision A-6).

RESEARCH ONLY since A-19: no build step reads these any more (zex_bones.py's weights are all
ours), and the release never needs JaneBod Extended.

    build/references/AnatomyRefJBE.nif      JaneBod Extended's body, as shipped
    build/references/AnatomyRefJBE_CBP.nif  the same file with the five vagina bones renamed to
                                            ZeX's _CBP_ twins, so a second copy pass puts the
                                            same weight pattern on the bones physics moves

The twins sit exactly where the animated bones sit (identical local transforms under Pelvis in
ZeX 6.0), so the renamed file's bind transforms are the twins' own. The rename rewrites only the
header string table and is PROVEN here: every block of the renamed file must be byte-identical
to the original's, and only the named strings may differ.

    python tools/references.py
"""
import pathlib
import shutil
import sys

import nif

ROOT = pathlib.Path(__file__).resolve().parent.parent
JBE = ROOT / 'inputs/jbe/JaneBodVag/Data/Tools/BodySlide/ShapeData/JaneBodVag-CBBE-CBP/JaneBodVag-CBBE-CBP.nif'
OUT = ROOT / 'build/references'
TWINS = {'Vagina_00': 'Vagina_CBP_00',
         'Vagina_L_01': 'Vagina_CBP_L_01', 'Vagina_L_02': 'Vagina_CBP_L_02',
         'Vagina_R_01': 'Vagina_CBP_R_01', 'Vagina_R_02': 'Vagina_CBP_R_02'}


FRAME_BONES = ('Pelvis_skin', 'SPINE1', 'LLeg_Thigh_skin', 'RLeg_Thigh_skin')


def frame_offset(ours, jbe):
    """The translation that carries JaneBod's skin space onto ours, measured on bones both skins
    bind (their origins must all agree on one offset, or the frames differ by more than a move)."""
    ob, ox = ours.skin(ours.shape('CBBE'))
    jb, jx = jbe.skin(jbe.shapes()[0])
    shared = [b for b in FRAME_BONES if b in ob and b in jb]
    offs = []
    for b in shared:
        o, j = nif.bone_origin(ox[ob.index(b)]), nif.bone_origin(jx[jb.index(b)])
        offs.append(tuple(o[k] - j[k] for k in range(3)))
    d = tuple(sum(x[k] for x in offs) / len(offs) for k in range(3))
    spread = max(max(abs(x[k] - d[k]) for k in range(3)) for x in offs)
    if spread > 0.01:
        raise SystemExit(f'frames differ by more than a translation: offsets {offs}')
    return d, shared


def main():
    import align_body as ab
    if not JBE.exists():
        raise SystemExit(f'missing {JBE}: copy JaneBod Extended\'s files into inputs/jbe (A-3)')
    OUT.mkdir(parents=True, exist_ok=True)
    plain, cbp = OUT / 'AnatomyRefJBE.nif', OUT / 'AnatomyRefJBE_CBP.nif'

    # JaneBod's mesh lives 120.8 units away from ours in raw skin space. Outfit Studio's proximity
    # copy found nothing across that gap (measured: 0 of 14 bones arrived), so the reference is
    # moved into our frame first: vertices by d, bind translations by -R d.
    ours = nif.Nif(ab.OUT / 'ShapeData' / ab.DATA_FOLDER / f'{ab.DATA_FOLDER}.nif')
    jbe = nif.Nif(JBE)
    d, shared = frame_offset(ours, jbe)
    jbe.translate_skin_space(jbe.shapes()[0], d)
    jbe.save(plain)
    a = nif.Nif(plain)
    after, _ = frame_offset(ours, a)
    print(f'frame offset {tuple(round(x, 3) for x in d)} (from {", ".join(shared)}); after the move: '
          f'{tuple(round(x, 4) for x in after)}')
    if max(abs(x) for x in after) > 0.01:
        raise SystemExit('the move did not bring the frames together')
    a.save_renamed(cbp, TWINS)
    b = nif.Nif(cbp)

    problems = []
    if a.types != b.types or len(a.offsets) != len(b.offsets):
        problems.append('block list differs')
    else:
        for i, ((oa, sa), (ob, sb)) in enumerate(zip(a.offsets, b.offsets)):
            if a.b[oa:oa + sa] != b.b[ob:ob + sb]:
                problems.append(f'block {i} ({a.types[i]}) changed')
    changed = {x: y for x, y in zip(a.strings, b.strings) if x != y}
    if changed != TWINS:
        problems.append(f'strings changed {changed}, expected exactly {TWINS}')
    bones = b.skin(b.shapes()[0])[0]
    missing = [t for t in TWINS.values() if t not in bones]
    if missing:
        problems.append(f'renamed skin lacks {missing}')
    print(f'{plain.name}: {len(a.offsets)} blocks; {cbp.name}: blocks identical, '
          f'{len(changed)} strings renamed; skin now has {sorted(t for t in bones if "CBP" in t and "Vagina" in t)}')
    if problems:
        print('FAIL - ' + '; '.join(problems))
        sys.exit(1)
    print('PASS')


if __name__ == '__main__':
    main()
