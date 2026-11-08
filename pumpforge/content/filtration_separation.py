"""Learning content — Filtration & Separation Equipment (EQ-253 … EQ-270)."""
from pumpforge.learning import mod, step, P, F, Q, M

MODULES = {}


def fs(size, capacity, pressure, separation, **extra):
    """Required parameters for the filtration_separation family: size, capacity, operating_pressure, separation_performance."""
    ref = {'manufacturer': None, 'model': None, 'datasheet': None,
           'rated_point': {'flow': None, 'operating_pressure': None, 'cut_size_or_rejection': None, 'feed_solids_or_contaminant': None, 'power_kW': None},
           'status': 'empty — fill from the equipment datasheet / performance guarantee'}
    return dict(size=size, capacity=capacity, operating_pressure=pressure, separation_performance=separation, reference_model=ref, extra=extra)


def _m(r, p, o, l):
    return dict(routine=r, periodic=p, overhaul=o, lubrication=l)


_VI = dict(foundation=['Level foundation/skid for operating (full) weight; access for element/media change and lifting.'],
           alignment=['Vertical vessels plumb; skids level; align pumps/drives.'],
           piping=['Isolation and bypass valves; vents and drains; pressure gauges or ΔP transmitter across the unit; relief protection where the vessel can be over-pressured.'],
           commissioning=['Leak/pressure test; flush lines before installing elements/media; bring flow on gradually; record clean ΔP and performance baseline.'])
_MI = dict(foundation=['Skid or tank on level foundation; room for module removal and CIP equipment.'],
           alignment=['Modules/vessels square and supported without strain on ports.'],
           piping=['Pre-treatment (strainer/cartridge filter) ahead of membranes; sampling points for feed, permeate and concentrate; CIP connections.'],
           commissioning=['Flush preservative; integrity test; start at low flux; set recovery; record normalised flux, ΔP and rejection baseline.'])
_CI = dict(foundation=['Massive foundation or inertia block on anti-vibration mounts designed for dynamic loads (maker data).'],
           alignment=['Level the machine; align motor and belt/coupling; check bowl run-out.'],
           piping=['Flexible connections to feed and outlets so no pipe loads reach the machine; vent the casing.'],
           commissioning=['Check rotation, lubrication and vibration empty; introduce feed gradually; set differential speed/ejection interval; verify interlocks (cover, vibration, speed).'])
_TI = dict(foundation=['Tanks on level foundations; access walkways for inspection and skimmer maintenance.'],
           alignment=['Weirs and launders set level so flow and overflow are even.'],
           piping=['Inlet distribution to avoid short-circuiting; sludge/float lines sized for thick material; chemical dosing points upstream.'],
           commissioning=['Fill with water and check levels; start air/recycle; optimise chemical dosing with jar tests.'])
_NL = ['No lubrication of static parts; lubricate pumps, drives and valve actuators per maker.']

MODULES['cartridge_filter'] = mod(
    definition=('A cartridge filter removes fine particles from a liquid or gas. Several pleated filter cartridges stand on a tube sheet inside a pressure housing. The fluid flows from outside to inside through '
                'the filter media; particles are trapped on the media surface, and the clean fluid flows down the cartridge cores to the outlet.'),
    applications=['Pre-filtration before RO/NF membranes (≈ 5 µm)', 'Polishing of chemicals, water and solvents', 'Fuel and lube-oil filtration', 'Pharmaceutical and food liquids'],
    key_points=['Rated by micron size (nominal or absolute)', 'ΔP rises as dirt loads the media', 'Change at terminal ΔP', 'Seals prevent bypass of dirty fluid'],
    principle=[step('Dirty fluid enters the housing.', 'nozzles_gauge', overlay='flow'), step('It flows through the pleated media from outside to inside.', 'cartridges'),
               step('Particles are trapped on the media surface.', 'cartridges', overlay='pressure'), step('The tube sheet keeps dirty and clean sides apart.', 'tube_sheet'),
               step('Filtered fluid leaves through the bottom outlet.', 'housing', overlay='flow')],
    curve='ΔP vs time: slow rise then rapid rise as the media blinds; filter life ends at the terminal ΔP.',
    params=fs(P('Housing ~ 100 – 800 mm diameter; 1 – 100+ cartridges'), P('~ 1 – 1000', 'm³/h'), P('Up to ~ 10 – 100 (housing rating)', 'bar'), P('~ 0.1 – 100 µm rating', 'µm')),
    install=_VI, maint=_m([M('Record ΔP.', 'nozzles_gauge', 'daily')], [M('Replace cartridges at terminal ΔP; inspect seals.', 'cartridges', 'as required')], [M('Inspect housing and cover seal.', 'cover')], _NL),
    failures=[F('Rapid ΔP rise', ['Short cartridge life'], ['High solids load, upstream upset'], ['Improve pre-treatment; coarser pre-filter'], 'cartridges'),
              F('Bypass', ['Particles downstream'], ['Damaged O-rings, poor seating'], ['Re-seat; replace seals'], 'tube_sheet')],
    quiz=[Q('Why does ΔP rise during operation?', ['Dirt builds up on the media', 'Fluid gets lighter', 'Pump speeds up', 'Media cleans itself'], 0, 'Loading.'),
          Q('What does "absolute rating" mean?', ['Removes essentially all particles above the stated size', 'Removes half', 'Colour', 'Housing pressure'], 0, 'High efficiency at size.'),
          Q('Why must the tube sheet seal well?', ['To stop dirty fluid bypassing the cartridges', 'For noise', 'For weight', 'No reason'], 0, 'Bypass.')],
    selection=['Choose rating and media for the fluid; size number of cartridges for flux and life.'],
    safety=['Depressurise and drain before opening; hazardous fluids require PPE.'], refs=['Sutherland — Filters and Filtration Handbook'])

