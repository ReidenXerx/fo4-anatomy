"""UAP's synth penis: rest geometry, bone positions (from the skin-to-bone binds) and what each .tri morph does.
    python -I nick_tri_probe.py"""
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402
import tri_sync  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
NIF = r'D:\F4Output\creatures\nick\src\uap\SynthGen2Body.nif'
TRI = r'D:\Vortex\fallout4\mods\1387286231_UAPv2.6.64-1+2\Meshes\Actors\Synths\SynthGen2Body.tri'
m = nif.Nif(NIF)
s = m.shape('Synt_Gen2_Penis')
P = np.array(s.positions())
bones, xf = m.skin(s)
print('verts', len(P), 'min', P.min(0).round(2), 'max', P.max(0).round(2))
for name, (rot, tr, sc) in zip(bones, xf):
    R = np.array(rot).reshape(3, 3)
    t = np.array(tr)
    # skin->bone: v_bone = R v + t (rows = axes, see nimatrix3 rows note); bone origin in skin space = -R^T t / sc
    o1 = -R.T @ t / sc
    o2 = -R @ t / sc
    print(f'  {name:16s} originT {o1.round(2)}  originN {o2.round(2)}')
# dominant weights per vertex
w = [s.skin_weights(i) for i in range(len(P))]
for name in bones:
    pass
shapes = tri_sync.read(TRI)
for sh, morphs in shapes:
    print('==', sh)
    for name, mult, d in morphs:
        idx = np.array(list(d.keys()))
        dl = np.array(list(d.values()), float) * mult
        mag = np.linalg.norm(dl, axis=1)
        print(f'  {name:14s} n={len(d):5d} mult={mult:.6f} max|d|={mag.max():.2f} mean d={dl.mean(0).round(2)}')
        if sh == 'Synt_Gen2_Penis' and len(idx):
            Q = P.copy()
            Q[idx] += dl
            tip0 = P[np.argmax(P[:, 1])]
            print(f'      rest y-extreme {tip0.round(2)} -> morphed bbox min {Q.min(0).round(2)} max {Q.max(0).round(2)}')
print('weights sample', w[0], w[len(P) // 2])
