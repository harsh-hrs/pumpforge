"""Learning content — Safety & Environmental equipment, EQ-346 … EQ-360.
Typical ranges are general engineering guidance; standard editions are marked 'to be verified' in the model metadata."""
from pumpforge.learning import mod, step, P, F, Q, M

MODULES = {}


def se(size, capacity, conditions, performance, **extra):
    """Required parameters for the safety_environmental family: size, capacity, operating_conditions, performance."""
    ref = {'manufacturer': None, 'model': None, 'datasheet': None,
           'rated_point': {'capacity': None, 'design_pressure': None, 'design_temperature': None, 'performance_guarantee': None},
           'status': 'empty — fill from the equipment datasheet / safety study'}
    return dict(size=size, capacity=capacity, operating_conditions=conditions, performance=performance, reference_model=ref, extra=extra)


def _m(r, p, o, l):
    return dict(routine=r, periodic=p, overhaul=o, lubrication=l)


_PRC = dict(foundation=['Foundations / supports designed for operating, test, wind/seismic and (for relief) reaction loads.'],
            alignment=['Vessels plumb; headers sloped continuously as specified (no pockets).'],
            piping=['Relief/drain lines self-draining to the destination; supports for reaction and thermal loads; isolation valves car-sealed / locked as required.'],
            commissioning=['Pressure test; verify set pressures and certificates; function-test instruments and interlocks; record as-built in the safety documentation.'])
_ENVI = dict(foundation=['Structure for equipment, liquid / dust loads and wind; access platforms for maintenance.'],
             alignment=['Fans and pumps aligned; ducts supported to avoid loads on equipment.'],
             piping=['Corrosion-resistant materials for wet acid service; drains at low points; expansion joints on hot ducts.'],
             commissioning=['Run on air/water; check ΔP, flows and controls; then process gas; emission test against permit.'])
_FIREI = dict(foundation=['Supports per fire code; protected cabling and piping in fire zones.'],
              alignment=['Detectors aimed / monitors oriented per coverage study.'],
              piping=['Fire water / foam lines flushed; drains and test connections provided.'],
              commissioning=['Acceptance tests with witnesses (flow, foam ratio, detector function, cause & effect).'])
_NL = ['No routine lubrication (valve stems / actuators per maker).']
_LB = ['Fan / pump bearings and gearboxes per maker schedule.']

MODULES['emergency_pressure_relief_system'] = mod(
    definition=('An emergency pressure relief system protects equipment from overpressure. Spring-loaded safety valves (PSVs), often duplicated on an interlocked change-over valve, and/or a rupture disc open '
                'automatically at the set pressure and discharge into a closed relief header that drains to the flare knockout drum.'),
    applications=['Pressure vessels, columns, exchangers and reactors in process plants', 'Compressors, pumps (thermal relief) and storage systems'],
    key_points=['Last line of defence (not a control device)', 'Set ≤ MAWP; accumulation 10/16/21 %', 'Inlet loss < 3 %, back pressure within limits', 'Never isolate the only PSV'],
    principle=[step('A fire or upset raises vessel pressure.', 'contents', overlay='pressure'), step('The PSV disc lifts at set pressure.', 'psv_disc_spring', overlay='flow'),
               step('Gas flows into the relief header.', 'relief_header', overlay='flow'), step('The change-over valve keeps one PSV always in service.', 'changeover_valve'),
               step('The rupture disc gives fast full-bore relief if needed.', 'rupture_disc')],
    curve='PSV lift and flow vs pressure (set, overpressure, blowdown).',
    params=se(P('PSV orifices D … T (API 526)'), P('Sized for the worst credible case', 'kg/h'), P('Set ≤ MAWP; back pressure per valve type', '—'), P('Accumulation ≤ 10 % (single), 16 % (multiple), 21 % (fire)', '—')),
    install=_PRC, maint=_m([M('Check car-seals / change-over position.', 'changeover_valve', 'weekly')], [M('Bench-test PSVs per interval (RBI).', 'safety_valves', 'per interval')],
                          [M('Overhaul PSVs; replace rupture discs per schedule.', 'rupture_disc')], _NL),
    failures=[F('PSV chatter', ['Rapid opening/closing, damage'], ['High inlet loss, oversizing'], ['Fix inlet piping; resize'], 'safety_valves'), F('Stuck closed', ['No relief at set'], ['Fouling, corrosion'], ['Test & overhaul; rupture disc upstream'], 'safety_valves')],
    quiz=[Q('Fire-case accumulation allowed (typical)?', ['21 % above MAWP', '0 %', '50 %', '100 %'], 0, 'Fire case.'), Q('Purpose of the change-over valve?', ['Test/maintain one PSV while the other protects', 'Increase flow', 'Control pressure', 'Drain'], 0, 'Spare.'),
          Q('Maximum PSV inlet pressure loss (rule of thumb)?', ['≈ 3 % of set', '≈ 30 %', '≈ 50 %', 'No limit'], 0, '3 %.')],
    selection=['Size per API 520 for each scenario (API 521); choose conventional / balanced bellows / pilot by back pressure.'], safety=['Discharge to a safe location; never block relief paths; management of change for any set change.'], refs=['API 520', 'API 521'])

