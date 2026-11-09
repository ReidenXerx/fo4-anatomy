"""UAP deathclaw Penis: centreline + mean radius per state (bins fixed by the ERECT axis), so ours can follow each
morph.  python -I dc_states.py"""
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402
import tri_sync  # noqa: E402

UAP = r'D:\SteamFreeGames\Fallout 4 AE\Data\meshes\actors\Deathclaw\DeathclawPenis'
m = nif.Nif(UAP + '.nif')
tri = {s: {n: (mu, d) for n, mu, d in ms} for s, ms in tri_sync.read(UAP + '.tri')}
NB = 8


def delta(shape, P, name):
    D = np.zeros_like(P)
    mu, d = tri[shape][name]
    for i, v in d.items():
        D[i] = np.array(v, float) * mu
    return D


P = np.array(m.shape('Penis').positions())
E = P + delta('Penis', P, 'Erection')
c0 = E.mean(0)
ax = np.linalg.svd(E - c0, full_matrices=False)[2][0]
if ax[1] < 0:
    ax = -ax
proj = (E - c0) @ ax
bins = np.minimum(((proj - proj.min()) / np.ptp(proj) * NB).astype(int), NB - 1)
print('erect axis', ax.round(3), 'length', round(float(np.ptp(proj)), 1))


def line(Q, label):
    cs = np.array([Q[bins == b].mean(0) for b in range(NB)])
    rs = [np.linalg.norm(Q[bins == b] - cs[b], axis=1).mean() for b in range(NB)]
    print(f'{label:16s}', ' '.join(f'({c[1]:5.1f},{c[2]:5.1f})' for c in cs))
    print(f'{"":16s}', ' '.join(f'{r:13.1f}' for r in rs), ' x range', round(float(np.abs(cs[:, 0]).max()), 2))
    return cs


line(P, 'rest')
line(E, 'E')
for n in ('Erection Up', 'Erection Down', 'Length', 'Penis Adjust', 'Scale'):
    line(E + delta('Penis', P, n), 'E+' + n)
    line(P + delta('Penis', P, n), 'rest+' + n)
B = np.array(m.shape('Base').positions())
for n in ('Erection', 'Penis Adjust', 'Scale'):
    D = delta('Base', B, n)
    mv = np.linalg.norm(D, axis=1)
    k = mv > 0.3 * mv.max()
    print('Base', n, 'max', mv.max().round(2), 'mean dir of big movers', D[k].mean(0).round(2),
          'at', B[k].mean(0).round(1), 'n', k.sum())
