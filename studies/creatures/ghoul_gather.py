"""Ghoul skin job (alasdairn 11-09): find every ghoul skin texture + material the game can load (all BA2s by name,
plus the loose winners in Ivy's staging), copy/extract them to D:\\F4Output\\ghoulskin\\src\\<source>\\<path>, and
print size/format. Read-only on the game and staging.
    python -I ghoul_gather.py"""
import pathlib
import re
import shutil
import struct
import sys

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import gamedata  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')
STAGING = pathlib.Path(r'D:\Vortex\fallout4\mods')
OUT = pathlib.Path(r'D:\F4Output\ghoulskin\src')
PAT = re.compile(r'(textures|materials)[/\\]actors[/\\]character[/\\](custombody[/\\]ghoul|ghoul)', re.I)
SKIP = re.compile(r'child|feral', re.I)
LOOSE_MODS = ['BodyTalk-72310-3-8-1687372211',
              "Caliente's Beautiful Bodies Enhancer - v2.7.2-15-2-7-2-1766404952",
              'CBBE HeadRear Absolute Fix 107187 1 2026-07-21T15-39Z VZ2gWd7k7']


def dds_info(b):
    h, w, mips = struct.unpack_from('<III', b, 12)[0], struct.unpack_from('<I', b, 16)[0], struct.unpack_from('<I', b, 28)[0]
    four = b[84:88]
    fmt = four.decode('latin1')
    if four == b'DX10':
        fmt = f'DXGI{struct.unpack_from("<I", b, 128)[0]}'
    return f'{w}x{h} {fmt} mips{mips}'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for ba2 in sorted(DATA.glob('*.ba2')):
        try:
            arc = gamedata.Ba2(ba2)
        except Exception as e:                                          # noqa: BLE001
            print('skip', ba2.name, e)
            continue
        hits = [n for n in arc.names if PAT.search(n) and not SKIP.search(n)]
        for n in hits:
            blob = arc.read(n)
            dst = OUT / ba2.stem / n.replace('\\', '/')
            if not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(blob)
            print(f'{ba2.name} | {n} | {dds_info(blob) if n.endswith(".dds") else len(blob)}')
    for m in LOOSE_MODS:
        for q in (STAGING / m).rglob('*'):
            rel = q.relative_to(STAGING / m).as_posix().lower()
            if q.is_file() and PAT.search(rel) and not SKIP.search(rel):
                dst = OUT / ('loose_' + m.split('-')[0].split(' 1')[0].strip()) / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(q, dst)
                b = q.read_bytes()
                print(f'LOOSE {m[:30]} | {rel} | {dds_info(b) if rel.endswith(".dds") else len(b)}')


if __name__ == '__main__':
    main()
