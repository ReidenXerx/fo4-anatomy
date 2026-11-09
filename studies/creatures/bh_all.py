"""Behemoth genitals end to end: geometry -> Blender export of our shapes -> seg_fix (UAP's torso4 layout, against
the vanilla behemoth which has no penis) -> .tri -> transplant onto UAP's NUDE behemoth body (vanilla's has a loincloth):
UAP's Behemoth_Penis1 replaced IN PLACE by ours (its shader/texture set overwritten with the lower-body material),
our glans appended.  python -I bh_all.py <out Data>"""
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from transplant import transplant  # noqa: E402

out = pathlib.Path(sys.argv[1])
B = pathlib.Path(r'D:\F4Output\creatures\bh')
UAP = r'D:\SteamFreeGames\Fallout 4 AE\Data\meshes\actors\supermutantbehemoth\characterassets\supermutantbehemoth.nif'
VAN = r'D:\F4Output\creatures\sm\vanilla\supermutantbehemoth.nif'
BL = r'D:\F4Tools\blender-5.1.2-windows-x64\blender.exe'
REL = 'meshes/actors/supermutantbehemoth/characterassets'
GLANS = ('Materials\\Anatomy\\Creatures\\MutantGlans.bgsm',
         ['textures\\Anatomy\\Creatures\\MutantGlans_d.dds', 'textures\\Anatomy\\Creatures\\MutantGlans_n.dds',
          'textures\\Anatomy\\Creatures\\MutantGlans_s.dds'])


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stdout[-1500:] + r.stderr[-1500:])
    return r.stdout


print(run([sys.executable, '-I', str(HERE / 'bh_geom.py'), str(B / 'geom.json')]).splitlines()[-1])
exp = B / 'build' / 'supermutantbehemoth.nif'
o = run([BL, '-b', '-P', str(HERE / 'chain_build.py'), '--', str(B / 'geom.json'), UAP, 'Behemoth_Penis1', str(exp)])
print([l for l in o.splitlines() if l.startswith('BUILT')])
print(run([sys.executable, '-I', str(HERE / 'seg_fix.py'), VAN, str(exp), 'torso4']).strip()[:300])
(out / REL).mkdir(parents=True, exist_ok=True)
print(run([sys.executable, '-I', str(HERE / 'geom_tri.py'), str(B / 'geom.json'), str(exp),
           str(out / REL / 'SuperMutantBehemoth.tri')]).strip())
info = transplant(UAP, exp, out / REL / 'SuperMutantBehemoth.nif',
                  {'Behemoth_PenisGlans': ('Behemoth_Lower.0011', GLANS[0], GLANS[1])},
                  replace=['Behemoth_Penis1'],
                  replace_mat={'Behemoth_Penis1': ('Behemoth_Lower.0011', None, None)})
print(info)
