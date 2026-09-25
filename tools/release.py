"""Assemble the release archives (release-plan.md): the engine, Anatomy, and Anatomy Rebuild.

    python tools/release.py [--version 1.0.0] [--what all|engine|anatomy|rebuild]
        -> build/release/fo4-ocbpc-<version>.7z        the engine: cbp.dll, its own Nexus page
           build/release/Anatomy-<version>.7z          Anatomy (requires the engine)
           build/release/AnatomyRebuild-<version>.7z   the optional tool (A-36, A-37 on the player's builds)

Two mods since the owner's release call (2026-09-26: "separately our upgraded cbp engine and
anatomy"): the engine is the ONLY archive carrying cbp.dll, so a player never resolves two copies of it
and Anatomy never ships a DLL older than the engine's page.

Anatomy ships (nothing of anyone else's but Nahka's own work, with her page's permission, A-23):
    Anatomy.esp, Scripts/Anatomy/Arousal.pex, MCM/Config/Anatomy/*     arousal and its menu
    Scripts/AnatomyAim.pex                                             the aim's scene list (A-28)
    F4SE/Plugins/F4EE/Overlays/Anatomy.esp, Materials|Textures/Overlays/Anatomy   the glans colour (A-31)
    F4SE/Plugins/Anatomy/ocbp.ini, OCBPCollisionConfig.txt             our physics lines and [Bones]
    Tools/AnatomyBuilder/AnatomyBuilder.exe (+ _internal)              the builder
    Tools/AnatomyBuilder/data/nahka_patch.json.gz, data/tex/*          her genitals, as a patch and her
                                                                       texture island
    fomod/info.xml, fomod/ModuleConfig.xml                             one page: what to do next
    Anatomy - README.txt                                               install, credits, licences
Every file is checked present, and the archive must list every one of them back.

Both binaries are built from source on every run, so an archive never carries one older than its
code: the builder exe (PyInstaller, one folder) and cbp.dll (MSBuild). The fork must have no
uncommitted change: F4SE requires a plugin's source to be public, and the source we point players
to is that commit, which the README names.
"""
import argparse
import pathlib
import shutil
import subprocess
import sys
from xml.sax.saxutils import escape

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILD = ROOT / 'build'
FORK = ROOT.parent / 'fo4-ocbpc'
NAME = 'Anatomy'                                            # file names: Anatomy.esp, the archive
TITLE = 'Anatomy - CBBE Genitals, Physics and Arousal'     # the Nexus page's title (owner's poll)
AUTHOR = 'ReidenXerx'
FORK_URL = 'https://github.com/ReidenXerx/fo4-ocbpc'      # its public source, F4SE's rule
ANATOMY_URL = 'https://github.com/ReidenXerx/fo4-anatomy'
ENGINE = 'fo4-ocbpc'                                        # the engine's archive name

NEXT_STEPS = """Anatomy needs the fo4-ocbpc engine (its cbp.dll), a separate download.
After this installs:
1. Run Data\\Tools\\AnatomyBuilder\\AnatomyBuilder.exe once (MO2: add it to MO2's executables and run it
   from there, like BodySlide). It builds the body from YOUR CBBE and skin and writes only new files.
2. Open BodySlide, choose "Anatomy Body", your preset, and Build.
Re-run the builder whenever you change your CBBE or your skin mod.
Optional: Anatomy Rebuild (its own download) after every BodySlide build."""

