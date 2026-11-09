"""Per FO4 nif: each shape's type and, for BSSubIndexTriShape, its segment/sub-segment counts and SSF path.
    python -I segments.py <nif or folder> [...]   (folders: every *.nif below, summary per file)"""
import pathlib
import struct
import sys

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif as N  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def seg_info(n, i):
    o, size = n.offsets[i]
    c = N.Cursor(n.b, o)
    name, *_ = n._av(c)
    c.take('4f')
    c.take('i'); c.take('i'); c.take('i')
    desc = c.take('Q')
    ntri = c.take('I')
    nv = c.take('H')
    dsize = c.take('I')
    stride = (desc & 0xF) * 4
    if dsize == 0:
        return name, 'no data'
    c.o += nv * stride + ntri * 6
    nprim, nseg, total = c.take('I'), c.take('I'), c.take('I')
    subs = 0
    for _ in range(nseg):
        c.take('I'); c.take('I'); c.take('I')
        k = c.take('I')
        subs += k
        c.o += k * 16
    ssf = ''
    if nseg < total:
        ns2, tot2 = c.take('I'), c.take('I')
        c.o += ns2 * 4
        for _ in range(tot2):
            c.take('I'); c.take('I')
            nd = c.take('I')
            c.o += nd * 4
        ln = c.take('H')
        ssf = n.b[c.o:c.o + ln].decode('latin1')
    return name, f'segments {nseg}, sub-segments {subs}, total {total}, ssf {ssf!r}'


def report(path, brief):
    try:
        n = N.Nif(path)
    except Exception as e:
        print(f'{path}: unreadable ({e})')
        return
    lines = []
    for i, k in enumerate(n.types):
        if k == 'BSSubIndexTriShape':
            try:
                lines.append(('SITS',) + seg_info(n, i))
            except Exception as e:
                lines.append(('SITS', '?', f'parse error {e}'))
        elif k in N.SHAPES:
            o, _ = n.offsets[i]
            lines.append((k, n._av(N.Cursor(n.b, o))[0], ''))
    if brief:
        sits = [l for l in lines if l[0] == 'SITS']
        segd = [l for l in sits if 'segments 0,' not in l[2] and 'no data' not in l[2]]
        print(f'{path.name}: shapes {len(lines)}, SITS {len(sits)}, with segments {len(segd)}'
              + ('' if not segd else f"; e.g. {segd[0][1]}: {segd[0][2]}"))
    else:
        print(path)
        for l in lines:
            print('  ', *l)


for a in sys.argv[1:]:
    p = pathlib.Path(a)
    if p.is_dir():
        for f in sorted(p.rglob('*.nif')):
            report(f, True)
    else:
        report(p, False)
