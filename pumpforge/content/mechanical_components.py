"""Learning content — Mechanical Components & Maintenance, EQ-321 … EQ-345.
Typical ranges are general engineering guidance; standard editions are marked 'to be verified' in the model metadata."""
from pumpforge.learning import mod, step, P, F, Q, M

MODULES = {}


def mc(size, speed, load, conditions, **extra):
    """Required parameters for the mechanical_components family: size, speed, load_capacity, operating_conditions."""
    ref = {'manufacturer': None, 'model': None, 'part_number': None, 'datasheet': None,
           'rated_point': {'speed_rpm': None, 'load_or_torque': None, 'temperature': None, 'pressure': None},
           'status': 'empty — fill from the component datasheet'}
    return dict(size=size, speed=speed, load_capacity=load, operating_conditions=conditions, reference_model=ref, extra=extra)


def _m(r, p, o, l):
    return dict(routine=r, periodic=p, overhaul=o, lubrication=l)


_CMP = dict(foundation=['Component is installed in its machine: housing bores, shaft fits and shoulders to drawing tolerances; clean, burr-free surfaces.'],
            alignment=['Concentricity and squareness checked with dial indicators (runout, face run-out) to maker limits.'],
            piping=['Lubrication / flush / buffer connections clean and flushed before first run; correct orientation of ports.'],
            commissioning=['Hand-turn first; run at low speed, check temperature, leakage and vibration; record baselines.'])
_SYS = dict(foundation=['Skid / unit on a level, rigid base; anchor bolts; accessible for maintenance.'],
            alignment=['Align pump-motor drives; level reservoirs and headers; slope drain lines as specified.'],
            piping=['Pickle / flush lube piping to the cleanliness target before connecting to bearings; avoid low pockets in mist/grease lines.'],
            commissioning=['Fill with the specified lubricant; vent air; test alarms, auto-start and pressure settings; check delivery at every point.'])
_TOOL = dict(foundation=['Machine on a stable base; for alignment, check and correct soft foot before measuring.'],
             alignment=['Mount brackets / sensors rigidly and square; check bracket sag (dial) or warm-up (laser).'],
             piping=['Cables / wireless links routed safely away from rotating parts.'],
             commissioning=['Verify sensor function and calibration; record as-found and as-left values.'])
_OIL = ['Oil or grease to maker specification; change on condition (oil analysis) or interval.']
_NL = ['No routine lubrication.']

# ===================================================================== sealing systems
MODULES['labyrinth_seal'] = mod(
    definition=('A labyrinth seal is a non-contacting seal used on compressors, turbines and bearing housings. A row of knife-edge teeth runs with a small clearance to the shaft; leaking gas is throttled at '
                'each tooth and loses its energy in the cavity after it, so pressure drops in steps and leakage stays small without any rubbing.'),
    applications=['Interstage and shaft-end seals of centrifugal compressors and steam turbines', 'Bearing-housing isolators and oil seals on pumps, fans and gearboxes'],
    key_points=['Non-contacting → no wear in normal running', 'Leakage falls with more teeth and smaller clearance', 'Buffer / eductor port at a middle cavity', 'Clearance grows if teeth rub'],
    principle=[step('High-pressure gas reaches the first tooth.', 'labyrinth_stator', overlay='flow'), step('It accelerates through the tiny clearance and loses pressure.', 'labyrinth_stator', overlay='pressure'),
               step('Its kinetic energy is dissipated as turbulence in the cavity.', 'casing'), step('The process repeats at every tooth until the low-pressure side.', 'shaft', overlay='pressure')],
    curve='Leakage vs number of teeth and clearance.',
    params=mc(P('Shaft ≈ 25 – 400 mm diameter'), P('Up to ≈ 15,000 – 20,000', 'rpm'), P('Pressure difference up to tens of bar (multi-stage)', '—'), P('Radial clearance ≈ 0.1 – 0.5 mm; gas or oil-mist service', '—')),
    install=_CMP, maint=_m([M('Trend leakage / buffer flow and bearing temperatures.', 'casing', 'daily')], [M('Inspect for rub marks during outages.', 'labyrinth_stator', 'at outage')], [M('Replace damaged labyrinths; restore clearance.', 'labyrinth_stator')], _NL),
    failures=[F('Excess leakage', ['High buffer flow, efficiency loss'], ['Teeth rubbed (vibration, thermal bow)'], ['Replace; correct the cause of the rub'], 'labyrinth_stator'),
              F('Oil leak at bearing labyrinth', ['Oil at the shaft'], ['Drain blocked, pressurised housing'], ['Clear drain; vent housing'], 'casing')],
    quiz=[Q('Does a labyrinth seal touch the shaft in normal running?', ['No — it is non-contacting', 'Yes, always', 'Only at full speed', 'Only when cold'], 0, 'Non-contacting.'),
          Q('How does it reduce leakage?', ['Repeated throttling and energy dissipation at many teeth', 'Spring-loaded faces', 'Rubber lips', 'Magnetism'], 0, 'Throttling.'),
          Q('What happens to leakage after a rub?', ['It increases (clearance larger)', 'It falls', 'No change', 'Becomes zero'], 0, 'Larger clearance.')],
    selection=['Select tooth count, clearance and material (aluminium, abradable, steel) for pressure, speed and rub tolerance.'], safety=['Toxic/flammable process gas: buffer or eductor systems to prevent release.'], refs=['API 617'])

MODULES['oil_seal'] = mod(
    definition=('A radial oil seal (lip seal) keeps lubricant inside a housing and dirt outside. An elastomer lip, moulded slightly smaller than the shaft and loaded by a garter spring, runs on a smooth, '
                'hard shaft surface with a thin oil film; its asymmetric shape pumps oil back toward the oil side. A dust lip faces outward.'),
    applications=['Gearboxes, motors and pump bearing housings', 'Vehicle axles, hydraulic motors and general machinery'],
    key_points=['Low pressure (≈ ≤ 0.5 bar)', 'Lip + garter spring + oil film', 'Shaft finish & hardness matter', 'Install with the lip toward the oil'],
    principle=[step('The case is pressed into the housing bore.', 'metal_case'), step('The garter spring presses the lip on the shaft.', 'garter_spring', overlay='pressure'),
               step('A thin oil film lubricates the lip contact.', 'sealing_lip'), step('Lip geometry pumps oil back to the oil side.', 'oil', overlay='flow')],
    curve='Allowable surface speed vs shaft diameter for NBR / FKM / PTFE.',
    params=mc(P('Shaft ≈ 6 – 500 mm'), P('Surface speed ≤ ≈ 10 – 30', 'm/s'), P('Pressure ≤ ≈ 0.5 bar (standard)', '—'), P('NBR ≈ −40…100 °C; FKM ≈ −20…200 °C', '—')),
    install=_CMP, maint=_m([M('Check for weeping / oil drips.', 'sealing_lip', 'weekly')], [M('Check shaft for grooving when seals are replaced.', 'shaft', 'at replacement')], [M('Replace seal; use wear sleeve if shaft is grooved.', 'sealing_lip')], _NL),
    failures=[F('Leakage', ['Oil at the shaft'], ['Hardened lip (heat)', 'Grooved shaft', 'Installed backwards / damaged at fitting'], ['Replace; repair shaft; use fitting tool'], 'sealing_lip'),
              F('Lip wear', ['Short life'], ['Dry running, abrasive dirt, rough shaft'], ['Lubricate; dust lip; correct finish'], 'shaft')],
    quiz=[Q('What keeps the lip loaded as it wears?', ['Garter spring', 'Oil pressure', 'Magnet', 'Case'], 0, 'Spring.'), Q('Which way does the main lip face?', ['Toward the oil', 'Toward the air', 'Either', 'Up'], 0, 'Oil side.'),
          Q('Typical pressure limit of a standard lip seal?', ['≈ 0.5 bar', '≈ 50 bar', '≈ 500 bar', 'No limit'], 0, 'Low.')],
    selection=['Choose elastomer for temperature and fluid; check surface speed, shaft finish Ra ≈ 0.2–0.8 µm and hardness ≥ ≈ 45 HRC.'], safety=['Use fitting sleeves over keyways; never hammer the case directly.'], refs=['ISO 6194', 'DIN 3760'])