MODULES['blowdown_tank'] = mod(
    definition=('A boiler blowdown tank receives water blown down from boilers at high pressure and temperature. Entering tangentially, part of it flashes to steam that leaves through a large vent; the rest is '
                'retained, mixed with cooling water and drained at a safe temperature to the sewer.'),
    applications=['Continuous and intermittent (bottom) boiler blowdown', 'Drain collection from high-pressure steam traps and drains'],
    key_points=['Vented to atmosphere — never pressurised', 'Tangential inlet + wear plate', 'Cooling-water quench for discharge temperature', 'Siphon-loop drain holds a water seal'],
    principle=[step('Blowdown enters tangentially.', 'piping', overlay='flow'), step('It swirls and partly flashes to steam.', 'wear_plate', overlay='temperature'),
               step('Flash steam leaves through the vent.', 'piping', overlay='flow'), step('Retained water is cooled and drained.', 'water', overlay='temperature')],
    curve='Flash fraction vs boiler pressure.',
    params=se(P('Tanks ≈ 0.5 – 2 m diameter'), P('Sized for maximum blowdown rate', 'kg/s'), P('Atmospheric; inlet at boiler pressure', '—'), P('Drain ≤ ≈ 40–60 °C (local limit)', '—')),
    install=_PRC, maint=_m([M('Check vent is clear; discharge temperature.', 'piping', 'daily')], [M('Inspect wear plate and shell thickness.', 'wear_plate', 'annually')], [M('Repair erosion areas.', 'tank')], _NL),
    failures=[F('Tank pressurised', ['Steam leaks, overpressure'], ['Vent blocked or undersized'], ['Clear / resize vent'], 'piping'), F('Shell erosion', ['Thinning at inlet'], ['Worn wear plate'], ['Replace plate'], 'wear_plate')],
    quiz=[Q('Why tangential inlet?', ['Swirl separates steam and protects the shell (with wear plate)', 'Looks better', 'Cheaper', 'No reason'], 0, 'Swirl.'),
          Q('Can the vent have a valve?', ['No — tank must never be pressurised', 'Yes', 'Only at night', 'Only at start'], 0, 'Never valved.'), Q('Why add cooling water?', ['Limit drain temperature', 'Make steam', 'Raise pressure', 'Clean tank'], 0, 'Temperature limit.')],
    selection=['Size by blowdown flow and flash steam; vent area per guidance.'], safety=['Hot water / steam burns; never stand near the vent outlet.'], refs=['NBBI blowoff guidelines'])

MODULES['closed_drain_system'] = mod(
    definition=('A closed drain system collects hydrocarbons and hazardous liquids drained from process equipment through a closed, sloped header into a drum located below grade and vented to the flare, so '
                'nothing is released to atmosphere. A level-controlled pump returns the liquid to slop or process.'),
    applications=['Refineries, gas plants and offshore platforms', 'Chemical plants handling toxic or flammable liquids'],
    key_points=['Closed to atmosphere; vent to flare', 'Gravity flow — drum below grade', 'Never connect to open drains', 'Double block valves at drain points'],
    principle=[step('Drains open from equipment into the header.', 'drain_header', overlay='flow'), step('Liquid flows by gravity to the drum.', 'drain_drum'),
               step('Vapour goes to the flare.', 'vent_to_flare', overlay='flow'), step('The pump empties the drum on level.', 'pump_out_pump', overlay='flow')],
    curve='Drum level vs drain events and pump-out cycles.',
    params=se(P('Drums ≈ 1 – 3 m diameter'), P('Hold-up for the largest drain-down event', 'm³'), P('Near atmospheric (flare back pressure)', '—'), P('Pump-out on high level', '—')),
    install=_PRC, maint=_m([M('Check level and pump auto-start.', 'instruments', 'daily')], [M('Inspect pit for liquid / gas accumulation.', 'drum_pit', 'monthly')], [M('Internal inspection of drum.', 'drain_drum')], _LB),
    failures=[F('Drum overfill', ['High-level alarm'], ['Pump failure, big drain'], ['Repair; standby'], 'pump_out_pump'), F('Header plugging', ['Slow drainage'], ['Wax / solids, freezing'], ['Heat tracing; flushing'], 'drain_header')],
    quiz=[Q('Where is the closed drain drum vented?', ['To the flare', 'To atmosphere', 'To sewer', 'Not vented'], 0, 'Flare.'), Q('Why below grade?', ['Drains flow by gravity', 'Cooler', 'Hidden', 'Cheaper'], 0, 'Gravity.'),
          Q('Can it connect to open drains?', ['No', 'Yes', 'Sometimes', 'Only for water'], 0, 'Never.')],
    selection=['Size for drain-down of the largest system; materials for fluids; heating for waxy liquids.'], safety=['Pit is a confined space; gas testing before entry.'], refs=['API 521'])

