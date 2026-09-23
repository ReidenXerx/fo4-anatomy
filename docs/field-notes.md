# Fallout 4 field notes: what we know, measured

Everything here was **measured on the owner's install** (Fallout 4 GOG 1.10.163, F4SE 0.6.23, Vortex),
mostly on 2026-09-23. It is the reference for the next job, not a history: the WHY of each choice
lives in `decisions.md` (A-1 … A-17), and the first survey in `research.md`. Where this file and
an older note disagree, this file is newer.

**Conventions used throughout.**
- Units are game units. 1 unit ≈ 1.43 cm, a hand is 5.4 units across the knuckles.
- **Skin space** is the body mesh's own space. The character's left is **−x**, her front is **+y**,
  up is **+z**. Skeleton space = skin space − (0, 0.882, −120.844).
- "Measured" means a script read it from the file or the game. Numbers without a source are
  marked as estimates.

---

## 0. The facts that cost the most to learn

1. **Women do not load ZeX's skeleton.** DiscreteFemaleSkeleton.esp is active, so HumanRace women
   load `CharacterAssets/female/skeleton.nif` (Skeletal Adjustments for CBBE) and `female/skeleton.hkx`
   (More Flexible Ragdoll). **Neither has a single genital bone.** Men load ZeX's skeleton (§1, §2).
2. **A mesh weighted to a bone the skeleton lacks strands those vertices at their bind place under
   the actor's root.** Standing, it looks perfect. When the pelvis moves, a fin or rod stretches toward
   where the standing crotch would be. That was the whole "fin" saga (§17).
3. **OCBPC SETS a simulated bone's local transform** every frame (first-seen local + physics). Any
   animation of that bone is thrown away (§4).
4. **The owner's `cbp.dll` is OCBPC 0.3 = commit abc0192** (2020). It is identified by its config
   keys, because release builds compile the logging strings out (§4, §5).
5. **LooksMenu shows, per morph, the MAX over its keyword layers.** A keyed layer can only raise a
   morph. BodyGen generates a body only for an actor with NO stored morphs at all (§8).
6. **FO4 faces open the mouth with expression morphs, not bones.** A FaceGen head is skinned to 10
   body bones and none of the face skeleton's mouth bones (§10).
7. **Vortex's first Deploy of a conflicting file may hand it to the OTHER mod.** Check
   `Data/vortex.deployment.json` → `source` for the file (§15).
8. **Every "against the skeleton" check must use the skeleton that actor actually loads.** Read
   `plugins.txt` first.
9. **A row of collision spheres wider than an opening pushes its lips INWARD.** The outer spheres
   sit beyond the lip bones (§11).
10. **A simulation is only as good as its scenario's coverage.** A fist modelled with a 7-unit gap
    held the entrance on the gap and "showed" a fist opening less than a penis (§7).

---

## 1. The owner's install: who provides what

