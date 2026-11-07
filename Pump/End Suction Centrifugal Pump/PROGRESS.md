# End Suction Centrifugal Pump — progress log

Resume point for any session. Update after every milestone. A copy lives in
`OneDrive/Documents/Claude Warning/Pump 3D Model/Project/Pump/End Suction Centrifugal Pump/PROGRESS.md`.

## Status (2026-11-06 07:50)

**Stage 1** of the master prompt (foundation, 3D explorer, component content, engineering calcs/curves) is
**complete**. The stage-1 workflow finished at 07:35 with 15/15 agents done.

| Work item | State | Evidence / notes |
|---|---|---|
| Registry (≈80 ids, variants, explode modes, presets, sections) | done | `registry.ts` |
| Geometry — impeller | done | 27,076 tri high / 9,684 low; closed vanes, backward-curved |
| Geometry — casing / volute | done | 29,440 / 11,460; SDF + marching cubes cast body |
| Geometry — shaft + seal (mechanical and packing) | done | `model/shaftSeal*.ts` |
| Geometry — bearing frame (variants a/b) | done | `model/bearings*.ts` |
| Geometry — coupling, motor, baseplate | done | 35,980 / 14,560 |
| GLB pipeline (`npm run models:build`) | done | high 137,712 tri, 107 meshes, 1.19 MB; low 53,976 tri, 105 meshes, 0.58 MB |
| Viewer (select, explode, section, x-ray, rotation, presets) | done | `src/platform/viewer/*` |
| App UI (catalog, overview, explorer, components, engineering) | done | `src/app/*`, `src/platform/ui/*` |
| Engineering (units, calcs, NPSH, illustrative curves; 66 tests) | done | `src/platform/engineering/*`, `content/curves.ts` |
| Content wet end (53 records, 55 refs) | done; fact-checked (about 25 corrections) | `content/components-wet-end.ts` |
| Content drive end (38 records, 60 refs) | done; fact-checked (about 40 corrections) | `content/components-drive-end.ts` |
| Whole-pump geometry integration review | done (all 7 explode modes collision-free; 78 tests pass) | screenshots → `.shots/integration/` |
| Final integration + e2e QA (`tools/e2e.mjs`) | done: 136/136 e2e checks; tsc, vitest (78) and build clean; entry chunk 230 kB | screenshots → `.shots/e2e/` |
| Phones default to the low-detail GLB | done (07:45); tsc and vitest clean. The e2e re-run reached mobile step m06 with no failures before Claude Code stopped it for low system memory; m07 onwards was not re-run | `explorerStore` `defaultDetail()`, `.shots/e2e-verify/` |

## Known limitations (stage 1)

- **Explode animation:** parts can pass through each other part-way through the animation (coupling bolts and hubs, the outboard cover against the guard end plates, O-rings, keys). Straight-line offsets can't sequence this; the fix is staged explode, which is the same work as backlog item 4.
- **Axial cut:** parts that are never cut (studs, springs) float in front of the cut when they sit on the removed side.
- **Missing ids:** the hold-down bolts have no registry ids of their own, so they highlight as "Casing feet" / "Motor frame". The motor bearings have no DE/NDE ids.
- **Open-impeller variant:** it sits in the closed-impeller casing, so the wear-ring seat is empty.
- **Small UI issues:**
  - The Bottom camera preset is mostly blocked by the baseplate.
  - A hidden part's label still shows when it's selected.
  - The Options panel scrolls at 1440×900.
  - The Explorer chunk is 695 kB, which triggers Vite's >500 kB warning.
- **Load timings** come from headless software rendering, not a real phone. Test on a real phone over the LAN.
- **Contract-change requests:**
  - consolidate `dimensions.ts` (stud angles, back bore, discharge split height, keyways, foot slots);
  - move the highlight/section colours out of `kit/materials`;
  - add an option to keep the selection when a part is hidden.

## Usage measured for this pump (stage 1, includes building the shared platform)

- **Agents** (15 jobs, 1,666 API calls): about 9.2M fresh input tokens, 390M cache-read tokens and 2.9M output tokens.
- **Main session:** about 0.55M fresh input tokens, 16M cache-read tokens and 0.27M output tokens.
- **Time:** about 4.5 h active plus a 3 h usage-limit pause. The session restart and the limit made 3 agents re-run partly.

## How to resume

1. Dev server: `cd /c/dev/equipment-learning && npx vite --port 5173 --strictPort --host`.
2. The build workflow is `end-suction-pump-build`, run id `wf_2b9536a8-8f2`. Script:
   `C:\Users\harsh\.claude\projects\C--Users-harsh-OneDrive-Documents-Claude-Warning-Pump-3D-Model-Project-Pump\1013e77a-98e0-4dc0-b75e-e6a74282ebc6\workflows\scripts\end-suction-pump-build-wf_2b9536a8-8f2.js`
   - In the same Claude session: `Workflow({scriptPath, resumeFromRunId: "wf_2b9536a8-8f2"})`. Completed agents come back from
     cache; only unfinished ones re-run.
   - In a NEW session the cache is unavailable: do the pending rows above by hand (or with a new, smaller workflow).
     The agent reports are in `.../subagents/workflows/wf_2b9536a8-8f2/journal.jsonl`.
