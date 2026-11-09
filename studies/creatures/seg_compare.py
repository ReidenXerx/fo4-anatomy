"""Structure check after seg_fix.py: for every shape the vanilla mesh also has, the segment layout must match vanilla
(segment count, sub-segment counts, parent indices, per-segment user index + bone id, cut offsets within 0.01, ssf);
only start/count numbers may differ (sculpted shapes have more triangles). New shapes must be sub-index.
    python -I seg_compare.py <vanilla dir> <ours dir> [suffix strip, default _F]"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import importlib.util  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
spec = importlib.util.spec_from_file_location('segdump', pathlib.Path(__file__).resolve().parent / 'seg_dump.py')
sd = importlib.util.module_from_spec(spec)
_argv = sys.argv
sys.argv = ['x', __file__.replace('seg_compare.py', 'seg_dump.py')]           # seg_dump runs a demo on import
src = (pathlib.Path(__file__).resolve().parent / 'seg_dump.py').read_text()
ns = {}
exec(compile(src.split('\na = segs(')[0], 'seg_dump', 'exec'), ns)
segs = ns['segs']
sys.argv = _argv
van, ours = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
bad = 0
for f in sorted(ours.glob('*.nif')):
    base = f.stem.removesuffix('_F')
    a, b = segs(van / f'{base}.nif'), segs(f)
    for name, d in b.items():
        if name not in a:
            if d is None:
                print(f'{f.name} {name}: NEW shape is not sub-index')
                bad += 1
            continue
        e = a[name]
        if (e is None) != (d is None):
            print(f'{f.name} {name}: type differs')
            bad += 1
            continue
        if e is None:
            continue
        lay = lambda x: [(s[2], len(s[3]), [q[2] for q in s[3]]) for s in x['seg']]           # noqa: E731
        sh = lambda x: None if not x['shared'] else (x['shared']['starts'], x['shared']['ssf'],  # noqa: E731
                                                     [(p[0], p[1], len(p[2])) for p in x['shared']['per']])
        cuts = lambda x: [] if not x['shared'] else [c for p in x['shared']['per'] for c in p[2]]  # noqa: E731
        ok = lay(d) == lay(e) and sh(d) == sh(e) and all(abs(p - q) < 0.01 for p, q in zip(cuts(d), cuts(e)))
        if not ok:
            bad += 1
            print(f'{f.name} {name}: LAYOUT DIFFERS layout {lay(d) == lay(e)} shared {sh(d) == sh(e)}')
print('files', len(list(ours.glob('*.nif'))), 'problems', bad)
