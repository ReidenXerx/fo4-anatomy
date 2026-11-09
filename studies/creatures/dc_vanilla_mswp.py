"""Fallout4.esm: the deathclaw skin ARMAs (+ their MO2S material swaps) and every MSWP / ARMO that mentions a deathclaw.
    python -I dc_vanilla_mswp.py"""
import pathlib
import struct
import sys

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-refit\tools')
import esl  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
pl = esl.Plugin(pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data\Fallout4.esm'))


def subs(d):
    o = 0
    while o + 6 <= len(d):
        t, n = d[o:o + 4], struct.unpack_from('<H', d, o + 4)[0]
        yield t, d[o + 6:o + 6 + n]
        o += 6 + n


def show(r, body):
    print(f'{r[2]} {r[3]:08X}')
    for t, v in subs(body):
        tt = t.decode('latin1')
        if len(v) > 1 and all(32 <= c < 127 for c in v[:-1]) and v[-1] == 0:
            print(f'   {tt} "{v[:-1].decode()}"')
        elif len(v) == 4:
            print(f'   {tt} {struct.unpack("<I", v)[0]:08X}')
        else:
            print(f'   {tt} [{len(v)}]')


for r in pl.records:
    if r[0] != 'R' or r[2] not in ('ARMA', 'MSWP', 'ARMO', 'NPC_'):
        continue
    try:
        body = pl.body(r)
    except Exception:                                                               # noqa: BLE001
        continue
    low = body.lower()
    if r[2] == 'NPC_':
        if b'deathclaw' in low and b'matriarch' in low:
            show(r, body)
        continue
    if b'deathclaw' in low:
        show(r, body)
