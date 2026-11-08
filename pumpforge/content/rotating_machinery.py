"""Learning content — Rotating Equipment, additional machinery (EQ-141 … EQ-170)."""
from pumpforge.learning import mod, step, P, F, Q, M

MODULES = {}


def rm(size, power, speed, capacity, **extra):
    ref = {'manufacturer': None, 'model': None, 'datasheet': None,
           'rated_point': {'capacity': None, 'pressure_or_head': None, 'speed_rpm': None, 'power_kW': None, 'efficiency_pct': None},
           'status': 'empty — fill from the selected manufacturer datasheet / test certificate'}
    return dict(size=size, power_rating=power, speed=speed, capacity=capacity, reference_model=ref, extra=extra)


_MACH = dict(
    foundation=['Mount on a rigid, level foundation or grouted baseplate sized for the machine mass and dynamic loads (typically ≥3–5 × machine mass for reciprocating machines).',
                'Check for soft foot before final bolting.'],
    alignment=['Align driver and driven shafts with a laser or dial-indicator method to the coupling maker\'s tolerances; re-check hot alignment where thermal growth is significant.'],
    piping=['Support suction and discharge piping independently so no pipe strain reaches the casing; fit flexible connections where vibration or thermal movement is expected.',
            'Install inlet filters/strainers and isolation valves; add drains and vents.'],
    commissioning=['Check rotation direction with the coupling disconnected.', 'Fill lubricant to the correct level and grade.',
                   'Start unloaded where possible; record vibration, temperatures, current and pressures as a baseline.'])
_ELEC = dict(
    foundation=['Install on a level plinth or wall in a clean, dry, ventilated room within the rated ambient temperature.'],
    alignment=['Keep the specified clearances above and below for cooling air; mount vertically as the maker requires.'],
    piping=['Cabling: size cables for current and voltage drop; use screened (EMC) motor cable where required and bond the screen 360° at both ends.',
            'Segregate power and control cables; fit the correct glands to keep the IP rating.'],
    commissioning=['Check supply voltage, earthing and insulation resistance of the motor and cables before energising.',
                   'Enter motor nameplate data and protection settings; run an identification/auto-tune if available.', 'Check direction of rotation and record currents.'])
_DRIVE = dict(
    foundation=['Mount driver and driven machines on a rigid common base so centre distances and alignment stay fixed.'],
    alignment=['Align shafts parallel and the wheels/hubs in the same plane (straight-edge or laser); misalignment is the main cause of early wear.'],
    piping=['Fit guards that fully enclose moving parts but allow inspection and lubrication.'],
    commissioning=['Check rotation, set tension/slack or torque setting, run in and re-check after the first hours of operation.'])


def _maint(routine, periodic, overhaul, lub):
    return dict(routine=routine, periodic=periodic, overhaul=overhaul, lubrication=lub)


# ===================================================================== compressors & blowers
MODULES['reciprocating_compressor'] = mod(
    definition=('A reciprocating compressor raises gas pressure with a piston moving back and forth in a cylinder. Automatic suction and discharge valves let gas in and out. '
                'In a double-acting cylinder both ends compress gas alternately; the crankshaft, connecting rod and crosshead convert the motor\'s rotation into straight-line piston motion.'),
    applications=['Process gas compression in refineries and petrochemical plants', 'Hydrogen and natural-gas boosting', 'Instrument/plant air at high pressure', 'CNG filling stations', 'Refrigeration (older/large plants)'],
    key_points=['Positive displacement — flow nearly independent of pressure', 'Best for high pressure ratios and small-to-medium flows', 'Valves are the most frequent maintenance item', 'Pulsations need damping bottles'],
    principle=[step('The motor turns the crankshaft; the connecting rod drives the crosshead back and forth.', 'crankshaft'),
               step('The piston rod transmits this motion through the packing to the piston.', 'piston'),
               step('As the piston moves away from one end, pressure there falls and the suction valve opens — gas flows in.', 'valve_he_s', overlay='flow'),
               step('On the return stroke the trapped gas is compressed; when it exceeds discharge pressure the discharge valve opens.', 'valve_he_d', overlay='flow'),
               step('The other end of the cylinder works the opposite way at the same time (double-acting).', 'valve_ce_s'),
               step('Pulsation bottles smooth the intermittent flow before the piping.', 'pulsation_bottles', cut=False)],
    curve='Capacity ≈ swept volume × volumetric efficiency; volumetric efficiency falls as the pressure ratio rises (clearance-volume re-expansion).',
    params=rm(P('Bore 50–1000 mm; stroke 75–450 mm', 'mm'), P('5 – 30 000', 'kW'), P('250 – 1800 (process) ', 'rpm'), P('Up to ~ 30 000 m³/h; discharge to 1000 bar(g) and above in multistage', ''),
              pressure_ratio_per_stage=P('Typically ≤ 3–4 (temperature limited)', '')),
    install=_MACH | dict(foundation=['Use a massive concrete block foundation or skid designed for the unbalanced forces and couples; grout the frame.'],
                         piping=['Follow the pulsation/acoustic study (API 618): bottle sizes, orifice plates, pipe support spacing.', 'Fit suction strainers for start-up.']),
    maint=_maint([M('Check frame oil level and pressure, cylinder lubrication rate, cooling water.', 'crankcase', 'daily'), M('Monitor valve cover temperatures (a hot valve is leaking).', 'valve_he_d', 'daily')],
                 [M('Inspect and recondition valves.', 'valve_he_s', '4000–8000 h'), M('Check rod run-out and rider band wear (rod drop).', 'piston', '6–12 months')],
                 [M('Replace piston rings, rider bands and packing; check liner wear.', 'cylinder'), M('Inspect crankshaft, bearings and crosshead clearances.', 'crankshaft')],
                 ['Frame (crankcase) oil by splash or pressure lubrication; cylinders and packing by a separate lubricator (lubricated machines).']),
    failures=[F('Valve failure', ['High discharge temperature', 'Capacity loss', 'Knocking'], ['Broken plates/springs', 'Liquid or dirt carry-over', 'Wrong lift'], ['Replace valve; fix separator/strainer'], 'valve_he_d'),
              F('Packing leakage', ['Gas at the distance-piece vent'], ['Worn rings', 'Rod scoring'], ['Replace packing, re-finish rod'], 'distance_piece'),
              F('High vibration / pulsation', ['Pipe shaking', 'Cracked small-bore connections'], ['Acoustic resonance', 'Poor supports'], ['Add orifice plates/supports; pulsation study'], 'pulsation_bottles')],
    quiz=[Q('Why does a double-acting compressor deliver about twice the flow of a single-acting one of the same size?', ['Higher speed', 'Both ends of the cylinder compress gas', 'Bigger valves', 'It has two crankshafts'], 1, 'Each stroke compresses gas on one side.'),
          Q('What opens the suction and discharge valves?', ['A camshaft', 'The pressure difference across them', 'Solenoids', 'The crosshead'], 1, 'They are automatic, spring-loaded valves.'),
          Q('What is the purpose of the crosshead?', ['To cool the gas', 'To take the side thrust so the piston rod moves in a straight line', 'To seal the cylinder', 'To start the motor'], 1, 'Rod packing then seals a purely axial motion.'),
          Q('A discharge valve cover much hotter than the others usually means…', ['Normal operation', 'That valve is leaking (gas recompressed)', 'Too much oil', 'Low speed'], 1, 'Leaking valves heat up.')],
    selection=['Choose stages so the discharge temperature per stage stays within limits (API 618 guidance).', 'Lubricated vs non-lubricated cylinders depending on gas purity.'],
    refs=['API 618 — Reciprocating compressors'],
)

MODULES['rotary_screw_compressor'] = mod(
    definition=('A rotary screw compressor compresses gas between two meshing helical rotors. Gas fills the lobe spaces at the inlet, is sealed off and carried along the rotors '
                'while the pocket shrinks, then leaves through the discharge port. Oil-injected machines use oil to seal, cool and lubricate; it is separated afterwards.'),
    applications=['Plant and instrument air (most common industrial compressor)', 'Refrigeration and heat pumps', 'Gas boosting (fuel gas, flare gas recovery)', 'Mobile construction compressors'],
    key_points=['Continuous, almost pulsation-free flow', 'Few wear parts — long service intervals', 'Built-in volume ratio set by the ports', 'Oil separator and oil quality are critical'],
    principle=[step('Air enters through the filter and inlet valve into the lobes at the inlet end.', 'inlet_valve_filter', overlay='flow'),
               step('The male rotor (driven by the motor) turns the female rotor; a pocket of air is sealed between the lobes and the casing.', 'male_rotor'),
               step('As the rotors turn, the pocket moves toward the discharge end and its volume shrinks — pressure rises.', 'female_rotor', overlay='pressure'),
               step('Oil injected into the pockets seals the clearances and absorbs the heat of compression.', 'piping'),
               step('The air–oil mixture leaves through the discharge port to the separator vessel; clean air goes to service and oil returns.', 'oil_separator', overlay='flow')],
    curve='Flow almost constant with pressure; specific power (kW per m³/min) is the key efficiency measure (ISO 1217 Annex C/E).',
    params=rm(P('Rotor diameter ~ 50 – 500 mm'), P('4 – 500 (oil-injected air)', 'kW'), P('1500 – 6000 (rotor tip speed governed)', 'rpm'), P('0.5 – 100 m³/min free air delivery', ''),
              discharge_pressure=P('7 – 13 bar(g) typical (single stage)', 'bar')),
    install=_MACH | dict(piping=['Use an air receiver, dryer and filters per the required ISO 8573-1 class; slope pipework to drains.', 'Provide enough ventilation to remove the compressor heat (or recover it).']),
    maint=_maint([M('Check oil level, discharge temperature and separator ΔP.', 'oil_separator', 'daily')],
                 [M('Change oil, oil filter, air filter and separator element per running hours.', 'oil_separator', '2000–8000 h'), M('Check inlet valve function.', 'inlet_valve_filter', 'annual')],
                 [M('Replace rotor bearings and shaft seal (airend overhaul).', 'bearings', '~ 40 000 h')],
                 ['Compressor oil (mineral or synthetic) as specified; oil also lubricates the bearings.']),
    failures=[F('High discharge temperature', ['Trips on temperature'], ['Low oil, blocked oil cooler, high ambient'], ['Top up oil, clean cooler, improve ventilation'], 'piping'),
              F('Oil carry-over', ['Oil in the air system'], ['Separator element failed, high oil level, scavenge line blocked'], ['Replace element, correct level'], 'oil_separator'),
              F('Bearing wear', ['Rising vibration and noise'], ['Age, oil contamination'], ['Airend overhaul'], 'bearings')],
    quiz=[Q('In an oil-injected screw compressor the oil does NOT…', ['Seal the clearances', 'Cool the air', 'Lubricate bearings', 'Drive the female rotor through gears'], 3, 'In oil-injected units the male drives the female through the oil film — no timing gears.'),
          Q('Why does the pressure rise along the rotors?', ['The rotors heat the air', 'The trapped pocket gets smaller', 'The motor speeds up', 'Oil pushes the air'], 1, 'Positive displacement.'),
          Q('What sets the "built-in" pressure ratio?', ['Motor size', 'The size and position of the discharge port', 'The air filter', 'Oil grade'], 1, 'Built-in volume ratio.'),
          Q('The male rotor has 4 lobes and the female 6. If the male turns at 3000 rpm, the female turns at…', ['4500 rpm', '3000 rpm', '2000 rpm', '1500 rpm'], 2, '3000 × 4/6.')],
)

