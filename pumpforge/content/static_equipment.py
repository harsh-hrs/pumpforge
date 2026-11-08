"""Learning content — Static Equipment, additional items (EQ-171 … EQ-195)."""
from pumpforge.learning import mod, step, P, F, Q, M

MODULES = {}


def se(size, pressure, temperature, capacity, **extra):
    ref = {'manufacturer': None, 'model': None, 'datasheet': None,
           'rated_point': {'capacity': None, 'design_pressure': None, 'design_temperature': None, 'duty_or_volume': None, 'material': None},
           'status': 'empty — fill from the equipment datasheet / U-1A or nameplate'}
    return dict(size=size, design_pressure=pressure, design_temperature=temperature, capacity=capacity, reference_model=ref, extra=extra)


_V_INST = dict(
    foundation=['Set on a level foundation designed for operating, hydro-test and wind/seismic loads; grout base plates; anchor bolts per drawing.'],
    alignment=['Check verticality (vertical vessels) or level and slope (horizontal); one saddle bolted, the other slotted for thermal expansion.'],
    piping=['Connect nozzles without forcing — check allowable nozzle loads; support piping independently.', 'Fit the required pressure relief device and isolation as per code.'],
    commissioning=['Hydro/pneumatic test per code; inspect internals before closing; purge and leak test; commission instruments and relief valves.'])
_T_INST = dict(
    foundation=['Ring-wall or slab foundation with settlement monitoring; tank bottom with drainage slope and leak detection.'],
    alignment=['Check shell plumbness and roundness after erection (API 650 tolerances).'],
    piping=['Flexible connections at shell nozzles to absorb settlement; fire protection and bunding per code.'],
    commissioning=['Hydrostatic test with settlement survey; calibrate level gauges and overfill protection.'])
_HX_INST = dict(
    foundation=['Support on saddles/structure designed for full-of-water weight; allow one end to slide.'],
    alignment=['Provide pull-out space for tube bundles or plates; align nozzles to piping without strain.'],
    piping=['Install vents and drains on both sides; fit strainers where fouling solids are expected.', 'Arrange counter-current connections as designed.'],
    commissioning=['Pressure-test each side; vent air; bring flows on gradually to avoid thermal shock.'])
_RX_INST = dict(_V_INST, commissioning=['Pressure and leak test; check agitator rotation and seal flush; calibrate temperature/pressure instruments; test interlocks and relief devices.'])


def _m(r, p, o, l):
    return dict(routine=r, periodic=p, overhaul=o, lubrication=l)


_NOLUBE = ['No lubrication — static equipment (lubricate valve stems and manway hinges only).']

MODULES['double_pipe_heat_exchanger'] = mod(
    definition=('A double pipe heat exchanger has one pipe inside another. The hot fluid flows through the inner tube and the cold fluid through the annulus around it, in opposite directions '
                '(counter-current). Heat passes through the inner tube wall. Several hairpins can be connected in series for more area.'),
    applications=['Small duties and high-pressure services', 'Sludges and viscous fluids (finned/scraped versions)', 'Pilot plants and process heating/cooling', 'Lube-oil coolers'],
    key_points=['Simple and easy to clean', 'True counter-current flow', 'Q = U·A·LMTD', 'Economical up to ~ 30–50 m² per unit'],
    principle=[step('Hot fluid enters the inner tube.', 'inner_tube', overlay='flow'), step('Cold fluid enters the annulus at the far end and flows the opposite way.', 'shell_pipes', overlay='flow'),
               step('Heat passes through the tube wall from hot to cold.', 'inner_tube', overlay='temperature'), step('The return bend links the two legs of the hairpin.', 'nozzles')],
    curve='Temperature profiles along the length; LMTD for counter-current > co-current for the same terminal temperatures.',
    params=se(P('Inner tube ~ 20 – 100 mm; outer ~ 50 – 200 mm'), P('Up to ~ 300+ (high-pressure hairpins)', 'bar'), P('-50 to 500 (material dependent)', '°C'), P('Area ~ 1 – 50 m² per hairpin', 'm²')),
    install=_HX_INST, maint=_m([M('Monitor outlet temperatures and ΔP.', 'nozzles', 'daily')], [M('Clean tube and annulus (mechanical/chemical).', 'inner_tube', 'as fouling dictates')],
                               [M('Hydro-test; replace gaskets/inner tube.', 'shell_pipes')], _NOLUBE),
    failures=[F('Fouling', ['Falling duty, rising ΔP'], ['Deposits, scale'], ['Clean; raise velocity'], 'inner_tube'), F('Leak between fluids', ['Contamination'], ['Tube corrosion, cracked bend'], ['Replace tube'], 'inner_tube')],
    quiz=[Q('Why is counter-current flow preferred?', ['Easier piping', 'Larger mean temperature difference → more heat transfer', 'Lower pressure drop', 'Cheaper'], 1, 'Higher LMTD.'),
          Q('Heat transfer rate is given by…', ['Q = m·g·h', 'Q = U·A·ΔT_lm', 'Q = ½ m v²', 'Q = P/V'], 1, 'Basic exchanger equation.'),
          Q('Where does the cold fluid flow?', ['Inside the inner tube', 'In the annulus', 'Outside the outer pipe', 'In the bend only'], 1, 'Annulus side.')])

MODULES['air_cooled_heat_exchanger'] = mod(
    definition=('An air-cooled heat exchanger (fin-fan) cools or condenses a process stream with ambient air. The fluid flows through finned tubes between header boxes; axial fans force air across '
                'the bundle. It removes the need for cooling water.'),
    applications=['Refinery and gas-plant product coolers and condensers', 'Compressor inter/after-coolers', 'Power-plant air-cooled condensers', 'Remote sites without water'],
    key_points=['No cooling water needed', 'Outlet limited to ~ 10–15 °C above ambient', 'Fins increase air-side area 15–25×', 'Fan pitch/VFD/louvres control'],
    principle=[step('Hot fluid enters the inlet header and is spread over the tubes.', 'headers', overlay='flow'), step('Fans push ambient air up through the finned bundle.', 'fan_1', overlay='flow'),
               step('Heat passes from the fluid through the tube and fins into the air.', 'tube_bundle'), step('Cooled fluid leaves through the outlet header nozzle.', 'nozzles')],
    curve='Duty falls as ambient air temperature rises; design on summer ambient.',
    params=se(P('Bundles up to ~ 12 m long, 3–4 m wide'), P('Up to ~ 200+', 'bar'), P('Up to ~ 350 (fin type limited)', '°C'), P('0.1 – 50 MW per bay', 'MW')),
    install=_HX_INST | dict(foundation=['Elevate on structure with free air inlet; avoid hot-air recirculation and nearby obstructions.']),
    maint=_m([M('Check fan vibration and belt/drive.', 'fan_1', 'weekly')], [M('Wash fins (low-pressure water).', 'tube_bundle', '6–12 months'), M('Check fan pitch and tip clearance.', 'fan_2', 'annual')],
             [M('Remove plugs; clean and inspect tubes.', 'headers')], ['Grease fan shaft bearings; lubricate gearboxes if fitted.']),
    failures=[F('Fin fouling', ['High outlet temperature'], ['Dust, insects, fibres'], ['Clean fins'], 'tube_bundle'), F('Fan failure', ['Loss of capacity, vibration'], ['Bearing/belt failure'], ['Repair drive'], 'drive_1')],
    quiz=[Q('What limits the outlet temperature of an air cooler?', ['Tube length only', 'Ambient air temperature', 'Fan colour', 'Header size'], 1, 'Approach to ambient.'),
          Q('Why are the tubes finned?', ['Strength', 'Air has a low heat-transfer coefficient — fins add area', 'Noise', 'Weight'], 1, 'Extended surface.'),
          Q('Forced draft means the fans are…', ['Above the bundle pulling air', 'Below the bundle pushing air', 'Inside the tubes', 'Absent'], 1, 'Induced draft pulls from above.')])