MODULES['membrane_filter'] = mod(
    definition=('A plate-and-frame membrane filter clamps flat-sheet membranes between support plates. Feed under pressure flows across the membrane surfaces (cross-flow); the liquid that passes '
                'through (permeate) drains from each plate, while the concentrated retentate leaves at the end of the stack.'),
    applications=['Dairy and food concentration', 'Pharmaceutical and biotech clarification', 'Industrial wastewater and leachate treatment'],
    key_points=['Cross-flow limits fouling', 'Trans-membrane pressure drives flux', 'Easy access to individual membranes', 'Hydraulic closure seals the stack'],
    principle=[step('Feed enters through the fixed head.', 'ports', overlay='flow'), step('It sweeps across the membranes between the plates.', 'plate_stack', overlay='pressure'),
               step('Permeate passes through and drains from each plate.', 'permeate_collection'), step('The hydraulic cylinder clamps the stack.', 'closure'),
               step('Retentate leaves at the head.', 'fixed_head', overlay='flow')],
    curve='Flux vs TMP: rises linearly at first, then levels off (fouling/concentration polarisation limit).',
    params=fs(P('Membrane area ~ 1 – 100 m² per stack'), P('~ 0.1 – 20', 'm³/h permeate'), P('TMP ~ 0.5 – 10 (UF/MF); higher for RO', 'bar'), P('MF/UF/NF/RO cut-off depending on membrane', '—')),
    install=_MI, maint=_m([M('Monitor flux, TMP and permeate quality.', 'plate_stack', 'daily')], [M('CIP cleaning.', 'plate_stack', 'per schedule')], [M('Replace membranes.', 'plate_stack')], ['Hydraulic closure: oil per maker.']),
    failures=[F('Flux decline', ['Lower permeate rate'], ['Fouling, scaling'], ['CIP; improve pre-treatment'], 'plate_stack'), F('Leak', ['Feed in permeate'], ['Damaged membrane/gasket'], ['Replace'], 'plate_stack')],
    quiz=[Q('What drives liquid through the membrane?', ['Trans-membrane pressure', 'Gravity only', 'Heat', 'Magnetism'], 0, 'TMP.'),
          Q('Why use cross-flow?', ['To sweep away the fouling layer', 'To heat the feed', 'To reduce pressure', 'No reason'], 0, 'Limits cake.'),
          Q('What leaves through the membrane?', ['Permeate', 'Retentate', 'Sludge', 'Air'], 0, 'Permeate.')],
    selection=['Pick membrane type by cut-off and chemistry; size area from design flux.'], safety=['Release hydraulic closure pressure safely; chemical CIP precautions.'], refs=['Baker — Membrane Technology and Applications'])

MODULES['microfiltration_system'] = mod(
    definition=('A submerged hollow-fibre microfiltration system immerses cassettes of porous fibres directly in the feed tank. A permeate pump applies gentle suction so clean water passes into the fibres while '
                'suspended solids and bacteria stay outside. Air scouring and periodic back-pulsing keep the fibres clean.'),
    applications=['Membrane bioreactors (MBR) for wastewater', 'Surface-water treatment', 'Tertiary filtration'],
    key_points=['Pores ≈ 0.1–0.4 µm', 'Low TMP (≈ 0.1–0.5 bar suction)', 'Air scour is the main fouling control', 'Replaces clarifiers and sand filters'],
    principle=[step('Feed fills the membrane tank.', 'mixed_liquor', overlay='flow'), step('The permeate pump draws water into the fibres.', 'permeate_pump', overlay='pressure'),
               step('Solids are retained on the fibre surface.', 'membrane_cassette'), step('The blower supplies air that scours the fibres.', 'air_diffuser'), step('Permeate leaves via the header.', 'permeate_line', overlay='flow')],
    curve='TMP rises over time at constant flux; relax/backpulse and maintenance cleans restore it.',
    params=fs(P('Cassettes ~ 10 – 2000 m² each'), P('~ 10 – 100 000', 'm³/d'), P('TMP ~ 0.1 – 0.5 (suction)', 'bar'), P('~ 0.1 – 0.4 µm; > 4-log bacteria removal', 'µm')),
    install=_MI, maint=_m([M('Monitor TMP, flux and air flow.', 'membrane_cassette', 'continuous')], [M('Maintenance clean (hypochlorite/citric).', 'membrane_cassette', 'weekly')],
                          [M('Recovery clean; fibre repair/replacement.', 'membrane_cassette')], ['Blower and pump bearings per maker.']),
    failures=[F('Sludging of the cassette', ['Rising TMP, clogged fibres'], ['Low air scour, high solids'], ['Restore aeration; clean'], 'membrane_cassette'),
              F('Fibre breakage', ['Turbidity in permeate'], ['Abrasive debris, poor screening'], ['Fine screening; repair'], 'membrane_cassette')],
    quiz=[Q('How is water drawn through a submerged membrane?', ['Suction from the permeate pump', 'High-pressure feed pump', 'Gravity only', 'Air pressure'], 0, 'Suction.'),
          Q('What is air scour for?', ['Keeping fibre surfaces clean', 'Aerating permeate', 'Cooling', 'Lifting the tank'], 0, 'Fouling control.'),
          Q('Typical MF pore size is…', ['0.1–0.4 µm', '1 mm', '1 nm', '10 µm'], 0, 'Microfiltration.')],
    selection=['Size membrane area from design flux; fine screening (≈ 1–3 mm) upstream.'], safety=['Chemical cleaning hazards; confined-space entry rules for tanks.'], refs=['Judd — The MBR Book'])

MODULES['ultrafiltration_system'] = mod(
    definition=('An ultrafiltration system pumps water through pressurised modules packed with hollow fibres with very fine pores. Water and dissolved salts pass through; suspended solids, colloids, bacteria and '
                'most viruses are held back. Short backwashes with filtrate restore flux every 20–60 minutes.'),
    applications=['Drinking-water treatment', 'Pre-treatment before reverse osmosis', 'Industrial process water and wastewater reuse'],
    key_points=['Pores ≈ 0.01–0.1 µm', 'Barrier to pathogens', 'Backwash and CEB cleaning cycles', 'Integrity testing proves the barrier'],
    principle=[step('The feed pump supplies water through the strainer.', 'feed_pump', overlay='flow'), step('Water enters the modules and passes through the fibres.', 'fibres', overlay='pressure'),
               step('Filtrate collects in the top header and tank.', 'headers'), step('Periodically the backwash pump reverses flow to clean the fibres.', 'backwash_pump', overlay='flow')],
    curve='TMP vs time saw-tooth: rises during filtration, drops after each backwash.',
    params=fs(P('Modules ~ 20 – 80 m² each'), P('~ 10 – 100 000', 'm³/d'), P('TMP ~ 0.2 – 2', 'bar'), P('~ 0.01 – 0.1 µm; > 4-log virus removal (validated)', 'µm')),
    install=_MI, maint=_m([M('Trend TMP and permeability.', 'modules', 'daily')], [M('Pressure-decay integrity test.', 'fibres', 'daily/weekly')], [M('Recovery CIP; replace modules.', 'modules')], ['Pump bearings per maker.']),
    failures=[F('Integrity failure', ['Pressure-decay test fails'], ['Broken fibres'], ['Pin/repair fibres'], 'fibres'), F('Irreversible fouling', ['Low permeability after cleaning'], ['Organics, iron/manganese'], ['Optimise pre-treatment and CIP'], 'modules')],
    quiz=[Q('What does UF remove that MF may not fully remove?', ['Viruses and fine colloids', 'Salts', 'Dissolved gases', 'Nothing'], 0, 'Smaller pores.'),
          Q('Why backwash?', ['To remove the fouling layer', 'To add salt', 'To heat', 'To test pumps'], 0, 'Flux recovery.'),
          Q('How is membrane integrity checked?', ['Pressure-decay test', 'By colour', 'By noise', 'Not possible'], 0, 'PDT.')],
    selection=['Size for flux, recovery and backwash losses; select inside-out or outside-in fibres.'], safety=['Chemical dosing safety; pressure parts.'], refs=['AWWA M53'])

