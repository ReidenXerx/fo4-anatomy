"""Assemble the release archives (release-plan.md): the engine, Anatomy, and its two tools.

    python tools/release.py [--version 1.0.1] [--what all|engine|anatomy|builder|rebuild]
        -> build/release/fo4-ocbpc-<version>.7z        the engine: cbp.dll, its own Nexus page
           build/release/Anatomy-<version>.7z          Anatomy's GAME files (requires the engine): Nexus
           build/release/AnatomyBuilder-<version>.zip  the builder, alone: GitHub releases only
           build/release/AnatomyRebuild-<version>.zip  Anatomy Rebuild, alone: GitHub releases only
    ("all" is the last three; the engine is released on its own.)

The tools live on GitHub only (the owner's poll, 2026-09-26): Nexus's automated check quarantined
Anatomy 1.0.0 and its Rebuild file for "executables and similar file types" (the PyInstaller exes and
their _internal .pyd/.dll). So the Nexus archive carries no .exe, .dll or .pyd anywhere, and refuses to
build if one gets in. The tools find the game themselves (gamedata.find_data), wherever they are put.

Two mods since the owner's release call (2026-09-26: "separately our upgraded cbp engine and
anatomy"): the engine is the ONLY archive carrying cbp.dll, so a player never resolves two copies of it
and Anatomy never ships a DLL older than the engine's page.

Anatomy (the Nexus archive) ships:
    Anatomy.esp, Scripts/Anatomy/Arousal.pex, MCM/Config/Anatomy/*     arousal and its menu
    Scripts/AnatomyAim.pex                                             the aim's scene list (A-28)
    F4SE/Plugins/F4EE/Overlays/Anatomy.esp, Materials|Textures/Overlays/Anatomy   the glans colour (A-31)
    F4SE/Plugins/Anatomy/ocbp.ini, OCBPCollisionConfig.txt             our physics lines and [Bones]
    fomod/info.xml, fomod/ModuleConfig.xml                             one page: what to do next
    Anatomy - README.txt, Anatomy - LICENSE.txt                        install, credits, licences
The builder's zip carries AnatomyBuilder.exe (+ _internal), data/nahka_patch.json.gz and data/tex/* (her
genitals, as a patch and her texture island: nothing of anyone else's but Nahka's own work, with her
page's permission, A-23) and the Python and Pillow licences.
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
TOOLS_URL = 'https://github.com/ReidenXerx/fo4-anatomy/releases'   # the builder and Rebuild zips
BINARIES = ('.exe', '.dll', '.pyd')                         # never in the Nexus archive (Nexus quarantine)

NEXT_STEPS = f"""Anatomy needs the fo4-ocbpc engine (its cbp.dll), a separate download.
After this installs:
1. Get the latest AnatomyBuilder zip from
   {TOOLS_URL}
   extract it into a folder of its own and run AnatomyBuilder.exe once. It finds your game by
   itself. MO2: add it to MO2's executables and run it from there, like BodySlide. It builds the body from YOUR CBBE and skin.
2. Open BodySlide, choose "Anatomy Body", your preset, and Build.
Re-run the builder whenever you change your CBBE or your skin mod.
Optional: Anatomy Rebuild (the latest AnatomyRebuild zip, same page) after every BodySlide build."""

README = f"""{TITLE}
Working genitals for Fallout 4 CBBE women: physics, arousal, contact.

