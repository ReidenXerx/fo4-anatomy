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
   SETTLED (the owner's poll, 2026-10-02): the page is **"Anatomy Tailor - ESL"**; distribution by **RobCo Patcher
   INIs** (nothing in saves, gone on uninstall, OG and AE); NPCs wear them, vendors sell them, loot and containers
   carry them; **non-lore-friendly outfits** (e.g. Vtaw's cosplays) are NOT spread around: they are rewards in chests
   we pick at specific quest spots and behind tough enemies; **how often is the player's pick in the FOMOD**.
   SCOPE WIDENED (the owner, 2026-10-02, after fo4-refit tools/esl.py's survey: 5 of 105 armor mods pass the strict
   rules): (a) outfit-adjacent records allowed (an armor enchantment, a chest or book that carries the outfit; quest
   and world mods stay out); (b) a mod's OWN extra plugins (its CBBE variant, LL integration, tAE patch) are made
   light in the same file with their references rewritten; (c) a mod's OWN RobCo INIs ship rewritten at the same
   path. Other authors' patches that need the old ids: the FOMOD warns when one is active and the hub page links our
   distribution ("the originals' distribution does not work with the light version; we made our own"). Why rewrite
   rather than leave: a light plugin's ids are masked to 12 bits, so an old id left in an INI or patch can resolve
   to a DIFFERENT record of ours, not just fail.
   DISTRIBUTION (the owner's poll, 2026-10-02): NON-LORE = Vtaw Wardrobe 5, Vtaw Utility Pack 1, Apal Leotard, DX
   Naughty Secretary, MM69 Wraith Cyber Armor -> only rewards in chests at single spots I propose and the owner
   approves; the Naughty Secretary set is also Geneva's own outfit (RobCo outfitDefault). Modular mods get SETS we
   compose from their own pieces (no slot overlap), distributed as sets. RobCo cannot create records, so each mod's
   file carries a small light plugin of ours (no scripts) with the sets (LVLI "use all") and outfits (OTFT); RobCo INIs
   put them into vanilla lists. Women-only sets never go into lists that dress men: female templates only (RobCo
   outfitDefault/filters), or vendors/loot. strong_PA (NPC-only power armour) gets the flag, no distribution.
   The 31 sets (fo4-refit data/esl_sets.json, renders D:/F4Output/esl/sets) APPROVED by the owner, 2026-10-02.
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
   OPEN (2026-10-02, fo4-refit studies/skirt_gif.py, the real solver on the preview jump): coats and closed dresses
   keep the thighs covered (hunter longcoat, slinky dress), but a SLIT dress (vtaw wardrobe5 Dress) throws its front
   panel out flat on the landing: the filter should leave slit cloth plain, or the weights follow the slit.

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
- **Labia fold inward in some animations** (demonjemiy, Discord via Watcher, 2026-10-02; screenshots coming): the
  inner labia close or fold INWARD and the penis clips through instead of being wrapped. Named: BP70 doggy, a
  shower animation; a cowgirl variant wraps fine. Likely the approach angle from behind vs the labia colliders'
  push direction. His idea: an MCM labia preset, "bigger, more rigid" to "almost off".
- **The vaginal canal's interior, improved** (the owner promised it to demonjemiy, 2026-10-02).
- **Volumetric fluids** (demonjemiy, 2026-10-02; the owner: a big job, not now): dripping meshes instead of
  LL's flat overlays, e.g. inside after sex. References: Skyrim SE mods 77506 and 79014.
- **Futanari + strap-ons** (demonjemiy's top asks, 2026-10-02): futanari options that work with the Anatomy Engine
  and 3BBB; strap-ons/toys that collide properly (LL strap-on mods are awkward or broken, the ZeX strap-on fork needs
  outdated files). His idea: our own toy/strap-on fork on Nexus, or ask the strap-on author for one. The owner's
  answer: toys already work when the object is tagged correctly. Later ideas: OCum-like and inflation-like systems.
- **Clothes for Servitrons** (the owner, 2026-10-08: "make it universally being able wear 3bbb, even a male servitron
  with dick"; put on the roadmap the same day). Servitron's whole robot, head and limbs included, is ONE skin item in
  body slot 33 with its parts as mods on it, so any normal outfit (slot 33) replaces the robot entirely. Lending
  ServitronRace HumanRace's armour race is built in the engine but OFF ([Servitron] humanClothes=0, fo4-ocbpc 7d95cd6):
  on, full outfits would erase the robot; accessory slots (hats, glasses, jewellery) would layer. The working route is
  per-outfit Servitron versions like its own Bunny and French Maid: slots other than 33, no human body pieces,
  ServitronRace addons, weighted to her 3BBB body (the Tailor pipeline can do the weighting). Pick a short list of
  favourite 3BBB outfits first; a male Servitron wears them too (his penis under the clothes needs a look).
  Also pending for Anatomy Servitron 1.0.1: the 3BBB Bunny and French Maid projects (D:\F4Output\servitron\outfits3bbb,
  built and in the owner's game 10-08).
- **Servitron spawn helper**: `cgf "Anatomy:DebugSpawn.Servitron"` can land the robot dead (Resurrect in the script did
  not help; console `resurrect 1` does). Workbench-built Servitrons are fine.
- **Polish**: arousal cools down across a game-time jump (sleep/wait: today it ticks on real time and carries
  through a long sleep, fading over the next minute; Arousal.psc Tick); the wrist line; the small colour bias of the repainted genital patch on DXT1 skins; more pre-built
  presets if asked.

## Settled (not on the roadmap)

- Our own physics preset and collision exist (A-46): Anatomy no longer depends on MadKita's or Jiggle Physics.
- No pre-built .tri on Anatomy's page (Ousnius, 2026-09-28); Ivy's collection keeps its own bundled body.
