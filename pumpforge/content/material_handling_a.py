"""Learning content — Material Handling & Heavy Machinery, part A (EQ-196 … EQ-209): feeders, screens, crushers."""
from pumpforge.learning import mod, step, P, F, Q, M

MODULES = {}


def mh(size, power, speed, capacity, **extra):
    """Required parameters for the material_handling family: size, power_rating, speed, capacity."""
    ref = {'manufacturer': None, 'model': None, 'datasheet': None,
           'rated_point': {'capacity': None, 'material_and_bulk_density': None, 'speed': None, 'power_kW': None, 'lump_size_or_load': None},
           'status': 'empty — fill from the selected manufacturer datasheet / duty specification'}
    return dict(size=size, power_rating=power, speed=speed, capacity=capacity, reference_model=ref, extra=extra)


def _maint(routine, periodic, overhaul, lub):
    return dict(routine=routine, periodic=periodic, overhaul=overhaul, lubrication=lub)


_FEED_INST = dict(
    foundation=['Support on steelwork or a concrete plinth designed for the hopper/bin load on the feeder plus impact and dynamic loads.',
                'Isolate vibrating machines from the structure with their springs/rubber mounts — never weld or rigidly bolt the vibrating body to the structure.'],
    alignment=['Set the feeder at the designed slope and centre it under the hopper outlet; set skirt boards and the hopper gate to the design bed depth.',
               'Align drive and driven shafts (laser or dial gauge) or set the exciter motors as the maker specifies.'],
    piping=['Chutes and skirts: allow a gap that widens in the direction of travel so material does not jam; fit dust seals and connect dust extraction where required.',
            'Leave clear access for liner change and for the hopper shut-off gate.'],
    commissioning=['Run empty first: check direction, amplitude/speed, temperatures and noise.',
                   'Load gradually, check the material bed is even and the discharge rate matches the set-point; record motor current as a baseline.'])
_SCREEN_INST = dict(
    foundation=['Mount on a structure stiff enough that its natural frequencies are well away from the screen running speed (resonance check by the structural engineer).'],
    alignment=['Set the screen to the design inclination and level it side-to-side so material spreads across the full width.',
               'Check spring heights are equal; tension the screen media evenly (side-tensioned cloths) or bolt modular panels correctly.'],
    piping=['Feed box/chute should spread the feed across the full width and drop it with low velocity; fit flexible dust seals between the vibrating body and fixed chutes.',
            'Provide spray water headers for wet screening where needed.'],
    commissioning=['Run empty and measure stroke/amplitude and stroke angle (stroke card) at all four corners; check for rocking.',
                   'Check direction of rotation, bearing temperatures and the time to stop through resonance.'])
_CRUSH_INST = dict(
    foundation=['Mount on a massive reinforced-concrete foundation or steel structure designed for the crusher\'s dynamic loads (maker\'s load data); use anti-vibration mounts where specified.',
                'Allow crane access and lay-down space for liner and wear-part changes.'],
    alignment=['Align motor and crusher sheaves or coupling; set V-belt tension to the maker\'s figure.',
               'Set the closed-side setting (CSS) or gap with the maker\'s gauge/lead-ball method.'],
    piping=['Feed with a controlled feeder (choke or regulated feed as designed); avoid segregated or one-sided feed.',
            'Fit a tramp-metal magnet or metal detector ahead of the crusher and dust extraction at transfer points.',
            'Lubrication system: connect oil supply/return, cooler and filter; check flow and pressure switches.'],
    commissioning=['Check lubrication flows and temperatures before starting; run empty to check direction, vibration and current.',
                   'Introduce feed gradually; measure product size and adjust the setting; record power draw as a baseline.'])

_GREASE = ['Bearings: grease or oil to the maker\'s schedule and quantity — do not over-grease vibrating-machine bearings (heat).']

# ===================================================================== feeders
MODULES['apron_feeder'] = mod(
    definition=('An apron feeder is a heavy-duty feeder that draws material out from under a hopper or bin. Overlapping steel pans are bolted to two strands of crawler-type chain. '
                'The chains run around a head (drive) sprocket and a tail sprocket. The pans carry the material forward at low speed and drop it off the head end. '
                'It is built to take large lumps and the impact of material dumped from trucks.'),
    applications=['Primary feeding of run-of-mine ore from a dump hopper to a primary crusher', 'Withdrawing coal, limestone and ore from stockpile tunnels', 'Feeding sticky or wet material that would hang on a vibrating feeder', 'Reclaim from large bins'],
    key_points=['Handles large lumps and high impact', 'Low speed — feed rate set by bed depth × width × speed', 'Variable-speed drive controls the feed rate', 'Pans and chains are the main wear items'],
    principle=[step('Material from the hopper sits on the overlapping pans.', 'hopper', overlay='flow'),
               step('The drive turns the head sprocket and shaft, pulling the chain and pans forward.', 'head_shaft'),
               step('The pans carry a bed of material under the hopper skirts at low speed.', 'pans', overlay='flow'),
               step('At the head end material falls off into the crusher or chute; the empty pans return underneath around the tail sprocket.', 'tail_shaft')],
    curve='Feed rate ∝ belt speed for a fixed bed depth (Q = 3600 · B · h · v · ρ · fill factor, t/h with B, h, v in m and m/s, ρ in t/m³).',
    params=mh(P('Pan width ~ 0.9 – 3 m; length 3 – 30 m'), P('~ 10 – 200+', 'kW'), P('~ 0.05 – 0.4', 'm/s', 'low speed to limit wear'), P('~ 50 – 10 000+', 't/h')),
    install=_FEED_INST,
    maint=_maint([M('Check for spillage, pan damage and chain tracking.', 'pans', 'daily'), M('Check drive temperature and oil level.', 'drive', 'daily')],
                 [M('Measure chain/roller wear and pan gaps; adjust chain tension at the tail.', 'tail_shaft', 'monthly'), M('Inspect skirt liners and hopper wear liners.', 'hopper', 'quarterly')],
                 [M('Replace worn pans, chain links, rollers and sprockets as a set where pitch has grown.', 'head_shaft')],
                 ['Gear reducer: oil to grade and change interval.', 'Chain rollers and shaft bearings: grease to schedule (sealed-for-life rollers need none).']),
    failures=[F('Chain or pan breakage', ['Sudden stop, broken pans, spillage'], ['Large lumps dropped from height without a rock box', 'Worn chain pitch, loose bolts'], ['Keep a material cushion in the hopper', 'Replace worn chain; torque bolts'], 'pans'),
              F('Excessive spillage', ['Material on the floor under the feeder'], ['Skirt gap or liners worn', 'Bed depth too high for the skirts'], ['Re-set skirts/liners', 'Reduce gate height'], 'hopper'),
              F('Drive overload', ['High current, trips'], ['Packed material, frozen or sticky feed', 'Too deep a bed'], ['Clear build-up; reduce bed depth; check VSD settings'], 'drive')],
    quiz=[Q('Why is an apron feeder chosen for primary crusher feed?', ['It is the cheapest feeder', 'It takes large lumps and high impact loads', 'It screens out fines', 'It runs at very high speed'], 1, 'Heavy pans on crawler chains withstand impact.'),
          Q('Feed rate of an apron feeder is mainly controlled by…', ['Hopper height', 'Pan speed (VSD) and bed depth', 'Pan colour', 'Tail sprocket diameter only'], 1, 'Q ∝ B·h·v.'),
          Q('Why do apron feeders run slowly?', ['To reduce wear and spillage', 'To increase noise', 'Because chains cannot turn faster', 'To heat the material'], 0, 'Low speed limits wear and impact.')],
    selection=['Size the width for about 2–3 × the maximum lump size and the bed depth for the required rate at a moderate speed.',
               'Check the hopper load on the pans (draw-down vs static load) — it sets drive power.'],
    safety=['Lock out and block the pans before working under a loaded hopper — stored material can drive the pans.', 'Never clear blockages with the feeder running.'],
    refs=['CEMA — Bulk material handling practice', 'Manufacturer apron feeder design guides'])

