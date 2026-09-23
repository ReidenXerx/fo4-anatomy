# Decisions

Numbered, settled. A later entry may supersede an earlier one; say so in both.

## A-1 — Full physics, not morphs alone (owner poll, 2026-09-23)

The body opens because something pushes it open: ZeX genital bones weighted into the mesh, driven by
OCBP physics, pushed by OCBPC collision spheres on the partner's penis bones. Morph-driven opening
(Animated Fannies' way) may be layered on later as a resting shape, never as the mechanism.

## A-2 — It ships one day, so third-party assets never enter the repo (owner poll, 2026-09-23)

The owner answered "ship it eventually". Nothing here may depend on redistributing someone else's
geometry without their permission. Consequences:

- The repository holds tools, our own configs and docs. Inputs (Nahka's CBBEVaginaMorphs, CBBE,
  JaneBod Extended) live in `inputs/` and are gitignored, and every output is rebuilt from them.
- Before any release: written permission from Nahka (the geometry) and from the CBBE team (a CBBE
  derivative; 3BBB needed theirs), OR our own geometry. Asking is outward-facing, so it is the
  owner's act.

## A-3 — JaneBod Extended is the reference for ZeX weights and physics values (owner poll, 2026-09-23)

JBE (Nexus 32442) ships genital weights on ZeX bones and OCBP configs that were tuned in game. The
owner downloads it through Vortex without installing it, and the tools read the archive. It is a
reference, never an input copied into the output.

## A-4 — Geometry: Nahka's CBBEVaginaMorphs, aligned to today's CBBE (agent, 2026-09-23)

Nahka's physics variant is CBBE plus 2,591 vertices: a real slit, a vaginal canal about 6 units
deep and a shallow anal pocket about 2 units deep. It has twelve genital sliders (VaginaPenetrate, AnusPenetrate, ...)
and no genital bones. CBBE itself is ONE closed skin at the crotch, so no amount of weighting could
open it. This is measured, see `research.md`.

Alignment rule: every vertex Nahka shares with today's CBBE, matched by UV and position,
takes today's CBBE exactly: position, normal, tangent, weights and every slider diff. So outfits and
Silhouette's presets behave exactly as they do on CBBE today. The new or changed genital vertices
keep Nahka's shapes, corrected so they meet the aligned skin without a seam.

Why not conform everything from CBBE: conform averages neighbours, so it would smear the exact
data on the 22,386 vertices that already match. The 2017 data drifts from today's CBBE by up to 0.9
units on AppleCheeks, so taking Nahka's data wholesale is out too.

## A-5 — Working name "Anatomy" (agent, 2026-09-23)

The project folder is `fo4-anatomy` until the owner names it. Renaming is cheap. Poll it before
anything user-visible exists.

## A-6 — Weight both the animated genital bones and their `_CBP_` twins (agent, 2026-09-23)

JaneBod Extended weights only ZeX's ANIMATED genital bones, lightly (0.37 at most), and gives them
no physics. The CBP lineage SETS the transform of any bone it simulates each frame (CBPSSE
`Thing::update`), which is why ZeX keeps `_CBP_` twins. So:

- Vagina: JaneBod's weight pattern goes on the animated bones (Vagina_00, L/R_01, L/R_02) AND the
  same pattern on their twins (Vagina_CBP_00, CBP_L/R_01, CBP_L/R_02). ZeX-rigged animations move
  the first set, and OCBP physics plus OCBPC collisions move only the second. A vertex moves by
  both.
- Anus: ZeX has no twins, so it gets the animated bones only (Anus_01-04). Whether physics can sit
  on them without fighting animations is for the in-game test.
- How the bones get in: Outfit Studio 5.8.2 drops unweighted bones on save (`CleanupBones`), so each
  set arrives WITH its weights. Two `CopyBoneWeights` passes, one from JaneBod's mesh and one from a
  copy whose bone names were renamed to the twins. The rename touches only the header string table;
  blocks refer to strings by index.
- The final per-vertex balance between Pelvis_skin, the animated bone and the twin is set after
  measuring what Outfit Studio's spreading copy produced.
