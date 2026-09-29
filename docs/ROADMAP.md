# Anatomy + Anatomy Engine roadmap

Agreed with the owner on 2026-09-28. Each item names what "done" means; finished items move to decisions.md.
HOW each item is done (the approaches we settled): ROADMAP-DESIGN.md.

## Now (high priority)

1. **The vaginal canal's lining.** The same wet mucosa the anal canal got (A-50): the canal's inner walls take
   the mucosa tone and folds, blended into the vulva at the entrance. Done when the builder paints it and the owner
   has looked in game.
2. **The squeeze jitter.** A hand pressing a breast or the butt makes it twitch: the engine replaces the bone's
   motion with a kick scaled by 1/linear (Thing.cpp, from OCBPC), so it bounces out and back every frame. Resolve
   contact as a constraint (out of the sphere, only the inward motion removed, a little friction, frame-rate
   independent). Reproduce it in ocbpc_sim first; done when a steady squeeze holds still, for any preset.
3. **The inner-thigh crease** (the 4x left after A-30) **and the outfit weights** for garments worn over the body
   (panties, stockings), which must match the body. Done when legs-up poses show no fold and those garments no
   longer part from the skin. Any body re-weight means a fresh .tri for bundled bodies and a garments.py regen.
4. **3BBB bodies** (the owner moved it here, 2026-09-28): build Anatomy from the 3BBB body when the player has it
   (the same genitals, canal and bones on a body with three bones per breast and the extra butt/thigh bones), so
   3BBB presets move it. Our CBBE body stays the default and the lighter one (about half the simulated flesh
   bones). Done when a 3BBB preset bounces an Anatomy body in game. Add per-frame physics timing to the log then,
   to put numbers on the CBBE-vs-3BBB cost.
5. **Automatic outfit refits** (the owner's idea, 2026-09-28): convert an outfit made for one body to another
   (vanilla -> CBBE, CBBE -> 3BBB, -> BodyTalk4) with no manual Outfit Studio work, as a BodySlide project. Reshape
   by the body change under each vertex (BodySlide's conversion sets for vanilla -> CBBE), copy bone weights from
   the target body (3BBB's extra breast/butt bones included), carry every slider; rigid parts (plates, pouches)
   move whole. Verified offline: pose-and-preset clipping via our LBS posing tools, physics motion via ocbpc_sim,
   clipping vertices pushed out and re-tested. Output per outfit: a project plus a measured report. Publishing
   policy (the owner): the original mod is a requirement and credited; authors who object PM him. Start: one
   vanilla-body outfit the owner picks -> CBBE, measured, then his look in game.
6. **Engine-driven sex sounds** (the owner's idea, 2026-09-29): body sounds (slaps, wet squelch, penetration,
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

## Later (low priority)

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
