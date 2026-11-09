"""Radstag genitals (deer: furred sheath along the belly, thin pointed penis, furred scrotum), from UAP's ONE 'Penis'
shape (moving part = penis, static = sheath/scrotum): RadStag.nif (morphs, own .tri) + RadStag_Nude.nif (UAP's is a
permanently erect copy: ours = Erection baked in, no morphs). Transplanted onto the VANILLA radstag body.
    python -I rs_all.py <out Data>"""
import json
import pathlib
import shutil
import subprocess
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from transplant import transplant  # noqa: E402

out = pathlib.Path(sys.argv[1])
R = pathlib.Path(r'D:\F4Output\creatures\rs')
D = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data\meshes\actors\radstag\characterassets')
VAN = R / 'vanilla' / 'radstag.nif'
BL = r'D:\F4Tools\blender-5.1.2-windows-x64\blender.exe'
REL = 'meshes/actors/radstag/characterassets'
PEN = ('Materials\\Anatomy\\Creatures\\CaninePenis.bgsm',
       ['textures\\Anatomy\\Creatures\\CaninePenis_d.dds', 'textures\\Anatomy\\Creatures\\CaninePenis_n.dds',
        'textures\\Anatomy\\Creatures\\CaninePenis_s.dds'])


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stdout[-1500:] + r.stderr[-1500:])
    return r.stdout


geom = R / 'geom_RadStag.json'
o = run([sys.executable, '-I', str(HERE / 'canine_geom.py'), str(D / 'RadStag.nif'), 'Penis', 'Penis',
         str(D / 'RadStag.tri'), str(VAN), str(geom), 'noknot', 'sack', 'nosheath',
         'sackuv=0.30,0.40,0.36,0.46'])                  # brown belly fur inside the main body island
print([l for l in o.splitlines() if l.startswith(('penis:', 'sheath:', 'sack', 'one-shape'))])
G = json.load(open(geom))
for part in ('penis', 'sheath', 'sack'):                  # the nude copy: erect, no morphs
    V = np.array(G[part]['verts']) + np.array(G[part]['morphs']['Erection'])
    G[part]['verts'] = V.tolist()
    G[part]['morphs'] = {}
json.dump(G, open(R / 'geom_RadStag_Nude.json', 'w'))
for name, gj, morphs in (('RadStag', geom, True), ('RadStag_Nude', R / 'geom_RadStag_Nude.json', False)):
    exp = R / 'build' / REL / f'{name}.nif'
    o = run([BL, '-b', '-P', str(HERE / 'canine_build.py'), '--', str(gj), str(VAN), str(exp), 'Penis', 'RadStag_Sheath',
             'Pelvis', 'RadStag_Scrotum'])
    print([l for l in o.splitlines() if l.startswith(('BUILT', 'sheath fur', 'sack uv'))])
    print(run([sys.executable, '-I', str(HERE / 'seg_fix.py'), str(VAN), str(exp), 'single'])[:160])
    if morphs:
        run([sys.executable, '-I', str(HERE / 'tri_normalize.py'), str(exp.with_suffix('.tri'))])
    dst = out / REL / f'{name}.nif'
    dst.parent.mkdir(parents=True, exist_ok=True)
    # no sheath on the radstag (UAP's hangs; a sheath riding a hanging penis looked wrong): penis + scrotum
    info = transplant(VAN, exp, dst, {'Penis': ('RadStag_mesh:0', PEN[0], PEN[1]),
                                      'RadStag_Scrotum': ('RadStag_mesh:0', None, None)},
                      bodytri=f'Actors\\RadStag\\CharacterAssets\\{name}.tri' if morphs else None)
    if morphs:
        shutil.copyfile(exp.with_suffix('.tri'), dst.with_suffix('.tri'))
    print(name, info['blocks'], info['shapes'][-3:])
src_tex = pathlib.Path(r'D:\F4Output\creatures\canine\out9\Data')
for top in ('textures', 'materials'):
    shutil.copytree(src_tex / top, out / top, dirs_exist_ok=True)