MODULES['spiral_heat_exchanger'] = mod(
    definition=('A spiral heat exchanger is two long plates wound into a spiral, forming two separate channels. One fluid spirals inward, the other outward — counter-current in single channels. '
                'The curved channel and high shear make it self-cleaning, ideal for fouling liquids and slurries.'),
    applications=['Slurries, sludges and fibrous liquids', 'Heat recovery in pulp & paper and wastewater', 'Condensing vapours', 'Viscous and fouling process fluids'],
    key_points=['Single channel per side — no bypassing', 'Self-cleaning effect', 'Compact', 'Covers open for full channel access'],
    principle=[step('Hot fluid enters at the periphery and spirals toward the centre.', 'spiral_plates', overlay='flow'), step('Cold fluid enters at the centre cover and spirals outward.', 'rear_cover', overlay='flow'),
               step('Heat passes through the spiral plates between the channels.', 'spiral_plates'), step('Covers seal alternate sides of the channels and open for cleaning.', 'front_cover')],
    curve='High U values thanks to curved-flow turbulence; ΔP scales with channel length.',
    params=se(P('Up to ~ 1.8 m diameter'), P('Up to ~ 25', 'bar'), P('Up to ~ 400', '°C'), P('Up to ~ 500 m² per unit', 'm²')),
    install=_HX_INST, maint=_m([M('Monitor ΔP and temperatures.', 'shell', 'daily')], [M('Open covers and flush/clean channels.', 'front_cover', 'as needed')], [M('Replace cover gaskets.', 'rear_cover')], _NOLUBE),
    failures=[F('Channel blockage', ['High ΔP'], ['Solids above design size'], ['Open covers, clean; add strainer'], 'spiral_plates'), F('Gasket leak', ['External leak'], ['Ageing'], ['Replace gasket'], 'front_cover')],
    quiz=[Q('Why do spiral exchangers resist fouling?', ['Smooth paint', 'Single curved channel with high shear scrubs deposits', 'Cold walls', 'Magnetic'], 1, 'Self-cleaning.'),
          Q('How many channels does it have?', ['One', 'Two (one per fluid)', 'Hundreds of tubes', 'Four'], 1, 'Two spiral channels.'),
          Q('Flow arrangement?', ['Co-current only', 'Counter-current', 'Cross only', 'None'], 1, 'In/out spirals.')])

MODULES['jacketed_vessel'] = mod(
    definition=('A jacketed vessel has an outer jacket around its lower shell. Steam, hot oil or cooling water flows through the jacket space and heats or cools the contents through the vessel wall. '
                'A spiral baffle in the jacket makes the medium flow fast around the vessel for good heat transfer.'),
    applications=['Batch heating/cooling in chemicals, food and pharma', 'Melting and holding tanks', 'Crystallisers and reactors', 'Storage of temperature-sensitive products'],
    key_points=['No contact between medium and product', 'Jacket pressure acts externally on the shell', 'Heat transfer limited by wall area', 'Spiral baffle raises velocity'],
    principle=[step('The heating/cooling medium enters the jacket.', 'jacket', overlay='flow'), step('The spiral baffle guides it round the vessel.', 'spiral_baffle'),
               step('Heat passes through the vessel wall into the product.', 'vessel'), step('The product level rises and falls as the batch is filled and emptied.', 'product')],
    curve='Batch heating time from Q = U·A·ΔT; U drops if the product is viscous or the wall fouls.',
    params=se(P('Vessel 0.1 – 50 m³'), P('Vessel FV–10 bar; jacket ~ 3–10 bar', 'bar'), P('-20 to 200', '°C'), P('Working volume', 'm³')),
    install=_V_INST, maint=_m([M('Check jacket steam trap and temperatures.', 'nozzles', 'daily')], [M('Descale jacket; inspect inner surface.', 'jacket', 'annual')], [M('Hydro-test both spaces.', 'vessel')], _NOLUBE),
    failures=[F('Poor heating', ['Long batch times'], ['Air/condensate in jacket, scale'], ['Vent, fix trap, descale'], 'jacket'), F('Inner shell buckling', ['Deformation'], ['Excess jacket pressure / vacuum inside'], ['Relief on jacket; vacuum breaker'], 'vessel')],
    quiz=[Q('What is the jacket for?', ['Insulation only', 'To carry a heating/cooling medium against the vessel wall', 'Mixing', 'Storage'], 1, 'Indirect heat transfer.'),
          Q('Jacket pressure on the inner shell is…', ['Internal', 'External — check for buckling', 'Zero', 'Irrelevant'], 1, 'External pressure design.'),
          Q('The spiral baffle…', ['Mixes the product', 'Increases medium velocity in the jacket', 'Supports the vessel', 'Seals the lid'], 1, 'Better h.')])

MODULES['agitated_reactor'] = mod(
    definition=('An agitated reactor is a vessel with a motor-driven agitator in which reactions are carried out. Impellers mix the contents, baffles turn swirl into top-to-bottom circulation, and a '
                'jacket and/or internal coil add or remove heat to keep the reaction at the right temperature.'),
    applications=['Batch chemical and pharmaceutical synthesis', 'Polymerisation', 'Fermentation (bioreactors)', 'Neutralisation and crystallisation'],
    key_points=['Mixing + heat transfer + residence time', 'Baffles prevent vortexing', 'Power ∝ N³·D⁵ (turbulent)', 'Seal and temperature control critical'],
    principle=[step('The drive turns the agitator shaft.', 'agitator_drive', cut=False), step('Pitched-blade impellers pump liquid down; it rises at the walls.', 'agitator', overlay='flow'),
               step('Baffles stop the liquid swirling round as a whole.', 'baffles'), step('The jacket and coil remove the reaction heat.', 'cooling_coil', overlay='flow'),
               step('Reactants enter through the top nozzles; product leaves at the bottom.', 'nozzles')],
    curve='Power number vs Reynolds number for the impeller type; heat-removal capacity vs reaction rate.',
    params=se(P('0.05 – 100 m³'), P('FV – 10 (typical)', 'bar'), P('-30 to 250', '°C'), P('Working volume', 'm³'), agitator_power=P('~ 0.1 – 3 kW/m³', 'kW/m³')),
    install=_RX_INST, maint=_m([M('Check seal, agitator current, temperatures.', 'agitator_drive', 'daily')], [M('Inspect impellers, baffles, coil.', 'agitator', 'annual')],
                                [M('Seal and gearbox overhaul.', 'agitator_drive')], ['Gearbox oil and motor bearings; seal support system fluid.']),
    failures=[F('Runaway temperature', ['Temperature/pressure rise'], ['Cooling failure, overcharge'], ['Emergency cooling/quench; relief'], 'cooling_coil'),
              F('Seal leakage', ['Leak at agitator'], ['Seal wear, shaft run-out'], ['Replace seal; check run-out'], 'agitator_drive'), F('Poor mixing', ['Hot spots, off-spec'], ['Wrong speed/impeller, missing baffles'], ['Review mixing design'], 'agitator')],
    quiz=[Q('Why fit baffles?', ['Strength', 'Convert swirl into vertical circulation', 'Cooling', 'Support the shaft'], 1, 'Better mixing.'),
          Q('Doubling agitator speed changes power by about…', ['×2', '×4', '×8', '×16'], 2, 'P ∝ N³.'),
          Q('Reaction heat is removed by…', ['The motor', 'Jacket and coil', 'Baffles', 'Nozzles'], 1, 'Heat transfer surfaces.')])