MODULES['rotary_vane_compressor'] = mod(
    definition=('A rotary vane compressor has an off-centre slotted rotor inside a cylinder. Vanes slide out against the cylinder wall and trap air in cells that grow on the inlet '
                'side and shrink on the outlet side, compressing the air. Oil injected into the cells seals and cools.'),
    applications=['Workshop and small industrial air', 'Vehicle-mounted compressors', 'Vacuum/pressure duty in packaging and printing', 'Gas boosting at low ratio'],
    key_points=['Simple, low speed, few parts', 'Vane wear is self-compensating', 'Oil-flooded designs reach ~ 7–10 bar in one stage', 'Efficiency competitive at small sizes'],
    principle=[step('The rotor turns off-centre in the stator; vanes slide out by centrifugal force to touch the wall.', 'rotor'),
               step('On the inlet side, cells between vanes grow and draw air in.', 'stator', overlay='flow'),
               step('Further round, the cells shrink and the air is compressed.', 'vane_1'),
               step('Compressed air leaves through the discharge port to the oil separator.', 'oil_separator', overlay='flow')],
    curve='Near-constant flow vs pressure; capacity proportional to speed.',
    params=rm(P('Rotor diameter ~ 100 – 400 mm'), P('2 – 250', 'kW'), P('1000 – 3000', 'rpm'), P('0.2 – 40 m³/min', ''), discharge_pressure=P('up to ~ 10 bar(g) (oil-flooded)', 'bar')),
    install=_MACH,
    maint=_maint([M('Check oil level and discharge temperature.', 'oil_separator', 'daily')], [M('Change oil, filters and separator element.', 'oil_separator', '2000–4000 h')],
                 [M('Check vane height and stator bore; replace vanes.', 'vane_1')], ['Compressor oil injected into the cells; same oil lubricates bearings.']),
    failures=[F('Capacity loss', ['Lower pressure/flow'], ['Worn vanes, stuck vanes (varnish)'], ['Clean/replace vanes'], 'vane_1'),
              F('Overheating', ['High-temperature trip'], ['Low oil, dirty cooler'], ['Restore oil, clean cooler'], 'oil_separator')],
    quiz=[Q('What makes the vanes touch the stator wall?', ['Magnets', 'Centrifugal force (and sometimes springs/oil pressure)', 'Gravity', 'Gears'], 1, 'They slide out in the slots.'),
          Q('Why must the rotor be off-centre?', ['For balance', 'So the cell volume changes as it turns', 'To reduce noise', 'It is not'], 1, 'Eccentricity makes cells grow and shrink.'),
          Q('Vane wear is "self-compensating" because…', ['Vanes grow back', 'Vanes simply slide out further', 'The stator shrinks', 'Oil fills the gap'], 1, 'They move out to keep contact.')],
)

MODULES['roots_blower'] = mod(
    definition=('A Roots blower uses two lobed rotors turning in opposite directions, kept in step by timing gears and never touching. Each rotor carries pockets of air from the '
                'inlet to the outlet around the casing. There is no internal compression: pressure rises when the pocket opens to the discharge and higher-pressure gas flows back into it.'),
    applications=['Aeration of wastewater (biological treatment)', 'Pneumatic conveying of powders', 'Fluidising air, combustion air', 'Vacuum duty (mechanical boosters)'],
    key_points=['Positive displacement, low pressure (≤ ~1 bar)', 'Oil-free air (gears sealed off)', 'Noisy — silencers essential', 'Never throttle the outlet — use a relief valve'],
    principle=[step('Air enters the inlet at the top.', 'casing', overlay='flow'),
               step('Each rotor traps a pocket of air against the casing wall.', 'rotor_1'),
               step('The pockets are carried round to the outlet; the rotors mesh in the middle without touching.', 'rotor_2'),
               step('Timing gears keep the rotors in exact phase.', 'timing_gear_1', cut=False),
               step('Silencers reduce the pulsation noise.', 'silencers', cut=False)],
    curve='Flow ≈ displacement × speed minus slip; slip rises with pressure difference. Power rises linearly with pressure.',
    params=rm(P('DN 50 – 400 connections'), P('1 – 400', 'kW'), P('1000 – 6000', 'rpm'), P('1 – 300 m³/min', ''), pressure=P('up to ~ 1 bar(g) (single stage); vacuum ~ 0.5 bar(a)', 'bar')),
    install=_MACH | dict(piping=['Fit a pressure relief valve and a non-return valve on the discharge; never close the outlet against a running blower.']),
    maint=_maint([M('Check gearbox oil level and belt tension.', 'gearbox', 'weekly')], [M('Change gear oil; clean inlet filter.', 'gearbox', '~ 4000 h')],
                 [M('Replace bearings and seals; check rotor clearances.', 'rotor_1')], ['Splash-lubricated timing gears and bearings in oil sumps at both ends.']),
    failures=[F('Rotor contact', ['Knocking, seizure'], ['Bearing failure, overheating (over-pressure), gear wear'], ['Replace bearings; check relief valve'], 'rotor_1'),
              F('Overheating', ['High discharge temperature'], ['Excess pressure, blocked filter'], ['Reduce pressure; clean filter'], 'casing')],
    quiz=[Q('Why do Roots blower rotors never touch?', ['Magnetic bearings', 'Timing gears keep them in phase with small clearances', 'They are rubber', 'They do touch'], 1, 'Oil-free compression.'),
          Q('Is there internal compression in a Roots blower?', ['Yes, like a screw', 'No — pressure rises when the pocket opens to discharge', 'Only at high speed', 'Only with oil'], 1, 'Isochoric back-flow compression.'),
          Q('What must be installed on the discharge?', ['A throttle valve to control flow', 'A pressure relief valve', 'A flow meter only', 'Nothing'], 1, 'Positive displacement — closing the outlet causes overpressure.')],
)

MODULES['side_channel_blower'] = mod(
    definition=('A side channel blower has an impeller with many blades next to a ring-shaped side channel. Air is thrown outward by the blades into the channel and returns to the blade '
                'roots, repeating many times as it travels round. This regenerative, helical flow builds higher pressure than a single fan stage, oil-free.'),
    applications=['Aquaculture and pond aeration', 'Pneumatic conveying (light)', 'Vacuum lifting and hold-down', 'Air knives, drying, gas recirculation'],
    key_points=['Oil-free, low maintenance', 'Higher pressure than fans, lower flow', 'Interrupter separates outlet from inlet', 'Pressure relief valve recommended'],
    principle=[step('Air enters through the inlet port into the side channel.', 'silencers', overlay='flow'),
               step('The impeller blades fling air outward into the channel.', 'impeller'),
               step('The air circulates back to the blade roots and is picked up again — a helical path.', 'housing', overlay='flow'),
               step('After almost one revolution the pressurised air leaves at the outlet; the interrupter blocks the return to the inlet.', 'housing')],
    curve='Pressure falls steeply with flow; power rises as flow falls (opposite to centrifugal fans) — avoid closed outlets.',
    params=rm(P('Impeller ~ 200 – 600 mm'), P('0.2 – 25', 'kW'), P('2900 / 3500 (direct drive)', 'rpm'), P('up to ~ 2000 m³/h', ''), pressure=P('up to ~ 500 mbar (single stage)', 'mbar')),
    install=_MACH,
    maint=_maint([M('Check filter and noise.', 'silencers', 'monthly')], [M('Clean inlet filter / silencer.', 'silencers', '3 months')], [M('Replace motor bearings.', 'm_motor_bearings')],
                 ['Sealed-for-life motor bearings (re-greasable on large units).']),
    failures=[F('Overheating', ['Thermal trip'], ['Operation at too high pressure, blocked filter'], ['Fit relief valve, clean filter'], 'housing'),
              F('Noise/vibration', ['Rough running'], ['Debris, bearing failure'], ['Clean, replace bearings'], 'impeller')],
    quiz=[Q('How does a side channel blower build pressure?', ['Single pass through the impeller', 'Repeated circulation between blades and side channel', 'Pistons', 'Screws'], 1, 'Regenerative principle.'),
          Q('What happens to power if the outlet is throttled?', ['It falls', 'It rises', 'No change', 'It stops'], 1, 'Unlike centrifugal fans.'),
          Q('What stops air going straight from outlet back to inlet?', ['A check valve', 'The interrupter (stripper) zone', 'The motor', 'The silencer'], 1, 'Solid section of channel.')],
)

# ===================================================================== fans
_FAN_INSTALL = _MACH | dict(piping=['Provide good inlet conditions: straight duct or bellmouth; avoid elbows close to the inlet (system effect).', 'Fit flexible connections at inlet and outlet.'])

MODULES['axial_flow_fan'] = mod(
    definition=('An axial flow fan moves air along its axis with rotating aerofoil blades. Each blade acts like a wing; the blade pitch sets the flow and pressure. Guide vanes after '
                'the rotor remove swirl and recover pressure.'),
    applications=['Tunnel and mine ventilation', 'Cooling towers and air-cooled condensers', 'HVAC supply/exhaust', 'Boiler draft (variable-pitch axial fans)'],
    key_points=['High flow, low-to-medium pressure', 'Stall region on the curve — avoid', 'Pitch angle sets duty', 'Guide vanes improve efficiency'],
    principle=[step('Air enters smoothly through the inlet bell.', 'inlet_bell', overlay='flow'),
               step('The rotating blades push air axially and add swirl.', 'impeller'),
               step('Outlet guide vanes straighten the flow and convert swirl to pressure.', 'guide_vanes', overlay='flow'),
               step('The motor sits in the air stream and is cooled by it.', 'motor')],
    curve='Steep pressure curve with a stall dip at low flow; power is roughly flat or falls with flow.',
    params=rm(P('Ø 0.3 – 5 m'), P('0.5 – 1000+', 'kW'), P('500 – 3000', 'rpm'), P('1 – 1000 m³/s', ''), pressure=P('100 – 3000', 'Pa')),
    install=_FAN_INSTALL,
    maint=_maint([M('Check vibration and noise.', 'impeller', 'weekly')], [M('Check blade pitch and tightness; clean blades.', 'impeller', '6 months')],
                 [M('Replace motor bearings; inspect blade roots.', 'motor')], ['Motor bearings greased per motor maker.']),
    failures=[F('Stall / surge', ['Noise, pulsating flow'], ['Operating at too high resistance'], ['Reduce pitch, reduce system resistance'], 'impeller'),
              F('Vibration', ['High vibration'], ['Unequal blade pitch, fouling'], ['Set pitch equally, clean, balance'], 'impeller')],
    quiz=[Q('What sets the duty of an adjustable-pitch axial fan?', ['Blade pitch angle', 'Casing colour', 'Inlet bell size only', 'Number of guide vanes'], 0, 'Pitch changes flow and pressure.'),
          Q('Why are outlet guide vanes fitted?', ['To heat the air', 'To remove swirl and recover pressure', 'To support the casing only', 'For noise only'], 1, 'Straighteners.'),
          Q('Operating in the stall region causes…', ['Higher efficiency', 'Unstable, noisy flow and blade stress', 'Lower noise', 'Nothing'], 1, 'Avoid stall.')],
)

_CF_PRINC = [step('Air is drawn through the inlet cone into the eye of the impeller.', 'inlet_cone', overlay='flow'),
             step('The spinning blades throw the air outward, adding velocity and pressure.', 'impeller'),
             step('The scroll housing collects the air; its widening passage slows it and turns velocity into pressure.', 'housing', overlay='flow'),
             step('Bearings and the coupled motor drive the shaft.', 'bearings', cut=False)]


