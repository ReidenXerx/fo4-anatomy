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

**Why.** OCBPC is open source (github.com/ericncream/OpenCBP_FO4, branch `cbpc`), and
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
- **Which scenes also drive the opening morph (measured in Data/AAF):**
  - Only ZaZOut4's 11 pillory animations (`PillorySex_A-Pussy-*`) set VaginaPenetrate, to 1.0.
  - The morph sets (rxl_bp70, Rufgt, AAF, Atomic Lust, BodyTalk's Theme_SexAnimations) are
    `isFemale="false"` erection sets. The only female condition is BodyTalk's nipples at 0.25.
  - UAP's "Anus Spread" (103 entries) is a name our body does not have.
  - An earlier note that BP70 opened the vagina by morph was wrong.
- **What the morph adds, simulated:** in those pillory scenes the morph and physics add up. The
  entrance's median radius is 1.82 (p90 2.19) against a 1.55 shaft, where physics alone gives 1.33
  and the target is 1.36. So pillory scenes may open wider than the shaft.
- **Kept anyway:** the slider's name, because Silhouette lists VaginaPenetrate and AnusPenetrate
  as runtime states (`silhouette_gen.py` STATE_MORPHS, `Player.psc`), and renaming it would
  reach into the fork's code.
- **Open, for the owner's look:** the anal aim. Does the shaft enter Nahka's ring?

## A-15 — It works; the entrance opens to the shaft (the owner's first look at A-14, 2026-09-23)

- **The owner:** "man it works! ... its hard to see on screenshot but it works! only 1 thing we need
  to widen vagina slightly more". Photo145 (standing bent over, the pose that used to show the
  longest rod) is intact from below.
- **Change:** the vagina's fitted layer aims at Nahka's drawing × 1.41 × gain 1.35
  (`physics_design.OPENINGS['vagina']['gain']`). The push is unchanged (2.21); the inner-lip weights
  rise from 0.55 to at most 0.74.
- **Simulated (the entrance ring, 738 vertices):**

  | gain  | median radius | inside the shaft | stretch p99 / max |
  | ----- | ------------- | ---------------- | ----------------- |
  | 1.00  | 1.33          | 56%              | 3.9 / 7.1         |
  | 1.25  | 1.49          | 35%              | 4.7 / 8.7         |
  | 1.35  | 1.55          | 30%              | 5.0 / 9.3         |
  | 1.50  | 1.65          | 25%              | 5.5 / 10.2        |

  At 1.35 the entrance matches the partner's shaft (1.55) and stretches less than Nahka's own
  slider (5.2 / 13.0). At 1.5 the p99 passes hers.
- **Build:** bbbc36acde38, restaged in place (no Deploy). The rebuilt body measures 1.55 / 30% /
  5.0 / 9.3, as predicted. verify_zex PASS.

## A-16 — Arousal, and her nipples follow it (the owner's poll, 2026-09-23)

The owner, relayed by the Silhouette session: "nipple feature when char is aroused (i am not sure
does we have such metric)".
- **The poll:**
  - Triggers: "Scenes + nudity + watching" AND "Companions' own arousal" (the owner: "lets make
    2 + 3").
  - Strength: "Clearly visible".
- **No arousal metric exists** in the owner's game (measured):
  - AAF's stat layer is empty. UAP defines an `Arousal` actor stat, but it is not persistent and
    decays almost at once, and nothing reads it.
  - Ivy keeps her own flag (`_ivy_IsAroused`, CompanionIvy.esm 0011AA).
  - Overture's companion Desire is an actor value (`OvertureCompanionDesire`, Overture.esp 0x851,
    0..1; a scaffold on their side). Overture belongs to another session; we only read it.
- **The model (`papyrus/Anatomy/Arousal.psc`):**
  - Every 3 s, each human woman within ~43 m of the player (and the player) moves toward the
    strongest source. Each source has a drive and a half-life:

    | source                         | drive          | half-life |
    | ------------------------------ | -------------- | --------- |
    | in an AAF scene (busy keyword) | 1.0            | 10 s      |
    | Ivy's own flag                 | 0.8            | 20 s      |
    | watching a scene within ~17 m  | 0.55           | 30 s      |
    | Overture Desire                | 0.7 × Desire   | 45 s      |
    | naked (body slot empty)        | 0.3            | 45 s      |

  - Arousal falls with a 60 s half-life, so she stays aroused a while after a scene.
  - Time is real time, and a step is capped at 10 s, because menus stop the timer but not the
    clock.
- **The nipples:** NippleLength +0.55, NipplePerk2 +0.5, NippleTip +0.4, NippleSize +0.25 at full
  arousal, in tenths.
  - Measured on the body: NippleLength is the erection itself, up to 1.1 units out at 1.0.
  - The rise goes under Anatomy.esp's keyword, on top of her strongest other layer. LooksMenu shows
    the MAX over its layers, so the rise adds to her own shape (Silhouette's variety, AAF's scene
    values) instead of replacing it.
  - Silhouette's NipBGone under heavy clothes still wins.
  - At zero the layer is removed and she is forgotten.
- **What is not done:**
  - No AAF call is made (one can end the calling stack); only `AAF_API.AAF_ActorBusy` is read.
  - Every source is optional: a missing plugin only removes that source.