| File (in Data) | Comes from | Notes |
| --- | --- | --- |
| `CharacterAssets/skeleton.nif` + `.hkx` | ZeX - ZaZ Extended Skeleton 6.0 | men (and women if DFS is off) |
| `CharacterAssets/female/skeleton.nif` | Skeletal Adjustments for CBBE (39006) → **now ours** (Anatomy-dev wins) | 3BBB-style, 208 nodes, no genital bones |
| `CharacterAssets/female/skeleton.hkx` | More Flexible Ragdoll | names 74 of the .nif's nodes, no genital bone |
| `skeleton_faceBones.nif`, `skeleton_female_faceBones.nif` | ZeX | 269 nodes incl. `skin_bone_*` mouth bones, Tongue_00-04 |
| `FemaleBody.nif/.tri` | Anatomy-dev (ours) | was bodyslides_f4_sd (owner's BodySlide output) |
| `F4SE/Plugins/cbp.dll` | Jiggle Physics (= OCBPC 0.3) → **ours once deployed** (fo4-ocbpc) | OCBPC-0.3-CBBE holds the same 2020 file |
| `F4SE/Plugins/ocbp.ini` | MadKita's Actual Jiggle → ours (every line kept + our bones) | `detectArmor=0`, `femaleOnly=1`, has `[Attach]`, `[Attach.A]`, `[Override:…]` |
| `F4SE/Plugins/OCBPCollisionConfig.txt` | Jiggle Physics → ours (+ our spheres) | `[ExtraOptions]` collisionX/Y/Z = 1.0 |
| body textures `FemaleBody_d/n/s` … | CBBE HeadRear Absolute Fix → ours (genital island patched) | the material decides the paths (§12) |
| `Anatomy.esp`, `Scripts/Anatomy/Arousal.pex` | Anatomy-dev | light plugin, must be enabled |

- **Plugins:** `%LOCALAPPDATA%/Fallout4/plugins.txt`, where `*` means enabled. DiscreteFemaleSkeleton.esp is
  active there; the owner's ini has Papyrus logging off (`bEnableLogging=0`).
- **Physics:** OCBPC runs; FO4FasterHdtSMP is also installed (no XML config names genital bones).
- **AAF:** AAF 1.7.4.1 with UAP (only its "[UAP] …" positions animate here), BP70, Rufgt, Atomic
  Lust, ZaZOut4, darthroman's DR pack, and BodyTalk's theme files.
- **LooksMenu** runs BodyGen; Silhouette (a sibling project) generates its templates.

---

## 2. Skeletons, skinning, and the missing-bone stretch

### What each skeleton holds (measured)
| | ZeX `skeleton.nif` | women's `female/skeleton.nif` (base) |
| --- | --- | --- |
| blocks / nodes | 243 / 206 | 245 / 208 |
| genital nodes | 31: Vagina_*, Vagina_CBP_*, Anus_00-04, Penis_*, Penis_CBP_*, Penis_Balls* | **0** |
| extra | Breast/Butt/Thigh/Tail `_CBP_` bones, Tongue_00-04, Belly | 3BBB bones: LBreast_01-03_skin, LButt_01-03_skin, LLeg_Thigh_01_F/R_skin, `*_OFFSET` nodes, `*_00_3B` |
| bone LOD (`BSBoneLODExtraData`) | 3 entries: L_RibHelper 1504, LLeg_Toe1 2500, LArm_UpperTwist1 3500 | same |

- The women's skeleton moves some skin bones compared with ZeX: `L/RLeg_Thigh_Fat_skin` by 2.0
  (re-parented under the knee offset), the calf skins by 2.0, the thigh skins by a 2.5° rotation.
  That is the mod's intended effect on CBBE, and it shows as a 0.36 rest-pose drift in the crotch.
- `Pelvis` and `Pelvis_skin` are identical in both (Δ 0.0). `Pelvis_skin` has local translation 0
  and identity rotation, so it sits exactly on the pelvis.
- **Which nodes animations can move:** only nodes named in the `.hkx`. ZeX's `.hkx` keys
  Vagina_00, Vagina_L/R_01-02, Anus_00-04 and Penis_*, **never the `_CBP_` twins**. The ragdoll `.hkx`
  names 74 nodes: Root, COM, Pelvis and the limbs yes; `Pelvis_skin` and every `_skin`/`_OFFSET`
  node no.
- **Checking names in an `.hkx`:** search for the name followed by `\0` with a non-identifier byte
  before it; plain `strings` is not available. A regex over printable runs merges neighbours.
- **Prop attach nodes** (both skeletons): `WEAPON`, `AnimObjectR1-3` under RArm_Hand; `WeaponLeft`,
  `AnimObjectL1-3` under LArm_Hand; `AnimObjectA/B` under Root.

### The missing-bone stretch (the fin)
- A body `.nif` carries its own node for every bone it is skinned to, placed at the bind pose. When
  the actor's skeleton has a node of that name, the skin binds to it. **When it does not, the
  vertex's share for that bone follows the body file's own node, which stays at the bind place under
  the actor's root.**
- The signature: invisible standing; in any pose that moves the pelvis against the root (lying back,
  kneeling, bent over) a fin or rod stretches from the crotch toward its standing position. It is
  10-20 units, far longer than any physics cap.
- **Reproduced offline:** `tools/pose_check.py` poses the skeleton the women load, gives a missing
  bone's share its bind place, and moves COM (down 15; pitched 90° + down 30). The old build tore
  2,613 / 3,824 crotch edges; the fixed one tore 0.
- **Prevention:** `verify_zex.py` and `restage.py` (step 7) refuse a weighted bone the women's skeleton
  lacks. `skeleton.py --deployed` checks the game, reading plugins.txt for DFS.

### Adding our own bones (the fix, A-14)
- `tools/skeleton.py` copies the women's `.nif` from its owning mod's staging folder, never from
  Data (Data's copy becomes ours once deployed). It appends NiNodes with `nif.Nif.with_nodes()`:
  - Each new node is appended after the last block, so no reference moves.
  - Only the parent's child list grows.
  - The header gains the block count, the type indices, the sizes and the names.
  - Proven: only the parent block changes, no original node moves, and the new nodes land within
    1.5e-6 of the design.
- **9 bones under `Pelvis_skin`** (identity rotation): AnatVulva, AnatLipOuter_L/R, AnatLip_L/R,
  AnatAnus_F/B/L/R. **6 `_Stretch` children** sit on the lip and anus bones (A-17).
- **Nodes that are not in the `.hkx` still work for skinning and for OCBPC.** The body is already
  weighted to `Pelvis_skin` and the other `_skin` nodes, none of which the `.hkx` names.
- A release cannot ship this derivative without Skeletal Adjustments' permission. The alternative is
  a small F4SE plugin that adds the nodes at load time.

---

## 3. Coordinates and conventions

- **Skin offset:** skin = skeleton world + (0, 0.882, −120.844). `zex_bones` step 2 re-measures it
  from the body's bind data (spread 0.005), and `physics_design.SKIN_OFFSET` must agree.
- **NIF rotations:** stored as 9 floats. With `rows(r9)`, world = R × local (`zex_bones.compose`),
  proven by reproducing the body's bone nodes to 0.0000. `skin-to-bone` = inverse(node world) after
  moving skin space by −offset (`bone_origin()` recovers a bone's skin-space origin).
- **OCBPC in memory (F4SE `NiMatrix43`):** world = `rot^T` × local, so its matrix is the transpose.
  A bone's displacement in its parent's frame is `rot × world`. To express a skin-space direction in
  the parent's frame: **local = R_parentᵀ × a_world**, with R in the `zex_bones` convention.
  - Vagina axis in Pelvis_skin's frame: (0.878, 0.479, 0).
  - Anus axis in Pelvis_skin's frame: (0.892, 0.451, 0).
- **OCBPC sphere offsets** are in the actor's heading frame (the skeleton.nif node's rotation), not
  the bone's. Only x offsets survive the pelvis pitching, so place bones at their sphere centres.
- **Half floats:** the body's vertices are stored as half floats unless flagged full precision
  (`VA_FULL`). Skin data per vertex is 4 half weights and 4 byte slots, so **at most 4 influences**.

---

## 4. OCBPC (CBP physics with collisions), reverse-engineered

Source: github.com/ericncream/OpenCBP_FO4, branch `cbpc`, GPL-3.0. The owner runs **abc0192**. The
simulator `tools/ocbpc_sim.py` ports `Thing::Update` and `Collision::IsItColliding`, and is GPL too.

- **Update (`Thing.cpp`):**
  - The first time OCBPC sees a bone, it stores the local position and rotation.
  - Every frame it computes a target (the parent's world transform ∘ the stored local), springs
    toward it (stiffness, stiffness2 × the squared offset, damping, timeTick/timeStep substeps), and
    **SETS** `m_localTransform.pos` to the stored local + displacement × linear.
  - Rotation is the stored rotation times Euler(rotational × displacement).
- **Collisions:**
  - Pushes from overlapping collider spheres are summed, divided by `linear`, scaled by
    timeTick/deltaT, and clamped to `maxoffset`.
  - The displayed displacement is internal × linear, so a push reaches up to
    **maxoffset × linear per axis**, while linear does not weaken a push.
  - **While colliding the spring does not run.**
  - A second, "maybe" check predicts the post-spring position with the internal step.
  - A collider sharing k grid cells with the bone pushes k times.
- **Colliders are rebuilt by name every frame** (scan.cpp: `otherColliders.clear(); CreateOtherColliders();
  UpdateColliderPositions()`), for every tracked actor in the cell.
- **Which actors:**
  - `femaleOnly` limits whose bones are SIMULATED, not whose colliders count.
  - An actor's own colliders act on its own bones, except the same-named node.
- **`[Attach.A]` is inert** unless `detectArmor=1` or a `[Priority]` section exists: without a priority
  the `std::stoul` of an empty string throws and the section is skipped. The owner's MadKita ini has
  `detectArmor=0`, so only `[Attach]` counts.
- **Global multipliers:** `[ExtraOptions]` collisionX/Y/Z (1.0 here) multiply every push.
- **A reset:** a bone further than 100 units from its target snaps back to rest.
- **Logging is compiled out** of release builds; there is no collision log.
- **Identify a `cbp.dll` by the config keys it contains.** 0.3 has `detectArmor`, `Override:`,
  `Attach.` and `armorIgnore`. 2022's HEAD adds `Priority`, `Armor.` and `invertFilter`, plus
  position-offset keys (2021).

---

## 5. Our OCBPC fork: `Documents/Projects/fo4-ocbpc`

- **Branch** `anatomy` from abc0192.
- **Build fixes** (6cd020c): `CompareMaterial::operator() const` for VS2022's STL, and a
  toolset-independent `common_vc14.lib` path.
- **Build:**
  `MSBuild OpenCBP_FO4.sln /t:CBPSSE /p:Configuration=Release /p:Platform=x64 /p:PlatformToolset=v143 /p:WindowsTargetPlatformVersion=10.0.22621.0`
  → `x64/Release/cbp.dll`. It imports only KERNEL32 and exports `F4SEPlugin_Query/Load`, like the
  original.
- **Stretch groups** (2fc9a05):
  - Section keys: `stretchGroup`, `stretchKnee`, `stretchGain`, `stretchMax`, `stretchAxisX/Y/Z`.
  - After an actor's bones update, each group takes the **smallest push across its axis**. Past the
    knee, each member moves its child `<bone>_Stretch` by gain × (smallest − knee), capped at max,
    along its own across-axis push.
  - A group needs ≥ 2 members.
  - What this tells apart: a big object (all bones pushed), a small one off-centre (one side), and a
    hand pressing from outside (along the axis).
- **`[Props]`** (2fc9a05):
  - Keys: `nodes=` (comma list), `radius`, `spacing`, `maxLength`, `minBound`.
  - Every frame, the biggest child (by rendered world bound) of each listed attach node becomes a
    line of collider spheres: from the node, through the bound's centre, to its far side.
  - Offsets are written so that `UpdateColliderPositions` (node + skeletonRotᵀ × offset) reproduces
    the world points.
- **Discovery log** (a33ef50): `Documents\My Games\Fallout4\F4SE\anatomy_ocbpc.log`. It notes,
  once each:
  - every prop that becomes a collider;
  - every node on a nearby actor whose name looks genital or like a toy (penis, cock, dick, knot,
    dildo, strap, toy, tentacle, baseball, vibr, genit, phallus), with its parent and world bound.

  The scan runs every 2 s at most. This is how an unknown toy or creature part gets a name for the
  config. OCBPC's own logging stays compiled out (`LOG_ON` undefined in log.cpp).
- **Safe fallback:** OCBPC 0.3 ignores every new key, so a body weighted to `_Stretch` children
  behaves exactly as before under the old DLL.
- **GPL-3.0:** distributing the DLL means offering this source.

---

## 6. The genitals: geometry, openings, bones, weights

- **Geometry:** Nahka's CBBEVaginaMorphs (LoversLab 4302), aligned to today's CBBE.
  - 25,299 vertices and 12 genital sliders.
  - A canal ~6 units deep and an anal pocket ~2 deep.
  - CBBE itself has no opening: welded by position, its only holes are the neck and the wrists.
- **The openings, from Nahka's own sliders** (scaled to the partner's shaft):

  | | centre (skin) | axis | slider moves | drawn for a shaft of |
  | --- | --- | --- | --- | --- |
  | vagina | (0, 1.55, −55.58) | unit(0, 0.48, 0.88) | VaginaPenetrate up to 0.92 per side | ~1.1 radius |
  | anus | (0, −1.58, −54.07) | unit(0, 0.45, 0.89) | AnusPenetrate: a 0.45 ring by up to 1.04 | ~1.35 radius |

  - The partner (BodyTalk male) has a visible shaft 1.5-1.66 in radius, and his penis bones are
    2.7-3.1 apart.
  - ZeX's anus bones sit 1.0-1.4 units BEHIND Nahka's ring.
  - The vagina lies 3.47 from the anus centre, in the ring's plane.
- **Our bones (skin space):**

  | bone | position | sphere radius | section |
  | --- | --- | --- | --- |
  | AnatVulva | (0, 4.0, −55.5) | none (it only sways) | Vulva |
  | AnatLipOuter_L/R | (∓1.4, 2.45, −55.71) | 0.8 | LabiaOuter |
  | AnatLip_L/R | (∓1.2, 1.08, −55.71) | 1.2 | Labia |
  | AnatAnus_F | ring centre + 0.7 toward the vulva | 0.3 (so the vaginal shaft clears it by 0.47) | Anus |
  | AnatAnus_B/L/R | 1.0 out | 0.6 | Anus |

- **Weights (`zex_bones.py`):**
  - JaneBod Extended's genital pattern, copied by proximity (K=4 within 1.0) and **averaged with its
    mirror image**: JBE's painting is lopsided (1,501 vs 1,020 vertices before, 1,540 vs 1,501
    after). Half of it goes to the vulva and outer lips.
  - Plus a layer **fitted to Nahka's opening**: for each vertex, the non-negative least-squares
    weights of the opening's bones' pushes reproduce her morph displacement × (shaft / drawn-for) ×
    gain.
    - Every bone subset is tried (≤ 4 bones, 15 subsets).
    - A vertex may use only bones on its own side (or the midline).
    - The layer is capped at 0.9.
    - The fit reproduces 51% of the vagina's morph (two side bones) and 94% of the anus's.
  - Then 3 rounds of smoothing on **welded** vertices: UV seams split vertices, and unwelded
    smoothing cracks the seam.
  - Plus a soft outer-lip layer of 0.45 on the crests, fading at every border.
  - The vertex keeps at least 5% of its own weights. The vertex's own largest influence (its anchor,
    usually Pelvis_skin) always stays; the rest are chosen by weight.