MODULES['pressure_reactor'] = mod(
    definition=('A high-pressure reactor carries out reactions such as hydrogenation at high pressure and temperature. Its thick forged body and bolted cover with a metal seal contain the pressure; '
                'a magnetic drive stirs without a shaft seal, gas is fed through a sparger, and a coil removes heat. Relief valve and rupture disc protect against over-pressure.'),
    applications=['Hydrogenation', 'Polymerisation and oxidation under pressure', 'Catalyst testing and R&D', 'Supercritical processes'],
    key_points=['Design pressure and temperature on nameplate', 'Bolted closure torqued in sequence', 'Sealless magnetic drive', 'Relief for runaway cases'],
    principle=[step('Liquid is charged and the cover bolted with a metal seal ring.', 'closure', cut=False), step('Gas is fed through the sparger ring at the bottom.', 'internals', overlay='flow'),
               step('The magnetically driven turbines disperse the gas into the liquid.', 'agitator', overlay='flow'), step('The coil removes reaction heat.', 'internals'),
               step('Safety valve and rupture disc protect against over-pressure.', 'safety_instruments', cut=False)],
    curve='Gas uptake rate vs pressure and agitation; heat release vs cooling capacity.',
    params=se(P('0.05 L – 5 m³'), P('Up to ~ 350 (lab) / ~ 200 (production)', 'bar'), P('Up to ~ 500', '°C'), P('Volume', 'L')),
    install=_RX_INST, maint=_m([M('Leak test closure before each run.', 'closure', 'each batch')], [M('Replace seal ring; check stud threads.', 'closure', 'per runs')],
                                [M('Re-certify vessel (hydro-test, NDT).', 'body')], ['Anti-seize on studs; magnetic-drive bearings per maker.']),
    failures=[F('Closure leak', ['Pressure decay'], ['Damaged seal, uneven bolt torque'], ['Replace seal; torque in star pattern'], 'closure'),
              F('Decoupling of magnetic drive', ['Agitation stops'], ['High viscosity, overheating'], ['Reduce load; check magnets'], 'magnetic_drive')],
    quiz=[Q('Why use a magnetic drive?', ['Cheaper', 'No rotating shaft seal → no leakage path', 'Faster', 'Quieter only'], 1, 'Sealless.'),
          Q('Studs of a bolted closure should be tightened…', ['All at once', 'In a star/criss-cross pattern in stages', 'Randomly', 'Only finger tight'], 1, 'Even seal load.'),
          Q('Why both a safety valve and a rupture disc?', ['Decoration', 'Disc protects the valve/gives fast full relief; valve recloses', 'Required by colour code', 'No reason'], 1, 'Combined protection.')])

MODULES['autoclave'] = mod(
    definition=('An autoclave is a pressure vessel that treats a load with heat and pressure (steam or hot gas) — for curing composites, vulcanising rubber, treating wood or sterilising. A quick-opening '
                'door locked by a rotating ring allows fast loading; safety interlocks prevent opening while pressurised.'),
    applications=['Aerospace composite curing', 'Rubber vulcanising', 'Medical/waste sterilisation', 'Autoclaved aerated concrete, glass laminating'],
    key_points=['Quick-opening closure needs interlocks', 'Pressure–temperature cycle controlled', 'Fatigue from cycling', 'Vacuum often used before steam'],
    principle=[step('The load cart is rolled in on rails.', 'load_cart'), step('The door closes and the locking ring rotates to engage the lugs.', 'lock_ring', cut=False),
               step('Steam enters through the distributor; the fan evens the temperature.', 'steam_distributor', overlay='flow'), step('After the hold time, pressure is released, the ring unlocks and the door opens.', 'door', cut=False)],
    curve='Cycle chart: vacuum → ramp → hold (pressure & temperature) → cool/vent.',
    params=se(P('Ø 0.5 – 10 m; length up to ~ 40 m'), P('Up to ~ 10–20 (composites); ~3 (sterilisers)', 'bar'), P('Up to ~ 400', '°C'), P('Chamber volume', 'm³')),
    install=_V_INST, maint=_m([M('Check door seal and interlock function.', 'door', 'each cycle')], [M('Inspect lock-ring lugs (NDT); calibrate sensors.', 'lock_ring', 'annual')],
                               [M('Pressure-vessel inspection; replace door seal.', 'shell')], ['Grease lock-ring guides and door hinge.']),
    failures=[F('Door seal leak', ['Steam leak at door'], ['Worn/damaged seal'], ['Replace seal'], 'door'), F('Interlock fault', ['Door cannot open/close'], ['Sensor failure'], ['Repair — never bypass'], 'lock_ring')],
    quiz=[Q('What prevents opening the door under pressure?', ['Operator memory', 'Safety interlocks', 'Gravity', 'Nothing'], 1, 'Mandatory for quick-actuating closures.'),
          Q('Why rotate a locking ring?', ['Decoration', 'To engage/disengage the door lugs (bayonet)', 'To heat the door', 'To seal electrically'], 1, 'Quick closure.'),
          Q('Why run a fan inside?', ['Cooling the motor', 'Uniform temperature around the load', 'Noise', 'Lighting'], 1, 'Uniformity.')])

MODULES['packed_bed_reactor'] = mod(
    definition=('A packed (fixed) bed reactor passes reactants through a bed of solid catalyst. Feed enters at the top, is spread by a distributor and reacts as it flows down through the beds; '
                'cold quench between beds controls temperature in exothermic reactions; product leaves through the outlet collector.'),
    applications=['Hydrotreating and hydrocracking', 'Ammonia and methanol synthesis', 'Reforming and isomerisation', 'Catalytic oxidation'],
    key_points=['Even flow distribution is vital', 'Pressure drop grows with fouling', 'Quench limits hot spots', 'Catalyst changed at turnarounds'],
    principle=[step('Feed enters through the inlet diffuser and distribution tray.', 'distributors', overlay='flow'), step('It reacts while flowing through the catalyst bed.', 'catalyst_beds', overlay='temperature'),
               step('Cold quench gas mixes in between the beds.', 'distributors', overlay='flow'), step('Product leaves through the outlet collector at the bottom.', 'nozzles')],
    curve='Temperature rise per bed and ΔP vs time on stream.',
    params=se(P('Ø 1 – 5 m; height 5 – 30 m'), P('Up to ~ 200', 'bar'), P('Up to ~ 450 (hydroprocessing)', '°C'), P('Catalyst volume', 'm³')),
    install=_V_INST, maint=_m([M('Monitor bed ΔP and thermocouples.', 'catalyst_beds', 'continuous')], [M('Skim/regenerate catalyst as required.', 'catalyst_beds', 'per cycle')],
                               [M('Change catalyst; inspect internals.', 'distributors')], _NOLUBE),
    failures=[F('Hot spots', ['Local high temperature'], ['Maldistribution, quench failure'], ['Improve distribution; restore quench'], 'distributors'), F('High pressure drop', ['ΔP rise'], ['Fouling/crusting at bed top'], ['Skim top layer'], 'catalyst_beds')],
    quiz=[Q('Why inject quench between beds?', ['To add reactant only', 'To limit temperature rise in exothermic reactions', 'To clean catalyst', 'Noise'], 1, 'Temperature control.'),
          Q('Poor distribution causes…', ['Even reaction', 'Channelling and hot spots', 'Lower ΔP only', 'Nothing'], 1, 'Maldistribution.'),
          Q('Ceramic balls above and below the bed…', ['React', 'Support and distribute, and hold the catalyst down', 'Cool', 'Measure flow'], 1, 'Grading.')])