MODULES['nanofiltration_system'] = mod(
    definition=('A nanofiltration system forces water at moderate pressure through spiral-wound membrane elements. NF lets water and most monovalent salts through but rejects hardness (calcium, magnesium), '
                'sulphate, colour and many organic molecules. Elements are housed in pressure vessels arranged in stages to increase recovery.'),
    applications=['Water softening and colour removal', 'Sulphate removal from seawater (oil-field injection)', 'Food and dairy (demineralisation)', 'Wastewater reuse'],
    key_points=['Between UF and RO', 'Feed pressure ≈ 5–20 bar', 'High rejection of divalent ions', 'Concentrate valve sets recovery'],
    principle=[step('The cartridge pre-filter protects the elements.', 'cartridge_prefilter', overlay='flow'), step('The high-pressure pump raises the feed pressure.', 'hp_pump', overlay='pressure'),
               step('Feed flows along the element spacers; water permeates the membrane leaves.', 'spiral_elements'), step('Stage-1 concentrate feeds stage 2.', 'pressure_vessels'),
               step('Permeate and concentrate leave through their headers.', 'piping', overlay='flow')],
    curve='Normalised permeate flow and salt passage vs time — the basis for deciding when to clean.',
    params=fs(P('8-inch elements, ~ 37 – 41 m² each'), P('~ 10 – 100 000', 'm³/d'), P('~ 5 – 20', 'bar'), P('Divalent rejection typically > 90 %', '%')),
    install=_MI, maint=_m([M('Record pressures, flows, conductivity; normalise data.', 'piping', 'daily')], [M('CIP when normalised flow drops ~ 10–15 %.', 'spiral_elements', 'as required')],
                          [M('Replace elements (typically 3–7 years).', 'spiral_elements')], ['HP pump per maker.']),
    failures=[F('Scaling', ['Rising ΔP in last stage, falling flow'], ['Exceeding solubility (CaSO₄, CaCO₃)'], ['Antiscalant; acid; lower recovery'], 'spiral_elements'),
              F('Fouling', ['First-stage ΔP rise'], ['Colloids, biofilm'], ['Better pre-treatment; CIP'], 'pressure_vessels')],
    quiz=[Q('NF strongly rejects…', ['Divalent ions like Ca²⁺ and SO₄²⁻', 'All monovalent ions', 'Only bacteria', 'Nothing'], 0, 'Divalent.'),
          Q('Typical NF feed pressure is…', ['~ 5–20 bar', '~ 0.1 bar', '~ 200 bar', '~ 1000 bar'], 0, 'Moderate.'),
          Q('What does the second stage treat?', ['First-stage concentrate', 'Permeate', 'Air', 'Clean water'], 0, 'Raises recovery.')],
    selection=['Use projection software of the membrane maker; set recovery from scaling limits.'], safety=['High pressure; chemical cleaning.'], refs=['ASTM D4516', 'Membrane maker design guides'])

MODULES['disc_stack_centrifuge'] = mod(
    definition=('A disc stack centrifuge (separator) spins a bowl at thousands of rpm. Inside, a stack of conical discs splits the liquid into thin layers so that particles and droplets only need to travel a short '
                'distance to separate. Heavier phases move outwards; lighter liquid moves inwards and leaves at the top. Collected solids are ejected periodically.'),
    applications=['Milk skimming and clarification', 'Fuel and lube-oil purification (ships, power plants)', 'Beer, wine and juice clarification', 'Biotech and pharma'],
    key_points=['g-force = ω²r/g (thousands of g)', 'Discs give a large equivalent settling area', 'Two- or three-phase separation', 'Self-cleaning by intermittent ejection'],
    principle=[step('Feed enters down the central pipe into the distributor.', 'inlet_outlets', overlay='flow'), step('The bowl and discs spin at high speed.', 'bowl', overlay='pressure'),
               step('Heavy phase and solids move outward along the discs.', 'bowl'), step('Light phase moves inward and is pumped out by the paring disc.', 'inlet_outlets'),
               step('Solids are ejected through the ports at intervals.', 'lock_ring_nozzles')],
    curve='Separation capacity ∝ equivalent clarifying area Σ; throughput falls for finer particles.',
    params=fs(P('Bowl ~ 0.2 – 1 m diameter'), P('~ 0.1 – 100', 'm³/h'), P('Atmospheric to ~ 6 bar outlet', 'bar'), P('Particles down to ~ 0.5 – 1 µm', 'µm')),
    install=_CI, maint=_m([M('Monitor vibration, speed, outlet pressure.', 'spindle', 'continuous')], [M('Inspect and clean disc stack.', 'bowl', 'periodic')],
                          [M('Bowl overhaul and balancing; spindle bearings.', 'bowl', '≈ 8 000 h (maker)')], ['Spindle bearings: oil bath/mist per maker.']),
    failures=[F('Vibration', ['High vibration trip'], ['Unbalanced bowl (uneven solids), worn bearings'], ['Clean/balance; replace bearings'], 'bowl'),
              F('Poor separation', ['Cloudy light phase'], ['Too high flow, wrong gravity disc'], ['Reduce flow; correct disc/temperature'], 'inlet_outlets')],
    quiz=[Q('Why use a disc stack?', ['Short settling distance and large settling area', 'For weight', 'To heat', 'To pump'], 0, 'Σ-area.'),
          Q('g-force depends on…', ['Speed squared and radius', 'Colour', 'Feed temperature only', 'Disc count only'], 0, 'ω²r.'),
          Q('Where do heavy solids collect?', ['Bowl periphery', 'Centre', 'Top', 'Feed pipe'], 0, 'Outward.')],
    selection=['Size from Σ and settling velocity; choose 2- or 3-phase and discharge type.'], safety=['Never open before full stop; interlocks; vibration trips.'], refs=['EN 12547'])

