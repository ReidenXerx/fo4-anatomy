"""Canine meshes by transplant: each VANILLA body nif byte for byte + our penis and sheath from the seg_fix'ed export
(canine_all.py output) + BODYTRI; the .tri files and our textures/materials copied alongside.
    python -I canine_transplant.py <export Data> <out Data>"""
import pathlib
import re
import shutil
import struct
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import nif  # noqa: E402
from canine_all import JOBS  # noqa: E402
from transplant import _shape_refs_at, transplant  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
VAN = pathlib.Path(r'D:\F4Output\creatures\canine\vanilla')
PEN = ('Materials\\Anatomy\\Creatures\\CaninePenis.bgsm',
       ['textures\\Anatomy\\Creatures\\CaninePenis_d.dds', 'textures\\Anatomy\\Creatures\\CaninePenis_n.dds',
        'textures\\Anatomy\\Creatures\\CaninePenis_s.dds'])
for top in ('textures', 'materials'):
    if not (out / top).exists():
        shutil.copytree(src / top, out / top)
for name, rel, van, ref, pen, sh, pelvis, morphs in JOBS:
    P_path = src / 'meshes' / rel
    V = nif.Nif(VAN / van)
    P = nif.Nif(P_path)
    lit = [s for s in V.shapes()
           if V.types[struct.unpack_from('<3i', V.b, _shape_refs_at(V, s.index))[1]] == 'BSLightingShaderProperty'
           and 'cap' not in s.name.lower() and 'eye' not in s.name.lower()]
    body = max(lit, key=lambda s: s.count).name
    c = np.array(P.shape(sh).positions()).mean(0)
    near = min(lit, key=lambda s: np.linalg.norm(np.array(s.positions()) - c, axis=1).min()).name
    tri = [s for s in P.strings if s.lower().endswith('.tri')]
    dst = out / 'meshes' / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    info = transplant(VAN / van, P_path, dst, {pen: (body, PEN[0], PEN[1]), sh: (near, None, None)},
                      bodytri=tri[0].replace('/', '\\') if tri else None)
    t = P_path.with_suffix('.tri')
    if t.exists():
        shutil.copyfile(t, dst.with_suffix('.tri'))
    print(f'{name}: body {body}, sheath fur {near}, bodytri {tri[0] if tri else "-"}, blocks {len(V.types)}->'
          f'{info["blocks"]}')
