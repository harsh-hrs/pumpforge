# Horizontal Multistage Pump (ring-section) - equipment module

Generic educational **horizontal ring-section (segmental) multistage centrifugal pump**. Illustrative proportions,
not a manufacturer design, no claim of conformity to any standard. Barrel-type and axially split multistage designs are
explained in the content (`TOPICS.other-configurations`) but not modelled.

## What is in the model
- **Casing:** suction casing (+ nozzle, inlet chamber, DE bracket, feet), 2-5 ring-section stage casings, discharge casing
  (+ nozzle, collector, balance seat/chamber, NDE bracket, feet), discharge cover, seal chambers, joint gaskets, and tie bolts.
- **Stages (1-6):** impeller, key, diffuser, casing wear ring, gasket. Every stage except the last also has a return channel,
  a stage casing, an interstage bush and an interstage sleeve.
- **Rotor:** a shaft for each stage count, DE/NDE sleeves, shaft nuts, and a balance drum + bush or a balance disc + seat.
- **Balance line:** the leak-off line to suction.
- **Reused from the Horizontal Split Case builders:** bearings (DE floating radial; NDE paired angular-contact for the drum
  design, or a radial bearing for the disc design), mechanical seals, coupling and motor. NDE parts are translated.
- **Base:** baseplate sized for 6 stages, pump rails, motor pedestals, shims, bolts, grout and foundation.

## Variants (contract v2)
- `stages` 3 | 4 | 5 | 6 (default 4). Stage k parts use `variant: 'stages:k|..|6'`. The discharge end uses `variantOffset`
  `(6 - N) * 0.115 m` toward +X. Shaft, tie bolts and balance line have one part per option.
- `balance` drum | disc. The NDE bearing changes with it (thrust pair vs. axially free radial bearing).

## Viewer data in `registry.ts`
- **Explode modes:** all, stages (casing sections), stage-anatomy, balance, seal, bearing, coupling, motor.
- **X-ray sets:** housings, stage-internals, rotor (invert).
- **Sections:** axial, horizontal, radial (through stage 2).
- **Camera presets:** 13, including stage-1-close, stage-section and balance-close.
- **Overlays:**
  - `flow`: schematic paths with a blue-to-red colour per stage (qualitative pressure), the last-stage path per N, and the leak-off path.
  - `thrust`: impeller thrust vs. balance force.
- **Sequences:** `working-principle` (8 steps, uses the flow overlay); `dismantle-N` and `assemble-N` for each stage count.

## Content
- `content/components.ts`: a record for every part.
  - Stage parts are generated from templates.
  - Generic coupling, motor, bearing and seal-face records are reused from the HSC adapter, without its keyConcepts.
  - A test makes sure no split-case wording leaks through.
- `content/extended.ts` covers:
  - why multistage, and pressure progression
  - 11 advanced topics
  - materials: families, a component table, and clean water / boiler feedwater / chemical services
  - 12 formulas with worked examples
  - 9 maintenance tasks, 12 failure cases and 6 standards
  - 24 quiz questions (8 beginner, 8 intermediate, 8 advanced)
  - 8 narrated 3D video lessons. `videoUrl` stays null until recorded or licensed videos exist.
- `content/curves.ts`: ILLUSTRATIVE 4-stage curves. `EquipmentContent.engineering` holds the example inputs (4 stages, 2950 rpm, 60 m3/h, 280 m).

## Commands (in the worktree C:\dev\el-multistage)
- Harness: `/src/equipment/pumps/horizontal-multistage/dev/harness.html?stages=4&balance=drum&view=iso&explode=stage-anatomy&section=axial&flow=1&forces=1&seq=working-principle&step=3`
- Node check: `npx tsx src/equipment/pumps/horizontal-multistage/dev/check.ts`
- GLBs: `npm run models:build -- --only horizontal-multistage` (set `DEV_SERVER` to this worktree's dev server for the thumbnail).
- JSON export: `npx tsx src/equipment/pumps/horizontal-multistage/dev/export-json.ts <dir>`
- Tests: `npx vitest run src/equipment/pumps/horizontal-multistage`
