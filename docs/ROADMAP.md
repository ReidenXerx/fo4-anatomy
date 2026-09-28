# Anatomy + Anatomy Engine roadmap

Agreed with the owner on 2026-09-28. Each item names what "done" means; finished items move to decisions.md.

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

## Later (low priority)

- **Men's anus**: a second opening on BodyTalk4 men (geometry, canal, bones at run time, an aim target), built on
  the player's own BodyTalk4. Needs BodyTalk's author's permission first, like CBBE's (Ousnius, 2026-09-28).
- **3BBB bodies**: build Anatomy from the 3BBB body when the player has it, so 3BBB presets bounce.
- **The aim**: tolerate extra nodes between Penis_00..05 (erection mods); optionally prefer the scene's own tag.
- **Built, not yet seen in game**: genitals staying on actors outside your cell and after a ragdoll (A-44/45),
  next-gen 1.10.984, toys as one tube, fisting and big-toy stretch, brows by vaginal and anal depth.
- **Polish**: the wrist line; the small colour bias of the repainted genital patch on DXT1 skins; more pre-built
  presets if asked.

## Settled (not on the roadmap)

- Our own physics preset and collision exist (A-46): Anatomy no longer depends on MadKita's or Jiggle Physics.
- No pre-built .tri on Anatomy's page (Ousnius, 2026-09-28); Ivy's collection keeps its own bundled body.
