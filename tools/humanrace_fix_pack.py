"""alasdairn's HumanRace Skeleton Fix as an optional file on the Anatomy page (the owner, 2026-10-08: "yes good idea" to
alasdairn's offer). One record, HumanRace (Fallout4.esm 0x13746), built off the Pip-Boy 2000 + LooksMenu Customization
Compendium patch with the female skeleton sent back to DiscreteFemaleSkeleton.esp's path. Both mods override HumanRace
and drop that path, so women load the base skeleton and Anatomy's breast and butt bones stay nailed in place.

Checked here: masters Fallout4.esm + LooksMenu Customization Compendium.esp; no records of its own (nothing to clean:
one intended override); its female ANAM is DiscreteFemaleSkeleton's female\\skeleton.nif. ESL-flagged (3 bytes: the
flag and HEDR's next id). FOMOD per nexus-tools/docs/FOMOD-STANDARD.md.

    python tools/humanrace_fix_pack.py [--esp D:/F4Output/humanracefix/out/HumanRaceSkeletonFix.esp] [--version 1.0]
"""
import argparse
import pathlib
import shutil
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import release as rel  # noqa: E402

TITLE = 'HumanRace Skeleton Fix - LMCC and Pip-Boy 2000'
SPEC = dict(
    hard=['LooksMenu Customization Compendium.esp', 'DiscreteFemaleSkeleton.esp'],
    setup=['LooksMenu Customization Compendium.esp: found (its patch: this plugin is built on its HumanRace)',
           'DiscreteFemaleSkeleton.esp: found (the women\'s skeleton path this plugin restores)',
           'Pip-Boy 2000: this plugin also carries its HumanRace changes; it is made for LMCC with Pip-Boy 2000',
           'Pip-Pad users: not for you -- Pip-Pad changes HumanRace in its own way and needs a patch of its own',
           'Load it LAST of everything that edits HumanRace: after LMCC, Pip-Boy 2000 and DiscreteFemaleSkeleton.esp.',
           'Anatomy_Health.txt (F4SE folder) names the plugin that overrides HumanRace if breasts or butt still stay '
           'nailed in place.',
           'Made by alasdairn (Dudu\'s Den Discord); cleaned and ESL-flagged for this release with his permission.',
           'Install with Vortex or MO2; manual installs are not supported.'],
    setup_card='anatomy-rig.jpg',
    features=[('Women load their own skeleton again', 'The skeleton fix',
               'LooksMenu Customization Compendium and Pip-Boy 2000 override HumanRace and drop the women\'s skeleton '
               'path that DiscreteFemaleSkeleton.esp sets, so women load the base skeleton: the bones Anatomy\'s body '
               'is weighted to are missing and breasts and butt stay nailed in place while she moves. This plugin keeps '
               'both mods\' changes and sends women back to their own skeleton. One record, light (ESL).',
               'anatomy-rig.jpg')],
    notes=[], conflicts=[])
README = f"""{TITLE}

By alasdairn. Released with the Anatomy mod (https://www.nexusmods.com/fallout4/mods/109435) with his permission:
cleaned and ESL-flagged, nothing else changed.

What it does: LooksMenu Customization Compendium and Pip-Boy 2000 override HumanRace and drop the women's skeleton
path that DiscreteFemaleSkeleton.esp sets. Women then load the base skeleton, which lacks the bones Anatomy's body is
weighted to, and breasts and butt stay nailed in place. This plugin is their HumanRace with the women's skeleton path
restored.

Needs: LooksMenu Customization Compendium, DiscreteFemaleSkeleton.esp (Skeletal Adjustments for CBBE). Made for LMCC
with Pip-Boy 2000. Not for Pip-Pad. Load it after everything else that edits HumanRace.
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--esp', default=r'D:\F4Output\humanracefix\out\HumanRaceSkeletonFix.esp')
    ap.add_argument('--version', default='1.0')
    a = ap.parse_args()
    stage = rel.BUILD / 'release' / f'HumanRaceSkeletonFix-{a.version}'
    shutil.rmtree(stage, ignore_errors=True)
    (stage / 'Data').mkdir(parents=True)
    (stage / 'fomod/images').mkdir(parents=True)
    shutil.copy2(a.esp, stage / 'Data/HumanRaceSkeletonFix.esp')
    (stage / 'Data/HumanRaceSkeletonFix - README.txt').write_text(README, encoding='utf-8')
    info, module = rel.fomod_std(a.version, TITLE, SPEC, stage)
    (stage / 'fomod/info.xml').write_text(info, encoding='utf-8')
    (stage / 'fomod/ModuleConfig.xml').write_text(module, encoding='utf-8')
    archive = stage.parent / f'HumanRaceSkeletonFix-{a.version}.7z'
    archive.unlink(missing_ok=True)
    subprocess.run(['7z', 'a', '-bso0', str(archive), '.\\*'], cwd=stage, check=True)
    print(archive, archive.stat().st_size)


if __name__ == '__main__':
    main()