MODULES['decanter_centrifuge'] = mod(
    definition=('A decanter centrifuge separates solids from liquid continuously. A horizontal solid bowl spins at high speed so the solids settle against its wall. A scroll conveyor inside turns slightly slower or faster '
                'than the bowl (differential speed) and pushes the settled solids up the conical beach to the solids outlet; clarified liquid overflows the weirs at the other end.'),
    applications=['Sludge dewatering (wastewater)', 'Drilling-mud and oil-sludge treatment', 'Olive oil and food processing', 'Chemical and mineral slurries'],
    key_points=['Continuous solids discharge', 'Differential speed controls cake dryness and residence time', 'Pool depth set by weir plates', 'Polymer flocculant improves capture'],
    principle=[step('Feed enters through the central pipe into the bowl.', 'casing', overlay='flow'), step('Solids settle on the bowl wall under high g.', 'bowl', overlay='pressure'),
               step('The scroll conveys solids up the beach.', 'scroll'), step('The gearbox sets the differential speed.', 'gearbox_backdrive'),
               step('Clear liquid overflows the weirs; cake drops out at the cone end.', 'bowl_head_weirs', overlay='flow')],
    curve='Cake dryness vs centrate clarity trade-off: lower differential speed → drier cake but more solids loss.',
    params=fs(P('Bowl ~ 0.2 – 1.2 m diameter, L/D ~ 3 – 5'), P('~ 1 – 200', 'm³/h'), P('Atmospheric', 'bar'), P('Capture typically ~ 95 – 99 %', '%')),
    install=_CI, maint=_m([M('Monitor vibration, torque, differential speed.', 'gearbox_backdrive', 'continuous')], [M('Inspect scroll flight wear.', 'scroll', 'quarterly')],
                          [M('Re-hard-face scroll; bearing and gearbox overhaul.', 'scroll')], ['Main bearings grease/oil; gearbox oil per maker.']),
    failures=[F('Scroll wear', ['Wet cake, falling capacity'], ['Abrasive solids'], ['Tungsten-carbide tiles; repair'], 'scroll'), F('Overtorque', ['Trip'], ['High solids load'], ['Reduce feed; raise differential'], 'gearbox_backdrive')],
    quiz=[Q('What does the scroll do?', ['Conveys settled solids to the outlet', 'Heats the bowl', 'Pumps liquid in', 'Measures flow'], 0, 'Conveying.'),
          Q('What sets pool depth?', ['Weir plate setting', 'Motor size', 'Gearbox colour', 'Casing'], 0, 'Weirs.'),
          Q('Lower differential speed generally gives…', ['Drier cake (longer residence)', 'Wetter cake', 'No change', 'No solids'], 0, 'Trade-off.')],
    selection=['Size from solids load, g-force and residence time; test with the actual slurry.'], safety=['Guarding; vibration and overspeed protection; never open while running.'], refs=['Records & Sutherland — Decanter Centrifuge Handbook'])

MODULES['basket_centrifuge'] = mod(
    definition=('A basket centrifuge filters a slurry in a spinning perforated basket lined with filter cloth. Centrifugal force drives the liquid through the cake and cloth, while the solids form a cake on the cloth. '
                'The cake can be washed, spun dry and then removed by a plough at low speed.'),
    applications=['Pharmaceutical and fine-chemical crystals', 'Sugar (batch centrifugals)', 'Dewatering of solids that need washing'],
    key_points=['Batch filtering centrifuge', 'Cycle: fill – wash – spin dry – discharge', 'Cake washing possible', 'Cloth selection is critical'],
    principle=[step('Slurry enters through the feed pipe.', 'feed_pipe', overlay='flow'), step('The basket spins and throws slurry against the cloth.', 'basket', overlay='pressure'),
               step('Liquid passes the cake and cloth to the casing.', 'casing'), step('Solids build up as the cake.', 'cake'), step('The plough discharges the cake at low speed.', 'plough')],
    curve='Residual moisture vs spin time and g: falls quickly then levels off.',
    params=fs(P('Basket ~ 0.3 – 1.8 m diameter'), P('Batch ~ 10 – 1500 kg', 'kg'), P('Atmospheric (inerted for solvents)', 'bar'), P('Depends on cloth; crystals typically > 10 µm', 'µm')),
    install=_CI, maint=_m([M('Check vibration and cloth condition.', 'basket', 'per batch')], [M('Replace cloth; inspect plough.', 'plough', 'as needed')], [M('Bearing and drive overhaul.', 'drive')], ['Drive bearings per maker.']),
    failures=[F('Cloth blinding', ['Slow filtration'], ['Fines'], ['Wash/replace cloth'], 'basket'), F('Imbalance', ['Vibration'], ['Uneven loading'], ['Slower feeding; re-distribute'], 'basket')],
    quiz=[Q('What holds back the solids?', ['Filter cloth in the basket', 'Bowl wall without holes', 'A scroll', 'Discs'], 0, 'Filtering centrifuge.'),
          Q('How is the cake removed?', ['Plough at low speed', 'Air', 'Scroll', 'Discs'], 0, 'Plough.'),
          Q('Why is uneven loading dangerous?', ['It causes imbalance and vibration', 'It cools', 'No issue', 'It improves washing'], 0, 'Imbalance.')],
    selection=['Choose basket size and g for crystal size and batch size; cloth for particle size.'], safety=['Lid interlocks; nitrogen inerting for flammable solvents.'], refs=['Svarovsky — Solid-Liquid Separation'])

MODULES['magnetic_separator'] = mod(
    definition=('A wet drum magnetic separator recovers magnetic particles such as magnetite from a slurry. A non-magnetic stainless drum turns around a stationary permanent-magnet arc. Magnetic particles are attracted '
                'to the drum surface, carried out of the slurry and released into the concentrate launder where the field ends; non-magnetic particles flow on to tailings.'),
    applications=['Magnetite recovery in iron-ore concentrators', 'Dense-medium recovery in coal washing', 'Removal of iron from minerals'],
    key_points=['Stationary magnets, rotating drum', 'Field typically ~ 0.1–0.3 T at drum surface (low intensity)', 'Concurrent, counter-rotation and counter-current tanks', 'Magnetic susceptibility drives separation'],
    principle=[step('Slurry enters the feed box.', 'tank', overlay='flow'), step('The magnet arc creates a field round the lower drum.', 'magnet_assembly', overlay='magnetic_field'),
               step('Magnetic particles stick to the turning drum.', 'drum'), step('They are released into the concentrate launder.', 'outlets'), step('Non-magnetic particles leave as tailings.', 'slurry', overlay='flow')],
    curve='Recovery vs field strength and drum speed; too fast a drum loses magnetics, too slow reduces capacity.',
    params=fs(P('Drum ~ 0.6 – 1.5 m diameter, up to ~ 4 m wide'), P('~ 10 – 300', 't/h solids'), P('Atmospheric', 'bar'), P('Magnetite recovery typically > 95 %', '%')),
    install=_TI, maint=_m([M('Check slurry level and drum surface.', 'drum', 'daily')], [M('Measure field strength; inspect wear liner.', 'magnet_assembly', 'annual')], [M('Replace drum shell/liners.', 'drum')], ['Drive bearings and gearbox per maker.']),
    failures=[F('Loss of magnetics to tailings', ['Low recovery'], ['Field weakening, high slurry velocity'], ['Check magnets; adjust feed'], 'magnet_assembly'), F('Drum wear', ['Holes in shell'], ['Abrasion'], ['Wear liners; replace'], 'drum')],
    quiz=[Q('Which part rotates?', ['The non-magnetic drum', 'The magnet arc', 'The tank', 'The feed box'], 0, 'Drum.'),
          Q('Why is the drum stainless (non-magnetic)?', ['So the field passes through it', 'For colour', 'For weight', 'To heat'], 0, 'Field penetration.'),
          Q('Where do non-magnetic particles go?', ['Tailings', 'Concentrate', 'Drum', 'Motor'], 0, 'Tailings.')],
    selection=['Choose tank style and field strength for particle size and duty.'], safety=['Strong magnets — keep tools and pacemakers away; lock out drive.'], refs=['Wills\' Mineral Processing Technology'])

