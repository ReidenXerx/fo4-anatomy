"""Dogs / wolves / hounds: for every canine body mesh path any mod ships, which mod's copy is DEPLOYED in the game Data
(sha1 match), its shapes, genital shapes + bones, BODYTRI and the .tri morphs per shape.
    python -I canine_survey.py"""
import hashlib
import pathlib
import re
import sys

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402
import tri_sync  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
MODS = pathlib.Path(r'D:\Vortex\fallout4\mods')
DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')
RX = re.compile(r'meshes/actors/(supermutant|supermutantbehemoth|behemoth)[^/]*/.*\.nif$', re.I)
GEN = re.compile(r'penis|balls|sheath|knot|testic|scrot|vagin|vulva|genital|part', re.I)


def sha(p):
    return hashlib.sha1(p.read_bytes()).hexdigest()


hits = {}
for mod in sorted(MODS.iterdir()):
    if not mod.is_dir():
        continue
    for f in mod.rglob('*.nif'):
        rel = f.relative_to(mod).as_posix()
        i = rel.lower().find('meshes/')
        if i < 0:
            continue
        rel = rel[i:].lower()
        if RX.search(rel) and '1stperson' not in rel and 'armor' not in rel:
            hits.setdefault(rel, []).append(f)
for rel, files in sorted(hits.items()):
    dep = DATA / rel
    live = dep if dep.exists() else next((p for p in DATA.glob('**/*') if p.as_posix().lower().endswith(rel)), None) \
        if False else (dep if dep.exists() else None)
    lsha = sha(live) if live else None
    print(f'== {rel}')
    for f in files:
        mark = 'LIVE' if lsha and sha(f) == lsha else '    '
        print(f'   {mark} {f.parts[len(MODS.parts)]}')
    if not live:
        print('   (not deployed loose)')
        continue
    try:
        m = nif.Nif(live)
    except Exception as e:                                                      # noqa: BLE001
        print('   unreadable', e)
        continue
    shapes = m.shapes()
    print('   shapes', [(s.name, s.count) for s in shapes])
    for s in shapes:
        bones = m.skin(s)[0]
        g = [b for b in bones if b and GEN.search(b)]
        if GEN.search(s.name) or g:
            print(f'   genital shape {s.name}: {s.count}v, genital bones {g}')
    tri = re.findall(rb'BODYTRI.{0,8}?([ -~]{5,}\.tri)', m.b, re.S)
    for t in tri:
        tp = DATA / 'meshes' / t.decode().replace('\\', '/')
        print('   BODYTRI', t.decode(), 'deployed' if tp.exists() else 'MISSING')
        if tp.exists():
            for shname, morphs in tri_sync.read(tp):
                print(f'      tri {shname}: {[n for n, _, _ in morphs]}')
