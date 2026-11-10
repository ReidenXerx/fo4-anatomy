"""Female creature meshes (Dudu 11-10): per body, fem_geom (vulva + teats on the vanilla body) -> dc_build (Blender,
our shapes only) -> seg_fix single -> transplant onto the VANILLA body -> <Name>_F.nif (the female model the plugin
assigns). No morphs. Material: lips + teats a copy of the body's own shader, inner the CaninePenis flesh.
    python -I fem_all.py <out Data> [job ...]"""
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from transplant import transplant  # noqa: E402

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402

out = pathlib.Path(sys.argv[1])
C = pathlib.Path(r'D:\F4Output\creatures')
F = C / 'fem'
BL = r'D:\F4Tools\blender-5.1.2-windows-x64\blender.exe'
FLESH = ('Materials\\Anatomy\\Creatures\\CaninePenis.bgsm',
         ['textures\\Anatomy\\Creatures\\CaninePenis_d.dds', 'textures\\Anatomy\\Creatures\\CaninePenis_n.dds',
          'textures\\Anatomy\\Creatures\\CaninePenis_s.dds'])


def teats(ys, x, r, h):
    return [[y, s * x, r, h] for y in ys for s in (1, -1)]


import fem_auto  # noqa: E402

DOG = 72.9                       # the raider dog's height: the reference size the dog's hand-tuned sizes were made at
SPECIES = {  # name: (vanilla nif, output path under meshes, teat pairs, teat layout)
    'raiderdog': (C / 'canine/vanilla/raiderdog.nif', 'Actors/Dogmeat/CharacterAssets/RaiderDog_F.nif', 5, 'row'),
    'viciousdog': (C / 'canine/vanilla/viciousdog.nif', 'Actors/ViciousDog/ViciousDog_F.nif', 5, 'row'),
    'viciousdogpackleader': (C / 'canine/vanilla/viciousdogpackleader.nif',
                             'Actors/ViciousDog/ViciousDogPackLeader_F.nif', 5, 'row'),
    'wolfalpha': (C / 'canine/vanilla/wolfalpha.nif', 'Actors/DLC03/MutatedWolf/WolfAlpha_F.nif', 5, 'row'),
    'wolffuzzy': (C / 'canine/vanilla/wolffuzzy.nif', 'Actors/DLC03/MutatedWolf/WolfFuzzy_F.nif', 5, 'row'),
    'fevhound': (C / 'canine/vanilla/fevhound.nif', 'Actors/FEVHound/CharacterAssets/FEVHound_F.nif', 4, 'row'),
    'yaoguai': (C / 'yg/vanilla/yaoguai.nif', 'Actors/YaoGuai/CharacterAssets/YaoGuai_F.nif', 3, 'row'),
    'yaoguaishaggy': (C / 'yg/vanilla/yaoguaishaggy.nif', 'Actors/YaoGuai/CharacterAssets/YaoGuaiShaggy_F.nif', 3, 'row'),
    'radstagdoe': (C / 'fem/vanilla/radstagdoe.nif', 'Actors/RadStag/CharacterAssets/RadStagDoe_F.nif', 2, 'udder'),
    'molerat': (C / 'mr/vanilla/molerat.nif', 'Actors/Molerat/CharacterAssets/Molerat_F.nif', 4, 'row'),
    'molerat01': (C / 'mr/vanilla/molerat01.nif', 'Actors/Molerat/CharacterAssets/Molerat01_F.nif', 4, 'row'),
    'molerat02': (C / 'mr/vanilla/molerat02.nif', 'Actors/Molerat/CharacterAssets/Molerat02_F.nif', 4, 'row'),
    'broodmother': (C / 'fem/vanilla/broodmother.nif', 'Actors/Molerat/CharacterAssets/Broodmother_F.nif', 5, 'row'),
}


# per body: a measured vulva height and size where the automatic rear face is wrong (the wolves' tail hangs down
# over the rump and merges with it: above ~z 47 the "face" is the tail's underside)
OVERRIDE = {'wolfalpha': {'z': 43.2, 'k': 0.75}, 'wolffuzzy': {'z': 43.2, 'k': 0.75},
            'molerat': {'z': 20.5, 'k': 1.3}, 'molerat01': {'z': 20.5, 'k': 1.3}, 'molerat02': {'z': 20.5, 'k': 1.3},
            'broodmother': {'z': 18.5, 'k': 1.0},  # mole rats: a low tail too
            'fevhound': {'z': 51.5, 'k': 1.0},
            'yaoguai': {'z': 61.0, 'k': 1.4, 'open': 1.8},   # dark painted fur swallows a dog-sized slit
            'yaoguaishaggy': {'z': 61.0, 'k': 1.4, 'open': 1.8}}      # below z ~49 the FEV rump curls under into a deep midline crease


def fur_hole(dst, G, body):
    """fur shells (yao guai) float ~1.5 above the skin: collapse their triangles over the vulva (fixed-size edit)"""
    import struct
    import numpy as np
    L = np.array(G['FemVulvaLips']['verts'])
    lo, hi = L.min(0) - [0.8, 4.0, 0.8], L.max(0) + [0.8, 4.0, 0.8]
    m = nif.Nif(dst)
    n = 0
    for s in m.shapes():
        if s.name == body or 'fur' not in s.name.lower():
            continue
        P = np.array(s.positions())
        o = s.data_at + s.count * s.stride
        for k, t in enumerate(s.triangles()):
            c = P[list(t)].mean(0)
            if (c > lo).all() and (c < hi).all():
                struct.pack_into('<3H', m.b, o + 6 * k, t[0], t[0], t[0])
                n += 1
    if n:
        m.save(dst)
    return n


