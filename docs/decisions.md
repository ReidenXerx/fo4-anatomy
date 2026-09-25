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
- **The owner's second look (2026-09-24, Photo163, a scene):** "lets make nipple erection SLIGHLY less".
  In the photo the erect nipple reads as a long tube. Every gain comes down about an eighth: length +0.70
  to +0.60, perk +0.5 to +0.44, tip +0.4 to +0.35, size +0.40 to +0.35. `Setup()` sets the gains on every
  load, so a save made before this takes the new look at its next load. MCM's strength slider still
  scales all four.
- **The owner's third look (2026-09-25):** "not only longer but also wider? to make it more BUMPED not
  just STRETCHED". Measured, as the nipple's radius at heights over its resting tip
  (scratchpad nipple_shape2):
  - NippleLength pushes out a thin tube (radius ~0.5).
  - NippleSize NARROWS the tip (0.43 -> 0.25 at the tip): it was working against "bigger" all along.
  - NipplePerk2 and NipplePerkiness widen it into a dome.
  Now: length +0.30, perk2 +0.70, tip +0.35, and **perkiness +0.40 in place of size**. The height is the
  same (0.85 over the resting tip, was 0.83), and it is 1.6-2x as wide all the way up (0.92 against 0.49
  a quarter up, 0.70 against 0.44 half up). `Show` now rewrites our layer whole
  (`RemoveMorphsByKeyword`, then each morph), so the dropped NippleSize does not stay on a woman who was
  aroused when a save was made.

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
  - **Answered the same hour by the rapport session:** all 6,656 of Rapport's .fuz files carry a
    0-byte lip track. Its packer takes --lip but was never given one; Overture's pipeline runs the
    game's LipGenerator.exe and is fine.
    - A line with no lip track still plays for its full length, with nothing to animate. The flat
      layer was the right reading.
    - Rapport is regenerating its barks with lip tracks. Its first held bark afterwards gives the
      measured MOUTH ids.
- Live, with the owner's word that the game was closed: cbp.dll 013278e6cd67 (fork ebe2195), and
  the ini is still fd9a077a0849.

## A-28 — The penis finds its opening (the owner, 2026-09-24)

- **The ask:** "autotargeting ... of cock into targeted holes ... if its vaginal pose - autotargeting vagina
  with perfect fit into hole with aligning penis inside it and for mouth and anus too". The owner called it
  "the last piece we miss for make all our engine TRULY amazing". I recommended automatic detection by
  geometry (AAF's position tags could come later as a tie-breaker); the owner said "ofc".
- **Why it is needed:** animations are made against ZeX's anatomy, not ours. A-14 measured anal
  animations aiming 1.2 behind Nahka's ring; a shaft beside the opening pushes the lips instead of
  entering.
- **What it does (fo4-ocbpc `Aim.cpp`, `AimSolve.cpp`; `ocbp.ini [Aim]`):** each frame, before the colliders
  are built, every chain `Penis_00`..`Penis_05` turns about `Penis_00` onto the opening it is closest to
  entering, and its children's offsets stretch up to 10% when it falls short.
  - The openings: her vagina and anus are the fit's own lines (`VAGINA/ANUS_CENTRE` along their `_AXIS`, the
    paths every shaft was simulated along), in Pelvis_skin's frame. Only women carrying our bones
    (`AnatVulva`) have them. Every mouth is [Mouth]'s own point, entered against the way the face looks.
  - The rules: a new lock turns the shaft at most 35 degrees and is kept up to 45, so it does not flicker at
    the edge. The shaft must run within 75 degrees of the opening's axis (never in from the side or from
    inside). The opening is 2 to 1.3 x the chain's length (16.1) from its root. It aims 2 inside, so the
    shaft follows the opening in. Never one's own opening. A lock is never stolen by a better one.
  - The correction sits ON TOP of the animation's pose, in the root's parent's frame (it rides along
    when the actor turns), and eases in and out (rate 8/s). A pose past the angles stays the
    animation's. When nothing is locked, the animation's pose is put back exactly.
  - The lips then open around the corrected shaft, because the colliders are built after it (A-15,
    A-17), and the mouth opens to it (A-20).
- **Only in scenes:** out of a scene the bind pose points the bones forward, so two nude people standing
  close must never be aimed. `Anatomy:Arousal` already reads AAF's busy keyword each tick; it now tells the
  fork who is busy through a native of our own, `AnatomyAim.SetBusy` (`Scripts/AnatomyAim.pex`). It does
  this even with arousal switched off. OCBPC's `OCBP_API` script is not touched (A-21). The fork forgets
  the list after 10 s of silence. The call is made while anyone is busy and once more after, so a cbp.dll
  without the native can only complain during scenes.
- **Tested offline:** `tests/aim` has 13 cases: the settled shaft runs through the aim point, gates,
  hysteresis, the stretch cap, a turned parent, the fade, choice, smoothing, and the matrix round trip.
  Fourteen mutations of the solver are each caught. Two checks no test could tell apart (an opening
  behind the root; snapping the fade to exactly zero) turned out redundant and were removed.
