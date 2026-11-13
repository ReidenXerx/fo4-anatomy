"""Review build for Immersive Aliens (never shipped): al_geom.py's json -> dc_build.py (Blender, our shape only, skinned
on the alien armature) for rest AND erect (morph baked in), transplanted next to the vanilla Zetan body, the alien's
textures prepared as PNGs (feral_tex_prep.py) + kassarawi's texture, then textured renders (RAW=1 skin space).
    python -I al_review.py <build dir> <tag>"""
import json
import pathlib
import shutil
import subprocess
import sys

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
from transplant import transplant  # noqa: E402

B = pathlib.Path(sys.argv[1])
TAG = sys.argv[2]
A = pathlib.Path(r'D:\F4Output\creatures\alien')
VAN = A / 'vanilla' / 'alien_body.nif'
BL = r'D:\F4Tools\blender-5.1.2-windows-x64\blender.exe'
TEX = pathlib.Path(r'D:\F4Output\incoming\kassarawi-lw-Vp5Da-x\Assets\tenti\Tex')
PNG = A / 'png'


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode or 'Traceback' in r.stdout + r.stderr:
        raise SystemExit((r.stdout + r.stderr)[-2000:])
    return r.stdout


G = json.load(open(B / 'geom.json'))
mat = G['AlienTenta']['mat']
E = json.loads(json.dumps(G))
for g in E.values():
    g['verts'] = [[a + b for a, b in zip(v, d)] for v, d in zip(g['verts'], g['morphs']['Erection'])]
json.dump(E, open(B / 'geom_erect.json', 'w'))
revs = {}
for state, gj in (('', 'geom.json'), ('e', 'geom_erect.json')):
    exp = B / f'alien{state}.nif'
    o = run([BL, '-b', '-P', HERE / 'dc_build.py', '--', B / gj, VAN, exp])
    print([line for line in o.splitlines() if line.startswith('BUILT')])
    rev = B / f'review_{TAG}{state}.nif'
    info = transplant(VAN, exp, rev, {'AlienTenta': ('Alien_01:0', mat[0], mat[1:3])},
                      bodytri=f'Actors\\Alien\\review_{TAG}{state}.tri')
    if exp.with_suffix('.tri').exists():
        shutil.copyfile(exp.with_suffix('.tri'), rev.with_suffix('.tri'))
    revs[state] = rev
    print('review nif', rev, info['shapes'])
# textures: the alien's (game BA2s) + hers
if not (PNG / 'anatomy__creatures__aliententa_d.png').exists():
    tj = B / 'tex.json'
    run([BL, '-b', '-P', HERE / 'feral_tex_render.py', '--', 'list', tj, revs['']])
    run([sys.executable, '-I', HERE / 'feral_tex_prep.py', tj, PNG, B / 'nodata'])
    for src, dst in (('DefaultMaterial_BaseColor.png', 'anatomy__creatures__aliententa_d.png'),
                     ('DefaultMaterial_Normal.png', 'anatomy__creatures__aliententa_n.png')):
        Image.open(TEX / src).convert('RGB').resize((2048, 2048), Image.LANCZOS).save(PNG / dst)
V = ('pt=0/2/-13/0/-10/40/front,pt=0/2/-13/90/-5/40/side,pt=0/2/-13/35/-25/40/q,'
     'pt=0/0/0/20/-5/190/context')
o = run([BL, '-b', '-P', HERE / 'feral_tex_render.py', '--', 'render', PNG, B / 'shots',
         f'{TAG}|{revs[""]}|{V}|RAW=1', f'{TAG}e|{revs["e"]}|{V}|RAW=1'])
print(sum('Saved' in line for line in o.splitlines()), 'renders ->', B / 'shots')
