# Anatomy + Anatomy Engine roadmap

Agreed with the owner on 2026-09-28. Each item names what "done" means; finished items move to decisions.md.
HOW each item is done (the approaches we settled): ROADMAP-DESIGN.md.

## Now (high priority)

Done 2026-09-30 (decisions.md): 1. the vaginal canal's lining (A-54), 2. the squeeze jitter (A-55); 3. the
inner-thigh crease and over-body garment weights, skipped by the owner (A-56: A-30 is the floor for weights).

1. **3BBB bodies** (the owner moved it here, 2026-09-28): build Anatomy from the 3BBB body when the player has it
   (the same genitals, canal and bones on a body with three bones per breast and the extra butt/thigh bones), so
   3BBB presets move it. Our CBBE body stays the default and the lighter one (about half the simulated flesh
   bones). Done when a 3BBB preset bounces an Anatomy body in game. Add per-frame physics timing to the log then,
   to put numbers on the CBBE-vs-3BBB cost.
2. **Automatic outfit refits** (the owner's idea, 2026-09-28): convert an outfit made for one body to another
   (vanilla -> CBBE, CBBE -> 3BBB, -> BodyTalk4) with no manual Outfit Studio work, as a BodySlide project. Reshape
   by the body change under each vertex (BodySlide's conversion sets for vanilla -> CBBE), copy bone weights from
   the target body (3BBB's extra breast/butt bones included), carry every slider; rigid parts (plates, pouches)
   move whole. Verified offline: pose-and-preset clipping via our LBS posing tools, physics motion via ocbpc_sim,
   clipping vertices pushed out and re-tested. Output per outfit: a project plus a measured report. Publishing
   policy (the owner): the original mod is a requirement and credited; authors who object PM him. Start: one
   vanilla-body outfit the owner picks -> CBBE, measured, then his look in game.
3. **DONE 2026-10-01 (A-67, A-68): Engine-driven sex sounds** (the owner's idea, 2026-09-29): body sounds (slaps, wet squelch, penetration,
   furniture creaks) made by the engine from what it measures every frame -- which opening, depth and its change,
   thrust speed, hip/butt impact speed (CollisionHub), arousal as wetness -- instead of the animation packs'
   hand-placed ones. 3D at the pelvis, loudness and pitch from the motion, many variations per kind so nothing
   repeats; the same set for every pack, OG and AE. One feature split between two mods (the owner, 2026-09-29): the
   Anatomy Engine makes the body sounds from its measurements, Rapport keeps the moans and voices, and ONE toggle in
   **Rapport's MCM** switches the whole sound override on or off across both (coordinate with the rapport session:
   the toggle reaches the engine over the existing Rapport -> "OCBPC plugin" messaging). The packs' own body sounds
   are MUTED in scenes while it is on (the owner's poll). Open: which mod ships the clips. First research how the common packs
   fire theirs (animation annotations, their SNDR records). Our own clips (ElevenLabs sound effects, the squelch
   recipe in memory), so no permissions. Done when a scene from two different packs sounds the same and in sync.
4. **ESL versions of outfit mods** (the owner, 2026-10-01; after item 3's test): a separate Nexus page like Anatomy
   Tailor's, one file per outfit mod, the mod's plugin light-flagged with its new records renumbered into
   0x800-0xFFF. Scope (the owner's pick): PURE outfit mods only -- no Papyrus scripts (an injector's
   GetFormFromFile ids would silently miss), no plugin in the load order using it as a master, and no text config
   in Data (RobCo Patcher INIs, AAF XMLs, any "plugin|id" reference, loose and in BA2s) naming its records; a mod
   that fails any check is left out. Same file name, so BA2s and masters still match. Existing saves lose that mod's
   items: the owner accepts it (each file says "new game, or lose its items"; patches for it break; made for
   version X). The 10-01 survey of the owner's 806 active plugins: 105 full plugins add armor -- 5 fit as they are,
   52 fit after renumbering, 48 are too big (>2048 new records; nearly all quest/world mods, plus Vtaw Wardrobe 7
   at 2577). Tooling: our compactor (studies/esl_compact.py, survey studies/esl_survey.py, proven on BoS Recon: 4 ids, 3
   references) grown into a tool, cross-checked by FO4Edit 4.1.5f (D:\xEdit.4.1.5f) "Check for Errors".
   **Plus optional distribution** (the owner, 2026-10-01): every file's FOMOD asks whether to add the outfits to the
   world (NPCs, vendors, containers), written against the NEW ids we assign, so it cannot drift. To decide when we
   get there (poll): the mechanism (RobCo Patcher INIs, already in the owner's list, vs a Papyrus injector), which
   lists, and how often. It may also widen the scope: a mod whose only blocker is its OWN injector script could ship
   with that script left out and ours offered instead.
5. **Collided skirt bones for coats and dresses** (the owner, 2026-10-01; after item 4): legs come through hanging
   cloth when they bend (the jump GIFs). Reweighting alone was measured and rejected (fo4-refit R-18,
   studies/legs_through.py: 10-30% at best, the clipping moves rather than goes, strong settings tear edges 41x).
   The fix: the engine adds a ring of skirt bone chains at the hips at run time (as it adds the genital bones; the
   women's skeleton has none), swings them with its physics and pushes them out of the thigh and calf colliders;
   Anatomy Tailor weights each garment's hanging cloth to them (by angle around the hips and by height). Done when
   legs_through.py, run with the skirt bones simulated, shows the clipping gone in crouch, sit and stride, and the
   jump GIFs agree. Coats also sway as a result.
   Pages (the owner, 2026-10-01): every Tailor conversion page shows GIF collages of a jumping character in coats
   and skirts WITH the Anatomy Engine and WITHOUT it (rendered by preview.py; Publisher-bud told). Open: the engine
   as a requirement of skirt-weighted files, or a FOMOD option -> SETTLED (the owner, 2026-10-01): a FOMOD option
   "Skirt physics (needs Anatomy Engine)"; no = today's weights. Without the engine skirt-weighted cloth would freeze
   in the standing pose (A-14's missing-bone behaviour), so it is never the only version. Tailor builds BOTH variants
   of every garment with hanging cloth in the same run (plain + skirt), and each pack carries both for the FOMOD.

## Later (low priority)

- **Collision spheres fitted to each player's body** (the owner, 2026-10-01: low priority, "with supporting cbbe
  and 3bbb reasonable shapes we are good"): AnatomyBuilder writes OCBPCollisionConfig-body.txt from one of two
  fixed presets (CBBE, 3BBB; spheres measured once on the reference body, tools/default_preset.py). A very big or
  small BodySlide preset keeps those sizes. AnatomyRebuild runs after every BodySlide build and could measure the
  built body and write spheres that fit it.

- **The inner-thigh crease** (A-56): an engine-driven corrective bone at the lip-thigh fold, moved by the
  thigh's angle, is the one untried route past A-30's 4x in legs-up poses; over-body garment weights with it.
- **Men's anus**: a second opening on BodyTalk4 men (geometry, canal, bones at run time, an aim target), built on
  the player's own BodyTalk4. Needs BodyTalk's author's permission first, like CBBE's (Ousnius, 2026-09-28).
- **The aim**: tolerate extra nodes between Penis_00..05 (erection mods); optionally prefer the scene's own tag.
- **Built, not yet seen in game**: genitals staying on actors outside your cell and after a ragdoll (A-44/45),
  next-gen 1.10.984, toys as one tube, fisting and big-toy stretch, brows by vaginal and anal depth.
- **Polish**: arousal cools down across a game-time jump (sleep/wait: today it ticks on real time and carries
  through a long sleep, fading over the next minute; Arousal.psc Tick); the wrist line; the small colour bias of the repainted genital patch on DXT1 skins; more pre-built
  presets if asked.

## Settled (not on the roadmap)

- Our own physics preset and collision exist (A-46): Anatomy no longer depends on MadKita's or Jiggle Physics.
- No pre-built .tri on Anatomy's page (Ousnius, 2026-09-28); Ivy's collection keeps its own bundled body.