- **The shaft's reach in the fit must be the Penis spheres only.** Taking the max over all
  colliders picked up the 3.0 fist ball and shrank every fitted weight (caught before shipping).

---

## 7. The physics design, and how it was tuned offline

- **Springs:**

  | section | stiffness | damping | linear | maxoffset | cap |
  | --- | --- | --- | --- | --- | --- |
  | Labia, Anus | 150 | 6 | 0.2 | 20 | 4.0 per axis (fist-ready) |
  | LabiaOuter | 60 | 3 | 0.5 | 2.4 | 1.2 (wobbles: 0.30 walking, 0.63 running at the crest) |
  | Vulva | 150 | 6 | 0.2 | 12.5 | 2.5 |

- **The vagina opening:** gain 1.35 on the fit (A-15). A penis opens the entrance to a median
  radius of 1.55 (the shaft), with 30% of the entrance still inside it. Stretch is p99 5.0 / max 9.3,
  below Nahka's own slider (5.2 / 13.0). At gain 1.5 the p99 passes hers.
- **The anus opening:** 71% inside (her slider: 68%), stretch 5.2 / 7.9.
- **Cross-contact:**
  - A vaginal shaft reaches the anus bones only 1.2 off-centre, and then by 0.08.
  - An anal shaft reaches the inner lips only 0.6 ahead, by 0.32.
  - The outer lips DO get squished by a vaginal shaft (0.5-1.1), by design.
