"""Generate Anatomy.esp: one quest running Anatomy:Arousal, and the keyword its morph layer uses (A-16).

The shape is fo4-silhouette's make_esp.py (itself fo4-chemistry's, read out of AAF.esm's
AAF_MainQuest): a QUST whose VMAD names one script with no properties and no fragments, DNAM
"start game enabled" at priority 100. Both plugins run in the owner's game. The script finds every
form it needs at run time (Game.GetFormFromFile), so nothing is filled in here.

The keyword is the LooksMenu layer key: our nipple values live under it, apart from Silhouette's
(unkeyed) and AAF's. Its fields are a vanilla 131-version KYWD's (Fallout4.esm 0024A351): EDID,
CNAM (colour), TNAM (type 0).

Flagged LIGHT (TES4 0x200): no load-order slot; object ids 0x800-0xFFF (0x800 and 0x801 here).

    python tools/make_esp.py build/plugin/Anatomy.esp
    python tools/make_esp.py --verify <plugin>          (package, restage and release call verify())
"""
import pathlib
import struct
import sys

SCRIPT = 'Anatomy:Arousal'
QUEST_EDID = 'AnatomyArousalQuest'
LAYER_EDID = 'AnatomyArousalLayer'
AUTHOR = 'fo4-anatomy'
MASTER = 'Fallout4.esm'
QUEST_ID = 0x01000800
LAYER_ID = 0x01000801          # Anatomy:Arousal reads it back as 0x801 of Anatomy.esp
TES4_LIGHT = 0x200


def field(sig, data):
    return sig.encode('ascii') + struct.pack('<H', len(data)) + data


def zstring(text):
    return text.encode('ascii') + b'\0'


def wstring(text):
    raw = text.encode('ascii')
    return struct.pack('<H', len(raw)) + raw


def record(sig, form_id, blob, flags=0):
    return (sig.encode('ascii') + struct.pack('<III', len(blob), flags, form_id)
            + struct.pack('<IHH', 0, 131, 0) + blob)


def group(label, blob):
    return (b'GRUP' + struct.pack('<I', 24 + len(blob)) + label.encode('ascii')
            + struct.pack('<I', 0) + struct.pack('<IHH', 0, 0, 0) + blob)


def build():
    vmad = struct.pack('<hhH', 6, 2, 1) + wstring(SCRIPT) + struct.pack('<B', 0) + struct.pack('<H', 0)
    quest = (field('EDID', zstring(QUEST_EDID)) + field('VMAD', vmad)
             + field('DNAM', bytes.fromhex('110064670000000000000000')) + field('NEXT', b''))
    layer = (field('EDID', zstring(LAYER_EDID)) + field('CNAM', bytes.fromhex('ffffff00'))
             + field('TNAM', struct.pack('<I', 0)))
    body = group('KYWD', record('KYWD', LAYER_ID, layer)) + group('QUST', record('QUST', QUEST_ID, quest))
    hedr = struct.pack('<fiI', 1.0, 4, LAYER_ID + 1)          # version, records + groups, next object id
    header = (field('HEDR', hedr) + field('CNAM', zstring(AUTHOR))
              + field('MAST', zstring(MASTER)) + field('DATA', struct.pack('<Q', 0)))
    return record('TES4', 0, header, flags=TES4_LIGHT) + body


def records(blob):
    """(signature, form id, flags, EDID or None) of every record in a plugin, TES4 included."""
    out = []

    def walk(pos, end):
        while pos < end:
            sig = blob[pos:pos + 4].decode('ascii', 'replace')
            size = struct.unpack_from('<I', blob, pos + 4)[0]
            if sig == 'GRUP':                               # size counts its own 24-byte header
                walk(pos + 24, pos + size)
                pos += size
                continue
            flags, form_id = struct.unpack_from('<II', blob, pos + 8)
            data, edid, f = blob[pos + 24:pos + 24 + size], None, 0
            while f + 6 <= len(data) and not flags & 0x40000:   # compressed records keep no plain EDID
                fsig, fsize = data[f:f + 4], struct.unpack_from('<H', data, f + 4)[0]
                if fsig == b'EDID':
                    edid = data[f + 6:f + 6 + fsize].rstrip(b'\0').decode('ascii', 'replace')
                    break
                f += 6 + fsize
            out.append((sig, form_id, flags, edid))
            pos += 24 + size

    walk(0, len(blob))
    return out


def verify(path):
    """Refuse a plugin that must not ship as Anatomy.esp. LooksMenu stores our nipple values under the
    keyword 0x801 and, on load, looks the keyword up by plugin NAME and form id: a plugin of this name
    without that keyword (an older build, a renumbered one) files every stored value under key 0, the
    woman's own body, for good (f4ee BodyMorphInterface.cpp, read by the Silhouette session
    2026-09-23). Removing the plugin entirely is safe; shipping a wrong one is not."""
    blob = pathlib.Path(path).read_bytes()
    found = records(blob)
    problems = []
    if not found or found[0][0] != 'TES4' or not found[0][2] & TES4_LIGHT:
        problems.append('not a light plugin')
    by_id = {(sig, form_id): edid for sig, form_id, _, edid in found}
    if by_id.get(('KYWD', LAYER_ID)) != LAYER_EDID:
        problems.append(f'no KYWD {LAYER_ID:08X} "{LAYER_EDID}" (the LooksMenu layer key)')
    if by_id.get(('QUST', QUEST_ID)) != QUEST_EDID:
        problems.append(f'no QUST {QUEST_ID:08X} "{QUEST_EDID}"')
    if problems:
        raise SystemExit(f'{path} must not ship as Anatomy.esp: {"; ".join(problems)}')
    return f'{path}: KYWD {LAYER_ID:08X} {LAYER_EDID}, QUST {QUEST_ID:08X} {QUEST_EDID}, light'


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    out = pathlib.Path(sys.argv[1])
    out.parent.mkdir(parents=True, exist_ok=True)
    if sys.argv[1] == '--verify':
        print(verify(sys.argv[2]))
        return 0
    blob = build()
    out.write_bytes(blob)
    verify(out)
    print(f'wrote {out} ({len(blob)} bytes): light; keyword {LAYER_EDID} {LAYER_ID:08X}; quest {QUEST_EDID} '
          f'{QUEST_ID:08X} running {SCRIPT}; master {MASTER}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
