"""Rebuild the game body and put it into the owner's DEPLOYED Anatomy-dev, proven at every step.

    1. refuse while Fallout4.exe runs (BodySlide's window; and Data changes at once below)
    2. lab setup + BodySlide build with the "Anatomy Zero" preset
    3. compare_builds against the owner's pre-anatomy body (out/current) -- must PASS
    4. package (tools/package.py)
    5. every packaged file into D:\\Vortex\\fallout4\\mods\\Anatomy-dev IN PLACE: an existing file is
       rewritten through its hardlink, so the deployed copy in Data changes with it; a file new
       to the mod is copied and reported (it needs the owner's Deploy)
    6. prove Data holds the new bytes; print the build id (FemaleBody.nif sha1, 12 chars)
    7. check the skeleton women load in Data carries every bone the body is weighted to (A-14): a new
       skeleton needs the owner's Deploy first, and the game must not start before it

Anatomy-dev is OUR mod, created at the owner's request and deployed by them (A-8); no other mod's
file is touched.

    python tools/restage.py
    python tools/restage.py --build-only   # steps 2-4 only: nothing reaches Data, so it runs while
                                           # someone else holds the game
"""
import hashlib
import pathlib
import shutil
import subprocess
import sys

import lab
import package

ROOT = pathlib.Path(__file__).resolve().parent.parent
MOD = pathlib.Path(r'D:\Vortex\fallout4\mods\Anatomy-dev')
DATA = pathlib.Path(r'D:\GOGGames\Fallout 4 GOTY\Data')
ZERO = pathlib.Path(r'D:\F4Output\AnatomyLab\out\zero')
CURRENT = pathlib.Path(r'D:\F4Output\AnatomyLab\out\current')


def sha(p):
    return hashlib.sha1(pathlib.Path(p).read_bytes()).hexdigest()[:12]


def run(args):
    r = subprocess.run([sys.executable] + args, cwd=ROOT / 'tools')
    if r.returncode:
        raise SystemExit(f'{" ".join(args)} failed ({r.returncode})')


def main():
    build_only = '--build-only' in sys.argv[1:]
    if not build_only and lab.game_running():
        raise SystemExit('Fallout4.exe is running: take the game from its holder first')
    lab.setup()
    if ZERO.exists():
        shutil.rmtree(ZERO)
    if lab.build('AnatomyZeXLab', 'Anatomy Zero', ZERO, 600):
        raise SystemExit('BodySlide build failed')
    run(['compare_builds.py', str(CURRENT), str(ZERO)])
    stage = package.main()
    if build_only:
        print(f'built and packaged ({stage}); body {sha(ZERO / "Meshes/Actors/Character/CharacterAssets/FemaleBody.nif")}; '
              f'nothing written to Anatomy-dev')
        return
    changed, new = [], []
    for src in sorted(p for p in stage.rglob('*') if p.is_file()):
        rel = src.relative_to(stage)
        dst = MOD / rel
        content = src.read_bytes()
        if dst.exists():
            if dst.read_bytes() != content:
                with open(dst, 'r+b') as f:
                    f.seek(0)
                    f.write(content)
                    f.truncate()
                changed.append(rel)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(content)
            new.append(rel)
    # files an older package carried and this one does not: removed from OUR mod folder only; the
    # owner's Deploy then hands those paths back to the mods that own them (A-21)
    removed = []
    for rel in package.RETIRED:
        dst = MOD / rel
        if dst.exists():
            dst.unlink()
            removed.append(rel)
    stale = [rel for rel in changed if (DATA / rel).exists() and (DATA / rel).read_bytes() != (MOD / rel).read_bytes()]
    print(f'Anatomy-dev: {len(changed)} file(s) rewritten in place, {len(new)} new, {len(removed)} removed '
          f'(new and removed need a Deploy): new {[str(r) for r in new]}, removed {removed}')
    if stale:
        raise SystemExit(f'Data does not see the new bytes for {stale}: a hardlink is broken')
    body = 'Meshes/Actors/Character/CharacterAssets/FemaleBody.nif'
    print(f'build id {sha(DATA / body)} (Data {body}) = staged {sha(MOD / body)}')
    # 7. the body must not reach the game ahead of its bones: a weighted bone the women's skeleton
    #    lacks leaves its vertices at their standing-pose place whenever she moves (A-14). Our own
    #    bones are the fork's to add at run time since A-21, so only OTHER missing bones stop play.
    import physics_design as pd
    import skeleton
    ours = set(pd.REST) | set(pd.STRETCH_BONES.values())
    missing = skeleton.deployed()
    others = [b for b in missing if b not in ours]
    if others:
        print(f'!! NOT READY TO PLAY: the skeleton women load lacks bones the body is weighted to: {others}')
    elif missing:
        print(f'   our {len(missing)} bones are not in that skeleton: the fork adds them at run time (A-21), '
              f'which needs Data/F4SE/Plugins/Anatomy/ocbp.ini ([Bones]) and the fork\'s cbp.dll deployed')


if __name__ == '__main__':
    main()