- **Stretch groups (A-17):**
  - Labia: knee 2.4, gain 3. Anus: knee 1.8, gain 2. Max 1.5 to start.
  - Simulated, the smallest push across the axis:

    |                              | vagina | anus   |
    | ---------------------------- | ------ | ------ |
    | every penis path             | ≤ 2.21 | ≤ 1.13 |
    | two fingers                  | 2.11   | 1.34   |
    | a fist filling the entrance  | 4.45   | 4.0    |
    | a wrist filling the entrance | 3.89   | 3.18   |

  - At max 2.5 a fist opens the entrance to a median 3.0, but stretches the worst edges ×27.
- **The tools:**
  - `fit_check.py`: runs each affected bone through the OCBPC port against the collider spheres
    sliding in along six shaft paths (as drawn, ±0.6, 0.4 sideways, steeper, flatter). It moves the
    vertices by weight × push, then measures:
    - the vertices still inside the shaft around the entrance ("through", only those inside by more
      than 0.15);
    - edge stretch (p99 and max, edges ≥ 0.05 only);
    - seam cracks;
    - walking flap.
  - `pose_check.py`: limb and whole-body poses on the women's skeleton, with missing bones stranded.
  - `scratchpad`-style scenario scripts for widening, fists and stretch; see `stretch_sim.py` in the
    session notes. `ocbpc_sim.run_insert` pushes the collider line to depth 5, so **a scenario's
    spheres must cover the entrance at that depth**.
