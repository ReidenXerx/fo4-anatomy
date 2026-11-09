"""For the creatures in the 11-09 lore-genitals list: which body mesh the game loads (loose in Data, else which BA2),
its shapes, and any genital-looking bones/shapes, so the scope says per creature what exists today.
    python -I creature_shapes.py"""
import pathlib
import re
import sys

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import gamedata  # noqa: E402
import nif  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')
TMP = pathlib.Path(r'D:\F4Output\creatures\probe')
GEN = re.compile(r'(?i)penis|genital|vagina|schlong|cock|dick|erect|udder|testic|scrot|balls|sheath|pussy|labia|anus|'
                 r'clit|nipple|breast|boob|nude')
A = 'meshes/actors/'
WANT = {
    'Super mutant': A + 'supermutant/characterassets/supermutantbody.nif',
    'Behemoth': A + 'supermutantbehemoth/characterassets/supermutantbehemoth.nif',
    'Feral ghoul': A + 'feralghoul/characterassets/feralghoul.nif',
    'Yao guai': A + 'yaoguai/characterassets/yaoguai.nif',
    'Dogmeat': A + 'dogmeat/characterassets/dogmeat.nif',
    'Dogmeat nude': A + 'dogmeat/characterassets/dogmeat_nude.nif',
    'Raider dog': A + 'dogmeat/characterassets/raiderdog.nif',
    'Vicious dog': A + 'viciousdog/viciousdog.nif',
    'Radstag': A + 'radstag/characterassets/radstag.nif',
    'Radstag nude': A + 'radstag/characterassets/radstag_nude.nif',
    'Brahmin': A + 'brahmin/characterassets/brahmin.nif',
    'Mole rat': A + 'molerat/characterassets/molerat.nif',
    'Wolf (FH)': A + 'dlc03/mutatedwolf/wolfalpha.nif',
    'Mutant hound': A + 'fevhound/characterassets/fevhound.nif',
    'Nick Valentine': A + 'synths/valentinebody.nif',
}


def main():
    TMP.mkdir(parents=True, exist_ok=True)
    arcs = []
    for p in sorted(DATA.glob('*.ba2'), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            a = gamedata.Ba2(p)
            if a.kind == 'GNRL':
                arcs.append(a)
        except Exception:                                               # noqa: BLE001
            pass
    for who, rel in WANT.items():
        loose = DATA / rel
        holders = [a.path.name for a in arcs if rel in a]
        if loose.exists():
            src, path = 'LOOSE', loose
        elif holders:
            a = next(a for a in arcs if a.path.name == holders[0])
            path = TMP / pathlib.Path(rel).name
            path.write_bytes(a.read(rel))
            src = holders[0]
        else:
            print(f'{who}: NOT FOUND {rel}')
            continue
        try:
            m = nif.Nif(path)
        except Exception as e:                                          # noqa: BLE001
            print(f'{who}: {src} unreadable {e}')
            continue
        shapes = [s.name for s in m.shapes()]
        names = sorted({n['name'] for n in m.nodes.values() if n['name'] and GEN.search(n['name'])} |
                       {s for s in m.strings if s and GEN.search(s)})
        print(f'{who}: {src} (BA2s also: {holders[:3]})\n    shapes {shapes}\n    genital names {names[:14]}')


if __name__ == '__main__':
    main()