MODULES['flotation_cell'] = mod(
    definition=('A mechanical flotation cell separates valuable mineral particles from waste. Reagents make the wanted mineral surfaces water-repellent. Air enters down a hollow shaft and a spinning rotor–stator breaks it into fine '
                'bubbles; the hydrophobic particles attach to the bubbles and rise into a froth, which overflows into the launder as concentrate.'),
    applications=['Copper, lead, zinc, gold and phosphate concentration', 'Coal fines cleaning', 'De-inking of paper pulp'],
    key_points=['Separation by surface chemistry (hydrophobicity)', 'Rotor suspends solids and disperses air', 'Froth depth and air rate control grade/recovery', 'Cells in banks: rougher, scavenger, cleaner'],
    principle=[step('Conditioned pulp enters the cell.', 'air_feed_tailings', overlay='flow'), step('Air flows down the hollow shaft.', 'rotor'),
               step('Rotor and stator create fine bubbles.', 'stator'), step('Hydrophobic particles ride bubbles into the froth.', 'froth', overlay='pressure'), step('Froth overflows into the launder.', 'tank', overlay='flow')],
    curve='Grade–recovery curve: higher recovery usually means lower concentrate grade.',
    params=fs(P('Cell ~ 1 – 600 m³'), P('~ 10 – 5000', 'm³/h pulp'), P('Air ~ 0.2 – 0.5 bar g at rotor', 'bar'), P('Recovery typically ~ 80 – 95 %', '%')),
    install=_TI, maint=_m([M('Check froth, air flow and level.', 'froth', 'per shift')], [M('Inspect rotor/stator wear.', 'rotor', 'quarterly')], [M('Replace rotor/stator.', 'stator')], ['Drive bearings per maker.']),
    failures=[F('Poor recovery', ['Mineral in tailings'], ['Wrong reagent dose, coarse particles, low air'], ['Optimise reagents and air'], 'froth'), F('Rotor wear', ['Bubble size grows'], ['Abrasion'], ['Replace'], 'rotor')],
    quiz=[Q('Particles float because they are…', ['Hydrophobic and attached to bubbles', 'Lighter than water', 'Magnetic', 'Hot'], 0, 'Surface chemistry.'),
          Q('Collectors are added to…', ['Make target mineral surfaces hydrophobic', 'Make froth', 'Raise pH only', 'Cool pulp'], 0, 'Collectors.'),
          Q('Higher recovery usually means…', ['Lower grade', 'Higher grade always', 'No change', 'No froth'], 0, 'Trade-off.')],
    selection=['Size cell volume from residence time (lab kinetics × scale-up); choose forced-air or self-aspirated.'], safety=['Reagent handling; guard drives; slippery froth areas.'], refs=['Wills\' Mineral Processing Technology'])

MODULES['dissolved_air_flotation_unit'] = mod(
    definition=('A dissolved air flotation (DAF) unit removes suspended solids, oil and grease from water. A recycle stream of clarified water is pressurised and saturated with air. When the pressure is released in the '
                'tank, micro-bubbles form and attach to the flocs, floating them to the surface, where a skimmer removes the float as sludge.'),
    applications=['Industrial wastewater (food, dairy, refinery, paper)', 'Algae removal in drinking water', 'Oily water treatment'],
    key_points=['Micro-bubbles ≈ 30–100 µm', 'Saturator at ≈ 4–6 bar', 'Coagulant/flocculant needed', 'Thicker float than gravity settling'],
    principle=[step('Flocculated feed enters the contact zone.', 'tank', overlay='flow'), step('The recycle pump pressurises water into the saturator.', 'saturator', overlay='pressure'),
               step('Pressure release forms micro-bubbles.', 'recycle_piping'), step('Bubbles float the flocs into a surface layer.', 'float_layer'), step('The skimmer pushes float into the hopper.', 'skimmer')],
    curve='Air-to-solids ratio (A/S, typically ~ 0.005–0.06) controls float performance.',
    params=fs(P('Tank ~ 5 – 200 m²'), P('~ 5 – 2000', 'm³/h'), P('Saturator ~ 4 – 6', 'bar'), P('TSS removal typically ~ 85 – 98 %', '%')),
    install=_TI, maint=_m([M('Check bubble quality, float and chemicals.', 'float_layer', 'daily')], [M('Clean release nozzles; inspect skimmer chain.', 'recycle_piping', 'monthly')], [M('Saturator inspection.', 'saturator')], ['Skimmer drive and pumps per maker.']),
    failures=[F('Poor float', ['Solids in effluent'], ['Low air, poor flocculation'], ['Check saturator pressure; jar test'], 'saturator'), F('Nozzle clogging', ['Large bubbles'], ['Scale/solids'], ['Clean nozzles'], 'recycle_piping')],
    quiz=[Q('How are micro-bubbles produced?', ['Releasing pressure on air-saturated water', 'Blowing air through holes', 'Chemical reaction', 'Heating'], 0, 'Henry\'s law.'),
          Q('What removes the float?', ['Surface skimmer', 'Bottom drain', 'Pump only', 'Magnet'], 0, 'Skimmer.'),
          Q('Why add coagulant/flocculant?', ['To form flocs bubbles can lift', 'To colour water', 'To heat', 'No reason'], 0, 'Flocs.')],
    selection=['Size from hydraulic loading (≈ 5–15 m/h) and solids loading; set recycle ratio from A/S.'], safety=['Pressure vessel; chemicals; walkway guards.'], refs=['Metcalf & Eddy — Wastewater Engineering'])