- **Lessons:**
  - Dense sphere lines (no gaps) hold far more than gapped ones: the lips spring back into the gaps.
  - A fist is best one ball (3.0 on the middle knuckle), not a row.
  - The upper-lip bones used as collision bones stretched the canal mouth ×35 (dropped).

---

## 8. Arousal and nipples (LooksMenu BodyGen, A-16)

- **LooksMenu BodyGen facts:**
  - Templates accept `Morph@low:high` ranges.
  - **BodyGen never re-rolls an NPC already met.**
  - **It generates only for an actor with NO stored morphs.** A keyed layer written early blocks
    generation, so our script waits until the actor has an unkeyed morph.
  - The effective value is the **MAX over keyword layers** (UserValues::GetEffectiveValue). Silhouette
    writes the unkeyed (None) layer, and AAF writes its own key.
  - `RemoveMorphsByKeyword(kw)` clears one layer. `RegenerateMorphs` clears everything; Silhouette
    saves and restores keyed values around it.
  - The Papyrus API (declared in `papyrus-stubs/BodyGen.psc`): `SetMorph`, `GetMorph`, `GetKeywords`,
    `GetMorphs`, `RemoveMorphsByKeyword`, `UpdateMorphs`, …
- **No arousal metric exists** in this load order:
  - AAF's stat layer is empty.
  - UAP's `Arousal` stat decays almost at once and nothing reads it.
  - Ivy has `_ivy_IsAroused` (CompanionIvy.esm 0x11AA; her NPC_ is 0x803).
  - Overture's Desire is ActorValue 0x851 in Overture.esp (0..1, a published id, not built yet: it
    returns None today).
- **Ours:** `Anatomy:Arousal` on `Anatomy.esp` (a light plugin: quest 0x800, keyword 0x801 = the layer).
  - A 3 s real-time tick over human women within ~43 m.
  - Drives: an AAF scene (busy keyword) 1.0 with a 10 s half-life; Ivy 0.8; watching within ~17 m
    0.55; Desire × 0.7; naked (body slot empty) 0.3 with a 45 s half-life.
  - It falls with a 60 s half-life.
  - Nipples on top of her strongest other layer: NippleLength +0.70, NipplePerk2 +0.5, NippleTip
    +0.4, NippleSize +0.40.
- **Nipple morphs measured** (the most movement at 1.0):

  | morph | moves up to | notes |
  | --- | --- | --- |
  | NippleLength | 1.13 | the erection itself |
  | NipplePerk2 | 0.45 | |
  | NippleTip | 0.37 | |
  | NippleSize | 0.28 | |
  | NippleAreola | 0.84 | also pulls the tip back |
  | NipBGone | 0.35 | flattens |

  The nipple sits at about (±7.3, 9.1, −23.0).

---

## 9. AAF: what it does to bodies (measured in Data/AAF)

- **Morph sets:**
  - bp70, Rufgt, AAF and Atomic Lust are all `isFemale="false"` erection sets.
  - BodyTalk's `Theme_SexAnimations` sets women's NippleLength and NipplePerk2 to 0.25 in
    "ready", "Erect" and similar sets, and back to 0 in "unReady"/"Flaccid".
  - **Only ZaZOut4's 11 pillory animations set VaginaPenetrate** (1.0).
  - UAP's "Anus Spread" (103 entries) is a morph our body does not have.
