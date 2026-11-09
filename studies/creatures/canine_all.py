"""Canine genitals, every dog / wolf / hound mesh UAP gives a penis (owner: ours replace UAP's, same paths + names):
  1 canine_geom.py: our penis + sheath from UAP's reference tubes + morphs, fitted to the VANILLA body's belly
  2 canine_build.py (Blender): vanilla body + ours (+ '>' morph keys -> PyNifly writes the .tri + BODYTRI)
  3 post: restore vanilla shape transforms, seg_fix (vanilla segment bytes back, ours -> BSSubIndexTriShape single),
    BODYTRI with backslashes like UAP's, verify body shapes == vanilla (positions, UVs, weights) and segments
    python -I canine_all.py [--only name]"""
import argparse
import pathlib
import re
import subprocess
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
sys.path.insert(0, str(HERE))
import nif  # noqa: E402
from feral_all import restore_transforms  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data\meshes')
C = pathlib.Path(r'D:\F4Output\creatures\canine')
OUT = C / 'out8' / 'Data'
BLENDER = r'D:\F4Tools\blender-5.1.2-windows-x64\blender.exe'
DOG = ('actors/dogmeat/characterassets/dogmeat.nif', 'RaiderDog_Penis', 'RaiderDog_Penis_Sheath',
       'actors/dogmeat/characterassets/Dogmeat.tri')
FEV = ('actors/fevhound/characterassets/fevhound.nif', 'RaiderDog_Penis', 'dick_base.001',
       'actors/fevhound/characterassets/FEVHound.tri')
# name, output path (UAP's capitalisation), vanilla source in canine/vanilla, reference, penis, sheath, pelvis, morphs
JOBS = [
    ('Dogmeat', 'Actors/Dogmeat/CharacterAssets/Dogmeat.nif', 'dogmeat.nif', DOG, 'RaiderDog_Penis',
     'RaiderDog_Penis_Sheath', 'Dogmeat_Pelvis', True),
    ('Dogmeat_Nude', 'Actors/Dogmeat/CharacterAssets/Dogmeat_Nude.nif', 'dogmeat.nif', DOG, 'Dogmeat_Part',
     'Dogmeat_Part_Sheath', 'Dogmeat_Pelvis', False),
    ('RaiderDog', 'Actors/Dogmeat/CharacterAssets/RaiderDog.nif', 'raiderdog.nif', DOG, 'RaiderDog_Penis',
     'RaiderDog_Penis_Sheath', 'Dogmeat_Pelvis', True),
    ('RaiderDog_Nude', 'Actors/Dogmeat/CharacterAssets/RaiderDog_Nude.nif', 'raiderdog.nif', DOG, 'RaiderDog_Penis',
     'RaiderDog_Penis_Sheath', 'Dogmeat_Pelvis', False),
    ('ViciousDog', 'Actors/ViciousDog/ViciousDog.nif', 'viciousdog.nif', DOG, 'RaiderDog_Penis',
     'RaiderDog_Penis_Sheath', 'Dogmeat_Pelvis', True),
    ('ViciousDogPackLeader', 'Actors/ViciousDog/ViciousDogPackLeader.nif', 'viciousdogpackleader.nif', DOG,
     'RaiderDog_Penis', 'RaiderDog_Penis_Sheath', 'Dogmeat_Pelvis', True),
    ('WolfAlpha', 'Actors/DLC03/MutatedWolf/WolfAlpha.nif', 'wolfalpha.nif', DOG, 'RaiderDog_Penis',
     'RaiderDog_Penis_Sheath', 'Dogmeat_Pelvis', True),
    ('WolfFuzzy', 'Actors/DLC03/MutatedWolf/WolfFuzzy.nif', 'wolffuzzy.nif', DOG, 'RaiderDog_Penis',
     'RaiderDog_Penis_Sheath', 'Dogmeat_Pelvis', True),
    ('FEVHound', 'Actors/FEVHound/CharacterAssets/FEVHound.nif', 'fevhound.nif', FEV, 'RaiderDog_Penis',
     'dick_base.001', 'Pelvis', True),
]


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    return r.returncode, r.stdout + r.stderr


def bodytri_backslash(path):
    b = bytearray(path.read_bytes())
    n = 0
    for m in re.finditer(rb'[A-Za-z0-9_ ./\\-]{5,}\.tri', b):
        s = m.group(0)
        if b'/' in s:
            b[m.start():m.end()] = s.replace(b'/', b'\\')
            n += 1
    path.write_bytes(bytes(b))
    return n


