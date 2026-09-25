# Anatomy - CBBE Genitals, Physics and Arousal

Working genitals for Fallout 4's CBBE women: a real vulva, vaginal canal and anus, bones added at
run time to whatever skeleton you have, collision physics that opens the body to a penis, a hand or a
toy, a mouth that opens to what is at the lips, penis aim into the right opening, and arousal.

**Every feature, with its measurements: [docs/FEATURES.md](docs/FEATURES.md).**

It runs on [fo4-ocbpc](https://github.com/ReidenXerx/fo4-ocbpc), an extended OCBPC `cbp.dll`
released as its own mod. The body is built on the player's PC from their own CBBE and skin: nothing
of CBBE's or Nahka's original files is in this repository or in the release (decisions A-2, A-23).

## For players

Requirements: Fallout 4 1.10.163 (Steam or GOG, not next-gen), F4SE 0.6.23, the fo4-ocbpc engine,
CBBE with its BodySlide files, BodySlide. LooksMenu (nipples, glans colour), AAF (scenes) and MCM
(settings) for the parts that use them.

1. Install the engine, then Anatomy.
2. Run `Data\Tools\AnatomyBuilder\AnatomyBuilder.exe` once (MO2: run it from MO2, like BodySlide).
3. BodySlide: "Anatomy Body", your preset, Build.
4. Optional: after every BodySlide build, run `Data\Tools\AnatomyRebuild\AnatomyRebuild.exe` (its own
   download) for the outfit hip fix and the neck seam fix.

Re-run the builder after changing your CBBE or skin mod.

## What is here

| path | what |
| --- | --- |
| `tools/builder.py` | the Anatomy Builder (packed as `AnatomyBuilder.exe`): every stage proves itself or stops |
| `tools/rebuild.py` | Anatomy Rebuild (packed as `AnatomyRebuild.exe`): outfit hip handover and neck seam on the player's builds |
| `tools/release.py` | builds the three archives: the engine, Anatomy, Anatomy Rebuild |
| `papyrus/` | `Anatomy:Arousal` (arousal, nipples, glans colour, the aim's scene list) and `AnatomyAim` |
| `tools/make_esp.py`, `tools/build_mcm.py` | `Anatomy.esp` and the MCM page, generated and verified |
| `tools/physics_design.py`, `tools/physics_config.py` | Anatomy's `ocbp.ini` and collision lines |
| `tools/align_body.py`, `apply_patch.py`, `zex_bones.py`, `hip_fold.py`, `split_genitals.py`, `genital_texture.py`, `neck_seam.py` | the body's stages |
| `tools/verify_*.py`, `compare_builds.py`, `pose_check.py`, `fit_check.py`, `ocbpc_sim.py`, `tube_check.py`, `lips.py`, `canal.py`, `glans_profile.py` | the measurements behind every number: offline physics, poses, lips, canal paths |
| `tools/garments.py`, `tools/rebuild_all.py` | the curator's own full BodySlide rebuild (women, men, outfits) |
| `docs/decisions.md` | every decision (A-1 ..), with what was measured and why |

The tools rebuild everything from inputs you place in `inputs/` (Nahka's BodySlide files) and your
installed CBBE; third-party files never enter the repository (`.gitignore`).

## Licence

GNU General Public License, version 3 (`LICENSE`). The engine is GPL-3.0 too, with an MIT base
(see its repository).

## Credits

Nahka (the vulva and anus geometry, sliders and texture: Animated Fannies, "up for adoption"), with
BringTheNoise and Alan (UN7B); Ousnius and the CBBE team; ericncream and the OpenCBP authors;
maximusmaxy, whose Screen Archer Menu source documented the face data the mouth uses.