- **Equipment sets:** CockErect (879 uses: Atomic Muscle 0x803 / A-Body 0xF99), un/reEquip, ZaZ
  particles, Vioxsis strap-ons (0x173B).
- **Props:** DR pack's held toys ("DR Fist Dildo 01/02", "DR Fist BaseballBat (anal) 01") should
  be animation objects on the hands' AnimObject nodes, which the fork's `[Props]` covers. Not yet
  confirmed in game: the discovery log will say.
- **DR pack's solo dildos are FURNITURE.** Positions like "DR Dildo vaginal01" carry
  `location="Dildo07"` and the tags `Furn`/`Masturbation`. The toy is a world object she uses, not
  something attached to an actor, so no per-actor collider scan can see it. Supporting them would
  mean colliding with the furniture reference the actor uses.
- **API:** `AAF:AAF_API api = Game.GetFormFromFile(0xF99, "AAF.esm") as AAF:AAF_API`.
  - `api.AAF_ActorBusy` is the keyword on actors in a scene (reading it is safe).
  - `AAF_BlockMFG_Mouth` and `AAF_BlockMFG_All` are keywords that stop AAF's face control per actor.
  - **Any AAF call can end the calling Papyrus stack** (ui.Invoke). Read, don't call.
- Deeper AAF behaviour (events and their arguments, scene end, readiness): `fo4-rapport/docs/aaf-api.md`
  and `aaf-under-the-hood.md`.

---

## 10. The face and the mouth (for the next job)

- **FaceGen heads are skinned to 10 body bones only.** Measured: MaleHeadHuman has 1,696 vertices
  and 10 bones, and no vertex is weighted above 0.05 to any mouth bone.
- **The face skeleton** (ZeX `skeleton_female_faceBones.nif`, 269 nodes) has `skin_bone_C_MasterMouth`,
  L/R/C MouthTop/Bot, MouthCorners, JawMid/Side, `skin_bone_C_Chin` and Tongue_00-04. Heads do not
  use them.
- **The mouth opens through expression morphs.** FO4's facial morph table has 50 entries ("Jaw Open",
  "Lower Lip Down", "Pucker", "Lower Lip Funnel", …); `fo4-rapport/tools/make_mfg.py` lists them.
  AAF drives them from mfgSet XML; Rapport's `Expressions.cpp` applies AAF mfgSets with `lock="true"`.
- **The owner's oral look (Photo149-154):**
  - Mostly the animation's open mouth wraps the shaft fine (Photos 152, 153).
  - In Photo150 the lips stay CLOSED while the penis head is at her mouth, so it clips through.
    This is exactly what a contact-driven mouth fixes.
- **The plan for a contact-driven mouth:**
  - An F4SE plugin measures the partner's penis, finger or toy against her mouth every frame, and
    sets Jaw Open and the lips to fit.
  - It puts `AAF_BlockMFG_Mouth` on her, so animations stop touching the mouth.
  - Lip-sync is left alone when nothing is there.
  - Coordinate with the Rapport session, which also sets faces.

---

## 11. Hands, fists, props

- **Hand size (MaleHands/FemaleHands):**
  - 5.42 across the four knuckles (index to pinky).
  - Wrist to knuckles 7.32.
  - Fingertip bones 4.2-5.6 beyond the knuckles.
  - So a fist is ~6.5 wide, radius ~3.
- **Finger bones:** `L/RArm_FingerXY`, where X is the finger (1 = thumb) and Y the segment (1 =
  proximal, at the knuckle).
- **Jiggle Physics' colliders:**
  - hand (the wrist bone) 2.5
  - Finger12 1.8
  - fingertips (X3) 1.5
  - forearms
- **Ours:** Penis_01-05 (2.0, 1.8), plus **one 3.0 fist ball on Finger31** (A-17). Four 1.6 knuckle
  spheres were tried first; the row is wider than the opening, and the outer spheres pushed the lips
  in.
- **Props:** see §5. The WEAPON nodes are left out, because a held rifle's capsule would squash her
  breasts.
- **Open:** a fisting animation may pulse, because the knuckle ball and the wrist are 7 units apart.
- **In the owner's look (Photo148):** a fisting scene works. The vulva opens around the forearm, the
  lips part around the arm, and the nipples are erect.
- **Creature skeletons deployed here:**
  - Alien, Bloatfly, Molerat, RadRoach, Radscorpion, RadStag and YaoGuai (the DR creature pack)
    have NO penis bones.
  - UAP's Supermutant skeleton has `Penis1-4`, now colliders at 2.5.
  - Dogs use the vanilla skeleton from the BA2. A creature penis is then an attached mesh with no
    bone of its own to collide with. The discovery log finds such meshes.
- **In the owner's look (Photo146-147):** a thick purple knotted object at her vulva did not open
  it. The object is either a creature part or a furniture dildo; the discovery log decides which.

---

## 12. Textures and materials

