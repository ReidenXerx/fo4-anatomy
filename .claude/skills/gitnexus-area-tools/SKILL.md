---
name: gitnexus-area-tools
description: "Skill for the Tools area of fo4-anatomy. 423 symbols across 50 files."
---

# Tools

423 symbols | 50 files | Cohesion: 76%

## When to Use

- Working with code in `tools/`
- Understanding how extract_nahka, idw, main work
- Modifying tools-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tools/garments.py` | check, fit, l1, patch_nif, reparse (+22) |
| `tools/nif.py` | Nif, bone_origin, extra_block, save, save_renamed (+19) |
| `tools/gamedata.py` | Game, main, _ba2, describe, find (+19) |
| `tools/genital_texture.py` | main, verify, verify_island, build, encode_blocks (+15) |
| `tools/ocbpc_sim.py` | Bone, ContactBone, clamp, contact_distance, gait (+14) |
| `tools/zex_bones.py` | smooth, apply, flat, skin_to_bone, transpose (+14) |
| `tools/release.py` | build_dll, builder_files, engine_files, face_section, files (+13) |
| `tools/physics_config.py` | lip_keys, aim_keys, axis, fmt, path (+12) |
| `tools/mouth.py` | measure, read_tri, rot, add, ba2_extract (+11) |
| `tools/rebuild.py` | neck, outfits, find_data, __init__, sha (+10) |

## Entry Points

Start here when exploring this area:

- **`extract_nahka`** (Function) — `tools/align_body.py:60`
- **`idw`** (Function) — `tools/align_body.py:202`
- **`main`** (Function) — `tools/align_body.py:218`
- **`match`** (Function) — `tools/align_body.py:127`
- **`score`** (Function) — `tools/align_body.py:163`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `Grid` | Class | `tools/align_body.py` | 92 |
| `Nif` | Class | `tools/nif.py` | 134 |
| `Bone` | Class | `tools/ocbpc_sim.py` | 50 |
| `ContactBone` | Class | `tools/ocbpc_sim.py` | 127 |
| `Game` | Class | `tools/gamedata.py` | 276 |
| `Body` | Class | `tools/garments.py` | 220 |
| `Cursor` | Class | `tools/nif.py` | 38 |
| `Build` | Class | `tools/fit_check.py` | 71 |
| `Dds` | Class | `tools/genital_texture.py` | 91 |
| `extract_nahka` | Function | `tools/align_body.py` | 60 |
| `idw` | Function | `tools/align_body.py` | 202 |
| `main` | Function | `tools/align_body.py` | 218 |
| `match` | Function | `tools/align_body.py` | 127 |
| `score` | Function | `tools/align_body.py` | 163 |
| `read_set` | Function | `tools/align_body.py` | 74 |
| `shader_from_cbbe` | Function | `tools/align_body.py` | 367 |
| `ours_index` | Function | `tools/align_body.py` | 388 |
| `write_osp` | Function | `tools/align_body.py` | 402 |
| `build` | Function | `tools/apply_patch.py` | 40 |
| `ref` | Function | `tools/apply_patch.py` | 98 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Build → String` | cross_community | 7 |
| `Build → Take` | cross_community | 6 |
| `Main → String` | cross_community | 6 |
| `Main → V_add` | cross_community | 5 |
| `Main → V_mul` | cross_community | 5 |
| `Main → V_sub` | cross_community | 5 |
| `Main → Norm` | cross_community | 5 |
| `Main → Game` | cross_community | 5 |
| `Main → Apply` | cross_community | 5 |
| `Main → Mul` | cross_community | 5 |

## How to Explore

1. `context({name: "extract_nahka"})` — see callers and callees
2. `query({search_query: "tools"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