README = f"""{TITLE}
Working genitals for Fallout 4 CBBE women: physics, arousal, contact.

WHAT YOU NEED
  Fallout 4 1.10.163 (Steam or GOG, not the next-gen update) with F4SE 0.6.23.
  The fo4-ocbpc engine (cbp.dll, its own download), CBBE (with its BodySlide files) and BodySlide.
  LooksMenu for the arousal nipples and the glans colour; AAF for scenes; MCM for the settings page.
  A physics config (e.g. Jiggle Physics / MadKita's) is optional; Anatomy brings its own lines.

INSTALL
  1. Install the fo4-ocbpc engine, then this archive, with your mod manager. Nothing of this archive
     overlaps another mod.
  2. Run Data\\Tools\\AnatomyBuilder\\AnatomyBuilder.exe once. MO2: add it to MO2's executables and
     run it from MO2, as you do BodySlide. It reads your CBBE, your skeleton and your skin (as the
     game loads them), checks every step, and writes only new files:
       Tools\\BodySlide\\SliderSets\\Anatomy.osp and ShapeData\\Anatomy\\*, the "Anatomy Body" set
       Textures\\Anatomy\\*, Materials\\Anatomy\\*, the genitals' own texture and material
     Its log is AnatomyBuilder.log next to it.
  3. BodySlide: choose "Anatomy Body", your preset, Build (or Batch Build). The category "Anatomy"
     has "Opening, front": extra opening toward the front, on top of the built-in one (0% leaves
     it as designed).
  Re-run the builder after changing your CBBE or skin mod.
  4. Optional, Anatomy Rebuild (its own download): run it after every BodySlide build. It gives your
     built outfits the body's hip handover and the body's neck its seam fix, which BodySlide itself
     cannot carry.

WHAT IT DOES
  - The genitals are their own part of the body, with bones added at run time to whatever skeleton
    your game loads; they open to a penis, a hand or a toy through collision physics, and stretch
    for something bigger.
  - The mouth opens to what is at the lips, over the animation's own face.
  - Women's nipples respond to arousal (scenes, watching, nudity, companions' own arousal); the MCM
    page "Anatomy" sets how much and what counts.

CREDITS
  Nahka - the vulva and anus geometry, sliders and texture (Animated Fannies on LoversLab: "up for
    adoption ... can be used in whatever way any other modders see fit"), with BringTheNoise and
    Alan (UN7B). Only her own work ships here, as a patch applied to your CBBE.
  Ousnius and the CBBE team - CBBE, which this is built on (never included: read from your install).
  ericncream and the OpenCBP authors - OCBPC, which cbp.dll extends.
  maximusmaxy - Screen Archer Menu's source, which documented the face data the mouth uses.

LICENCES
  Anatomy is distributed under the GNU General Public License, version 3
  (Tools\\AnatomyBuilder\\licences\\Anatomy - LICENSE.txt).
  Its source: {ANATOMY_URL}
  The engine's source: {FORK_URL} (this release was made with commit @FORK_COMMIT@).
  The builder is our own code, run by Python and Pillow, which are packed inside it under their own
  licences (Tools\\AnatomyBuilder\\licences). The plugin, scripts, MCM and configs are our own work.
"""


ENGINE_TITLE = 'fo4-ocbpc - OCBPC physics engine, extended'
ENGINE_README = f"""{ENGINE_TITLE}
cbp.dll: OCBPC (OpenCBP physics with collisions) for Fallout 4, extended by the Anatomy project.
Built from {FORK_URL} (commit @FORK_COMMIT@).

WHAT YOU NEED
  Fallout 4 1.10.163 (Steam or GOG, not the next-gen update) with F4SE 0.6.23.

INSTALL
  Install with your mod manager and let its cbp.dll win over any other OCBPC-based mod's (Jiggle
  Physics, MadKita's, OCBPC itself). Your own ocbp.ini and OCBPCollisionConfig.txt keep working as
  they are: this is the same engine, with everything new either off until a config turns it on or
  fixing OCBPC's own faults.

WHAT IT ADDS
  On its own: Rapport's face authority (with Rapport installed, a face it holds is written after
  the engine's own merge, so eyelids and a jaw an animation opened can close, and a spoken line
  still moves the mouth), and a log a second game process cannot truncate. Every engine hook reads
  the game's code before patching it and stays off, logged, on any other game build.
  With Anatomy's config (Data\\F4SE\\Plugins\\Anatomy\\ocbp.ini, read after yours): run-time genital
  bones, stretch groups, props and toys as colliders, one-tube penis collision, the contact-driven
  mouth with lips fitted to what is in it, penis aim into the right opening, per-man shape, and
  partner glances. The full list and every setting: {FORK_URL}

LICENCES
  cbp.dll is distributed under the GNU General Public License, version 3 (fo4-ocbpc - GPL-3.0.txt),
  with an additional permission to link with F4SE. It is a fork of OpenCBP_FO4 / OCBPC, whose code
  it carries under the MIT licence (fo4-ocbpc - MIT (OCBPC).txt).

CREDITS
  JS and the OpenCBP authors; ericncream, for OCBPC; the F4SE team; Ian Patterson, for common; the
  DetourXS and BeaEngine authors; maximusmaxy, whose Screen Archer Menu source documented the face
  data the mouth uses.
"""