- **The body's shader names a material** (`basehumanFemaleskin.bgsm`), and the material decides the
  textures. The mesh's own texture paths are ignored. So a skin patch must replace the files at the
  material's paths and win the conflict (A-10; CBBE HeadRear Absolute Fix owns them here).
- **`genital_texture.py`:**
  - It patches only the genital island's texels: triangles in the corner UV block with a new vertex,
    padded 8.
  - Colour gains are applied in linear light.
  - Specular is matched by offset, because the owner's skin spec is ~0 and a gain would crush it.
  - Normals are copied.
  - The seam is feathered (32 px, σ 10).
  - It re-encodes only the affected DXT1/BC5 blocks on every mip, and proves every other block
    byte-identical.
- **ComMoisturizer's cum:** `kzSemen_Female.nif` with `bukkake_show*.bgsm`, alpha 1.0 with blending
  on, so the texture's alpha decides. `CumLook-dev` (alpha 0.55 at offset 28) is an optional
  softener.

---

## 13. BodySlide, Outfit Studio, NIF writing

- **Outfit Studio 5.8.2 headless** (`-a <script>`):
  - 39 step types; an unknown type silently becomes LoadReference.
  - The exit code is always 0; read `Log_OS.txt`.
  - Weight operations are discarded headless.
  - SaveProject drops weightless bones.
  - So bones and weights are written by our own code.
- **`tools/nif.py`:**
  - It edits vertex records in place (same size) and round-trips byte-identically.
  - `with_bones` appends bones to a shape's skin.
  - `with_nodes` appends child nodes anywhere.
  - `with_blocks` replaces blocks.
  - `save_renamed` renames string-table entries, which renames every user of the string.
- **A BodySlide build keeps project bones missing from its reference skeleton** (our 9 + 6 went
  through the ZeX-referenced lab build unchanged, 0.0004 from the design).
- **An omitted slider builds at its DEFAULT.** The owner's bodies are built zeroed and morphed by BodyGen.
- **`compare_builds.py` must PASS:** the anatomy build is today's CBBE build on every shared vertex,
  mesh and morph.

---

## 14. Papyrus and plugins, from scratch

- **Compiler:** `D:/GOGGames/Fallout 4 GOTY/Papyrus Compiler/PapyrusCompiler.exe`, with the
  reconstructed base in `D:/F4CustomMods/PapyrusBase/Source/Base` (including AAF's sources and
  `Institute_Papyrus_Flags.flg`).
- **Import F4SE's own sources FIRST:** `…/Fallout 4 Script Extender (F4SE)-42147-0-6-23-…/Data/Scripts/Source`,
  29 scripts with defaults intact (for `Actor.GetWornItem`). Then the base, then ours and the stubs.
- **Compile in batch mode** (`<dir> -all`): a namespaced script takes its namespace from the import
  paths. `scripts/build-papyrus.ps1` does this.
- **The decompiled base lost every default argument.** Pass all arguments to vanilla functions.
- **An unknown method compiles as "Index … argument list" at 0,0.** Bisect the file to find it.
- **A failed cast inside a loop freezes its counter.** Test with `is` before `as`.
- **Useful ids and calls:**
  - `ActorTypeNPC` Fallout4.esm 0x13794; `HumanRace` 0x13746.
  - `GetWornItem(3)` is biped slot 33, the body.
  - `FindAllReferencesWithKeyword(kw, radius)`, `Utility.GetCurrentRealTime()`.
  - Timers stop in menus but the real clock doesn't, so cap the step.
- **A light plugin by hand (`tools/make_esp.py`):**
  - TES4 flag 0x200, ids 0x800-0xFFF.
  - QUST: VMAD v6, object format 2, one script, no properties; DNAM `110064670000000000000000`
    (start game enabled, priority 100).
  - KYWD: EDID, CNAM `ffffff00`, TNAM 0, form version 131.
  - fo4-rapport's `tools/read_esp.py` parses the VMAD back.

---

## 15. Vortex deployment

- **Hardlinks:** rewriting a staging file IN PLACE (same inode) changes Data at once, so no Deploy
  is needed. **A new file needs a Deploy.** Never write through a hardlink into another mod's file.
- **Conflicts:** a new file that collides with another mod's needs a rule, and **the first Deploy may
  give it to the other mod.**
  - Check `Data/vortex.deployment.json`: the file's `source`.
  - Anatomy-dev must win `female/skeleton.nif` over Skeletal Adjustments, the textures over CBBE
    HeadRear Absolute Fix, and `cbp.dll` over Jiggle Physics.
- **Plugins:** a new plugin lands in `plugins.txt` unticked. Watch for `*Anatomy.esp`.
- **Deployment watchers:** poll for the file's hash in Data, or for `vortex.deployment.json`'s mtime,
  then verify the source. One-shot background scripts beat asking the owner.
- **Restage** (`tools/restage.py`), in order:
  1. Refuse while Fallout4.exe runs.
  2. Lab BodySlide build.
  3. `compare_builds`.
  4. Package.
  5. Rewrite in place, or add new files.
  6. Prove that Data sees the bytes.
  7. Check the women's skeleton carries every weighted bone.