MODULES['oil_water_separator'] = mod(
    definition=('An oil–water separator removes free oil and settleable solids from wastewater by gravity. In a corrugated plate interceptor (CPI), packs of inclined plates give oil droplets only a short distance to rise; '
                'they coalesce on the plates and slide up to the oil layer, which is skimmed off, while solids slide down into the hopper.'),
    applications=['Refinery and terminal drainage', 'Workshops, car washes and fuel stations', 'Ballast and produced water pre-treatment'],
    key_points=['Stokes\' law governs separation', 'Plates shorten rise distance', 'Removes free oil, not emulsions', 'Regular skimming and desludging'],
    principle=[step('Oily water enters through the inlet baffle.', 'nozzles', overlay='flow'), step('It flows through the inclined plate pack.', 'plate_pack', overlay='pressure'),
               step('Oil droplets rise and form a layer.', 'oil_layer'), step('The skimmer removes the oil.', 'oil_skimmer'), step('Clean water leaves under the oil baffle over the weir.', 'tank', overlay='flow')],
    curve='Removal efficiency vs droplet size: near 100 % above design size (~ 60 µm CPI), falling steeply below.',
    params=fs(P('Tank ~ 1 – 20 m long'), P('~ 1 – 500', 'm³/h'), P('Atmospheric', 'bar'), P('Free oil droplets ≥ ~ 50–60 µm (CPI)', 'µm')),
    install=_TI, maint=_m([M('Skim oil; check levels.', 'oil_skimmer', 'daily')], [M('Desludge hopper; clean plates.', 'plate_pack', 'monthly/quarterly')], [M('Inspect tank coating.', 'tank')], _NL),
    failures=[F('Oil carry-over', ['Sheen in effluent'], ['Emulsified oil, overload, plates fouled'], ['Reduce flow; clean plates; break emulsions upstream'], 'plate_pack'), F('Sludge build-up', ['Short-circuiting'], ['Infrequent desludging'], ['Desludge'], 'tank')],
    quiz=[Q('Oil droplet rise velocity is proportional to…', ['Diameter squared', 'Diameter', 'Temperature only', 'Flow'], 0, 'Stokes.'),
          Q('Why inclined plates?', ['Short rise distance; more separation area', 'Decoration', 'To slow pumps', 'To heat'], 0, 'Plate pack.'),
          Q('Can gravity separators remove emulsified oil?', ['Not effectively', 'Yes, fully', 'Only hot', 'Only cold'], 0, 'Needs chemical/DAF.')],
    selection=['Size from design droplet size, flow and oil density (API 421 method).'], safety=['Flammable vapours; confined space; spill containment.'], refs=['API Publication 421'])

MODULES['coalescer'] = mod(
    definition=('A liquid–liquid coalescer removes fine droplets of one liquid from another — for example water from jet fuel or diesel. The fluid passes through coalescing cartridges whose fibres catch tiny droplets and '
                'merge them into large drops; these settle quickly into the water boot, from which an interface controller drains the water.'),
    applications=['Aviation fuel and diesel water removal', 'Water removal from LPG/condensates', 'Oil removal from water (reverse configuration)'],
    key_points=['Turns small droplets into large drops', 'Large drops settle fast (Stokes)', 'Surfactants can disarm media', 'Interface level control on the boot'],
    principle=[step('Fluid with dispersed water enters the vessel.', 'nozzles_instruments', overlay='flow'), step('It flows through the coalescing cartridges.', 'coalescing_elements', overlay='pressure'),
               step('Droplets grow and fall out of the flow.', 'liquid'), step('The vane pack catches remaining drops.', 'coalescing_elements'), step('Water collects in the boot and is drained.', 'boot_water')],
    curve='Outlet water content vs flow: rises sharply above the rated flux of the elements.',
    params=fs(P('Vessel ~ 0.3 – 2 m diameter'), P('~ 1 – 1000', 'm³/h'), P('Up to ~ 10 – 100 (rating)', 'bar'), P('Outlet free water typically < 15 ppm (fuel)', 'ppm')),
    install=_VI, maint=_m([M('Drain/check boot interface; ΔP.', 'boot_water', 'daily')], [M('Sample outlet water content.', 'nozzles_instruments', 'weekly')], [M('Replace coalescer elements.', 'coalescing_elements')], _NL),
    failures=[F('Media disarming', ['Water passes through'], ['Surfactants'], ['Change media; remove surfactant source'], 'coalescing_elements'), F('High ΔP', ['Flow restriction'], ['Particulates'], ['Pre-filter; replace'], 'coalescing_elements')],
    quiz=[Q('What does a coalescer do to droplets?', ['Merges small droplets into large drops', 'Evaporates them', 'Heats them', 'Charges them'], 0, 'Coalescence.'),
          Q('Why do large drops separate faster?', ['Settling velocity ∝ d²', 'They are lighter', 'Magnetism', 'No reason'], 0, 'Stokes.'),
          Q('What can disarm coalescer media?', ['Surfactants', 'Cold', 'Light', 'Steel'], 0, 'Lower IFT.')],
    selection=['Choose media for interfacial tension; size elements for rated flux.'], safety=['Flammable fluids — earthing, depressurise before opening.'], refs=['API/EI 1581 (aviation filter-separators, to be verified)', 'Maker data'])