def _fan_maint(extra_routine=None):
    return _maint([M('Check bearing temperature and vibration.', 'bearings', 'daily')] + (extra_routine or []),
                  [M('Clean impeller and housing; check inlet cone gap.', 'impeller', '6–12 months'), M('Check coupling alignment.', 'coupling', 'annual')],
                  [M('Inspect impeller for erosion/cracks; re-balance.', 'impeller'), M('Replace bearings.', 'bearings')],
                  ['Grease or oil bath for the plummer-block bearings; motor bearings per maker.'])


_CF_FAIL = [F('Vibration from imbalance', ['Rising 1× running-speed vibration'], ['Dust build-up or erosion on blades'], ['Clean / repair and balance'], 'impeller'),
            F('Bearing overheating', ['High bearing temperature'], ['Lack/excess of grease, misalignment'], ['Correct lubrication; align'], 'bearings')]

MODULES['centrifugal_fan'] = mod(
    definition=('A centrifugal fan draws air into the centre of a rotating impeller and throws it outward into a scroll-shaped housing, which converts the velocity into pressure. '
                'Backward-curved blades give high efficiency and a power curve that does not overload.'),
    applications=['HVAC air handling', 'Dust collection and process exhaust', 'Combustion air', 'Drying and cooling'],
    key_points=['Higher pressure than axial fans', 'Backward-curved: efficient, non-overloading', 'Fan laws: Q ∝ N, p ∝ N², P ∝ N³', 'Inlet conditions strongly affect performance'],
    principle=_CF_PRINC,
    curve='Pressure falls gently with flow; power peaks then falls (non-overloading) for backward-curved blades. Affinity (fan) laws apply.',
    params=rm(P('Impeller Ø 0.2 – 3 m'), P('0.5 – 500', 'kW'), P('500 – 3600', 'rpm'), P('0.1 – 100 m³/s', ''), pressure=P('250 – 15 000', 'Pa')),
    install=_FAN_INSTALL, maint=_fan_maint(), failures=_CF_FAIL,
    quiz=[Q('If fan speed is reduced by 20 %, the power falls to about…', ['80 %', '64 %', '51 %', '40 %'], 2, '0.8³ ≈ 0.51.'),
          Q('What does the scroll housing do?', ['Spins the air', 'Collects the air and converts velocity to pressure', 'Filters the air', 'Cools the motor'], 1, 'Diffusion.'),
          Q('Backward-curved blades are preferred because…', ['They are cheapest', 'High efficiency and non-overloading power', 'Highest pressure always', 'They handle sticky dust best'], 1, 'Radial blades suit dusty duty.')],
)
MODULES['induced_draft_fan'] = mod(
    definition=('An induced draft (ID) fan pulls flue gas out of a boiler or furnace through the air heater and dust collector and pushes it up the stack. It keeps the furnace slightly '
                'below atmospheric pressure (balanced draft with an FD fan). It handles hot, dusty gas, so it is robust and wear-protected.'),
    applications=['Utility and industrial boilers', 'Kilns and furnaces', 'Process gas exhaust after scrubbers / bag filters', 'Incinerators'],
    key_points=['Handles hot, dusty, corrosive gas', 'Controls furnace draft (pressure)', 'Erosion and build-up cause imbalance', 'Inlet dampers or VFD for control'],
    principle=[step('Flue gas comes down the duct into the inlet box.', 'inlet_box', overlay='flow', cut=False), step('The louvre damper modulates to control furnace draft.', 'inlet_damper', cut=False)] + _CF_PRINC[1:],
    curve='As centrifugal fans; system resistance rises with boiler load and dust collector ΔP. Gas density (temperature) changes pressure: p ∝ ρ.',
    params=rm(P('Impeller Ø 1.5 – 5 m (utility)'), P('100 – 10 000', 'kW'), P('500 – 1500', 'rpm'), P('20 – 1000 m³/s', ''), gas_temperature=P('~ 120 – 200 (after air heater)', '°C')),
    install=_FAN_INSTALL | dict(piping=['Fit expansion joints at inlet and outlet ducts for thermal movement; insulate hot ducts.']),
    maint=_fan_maint([M('Check damper actuator response.', 'inlet_damper', 'weekly')]), failures=_CF_FAIL + [F('Erosion of blades', ['Falling performance, vibration'], ['Fly ash'], ['Hard-facing, liners, improve dust collection'], 'impeller')],
    quiz=[Q('An ID fan keeps the furnace at…', ['High positive pressure', 'Slightly below atmospheric pressure', 'Exactly zero flow', 'Vacuum of 1 bar'], 1, 'Balanced draft.'),
          Q('Hot gas has lower density; for the same speed the fan pressure…', ['Increases', 'Decreases', 'Is unchanged', 'Doubles'], 1, 'p ∝ ρ.'),
          Q('A common cause of ID fan vibration is…', ['Clean air', 'Ash build-up or erosion on the impeller', 'Low speed', 'Paint colour'], 1, 'Imbalance.')],
)
MODULES['forced_draft_fan'] = mod(
    definition=('A forced draft (FD) fan pushes combustion air into a boiler through the air heater and windbox to the burners. It handles clean ambient air; inlet guide vanes (or blade '
                'pitch / speed) control the airflow to match the fuel.'),
    applications=['Boilers (combustion air)', 'Furnaces and kilns', 'Fluidised bed boilers (with PA fans)', 'Large burner systems'],
    key_points=['Clean air → high efficiency', 'Airflow follows fuel (combustion control)', 'Inlet silencer reduces noise', 'IGVs save energy compared with dampers'],
    principle=[step('Air enters through the inlet silencer.', 'inlet_silencer', overlay='flow', cut=False), step('Inlet guide vanes pre-swirl the air to reduce flow and power at part load.', 'inlet_guide_vanes', cut=False)] + _CF_PRINC[1:],
    curve='Fan curves for each IGV angle; system curve from air heater, windbox and burner resistance.',
    params=rm(P('Impeller Ø 1 – 4 m'), P('50 – 5000', 'kW'), P('750 – 1500', 'rpm'), P('10 – 500 m³/s', ''), pressure=P('2 – 10', 'kPa')),
    install=_FAN_INSTALL, maint=_fan_maint([M('Stroke-test IGV actuator.', 'inlet_guide_vanes', 'monthly')]), failures=_CF_FAIL + [F('IGV linkage seizure', ['Airflow not controllable'], ['Corrosion, lack of lubrication'], ['Free and lubricate linkage'], 'igv_ring')],
    quiz=[Q('An FD fan supplies…', ['Flue gas to the stack', 'Combustion air to the boiler', 'Coal to the mills', 'Water to the drum'], 1, 'Forced draft.'),
          Q('Inlet guide vanes reduce flow by…', ['Blocking the outlet', 'Pre-swirling the air in the direction of rotation', 'Slowing the motor', 'Heating the air'], 1, 'Pre-rotation lowers the work done.'),
          Q('Why are FD fans more efficient than ID fans?', ['Smaller', 'They handle clean, cold air', 'Faster', 'They have no bearings'], 1, 'No erosion/build-up allowance needed.')],
)
MODULES['primary_air_fan'] = mod(
    definition=('A primary air (PA) fan supplies high-pressure air to coal pulverisers (mills): it dries the coal and carries the pulverised fuel to the burners. It needs much higher '
                'pressure than an FD fan at lower flow, hence a narrow high-speed impeller, with inlet vanes for control and an outlet damper for isolation.'),
    applications=['Pulverised-coal fired boilers', 'Biomass and coal mill systems', 'Fluidised bed boilers (fluidising air)', 'High-pressure process air'],
    key_points=['High pressure, moderate flow', 'Mill air flow and temperature control fuel transport', 'Outlet damper isolates a fan in parallel operation', 'Watch for parallel-fan instability'],
    principle=_CF_PRINC[:2] + [step('Inlet guide vanes control the airflow.', 'inlet_guide_vanes', cut=False), step('The scroll builds the high pressure needed by the mills.', 'housing', overlay='flow'),
                               step('The outlet damper isolates or throttles the fan.', 'outlet_damper', cut=False)],
    curve='Steep pressure curve; parallel operation requires matching curves to avoid hunting.',
    params=rm(P('Impeller Ø 1 – 3 m'), P('200 – 5000', 'kW'), P('1000 – 1500', 'rpm'), P('5 – 200 m³/s', ''), pressure=P('8 – 20', 'kPa')),
    install=_FAN_INSTALL, maint=_fan_maint([M('Check damper seals and actuator.', 'outlet_damper', 'monthly')]), failures=_CF_FAIL,
    quiz=[Q('PA fans supply air to…', ['The stack', 'The coal mills to dry and carry coal', 'The condenser', 'The turbine'], 1, 'Primary air.'),
          Q('Compared with FD fans, PA fans have…', ['Lower pressure, higher flow', 'Higher pressure, lower flow', 'No impeller', 'Same duty'], 1, 'Narrow impeller.'),
          Q('Why have an outlet damper?', ['To isolate the fan when it is stopped or in parallel operation', 'To heat the air', 'For noise', 'No reason'], 0, 'Isolation and control.')],
)