---

## 16. Silhouette interplay (sibling project)

- **Silhouette writes the unkeyed layer.** From its next restage, clothing refit becomes a keyed,
  raise-only layer (Silhouette.esp 0x803): BreastsTogether ≥ 0.3, PushUp ≥ 0.2, NipBGone = 1 under
  heavy armour.
- **The "top-up" plan:** a plugin that fills variety morphs on women already met (asks the owner).
- **Variety ranges:**
  - Genitals (S-17): LabiaSize 0..0.9, Innie 0..0.4, Size −0.35..0.35, Narrower 0..0.5, ClitSize
    0..0.5, AnusDonut 0..0.35.
  - Nipples (S-21): Length 0..0.25, Size −0.2..0.5, Areola −0.2..0.5, Tip 0..0.35.
- **Keep off Silhouette's STATE_MORPHS:** VaginaPenetrate, AnusPenetrate, VaginaSpread and
  ButtcheeksSpread are runtime states, not shapes. Don't rename them.

---

## 17. The fin: a diagnosis post-mortem

| Step | What we believed | What was actually true |
| --- | --- | --- |
| Photo118-120: a spike from the anus | OCBPC pins the anus bones at the cap (A-11) | the anus bones were missing on women |
| Photo125-137: a rod in doggy | animations key the animated genital bones (A-12) | ZeX's `.hkx` never keys `_CBP_`; women's `.hkx` keys nothing genital |
| No twin physics | still the rod, so it's "not OCBPC" | correct, but not a cause |
| No genital weights at all | the rod is gone | **the class of cause: the weights on those bones** |
| Female skeleton inspected | | **0 genital bones: the missing-bone stretch** |

- **Lessons:**
  - Every check (pose_check, the ini's "dead line" cleanup) used ZeX's skeleton, the one women do
    not load. A proxy that passes proves nothing about the runtime.
  - The same wrong skeleton had led the config cleanup to comment out 18 of MadKita's 3BBB attach
    lines. Those bones ARE in the women's skeleton, so that removed working breast, butt and thigh
    physics (restored in A-14).
  - The decisive experiment was subtractive: remove ALL weights of a class, and see whether the
    symptom survives.

---

## 18. Gotchas, one line each

- Heredocs collapse backslashes in this harness; write code with a file tool.
- The Edit tool refuses a file not read in this context.
- Windows `git` warns about LF→CRLF, and the blobs stay LF. Python's `write_text` on Windows writes
  CRLF.
- A regex over an `.hkx` must require `\0` after the name.
- Vortex keeps staging copies in `D:/Vortex/fallout4/mods/<mod>`. Mod folder casing varies
  (`meshes/actors/...`).
- A plain `git commit` in a shared tree swallows another session's staged files; use
  `commit --only -- <paths>`.
- The game's screenshots show the camera's near plane as pale, straight-edged slivers; they are not
  the mesh.
- In-game looks are the owner's: an agent-driven sex-scene capture was stopped by a safety
  classifier (2026-09-23).
- One holder for the running game: never deploy, restage or launch while someone else holds it.
- `GetFormFromFile` on an installed plugin can still return None (Overture's 0x851 today). Check the
  form, not the plugin.
- A fist-sized collider in the "design" dict changes any computation that takes a max over it.
- OCBPC reads `OCBPCollisionConfig.txt` by exact name from `Data\F4SE\Plugins`.

---

## 19. The tools here, and the order they run in

1. `align_body.py`: Nahka's geometry aligned to today's CBBE (stage 1).
2. `mask.py`: the genital region mask (protected = 1).
3. `references.py`: JBE's reference moved into our frame.
4. `skeleton.py`: the women's skeleton plus our bones. `--deployed` checks the game.
5. `zex_bones.py`: bones, weights, the fitted layers and the breast move → `build/project`.
6. `physics_config.py`: ocbp.ini and OCBPCollisionConfig.txt from the owner's, ours appended.
7. `make_esp.py` and `scripts/build-papyrus.ps1`: Anatomy.esp and the arousal script.
8. Verification:
   - `verify_zex.py`
   - `fit_check.py`
   - `pose_check.py`
   - `compare_builds.py` (inside restage)
   - `uv_check.py`
   - `verify_body.py`
9. `genital_texture.py`: the texture patch (only when the skin mod changes).
10. `restage.py`: build, package, and put it into Anatomy-dev. Needs the game closed.

---

## 20. Open questions

- The anal aim: do anal animations enter Nahka's ring, or ZeX's anus position 1.2 behind it? (Not
  yet looked at.)
- Strap-ons on women: Vioxsis' strap-on is probably weighted to Penis_* bones, which the women's
  skeleton lacks. The same stretch would appear; add the bones or re-weight.
- Tune the stretch max/gain and the prop radius from the owner's look.
- The mouth (§10).
- Release:
  - permission for the women's skeleton derivative (or an F4SE node injector);
  - GPL source for the fork;
  - Nahka's and the CBBE team's permissions for the body (A-2).
