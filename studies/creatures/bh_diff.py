"""Behemoth: vanilla body (loincloth) vs UAP's nude body - which vertices are vanilla-only (the loincloth) and which
are UAP-only (skin UAP sculpted under it); open holes of the vanilla lower body once the loincloth is cut away.
    python -I bh_diff.py <vanilla nif> <uap nif>"""
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402

v, u = nif.Nif(sys.argv[1]), nif.Nif(sys.argv[2])
pairs = [('Behemoth_Body_New:1', 'Behemoth_Lower.0011'), ('Behemoth_Body_New:0', 'Behemoth_Upper.0011')]
for vn, un in pairs:
    V, U = np.array(v.shape(vn).positions()), np.array(u.shape(un).positions())
    dv = np.array([np.linalg.norm(U - p, axis=1).min() for p in V])
    du = np.array([np.linalg.norm(V - p, axis=1).min() for p in U])
    vo, uo = np.where(dv > 0.3)[0], np.where(du > 0.3)[0]
    print(f'{vn} ({len(V)}) vs {un} ({len(U)}): vanilla-only {len(vo)}, UAP-only {len(uo)}')
    if len(vo):
        print('   vanilla-only bbox', V[vo].min(0).round(1), V[vo].max(0).round(1))
    if len(uo):
        print('   UAP-only bbox', U[uo].min(0).round(1), U[uo].max(0).round(1))
    # vanilla lower without the vanilla-only vertices: holes
    keep = set(range(len(V))) - set(vo.tolist())
    tris = [t for t in v.shape(vn).triangles() if all(i in keep for i in t)]
    holes = nif.openings(V.tolist(), tris)
    print('   holes after removing vanilla-only:', [(h[0], np.round(h[1], 1).tolist(), np.round(h[2], 1).tolist())
                                                  for h in holes[:6]])
    holes = nif.openings(V.tolist(), v.shape(vn).triangles())
    print('   holes in vanilla as is:', [(h[0], np.round(h[1], 1).tolist(), np.round(h[2], 1).tolist())
                                       for h in holes[:6]])