MODULES['gland_packing_assembly'] = mod(
    definition=('A gland packing assembly seals a pump shaft with rings of braided packing compressed in a stuffing box by a gland follower. The packing presses on the shaft sleeve and throttles leakage; a '
                'small controlled leakage lubricates and cools it. A lantern ring in the middle of the set can feed clean flush water.'),
    applications=['Water, slurry and general service pumps', 'Valve stems, agitators and older plant equipment'],
    key_points=['Must leak a little (≈ 40–60 drops/min)', 'Tighten evenly, a little at a time', 'Stagger ring joints', 'Sleeve takes the wear'],
    principle=[step('Packing rings fill the stuffing box.', 'packing_rings'), step('The gland follower compresses them.', 'gland_follower', overlay='pressure'),
               step('Pressure drops ring by ring along the shaft.', 'packing_rings', overlay='pressure'), step('The lantern ring distributes flush liquid.', 'lantern_ring', overlay='flow'),
               step('A small leakage lubricates and cools.', 'shaft_sleeve', overlay='flow')],
    curve='Leakage vs gland compression; temperature rises sharply when over-tightened.',
    params=mc(P('Shaft ≈ 20 – 300 mm; packing cross-section ≈ 6 – 25 mm'), P('Surface speed ≤ ≈ 10 – 25', 'm/s'), P('Pressure ≤ ≈ 10 – 25 bar (material dependent)', '—'), P('Temperature per packing material', '—')),
    install=_CMP, maint=_m([M('Check leakage rate and gland temperature.', 'gland_follower', 'daily')], [M('Adjust gland nuts evenly by small steps.', 'gland_studs', 'as needed')], [M('Repack; inspect sleeve; replace if grooved.', 'packing_rings')], _NL),
    failures=[F('Burnt packing', ['Smoke, no leakage, hot gland'], ['Over-tightening, no flush'], ['Repack; adjust correctly; restore flush'], 'packing_rings'),
              F('Excess leakage', ['Steady stream'], ['Worn packing / sleeve, shaft runout'], ['Repack; replace sleeve; check bearings'], 'shaft_sleeve')],
    quiz=[Q('Why must packing leak a little?', ['Liquid lubricates and cools the packing', 'To save water', 'To check flow', 'No reason'], 0, 'Lubrication.'),
          Q('What does the lantern ring do?', ['Distributes flush liquid into the packing', 'Holds the gland', 'Drives the shaft', 'Measures pressure'], 0, 'Flush.'),
          Q('How should joints of successive rings be placed?', ['Staggered (e.g. 90°)', 'In line', 'Random', 'All at top'], 0, 'Stagger.')],
    selection=['Choose packing material (PTFE, graphite, aramid) for fluid, temperature, pressure and speed.'], safety=['Adjust only with guards in place; never touch a rotating sleeve.'], refs=['FSA compression packing manual'])

MODULES['mechanical_cartridge_seal'] = mod(
    definition=('A mechanical cartridge seal seals a rotating shaft with two very flat faces — one rotating with the shaft, one stationary in the gland — pressed together by springs and fluid pressure. A '
                'micro-thin liquid film between the faces lubricates them. The cartridge comes pre-assembled on its own sleeve and gland, set with clips that are removed after installation.'),
    applications=['Process pumps in refineries, chemical and water plants', 'Mixers, agitators and compressors (gas seals)'],
    key_points=['Faces lapped flat to ≈ 1 µm', 'Film ≈ 0.5–1 µm', 'Flush plan cools the faces', 'Remove setting clips before start'],
    principle=[step('The cartridge sleeve turns with the shaft.', 'sleeve'), step('Springs push the rotating face onto the seat.', 'rotating_unit', overlay='pressure'),
               step('A thin liquid film forms between the faces.', 'rotating_face', overlay='pressure'), step('Flush liquid cools the seal chamber.', 'gland_plate', overlay='flow'),
               step('Setting clips centre the cartridge during fitting.', 'setting_clips')],
    curve='Seal face temperature vs PV (pressure × velocity) and flush flow.',
    params=mc(P('Shaft ≈ 20 – 200 mm'), P('Up to ≈ 3600 – 6000', 'rpm'), P('Seal chamber pressure up to ≈ 20 – 40 bar (single)', '—'), P('Flush plan per API 682 (e.g. Plan 11)', '—')),
    install=_CMP, maint=_m([M('Check for leakage and gland temperature.', 'gland_plate', 'daily')], [M('Check flush line, orifice and cooler.', 'gland_plate', 'monthly')], [M('Exchange cartridge; refurbish faces.', 'rotating_face')], _NL),
    failures=[F('Dry running', ['Squeal, heat, rapid leakage'], ['Pump started empty, flush blocked'], ['Prime pump; clear flush; replace faces'], 'rotating_face'),
              F('Setting clips left in', ['Clips rub and break, seal damaged'], ['Installation error'], ['Remove clips before start'], 'setting_clips')],
    quiz=[Q('How thick is the face film?', ['≈ 0.5–1 µm', '≈ 1 mm', '≈ 1 cm', 'Zero'], 0, 'Micro-thin.'), Q('What must be removed before start-up?', ['Setting clips', 'Springs', 'Flush line', 'Sleeve'], 0, 'Clips.'),
          Q('Why use a flush?', ['Cool and clean the faces', 'Add pressure only', 'Lubricate bearings', 'No reason'], 0, 'Cooling.')],
    selection=['Choose arrangement (single/dual), face materials and flush plan per API 682 for the fluid, pressure and temperature.'], safety=['Hazardous fluids need dual seals with barrier/buffer and leak detection.'], refs=['API 682'])

# ===================================================================== bearings
MODULES['thrust_bearing_assembly'] = mod(
    definition=('A tilting-pad thrust bearing carries the axial thrust of a rotor on hydrodynamic oil films. Pads arranged around a thrust collar each tilt on a pivot so a converging oil wedge forms; the '
                'pressure in the wedges carries the load without metal contact. Double-acting bearings have active and inactive pad sets for thrust in both directions.'),
    applications=['Centrifugal compressors, steam and gas turbines', 'Large pumps, gearboxes and hydro generators'],
    key_points=['Pads tilt to form oil wedges', 'Load carried on ≈ 10–50 µm film', 'Pad RTD temperature = health', 'Inactive side takes reverse thrust'],
    principle=[step('The rotor pushes the collar axially.', 'thrust_collar', overlay='thrust'), step('Oil is dragged into the wedge between collar and pad.', 'active_pads', overlay='flow'),
               step('Film pressure builds toward the trailing edge.', 'active_pads', overlay='pressure'), step('Carrier rings hold the pads; the housing holds oil.', 'carrier_rings')],
    curve='Pad temperature and film thickness vs thrust load.',
    params=mc(P('Collar ≈ 100 – 600 mm'), P('Up to ≈ 15,000', 'rpm'), P('Unit load ≈ 1.5 – 4 MPa (design dependent)', '—'), P('Oil ≈ 40–50 °C supply; babbitt ≤ ≈ 120–130 °C', '—')),
    install=_CMP, maint=_m([M('Trend pad temperatures and axial position.', 'active_pads', 'continuous')], [M('Check axial float and oil quality.', 'housing', 'annually')], [M('Inspect pads; replace wiped pads.', 'active_pads')], _OIL),
    failures=[F('Wiped babbitt', ['High pad temperature, axial shift'], ['Overload, oil loss, surge'], ['Replace pads; fix cause'], 'active_pads'), F('Collar damage', ['Scoring'], ['Dirty oil'], ['Recondition; filter oil'], 'thrust_collar')],
    quiz=[Q('What makes the oil wedge?', ['Pads tilting on pivots', 'Grooves only', 'Pumps', 'Magnets'], 0, 'Tilting pads.'), Q('Best health indicator?', ['Pad (babbitt) temperature', 'Colour', 'Noise only', 'Oil level only'], 0, 'RTD.'),
          Q('Why inactive pads?', ['Reverse thrust in transients', 'Spare pads', 'Cooling', 'Weight'], 0, 'Reverse thrust.')],
    selection=['Size from maximum thrust, speed and allowable pad temperature (maker programs).'], safety=['Axial-position trips protect the machine; never bypass.'], refs=['API 617 / 612'])

