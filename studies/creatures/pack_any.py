"""Pack one Data-root folder into a 7z in a fresh folder, re-extract and sha1-check every file.
Arguments instead of edited constants (sed/str-replace on Windows paths packed the wrong folder twice).
    python -I pack_any.py <src Data dir> <out dir> <archive name>"""
import hashlib
import pathlib
import shutil
import subprocess
import sys
import tempfile

SRC, OUT, NAME = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]
SEVENZIP = shutil.which('7z') or r'C:\Program Files\7-Zip\7z.exe'


def sha1(p):
    return hashlib.sha1(pathlib.Path(p).read_bytes()).hexdigest()


if not (SRC / 'meshes').exists():
    raise SystemExit(f'{SRC} has no meshes folder: wrong source?')
OUT.mkdir(parents=True, exist_ok=True)
arc = OUT / NAME
if arc.exists():
    raise SystemExit(f'{arc} exists: use a fresh folder')
files = {q.relative_to(SRC).as_posix(): q for q in SRC.rglob('*') if q.is_file()}
r = subprocess.run([SEVENZIP, 'a', '-t7z', '-mx=5', str(arc), '*'], cwd=SRC, capture_output=True, text=True)
if r.returncode:
    raise SystemExit(r.stdout[-800:] + r.stderr[-800:])
check = pathlib.Path(tempfile.mkdtemp(prefix='checkpack-', dir=r'D:\F4Output'))
subprocess.run([SEVENZIP, 'x', '-y', f'-o{check}', str(arc)], capture_output=True, check=True)
got = {q.relative_to(check).as_posix(): q for q in check.rglob('*') if q.is_file()}
bad = [k for k, q in files.items() if k not in got or sha1(got[k]) != sha1(q)]
extra = sorted(set(got) - set(files))
print(f'{arc}: {len(files)} files, {arc.stat().st_size / 1e6:.1f} MB, sha1 {sha1(arc)}; {len(bad)} mismatched, '
      f'{len(extra)} extra')
if bad or extra:
    raise SystemExit(f'mismatch {bad[:5]} {extra[:5]}')
for k in sorted(files):
    print('   ', k)
