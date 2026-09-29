---
name: gitnexus-area-scripts
description: "Skill for the Scripts area of fo4-anatomy. 44 symbols across 4 files."
---

# Scripts

44 symbols | 4 files | Cohesion: 82%

## When to Use

- Working with code in `scripts/`
- Understanding how verifyInstall, answered work
- Modifying scripts-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `scripts/bearing-verify.mjs` | checkFile, checkManifest, checkPackageGates, checkRetiredHookKeys, checkSkillsStore (+13) |
| `scripts/bearing-ci.mjs` | blastRadius, collectDiff, detectChanges, num, git (+9) |
| `scripts/bearing-token-benchmark.mjs` | answered, classicalCost, cypher, gn, graphCost (+2) |
| `scripts/bearing-agent.mjs` | currentBranch, git, resolveBaseRef, run, runAllowFail |

## Entry Points

Start here when exploring this area:

- **`verifyInstall`** (Function) — `scripts/bearing-verify.mjs:367`
- **`answered`** (Function) — `scripts/bearing-token-benchmark.mjs:163`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `verifyInstall` | Function | `scripts/bearing-verify.mjs` | 367 |
| `answered` | Function | `scripts/bearing-token-benchmark.mjs` | 163 |
| `blastRadius` | Function | `scripts/bearing-ci.mjs` | 110 |
| `collectDiff` | Function | `scripts/bearing-ci.mjs` | 78 |
| `detectChanges` | Function | `scripts/bearing-ci.mjs` | 92 |
| `num` | Function | `scripts/bearing-ci.mjs` | 95 |
| `git` | Function | `scripts/bearing-ci.mjs` | 49 |
| `gn` | Function | `scripts/bearing-ci.mjs` | 57 |
| `main` | Function | `scripts/bearing-ci.mjs` | 331 |
| `postSticky` | Function | `scripts/bearing-ci.mjs` | 299 |
| `repoName` | Function | `scripts/bearing-ci.mjs` | 73 |
| `structural` | Function | `scripts/bearing-ci.mjs` | 125 |
| `checkFile` | Function | `scripts/bearing-verify.mjs` | 106 |
| `checkManifest` | Function | `scripts/bearing-verify.mjs` | 111 |
| `checkPackageGates` | Function | `scripts/bearing-verify.mjs` | 121 |
| `checkRetiredHookKeys` | Function | `scripts/bearing-verify.mjs` | 270 |
| `checkSkillsStore` | Function | `scripts/bearing-verify.mjs` | 292 |
| `checkZed` | Function | `scripts/bearing-verify.mjs` | 326 |
| `readStealth` | Function | `scripts/bearing-verify.mjs` | 43 |
| `classicalCost` | Function | `scripts/bearing-token-benchmark.mjs` | 175 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → Git` | intra_community | 3 |
| `Main → Num` | intra_community | 3 |
| `Main → Gn` | intra_community | 3 |
| `VerifyInstall → ReadStealth` | intra_community | 3 |

## How to Explore

1. `context({name: "verifyInstall"})` — see callers and callees
2. `query({search_query: "scripts"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
