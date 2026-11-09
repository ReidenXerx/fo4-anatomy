"""Does our deathclaw vent sit on each body? Distance from every vent-lip vertex (our DeathclawMale.nif 'Base', skin
space) to the nearest body vertex, per body nif; the vanilla base deathclaw is the reference.
    python -I dc_fit_check.py"""
import pathlib
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402

V = pathlib.Path(r'D:\F4Output\creatures\dc\vanilla')
S = pathlib.Path(r'D:\F4Output\creatures\dc\ivy_survey')
ours = np.array(nif.Nif(r'D:\F4Output\creatures\dc\sa\Data\meshes\Actors\Deathclaw\Anatomy\DeathclawMale.nif')
                .shape('Base').positions())
for p in [V / 'deathclaw.nif', V / 'deathclaw_alpha.nif', V / 'deathclaw_savage.nif', V / 'deathclaw_albino.nif',
          V / 'deathclaw_matriarch.nif', V / 'deathclawchameleon.nif'] + sorted(S.glob('*.nif')):
    m = nif.Nif(p)
    body = max(m.shapes(), key=lambda s: s.count)
    B = np.array(body.positions())
    d = np.array([np.sqrt(((B - q) ** 2).sum(1)).min() for q in ours])
    print(f'{p.name:32s} {body.name:24s} {len(B):6d}v  vent->body median {np.median(d):.2f} p95 {np.percentile(d, 95):.2f}'
          f' max {d.max():.2f}')
