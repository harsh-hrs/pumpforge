# Horizontal Split Case pump — progress log / hand-off

Last updated: 2026-11-06 ~02:35 IST. Source brief: the user's "MASTER DEVELOPMENT PROMPT — INTERACTIVE
HORIZONTAL SPLIT CASE CENTRIFUGAL PUMP" (22 sections). Location chosen by the user: the shared app
`C:\dev\equipment-learning` (this folder) + copies of the outputs in the OneDrive folder
`...\Pump 3D Model\Project\Pump\Horizontal Split Case Pump\model\`.

If a session ends (token / usage limit): wait for the reset, then continue from "NEXT STEPS" below.
Nothing needs re-doing — everything listed under DONE is saved on disk.

## DONE (saved)
- [x] Geometry builders `model/*.ts` — casing (CSG, split halves), impeller, shaft, bearings (DE floating / NDE locating + DGBB variant), sealing (mechanical + packing), coupling, motor, baseplate/foundation, piping (variant), lifting gear + rotor stands (variant). 140 meshes.
- [x] Registry / descriptor `registry.ts` — tree, variants (seal, volute, lubrication, thrustBearing, passages, markers, piping, tools), explode offsets (platform modes + HSC extras shaft / bearing-de / bearing-nde), sections, camera presets, maintenance-sequence lists (HSC_UPPER_IDS, HSC_NUT_IDS, HSC_ROTOR_IDS, HSC_GLAND_SLIDE, ...), offsets in `model/dimensions.ts` MAINT.
- [x] CSG fixes: loft cap winding, degenerate triangles before CSG, zero-length bore (casing now clean at high detail).
- [x] Budgets met: high 146.6k tris / 140 meshes / 1.15 MB; low 59.7k / 140 / 0.61 MB (`public/models/pumps/horizontal-split-case/report.json`).
- [x] GLB exporter `tools/export-horizontal-split-case.ts` (meshopt + quantize; `--copy <dir>`).
- [x] Dev harness `dev/horizontal-split-case.html` + `dev/harness.ts` (states: maint=..., explode extras, section=horizontal, show=...).
- [x] Content `content/data/*.ts` (from 8 parallel authoring agents): 149 component records, 57 topics, 24 failures + 17 symptoms, 39 materials + 16 rows + 3 service examples, 6 standards + 14 sources, 4 procedures (51 steps), 38 guidance topics, 4 checklists, 14 lessons (89 chapters), 83 quiz questions, overview, 5 working stages, thrust lesson, 17 hydraulic parameters, 9 formulas.
- [x] Adapter `content/index.ts` -> platform EquipmentContent; `content/curves.ts` illustrative curves; `content/overview.ts`.
- [x] Module `index.ts`; registered in `src/catalog.ts` (status in-development) and `src/app/overviews.ts`. Works in the app at `#/e/pumps/horizontal-split-case/explorer` (selection + info panel verified).
- [x] Outputs copied to OneDrive `Horizontal Split Case Pump\model\` (model.glb, model-low.glb, report.json, hsc-descriptor.json, hsc-content.json, hsc-extended-content.json) + README. Temporary Next.js scaffold there removed (its content was byte-identical to `content/data`).
- [x] Typecheck clean (`npx tsc -p tsconfig.app.json --noEmit`), existing 71 vitest tests pass.

- [x] 3D-model completeness audit DONE (attempt 2, run wf_6c3d2eab-899; 18 agents): 98 confirmed findings
      (1 critical, 36 major, 61 minor), 2 refuted; 271/317 coverage checks complete. Summary + resolution in `AUDIT.md`.
- [x] Fix pass 1 (2026-11-06 ~07:30 IST): all model/registry findings fixed (explodes redesigned & collision-checked, maintenance
      supports, lugs, jacking screws, oil level, NDE clamping, flush passages, gland studs, hold-down bolts, grout fill, motor
      bearings/proportions, guard end plates, etc.). Budgets: high 149.4k/140/1.18 MB, low 59.8k/140/0.62 MB. GLBs + JSON
      snapshots re-copied to OneDrive. Typecheck clean, 78 tests pass.

## IN PROGRESS
- [x] (completed — see DONE) 3D-model completeness audit — attempt 2 (2026-11-06 ~03:05 IST). Attempt 1 (run wf_5ab88a6a-105) was cut
      off when the session ended: 6 inspectors had rendered ~136 screenshots but none returned results.
      Attempt 2 REUSES those screenshots: index of screenshot -> harness params at
      `C:\Users\harsh\AppData\Local\Temp\claude\56ee1e4ba6e86199\b6b70969-ff7e-4a83-b964-e99490507d76\scratchpad\hsc\audit-shot-index.json`
      (screenshots in `...\scratchpad\hsc\audit\<area>\`). Fewer new renders per inspector, max 3 concurrent renders.
      Attempt 2 run id `wf_6c3d2eab-899`, script
      `C:\Users\harsh\.claude\projects\C--Users-harsh-OneDrive-Documents-Claude-Warning-Pump-3D-Model-Project-Pump\b6b70969-ff7e-4a83-b964-e99490507d76\workflows\scripts\hsc-3d-model-completeness-audit-2-wf_6c3d2eab-899.js`
      (resume in the same session with Workflow({scriptPath, resumeFromRunId: 'wf_6c3d2eab-899'}); in a new session
      relaunch that script — completed inspectors' screenshots stay in `audit\<area>-2\`).
      Repo note: a local git repo (no remote) was created by the End Suction session for checkpoint commits —
      only path-limited `git add/commit` of HSC files; never init/reset/checkout/stash; don't touch end-suction files.
- [x] (attempt 1 details, for reference) 3D-model completeness audit (Workflow, background) — 9 inspectors (casing, impeller-shaft, bearings,
      sealing, drive-base, maintenance-explode, low-detail, app-integration, brief-coverage) + adversarial verifiers.
      Run id `wf_5ab88a6a-105`. Script:
      `C:\Users\harsh\.claude\projects\C--Users-harsh-OneDrive-Documents-Claude-Warning-Pump-3D-Model-Project-Pump\b6b70969-ff7e-4a83-b964-e99490507d76\workflows\scripts\hsc-3d-model-completeness-audit-wf_5ab88a6a-105.js`
      Journal / results: `...\subagents\workflows\wf_5ab88a6a-105\journal.jsonl`. Screenshots:
      `C:\Users\harsh\AppData\Local\Temp\claude\56ee1e4ba6e86199\b6b70969-ff7e-4a83-b964-e99490507d76\scratchpad\hsc\audit\`.
      If interrupted: re-run with Workflow({scriptPath: <script>, resumeFromRunId: 'wf_5ab88a6a-105'}) in the same
      session (cached agents return instantly), or start a fresh audit in a new session.
      Results will be summarised in `AUDIT.md` next to this file.

## NEXT STEPS (in order)
1. (done) Audit + fix pass 1 — see AUDIT.md "Resolution". Re-export command:
   `npx tsx tools/export-horizontal-split-case.ts --copy "<OneDrive>\Horizontal Split Case Pump\model"`.
2. AGREED 2026-11-06 ~07:45 IST: the End Suction session (owner of src/platform + src/app) will build items 1-7 of AUDIT.md
   "Still open" generically (string camera presets incl. DE/NDE, select-ghosting, descriptor explode modes + horizontal section,
   descriptor.sequences + player, named transparency sets, overlay slot for flow/arrows, engineering defaults per module) after
   its QA and the user's go-ahead; offline/Capacitor is a later packaging stage. DO NOT edit src/platform or src/app. Keep the
   HSC_* exports + MAINT offsets stable; when the contract lands, port them into descriptor.sequences / presets / x-ray sets.
   (Original note:) Missing 3D interaction for this pump in the APP (data exists; needs viewer support — coordinate with the
   session that owns `src/platform`): upper-casing removal / rotor removal sequence player (nut pairs 1-8,
   separated -> lifted -> removed, glands slid, spacer off, rotor lifted -> stands); DE / NDE camera views;
   per-part transparent modes (upper / lower / impeller / internal); horizontal section; the 3 HSC explode extras;
   double-suction flow particles (stages 1-5, qualitative); axial-thrust and bearing-load arrows.
3. Geometry still approximate / absent: impeller balance arrangement (content only); motor end shields merged
   into the frame (mesh budget); simplified suction chamber shapes.
4. Learning sections (platform "Next stage"): working principle, materials, installation, failure analysis,
   standards, video (narrated lessons), quiz (incl. click-on-model), maintenance simulator, documents library,
   offline/PWA + IndexedDB progress — consume `loadExtendedContent()`.
5. Before publishing: verify AWWA E103-21 and API 610 13th ed. (2026) on the issuers' sites; ISO entries were
   confirmed only via ISO member catalogues (iso.org blocked automated access).
6. Perf follow-up: pre-build platform content to JSON (first dev load of the content chunk ~30 s).