REBUILD_TITLE = 'Anatomy Rebuild'
REBUILD_STEPS = """Run Data\\Tools\\AnatomyRebuild\\AnatomyRebuild.exe after every BodySlide build (MO2: add it to
MO2's executables and run it from there, like BodySlide). --undo puts your builds back."""
REBUILD_README = f"""{REBUILD_TITLE} (optional, for Anatomy)
Your BodySlide builds get the two fixes BodySlide cannot carry.

WHAT IT DOES
  - Outfits: every CBBE outfit a woman wears in your game gets the Anatomy body's hip handover, so
    an outfit no longer parts from the skin at the groin and hip in legs-up poses (it was up to 3.8
    units). Only the pelvis/spine/thigh skinning near the body's hip fold moves.
  - The neck: the body's neck ring is turned to face the way the head does (and CBBE HeadRear
    Absolute Fix's rear piece, when installed), so the join no longer shows as a line in the light.

HOW TO USE
  1. Anatomy installed and its builder run; build "Anatomy Body" and your outfits in BodySlide as
     usual, with any preset.
  2. Run Data\\Tools\\AnatomyRebuild\\AnatomyRebuild.exe (MO2: from MO2, like BodySlide). The log is
     AnatomyRebuild.log next to it.
  3. After every BodySlide build, run it again: BodySlide writes its meshes whole.
  --undo puts back every mesh it changed that BodySlide has not rebuilt since.

WHY IT IS SAFE
  It never runs BodySlide and never moves a vertex, a morph or a slider: your preset, zaps and
  BodyGen morphs stay exactly as built. It works out the new skinning on each outfit's own BodySlide
  source and writes it onto your built mesh only after proving the two are the same mesh, vertex by
  vertex. It writes only meshes BodySlide built (in place, so a Vortex hardlink stays one), keeps
  every original in backup\\ first, and refuses to run while the game runs.

LICENCES
  GNU General Public License, version 3 (licences\\Anatomy - LICENSE.txt).
  Source: {ANATOMY_URL}
  It runs on Python, packed inside it under its own licence (licences\\).
"""


MSBUILD = r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\MSBuild.exe'


def build_dll():
    """cbp.dll from the fork's committed source; returns that commit (the source players are pointed to)."""
    dirty = subprocess.run(['git', 'status', '--porcelain'], cwd=FORK, capture_output=True, text=True).stdout
    if dirty.strip():
        raise SystemExit('the fork has uncommitted changes, so no published commit would be the source of '
                         f'this cbp.dll; commit them first:\n{dirty}')
    # PostBuildEventUseInBuild=false: the fork's post-build copies cbp.dll to $(Fallout4Path), which
    # is unset here, so it lands at the drive root (C:\cbp.dll). A release copies nothing anywhere.
    subprocess.run([MSBUILD, 'OpenCBP_FO4.sln', '/t:CBPSSE', '/p:Configuration=Release', '/p:Platform=x64',
                    '/p:PlatformToolset=v143', '/p:WindowsTargetPlatformVersion=10.0.22621.0',
                    '/p:PostBuildEventUseInBuild=false', '/v:m'],
                   cwd=FORK, check=True, stdout=subprocess.DEVNULL)
    return subprocess.run(['git', 'rev-parse', '--short=12', 'HEAD'], cwd=FORK, capture_output=True,
                          text=True, check=True).stdout.strip()