- **Built:**
  - `Anatomy.esp` is light, made by `tools/make_esp.py`: quest 0x800 running the script, and
    keyword 0x801, a vanilla v131 KYWD's fields. It has the same shape as Silhouette.esp and
    Chemistry.esp, which run in the owner's game.
  - `scripts/build-papyrus.ps1` imports F4SE's own sources (for `GetWornItem`), then the base, AAF
    and a BodyGen stub.
  - Compiled first time. The plugin tiles exactly, and fo4-rapport's reader parses its VMAD.
- **Deploy:** both files are new in Anatomy-dev, so they need the owner's Deploy and the plugin
  enabled.
- **To uninstall:** do it when no woman is aroused. Otherwise her layer stays in LooksMenu's
  co-save under a keyword that no longer resolves.
- **Open:** gains and half-lives, tuned by the owner's look.
- **The owner's look (20:00):** "man thats fucking gorgeous ... lets make nipples a slightly bigger
  in erect state". Length went from +0.55 to +0.70 and size from +0.25 to +0.40 (d2c4321).

## A-17 — Fisting and toys, through our own OCBPC (the owner's poll, 2026-09-23)

- **The poll:**
  - Order: fisting, then toys and the bat, then the mouth.
  - Toys: upgrade the physics plugin, not per-toy meshes.
- **The plugin:** fo4-ocbpc, a sibling repo. Its base, abc0192, is MIT. Upstream's `cbpc` branch
  moved to GPL-3.0 only on 2021-07-21 (c69c98a), after our base. The source must be public all
  the same: F4SE's readme requires it of every plugin.
  - It branches at abc0192, the commit behind the deployed OCBPC 0.3 `cbp.dll` (2020-04-16), found
    by its config keys: it knows `detectArmor`, `Override:` and `Attach.`, and none of 2021-2022's.
    Everything else keeps behaving as the owner's does.
  - Built with VS2022, after two build-only fixes. The rebuilt DLL imports only KERNEL32 and
    exports the same two entry points.
- **Stretch groups (fork 2fc9a05):**
  - A section may carry `stretchGroup/Knee/Gain/Max/AxisX/Y/Z`. After an actor's bones run, each
    group takes the SMALLEST push across its opening's axis. A big object pushes every bone; a small
    one off-centre pushes one side; a hand pressing from outside pushes along the axis.
  - Past the knee, each bone's child `<bone>_Stretch` moves out by gain × (smallest − knee), capped
    at max.
  - The body's lip and anus weights sit on those children, which sit on their bones. A penis below
    the knee moves the body exactly as before (fit_check identical: 30% / 71%).
  - Labia knee 2.4, gain 3; anus knee 1.8, gain 2; max 1.5 to start.
  - Simulated (smallest push across):

    |                               | vagina  | anus    |
    | ------------------------------ | ------- | ------- |
    | every penis path               | ≤ 2.21  | ≤ 1.13  |
    | two fingers                    | 2.11    | 1.34    |
    | a fist filling the entrance    | 4.45    | 4.0     |
    | a wrist filling the entrance   | 3.89    | 3.18    |

    At max 2.5 a fist opens the entrance to a median 3.0 but stretches its worst edges ×27, which
    is why max starts at 1.5.
- **The fist:** one 3.0 ball on the middle knuckle (Finger31). A hand is 5.42 across the knuckles.
  Four small knuckle spheres made a row wider than the opening, and the outer ones pushed the lips
  back in.
- **Props (fork 2fc9a05):**
  - `ocbp.ini [Props]` lists the hands' AnimObject nodes. Whatever hangs there becomes a line of
    1.6 spheres from the node, through its rendered bound's centre, to the far side. This covers DR
    pack's dildos and bat (`DR_sex_Dildo03_BaseballBatt`).
  - Colliders are rebuilt every frame, so a prop that appears mid-scene collides at once.
  - WEAPON nodes are left out: a held rifle would squash her breasts.
- **A trap caught:** the weight fit took the LARGEST collider as the shaft, so the fist ball would
  have shrunk every fitted weight. It now uses the Penis spheres only.
- **Deploy:** `cbp.dll` is new in Anatomy-dev and must win over Jiggle Physics (which deploys OCBPC
  0.3 now) and OCBPC-0.3-CBBE. Until it does, 0.3 ignores the new keys, the stretch children stay
  put, and nothing changes from A-16. Build a13c4011c17b.
- **Open:** tune the stretch and the prop radius by the owner's look. A fisting animation may pulse,
  because the knuckle ball and the wrist are 7 units apart.

## A-18 — The arousal MCM (the owner's poll, 2026-09-23)

- **The poll:** "What should the MCM menu hold?" was answered "Arousal only". The genitals and the
  physics have no player-facing knob in v1.