_VIB_FAIL = [F('Uneven or reduced feed', ['Feed rate drops, material builds up'], ['Sticky material', 'Lost amplitude (exciter fault, loose weights)', 'Springs broken'], ['Clean liners; check eccentric weights and spring condition'], 'exciters'),
             F('Cracks in tray or body', ['Visible cracks near stiffeners'], ['Fatigue from long running at high amplitude', 'Resonance'], ['Repair to maker\'s procedure; check amplitude and isolators'], 'tray')]

MODULES['vibrating_feeder'] = mod(
    definition=('A vibrating feeder moves bulk material along a tray by vibration. Two unbalanced (exciter) motors turn in opposite directions; their forces cancel sideways and add in one '
                'direction, so the tray moves along a straight line at an angle. Each stroke throws the particles slightly up and forward, so the material "hops" along. '
                'Springs isolate the vibrating tray from the hopper support.'),
    applications=['Feeding crushers, screens and conveyors from hoppers', 'Controlled feeding of aggregates, coal, ore, food products', 'Batching and dosing (variable frequency)'],
    key_points=['Linear motion from twin counter-rotating exciters', 'Feed rate set by amplitude and frequency (VFD)', 'Springs isolate vibration', 'No moving parts in contact with material except the liner'],
    principle=[step('Material from the hopper rests on the tray.', 'hopper', overlay='flow'), step('The counter-rotating exciters create a straight-line vibration at about 30° to the tray.', 'exciters'),
               step('Each stroke throws particles up and forward, so they progress along the tray.', 'tray', overlay='flow'),
               step('Coil springs isolate the tray from the support so little vibration reaches the structure.', 'springs')],
    curve='Feed rate rises with amplitude and frequency until particles leave the tray (throw number); most feeders run below that point for control.',
    params=mh(P('Tray width ~ 0.3 – 2.5 m'), P('~ 0.2 – 30 (exciter motors)', 'kW'), P('~ 750 – 1500 rpm exciters (~ 12 – 25 Hz)', 'rpm'), P('~ 5 – 2000', 't/h')),
    install=_FEED_INST,
    maint=_maint([M('Check feed, noise and that the tray is free (no contact with chutes).', 'tray', 'daily')], [M('Inspect springs and liners; check exciter bolts and weight settings.', 'springs', 'monthly')],
                 [M('Replace exciter bearings, liners and springs as needed.', 'exciters')], _GREASE),
    failures=_VIB_FAIL,
    quiz=[Q('How do two counter-rotating exciters produce straight-line vibration?', ['Their forces add in all directions', 'Sideways components cancel, components along one line add', 'They spin at different speeds', 'They are magnetic'], 1, 'Opposite rotation cancels the cross-components.'),
          Q('What do the springs do?', ['Push the material', 'Isolate vibration from the structure', 'Heat the tray', 'Measure weight'], 1, 'Vibration isolation.'),
          Q('How is feed rate commonly adjusted?', ['Change hopper colour', 'Vary frequency (VFD) or exciter weight setting', 'Change spring colour', 'Tilt the motor'], 1, 'Amplitude and frequency set the rate.')],
    selection=['Size the tray width and length for the required rate and the hopper opening; select exciters for the vibrating mass and the head load from the hopper.'],
    safety=['Lock out exciter motors; beware stored energy in springs and hanging material in the hopper.'],
    refs=['Manufacturer vibrating feeder data', 'CEMA — Bulk material handling practice'])