BUILDER_MODULES = ('gamedata', 'genital_texture', 'apply_patch', 'make_patch', 'mask', 'split_genitals',
                   'opening', 'verify_zex', 'zex_bones', 'physics_config', 'physics_design', 'bgsm')
REBUILD_MODULES = ('gamedata', 'garments', 'hip_fold', 'neck_seam', 'align_body', 'nif', 'osd')


def build_exe(name='AnatomyBuilder', script='tools/builder.py', modules=BUILDER_MODULES):
    """PyInstaller one-folder build of a tool into build/dist/<name> (wiped first). The tools import
    their stages by name at run time, so each is named here as a hidden import."""
    hidden = [arg for m in modules for arg in ('--hidden-import', m)]
    # no network, so no OpenSSL in the bundle: urllib and http.client take ssl as optional, and hashlib
    # falls back to Python's built-in SHA-1. (socket stays: xml.sax.saxutils -> urllib -> email.utils
    # imports it at load, and without it the builder fails at once; tried 2026-09-23.)
    excluded = [arg for m in ('ssl', '_ssl', '_hashlib') for arg in ('--exclude-module', m)]
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onedir', '--console',
                    '--name', name, '--paths', 'tools', *hidden, *excluded,
                    '--distpath', 'build/dist', '--workpath', 'build/pyi', '--specpath', 'build/pyi',
                    script], cwd=ROOT, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def pillow_licence():
    import importlib.metadata
    dist = importlib.metadata.distribution('pillow')
    found = [dist.locate_file(f) for f in dist.files if f.name.upper() == 'LICENSE']
    if not found:
        raise SystemExit('Pillow is installed without its LICENSE file; it must ship with the builder')
    return pathlib.Path(found[0])


def face_section(ini):
    """The fork's ini as players get it: [Face] authority on, and nothing a tester sets in ANY section (A-27).
    Only [Face] and [Eyes] were scanned until the release review (2026-09-26); [Aim] has a probe too."""
    keys, section = {}, None
    for line in ini.splitlines():
        s = line.strip()
        if s.startswith('['):
            section = s
            keys.setdefault(section, {})
        elif section and '=' in s and not s.startswith(';'):
            key, value = s.split('=', 1)
            keys[section][key.strip()] = value.strip()
    face = keys.get('[Face]', {})
    testers = {f'{sec} {k}': v for sec, vals in keys.items() for k, v in vals.items()
               if k in ('probe', 'test') and v not in ('', '0')}
    if face.get('authority') != '1' or testers:
        raise SystemExit(f'Anatomy/ocbp.ini is not what players get: [Face] {face}, tester keys {testers}. Rerun '
                         'tools/physics_config.py (a dev ini with probe= or test= must not ship)')
    return '[Face]: authority=1; no probe or self-test in any section'


