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
| geometry inside | none | vaginal canal ~6 units deep; anal pocket ~2 units (corrected: an early count included the buttock crack's skin) |
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

## Outfit Studio 5.8.2 runs headless, but it is not master

`OutfitStudio.exe -a <script name>` runs `<ProjectPath>/Automations/<name>.xml` (`<AutomationScript>`
with `<Step type="...">` children) without showing a window. This was proven in the lab: the log
said "Running script ... in headless mode".

The v5.8.2 tag's source differs from master, and master is what I read first:

- **39 step types.** Among them LoadReference, AddProject, CopyBoneWeights, DeleteBones,
  AddCustomBone (name, parent, translation and rotation vector), EditBone, ConformSliders,
  ImportSliderData, SaveProject, LoadMask, ClearMask and RemoveUnusedNodes. There is **no
  AddBone** from the skeleton, no TransferWeights and no LogMessage. An unknown type silently
  becomes LoadReference: measured, a LogMessage step ran as "LoadReference - no source file".
- **The exit code is 0 even when a step fails.** Only master passes it on. Judge a run by
  `Log_OS.txt`, where level `[1]` is an error; `tools/lab.py` does this.
- **Bones reach the body through CopyBoneWeights.** It copies the listed bones' weights from the
  loaded reference by proximity (ProximityRadius, MaxResults), adds the bones the target lacks,
  honours a loaded mask, spreads the difference over the normalize bones, then runs
  `CleanupBones`. So does `OutfitProject::Save` (OutfitProject.cpp:535 in v5.8.2), and
  `CleanupBones` removes every bone that carries no weight. A bone added by `AddCustomBone` and
  left unweighted therefore never reaches the saved file. Bones arrive only with weights, from a
  WEIGHTED reference (A-3).
- `Anim/DefaultSkeletonReference` in `Config.xml` names the skeleton that custom bones and poses
  use. The owner's points at BodySlide's vanilla skeleton, so the lab copy points at ZeX.

## JaneBod Extended, read from its files (the A-3 reference)

- **Mesh:** `JaneBodyHDShapeDataVag`, 24,924 vertices, 50 bones.
- **Genital weights on the ANIMATED ZeX bones only:** Vagina_00, Vagina_L/R_01-02 and
  Anus_01-04, never the `_CBP_` copies. The weights are light: at most 0.37 on L_02/R_02, 0.20-0.22
  on 00/L_01/R_01, 0.10 on the anus, and no vertex above 0.5. They are layered over Pelvis_skin,
  SPINE1, the thighs and Butt_CBP.
- **Physics:** its `ocbp.ini` attaches breasts, butt, belly, thighs and balls, and NO vagina or
  anus bone. Its genitals move by animation (ZeX-rigged animations moving the genital bones) and by
  Animated Fannies' morphs, never by physics or collision. Its [General] also has playerOnly=1 and
  detectArmor=1.
- **Its "modified skeleton"** only re-parents HEAD, Neck, the collarbones and shoulder fat under
  `CME_*` scaling nodes. It is an older ZeX without Penis_CBP, Tail_CBP or Thigh_CBP. The genital
  bones are identical to ZeX 6.0.
- **Frame:** JaneBod's mesh space is ours translated by (0, -0.882, +120.843). This was measured
  on Pelvis_skin and SPINE1, which agree exactly; its Vagina_00 maps onto ZeX's (0, 4.00, -55.50).
- **Overlap:** after that shift, our 2,811 genital vertices lie within 0.23 units of JaneBod's
  (median; 0.47 at 90%, 0.77 max), and both vaginal canals reach the same depth. Both descend from
  Animated Fannies' geometry, so a proximity copy transfers its pattern faithfully.

## What original CBP does to a bone it simulates (the reason ZeX has `_CBP_` copies)

From `cbpphysics/CBPSSE` Thing.cpp, `Thing::update`: every frame it SETS
`m_localTransform.pos = ldiff * linear` and `rot = Euler(0, 0, rdiff.z)`. It does not add to the
animated transform. A bone that both an animation and the physics move therefore ends up where
the physics says. ZeX's answer is twin bones: animations move `Vagina_L_01`, physics moves
`Vagina_CBP_L_01`. A vertex weighted to BOTH gets both motions.

OCBP (the Fallout 4 port) must at least keep a bone's rest offset: `Penis_Balls_CBP_01` sits
7.6 units from its parent, and popular configs jiggle it without it snapping. Whether OCBP also
discards the animated transform is unmeasured; the in-game test decides it. The anus has no twins,
so its physics would sit on the animated bones directly.
