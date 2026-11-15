"""Our own morph names on every ANIMAL creature mesh (Dudu 2026-11-16, see docs/creature-morphs.md).
UAP's / darthroman's names ('Erection', ...) let the AAF creature packs drive our meshes; ours ('Anatomy Aroused', ...)
are driven only by our own future behaviour (same-species mating). Run it LAST on every animal build, after
tri_normalize / transplant, and before packing. Humanoids (super mutants, behemoths, synths, ghouls) are out of scope.
Rewrites each .tri in place: same shapes, same deltas, only the morph names change; re-read and compared.
    python -I morph_rename.py <folder> [...]        (every .tri below each folder)
    python -I morph_rename.py --check <folder> [...]  (report only: any UAP name left = exit 1)"""
import pathlib
import sys
import tempfile

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import tri_sync  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
MAP = {
    'Erection': 'Anatomy Aroused',
    'Erection Up': 'Anatomy Aroused Up',
    'Erection Down': 'Anatomy Aroused Down',
    'Penis Adjust': 'Anatomy Adjust',
    'Scale': 'Anatomy Scale',
    'Length': 'Anatomy Length',
}
OURS = set(MAP.values())


def lossless(path):
    """tri_sync.write(read(x)) must reproduce x byte for byte, else renaming through it could change the morphs"""
    with tempfile.TemporaryDirectory() as d:
        t = pathlib.Path(d) / 'x.tri'
        tri_sync.write(t, tri_sync.read(path))
        return t.read_bytes() == pathlib.Path(path).read_bytes()


def rename(path, check):
    shapes = tri_sync.read(path)
    left = sorted({n for _, ms in shapes for n, _, _ in ms if n not in OURS})
    if check:
        return left
    unknown = [n for n in left if n not in MAP]
    if unknown:
        raise SystemExit(f'{path}: morph names with no mapping {unknown} - add them to MAP and the doc first')
    if not left:
        return []
    if not lossless(path):
        raise SystemExit(f'{path}: tri_sync round trip is not byte-identical, not touching it')
    new = [(s, [(MAP.get(n, n), mu, d) for n, mu, d in ms]) for s, ms in shapes]
    tri_sync.write(path, new)
    back = tri_sync.read(path)
    assert [(s, [(mu, d) for _, mu, d in ms]) for s, ms in back] == [(s, [(mu, d) for _, mu, d in ms]) for s, ms in shapes]
    assert all(n in OURS for _, ms in back for n, _, _ in ms)
    return left


def main():
    args = sys.argv[1:]
    check = '--check' in args
    bad = 0
    for root in [pathlib.Path(a) for a in args if a != '--check']:
        for t in sorted(root.rglob('*.tri')):
            left = rename(t, check)
            if left:
                print(('UAP NAMES ' if check else 'renamed ') + str(t.relative_to(root)), left)
                bad += check
    print('problems', bad)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