# ===================================================================== turbines
MODULES['steam_turbine'] = mod(
    definition=('A steam turbine converts the thermal energy of steam into rotation. Stationary nozzles accelerate the steam, and moving blades on the rotor turn its velocity into torque, '
                'stage after stage, while the steam expands to the exhaust (condenser) pressure. A governor valve controls the steam flow to hold speed or load.'),
    applications=['Power generation (thermal, nuclear, solar thermal, biomass)', 'Driving compressors and pumps (mechanical drive)', 'Cogeneration (back-pressure/extraction)', 'Marine propulsion'],
    key_points=['Many stages; blades grow longer toward the exhaust', 'Impulse vs reaction stages', 'Condensing vs back-pressure', 'Overspeed protection is critical'],
    principle=[step('High-pressure steam enters through the steam chest and governor (control) valve.', 'control_valve', overlay='flow'),
               step('Fixed nozzles in each diaphragm accelerate the steam.', 'diaphragms'),
               step('The steam jet pushes the moving blades and turns the rotor.', 'rotor', overlay='pressure'),
               step('Stage by stage the pressure falls and the volume grows — blades get longer.', 'rotor', overlay='pressure'),
               step('Exhaust steam goes down to the condenser; the rotor drives the generator through the coupling.', 'generator', cut=False)],
    curve='Willans line: steam flow vs power is nearly linear; efficiency depends on stage design and exhaust vacuum.',
    params=rm(P('Small drives ~ 0.1 MW up to ~ 1500 MW sets'), P('0.1 – 1 500 000', 'kW'), P('3000/3600 (power gen); up to ~ 15 000 (drives)', 'rpm'), P('Steam flow ~ 1 – 4000 t/h', ''),
              inlet_conditions=P('Up to ~ 300 bar, 600 °C (supercritical)', '')),
    install=_MACH | dict(foundation=['Table-top concrete or steel foundation with dynamic analysis; turbine–generator alignment includes catenary.'],
                         piping=['Steam lines drained and warmed before admission; limit piping forces on casing nozzles (NEMA SM 23 / API 612).']),
    maint=_maint([M('Monitor vibration, bearing temperatures, expansion, eccentricity.', 'bearings', 'continuous')],
                 [M('Overspeed trip test; valve stem free-movement test.', 'governor_actuator', 'per procedure'), M('Lube-oil analysis.', 'bearings', 'monthly')],
                 [M('Open casing: inspect blades, diaphragms, seals; clean deposits.', 'rotor', '4–8 years')], ['Forced lube-oil system for journal and thrust bearings; control oil for governor.']),
    failures=[F('Blade erosion / fouling', ['Efficiency loss', 'Stage pressure changes'], ['Wet steam, carry-over of silica/salts'], ['Improve steam purity; repair blades'], 'rotor'),
              F('High vibration', ['Trip on vibration'], ['Rub, imbalance, misalignment, bowed rotor'], ['Slow roll, balance, align'], 'bearings'),
              F('Sticking control valve', ['Poor speed control'], ['Deposits on stem'], ['Exercise / clean valve'], 'control_valve')],
    quiz=[Q('Why do turbine blades get longer toward the exhaust?', ['To reduce weight', 'Steam volume increases as pressure falls', 'For balance only', 'They do not'], 1, 'Specific volume grows.'),
          Q('In an impulse stage the pressure drop happens mainly in…', ['The moving blades', 'The fixed nozzles', 'The bearings', 'The condenser'], 1, 'Reaction stages share the drop.'),
          Q('What protects the turbine against runaway speed?', ['The coupling', 'An independent overspeed trip', 'The condenser', 'Gland seals'], 1, 'Overspeed trip closes the stop valves.'),
          Q('Gland seals in a turbine…', ['Lubricate the bearings', 'Limit steam leakage/air in-leakage along the shaft', 'Cool the blades', 'Control speed'], 1, 'Labyrinth glands.')],
)
MODULES['gas_turbine'] = mod(
    definition=('A gas turbine compresses air, burns fuel in it and expands the hot gas through a turbine (Brayton cycle). Part of the turbine power drives the compressor; the rest '
                'drives a generator or compressor. The hot exhaust can raise steam in a heat-recovery boiler (combined cycle).'),
    applications=['Power generation (simple and combined cycle)', 'Mechanical drive for pipeline compressors', 'Offshore platforms', 'Aircraft and marine propulsion (aero-derivatives)'],
    key_points=['Compressor uses roughly half of turbine work', 'Efficiency rises with pressure ratio and firing temperature', 'Inlet air temperature strongly affects output', 'Hot-gas-path parts limit life'],
    principle=[step('Air enters through the inlet bellmouth.', 'inlet', overlay='flow'),
               step('The axial compressor raises the air pressure stage by stage.', 'rotor', overlay='pressure'),
               step('Fuel burns in the combustors at nearly constant pressure.', 'combustors', overlay='flow'),
               step('Hot gas expands through the turbine stages, turning the rotor.', 'stator_vanes', overlay='pressure'),
               step('Exhaust leaves through the diffuser near atmospheric pressure.', 'exhaust', overlay='flow')],
    curve='Output and heat rate vs compressor inlet temperature: output falls roughly 0.5–0.9 % per °C rise (typical, design-specific).',
    params=rm(P('Industrial frames ~ 1 – 500+ MW'), P('1000 – 500 000', 'kW'), P('3000/3600 (single shaft); higher for small units', 'rpm'), P('Exhaust flow ~ 5 – 900 kg/s', ''),
              pressure_ratio=P('~ 10 – 25 (industrial); higher for aero-derivatives', '')),
    install=_MACH | dict(piping=['Inlet filtration house, exhaust stack/HRSG, fuel gas conditioning; fire protection in the enclosure.']),
    maint=_maint([M('Monitor exhaust temperature spread, vibration, compressor ΔP.', 'exhaust', 'continuous')],
                 [M('Online/offline compressor wash.', 'rotor', 'as fouling dictates'), M('Combustion inspection.', 'combustors', '8000–12 000 h (typical)')],
                 [M('Hot-gas-path inspection; major overhaul.', 'stator_vanes', '24 000–48 000 h (typical)')], ['Forced lube-oil system for bearings; accessory gearbox.']),
    failures=[F('Compressor fouling', ['Lower output, higher heat rate'], ['Dirty inlet air'], ['Wash; improve filtration'], 'rotor'),
              F('Combustion problems', ['Exhaust temperature spread, flame-out'], ['Nozzle fouling, liner cracks'], ['Combustion inspection'], 'combustors'),
              F('Hot-gas-path damage', ['Borescope findings'], ['Over-firing, coating loss'], ['Repair/replace blades & vanes'], 'stator_vanes')],
    quiz=[Q('Which thermodynamic cycle does a gas turbine follow?', ['Rankine', 'Brayton', 'Otto', 'Diesel'], 1, 'Compression–heat addition–expansion.'),
          Q('About how much of the turbine work drives the compressor?', ['5 %', '50–60 %', '100 %', 'None'], 1, 'Back-work ratio is high.'),
          Q('On a hot day, gas turbine output…', ['Rises', 'Falls', 'Is unchanged', 'Doubles'], 1, 'Lower air density.'),
          Q('Combined cycle uses the exhaust to…', ['Heat the inlet air', 'Raise steam for a steam turbine', 'Cool the blades', 'Drive the starter'], 1, 'HRSG + steam turbine.')],
)
MODULES['hydraulic_turbine'] = mod(
    definition=('A Francis turbine is a reaction water turbine. Water from the penstock fills the spiral casing, passes the stay vanes and adjustable wicket gates and flows inward through '
                'the runner, turning it, then leaves down the draft tube. The gates control flow; the vertical shaft drives a generator.'),
    applications=['Hydropower plants (medium heads ~ 40–600 m)', 'Pumped storage (reversible pump-turbines)', 'Small hydro'],
    key_points=['Reaction turbine — full of water, pressure drops across the runner', 'Wicket gates control flow and power', 'Draft tube recovers energy', 'Cavitation if set too high'],
    principle=[step('Water enters the spiral casing from the penstock.', 'spiral_casing', overlay='flow'),
               step('Stay vanes and wicket gates guide the water and set the flow.', 'wicket_gates'),
               step('Water flows inward through the runner blades, turning the runner.', 'runner', overlay='flow'),
               step('The water leaves downward through the draft tube, which recovers kinetic energy.', 'draft_tube'),
               step('The shaft turns the generator above.', 'generator_stator', cut=False)],
    curve='Efficiency hill chart vs flow and head; peak ~ 90–95 % near design point; part-load draft-tube vortex.',
    params=rm(P('Runner Ø 0.3 – 10 m'), P('0.1 – 800 000', 'kW'), P('~ 75 – 1000 (synchronous speeds)', 'rpm'), P('Flow 0.1 – 1000 m³/s', ''), head=P('~ 40 – 600', 'm')),
    install=_MACH | dict(foundation=['Embedded in reinforced concrete; spiral casing and draft tube liner concreted in place.'],
                         alignment=['Shaft line plumb and centred to tight limits; guide bearing clearances set.']),
    maint=_maint([M('Monitor vibration, bearing temperatures, gate position and head-cover pressure.', 'head_cover', 'continuous')],
                 [M('Check wicket gate shear pins and bushings.', 'wicket_gates', 'annual')],
                 [M('Repair cavitation damage on runner; inspect draft tube.', 'runner', 'major outage')], ['Oil-lubricated guide and thrust bearings; greased gate bushings (or self-lubricated).']),
    failures=[F('Cavitation erosion', ['Pitting on blades, noise'], ['Low tailwater/setting, off-design operation'], ['Weld repair with stainless; operate in good zone'], 'runner'),
              F('Draft-tube pressure pulsation', ['Vibration at part load'], ['Vortex rope'], ['Air admission, avoid rough zone'], 'draft_tube')],
    quiz=[Q('What do the wicket gates do?', ['Seal the shaft', 'Control the flow and inflow angle', 'Cool the generator', 'Store water'], 1, 'They are the turbine "throttle".'),
          Q('Francis turbines are best for…', ['Very high heads > 1000 m', 'Medium heads', 'Very low heads < 5 m', 'Wind'], 1, 'Pelton for high, Kaplan for low.'),
          Q('Why is there a draft tube?', ['To recover kinetic energy of the outflow', 'To add water', 'To lift the runner', 'Decoration'], 0, 'Lowers runner outlet pressure.')],
)
MODULES['expander_turbine'] = mod(
    definition=('A turboexpander is a radial-inflow turbine through which high-pressure gas expands. Because the gas does work on the wheel, its temperature drops far more than across a valve '
                '(near-isentropic expansion). The power is recovered in a compressor wheel on the same shaft or a generator.'),
    applications=['Natural-gas processing (NGL recovery, dew-point control)', 'Air separation (cryogenic)', 'LNG and hydrogen liquefaction', 'Pressure letdown energy recovery'],
    key_points=['Large temperature drop → refrigeration', 'Variable nozzles control flow', 'Very high speed', 'Seal gas keeps oil out of the process'],
    principle=[step('High-pressure gas enters the inlet scroll.', 'expander_casing', overlay='flow'),
               step('Variable nozzles accelerate it onto the wheel and control the flow.', 'nozzles'),
               step('The gas expands through the expander wheel, cooling strongly and driving the shaft.', 'rotor', overlay='pressure'),
               step('The same shaft drives the compressor wheel, which recompresses gas.', 'compressor_casing', overlay='flow'),
               step('Tilting-pad bearings and seals in the centre housing support the high-speed rotor.', 'bearing_housing')],
    curve='Isentropic efficiency ~ 80–90 % at design; nozzle opening varies flow.',
    params=rm(P('Wheel Ø ~ 50 – 600 mm'), P('50 – 20 000', 'kW'), P('10 000 – 100 000+ (size dependent)', 'rpm'), P('Gas flow ~ 1 – 400 MMSCFD', ''), temperature_drop=P('Tens of °C or more (process dependent)', '°C')),
    install=_MACH | dict(piping=['Fit inlet strainers (fine screens) to protect the wheel; liquids/solids must be removed upstream.']),
    maint=_maint([M('Monitor speed, vibration, bearing temperatures and seal-gas ΔP.', 'bearing_housing', 'continuous')],
                 [M('Clean inlet screen; check nozzle actuator.', 'nozzles', 'quarterly')], [M('Replace bearings and seals; inspect wheels.', 'rotor')],
                 ['Pressurised lube-oil system (or active magnetic bearings with no oil).']),
    failures=[F('Wheel erosion', ['Efficiency loss, vibration'], ['Liquid droplets or solids'], ['Improve separation upstream; replace wheel'], 'rotor'),
              F('Oil contamination of process', ['Oil in cold box'], ['Seal-gas failure'], ['Restore seal gas, replace seals'], 'bearing_housing')],
    quiz=[Q('Why does gas cool more in an expander than across a valve?', ['The expander adds heat', 'The gas does work on the wheel (near-isentropic)', 'Valves heat gas', 'It does not'], 1, 'Work extraction.'),
          Q('What usually absorbs the expander power?', ['A brake compressor or generator on the same shaft', 'The bearings', 'The nozzles', 'Nothing'], 0, 'Expander-compressor.'),
          Q('Variable nozzles are used to…', ['Seal the shaft', 'Control flow through the expander', 'Lubricate', 'Measure speed'], 1, 'Capacity control.')],
)