MODULES['fluidized_bed_reactor'] = mod(
    definition=('In a fluidized bed reactor gas blown up through a distributor lifts fine solid particles so the bed behaves like a boiling liquid. Excellent mixing gives uniform temperature; '
                'internal cyclones recover entrained particles and return them to the bed.'),
    applications=['Fluid catalytic cracking (FCC)', 'Polyethylene/polypropylene gas-phase reactors', 'Roasting and calcination', 'Biomass gasification'],
    key_points=['Gas velocity above minimum fluidization', 'Uniform temperature', 'Erosion and attrition', 'Cyclones capture fines'],
    principle=[step('Fluidizing gas enters the plenum below the distributor.', 'distributor', overlay='flow'), step('Gas through the caps lifts the particles — the bed expands and bubbles.', 'bed'),
               step('Bubbles rise and burst at the surface.', 'bubbles'), step('Cyclones separate entrained particles and return them through diplegs.', 'cyclones', overlay='flow'), step('Product gas leaves at the top.', 'nozzles')],
    curve='Bed ΔP vs gas velocity: rises, then flat once fluidized (ΔP ≈ bed weight / area).',
    params=se(P('Ø 0.3 – 15 m'), P('~ 1 – 40', 'bar'), P('Up to ~ 1000', '°C'), P('Bed inventory', 't')),
    install=_V_INST, maint=_m([M('Monitor bed ΔP and temperatures.', 'bed', 'continuous')], [M('Inspect distributor nozzles and cyclones.', 'cyclones', 'turnaround')],
                               [M('Refractory and erosion repairs.', 'vessel')], _NOLUBE),
    failures=[F('Defluidization / agglomeration', ['ΔP change, hot spots'], ['Sticky particles, low gas flow'], ['Restore flow; control temperature'], 'bed'), F('Cyclone erosion', ['Catalyst losses'], ['High velocity'], ['Repair liners'], 'cyclones')],
    quiz=[Q('What keeps the particles suspended?', ['Mechanical stirrer', 'Upward gas flow', 'Magnets', 'Vibration'], 1, 'Drag balances weight.'),
          Q('Bed pressure drop in the fluidized state is about…', ['Zero', 'Weight of the bed per unit area', 'Atmospheric', 'Infinite'], 1, 'Classic result.'),
          Q('What do the cyclones do?', ['Heat the gas', 'Catch entrained particles and return them', 'Add catalyst', 'Measure flow'], 1, 'Solids recovery.')])

MODULES['deaerator'] = mod(
    definition=('A deaerator removes dissolved oxygen and CO₂ from boiler feedwater. Water is sprayed into steam and cascades over trays, reaching saturation temperature so the gases are released and '
                'vented. The hot, deaerated water collects in the storage tank and feeds the boiler feed pumps.'),
    applications=['Power-station and industrial boiler feed systems', 'Process steam plants', 'HRSGs'],
    key_points=['Hot (saturated) water holds almost no gas', 'Vent must show a small steam plume', 'Storage gives feed-pump NPSH (elevated)', 'Oxygen guarantee ~ 7 ppb (typical)'],
    principle=[step('Feedwater is sprayed into the deaerator head.', 'spray_valves', overlay='flow'), step('It cascades over the trays in counter-flow to rising steam.', 'trays'),
               step('Heated to saturation, the water releases O₂ and CO₂, which leave through the vent with a little steam.', 'deaerator_head', overlay='flow'),
               step('Deaerated water collects in the storage tank.', 'water'), step('The feed pumps draw from the bottom outlet.', 'nozzles')],
    curve='Dissolved O₂ vs water temperature/pressure: approaches zero at saturation.',
    params=se(P('Storage 1 – 500 m³'), P('~ 0.2 – 10 (pegged pressure)', 'bar(g)'), P('~ 105 – 180 (saturation)', '°C'), P('Feedwater flow', 't/h')),
    install=_V_INST | dict(foundation=['Elevate the deaerator to give the feed pumps sufficient NPSH margin.']),
    maint=_m([M('Check vent plume, pressure and level.', 'nozzles', 'daily')], [M('Measure dissolved O₂.', 'water', 'weekly')], [M('Inspect trays and spray valves.', 'trays')], _NOLUBE),
    failures=[F('High dissolved oxygen', ['O₂ above limit'], ['Vent closed, low pressure, spray valve fault'], ['Open vent, restore steam, repair valves'], 'spray_valves'),
              F('Feed-pump cavitation', ['Noise, low flow'], ['Pressure decay on load change'], ['Stabilise pressure'], 'storage_tank')],
    quiz=[Q('Why heat feedwater to saturation in a deaerator?', ['To boil it away', 'Gas solubility is near zero at saturation', 'To save fuel only', 'To add oxygen'], 1, 'Henry\'s law.'),
          Q('The vent should show…', ['Nothing', 'A small steam plume', 'Water', 'Smoke'], 1, 'Carries gases out.'),
          Q('Why elevate the deaerator?', ['Appearance', 'NPSH for the feed pumps', 'Ventilation', 'Easier painting'], 1, 'Saturated water.')])

MODULES['boiler_feedwater_tank'] = mod(
    definition=('A boiler feedwater tank stores condensate returns and treated make-up water for the boiler feed pumps. Keeping it hot (often ~85–90 °C via a steam sparger) reduces dissolved oxygen and '
                'improves boiler efficiency.'),
    applications=['Small/medium industrial boiler houses', 'Before a deaerator in larger plants', 'Condensate recovery systems'],
    key_points=['Hot feedwater = less O₂', 'Level control with make-up valve', 'Pump suction needs NPSH', 'Overflow and vent required'],
    principle=[step('Condensate returns and make-up water enter at the top.', 'nozzles', overlay='flow'), step('The steam sparger heats the water.', 'steam_sparger'),
               step('Level rises and falls with demand; the level gauge shows it.', 'water'), step('Feed pumps draw from the bottom outlet.', 'tank', overlay='flow')],
    curve='Dissolved oxygen vs temperature; flash steam from high-pressure returns.',
    params=se(P('1 – 100 m³'), P('Atmospheric (vented) – low pressure', 'bar'), P('Up to ~ 100', '°C'), P('Storage ~ 20–60 min of boiler steaming (rule of thumb)', 'min')),
    install=_V_INST, maint=_m([M('Check level and temperature.', 'water', 'daily')], [M('Check sparger and level gauge.', 'steam_sparger', 'monthly')], [M('Internal inspection/coating.', 'tank')], _NOLUBE),
    failures=[F('Pump cavitation', ['Noise'], ['Water too hot for available NPSH'], ['Raise tank or reduce temperature'], 'tank'), F('Corrosion', ['Rust, leaks'], ['Oxygen, low pH'], ['Heat water, dose chemicals'], 'tank')],
    quiz=[Q('Why keep feed tank water hot?', ['Comfort', 'Lower dissolved oxygen and better efficiency', 'Lower NPSH needed', 'No reason'], 1, 'O₂ solubility falls with temperature.'),
          Q('What sets the make-up flow?', ['Level control', 'Pump speed only', 'Vent size', 'Manway'], 0, 'Level controller.'),
          Q('Hot water in the tank reduces the pump\'s…', ['Head', 'Available NPSH', 'Speed', 'Efficiency only'], 1, 'Higher vapour pressure.')])

MODULES['hotwell'] = mod(
    definition=('The hotwell is the condensate collection box under a steam surface condenser. Turbine exhaust steam condenses on cold tubes, drips into the hotwell, and the condensate extraction pumps '
                'draw it out. The hotwell gives a little storage and the suction head for those pumps; a level controller holds the level.'),
    applications=['Steam turbine surface condensers', 'Process condensers'],
    key_points=['Under vacuum — air leaks harm performance', 'Level control protects CEPs', 'Storage typically a few minutes of flow', 'Make-up enters here'],
    principle=[step('Exhaust steam enters the condenser from the turbine above.', 'condenser_shell', overlay='flow'), step('It condenses on the cold tubes carrying cooling water.', 'tube_bundle', overlay='flow'),
               step('Condensate drips into the hotwell.', 'hotwell_box'), step('Level is held by the controller; CEPs draw condensate out.', 'connections', overlay='flow')],
    curve='Condenser pressure vs cooling-water temperature and flow.',
    params=se(P('Storage ~ 1 – 3 min of condensate flow (HEI typical)'), P('Vacuum (~ 0.05 – 0.1 bar abs)', 'bar(a)'), P('~ 30 – 50', '°C'), P('Condensate flow', 't/h')),
    install=_V_INST, maint=_m([M('Monitor level, vacuum and condensate conductivity.', 'condensate', 'continuous')], [M('Leak test for air in-leakage.', 'condenser_shell', 'quarterly')],
                               [M('Clean tubes; inspect hotwell.', 'tube_bundle')], _NOLUBE),
    failures=[F('Low level / CEP cavitation', ['Pump noise, trips'], ['Level control fault'], ['Fix controller; make-up'], 'connections'), F('Tube leak', ['High conductivity'], ['Tube corrosion/erosion'], ['Plug tubes'], 'tube_bundle')],
    quiz=[Q('What is the hotwell?', ['Turbine casing', 'Condensate collection box under the condenser', 'Boiler drum', 'Cooling tower basin'], 1, 'Collection box.'),
          Q('Why monitor condensate conductivity?', ['Colour', 'To detect cooling-water tube leaks', 'Temperature', 'Level'], 1, 'Contamination.'),
          Q('Air in-leakage causes…', ['Better vacuum', 'Poorer vacuum and lower efficiency', 'No effect', 'Higher level'], 1, 'Non-condensables.')])

