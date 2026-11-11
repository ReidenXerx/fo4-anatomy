"""Female super mutant body (Dudu 11-11): smf_geom's shapes -> dc_build (Blender, our shapes only) -> seg_fix single
-> transplant onto the VANILLA SupermutantBody.nif -> the body warp written in place (positions only; topology,
segments, skin untouched) -> SupermutantBody_F.nif (the female model the plugin assigns).
    python -I smf_build.py <geom json> <out Data>"""
import json
import pathlib
import subprocess
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402
from smf_geom import warp  # noqa: E402
from transplant import transplant  # noqa: E402

BL = r'D:\F4Tools\blender-5.1.2-windows-x64\blender.exe'
VAN = pathlib.Path(r'D:\F4Output\creatures\sm\vanilla\supermutantbody.nif')
REL = 'meshes/Actors/Supermutant/CharacterAssets/SupermutantBody_F.nif'


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(' '.join(map(str, cmd))[:200] + '\n' + r.stdout[-1500:] + r.stderr[-1500:])
    return r.stdout


geom, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
params = json.load(open(str(geom).removesuffix('.json') + '.params.json'))
G = json.load(open(geom))
exp = geom.parent / 'build' / 'smf_export.nif'
exp.parent.mkdir(parents=True, exist_ok=True)
run([BL, '-b', '-P', HERE / 'dc_build.py', '--', geom, VAN, exp])
run([sys.executable, '-I', HERE / 'seg_fix.py', VAN, exp, 'single'])
body = max(nif.Nif(VAN).shapes(), key=lambda s: s.count).name
dst = out / REL
dst.parent.mkdir(parents=True, exist_ok=True)
new = {k: (body, v['mat'][0], v['mat'][1:]) if 'mat' in v else (body, None, None) for k, v in G.items()}
info = transplant(VAN, exp, dst, new)
m = nif.Nif(dst)
s = next(q for q in m.shapes() if q.name == body)
P = np.array(s.positions())
W = warp(P, params)
for i, p in enumerate(W):
    s.set_position(i, p)
m.save(dst)
moved = np.linalg.norm(W - P, axis=1)
print('->', dst, info['shapes'][-6:], '| body verts moved', int((moved > 1e-4).sum()), 'max', round(float(moved.max()), 2))
