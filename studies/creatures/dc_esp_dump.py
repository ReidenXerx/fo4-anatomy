"""Dump Deathclaw_nude.esp: every record, its subrecords (strings readable, form ids hex).
    python -I dc_esp_dump.py <esp>"""
import pathlib
import struct
import sys

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-refit\tools')
import esl  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
pl = esl.Plugin(pathlib.Path(sys.argv[1]))
print('masters', pl.masters)


def subs(d):
    o = 0
    while o + 6 <= len(d):
        t, n = d[o:o + 4], struct.unpack_from('<H', d, o + 4)[0]
        yield t, d[o + 6:o + 6 + n]
        o += 6 + n


for r in pl.records:
    if r[0] != 'R':
        continue
    print(f'{r[2]} {r[3]:08X} flags {r[4]:X}')
    for t, v in subs(pl.body(r)):
        tt = t.decode('latin1')
        if len(v) > 1 and all(32 <= c < 127 for c in v[:-1]) and v[-1] == 0:
            print(f'   {tt} "{v[:-1].decode()}"')
        elif len(v) == 4:
            print(f'   {tt} {struct.unpack("<I", v)[0]:08X}')
        else:
            print(f'   {tt} [{len(v)}] {v[:48].hex()}')