# ===================================================================== vacuum
MODULES['rotary_vacuum_pump'] = mod(
    definition=('An oil-sealed rotary vane vacuum pump traps gas between vanes in an eccentric chamber, compresses it to just above atmospheric pressure and expels it through an exhaust '
                'valve under oil. The oil seals clearances so it reaches rough-to-medium vacuum.'),
    applications=['Laboratory and vacuum furnaces', 'Packaging and vacuum forming', 'Refrigeration evacuation', 'Backing pump for high-vacuum pumps'],
    key_points=['Ultimate pressure ~ 10⁻¹–10⁻³ mbar (single/two-stage)', 'Gas ballast prevents vapour condensing in the oil', 'Oil condition determines performance', 'Exhaust filter removes oil mist'],
    principle=[step('Gas from the vessel enters through the inlet as the cell grows.', 'stator', overlay='flow'),
               step('The vanes sweep the gas round and compress it.', 'vane_1'),
               step('When above atmospheric pressure the exhaust valve opens under the oil.', 'exhaust_valve', overlay='flow'),
               step('Gas passes the oil box and demister to atmosphere; the oil is retained.', 'oil_casing')],
    curve='Pumping speed nearly constant from atmosphere down to ~1 mbar, then falls toward the ultimate pressure.',
    params=rm(P('Inlet DN 16 – 100'), P('0.2 – 15', 'kW'), P('1500 / 3000', 'rpm'), P('1 – 1600 m³/h pumping speed', ''), ultimate_pressure=P('~ 0.1 (single stage) / ~ 0.001 (two-stage)', 'mbar')),
    install=_MACH | dict(piping=['Keep inlet line short and of full size; fit an inlet trap/filter for dust and condensables.', 'Pipe the exhaust away from occupied areas.']),
    maint=_maint([M('Check oil level and colour.', 'sight_glass', 'daily')], [M('Change oil and exhaust filter.', 'connections', '500–2000 h'), M('Run with gas ballast to purge vapours.', 'connections', 'as needed')],
                 [M('Replace vanes, shaft seal and exhaust valve.', 'vane_1')], ['Vacuum pump oil (low vapour pressure); never use ordinary lube oil.']),
    failures=[F('Poor ultimate vacuum', ['Cannot reach pressure'], ['Contaminated oil, leaks, worn vanes'], ['Change oil, leak test, overhaul'], 'oil_casing'),
              F('Oil mist at exhaust', ['Smoke'], ['Saturated demister, high inlet pressure for long periods'], ['Replace exhaust filter'], 'connections')],
    quiz=[Q('Why is the pump "oil-sealed"?', ['To cool only', 'Oil seals the clearances so lower pressure is reached', 'For colour', 'To drive the vanes'], 1, 'Sealing.'),
          Q('What is the gas-ballast valve for?', ['Raising pumping speed', 'Preventing vapours condensing in the oil', 'Lubrication', 'Starting'], 1, 'Admits air during compression.'),
          Q('A dirty, milky oil indicates…', ['Normal', 'Water/vapour contamination — change oil, use gas ballast', 'Overspeed', 'Good sealing'], 1, 'Condensed vapour.')],
)
MODULES['liquid_ring_vacuum_pump'] = mod(
    definition=('A liquid ring vacuum pump has an eccentric bladed impeller in a casing partly filled with liquid. The liquid forms a ring; because of the eccentricity the spaces between '
                'blades grow (suction) and shrink (compression). It handles wet, dirty and condensable gases.'),
    applications=['Paper machine vacuum', 'Steam-condenser air removal', 'Chemical process vacuum (solvent recovery)', 'Vacuum filtration, priming systems'],
    key_points=['Tolerates liquids and vapours', 'Near-isothermal compression (liquid cools)', 'Vacuum limited by service-liquid vapour pressure', 'Cavitation if run below its limit'],
    principle=[step('Rotation throws the service liquid into a ring concentric with the casing.', 'liquid_ring'),
               step('On the suction side the liquid recedes from the hub and the cells draw gas in through the port plate.', 'port_plate', overlay='flow'),
               step('On the other side the liquid moves in, compressing the gas.', 'impeller'),
               step('Gas and some liquid leave through the discharge port to the separator; liquid is cooled and returned.', 'separator', overlay='flow')],
    curve='Capacity vs suction pressure; capacity falls as pressure approaches the vapour pressure of the service liquid.',
    params=rm(P('Inlet DN 25 – 600'), P('1 – 1000', 'kW'), P('300 – 3600', 'rpm'), P('10 – 30 000 m³/h', ''), suction_pressure=P('~ 33 – 1013 (single stage ~ 33 mbar with 15 °C water)', 'mbar(a)')),
    install=_MACH | dict(piping=['Provide service-liquid supply with flow control and cooling; discharge separator above the pump.']),
    maint=_maint([M('Check service-liquid flow and temperature.', 'liquid_ring', 'daily')], [M('Descale casing and port plate.', 'port_plate', 'annual')],
                 [M('Inspect impeller for cavitation erosion; replace seals/bearings.', 'impeller')], ['Grease-lubricated bearings outside the casing.']),
    failures=[F('Cavitation', ['Rattling noise, erosion'], ['Operating below the minimum suction pressure, hot service liquid'], ['Open anti-cavitation valve; cool the liquid'], 'impeller'),
              F('Loss of capacity', ['Higher suction pressure'], ['Hot or too little service liquid, scale'], ['Restore flow/cooling; descale'], 'liquid_ring')],
    quiz=[Q('Why is the impeller eccentric?', ['For balance', 'So the cells between blades change volume', 'To save space', 'It is not'], 1, 'Like a vane pump.'),
          Q('What limits the vacuum?', ['Motor size', 'Vapour pressure of the service liquid', 'Colour', 'Impeller material'], 1, 'Warmer liquid → poorer vacuum.'),
          Q('Liquid ring pumps are good for wet gases because…', ['They are oil-sealed', 'Liquid in the gas just joins the ring', 'They are dry', 'They run slow'], 1, 'Tolerant of carry-over.')],
)
MODULES['dry_screw_vacuum_pump'] = mod(
    definition=('A dry screw vacuum pump uses two non-contacting screw rotors, synchronised by timing gears, to carry gas from the inlet to the exhaust. Variable pitch compresses the gas '
                'internally. There is no oil or liquid in the gas path, so the process is not contaminated.'),
    applications=['Chemical and pharmaceutical processes (distillation, drying)', 'Semiconductor and solar manufacturing', 'Vacuum degassing, coating', 'Solvent recovery'],
    key_points=['No contamination, no waste oil', 'Handles condensables with purge and temperature control', 'Variable pitch reduces power', 'Watch for deposits'],
    principle=[step('Gas enters the inlet at the vacuum end.', 'casing', overlay='flow'),
               step('Gas trapped in the threads is moved along by the counter-rotating screws.', 'screw_1'),
               step('Shorter pitch near the exhaust compresses the gas internally.', 'screw_2', overlay='pressure'),
               step('Timing gears keep the screws in step without contact.', 'timing_gear_1', cut=False),
               step('Gas exhausts near atmospheric pressure.', 'connections', overlay='flow')],
    curve='Pumping speed high over a wide range; ultimate pressure ~ 10⁻²–10⁻³ mbar class (design-specific).',
    params=rm(P('Inlet DN 25 – 250'), P('1.5 – 75', 'kW'), P('3000 – 6000 (VFD)', 'rpm'), P('25 – 2000 m³/h', ''), ultimate_pressure=P('~ 0.001 – 0.05', 'mbar')),
    install=_MACH | dict(piping=['Fit inlet trap/condenser for heavy vapour loads; provide nitrogen purge and cooling water.']),
    maint=_maint([M('Check cooling water and purge flow; motor current trend.', 'casing', 'daily')], [M('Flush with solvent if deposits are expected.', 'screw_1', 'per process')],
                 [M('Replace bearings and gear oil; inspect screws.', 'gearbox')], ['Gear case oil (separated from the gas by seals).']),
    failures=[F('Deposits / seizure', ['Rising current, trips'], ['Process polymerises or condenses inside'], ['Raise temperature, solvent flushing'], 'screw_1'),
              F('Overheating', ['High casing temperature'], ['Cooling-water loss'], ['Restore cooling'], 'casing')],
    quiz=[Q('Why is it called "dry"?', ['It is air cooled', 'No oil or liquid in the compression chamber', 'It pumps only dry gas', 'It has no bearings'], 1, 'Clean vacuum.'),
          Q('Why do the screws have variable pitch?', ['Appearance', 'To compress gas internally and reduce power', 'For balance', 'To reduce weight'], 1, 'Internal compression.'),
          Q('What keeps the screws from touching?', ['Oil film', 'Timing gears', 'Springs', 'Gas pressure'], 1, 'Synchronisation.')],
)
MODULES['vacuum_ejector'] = mod(
    definition=('A steam jet vacuum ejector has no moving parts. Motive steam expands in a converging–diverging nozzle to supersonic speed and low pressure, entraining gas from the suction '
                'chamber; the diffuser then slows the mixture and recovers its pressure to the discharge.'),
    applications=['Refinery vacuum distillation', 'Steam-turbine condenser air removal', 'Evaporators and crystallisers', 'Deodorisers (edible oil)'],
    key_points=['No moving parts — very reliable', 'Uses motive steam (energy cost)', 'Multi-stage with condensers for deep vacuum', 'Sensitive to steam pressure and discharge pressure'],
    principle=[step('Motive steam enters the steam chest at high pressure.', 'steam_chest', overlay='pressure'),
               step('The nozzle converts pressure into a supersonic jet.', 'nozzle', overlay='flow'),
               step('The jet entrains gas from the suction chamber.', 'suction_chamber', overlay='flow'),
               step('In the diffuser the mixture slows and the pressure recovers.', 'diffuser', overlay='pressure')],
    curve='Suction pressure vs non-condensable load (ejector curve); breaks if discharge pressure exceeds the design limit.',
    params=rm(P('Suction DN 25 – 1500'), P('Steam consumption ~ kg/h per kg/h of load (design specific)', 'kg/h'), P('— (no moving parts)', ''), P('Load: kg/h of air/vapour', ''),
              suction_pressure=P('~ 50 mbar per stage; < 1 mbar with 4–6 stages', 'mbar(a)')),
    install=_MACH | dict(alignment=['Install diffuser outlet to condenser without pipe strain; keep nozzle concentric.'],
                         piping=['Supply dry, superheated motive steam at design pressure with a strainer and separator.']),
    maint=_maint([M('Check motive steam pressure and suction pressure.', 'steam_chest', 'daily')], [M('Inspect and clean the nozzle throat.', 'nozzle', 'annual')],
                 [M('Inspect diffuser for erosion; replace nozzle.', 'diffuser')], ['No lubrication required.']),
    failures=[F('Loss of vacuum ("break")', ['Suction pressure jumps up'], ['Low steam pressure, high discharge pressure, worn nozzle'], ['Restore steam/condenser; replace nozzle'], 'nozzle'),
              F('Air in-leakage', ['Higher load, poor vacuum'], ['Leaking flanges/process'], ['Leak test'], 'suction_chamber')],
    quiz=[Q('What creates the low pressure in an ejector?', ['A piston', 'A high-velocity steam jet from the nozzle', 'A fan', 'A cold surface'], 1, 'Momentum transfer.'),
          Q('What does the diffuser do?', ['Accelerates steam', 'Slows the mixture and recovers pressure', 'Condenses steam', 'Filters gas'], 1, 'Pressure recovery.'),
          Q('Why use several stages with condensers?', ['To use less steam for deep vacuum', 'For noise', 'For appearance', 'Not needed'], 0, 'Each stage has a limited compression ratio.')],
)

# ===================================================================== power equipment
_GEN_MAINT = _maint([M('Check output voltage, frequency and alarms.', 'control_panel', 'daily'), M('Check coolant, oil and fuel levels.', 'radiator', 'daily')],
                    [M('Change engine oil and filters; check belts and battery.', 'e_block', '250–500 h'), M('Measure generator insulation resistance.', 'g_stator', 'annual')],
                    [M('Engine top/major overhaul; alternator bearing replacement.', 'e_head')], ['Engine oil per maker (API/ACEA class); alternator bearings greased or sealed.'])