MODULES['grizzly_feeder'] = mod(
    definition=('A vibrating grizzly feeder is a vibrating feeder with a section of parallel bars (the grizzly) at its discharge end. As the material is fed forward, the fines fall through the '
                'gaps between the bars and bypass the crusher, while the oversize continues to the crusher. This scalps the feed and reduces crusher load and wear.'),
    applications=['Primary crusher feed in quarries and mines', 'Scalping of run-of-mine material', 'Removing soil and fines before crushing'],
    key_points=['Feeds and scalps in one machine', 'Bar gap sets the scalping size', 'Bars usually tapered to stop pegging', 'Fines bypass to save crusher capacity'],
    principle=[step('Material from the hopper is fed onto the vibrating pan.', 'hopper', overlay='flow'), step('The exciters move the material forward onto the grizzly bars.', 'exciters'),
               step('Fines fall through the bar gaps into the bypass chute.', 'bypass_chute', overlay='flow'), step('Oversize travels over the bars into the crusher.', 'tray')],
    curve='Scalping efficiency falls with feed rate and bed depth; gap selected so the crusher receives only material it needs to break.',
    params=mh(P('Width ~ 0.8 – 2 m; bar gap ~ 50 – 200 mm'), P('~ 10 – 75', 'kW'), P('~ 750 – 1000 rpm exciters', 'rpm'), P('~ 100 – 2000+', 't/h')),
    install=_FEED_INST,
    maint=_maint([M('Check for pegged or blocked bar gaps.', 'tray', 'daily')], [M('Measure bar wear and gap; inspect springs.', 'springs', 'monthly')],
                 [M('Replace grizzly bars and pan liners.', 'tray')], _GREASE),
    failures=_VIB_FAIL + [F('Pegging/blinding of bars', ['Fines carried to the crusher'], ['Near-size lumps wedged between bars'], ['Use tapered/stepped bars; clear regularly'], 'tray')],
    quiz=[Q('Why scalp before the primary crusher?', ['To add fines', 'To bypass material already smaller than the crusher setting', 'To heat the rock', 'To slow the feed'], 1, 'Saves capacity and wear.'),
          Q('What sets the scalping size?', ['Bar gap', 'Motor colour', 'Spring length', 'Hopper height'], 0, 'Gap between bars.'),
          Q('Why are grizzly bars often tapered?', ['To look better', 'To open the gap downwards so near-size pieces do not wedge', 'To make them lighter only', 'To reduce noise'], 1, 'Prevents pegging.')],
    selection=['Choose bar gap close to the crusher closed-side setting; allow open area and length for the required scalping efficiency.'],
    safety=['Never stand on or clear the grizzly while running; lock out and secure the hopper load.'],
    refs=['Manufacturer grizzly feeder data'])

MODULES['rotary_airlock_feeder'] = mod(
    definition=('A rotary airlock (rotary valve) feeder has a rotor with pockets turning in a close-fitting housing. Powder enters the top pockets, is carried round and drops out at the bottom. '
                'Because the vane tips seal against the housing, it meters the solids while limiting air leakage between two zones at different pressure — for example a hopper and a pneumatic conveying line.'),
    applications=['Feeding pneumatic conveying lines', 'Discharging dust collectors and cyclones', 'Metering powders from silos (cement, flour, plastics, fly ash)', 'Explosion isolation (certified designs)'],
    key_points=['Volumetric — rate ∝ rotor speed × pocket volume × fill', 'Seals pressure difference by tight tip clearance', 'Leakage air rises with clearance and ΔP', 'Speed kept moderate so pockets fill'],
    principle=[step('Powder from above falls into the open rotor pockets.', 'connections', overlay='flow'), step('The drive turns the rotor; full pockets are carried round inside the housing.', 'rotor'),
               step('Close vane-tip and side clearances limit air leakage from the high-pressure side.', 'housing'),
               step('At the bottom the pockets empty into the outlet or conveying line.', 'powder', overlay='flow')],
    curve='Throughput rises linearly with speed, then falls off as pockets no longer fill completely (fill efficiency drops at high tip speed).',
    params=mh(P('~ 150 – 600 mm inlet'), P('~ 0.37 – 11', 'kW'), P('~ 5 – 30', 'rpm', 'typical'), P('~ 0.1 – 100', 'm³/h')),
    install=_FEED_INST | dict(piping=['Fit a vent on the inlet side of airlocks feeding pressure lines so leakage air does not fluidise or block the incoming powder.',
                                      'Bolt flanges without distorting the housing (clearances are small).']),
    maint=_maint([M('Watch for falling throughput, noise and leakage.', 'rotor', 'daily')], [M('Check tip/side clearances with feeler gauges.', 'housing', 'quarterly')],
                 [M('Rebuild rotor (re-tip) and housing; replace shaft seals and bearings.', 'rotor')], ['Drive gearbox and chain: oil/grease to schedule; end-plate bearings greased.']),
    failures=[F('Excessive air leakage', ['Reduced capacity, powder bridging above valve'], ['Worn tips/housing', 'Higher ΔP'], ['Restore clearances; fit vent; consider adjustable tips'], 'housing'),
              F('Rotor jam', ['Motor trip, shear pin broken'], ['Foreign object, thermal expansion with hot product'], ['Remove debris; use hot-clearance rotor'], 'rotor')],
    quiz=[Q('What two jobs does a rotary airlock do?', ['Heats and cools powder', 'Meters solids and limits air leakage', 'Grinds and screens', 'Weighs and labels'], 1, 'Feeding and sealing.'),
          Q('What happens to leakage as the clearance wears?', ['Falls', 'Rises', 'Stays the same', 'Becomes zero'], 1, 'Larger gap → more air.'),
          Q('Why not run the rotor very fast?', ['Pockets do not fill completely so throughput stops rising', 'It becomes silent', 'It makes the powder heavier', 'Seals improve'], 0, 'Fill efficiency drops.')],
    selection=['Size pocket volume and speed for rate at about 60–80 % fill; select clearances, materials and seals for temperature, abrasion and ΔP.'],
    safety=['Never put fingers in the inlet or outlet — the rotor shears like a guillotine. Lock out before inspection.', 'Use certified flameproof designs for combustible dust zones.'],
    refs=['Manufacturer rotary valve data', 'Pneumatic conveying design guides'])

