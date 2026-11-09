"""Feral meshes rebuilt by transplant (crash 11-09: our PyNifly files lost the vanilla glow effect shaders, alpha,
controllers, sequences and palette, and every cut of a Bloated Glowing One crashed - males too). Vanilla bytes +
our shapes from the seg_fix'ed export (out3).  python -I feral_transplant.py <src Data> <out Data>"""
import pathlib
import shutil
import sys

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import nif  # noqa: E402
from transplant import transplant  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
SRC, OUT = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
VAN = pathlib.Path(r'D:\F4Output\creatures\feral\vanilla')
REL = 'meshes/actors/feralghoul/characterassets'
WOUND = ('Materials\\Anatomy\\Creatures\\FeralStumpWound.bgsm',
         ['textures\\Anatomy\\Creatures\\FeralStumpWound_d.dds', 'textures\\Anatomy\\Creatures\\FeralStumpWound_n.dds',
          'textures\\Anatomy\\Creatures\\FeralStumpWound_s.dds'])
(OUT / REL).mkdir(parents=True, exist_ok=True)
for top in ('textures', 'materials'):
    if (SRC / top).exists() and not (OUT / top).exists():
        shutil.copytree(SRC / top, OUT / top)
for p in sorted(SRC.glob('*.esp')):
    shutil.copyfile(p, OUT / p.name)
for f in sorted((SRC / REL).glob('*.nif')):
    base = f.stem.removesuffix('_F')
    V, P = nif.Nif(VAN / f'{base}.nif'), nif.Nif(f)
    vs = {s.name: s for s in V.shapes()}
    lit = [s for s in V.shapes() if V.types[__import__('transplant')._shape_refs_at(V, s.index) and
                                             __import__('struct').unpack_from('<3i', V.b, __import__('transplant')
                                                                              ._shape_refs_at(V, s.index))[1]]
           == 'BSLightingShaderProperty']
    body = max(lit, key=lambda s: s.count).name
    replace = [s.name for s in P.shapes() if s.name in vs and s.count != vs[s.name].count]
    new = {}
    for s in P.shapes():
        if s.name in vs:
            continue
        if s.name == 'FeralStumpWound':
            new[s.name] = (body, WOUND[0], WOUND[1])
        elif s.name == 'FeralVulvaInner':                       # run 6: own pink mucosa (the dark wound vanished)
            new[s.name] = (body, WOUND[0].replace('FeralStumpWound', 'FeralVulvaInner'),
                           [t.replace('FeralStumpWound', 'FeralVulvaInner') for t in WOUND[1]])
        else:
            new[s.name] = (body, None, None)
    info = transplant(VAN / f'{base}.nif', f, OUT / REL / f.name, new, replace)
    print(f'{f.name}: body {body}; replaced {replace}; new {list(new)}; blocks {len(V.types)}->{info["blocks"]}')