3. Checks: `npm run models:build`, `npx tsc -b --noEmit`, `npx vitest run`, `npm run build`.
4. Local git repo (no remote). Checkpoint commits only; nothing is pushed.
5. **OneDrive mirror** (`...\Pump\End Suction Centrifugal Pump\`) holds copies: README.md, PROGRESS.md and `model/`.
   - `model/` contains the GLBs, stats, thumbnail, `es-descriptor.json` and `es-content.json`.
   - After any model or content change, refresh `model/`: copy `public/models/pumps/end-suction-centrifugal/*`, and
     re-export the JSON with a tsx script that imports this module's `index.ts` default export
     (`descriptor` + `await loadContent()`).

## Shared-platform backlog (requested by the HSC session, 2026-11-06; owner: this session; needs the user's go-ahead)

Details: `src/equipment/pumps/horizontal-split-case/AUDIT.md` ("Still open"). Do these after stage-1 QA, keep them generic and backward-compatible, and tell the HSC session before the contract changes land.
1. Descriptor-defined camera presets with string ids (drive-end / non-drive-end views).
2. Auto-ghost the parts covering an enclosed selected part (bearing, seal face, wear ring).
3. Descriptor-defined explode modes (shaft, DE/NDE bearing) and section planes, including a horizontal split-plane section.
4. `descriptor.sequences` and a maintenance-sequence player (HSC exports HSC_UPPER_IDS, NUT_IDS, ROTOR_IDS, GLAND_SLIDE, AUX_IDS, LAYDOWN_IDS + MAINT offsets).
   HSC sequence data (from the HSC session):
   - **Upper-casing removal:** nut groups HSC_NUT_IDS 1→4 (4 nuts each, outermost first). Then HSC_UPPER_IDS move to MAINT.upperSeparated, then upperLifted (casing-lifting-gear visible only then), then upperRemoved. HSC_LAYDOWN_IDS become visible from "removed"; HSC_AUX_IDS are hidden from "lifted".
   - **Rotor removal:** hide HSC_COUPLING_REMOVED_IDS and HSC_BEARING_BOLT_IDS. HSC_GLAND_SLIDE gives signed X slides. Then HSC_ROTOR_IDS move to MAINT.rotorLifted (rotor-lifting-gear visible only then), then MAINT.rotorOnStands.
   - **Offsets** are world-axis Vec3s. The HSC dev/harness.ts (about lines 120–145) is a working reference implementation.
   - **Lesson directives** use nutsRemoved 0–16, which maps to nut group ceil(n/4).
   - The HSC session will move its data into descriptor.sequences, transparency sets and string presets once the contract lands. **Message it then.**
5. Named transparency sets (upper casing / lower casing / impeller / internal assembly).
6. Overlay slot for flow particles and axial-thrust / bearing-load arrows (also needed for the working-principle stage).
7. Engineering-page defaults from the equipment module (double suction: per-eye flow).
8. Offline download (PWA / Capacitor): a later packaging stage.

## Next stages (not started — wait for the user's go-ahead)

Working-principle flow animation · materials module (Service A/B/C) · assembly/dismantling sequence ·
installation/commissioning · failure analysis + troubleshooting · standards (verified editions) · documentation ·
video module (needs user-supplied or licensed videos) · quizzes with local progress · offline download · Capacitor packaging.

## Notes

- Another session builds the **Horizontal Split Case** pump in the same project (`src/equipment/pumps/horizontal-split-case/`).
  Don't edit its files; shared files (`src/catalog.ts`, `src/app/overviews.ts`, `src/platform/**`, `src/kit/**`,
  `tools/build-models.ts`) must keep both pumps working.
  The HSC session confirmed (2026-11-06) that it touched only these shared items: the HSC entry in `src/catalog.ts`, the
  `HSC_OVERVIEW` import and map entry in `src/app/overviews.ts`, the devDependency `three-bvh-csg@^0.0.17` in package.json
  (0.0.18 conflicts with drei's three-mesh-bvh), and new files `dev/horizontal-split-case.html` and
  `tools/export-horizontal-split-case.ts`. HSC uses extra variant axes (passages/markers/piping/tools, default 'hidden').
- The session was cut off once at about 02:58 on 2026-11-06. The workflow was resumed at 03:05 with 11 of 14 agents cached.
- A usage limit paused everything from about 03:08 to 06:10. After the reset the workflow restarted the 3 unfinished agents (2 fact-checkers and the geometry review) on its own.