MODULES['screw_feeder'] = mod(
    definition=('A screw feeder meters bulk solids with a rotating helical screw in a trough or tube under a hopper. The screw flights move material forward like a nut on a thread. '
                'Its flights, pitch or shaft diameter usually vary along the inlet so material is drawn evenly from the whole hopper outlet, not just the back.'),
    applications=['Metering powders and granules (cement, lime, flour, chemicals)', 'Feeding mixers, kilns and dryers', 'Withdrawing from bins and bag dump stations'],
    key_points=['Volumetric feeding — rate ∝ speed', 'Variable pitch/diameter gives even draw-down', 'Totally enclosed and dust-tight', 'Run full (100 %) under the hopper'],
    principle=[step('Material from the inlet hopper fills the screw flights.', 'inlet_hopper', overlay='flow'), step('The motor and coupling turn the screw.', 'coupling'),
               step('Rotating flights push the material along the trough.', 'screw', overlay='flow'), step('Material drops out at the discharge end.', 'trough')],
    curve='Q = 60 · (π/4)(D² − d²) · p · n · φ · ρ (t/h) — linear with speed n; φ = fill (≈1 under the hopper).',
    params=mh(P('Screw ~ 100 – 600 mm diameter'), P('~ 0.5 – 50', 'kW'), P('~ 10 – 150', 'rpm'), P('~ 0.1 – 200', 'm³/h')),
    install=_FEED_INST,
    maint=_maint([M('Check discharge rate, noise and seal leakage.', 'trough', 'daily')], [M('Check flight wear and coupling condition.', 'screw', 'quarterly')],
                 [M('Replace screw/hanger bearings and liners.', 'screw')], ['End bearings and gearmotor: lubricate to schedule.']),
    failures=[F('Flooding of fluid powders', ['Rate higher than expected, product flushes through'], ['Aerated powder'], ['Use shorter pitch, longer choke section or rotary valve'], 'screw'),
              F('Overload/jamming', ['High current'], ['Lumps, compaction under hopper'], ['Check hopper design; use larger screw/lump breaker'], 'screw')],
    quiz=[Q('Why does a screw feeder often use variable pitch?', ['Decoration', 'To draw material from the whole hopper outlet evenly', 'To increase noise', 'To make it lighter'], 1, 'Prevents dead zones.'),
          Q('Throughput of a screw feeder is roughly…', ['Proportional to speed', 'Independent of speed', 'Inversely proportional to speed', 'Set by motor colour'], 0, 'Volumetric device.'),
          Q('A screw feeder normally runs…', ['Empty', 'Full under the hopper', 'At 10 % fill', 'Vertically only'], 1, 'Unlike a screw conveyor which runs part-full.')],
    selection=['Choose diameter for lump size and rate at a moderate speed; use a variable-pitch screw for even draw-down.'],
    safety=['Guard the inlet — screws can draw in hands and clothing. Lock out before opening covers.'],
    refs=['CEMA 350 — Screw conveyors', 'Manufacturer screw feeder data'])

MODULES['weigh_feeder'] = mod(
    definition=('A weigh feeder (gravimetric belt feeder) is a short belt conveyor that measures and controls the mass flow of material. Load cells under a weigh idler measure the belt load per metre; '
                'a speed sensor measures belt speed. The controller multiplies the two to get the flow rate (kg/s) and adjusts belt speed to hold the set-point.'),
    applications=['Feeding raw meal, coal and additives to kilns and mills', 'Blending in cement, minerals and chemicals', 'Proportioning ingredients in food and plastics processes'],
    key_points=['Rate = belt load (kg/m) × belt speed (m/s)', 'Closed-loop control via VSD', 'Typical accuracy about ±0.5 – 1 % (well installed)', 'Needs regular zero and span calibration'],
    principle=[step('Material from the inlet chute forms a bed on the belt.', 'inlet', overlay='flow'), step('Load cells under the weigh idler measure the belt load.', 'weigh_idler'),
               step('A speed sensor on the tail pulley measures belt speed.', 'speed_sensor'),
               step('The controller computes rate = load × speed and trims the drive speed to hold the set-point.', 'controller')],
    curve='Accuracy is best between about 20–100 % of rated capacity; at very low belt loads zero errors dominate.',
    params=mh(P('Belt width ~ 0.3 – 1.6 m; centres ~ 1.5 – 5 m'), P('~ 0.37 – 15', 'kW'), P('~ 0.02 – 0.5', 'm/s'), P('~ 0.1 – 1000', 't/h')),
    install=_FEED_INST | dict(alignment=['Install the weigh idler and approach idlers in line (laser) — misalignment causes belt-tension errors.', 'Protect the weigh section from wind, dust build-up and skirt friction.']),
    maint=_maint([M('Clean the belt and weigh area; check belt tracking.', 'bfbelt', 'daily')], [M('Zero calibration and test-weight span check.', 'weigh_idler', 'weekly/monthly')],
                 [M('Material (drop) test against a reference scale; replace belt and idlers.', 'controller')], ['Pulley bearings and gearmotor: lubricate to schedule.']),
    failures=[F('Weighing drift', ['Rate disagrees with stock reconciliation'], ['Build-up on weigh idler, belt tension change, wind'], ['Clean, re-zero, re-span; enclose'], 'weigh_idler'),
              F('Belt mistracking', ['Belt runs off, edge wear'], ['Pulley misalignment, material build-up'], ['Re-align, clean pulleys'], 'bfbelt')],
    quiz=[Q('How does a weigh feeder calculate flow rate?', ['Motor current only', 'Belt load per metre × belt speed', 'Pulley diameter × voltage', 'Hopper level × time'], 1, 'Load × speed.'),
          Q('What is the purpose of the speed sensor?', ['To weigh the belt', 'To measure belt speed for the rate calculation', 'To stop the belt', 'To heat the belt'], 1, 'Speed term.'),
          Q('Why is zero calibration needed?', ['To remove the empty-belt weight and its changes', 'To make the belt faster', 'To change the set-point', 'It is not needed'], 0, 'Tare drifts with belt build-up and tension.')],
    selection=['Choose belt width and speed so the design rate falls in the mid-range of the weighing capacity; specify accuracy and turndown.'],
    safety=['Lock out before cleaning; use guards at pulleys (nip points).'],
    refs=['OIML R 50 — Continuous totalizing automatic weighing instruments (belt weighers)', 'Manufacturer weigh feeder data'])

