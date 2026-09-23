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

## A-7 — Physics config: built from the owner's, dead lines out, ours in (agent, 2026-09-23; owner: "feel free enhance physics config")

Deployed today: `ocbp.ini` from MadKita's Actual Jiggle, and `OCBPCollisionConfig.txt` plus the
plugin (`cbp.dll`, OCBPC 0.3) from Jiggle Physics. `tools/physics_config.py` rebuilds both from the
deployed copies, so nothing the owner tuned is lost:

- **Dead lines are commented out with the reason.** 12 of the 17 attached bones are 3BBB names the
  ZeX skeleton does not have (18 lines, counting `[Attach.A]`).
- **Breasts** (owner's request) are fixed in the BODY, not the config. CBBE's breast weights moved
  from the Havok-cloth `CLOTH_Bone_Googles_00/01` to `LBreast_skin`/`RBreast_skin`, bit-identical
  (`zex_bones.py`). The existing `[Breast]` section and the hand collisions reach them now.
- **Vagina:** the five `_CBP_` twins get springs (`[Labia]`, `[Clitoris]`). They are stiff and
  damped, so walking does not wobble them, with linear 0.9 so a collision's push is not scaled away.
- **Anus:** the four `Anus_0x` bones get springs (`[Anus]`); ZeX has no anus twins.
- **Collisions:** the lower-labia twins and the four anus bones are affected; `Penis_01`-`05` are
  colliders. Every sphere of ours sits ON its bone (offset 0,0,0). Whether OCBPC 0.3 rotates an
  offset by the bone is unproven: CBPC does (`worldPos = pos + rot * offset`), yet the deployed
  breast spheres only make sense as world offsets. A zero offset means the same either way. The
  opening then comes from the bones' own placement, L_02 0.64 left of the midline and R_02 0.53
  right. `Penis_00` is left out because every skeleton has it, and a female's own `Penis_00` rests
  2 units from her vulva.

## A-8 — The in-game test ships as a Vortex mod, not as edits to deployed files (2026-09-23)

The first plan wrote the test build into the four deployed files in place (with backups and a
restore). The session's permission policy refused it as modifying shared resources, and it was
right: a mod the owner installs is visible, conflict-managed by Vortex, and undone by disabling it.
`tools/package.py` builds `D:\F4Output\AnatomyLab\package\Anatomy-test-<stamp>.7z`. It holds the
zeroed body, the two configs, and the BodySlide project with its zero preset. It must win its three
conflicts: `bodyslides_f4_sd`, MadKita's Actual Jiggle, and Jiggle Physics.
`tools/install_test.py` stays for an owner who explicitly wants the in-place route.

## A-9 — Collision-grade genital weights and physics values, measured offline (agent, 2026-09-23)

Supersedes A-6 for the lower-lip twins (`Vagina_CBP_L_02` / `_R_02`) and the anus, and A-7's spring
and sphere values. The owner's words: "feel free enhance physics config"; A-1 (full physics) is the
goal this serves.

**Why.** OCBPC is open source (github.com/ericncream/OpenCBP_FO4, branch `cbpc`, GPL-3.0), and
`tools/ocbpc_sim.py` ports its per-bone update faithfully. Measured with it and `tools/fit_check.py`
on the deployed build (86f6fc78): JaneBod's weights, made for animations that swing a bone several
units, put at most 0.17 on a lip twin and 0.07 on the anus. A collision moves a bone only as far as
the shaft needs, so the lips opened about 0.2 units: nothing to see. `linear` 0.9 made the bones flap
0.95 units at a walk. The 1.3-unit penis spheres, 3 units apart, left gaps that the lips fell into
as the shaft slid (push 0.23..0.98).

**What the source settled** (it was "unmeasured" in research.md):
- OCBPC SETS a simulated bone's local transform from its first-seen value plus the physics offset
  (Thing.cpp:640-662). An animation of the same bone is discarded, so the anus bones, which have no
  twins, move by physics alone.
- `femaleOnly` does not drop a male's colliders: an untracked actor is still entered
  (scan.cpp:204-218). Every actor's colliders act, its own included (only a bone's own spheres are
  skipped).
