"""Copy the meshes that wear the ghoul skin textures (loose in game Data first, else the BA2 that holds them) to
D:\\F4Output\\ghoulskin\\mesh, and print each shape's vertex/triangle counts, UV range, position bounds.
    python -I ghoul_meshes.py"""
import pathlib
import shutil
import sys

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import gamedata  # noqa: E402
import nif  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')
OUT = pathlib.Path(r'D:\F4Output\ghoulskin\mesh')
CA = 'meshes/actors/character/characterassets/'
WANT = [CA + 'femalebody.nif', CA + 'femalehands.nif', CA + 'femaleghoulhead.nif', CA + 'faceparts/femaleheadrear.nif',
        CA + 'malebody.nif', CA + 'malehands.nif', CA + 'maleghoulhead.nif', CA + 'faceparts/maleghoulheadrear.nif',
        CA + 'femalehead.nif']
ARCHIVES = ['CBBEHolyFix - Main.ba2', 'Fallout4 - Meshes.ba2', 'Fallout4 - MeshesExtra.ba2']


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    arcs = []
    for n in ARCHIVES:
        if (DATA / n).exists():
            arcs.append(gamedata.Ba2(DATA / n))
    for rel in WANT:
        dst = OUT / pathlib.Path(rel).name
        loose = DATA / rel
        src = None
        if loose.exists():
            shutil.copy2(loose, dst)
            src = 'loose'
        else:
            for a in arcs:
                if rel in a:
                    dst.write_bytes(a.read(rel))
                    src = a.path.name
                    break
        if not src:
            print('MISSING', rel)
            continue
        m = nif.Nif(dst)
        print(f'{dst.name} <- {src}')
        for s in m.shapes():
            try:
                ps = s.positions()
                uvs = [s.uv(i) for i in range(s.count)]
            except Exception as e:                                      # noqa: BLE001
                print(f'   {s.name}: unreadable ({e})')
                continue
            xs, ys, zs = zip(*ps)
            us, vs = zip(*uvs)
            print(f'   {s.name}: v{s.count} t{s.triangle_count} full={s.full} uv u[{min(us):.3f},{max(us):.3f}] '
                  f'v[{min(vs):.3f},{max(vs):.3f}] pos x[{min(xs):.1f},{max(xs):.1f}] y[{min(ys):.1f},{max(ys):.1f}] '
                  f'z[{min(zs):.1f},{max(zs):.1f}]')


if __name__ == '__main__':
    main()