# ===================================================================== screens
MODULES['vibrating_screen'] = mod(
    definition=('A vibrating screen separates particles by size. An inclined deck (or decks) of wire mesh, polyurethane or perforated plate vibrates in a circular motion produced by an exciter shaft. '
                'Particles smaller than the openings pass through; larger ones travel over the deck and leave at the discharge end. Multi-deck screens make several products at once.'),
    applications=['Sizing crushed rock and aggregates', 'Sizing coal and ore after crushing', 'Dewatering and desliming', 'Recycling and sand/gravel plants'],
    key_points=['Inclined (≈15–25°) circular-motion screen', 'Each deck gives one cut size', 'Efficiency falls with overload or blinding', 'Springs isolate the vibrating body'],
    principle=[step('Feed enters the top of the inclined deck through the feed chute.', 'chutes', overlay='flow'), step('The exciter shaft with unbalanced weights makes the body vibrate in a circle.', 'exciter'),
               step('Particles are thrown and stratify; fines pass through the openings of each deck.', 'screen_body', overlay='flow'),
               step('Oversize leaves over the top deck, middlings over the lower deck, fines through the bottom.', 'oversize')],
    curve='Screening efficiency vs feed rate: high at moderate loads, falling as bed depth grows; near-size particles are hardest to pass.',
    params=mh(P('Deck ~ 1.2 × 3.6 m up to ~ 3.6 × 9.8 m; 1 – 3 decks'), P('~ 7.5 – 75', 'kW'), P('~ 750 – 1000 rpm (stroke ~ 6 – 10 mm)', 'rpm'), P('~ 50 – 3000+', 't/h')),
    install=_SCREEN_INST,
    maint=_maint([M('Check media for holes and blinding; check feed distribution.', 'screen_body', 'daily')], [M('Measure stroke; check springs and bolts; check bearing temperatures.', 'springs', 'weekly')],
                 [M('Replace screen media, side liners and exciter bearings.', 'exciter')], ['Exciter bearings: oil/grease to maker\'s schedule (critical — high speed, high load).']),
    failures=[F('Blinding/pegging', ['Fines in oversize, falling capacity'], ['Wet or near-size material'], ['Use anti-blinding media, sprays, change opening shape'], 'screen_body'),
              F('Torn media', ['Oversize in fines product'], ['Impact at feed point, wear, poor tension'], ['Replace; fit impact plates; tension correctly'], 'screen_body'),
              F('Bearing failure', ['High temperature, noise'], ['Lubrication fault, contamination'], ['Replace; correct lubrication'], 'exciter')],
    quiz=[Q('What does each screen deck produce?', ['One cut size between two products', 'Heat', 'Air flow', 'Electricity'], 0, 'One separation per deck.'),
          Q('What is "blinding"?', ['Openings blocked by particles', 'Excess light', 'Motor stopping', 'Spring breaking'], 0, 'Blocked apertures.'),
          Q('Why are inclined screens used?', ['Gravity helps move material while vibration stratifies it', 'They are quieter', 'They need no motor', 'They weigh more'], 0, 'Slope + vibration.')],
    selection=['Size the deck area from capacity per unit area for each opening, corrected for moisture, near-size and deck position (VSMA/maker method).'],
    safety=['Lock out before media change; beware of the body moving on springs during start/stop (resonance).'],
    refs=['VSMA Handbook (screen sizing method)', 'Manufacturer screen data'])

MODULES['trommel_screen'] = mod(
    definition=('A trommel is a rotating cylindrical or slightly conical screen. Material fed at the higher end tumbles inside the slowly turning drum; fines pass through the perforated shell and '
                'oversize leaves at the far end. The tumbling action breaks up lumps and frees fines, which makes trommels good for sticky or wet material.'),
    applications=['Compost, municipal waste and recycling', 'Topsoil and sand/gravel', 'Gold and alluvial mining (scrubbing)', 'Coal and ore desliming'],
    key_points=['Rotates at about 30–40 % of critical speed', 'Critical speed n_c ≈ 42.3 / √D (rpm, D in m)', 'Tumbling scrubs sticky material', 'Low vibration, robust'],
    principle=[step('Feed enters the drum through the feed chute.', 'feed_chute', overlay='flow'), step('The drive turns the drum on its trunnion rollers.', 'trunnions'),
               step('Material tumbles and fines fall through the perforations into the hood/hopper.', 'drum', overlay='flow'), step('Oversize discharges at the end of the drum.', 'oversize')],
    curve='Screening improves with retention time (length, slope, speed) up to a point; above about 50–60 % of critical speed material centrifuges and screening stops.',
    params=mh(P('Drum ~ 1 – 3.5 m diameter, 3 – 15 m long'), P('~ 5 – 75', 'kW'), P('~ 5 – 25', 'rpm', '30–40 % of critical speed'), P('~ 10 – 500', 't/h')),
    install=_SCREEN_INST | dict(alignment=['Set the drum slope (typically a few degrees) and align trunnion rollers so the drum runs without axial thrust.']),
    maint=_maint([M('Check for blinded holes and spillage.', 'drum', 'daily')], [M('Check trunnion wheels, tyres and drive.', 'trunnions', 'monthly')],
                 [M('Replace screen panels and trunnion wheels.', 'drum')], ['Trunnion and drive bearings greased; gearbox oil to schedule.']),
    failures=[F('Blinded apertures', ['Fines in oversize'], ['Wet clayey material, fibres wrapping'], ['Brush cleaners, sprays, larger holes'], 'drum'),
              F('Drum wander/thrust', ['Drum moves axially, wear on thrust rollers'], ['Trunnion misalignment'], ['Re-align rollers'], 'trunnions')],
    quiz=[Q('Why does a trommel run well below its critical speed?', ['So material tumbles instead of sticking to the shell', 'To save paint', 'To create air flow', 'To increase vibration'], 0, 'At critical speed material centrifuges.'),
          Q('Critical speed of a 2 m drum is about…', ['30 rpm', '300 rpm', '3 rpm', '3000 rpm'], 0, '42.3/√2 ≈ 30 rpm.'),
          Q('An advantage of trommels is…', ['They scrub sticky material', 'They need no drive', 'They are vibrating', 'They have no openings'], 0, 'Tumbling action.')],
    selection=['Select diameter and length for retention time; speed ~ 30–40 % of critical; hole size per product cut.'],
    safety=['Guard trunnion and drive nips; lock out before entering the drum (confined space).'],
    refs=['Manufacturer trommel data'])