MODULES['molecular_sieve_adsorber'] = mod(
    definition=('A molecular sieve adsorber removes water (and sometimes CO₂, H₂S or mercaptans) from gas using zeolite beads with uniform pores. Two towers work in turn: one adsorbs while the other is regenerated by hot '
                'gas (temperature swing). Very low dew points are achieved, which is essential before cryogenic gas processing.'),
    applications=['Natural gas drying before NGL/LNG plants', 'Air separation pre-purification', 'Ethanol dehydration (vapour phase)'],
    key_points=['Zeolites 3A/4A/5A/13X by pore size', 'Dew point ≈ −70 to −100 °C', 'TSA regeneration ≈ 200–300 °C', 'Cycle switching by time or breakthrough'],
    principle=[step('Wet gas flows down through tower A.', 'tower_a', overlay='flow'), step('Water is adsorbed in the sieve pores.', 'tower_a_bed', overlay='temperature'),
               step('The mass-transfer zone moves down the bed.', 'mass_transfer_zone'), step('Hot regeneration gas flows up through tower B.', 'regen_heater', overlay='flow'),
               step('Valves switch the towers at the end of the cycle.', 'switching_valves')],
    curve='Breakthrough curve: outlet water stays near zero until the MTZ reaches the bottom, then rises steeply.',
    params=fs(P('Towers ~ 1 – 5 m diameter'), P('~ 1 – 50', 'MMSCMD gas'), P('~ 20 – 100', 'bar'), P('Outlet water < 1 ppmv; dew point ≈ −70 to −100 °C', 'ppmv')),
    install=_VI, maint=_m([M('Monitor outlet dew point and bed ΔP.', 'tower_a_bed', 'continuous')], [M('Check regeneration temperatures and valve leak-tightness.', 'switching_valves', 'monthly')],
                          [M('Replace sieve (typically 3–5 years).', 'tower_b_bed')], ['Valve actuators per maker.']),
    failures=[F('Early breakthrough', ['Rising outlet water'], ['Sieve ageing, incomplete regeneration, liquid carry-over'], ['Check regen; inlet separation; replace sieve'], 'tower_a_bed'),
              F('Valve leakage', ['Wet gas bypass'], ['Seat wear from thermal cycling'], ['Repair valves'], 'switching_valves')],
    quiz=[Q('How is the sieve regenerated here?', ['Heating with hot gas (TSA)', 'Washing with water', 'Replacing every cycle', 'Cooling'], 0, 'TSA.'),
          Q('Why twin towers?', ['One adsorbs while the other regenerates', 'Redundancy only', 'Decoration', 'Higher pressure'], 0, 'Continuous operation.'),
          Q('Typical outlet dew point?', ['≈ −70 to −100 °C', '≈ 0 °C', '≈ +20 °C', '≈ −10 °C'], 0, 'Very dry.')],
    selection=['Size bed for water load, cycle time and MTZ length; choose sieve type by molecules to remove.'], safety=['Hot regeneration; dust when loading sieve; pressure.'], refs=['GPSA Engineering Data Book — Dehydration'])

MODULES['activated_alumina_adsorber'] = mod(
    definition=('An activated alumina adsorber passes a gas or liquid down through a fixed bed of porous aluminium-oxide beads supported on graded ceramic balls. The beads adsorb water or contaminants such as fluoride, arsenic '
                'or acids. The working (mass-transfer) zone moves down the bed until breakthrough, when the bed is regenerated or replaced.'),
    applications=['Drying of air, gases and liquids', 'Fluoride and arsenic removal from drinking water', 'HCl and acid removal in refinery streams', 'Transformer-oil and liquid hydrocarbon drying'],
    key_points=['High surface area (≈ 300 m²/g)', 'Dew points around −40 °C (drying)', 'Regenerated by heat (drying) or chemicals (fluoride)', 'Graded ceramic balls support the bed'],
    principle=[step('Fluid enters through the inlet distributor.', 'internals', overlay='flow'), step('It passes down through the alumina bed.', 'bed', overlay='pressure'),
               step('Contaminants are adsorbed in the mass-transfer zone.', 'mass_transfer_zone'), step('The saturated zone grows from the top.', 'saturated_zone'),
               step('Treated fluid leaves through the bottom collector.', 'vessel', overlay='flow')],
    curve='Breakthrough curve and adsorption isotherm (capacity vs concentration/humidity).',
    params=fs(P('Vessel ~ 0.3 – 4 m diameter'), P('~ 1 – 1000', 'm³/h'), P('Atmospheric to ~ 100', 'bar'), P('Drying to ≈ −40 °C dew point; fluoride to < 1.5 mg/L (WHO guideline)', '—')),
    install=_VI, maint=_m([M('Monitor outlet quality and ΔP.', 'bed', 'daily')], [M('Regenerate at breakthrough.', 'bed', 'per cycle')], [M('Replace alumina; inspect internals.', 'internals')], _NL),
    failures=[F('Channelling', ['Early breakthrough'], ['Poor distribution, bed settling'], ['Repair distributor; re-load'], 'internals'), F('Bead breakdown', ['Fines, ΔP rise'], ['Liquid water slugs, thermal shock'], ['Inlet separation; controlled regeneration'], 'bed')],
    quiz=[Q('What is "breakthrough"?', ['When contaminant appears at the outlet as the MTZ reaches the bottom', 'Bed breaking', 'Valve opening', 'Start-up'], 0, 'Breakthrough.'),
          Q('Why ceramic support balls?', ['Support the bed and distribute flow', 'Adsorb water', 'Add weight only', 'Colour'], 0, 'Support.'),
          Q('Fluoride-loaded alumina is regenerated by…', ['Chemicals (e.g. caustic then acid)', 'Heat only', 'Nothing', 'Air'], 0, 'Chemical regeneration.')],
    selection=['Size from contaminant load, contact time and regeneration method.'], safety=['Dust when loading; chemical regenerants.'], refs=['Maker data', 'WHO Guidelines for Drinking-water Quality (fluoride)'])

MODULES['desiccant_dryer'] = mod(
    definition=('A heatless desiccant dryer dries compressed air by pressure-swing adsorption. One tower dries the air at line pressure while the other is depressurised and swept by a small part of the dried air (purge) that '
                'carries away the adsorbed water. The towers switch every few minutes.'),
    applications=['Instrument air', 'Pharmaceutical and food air', 'Outdoor air lines in freezing climates'],
    key_points=['Pressure swing: adsorb high, desorb low', 'Purge air ≈ 15–20 % (heatless)', 'Dew point −40 °C (alumina) or −70 °C (mol sieve)', 'Pre-filter protects desiccant from oil'],
    principle=[step('Wet compressed air passes the pre-filter.', 'filters', overlay='flow'), step('The shuttle valve directs it into the drying tower.', 'shuttle'),
               step('Desiccant adsorbs the water vapour.', 'tower_left_bed', overlay='pressure'), step('Dry air purges the other tower at low pressure.', 'tower_right', overlay='flow'),
               step('The controller switches towers.', 'controller')],
    curve='Pressure dew point vs inlet temperature and flow; purge consumption vs cycle control (dew-point demand saves purge).',
    params=fs(P('Towers ~ 0.1 – 1 m diameter'), P('~ 10 – 10 000', 'Nm³/h'), P('~ 4 – 16', 'bar g'), P('PDP −40 °C (Class 2) to −70 °C (Class 1) per ISO 8573-1', '°C')),
    install=_VI, maint=_m([M('Check dew point and filter ΔP.', 'filters', 'daily')], [M('Replace filter elements; check silencers.', 'valve_manifolds', '6–12 months')], [M('Replace desiccant (≈ 3–5 years).', 'tower_left_bed')], _NL),
    failures=[F('High dew point', ['Moisture downstream'], ['Oil-fouled desiccant, low purge, valve fault'], ['Replace filters/desiccant; check valves'], 'tower_left_bed'), F('Silencer blockage', ['Slow depressurisation'], ['Desiccant dust'], ['Replace silencer'], 'valve_manifolds')],
    quiz=[Q('How is the desiccant regenerated in a heatless dryer?', ['Depressurising and purging with dry air', 'Electric heater', 'Replacing', 'Water wash'], 0, 'PSA.'),
          Q('Typical purge consumption?', ['~ 15–20 % of rated flow', '~ 1 %', '~ 80 %', '0 %'], 0, 'Heatless.'),
          Q('Why a coalescing pre-filter?', ['Oil and liquid would foul the desiccant', 'For noise', 'For heating', 'Not needed'], 0, 'Protection.')],
    selection=['Size from flow, inlet temperature and pressure; choose dew point class.'], safety=['Pressure; loud depressurisation (silencers).'], refs=['ISO 8573-1', 'ISO 7183'])

