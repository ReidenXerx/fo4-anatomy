"""Put the anatomy body and its physics configs into the owner's game FOR TESTING, reversibly.

The owner asked for an in-game test while asleep; a new file needs the owner's Vortex Deploy, but
an EXISTING deployed file is a hardlink shared by Vortex's staging folder and Data, so writing
into it in place changes the game at once (the one-holder rule's scar). Only these four
existing files are written, each only after it is proven to be the deployed one:

    FemaleBody.nif / .tri       bodyslides_f4_sd (the owner's BodySlide output mod)
    F4SE/Plugins/ocbp.ini       MadKita's Actual Jiggle
    OCBPCollisionConfig.txt     Jiggle Physics

    python tools/install_test.py install     # backup, write in place, prove Data sees it
    python tools/install_test.py restore     # the latest backup back, proven the same way
    python tools/install_test.py status      # which version Data holds now

Refuses while Fallout4.exe runs. Backups: D:\\F4Output\\AnatomyLab\\backup\\<stamp>\\ + manifest.json.
"""
import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = pathlib.Path(r'D:\GOGGames\Fallout 4 GOTY\Data')
MODS = pathlib.Path(r'D:\Vortex\fallout4\mods')
BACKUPS = pathlib.Path(r'D:\F4Output\AnatomyLab\backup')
BUILT = pathlib.Path(r'D:\F4Output\AnatomyLab\out\zero\Meshes\Actors\Character\CharacterAssets')
CONFIG = ROOT / 'build/config'

TARGETS = [
    ('Meshes/Actors/Character/CharacterAssets/FemaleBody.nif', BUILT / 'FemaleBody.nif'),
    ('Meshes/Actors/Character/CharacterAssets/FemaleBody.tri', BUILT / 'FemaleBody.tri'),
    ('F4SE/Plugins/ocbp.ini', CONFIG / 'ocbp.ini'),
    ('F4SE/Plugins/OCBPCollisionConfig.txt', CONFIG / 'OCBPCollisionConfig.txt'),
]


def sha1(b):
    return hashlib.sha1(b).hexdigest()[:12]


def game_running():
    r = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq Fallout4.exe'], capture_output=True, text=True)
    return 'Fallout4.exe' in r.stdout


def deployed_source(rel):
    """The staging file that IS the deployed Data file (same NTFS file id), or an error."""
    data_file = DATA / rel
    if not data_file.exists():
        raise SystemExit(f'{rel}: not in Data')
    ino = os.stat(data_file).st_ino
    hits = []
    for mod in MODS.iterdir():
        cand = mod / rel
        if cand.exists() and os.stat(cand).st_ino == ino:
            hits.append(cand)
    if len(hits) != 1:
        raise SystemExit(f'{rel}: {len(hits)} staging files share the deployed file id ({hits}); not writing')
    return data_file, hits[0]


def write_in_place(path, content):
    """Same file, new bytes: the hardlink (and so Data) keeps pointing at it."""
    with open(path, 'r+b') as f:
        f.seek(0)
        f.write(content)
        f.truncate()


def install():
    if game_running():
        raise SystemExit('Fallout4.exe is running: close it (or ask its holder) first')
    stamp = time.strftime('%Y%m%d-%H%M%S')
    root = BACKUPS / stamp
    manifest = []
    plan = []
    for rel, new in TARGETS:
        if not new.exists():
            raise SystemExit(f'missing build output {new}')
        data_file, staged = deployed_source(rel)
        plan.append((rel, new, data_file, staged))
    for rel, new, data_file, staged in plan:
        old = staged.read_bytes()
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_bytes(old)
        content = new.read_bytes()
        write_in_place(staged, content)
        seen = data_file.read_bytes()
        ok = seen == content
        manifest.append(dict(rel=rel, staged=str(staged), data=str(data_file), before=sha1(old),
                             after=sha1(content), data_sees_new=ok))
        print(f'{"OK  " if ok else "FAIL"} {rel}: {sha1(old)} -> {sha1(content)} (staged in {staged.parents[len(pathlib.Path(rel).parts) - 1].name})')
        if not ok:
            raise SystemExit('Data does not see the new bytes: the hardlink is broken; run restore')
    (root / 'manifest.json').write_text(json.dumps(manifest, indent=1))
    print(f'backup + manifest: {root}')


def restore():
    if game_running():
        raise SystemExit('Fallout4.exe is running: close it (or ask its holder) first')
    stamps = sorted(p for p in BACKUPS.iterdir() if (p / 'manifest.json').exists()) if BACKUPS.exists() else []
    if not stamps:
        raise SystemExit('no backup to restore')
    root = stamps[-1]
    for entry in json.loads((root / 'manifest.json').read_text()):
        old = (root / entry['rel']).read_bytes()
        write_in_place(pathlib.Path(entry['staged']), old)
        ok = pathlib.Path(entry['data']).read_bytes() == old
        print(f'{"OK  " if ok else "FAIL"} restored {entry["rel"]} to {sha1(old)}')


def status():
    for rel, new in TARGETS:
        cur = (DATA / rel).read_bytes()
        print(f'{rel}: Data {sha1(cur)}; anatomy build {sha1(new.read_bytes()) if new.exists() else "-"}'
              f'{"  <- anatomy installed" if new.exists() and cur == new.read_bytes() else ""}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('action', choices=('install', 'restore', 'status'))
    a = ap.parse_args()
    {'install': install, 'restore': restore, 'status': status}[a.action]()