MODULES['surge_vessel'] = mod(
    definition=('A surge vessel protects pipelines from water hammer. When a pump trips or a valve closes, a pressure wave travels along the pipe; the vessel\'s compressed-air cushion lets water flow '
                'out or in, damping the pressure swings and preventing vacuum.'),
    applications=['Pumped water mains and irrigation lines', 'Sewage rising mains', 'Cooling water and fire water systems', 'Oil pipelines (bladder type)'],
    key_points=['Sized by transient (surge) analysis', 'Air volume must be maintained', 'Close to the pump discharge', 'Bladder types avoid air dissolving'],
    principle=[step('In normal running the air cushion is compressed to line pressure.', 'air_cushion'), step('When the pump trips, water flows out of the vessel into the main, preventing vacuum.', 'water', overlay='flow'),
               step('When the reverse wave returns, water flows back in and compresses the air.', 'connections', overlay='flow'), step('The compressor tops up air that dissolves over time.', 'air_compressor', cut=False)],
    curve='Pressure envelope (max/min) along the pipeline with and without protection.',
    params=se(P('0.5 – 200 m³'), P('Up to ~ 40', 'bar'), P('0 – 50', '°C'), P('Total vessel volume', 'm³')),
    install=_V_INST, maint=_m([M('Check water level/air volume.', 'water', 'daily')], [M('Service compressor; test relief valve.', 'air_compressor', 'monthly')], [M('Internal inspection.', 'vessel')], ['Compressor oil per maker.']),
    failures=[F('Loss of air cushion', ['Vessel full of water; surges unprotected'], ['Air dissolved, compressor fault'], ['Restore air; repair compressor'], 'air_cushion'),
              F('Over-pressure', ['High transient pressures'], ['Undersized/incorrect pre-charge'], ['Re-check surge analysis'], 'vessel')],
    quiz=[Q('What causes water hammer?', ['Slow valve closure', 'Sudden change in flow (pump trip, fast valve closure)', 'Low temperature', 'Pipe colour'], 1, 'Transient.'),
          Q('What absorbs the surge?', ['The vessel steel', 'The compressed air cushion', 'The pump', 'The ground'], 1, 'Gas spring.'),
          Q('Why is air topped up?', ['To cool water', 'Air dissolves into water over time', 'To clean', 'Not needed'], 1, 'Maintain volume.')])

MODULES['knockout_drum'] = mod(
    definition=('A knockout drum removes liquid droplets from a gas stream — typically in flare systems. The gas slows down in the large drum so droplets settle by gravity and collect at the bottom; '
                'dry gas leaves for the flare and the liquid is pumped out.'),
    applications=['Flare and blowdown systems', 'Compressor suction protection', 'Fuel gas systems'],
    key_points=['Low gas velocity lets drops settle', 'Sized per API 521 for droplet size', 'Liquid hold-up for relief scenarios', 'Level alarms and pump-out'],
    principle=[step('Wet gas enters through the inlet and hits the diverter.', 'inlet', overlay='flow'), step('Gas slows down across the drum; droplets fall out.', 'drops'),
               step('Liquid collects at the bottom; level rises.', 'liquid'), step('Dry gas leaves for the flare; liquid is pumped out.', 'nozzles', overlay='flow')],
    curve='Settling velocity vs droplet diameter (Stokes/intermediate laws).',
    params=se(P('Ø 1 – 5 m; length 3 – 20 m'), P('Low pressure (~ 3.5 bar(g) design typical)', 'bar(g)'), P('-46 to 300 (flare dependent)', '°C'), P('Liquid hold-up', 'm³')),
    install=_V_INST, maint=_m([M('Check level and pump-out.', 'liquid', 'daily')], [M('Test level alarms.', 'nozzles', 'monthly')], [M('Internal inspection.', 'drum')], _NOLUBE),
    failures=[F('Liquid carry-over to flare', ['Burning rain, smoke'], ['High level, undersized drum'], ['Pump out; resize'], 'liquid'), F('Freezing/hydrates', ['Blockage'], ['Cold expansion'], ['Heat tracing'], 'nozzles')],
    quiz=[Q('Why must liquid be removed before the flare?', ['Cost', 'Burning liquid droplets ("rain") are a fire hazard', 'Noise', 'No reason'], 1, 'Safety.'),
          Q('Droplets separate mainly by…', ['Filtration', 'Gravity settling at low velocity', 'Magnetism', 'Heating'], 1, 'Settling.'),
          Q('Which standard covers KO drum sizing?', ['API 650', 'API 521', 'API 610', 'ASME B31.3'], 1, 'Pressure relief systems.')])

MODULES['gas_liquid_separator'] = mod(
    definition=('A two-phase separator splits a mixed stream into gas and liquid. The inlet device breaks the momentum, liquid drops out by gravity, a mesh pad catches fine mist near the top, and a level '
                'control valve keeps the liquid at the right level.'),
    applications=['Production separators (oil & gas)', 'Compressor suction scrubbers', 'Flash drums', 'Steam/water separation'],
    key_points=['Souders–Brown K-factor sets diameter', 'Inlet device, gravity, mist, liquid sections', 'Vortex breaker on liquid outlet', 'Level control critical'],
    principle=[step('Mixed flow enters and hits the inlet diverter.', 'inlet_diverter', overlay='flow'), step('Droplets settle in the gravity section.', 'drops'),
               step('The mesh pad captures fine mist before the gas outlet.', 'mist_eliminator', overlay='flow'), step('Liquid collects at the bottom; level controller and valve hold it steady.', 'liquid')],
    curve='Allowable gas velocity v = K·√((ρL−ρG)/ρG).',
    params=se(P('Ø 0.3 – 4 m'), P('Up to ~ 150', 'bar'), P('-46 to 200', '°C'), P('Gas & liquid flows', '—')),
    install=_V_INST, maint=_m([M('Check level control and ΔP across mesh.', 'mist_eliminator', 'daily')], [M('Calibrate level instruments.', 'nozzles', 'quarterly')], [M('Inspect/replace mesh pad.', 'mist_eliminator')], _NOLUBE),
    failures=[F('Liquid carry-over', ['Liquid in gas line'], ['High gas rate, plugged/damaged mesh, high level'], ['Reduce rate; clean pad'], 'mist_eliminator'), F('Gas blow-by', ['Gas in liquid line'], ['Low level'], ['Fix level control'], 'liquid')],
    quiz=[Q('What sizes the separator diameter?', ['Liquid colour', 'Allowable gas velocity (K-factor)', 'Nozzle count', 'Paint'], 1, 'Souders–Brown.'),
          Q('Purpose of the vortex breaker?', ['Heat', 'Prevent gas being sucked into the liquid outlet', 'Mix', 'Measure'], 1, 'Anti-vortex.'),
          Q('The mesh pad removes…', ['Large slugs', 'Fine mist droplets', 'Solids only', 'Gas'], 1, 'Mist eliminator.')])