MODULES['engine_driven_generator'] = mod(
    definition=('An engine-driven generator uses a reciprocating engine to turn an AC generator. In a spark-ignition gas engine the fuel–air mixture is ignited by spark plugs; the pistons drive '
                'the crankshaft and flywheel, which turn the generator rotor. The governor holds constant speed so the frequency stays at 50/60 Hz.'),
    applications=['Gas-engine CHP (combined heat and power)', 'Biogas and landfill-gas power', 'Prime power in remote sites', 'Peaking and grid support'],
    key_points=['Speed fixes frequency: f = p·n/120', 'Governor controls speed, AVR controls voltage', 'Heat can be recovered (CHP)', 'Load acceptance limited by engine'],
    principle=[step('Fuel–air mixture burns in each cylinder and pushes the piston down.', 'e_pistons'),
               step('Connecting rods turn the crankshaft; the flywheel smooths the torque.', 'e_crankshaft'),
               step('The flywheel drives the generator rotor through the housing adaptor.', 'flywheel', cut=False),
               step('The rotating field induces 3-phase voltage in the stator.', 'g_stator'),
               step('The radiator and fan remove engine heat.', 'radiator', cut=False, overlay='flow')],
    curve='Fuel consumption vs load: best specific consumption near 75–100 % load.',
    params=rm(P('Frame sizes ~ 20 kW – 10 MW'), P('20 – 10 000', 'kWe'), P('1500 / 1800 (4-pole)', 'rpm'), P('Output 400 V–11 kV, 50/60 Hz', ''), electrical_efficiency=P('~ 35 – 45', '%')),
    install=_MACH | dict(piping=['Fuel gas train with pressure regulation; exhaust with silencer and flexible connection; ventilation for combustion and cooling air.']),
    maint=_GEN_MAINT,
    failures=[F('Engine misfire', ['Rough running, power loss'], ['Spark plug wear, ignition fault'], ['Replace plugs/coils'], 'e_head'),
              F('Overheating', ['High coolant temperature'], ['Blocked radiator, fan belt'], ['Clean radiator, check fan'], 'radiator'),
              F('Voltage instability', ['Voltage hunting'], ['AVR fault'], ['Check AVR'], 'g_exciter')],
    quiz=[Q('What sets the output frequency?', ['Engine speed and number of poles', 'Fuel type', 'Radiator size', 'Cable length'], 0, 'f = p·n/120.'),
          Q('Which device keeps voltage constant?', ['Governor', 'AVR', 'Radiator', 'Flywheel'], 1, 'Automatic voltage regulator.'),
          Q('What is the flywheel for?', ['Cooling', 'Smoothing engine torque pulses', 'Measuring speed', 'Starting only'], 1, 'Energy storage between firing strokes.')],
)
MODULES['alternator'] = mod(
    definition=('An alternator is a synchronous AC generator. A DC-excited rotor (here 4 salient poles) turns inside a 3-phase stator winding; its moving magnetic field induces AC voltage. '
                'A brushless exciter with rotating diodes supplies the field current, controlled by the AVR.'),
    applications=['Diesel and gas generating sets', 'Hydro and steam turbine generators', 'Marine and rail power', 'Wind turbines (synchronous types)'],
    key_points=['Frequency = poles × rpm / 120', 'Brushless excitation — no slip rings', 'AVR holds voltage', 'Insulation class sets temperature limit'],
    principle=[step('The prime mover turns the rotor through the drive hub.', 'drive_hub', cut=False),
               step('The exciter produces AC that the rotating rectifier turns into DC for the field coils.', 'a_exciter'),
               step('The excited rotor poles form a rotating magnetic field.', 'a_rotor', overlay='magnetic_field'),
               step('The field sweeps the stator conductors and induces 3-phase AC voltage.', 'a_stator', overlay='flow'),
               step('The AVR measures output voltage and adjusts the exciter field.', 'avr', cut=False)],
    curve='Open-circuit (magnetisation) curve and capability (P–Q) chart.',
    params=rm(P('Frames ~ 5 kVA – 1500 MVA'), P('5 – 1 500 000', 'kVA'), P('1500/1800 (4-pole); 3000/3600 (2-pole)', 'rpm'), P('Voltage 230 V – 27 kV', ''),
              power_factor=P('0.8 lagging (rated, typical)', '')),
    install=_MACH | dict(piping=['Cable termination sized for rated current; earthing of frame and neutral per system design.']),
    maint=_maint([M('Check voltage, current balance, temperatures.', 'a_stator', 'daily')], [M('Insulation resistance / polarisation index test.', 'a_stator', 'annual'), M('Test rotating diodes.', 'a_exciter', 'annual')],
                 [M('Clean windings, replace bearings.', 'bearings')], ['Bearing grease per nameplate interval.']),
    failures=[F('Loss of voltage', ['No output'], ['Failed diode, AVR fault, loss of residual magnetism'], ['Test diodes/AVR; flash field'], 'a_exciter'),
              F('Winding insulation failure', ['Earth fault trip'], ['Moisture, overheating, ageing'], ['Dry out, rewind'], 'a_stator')],
    quiz=[Q('A 4-pole alternator at 1500 rpm produces…', ['25 Hz', '50 Hz', '60 Hz', '100 Hz'], 1, '4 × 1500 / 120 = 50.'),
          Q('Why "brushless"?', ['No bearings', 'Field current comes from a shaft-mounted exciter and rotating diodes', 'No stator', 'No field'], 1, 'No slip rings/brushes.'),
          Q('Which part has the 3-phase output winding?', ['Rotor', 'Stator', 'Exciter rotor', 'Fan'], 1, 'Armature on the stator.')],
)
MODULES['diesel_generator_set'] = mod(
    definition=('A diesel generator set is a complete power unit on a skid: a compression-ignition diesel engine drives an alternator through a flywheel, with radiator, base-frame fuel tank, '
                'exhaust silencer and a controller. It provides standby, prime or continuous power.'),
    applications=['Standby power for hospitals, data centres, plants', 'Prime power at remote sites and mines', 'Emergency fire-pump and safety systems', 'Construction and events (rental)'],
    key_points=['Ratings: standby / prime / continuous (ISO 8528-1)', 'Automatic start on mains failure (with ATS)', 'Regular test runs under load', 'Fuel quality and storage matter'],
    principle=[step('Air is compressed in the cylinders; injected diesel ignites from the heat of compression.', 'e_head'),
               step('Pistons and connecting rods turn the crankshaft.', 'e_pistons'),
               step('The turbocharger uses exhaust energy to push more air in.', 'turbocharger', cut=False),
               step('The flywheel drives the alternator, which produces AC power.', 'g_rotor', overlay='flow'),
               step('The radiator cools the engine; the silencer quietens the exhaust.', 'radiator', cut=False, overlay='flow')],
    curve='Fuel consumption (L/h) vs load %; avoid long periods at very low load (wet stacking).',
    params=rm(P('~ 10 kVA – 4 MVA (single sets)'), P('8 – 3200', 'kWe'), P('1500 / 1800', 'rpm'), P('400 V – 13.8 kV, 50/60 Hz', ''), fuel_consumption=P('~ 0.2 – 0.3 L per kWh at full load', 'L/kWh')),
    install=_MACH | dict(foundation=['Level concrete plinth; anti-vibration mounts between engine/alternator and base.'],
                         piping=['Exhaust with flexible bellows, silencer and rain cap away from air intakes; radiator air discharge ducted out.', 'Fuel supply/return with day tank and bund.']),
    maint=_GEN_MAINT | dict(routine=[M('Weekly no-load test run; monthly load test.', 'control_panel', 'weekly'), M('Check coolant, oil, fuel, battery.', 'radiator', 'weekly')]),
    failures=[F('Fails to start', ['Cranks but no start'], ['Fuel air-lock, weak battery, low fuel'], ['Bleed fuel, charge battery'], 'e_head'),
              F('Wet stacking', ['Black oily exhaust'], ['Running at very low load'], ['Load bank test'], 'exhaust_silencer'),
              F('Overheating', ['Shutdown on temperature'], ['Blocked radiator, low coolant'], ['Clean, refill'], 'radiator')],
    quiz=[Q('How is diesel fuel ignited?', ['Spark plug', 'Heat of compression', 'Glow from the exhaust', 'Electric heater'], 1, 'Compression ignition.'),
          Q('What does the turbocharger do?', ['Cools oil', 'Compresses intake air using exhaust energy', 'Starts the engine', 'Regulates voltage'], 1, 'More air → more power.'),
          Q('"Standby" rating means…', ['Unlimited hours at full load', 'Emergency use for a limited number of hours per year', 'No load', 'Base load'], 1, 'Per ISO 8528-1 definitions.'),
          Q('Wet stacking is caused by…', ['Overloading', 'Long running at very light load', 'Cold weather only', 'Old batteries'], 1, 'Incomplete combustion.')],
)
MODULES['variable_frequency_drive'] = mod(
    definition=('A variable frequency drive controls an AC motor\'s speed by changing the frequency and voltage it supplies. A rectifier makes DC, a DC link smooths it and an IGBT inverter '
                'switches it with pulse-width modulation (PWM) to synthesise AC of any frequency.'),
    applications=['Pumps and fans (energy saving)', 'Conveyors and process lines', 'Compressors', 'Cranes and hoists (with braking)'],
    key_points=['Speed ≈ 120·f / poles', 'Energy: P ∝ N³ for pumps/fans', 'Harmonics and EMC need attention', 'Soft start and controlled stop built in'],
    principle=[step('Mains AC passes the line reactor into the rectifier, which turns it into DC.', 'rectifier', overlay='waveforms'),
               step('The DC link capacitors smooth the DC voltage.', 'dc_bus'),
               step('IGBTs switch the DC thousands of times per second (PWM) to build a sine-like AC of the chosen frequency.', 'inverter', overlay='waveforms'),
               step('The motor speed follows the output frequency — watch the motor ramp up and down.', 'motor_rotor', overlay='flow'),
               step('The control board sets speed, ramps and protection; the fan cools the heatsink.', 'control')],
    curve='Constant V/f (or vector control) up to base speed; field weakening above. Pump/fan power falls with the cube of speed.',
    params=rm(P('Frames 0.2 kW – several MW'), P('0.2 – 10 000+', 'kW'), P('Output 0 – 60/120 Hz (application dependent)', 'Hz'), P('Rated output current (A) per frame', ''),
              efficiency=P('~ 96 – 98', '%')),
    install=_ELEC, maint=_maint([M('Check fan and heatsink temperature; read fault log.', 'cooling_fan', 'monthly')],
                                [M('Clean filters and heatsink; check terminal torque.', 'enclosure', '6–12 months')],
                                [M('Replace cooling fans and DC capacitors (end of life).', 'dc_bus', '~ 5–10 years')], ['No lubrication; fan bearings are sealed.']),
    failures=[F('Overcurrent / overvoltage trips', ['Drive trips'], ['Too-short ramps, motor fault, regenerative load'], ['Lengthen ramps; braking resistor'], 'inverter'),
              F('Overheating', ['Over-temperature trip'], ['Blocked filters, failed fan, high ambient'], ['Clean, replace fan'], 'cooling_fan'),
              F('DC-link capacitor failure', ['Ripple, bus faults'], ['Age, heat'], ['Replace capacitors'], 'dc_bus')],
    quiz=[Q('A pump slowed to 80 % speed by a VFD uses about…', ['80 % power', '64 % power', '51 % power', '100 % power'], 2, 'Cube law.'),
          Q('What does the DC link do?', ['Converts DC to AC', 'Stores energy and smooths the rectified voltage', 'Measures speed', 'Cools the IGBTs'], 1, 'Capacitor bank.'),
          Q('PWM means the output voltage is made of…', ['Pure sine from a transformer', 'Fast on/off pulses whose average follows a sine', 'DC only', 'Random noise'], 1, 'Pulse-width modulation.'),
          Q('To run a 4-pole motor at about 750 rpm, the VFD outputs roughly…', ['12.5 Hz', '25 Hz', '50 Hz', '100 Hz'], 1, 'n = 120 f / p → f = 25 Hz.')],
)
MODULES['soft_starter'] = mod(
    definition=('A soft starter limits the starting current and torque of an AC motor. Anti-parallel thyristors in each phase pass only part of each half-cycle at first and the firing angle is '
                'advanced over the ramp until full voltage; a bypass contactor then closes. It does not control running speed.'),
    applications=['Pumps (reduces water hammer with soft stop)', 'Fans and compressors', 'Conveyors (avoids belt slip)', 'Where supply capacity limits direct-on-line starting'],
    key_points=['Reduced voltage start: torque ∝ V²', 'Starting current typically 2–4 × FLC', 'Bypass contactor removes heat during running', 'Cheaper than a VFD; no speed control'],
    principle=[step('At start, the thyristors fire late in each half-cycle — reduced voltage reaches the motor.', 'thyristors', overlay='waveforms'),
               step('The control module advances the firing angle along the ramp; the motor accelerates smoothly.', 'control_module', overlay='flow'),
               step('Current transformers monitor current for current-limit and protection.', 'current_transformers'),
               step('At full voltage the bypass contactor closes and carries the running current.', 'bypass_contacts', overlay='flow'),
               step('A soft stop reverses the ramp (useful against pump water hammer).', 'motor_rotor')],
    curve='Starting current and torque vs speed for DOL vs soft start; current limit typically 2–4 × FLC.',
    params=rm(P('Frames ~ 3 kW – several MW'), P('3 – 5000+', 'kW'), P('Motor runs at its normal speed', 'rpm'), P('Rated current (A); starts per hour', ''), ramp_time=P('~ 2 – 60', 's')),
    install=_ELEC, maint=_maint([M('Check fault log and temperatures.', 'control_module', 'monthly')], [M('Check terminal torque; clean heatsinks.', 'thyristors', 'annual')],
                                [M('Inspect bypass contacts.', 'bypass_contacts')], ['None.']),
    failures=[F('Thyristor failure', ['Phase loss / shorted SCR trip'], ['Overload, too many starts, surge'], ['Replace SCR; check starts per hour'], 'thyristors'),
              F('Long start / stall', ['Motor does not reach speed'], ['Current limit too low for the load'], ['Raise current limit; check load'], 'control_module')],
    quiz=[Q('Does a soft starter change the running speed?', ['Yes', 'No — it only controls start and stop', 'Only for pumps', 'Only at night'], 1, 'Unlike a VFD.'),
          Q('If voltage is halved during the start, motor torque falls to about…', ['50 %', '25 %', '75 %', '100 %'], 1, 'Torque ∝ V².'),
          Q('Why close a bypass contactor after the ramp?', ['To speed up the motor', 'To remove thyristor losses and heat in running', 'For EMC only', 'To stop the motor'], 1, 'Efficiency.')],
)

