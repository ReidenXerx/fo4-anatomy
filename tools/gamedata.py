"""The files the game would load: loose first, then BA2 archives, in the game's own order (builder-design.md).

    python tools/gamedata.py which <path>            # who provides it (loose / archive name)
    python tools/gamedata.py extract <path> <file>   # write the winning copy out
    python tools/gamedata.py plugins                 # the active plugins, in load order

The order, as Fallout 4 loads it (later wins):
  1. the INI archives: [Archive] sResourceIndexFileList, SResourceArchiveList, SResourceArchiveList2
     (Fallout4.ini, then Fallout4Custom.ini; the game folder's Fallout4_Default.ini when neither sets them);
  2. per active plugin, in load order: "<plugin> - Main.ba2", "<plugin> - Textures.ba2" (and any other
     "<plugin> - *.ba2"). The base game's masters and DLCs load first, then Creation Club (Fallout4.ccc),
     then plugins.txt;
  3. loose files in Data.

Both BA2 kinds are read: GNRL (anything; zlib) and DX10 (textures, stored as mip chunks with no file
header: the DDS header is rebuilt from the record, a legacy FourCC one for BC1/BC3/BC5 so every DDS
reader here takes it, DX10 otherwise).
"""
import os
import pathlib
import re
import struct
import sys
import zlib

BASE_MASTERS = ['Fallout4.esm', 'DLCRobot.esm', 'DLCworkshop01.esm', 'DLCCoast.esm', 'DLCworkshop02.esm',
                'DLCworkshop03.esm', 'DLCNukaWorld.esm', 'DLCUltraHighResolution.esm']
INI_KEYS = ('sResourceIndexFileList', 'SResourceArchiveList', 'SResourceArchiveList2')


def norm(path):
    return str(path).replace('/', '\\').lower().lstrip('\\')


class Ba2:
    """One BA2's index; entries are read on demand."""

    def __init__(self, path):
        self.path = pathlib.Path(path)
        with open(self.path, 'rb') as f:
            magic, self.version, kind, count, names_at = struct.unpack('<4sI4sIQ', f.read(24))
            if magic != b'BTDX':
                raise ValueError(f'{self.path}: not a BA2')
            self.kind = kind.decode('ascii')
            if self.version in (2, 3):
                f.read(8 if self.version == 2 else 12)            # Starfield's extra header fields
            self.records = []
            if self.kind == 'GNRL':
                for _ in range(count):
                    self.records.append(struct.unpack('<I4sIIQIII', f.read(36)))
            elif self.kind == 'DX10':
                for _ in range(count):
                    head = struct.unpack('<I4sIBBHHHBBBB', f.read(24))
                    chunks = [struct.unpack('<QIIHHI', f.read(24)) for _ in range(head[4])]
                    self.records.append((head, chunks))
            else:
                raise ValueError(f'{self.path}: unknown BA2 kind {self.kind}')
            f.seek(names_at)
            self.names = {}
            for i in range(count):
                (n,) = struct.unpack('<H', f.read(2))
                self.names[norm(f.read(n).decode('utf-8', 'replace'))] = i

    def __contains__(self, rel):
        return norm(rel) in self.names

    def read(self, rel):
        i = self.names[norm(rel)]
        with open(self.path, 'rb') as f:
            if self.kind == 'GNRL':
                _h, _e, _d, _fl, offset, packed, size, _a = self.records[i]
                f.seek(offset)
                blob = f.read(packed or size)
                return zlib.decompress(blob) if packed else blob
            head, chunks = self.records[i]
            _h, _e, _d, _u, _n, _chs, height, width, mips, fmt, cube, _tile = head
            body = bytearray()
            for offset, packed, size, _s, _t, _a in chunks:
                f.seek(offset)
                blob = f.read(packed or size)
                body += zlib.decompress(blob) if packed else blob
            return dds_header(width, height, mips, fmt, bool(cube), len(body)) + bytes(body)


# DXGI formats seen in Fallout 4's texture archives -> (FourCC or None, bytes per 4x4 block or per pixel)
_LEGACY = {71: b'DXT1', 72: b'DXT1', 77: b'DXT5', 78: b'DXT5', 83: b'ATI2', 74: b'DXT3', 75: b'DXT3'}
_BLOCK = {71: 8, 72: 8, 70: 8, 80: 8, 81: 8, 74: 16, 75: 16, 77: 16, 78: 16, 83: 16, 84: 16, 98: 16, 99: 16}