WHAT YOU NEED
  Fallout 4 1.10.163 (Steam or GOG, not the next-gen update) with F4SE 0.6.23.
  The fo4-ocbpc engine (cbp.dll, its own download), CBBE (with its BodySlide files) and BodySlide.
  LooksMenu for the arousal nipples and the glans colour; AAF for scenes; MCM for the settings page.
  A physics config (e.g. Jiggle Physics / MadKita's) is optional; Anatomy brings its own lines.

INSTALL
  1. Install the fo4-ocbpc engine, then this archive, with your mod manager. Nothing of this archive
     overlaps another mod, and it holds no program: the tools are on GitHub.
  2. Download the latest AnatomyBuilder zip from
       {TOOLS_URL}
     extract it into a folder of its own (anywhere; Data\\Tools works too) and run AnatomyBuilder.exe once. It finds your game by
     itself (or run it with --data "<your Fallout 4>\\Data"). MO2: add it to MO2's executables and run
     it from MO2, as you do BodySlide; outside MO2 it cannot see MO2's mods. It reads your CBBE, your
     skeleton and your skin (as the game loads them), checks every step, and writes only new files:
       Tools\\BodySlide\\SliderSets\\Anatomy.osp and ShapeData\\Anatomy\\*, the "Anatomy Body" set
       Textures\\Anatomy\\*, Materials\\Anatomy\\*, the genitals' own texture and material
     Its log is AnatomyBuilder.log next to it.
  3. BodySlide: choose "Anatomy Body", your preset, Build (or Batch Build). The category "Anatomy"
     has "Opening, front": extra opening toward the front, on top of the built-in one (0% leaves
     it as designed).
  Re-run the builder after changing your CBBE, skin or physics preset (ocbp.ini).
  4. Optional, Anatomy Rebuild (the latest AnatomyRebuild zip, same page): run it after every
     BodySlide build. It gives your built outfits the body's hip handover and the body's neck its seam fix, which BodySlide itself
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
  Anatomy is distributed under the GNU General Public License, version 3 (Anatomy - LICENSE.txt).
  Its source: {ANATOMY_URL}
  The engine's source: {FORK_URL} (this release was made with commit @FORK_COMMIT@).
  The plugin, scripts, MCM and configs are our own work. The builder and Rebuild are our own code, run
  by Python (and Pillow, for the builder), packed inside them with their licences.
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

BUILDER_README = f"""Anatomy Builder (for Anatomy - CBBE Genitals, Physics and Arousal)
Builds the Anatomy body on your PC from YOUR CBBE, skin and skeleton. Nexus carries Anatomy's game
files; its tools are here, on GitHub ({TOOLS_URL}).

INSTALL AND RUN
  1. Install the fo4-ocbpc engine and Anatomy with your mod manager.
  2. Extract this zip into a folder of its own (anywhere; <your Fallout 4>\\Data\\Tools works too).
  3. Vortex, or no mod manager: double-click AnatomyBuilder\\AnatomyBuilder.exe.
     MO2: add AnatomyBuilder.exe to MO2's executables and run it from MO2, like BodySlide. Run
     outside MO2, it cannot see the mods MO2 manages.
     It finds the game by itself: the Data folder it sits in, else the folder the game's installer
     recorded (Steam or GOG). If it cannot, run it with --data "<your Fallout 4>\\Data".
     It reads CBBE's BodySlide set, your skeleton and your skin as the game loads them, checks every
     stage, and writes only new files into Data (MO2: into its overwrite folder): the "Anatomy Body"
     BodySlide set and the genitals' own texture and material. Its log is AnatomyBuilder.log beside it.
  4. BodySlide: choose "Anatomy Body", your preset, and Build.
  Re-run it after changing your CBBE or your skin mod.

LICENCES
  GNU General Public License, version 3 (licences\\Anatomy - LICENSE.txt). Source: {ANATOMY_URL}
  It runs on Python and Pillow, packed inside it under their own licences (licences\\). data\\ holds
  Nahka's genitals as a patch against your CBBE, with her permission ("up for adoption").
"""

REBUILD_TITLE = 'Anatomy Rebuild'
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
  2. Extract this zip into a folder of its own and KEEP it there: its backup\\ (for --undo) lives
     beside it. Anywhere works; it finds your game by itself, or takes --data "<your Fallout 4>\\Data".
  3. Vortex, or no mod manager: run AnatomyRebuild\\AnatomyRebuild.exe. MO2: add it to MO2's
     executables and run it from MO2, like BodySlide. The log is AnatomyRebuild.log beside it.
  4. After every BodySlide build, run it again: BodySlide writes its meshes whole.
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


# Microsoft Defender's cloud ML flagged the 1.0.1 exes "Trojan:Win32/Wacatac.B!ml" on VirusTotal (3/75; the
# 1.0.0 ones were 2/75 without Microsoft; the owner's scans, 2026-09-26). The usual trigger is PyInstaller's
# stock, prebuilt bootloader, shared by countless packed malware samples. So the release's exes get a
# bootloader compiled here from PyInstaller's own source (MSVC, into build/pyi-venv) and a version-info
# resource saying what they are. Local Defender flagged neither version: only a VirusTotal scan decides.
PYI_VERSION = '6.22.3'
PYI_VENV = BUILD / 'pyi-venv'
VCVARS = r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat'
DESCRIPTIONS = {'AnatomyBuilder': 'Anatomy Builder: builds the Anatomy body from your own CBBE and skin',
                'AnatomyRebuild': 'Anatomy Rebuild: the hip and neck fixes on your BodySlide builds'}


def source_bootloader_python():
    """The Python of a venv whose PyInstaller carries a bootloader compiled from source (made once)."""
    py = PYI_VENV / 'Scripts/python.exe'
    marker = PYI_VENV / f'pyinstaller-{PYI_VERSION}-source-bootloader'
    if marker.exists():
        return py
    subprocess.run([sys.executable, '-m', 'venv', str(PYI_VENV)], check=True)
    subprocess.run([str(py), '-m', 'pip', 'install', '-q', 'pillow'], check=True)
    script = PYI_VENV / 'build-bootloader.bat'
    script.write_text(f'@call "{VCVARS}" >nul || exit /b 1\r\n'
                      f'@set PYINSTALLER_COMPILE_BOOTLOADER=1\r\n'
                      f'@"{py}" -m pip install --no-binary pyinstaller --no-cache-dir pyinstaller=={PYI_VERSION}\r\n',
                      encoding='utf-8')
    subprocess.run(['cmd', '/c', str(script)], check=True, stdout=subprocess.DEVNULL)
    marker.write_text('PyInstaller installed from source with PYINSTALLER_COMPILE_BOOTLOADER=1\n', encoding='utf-8')
    return py


def version_file(name, version):
    """A VS_VERSIONINFO resource for the exe: who made it and what it is (PyInstaller --version-file)."""
    nums = [int(x) for x in (version.split('.') + ['0', '0', '0'])[:4]]
    v = '.'.join(map(str, nums))
    f = BUILD / 'pyi' / f'{name}-version.txt'
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers={tuple(nums)}, prodvers={tuple(nums)}, mask=0x3f, flags=0x0, OS=0x40004,
                    fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', '{AUTHOR}'),
      StringStruct('FileDescription', '{DESCRIPTIONS[name]}'),
      StringStruct('FileVersion', '{v}'),
      StringStruct('InternalName', '{name}'),
      StringStruct('LegalCopyright', 'GNU GPL v3; source: {ANATOMY_URL}'),
      StringStruct('OriginalFilename', '{name}.exe'),
      StringStruct('ProductName', 'Anatomy for Fallout 4'),
      StringStruct('ProductVersion', '{v}')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
""", encoding='utf-8')
    return f


NUITKA_VERSION = '4.2.2'
NUITKA_VENV = BUILD / 'nuitka-venv'


def nuitka_python():
    """A venv holding Nuitka and the tools' own dependencies (made once)."""
    py = NUITKA_VENV / 'Scripts/python.exe'
    if not py.exists():
        subprocess.run([sys.executable, '-m', 'venv', str(NUITKA_VENV)], check=True)
        subprocess.run([str(py), '-m', 'pip', 'install', '-q', f'nuitka=={NUITKA_VERSION}', 'pillow', 'ordered-set',
                        'zstandard'], check=True)
    return py


def build_nuitka(name, script, modules, version):
    """Nuitka standalone build of a tool into build/dist/<name> (wiped first): the Python compiled to C with
    MSVC, so there is no PyInstaller bootloader at all. Microsoft's cloud ML flagged the PyInstaller builds
    "Wacatac.B!ml" with the stock bootloader AND with one compiled from source (candidate B, 2026-09-26)."""
    nums = '.'.join((version.split('.') + ['0', '0', '0'])[:4])
    out = BUILD / 'nuitka' / name
    if out.exists():
        shutil.rmtree(out)
    stem = pathlib.Path(script).stem
    subprocess.run([str(nuitka_python()), '-m', 'nuitka', '--standalone', '--assume-yes-for-downloads',
                    '--msvc=latest', '--windows-console-mode=force', f'--output-dir={out}',
                    f'--output-filename={name}.exe', f'--company-name={AUTHOR}',
                    '--product-name=Anatomy for Fallout 4', f'--file-version={nums}', f'--product-version={nums}',
                    f'--file-description={DESCRIPTIONS[name]}',
                    f'--copyright=GNU GPL v3; source: {ANATOMY_URL}',
                    # no network: no OpenSSL in the bundle (as the PyInstaller builds; _ssl pulled libssl/libcrypto in)
                    *[f'--nofollow-import-to={m}' for m in ('ssl', '_ssl', '_hashlib')],
                    *[f'--include-module={m}' for m in modules], script],
                   cwd=ROOT, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    dist = BUILD / 'dist' / name
    if dist.exists():
        shutil.rmtree(dist)
    shutil.move(str(out / f'{stem}.dist'), str(dist))
    if not (dist / f'{name}.exe').exists():
        raise SystemExit(f'Nuitka ran but left no {name}.exe')


def build_exe(name='AnatomyBuilder', script='tools/builder.py', modules=BUILDER_MODULES, version='0.0.0',
              bootloader='nuitka'):
    """One-folder build of a tool into build/dist/<name> (wiped first). bootloader: 'nuitka' (the default:
    compiled, no bootloader), 'source' (PyInstaller, bootloader compiled here) or 'prebuilt' (stock PyInstaller).
    The tools import their stages by name at run time, so each is named here as a hidden import."""
    if bootloader == 'nuitka':
        return build_nuitka(name, script, modules, version)
    python = source_bootloader_python() if bootloader == 'source' else pathlib.Path(sys.executable)
    hidden = [arg for m in modules for arg in ('--hidden-import', m)]
    # no network, so no OpenSSL in the bundle: urllib and http.client take ssl as optional, and hashlib
    # falls back to Python's built-in SHA-1. (socket stays: xml.sax.saxutils -> urllib -> email.utils
    # imports it at load, and without it the builder fails at once; tried 2026-09-23.)
    excluded = [arg for m in ('ssl', '_ssl', '_hashlib') for arg in ('--exclude-module', m)]
    subprocess.run([str(python), '-m', 'PyInstaller', '--noconfirm', '--clean', '--onedir', '--console',
                    '--noupx', '--version-file', str(version_file(name, version)),
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
               if k in ('probe', 'test', 'discover') and v not in ('', '0')}
    if face.get('authority') != '1' or testers:
        raise SystemExit(f'Anatomy/ocbp.ini is not what players get: [Face] {face}, tester keys {testers}. Rerun '
                         'tools/physics_config.py (a dev ini with probe= or test= must not ship)')
    return '[Face]: authority=1; no probe or self-test in any section'


def files(version):
    """Anatomy's game files (the Nexus archive): no program of any kind."""
    return {
        'Anatomy.esp': BUILD / 'plugin/Anatomy.esp',
        'Scripts/Anatomy/Arousal.pex': BUILD / 'papyrus/Anatomy/Arousal.pex',
        'Scripts/AnatomyAim.pex': BUILD / 'papyrus/AnatomyAim.pex',
        'MCM/Config/Anatomy/config.json': BUILD / 'mcm/MCM/Config/Anatomy/config.json',
        'MCM/Config/Anatomy/settings.ini': BUILD / 'mcm/MCM/Config/Anatomy/settings.ini',
        'F4SE/Plugins/Anatomy/ocbp.ini': BUILD / 'config/Anatomy/ocbp.ini',
        'F4SE/Plugins/Anatomy/OCBPCollisionConfig.txt': BUILD / 'config/Anatomy/OCBPCollisionConfig.txt',
        # A-46: our own default physics preset and collision, read by the engine only when the player has none
        'F4SE/Plugins/Anatomy/ocbp-default.ini': BUILD / 'config/Anatomy/ocbp-default.ini',
        'F4SE/Plugins/Anatomy/OCBPCollisionConfig-default.txt': BUILD / 'config/Anatomy/OCBPCollisionConfig-default.txt',
        # the men's glans colour (A-31, MCM "Glans colour"): our own mask in BodyTalk4's UV. Until the
        # release gathering (2026-09-26) it was never listed, and the switch would have found no template
        'F4SE/Plugins/F4EE/Overlays/Anatomy.esp/overlays.json':
            BUILD / 'overlays/F4SE/Plugins/F4EE/Overlays/Anatomy.esp/overlays.json',
        'Materials/Overlays/Anatomy/AnatomyGlansFlush.bgem': BUILD / 'overlays/Materials/Overlays/Anatomy/AnatomyGlansFlush.bgem',
        'Textures/Overlays/Anatomy/GlansFlush.dds': BUILD / 'overlays/Textures/Overlays/Anatomy/GlansFlush.dds',
    }


def builder_files():
    """The builder's zip: AnatomyBuilder/ with the exe, its data (Nahka's patch) and the licences."""
    dist = BUILD / 'dist/AnatomyBuilder'
    out = {
        'AnatomyBuilder/licences/Anatomy - LICENSE.txt': ROOT / 'LICENSE',
        # the builder runs on Python and Pillow, packed inside it: their notices go with them
        'AnatomyBuilder/licences/Python LICENSE.txt': pathlib.Path(sys.base_prefix) / 'LICENSE.txt',
        'AnatomyBuilder/licences/Pillow LICENSE.txt': pillow_licence(),
        'AnatomyBuilder/data/nahka_patch.json.gz': BUILD / 'patch/nahka_patch.json.gz',
    }
    for p in sorted((BUILD / 'patch/tex').iterdir()):
        out[f'AnatomyBuilder/data/tex/{p.name}'] = p
    for p in sorted(dist.rglob('*')):
        if p.is_file() and p.parent.name != 'data' and 'data' not in p.relative_to(dist).parts[:1] \
                and p.name != 'AnatomyBuilder.log':
            out[f'AnatomyBuilder/{p.relative_to(dist).as_posix()}'] = p
    return out


def engine_files():
    return {
        'F4SE/Plugins/cbp.dll': FORK / 'x64/Release/cbp.dll',
        'F4SE/Plugins/fo4-ocbpc - GPL-3.0.txt': FORK / 'COPYING',            # the DLL's licence
        'F4SE/Plugins/fo4-ocbpc - MIT (OCBPC).txt': FORK / 'LICENSE',        # the notice of the code it carries
    }


def rebuild_files():
    """Rebuild's zip: AnatomyRebuild/ with the exe and the licences."""
    dist = BUILD / 'dist/AnatomyRebuild'
    out = {
        'AnatomyRebuild/licences/Python LICENSE.txt': pathlib.Path(sys.base_prefix) / 'LICENSE.txt',
        'AnatomyRebuild/licences/Anatomy - LICENSE.txt': ROOT / 'LICENSE',
    }
    for p in sorted(dist.rglob('*')):
        if p.is_file() and p.name != 'AnatomyRebuild.log' and 'backup' not in p.relative_to(dist).parts:
            out[f'AnatomyRebuild/{p.relative_to(dist).as_posix()}'] = p
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


def sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def pack_zip(name, version, wanted, readme_name, readme):
    """A tool's zip for the GitHub release: its folder, a README beside it, every entry read back."""
    import zipfile
    missing = [str(src) for src in wanted.values() if not src.exists()]
    if missing:
        raise SystemExit(f'{name}: missing {missing}')
    archive = BUILD / 'release' / f'{name}-{version}.zip'
    archive.parent.mkdir(parents=True, exist_ok=True)
    if archive.exists():
        archive.unlink()
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr(readme_name, readme.replace('\n', '\r\n'))
        for rel, src in wanted.items():
            z.write(src, rel)
    with zipfile.ZipFile(archive) as z:
        names = set(z.namelist())
        bad = z.testzip()
    if bad or names != set(wanted) | {readme_name}:
        raise SystemExit(f'{name}: the zip does not read back as written ({bad or "entries differ"})')
    print(f'{archive} ({archive.stat().st_size // 1024} KB): {len(names)} entries\n  sha256 {sha256(archive)}')
    return archive


def pack(name, version, wanted, readme_name, readme, fomod_args=None, extras=None, no_binaries=False):
    """One archive: every file present, a README, a FOMOD page if asked, and every file listed back.
    extras: {name at the archive's root: source}. no_binaries: refuse any .exe/.dll/.pyd anywhere in it."""
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
    for rel, src in (extras or {}).items():
        shutil.copy2(src, stage / rel)
    if no_binaries:
        found = [str(q.relative_to(stage)) for q in stage.rglob('*') if q.suffix.lower() in BINARIES]
        if found:
            raise SystemExit(f'{name}: a program in the Nexus archive (Nexus quarantines these): {found}')
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
    if no_binaries:                                      # and the archive itself, as Nexus will read it
        rows = [line.split()[-1] for line in listed.splitlines() if len(line.split()) >= 6]
        found = [r for r in rows if r.lower().endswith(BINARIES)]
        if found:
            raise SystemExit(f'{name}: the built archive lists a program: {found}')
    print(f'  sha256 {sha256(archive)}')
    return archive


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--version', default='1.0.1')
    ap.add_argument('--what', choices=('all', 'engine', 'anatomy', 'builder', 'rebuild'), default='all')
    ap.add_argument('--bootloader', choices=('nuitka', 'source', 'prebuilt'), default='nuitka',
                    help="how the tools are packed: Nuitka (default, no bootloader), or PyInstaller with its "
                         "bootloader compiled here from source, or its stock one")
    args = ap.parse_args()
    commit = build_dll()                                       # every archive names the engine commit
    print(f'engine: cbp.dll from fork commit {commit}')
    if args.what == 'engine':
        pack(ENGINE, args.version, engine_files(), f'{ENGINE} - README.txt',
             ENGINE_README.replace('@FORK_COMMIT@', commit))
    if args.what in ('all', 'anatomy'):
        wanted = files(args.version)
        sys.path.insert(0, str(ROOT / 'tools'))
        import make_esp
        print(make_esp.verify(wanted['Anatomy.esp']))    # a keyword-less Anatomy.esp would move our layer into bodies
        print(face_section(wanted['F4SE/Plugins/Anatomy/ocbp.ini'].read_text(encoding='utf-8')))
        pack(NAME, args.version, wanted, f'{NAME} - README.txt',
             README.replace('@FORK_COMMIT@', commit),   # the tools version on their own (A-40): the
             (TITLE, NEXT_STEPS, 'Get the Anatomy Builder, run it, then BodySlide'),   # texts say 'latest'
             extras={f'{NAME} - LICENSE.txt': ROOT / 'LICENSE'}, no_binaries=True)
    if args.what in ('all', 'builder'):
        build_exe(version=args.version, bootloader=args.bootloader)
        wanted = builder_files()
        if not any(k.endswith('AnatomyBuilder.exe') for k in wanted):
            raise SystemExit('PyInstaller ran but left no AnatomyBuilder.exe in build/dist/AnatomyBuilder')
        pack_zip('AnatomyBuilder', args.version, wanted, 'Anatomy Builder - README.txt', BUILDER_README)
    if args.what in ('all', 'rebuild'):
        build_exe('AnatomyRebuild', 'tools/rebuild.py', REBUILD_MODULES, args.version, args.bootloader)
        wanted = rebuild_files()
        if not any(k.endswith('AnatomyRebuild.exe') for k in wanted):
            raise SystemExit('PyInstaller ran but left no AnatomyRebuild.exe in build/dist/AnatomyRebuild')
        pack_zip('AnatomyRebuild', args.version, wanted, f'{REBUILD_TITLE} - README.txt', REBUILD_README)


if __name__ == '__main__':
    sys.exit(main())