MODULES['journal_bearing'] = mod(
    definition=('A hydrodynamic journal bearing supports a rotating shaft on an oil film. The shaft runs slightly off-centre in a babbitt-lined bore; its rotation drags oil into the narrowing gap and '
                'generates pressure that lifts the shaft. Oil enters through holes and axial grooves at the split line and leaves at the ends, carrying heat away.'),
    applications=['Turbines, compressors, large motors and generators', 'Engines (crankshaft bearings) and large pumps'],
    key_points=['Film pressure from rotation (no pump needed for load)', 'Clearance ≈ 1–2 µm per mm diameter', 'Eccentricity & attitude angle balance load', 'Most wear at start/stop'],
    principle=[step('Oil is supplied to the grooves.', 'pedestal', overlay='flow'), step('The turning journal drags oil around.', 'journal', overlay='flow'),
               step('The converging gap builds pressure.', 'oil_film', overlay='pressure'), step('The babbitt lining provides a forgiving running surface.', 'babbitt_lining')],
    curve='Eccentricity ratio vs Sommerfeld number.',
    params=mc(P('Journal ≈ 25 – 1000 mm'), P('Up to ≈ 20,000', 'rpm'), P('Specific load ≈ 0.5 – 3 MPa', '—'), P('Babbitt ≤ ≈ 120 °C; oil ISO VG 32/46', '—')),
    install=_CMP, maint=_m([M('Trend bearing temperature and shaft vibration.', 'babbitt_lining', 'continuous')], [M('Check clearance (lead/plastigage) and oil.', 'bearing_shell', 'at outage')], [M('Re-babbitt / replace shells.', 'babbitt_lining')], _OIL),
    failures=[F('Wiping', ['Temperature spike'], ['Oil starvation, overload'], ['Replace shell; restore oil'], 'babbitt_lining'), F('Oil whirl', ['Sub-synchronous vibration ≈ 0.42–0.48×'], ['Light load, high speed'], ['Tilting-pad or pressure-dam bearing'], 'oil_film')],
    quiz=[Q('What generates the film pressure?', ['Shaft rotation dragging oil into a converging gap', 'A high-pressure pump', 'Gravity', 'Magnets'], 0, 'Hydrodynamic.'),
          Q('When does most wear occur?', ['Start-up and shut-down', 'At full speed', 'Never', 'Only overloaded'], 0, 'Low speed.'), Q('What is babbitt?', ['Soft white-metal lining', 'Hard steel', 'Ceramic', 'Rubber'], 0, 'Babbitt.')],
    selection=['From load, speed, viscosity and allowable temperature (ISO 7902).'], safety=['Oil-pressure trips and temperature alarms protect the machine.'], refs=['ISO 7902'])

MODULES['bearing_housing'] = mod(
    definition=('A pump bearing housing (bearing frame) supports the shaft in a radial bearing and a thrust bearing set, holds the lubricating oil and keeps contaminants out. An oil ring riding on the shaft '
                'lifts oil from the sump onto the bearings; a constant-level oiler keeps the oil level right; bearing isolators seal the shaft openings.'),
    applications=['Process pumps (API 610 OH/BB types)', 'Fans, blowers and other overhung machines'],
    key_points=['Radial + duplex thrust bearings', 'Oil level ≈ centre of lowest ball', 'Isolators keep water and dust out', 'Temperature & vibration show health'],
    principle=[step('The shaft turns in two bearings.', 'shaft'), step('The oil ring lifts oil from the sump.', 'oil_ring', overlay='flow'),
               step('Oil wets the bearings and returns.', 'oil_sump'), step('The constant-level oiler and isolators maintain clean oil.', 'accessories', overlay='temperature')],
    curve='Bearing temperature vs oil level (too low and too high both run hot).',
    params=mc(P('Shaft ≈ 25 – 120 mm at bearings'), P('≈ 1000 – 3600', 'rpm'), P('Bearing L10 ≥ ≈ 25,000 h (API 610 basis)', '—'), P('Housing ≤ ≈ 80–85 °C; ISO VG 46/68 oil', '—')),
    install=_CMP, maint=_m([M('Check oiler level, temperature and vibration.', 'accessories', 'daily')], [M('Change oil / sample for analysis.', 'oil_sump', 'quarterly')], [M('Replace bearings and isolators.', 'outboard_bearing_rings')], _OIL),
    failures=[F('Bearing overheating', ['High temperature'], ['Wrong oil level, wrong oil, over-greasing'], ['Correct level; correct oil'], 'oil_sump'), F('Water contamination', ['Milky oil, rust'], ['Failed isolator, washdown'], ['Replace isolator; change oil'], 'accessories')],
    quiz=[Q('What lifts the oil to the bearings?', ['Oil ring', 'Pump', 'Fan', 'Gravity only'], 0, 'Oil ring.'), Q('Right oil level?', ['About the centre of the lowest ball', 'Full housing', 'Empty', 'Top of shaft'], 0, 'Centre of ball.'),
          Q('Leading cause of bearing failure?', ['Contamination / lubrication problems', 'Paint', 'Colour', 'Noise'], 0, 'Contamination.')],
    selection=['Bearings and housing size from loads and speed per API 610; consider oil mist or purge for wet areas.'], safety=['Hot surfaces; never fill oiler while running without procedure.'], refs=['API 610'])

# ===================================================================== couplings
MODULES['expansion_coupling'] = mod(
    definition=('An expansion (axial-float) coupling joins two shafts and lets one move axially, for example as a hot pump or turbine shaft grows. In this gear type, crowned external teeth on each hub mesh with '
                'internal teeth in a sleeve; the teeth transmit torque and can slide, and the crowning also accepts small angular and offset misalignment.'),
    applications=['Turbine- and motor-driven pumps and compressors with thermal growth', 'Steel-mill drives and heavy machinery'],
    key_points=['Transmits torque, allows axial float', 'Crowned teeth tolerate misalignment', 'Must be lubricated', 'Lock-up → large thrust on bearings'],
    principle=[step('The driver hub teeth turn the sleeve.', 'driver_teeth_shaft', overlay='flow'), step('The sleeve drives the other hub.', 'sleeve', overlay='pressure'),
               step('The driven shaft grows and slides axially.', 'driven_teeth_shaft', overlay='thrust'), step('Lubricant lets the teeth slide.', 'lubricant')],
    curve='Coupling axial force vs friction coefficient (lubricated vs dry).',
    params=mc(P('Bore ≈ 20 – 400 mm'), P('Up to ≈ 10,000+', 'rpm'), P('Torque ≈ 0.1 – 1000 kN·m', '—'), P('Axial float ≈ ±(2–10) mm; misalignment ≈ 0.5–1.5° per mesh', '—')),
    install=_CMP, maint=_m([M('Check for grease leakage and noise.', 'sleeve', 'weekly')], [M('Re-grease / check oil spray.', 'lubricant', 'semi-annually')], [M('Inspect tooth wear; replace hubs/sleeve.', 'driver_teeth_shaft')], ['Grease or oil per maker interval.']),
    failures=[F('Tooth wear / lock-up', ['Rising vibration, axial thrust'], ['Lack of lubrication, misalignment'], ['Re-lubricate; align; replace'], 'driven_teeth_shaft'), F('Seal leakage', ['Grease loss'], ['Damaged seal'], ['Replace seal'], 'sleeve')],
    quiz=[Q('Why allow axial float?', ['Thermal growth of the shaft', 'Faster speed', 'Less torque', 'Noise'], 0, 'Thermal growth.'), Q('What happens if teeth run dry?', ['Wear and lock-up', 'Nothing', 'Better', 'Cooler'], 0, 'Lock-up.'),
          Q('What tolerates angular misalignment?', ['Crowned teeth', 'Straight bolts', 'Shaft key', 'Grease'], 0, 'Crowning.')],
    selection=['Size by torque × service factor, speed, bore and required float.'], safety=['Coupling guards required; balance for high speed.'], refs=['API 671', 'AGMA 9000'])