MODULES['three_phase_separator'] = mod(
    definition=('A three-phase separator splits well fluid into gas, oil and water. Gas rises; liquid settles into water below oil. Oil spills over a weir into a compartment; water is drawn from '
                'beneath the oil. Level and interface controllers set each outlet.'),
    applications=['Oil & gas production', 'Refinery desalter feed / slop oil', 'Produced-water treatment front end'],
    key_points=['Retention time for oil–water separation', 'Weir sets interface', 'Emulsions slow separation', 'Sand drains/jetting'],
    principle=[step('Well fluid enters and hits the inlet diverter.', 'internals', overlay='flow'), step('Gas separates and leaves through the mist eliminator.', 'mist_eliminator', overlay='flow'),
               step('Water droplets fall out of the oil to the bottom.', 'water_layer'), step('Oil spills over the weir into the oil bucket.', 'oil_layer', overlay='flow'), step('Water and oil leave through separate outlets.', 'nozzles')],
    curve='Separation vs retention time (typically 3–10+ min, oil gravity/emulsion dependent).',
    params=se(P('Ø 1 – 4 m; length 3 – 20 m'), P('Up to ~ 100', 'bar'), P('Up to ~ 120', '°C'), P('Liquid retention time', 'min')),
    install=_V_INST, maint=_m([M('Check levels and interface.', 'water_layer', 'daily')], [M('Sand jetting/draining.', 'nozzles', 'as needed')], [M('Inspect weir and internals.', 'internals')], _NOLUBE),
    failures=[F('Oil in water outlet', ['Oily produced water'], ['Interface too low, emulsion'], ['Adjust interface; chemicals'], 'water_layer'), F('Water in oil', ['High BS&W'], ['Short retention, emulsion'], ['Demulsifier, heat'], 'oil_layer')],
    quiz=[Q('Why does oil float on water?', ['It is hotter', 'Lower density', 'It is a gas', 'Magnetism'], 1, 'Density difference.'),
          Q('The weir…', ['Heats oil', 'Lets oil spill into its own compartment while water stays behind', 'Measures gas', 'Supports vessel'], 1, 'Oil bucket.'),
          Q('Emulsions make separation…', ['Faster', 'Slower', 'Unchanged', 'Impossible always'], 1, 'Stable droplets.')])

MODULES['scrubber_vessel'] = mod(
    definition=('A wet scrubber removes pollutants from gas by contact with a liquid. Gas flows up through a packed bed while scrubbing liquor trickles down; acids, dust or odours dissolve or react. '
                'A mist eliminator catches droplets before the clean gas leaves.'),
    applications=['Acid gas removal (HCl, SO₂, NH₃)', 'Odour control', 'Process vent treatment', 'Dust removal (venturi/packed)'],
    key_points=['Counter-current contact', 'Liquid-to-gas ratio and pH control', 'Flooding limits gas rate', 'Mist eliminator prevents carry-over'],
    principle=[step('Dirty gas enters near the bottom.', 'nozzles', overlay='flow'), step('Liquor is sprayed on top of the packing.', 'spray_header'),
               step('Gas and liquid contact on the packing surface; pollutants transfer to the liquid.', 'packing', overlay='flow'), step('The mist eliminator removes droplets; clean gas exits.', 'mist_eliminator'),
               step('Liquor collects in the sump and is recirculated.', 'recirculation_pump', cut=False)],
    curve='Removal efficiency vs L/G ratio and packing height (NTU × HTU).',
    params=se(P('Ø 0.3 – 5 m'), P('Near atmospheric', 'mbar'), P('Up to ~ 80 (plastics)', '°C'), P('Gas flow', 'm³/h')),
    install=_V_INST, maint=_m([M('Check pH, recirculation flow, ΔP.', 'sump', 'daily')], [M('Clean spray nozzles; check packing.', 'spray_header', 'monthly')], [M('Replace packing/mist eliminator.', 'packing')], ['Pump bearings per maker.']),
    failures=[F('Flooding', ['High ΔP, liquid carry-over'], ['Too much gas or liquid, fouled packing'], ['Reduce load; clean packing'], 'packing'), F('Low efficiency', ['Emissions high'], ['Low pH/flow, blocked nozzles'], ['Restore chemistry; clean'], 'spray_header')],
    quiz=[Q('Counter-current means gas and liquid flow…', ['The same way', 'In opposite directions', 'Sideways', 'Not at all'], 1, 'Gas up, liquid down.'),
          Q('Why is packing used?', ['Weight', 'Large contact surface', 'Colour', 'Noise'], 1, 'Mass transfer area.'),
          Q('Flooding happens when…', ['Flow too low', 'Gas/liquid loads too high', 'pH high', 'Fan off'], 1, 'Hydraulic limit.')])

MODULES['demister_vessel'] = mod(
    definition=('A demister vessel removes fine liquid mist from gas. Droplets strike the wires of a knitted mesh pad, coalesce into larger drops and drain; a chevron vane pack catches what remains by '
                'repeated changes of direction. Clean gas leaves at the top.'),
    applications=['Compressor and turbine inlet protection', 'Absorber/scrubber outlets', 'Sulphuric acid plants', 'Steam drums and evaporators'],
    key_points=['Mesh for fine droplets (≥ ~3–5 µm)', 'Vanes for higher loads', 'Velocity window (K-factor)', 'ΔP indicates fouling'],
    principle=[step('Mist-laden gas enters below the mesh pad.', 'nozzles', overlay='flow'), step('Droplets impact and coalesce on the mesh wires.', 'mesh_pad'),
               step('The vane pack catches remaining droplets.', 'vane_pack'), step('Coalesced liquid drains to the bottom.', 'drained_liquid')],
    curve='Separation efficiency vs droplet size and gas velocity.',
    params=se(P('Ø 0.2 – 5 m'), P('Up to ~ 150', 'bar'), P('-20 to 300', '°C'), P('Gas flow', 'm³/h')),
    install=_V_INST, maint=_m([M('Monitor ΔP across pad.', 'nozzles', 'daily')], [M('Wash/clean pad.', 'mesh_pad', 'as needed')], [M('Replace pad/vanes.', 'vane_pack')], _NOLUBE),
    failures=[F('Plugged pad', ['High ΔP'], ['Solids, salts, polymers'], ['Wash or replace'], 'mesh_pad'), F('Re-entrainment', ['Liquid carry-over'], ['Velocity too high'], ['Reduce flow; resize'], 'mesh_pad')],
    quiz=[Q('How does a mesh pad catch droplets?', ['Heating', 'Impaction and coalescence on wires', 'Electric field', 'Freezing'], 1, 'Inertial impaction.'),
          Q('Too high gas velocity causes…', ['Better efficiency', 'Re-entrainment of liquid', 'Lower ΔP', 'Nothing'], 1, 'Flooding of pad.'),
          Q('Rising ΔP across the pad means…', ['Pad fouling', 'Pad missing', 'Low flow', 'Nothing'], 0, 'Deposits.')])

