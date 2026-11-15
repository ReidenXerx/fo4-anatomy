# Creature morph names (animals)

Settled with Dudu on 2026-11-16.

## The rule

Every ANIMAL creature mesh we ship uses our own morph names, never UAP's or darthroman's. Their names ("Erection",
...) let the AAF creature animation packs drive our meshes automatically. We do not support sex scenes between people
and animals. Our morphs are driven only by our own future behaviour: animals mating with animals of their own species,
with babies, nature-documentary style.

Scope: dogs, wolves, FEV hounds, yao guai, radstags, mole rats, deathclaws, and every animal added later (brahmin
next). Humanoids are not animals and keep their current names: super mutants, behemoths, synths/Nick, ghouls, aliens.

## The names

| Old (UAP / darthroman) | Ours |
| --- | --- |
| Erection | Anatomy Aroused |
| Erection Up | Anatomy Aroused Up |
| Erection Down | Anatomy Aroused Down |
| Penis Adjust | Anatomy Adjust |
| Scale | Anatomy Scale (deathclaw) |
| Length | Anatomy Length (deathclaw) |

The meshes have no genital bones; all motion is these morphs, so the rename fully disconnects the creature packs.
Our mating behaviour drives the new names, by LooksMenu BodyMorph by name or by our own AAF morph file listing them.

## How

- `studies/creatures/morph_rename.py <folder>` rewrites every .tri below a folder (lossless round trip checked, deltas
  compared after); `--check` reports any old name left. Run it LAST on every animal build, before packing.
- Installers for animals carry no AAF / scene lines (`creature_fomods.py` CREDIT_A / CREDIT_DR_A: positions measured
  from UAP's or darthroman's meshes, credited).

## Released

- 2026-11-16: Immersive Dogs 1.1.1, Mole Rats 1.1.1, Radstags 1.1.1, Yao Guai 1.1.1, Deathclaws 1.0.2 (only .tri
  names + installer text changed), and the Ivy-only "Anatomy Deathclaws Ivy Patch" 2026-11-16.
  Built from the live archives by repacking (D:\F4Output\immersive\pack1116).
- Ivy drops the creature animation packs (Fallout-collection); anything another mod depends on stays.