MODULES['open_drain_system'] = mod(
    definition=('An open drain system collects non-pressurised spills, leaks, wash water and rainwater from paved process areas through drain hubs and trenches. Every inlet has a liquid seal so vapour and '
                'flame cannot travel through the network; oily water is collected in a sump, oil is skimmed and the water pumped to an oil-water separator.'),
    applications=['Process units, pump bays and loading areas', 'Tank farms and utility areas with oil contamination'],
    key_points=['Liquid seals (P-traps) at every inlet', 'Keep seals filled', 'Separate from closed drains', 'Oily water to OWS'],
    principle=[step('Spills drain into hubs under equipment.', 'drain_hubs_seals', overlay='flow'), step('Seals block vapour and fire paths.', 'drain_hubs_seals', overlay='pressure'),
               step('Water runs along the trench to the sump.', 'trench_grating', overlay='flow'), step('Oil is skimmed; water pumped to the OWS.', 'oil_skimmer', overlay='flow')],
    curve='Sump level vs rainfall / spill events.',
    params=se(P('Trenches ≈ 0.3 – 0.6 m wide'), P('Design rainfall + firewater', 'm³/h'), P('Atmospheric', '—'), P('Water seal depth ≈ 100–150 mm (typical)', '—')),
    install=_PRC, maint=_m([M('Top up seals; clear gratings.', 'drain_hubs_seals', 'weekly')], [M('Skim oil, desludge sump.', 'sump', 'monthly')], [M('Inspect trench and seals.', 'trench_grating')], _LB),
    failures=[F('Dry seal', ['Hydrocarbon smell in drains'], ['Evaporation'], ['Refill; use seal pots'], 'drain_hubs_seals'), F('Sump overflow', ['Oil spread'], ['Pump failure, heavy rain'], ['Repair; size for rain'], 'sump_pump')],
    quiz=[Q('Why liquid seals?', ['Stop vapour and fire travelling through drains', 'Look neat', 'Reduce flow', 'Add pressure'], 0, 'Seals.'), Q('Where does oily water go?', ['Oil-water separator', 'Flare', 'River', 'Closed drum'], 0, 'OWS.'),
          Q('What removes floating oil?', ['Skimmer', 'Pump', 'Grating', 'Trench'], 0, 'Skimmer.')],
    selection=['Size for rainfall, firewater and spills; fire-zone separation.'], safety=['Hot work near drains only with gas testing and sealed drains.'], refs=['Plant layout practice'])

MODULES['flare_stack'] = mod(
    definition=('A flare stack safely burns hydrocarbon gas released by relief valves, blowdown and upsets. Gas passes a water-seal drum (stopping flashback and air ingress), rises up the riser to the tip where '
                'continuous pilots ignite it; steam injected at the tip entrains air for smokeless burning. Its height limits radiation at grade.'),
    applications=['Refineries, petrochemical plants and gas processing', 'Production platforms and LNG facilities'],
    key_points=['Radiation sets height and location', 'Pilots always lit', 'Steam (or air) for smokeless burning', 'Water seal + purge prevent air ingress'],
    principle=[step('Relief gas arrives from the KO drum.', 'inlet_dip_leg', overlay='flow'), step('It bubbles through the water seal.', 'seal_water'), step('It rises up the riser.', 'riser', overlay='flow'),
               step('Pilots ignite it at the tip.', 'pilots_ignition'), step('Steam makes the flame smokeless.', 'flare_tip', overlay='temperature')],
    curve='Radiation at grade vs distance for different flare rates.',
    params=se(P('Heights ≈ 20 – 150 m; tips DN 100 – 1500'), P('Up to thousands of t/h (emergency)', 't/h'), P('Near-atmospheric back pressure', '—'), P('Grade radiation ≤ ≈ 1.58 kW/m² continuous (API 521)', '—')),
    install=_PRC, maint=_m([M('Monitor pilots, steam, flame (camera).', 'pilots_ignition', 'continuous')], [M('Check seal level and purge flow.', 'seal_drum', 'daily')], [M('Inspect tip and pilots at turnaround.', 'flare_tip')], _NL),
    failures=[F('Smoking flare', ['Black smoke'], ['Too little steam'], ['Increase steam ratio'], 'flare_tip'), F('Pilot out', ['Flame-out alarm'], ['Fuel / wind'], ['Re-ignite; repair'], 'pilots_ignition')],
    quiz=[Q('Why steam at the tip?', ['Entrain air for smokeless burning', 'Cool the stack', 'Raise pressure', 'Clean pilots'], 0, 'Smokeless.'), Q('What prevents flashback?', ['Water seal & purge / molecular seal', 'Pilots', 'Steam', 'Height'], 0, 'Seal.'),
          Q('What sets stack height?', ['Thermal radiation limits', 'Cost only', 'Wind only', 'Color'], 0, 'Radiation.')],
    selection=['Per API 521/537: radiation, smokeless capacity, noise, dispersion.'], safety=['Exclusion zones by radiation; never stop purge or pilots.'], refs=['API 521', 'API 537'])

