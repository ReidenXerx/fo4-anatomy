"""Female super mutant armour (Dudu 11-11, option A): every vanilla SM armour/rags/chains piece refitted to the female
body with the SAME field smf_geom.warp() shapes the body with: waist + hips (x scale) and the breast bulge (+ nipple)
along +y. The bulge reaches each armour vertex by its distance from the chest: full within 3 units of the skin, fading
to nothing at 8 (a plate's inner and outer faces move together; plates standing far off the chest stay put).
Positions only, written in place into a copy of the VANILLA nif (from Fallout4 - Meshes.ba2) -> <name>_F.nif.
Check: every armour vertex that sat outside the male chest stays outside the female breasts.
    python -I smf_refit.py <geom json> <out Data>"""
import json
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import gamedata  # noqa: E402
import nif  # noqa: E402
from smf_geom import Body, bulge  # noqa: E402

DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')
VAN = r'D:\F4Output\creatures\sm\vanilla\supermutantbody.nif'
CA = 'meshes/actors/supermutant/characterassets/'
PIECES = ['SMArmor0_Arms', 'SMArmor0_Torso', 'SMArmor1', 'SMArmor1_Arms', 'SMArmor1_Lower', 'SMArmor1_Torso',
          'SMArmor2_Arms', 'SMArmor2_Lower', 'SMArmor2_Torso', 'SMArmor3_Torso', 'SMRags1_Lower', 'SMRags1_Torso',
          'SMRags2_Arms', 'SMRags2_Torso', 'SuicideChains']
NEAR, FAR = 3.0, 8.0


def nipple_bump(x, z, p):
    b = p['breast']
    out = np.zeros(np.shape(x))
    for s in (1, -1):
        out += (b['nipple_h'] + 0.3) * np.exp(-(((x - s * b['cx']) ** 2 + (z - (b['cz'] - b['droop'] * 0.4)) ** 2)
                                               / (2 * b['nipple_r']) ** 2))
    return out


def chest_y(B, x, z):
    h = B.ray(np.array([x, -6.0, z]), np.array([0, 1.0, 0]))
    return None if h is None else float(h[0][1])


def refit(P, p, B):
    P = np.array(P, dtype=float)
    out = P.copy()
    w, h = p['waist'], p['hips']
    k = 1 + (w['k'] - 1) * np.exp(-((P[:, 2] - w['z']) / w['sz']) ** 2) \
        + (h['k'] - 1) * np.exp(-((P[:, 2] - h['z']) / h['sz']) ** 2)
    out[:, 0] = P[:, 0] * k
    bl = bulge(P[:, 0], P[:, 2], p) + nipple_bump(P[:, 0], P[:, 2], p) * (bulge(P[:, 0], P[:, 2], p) > 0)
    gap0 = np.full(len(P), np.inf)
    for i in np.where((bl > 1e-3) & (P[:, 1] > 0))[0]:
        cy = chest_y(B, P[i, 0], P[i, 2])
        if cy is not None:
            gap0[i] = P[i, 1] - cy
    fall = np.clip((FAR - gap0) / (FAR - NEAR), 0, 1)
    out[:, 1] += bl * fall
    return out, gap0, bl


def bind(xf):
    """skin-to-bone as (A 3x3, t): bone = A @ p + t (nif.py stores rotation rows, translation, scale)"""
    r, t, s = xf
    return s * np.array(r, float).reshape(3, 3), np.array(t, float)


def to_body(m, s, body_bind):
    """each vertex of an armour shape in the BODY's skin space, through its own bones (weighted blend of
    body_bind^-1 o armour_bind): pieces bound in another space (the rags) land where they render on the body.
    Returns positions in body space and, per vertex, the blended linear part (to bring displacements back)."""
    names, xf = m.skin(s)
    Y = []
    for n, x in zip(names, xf):
        if n not in body_bind:
            Y.append(None)
            continue
        Aa, ta = bind(x)
        Ab, tb = body_bind[n]
        Abi = np.linalg.inv(Ab)
        Y.append((Abi @ Aa, Abi @ (ta - tb)))
    P = np.array(s.positions())
    Q, L = np.zeros_like(P), np.zeros((len(P), 3, 3))
    for i in range(len(P)):
        acc, lin, tot = np.zeros(3), np.zeros((3, 3)), 0.0
        for slot, w in s.skin_weights(i):
            if w <= 0 or Y[slot] is None:
                continue
            Ml, mt = Y[slot]
            acc += w * (Ml @ P[i] + mt)
            lin += w * Ml
            tot += w
        if tot <= 0:
            raise SystemExit(f'{s.name}: vertex {i} has no bone the body shares')
        Q[i], L[i] = acc / tot, lin / tot
    return P, Q, L


def main():
    p = json.load(open(sys.argv[1].removesuffix('.json') + '.params.json'))
    out = pathlib.Path(sys.argv[2])
    B = Body(VAN)
    vb = nif.Nif(VAN)
    bs = max(vb.shapes(), key=lambda q: q.count)
    body_bind = {n: bind(x) for n, x in zip(*vb.skin(bs))}
    arcs = [gamedata.Ba2(a) for a in sorted(DATA.glob('Fallout4 - Meshes*.ba2'))]
    bad_total = 0
    for name in PIECES:
        rel = f'{CA}{name.lower()}.nif'
        arc = next((a for a in arcs if rel in a), None)
        if arc is None:
            print(f'{name}: not in the vanilla mesh archives')
            continue
        dst = out / 'meshes/Actors/Supermutant/CharacterAssets' / f'{name}_F.nif'
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(arc.read(rel))
        m = nif.Nif(dst)
        moved, bad = 0, 0
        for s in m.shapes():
            if s.skin < 0:
                continue
            S0, P, L = to_body(m, s, body_bind)           # P: body space from here on
            W, gap0, bl = refit(P, p, B)
            D = W - P
            for i in range(len(P)):                        # the displacement back into the shape's own space
                s.set_position(i, S0[i] + np.linalg.solve(L[i], D[i]))
            moved += int((np.linalg.norm(D, axis=1) > 1e-4).sum())
            # outside the male chest before -> outside the female breasts now
            sel = np.where(np.isfinite(gap0) & (gap0 > 0) & (bl > 0.05))[0]
            for i in sel:
                cy = chest_y(B, P[i, 0], P[i, 2])
                dome = cy + bulge(np.array([P[i, 0]]), np.array([P[i, 2]]), p)[0]
                if W[i, 1] < dome - 1e-3:
                    bad += 1
        m.save(dst)
        bad_total += bad
        # a preview copy in the BODY's space (renders beside the body with RAW=1); never shipped
        pv = out.parent / '_preview' / f'{name}_F.nif'
        pv.parent.mkdir(parents=True, exist_ok=True)
        m2 = nif.Nif(dst)
        for s in m2.shapes():
            if s.skin < 0:
                continue
            _, Pb, _ = to_body(m2, s, body_bind)
            for i, q in enumerate(Pb):
                s.set_position(i, q)
        m2.save(pv)
        print(f'{name}_F.nif: {moved} vertices moved, {bad} now inside the breasts')
    print('inside-breast vertices in total:', bad_total)


if __name__ == '__main__':
    main()