MODULES['universal_joint'] = mod(
    definition=('A universal (Cardan) joint connects two shafts at an angle. Each shaft ends in a yoke; the yokes are linked by a cross whose four journals run in needle bearings. Torque passes through the '
                'angle, but a single joint makes the output speed fluctuate twice per revolution; two joints in phase cancel this.'),
    applications=['Drive shafts of vehicles, rolling mills and paper machines', 'Steering columns and machinery with offset shafts'],
    key_points=['Speed ratio swings between cos β and 1/cos β', 'Use two joints in phase (Z/W) to cancel', 'Needles only oscillate — keep a small angle', 'Grease the cross regularly'],
    principle=[step('The input yoke turns uniformly.', 'input_yoke', overlay='flow'), step('The cross rocks as it transmits torque.', 'cross_spider'),
               step('The output yoke turns with varying speed.', 'output_yoke', overlay='pressure'), step('Supports carry the shafts.', 'supports')],
    curve='Output speed ratio vs input angle for β = 10°, 20°, 30°.',
    params=mc(P('Cross journal ≈ 10 – 150 mm'), P('Up to ≈ 3000 – 6000', 'rpm (size dependent)'), P('Torque ≈ 0.01 – 500 kN·m', '—'), P('Working angle ≈ 1° – 25° (higher for low speed)', '—')),
    install=_CMP, maint=_m([M('Check for play and noise.', 'cross_spider', 'weekly')], [M('Grease the cross bearings.', 'cross_spider', 'monthly')], [M('Replace cross & bearings.', 'cross_spider')], ['Grease the cross journals until fresh grease appears at all four seals.']),
    failures=[F('Brinelling of needle tracks', ['Notchy feel'], ['Zero angle, shock loads'], ['Keep small angle; replace'], 'cross_spider'), F('Vibration', ['2× running speed'], ['Joints out of phase / unequal angles'], ['Phase yokes; equalise angles'], 'output_yoke')],
    quiz=[Q('Does a single U-joint give constant output speed at an angle?', ['No — it fluctuates twice per rev', 'Yes', 'Only at 90°', 'Only reversed'], 0, 'Fluctuation.'),
          Q('How are fluctuations cancelled?', ['Two joints with equal angles and yokes in phase', 'More grease', 'Bigger cross', 'Faster speed'], 0, 'Two joints.'), Q('What links the yokes?', ['Cross (spider)', 'Gear', 'Chain', 'Belt'], 0, 'Cross.')],
    selection=['Size by torque, angle and speed (maker ratings); check bearing life.'], safety=['Guard rotating shafts; secure telescopic sections.'], refs=['Machinery\'s Handbook'])

MODULES['torsional_coupling'] = mod(
    definition=('A highly flexible torsional coupling links an engine flywheel to a driven machine through a soft rubber element. Its low torsional stiffness shifts the shaft system\'s natural frequencies '
                'away from the engine\'s firing orders, and rubber hysteresis damps torque pulsations, protecting gears and generators.'),
    applications=['Diesel generator sets and marine propulsion', 'Engine-driven pumps and compressors'],
    key_points=['Tuned stiffness (torsional vibration analysis)', 'Damps engine torque pulses', 'Allowable damping heat limits rating', 'Rubber ages — inspect for cracks'],
    principle=[step('The flywheel delivers pulsating torque.', 'flywheel_outer', overlay='flow'), step('The rubber element twists and damps.', 'rubber_element', overlay='pressure'),
               step('The hub receives a much smoother torque.', 'hub_shaft'), step('The driven machine bearing carries the shaft.', 'bearing_support')],
    curve='Torsional amplitude vs speed (resonance peaks shifted / damped).',
    params=mc(P('OD ≈ 0.2 – 1.5 m'), P('Up to ≈ 1000 – 3000', 'rpm'), P('Nominal torque ≈ 0.5 – 500 kN·m', '—'), P('Element temperature ≤ ≈ 80–90 °C (rubber)', '—')),
    install=_CMP, maint=_m([M('Look for rubber dust or cracks.', 'rubber_element', 'monthly')], [M('Measure twist marks / check bolts.', 'rubber_element', 'annually')], [M('Replace elements per hours / ageing.', 'rubber_element')], _NL),
    failures=[F('Element overheating', ['Cracks, burning smell'], ['Running near resonance, misfire'], ['TVA review; fix engine; replace'], 'rubber_element'), F('Bolt loosening', ['Knocking'], ['Wrong torque'], ['Torque to spec'], 'flywheel_outer')],
    quiz=[Q('Main purpose?', ['Tune and damp torsional vibration', 'Increase speed', 'Seal oil', 'Cool engine'], 0, 'Torsional.'), Q('What study selects stiffness?', ['Torsional vibration analysis', 'Pump curve', 'Thermal survey', 'Leak test'], 0, 'TVA.'),
          Q('What limits the element rating?', ['Heat from damping', 'Paint', 'Weight', 'Colour'], 0, 'Heat.')],
    selection=['From engine torque, firing orders and TVA; check misalignment capacity.'], safety=['Guard; never run with damaged elements.'], refs=['Maker catalogues', 'Class rules'])

# ===================================================================== pump components
MODULES['shaft_sleeve'] = mod(
    definition=('A shaft sleeve is a replaceable tube over the pump shaft where packing or a seal runs. It protects the shaft from wear and corrosion; when grooved it is replaced instead of the shaft. It is '
                'keyed or clamped to turn with the shaft, located against the impeller hub and sealed with an O-ring.'),
    applications=['Packed and mechanically sealed centrifugal pumps', 'Agitators and valves with packing'],
    key_points=['Sacrificial wear surface', 'Hard coating (ceramic / WC / hardened steel)', 'O-ring stops creep leakage', 'Check runout after fitting'],
    principle=[step('The sleeve slides over the shaft and locates on the impeller hub.', 'sleeve'), step('The O-ring seals between sleeve and shaft.', 'sleeve_seals'),
               step('Packing rubs on the sleeve, not the shaft.', 'stuffing_box', overlay='wear'), step('Grooved sleeves are replaced at overhaul.', 'sleeve', overlay='wear')],
    curve='Sleeve wear depth vs running hours for different coatings.',
    params=mc(P('Sleeve OD ≈ 25 – 200 mm'), P('As pump', 'rpm'), P('Runs under packing / seal', '—'), P('Runout ≤ ≈ 0.05 mm TIR typical', '—')),
    install=_CMP, maint=_m([M('Monitor packing leakage (sleeve wear sign).', 'stuffing_box', 'daily')], [M('Inspect sleeve at repack.', 'sleeve', 'at repack')], [M('Replace sleeve and O-ring.', 'sleeve')], _NL),
    failures=[F('Grooving', ['Packing cannot be adjusted'], ['Abrasives, over-tightened packing'], ['Replace sleeve; harder coating'], 'sleeve'), F('Leak under sleeve', ['Leak despite good packing'], ['O-ring missing / damaged'], ['Replace O-ring'], 'sleeve_seals')],
    quiz=[Q('Why use a sleeve?', ['So the cheap sleeve wears, not the shaft', 'For balance', 'To add speed', 'For looks'], 0, 'Sacrificial.'), Q('What seals under the sleeve?', ['O-ring / gasket', 'Packing', 'Grease', 'Nothing'], 0, 'O-ring.'),
          Q('What to check after fitting?', ['Runout', 'Colour', 'Weight', 'Length only'], 0, 'Runout.')],
    selection=['Material and coating for abrasion and corrosion; hook vs clamped type.'], safety=['Lock out before removing; heavy rotating assemblies.'], refs=['API 610'])

MODULES['wear_ring'] = mod(
    definition=('Wear rings are renewable rings — one on the impeller eye, one in the casing — forming a small running clearance between the high-pressure discharge side and the low-pressure eye. They limit '
                'internal recirculation and are the sacrificial parts that wear instead of the impeller and casing.'),
    applications=['Closed-impeller centrifugal pumps', 'Multistage pumps (also interstage bushings)'],
    key_points=['Clearance controls internal leakage', 'Replace at ≈ 2× new clearance', 'Dissimilar, galling-resistant materials', 'API 610 sets minimum clearances'],
    principle=[step('Discharge pressure acts in front of the shroud.', 'casing', overlay='pressure'), step('Leakage passes the narrow wear-ring clearance.', 'casing_wear_ring', overlay='flow'),
               step('It re-enters the eye, wasting energy.', 'impeller', overlay='flow'), step('The rings wear instead of the impeller.', 'impeller_wear_ring', overlay='wear')],
    curve='Pump efficiency vs wear-ring clearance.',
    params=mc(P('Ring ≈ 50 – 600 mm diameter'), P('As pump', 'rpm'), P('Pressure difference = stage head', '—'), P('Diametral clearance ≈ 0.25 – 0.5 mm (API 610 table)', '—')),
    install=_CMP, maint=_m([M('Trend pump performance (flow/head/power).', 'impeller', 'monthly')], [M('Measure clearance at overhaul.', 'casing_wear_ring', 'at overhaul')], [M('Replace rings when ≈ 2× new clearance.', 'impeller_wear_ring')], _NL),
    failures=[F('Excess clearance', ['Lower head and efficiency'], ['Abrasive wear, erosion'], ['Replace rings'], 'casing_wear_ring'), F('Galling / seizure', ['Pump locks, damage'], ['Same materials, tight clearance, dry run'], ['Use dissimilar materials; correct clearance'], 'impeller_wear_ring')],
    quiz=[Q('What does the clearance separate?', ['High-pressure discharge from low-pressure eye', 'Oil from water', 'Motor from pump', 'Air from gas'], 0, 'Pressure zones.'),
          Q('When to replace?', ['At about twice new clearance', 'Never', 'Every day', 'When painted'], 0, '2×.'), Q('Why dissimilar materials?', ['Avoid galling', 'Colour', 'Weight', 'Cost only'], 0, 'Galling.')],
    selection=['Clearance and materials per API 610 for temperature and service.'], safety=['Seizure can shatter rings — follow minimum clearance rules.'], refs=['API 610'])