- Sphere offsets are in the actor's frame, heading only (CollisionHub.cpp:124, Thing.cpp:326).
- A push is divided by `linear` and multiplied back, so `linear` does not weaken it; but `maxoffset`
  caps the INTERNAL offset (actual cap = maxoffset × linear).
- While a bone overlaps, only the push runs; the spring is skipped. A pushed lip rests wherever the
  insertion left it on the shaft's surface.

**What changed:**
- **Weights** (`zex_bones.py`): the lower-lip twins and the anus bones carry a layer FITTED to
  Nahka's own openings. For each vertex her VaginaPenetrate / AnusPenetrate moves (scaled from the
  shaft she drew for to BodyTalk's 1.55), take the non-negative weights whose bone pushes best
  reproduce it. A vertex is fitted only to bones on its own side, smoothed three rounds over
  position-welded vertices (seam copies stay identical: crack 0.0000). The animated lips keep
  JaneBod's weight whole; JaneBod's light anus pattern stays underneath, so no anus bone is left
  weightless.
- **Spheres** (`physics_design.py`, the one place): lip spheres 0.6 outside their bones (x only,
  which survives the pelvis pitching), r 1.2; penis spheres r 2.0 (tip 1.8), so lip + penis = 3.2
  closes the gaps; anus back/front on-bone r 0.5, sides 1.0 outside r 0.6.
- **Springs** (`physics_config.py`): stiffness 150, stiffness2 0, damping 6, linear 0.2,
  maxoffset 15 (3 units of real room).

**Measured** (`fit_check.py`: six shaft paths, the deployed build against the new one):
- Entrance vertices left inside a 1.55 shaft: 75-85% before, 47-71% after. On the visible lip
  surface outside the entrance (the "as drawn" path): 344 before, 127 after. Nahka's own slider,
  scaled to the same shaft, leaves 232.
- Stretch: 99th percentile 3.95, worst 7.95, both below Nahka's own slider (5.17 / 13.0).
- Walking flap: 0.17 / 0.41 before, 0.07 / 0.29 after (walk / run).
- The anus is unchanged in clearance. ZeX puts its four bones 1.0-1.4 units BEHIND Nahka's ring, so
  a shaft in her ring pushes all four backwards and the ring's front has no bone to open it.
  Fitting cannot fix that; moving the ring or the bones could. This is open, and the in-game test
  says how visible it is.

**Tried and dropped:** the upper-lip twins as collision bones too. The fit reproduced 78% instead
of 51% and cleared more of the entrance, but those bones sit 0.9 ahead of the shaft, so it drives
them forward, and canal-mouth vertices were pulled out of the shaft (edges stretched 35×).

**Known limit:** a woman's own penis bones are colliders for OTHER actors, and no key filters
colliders by sex. In a female/female scene, the partner's invisible Penis_01-05 (7-20 units in
front of her pubis) can push these spheres.

## A-10 — The genitals' texture: Nahka's patch in the owner's skin, nothing else touched (agent, 2026-09-23)

The owner said "do rest stuff meanwhile I will be able eyeball". Nahka's genital triangles sample
a corner of the body atlas that CBBE does not use. The owner's skin maps (CBBE HeadRear Absolute
Fix) are flat filler there, so the lips and canals rendered as plain skin; with A-9 opening the lips
about six times wider, that inside shows more.