def verify(van, ours, pen, sh):
    v, d = nif.Nif(van), nif.Nif(ours)
    vs = {s.name: s for s in v.shapes()}
    notes, bad = [], 0
    for s in d.shapes():
        if s.name in (pen, sh):
            notes.append(f'{s.name}:{s.count}v/{d.types[s.index]}')
            continue
        if s.name not in vs:
            notes.append(f'UNEXPECTED {s.name}')
            bad += 1
            continue
        t = vs[s.name]
        dp = np.abs(np.array(s.positions()) - np.array(t.positions())).max()
        du = np.abs(np.array([s.uv(i) for i in range(s.count)]) - np.array([t.uv(i) for i in range(t.count)])).max()
        sb, tb = d.skin(s)[0], v.skin(t)[0]
        dw = 0.0
        for i in range(s.count):
            a = {sb[k]: w for k, w in s.skin_weights(i) if w > 1e-4}
            b = {tb[k]: w for k, w in t.skin_weights(i) if w > 1e-4}
            dw = max(dw, max([abs(a.get(n, 0) - b.get(n, 0)) for n in set(a) | set(b)] or [0]))
        if dp > 1e-3 or du > 1e-3 or dw > 0.01 or s.triangle_count != t.triangle_count:
            notes.append(f'!{s.name} dpos {dp:.4f} duv {du:.4f} dw {dw:.3f}')
            bad += 1
    missing = [n for n in vs if n not in {s.name for s in d.shapes()}]
    if missing:
        notes.append(f'MISSING {missing}')
        bad += 1
    return bad, notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    a = ap.parse_args()
    total = 0
    for name, rel, van, ref, pen, sh, pelvis, morphs in JOBS:
        if a.only and name != a.only:
            continue
        geom = C / f'geom_{name}.json'
        cmd = [sys.executable, '-I', str(HERE / 'canine_geom.py'), str(DATA / ref[0]), ref[1], ref[2],
               str(DATA / ref[3]) if morphs else '-', str(C / 'vanilla' / van), str(geom)] + ([] if morphs else
                                                                                           ['nomorph'])
        rc, out = run(cmd)
        dz = re.search(r'-> dz (\S+)', out)
        if rc:
            print(name, 'GEOM FAILED', out[-800:])
            total += 1
            continue
        dst = OUT / 'meshes' / rel
        if dst.exists():
            raise SystemExit(f'{dst} exists: use a fresh out dir')
        rc, out = run([BLENDER, '-b', '-P', str(HERE / 'canine_build.py'), '--', str(geom), str(C / 'vanilla' / van),
                       str(dst), pen, sh, pelvis], timeout=1800)
        if 'BUILT' not in out:
            print(name, 'BUILD FAILED', out[-1500:])
            total += 1
            continue
        fur = re.search(r'sheath fur from (.*)', out)
        fixed = restore_transforms(C / 'vanilla' / van, dst)
        rc, segout = run([sys.executable, '-I', str(HERE / 'seg_fix.py'), str(C / 'vanilla' / van), str(dst),
                          'single'])
        if rc:
            print(name, 'SEG FIX FAILED', segout[-800:])
            total += 1
            continue
        nb = bodytri_backslash(dst)
        tri = dst.with_suffix('.tri')
        if tri.exists():                                        # BodySlide layout (trailing empty UV section)
            run([sys.executable, '-I', str(HERE / 'tri_normalize.py'), str(tri)])
        for want in (pen, sh):
            got = re.sub(r'\.\d{3}$', '', want)
            if got != want:                                     # PyNifly dropped Blender's '.001'-style suffix
                rc, rout = run([sys.executable, '-I', str(HERE / 'canine_rename.py'), str(dst), got, want])
                if rc:
                    print(name, 'RENAME FAILED', rout[-500:])
                    total += 1
        bad, notes = verify(C / 'vanilla' / van, dst, pen, sh)
        tri = dst.with_suffix('.tri')
        total += bad
        print(f'{name}: dz {dz.group(1) if dz else "?"}, fur {fur.group(1).strip() if fur else "?"}, '
              f'xf restored {len(fixed)}, bodytri fixed {nb}, tri {"yes" if tri.exists() else "no"}; '
              f'{" ".join(notes)} {"OK" if not bad else "PROBLEMS"}')
    print('problems', total)


if __name__ == '__main__':
    main()