MODULES['flare_knockout_drum'] = mod(
    definition=('A flare knockout drum removes liquid from relief gas before the flare. The large horizontal drum (split entry, central outlet) slows the gas so droplets settle; liquid is held and pumped out. '
                'This prevents a burning liquid rain from the flare tip.'),
    applications=['Main flare systems of refineries and gas plants', 'Unit flare headers with liquid carry-over'],
    key_points=['Droplets ≈ 300–600 µm settle', 'Hold-up ≈ 20–30 min of largest liquid release', 'Low pressure drop', 'Heating coil for cold climates'],
    principle=[step('Relief gas enters at both ends.', 'nozzles_piping', overlay='flow'), step('Gas slows across the drum.', 'drum', overlay='pressure'),
               step('Droplets settle out.', 'liquid'), step('Pumps remove the liquid on level.', 'pump_out_1', overlay='flow')],
    curve='Droplet settling velocity vs size (drag correlation).',
    params=se(P('Diameter ≈ 2 – 5 m, length ≈ 6 – 20 m'), P('Sized for the governing relief load', 't/h'), P('Near atmospheric', '—'), P('Remove droplets ≥ ≈ 300–600 µm', '—')),
    install=_PRC, maint=_m([M('Check level and pump status.', 'pump_lines_level', 'daily')], [M('Test high-level alarm.', 'pump_lines_level', 'monthly')], [M('Internal inspection.', 'drum')], _LB),
    failures=[F('Liquid carry-over to flare', ['Burning rain, smoke'], ['High level'], ['Pump out; alarms'], 'liquid'), F('Frozen drain', ['No pump-out'], ['Coil failure'], ['Repair coil; trace lines'], 'heating_coil')],
    quiz=[Q('Main job?', ['Remove liquid before the flare', 'Burn gas', 'Store gas', 'Cool steam'], 0, 'KO.'), Q('Why split entry?', ['Shares flow, lowers velocity', 'Cheaper', 'Noise', 'No reason'], 0, 'Lower velocity.'),
          Q('Why heating coil?', ['Prevent freezing / waxing', 'Raise pressure', 'Burn gas', 'Dry gas'], 0, 'Freezing.')],
    selection=['Size per API 521 for droplet removal and liquid hold-up.'], safety=['High-high level trips; drum is part of the relief path — never isolate.'], refs=['API 521'])

MODULES['gas_scrubbing_system'] = mod(
    definition=('A gas scrubbing system removes acid or toxic gases (H₂S, HCl, SO₂, Cl₂, NH₃) from a vent stream by absorbing them into a circulating liquid — here dilute caustic — in a packed tower. pH-controlled '
                'dosing keeps the liquor strong; an ID fan draws the gas through and discharges it up a stack.'),
    applications=['Process vents, tank vents and odour control', 'Emergency chlorine / ammonia scrubbers'],
    key_points=['Counter-current packed absorber', 'pH control keeps removal high', 'Removal > 99 % possible', 'Bleed spent liquor'],
    principle=[step('Contaminated gas enters below the packing.', 'gas_path', overlay='flow'), step('Liquor flows down over the packing.', 'distributor_demister', overlay='flow'),
               step('The gas dissolves and reacts with caustic.', 'packing', overlay='pressure'), step('Clean gas leaves via fan and stack.', 'fan_impeller', overlay='flow'),
               step('Dosing holds pH; spent liquor is bled.', 'liquor_circuit')],
    curve='Removal efficiency vs liquid/gas ratio and pH.',
    params=se(P('Towers ≈ 0.5 – 4 m diameter'), P('≈ 500 – 100,000', 'm³/h gas'), P('pH ≈ 8–10 (caustic)', '—'), P('Removal ≈ 95 – 99.9 %', '—')),
    install=_ENVI, maint=_m([M('Check pH, ΔP and recirculation flow.', 'liquor_circuit', 'daily')], [M('Clean packing / distributor.', 'packing', 'annually')], [M('Replace packing / pump parts.', 'recirc_pump')], _LB),
    failures=[F('Breakthrough', ['Odour / emission'], ['Low pH, low liquor flow'], ['Dose caustic; restore flow'], 'liquor_circuit'), F('Packing fouling', ['ΔP rise'], ['Salts / solids'], ['Wash / replace'], 'packing')],
    quiz=[Q('Why counter-current?', ['Strongest liquor meets cleanest gas', 'Cheaper', 'Less fan power', 'No reason'], 0, 'Driving force.'), Q('What controls caustic dosing?', ['pH', 'Temperature', 'Colour', 'Noise'], 0, 'pH.'),
          Q('Why bleed liquor?', ['Remove dissolved salts', 'Lower level only', 'Add caustic', 'Cool'], 0, 'Salts.')],
    selection=['From gas flow, composition and emission limit; packing height by NTU/HTU.'], safety=['Caustic handling; H₂S / Cl₂ toxicity; fan failure alarms.'], refs=['Perry\'s Handbook'])