- **Why the same files:** the body's shader names a material (`basehumanFemaleskin.bgsm`), and the
  material decides the textures. New texture paths in the mesh would change nothing. So
  Anatomy-dev carries patched copies of the owner's six body maps (clean and dirty: `_d`, `_n`,
  `_s`) at their own paths, and must win over the skin mod (the owner's conflict rule and Deploy).
- **What changes:** only the texels the genital triangles sample, padded 8 for filtering, and never
  a texel any other triangle samples (measured: none do). Colour is matched in linear light by
  per-channel gains from the crotch-skin ring in both textures (1.42 / 1.99 / 1.49), so her mucosa
  keeps its shift relative to her skin. Specular is matched by OFFSET: the owner's skin has almost
  none (red about 0.3 of 255 against her 48), and a gain would make the mucosa matte. Normals are
  copied. Where the island meets the crotch skin (a UV seam, 116 points), colour and specular are
  pulled onto the skin side and faded inward over 32 texels: the seam step is 2.3 / 1.1 / 1.9 of
  255 (it was 9.0 / 4.0 / 8.1 unfeathered, and 1.2 / 0 / 1.2 before any patch). Normals fade to
  flat at the edge, because the two sides use different tangent frames.
- **Proof:** DXT1/BC5 are re-encoded only in the blocks the padded patch reaches, on every mip
  level. `tools/genital_texture.py` verifies that every other block of every level is the owner's,
  byte for byte, and a decode shows no black specks (DXT1's transparent mode).
- **If the owner changes skin mods:** rerun `genital_texture.py` then `restage.py`. The patch is
  derived from whatever skin is deployed.

## A-11 — No physics on the anus; lips capped at 2.5 (the owner's own look, 2026-09-23)

(Superseded by A-14: the spike was a missing bone, not physics. Kept as the record of the reasoning.)

Supersedes A-9 for the anus. The owner looked in game and took screenshots (Photo116-124).
- **What they showed:** in "[UAP] BP70" doggy, a thin dark spike of the anal pocket, about 5
  units long, reached from the buttock cleft toward the partner's torso ("stretched and stuck in
  man's chest ... looks like black hole"). The cowgirl frames showed the shaft entering the vulva
  with no spike. The spike is about 5 units long, which is OCBPC's cap for a bone (maxoffset 15 ×
  linear 0.2 = 3 per axis), times the anus layer's weights of up to 0.88. The simulator had
  predicted exactly this pinning: the anus bones hold at 4.24, the cap, when a shaft passes beside
  them.
- **Why the anus cannot have collision physics on this rig:** ZeX's four anus bones sit 1.0-1.4
  units BEHIND Nahka's ring. A shaft beside them pins them at the cap, and a shaft in her ring
  pushes all four backwards. Either way the pocket is dragged, never opened.
- **Now:** no anus bone is attached or affected in the configs, so OCBPC no longer SETS them and
  animations drive them again. Their weights are JaneBod's light pattern (at most 0.07), as in
  JaneBod Extended. The lips' cap drops to 2.5 real units (maxoffset 12.5): above the ~1.9 a shaft
  needs, below what pinned. `fit_check`: the vagina is unchanged on all six paths, the anus neither
  opens nor spikes, and walking flap is 0.05 / 0.21.
- **Open:** an anal opening needs either Nahka's ring moved back onto ZeX's anus bones (geometry)
  or a morph-driven opening (A-1 allows morphs as a layer). Decide from the owner's anal look.

## A-12 — The animated genital bones carry no weight (the owner's own look, 2026-09-23)

(Superseded by A-14: no animation could key those bones on a woman; they were missing from her
skeleton. Kept as the record of the reasoning.)

Supersedes A-6 and A-9 for the animated bones (Vagina_00, Vagina_L/R_01-02, Anus_01-04). The
_CBP_ twins keep their weights.
- **What was seen:** after A-11 removed the anus physics, the owner's frames (Photo125-130, new
  build) still showed a thin rod of the genital mesh. It was about 10 units long in doggy, and about
  20 in a standing, bent-over pose.
- **What cannot make it, measured:**
  - Physics: OCBPC caps a bone at 2.5 per axis, and the heaviest physics weight is 0.56, so at
    most ~2.4 units.
  - Limbs: `tools/pose_check.py` skins the body in bent poses. A 90° thigh stretches the crotch
    by ~3 units, and it does the same on the owner's untouched CBBE (x12.3 against ours x12.4).
    Nahka's heavier thigh weights at the perineum (0.34-0.54, against CBBE's 0.08) are real but
    not the rod.
  - Bad weights: none. BodySlide's output equals the project on every vertex, and no genital
    vertex is weighted to a far bone.
- **What can:** an animation keying the animated genital bones somewhere this skeleton does not
  rest them, for example a pack rigged on another ZeX version. That displacement has no bound,
  and the vertices follow it by their weight (up to 0.34 on the lips since A-9).
- **Now:** those bones keep their place in the skin but carry nothing, so no animation can move
  the genitals. Physics on the twins is the mechanism, as A-1 intends. Build df85d105:
  verify_zex PASS, compare_builds PASS.