MODULES['impeller'] = mod(
    definition=('A centrifugal pump impeller is a rotating wheel with curved vanes between a back shroud and a front shroud. Liquid enters at the eye, is turned outward through the vane passages and leaves '
                'the rim with higher pressure and velocity. Back vanes and balance holes reduce axial thrust; the impeller is dynamically balanced.'),
    applications=['All centrifugal pumps (water, process, slurry with open/semi-open types)', 'Fans and compressors (similar principle)'],
    key_points=['Head ∝ tip speed² (u₂ = π·D·n)', 'Backward-curved vanes → stable curve', 'Trim diameter to adjust duty', 'Balance to ISO 21940 grade'],
    principle=[step('Liquid enters the eye.', 'impeller', overlay='flow'), step('Vanes add angular momentum.', 'impeller', overlay='pressure'), step('Pressure and velocity rise to the rim.', 'impeller', overlay='pressure'),
               step('Back vanes reduce pressure behind the impeller.', 'back_vanes'), step('The key and shaft drive it.', 'shaft_key')],
    curve='Head–flow curve; effect of trimming (affinity).',
    params=mc(P('Diameter ≈ 80 – 1500 mm'), P('≈ 750 – 3600 (higher for special pumps)', 'rpm'), P('Head per stage ≈ 5 – 300 m', '—'), P('Balance G6.3 (typical pumps)', '—')),
    install=_CMP, maint=_m([M('Trend vibration and performance.', 'impeller', 'monthly')], [M('Inspect for erosion / cavitation.', 'impeller', 'at overhaul')], [M('Repair or replace; rebalance.', 'impeller')], _NL),
    failures=[F('Cavitation damage', ['Noise, pitted vanes'], ['Low NPSHa'], ['Improve suction; NPSH margin'], 'impeller'), F('Imbalance', ['1× vibration'], ['Erosion, deposits'], ['Clean; rebalance'], 'impeller')],
    quiz=[Q('Head depends mainly on…', ['Tip speed squared', 'Colour', 'Shaft length', 'Weight only'], 0, 'u₂².'), Q('Purpose of back vanes?', ['Reduce pressure behind impeller / thrust', 'Add flow', 'Cool', 'Balance only'], 0, 'Thrust.'),
          Q('How is duty reduced permanently?', ['Trim impeller diameter', 'Paint', 'Add vanes', 'Lower NPSH'], 0, 'Trim.')],
    selection=['From duty point, specific speed and NPSH; material for fluid.'], safety=['Lock out; heavy parts; correct rotation before start.'], refs=['Gülich — Centrifugal Pumps', 'API 610'])

# ===================================================================== rotating components & power transmission
MODULES['rotor'] = mod(
    definition=('The rotor of an induction motor is the rotating part: a laminated steel core with conducting bars in its slots, short-circuited by end rings (the squirrel cage), on a shaft that carries the '
                'bearing journals and cooling fan. The stator\'s rotating field induces currents in the bars, producing torque.'),
    applications=['Squirrel-cage induction motors for pumps, fans and compressors', 'Generators (similar rotating assemblies)'],
    key_points=['Slip makes the induced current', 'Skewed bars smooth torque', 'Balanced as an assembly', 'Broken bars → current side-bands'],
    principle=[step('The stator field sweeps across the bars.', 'rotor_core_bars', overlay='magnetic_field'), step('Induced currents flow through bars and end rings.', 'end_rings'),
               step('Force on the currents turns the rotor.', 'rotor_core_bars', overlay='magnetic_field'), step('The shaft delivers torque; the fan cools.', 'shaft_fan', overlay='flow')],
    curve='Torque–speed curve of an induction motor.',
    params=mc(P('Core ≈ 0.05 – 1.5 m diameter'), P('Synchronous ≈ 750 – 3600', 'rpm'), P('Motor ratings ≈ 0.1 – 20,000 kW', '—'), P('Slip ≈ 0.5 – 5 % at rated load', '—')),
    install=_CMP, maint=_m([M('Trend vibration and current.', 'shaft_fan', 'monthly')], [M('Motor current signature analysis.', 'rotor_core_bars', 'annually')], [M('Inspect bars/rings; rebalance at overhaul.', 'end_rings')], _NL),
    failures=[F('Broken rotor bar', ['Current side-bands, vibration'], ['Frequent starts, thermal stress'], ['Repair/replace rotor'], 'rotor_core_bars'), F('Imbalance', ['1× vibration'], ['Fan damage, deposits'], ['Clean; rebalance'], 'shaft_fan')],
    quiz=[Q('What induces rotor current?', ['Relative motion of the rotating field (slip)', 'Brushes', 'Battery', 'Permanent magnets'], 0, 'Slip.'), Q('Why skew bars?', ['Smooth torque, less noise', 'Cheaper', 'Colour', 'Weight'], 0, 'Skew.'),
          Q('How detect broken bars?', ['Current signature side-bands', 'Paint test', 'Oil colour', 'Weight'], 0, 'MCSA.')],
    selection=['Matched to stator by motor maker.'], safety=['Heavy — use correct lifting; protect journals.'], refs=['IEC 60034'])

MODULES['stator'] = mod(
    definition=('The stator is the stationary part of an induction motor: a frame holding a laminated, slotted core in which three-phase windings are laid. Currents 120° apart in the three windings create a '
                'magnetic field that rotates at synchronous speed and drives the rotor.'),
    applications=['Induction motors for all industrial drives', 'Generators (armature windings)'],
    key_points=['n_s = 120·f / p', 'Laminations cut eddy-current loss', 'Insulation class sets temperature limit', '10 °C over → ≈ half insulation life'],
    principle=[step('Three-phase supply enters the terminal box.', 'terminal_box', overlay='flow'), step('Currents flow in the windings.', 'windings', overlay='magnetic_field'),
               step('A rotating field forms in the bore.', 'rotating_field', overlay='magnetic_field'), step('The laminated core carries the flux.', 'stator_core')],
    curve='Insulation life vs winding temperature.',
    params=mc(P('Bore ≈ 0.05 – 1.5 m'), P('Synchronous ≈ 750 – 3600', 'rpm'), P('≈ 0.1 – 20,000 kW', '—'), P('Class F (155 °C) / H (180 °C) insulation', '—')),
    install=_CMP, maint=_m([M('Check winding temperature and currents.', 'windings', 'daily')], [M('Insulation resistance / PI test.', 'windings', 'annually')], [M('Clean, dry, varnish; rewind if needed.', 'windings')], _NL),
    failures=[F('Insulation failure', ['Earth fault trip'], ['Overheating, moisture, contamination'], ['Dry out / rewind'], 'windings'), F('Single phasing', ['Hum, overheating'], ['Lost phase'], ['Protection relays'], 'terminal_box')],
    quiz=[Q('Synchronous speed of a 4-pole motor at 50 Hz?', ['1500 rpm', '3000 rpm', '1000 rpm', '750 rpm'], 0, '120×50/4.'), Q('Why laminate the core?', ['Reduce eddy-current losses', 'Look nice', 'Lighter only', 'Cooling only'], 0, 'Eddy currents.'),
          Q('Common insulation test?', ['Insulation resistance / polarisation index', 'Pressure test', 'Leak test', 'Hardness'], 0, 'IR/PI.')],
    selection=['By motor rating, voltage, enclosure and duty.'], safety=['High voltage — isolate and earth before work.'], refs=['IEC 60034', 'IEEE 43'])