MODULES['wet_scrubber'] = mod(
    definition=('A venturi wet scrubber removes fine dust and mist from gas. The gas accelerates through a narrow throat where injected liquid is shattered into fine droplets; particles impact the droplets, '
                'and a cyclonic separator then spins the dirty droplets out. It can also cool the gas and absorb soluble gases.'),
    applications=['Dust from kilns, dryers, furnaces and incinerators', 'Sticky / wet or explosive dusts unsuitable for bag filters'],
    key_points=['Efficiency rises with throat ΔP', 'High fan power', 'Produces slurry to treat', 'Handles hot, wet, sticky gases'],
    principle=[step('Dusty gas enters the converging section.', 'venturi', overlay='flow'), step('Liquid is injected at the throat.', 'liquid_injection', overlay='pressure'),
               step('Droplets capture particles.', 'venturi'), step('The separator removes droplets.', 'cyclonic_separator', overlay='flow'), step('Slurry is recycled / bled.', 'recycle_pump')],
    curve='Collection efficiency vs particle size for different throat ΔP.',
    params=se(P('Throats ≈ 0.1 – 1 m'), P('≈ 1,000 – 200,000', 'm³/h'), P('Throat ΔP ≈ 25 – 100 mbar', '—'), P('> 95–99 % for ≥ 1 µm (ΔP dependent)', '—')),
    install=_ENVI, maint=_m([M('Check ΔP, liquid flow and pH.', 'liquid_injection', 'daily')], [M('Inspect throat / nozzles for erosion.', 'venturi', 'quarterly')], [M('Reline throat; pump overhaul.', 'venturi')], _LB),
    failures=[F('Low efficiency', ['Visible emission'], ['Low ΔP / liquid flow'], ['Restore flow; adjust throat'], 'venturi'), F('Mist carry-over', ['Wet stack'], ['Separator overloaded'], ['Clean eliminator'], 'separator_outlet')],
    quiz=[Q('What drives venturi efficiency?', ['Throat pressure drop', 'Colour', 'Stack height', 'Pump speed'], 0, 'ΔP.'), Q('What does the cyclonic separator do?', ['Removes the dirty droplets', 'Adds water', 'Heats gas', 'Measures'], 0, 'Droplets.'),
          Q('A drawback?', ['High fan power & slurry treatment', 'No efficiency', 'Cannot handle hot gas', 'Silent'], 0, 'Energy & slurry.')],
    selection=['Throat ΔP from particle size and required efficiency.'], safety=['Corrosive slurry; confined spaces.'], refs=['EPA Cost Manual'])

MODULES['dry_scrubber'] = mod(
    definition=('A dry scrubber removes acid gases by injecting fine dry sorbent — hydrated lime or sodium bicarbonate — into the flue gas. The sorbent reacts with SO₂ and HCl in a reaction chamber; the dry '
                'product and unreacted sorbent are captured in a fabric filter, partly recirculated, and disposed of as powder with no wastewater.'),
    applications=['Waste incinerators, biomass and small coal boilers', 'Glass, cement and metal furnaces'],
    key_points=['No liquid effluent', 'Stoichiometric ratio ≈ 1.5–3', 'Bag filter cake adds contact', 'Temperature matters (NaHCO₃ > ≈ 140 °C)'],
    principle=[step('Sorbent is fed from the silo.', 'sorbent_silo'), step('It is blown into the duct through lances.', 'injection_lances', overlay='flow'),
               step('Acid gases react in the chamber.', 'reaction_chamber', overlay='pressure'), step('Solids go to the fabric filter.', 'outlet_filter', overlay='flow')],
    curve='Removal efficiency vs stoichiometric ratio.',
    params=se(P('Reactors ≈ 1 – 6 m diameter'), P('≈ 10,000 – 500,000', 'm³/h'), P('≈ 140 – 250 °C (sorbent dependent)', '—'), P('SO₂ ≈ 50–90 %, HCl ≈ 90–99 %', '—')),
    install=_ENVI, maint=_m([M('Check sorbent feed rate and stack emissions.', 'feeder_conveying', 'daily')], [M('Clear lances; inspect silo vent.', 'injection_lances', 'monthly')], [M('Inspect reactor / ducts for deposits.', 'reaction_chamber')], _LB),
    failures=[F('Poor removal', ['Emission high'], ['Low feed, bad mixing, wrong temperature'], ['Increase ratio; adjust lances'], 'feeder_conveying'), F('Feeder bridging', ['No sorbent'], ['Moisture'], ['Aeration; dry storage'], 'sorbent_silo')],
    quiz=[Q('Main advantage of dry scrubbing?', ['No wastewater', 'No solids', 'No fan', 'No filter'], 0, 'Dry product.'), Q('Where are products captured?', ['Fabric filter', 'Stack', 'Silo', 'Lances'], 0, 'Filter.'),
          Q('Typical sorbent?', ['Hydrated lime or sodium bicarbonate', 'Sand', 'Water', 'Sugar'], 0, 'Sorbents.')],
    selection=['Sorbent and ratio by acid-gas load and limits.'], safety=['Lime dust is caustic — PPE; silo entry is confined space.'], refs=['EPA Cost Manual'])