def params_for(van, pairs, layout, name=None):
    """vulva at 22 % up the rump's rear face, sizes scaled from the hand-tuned raider dog; teats on the belly line"""
    L = fem_auto.landmarks(str(van))
    k = L['size'] / DOG
    z0, z1 = L['face']
    vz = max(z0 + 0.22 * (z1 - z0), z0 + 1.5 * 3.0 * k + 0.5)      # the whole lens must stay on the rear face
    if name in OVERRIDE:
        vz, k = OVERRIDE[name]['z'], k * OVERRIDE[name]['k']
    B = L['B']
    length = B[:, 1].max() - B[:, 1].min()
    pel = L['pelvis']
    iz = pel[2]
    # the belly: midline underside from the pelvis forward; its low, continuous run (legs/chest excluded)
    line = [(y, z) for y, z in fem_auto.belly(L, pel[1], pel[1] + 0.65 * length, 0.0, iz, n=40) if z is not None]
    zmin = min(z for _, z in line)
    low = [(y, z) for y, z in line if z < zmin + 0.12 * L['size']]
    ya, yb = low[0][0], low[-1][0]
    if layout == 'udder':                               # between the hind legs, close together
        ys = [ya + 0.06 * length, ya + 0.12 * length]
        xo = 0.02 * L['size']
    else:
        span = yb - ya
        ys = [ya + span * (0.1 + 0.8 * i / max(pairs - 1, 1)) for i in range(pairs)]
        xo = 0.033 * L['size']
    return {'vulva': {'z': round(vz, 2), 'inside_y': L['inside_y'], 'depth': round(0.08 * L['size'], 2),
                      'a0': 1.5 * k, 'b0': 0.3 * k * OVERRIDE.get(name, {}).get('open', 1.0), 'L': 3.0 * k, 'W': 2.5 * k, 'H': 0.95 * k},
            'teat_inside_z': iz, 'teats': teats([round(y, 2) for y in ys], xo, 0.0068 * L['size'], 0.011 * L['size'])}


JOBS = {n: (v, rel, None) for n, (v, rel, _, _) in SPECIES.items()}


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(' '.join(map(str, cmd))[:200] + '\n' + r.stdout[-1500:] + r.stderr[-1500:])
    return r.stdout


for name in (sys.argv[2:] or list(JOBS)):
    van, rel, _, layout = SPECIES[name][0], SPECIES[name][1], None, SPECIES[name][3]
    params = params_for(van, SPECIES[name][2], layout, name)
    pj = F / f'{name}.json'
    json.dump(params, open(pj, 'w'))
    geom = F / f'geom_{name}.json'
    print(name, run([sys.executable, '-I', HERE / 'fem_geom.py', van, geom, pj]).strip().replace('\n', '; '))
    exp = F / 'build' / f'{name}.nif'
    run([BL, '-b', '-P', HERE / 'dc_build.py', '--', geom, van, exp])
    run([sys.executable, '-I', HERE / 'seg_fix.py', van, exp, 'single'])
    G = json.load(open(geom))
    vs = nif.Nif(van).shapes()
    shell = lambda s: any(k in s.name.lower() for k in ('dirt', 'fur', 'cap'))   # noqa: E731
    body = max((s for s in vs if not shell(s)), key=lambda s: s.count).name       # the SKIN, never an overlay shell
    dirt = [s for s in vs if 'dirt' in s.name.lower()]
    dirt_copies = {}
    if dirt:                     # mole rats: pink skin under an alpha dirt shell; our skin pieces get a dirt copy too
        import numpy as np
        for k in ('FemVulvaLips', 'FemTeats'):
            g = dict(G[k])
            N = np.array(g['normals'])
            if k == 'FemVulvaLips':              # lift along the vulva's outward axis: per-vertex rim normals lean
                ax = N.mean(0)                   # into the slit and close the narrow opening
                N = np.tile(ax / np.linalg.norm(ax), (len(N), 1))
            g['verts'] = (np.array(g['verts']) + 0.12 * N).round(5).tolist()
            G[k + 'Dirt'] = g
            dirt_copies[k + 'Dirt'] = (dirt[0].name, None, None, True)
        json.dump(G, open(geom, 'w'))
        run([BL, '-b', '-P', HERE / 'dc_build.py', '--', geom, van, exp])
        run([sys.executable, '-I', HERE / 'seg_fix.py', van, exp, 'single'])
    dst = out / 'meshes' / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    new = {k: (body, FLESH[0], FLESH[1]) if k in ('FemVulvaInner', 'FemTeatTips') else (body, None, None) for k in G}
    new.update(dirt_copies)
    info = transplant(van, exp, dst, new)
    print('  ->', dst.relative_to(out), info['shapes'][-3:], info['blocks'], 'fur hole tris', fur_hole(dst, G, body))
