"""A Vortex-installable test archive of the anatomy body (for the owner's own game; not a release, A-2).

    Meshes/Actors/Character/CharacterAssets/FemaleBody.nif, .tri   the zeroed build (Silhouette S-5)
    F4SE/Plugins/ocbp.ini, OCBPCollisionConfig.txt                  tools/physics_config.py output
    Tools/BodySlide/SliderSets/AnatomyBodyZeX.osp                   the project, to rebuild with any preset
    Tools/BodySlide/ShapeData/AnatomyBodyZeX/...

Installed as a mod that wins its conflicts (bodyslides_f4_sd for the body, MadKita's Actual
Jiggle for ocbp.ini, Jiggle Physics for OCBPCollisionConfig.txt), it replaces them; disabling it
puts every one of them back. Why an archive and not an in-place edit of the deployed files: the
session's permission policy refused writing into other mods' deployed files (2026-09-23), and a
mod the owner installs is the reversible, visible way anyway.

    python tools/package.py      -> D:\\F4Output\\AnatomyLab\\package\\Anatomy-test-<stamp>.7z
"""
import pathlib
import shutil
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILT = pathlib.Path(r'D:\F4Output\AnatomyLab\out\zero\Meshes\Actors\Character\CharacterAssets')
CONFIG = ROOT / 'build/config'
PROJECT = ROOT / 'build/project'
OUT = pathlib.Path(r'D:\F4Output\AnatomyLab\package')


def main():
    stamp = time.strftime('%Y%m%d-%H%M')
    stage = OUT / f'Anatomy-test-{stamp}'
    if stage.exists():
        shutil.rmtree(stage)
    files = {
        'Meshes/Actors/Character/CharacterAssets/FemaleBody.nif': BUILT / 'FemaleBody.nif',
        'Meshes/Actors/Character/CharacterAssets/FemaleBody.tri': BUILT / 'FemaleBody.tri',
        'F4SE/Plugins/ocbp.ini': CONFIG / 'ocbp.ini',
        'F4SE/Plugins/OCBPCollisionConfig.txt': CONFIG / 'OCBPCollisionConfig.txt',
        'Tools/BodySlide/SliderSets/AnatomyBodyZeX.osp': PROJECT / 'SliderSets/AnatomyBodyZeX.osp',
        'Tools/BodySlide/ShapeData/AnatomyBodyZeX/AnatomyBodyZeX.nif': PROJECT / 'ShapeData/AnatomyBodyZeX/AnatomyBodyZeX.nif',
        'Tools/BodySlide/ShapeData/AnatomyBodyZeX/AnatomyBodyZeX.osd': PROJECT / 'ShapeData/AnatomyBodyZeX/AnatomyBodyZeX.osd',
        'Tools/BodySlide/SliderPresets/AnatomyZero.xml': PROJECT / 'SliderPresets/AnatomyZero.xml',
    }
    for rel, src in files.items():
        if not src.exists():
            raise SystemExit(f'missing {src}: run align_body, zex_bones, physics_config and the zero build first')
        dst = stage / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    archive = OUT / f'Anatomy-test-{stamp}.7z'
    subprocess.run(['7z', 'a', '-t7z', '-mx=7', str(archive), '.\\*'], cwd=stage, check=True,
                   stdout=subprocess.DEVNULL)
    listed = subprocess.run(['7z', 'l', '-sccUTF-8', str(archive)], capture_output=True, text=True).stdout
    count = sum(1 for rel in files if rel.replace('/', '\\') in listed)
    print(f'{archive} ({archive.stat().st_size // 1024} KB): {count}/{len(files)} files listed back')
    if count != len(files):
        raise SystemExit('the archive does not list every file')


if __name__ == '__main__':
    main()