def files(version):
    dist = BUILD / 'dist/AnatomyBuilder'
    out = {
        'Anatomy.esp': BUILD / 'plugin/Anatomy.esp',
        'Scripts/Anatomy/Arousal.pex': BUILD / 'papyrus/Anatomy/Arousal.pex',
        'Scripts/AnatomyAim.pex': BUILD / 'papyrus/AnatomyAim.pex',
        'MCM/Config/Anatomy/config.json': BUILD / 'mcm/MCM/Config/Anatomy/config.json',
        'MCM/Config/Anatomy/settings.ini': BUILD / 'mcm/MCM/Config/Anatomy/settings.ini',
        'Tools/AnatomyBuilder/licences/Anatomy - LICENSE.txt': ROOT / 'LICENSE',
        # the builder runs on Python and Pillow, packed inside it: their notices go with them
        'Tools/AnatomyBuilder/licences/Python LICENSE.txt': pathlib.Path(sys.base_prefix) / 'LICENSE.txt',
        'Tools/AnatomyBuilder/licences/Pillow LICENSE.txt': pillow_licence(),
        'F4SE/Plugins/Anatomy/ocbp.ini': BUILD / 'config/Anatomy/ocbp.ini',
        'F4SE/Plugins/Anatomy/OCBPCollisionConfig.txt': BUILD / 'config/Anatomy/OCBPCollisionConfig.txt',
        'Tools/AnatomyBuilder/data/nahka_patch.json.gz': BUILD / 'patch/nahka_patch.json.gz',
        # the men's glans colour (A-31, MCM "Glans colour"): our own mask in BodyTalk4's UV. Until the
        # release gathering (2026-09-26) it was never listed, and the switch would have found no template
        'F4SE/Plugins/F4EE/Overlays/Anatomy.esp/overlays.json':
            BUILD / 'overlays/F4SE/Plugins/F4EE/Overlays/Anatomy.esp/overlays.json',
        'Materials/Overlays/Anatomy/AnatomyGlansFlush.bgem': BUILD / 'overlays/Materials/Overlays/Anatomy/AnatomyGlansFlush.bgem',
        'Textures/Overlays/Anatomy/GlansFlush.dds': BUILD / 'overlays/Textures/Overlays/Anatomy/GlansFlush.dds',
    }
    for p in sorted((BUILD / 'patch/tex').iterdir()):
        out[f'Tools/AnatomyBuilder/data/tex/{p.name}'] = p
    for p in sorted(dist.rglob('*')):
        if p.is_file() and p.parent.name != 'data' and 'data' not in p.relative_to(dist).parts[:1] \
                and p.name != 'AnatomyBuilder.log':
            out[f'Tools/AnatomyBuilder/{p.relative_to(dist).as_posix()}'] = p
    return out


def engine_files():
    return {
        'F4SE/Plugins/cbp.dll': FORK / 'x64/Release/cbp.dll',
        'F4SE/Plugins/fo4-ocbpc - GPL-3.0.txt': FORK / 'COPYING',            # the DLL's licence
        'F4SE/Plugins/fo4-ocbpc - MIT (OCBPC).txt': FORK / 'LICENSE',        # the notice of the code it carries
    }


def rebuild_files():
    dist = BUILD / 'dist/AnatomyRebuild'
    out = {
        'Tools/AnatomyRebuild/licences/Python LICENSE.txt': pathlib.Path(sys.base_prefix) / 'LICENSE.txt',
        'Tools/AnatomyRebuild/licences/Anatomy - LICENSE.txt': ROOT / 'LICENSE',
    }
    for p in sorted(dist.rglob('*')):
        if p.is_file() and p.name != 'AnatomyRebuild.log' and 'backup' not in p.relative_to(dist).parts:
            out[f'Tools/AnatomyRebuild/{p.relative_to(dist).as_posix()}'] = p
    return out


def fomod(version, title=TITLE, steps=NEXT_STEPS, entry='Run the Anatomy Builder, then BodySlide'):
    info = (f'<?xml version="1.0" encoding="UTF-8"?>\n<fomod>\n    <Name>{escape(title)}</Name>\n    <Author>{AUTHOR}</Author>\n'
            f'    <Version>{version}</Version>\n    <Description>{escape(steps)}</Description>\n</fomod>\n')
    config = f"""<?xml version="1.0" encoding="UTF-8"?>
<config xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://qconsulting.ca/fo3/ModConfig5.0.xsd">
    <moduleName>{escape(title)}</moduleName>
    <requiredInstallFiles>
        <folder source="Data" destination="" />
    </requiredInstallFiles>
    <installSteps order="Explicit">
        <installStep name="After installing">
            <optionalFileGroups order="Explicit">
                <group name="Next steps" type="SelectAll">
                    <plugins order="Explicit">
                        <plugin name="{escape(entry)}">
                            <description>{escape(steps)}</description>
                            <typeDescriptor>
                                <type name="Required" />
                            </typeDescriptor>
                        </plugin>
                    </plugins>
                </group>
            </optionalFileGroups>
        </installStep>
    </installSteps>
</config>
"""
    return info, config


