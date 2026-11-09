"""Behemoth on VANILLA only (Dudu 11-09: no UAP nude body): vanilla supermutantbehemoth.nif with the loincloth piece
cut out of Behemoth_Body_New:1 (bh_cut.py, replaced in place by transplant) + our Behemoth_Penis1 (vanilla lower-body
material) + Behemoth_PenisGlans (MutantGlans) as NEW shapes from the existing seg_fix'ed export (bh\\build), BODYTRI
+ our .tri.  python -I bh_vanilla.py <out Data>"""
import collections
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
B = pathlib.Path(r'D:\F4Output\creatures\bh')
VAN = pathlib.Path(r'D:\F4Output\creatures\sm\vanilla\supermutantbehemoth.nif')
BL = r'D:\F4Tools\blender-5.1.2-windows-x64\blender.exe'
REL = 'meshes/actors/supermutantbehemoth/characterassets'
LOWER = 'Behemoth_Body_New:1'
GLANS = ('Materials\\Anatomy\\Creatures\\MutantGlans.bgsm',
         ['textures\\Anatomy\\Creatures\\MutantGlans_d.dds', 'textures\\Anatomy\\Creatures\\MutantGlans_n.dds',
          'textures\\Anatomy\\Creatures\\MutantGlans_s.dds'])


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stdout[-1500:] + r.stderr[-1500:])
    return r.stdout


# the loincloth = the smallest welded component of the vanilla lower body
m = nif.Nif(VAN)
s = m.shape(LOWER)
P = np.array(s.positions())
w = nif.weld(P.tolist())
par = list(range(max(w) + 1))


def find(a):
    while par[a] != a:
        par[a] = par[par[a]]
        a = par[a]
    return a


for a, b, c in s.triangles():
    for x, y in ((w[a], w[b]), (w[b], w[c])):
        rx, ry = find(x), find(y)
        if rx != ry:
            par[rx] = ry
comp = collections.Counter(find(w[i]) for i in range(len(P)))
cloth_root = min(comp, key=comp.get)
cloth = [P[i].tolist() for i in range(len(P)) if find(w[i]) == cloth_root]
print('components', sorted(comp.values()), 'loincloth', len(cloth))
cj = B / 'vanilla_cut' / 'cloth.json'
cj.parent.mkdir(parents=True, exist_ok=True)
json.dump(cloth, open(cj, 'w'))
exp = B / 'vanilla_cut' / 'lower.nif'
print([l for l in run([BL, '-b', '-P', str(HERE / 'bh_cut.py'), '--', str(VAN), LOWER, str(cj), str(exp)]).splitlines()
       if l.startswith(('CUT', 'BUILT'))])
print(run([sys.executable, '-I', str(HERE / 'seg_fix.py'), str(VAN), str(exp), 'torso4']).strip()[:300])
tmp = B / 'vanilla_cut' / 'nude.nif'
info = transplant(VAN, exp, tmp, {}, replace=[LOWER])
print('nude body', info['shapes'])
(out / REL).mkdir(parents=True, exist_ok=True)
pen_exp = B / 'build' / 'supermutantbehemoth.nif'
info = transplant(tmp, pen_exp, out / REL / 'SuperMutantBehemoth.nif',
                  {'Behemoth_Penis1': (LOWER, None, None), 'Behemoth_PenisGlans': (LOWER, GLANS[0], GLANS[1])},
                  bodytri='Actors\\SuperMutantBehemoth\\CharacterAssets\\SuperMutantBehemoth.tri')
print('final', info['shapes'], info['blocks'])
shutil.copyfile(B / 'out5' / 'Data' / REL / 'SuperMutantBehemoth.tri', out / REL / 'SuperMutantBehemoth.tri')
# the glans texture/material from the approved pack
for top in ('textures', 'materials'):
    shutil.copytree(B / 'out5' / 'Data' / top, out / top, dirs_exist_ok=True)
