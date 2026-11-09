"""Super mutant genitals end to end: geometry -> Blender export of our shapes -> seg_fix (UAP's single-segment
layout) -> .tri -> transplant onto the VANILLA supermutantbody.nif (+ genital bone nodes + BODYTRI) -> check.
    python -I sm_all.py <out Data>"""
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from transplant import transplant  # noqa: E402

out = pathlib.Path(sys.argv[1])
S = pathlib.Path(r'D:\F4Output\creatures\sm')
UAP = r'D:\SteamFreeGames\Fallout 4 AE\Data\meshes\actors\supermutant\characterassets\supermutantbody.nif'
VAN = S / 'vanilla' / 'supermutantbody.nif'
BL = r'D:\F4Tools\blender-5.1.2-windows-x64\blender.exe'
REL = 'meshes/actors/supermutant/characterassets'
GLANS = ('Materials\\Anatomy\\Creatures\\MutantGlans.bgsm',
         ['textures\\Anatomy\\Creatures\\MutantGlans_d.dds', 'textures\\Anatomy\\Creatures\\MutantGlans_n.dds',
          'textures\\Anatomy\\Creatures\\MutantGlans_s.dds'])


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stdout[-1500:] + r.stderr[-1500:])
    return r.stdout


print(run([sys.executable, '-I', str(HERE / 'sm_geom.py'), str(S / 'geom.json')]).splitlines()[-1])
exp = S / 'build' / 'supermutantbody.nif'
o = run([BL, '-b', '-P', str(HERE / 'chain_build.py'), '--', str(S / 'geom.json'), UAP, 'SM Penis', str(exp)])
print([l for l in o.splitlines() if l.startswith('BUILT')])
print(run([sys.executable, '-I', str(HERE / 'seg_fix.py'), str(VAN), str(exp), 'single']).strip()[:300])
(out / REL).mkdir(parents=True, exist_ok=True)
print(run([sys.executable, '-I', str(HERE / 'geom_tri.py'), str(S / 'geom.json'), str(exp),
           str(out / REL / 'SupermutantBody.tri')]).strip())
info = transplant(VAN, exp, out / REL / 'SupermutantBody.nif',
                  {'SM Penis': ('SupermutantBodyNew:0', None, None),
                   'SM PenisGlans': ('SupermutantBodyNew:0', GLANS[0], GLANS[1])},
                  bodytri='Actors\\Supermutant\\CharacterAssets\\SupermutantBody.tri')
print(info)
for top in ('textures', 'materials'):
    shutil.copytree(S / 'texdata' / top, out / top, dirs_exist_ok=True)
