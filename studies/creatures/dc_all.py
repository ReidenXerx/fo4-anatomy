"""Deathclaw: dc_geom -> dc_build (Blender) -> seg_fix torso4 -> tri normalize -> transplant into UAP's
DeathclawPenis.nif (male: Base + Penis replaced; Base takes the VANILLA body material so its body-projected UVs are
seamless) and into a renamed copy of it (female: DeathclawVulva.nif, VulvaLips + VulvaInner, own .tri).
    python -I dc_all.py <out Data>"""
import json
import pathlib
import shutil
import subprocess
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402
from transplant import transplant  # noqa: E402

out = pathlib.Path(sys.argv[1])
D = pathlib.Path(r'D:\F4Output\creatures\dc')
UAP = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data\meshes\actors\Deathclaw\DeathclawPenis.nif')
VAN = D / 'vanilla' / 'deathclaw.nif'
BL = r'D:\F4Tools\blender-5.1.2-windows-x64\blender.exe'
REL = 'meshes/actors/deathclaw'
BODY_MAT = ('Materials\\actors\\Deathclaw\\Deathclaw.BGSM',
            ['textures\\actors\\deathclaw\\deathclaw_d.dds', 'textures\\actors\\deathclaw\\deathclaw_n.dds'])


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(' '.join(map(str, cmd))[:300] + '\n' + r.stdout[-1500:] + r.stderr[-1500:])
    return r.stdout


print(run([sys.executable, '-I', str(HERE / 'dc_geom.py'), str(D / 'geom_male.json'), str(D / 'geom_female.json')])
      .splitlines()[-6:])
(out / REL).mkdir(parents=True, exist_ok=True)
# female template: UAP's file with the shape names + BODYTRI renamed (every block keeps its bytes)
tmpl = D / 'build' / 'female_template.nif'
tmpl.parent.mkdir(parents=True, exist_ok=True)
nif.Nif(UAP).save_renamed(tmpl, {'Base': 'VulvaLips', 'Penis': 'VulvaInner',
                                 'Actors\\Deathclaw\\DeathclawPenis.tri': 'Actors\\Deathclaw\\DeathclawVulva.tri'})
for g, base, lips, inner, name in (('male', UAP, 'Base', 'Penis', 'DeathclawPenis'),
                                   ('female', tmpl, 'VulvaLips', 'VulvaInner', 'DeathclawVulva')):
    exp = D / 'build' / f'{g}.nif'
    o = run([BL, '-b', '-P', str(HERE / 'dc_build.py'), '--', str(D / f'geom_{g}.json'), str(VAN), str(exp)])
    print([l for l in o.splitlines() if l.startswith('BUILT')])
    print(run([sys.executable, '-I', str(HERE / 'seg_fix.py'), str(VAN), str(exp), 'torso4'])[:200])
    run([sys.executable, '-I', str(HERE / 'tri_normalize.py'), str(exp.with_suffix('.tri'))])
    G = json.load(open(D / f'geom_{g}.json'))
    m = nif.Nif(exp)
    for sn in (lips, inner):
        P = np.array(m.shape(sn).positions())
        Q = np.array(G[sn]['verts'])
        if len(P) != len(Q) or np.abs(P - Q).max() > 0.1:
            raise SystemExit(f'{g} {sn}: export {len(P)} v vs json {len(Q)} (split or reordered)')
    dst = out / REL / f'{name}.nif'
    info = transplant(base, exp, dst, {}, replace=(lips, inner),
                      replace_mat={lips: (lips, BODY_MAT[0], BODY_MAT[1])})
    shutil.copyfile(exp.with_suffix('.tri'), dst.with_suffix('.tri'))
    print(g, info['blocks'], info['shapes'])