MODULES['baghouse_dust_collector'] = mod(
    definition=('A pulse-jet baghouse filters dust from gas through rows of fabric bags supported on wire cages. Dust builds a cake on the outside of the bags; short reverse pulses of compressed air flex the bags '
                'row by row so the cake falls into the hopper, from where a rotary airlock discharges it.'),
    applications=['Cement, mining, alumina and power plants', 'Dust extraction, kilns and dry-scrubber product collection'],
    key_points=['Outlet ≈ < 5–10 mg/Nm³', 'Air-to-cloth ≈ 0.8–1.5 m/min', 'ΔP-controlled pulsing', 'Watch temperature and dew point'],
    principle=[step('Dusty gas enters the dirty-gas chamber.', 'casing_hopper', overlay='flow'), step('Dust forms a cake on the bags.', 'filter_bags_row_1', overlay='pressure'),
               step('Clean gas leaves through the plenum.', 'filter_bags_cages', overlay='flow'), step('Pulses clean each row in turn.', 'pulse_cleaning'), step('The airlock discharges dust.', 'rotary_valve_rotor')],
    curve='Filter ΔP vs time between cleaning pulses.',
    params=se(P('Bags ≈ 120 – 160 mm × 2 – 8 m'), P('≈ 1,000 – 2,000,000', 'm³/h'), P('ΔP ≈ 1 – 1.5 kPa; temperature by bag material', '—'), P('Outlet < ≈ 5–10 mg/Nm³', '—')),
    install=_ENVI, maint=_m([M('Check ΔP and opacity / dust monitor.', 'pulse_cleaning', 'daily')], [M('Check pulse valves and compressed air.', 'pulse_cleaning', 'monthly')], [M('Replace bags (≈ 2–5 years).', 'filter_bags_row_1')], _LB),
    failures=[F('Bag leak', ['Dust emission spike'], ['Abrasion, burn holes'], ['Find & replace bag'], 'filter_bags_row_2'), F('High ΔP', ['Reduced airflow'], ['Blinding (moisture), cleaning failure'], ['Fix pulse; avoid dew point'], 'pulse_cleaning')],
    quiz=[Q('What actually filters the fine dust?', ['The dust cake on the bags', 'Cages', 'Hopper', 'Fan'], 0, 'Cake.'), Q('How are bags cleaned?', ['Reverse compressed-air pulse', 'Washing', 'Vibration only', 'Not cleaned'], 0, 'Pulse-jet.'),
          Q('Risk of running below dew point?', ['Wet, blinded bags', 'Faster flow', 'Lower ΔP', 'None'], 0, 'Blinding.')],
    selection=['Bag area from gas flow ÷ air-to-cloth ratio; media by temperature and chemistry.'], safety=['Combustible dust: explosion venting, spark arrestors; confined-space entry.'], refs=['EPA Cost Manual'])

MODULES['ventilation_system'] = mod(
    definition=('An industrial ventilation system supplies filtered, conditioned air to a room and exhausts contaminated air, removing heat and diluting gases. Supply slightly exceeding exhaust keeps electrical '
                'and control rooms at positive pressure so dust and flammable gas cannot enter; low-level exhaust removes heavy vapours.'),
    applications=['Electrical / control rooms, analyser houses, battery rooms', 'Process buildings, workshops and compressor houses'],
    key_points=['Air changes or heat-load based rate', 'Positive pressure ≈ 25–50 Pa', 'Fire dampers close on alarm', 'Filters keep equipment clean'],
    principle=[step('The AHU draws and filters outdoor air.', 'air_handling_unit', overlay='flow'), step('The supply fan pushes it through ducts.', 'supply_fan', overlay='flow'),
               step('Diffusers spread it across the room.', 'supply_ductwork'), step('Exhaust removes heat and contaminants.', 'exhaust_fan', overlay='flow'), step('Sensors hold room pressure.', 'controls_equipment', overlay='pressure')],
    curve='Room temperature vs air flow for a given heat load.',
    params=se(P('Rooms ≈ 20 – 2000 m²'), P('≈ 1,000 – 200,000', 'm³/h'), P('Room ΔP ≈ +25–50 Pa; temperature ≈ 20–30 °C', '—'), P('≈ 6–12 air changes/h (typical)', '—')),
    install=_ENVI, maint=_m([M('Check room ΔP and temperature.', 'controls_equipment', 'daily')], [M('Change filters on ΔP.', 'air_handling_unit', 'quarterly')], [M('Service fans, coils, dampers.', 'supply_fan')], _LB),
    failures=[F('Loss of pressurisation', ['Alarm'], ['Fan trip, door open'], ['Restore fan; door closers'], 'supply_fan'), F('Overheating', ['High room temperature'], ['Blocked filter, coil fouled'], ['Clean / replace'], 'air_handling_unit')],
    quiz=[Q('Why positive pressure in electrical rooms?', ['Keep dust and flammable gas out', 'Cool faster', 'Less noise', 'No reason'], 0, 'Ingress.'), Q('Why low-level exhaust?', ['Remove heavier-than-air vapours', 'Look nice', 'Save fan', 'Heat'], 0, 'Heavy gas.'),
          Q('What closes on fire alarm?', ['Fire dampers', 'Doors only', 'Filters', 'Coils'], 0, 'Dampers.')],
    selection=['Flow from heat load, dilution and pressurisation needs.'], safety=['Hazardous-area rules for equipment; interlocks with gas detection.'], refs=['ASHRAE', 'IEC 60079'])