# ===================================================================== couplings & mechanical drives
MODULES['magnetic_coupling'] = mod(
    definition=('A magnetic coupling transmits torque without contact. Permanent magnets on an outer rotor attract opposite poles on an inner rotor through a thin containment shell, '
                'so the load side is hermetically sealed — no dynamic shaft seal is needed.'),
    applications=['Sealless (mag-drive) pumps for toxic/flammable liquids', 'Mixers and reactors', 'Vacuum and pressurised equipment', 'Food and pharma (hygienic)'],
    key_points=['Zero leakage — static seal only', 'Torque limited: decouples on overload', 'Metal shells generate eddy-current heat', 'Magnets are temperature limited'],
    principle=[step('The motor turns the outer magnet rotor.', 'outer_rotor', overlay='flow'),
               step('Magnetic flux passes through the non-magnetic containment shell.', 'containment_shell', overlay='magnetic_field'),
               step('The inner magnets follow, turning the load shaft at the same speed.', 'inner_rotor'),
               step('If the load torque exceeds the coupling rating, the rotors slip (decouple).', 'inner_rotor')],
    curve='Torque vs angular displacement between rotors: rises to a maximum (breakaway) at about half a pole pitch.',
    params=rm(P('Torque range ~ 1 Nm – several kNm'), P('0.1 – 500', 'kW'), P('Up to ~ 3600 (higher on special units)', 'rpm'), P('Rated transmissible torque', 'Nm'),
              shell=P('Stainless / Hastelloy / non-metallic', '')),
    install=_DRIVE | dict(alignment=['Centre the outer rotor around the shell with the specified radial clearance; magnetic forces are strong — use assembly fixtures.']),
    maint=_maint([M('Monitor bearing temperature and vibration.', 'bearing_housings', 'weekly')], [M('Check for rubbing marks on the shell.', 'containment_shell', 'at overhaul')],
                 [M('Replace bearings; check magnet strength.', 'inner_rotor')], ['Grease for motor-side bearings; process-lubricated inner bearings on mag-drive pumps.']),
    failures=[F('Decoupling', ['Motor runs, load stopped'], ['Overload, high viscosity, magnet overheating'], ['Stop, find cause, restart'], 'inner_rotor'),
              F('Shell rupture', ['Leak'], ['Rubbing from bearing wear, overheating'], ['Replace shell; monitor bearings'], 'containment_shell')],
    quiz=[Q('Why is a magnetic coupling leak-free?', ['Special packing', 'Torque passes through a solid shell — no rotating seal', 'Oil film', 'It is not'], 1, 'Static containment.'),
          Q('What happens on overload?', ['The shaft breaks', 'The rotors slip/decouple', 'Torque increases', 'Shell expands'], 1, 'Built-in torque limit.'),
          Q('A metal containment shell heats up because of…', ['Friction', 'Eddy currents', 'Sunlight', 'Oil'], 1, 'Rotating field induces currents.')],
)
MODULES['torque_limiter'] = mod(
    definition=('A torque limiter protects a drive from overload. In a friction type, disc springs clamp the driven member (sprocket) between friction facings; below the set torque it drives '
                'normally, above it the facings slip and the jam does not damage motor or gearbox.'),
    applications=['Conveyors and feeders', 'Packaging and printing machines', 'Crushers and mixers', 'Agricultural machinery'],
    key_points=['Set by spring force (adjusting nut)', 'Slips on overload, re-engages automatically', 'Keep facings dry', 'Slip detection sensor recommended'],
    principle=[step('The hub on the driving shaft turns the pressure plate and springs.', 'hub', overlay='torque'),
               step('Spring force clamps the sprocket between the friction facings.', 'pressure_plate'),
               step('Below the set torque the sprocket turns with the hub and drives the chain.', 'sprocket', overlay='flow'),
               step('On a jam the load torque exceeds the setting — the facings slip and the sprocket stops.', 'friction_facings', overlay='torque')],
    curve='Transmitted torque rises with load until the slip torque, then stays roughly constant while slipping.',
    params=rm(P('Bore ~ 10 – 150 mm'), P('Depends on speed', 'kW'), P('Up to ~ 1500 (friction type)', 'rpm'), P('Slip torque ~ 2 Nm – 20 kNm', 'Nm')),
    install=_DRIVE | dict(commissioning=['Set the nut to the maker\'s chart for the required slip torque; run in the facings; verify slip with a torque wrench.']),
    maint=_maint([M('Check for signs of slipping (heat, dust).', 'friction_facings', 'weekly')], [M('Verify slip torque.', 'pressure_plate', 'annual')],
                 [M('Replace facings and bush.', 'friction_facings')], ['No lubrication of facings; grease the sprocket bush only if specified.']),
    failures=[F('Nuisance slipping', ['Slips under normal load'], ['Setting too low, worn/oily facings'], ['Re-set, replace facings'], 'friction_facings'),
              F('No slip on jam', ['Damage to drive'], ['Rusted/seized facings, over-tightened'], ['Free, re-set, test'], 'pressure_plate')],
    quiz=[Q('How is the slip torque set?', ['By chain length', 'By the spring force via the adjusting nut', 'By motor speed', 'By oil'], 1, 'More preload → higher torque.'),
          Q('During an overload the sprocket…', ['Speeds up', 'Stops while the hub keeps turning', 'Reverses', 'Breaks'], 1, 'Slip.'),
          Q('Why keep facings free of oil?', ['Oil lowers friction → slip torque falls', 'Oil raises torque', 'No reason', 'Colour'], 0, 'Friction coefficient.')],
)
MODULES['speed_reducer'] = mod(
    definition=('A speed reducer is an enclosed gear drive that lowers speed and raises torque. In this two-stage helical reducer, each stage\'s ratio equals its tooth ratio (32/16 and 45/15), '
                'giving 6:1 overall; output torque ≈ input torque × ratio × efficiency.'),
    applications=['Conveyors, mixers, agitators', 'Cranes and hoists', 'Pump and fan drives at low speed', 'Extruders and mills'],
    key_points=['Ratio = product of stage ratios', 'Torque multiplied, speed divided', 'Helical gears: quiet, axial thrust', 'Oil level and cleanliness critical'],
    principle=[step('The motor drives the input shaft and pinion at high speed.', 'input_shaft', overlay='flow'),
               step('The pinion turns the larger gear — first reduction (2:1).', 'intermediate_shaft'),
               step('The intermediate pinion drives the output gear — second reduction (3:1).', 'output_shaft'),
               step('Gears dip into the oil bath, which lubricates gears and bearings by splash.', 'oil_bath'),
               step('Bearings carry radial and helical axial loads.', 'bearings')],
    curve='Efficiency ~ 97–98 % per helical stage; thermal rating may limit continuous power.',
    params=rm(P('Centre distance ~ 50 – 1000+ mm'), P('0.1 – 5000', 'kW'), P('Input typically 750 – 3000', 'rpm'), P('Output torque up to ~ 1 000 000 Nm', 'Nm'), ratio=P('~ 1.25 – 400 (1–4 stages)', '')),
    install=_DRIVE | dict(foundation=['Rigid, flat mounting; shim to avoid housing distortion.']),
    maint=_maint([M('Check oil level, temperature and noise.', 'oil_bath', 'weekly')], [M('Change oil; oil analysis.', 'oil_bath', '~ 5000–10 000 h'), M('Clean breather.', 'breather', '6 months')],
                 [M('Replace bearings and seals; inspect tooth contact.', 'bearings')], ['Gear oil grade per AGMA 9005 / maker (ISO VG 150–460 typical).']),
    failures=[F('Tooth pitting / wear', ['Noise, vibration, metal in oil'], ['Overload, poor lubrication'], ['Correct oil; replace gears'], 'output_shaft'),
              F('Oil leakage', ['Oil on base'], ['Worn seals, blocked breather'], ['Replace seals, clean breather'], 'housing'),
              F('Overheating', ['High oil temperature'], ['Overload, wrong oil level'], ['Correct level/load; add cooling'], 'oil_bath')],
    quiz=[Q('Overall ratio of stages 2:1 and 3:1 is…', ['5:1', '6:1', '1.5:1', '3:2'], 1, 'Multiply stage ratios.'),
          Q('If the input is 1500 rpm, the output of a 6:1 reducer is…', ['9000 rpm', '250 rpm', '1500 rpm', '600 rpm'], 1, '1500/6.'),
          Q('Helical gears produce…', ['No axial force', 'An axial thrust the bearings must carry', 'Lower torque', 'Higher speed'], 1, 'Due to the helix angle.')],
)
MODULES['belt_drive_assembly'] = mod(
    definition=('A V-belt drive transmits power between parallel shafts by friction between wedge-shaped belts and grooved sheaves. The speed ratio is the ratio of the sheave pitch diameters. '
                'Correct tension and alignment give long belt life.'),
    applications=['Fans and blowers', 'Pumps and compressors', 'Agricultural and workshop machines', 'Crushers and mills'],
    key_points=['Ratio = D_driven / D_driver', 'Tension: not too slack (slip), not too tight (bearings)', 'Replace belts as a matched set', 'Guard required'],
    principle=[step('The motor turns the small driver sheave.', 'driver_sheave'),
               step('Belts wedge into the grooves; friction transmits the torque.', 'belts', overlay='flow'),
               step('The large driven sheave turns slower in proportion to the diameters.', 'driven_sheave'),
               step('The slide base tensions the belts.', 'slide_base', cut=False),
               step('The guard encloses the drive for safety.', 'guard', cut=False)],
    curve='Power rating per belt vs speed (belt maker tables); efficiency ~ 93–97 %.',
    params=rm(P('Sheave Ø ~ 50 – 2000 mm'), P('0.1 – 1000', 'kW'), P('Belt speed typically 5 – 35 m/s', 'm/s'), P('Ratio up to ~ 8:1', ''), belts=P('Section SPZ/SPA/SPB/SPC or A/B/C', '')),
    install=_DRIVE | dict(commissioning=['Tension by the deflection method (force for a given deflection per span); re-tension after the first 24 h.']),
    maint=_maint([M('Look/listen for slip, cracking, squeal.', 'belts', 'weekly')], [M('Check tension and alignment.', 'slide_base', 'monthly')],
                 [M('Replace belts as a set; check groove wear.', 'driver_sheave')], ['No belt dressing; grease plummer blocks per schedule.']),
    failures=[F('Belt slip', ['Squeal, glazing, heat'], ['Low tension, worn grooves, overload'], ['Re-tension; replace sheaves'], 'belts'),
              F('Rapid belt wear', ['Frayed sides'], ['Misalignment'], ['Align sheaves'], 'slide_base')],
    quiz=[Q('A 150 mm driver drives a 375 mm sheave. The driven speed at 1450 rpm input is about…', ['3625 rpm', '580 rpm', '1450 rpm', '725 rpm'], 1, '1450 × 150/375.'),
          Q('Why replace V-belts as a matched set?', ['Cheaper', 'So all belts share the load equally', 'Colour matching', 'Not necessary'], 1, 'Different lengths unbalance load.'),
          Q('Over-tensioning belts mainly damages…', ['The guard', 'Shaft bearings', 'The motor windings', 'Nothing'], 1, 'High bearing loads.')],
)
MODULES['chain_drive_assembly'] = mod(
    definition=('A roller chain drive transmits power positively between sprockets. Chain rollers seat in the tooth gaps, so there is no slip and the ratio equals the tooth ratio. '
                'Chains need lubrication and correct slack.'),
    applications=['Conveyors and elevators', 'Agricultural and food machinery', 'Low-speed, high-torque drives', 'Motorcycles and bicycles'],
    key_points=['Positive drive — exact ratio', 'Lubrication is essential', 'Replace at ~3 % elongation (typical)', 'Odd tooth count on small sprocket'],
    principle=[step('The motor turns the driver sprocket.', 'driver_sprocket'),
               step('Teeth engage the rollers and pull the chain round.', 'chain', overlay='flow'),
               step('The driven sprocket turns at the tooth ratio (15/30 = half speed).', 'driven_sprocket'),
               step('The idler takes up slack on the slack side.', 'tensioner'),
               step('The drip lubricator oils the chain joints.', 'lubricator', cut=False)],
    curve='Power rating vs small-sprocket speed (chain maker tables); efficiency ~ 97–98 %.',
    params=rm(P('Pitch 6 – 76 mm (ISO 606)'), P('0.1 – 500+', 'kW'), P('Small sprocket up to ~ 3000 (small pitch)', 'rpm'), P('Ratio up to ~ 7:1 per stage', ''), links=P('Even number of links preferred', '')),
    install=_DRIVE | dict(commissioning=['Set slack ~ 2–4 % of span (typical); lubricate before start.']),
    maint=_maint([M('Check lubrication and noise.', 'lubricator', 'daily')], [M('Measure chain elongation; check sprocket teeth.', 'chain', 'monthly')],
                 [M('Replace chain and sprockets together when worn.', 'driver_sprocket')], ['Chain oil by drip, bath or spray depending on chain speed.']),
    failures=[F('Chain elongation (wear)', ['Riding up on teeth, jumping'], ['Lack of lubrication, age'], ['Lubricate; replace chain'], 'chain'),
              F('Sprocket tooth wear', ['Hooked teeth'], ['Worn chain run too long'], ['Replace sprockets with chain'], 'driven_sprocket')],
    quiz=[Q('Ratio of a 15T driver and 30T driven sprocket is…', ['1:1', '2:1 reduction', '1:2 increase', '15:1'], 1, '30/15.'),
          Q('Why does a chain drive not slip?', ['Belts are rubber', 'Rollers mesh positively with the teeth', 'Magnetism', 'Oil'], 1, 'Positive engagement.'),
          Q('A worn chain on new sprockets will…', ['Last longer', 'Wear the new sprockets quickly — replace together', 'Run quieter', 'Be fine'], 1, 'Mismatched pitch.')],
)
MODULES['flywheel_assembly'] = mod(
    definition=('A flywheel is a heavy rotating wheel that stores kinetic energy, E = ½·I·ω². It smooths fluctuating torque and supplies short bursts of high power — in a crank press it '
                'slows slightly at each stroke, giving up energy, and the motor brings it back up to speed between strokes.'),
    applications=['Mechanical presses and punches', 'Reciprocating engines and compressors', 'Energy storage (high-speed composite flywheels)', 'Rolling mills, shears'],
    key_points=['Energy ∝ I·ω² — speed matters most', 'Mass at the rim gives high inertia', 'Coefficient of speed fluctuation sets size', 'Burst speed limits rim speed'],
    principle=[step('The motor drives the flywheel to full speed.', 'flywheel', overlay='flow'),
               step('The flywheel stores energy in its heavy rim.', 'flywheel'),
               step('At each stroke, the crank and rod push the ram — the flywheel slows a little and releases energy.', 'connecting_rod'),
               step('The ram punches the workpiece with a peak power far above the motor rating.', 'ram'),
               step('Between strokes the motor restores the speed.', 'shaft_crank')],
    curve='Speed vs time: dips during the work stroke; ΔE = I·ω_mean²·Cs (Cs = coefficient of speed fluctuation).',
    params=rm(P('Ø ~ 0.3 – 5 m'), P('Motor 1 – 500', 'kW'), P('100 – 3000 (steel/cast iron)', 'rpm'), P('Stored energy ~ kJ – MJ', 'kJ'), rim_speed=P('≤ ~ 30–50 m/s for cast iron (check maker)', 'm/s')),
    install=_DRIVE,
    maint=_maint([M('Check vibration and bearing temperature.', 'bearings', 'daily')], [M('Check key and hub tightness.', 'flywheel', '6 months')],
                 [M('NDT of rim and spokes for cracks.', 'flywheel')], ['Grease or oil the main bearings per schedule.']),
    failures=[F('Loose flywheel on shaft', ['Knocking, fretting'], ['Worn key/keyway'], ['Re-fit with new key'], 'flywheel'),
              F('Cracked rim/spokes', ['Vibration, visible cracks'], ['Fatigue, overspeed'], ['Replace; never overspeed'], 'flywheel')],
    quiz=[Q('Doubling flywheel speed changes stored energy by…', ['×2', '×4', '×8', 'no change'], 1, 'E ∝ ω².'),
          Q('Why put most mass in the rim?', ['Easier casting', 'Maximum inertia for a given mass', 'Balance', 'Cooling'], 1, 'I ∝ m·r².'),
          Q('During the punching stroke, the flywheel…', ['Speeds up', 'Slows slightly, giving up energy', 'Stops', 'Reverses'], 1, 'Energy released.')],
)
MODULES['rotor_assembly'] = mod(
    definition=('A rotor assembly is the complete rotating element of a machine. For a multistage pump it includes the shaft, impellers, interstage sleeves, balance drum, thrust collar, '
                'locknuts and coupling hub, assembled in sequence and then dynamically balanced in two planes.'),
    applications=['Pump and compressor overhauls', 'Motor and turbine rotors', 'Spare (ready-to-install) rotors', 'Balancing shop work'],
    key_points=['Assembly order and stack-up matter', 'Check run-out at each step', 'Two-plane dynamic balancing (ISO 21940-11)', 'Store spare rotors vertically or turned regularly'],
    principle=[step('The shaft is checked for straightness (run-out).', 'shaft', explode=1.0),
               step('Impellers and sleeves are fitted in sequence, keyed and locked.', 'impeller_1', explode=0.6),
               step('The balance drum and thrust collar complete the stack; locknuts lock it.', 'balance_drum', explode=0.3),
               step('On the balancing machine the rotor is spun and unbalance is measured at both supports.', 'balancing_stand', overlay='balance'),
               step('Correction in two planes brings the residual unbalance within the grade.', 'impeller_4', overlay='balance')],
    curve='Permissible residual unbalance U = 9549 · m · G / n (g·mm, m in kg, n in rpm, G grade).',
    params=rm(P('Shaft length ~ 0.3 – 10 m'), P('Machine dependent', 'kW'), P('Service speed (sets balance tolerance)', 'rpm'), P('Rotor mass ~ kg – tonnes', 'kg'), balance_grade=P('G2.5 typical for pump rotors (ISO 21940-11)', '')),
    install=_DRIVE | dict(foundation=['Assemble in a clean shop on V-blocks or a stand; protect journals.'],
                          alignment=['Check run-out of journals, impeller hubs and seal sleeves with dial indicators (API 610 limits).'],
                          piping=['—'], commissioning=['Record final balance report and run-out readings; lift with approved slings at designated points.']),
    maint=_maint([M('Store spare rotor protected; rotate periodically if horizontal.', 'shaft', 'monthly')], [M('Check run-out before installation.', 'shaft', 'at use')],
                 [M('Re-balance after any component change.', 'balancing_stand')], ['Light preservative oil on journals in storage.']),
    failures=[F('High vibration after overhaul', ['1× vibration'], ['Imbalance, bent shaft, loose fits'], ['Re-balance; check run-out and fits'], 'shaft'),
              F('Axial rub', ['Noise, wear'], ['Wrong stack-up/impeller positions'], ['Re-check axial positions'], 'sleeve_1')],
    quiz=[Q('Why balance in two planes?', ['Cheaper', 'To correct both static and couple unbalance of a long rotor', 'Only one is needed', 'For appearance'], 1, 'Dynamic balancing.'),
          Q('What does "run-out" measure?', ['Speed', 'How much a surface wobbles when rotated', 'Length', 'Weight'], 1, 'Straightness/concentricity.'),
          Q('The balance drum on a multistage pump rotor…', ['Measures flow', 'Counteracts axial thrust', 'Drives the coupling', 'Holds oil'], 1, 'Thrust balancing.')],
)