def pack(name, version, wanted, readme_name, readme, fomod_args=None):
    """One archive: every file present, a README, a FOMOD page if asked, and every file listed back."""
    missing = [str(src) for src in wanted.values() if not src.exists()]
    if missing:
        raise SystemExit(f'{name}: missing {missing}')
    stage = BUILD / 'release' / f'{name}-{version}'
    if stage.exists():
        shutil.rmtree(stage)
    for rel, src in wanted.items():
        dst = stage / 'Data' / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    if fomod_args:
        info, config = fomod(version, *fomod_args)
        (stage / 'fomod').mkdir(parents=True, exist_ok=True)
        (stage / 'fomod/info.xml').write_text(info, encoding='utf-8')
        (stage / 'fomod/ModuleConfig.xml').write_text(config, encoding='utf-8')
        import xml.etree.ElementTree as ET
        ET.parse(stage / 'fomod/info.xml')
        ET.parse(stage / 'fomod/ModuleConfig.xml')             # both must at least be well-formed
    (stage / readme_name).write_text(readme.replace('\n', '\r\n'), encoding='utf-8')
    archive = stage.parent / f'{name}-{version}.7z'
    if archive.exists():
        archive.unlink()
    subprocess.run(['7z', 'a', '-t7z', '-mx=9', str(archive), '.\\*'], cwd=stage, check=True, stdout=subprocess.DEVNULL)
    listed = subprocess.run(['7z', 'l', '-sccUTF-8', str(archive)], capture_output=True, text=True).stdout
    all_files = [p.relative_to(stage) for p in stage.rglob('*') if p.is_file()]
    back = sum(1 for p in all_files if str(p) in listed)
    size = archive.stat().st_size // 1024
    print(f'{archive} ({size} KB): {len(all_files)} files ({len(wanted)} in Data), {back} listed back')
    if back != len(all_files):
        raise SystemExit(f'{name}: the archive does not list every file')
    return archive


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--version', default='1.0.0')
    ap.add_argument('--what', choices=('all', 'engine', 'anatomy', 'rebuild'), default='all')
    args = ap.parse_args()
    commit = build_dll()                                       # every archive names the engine commit
    print(f'engine: cbp.dll from fork commit {commit}')
    if args.what in ('all', 'engine'):
        pack(ENGINE, args.version, engine_files(), f'{ENGINE} - README.txt',
             ENGINE_README.replace('@FORK_COMMIT@', commit))
    if args.what in ('all', 'anatomy'):
        build_exe()
        wanted = files(args.version)
        if not any(k.endswith('AnatomyBuilder.exe') for k in wanted):
            raise SystemExit('PyInstaller ran but left no AnatomyBuilder.exe in build/dist/AnatomyBuilder')
        sys.path.insert(0, str(ROOT / 'tools'))
        import make_esp
        print(make_esp.verify(wanted['Anatomy.esp']))    # a keyword-less Anatomy.esp would move our layer into bodies
        print(face_section(wanted['F4SE/Plugins/Anatomy/ocbp.ini'].read_text(encoding='utf-8')))
        pack(NAME, args.version, wanted, f'{NAME} - README.txt', README.replace('@FORK_COMMIT@', commit),
             (TITLE, NEXT_STEPS, 'Run the Anatomy Builder, then BodySlide'))
    if args.what in ('all', 'rebuild'):
        build_exe('AnatomyRebuild', 'tools/rebuild.py', REBUILD_MODULES)
        wanted = rebuild_files()
        if not any(k.endswith('AnatomyRebuild.exe') for k in wanted):
            raise SystemExit('PyInstaller ran but left no AnatomyRebuild.exe in build/dist/AnatomyRebuild')
        pack('AnatomyRebuild', args.version, wanted, f'{REBUILD_TITLE} - README.txt', REBUILD_README,
             (REBUILD_TITLE, REBUILD_STEPS, 'Run Anatomy Rebuild after every BodySlide build'))


if __name__ == '__main__':
    sys.exit(main())