def dds_header(width, height, mips, fmt, cube, size):
    flags = 0x1 | 0x2 | 0x4 | 0x1000 | 0x20000 | 0x80000          # caps, height, width, pixelformat, mipcount, linearsize
    block = _BLOCK.get(fmt)
    pitch = max(1, (width + 3) // 4) * max(1, (height + 3) // 4) * block if block else width * height * 4
    caps = 0x1000 | (0x400000 | 0x8 if mips > 1 else 0) | (0x8 if cube else 0)
    caps2 = 0xFE00 if cube else 0
    if fmt in _LEGACY:
        pf = struct.pack('<II4sIIIII', 32, 0x4, _LEGACY[fmt], 0, 0, 0, 0, 0)
        extra = b''
    elif fmt in (28, 29, 87, 88):                                  # RGBA8 / BGRA8
        bgra = fmt in (87, 88)
        masks = (0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000) if bgra else \
                (0x000000FF, 0x0000FF00, 0x00FF0000, 0xFF000000)
        pf = struct.pack('<II4sIIIII', 32, 0x41, b'\0\0\0\0', 32, *masks)
        flags = (flags & ~0x80000) | 0x8
        pitch = width * 4
        extra = b''
    else:
        pf = struct.pack('<II4sIIIII', 32, 0x4, b'DX10', 0, 0, 0, 0, 0)
        extra = struct.pack('<IIIII', fmt, 3, 0x4 if cube else 0, 1, 0)
    head = struct.pack('<4sIIIIIII', b'DDS ', 124, flags, height, width, pitch, 0, mips) + b'\0' * 44 + pf + \
        struct.pack('<IIIII', caps, caps2, 0, 0, 0)
    return head + extra


class Game:
    def __init__(self, data, plugins_txt=None, my_games=None):
        self.data = pathlib.Path(data)
        self.root = self.data.parent
        local = pathlib.Path(os.environ.get('LOCALAPPDATA', pathlib.Path.home() / 'AppData/Local'))
        self.plugins_txt = pathlib.Path(plugins_txt) if plugins_txt else local / 'Fallout4/plugins.txt'
        self.my_games = pathlib.Path(my_games) if my_games else pathlib.Path.home() / 'Documents/My Games/Fallout4'
        self.plugins = self._load_order()
        self.archives = self._archive_order()
        self._opened = {}

    # ---- load order ----
    def _load_order(self):
        order = [m for m in BASE_MASTERS if (self.data / m).exists()]
        ccc = self.root / 'Fallout4.ccc'
        if ccc.exists():
            for line in ccc.read_text(encoding='utf-8', errors='replace').splitlines():
                name = line.strip()
                if name and (self.data / name).exists() and name.lower() not in {p.lower() for p in order}:
                    order.append(name)
        if self.plugins_txt.exists():
            for line in self.plugins_txt.read_text(encoding='utf-8', errors='replace').splitlines():
                line = line.strip()
                if not line.startswith('*'):
                    continue
                name = line[1:].strip()
                if name.lower() not in {p.lower() for p in order}:
                    order.append(name)
        return order

    def active(self, plugin):
        return plugin.lower() in {p.lower() for p in self.plugins}

    def _ini_lists(self):
        lists = {}
        for ini in (self.root / 'Fallout4_Default.ini', self.my_games / 'Fallout4.ini',
                    self.my_games / 'Fallout4Custom.ini'):
            if not ini.exists():
                continue
            section = None
            for line in ini.read_text(encoding='utf-8', errors='replace').splitlines():
                m = re.match(r'^\s*\[([^\]]+)\]', line)
                if m:
                    section = m.group(1).strip().lower()
                    continue
                if section != 'archive' or '=' not in line:
                    continue
                key, value = (s.strip() for s in line.split('=', 1))
                for k in INI_KEYS:
                    if key.lower() == k.lower():
                        lists[k] = [v.strip() for v in value.split(',') if v.strip()]
        return lists

    def _archive_order(self):
        order = []
        lists = self._ini_lists()
        for key in INI_KEYS:
            for name in lists.get(key, []):
                if (self.data / name).exists() and name.lower() not in {o.name.lower() for o in order}:
                    order.append(self.data / name)
        if not lists:                                               # no INI: every base archive
            order += sorted(self.data.glob('Fallout4 - *.ba2'))
        all_ba2 = {p.name.lower(): p for p in self.data.glob('*.ba2')}
        taken = {o.name.lower() for o in order}
        for plugin in self.plugins:
            stem = pathlib.Path(plugin).stem.lower()
            mine = sorted(p for n, p in all_ba2.items() if (n == f'{stem}.ba2' or n.startswith(f'{stem} - '))
                          and n not in taken)
            # Main before Textures, the game's own habit; the rest after
            mine.sort(key=lambda p: (0 if p.name.lower().endswith(' - main.ba2') else
                                     1 if p.name.lower().endswith(' - textures.ba2') else 2, p.name.lower()))
            for p in mine:
                order.append(p)
                taken.add(p.name.lower())
        return order

    def _ba2(self, path):
        if path not in self._opened:
            self._opened[path] = Ba2(path)
        return self._opened[path]

    # ---- lookup ----
    def find(self, rel):
        """('loose', path) or ('archive', archive path) for the copy the game would load, or None."""
        loose = self.data / rel
        if loose.exists():
            return 'loose', loose
        for path in reversed(self.archives):
            try:
                if rel in self._ba2(path):
                    return 'archive', path
            except (OSError, ValueError, struct.error):
                continue
        return None

    def read(self, rel):
        where = self.find(rel)
        if where is None:
            raise FileNotFoundError(f'{rel}: not loose in {self.data} and in none of {len(self.archives)} archives')
        kind, path = where
        return path.read_bytes() if kind == 'loose' else self._ba2(path).read(rel)

    def describe(self, rel):
        where = self.find(rel)
        if where is None:
            return f'{rel}: nowhere'
        kind, path = where
        return f'{rel}: {kind} {path.name if kind == "archive" else path}'


def main(argv):
    data = pathlib.Path(os.environ.get('ANATOMY_DATA', r'D:\GOGGames\Fallout 4 GOTY\Data'))
    game = Game(data)
    if argv[:1] == ['plugins']:
        for i, p in enumerate(game.plugins):
            print(f'{i:3} {p}')
        print(f'{len(game.archives)} archives in load order')
    elif argv[:1] == ['which'] and len(argv) == 2:
        print(game.describe(argv[1]))
    elif argv[:1] == ['extract'] and len(argv) == 3:
        blob = game.read(argv[1])
        pathlib.Path(argv[2]).write_bytes(blob)
        print(f'{game.describe(argv[1])} -> {argv[2]} ({len(blob)} bytes)')
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
