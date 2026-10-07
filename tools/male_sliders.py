"""LooksMenu body sliders for the men's body (an Ivy player, 2026-10-08: "the male advanced creation has no sliders").
The built men's body (BodyTalk 4 through AnatomyBuilder / the prebuilt bodies) ships its .tri with BodyTalk's morphs,
but nothing told LooksMenu about them: BodyTalk ships no F4EE sliders.json. This writes one for every morph the .tri
carries, men only (gender 0), under Anatomy.esp's folder (LooksMenu reads Data/F4SE/Plugins/F4EE/Sliders/<an active
plugin>/sliders.json). The erection morphs are left out: AAF drives them in scenes, and a menu value would stay on.

    python tools/male_sliders.py <MaleBody.tri> <out sliders.json>
"""
import json
import re
import struct
import sys

SKIP = {'Erection', 'Erection Up', 'Erection Down'}


def morph_names(path):
    b = open(path, 'rb').read()
    if b[:4] != b'PIRT':
        raise ValueError(f'{path}: not a BodySlide .tri')
    o, names = 6, []
    for _ in range(struct.unpack_from('<H', b, 4)[0]):
        o += 1 + b[o]
        (count,) = struct.unpack_from('<H', b, o)
        o += 2
        for _ in range(count):
            names.append(b[o + 1:o + 1 + b[o]].decode('latin1').rstrip('\0'))
            o += 1 + b[o]
            o += 6 + 8 * struct.unpack_from('<fH', b, o)[1]
    return names


def label(morph):
    """'BTNegShoulder' -> 'Neg Shoulder', 'BT2AdonisBelt' -> 'Adonis Belt': BodyTalk's names, readable"""
    s = re.sub(r'^BT2?', '', morph) or morph
    s = re.sub(r'(?<=[a-z])(?=[A-Z])|(?<=[A-Za-z])(?=\d)', ' ', s).replace('-', ' ').replace('_', ' ')
    return ' '.join(s.split())


def main():
    names = [m for m in dict.fromkeys(morph_names(sys.argv[1])) if m not in SKIP]
    rows = [dict(name=label(m), morph=m, minimum=0.0, maximum=1.0, interval=0.01, gender=0) for m in names]
    with open(sys.argv[2], 'w', encoding='utf-8') as fh:
        json.dump(rows, fh, indent='\t')
    print(f'{len(rows)} men\'s sliders ({len(SKIP)} erection morphs left out) -> {sys.argv[2]}')


if __name__ == '__main__':
    main()
