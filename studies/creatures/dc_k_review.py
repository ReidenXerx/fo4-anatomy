"""Review build for the kassarawi deathclaw genitals (never shipped): Blender export of the geom json (dc_build.py)
for the rest AND the open state (morph baked in: renders need no shape-key toggling), our shapes transplanted next to
the vanilla body (the body stays untouched: dc_k_female.py's MOUND), then textured renders (feral_tex_render.py, RAW=1
skin space). Her flesh texture: her tile 1001 cropped (D:\\F4Output\\creatures\\dc_kassarawi\\png).
    python -I dc_k_review.py <build dir> <tag>"""
import json
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
from transplant import transplant  # noqa: E402

B = pathlib.Path(sys.argv[1])
TAG = sys.argv[2]
D = pathlib.Path(r'D:\F4Output\creatures\dc')
VAN = D / 'vanilla' / 'deathclaw.nif'
BL = r'D:\F4Tools\blender-5.1.2-windows-x64\blender.exe'
PEN = ('Materials\\Anatomy\\Creatures\\DeathclawVulva.bgsm',
       ['textures\\Anatomy\\Creatures\\DeathclawVulva_d.dds', 'textures\\Anatomy\\Creatures\\DeathclawVulva_n.dds'])
PNG = pathlib.Path(r'D:\F4Output\creatures\dc_kassarawi\png')     # vanilla deathclaw PNGs + her cropped tile
GEOM = sys.argv[3] if len(sys.argv) > 3 else 'geom_female.json'
PENIS = ('Materials\\Anatomy\\Creatures\\DeathclawPenisEquine.bgsm',       # dc_k_penis_tex.py
         ['textures\\Anatomy\\Creatures\\DeathclawPenisEquine_d.dds',
          'textures\\Anatomy\\Creatures\\DeathclawPenisEquine_n.dds'])
SHAPES = {'VulvaLips': ('DeathclawFX:0', None, None), 'VulvaInner': ('DeathclawFX:0', PEN[0], PEN[1]),
          'Base': ('DeathclawFX:0', None, None), 'Penis': ('DeathclawFX:0', PENIS[0], PENIS[1])}
MALE = 'Penis' in open(B / GEOM).read(200000)


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode or 'Traceback' in r.stdout + r.stderr:
        raise SystemExit((r.stdout + r.stderr)[-2000:])
    return r.stdout


G = {k: v for k, v in json.load(open(B / GEOM)).items() if not k.startswith('_')}
morph = 'Erection'
for g in G.values():
    g['verts'] = [[a + b for a, b in zip(v, d)] for v, d in zip(g['verts'], g['morphs'][morph])]
json.dump(G, open(B / ('open_' + GEOM), 'w'))
revs = {}
for state, gj in (('', GEOM), ('o', 'open_' + GEOM)):
    exp = B / f'{pathlib.Path(GEOM).stem}{state}.nif'
    o = run([BL, '-b', '-P', HERE / 'dc_build.py', '--', B / gj, VAN, exp])
    print([line for line in o.splitlines() if line.startswith('BUILT')])
    rev = B / f'review_{TAG}{state}.nif'
    shapes = {k: v for k, v in SHAPES.items() if k in G} or {k: ('DeathclawFX:0', None, None) for k in G}
    info = transplant(VAN, exp, rev, shapes, bodytri=f'Actors\\Deathclaw\\review_{TAG}{state}.tri')
    shutil.copyfile(exp.with_suffix('.tri'), rev.with_suffix('.tri'))
    revs[state] = rev
    print('review nif', rev, info['shapes'])
V = ('pt=0/-8/103/0/-30/34/fbelow,pt=0/-8/103/0.1/-80/34/below,pt=0/-12/98/180/-45/34/bbelow,'
     'pt=0/-8/103/35/-55/34/oblique,pt=0/-5/100/20/-20/110/context')
if MALE:
    V = ('pt=0/20/110/90/-5/75/side,pt=0/8/100/40/-25/62/threeq,pt=0/0/104/0/-20/40/front,'
         'pt=0/0/104/90/-10/30/sheath,pt=0/-5/100/20/-20/110/context')
o = run([BL, '-b', '-P', HERE / 'feral_tex_render.py', '--', 'render', PNG, B / 'shots',
         f'{TAG}|{revs[""]}|{V}|RAW=1;HIDE=tongue', f'{TAG}o|{revs["o"]}|{V}|RAW=1;HIDE=tongue'])
print(sum('Saved' in line for line in o.splitlines()), 'renders ->', B / 'shots')
