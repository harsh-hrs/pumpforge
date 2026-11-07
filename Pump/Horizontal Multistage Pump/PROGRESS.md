# Horizontal Multistage Pump - progress log

Worktree `C:\dev\el-multistage`, branch `model/horizontal-multistage`. It is based on `platform/viewer-v2` (contract v2, commit 8ff1bc8),
so merge it AFTER that branch. Session pump-83 started on 2026-11-06. The platform owner is session pump-14 (End Suction).

## Stage 1 - DONE (2026-11-06)
- [x] Geometry builders: `model/hydraulics.ts`, `model/rotor.ts`, `model/base.ts`, and `model/index.ts` (composer).
  - The composer reuses the HSC bearings, seals, coupling and motor.
  - Budgets: high 137.7k tris / 912 kB, low 55.3k tris / 482 kB, 129 meshes. All within budget, 128/128 components.
- [x] Registry (contract v2):
  - stage count 3-6 (variant lists + variantOffset) and balance drum/disc
  - 8 explode modes, 3 x-ray sets, 3 sections, 13 camera presets
  - flow and thrust overlays
  - working-principle sequence, plus dismantle and assemble sequences for each stage count
- [x] Content:
  - component records for every id, including group records
  - references, overview and illustrative curves
  - engineering defaults
  - extended content: topics, materials, formulas, maintenance, failures, standards, quiz and video lessons
- [x] Tests: `content.test.ts` (4 tests). The descriptor was added to the platform "catalog descriptors" test. Full suite: 98/98 pass. Typecheck and lint are clean.
- [x] Shared entries, one line each (approved by the platform owner): `src/catalog.ts` (in-development + load), `src/app/overviews.ts`, `tools/lib/equipment.ts`.
- [x] Harness screenshots reviewed:
  - iso view
  - cutaway (6 stages, flow overlay)
  - discharge end at 4 stages
  - radial vane section
  - stage-anatomy and complete explode
  - app explorer page (loads, tree, info panel)
- [x] OneDrive mirror: `...\Pump\Horizontal Multistage Pump\` holds README, PROGRESS and model/ (GLBs, stats, thumb, JSON).

## Depends on the platform (pump-14, branch platform/viewer-v2)
- ModelRuntime support for `variantOffset`. Until it lands, changing the stage count in the app hides and shows stages, but the discharge end stays where the 6-stage build puts it.
- These players and pages consume data that is already in the descriptor or content:
  - sequence player
  - OverlayLayer (flow particles, thrust arrows)
  - working-principle, materials, maintenance, failure, standards, quiz and video pages, which consume `loadExtendedContent()`
- Requested: a force arrow's `attachTo` should include the variantOffset of the part it is attached to (the balance-force arrow is attached to the balance drum).

## Not done / next stages
- Recorded or licensed videos. The lessons are narrated 3D walkthroughs (`videoUrl: null`); offline download follows once files exist.
- Offline (IndexedDB / PWA) packaging: platform stage.
- A light audit (inspector + verify) once the platform players render the sequences, to check step offsets visually in the app.
- Before publishing:
  - confirm API 610 13th ed. in the API catalogue
  - confirm the ISO 13709 relation
  - open the ISO pages in a browser

## How to resume
1. `cd /c/dev/el-multistage && npx vite --port 5176 --strictPort` (dev server for this worktree).
2. Run `npx tsx src/equipment/pumps/horizontal-multistage/dev/check.ts`, then `npx vitest run`, then `DEV_SERVER=http://localhost:5176 npm run models:build -- --only horizontal-multistage`.
3. Mirror to OneDrive:
   - copy `public/models/pumps/horizontal-multistage/*`
   - run `npx tsx src/equipment/pumps/horizontal-multistage/dev/export-json.ts "<OneDrive>/Horizontal Multistage Pump/model"`
   - copy README.md and PROGRESS.md
4. Push: the user runs `git push -u origin model/horizontal-multistage` (sessions never push).
