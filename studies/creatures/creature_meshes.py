"""Creature body meshes (meshes/actors/<creature>/...nif, not animation objects) that Ivy's BA2s and loose mod folders
carry, per creature, so we see who already gives which creature genitals.
    python -I creature_meshes.py"""
import collections
import pathlib
import re
import sys

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import gamedata  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')
STAGING = pathlib.Path(r'D:\Vortex\fallout4\mods')
CRE = re.compile(r'(?i)meshes[\\/]actors[\\/](?!character[\\/])(dlc0\d[\\/])?([^\\/]+)[\\/].*\.nif$')
WATCH = re.compile(r'(?i)supermutant|behemoth|feral|dog|yaoguai|radstag|brahmin|molerat|wolf|hound|valentine|synth|'
                   r'ghoul|deer')
GEN = re.compile(r'(?i)penis|genital|vagina|schlong|cock|dick|erect|udder|nude|naked')

found = collections.defaultdict(set)
for ba2 in sorted(DATA.glob('*.ba2')):
    if re.match(r'(?i)fallout4 - |dlc|cc', ba2.name):
        continue
    try:
        a = gamedata.Ba2(ba2)
    except Exception:                                                   # noqa: BLE001
        continue
    if a.kind != 'GNRL':
        continue
    for n in a.names:
        m = CRE.search(n)
        if m and WATCH.search(n):
            found[m.group(2).lower()].add(f'{ba2.name}: {n}')
for mod in STAGING.iterdir():
    if not mod.is_dir():
        continue
    for q in mod.rglob('*.nif'):
        rel = q.relative_to(mod).as_posix()
        m = CRE.search(rel)
        if m and WATCH.search(rel) and 'animobject' not in rel.lower():
            found[m.group(2).lower()].add(f'LOOSE {mod.name[:45]}: {rel}')
for k in sorted(found):
    print(f'== {k} ({len(found[k])})')
    for line in sorted(found[k])[:12]:
        print('   ', line, '<-- genital name' if GEN.search(line) else '')