- **Unknown until the owner's look:** the hook runs after the game's event queue. If the animation writes
  the penis bones AFTER it in the frame, the aim would be invisible. The log says which the first time a
  chain is aimed ("the animation keys Penis_00 every frame" or "nothing keys Penis_00").
- **Build:** fork 8eee190, cbp.dll 13bd73d14f73; Arousal.pex a9fa6c70692e, AnatomyAim.pex fc3ef4ce09ad (a NEW
  file: it needs the owner's Deploy). A review (Sonnet) found that someone leaving the scan with a correction on
  would keep it; they are now looked up by form and put back after half a second unseen.
- **The owner's first look (2026-09-24, Photo164-166): "it works!"** The log confirmed the animation keys
  Penis_00 every frame, and the correction still shows. Two problems:
  1. "vaginal scenes ... has tree stage or something with occasional handjob etc. but penis still try to go
     into vagina". The one lock logged was 32.8 degrees off, near the 35 limit: at 12 units that is a 6.5
     miss, not a near miss. An angle alone was too loose a gate.
  2. Clipping: in cowgirl the glans came out through her mons. The entrance's axis tilts forward 28 degrees;
     a whole shaft inside her along it ends at y 9.2, and her front is at 8.2. The owner pointed at PPA's
     answer: the penis bends inside, along the shape of the passage ("like snake in hole").
- **Second version (fork, `AimSolve` v2):**
  - A lock needs the animation's own shaft line to pass within 5 units of the entrance (kept to 8), and the
    closest of those wins, not the smallest angle.
  - A knuckle (`LArm/RArm_Finger31`) within 4 units of the shaft's outer part (past its first bone) means a
    hand holds it. It is not aimed, a lock lets go at once, and it stays unaimed 1 s after the hand leaves.
  - The snake: the shaft runs straight from its root to the entrance, then each joint lands ON the path
    inside, one bone's length from the last. That is a sphere-path crossing, not a distance along the path,
    because a bone spanning a bend would otherwise put its joint outside the path. Every bone keeps its
    length, and every joint's turn is its own correction in its parent's frame, smoothed.
  - The paths are measured, not drawn (`tools/canal.py`): the middle of her body along the midline, height
    by height. From the vagina the path leads 1.5 along the axis, curves back toward her middle
    (y 1.55 -> -0.27), then rises and drifts forward to y 2.1. It stays inside: 1.46 of flesh four units in,
    2.5 to 5.9 after. The anus joins the same midline. The throat is designed, not measured, in HEAD's
    frame: back from the mouth, then down the neck.
  - Offline: 17 cases (bending along a curve to 0.01, stretched too; a turned parent; the gates;
    choice by miss over angle). 22 of 22 solver mutations are caught. Two were first MISSED, and each
    revealed a weak test. The second revealed a real flaw: joints were placed a distance ALONG the path,
    which put them outside it at every bend.
- **The owner's second look (2026-09-24): "bending works gorgeous! for vagina".** Two more asks:
  - "mouth needs same treatment". The designed throat turned down the neck about 2 units inside the lips,
    and a blowjob keeps 6-8 of the shaft in the mouth, so the shaft bent down under her tongue. Now
    (`physics_design.THROAT`): straight back 6 (the mouth's depth), then down the front half of the neck,
    measured on the body (the lower neck's middle is at y -2; the path ends at -0.3). It is written as
    offsets from the mouth and placed in each skeleton's own HEAD frame (the women's, ZeX's).
  - "did u also do this for hands?" The hand gate had stepped aside, so the grip was the animation's. Now a
    gripping hand is a target (`kHand`): the grip is the middle of its four fingers' twelve joints (they
    ring a gripped shaft), its axis index knuckle to little knuckle, entered from either side. While a
    knuckle holds the shaft only hands may be entered, so the shaft runs through the grip, never
    stretched. His own hand counts too. For a second after it lets go, nothing is entered.
  - Offline: tests/aim now 18 cases, and 27 of 27 solver mutations are caught. A grip near the tip is
    needed to catch "a hand stretches". Fork build cbp.dll afab87963bd3.
- **The owner's third look (2026-09-24):** the vagina and hands are good. Two notes:
  - "mouth still needs work ... align with mouth itself pretty bad", with the glans clipping above the upper
    lip. The shaft's axis was aimed at the line where her lips meet, so its upper half rode over her upper
    lip into her cheek and nose. The log agreed: "upper lip 0.71 up". The mouth is now entered 1.3 below
    that line (`mouthDrop`, along the head's up) and the throat path moves down with it.
  - "anal looks good maybe would be good make a little more hole opening". Raising the fitted gain did
    almost nothing (1.25: 71% -> 70% still inside the shaft). The limit was the stretch group (A-17): its
    knee 1.8 is above the ~1.1 a penis pushes the ring across, so the stretch never opened for one.
    `fit_check` now simulates the stretch (a port of the fork's SimObj::UpdateStretch). By knee, as drawn:
    0.8 -> 68%, 0.7 -> 59%, 0.65 -> 47%, 0.6 -> 35%, 0.5 -> 23%. The owner asked for "a little", so 0.65:
    the worst edge stretch is 12.95, under Nahka's own slider's 14.77. Walking and seams are unchanged. It is
    an ini change; the body is not rebuilt.
  - The lip-sync probe data (Rapport's lip-synced barks now move +0xF0) went to Rapport with a caveat: AAF
    writes MFG during scenes too.
- **The owner's fourth look (2026-09-24, Image #8): "penis is clipping in the bottom chin ... when it go
  backward (pulling out) in particular moment the head of penis not blending as its expected".** The
  bend was right; its timing was not. Each joint's correction CHASED the needed one at a fixed pace, so
  while her head and his hips moved it lagged. On a fast pull-out a few degrees of lag along a 16-unit
  shaft put the glans a unit or more off, down through her chin. Now (fork 14ed18d) the bend is solved
  exactly every frame while locked, and only the lock's weight fades in and out. A switch between
  openings crossfades from the pose that was showing. A release is logged with its reason
  (`[aim] X: let go of Y's mouth: ...`), once per pair and reason. Offline: 20 cases. Case 19 bobs a
  mouth 6 units a second and backs off; the chain stays on it within 0.01 every frame and fails against
  the old chasing correction. 30 of 30 solver mutations caught.
- **The owner's fifth look (2026-09-25):**
  - A handjob before she sits on him: "penis didnt hurry up in vagina and stick to hand but it stick
    outside the grip ... from the 4 fingers side". The grip was the average of the fingers' twelve joints,
    and that sits IN the fingers. Every hand lock in the log was 2.0-2.1 off the animation's own shaft.
    Now (fork 5acb631, `AimSolve::GripCentre`) the grip is the centre of the circle through each curled
    finger's three joints, the axis they wrap around. A finger that barely bends (circle over 4) or is
    straight is skipped. With fewer than two curled, there is no grip and the animation's pose shows.
  - The x-ray (Photo176): "penis should go deeper to throat when it start beinding and go down to neck
    ... closer to back side of neck". Measured with the head mesh this time: under the jaw the throat's
    front is at y 1.1-1.5, and the old path ran 0.33-0.43 of flesh from it even standing. It also hung
    from HEAD alone, so a head thrown back swung it forward out of her throat. The owner: "if we will
    properly anchored ... by head and neck nodes we would be good with any position of head and neck".
    Now the path goes straight back 9 (to the pharynx), then down at 60% of the neck's depth: 1.4 to 3.8
    of flesh all the way. The mouth part is in HEAD's frame (`throatF/M`) and the neck part in Neck's
    (`throatNeckF/M`, new keys).
  - Offline: tests/aim 21 cases, 34 of 34 solver mutations caught. cbp.dll a0c8a574e403.
- **Open:** tune capture/keep/entry, depth and the stretch by the owner's look; AAF position tags as a
  tie-breaker in two-hole positions; men's openings (our bones are women's only).

## A-29 — Her brows frown as he goes deep (the owner, through the Rapport session, 2026-09-24)

- **Ask:** "can we make broves alive during blowjob? like when penis go deep in throat broves sliding
  closer like хмурится [frowning]".
- **Split (A-27 holds: Rapport authors faces):** Rapport sends a second face after its held one, the
  DEEP face (RFAD, `'RFAD'`, the RFAS layout, 232 bytes): a mask of brow, lid, nose and cheek ids and
  their values at full depth. It is the same for all six oral faces. The fork blends it in by depth, and
  it says it can in the hello (feature bit 3, value 8). Rapport stays silent until it sees that bit.
- **Blend (fork 10ca01f, `FaceAuthority::BlendDeep`):** masked ids move from the held value toward the
  deep one by w = inside × clamp(depth / 6), the same depth signal A-26's reaction reads. MOUTH ids are
  never blended, even if masked: the contact mouth owns them. A blink still closes over it (max of
  engine and blend). A-26 stands down on masked ids, so each id has one author.
- **Lifetime:** every RFAS drops the deep face, so Rapport re-sends RFAD after each one. RFAC drops it,
  and so does a mask of 0. A deep face for a form with no held face is dropped.
- **Offline:** tests/face has a deep-face section (decode and refusals, none/half/full depth, blink,
  A-26 standing down, lifetime). 16 of 16 authority mutations caught. One was first MISSED: the test
  masked only the jaw, which the contact mouth overwrites anyway. The test now masks 17 too.
- cbp.dll 6a40a1e7a848 carries A-29 and the A-28 pull-out fix. Staged 2026-09-24. The owner (2026-09-25):
  "facial deep expressions in browes is very immersive"; the throat bend (A-28) "is ideal".

## A-30 — The hip fold: a softer pelvis -> thigh handover (the owner's poll, 2026-09-25)

- **Ask:** "on inner side of hip its like a seam or something like mess with meshes and there not smooth
  skin", then Photo177-178 ("ляжка"): a fold and a fin on the inside of her hip in a legs-up scene.
- **What it is not (measured):** no weighted bone is missing from the skeleton women load (the A-14
  fin); SQr17's thigh jiggle bones carry no vertex of this body; ButtFat's physics swung 5 units bends
  edges 1.6x at most; the mesh at rest is sound, and texture cannot fold geometry.
- **What it is:** the skinning. CBBE hands the groin's vertices from Pelvis_skin to the thigh over a thin
  band, and with the legs up that band tears: worst edge 11x, 128 edges over 3x (the original CBBE:
  8x in the inner thigh alone). The worst sat in the perineum, where the split jumps 0.52 -> 0.16
  between neighbours.
- **The poll:** the cost is garments worn OVER the naked body (panties, stockings, leg pieces). They
  keep CBBE's weights, so in deep bends the skin can move up to 3.8 off them at the hip (1.5 walking).
  Full outfits replace the body. The owner: "I agree with recommendation". BodySlide's Fix Clipping
  does not cover this: it pushes a garment out of the body at rest, and here the rest shape is
  unchanged. For a garment that clips, copy its bone weights from this body in Outfit Studio.
- **Built (`tools/hip_fold.py`, builder stage 3b, before the genitals are split off):** the core bones'
  split (Pelvis, Pelvis_Rear, Spine1, the thighs) is averaged with the neighbours across the band (both
  groups >= 0.05, grown 4 rings, 20 rounds). The core's total and every other bone's weight stay
  exactly (a weight under 0.005 may give up its slot). When four slots are too few, the torso bones'
  shares merge (they barely move against each other when a leg bends) and the thigh keeps its share.
  A first cut that let the thigh drop tore 7.2x at the perineum; one that left the genital zone out
  kept its 11x there. With one slot, the bigger group takes it.
- **Measured on the built body (81626eed4a79) against the deployed one:**

  | pose | worst edge | edges > 3x | p99 |
  | --- | --- | --- | --- |
  | legs up 100 | 11.1 -> 4.0 | 128 -> 33 | 3.34 -> 2.61 |
  | legs up and spread | 10.6 -> 3.9 | 96 -> 15 | 3.10 -> 2.33 |
  | sitting 90 | 10.3 -> 3.8 | 107 -> 18 | 3.17 -> 2.46 |
  | spread 45 | 4.2 -> 1.8 | 3 -> 0 | 1.55 -> 1.30 |
  | walking | 3.5 -> 2.0 | 1 -> 0 | 1.59 -> 1.41 |

- **Proofs:** hip_fold stops on a weight set that is not four or fewer summing to 1, on a thigh given to
  the wrong side, on a lost non-core weight, and on welded copies that differ. verify_zex's check 4 now
  allows exactly this, and a planted ButtFat -> pelvis move still FAILS it. split_genitals: 2513 of
  2513 seam vertices move together. compare_builds: PASS, since the mesh and the morphs are untouched.

## A-31 — Every man's penis a mushroom: a thinner shaft, a bigger, redder, glossy head (the owner's poll, 2026-09-25)

- **Ask:** "i want make it mushroom bc personally i like it more ... more narrow ствол give us more fit
  stability especially with mouth ... i like when head is bigger ... lets make it more red bc rn its like
  dead color lol. and make it more glossy". Poll: mushroom only, **everyone** (the player too), the head
  **varied 1.2 to 1.4**.
- **Measured (BodyTalk4, the men's body here; scratchpad penis_shape):** the erect penis is a bullet, the
  head (1.89) narrower than the shaft (2.04). No slider makes a mushroom: TipShape and TipShapeRounded widen
  the head only up to the shaft. The tip bone Penis_05 carries the glans alone (0.96-1.00 over its last three
  slabs) and pivots near the tip. LooksMenu's layers are a MAX (field notes §8), so a thinner shaft cannot come
  from a BodyGen layer of ours.
- **Shape (fork 03bdbf4, `[Shape]`):** the fork scales the chain at run time. Penis_01 gets the shaft scale
  (0.85) and Penis_02..04 inherit it; each later joint's offset is divided by it, so every joint stays where
  the animation put it. The tip gets head/shaft, so the head is 1.2..1.4 in the world, a stable hash of the
  man's form id. The colliders scale with their bones. Shaft 2.04 -> 1.74; head 2.14 / 2.33 / 2.52 at
  1.2 / 1.3 / 1.4, crowned just behind the tip; length +0.2..0.4. tests/aim case 22; 39/39 mutations.
- **Colour and gloss (`tools/glans_overlay.py`, Arousal's `Glans`):** two LooksMenu overlays on every man,
  painted in his body's own UV triangle by triangle where Penis_05 carries the skin (smoothstep 0.35..0.8 of
  its weight, so both end at the crown). The stage stops if a triangle with no head weight covers a painted
  texel (0 of 3854; a probe confirms the check sees the crown's shared edge).
  - `AnatomyGlansFlush`: multiply (dest colour x ours, unlit). It is white everywhere and rose (1, .72, .75)
    on the head, so the lit skin keeps its detail and only its hue deepens.
  - `AnatomyGlansGloss`: additive, a faint sheen plus the game's ShinyGlass cubemap (Textures1.ba2) masked
    to the head, envmap scale 0.35.
  - The BGEM layout was decoded from materials that work in this game (Caliente's overlay, a glass
    material: nothing left over), and every file written is read back.
  - The Overlays API was read from LooksMenu's compiled script, not remembered: Add / GetAll / Remove /
    Update.
  - Each man in the scan is checked once, the player too. MCM "Glans colour and gloss" off removes ours,
    and only ours, from every man given them.
- **The owner's first look (2026-09-25):** "the shaft is perfect width!", and the head's shape is good. But
  the gloss was "not gloss its like condom of top of head ... maybe for gloss u use specular map". An unlit
  reflection reads as a clear shell. LMNSOverlays' nail polish showed LooksMenu takes LIT (BGSM) overlays.
  So `AnatomyGlansGloss` is now the men's own skin material (basehumanskin.bgsm, read as the game loads it):
  - its colour is black and fully transparent, blended one / inverse source alpha, so all it adds is its
    specular;
  - its specular map is ours (strength 1.0, smoothness 0.85, on the head only), over the skin's own
    normal map, with the specular multiplier at 1.6;
  - rim, subsurface, skin tint and shadow casting are off, and it writes no depth.
  The BGSM's lighting fields were decoded on two working files (the skin and the nail polish), which parse
  to the same 25 trailing bytes. The template id is unchanged, so the men who have it keep it.
- **Open:**
  - The overlays are painted in the owner's BodyTalk4 UV. For players, the Anatomy Builder must paint them
    from the player's own men's body before they can ship (they are not in release.py).
  - Tune FLUSH, SHEEN and ENV_SCALE by the owner's look.

## A-32 — The lips fitted round what is in her mouth (the owner, 2026-09-25)

- **Ask:** "minor clipping on mouth lips are we able to make mouth to automatically adjust to shape of thing
  (penis/hand) is puting there? like real humans lips do when u put something there and they shrink around
  it? would be a really realist look".
- **Why it clipped (measured):** A-20's femaleGap 2.97 was the distance between two OUTER lip points,
  including the jaw's forward swing. The shaft passes the lips' INNER edge, the rim of the head's mouth
  hole, and there Jaw Open 1.0 opens 1.91. The jaw opened a third too little: the log's "lower lip 2.43
  down -> Jaw Open 0.90" moves the edge only 1.72, so the lower lip sat ~0.7 inside the shaft.
- **What a mouth can do (`tools/lips.py`, on the heads the game loads):** per morph, how far the upper
  and lower inner edges move at seven points across the mouth (the rim is 3.2 wide):
  - Jaw Open opens a rounded hole (1.91 in the middle, 1.46-1.51 near the corners).
  - The lower funnel opens the middle only (0.32).
  - Upper Lip Up and Lower Lip Down open their side (0.38-0.39); Upper Lip Down and Lower Lip Up close it.
  - The upper lip rises at most ~0.6. A shaft wraps only riding below the lip line, which is where A-28's
    mouthDrop (1.3) puts it.
  - Pucker and the corners-in morphs narrow the OUTER mouth (6.2 wide) by at most 0.8, and do not change
    the opening: not used.
- **Built (fork b5e22d4):**
  - [Mouth] carries the table per sex (lipXs, lip<F|M><id>). Each crossing gives its section in the lip
    plane.
  - `LipFit::Fit` puts the upper edge 0.05 over it and the lower 0.05 under it wherever it spans, and keeps
    the lips closed elsewhere. Inside costs 30 times a gap. It is coordinate descent from last frame's lips,
    eased at the open and close rates.
  - The fitted lips replace jaw / funnel / lift in the contact-mouth layer; the anticipation floor stays.
    A finger opens only the middle; two things together get lips round both.
  - tests/lips: 9 cases, 10/10 mutations. tests/face: the lip path.
- **Open:** tune clearance and the inside cost by the owner's look; the log prints each mouth's first fit.

## A-33 — Rapport's MCM drives the fork's knobs; the deep face follows genital depth too (the owner, 2026-09-25)

- **Ask:** "yeah u can do mcm menu with rapport", and "can we also trigger something similar when penis deep
  in vagina/anus too?".
- **One hub:** Rapport's MCM page sends 'RFAK' (32 bytes: version, enabled bits aim / shape / lip fit /
  reaction / deep, then lip clearance, lip speed, shaft, head min, head max, reaction scale) after the hello
  and on every change. The fork clamps each value to a sane range. The ini's values stand until a message
  arrives, and a knob only switches off what the ini turned on. Hello bit 5 says the knobs are applied.
- **Genital depth:** while a shaft is locked, Aim measures the tip past the entrance along the opening's
  axis: his depth in any opening, and hers in her vagina or anus (a mouth's stays the contact mouth's). A held
  face's Deep face blends by the larger of the oral depth and this one, full at 6 units. Rapport's deep
  faces are Pleasure_1..3. Hello bit 6. It needs [Aim] on.
- **Built:** fork 5217f05. tests/face covers the decode, the clamps and the store; 21 of 21 authority
  mutations are caught.
- **Open:** verify in game: the knobs from the MCM page, and her brows by vaginal depth.

## A-34 — Glances: into the partner's eyes for a second or two (the owner, 2026-09-25)

- **Ask:** "its glance in the partnet eyes. for ex during blowjob time to time glances on 1-2 seconds maybe in
  another poses / if u know people love it during sex".
- **Split with Rapport:** Rapport decides who looks at whom, when and for how long, and sends 'RFAG' (24 bytes:
  looker, target, duration, how open the lids are). The fork turns the eye and opens the lids.
- **How FO4 turns an eye (measured, GOG 1.10.163):** it has no eye bones and no eye morphs. The eye's texture
  slides: a UV offset on the eye mesh's material, the same one Screen Archer Menu sets. The engine's eye update
  (+0x9C0410) eases every tracked actor's offset toward 0.25 x the look direction's sideways and up parts, at
  2.0 a second, and past about 40 degrees it looks straight ahead. The fork hooks that update's two calls and,
  after the engine, writes the glancing actor's eye toward the partner's eyes by the same numbers.
- **The lids:** a glance holds the upper lids (18/41) open, over Rapport's held face and the blink, as the last
  layer of FaceCompose. Eyes shut in pleasure open for the look.
- **Built:** fork 3f33d31 (Eyes.cpp, Glance.h; tests/face covers the decode, the store, the lids and the eye
  math, and 33 of 33 authority mutations are caught). [Eyes] in Anatomy/ocbp.ini; release.py refuses a dev
  [Eyes] probe= or test=.
- **Open:**
  - Which way +UV turns an eye (signX/signY) is for the dev probe and the owner's look to settle.
  - glances=1 (hello bit 4) comes only after the owner has seen eyes turn.

## A-35 — The mouth's lessons for the vagina and anus: a tube, not balls (2026-09-26)

- **Ask:** "check maybe lessons we teach during extensive fight with mouth lips in blowjob could also be used to
  improve our anus and vagina too".
- **What carried over, measured (tools/tube_check.py, fit_check's OCBPC port, on the deployed body):**
  - OCBPC collides sphere against sphere and adds every overlap; the partner's penis is five balls ~3 apart.
    Against the mesh's mean radius (A-31's shape), a labia sphere rides 0.13 inside to 0.69 off the flesh as
    the balls pass; the tip ball stands 0.6-1.4 ahead of the glans.
  - A ball in two spatial-grid cells pushed a bone once per cell (an upstream OCBPC fault).
  - A-31's thinner shaft silently undid A-15: the labia push fell 2.17 -> 1.65 and fit_check's "through" rose
    27% -> 42% (vagina) and the anus's 47% -> 72%. fit_check never knew the run-time shape: it reads the
    collision file's unscaled radii.
- **Built:**
  - fork b40dca1: [Tube] collides each penis chain as one tube (the mouth's reading, Glans.h's profile), one
    push per partner; each collider once per collision pass.
  - The inner lips' spheres 1.2 -> 1.7, so the vulva clears the thinner shaft again.
  - In the port: anus through 72% -> 27% and wobble 0.69 -> 0.21; vagina through 42% -> 26% (the approved
    27%), wobble halved, under the fist stretch's knee on every path.
- **Checked and not taken:**
  - A lead-in for the vagina/anus aim (the mouth's mouthLead). Steeper and flatter entries clip about as
    much as the drawn axis, so there is no oval to fix.
  - Tilting the anus's entry axis. With the rough estimate +40 degrees looked better; with the exact tube the
    drawn +27 is best. The entry POINT matters far more (0.3 off: 57-68%).
- **Open:** the owner's look (tube on, lips 1.7); the region's p99 edge stretch rises 3.7 -> 4.7 with the
  lips; stale: field-notes' "anus knee 1.8" (the code has 0.65 since 09-24).

## A-36 — Every CBBE garment gets the body's hip handover, rebuilt unattended (the owner's poll, 2026-09-26)

- **Ask:** A-30's cost was that garments over the naked body kept CBBE's handover and could part from the skin.
  - First poll: a builder stage per player, auto-detecting the pieces worn over the body.
  - The survey then showed that 126 of the 164 over-body pieces are armour, usually worn over a slot-33 outfit.
    Fixing them alone would part the armour from the outfit.
  - Second poll: "I agree with recommendation", so EVERY CBBE garment, "and we need full auto script that will do
    all machinery for bodyslides regeneration assuming it will work with our silhouette and other our mods".
- **Built (tools/garments.py):** `plan | build | regen | verify | install`, or `all`.
  - Selection: an active plugin's ARMA wears the output as a woman's model (MOD3), and the set was not made on
    BodyTalk or Fusion Girl. The CBBE group alone missed 399 CBBE garments that sit in no group.
    BuildSelection.xml decides between sets that build one mesh.
    Result: 964 sets, 603 of them on the hip band.
  - Per garment vertex:
    - only the core bones' SPLIT moves, and only next to a body vertex whose split the fold changed;
    - the change is full within 1.0 of the body and fades out by 2.5;
    - the vertex's core total, its other bones, and its own weight sum stay as the author made them.
      441 vertices of a vanilla outfit sum to 0.74, and BodySlide ships them that way.
  - It rebuilds in a private BodySlide copy, headless, "CBBE Zeroed Sliders" with --trimorphs, into a folder of
    its own. Nothing in Data/Tools/BodySlide changes.
  - `verify` checks every rebuild against the build it replaces: the same vertices, byte-identical .tri, and no
    weight changed except the core bones'. So LooksMenu BodyGen and Silhouette see exactly what they saw before.
  - `install` writes in place into the BodySlide output mod (hardlinked into Data). It refuses while
    Fallout4.exe runs and backs up what it replaces.
  - nif.py: `with_bones` reuses a node the file already has, and `set_skin_weights` can keep a vertex's sum.
- **Measured:**
  - 603/603 built, 0 BodySlide errors, and verify is clean against the live builds.
  - Pose gaps (garment vertex against its nearest body vertex, LBS), on 26 sampled sets x 7 poses: 100 rows
    better, 68 the same, and 14 with one worst vertex +0.15 .. +0.9 while p95 improved or held.
    Examples: combat-armour leg in doggy, worst 5.10 -> 2.25; a panty in a spine bend, p95 2.46 -> 0.54.
- **Scars (each caught before anything shipped):**
  - The thigh side rule was reversed (LLeg is x < 0): a leg piece parted 7.8 where it had parted 0.25.
  - hip_fold.fit's torso merge put a garment's pelvis share on Spine1: +3.5 in a spine bend. The garment fit now
    drops the smallest share into its nearest neighbour.
  - Dropping the last torso bone: a midline vertex parted 8.2.
  - A `<Shape DataFolder=...>` reads its sliders from another folder. Copying only the set's own folder built
    144 outfits whose body copy had NO morphs. BodySlide said nothing; verify's .tri check caught it.
- **Open:** the install needs a closed-game window and the owner's go-ahead. Also open: folding the stage into
  the frozen builder for other players.

## A-37 — The neck seam: the body's neck ring faces the way the head does (the owner, 2026-09-26)

- **Ask:** "we have some mod about cbbe rear fix ... that supposed to fix rears on waists, necks, and
  [the back of the head] but i think we overwrite it". Photos: Photo229-231.
- **Checked:** nothing of ours overrides CBBE HeadRear Absolute Fix (CBBEHolyFix.esp).
  - Its records win the load order: TXST SkinBodyFemale_1/Dirty_1 -> custombody textures, and the HDPT
    FemaleHeadHumanRearTEMP -> a rear-head piece.
  - Its textures win in Data.
  - Our body mesh equals CBBE's at every seam (UV splits and normals).
  - No body slider moves the neck or wrist edges.
- **The neck, measured:** the head (BaseFemaleHead.nif) and the rear piece meet our body's neck ring on
  coinciding vertices, 0.008 apart. Their normals differ by a median 14.4 deg, 37.5 worst: 22 ring points,
  11 at the front against the head, 9 at the back against the rear piece. The engine lights each mesh with
  its own normals, which gives a line at the join.
- **Built (tools/neck_seam.py, restage):**
  - Each ring point that coincides with the head or the rear piece gets the rotation that turns its
    normal onto theirs. Vertices within 1.5 take the nearest one's rotation, faded, so no crease forms.
  - The whole tangent frame turns (normal, tangent, and the bitangent spread over the position, normal
    and tangent w), so the normal maps read the same way.
  - Result: median 14.4 -> 0.0 deg, worst 37.5 -> 0.3.
  - Only 137 neck vertices' normals change. Positions, weights, the .tri and the genitals are identical;
    the sharpest neighbouring edge in the neck goes 34.3 -> 37.1 deg.
  - Body 52a79f4b7255, staged 2026-09-26.
- **Where it runs, and why:** in restage, on the BUILT body, after BodySlide.
  - BodySlide recalculates every normal on build, so the fix in ShapeData never reached the game.
  - LockNormals on the shape kept it, but it also shipped the crotch's unrecalculated ShapeData normals:
    2,526 vertices 20-180 deg off (measured). Rejected.
  - The first design interpolated a target between the head's ring points. It turned the back of the neck
    97 deg toward a head 7 units away, because the rear piece, not the head, meets the back. Now a point
    follows only a piece it coincides with.
- **Checked and not the cause:**
  - The wrist: diffuse identical at the seam, vertex normals identical, normal maps within 3 deg. The
    hands' specular map is glossier: 32/90 against the body's 23/69.
  - The "UNIQUE" hands material string is unused.
  - The ghoul rear piece samples ordinary ghoul skin (no purple at its UVs).
- **Open:**
  - The wrist's specular mismatch (feather the body's spec toward the hands').
  - The purple ghoul rear: which NPC; Point Lookout ghouls have their own rear part.
  - Players build their own body in BodySlide, which drops a post-build fix. For the release: a builder
    step after their build, or a shipped patcher.

## A-38 — A toy collides as one tube too (the owner's pick, 2026-09-26)

- **Ask:** the Sonnet harness found props excluded from the tube (TubeCollide.cpp: `!c.isProp`), so a toy still
  collided as its line of balls. The owner queued the fix: "yeah ofc go on".
- **Measured (fork tests/tube case 7):** a toy is AddPropColliders's line, balls of 1.6 every 1.5. They
  barely ride, but two or three push a lip at once and ADD. An inner lip (1.7) ended 4.96 .. 5.05 from the
  toy's axis, where the toy's surface is 3.10. As one tube it rests on the surface everywhere (3.100).
- **Built (fork):** [Tube] props=1 turns each prop's line into a tube, read like a penis's (radius less the
  skin).
  - Who it pushes differs from a penis (Tube::Reaches): a penis never pushes its own owner; a toy pushes
    only the [Props] target bones, its holder's own included (solo scenes). That is the rule its balls
    always had.
  - Tests: tube 8 cases; mutants 8/8, 3 of them on Reaches.
- **Open:** the owner's look in a toy scene.

## A-39 — Anatomy Rebuild: the outfit and neck fixes on the player's own builds (the owner's poll, 2026-09-26)

- **Ask:** A-36 (outfits) and A-37 (neck) ran only in the owner's pipeline; a player's own BodySlide
  build drops both. The owner: "we release today also that separate anatomy-rebuild tool also and pass
  to publish bud he will upload it in optional files in anatomy mod page".
- **Design:** patch AFTER BodySlide, not before. The owner's pipeline patches ShapeData, then runs
  BodySlide headless with a zero preset. A player's preset, zaps and BodySlide location are unknown, so
  `tools/rebuild.py` (AnatomyRebuild.exe) never runs BodySlide:
  - the new skinning is computed on the outfit's own ShapeData (unmorphed, where the body fix was
    made), with garments.py's own transfer and check;
  - it is written onto the player's BUILT mesh by vertex index, only after proving that each shape is
    the same mesh: name, UVs and non-core weights. A zap removes vertices and keeps the rest in order,
    so each built vertex is matched to the next source vertex that agrees (3 of 24 sampled outfits
    carry an always-on zap in their body copy);
  - positions, morphs (.tri) and sliders are never touched; a mesh that proves nothing is left as
    built and logged.
  - The neck: neck_seam.apply on the built femalebody.nif; a ring already within 3 deg is left alone.
  - In place (a Vortex hardlink stays one), originals kept in backup/ with a ledger; `--undo` restores
    only files still holding what it wrote. It refuses while Fallout 4 runs.
- **Measured (scratchpad rebuild_test/equiv.py):** 24 outfits built headless from the ORIGINAL
  ShapeData, then patched by the tool, against the verified pipeline's live builds: every weight equal
  (worst 0.0000 after the rerun tolerance was tightened from 2e-3 to 5e-4), positions identical. A
  second run: 0 changed, 15 already. `--undo`: byte-identical to the unpatched builds. The neck on a
  fresh "Anatomy Body" build: 14.4/37.5 -> 0.0/0.3 deg, 137 vertices, byte-identical to the staged body
  52a79f4b7255; a second run does nothing. The packed exe gives the same results.
- **Shipped:** `AnatomyRebuild-<version>.7z` (release.py), an optional file on Anatomy's page.

## A-40 — The tools leave the Nexus download (Nexus quarantine; the owner's poll, 2026-09-26)

- **What happened:** the owner published 1.0.0, and Nexus's automated check quarantined the Main file and the
  Rebuild file ("executables and similar file types"): AnatomyBuilder.exe and AnatomyRebuild.exe with their
  PyInstaller `_internal` .pyd/.dll. The engine (one F4SE .dll) passed.
- **Decision (the owner's poll, "split permanently"):** the tools live on GitHub only; Nexus carries game
  files. release.py builds `Anatomy-<v>.7z` (game files, no Data/Tools) and refuses any .exe/.dll/.pyd in it,
  twice: in the staged files and in the built archive's listing. `AnatomyBuilder-<v>.zip` and
  `AnatomyRebuild-<v>.zip` are for the GitHub release. 1.0.1, because the archive changed.
- **Finding the game:** a tool can now sit anywhere, so `gamedata.find_data` looks at `--data`, then the
  Data folder the tool sits in (Data/Tools/<tool>, as before), then the registry: Bethesda's
  `Fallout4\installed path` (Steam and GOG both write it; measured on the owner's GOG install) and GOG's own
  `GOG.com\Games\1998527297\path`. Under MO2 the tool must still be launched from MO2, because only then does the
  Data folder show the mods MO2 manages.