- **The page (`tools/build_mcm.py` -> `MCM/Config/Anatomy/`):**

  | setting | id | default | range |
  | --- | --- | --- | --- |
  | Arousal nipples (on/off) | `bEnabled:General` | on | switch |
  | Nipple response (× the A-16 gains) | `fNippleStrength:General` | 1.0 | 0 .. 2 |
  | Rise speed (divides every source's half-life) | `fRiseSpeed:General` | 1.0 | 0.25 .. 4 |
  | Fade speed (divides the 60 s fall) | `fFadeSpeed:General` | 1.0 | 0.25 .. 4 |
  | Being in a scene | `bScenes:Sources` | on | switch |
  | Watching a scene | `bWatching:Sources` | on | switch |
  | Companions' own arousal (Ivy, Overture) | `bCompanions:Sources` | on | switch |
  | Being naked | `bNaked:Sources` | on | switch |

- **One source of truth:** the defaults are read out of `Arousal.psc`'s `Defaults()`, never typed
  in the generator. The generator refuses when:
  - a default has no menu entry;
  - a menu entry has no default;
  - a default is outside its slider;
  - the ids the menu writes differ from the ids `LoadSettings` reads.
  All four refusals were made to fire once.
  This is fo4-chemistry's `build-mcm.py` rule, and its config shape, which runs in the owner's game.
- **Reading:** `LoadSettings()` runs every tick (3 s). MCM answers 0 / false for a mod with no
  settings at all, and `bEnabled = false` would then read as "switched off". The rise speed can
  never be 0 (its slider starts at 0.25), so a 0 there means "MCM has nothing for us" and the
  defaults stand. This is Chemistry's tell, too. `MCM.IsInstalled()` is asked once per load, not
  per tick: without MCM.pex the call fails and logs.
- **Behaviour:**
  - Off removes every layer of ours at the next tick and stops tracking.
  - A new strength rewrites every shown layer. Their `_shown` is set to -1, which means "a layer
    may be on her, value unknown". `Forget` removes a layer whenever `_shown != 0`, so a woman who
    leaves before the rewrite is still cleaned.
  - Strength 0 removes the layer rather than writing her own values back under our keyword.
  - Someone in a scene is not "watching" it. With scenes switched off, the partner next to her must
    not count as a scene she watches. With every switch on, `Next()` gives exactly the A-16
    numbers: the scene's 1.0 was already the top.
- **Save compatibility:** the new variables start at their declared values in an old save, and
  `LoadSettings` overwrites them at the first tick.

## A-19 — Our own weights everywhere: JaneBod's painting is gone (release plan item 1, 2026-09-23)

- **Why:** JaneBod Extended (Nexus 32442) needs permission for asset use, and the body's vulva and
  outer-lip base still came from its painting (half of it, copied by proximity since A-6). After
  this, no build step reads JaneBod. `references.py` and `inspect_jbe.py` stay as research tools.
- **What that painting contributed, measured on our mesh before removing it:**
  - AnatVulva: a near-flat 0.07-0.09 on 558 vertices around the bone (x ±1.9, y 3.4..6.0). That
    bone is stiff and nothing collides with it, so it moved the skin about 0.05 units.
  - AnatLipOuter_L/R: at most 0.10, median 0.02. On 1,188 vertices that is all the weight they
    have; those vertices are mostly near the midline, where A-13's layer is 0. The layer itself
    reaches 0.45.
- **The replacement (`zex_bones.vulva_weights`):**
  - The vulva gets a pad: 0.09 within 1.8 of the bone, fading to nothing at 3.0.
  - It is limited to what lies ahead of the lips. It fades in between the outer-lip bones' depth
    and its own (y 3.2 → 4.0), so the openings stay their fitted layers' alone.
  - It is symmetric by construction; JaneBod's needed mirror-averaging.
  - The outer lips keep only their own A-13 layer.
- **The entrance, simulated (`fit_check`, deployed build = with JaneBod):**
  - Without that painting, the entrance's front clipped a little more at gain 1.35: 30% → 32% as
    drawn, 27% → 31% steeper. Its small midline outer-lip weights had been pushing the front
    forward: the outer-lip bones are pushed outward and forward (0.85, 0.46), so on a midline
    vertex the two sides cancel in x and add in y.
  - **Rejected: fitting the entrance with the outer-lip bones too.** The fit itself improved (51% →
    73% of Nahka's displacement reproduced), yet the simulation clipped MORE (30% → 38%) and the
    walking flap doubled (run 0.63 → 1.00). Those bones are soft (stiffness 60) and can move 1.2
    units at most (maxoffset 2.4 × linear 0.5), so the fit's expected push is more than they can
    deliver. **Lesson:** a better fit to `expected_push` is not a better result. Only the
    simulation (`fit_check`) decides.
  - **Taken: vagina gain 1.35 → 1.40.** The six paths total 3,233 vertices still inside, against
    3,207 deployed (+0.8%). Stretch p99 as drawn is 5.17, Nahka's own slider and A-15's limit.
    Walking flap is lower than deployed: 0.26 / 0.55 against 0.30 / 0.63. The anus is identical on
    every path.
- **Poses (`pose_check` on the BodySlide output):**
  - Thighs are identical to deployed; those come from CBBE's own weights.
  - Spine bent ±60: 13 and 9 edges grown past 3× before, 0 now.
  - Kneeling and lying back: x1.5-1.6 → x1.7-1.9, both +0.04 units.
  - The 0.36 rest drift appears on the deployed body too, so it is not from this change.
- **verify_zex and compare_builds:** PASS.
- **Open:** the owner's look.

## A-20 — The mouth opens to what is in it (release plan item 3, 2026-09-23)

- **The owner's ask:** "physic based opening with universal override of animation's for restrict them
  touch it and touch it only by ourself via physics". The poll put it third, after fisting and toys.
- **What made it possible (field notes §10):**
  - FO4 heads have no mouth bones. The mouth is expression morph 2 (Jaw Open) and its neighbours.
  - Screen Archer Menu's source gave the face data's place: MiddleProcess data + 0x3C8, with the
    final weights at +0x18 and the overrides at +0xF0.
  - The merge itself was read out of the executable (0x6689D0). It takes max(override, animation),
    so an override alone can only open the mouth. The owner's "restrict the animations" therefore
    needs a write AFTER the merge. Its one caller rebuilds the mesh when it returns true.
- **Built in the fo4-ocbpc fork (1df5ed8), `Mouth.cpp`:**
  - Each frame, after the colliders move, every penis chain (Penis_01..05, and super mutants'
    Penis1..4), base to tip, is measured against every mouth.
  - Where a chain crosses the plane of her lips inside the mouth (2.9 to either side, 3 below, 1.5
    above), the lower lip must drop below the shaft's bottom: Jaw Open = need / gap + 0.08.
  - The upper lip lifts (Upper Lip Up, up to its 0.53 move) when the shaft rides above the lip line,
    and both lip funnels go to 0.3.
  - A tip within 3 units in front starts opening the mouth, up to Jaw Open 0.3.
  - The hook on the merge blends these over the final weights (rates 20/s opening, 6/s closing).
    While a shaft is in her mouth, the animation's, AAF's and Rapport's mouths give way. It holds
    for 0.35 s between strokes, then blends back to them.
  - No AAF block is needed.
- **Measured, not guessed (`tools/mouth.py`, which refuses if the design drifts off the game's own
  heads):**
  - Female lips meet at (-1.80, 8.12, 0) in HEAD bone space, and Jaw Open 1.0 parts them 2.97.
  - Male: (-1.84, 7.78, 0), 2.30.
  - The solver's mirror was run on six scenes:

    | scene | Jaw Open |
    | --- | --- |
    | shaft centred on the lip line | 0.60 |
    | a unit lower | 0.94 |
    | its top on the lip line | 1.00 |
    | a tip 2 units out | 0.33 lead-in |
    | beside the mouth | nothing |
    | at her chest | nothing |

- **Safety:**
  - The hook is installed only if the merge's 17-byte prologue and its one call match what was read.
    Otherwise the discovery log says so and nothing is patched.
  - Since fork 870adc4 (2026-09-23) the hook sits on the merge's one call site, through F4SE's branch
    trampoline. The merge's own code is never modified. The first version detoured the merge's entry
    with DetourXS, which copied 14 of the prologue's 17 bytes: every save load crashed, with no crash
    log (field notes, the face engine).
  - The face data is used only when its vtable is the engine's.
  - The pointers published for the hook are rebuilt every frame, so an actor who leaves is never
    steered.
- **A convention settled on the way:** in memory, a bone's rotation is the transpose of the math.
  OCBPC's `Thing.cpp` and SAF agree, and both are proven in game. F4SE's `NiTransform * point` does
  not.
- **Choices made without a poll (reversible in `ocbp.ini`):**
  - Props at the mouth are off, because vanilla eating and drinking idles use the same hand nodes.
  - Fingers are not a mouth chain.
- **Deploy:** `cbp.dll` and `ocbp.ini` were rewritten in place at 21:42, so no Deploy is needed.
- **Open:** the owner's look at an oral scene. The discovery log (`anatomy_ocbpc.log`) prints
  `[mouth] on`, each mouth's place, and each first contact with its Jaw Open.

### A-18, corrected the same evening: a sentinel instead of the rise speed
- The rise-speed tell had a hole, found by the Overture session:
  - Suppose MCM never loaded our `settings.ini` (for example, the file is not deployed yet).
  - A player's one moved slider is still answered, from `Data/MCM/Settings/Anatomy.ini`.
  - Every other key is then missing, so `bEnabled` reads false and arousal switches itself off.
- **Measured in MCM's own source** (reg2k/f4mcm `SettingStore.cpp`):
  - It loads EVERY key of `MCM/Config/<Mod>/settings.ini` through `GetPrivateProfileSection`,
    whether or not a control uses it.
  - A key it never loaded reads -1 (int), -1.0 (float) or false (bool).
- So `settings.ini` now ends with `[Meta] iDefaults=1`, on no control. `LoadSettings` reads the menu
  only when `GetModSettingInt("Anatomy", "iDefaults:Meta") == 1`; otherwise the defaults stand.
- `build_mcm.py` refuses a script that never tests the sentinel.

## A-21 — Zero-touch install: nothing of another mod is overwritten (owner polls, 2026-09-23)

- **The polls:**
  - Nahka's files: "Ship them, with credit". Her page says "up for adoption ... no need to ask me
    for permission"; credit Nahka, BringTheNoise and Alan (UN7B).
  - Output: the owner wrote "manual steps is very badly treated by noobs".
  - Then: "Yes, zero-touch design".
- **What that means:** every file of ours has a path no other mod ships, so the player never
  resolves a conflict. The one exception is `cbp.dll`, which must replace the physics mod's copy.
- **Bones at run time (fork 0e60cc0, `Bones.cpp`):**
  - Before, a patched skeleton had to win over Skeletal Adjustments, or over whatever skeleton the
    player has.
  - Now the fork finds the body's skin instance, takes the skeleton's own Pelvis_skin from it, and
    creates our 15 nodes under it from `Anatomy/ocbp.ini [Bones]`. It then points the skin's entries
    at them.
  - This works with any skeleton. A skeleton that already has them (the owner's current one) is left
    alone.
  - The bone table matches the patched skeleton to 1.2e-7 (`physics_config.py` checks it).
- **Physics lines at run time (fork 0e60cc0, `config.cpp`):**
  - `[Attach]` and the bone sections are read from the player's ocbp.ini and then from ours,
    `Data/F4SE/Plugins/Anatomy/ocbp.ini`.
  - The collision file is read the same way and appended: a node both files list keeps one entry
    and gains our spheres.
  - `[Props]`, `[Mouth]` and `[Bones]` come from ours.
- **Still to do for zero-touch:** the genitals get their own mesh part and texture, colour-matched
  once by the builder, so the skin mod is never overwritten. Raiders' dirty skin will not reach
  them (accepted in the poll).
- **The dev mod follows:**
  - Anatomy-dev drops the patched skeleton and the merged configs (`package.RETIRED`; `restage.py`
    deletes them from our own folder).
  - The owner's Deploy gives those paths back to Skeletal Adjustments, MadKita and Jiggle Physics,
    and adds `F4SE/Plugins/Anatomy/*`.
  - Until that Deploy, the new DLL runs on the old merged files exactly as before, with no sphere
    loaded twice.

## A-22 — The genitals are their own shape, with their own material (zero-touch, 2026-09-23)

- **Found on the way (it corrects A-10):** the genital texture patch was never shown in the owner's
  game.
  - A-10 wrote the patched skin to `Textures/Actors/Character/BaseHumanFemale/`.
  - But the body's material, `basehumanFemaleskin.bgsm`, wins from CBBE Holy Fix's archive, and it
    names `Actors/Character/custombody/FemaleBody_*.dds`.
  - Those files come from CBBE HeadRear Absolute Fix, at 4096 px; our patch was a 2048 px file.
  - Measured with `gamedata.py` and `bgsm.py`. The material decides the paths (field notes §12), and
    the patch was written to the wrong one.
- **Built (`split_genitals.py`):**
  - The 4,913 triangles `genital_texture.py` paints move into a new shape, `AnatomyGenitals`: the
    UV centroid lies in the island corner and at least one vertex is Nahka's. A plain UV box would
    also take about 2,000 of CBBE's own triangles.
  - Their 2,495 vertex records are copied byte for byte, with atlas UVs kept, so overlays behave as
    before.
  - The new shape has its own skin instance (the same 74 bones in the same slots) and a copy of the
    body's bone data.
  - Its shader is the body's, renamed to `Materials/Anatomy/AnatomyGenitals.bgsm`.
  - The body keeps every vertex, loses those triangles, and has its segments recounted.
  - 78,884 slider diffs of 47 sliders are re-indexed onto the new shape.
- **Proven:**
  - The BodySlide build of the new set "Anatomy Body" equals the single-shape build: all 48,215
    triangles match as positions.
  - `compare_builds` passes.
- **The material and textures (`genital_texture.py`, `bgsm.py`):**
  - The player's skin is read from whatever the winning skin material names, loose or in an archive.
  - Nahka's island is patched in. On the owner's skin the gains are 0.51/0.42/0.36, and the seam
    after feathering is 2.1 against the skin's own 4.5.
  - The output goes to `Textures/Anatomy/FemaleBody_d/n/s.dds`.
  - `AnatomyGenitals.bgsm` is that skin material with only the three texture paths changed.
- **Retired from Anatomy-dev:** the six BaseHumanFemale textures and the old "Anatomy Body ZeX"
  BodySlide set.
- **Deploy:** the new body (build b72181014994) is already in Data through its hardlink, but its
  material and textures are NEW files. The owner must Deploy before playing, or the genitals
  render with missing textures.

## A-23 — Nahka's work ships as a patch against the player's CBBE, not as her files (2026-09-23)

- **Why:**
  - The owner's poll said to ship Nahka's files with credit. Her page permits any use of HER work.
  - But her CBBEVaginaMorphsPhysics files are a whole 2017 CBBE body with her genitals in it.
  - CBBE's rule 3 asks permission for "uploading a modified body mesh outside of sliders".
  - So only what she added ships, expressed against the player's own CBBE. This is the settled
    principle of the release plan (nothing third-party redistributed), applied to her files.
- **`make_patch.py`** (run once, here) writes `build/patch/nahka_patch.json.gz`, 2.5 MB:
  - her 2,811 new vertex records, with bone slots as names;
  - her 5,579 new triangles, whose references are CBBE indices or new ones;
  - the 514 CBBE triangles and 220 CBBE vertices her geometry replaces;
  - per new vertex, the CBBE neighbours `align_body` blends from, with their weights;
  - per CBBE slider, her own deviation from that blend. That is `align_body`'s correction with no
    CBBE data in it;
  - her 12 genital sliders;
  - a fingerprint of the CBBE it was made against.
- **`apply_patch.py`** (what the builder runs; now also stage 1 here) rebuilds stage 1 from the
  player's CBBE plus the patch:
  - CBBE's vertices in CBBE order, minus the replaced ones, then hers;
  - hers take CBBE's bone slots by name. 51 that leaned on her 2017 cloth bones are re-weighted
    from their neighbours;
  - CBBE's own slider data;
  - segments recounted;
  - a CBBE other than the fingerprinted one is refused.
- **Proven against `align_body`** (by geometry, since the vertex order differs):
  - all 48,215 triangles are identical as positions;
  - all 25,292 distinct vertices (position + UV) match;
  - weights are identical by bone name;
  - records are identical outside the slot bytes;
  - the 96 slider sets agree to 7e-8.
  - Downstream:
    - `verify_zex` passes;
    - `fit_check` is identical to the deployed build on every path;
    - the BodySlide build equals b72181014994 per shape as positions.
  - The skin's bone table drops from 74 to 69: her 2017 cloth bones are gone.
- **Build e030b9406d09**, restaged in place at 22:34. No Deploy was needed. The Silhouette session
  was told this is the final vertex order before it regenerates.
- **Also in this build:** the arousal nipple layer comes off while Silhouette's refit marker says
  heavy clothes (its S-49/S-50 contract). Silhouette_Refit under Silhouette.esp|0x803 is then an
  even whole number of at least 2. It is read directly, with no call into Silhouette's scripts.

## A-24 — The fork's licence and the page title (owner's polls, 2026-09-23)

**Decision.**
- fo4-anatomy's changes to the fork (fo4-ocbpc) are under the **GNU GPL version 3**, like upstream's
  `cbpc` branch today.
- The code the fork starts from (abc0192, 2020) keeps its **MIT** licence. So `cbp.dll` is
  distributed under the GPL-3.0, with the MIT notice kept.
- The Nexus page title is **"Anatomy - CBBE Genitals, Physics and Arousal"**. The files keep the
  name Anatomy (Anatomy.esp, AnatomyBuilder, the archive).

**The facts that led to the question (read from git, 2026-09-23).**
- Every doc said the fork was GPL-3.0.
- Our base abc0192 carries upstream's MIT LICENSE. Upstream moved `cbpc` to the GPL-3.0 on
  2021-07-21 (c69c98a), a commit our base predates. GitHub shows GPL-3.0 for the repo because of
  it.
- The source must be public in any case: F4SE's readme says "plugins must have their source code
  publicly available".
- `tools/ocbpc_sim.py` ports 46cfb20, after the relicence, so it is GPL-3.0. It never ships.

**What was done (fork ed2253a, release 7039538).**
- Fork:
  - `COPYING` holds the GPL-3.0 text, taken byte for byte from upstream's own LICENSE.
  - A section 5a notice heads every source file we added or changed.
  - `README.md` states the licences, a section 7 additional permission to link with F4SE (our
    parts only), the build, and the third-party code in the tree.
- Release:
  - `cbp.dll` ships beside `cbp.dll - GPL-3.0.txt` and `cbp.dll - MIT (OCBPC).txt`.
  - The README names the exact fork commit players get as source.
  - The builder ships Python's and Pillow's licence files. OpenSSL is left out of its bundle
    (nothing uses the network).
- Publishing the fork's repository stays the owner's act.

## A-25 — The vaginal opening a little longer toward the mons (the owner's look, 2026-09-24)

**The owner's words**, after the first look at the zero-touch build ("genitals works fine really";
no regressions): "a little bit not sufficient big hole in vagina in axis along the lips ... if hole
would be slightly bigger for cover more space close to [the mons] bc rn hole in vagina is alongside
anus ... just make it slightly bigger for being slightly noticeable from front".

**What was measured.** Offline depth-buffered renders from below, with a grid in skin-space y.
- The visible opening runs y 0.4 to 1.9, the back half of the slit; the lips are closed from 1.9
  to 3.2, then the hood.
- None of Nahka's sliders does only what was asked:
  - VaginaPenetrate opens the entrance all round (gaping at 0.5);
  - VaginaSpread parts the outer lips and makes the hole look shorter;
  - VaginaSize shrinks the vulva.
- Stretching the tissue ahead of the hole lengthened the closed lips, not the hole (rendered and
  rejected).

**Decision.**
- A slider of our own, **AnatomyOpening** (`tools/opening.py`, run at the end of split_genitals),
  on both shapes. It is Nahka's own VaginaPenetrate shape, weighted by a smooth step over y from
  1.0 (0) to 2.0 (1), with 100% = 0.6x.
- The front of the opening opens forward, about 0.5 units at the default, and its back stays.
- **Default 50%.** BodySlide gives a slider its set's default whenever a preset does not name it.
  That covers the owner's zero build (measured: the lab build moved exactly the slider's vertices, to
  half-float precision) and every player's preset.
- It is adjustable in BodySlide under the category "Anatomy", as "Opening, front".

**Proven.**
- The seam: the two shapes move together, 2513 of 2513 coincident vertices.
- Folds: Nahka's own opening turns lip-edge slivers over at every strength. Ours adds only slivers
  under 0.002 square units that hers does not (2 at 50%, 4 at 100%). A tighter limit fails.
- fit_check, deployed body vs the build with the opening: every vagina path clips less (as drawn
  31% -> 26%) and stretches far less (worst 9.59 -> 6.36). The anus and walking are unchanged.
- The slit's front rim is partly CBBE's own vertices, so 26 shared vertices move by design (up to
  0.186 units, deep in the slit, where no outfit is fitted). compare_builds now expects exactly
  CBBE + 50% of the slider there and CBBE everywhere else. A gate expecting 100% fails.
- Restaged: build cb5d101c41f0.

**A-25 revised, the same night: the opening is BAKED into the base; the slider only adds.**
- The first version put the opening in a slider with a 50% default. A default applies wherever a
  preset does not name the slider, and that includes every tool that turns presets into run-time
  morphs the way BodySlide would.
- Silhouette's generator did exactly that. Its templates would have written AnatomyOpening 0.5 on
  top of the baked 0.5, doubling the opening on every body; its verifier caught it before anything
  was deployed.
- A player would do the same: build with zeroed sliders (the default bakes 50% in), then apply a
  BodySlide-saved preset through LooksMenu, which names AnatomyOpening=50.
- Now:
  - `opening.py` bakes 0.3 of the weighted VaginaPenetrate shape into Anatomy.nif, the old 50%.
  - AnatomyOpening ("Opening, front") is an EXTRA with default 0: 100% adds 0.3 more, so the
    maximum is unchanged.
  - Nothing that honours defaults can apply it twice.
  - A set already baked is refused (checked).
- The zero build is geometrically the live one: 6 vertices per shape differ by at most 0.00005.
  Build 9117dc1cb72f.
- compare_builds expects the bake on the 26 rim vertices, from CBBE's own positions. A gate
  expecting 0.6 fails (checked).

## A-26 — The face comes alive while the mouth is busy (the owner, 2026-09-24)

**The owner, after a clean smoke test of everything:** "during mouth busy actions which u already
handled for open mouth ... lets make expressions on the face instead of stony but mouth ... cheeks,
brows, nose".

**What Rapport already does there (corrected the same night, from the file the game loads).**
- Rapport has SIX oral styles, `Rapport_Oral_1` to `_6` in `fo4-rapport/data/AAF/Rapport_mfgSetData.xml`.
  All are locked.
- Each writes a few of these morphs and leaves the rest at rest:
  - Oral_1: outer brows 38;
  - Oral_2: nose 46, squeeze 56;
  - Oral_3: nose R 28, outer L 42;
  - Oral_4: inner brows 49;
  - Oral_5: nose 46/24, outer L 49;
  - Oral_6: cheeks 49, inner brows 42.
- This first said the oral set writes none of them. That came from make_mfg.py's single
  `Rapport_Oral` entry; the six styles are in the generated XML.
- The owner still saw a still face, and the styles differ: Oral_1 and Oral_3 deliberately leave
  the inner brows and cheeks alone.
- **Effect of max():** a style's value is the floor. Ours shows only where it is higher, e.g.
  Oral_4's inner brows 0.49 go to 0.6 at full depth, and Oral_1/3 gain inner brows and cheeks.
- The lock is AAF's own and does not reach a write after the merge.
- A look the owner dislikes can come from either side: ours is `FACE_WHILE_BUSY`, Rapport's is
  its styles. Rapport offered to move this into its styles if that is ever wanted.

**Decision.**
- The mouth hook, which already writes after the engine's merge, also shapes the upper face while
  something is in the mouth.
- Each `[Mouth] face=id:contact:depth:stroke` term raises one morph toward
  `contact + depth x (tip past the lips / faceDepth) + stroke x (in-and-out speed / faceStroke)`,
  eased at faceRate and faded with the mouth's own contact blend.
- It only ever RAISES: max with the merged weight. Rapport's sets and the animation's face are never
  erased, and a stronger brow from a Pleasure set wins.
- Refused at load and logged: ids outside 0-49, the mouth's own morphs, the blink (18/41), and more
  than 16 terms.
- First values (`physics_design.FACE_WHILE_BUSY`), for the owner's eye:

| Term | At contact | + with depth | + with stroke speed |
| --- | --- | --- | --- |
| inner brows up | 0.3 | +0.3 | |
| outer brows | 0.1 | +0.1 | |
| brow squeeze | | +0.15 | +0.2 |
| cheeks up | 0.3 | +0.15 | |
| nose up | | +0.1 | +0.15 |

- Tuning means changing the ini, regenerating and writing it in place, with no rebuild.
- physics_config refuses a line longer than the fork's INI reader takes (200 bytes); it would cut
  it silently.
- Rapport was told. Live: cbp.dll bd3362aefdb5 (fork 3edf048), Anatomy/ocbp.ini 8df243d02004.

## A-27 — Rapport is the source of truth for faces (the owner, through the Rapport session, 2026-09-24)

**The owner, to the Rapport session:** "we need grab whole power on ruling things we rule in rapport
including expressions bc we need to be SOT". His poll the same day: Rapport's faces in ALL AAF
scenes, the AAF menu's too.

**Why it happens in our plugin.**
- The engine merges a face as max(MFG override, animation), at +0x6689D0. An override can open a
  feature but never close what an animation opens.
- Read out of the executable the same day: after the merge, the upper eyelids are set to
  min(1, blink + animation). Overrides never reach them.
- Our mouth hook already writes after that merge. So Rapport sends its faces to cbp.dll, and they
  are written over the merged weights.

**The contract (agreed with the Rapport session; fork `CBPSSE/FaceAuthority.h`):**
- F4SE messaging, sender "Rapport", receiver "OCBPC plugin":
  - `'RFAS'` Set: u32 version 1, u32 formID, u64 owned, float value[54]. 232 bytes, values 0..1.
  - `'RFAC'` Clear: version 1, formID. Form 0 means everyone.
- Back to Rapport at PostPostLoad: `'RFAH'` Hello {version 1, features 1}.
  - It is sent only when the merge hook is installed. With no hello, Rapport keeps its own way.
- What Rapport sends:
  - It owns ids 0-49, and a morph it does not name goes out as 0.
  - It sends a face only when the face changes, and a clear at every scene end or afterglow end.
- For a spoken line, Rapport re-sends the face without its 29 mouth bits for about 9 s. An unowned
  morph keeps the engine's value, which is the lip sync. Bit 63 ("speaking") would do the same; it
  stays in the contract, unused.
- We drop every held face on PreLoadGame and NewGame. Rapport never sends a clear-all on a load.

**Composition, every frame, after the engine's merge:**
1. Owned morphs take Rapport's value. The blink (18/41) takes the larger of the engine's and
   Rapport's, so the eyes still close.
2. Then the contact mouth. It starts from Rapport's jaw (the oral base is 0.35), opens to the fit
   while something is inside, and blends back afterwards.
3. A-26's face terms are off on a held face: Rapport's is the face then.

**What changes on screen:**
- Rapport's faces hold in every scene, and they can CLOSE features, e.g. a jaw at 0 over an
  animation that opens it.
- Its eyelid values show for the first time, as a floor under the blink. The Rapport session was
  told its eyes will look more closed than its values ever did.

**Diagnostics:**
- `anatomy_ocbpc.log` gets `[face]` lines: listening, hello, the first set per actor, applied (found
  by the scan or looked up by form), let go.
- While a held face has handed its mouth back, the animation layer is watched. When the line ends,
  the log names the ids that moved (lip sync) and the ones that held steady. This is for Rapport's
  mouth table: its measured list wins.
- `[Mouth] authorityTest=<form id>` runs a self-test through F4SE: a test face, held 20 s of every 30.

**Build:** fork d4bff80, cbp.dll a0c7b04f70fe (sha1).
- Written in place 2026-09-24 16:19, with the game closed (fo4-mcp said "free"), and verified
  live.
- Offline test: 29/29. A mutant that ignores the owned mask fails 4 of them.

**Revision after a four-lens review (2026-09-24, fork c7a0115).**
- **The engine reads its own weights back.** The blink machine does not write the eyelids while a
  line plays, and nothing is computed while paused or in the eyes-closed mode, so the merge reads
  back what we wrote.
  - The review's frame model: a lowered eyelid stayed at 1.0 for a whole line, and so did a released
    one. The contact blend fed on itself while paused.
  - Now the engine's own weights go back before each merge, and ours go on after it.
- **Lines come from the engine.** Lip sync lives in +0xF0, the MFG layer, and a line plays while
  the lip object at +0x2C0 is in state 3 or 4.
  - A held face gives its mouth ids back to the engine for exactly the line, whoever made the actor
    speak.
  - Before, a line Rapport did not route kept a still mouth, and Rapport's own lines relied on its
    9 s guess.
- **The first speech diagnostic watched the wrong layer** (+0x1C8, the keyframes). Its two in-game
  lines were not lip sync, and Rapport was told not to use them. The probe now watches +0xF0.
- **Hardening:**
  - the F4SE listener registers after the hooks;
  - faces are released again at PostLoadGame;
  - on a cell change the held faces are found again by form;
  - the self-test is latched and can never send a clear-all;
  - versions from 1 up are read, append-only;
  - the log marks itself full at 4000 lines.
- **`[Face]` section:** `authority=1` ships. It is its own switch: the hook installs for the mouth
  OR the authority. `probe` and `test` are for testers, and release.py refuses an ini that sets
  them.
- **Tests, in the fork's tests/face:** 44 checks, 10 of them frame by frame against a model of the
  merge. Four planted faults are all caught.
- **A-26 under a held face: the owner's poll, 2026-09-24.** The recommendation was to layer it on
  top. His answer: "i agree with recommendation if it will work smoothly and wont bite as in future
  bc we dividing logic of face expressions on several branchs in architecture. so keep in mind
  this". Fork 8bec8a7 does it:
  - The layers still meet in one place, FaceCompose::AfterMerge, with each one's rights written
    there. The order is the engine, Rapport's face, the contact mouth (ids 2/21/22/44/46), then the
    reaction.
  - The reaction only RAISES its own ids (0, 3/26, 4/27, 14/37, 15/38), by at most its terms and
    only as far as the contact blend. So it comes and goes with the contact, and a brow Rapport sets
    higher stays Rapport's.
  - `[Face] react=0` takes it off held faces without a rebuild, if Rapport ever animates the
    reaction itself.
- **The hello's features (fork f39831b), so Rapport can rely on each:**
  - bit 0: set/clear, and the speaking bit;
  - bit 1: the engine's own lines hand the MOUTH ids back, so Rapport can drop its 9 s mouth-bit
    clearing;
  - bit 2: the reaction may rise above a held face (sent only with react=1).
- Rapport now also sends Clear(0) from its load Reset (its build 23AC97D9, not yet staged).
- **Staged 2026-09-24, with the game closed and fo4-mcp's "free":**
  - cbp.dll a8a641d91a24 (fork f39831b);
  - Anatomy/ocbp.ini fd9a077a0849. That is the dev ini: the release's 0af76318767b plus `probe=1`.

**Review wave 2 (2026-09-24, fork 2ab7df1), and the probe's first data (fork ebe2195).**
- A second review, on Sonnet by the owner's rule for review agents, found no critical issue. It found
  two gaps; both are closed.
  - **The engine weights were kept per face-data ADDRESS until a load.** A cell change frees faces,
    and the allocator may give a freed address to another actor, whose first merge would then get
    the old face back (for one frame, or until unpause). FaceCompose::Ledger now lets go by rule:
    - after the merge that gives a face back;
    - after two publishes without it;
    - at once on a cell change, keeping only the faces found again by form;
    - never across a different actor's form.
  - **The reaction's loader refused only the five contact-mouth ids and the blink.** AfterMerge now
    skips every MOUTH id and the blink whatever the terms say, so the right is enforced where the
    layers meet.
  - Tests: ten planted faults are all caught, including a reused address while paused after a
    cell change.
- **The probe's first real lines (the owner's 17:37 run, build a8a641d91a24):** Rapport held
  001D1F4B and 00115EA1, and each spoke.
  - The engine's line state lasted 4.2 s and 3.1 s.
  - The MFG layer did not move at all. So either those lines carry no lip data (both of Rapport's
    lines were borrowed voices), or lip sync lives somewhere not yet found.
  - The owner had not looked at the lips. The probe now watches every face in reach that speaks, so
    vanilla dialogue, which surely has lip data, will tell the two apart. Rapport was told.
- Live, with the owner's word that the game was closed: cbp.dll 013278e6cd67 (fork ebe2195), and
  the ini is still fd9a077a0849.