MODULES['emergency_ventilation_fan'] = mod(
    definition=('An emergency ventilation fan is an explosion-protected axial fan that starts automatically when gas detectors alarm, purging the building to dilute a leak below its flammable range. The impeller and '
                'casing are a non-sparking pair, the motor is flameproof, and a gravity damper closes when the fan stops.'),
    applications=['Compressor houses, analyser shelters, battery rooms', 'Pump houses and enclosed process modules'],
    key_points=['Auto-start at ≈ 10–20 % LEL', 'Ex-rated motor and non-sparking materials', 'Gravity back-draught damper', 'On essential power'],
    principle=[step('A gas detector senses the leak.', 'detection_control'), step('The panel starts the fan.', 'motor', overlay='flow'), step('The impeller extracts air.', 'impeller', overlay='pressure'),
               step('Damper blades open with fan pressure.', 'damper_blade_3')],
    curve='Gas concentration decay vs air changes (dilution curve).',
    params=se(P('Fans ≈ 300 – 1500 mm'), P('≈ 2,000 – 100,000', 'm³/h'), P('Zone 1/2, gas group IIA–IIC, T-class', '—'), P('Purge to < 10 % LEL rapidly (design)', '—')),
    install=_ENVI, maint=_m([M('Check standby status and alarms.', 'detection_control', 'daily')], [M('Run test; bump-test detector.', 'motor', 'monthly')], [M('Inspect tip clearance, Ex integrity.', 'fan_casing')], _LB),
    failures=[F('Fan fails to start', ['No ventilation on alarm'], ['Power / starter fault'], ['Test regularly; essential supply'], 'motor'), F('Impeller rub', ['Noise, spark risk'], ['Bearing wear'], ['Stop; repair'], 'impeller')],
    quiz=[Q('Why non-sparking materials?', ['A rub must not ignite gas', 'Lighter', 'Cheaper', 'Colour'], 0, 'Ignition.'), Q('What starts it?', ['Gas detection alarm', 'Timer only', 'Temperature only', 'Manual only'], 0, 'Gas.'),
          Q('What does the gravity damper do?', ['Close when fan stops', 'Open always', 'Control speed', 'Filter'], 0, 'Back-draught.')],
    selection=['Size by room volume and purge rate; Ex rating by area classification.'], safety=['Maintain Ex integrity; never defeat interlocks.'], refs=['EN 14986', 'IEC 60079'])

MODULES['fire_and_gas_detection_system'] = mod(
    definition=('A fire and gas (F&G) detection system watches a process area for gas leaks and fires. Point and open-path gas detectors, flame detectors, heat and smoke detectors and manual call points feed a '
                'SIL-rated logic panel that raises alarms and starts executive actions such as shutdown, isolation, deluge and ventilation changes.'),
    applications=['Process modules, compressor and pump areas', 'Offshore platforms, terminals and tank farms'],
    key_points=['Coverage mapping places detectors', 'Alarm at 20 % LEL, action at ≈ 50–60 % LEL', 'Voting avoids spurious trips', 'Regular bump tests & proof tests'],
    principle=[step('Gas leaks from a flange.', 'process_equipment', overlay='flow'), step('Point and open-path detectors sense it.', 'point_gas_detectors', overlay='pressure'),
               step('Flame detectors watch their cones of vision.', 'flame_heat_alarm_devices', overlay='pressure'), step('The F&G panel votes and acts.', 'fg_panel', overlay='flow')],
    curve='Detection probability vs number / placement of detectors (coverage).',
    params=se(P('Areas from single modules to whole plants'), P('Tens to thousands of detectors', '—'), P('Hazardous area rated devices', '—'), P('SIL 1–2 logic typical (by study)', '—')),
    install=_FIREI, maint=_m([M('Check panel faults / inhibits.', 'fg_panel', 'daily')], [M('Bump-test gas detectors; clean optics.', 'point_gas_detectors', 'quarterly')], [M('Full cause & effect proof test.', 'fg_panel')], _NL),
    failures=[F('Detector blinded', ['Fault / no response'], ['Dirty optics, blocked view'], ['Clean; re-aim'], 'flame_heat_alarm_devices'), F('Spurious trip', ['Unplanned shutdown'], ['Single-detector logic, interference'], ['Voting; shielding'], 'fg_panel')],
    quiz=[Q('Typical first gas alarm?', ['20 % LEL', '100 % LEL', '1 % LEL', '200 % LEL'], 0, 'Low alarm.'), Q('Open-path detectors measure…', ['Gas along a beam between transmitter and receiver', 'Temperature', 'Flow', 'Pressure'], 0, 'Line of sight.'),
          Q('Why voting logic?', ['Avoid spurious actions', 'Faster alarms', 'Cheaper', 'No reason'], 0, 'Reliability.')],
    selection=['By hazard study and coverage mapping (ISA TR84.00.07).'], safety=['Manage inhibits strictly; test after maintenance.'], refs=['ISA TR84.00.07', 'IEC 61511'])