MODULES['chimney_stack'] = mod(
    definition=('A chimney or stack releases flue gases high above the ground so they disperse safely. Hot gas rises by natural draft. Steel stacks are lined against heat and acid condensation, fitted '
                'with helical strakes against wind vibration, and carry sampling ports, platforms and warning lights.'),
    applications=['Boilers and furnaces', 'Power plants and incinerators', 'Process heaters and gas turbines', 'Kilns and dryers'],
    key_points=['Height set by dispersion modelling', 'Natural draft ∝ height × density difference', 'Strakes stop vortex-induced vibration', 'CEMS sampling ports'],
    principle=[step('Flue gas enters through the breeching.', 'breeching', overlay='flow'), step('It rises up the lined shell by draft.', 'lining', overlay='flow'),
               step('Strakes break up wind vortices.', 'strakes'), step('Gas is sampled at the ports for emissions monitoring.', 'access', cut=False), step('The plume disperses above the top.', 'plume')],
    curve='Draft = H·g·(ρ_air − ρ_gas).',
    params=se(P('Height 15 – 250 m; Ø 0.5 – 10 m'), P('Near atmospheric (draft ~ Pa)', 'Pa'), P('Flue gas ~ 80 – 600', '°C'), P('Gas flow', 'm³/s')),
    install=_T_INST | dict(alignment=['Erect plumb; check deflection limits; install aviation lighting per authority.']),
    maint=_m([M('Check lights and CEMS.', 'fittings', 'daily')], [M('Inspect shell thickness and lining.', 'shell', 'annual')], [M('Repaint/re-line; inspect anchor bolts.', 'foundation')], _NOLUBE),
    failures=[F('Acid corrosion', ['Thinning, holes'], ['Flue gas below dew point'], ['Maintain temperature; corrosion-resistant liner'], 'lining'), F('Wind vibration', ['Oscillation'], ['Vortex shedding'], ['Strakes/dampers'], 'strakes')],
    quiz=[Q('Natural draft depends on…', ['Stack colour', 'Height and density difference between hot gas and air', 'Number of ladders', 'Wind only'], 1, 'Buoyancy.'),
          Q('Helical strakes prevent…', ['Corrosion', 'Vortex-induced vibration', 'Lightning', 'Rain entry'], 1, 'Break up shedding.'),
          Q('Why line steel stacks?', ['Appearance', 'Protect against heat and acid condensation', 'Weight', 'Noise only'], 1, 'Durability.')])

MODULES['silencer'] = mod(
    definition=('A silencer reduces noise from flowing gas. Reactive chambers and baffles reflect low-frequency sound; absorptive packing behind a perforated tube converts high-frequency sound into heat. '
                'Together they give broad-band noise reduction with low pressure loss.'),
    applications=['Engine and gas-turbine exhausts', 'Steam and safety-valve vents', 'Blower/compressor intakes and outlets', 'Fan ducts'],
    key_points=['Insertion loss in dB', 'Reactive = low frequency; absorptive = high frequency', 'Back-pressure limits', 'Packing retention'],
    principle=[step('Noisy gas enters the inlet cone.', 'shell', overlay='flow'), step('Baffled chambers reflect low-frequency sound.', 'baffles', overlay='noise'),
               step('Packing behind the perforated tube absorbs high frequencies.', 'absorptive_section', overlay='noise'), step('Quieter gas leaves the outlet.', 'connections')],
    curve='Insertion loss vs frequency (octave bands).',
    params=se(P('DN 25 – 3000'), P('Up to ~ 40 (vent silencers)', 'bar'), P('Up to ~ 600', '°C'), P('Insertion loss ~ 20 – 40', 'dB(A)')),
    install=_V_INST, maint=_m([M('Check for rattles and leaks.', 'shell', 'monthly')], [M('Inspect packing condition.', 'absorptive_section', 'annual')], [M('Repack/replace.', 'absorptive_section')], _NOLUBE),
    failures=[F('Packing loss', ['Noise rises'], ['Erosion/burn-out of packing'], ['Repack with retention cloth'], 'absorptive_section'), F('Excess back-pressure', ['Engine power loss'], ['Blockage'], ['Clean'], 'baffles')],
    quiz=[Q('Reactive silencers mainly control…', ['High frequencies', 'Low frequencies', 'Vibration only', 'Temperature'], 1, 'Reflection.'),
          Q('Absorptive packing converts sound into…', ['Light', 'Heat', 'Pressure', 'Electricity'], 1, 'Dissipation.'),
          Q('Insertion loss is measured in…', ['bar', 'dB', 'kW', 'm/s'], 1, 'Decibels.')])

MODULES['gas_holder'] = mod(
    definition=('A wet gas holder stores low-pressure gas in a steel bell floating in a water tank. As gas flows in the bell rises; as gas is drawn off it sinks. The water forms the seal and the bell\'s '
                'weight keeps the pressure nearly constant.'),
    applications=['Biogas plants (wet/dry holders)', 'Historic town-gas storage', 'Process gas buffering', 'Landfill gas balancing'],
    key_points=['Constant low pressure', 'Water seal', 'Guide frame keeps bell vertical', 'Modern sites use dry membrane holders'],
    principle=[step('Gas enters through the inlet pipe rising through the water.', 'gas_pipes', overlay='flow'), step('The bell lifts as the gas volume increases.', 'bell'),
               step('The guide frame and rollers keep it vertical.', 'guide_frame', cut=False), step('When gas is drawn off, the bell sinks under its own weight.', 'seal_water', overlay='flow')],
    curve='Pressure ≈ bell weight / area (nearly constant over the stroke).',
    params=se(P('Ø 5 – 70 m (historic large)'), P('~ 10 – 30', 'mbar'), P('Ambient', '°C'), P('Stored volume', 'm³')),
    install=_T_INST, maint=_m([M('Check bell level and water seal.', 'seal_water', 'daily')], [M('Inspect rollers and guides.', 'guide_frame', 'quarterly')], [M('Repaint bell and tank.', 'bell')], ['Grease guide rollers.']),
    failures=[F('Bell jamming', ['Tilting, pressure surges'], ['Roller/guide wear, ice'], ['Repair guides; heat seal water'], 'guide_frame'), F('Water seal loss', ['Gas leak'], ['Evaporation, leak'], ['Top up water'], 'seal_water')],
    quiz=[Q('What sets the gas pressure in a wet holder?', ['Compressor', 'Bell weight', 'Water temperature', 'Pipe size'], 1, 'Weight/area.'),
          Q('What seals the gas?', ['Rubber', 'Water', 'Oil', 'Grease'], 1, 'Water seal.'),
          Q('Why guide columns?', ['Decoration', 'Keep the bell vertical', 'Store gas', 'Heat'], 1, 'Stability.')])

MODULES['lpg_storage_bullet'] = mod(
    definition=('An LPG bullet is a horizontal pressure vessel storing liquefied petroleum gas under its own vapour pressure. It is filled to no more than about 85 % to allow for liquid expansion, '
                'and protected by relief valves, water deluge and remote isolation.'),
    applications=['LPG bottling plants and depots', 'Refinery and gas-plant storage', 'Industrial fuel storage'],
    key_points=['Pressure = vapour pressure at temperature', 'Max fill ~ 85 % (typical)', 'Relief sized for fire exposure', 'BLEVE prevention: deluge, mounding, spacing'],
    principle=[step('LPG is stored as liquid with vapour above it.', 'lpg_liquid'), step('Liquid is drawn from the bottom; vapour line balances pressure.', 'fittings', overlay='flow'),
               step('Relief valves protect against overpressure (e.g. fire).', 'fittings', cut=False), step('The deluge ring cools the shell in a fire.', 'deluge', cut=False)],
    curve='Vapour pressure vs temperature for propane/butane.',
    params=se(P('Ø 2 – 4 m; length 10 – 60 m'), P('~ 17 – 20 (propane)', 'bar(g)'), P('-45 to 55', '°C'), P('Water capacity', 'm³')),
    install=_V_INST | dict(piping=['Excess-flow and remotely operated valves on liquid lines; spacing and fire protection per NFPA 58/API 2510.']),
    maint=_m([M('Check level and pressure.', 'lpg_liquid', 'daily')], [M('Test relief valves and deluge.', 'deluge', 'annual')], [M('Internal inspection and NDT.', 'bullet')], _NOLUBE),
    failures=[F('Overfill', ['High level'], ['Gauge fault'], ['Independent high-level trip'], 'fittings'), F('BLEVE risk in fire', ['Fire impingement'], ['Shell overheating above liquid'], ['Deluge, mounding, relief'], 'deluge')],
    quiz=[Q('Why not fill an LPG vessel to 100 %?', ['Cost', 'Liquid expands with temperature and could over-pressure', 'Colour', 'It is allowed'], 1, 'Expansion space.'),
          Q('What determines the pressure?', ['Fill level', 'Vapour pressure at the liquid temperature', 'Vessel size', 'Pump'], 1, 'Saturated.'),
          Q('Purpose of the deluge ring?', ['Washing', 'Cool the vessel in a fire', 'Fill', 'Earthing'], 1, 'Fire protection.')])