- **If the rod survives this build,** the next suspect is OCBPC on the twins (turn their
  physics off to prove it).

## A-13 — The outer lips jiggle and react (owner poll, 2026-09-23)

The owner asked to "handle the lips" and chose all three answers: jiggle and react, change their
look, vary per woman. This entry is the first; the look and the variety come through BodySlide
(the owner picks) and Silhouette's BodyGen ranges (`Morph@low:high`).
- **Weights:** a soft layer on the upper-lip twins (Vagina_CBP_L_01 / R_01), left side to L and
  right to R, 0.45 on the crests. It fades to nothing at the inner lips' edge (|x| 0.4-1.0), at the
  groin crease (|x| 1.8-2.8), at the perineum and mons, and up into the body. The inner zone stays
  the lower-lip twins' alone. The twins are the lower lips' parents, so the whole lip complex
  wobbles together.
- **Springs (`LabiaOuter`):** stiffness 60, damping 3, linear 0.5, cap 1.2 real units. Measured with
  ocbpc_sim: the bone moves 0.57 at a walk, 0.42 per thrust, and hits the cap running. That is
  0.26 / 0.19 / 0.54 units at the crest.
- **Collision:** a 0.8 sphere on each crest (x ±1.4 from the midline bones), so hands and the shaft
  squish the outer lips outward.
- **Measured (fit_check):** the entrance clears better (as drawn 64% → 55%, the same as Nahka's own
  slider; steeper 55% → 46%). Contact stretch is unchanged, and there are no seam cracks. With both
  bones pinned at the cap in any direction, the 99th percentile of edge growth is 1.3-2.0 and the
  worst edge is 4.7 (apart), below Nahka's slider (13). Only an unlikely diagonal extreme reaches 7.

## A-14 — Our own genital bones, in the skeleton women actually load (2026-09-23)

Supersedes the causes given in A-11 and A-12, and the bones of A-6, A-9 and A-13 (their designs
carry over to the new bones). The owner approved the direction: "disallow any animation touch
vagina and anus and manage it by ourself with physics only".
- **The cause of the fin, the rod and the anus spike (measured):** DiscreteFemaleSkeleton.esp is
  active, so women load `CharacterAssets/female/skeleton.nif` and `female/skeleton.hkx`, not ZeX's
  shared pair. The .nif is deployed from Skeletal Adjustments for CBBE: 3BBB-style, 208 nodes, and
  not one genital bone. The .hkx comes from More Flexible Ragdoll and has none either. Every one of
  the 14 ZeX genital bones the body was weighted to was missing on a woman. Such vertices stay where
  the body file binds them, relative to her root, while her pelvis moves. That is the classic
  missing-bone stretch: invisible standing, a fin or rod in any pose that moves the pelvis, reaching
  toward where the crotch would be standing. The diagnostic body with no genital weight (build
  0f68d592, Photo141-144) had none of it.
- **Reproduced offline, then gone:** `tools/pose_check.py` now poses the women's skeleton, and
  gives a missing bone's share of a vertex its bind place, as the game does. It also moves the
  whole body against the root, as every scene does. Crotch edges stretched more than 3×:

  | Pose                     | old fin build 118d00cb | this build |
  | ------------------------ | ---------------------- | ---------- |
  | kneeling (COM down 15)   | 2,613 (worst ×38.8)    | 0 (×1.5)   |
  | lying back (COM 90°, 30) | 3,824 (worst ×77.4)    | 0 (×1.6)   |

  Limb bends are unchanged, and the same as plain CBBE's (a 90° thigh: ×9.8).
- **What else follows:**
  - OCBPC never had a genital bone to move on a woman. Every in-game "physics" observation before
    this build was of no physics at all.
  - A-11 blamed OCBPC's cap; A-12 blamed animations keying the animated bones. Neither could
    happen: ZeX's .hkx never had the _CBP_ twins, and hers has no genital bone at all.
  - `pose_check` passed because it posed ZeX's skeleton, which has the bones.
  - `physics_config` had commented out 18 of MadKita's attach lines (LBreast_01-03_skin,
    LButt_01_skin, LLeg_Thigh_01_F/R_skin) as "not in the ZeX skeleton". The women's skeleton has
    all of them, so that took their 3BBB physics away. Every source line is kept now.
