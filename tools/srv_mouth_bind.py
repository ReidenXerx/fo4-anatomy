"""A Servitron head's mouth bones bound where the Anatomy Engine creates them (2026-11-22, Ilham's head by General-mods).

The engine makes AnatSrvMouth_L / _R at run time as children of the skeleton's HEAD with IDENTITY local rotation
(ocbp.ini [Bones]: name=parent,x,y,z), so a skin entry for them must say exactly that: HEAD's rotation, at the bone's
own place. An armature export (PyNifly) binds them along the bone's head->tail instead, and the panel would sit turned
by that difference. Each shape's entries for the mouth bones get HEAD's skin-to-bone rotation (from the same shape) and
the translation that keeps their bind origin; the [Bones] lines (the origin in HEAD's space) are printed.

    python tools/srv_mouth_bind.py <head.nif> <out.nif>
"""
import pathlib
import struct
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import nif  # noqa: E402

MOUTH = ('AnatSrvMouth_L', 'AnatSrvMouth_R')
BONE = 4 * 4 + 9 * 4 + 3 * 4 + 4               # BSSkin::BoneData per bone: sphere, rotation, translation, scale


def main():
    src, dst = sys.argv[1:3]
    n = nif.Nif(src)
    lines = {}
    for s in n.shapes():
        names, xf = n.skin(s)
        if not any(b in MOUTH for b in names):
            continue
        if 'HEAD' not in names:
            raise SystemExit(f'{s.name}: mouth bones without HEAD in the same skin')
        hr, ht, hs = xf[names.index('HEAD')]
        M = np.array(hr, float).reshape(3, 3)
        c = nif.Cursor(n.b, n.offsets[s.skin][0])
        c.take('i')
        data = c.take('i')
        data = data[0] if isinstance(data, tuple) else data
        base = n.offsets[data][0] + 4
        for k, b in enumerate(names):
            if b not in MOUTH:
                continue
            p = np.array(nif.bone_origin(xf[k]))             # where the export bound it (skin space)
            t = -(M @ p)
            o = base + k * BONE + 16
            struct.pack_into('<9f', n.b, o, *hr)
            struct.pack_into('<3f', n.b, o + 36, *t)
            struct.pack_into('<f', n.b, o + 48, hs)
            local = M @ p + np.array(ht)                     # the bind origin in HEAD's own space
            lines[b] = f'{b}=HEAD,{local[0]:.4f},{local[1]:.4f},{local[2]:.4f}'
            print(f'{s.name}: {b} rebound at {np.round(p, 3)} (HEAD rotation)')
    if not lines:
        raise SystemExit('no mouth bones found')
    n.save(dst)
    print('[Bones]\n' + '\n'.join(lines[b] for b in sorted(lines)))


if __name__ == '__main__':
    main()