# ===================================================================== crushers
MODULES['jaw_crusher'] = mod(
    definition=('A jaw crusher breaks rock by compression between a fixed jaw and a moving (swing) jaw. In the single-toggle design the swing jaw hangs on an eccentric shaft at the top and is '
                'supported at the bottom by a toggle plate. As the shaft turns, the jaw moves towards and away from the fixed jaw with an elliptical motion. Rock is nipped, crushed and moves '
                'down the V-shaped chamber until it is small enough to pass the closed-side setting (CSS) at the bottom.'),
    applications=['Primary crushing of hard rock, ore and recycled concrete', 'Quarry and mining primary stations', 'Mobile crushing plants'],
    key_points=['Compression crushing in a V-shaped chamber', 'Product size set by the closed-side setting (CSS)', 'Reduction ratio typically about 6–8 : 1', 'Toggle plate acts as a safety element'],
    principle=[step('Rock enters the top of the chamber between the jaws.', 'fixed_jaw', overlay='flow'),
               step('The eccentric shaft and flywheels drive the swing jaw towards and away from the fixed jaw.', 'eccentric_flywheels'),
               step('The swing jaw squeezes the rock against the fixed jaw; broken pieces fall lower each stroke.', 'swing_jaw', overlay='wear'),
               step('The toggle plate supports the bottom of the jaw and sets the closed-side setting.', 'toggle_plate'),
               step('Product leaves through the gap at the bottom.', 'product', overlay='flow')],
    curve='Capacity rises with CSS and speed (up to an optimum); product gradation becomes finer with smaller CSS.',
    params=mh(P('Feed opening ~ 0.4 × 0.6 m to 1.6 × 2.0 m'), P('~ 30 – 400', 'kW'), P('~ 200 – 350', 'rpm', 'eccentric shaft'), P('~ 50 – 1500+', 't/h')),
    install=_CRUSH_INST,
    maint=_maint([M('Check for bridging, unusual noise and oil/grease temperatures.', 'frame', 'daily')], [M('Measure CSS and jaw-die wear; re-set the setting.', 'fixed_jaw', 'weekly')],
                 [M('Turn or replace jaw dies; replace toggle plate and seats; replace eccentric bearings.', 'swing_jaw')],
                 ['Eccentric shaft bearings: grease or circulating oil to the maker\'s schedule.']),
    failures=[F('Toggle plate breakage', ['Crusher stops crushing, jaw hangs back'], ['Uncrushable tramp metal (designed safety failure), fatigue'], ['Remove tramp; replace toggle; improve tramp removal'], 'toggle_plate'),
              F('Product too coarse', ['Oversize in product'], ['Worn dies, CSS opened'], ['Re-set CSS; turn/replace dies'], 'fixed_jaw'),
              F('Bearing overheating', ['High temperature'], ['Lubrication fault, overload'], ['Correct lubrication; check feed'], 'eccentric_flywheels')],
    quiz=[Q('What sets the product size of a jaw crusher?', ['Feed opening', 'Closed-side setting (CSS)', 'Flywheel colour', 'Motor voltage'], 1, 'Smallest gap at the bottom.'),
          Q('What is the role of the toggle plate?', ['Decoration', 'Supports the jaw and breaks as a safety element on tramp metal', 'Feeds the rock', 'Heats the jaw'], 1, 'Sacrificial safety element.'),
          Q('Why are flywheels fitted?', ['To store energy and smooth the peak crushing loads', 'To cool the crusher', 'To weigh the rock', 'To lift the crusher'], 0, 'Energy storage.'),
          Q('Where do jaw dies wear most?', ['Top', 'Lower part near the discharge', 'Back side', 'They do not wear'], 1, 'Most crushing work occurs near the CSS.')],
    selection=['Feed opening ≥ about 1.2 × the largest lump; check capacity at the required CSS from maker\'s tables.'],
    safety=['Lock out and block the flywheels before entering the chamber; beware of rock falling or being ejected.', 'Never clear a blocked crusher by hand or with the drive running.'],
    refs=['Manufacturer crushing & screening handbooks (e.g. Metso, Sandvik)', 'MSHA/ISO machinery safety guidance'])

_GYR_MAINT = _maint([M('Check oil flow, pressure and temperature; listen for knocking.', 'eccentric', 'daily')], [M('Measure CSS and liner wear; adjust setting.', 'concaves', 'weekly')],
                    [M('Replace mantle and concaves; inspect eccentric bushing and gears.', 'mantle')], ['Circulating oil system: check filter ΔP, oil analysis, cooler performance.'])
_GYR_FAIL = [F('Liner wear', ['Product coarsening, falling capacity'], ['Normal abrasion, uneven feed'], ['Adjust setting; replace liners; distribute feed evenly'], 'concaves'),
             F('Lubrication failure', ['High oil temperature, low pressure alarm'], ['Pump/filter/cooler fault, contaminated oil'], ['Fix system; never run without oil flow'], 'eccentric'),
             F('Ring bounce / overload', ['Bowl lifts, loud bangs'], ['Tramp metal, packing, too small setting'], ['Remove tramp; increase setting; regulate feed'], 'shell')]

MODULES['cone_crusher'] = mod(
    definition=('A cone crusher crushes rock between a gyrating mantle and a fixed concave (bowl liner). The main shaft sits in an eccentric bushing; as the eccentric turns, the mantle moves '
                'closer to and away from each part of the concave in turn. Rock is squeezed repeatedly as it moves down the chamber and leaves through the closed-side setting.'),
    applications=['Secondary and tertiary crushing of aggregates and ore', 'Producing cubical aggregate', 'Pebble crushing in grinding circuits'],
    key_points=['Continuous compression crushing', 'Product size set by CSS (hydraulic or screw adjustment)', 'Reduction ratio typically about 3–6 : 1 per stage', 'Choke feeding gives best shape'],
    principle=[step('Feed enters the top and falls into the chamber.', 'shell', overlay='flow'), step('The pinion drives the eccentric; the eccentric makes the mantle gyrate.', 'pinion_shaft'),
               step('The mantle approaches each part of the concave in turn, squeezing the rock.', 'mantle', overlay='wear'),
               step('Product passes the closed-side setting at the bottom.', 'concaves', overlay='flow')],
    curve='Capacity and product size depend on CSS, eccentric throw and speed; choke-fed chambers give more inter-particle crushing and better shape.',
    params=mh(P('Head diameter ~ 0.9 – 3 m'), P('~ 90 – 1000', 'kW'), P('~ 250 – 450', 'rpm', 'eccentric/countershaft-dependent'), P('~ 50 – 2500', 't/h')),
    install=_CRUSH_INST, maint=_GYR_MAINT, failures=_GYR_FAIL,
    quiz=[Q('What makes the mantle gyrate?', ['A hydraulic cylinder', 'The rotating eccentric bushing', 'Gravity', 'A belt on the mantle'], 1, 'Eccentric drive.'),
          Q('Where does liner wear concentrate?', ['Upper chamber', 'Lower (parallel) zone near the CSS', 'Outside the bowl', 'Nowhere'], 1, 'Highest forces there.'),
          Q('"Choke feeding" means…', ['Keeping the chamber full of feed', 'Starving the crusher', 'Feeding water only', 'Feeding from one side'], 0, 'Full chamber improves shape.')],
    selection=['Pick chamber profile (coarse/medium/fine) for feed size and required product; check capacity at the CSS from maker\'s tables.'],
    safety=['Lock out; release hydraulic clearing/clamping pressure before maintenance; use proper lifting tools for mantle/bowl.'],
    refs=['Manufacturer crushing handbooks'])