- **The lesson:** any claim made "against the skeleton" must use the skeleton that ACTOR loads.
  Read plugins.txt for DiscreteFemaleSkeleton.esp before trusting a path.
- **The bones (`physics_design.REST`, skin space):**
  - AnatVulva (0, 4.0, -55.5): the vulva's small sway (JaneBod's Vagina_00 pattern × 0.5).
  - AnatLipOuter_L/R (∓1.4, 2.45, -55.71): the outer lips. They carry JaneBod's L/R_01 × 0.5 plus
    A-13's soft layer. Springs are A-13's, with a 0.8 sphere.
  - AnatLip_L/R (∓1.2, 1.08, -55.71): the inner lips. Their A-9 layer is fitted to VaginaPenetrate,
    with a 1.2 sphere.
  - AnatAnus_F/B/L/R: around Nahka's ring, in its plane. F is 0.7 toward the vulva with a 0.3
    sphere, so the vaginal shaft clears it by 0.47. B, L and R sit 1.0 out with 0.6 spheres. They
    carry a layer fitted to AnusPenetrate, on a new `Anus` spring section like `Labia`.
  - Each bone is its sphere's centre, so no offset can drift as the pelvis pitches.
  - JaneBod's pattern is averaged with its mirror image, because her painting is lopsided: 1,501
    against 1,020 vertices on the outer lips before, 1,540 against 1,501 after.
- **Where they live:** `tools/skeleton.py` copies the women's .nif from its owning mod's staging
  folder and appends the 9 NiNodes as children of Pelvis_skin, with identity rotation. Pelvis_skin
  sits exactly on the pelvis and no .hkx names it, so the bones follow the pelvis rigidly and only
  OCBPC moves them. Proven:
  - only Pelvis_skin's block changed, and no original node moved;
  - the bones are within 1.5e-6 of the design;
  - no .hkx in the game names them (the ragdoll pair and ZeX's).
  - `zex_bones` refuses a skeleton whose Pelvis_skin differs from the one the body is bound to
    (0.0).
  - `verify_zex` refuses a weighted bone the women's skeleton lacks.
  - `restage` step 7 says NOT READY until Data's women's skeleton carries every weighted bone.
- **Measured (`fit_check`, `ocbpc_sim`), against Nahka's own sliders scaled to the partner:**
  - vagina, as drawn: 56% of the entrance still inside the shaft, the same as her slider × 1.41.
    Edge stretch p99 3.9 / max 7.1, against her slider's 5.2 / 13.0.
  - anus, as drawn: 71% against her slider's 68% × 1.15. Stretch 5.2 / 7.9, against 7.7 / 14.8.
    The fit reproduces 94% of AnusPenetrate; ZeX's bones behind the ring reproduced almost none.
  - Cross-contact: a vaginal shaft never reaches the anus bones (0.08 when 1.2 off). An anal shaft
    reaches the inner lips only when 0.6 ahead (0.32). If anal animations aim 1.2 behind her ring
    (ZeX's anus), the ring's back is driven toward the shaft (3.1).
  - Walking: 0.30 / running 0.63 at the outer lips. No seam cracks.
- **Deployment:** the skeleton is a NEW file in Anatomy-dev, so it needs the owner's Deploy and a
  conflict rule: Anatomy-dev wins `female/skeleton.nif` over Skeletal Adjustments for CBBE. Build
  e157909873fb.
- **Dependencies this creates:**
  - The body now needs our skeleton. If DFS is ever switched off, women fall back to ZeX's shared
    .nif, which lacks our bones: `tools/skeleton.py --deployed` reads plugins.txt and says so.
  - A release needs either permission to ship a derivative of Skeletal Adjustments' skeleton, or a
    small F4SE plugin that adds the 9 nodes at load (A-2).
- **Open, for the owner's look:**
  - BP70's AAF morph sets also apply VaginaPenetrate 1.0 during penetration, on top of physics
    fitted to that same morph. The opening may come out doubled.
  - The anal aim: does the shaft enter Nahka's ring?