MODULES['gear_assembly'] = mod(
    definition=('A gear assembly transmits rotation and torque between shafts through meshing teeth. In this spur train a driving pinion turns an idler, which turns a larger driven gear; the output turns '
                'three times slower with about three times the torque, and the idler reverses direction without changing the ratio.'),
    applications=['Gearboxes, machine tools and conveyors', 'Pump and compressor speed increasers / reducers'],
    key_points=['Ratio = z_driven / z_driver', 'Idler changes direction only', '20° pressure angle', 'Backlash, contact pattern, lubrication'],
    principle=[step('The pinion drives the idler.', 'pinion', overlay='flow'), step('The idler reverses direction.', 'idler'), step('The driven gear turns slower with more torque.', 'gear', overlay='pressure'),
               step('Bearings carry tooth forces.', 'bearings')],
    curve='Torque and speed through the train.',
    params=mc(P('Module ≈ 1 – 30 mm'), P('Pitch-line speed up to ≈ 20 m/s (spur)', 'm/s'), P('Torque per gear rating (ISO 6336)', '—'), P('Lubricated by splash or spray oil', '—')),
    install=_CMP, maint=_m([M('Listen for noise; check temperature.', 'gear', 'daily')], [M('Check backlash and contact pattern; oil analysis.', 'pinion', 'annually')], [M('Replace worn gears / bearings.', 'bearings')], _OIL),
    failures=[F('Pitting', ['Noise, vibration at mesh frequency'], ['Overload, poor lubrication'], ['Correct load/oil; replace'], 'pinion'), F('Tooth breakage', ['Sudden stop'], ['Shock load, fatigue'], ['Replace; protect drive'], 'gear')],
    quiz=[Q('Ratio with z1 = 16 and z3 = 48?', ['3 : 1', '1 : 3', '2 : 1', '4 : 1'], 0, '48/16.'), Q('What does an idler do?', ['Reverses direction', 'Changes ratio', 'Adds power', 'Cools'], 0, 'Direction.'),
          Q('Standard pressure angle?', ['20°', '45°', '5°', '90°'], 0, '20°.')],
    selection=['By power, speed, ratio and service factor (ISO 6336 / AGMA 2001).'], safety=['Guard all meshes; lock out.'], refs=['ISO 6336', 'AGMA 2001'])

# ===================================================================== lubrication
MODULES['lubricating_oil_skid'] = mod(
    definition=('A lubricating oil skid supplies clean, cool oil at controlled pressure to the bearings of a turbine, compressor or large pump. Main and standby pumps draw from a heated reservoir, coolers and '
                'duplex filters condition the oil, a pressure-control valve spills excess back, and an accumulator bridges pump switch-over.'),
    applications=['Turbo-compressors, steam and gas turbines', 'Large pumps, gearboxes and generators'],
    key_points=['Standby pump auto-starts on low pressure', 'Duplex filters & coolers switch on-line', 'Oil cleanliness (ISO 4406) is critical', 'Rundown / accumulator protects coast-down'],
    principle=[step('The main pump draws oil from the reservoir.', 'pump_main', overlay='flow'), step('Coolers remove bearing heat.', 'coolers', overlay='flow'),
               step('Duplex filters clean the oil.', 'filters'), step('The PCV holds header pressure.', 'header_controls', overlay='pressure'), step('Oil returns to the reservoir.', 'reservoir', overlay='flow')],
    curve='Header pressure vs flow with PCV spill-back.',
    params=mc(P('Reservoir ≈ 0.5 – 20 m³'), P('Pumps ≈ 1500 – 3600', 'rpm'), P('Flow ≈ 50 – 2000 L/min', '—'), P('Supply ≈ 1–2.5 bar(g), 40–50 °C', '—')),
    install=_SYS, maint=_m([M('Check pressures, temperatures, filter ΔP, level.', 'header_controls', 'daily')], [M('Oil analysis; test standby auto-start.', 'oil', 'monthly')], [M('Clean reservoir; service pumps/coolers.', 'reservoir')], _OIL),
    failures=[F('Low oil pressure trip', ['Machine trips'], ['Filter blocked, PCV fault, pump failure'], ['Switch filter; repair'], 'filters'), F('Water in oil', ['Milky oil'], ['Cooler leak, seal steam'], ['Repair; purify oil'], 'coolers')],
    quiz=[Q('What starts on low pressure?', ['Standby pump', 'Heater', 'Cooler', 'Filter'], 0, 'Standby.'), Q('Why duplex filters?', ['Change element on-line', 'Double flow', 'Cooling', 'Weight'], 0, 'On-line change.'),
          Q('What does the PCV do?', ['Spills excess oil to hold pressure', 'Heats oil', 'Filters', 'Cools'], 0, 'Pressure control.')],
    selection=['Per API 614 from machine oil demand, pressure and cleanliness.'], safety=['Oil fires: keep hot surfaces insulated; spill containment.'], refs=['API 614'])

MODULES['grease_lubrication_system'] = mod(
    definition=('Grease lubrication feeds a rolling bearing with grease — base oil held in a thickener — through a grease nipple, by hand with a grease gun or automatically with a single-point lubricator. A '
                'relief plug lets old grease escape so the housing does not over-pressurise or overfill.'),
    applications=['Plummer blocks on conveyors, fans and crushers', 'Electric motor bearings and outdoor machinery'],
    key_points=['Right amount: G ≈ 0.005·D·B (g)', 'Right interval from maker charts', 'Open relief while greasing', 'Do not mix incompatible greases'],
    principle=[step('Fresh grease enters through the nipple.', 'nipple_relief', overlay='flow'), step('It reaches the rolling elements.', 'rollers'),
               step('Old grease purges through the relief.', 'nipple_relief', overlay='flow'), step('An automatic lubricator doses continuously.', 'lubricator_piston', overlay='temperature')],
    curve='Relubrication interval vs speed factor n·dm and temperature.',
    params=mc(P('Bearing bore ≈ 20 – 300 mm'), P('Speed factor n·dm up to ≈ 300,000 – 500,000 (grease)', 'mm/min'), P('Grease NLGI 2 typical', '—'), P('Lubricator 1 – 12 month settings', '—')),
    install=_SYS, maint=_m([M('Check lubricator level / bearing temperature.', 'single_point_lubricator', 'weekly')], [M('Relubricate per schedule.', 'nipple_relief', 'as scheduled')], [M('Clean housing; replace grease & seals.', 'plummer_block')], ['Use the specified grease; count gun strokes for quantity.']),
    failures=[F('Over-greasing', ['High temperature after greasing'], ['Too much grease, relief closed'], ['Purge; correct quantity'], 'grease_fill'), F('Starvation', ['Noise, heat'], ['Missed greasing, empty lubricator'], ['Re-establish schedule'], 'single_point_lubricator')],
    quiz=[Q('Why open the relief plug?', ['Let old grease out, avoid over-pressure', 'Add air', 'Drain oil', 'Look inside'], 0, 'Relief.'), Q('Grease is…', ['Oil held in a thickener', 'Solid wax', 'Pure oil', 'Water'], 0, 'Oil + thickener.'),
          Q('Risk of mixing greases?', ['Incompatible thickeners can soften/harden', 'None', 'Better', 'Colour'], 0, 'Compatibility.')],
    selection=['Grease type for speed, temperature, load and environment; interval from charts.'], safety=['Never grease rotating machines without guarding / safe access.'], refs=['SKF Bearing Maintenance Handbook'])