MODULES['gyratory_crusher'] = mod(
    definition=('A gyratory crusher is a large primary crusher with a long, steep crushing chamber. The main shaft, carrying the mantle, hangs from a spider at the top and is gyrated at the bottom '
                'by an eccentric. Large rocks are crushed between the mantle and the concaves lining the shell. It accepts direct truck dumping and has very high capacity.'),
    applications=['Primary crushing in large mines and quarries', 'High-tonnage copper, iron ore and gold operations'],
    key_points=['Very high capacity (thousands of t/h)', 'Continuous crushing on all sides of the head', 'Shaft supported by the top spider', 'Hydraulic adjustment of setting (many designs)'],
    principle=[step('Run-of-mine rock is dumped into the top of the shell.', 'shell', overlay='flow'), step('The spider supports the top of the main shaft.', 'spider'),
               step('The eccentric at the bottom gyrates the mantle.', 'eccentric'), step('Rock is crushed against the concaves and passes the open/closed setting at the bottom.', 'concaves', overlay='wear')],
    curve='Capacity rises with open-side setting and throw; product top size ≈ open-side setting.',
    params=mh(P('Feed opening ~ 1.0 – 1.6 m; mantle diameter ~ 1.5 – 3 m'), P('~ 300 – 1200', 'kW'), P('~ 100 – 160', 'rpm', 'eccentric'), P('~ 1000 – 10 000+', 't/h')),
    install=_CRUSH_INST, maint=_GYR_MAINT, failures=_GYR_FAIL,
    quiz=[Q('Where is the gyratory main shaft supported at the top?', ['In the spider', 'On the flywheel', 'In the feed hopper', 'It is not supported'], 0, 'Spider bearing.'),
          Q('Compared with a jaw crusher, a gyratory crusher…', ['Has higher capacity for the same feed opening', 'Has no moving parts', 'Is only for fine crushing', 'Runs on water'], 0, 'Crushes continuously all round.'),
          Q('Why is a large primary gyratory usually truck-fed directly?', ['Its chamber acts as a surge hopper', 'It cannot take feeders', 'Trucks are cheaper', 'It is upside down'], 0, 'Can be choke-fed from trucks.')],
    selection=['Use for primary duties above roughly 1000 t/h where a jaw crusher would need to be very large.'],
    safety=['Lock out; use the maker\'s lifting tools for the main shaft and spider; manage rock-fall risk at the dump pocket.'],
    refs=['Manufacturer crushing handbooks'])

_HSI_INST = _CRUSH_INST
MODULES['impact_crusher'] = mod(
    definition=('A horizontal shaft impact (HSI) crusher breaks material by impact rather than compression. A fast-turning rotor with blow bars strikes the falling feed and throws it against '
                'impact aprons (curtains). Rocks shatter along natural weaknesses, giving a well-shaped (cubical) product. The gap between the rotor and the aprons controls the product size.'),
    applications=['Limestone and softer rock crushing', 'Recycling concrete and asphalt', 'Secondary crushing for cubical aggregate'],
    key_points=['Impact crushing with blow bars', 'High reduction ratio and good shape', 'Apron gap sets product size', 'Best for low-abrasion feed (wear cost)'],
    principle=[step('Feed enters through the inlet into the path of the rotor.', 'housing', overlay='flow'), step('The rotor\'s blow bars hit the material at high tip speed.', 'rotor'),
               step('Particles are thrown against the impact aprons and break again.', 'impact_aprons', overlay='wear'), step('Crushed material leaves at the bottom.', 'rocks', overlay='flow')],
    curve='Finer product with higher rotor speed and smaller apron gap; wear rate rises steeply with abrasiveness and speed.',
    params=mh(P('Rotor ~ 1 – 1.6 m diameter, 1 – 2.5 m wide'), P('~ 100 – 800', 'kW'), P('Rotor tip speed ~ 25 – 50', 'm/s'), P('~ 100 – 1500', 't/h')),
    install=_HSI_INST,
    maint=_maint([M('Check vibration and blow-bar wear through inspection doors.', 'rotor', 'daily')], [M('Measure and adjust apron gaps.', 'impact_aprons', 'weekly')],
                 [M('Turn/replace blow bars (in balanced pairs) and liners; replace bearings.', 'rotor')], ['Rotor bearings: grease/oil to schedule.']),
    failures=[F('Rotor imbalance', ['High vibration'], ['Unequal blow-bar wear or mismatched bars'], ['Replace bars in sets; balance'], 'rotor'),
              F('Product too coarse', ['Oversize'], ['Worn bars/aprons, gap too large'], ['Adjust gap; replace wear parts'], 'impact_aprons')],
    quiz=[Q('An HSI crusher breaks rock mainly by…', ['Compression', 'Impact', 'Attrition only', 'Heating'], 1, 'Blow bars hit the feed.'),
          Q('What sets the product size?', ['Rotor colour', 'Apron gap and rotor speed', 'Feed hopper size', 'Motor voltage'], 1, 'Gap and speed.'),
          Q('Why are HSI crushers less suited to very abrasive rock?', ['Wear costs of blow bars become high', 'They cannot turn', 'They need water', 'They are too slow'], 0, 'Wear cost.')],
    selection=['Use for low-to-medium abrasive feed where shape matters; check silica/abrasion index with the maker.'],
    safety=['Lock out and pin the rotor before opening; flying debris hazard — keep doors closed when running.'],
    refs=['Manufacturer impact crusher data'])