MODULES['gas_dehydration_unit'] = mod(
    definition=('A TEG gas dehydration unit removes water vapour from natural gas to prevent hydrates and corrosion. Wet gas rises through the trays of a contactor against a downflow of lean triethylene glycol, which absorbs '
                'the water. The rich glycol is flashed, heated and boiled in a reboiler to drive off the water, then cooled and pumped back.'),
    applications=['Natural gas pipelines and gathering', 'Offshore gas processing', 'Gas storage withdrawal'],
    key_points=['Absorption into TEG', 'Reboiler ≈ 200 °C (TEG degrades above ~ 206 °C)', 'Lean TEG ≈ 98.5–99.9 wt %', 'Typical spec ≈ 7 lb/MMscf water'],
    principle=[step('Wet gas enters the bottom of the contactor.', 'piping', overlay='flow'), step('Lean glycol flows down across the trays.', 'trays_demister', overlay='temperature'),
               step('Glycol absorbs the water; dry gas leaves the top.', 'contactor'), step('Rich glycol is flashed and preheated.', 'flash_tank_exchanger'),
               step('The reboiler boils off the water; the pump returns lean glycol.', 'regenerator', overlay='flow')],
    curve='Outlet dew point vs lean TEG concentration and circulation rate (typically ~ 15–40 L TEG per kg water removed).',
    params=fs(P('Contactor ~ 0.3 – 3 m diameter'), P('~ 0.1 – 20', 'MMSCMD'), P('~ 30 – 100 (contactor)', 'bar'), P('Water dew-point depression ≈ 40 – 70 °C', '°C')),
    install=_VI, maint=_m([M('Check glycol level, reboiler temperature, dew point.', 'regenerator', 'daily')], [M('Glycol analysis (water, pH, contaminants); filter changes.', 'glycol_pump', 'monthly')],
                          [M('Inspect fire tube and trays.', 'fire_tube')], ['Glycol pump per maker.']),
    failures=[F('Glycol losses', ['Falling level'], ['Foaming, carry-over, high gas velocity'], ['Antifoam; check mist eliminator'], 'trays_demister'), F('Glycol degradation', ['Dark, acidic glycol'], ['Overheating, oxygen'], ['Control reboiler; gas blanket'], 'regenerator')],
    quiz=[Q('Why dehydrate natural gas?', ['Prevent hydrates and corrosion', 'Increase water', 'Make it heavier', 'Colour'], 0, 'Hydrates.'),
          Q('Why limit reboiler temperature to about 200 °C?', ['TEG degrades above ~ 206 °C', 'Water freezes', 'Gas burns', 'No reason'], 0, 'Degradation.'),
          Q('Where does glycol absorb water?', ['In the contactor', 'In the reboiler', 'In the pump', 'In the flash tank'], 0, 'Contactor.')],
    selection=['Size contactor for gas velocity; circulation for dew-point target; consider stripping gas for deeper dew points.'], safety=['Fired equipment; BTEX emissions from still vent; high pressure.'], refs=['GPSA Engineering Data Book', 'Campbell — Gas Conditioning and Processing'])

MODULES['sand_trap'] = mod(
    definition=('A sand trap removes sand and other solids from well fluids or process streams. A tangential inlet sets up a swirl that throws the sand to the wall; it slides into the conical bottom while the cleaned fluid turns and '
                'leaves through the central vortex finder. The accumulated sand is dumped periodically.'),
    applications=['Wellhead and production flowlines', 'Protection of chokes, separators and pumps', 'Water injection and produced-water systems'],
    key_points=['Centrifugal (cyclonic) separation', 'Protects downstream equipment from erosion', 'Sand dumped by ΔP or level', 'Erosion-resistant materials at inlet and dump'],
    principle=[step('Fluid enters tangentially.', 'nozzles_valves', overlay='flow'), step('The swirl throws sand to the wall.', 'vessel', overlay='pressure'),
               step('Sand slides down into the cone.', 'sand_bed'), step('Clean fluid leaves via the vortex finder.', 'internals', overlay='flow'), step('The dump valve flushes sand out.', 'nozzles_valves')],
    curve='Separation efficiency vs particle size (d50 cut size) and inlet velocity.',
    params=fs(P('Vessel ~ 0.3 – 1.5 m diameter'), P('~ 100 – 50 000', 'bbl/d or m³/d'), P('Up to wellhead pressure (≈ 100 – 700+)', 'bar'), P('Removes sand typically > 50 – 100 µm', 'µm')),
    install=_VI, maint=_m([M('Monitor ΔP / sand level; dump.', 'nozzles_valves', 'daily')], [M('UT thickness at inlet.', 'vessel', 'quarterly')], [M('Replace wear parts and dump valve.', 'internals')], _NL),
    failures=[F('Erosion', ['Wall thinning'], ['High velocity sand'], ['Wear plates; reduce velocity'], 'vessel'), F('Dump valve failure', ['Sand overflow downstream'], ['Erosion of valve'], ['Hard-faced valve; maintenance'], 'nozzles_valves')],
    quiz=[Q('How does a sand trap separate sand?', ['Swirl throws dense sand to the wall', 'Filter cloth', 'Magnet', 'Heat'], 0, 'Cyclonic.'),
          Q('Why remove sand?', ['To prevent erosion of downstream equipment', 'To add weight', 'To heat', 'No reason'], 0, 'Erosion protection.'),
          Q('What triggers a sand dump?', ['Rising ΔP or sand level', 'Time of day only', 'Colour', 'Noise'], 0, 'Instrumentation.')],
    selection=['Size for flow and target d50; erosion allowance.'], safety=['High-pressure, erosive discharge — controlled dumping only.'], refs=['Maker desander data'])