MODULES['cryogenic_storage_tank'] = mod(
    definition=('A full-containment LNG tank stores liquefied natural gas at about −162 °C. A 9 % nickel inner tank holds the liquid, thick insulation limits heat leak, and a pre-stressed concrete outer '
                'tank can contain liquid and vapour if the inner tank fails. In-tank pumps send LNG out through the roof; boil-off gas is recovered.'),
    applications=['LNG import/export terminals', 'Peak-shaving plants', 'Liquid nitrogen/oxygen/argon storage (smaller, vacuum-insulated)', 'Ethylene storage'],
    key_points=['Boil-off ~ 0.05 %/day (large tanks, typical)', 'No bottom penetrations', 'Materials ductile at cryogenic temperature', 'Rollover and stratification risk'],
    principle=[step('LNG is held in the 9 % Ni inner tank.', 'inner_tank'), step('Insulation and the suspended deck limit heat entering.', 'insulation'),
               step('Heat leak causes boil-off gas, removed at the roof.', 'roof_platform', overlay='flow'), step('In-tank pumps send LNG out through the columns.', 'in_tank_pumps', overlay='flow'),
               step('The concrete outer tank provides secondary containment.', 'outer_tank')],
    curve='Boil-off rate vs heat leak; level/density profiles for rollover monitoring.',
    params=se(P('Ø ~ 70 – 90 m; 50 000 – 270 000 m³'), P('~ 0.25 (slightly above atmospheric)', 'bar(g)'), P('-165 to ambient', '°C'), P('Working volume', 'm³')),
    install=_T_INST | dict(foundation=['Elevated pile cap or heated slab to prevent frost heave.']),
    maint=_m([M('Monitor level, temperature/density profiles, BOG.', 'lng', 'continuous')], [M('Test in-tank pumps (pull via columns).', 'in_tank_pumps', 'per hours')], [M('Inspection at decommissioning only (rare).', 'inner_tank')], ['Pump bearings lubricated by LNG.']),
    failures=[F('Rollover', ['Sudden large BOG release'], ['Stratification of different-density LNG'], ['Mixing/top-bottom filling'], 'lng'), F('Cold spots on outer wall', ['Thermography anomaly'], ['Insulation defect'], ['Investigate'], 'insulation')],
    quiz=[Q('Why 9 % nickel steel for the inner tank?', ['Cheap', 'Remains tough (ductile) at −162 °C', 'Magnetic', 'Light'], 1, 'Cryogenic toughness.'),
          Q('What is boil-off gas?', ['Leaked LNG', 'Vapour formed by heat leak into the tank', 'Nitrogen', 'Exhaust'], 1, 'Heat ingress.'),
          Q('Why no bottom nozzles?', ['Cheaper', 'Avoid a leak path below the liquid', 'Easier painting', 'Pumps need them'], 1, 'Full containment safety.')])

MODULES['floating_roof_tank'] = mod(
    definition=('An external floating roof tank stores volatile liquids like crude oil. The roof floats on the liquid and moves up and down with the level, so there is almost no vapour space — '
                'cutting evaporation losses and fire risk. A rim seal closes the gap to the shell; a rolling ladder follows the roof.'),
    applications=['Crude oil and gasoline storage', 'Refinery and terminal storage', 'Volatile intermediates'],
    key_points=['Minimal vapour space → low emissions', 'Rim seals are critical', 'Roof drain must work (rain)', 'Legs support the roof at low level'],
    principle=[step('Product enters through the inlet nozzle and the level rises.', 'nozzles', overlay='flow'), step('The roof floats on the liquid and rises with it.', 'floating_roof'),
               step('The rim seal closes the gap to the shell.', 'floating_roof'), step('The rolling ladder follows the roof for access.', 'rolling_ladder', cut=False),
               step('Rainwater drains through the articulated roof drain.', 'roof_drain')],
    curve='Standing and withdrawal losses (API MPMS Ch. 19) vs seal type.',
    params=se(P('Ø 10 – 120 m; height 10 – 25 m'), P('Atmospheric', 'bar'), P('Ambient – ~ 90', '°C'), P('Nominal capacity', 'm³')),
    install=_T_INST, maint=_m([M('Check roof position and drain.', 'floating_roof', 'daily')], [M('Inspect rim seals and pontoons.', 'floating_roof', 'annual')], [M('Out-of-service inspection (API 653).', 'shell')], ['Grease rolling-ladder wheels and drain swivel joints.']),
    failures=[F('Roof sinking', ['Roof tilts or sinks'], ['Rainwater not drained, pontoon leaks'], ['Repair drain/pontoons'], 'roof_drain'), F('Rim seal fire / emissions', ['Odour, fire'], ['Damaged seal'], ['Replace seal; foam system'], 'floating_roof')],
    quiz=[Q('Why use a floating roof?', ['Looks', 'Eliminates vapour space → less evaporation and fire risk', 'Stronger', 'Cheaper paint'], 1, 'Emissions control.'),
          Q('What follows the roof up and down?', ['Wind girder', 'Rolling ladder', 'Shell', 'Foundation'], 1, 'Access.'),
          Q('A blocked roof drain can…', ['Improve sealing', 'Sink the roof under rainwater', 'Nothing', 'Heat product'], 1, 'Weight.')])

MODULES['pressure_storage_tank'] = mod(
    definition=('A spherical pressure tank (Horton sphere) stores liquefied gases such as propane and butane under pressure. A sphere carries internal pressure with the least wall thickness for its '
                'volume. It stands on columns at the equator with bracing, with relief valves, deluge and level instruments.'),
    applications=['LPG and butane storage at refineries/terminals', 'Ammonia (refrigerated/pressurised)', 'Hydrogen and gas buffers'],
    key_points=['Uniform membrane stress σ = p·R / (2t)', 'Most volume per steel weight', 'Fire protection of legs', 'Stair access to top platform'],
    principle=[step('Liquefied gas is stored with vapour above it.', 'liquid'), step('Liquid leaves from the bottom nozzle.', 'fittings', overlay='flow'),
               step('Relief valves at the top protect against overpressure.', 'fittings', cut=False), step('Columns and bracing carry the weight; deluge cools in a fire.', 'legs', cut=False)],
    curve='Shell stress vs pressure: sphere needs half the thickness of a cylinder of the same radius.',
    params=se(P('Ø 10 – 25 m (up to ~ 6000 m³)'), P('~ 5 – 20', 'bar(g)'), P('-45 to 50', '°C'), P('Water capacity', 'm³')),
    install=_V_INST | dict(foundation=['Individual column footings with settlement monitoring; fireproof the legs.']),
    maint=_m([M('Check level and pressure.', 'liquid', 'daily')], [M('Test relief valves and deluge.', 'deluge', 'annual')], [M('Internal inspection (wet fluorescent MT of welds).', 'sphere')], _NOLUBE),
    failures=[F('Weld cracking', ['Indications in NDT'], ['Stress corrosion, fatigue'], ['Grind/repair; PWHT'], 'sphere'), F('Leg fire damage', ['Collapse risk'], ['Missing fireproofing'], ['Fireproof legs'], 'legs')],
    quiz=[Q('Why a sphere?', ['Easier to build', 'Uniform stress → thinnest wall for the volume', 'Cheaper legs', 'Looks'], 1, 'σ = pR/2t.'),
          Q('Supports are at the…', ['Bottom point', 'Equator (columns)', 'Top', 'Nowhere'], 1, 'Equatorial columns.'),
          Q('Why fireproof the legs?', ['Paint', 'A collapse in fire would release the contents', 'Insulation', 'Weight'], 1, 'Safety.')])