MODULES['centralized_lubrication_system'] = mod(
    definition=('A centralized (progressive) lubrication system feeds many bearings from one pump unit. Grease is pumped to a progressive divider whose pistons discharge in a fixed sequence, sending a measured '
                'dose to each feed line; a cycle indicator proves the whole divider has completed, so a blocked point is detected.'),
    applications=['Conveyors, crushers and mobile mining equipment', 'Paper machines, presses and machine tools'],
    key_points=['Measured doses to every point', 'Sequence guarantees delivery', 'Blockage → system stops → alarm', 'Small frequent doses'],
    principle=[step('The pump unit pressurises the main line.', 'pump_unit', overlay='flow'), step('Divider pistons discharge in sequence.', 'divider_block', overlay='pressure'),
               step('Each feed line delivers a dose.', 'lines', overlay='flow'), step('The cycle indicator confirms each cycle.', 'cycle_indicator')],
    curve='Delivered volume per cycle vs divider section size.',
    params=mc(P('Reservoir ≈ 2 – 30 L'), P('Pump cycles per controller', '—'), P('Up to ≈ 300 bar system pressure', '—'), P('Grease NLGI 000 – 2', '—')),
    install=_SYS, maint=_m([M('Check reservoir level and alarms.', 'grease_reservoir', 'daily')], [M('Check every lube point receives grease.', 'lube_points', 'monthly')], [M('Service pump element and dividers.', 'divider_block')], ['Refill with the specified grease through the fill coupling only (clean).']),
    failures=[F('Blocked line', ['Cycle fault alarm, pressure high'], ['Crushed line, hardened grease'], ['Find blocked point; replace line'], 'lines'), F('Empty reservoir', ['Low-level alarm'], ['Missed refill'], ['Refill; bleed air'], 'grease_reservoir')],
    quiz=[Q('What happens if one point blocks?', ['Whole divider stops and alarms', 'Others get more', 'Nothing', 'Pump speeds up'], 0, 'Fail-safe.'), Q('What proves a cycle completed?', ['Cycle indicator / switch', 'Noise', 'Colour', 'Temperature'], 0, 'Indicator.'),
          Q('Advantage over manual greasing?', ['Small frequent doses, no missed points', 'More grease', 'No pump', 'Cheaper grease'], 0, 'Consistency.')],
    selection=['Points, dose per point, grease type and pump size.'], safety=['High pressure lines — depressurise before work.'], refs=['SKF Lincoln manuals'])

MODULES['oil_mist_lubrication_system'] = mod(
    definition=('An oil mist system lubricates many pump and motor bearings from one generator. Compressed air through a venturi atomises oil into a very fine mist (≈ 1–3 µm) carried at low pressure through a '
                'header and drop legs; reclassifier fittings at each bearing coalesce the mist into droplets that wet the bearings. The slight positive pressure keeps contaminants out.'),
    applications=['Refinery and petrochemical pump fields', 'Electric motors and standby equipment (preservation)'],
    key_points=['Header ≈ 2–5 kPa', 'Take drop legs from the top of the header', 'Reclassifiers at bearings', 'Very low oil consumption'],
    principle=[step('Air atomises oil in the mist head.', 'mist_head', overlay='pressure'), step('Mist travels along the header.', 'header', overlay='flow'),
               step('Drop legs feed each bearing.', 'drop_legs_reclassifiers', overlay='flow'), step('Reclassifiers condense the mist on the bearings.', 'pump_1')],
    curve='Mist density vs air pressure and oil temperature.',
    params=mc(P('Generators serve ≈ 20 – 100+ bearings'), P('Bearings at pump speeds', 'rpm'), P('Mist header ≈ 2 – 5 kPa', '—'), P('Oil ISO VG 68–100 typical', '—')),
    install=_SYS, maint=_m([M('Check console alarms and oil level.', 'mist_head', 'daily')], [M('Check drain bottles / reclassifiers.', 'drop_legs_reclassifiers', 'monthly')], [M('Service console; clean header.', 'generator_console')], _OIL),
    failures=[F('Loss of mist', ['Console alarm'], ['Air failure, empty reservoir'], ['Restore air/oil'], 'mist_head'), F('Dry bearing', ['High temperature'], ['Plugged reclassifier'], ['Clean / replace fitting'], 'drop_legs_reclassifiers')],
    quiz=[Q('Why take drop legs from the top of the header?', ['Avoid draining condensed oil into bearings', 'Easier', 'Cheaper', 'Faster mist'], 0, 'Top take-off.'),
          Q('Purpose of a reclassifier?', ['Coalesce mist into droplets at the bearing', 'Filter air', 'Raise pressure', 'Heat oil'], 0, 'Coalesce.'), Q('Header pressure?', ['≈ 2–5 kPa', '≈ 10 bar', '≈ 100 bar', 'Vacuum'], 0, 'Low.')],
    selection=['Size generator for bearing count (BEU method); route sloped header.'], safety=['Stray mist is a slip / environmental issue — closed systems collect it.'], refs=['Bloch — Oil Mist Lubrication'])

# ===================================================================== maintenance tools & condition monitoring
MODULES['shaft_alignment_system'] = mod(
    definition=('Shaft alignment brings the shafts of a driver and a driven machine onto one centreline. With dial indicators on a bracket, both shafts are turned together and rim and face readings give the '
                'offset and angularity; the movable machine (usually the motor) is then shimmed and moved with jacking bolts until within tolerance.'),
    applications=['Pump–motor, fan–motor and gearbox trains', 'Any coupled rotating machinery after installation or maintenance'],
    key_points=['Offset & angularity, vertical & horizontal', 'Check soft foot first', 'Shim vertical, jack horizontal', 'Allow for thermal growth'],
    principle=[step('Mount the bracket and indicators.', 'indicator_bracket'), step('Rotate both shafts together and read rim & face.', 'pump_shaft_hub', overlay='pressure'),
               step('Calculate offset and angularity.', 'motor_shaft_hub'), step('Shim and jack the motor into line.', 'shims_jacking_bolts', overlay='pressure')],
    curve='Vibration and bearing life vs misalignment.',
    params=mc(P('Shafts ≈ 20 – 300 mm'), P('Tolerance tightens with speed', 'rpm'), P('Offset ≈ 0.05 – 0.08 mm at 1500 rpm (typical table)', '—'), P('Readings at 12-3-6-9 o\'clock', '—')),
    install=_TOOL, maint=_m([M('Check indicators and bracket sag before use.', 'indicator_bracket', 'each use')], [M('Re-check alignment after pipe work / hot run.', 'motor', 'after changes')], [M('Calibrate indicators.', 'indicator_bracket')], _NL),
    failures=[F('Wrong readings', ['Results do not repeat'], ['Bracket sag, loose mounting, soft foot'], ['Measure sag; tighten; fix soft foot'], 'indicator_bracket'), F('Misalignment returns', ['Vibration after start'], ['Pipe strain, thermal growth'], ['Remove strain; hot alignment'], 'pump')],
    quiz=[Q('Which machine is usually moved?', ['The motor (movable machine)', 'The pump', 'Both always', 'Neither'], 0, 'Motor.'), Q('What first?', ['Correct soft foot', 'Paint', 'Grease', 'Run'], 0, 'Soft foot.'),
          Q('Vertical corrections use…', ['Shims', 'Jacking bolts only', 'Hammer', 'Grease'], 0, 'Shims.')],
    selection=['Dial indicators for simple jobs; laser for precision and speed.'], safety=['Lock out both machines before turning shafts by hand.'], refs=['API 686', 'Piotrowski'])

MODULES['laser_alignment_equipment'] = mod(
    definition=('Laser alignment equipment measures shaft misalignment with two units, each with a laser and a position-sensitive detector, clamped to the two shafts. Turning the shafts together moves the beam '
                'spots; the display computes offset and angularity and gives shim and move values for each foot of the movable machine.'),
    applications=['Precision alignment of pumps, motors, fans, gearboxes, compressors', 'Machine-train alignment and thermal-growth checks'],
    key_points=['Resolution ≈ 1 µm', 'Only ≈ 70–140° rotation needed', 'Live move mode', 'No bracket sag'],
    principle=[step('Mount S- and M-units on the shafts.', 'stationary_unit'), step('Laser beams strike the detectors.', 'laser_beams', overlay='pressure'),
               step('Rotate shafts 9–12–3 o\'clock.', 'movable_unit', overlay='flow'), step('The display gives corrections.', 'display_unit')],
    curve='Alignment tolerance vs speed.',
    params=mc(P('Shafts ≈ 10 – 500 mm'), P('Tolerance table by speed', 'rpm'), P('Measuring distance up to several metres', '—'), P('Resolution ≈ 0.001 mm', '—')),
    install=_TOOL, maint=_m([M('Charge batteries; clean optics.', 'stationary_unit', 'each use')], [M('Check calibration certificate.', 'display_unit', 'annually')], [M('Send for recalibration.', 'stationary_unit')], _NL),
    failures=[F('Unstable readings', ['Values drift'], ['Air turbulence / heat, loose brackets'], ['Shield beam; tighten'], 'laser_beams'), F('Beam off detector', ['Out of range'], ['Large misalignment'], ['Rough-align first'], 'movable_unit')],
    quiz=[Q('Main advantage over dial indicators?', ['Higher precision and no bracket sag', 'Cheaper', 'No power', 'No rotation'], 0, 'Precision.'), Q('Rotation needed?', ['≈ 70–140°', '0°', '720°', '1080°'], 0, 'Partial rotation.'),
          Q('What is checked before measuring?', ['Soft foot', 'Paint', 'Oil colour', 'Noise'], 0, 'Soft foot.')],
    selection=['By shaft size, distance and functions (live move, thermal growth, train alignment).'], safety=['Class 2 lasers — do not stare into the beam; lock out machines.'], refs=['Maker manuals'])

