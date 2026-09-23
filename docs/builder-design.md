# The builder (release plan item 4)

The player runs it once, like BodySlide or Nemesis. It reads what is on their machine and writes
**Anatomy - Generated**, a mod folder they install on top. Nothing of anyone else's is in our download
(release-plan.md).

## Where it runs

- The FOMOD installs it at `Data/Tools/AnatomyBuilder/AnatomyBuilder.exe`. Data is two folders up.
  - Vortex deploys by hardlink, so Data holds every mod's files and nothing else is needed.
  - MO2 players run it from MO2's executables list, like BodySlide. The virtual file system then shows
    it the merged Data, and its output lands in MO2's overwrite (or a folder they pick).
- `--data <path>` overrides the location, for testing and for unusual setups.

## Zero-touch (A-21): nothing it writes collides with another mod

The owner's polls: ship Nahka's files with credit; "manual steps is very badly treated by noobs";
then zero-touch. So:

- **The skeleton and the physics configs are not the builder's job any more.** The fork adds our
  bones at run time to whatever skeleton loads, and reads its own `F4SE/Plugins/Anatomy/*` on top of
  the player's configs. Both files are static and ship in the FOMOD.
- **The genitals get their own mesh part and texture** (a separate shape with its own material,
  `Textures/Anatomy/...`). The skin mod's files are never touched.
- **So the builder writes only new paths**, straight into Data. MO2 players run it from MO2 and the
  files land in overwrite. There is nothing to resolve.

## What it reads (the winning copy: loose first, then BA2s in load order; `gamedata.py`)

| input | used for |
| --- | --- |
| CBBE's BodySlide files: `Tools/BodySlide/SliderSets/CBBE.osp`, `ShapeData/CBBE/CBBEBodyPhysics.nif/.osd` | the body the genitals are fitted into |
| Nahka's files: shipped by us, with credit | the genitals' geometry, sliders and texture |
| the player's skin: `Textures/Actors/Character/BaseHumanFemale/FemaleBody_d/n/s` (loose or DX10 BA2) | colour-matching our genital texture to their skin at the seam |

## What it writes

- `Tools/BodySlide/SliderSets/AnatomyBody.osp` and `ShapeData/AnatomyBody/*`: CBBE plus the genitals
  as their own shape. The player builds "Anatomy Body" in BodySlide with their preset, as with any
  CBBE body.
- `Textures/Anatomy/Genitals_d/n/s.dds`: Nahka's texture, matched to the player's skin.
- `AnatomyBuilder.log`: every input it used (path, archive, size, sha1) and every check's result.

## Every stage proves itself or stops

The current tools already do this, and the builder keeps it:

- align_body's shared-vertex match;
- zex_bones' bind checks;
- verify_zex's full pass;
- the texture's checks.

A failed check stops the build and names the input.