MODULES['hammer_crusher'] = mod(
    definition=('A hammer crusher (hammer mill) has a rotor carrying many pivoted (swing) hammers. At speed the hammers swing out and strike the feed, throwing it against a breaker plate; '
                'the material is then broken further until it is small enough to pass through the grate bars at the bottom. The grate opening controls the top size of the product.'),
    applications=['Coal crushing for power plants and cement kilns', 'Limestone, gypsum and clinker', 'Biomass and recycling'],
    key_points=['Swing hammers fold back on uncrushable objects', 'Grate sets the product top size', 'High reduction ratio in one pass', 'Not for very hard or abrasive rock'],
    principle=[step('Feed enters at the top.', 'housing', overlay='flow'), step('The swing hammers on the rotor strike the falling lumps.', 'rotor'),
               step('Material is thrown against the breaker plate and broken again.', 'grate_breaker', overlay='wear'), step('Crushed product passes the grate bars.', 'rocks', overlay='flow')],
    curve='Throughput falls and fines increase with smaller grate openings; moisture causes grate blinding.',
    params=mh(P('Rotor ~ 0.6 – 2 m diameter'), P('~ 30 – 1000', 'kW'), P('~ 600 – 1500', 'rpm', 'size-dependent'), P('~ 10 – 1500', 't/h')),
    install=_HSI_INST,
    maint=_maint([M('Check vibration and grate blockage.', 'grate_breaker', 'daily')], [M('Inspect hammers and pins for wear; reverse hammers.', 'rotor', 'weekly')],
                 [M('Replace hammers in balanced sets, pins, grate bars and liners.', 'rotor')], ['Rotor bearings: grease/oil to schedule.']),
    failures=[F('Grate blinding', ['Capacity drops, power rises'], ['Wet/sticky feed'], ['Dry feed or use larger openings'], 'grate_breaker'),
              F('Imbalance', ['Vibration'], ['Uneven hammer wear, lost hammer'], ['Replace sets; balance'], 'rotor')],
    quiz=[Q('Why are hammers pivoted (swing)?', ['To fold back when they hit something uncrushable', 'To save weight only', 'For noise', 'They are fixed'], 0, 'Reduces damage from tramp.'),
          Q('What limits product top size in a hammer crusher?', ['Grate bar opening', 'Feed chute length', 'Motor colour', 'Breaker plate colour'], 0, 'Grate.'),
          Q('Hammer sets are replaced in matched weights to…', ['Keep the rotor balanced', 'Look neat', 'Reduce price', 'Increase noise'], 0, 'Balance.')],
    selection=['Check feed hardness/abrasion and moisture; size rotor and grate for the required product and capacity.'],
    safety=['Lock out and block the rotor; flying debris hazard.'],
    refs=['Manufacturer hammer mill data'])

MODULES['roller_crusher'] = mod(
    definition=('A double roll crusher has two rolls turning towards each other. Material is drawn into the gap (nip) between them and crushed by compression and, with toothed rolls, by shearing. '
                'One roll is held by springs so it can move back and let uncrushable objects through. The gap between the rolls sets the product size, and fines are low.'),
    applications=['Coal and coke crushing', 'Secondary crushing of soft-to-medium ores, salt, limestone', 'Producing a product with few fines'],
    key_points=['Compression (and shear) between rolls', 'Gap sets product size', 'Spring relief protects against tramp', 'Low fines; reduction ratio about 3–4 : 1 for smooth rolls'],
    principle=[step('Material from the feed hopper falls onto the rolls.', 'feed_hopper', overlay='flow'), step('The two rolls turn towards each other and nip the lumps.', 'roll_1'),
               step('Lumps are crushed in the gap; the floating roll is held by springs.', 'relief_springs', overlay='wear'), step('Product falls from the bottom of the gap.', 'roll_2', overlay='flow')],
    curve='Nip condition: a lump is gripped only if the nip angle is below twice the friction angle; bigger rolls nip bigger lumps for the same gap.',
    params=mh(P('Roll ~ 0.4 – 1.5 m diameter, 0.3 – 2 m wide'), P('~ 10 – 300', 'kW'), P('~ 50 – 300', 'rpm'), P('~ 10 – 1000', 't/h')),
    install=_CRUSH_INST,
    maint=_maint([M('Check gap, spring tension and roll surface.', 'relief_springs', 'daily')], [M('Measure roll wear across the width.', 'roll_1', 'monthly')],
                 [M('Rebuild teeth/shell and replace bearings.', 'roll_2')], ['Roll bearings and drive gears: lubricate to schedule.']),
    failures=[F('Hollow (uneven) roll wear', ['Gap opens in the centre, product coarse'], ['Feed concentrated at the centre'], ['Spread feed; re-profile rolls'], 'roll_1'),
              F('Spring fatigue', ['Gap opens under load'], ['Fatigue, wrong pre-load'], ['Replace springs, re-set pre-load'], 'relief_springs')],
    quiz=[Q('Why is one roll spring-loaded?', ['To let tramp metal pass without damage', 'To make it spin faster', 'To heat the roll', 'For alignment only'], 0, 'Tramp relief.'),
          Q('What sets product size?', ['Gap between the rolls', 'Hopper volume', 'Spring colour', 'Motor speed only'], 0, 'Gap.'),
          Q('An advantage of roll crushers is…', ['Low fines production', 'Very high reduction ratio', 'No wear', 'No drive needed'], 0, 'Single-pass compression, little re-crushing.')],
    selection=['Choose roll diameter from the largest feed lump and gap (nip condition); toothed rolls for coal and softer material.'],
    safety=['Guard the in-running nip; lock out before clearing; never feed by hand.'],
    refs=['Manufacturer roll crusher data'])