MODULES['dynamic_balancing_machine'] = mod(
    definition=('A dynamic balancing machine spins a rotor on sensitive pedestals, measures the once-per-revolution vibration caused by unbalance and its phase (from a reference mark), and computes the mass '
                'and angle of correction in two planes so both static and couple unbalance are removed to the required grade.'),
    applications=['Fan rotors, pump impellers, motor rotors after repair', 'Turbine and compressor rotors, rolls and crankshafts'],
    key_points=['F = m·e·ω² rises with speed²', 'Two planes cancel static + couple', 'Grade G per ISO 21940-11', 'Reference mark gives angle'],
    principle=[step('The drive spins the rotor.', 'drive_shaft', overlay='flow'), step('Unbalance shakes the pedestals once per turn.', 'pedestal_1', overlay='pressure'),
               step('Pick-ups and photo-cell measure amplitude and phase.', 'console_sensors'), step('Correction weights are fitted in two planes.', 'rotor', overlay='pressure')],
    curve='Permissible residual unbalance vs speed for G2.5 / G6.3.',
    params=mc(P('Rotor mass ≈ 1 kg – 50 t'), P('Balancing speed ≈ 300 – 3000', 'rpm'), P('Residual U_per = G·m / ω', 'g·mm'), P('Soft- or hard-bearing machines', '—')),
    install=_TOOL, maint=_m([M('Check rollers and sensors.', 'pedestal_1', 'weekly')], [M('Verify with test rotor.', 'console_sensors', 'monthly')], [M('Calibration per ISO 21940-21.', 'console_sensors')], _OIL),
    failures=[F('Non-repeatable results', ['Readings vary'], ['Loose parts on rotor, worn rollers'], ['Fix rotor; replace rollers'], 'pedestal_1'), F('Wrong angle', ['Correction worsens'], ['Reference mark / sensor misread'], ['Re-check reference'], 'console_sensors')],
    quiz=[Q('Unbalance force grows with…', ['Speed squared', 'Speed', 'Constant', 'Temperature'], 0, 'ω².'), Q('Why two planes?', ['Remove static and couple unbalance', 'Faster', 'Cheaper', 'Noise'], 0, 'Dynamic.'),
          Q('Typical grade for pump impellers?', ['G6.3', 'G400', 'G0.4', 'G40'], 0, 'G6.3.')],
    selection=['By rotor mass, size, speed and required grade.'], safety=['Guards / enclosure around spinning rotors; secure weights.'], refs=['ISO 21940-11', 'ISO 21940-21'])

MODULES['vibration_monitoring_system'] = mod(
    definition=('A vibration monitoring system measures machine vibration continuously: accelerometers on bearing housings (horizontal, vertical, axial), proximity probes measuring shaft movement in oil-film '
                'bearings, and a keyphasor for phase. A monitor rack compares readings with alert and trip limits and feeds trends to the control system.'),
    applications=['Critical turbomachinery protection (API 670)', 'Pumps, fans and motors in process plants'],
    key_points=['ISO 20816 zones A–D', '1× unbalance, 2× misalignment', 'Bearing defect frequencies', 'Voting & delays avoid false trips'],
    principle=[step('Accelerometers sense casing vibration.', 'accelerometers', overlay='pressure'), step('Proximity probes sense shaft motion.', 'proximity_probes'),
               step('Signals go to the rack.', 'monitor_rack', overlay='flow'), step('Alerts and trips protect the machine.', 'monitor_rack')],
    curve='Vibration trend vs time with alert / danger limits.',
    params=mc(P('Machines of any size'), P('Up to ≈ 20,000+', 'rpm'), P('Velocity mm/s RMS; displacement µm pk-pk', '—'), P('Frequency range ≈ 10–1000 Hz (velocity)', '—')),
    install=_TOOL, maint=_m([M('Review alarms and trends.', 'monitor_rack', 'daily')], [M('Check sensor mounting and gap voltages.', 'proximity_probes', 'at outage')], [M('Loop-test channels and trips.', 'monitor_rack')], _NL),
    failures=[F('False trip', ['Trip without real vibration'], ['Loose connector, single-channel logic'], ['Fix wiring; 2oo2 voting'], 'monitor_rack'), F('Sensor detached', ['Flat or noisy signal'], ['Mounting failure'], ['Remount, stud'], 'accelerometers')],
    quiz=[Q('Dominant 1× vibration suggests…', ['Unbalance', 'Misalignment', 'Bearing defect', 'Cavitation'], 0, 'Unbalance.'), Q('Proximity probes measure…', ['Shaft relative displacement', 'Temperature', 'Pressure', 'Flow'], 0, 'Displacement.'),
          Q('Standard for protection systems?', ['API 670', 'API 610', 'ISO 5167', 'NFPA 20'], 0, 'API 670.')],
    selection=['Sensors by bearing type and machine criticality; rack per API 670.'], safety=['Never bypass trips without authorised procedure.'], refs=['ISO 20816', 'API 670'])

MODULES['online_condition_monitoring_system'] = mod(
    definition=('An online condition monitoring system gathers vibration, temperature and oil-condition data from many machines continuously through wired or wireless sensors and a gateway into a historian '
                'and analytics, which compare trends with baselines and alarm limits so developing faults are found early and repairs can be planned.'),
    applications=['Plant-wide monitoring of balance-of-plant machines', 'Remote sites and hazardous areas where routes are hard'],
    key_points=['Detect faults inside the P–F interval', 'Trend vs baseline', 'Wireless trade-offs: data rate vs battery', 'Critical machines still need API 670 protection'],
    principle=[step('Sensors measure on each machine.', 'wireless_sensors'), step('Data travels to the gateway.', 'gateway', overlay='flow'),
               step('Server analyses trends.', 'server_dashboard', overlay='flow'), step('Dashboard shows health and alerts.', 'server_dashboard', overlay='pressure')],
    curve='P–F curve: condition vs time from potential failure to functional failure.',
    params=mc(P('Tens to thousands of measurement points'), P('Any', 'rpm'), P('Update rate seconds – hours', '—'), P('Battery life ≈ 2–5 years (wireless, typical)', '—')),
    install=_TOOL, maint=_m([M('Review dashboard alerts.', 'server_dashboard', 'daily')], [M('Check battery and network health.', 'gateway', 'monthly')], [M('Replace sensors / batteries; update models.', 'wireless_sensors')], _NL),
    failures=[F('Missed fault', ['Failure without alert'], ['Wrong sensor location, poor limits'], ['Review set-up; adjust alarms'], 'wireless_sensors'), F('Data gaps', ['Missing trends'], ['Network / battery'], ['Repeater; battery change'], 'gateway')],
    quiz=[Q('What is the P–F interval?', ['Time from detectable fault to failure', 'Pump flow', 'Pressure ratio', 'Frequency'], 0, 'P–F.'), Q('Main benefit?', ['Planned repairs before breakdowns', 'No maintenance', 'Faster speed', 'Lower flow'], 0, 'Planning.'),
          Q('Do critical turbines rely on wireless only?', ['No — wired protection (API 670) remains', 'Yes', 'Sometimes always', 'Not needed'], 0, 'Protection.')],
    selection=['Choose sensors and update rates by asset criticality and failure modes (FMEA).'], safety=['Hazardous-area certification for sensors and gateways.'], refs=['ISO 17359', 'ISO 13374'])
