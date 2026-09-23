# Research: a working vagina and anus on CBBE (Fallout 4)

Everything here was measured on the owner's install on 2026-09-23. It was not read off a mod page.

## Nothing ready-made exists for CBBE

A Nexus v2 GraphQL sweep (about 55 name and description queries) found no CBBE body weighted to
ZeX's genital bones. Bodies that do carry ZeX genital weights:

| Body | Where | Notes |
| --- | --- | --- |
| Fusion Girl | LoversLab | its own body; every outfit needs FG conversions |
| Zaz Atomic Fusion Body | Nexus 41693 (2020) | Atomic Beauty + FG genitals + ZeX weights |
| JaneBod Extended | Nexus 32442 (2021) | JaneBod + Animated Fannies' geometry, redone; ZeX weights, OCBP configs, modified ZeX skeleton |
| A-Body (male) | Nexus 66788 (2026) | SMP physics with collisions, EVB/AM based |

Access traps:
- nexusmods.com and loverslab.com pages answer 403 to scripted fetches.
- The Nexus API answers 403 unless the request carries a User-Agent header.

## CBBE's crotch is one closed skin

Welded by position (UV seams split vertices, so index topology lies), CBBE Body Physics has
exactly three real openings: the neck and both wrists. The midline across the crotch is a single
layer. Bones and physics can dent it and jiggle it, but never open it. **Weights alone cannot make
CBBE work.**

## Nahka's CBBEVaginaMorphs has the geometry

This is the body behind Animated Fannies (LoversLab 4302). Nahka's own files are linked from Nexus
98984 "Expand Holes": a Dropbox archive holding three variants plus textures.

| | CBBE Body Physics | CBBEVaginaMorphsPhysics |
| --- | --- | --- |
| vertices / triangles | 22,708 / 43,150 | 25,299 / 48,215 |
| openings | neck, 2 wrists | + 2 at the vulva (a slit) |
| geometry inside | none | vaginal canal ~6 units deep, anal ~16 |
| sliders | 84 | 83 of CBBE's (no FeetFeminine) + 12 genital |
| genital bones | none | none |

The 12 genital sliders are VaginaClitSize, VaginaInnie, VaginaInnie2, VaginaLabiaSize,
VaginaPenetrate, VaginaNarrower, VaginaSpread, VaginaSize, AnusBack, AnusDonut, AnusPenetrate and
ButtcheeksSpread.

Compared with today's CBBE:
- Every vertex except the feet and the crotch is identical.
- The feet moved by up to 0.6 units.
- Slider data drifts on the hips and buttocks, up to 0.9 on AppleCheeks.
- The shared bones' bind transforms agree to 0.00013.

Two cautions:
- The 2017 weights lean on five cloth bones today's CBBE no longer uses, CLOTH_Bone_LefTtools and
  others; 51 of the new vertices use them.
- The left foot has 225 same-UV twin vertices, so UV plus position cannot pair it. Topology decides
  (see `align_body.py`).

## ZeX genital bones, where they sit in body space

Read from a mesh already weighted to them (an FG outfit):

| bone | position (x, y, z) |
| --- | --- |
| Vagina_00 | (0, 4.00, -55.50) |
| Vagina_L_01 / Vagina_R_01 | (0, 2.45, -55.71) |
| Vagina_L_02 | (-0.64, 1.09, -55.71) |
| Vagina_R_02 | (0.53, 1.07, -55.71) |
| Anus_01 | (0, -2.98, -54.26) |
| Anus_02 | (0, -2.53, -54.49) |
| Anus_03 / Anus_04 | (±0.10, -2.76, -54.44) |

The character's left is -x and the front is +y. ZeX 6.0 also has `_CBP_` copies meant for physics.

## Physics on the owner's install

- **OCBPC 0.3.** Its keys, read from `cbp.dll`: `[ExtraOptions]` collisionX/Y/Z and
  adjacencyValue; `[AffectedNodes]` and `[ColliderNodes]`, each node with "x,y,z,radius" spheres;
  and in `ocbp.ini` `[General]`, playerOnly, npcOnly, detectArmor, femaleOnly and
  useWhitelist/Whitelist. Nothing genital-specific: the opening has to come from sphere placement
  (left labia pushed left, right pushed right) and penis-bone colliders.
- **ocbp.ini** is SQr17's CBBE 3BBB config. The owner's built body is weighted to the old
  `CLOTH_Bone_Googles` breast bones, NOT to `LBreast_skin`, so its breast sections move nothing.
  This side finding is parked.
- **FO4FasterHdtSMP** is installed too. SMP is the other route (A-Body uses it).
- Nexus 95003 is a newer OCBPC with an FPS fix and an MCM, worth checking before we tune.

## Outfit Studio 5.8.2 runs headless

`OutfitStudio.exe -a <script name>` runs `<BodySlide>/Automations/<name>.xml` (`<AutomationScript>`
with `<Step>` children) without showing a window. It exits 0 when clean and 10 on errors. Steps
include AddBone, AddCustomBone, DeleteBones, CopyBoneWeights, TransferWeights, ConformSliders,
ImportSliderData, LoadReference, AddProject and SaveProject, plus masks. `AddBone` takes bones from
`Anim/DefaultSkeletonReference` in `Config.xml`. The owner's points at BodySlide's vanilla skeleton,
which has no ZeX bones, so the lab copy gets its own config.
