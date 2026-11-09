"""After nick_build.py: restore the vanilla shapes' transforms byte for byte, check every vanilla shape is vanilla
(positions, UVs, triangles; Body:0 weights by bone name), map our exported vertices to nick_geom.py's by position, and
write OUR SynthGen2Body.tri (UAP's morph names, our shapes only; Body:0 is vanilla so it gets none).
    python -I nick_post.py <geom.json> <built.nif> <out Data dir>"""
import json
import pathlib
import shutil
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import nif  # noqa: E402
import tri_sync  # noqa: E402
from feral_all import restore_transforms  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
VAN = r'D:\F4Output\creatures\nick\src\Fallout4 - Meshes\meshes\actors\synths\synthgen2body.nif'
geom_path, built, out = sys.argv[1], sys.argv[2], pathlib.Path(sys.argv[3])
G = json.load(open(geom_path))
dst = out / 'meshes/actors/synths/SynthGen2Body.nif'
dst.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(built, dst)
print('transforms restored', restore_transforms(VAN, dst))
# our skinned shapes: the same (identity) shape transform as vanilla Body:0; their skin binds already equal Body:0's
from feral_all import xf_offset  # noqa: E402

d = nif.Nif(dst)
bo = xf_offset(d, d.shape('Body:0'))
for name in ('Synt_Gen2_Penis', 'Synt_Gen2_PenisJoints'):
    o = xf_offset(d, d.shape(name))
    d.b[o:o + 52] = d.b[bo:bo + 52]
d.save(dst)
v, d = nif.Nif(VAN), nif.Nif(dst)
vs = {s.name: s for s in v.shapes()}
bad = 0
for s in d.shapes():
    if s.name not in vs:
        continue
    t = vs[s.name]
    dp = np.abs(np.array(s.positions()) - np.array(t.positions())).max()
    du = np.abs(np.array([s.uv(i) for i in range(s.count)]) - np.array([t.uv(i) for i in range(t.count)])).max()
    sb, tb = d.skin(s)[0], v.skin(t)[0]
    dw = 0.0
    for i in range(s.count):
        a = {sb[k]: w for k, w in s.skin_weights(i) if w > 1e-4}
        b = {tb[k]: w for k, w in t.skin_weights(i) if w > 1e-4}
        dw = max(dw, max(abs(a.get(n, 0) - b.get(n, 0)) for n in set(a) | set(b)))
    as_uap = ''
    if dw >= 0.01:                                          # differs from vanilla: is it UAP's own (shipped) weight?
        um = nif.Nif(r'D:\F4Output\creatures\nick\src\uap\SynthGen2Body.nif')
        us = um.shape(s.name)
        ub = um.skin(us)[0]
        du_w = 0.0
        for i in range(s.count):
            a = {sb[k]: w for k, w in s.skin_weights(i) if w > 1e-4}
            b = {ub[k]: w for k, w in us.skin_weights(i) if w > 1e-4}
            du_w = max(du_w, max(abs(a.get(n, 0) - b.get(n, 0)) for n in set(a) | set(b)))
        as_uap = f' (vs UAP {du_w:.4f}: {"same as the UAP file Ivy runs today" if du_w < 0.01 else "NEW"})'
    ok = dp < 1e-3 and du < 1e-3 and (dw < 0.01 or 'same as' in as_uap) and s.triangle_count == t.triangle_count
    bad += not ok
    print(f'{s.name}: dpos {dp:.5f} duv {du:.5f} dweight {dw:.4f}{as_uap} tris {t.triangle_count}->{s.triangle_count}',
          '' if ok else 'PROBLEM')
missing = [n for n in vs if n not in {s.name for s in d.shapes()}]
if missing:
    bad += 1
    print('MISSING', missing)
import struct  # noqa: E402

from feral_all import xf_offset  # noqa: E402

UAP = r'D:\F4Output\creatures\nick\src\uap\SynthGen2Body.nif'


def bone_origins(m, s):
    """Each bone's bind origin in the shape's SKIN space (what skinning uses: v_bone = skin-to-bone(v)); the shape's
    own transform is printed apart (PyNifly writes ours as identity, UAP's carries +120.8 z)."""
    print(f'   {s.name} shape translation {np.round(struct.unpack_from("<3f", m.b, xf_offset(m, s)), 3)}')
    out = {}
    for name, (rot, tr, sc) in zip(*m.skin(s)):
        out[name] = -np.array(rot).reshape(3, 3).T @ np.array(tr) / sc
    return out


u = nif.Nif(UAP)
ref = bone_origins(u, u.shape('Synt_Gen2_Penis'))
for name in ('Synt_Gen2_Penis', 'Synt_Gen2_PenisJoints'):
    got = bone_origins(d, d.shape(name))
    # Pelvis_skin: UAP's penis bound it 0.61 off; ours equals vanilla Body:0's (checked against the body instead)
    vb_names, _ = v.skin(v.shape('Body:0'))
    ref = dict(ref, Pelvis_skin=bone_origins(v, v.shape('Body:0'))['Pelvis_skin'])
    diffs = {b: round(float(np.linalg.norm(got[b] - ref[b])), 4) for b in got if b in ref}
    worst = max(diffs.values())
    bad += worst > 0.01
    print(f'{name} bind vs UAP penis bind (= ZeX skeleton): {diffs}', '' if worst <= 0.01 else 'PROBLEM')
shapes = []
for name in ('Synt_Gen2_Penis', 'Synt_Gen2_PenisJoints'):
    s = d.shape(name)
    g = G[name]
    Pe = np.array(s.positions())
    Pg = np.array(g['verts'])
    if len(Pe) == len(Pg) and np.abs(Pe - Pg).max() < 0.05:            # half-float positions (as every shape here)
        idx = np.arange(len(Pe))
        how = f'same order (half-float error {np.abs(Pe - Pg).max():.4f})'
    else:
        idx = np.array([np.argmin(np.linalg.norm(Pg - p, axis=1)) for p in Pe])
        gap = np.linalg.norm(Pg[idx] - Pe, axis=1).max()
        how = f'nearest (max {gap:.4f})'
        if gap > 1e-2:
            raise SystemExit(f'{name}: exported vertices do not match ours (shape space moved?)')
    bones = d.skin(s)[0]
    print(f'{name}: {len(Pe)} verts, {s.triangle_count} tris, {how}, bones {bones}')
    morphs = []
    for mname, D in g['morphs'].items():
        D = np.array(D)[idx]
        mx = np.abs(D).max()
        if mx < 1e-5:
            continue
        mult = mx / 32767.0
        q = np.round(D / mult).astype(int)
        nz = {int(i): tuple(int(x) for x in q[i]) for i in range(len(q)) if np.abs(D[i]).max() > 1e-4}
        morphs.append((mname, mult, nz))
        print(f'    {mname:14s} {len(nz):5d} verts  max {mx:.2f}')
    shapes.append((name, morphs))
tri_sync.write(out / 'meshes/actors/synths/SynthGen2Body.tri', shapes)
back = tri_sync.read(out / 'meshes/actors/synths/SynthGen2Body.tri')
print('tri', [(sh, [n for n, _, _ in ms]) for sh, ms in back])
print('problems', bad)
