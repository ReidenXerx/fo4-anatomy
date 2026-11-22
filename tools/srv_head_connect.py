"""A Servitron head module's root extra data copied onto another head nif (2026-11-22, Ilham's head by General-mods).

Servitron's own Head.nif hangs from the torso's head point through BSConnectPoint::Children (C-Head) and offers points
to the other head modules through BSConnectPoint::Parents (P-HeadArmor/Ears/Laser/Eyes/Mouth), with BSXFlags beside
them. A head exported without them still drew, but outside the skeleton tree the engine walks: its mouth panel was
never driven (Ilham test2). This appends those three blocks (bytes as they are; their names become new strings) and
lists them on the root node's extra data. BODYTRI is not copied (a head without a .tri).

    python tools/srv_head_connect.py <servitron Head.nif> <head in.nif> <head out.nif>
"""
import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import nif  # noqa: E402

COPY = ('BSXFlags', 'BSConnectPoint::Parents', 'BSConnectPoint::Children')


def main():
    src, head_in, head_out = sys.argv[1:4]
    s = nif.Nif(src)
    h = nif.Nif(head_in)
    have = [t for t in h.types if t in COPY]
    if have:
        raise SystemExit(f'{head_in} already has {have}')
    blocks, names = [], []
    for kind in COPY:
        i = s.types.index(kind)
        o, size = s.offsets[i]
        raw = bytearray(s.b[o:o + size])
        names.append(s.string(struct.unpack_from('<i', raw, 0)[0]))
        struct.pack_into('<i', raw, 0, len(h.strings) + len(names) - 1)   # its name: a new string of ours
        blocks.append((kind, bytes(raw)))
    # the root (block 0, a NiNode): NiObjectNET name, extra data count + refs, then the rest unchanged
    o, size = h.offsets[0]
    root = bytes(h.b[o:o + size])
    name, count = struct.unpack_from('<iI', root, 0)
    refs = list(struct.unpack_from(f'<{count}i', root, 8))
    first = len(h.offsets)
    refs += [first + k for k in range(len(blocks))]
    new_root = struct.pack('<iI', name, len(refs)) + struct.pack(f'<{len(refs)}i', *refs) + root[8 + 4 * count:]
    out = h.with_edits(replace={0: new_root}, append=blocks, add_strings=names)
    pathlib.Path(head_out).write_bytes(out)
    check = nif.Nif(head_out)
    print('root extra data:', [check.types[r] for r in refs], 'names', names,
          'shapes', [x.name for x in check.shapes()])


if __name__ == '__main__':
    main()
