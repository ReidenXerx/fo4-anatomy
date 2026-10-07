# Release facts: the canal (2026-10-07)

Engine 1.2.13, Anatomy 1.2.4, AnatomyBuilder 1.2.7, Anatomy Bodies (prebuilt) 1.2.4. Card: studio/anatomy/out/anatomy-canal.jpg.

## Changelogs

**Anatomy Engine 1.2.13**
- The vaginal canal wraps the shaft: its walls open round it ring by ring and close behind it (needs Anatomy 1.2.4 and a body from AnatomyBuilder 1.2.7 or the prebuilt bodies 1.2.4).
- Health check: the first-scene report waits for a scene with a woman in it, and counts her mouth as an opening.

**Anatomy 1.2.4**
- The canal's wrap: 48 ring bones and the [Canal] settings for the Engine 1.2.13.
- Sleeping, waiting or fast travel settles arousal at once instead of fading over the next minute.
- The installer warns when the Extended AAF Patch (EAP) is active: it is incompatible, use UAP.

**AnatomyBuilder 1.2.7**
- The vaginal canal goes 12.5 deep (was 5.6) to a rounded end, along the penis's path, and is weighted to the canal's ring bones.
- A richer canal lining: sharp folds, redder deeper in.
- A clearer message when another mod's skeleton.nif wins in your load order.

**Anatomy Bodies (prebuilt) 1.2.4**
- Rebuilt with the deeper canal, its ring bones and the new lining; needs Anatomy Engine 1.2.13.

## Measured (for cards and articles)
- Canal depth 5.6 -> 12.5 units along the penis path; 2.3+ from any skin (studies/canal_clearance.py).
- 6 rings x 8 spokes = 48 bones; wall points inside the shaft at full depth 116 -> 11 of 157, worst 0.34, loosest 0.73 (studies/canal_wrap_sim.py).
- Labia untouched: the wrap fades in 1 -> 2 units deep.
- Engine log on the owner's game: "[canal] 00004DED: the canal wraps a shaft (6 rings x 8 spokes, radius 1.98)".
- The [Canal] keys (radius, lead, rate, reach) are in Anatomy's ocbp.ini; no rebuild to retune.

## Compatibility
- Old engine + new body: the rings stay at rest, everything else works. New engine + old body: nothing changes.
- Bones per body shape 127 (limit ~190).
