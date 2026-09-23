"""A Vortex-installable test archive of the anatomy body (for the owner's own game; not a release, A-2).

    Meshes/Actors/Character/CharacterAssets/FemaleBody.nif, .tri   the zeroed build (Silhouette S-5)
    Meshes/Actors/Character/CharacterAssets/female/skeleton.nif    the women's skeleton with our genital
                                                                    bones (tools/skeleton.py, A-14); must
                                                                    win over Skeletal Adjustments for CBBE
    F4SE/Plugins/ocbp.ini, OCBPCollisionConfig.txt                  tools/physics_config.py output
    F4SE/Plugins/cbp.dll                                            the fo4-ocbpc fork (A-17): must win over
                                                                    Jiggle Physics and OCBPC-0.3-CBBE
    Anatomy.esp, Scripts/Anatomy/Arousal.pex                        arousal and nipples (A-16): tools/make_esp.py
                                                                    and scripts/build-papyrus.ps1; the plugin
                                                                    must be enabled
    MCM/Config/Anatomy/config.json, settings.ini                    the arousal menu (tools/build_mcm.py)
    Tools/BodySlide/SliderSets/AnatomyBodyZeX.osp                   the project, to rebuild with any preset
    Tools/BodySlide/ShapeData/AnatomyBodyZeX/...
    Textures/Actors/Character/BaseHumanFemale/FemaleBody*, femalebodydirty*
                                                                    the owner's skin with Nahka's genital
                                                                    texture patched in (genital_texture.py);
                                                                    must win over the skin mod

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
TEXTURES = pathlib.Path(r'D:\F4Output\AnatomyLab\textures')
TEXTURE_FILES = ['FemaleBody_d.dds', 'FemaleBody_n.DDS', 'FemaleBody_s.DDS',
                 'femalebodydirty_d.dds', 'FemaleBodydirty_n.DDS', 'FemaleBodydirty_s.DDS']
CONFIG = ROOT / 'build/config'
PROJECT = ROOT / 'build/project'
SKELETON = ROOT / 'build/skeleton/female/skeleton.nif'
PLUGIN = ROOT / 'build/plugin/Anatomy.esp'
PAPYRUS = ROOT / 'build/papyrus'
MCM = ROOT / 'build/mcm/MCM/Config/Anatomy'
# the fo4-ocbpc fork (GPL-3.0, sibling repo; A-17): OCBPC 0.3 plus stretch groups and prop colliders.
# Must win cbp.dll over Jiggle Physics and OCBPC-0.3-CBBE.
OCBPC_DLL = ROOT.parent / 'fo4-ocbpc/x64/Release/cbp.dll'
OUT = pathlib.Path(r'D:\F4Output\AnatomyLab\package')


def main():
    stamp = time.strftime('%Y%m%d-%H%M')
    stage = OUT / f'Anatomy-test-{stamp}'
    if stage.exists():
        shutil.rmtree(stage)
    files = {
        'Meshes/Actors/Character/CharacterAssets/FemaleBody.nif': BUILT / 'FemaleBody.nif',
        'Meshes/Actors/Character/CharacterAssets/FemaleBody.tri': BUILT / 'FemaleBody.tri',
        'Meshes/Actors/Character/CharacterAssets/female/skeleton.nif': SKELETON,
        'Anatomy.esp': PLUGIN,
        'Scripts/Anatomy/Arousal.pex': PAPYRUS / 'Anatomy/Arousal.pex',
        'MCM/Config/Anatomy/config.json': MCM / 'config.json',
        'MCM/Config/Anatomy/settings.ini': MCM / 'settings.ini',
        'F4SE/Plugins/ocbp.ini': CONFIG / 'ocbp.ini',
        'F4SE/Plugins/cbp.dll': OCBPC_DLL,
        'F4SE/Plugins/OCBPCollisionConfig.txt': CONFIG / 'OCBPCollisionConfig.txt',
        'Tools/BodySlide/SliderSets/AnatomyBodyZeX.osp': PROJECT / 'SliderSets/AnatomyBodyZeX.osp',
        'Tools/BodySlide/ShapeData/AnatomyBodyZeX/AnatomyBodyZeX.nif': PROJECT / 'ShapeData/AnatomyBodyZeX/AnatomyBodyZeX.nif',
        'Tools/BodySlide/ShapeData/AnatomyBodyZeX/AnatomyBodyZeX.osd': PROJECT / 'ShapeData/AnatomyBodyZeX/AnatomyBodyZeX.osd',
        'Tools/BodySlide/SliderPresets/AnatomyZero.xml': PROJECT / 'SliderPresets/AnatomyZero.xml',
        **{f'Textures/Actors/Character/BaseHumanFemale/{t}': TEXTURES / t for t in TEXTURE_FILES},
    }
    for rel, src in files.items():
        if not src.exists():
            raise SystemExit(f'missing {src}: run align_body, skeleton, zex_bones, physics_config, make_esp, '
                             f'build-papyrus.ps1, build_mcm and the zero build first')
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
    return stage


if __name__ == '__main__':
    main()