MODULES['firewater_monitor'] = mod(
    definition=('A firewater monitor is a fixed, swivelling nozzle mounted on a hydrant riser that throws a large stream of water — straight jet for reach or fog for cooling. Oscillating monitors sweep '
                'automatically using a water-powered drive so equipment can be cooled without people nearby.'),
    applications=['Cooling of tanks, vessels and structures during fires', 'Process areas, jetties and loading racks'],
    key_points=['≈ 1000–4000 L/min at ≈ 7 bar', 'Jet for reach, fog for cooling', 'Oscillating = unattended coverage', 'Q = K·√P'],
    principle=[step('Water comes up the riser.', 'riser_valve', overlay='flow'), step('The monitor head swivels and elevates.', 'monitor_head'), step('The nozzle forms jet or fog.', 'water_jet', overlay='pressure'),
               step('Water cools the protected equipment.', 'protected_equipment', overlay='flow')],
    curve='Reach vs nozzle pressure and elevation angle.',
    params=se(P('DN 65 – 150 monitors'), P('≈ 1,000 – 4,000 (plant) up to > 10,000', 'L/min'), P('≈ 7 – 10 bar at nozzle', '—'), P('Straight-stream reach ≈ 40 – 70 m', '—')),
    install=_FIREI, maint=_m([M('Visual check; drains clear.', 'riser_valve', 'monthly')], [M('Operate through full range; flow test.', 'monitor_head', 'annually')], [M('Overhaul swivels and nozzle.', 'monitor_head')], ['Grease swivel joints per maker.']),
    failures=[F('Seized swivel', ['Cannot aim'], ['Corrosion, no exercise'], ['Lubricate; exercise'], 'monitor_head'), F('Short reach', ['Weak stream'], ['Low pressure, debris in nozzle'], ['Check supply; clean'], 'water_jet')],
    quiz=[Q('Fog vs jet?', ['Fog cools/protects, jet reaches far', 'Same', 'Fog reaches farther', 'Jet cools better'], 0, 'Patterns.'), Q('Flow vs pressure?', ['Q ∝ √P', 'Q ∝ P²', 'Q constant', 'Q ∝ 1/P'], 0, '√P.'),
          Q('Why oscillating?', ['Unattended sweeping coverage', 'Save water', 'Noise', 'Looks good'], 0, 'Unattended.')],
    selection=['Flow and reach from fire-water study; materials for environment.'], safety=['High-pressure stream can injure — keep clear; test only in safe directions.'], refs=['NFPA 24', 'NFPA 15'])

MODULES['foam_firefighting_system'] = mod(
    definition=('A foam firefighting system extinguishes flammable-liquid fires. Fire water passes a ratio controller that draws foam concentrate from a bladder tank at a fixed percentage; foam chambers on the '
                'storage tank aspirate air to expand the solution and pour it gently onto the liquid surface, where the blanket smothers, cools and seals the fire.'),
    applications=['Hydrocarbon storage tanks and bund areas', 'Loading racks, aircraft hangars and process areas'],
    key_points=['Proportioning ≈ 1 % / 3 %', 'Application rate per NFPA 11', 'Blanket separates fuel and air', 'Alcohol-resistant foam for polar solvents'],
    principle=[step('Water flows through the deluge valve.', 'proportioning', overlay='flow'), step('The ratio controller draws concentrate from the bladder tank.', 'bladder_concentrate', overlay='flow'),
               step('Foam chambers expand and apply foam.', 'foam_chambers', overlay='flow'), step('The blanket spreads and the fire goes out.', 'foam_blanket', overlay='pressure')],
    curve='Extinguishing time vs application rate.',
    params=se(P('Tanks up to tens of metres diameter'), P('Application ≈ 4.1 L/min·m² (hydrocarbon, fixed outlets — verify)', 'L/min·m²'), P('Concentrate 1 % / 3 % (AFFF / AR-AFFF / F3)', '—'), P('Discharge time ≈ 30–55 min (fuel/system)', '—')),
    install=_FIREI, maint=_m([M('Check bladder tank and valves (visual).', 'bladder_tank', 'monthly')], [M('Concentrate sample test; proportioning test.', 'proportioning', 'annually')], [M('Inspect foam chambers & vapour seals.', 'foam_chambers')], _NL),
    failures=[F('Wrong proportioning', ['Weak / no foam'], ['Ratio controller fault, wrong concentrate'], ['Test & repair'], 'proportioning'), F('Bladder failure', ['Concentrate contaminated'], ['Leaking bladder'], ['Replace'], 'bladder_tank')],
    quiz=[Q('How does foam extinguish?', ['Smothers, cools and suppresses vapour', 'Adds oxygen', 'Heats fuel', 'Dilutes air'], 0, 'Blanket.'), Q('What draws concentrate in at a fixed ratio?', ['Ratio controller (proportioner)', 'Pump only', 'Fan', 'Chamber'], 0, 'Proportioner.'),
          Q('Foam for alcohols?', ['Alcohol-resistant (AR) foam', 'Any water', 'Dry powder only', 'Steam'], 0, 'AR foam.')],
    selection=['Per NFPA 11 by fuel, tank type and size.'], safety=['PFAS foams: environmental controls on testing and run-off.'], refs=['NFPA 11'])
