"""Learning content — Water Treatment & Utilities, EQ-296 … EQ-320.
Typical ranges are general engineering guidance; standard editions are marked 'to be verified' in the model metadata."""
from pumpforge.learning import mod, step, P, F, Q, M

MODULES = {}


def wu(size, capacity, conditions, power, **extra):
    """Required parameters for the water_utilities family: size, capacity, operating_conditions, power_rating."""
    ref = {'manufacturer': None, 'model': None, 'datasheet': None,
           'rated_point': {'capacity': None, 'operating_pressure': None, 'operating_temperature': None, 'water_or_gas_quality': None, 'power_kW': None},
           'status': 'empty — fill from the equipment datasheet'}
    return dict(size=size, capacity=capacity, operating_conditions=conditions, power_rating=power, reference_model=ref, extra=extra)


def _m(r, p, o, l):
    return dict(routine=r, periodic=p, overhaul=o, lubrication=l)


_BASIN = dict(foundation=['Reinforced-concrete tank on prepared ground; watertightness test before backfill; allow for buoyancy when empty (groundwater).'],
              alignment=['Weirs and launders levelled to a few millimetres so overflow is even; drive/bridge centred and level.'],
              piping=['Inlet arranged to spread flow without short-circuiting; sludge lines with flushing points; overflow and drain to a safe place.'],
              commissioning=['Fill with clean water, check for leaks; run mechanisms empty and with water; start chemical dosing and tune by jar tests.'])
_SKID = dict(foundation=['Level concrete plinth; anchor the skid; bund or drain for chemical / oil spills.'],
             alignment=['Skid level; check pump–motor alignment where not close-coupled; supports so piping loads do not reach equipment nozzles.'],
             piping=['Isolation valves and bypass for maintenance; drains and vents; correct materials for the chemical; label lines and flow direction.'],
             commissioning=['Pressure-test piping; flush; check rotation and interlocks; calibrate instruments; run on water before chemicals.'])
_IX = dict(foundation=['Vessels on level foundation or legs anchored; space above for resin loading and below for underdrain access.'],
           alignment=['Vessels plumb so the bed and distributors are level (uneven beds channel).'],
           piping=['Valve nest with service, backwash, regenerant, rinse; sample points before/after; acid/caustic-resistant lines and safety showers.'],
           commissioning=['Load support layers and resin (soaked), backwash to classify; first regeneration; rinse to quality; check conductivity/silica/hardness.'])
_PV = dict(foundation=['Supports designed for operating, test and wind/seismic loads; allow thermal movement of connected piping.'],
           alignment=['Vertical vessels plumb; nozzles and supports loaded within limits.'],
           piping=['Relief protection per code, drains at low points, isolations for inspection; slope lines to drains.'],
           commissioning=['Pressure test; set and seal relief valves; check instruments and drains; register with the authority where required.'])
_ROT = dict(foundation=['Rigid foundation or support steel to maker data; grout base plates; check natural frequencies away from running speed.'],
            alignment=['Laser-align drive train; check soft foot; set shaft runout and gear contact per maker.'],
            piping=['Lube/oil lines and vents accessible from outside; vibration switch wiring; guarding.'],
            commissioning=['Bump test rotation; run-in with vibration and temperature monitoring; record baseline spectrum.'])
_LUBE = ['Motor and drive bearings greased / oiled to maker schedule; gearbox oil changed by hours or oil analysis.']
_NL = ['No routine lubrication on static parts; lubricate valve stems and actuators per maker.']


# ===================================================================== raw water clarification
MODULES['clariflocculator'] = mod(
    definition=('A clariflocculator combines flocculation and clarification in one circular tank. Coagulated raw water rises into a central flocculation compartment where slow paddles let tiny particles collide '
                'and grow into flocs. The water passes under the compartment skirt into the outer clarifier zone, where flocs settle to the floor and are raked to a central sludge pit, while clear water '
                'overflows the peripheral weir.'),
    applications=['Surface-water treatment for drinking and process water', 'Clarification of cooling-tower make-up and industrial raw water'],
    key_points=['Coagulate → flocculate → settle in one unit', 'Gentle paddles (G ≈ 20–70 s⁻¹) grow flocs', 'Low surface loading (≈ 1–2 m/h) lets flocs settle', 'Rakes move sludge to the central pit'],
    principle=[step('Coagulated raw water rises through the central riser into the flocculation zone.', 'piping', overlay='flow'),
               step('Slow paddles turn so particles collide and grow into flocs.', 'flocculator_paddles'),
               step('Water flows under the skirt into the clarifier zone.', 'flocculation_zone', overlay='flow'),
               step('Flocs settle onto the floor; the rakes move them to the sludge pit.', 'cf_rakes', overlay='pressure'),
               step('Clear water overflows the peripheral weir to the filters.', 'cf_tank', overlay='flow')],
    curve='Effluent turbidity vs surface loading rate — rises sharply above the design overflow rate.',
    params=wu(P('Diameter ≈ 10 – 50 m; depth ≈ 3.5 – 5 m'), P('≈ 500 – 10,000', 'm³/h'), P('Surface loading ≈ 1 – 2 m/h; flocculation time ≈ 15 – 30 min', '—'), P('Rake drive ≈ 0.5 – 5; paddles ≈ 1 – 10', 'kW')),
    install=_BASIN, maint=_m([M('Check effluent turbidity, sludge blanket level and rake torque.', 'cf_rakes', 'daily')], [M('Clean weirs/launders (algae); check paddle bearings.', 'cf_tank', 'monthly')],
                             [M('Drain, inspect rakes, scrapers and drive gear; repair concrete.', 'cf_drive')], _LUBE),
    failures=[F('Floc carry-over', ['High outlet turbidity', 'Flocs over the weir'], ['Overloading', 'Wrong coagulant dose', 'Rising sludge blanket'], ['Jar test, adjust dose; desludge more often; reduce flow'], 'cf_clear'),
              F('Rake overload trip', ['Torque alarm, drive stops'], ['Heavy sludge accumulation', 'Debris'], ['Increase sludge withdrawal; lift rakes; clear obstruction'], 'cf_rakes')],
    quiz=[Q('Why are the flocculator paddles slow?', ['Large flocs are fragile; gentle mixing grows them without breaking them', 'To save power only', 'To heat the water', 'To add chemical'], 0, 'Gentle mixing.'),
          Q('Which design number controls clarifier size?', ['Surface loading (overflow) rate, m/h', 'Pipe diameter', 'Motor speed', 'Weir colour'], 0, 'Overflow rate.'),
          Q('Where does the sludge go?', ['Raked to the central pit and withdrawn', 'Over the weir', 'Into the flocculator', 'It dissolves'], 0, 'Sludge pit.')],
    selection=['Size area from design flow ÷ surface loading; flocculation volume from detention time; check with jar tests.'], safety=['Guard bridge drives; life-rings and handrails at open water; chemical handling PPE.'],
    refs=['AWWA / Ten States Standards', 'MWH Water Treatment'])

MODULES['flash_mixer'] = mod(
    definition=('A flash (rapid) mixer disperses coagulant into raw water within seconds. A high-speed turbine impeller creates intense turbulence in a small chamber so the chemical reaches every part of the '
                'flow before it reacts, giving uniform coagulation for the flocculation stage that follows.'),
    applications=['Coagulant (alum, ferric, PACl) dispersion at water treatment plants', 'pH adjustment and polymer dispersion in industrial water and wastewater'],
    key_points=['High energy: G ≈ 300–1000 s⁻¹', 'Short time: ≈ 10–60 s', 'Dose point at the impeller', 'Feeds the flocculator'],
    principle=[step('Raw water enters the mixing chamber near the bottom.', 'piping', overlay='flow'), step('Coagulant is dosed close to the impeller.', 'piping'),
               step('The high-speed impeller spreads the chemical in seconds.', 'fm_agitator', overlay='pressure'), step('Mixed water overflows to the flocculation tank.', 'fm_tank', overlay='flow')],
    curve='Coagulation efficiency vs velocity gradient G — rises then levels off.',
    params=wu(P('Chamber ≈ 1 – 3 m (side or diameter)'), P('≈ 100 – 5000', 'm³/h'), P('Detention ≈ 10 – 60 s; G ≈ 300 – 1000 s⁻¹', '—'), P('≈ 1 – 30', 'kW')),
    install=_BASIN, maint=_m([M('Check impeller running, dose rate and vibration.', 'fm_agitator', 'daily')], [M('Inspect impeller for wear and deposits.', 'fm_agitator', 'quarterly')], [M('Gearbox overhaul.', 'fm_drive')], _LUBE),
    failures=[F('Poor coagulation', ['Floc forms badly downstream'], ['Dose point far from impeller', 'Impeller worn/stopped'], ['Move dose to impeller; repair'], 'fm_agitator'),
              F('Gearbox noise', ['Vibration, heat'], ['Low oil, worn bearings'], ['Top up, replace bearings'], 'fm_drive')],
    quiz=[Q('Why must coagulant mix in seconds?', ['It reacts (hydrolyses) almost instantly', 'It evaporates', 'It is heavy', 'It is cold'], 0, 'Fast reaction.'),
          Q('Typical G in a flash mixer?', ['≈ 300 – 1000 s⁻¹', '≈ 1 s⁻¹', '≈ 10 s⁻¹', '≈ 100,000 s⁻¹'], 0, 'High G.'),
          Q('What comes after the flash mixer?', ['Flocculation', 'Disinfection only', 'Boiler', 'Discharge'], 0, 'Flocculation.')],
    selection=['Power P = G²·μ·V; choose impeller and speed for the target G.'], safety=['Lock out before entering; guard the coupling.'], refs=['AWWA', 'MWH Water Treatment'])

MODULES['flocculation_tank'] = mod(
    definition=('A flocculation tank stirs coagulated water gently for 15–30 minutes so small particles collide and stick together into large, heavy flocs. This tank has three compartments in series with '
                'horizontal paddle reels; each stage turns more slowly than the last (tapered energy) so the growing flocs are not broken.'),
    applications=['Ahead of clarifiers and lamella settlers in water treatment', 'Industrial wastewater physico-chemical treatment'],
    key_points=['Tapered energy: G falls stage by stage', 'G·t ≈ 10⁴ – 10⁵', 'Over-and-under baffles prevent short-circuiting', 'Paddle tip speed kept low'],
    principle=[step('Coagulated water enters stage 1.', 'tank', overlay='flow'), step('Paddle reel 1 turns fastest to start collisions.', 'paddle_reel_1', overlay='pressure'),
               step('Water passes under the first baffle into stage 2.', 'paddle_reel_2', overlay='flow'), step('Stage 3 is slowest so large flocs survive.', 'paddle_reel_3'),
               step('Flocculated water leaves to the clarifier.', 'tank', overlay='flow')],
    curve='Floc size vs time for different G values.',
    params=wu(P('≈ 3 – 20 m long, 3 – 5 m deep'), P('≈ 200 – 5000', 'm³/h'), P('Detention ≈ 15 – 30 min; G ≈ 70 → 10 s⁻¹', '—'), P('≈ 0.5 – 5 per stage', 'kW')),
    install=_BASIN, maint=_m([M('Check paddle speeds and floc appearance.', 'paddle_reel_1', 'daily')], [M('Inspect shaft seals and bearings.', 'drives', 'quarterly')], [M('Drain; replace worn paddle boards.', 'paddle_reel_2')], _LUBE),
    failures=[F('Pin-point floc', ['Small flocs, poor settling'], ['Under-dosing', 'Too short time', 'Too high G'], ['Jar test; reduce speed'], 'paddle_reel_3'),
              F('Shaft seal leak', ['Water at drive side'], ['Seal wear'], ['Replace seal'], 'drives')],
    quiz=[Q('Why taper the energy?', ['Large flocs are fragile and break at high G', 'To save money only', 'To heat water', 'To add oxygen'], 0, 'Tapered energy.'),
          Q('What does over-and-under baffling prevent?', ['Short-circuiting', 'Corrosion', 'Freezing', 'Noise'], 0, 'Plug flow.'),
          Q('Typical flocculation time?', ['≈ 15 – 30 min', '≈ 5 s', '≈ 12 h', '≈ 3 days'], 0, 'Minutes.')],
    selection=['Volume from flow × detention; power per stage from G.'], safety=['Guard drives; handrails at open tanks.'], refs=['AWWA', 'MWH'])

MODULES['lamella_clarifier'] = mod(
    definition=('A lamella clarifier uses a pack of inclined plates (≈ 55–60°) spaced a few centimetres apart. Each plate adds settling area, so particles settle only a short distance before sliding down '
                'the plate into the sludge hopper, while clear water rises between the plates to collection launders. It needs a fraction of the footprint of a conventional clarifier.'),
    applications=['Compact water and wastewater clarification', 'Mine water, filter backwash recovery and industrial effluents'],
    key_points=['Projected plate area does the settling', 'Inclined plates make sludge self-cleaning', 'Footprint ≈ 1/5 – 1/10 of a conventional clarifier', 'Laminar flow between plates'],
    principle=[step('Flocculated water enters the inlet channel.', 'nozzles', overlay='flow'), step('It turns under the plate pack and rises between the plates.', 'plate_pack', overlay='pressure'),
               step('Particles settle on the plates and slide down to the hopper.', 'plate_pack'), step('Clear water overflows the launders.', 'launders', overlay='flow'), step('Sludge is drawn from the hopper.', 'sludge')],
    curve='Effluent turbidity vs loading on projected area.',
    params=wu(P('Units ≈ 1 – 6 m wide; plate spacing ≈ 50 – 80 mm'), P('≈ 10 – 1000', 'm³/h'), P('Loading on projected area ≈ 0.5 – 1.5 m/h', '—'), P('Sludge scraper/pump ≈ 0.5 – 5', 'kW')),
    install=_BASIN, maint=_m([M('Check outlet turbidity and sludge level.', 'sludge', 'daily')], [M('Hose down plates; clean launders.', 'plate_pack', 'monthly')], [M('Remove plates; inspect supports.', 'plate_pack')], _NL),
    failures=[F('Plate fouling', ['Uneven flow, turbidity rise'], ['Biological growth, scale'], ['Wash plates'], 'plate_pack'), F('Sludge carry-over', ['Turbid launders'], ['Hopper full'], ['More frequent withdrawal'], 'sludge')],
    quiz=[Q('Where does a lamella clarifier get its extra settling area?', ['Projected area of the inclined plates', 'Taller tank', 'Chemicals', 'Faster flow'], 0, 'Plates.'),
          Q('Why are plates inclined ≈ 55–60°?', ['So settled sludge slides off', 'For appearance', 'To trap air', 'To heat water'], 0, 'Self-cleaning.'),
          Q('Main advantage?', ['Small footprint', 'No chemicals ever', 'No sludge', 'No power at all'], 0, 'Footprint.')],
    selection=['Projected area = flow ÷ allowable loading; check plate spacing for solids.'], safety=['Plate packs are heavy — use lifting gear; confined spaces in hoppers.'], refs=['AWWA', 'MWH'])

# ===================================================================== disinfection
MODULES['chlorination_system'] = mod(
    definition=('A gas chlorination system disinfects water with chlorine drawn from ton containers. The whole system works under vacuum: the ejector creates suction, the vacuum regulator on the container '
                'valve lets gas flow only while vacuum exists, the chlorinator meters the dose, and the ejector dissolves the gas into a water stream that is injected into a baffled contact tank.'),
    applications=['Drinking-water disinfection and residual in distribution', 'Cooling-water biocide and wastewater effluent disinfection'],
    key_points=['Vacuum operation: a broken line draws in air, it does not leak gas', 'Dose by rotameter (kg/day)', 'Disinfection = C × t', 'Leak detection and scrubbers in the chlorine room'],
    principle=[step('Containers sit on a scale so usage is measured.', 'containers_scale'), step('Vacuum regulators open only under ejector vacuum.', 'vacuum_regulators', overlay='pressure'),
               step('The chlorinator meters the gas rate.', 'chlorinator'), step('The ejector dissolves chlorine into motive water.', 'ejector_lines', overlay='flow'),
               step('The diffuser spreads the solution into the contact tank.', 'diffuser', overlay='flow')],
    curve='Residual chlorine vs dose (breakpoint curve).',
    params=wu(P('Ton containers ≈ 900 kg; chlorinator ≈ 1 – 200 kg/day'), P('≈ 1 – 200', 'kg Cl₂/day'), P('Vacuum operation; contact time ≥ ≈ 30 min typical', '—'), P('Booster pump ≈ 1 – 10', 'kW')),
    install=_SKID, maint=_m([M('Check residual, gas usage and vacuum.', 'chlorinator', 'daily')], [M('Test leak detector and alarms.', 'detector', 'monthly')],
                            [M('Overhaul regulators and ejector check valves.', 'vacuum_regulators')], _NL),
    failures=[F('Loss of vacuum', ['No feed, alarm'], ['Ejector blocked, low motive water pressure'], ['Clean ejector; restore water pressure'], 'ejector_lines'),
              F('Chlorine leak', ['Detector alarm, odour'], ['Damaged gasket at container valve'], ['Evacuate, use SCBA, follow emergency plan'], 'containers_scale')],
    quiz=[Q('Why is gas chlorination vacuum-operated?', ['A line break draws in air instead of leaking chlorine', 'It is cheaper', 'It heats water', 'No reason'], 0, 'Safety.'),
          Q('Disinfection effectiveness depends on…', ['C × t (residual × contact time)', 'Pipe colour', 'Motor speed', 'Container size'], 0, 'C·t.'),
          Q('What creates the vacuum?', ['The water ejector', 'The container', 'The scale', 'The tank'], 0, 'Ejector.')],
    selection=['Size from flow × dose; contact tank volume from required C·t.'], safety=['Toxic gas: leak detection, ventilation/scrubber, SCBA, emergency kits; trained staff only.'], refs=['WHO GDWQ', 'Chlorine Institute pamphlets'])

MODULES['uv_disinfection_system'] = mod(
    definition=('A UV disinfection reactor passes water through a stainless chamber close to ultraviolet lamps in quartz sleeves. UV-C light around 254 nm damages the DNA of bacteria, viruses and protozoa so '
                'they cannot reproduce. Automatic wipers keep the sleeves clean, and a sensor checks that the UV intensity is high enough.'),
    applications=['Drinking water (especially for Cryptosporidium/Giardia)', 'Wastewater effluent reuse and process water'],
    key_points=['Dose = intensity × time (mJ/cm²)', 'No chemicals, no residual', 'Water UV transmittance controls performance', 'Wipers and sensor keep dose assured'],
    principle=[step('Water enters the reactor chamber.', 'chamber', overlay='flow'), step('Lamps emit UV-C through quartz sleeves.', 'uv_lamps', overlay='pressure'),
               step('Microorganisms receive the UV dose as they pass.', 'quartz_sleeves'), step('Wipers clean the sleeves periodically.', 'wiper'), step('The sensor and panel confirm intensity.', 'control_sensor')],
    curve='Log inactivation vs UV dose for different organisms.',
    params=wu(P('Reactors DN 100 – 1000'), P('≈ 5 – 5000', 'm³/h'), P('Dose ≈ 40 mJ/cm² (typical drinking water); UVT ≥ ≈ 75 – 95 %', '—'), P('≈ 0.5 – 100', 'kW')),
    install=_SKID, maint=_m([M('Check UV intensity and alarms.', 'control_sensor', 'daily')], [M('Inspect wipers; clean sleeves if needed.', 'wiper', 'quarterly')], [M('Replace lamps (≈ 9,000 – 16,000 h).', 'uv_lamps')], _NL),
    failures=[F('Low UV intensity', ['Alarm, low sensor reading'], ['Fouled sleeves, aged lamps, low UVT'], ['Clean/replace; improve pretreatment'], 'quartz_sleeves'),
              F('Broken sleeve', ['Water in lamp, trip'], ['Thermal shock, impact'], ['Replace; check flow before lamp start'], 'quartz_sleeves')],
    quiz=[Q('How does UV disinfect?', ['Damages DNA/RNA so organisms cannot reproduce', 'Kills by heat', 'Adds chlorine', 'Filters them'], 0, 'DNA damage.'),
          Q('Does UV leave a residual?', ['No', 'Yes, for days', 'Only at night', 'Only in winter'], 0, 'No residual.'),
          Q('What reduces UV performance?', ['Low UV transmittance and sleeve fouling', 'Cold weather only', 'Blue paint', 'Low pressure'], 0, 'UVT and fouling.')],
    selection=['Size for peak flow, minimum UVT and target dose (validated reactors).'], safety=['UV burns eyes/skin — interlocks on covers; mercury in lamps: handle and dispose correctly.'], refs=['US EPA UVDGM', 'WHO GDWQ'])

MODULES['ozonation_system'] = mod(
    definition=('An ozonation system produces ozone on site by passing oxygen through a corona discharge (3 O₂ → 2 O₃) and bubbles it into water through fine diffusers in a covered contact tank. Ozone is a '
                'very strong oxidant: it disinfects and removes colour, taste, odour and micro-pollutants. Leftover ozone in the off-gas is destroyed before venting.'),
    applications=['Drinking-water oxidation and disinfection', 'Bottled water, cooling water, wastewater reuse and pulp bleaching'],
    key_points=['Made on site (unstable)', 'Corona discharge in dielectric tubes', 'Fine bubbles and depth give transfer', 'Off-gas destructor — ozone is toxic'],
    principle=[step('Oxygen is supplied from LOX or a PSA unit.', 'oxygen_supply', overlay='flow'), step('Corona discharge in the generator forms ozone.', 'dielectric_tubes'),
               step('Ozone gas bubbles through ceramic diffusers.', 'diffusers', overlay='flow'), step('Water flows under and over the baffles to get contact time.', 'contactor', overlay='pressure'),
               step('The destructor converts off-gas ozone back to oxygen.', 'off_gas_destructor')],
    curve='Ozone production vs power and gas flow; transfer efficiency vs bubble size.',
    params=wu(P('Generators ≈ 0.1 – 100 kg O₃/h'), P('≈ 0.1 – 100', 'kg O₃/h'), P('O₃ ≈ 6 – 12 wt % in O₂; dose ≈ 1 – 5 mg/L', '—'), P('≈ 8 – 12 kWh per kg O₃ (generator)', 'kWh/kg')),
    install=_SKID, maint=_m([M('Check ozone output, dew point of feed gas and residual.', 'generator_vessel', 'daily')], [M('Inspect dielectrics; check destructor.', 'dielectric_tubes', 'annually')],
                            [M('Replace dielectrics/diffusers as needed.', 'diffusers')], _NL),
    failures=[F('Low ozone output', ['Low residual'], ['Wet feed gas', 'Dielectric failure', 'Cooling water problem'], ['Dry gas; replace tube; restore cooling'], 'dielectric_tubes'),
              F('Ozone leak', ['Monitor alarm, smell'], ['Gasket failure'], ['Stop generator, ventilate, repair'], 'off_gas_destructor')],
    quiz=[Q('Why is ozone made on site?', ['It decomposes quickly', 'It is illegal to transport only', 'It is a liquid', 'It is too heavy'], 0, 'Unstable.'),
          Q('What converts O₂ to O₃?', ['Corona discharge', 'UV only', 'A pump', 'A filter'], 0, 'Corona.'), Q('Why destroy off-gas?', ['Ozone is toxic', 'It is valuable', 'It is flammable', 'It smells nice'], 0, 'Toxic.')],
    selection=['Size by dose × flow with transfer efficiency; contactor volume by C·t.'], safety=['Ambient ozone monitors and interlocks; oxygen-rich areas — no oil/ignition; high voltage.'], refs=['IOA guidance', 'WHO GDWQ'])

# ===================================================================== ion exchange
MODULES['demineralization_plant'] = mod(
    definition=('A two-bed demineralization (DM) plant removes dissolved salts by ion exchange. A strong-acid cation exchanger replaces Ca²⁺, Mg²⁺ and Na⁺ with H⁺; a degasser blows out the CO₂ formed from '
                'bicarbonate; a strong-base anion exchanger replaces Cl⁻, SO₄²⁻ and silica with OH⁻. H⁺ and OH⁻ combine to water, giving low-conductivity water for boilers and processes.'),
    applications=['Boiler feed make-up for medium/high-pressure boilers', 'Process water for chemicals, pharmaceuticals and power'],
    key_points=['Cation (H⁺) → degasser → anion (OH⁻)', 'Degasser saves anion capacity', 'Regenerate with acid and caustic', 'Monitor conductivity, silica, sodium slip'],
    principle=[step('Filtered water enters the cation exchanger.', 'cation', overlay='flow'), step('Cation resin captures metal ions and releases H⁺.', 'cation_resin', overlay='pressure'),
               step('The degasser strips CO₂.', 'degasser'), step('The anion resin captures anions and releases OH⁻.', 'anion_resin', overlay='pressure'),
               step('Acid and caustic regenerate the beds when exhausted.', 'regenerant_tanks')],
    curve='Outlet conductivity vs throughput — flat then rising at exhaustion.',
    params=wu(P('Vessels ≈ 0.5 – 4 m diameter'), P('≈ 5 – 500', 'm³/h'), P('Outlet < ≈ 5 – 10 µS/cm; silica < ≈ 0.1 mg/L', '—'), P('Pumps/blower ≈ 5 – 100', 'kW')),
    install=_IX, maint=_m([M('Log throughput, conductivity and silica.', 'piping', 'daily')], [M('Resin sample and capacity test.', 'cation_resin', 'annually')], [M('Inspect laterals/distributors; top up resin.', 'cation_internals')], _NL),
    failures=[F('Early exhaustion', ['Short runs'], ['Resin fouling', 'Poor regeneration'], ['Clean resin; check regenerant dose/concentration'], 'anion_resin'),
              F('Silica slip', ['High silica'], ['Anion exhausted, warm caustic not used'], ['Regenerate; use warm caustic'], 'anion_resin')],
    quiz=[Q('Which unit removes CO₂?', ['Degasser', 'Cation', 'Anion', 'Acid tank'], 0, 'Degasser.'), Q('What regenerates the cation resin?', ['Acid', 'Caustic', 'Brine', 'Water'], 0, 'Acid.'),
          Q('Why use a degasser?', ['Removes CO₂ cheaply, reducing anion load', 'Adds oxygen', 'Heats water', 'Filters solids'], 0, 'Saves anion capacity.')],
    selection=['From water analysis, flow and run length; consider RO + mixed bed for high TDS.'], safety=['Acid and caustic: PPE, safety showers, bunded storage; hydrogen release from some regenerations — ventilate.'], refs=['Ion exchange manuals (DuPont/Purolite)'])

MODULES['mixed_bed_polisher'] = mod(
    definition=('A mixed-bed polisher contains cation and anion resins mixed intimately in one vessel. The water meets H⁺ and OH⁻ sites alternately thousands of times, like many two-bed units in series, giving '
                'very pure water. To regenerate, the resins are separated by backwashing, regenerated separately with acid and caustic, and re-mixed with air.'),
    applications=['Polishing after RO or two-bed DM for high-pressure boilers', 'Electronics, pharmaceutical and laboratory water'],
    key_points=['Conductivity < ≈ 0.1 µS/cm', 'Separation by backwash (anion lighter)', 'Air mixing after regeneration', 'Interface collector between layers'],
    principle=[step('Pre-treated water enters at the top.', 'mb', overlay='flow'), step('Mixed resins remove the remaining ions.', 'mixed_resin', overlay='pressure'),
               step('For regeneration, backwash separates the resins.', 'mixed_resin'), step('Acid and caustic regenerate each layer; air re-mixes.', 'instruments_air')],
    curve='Outlet conductivity vs throughput.',
    params=wu(P('Vessels ≈ 0.5 – 3 m diameter'), P('≈ 5 – 300', 'm³/h'), P('Outlet ≈ 0.06 – 0.1 µS/cm; silica ≈ 10 – 20 µg/L', '—'), P('≈ 1 – 20', 'kW')),
    install=_IX, maint=_m([M('Check outlet conductivity and silica.', 'instruments_air', 'daily')], [M('Resin analysis.', 'mixed_resin', 'annually')], [M('Inspect interface collector and laterals.', 'mb_internals')], _NL),
    failures=[F('Poor separation', ['Short runs, poor quality'], ['Resin cross-contamination'], ['Improve backwash; resin replacement'], 'mixed_resin'), F('Resin loss', ['Resin downstream'], ['Broken nozzle'], ['Repair underdrain'], 'mb_internals')],
    quiz=[Q('Why is mixed-bed water so pure?', ['Water meets alternating H⁺/OH⁻ sites many times', 'It is boiled', 'Chlorine is added', 'It is filtered'], 0, 'Many stages.'),
          Q('How are resins separated?', ['Backwash — different densities', 'By magnet', 'By hand', 'By acid'], 0, 'Backwash.'), Q('How are they re-mixed?', ['Air', 'Paddles', 'Pumps', 'Not at all'], 0, 'Air.')],
    selection=['Use downstream of RO/two-bed; size by flow and ionic load.'], safety=['Acid/caustic handling; pressure vessel rules.'], refs=['Ion exchange manuals'])

MODULES['water_softener'] = mod(
    definition=('A water softener removes hardness (calcium and magnesium) by exchanging them for sodium on cation resin. Twin vessels alternate: one softens while the other is regenerated with strong brine, '
                'so soft water is always available for boilers, cooling and washing.'),
    applications=['Low-pressure boiler feed and cooling make-up', 'Laundries, food plants and building services'],
    key_points=['Ca²⁺/Mg²⁺ ↔ Na⁺', 'Brine ≈ 10 % NaCl regenerates', 'Twin units = continuous supply', 'Does not remove dissolved solids (TDS)'],
    principle=[step('Hard water flows down through the resin.', 'softener_1', overlay='flow'), step('Resin captures Ca²⁺ and Mg²⁺ and releases Na⁺.', 'softener_1_resin', overlay='pressure'),
               step('The control valve switches units at exhaustion.', 'control_valves'), step('Brine from the brine tank regenerates the exhausted unit.', 'brine_tank', overlay='flow')],
    curve='Outlet hardness vs throughput.',
    params=wu(P('Vessels ≈ 0.3 – 3 m diameter'), P('≈ 1 – 200', 'm³/h'), P('Outlet hardness < ≈ 1 mg/L as CaCO₃; salt ≈ 100 – 250 g per L resin', '—'), P('≈ 0.1 – 5', 'kW')),
    install=_IX, maint=_m([M('Test hardness and salt level.', 'brine_tank', 'daily')], [M('Clean brine tank; check injector.', 'brine_line', 'quarterly')], [M('Resin replacement as capacity falls.', 'softener_1_resin')], _NL),
    failures=[F('Hardness leakage', ['Scale downstream'], ['No salt, brine bridging, valve fault'], ['Refill salt, break bridge, repair valve'], 'brine'),
              F('Resin fouling by iron', ['Short runs'], ['Iron in feed'], ['Iron removal; resin cleaner'], 'softener_1_resin')],
    quiz=[Q('What ions are removed?', ['Calcium and magnesium', 'Chloride', 'Silica', 'Oxygen'], 0, 'Hardness.'), Q('What regenerates the resin?', ['Brine (NaCl)', 'Acid', 'Caustic', 'Air'], 0, 'Brine.'),
          Q('Does softening reduce TDS?', ['No — it exchanges ions', 'Yes, to zero', 'Yes, halves it', 'Only at night'], 0, 'No.')],
    selection=['Resin volume from flow, hardness and run length; brine system to match.'], safety=['Salt handling; pressure vessels.'], refs=['NSF/ANSI 44', 'Ion exchange manuals'])

MODULES['degasser_tower'] = mod(
    definition=('A forced-draught degasser (decarbonator) removes dissolved CO₂ from water, usually after a cation exchanger. Water is spread over packing and trickles down while a blower sends air up; the CO₂ '
                'moves from the water into the air (which contains almost none) and is vented. Degassed water collects in the sump below.'),
    applications=['Between cation and anion units in DM plants', 'After acid dosing ahead of RO; groundwater CO₂/H₂S stripping'],
    key_points=['Henry\'s law: gas leaves water when air has little of it', 'Counter-current air and water', 'Packing gives surface area', 'Outlet CO₂ ≈ 5 mg/L'],
    principle=[step('Water is distributed over the packing.', 'distributor_eliminator', overlay='flow'), step('It trickles down over the packing surface.', 'packing', overlay='pressure'),
               step('The blower sends air up the tower.', 'blower', overlay='flow'), step('CO₂-laden air leaves through the vent.', 'nozzles'), step('Degassed water collects in the sump.', 'sump')],
    curve='Outlet CO₂ vs air-to-water ratio.',
    params=wu(P('Towers ≈ 0.5 – 3 m diameter'), P('≈ 5 – 500', 'm³/h'), P('Air/water ≈ 20 – 40 m³/m³; outlet CO₂ ≈ 5 mg/L', '—'), P('Blower ≈ 1 – 30', 'kW')),
    install=_IX, maint=_m([M('Check blower and sump level.', 'blower', 'daily')], [M('Inspect distributor and packing.', 'packing', 'annually')], [M('Replace packing if fouled.', 'packing')], _LUBE),
    failures=[F('High CO₂ outlet', ['Anion runs short'], ['Blower failure, channelling'], ['Repair blower; clean distributor'], 'blower'), F('Packing fouling', ['High ΔP'], ['Biological growth'], ['Clean/replace'], 'packing')],
    quiz=[Q('What gas does it remove?', ['CO₂', 'O₂', 'N₂', 'H₂'], 0, 'CO₂.'), Q('Why counter-current?', ['Maximises driving force', 'Saves paint', 'Heats water', 'No reason'], 0, 'Driving force.'),
          Q('What benefit for the DM plant?', ['Lower load on the anion unit', 'Higher pH only', 'More silica', 'Less water'], 0, 'Anion load.')],
    selection=['Size by flow, CO₂ in/out and packing transfer data.'], safety=['Vent gases outside; acidic water — corrosion-resistant materials.'], refs=['Ion exchange manuals'])

# ===================================================================== chemical systems
MODULES['chemical_preparation_tank'] = mod(
    definition=('A chemical preparation (make-down) tank makes solutions such as polymer, lime milk or coagulant from dry powder and water. A screw feeder doses powder in proportion to the dilution water, '
                'an agitator wets and dissolves it, and the solution is held for ageing before the dosing pumps take it.'),
    applications=['Polymer make-down for clarifiers and sludge dewatering', 'Lime, soda ash and coagulant preparation'],
    key_points=['Even wetting avoids lumps (fish-eyes)', 'Feeder proportional to water', 'Polymer needs ageing ≈ 30–60 min', 'Strength ≈ 0.1–0.5 % polymer; 5–10 % lime'],
    principle=[step('Dry chemical is loaded into the hopper.', 'powder_feeder'), step('The screw feeder doses it into the tank.', 'powder_feeder', overlay='flow'),
               step('Dilution water is metered in.', 'water_instruments', overlay='flow'), step('The agitator dissolves and ages the solution.', 'cp_agitator', overlay='pressure'),
               step('Solution goes to the dosing pumps.', 'water_instruments', overlay='flow')],
    curve='Polymer viscosity vs ageing time.',
    params=wu(P('Tanks ≈ 0.5 – 20 m³'), P('≈ 1 – 100', 'kg/h powder'), P('Ambient; concentration per chemical', '—'), P('≈ 0.5 – 10', 'kW')),
    install=_SKID, maint=_m([M('Check hopper level and feeder calibration.', 'powder_feeder', 'daily')], [M('Clean tank of lumps and deposits.', 'cp_tank', 'monthly')], [M('Overhaul agitator gearbox.', 'cp_drive')], _LUBE),
    failures=[F('Fish-eyes / lumps', ['Blocked dosing pumps'], ['Poor wetting'], ['Use wetting cone/eductor; adjust feed'], 'powder_feeder'), F('Feeder bridging', ['No powder flow'], ['Damp powder'], ['Keep dry; vibrator'], 'powder_feeder')],
    quiz=[Q('Why age polymer?', ['Chains uncoil and become active', 'To cool it', 'To add colour', 'No reason'], 0, 'Uncoil.'), Q('What doses the powder?', ['Screw feeder', 'Agitator', 'Pump', 'Valve'], 0, 'Feeder.'),
          Q('What causes fish-eyes?', ['Poor wetting of powder', 'Too much water', 'High pH', 'Cold'], 0, 'Wetting.')],
    selection=['Tank size by consumption × ageing time; feeder by kg/h.'], safety=['Dust: extraction and masks; polymer spills are very slippery; lime is caustic.'], refs=['Maker manuals'])

MODULES['chemical_injection_skid'] = mod(
    definition=('A chemical injection skid doses a precise flow of chemical into a process line. Diaphragm metering pumps (duty/standby) draw from a day tank and deliver through a pulsation dampener, '
                'relief valve and back-pressure valve to an injection quill that places the chemical in the centre of the pipe.'),
    applications=['Biocide, inhibitor, coagulant, pH and oxygen-scavenger dosing', 'Oil & gas chemical injection (corrosion inhibitor, methanol)'],
    key_points=['Fixed volume per stroke (API 675)', 'Flow = stroke length × frequency', 'Back-pressure valve keeps accuracy', 'Calibration column verifies output'],
    principle=[step('Chemical is stored in the day tank.', 'storage_tank'), step('The diaphragm pump draws and delivers fixed volumes.', 'diaphragm_1', overlay='pressure'),
               step('Dampener smooths pulses; BPV holds pressure.', 'accessories', overlay='flow'), step('The quill injects into the process main.', 'piping_quill', overlay='flow')],
    curve='Delivered flow vs stroke length (linear).',
    params=wu(P('Pumps ≈ 0.1 – 1000 L/h'), P('≈ 0.1 – 1000', 'L/h'), P('Discharge up to ≈ 10 – 300 bar (application)', '—'), P('≈ 0.1 – 5', 'kW')),
    install=_SKID, maint=_m([M('Check tank level and draw-down calibration.', 'accessories', 'weekly')], [M('Clean check valves and strainers.', 'metering_pump_1', 'quarterly')], [M('Replace diaphragm and valves.', 'diaphragm_1')], _LUBE),
    failures=[F('Loss of prime', ['No flow'], ['Air/gas in suction, dirty valves'], ['Prime, clean valves'], 'metering_pump_1'), F('Diaphragm rupture', ['Leak detection alarm'], ['Fatigue, overpressure'], ['Replace; check PSV'], 'diaphragm_1')],
    quiz=[Q('How is flow adjusted?', ['Stroke length and frequency', 'Valve throttling only', 'Tank size', 'Pipe colour'], 0, 'Stroke.'), Q('Why a back-pressure valve?', ['Keeps metering accurate', 'Heats chemical', 'Filters', 'Mixes'], 0, 'Accuracy.'),
          Q('What does the calibration column do?', ['Measures actual pump output', 'Stores spare chemical', 'Vents gas', 'Cools pump'], 0, 'Calibration.')],
    selection=['Size for max dose × max flow with margin; materials compatible with chemical.'], safety=['Bunds, PPE, safety shower; relief valve on every PD pump discharge.'], refs=['API 675'])

# ===================================================================== compressed air & gases
MODULES['instrument_air_dryer'] = mod(
    definition=('An instrument air dryer removes water vapour from compressed air so control valves, positioners and instruments never see condensation, corrosion or ice. This twin-tower heated blower-purge '
                'type dries air in one desiccant tower while the other is regenerated by ambient air from a blower, heated to ≈ 150–200 °C and passed counter-flow through the wet bed; little or no dried '
                'compressed air is spent on purging.'),
    applications=['Instrument air for refineries, chemical, power and alumina plants', 'Dry air for pneumatic conveying, blanketing and outdoor lines in cold climates'],
    key_points=['Pressure dew point ≈ −40 °C (ISO 8573-1 class 2)', 'Adsorption at pressure, regeneration by heat', 'Counter-current regeneration keeps outlet end driest', 'Dew-point dependent switching saves energy'],
    principle=[step('Wet air passes the coalescing pre-filter.', 'filters', overlay='flow'), step('It flows up through the drying tower; desiccant adsorbs water.', 'desiccant_a', overlay='flow'),
               step('The moisture front rises through the bed.', 'moisture_front'), step('Blower and heater regenerate the other tower counter-flow.', 'regeneration_system', overlay='temperature'),
               step('Dry air leaves through the after-filter; valves switch towers.', 'switching_valves', overlay='flow')],
    curve='Outlet dew point vs time through a cycle.',
    params=wu(P('Towers ≈ 0.2 – 1.5 m diameter'), P('≈ 100 – 20,000', 'Nm³/h'), P('≈ 4 – 10 bar(g); inlet ≤ ≈ 40 °C; PDP ≈ −40 °C', '—'), P('Heater + blower ≈ 2 – 150', 'kW')),
    install=_PV, maint=_m([M('Check dew point, ΔP and drains.', 'controls', 'daily')], [M('Change filter elements; test switching valves.', 'filters', 'quarterly')],
                          [M('Replace desiccant (≈ 3 – 5 years); service blower and heater.', 'desiccant_a')], _LUBE),
    failures=[F('Wet air downstream', ['Dew point rises, water in lines'], ['Oil-fouled desiccant', 'Heater failed', 'Leaking switching valve'], ['Replace desiccant; repair heater/valve; check pre-filter'], 'desiccant_a'),
              F('Desiccant dusting', ['After-filter ΔP rises'], ['Bed fluidisation by fast depressurisation'], ['Slow depressurisation; replace beads'], 'filters')],
    quiz=[Q('Typical instrument-air dew point?', ['≈ −40 °C pressure dew point', '≈ +20 °C', '≈ +3 °C', '≈ 100 °C'], 0, 'Class 2.'),
          Q('Why regenerate counter-flow?', ['Keeps the outlet end of the bed driest', 'Cheaper piping', 'Heats the air', 'No reason'], 0, 'Counter-flow.'),
          Q('Advantage over a heatless dryer?', ['Uses little dried compressed air for purge', 'No electricity', 'No desiccant', 'Higher dew point'], 0, 'Purge saving.')],
    selection=['Size at maximum flow, minimum pressure and maximum inlet temperature (correction factors); choose PDP to the lowest ambient.'],
    safety=['Pressure vessels; hot surfaces on heater/purge line; depressurise before maintenance.'], refs=['ISO 8573-1', 'ISA-7.0.01'])

MODULES['air_receiver_dryer_package'] = mod(
    definition=('An air receiver and refrigerated dryer package stores compressed air and conditions it for plant use. The receiver buffers demand, smooths compressor cycling and lets condensate settle; the '
                'refrigerated dryer pre-cools the air, chills it to about +3 °C so water condenses and drains, then re-heats it; filters remove oil aerosols and dust.'),
    applications=['General plant (service) air for tools and machines', 'Pre-drying ahead of desiccant instrument-air dryers'],
    key_points=['Receiver: storage + condensate separation', 'Refrigerated dryer PDP ≈ +3 °C', 'Air-to-air exchanger saves energy and prevents sweating', 'Zero-loss drains save air'],
    principle=[step('Compressed air enters the receiver low and leaves high.', 'receiver', overlay='flow'), step('Condensate collects and the auto-drain removes it.', 'condensate'),
               step('The air-to-air exchanger pre-cools the air.', 'heat_exchangers', overlay='temperature'), step('The evaporator chills it; the separator drains water.', 'refrigeration_circuit', overlay='flow'),
               step('Filters remove oil aerosols and particles.', 'filters', overlay='flow')],
    curve='Dryer capacity correction vs inlet temperature and pressure.',
    params=wu(P('Receivers ≈ 0.5 – 30 m³'), P('≈ 50 – 10,000', 'Nm³/h'), P('≈ 7 – 13 bar(g); PDP ≈ +3 °C', '—'), P('Dryer ≈ 0.5 – 50', 'kW')),
    install=_PV, maint=_m([M('Check drains and dryer dew point/temperature.', 'receiver_fittings', 'daily')], [M('Clean condenser; change filters.', 'refrigeration_circuit', 'quarterly')],
                          [M('Receiver internal inspection / thickness check.', 'receiver')], _LUBE),
    failures=[F('Water in air lines', ['Wet tools/instruments'], ['Drain stuck, dirty condenser, overloaded dryer'], ['Repair drain, clean condenser, check sizing'], 'heat_exchangers'),
              F('Receiver corrosion', ['Wall thinning'], ['Standing water'], ['Keep drains working; inspect'], 'receiver')],
    quiz=[Q('Why does air enter the receiver low and leave high?', ['Lets water drop out before the outlet', 'For looks', 'Cheaper', 'To heat it'], 0, 'Separation.'),
          Q('Refrigerated dryer dew point?', ['≈ +3 °C', '≈ −70 °C', '≈ −40 °C', '≈ 50 °C'], 0, '+3 °C.'), Q('Why re-heat the air?', ['Saves energy and stops pipe sweating', 'Kills bacteria', 'Raises pressure', 'No reason'], 0, 'Re-heat.')],
    selection=['Receiver V ≈ t·Q·p₀/(p₁ − p₂) for a demand event; dryer by corrected flow.'], safety=['Statutory inspection of receivers; safety valve sized for full compressor flow.'], refs=['ISO 8573-1', 'CAGI'])

MODULES['nitrogen_generation_system'] = mod(
    definition=('A pressure-swing-adsorption (PSA) nitrogen generator makes nitrogen from compressed air. Two adsorbers filled with carbon molecular sieve take turns: at pressure the sieve takes up oxygen '
                'much faster than nitrogen, so nitrogen passes to a buffer vessel; the bed is then depressurised to release the oxygen and regenerate, while the other bed takes over.'),
    applications=['Inert blanketing and purging of tanks and vessels', 'Food packaging, laser cutting and instrument purge'],
    key_points=['Kinetic separation: O₂ diffuses faster into CMS', 'Cycle ≈ 60 s per bed', 'Purity ≈ 95 – 99.999 % (higher purity → lower yield)', 'Oxygen analyser and off-spec vent'],
    principle=[step('Clean, oil-free compressed air enters the active bed.', 'air_treatment', overlay='flow'), step('CMS adsorbs oxygen; the O₂ front advances.', 'oxygen_front', overlay='pressure'),
               step('Nitrogen passes to the buffer vessel.', 'nitrogen_buffer', overlay='flow'), step('The other bed vents O₂-rich gas and regenerates.', 'valve_manifold', overlay='flow'),
               step('The analyser checks purity before supply.', 'product_controls')],
    curve='Nitrogen yield vs purity (falls steeply above 99.9 %).',
    params=wu(P('Adsorbers ≈ 0.2 – 1.5 m diameter'), P('≈ 5 – 5000', 'Nm³/h N₂'), P('Feed ≈ 7 – 10 bar(g); purity ≈ 95 – 99.999 %', '—'), P('Mostly compressor power ≈ 0.25 – 0.5 kWh/Nm³', 'kWh/Nm³')),
    install=_PV, maint=_m([M('Check purity, pressure and cycle.', 'product_controls', 'daily')], [M('Change feed filters; calibrate analyser.', 'air_treatment', 'quarterly')], [M('Service valves; check CMS.', 'valve_manifold')], _NL),
    failures=[F('Purity drops', ['O₂ alarm'], ['Leaking valve, oil-poisoned CMS, overdraw'], ['Repair valve; replace CMS; reduce flow'], 'cms_a'), F('CMS dust', ['Filter blockage'], ['Bed movement'], ['Re-compact/replace'], 'cms_a')],
    quiz=[Q('Why does CMS separate O₂?', ['O₂ diffuses into the pores faster than N₂', 'O₂ is heavier', 'Magnetism', 'Temperature'], 0, 'Kinetics.'),
          Q('What happens if more purity is demanded?', ['Yield falls (more air per Nm³ N₂)', 'Yield rises', 'No change', 'Pressure drops to zero'], 0, 'Trade-off.'),
          Q('Biggest hazard of nitrogen?', ['Asphyxiation (no smell, no warning)', 'Explosion', 'Toxicity', 'Fire'], 0, 'Asphyxiation.')],
    selection=['Size by flow and purity; air demand from maker curves.'], safety=['O₂-deficiency monitors in enclosed spaces; vent O₂-rich exhaust safely.'], refs=['EIGA / CGA guidance'])

MODULES['nitrogen_storage_vessel'] = mod(
    definition=('A liquid nitrogen storage vessel keeps nitrogen as a liquid at about −196 °C in a stainless inner vessel surrounded by a perlite-filled, high-vacuum annulus inside a carbon-steel outer vessel. '
                'A pressure-building coil keeps tank pressure, and an ambient-air vaporiser turns withdrawn liquid into gas for the plant; a final regulator sets supply pressure.'),
    applications=['Back-up and peak supply of nitrogen for plant inerting', 'Cryogenic cooling, food freezing and laboratories'],
    key_points=['Boils at −196 °C (77 K)', '1 L liquid → ≈ 0.69 Nm³ gas', 'Vacuum insulation keeps boil-off low', 'Relief on every section that can trap liquid'],
    principle=[step('Liquid is stored in the inner vessel.', 'liquid_nitrogen', overlay='temperature'), step('The vacuum/perlite annulus limits heat leak.', 'annulus_insulation'),
               step('The pressure builder vaporises a little liquid to hold pressure.', 'pressure_builder', overlay='flow'), step('Withdrawn liquid warms in the ambient vaporiser.', 'ambient_vaporiser', overlay='flow'),
               step('Relief valves and gauges protect and monitor the tank.', 'safety_instruments')],
    curve='Vaporiser outlet temperature vs flow and running time (icing).',
    params=wu(P('Tanks ≈ 3 – 100 m³'), P('≈ 2,000 – 70,000', 'Nm³ stored'), P('≈ 2 – 17 bar; −196 °C liquid', '—'), P('Passive (ambient vaporiser)', '—')),
    install=_PV, maint=_m([M('Read level and pressure.', 'safety_instruments', 'daily')], [M('Check frost on shell (vacuum) and vaporiser icing.', 'outer_vessel', 'monthly')], [M('Test/replace relief valves.', 'safety_instruments')], _NL),
    failures=[F('High boil-off', ['Pressure rises, venting'], ['Vacuum loss'], ['Re-evacuate annulus (specialist)'], 'annulus_insulation'),
              F('Cold gas downstream', ['Frost on pipe, brittle failure risk'], ['Over-drawn/iced vaporiser'], ['Reduce flow; switch/defrost bank; low-temperature shut-off'], 'ambient_vaporiser')],
    quiz=[Q('Boiling point of nitrogen at 1 atm?', ['−196 °C', '−78 °C', '0 °C', '−40 °C'], 0, '77 K.'), Q('What keeps tank pressure?', ['Pressure-building coil', 'A compressor', 'A pump', 'The sun'], 0, 'PBC.'),
          Q('Why relief on liquid lines?', ['Trapped liquid warms and expands enormously', 'For flow', 'For colour', 'Not needed'], 0, 'Overpressure.')],
    selection=['Size for consumption × days of autonomy; vaporiser for peak flow and climate.'], safety=['Cryogenic burns — face shield, gloves; asphyxiation in enclosed areas; no carbon steel in cold service.'], refs=['EIGA Doc 115', 'EN 13458'])

# ===================================================================== steam utilities
MODULES['steam_distribution_header'] = mod(
    definition=('A steam distribution header receives steam from the boilers and distributes it to the plant. Branches leave from the top so they take dry steam; the header slopes to drip legs where steam traps '
                'remove condensate; a pressure-reducing station supplies lower-pressure users. Insulation, supports and guides handle heat loss and thermal expansion.'),
    applications=['Boiler house main steam headers', 'Plant steam distribution to process heaters, turbines and tracing'],
    key_points=['Take branches from the top', 'Drip legs every ≈ 30–50 m and at low points', 'Slope ≈ 1:100 toward drip legs', 'PRV + downstream safety valve'],
    principle=[step('Steam enters through the main stop valve.', 'main_valve', overlay='flow'), step('The header distributes steam; condensate runs along the bottom.', 'header', overlay='pressure'),
               step('Branches take dry steam from the top.', 'branch_takeoffs', overlay='flow'), step('The drip leg and trap remove condensate.', 'trap_station', overlay='flow'),
               step('The PRV station reduces pressure for LP users.', 'prv_station', overlay='pressure')],
    curve='Steam velocity and pressure drop vs flow and pipe size.',
    params=wu(P('Headers DN 100 – 600'), P('≈ 1 – 300', 't/h steam'), P('≈ 3 – 100 bar(g); saturated or superheated', '—'), P('— (static)', '—')),
    install=_PV, maint=_m([M('Check pressures and trap discharge.', 'trap_station', 'daily')], [M('Trap survey; inspect insulation.', 'trap_station', 'quarterly')], [M('Overhaul PRV and safety valves.', 'prv_station')], _NL),
    failures=[F('Water hammer', ['Bangs, pipe movement'], ['Failed trap, no drip leg, wrong slope'], ['Repair traps; add drip legs; warm up slowly'], 'trap_station'),
              F('Steam loss through trap', ['Live steam at discharge'], ['Trap failed open'], ['Replace trap'], 'trap_station')],
    quiz=[Q('Why take branches from the top?', ['To get dry steam, not condensate', 'For looks', 'Cheaper', 'To avoid air'], 0, 'Dry steam.'),
          Q('What causes water hammer?', ['Slugs of condensate driven by steam', 'Too much insulation', 'Superheat', 'Air'], 0, 'Condensate slugs.'),
          Q('What protects the LP side after a PRV?', ['A safety valve', 'A trap', 'A strainer', 'Insulation'], 0, 'Safety valve.')],
    selection=['Size for velocity ≈ 25–40 m/s (saturated) and allowable pressure drop.'], safety=['Hot surfaces; isolate and depressurise before work; never open a hot drain into a closed space.'], refs=['ASME B31.1', 'Spirax Sarco'])

MODULES['condensate_recovery_system'] = mod(
    definition=('A condensate recovery system returns hot condensate from steam users to the boiler. High-pressure condensate enters a flash vessel, where part of it flashes to low-pressure steam that is reused; '
                'the remaining condensate drains to a vented receiver, and duty/standby pumps return it to the boiler feed tank when the level switch calls.'),
    applications=['Process plants and boiler houses', 'Heat-exchanger and tracer condensate collection'],
    key_points=['Flash fraction = (h_f,HP − h_f,LP)/h_fg,LP', 'Saves fuel, water and chemicals', 'Receiver raised for pump NPSH', 'Vented receiver at atmospheric pressure'],
    principle=[step('HP condensate enters the flash vessel.', 'flash_vessel', overlay='flow'), step('Flash steam leaves the top to the LP header.', 'flash_vessel', overlay='pressure'),
               step('Condensate drains to the vented receiver.', 'receiver', overlay='flow'), step('The float starts a pump at high level.', 'level_float'), step('The pump returns condensate to the boiler.', 'pump_piping', overlay='flow')],
    curve='Flash fraction vs pressure drop.',
    params=wu(P('Receivers ≈ 0.2 – 10 m³'), P('≈ 0.5 – 100', 't/h condensate'), P('≈ 90 – 100 °C; atmospheric receiver', '—'), P('Pumps ≈ 1 – 30', 'kW')),
    install=_PV, maint=_m([M('Check level, pump cycling and vent.', 'level_float', 'daily')], [M('Inspect pump seals and check valves.', 'pump_1', 'quarterly')], [M('Inspect receiver internally.', 'receiver')], _LUBE),
    failures=[F('Pump cavitation', ['Noise, low flow'], ['Low NPSH (hot condensate, low head)'], ['Raise receiver; cool condensate; NPSH-suitable pump'], 'pump_1'),
              F('Receiver overflow', ['Hot water at overflow'], ['Pump/float failure'], ['Repair; check alarms'], 'level_float')],
    quiz=[Q('What is flash steam?', ['Steam formed when hot condensate drops in pressure', 'Boiler steam', 'Superheated steam', 'Steam from a leak only'], 0, 'Flash.'),
          Q('Why raise the receiver?', ['NPSH for pumps handling near-boiling water', 'For looks', 'Easier painting', 'Less steam'], 0, 'NPSH.'),
          Q('Benefits of returning condensate?', ['Fuel, water and chemical savings', 'More blowdown', 'Lower boiler efficiency', 'None'], 0, 'Savings.')],
    selection=['Size flash vessel for steam velocity; receiver for pump cycling; pumps for NPSH.'], safety=['Hot water and flash steam — vent to safe location; burns.'], refs=['Spirax Sarco', 'ASME B31.1'])

# ===================================================================== cooling utilities
MODULES['cooling_tower_basin'] = mod(
    definition=('The cold-water basin collects water falling from a cooling tower\'s fill and supplies the circulating-water pumps through a sump and screens. Make-up water replaces evaporation, drift and '
                'blowdown; blowdown limits the build-up of dissolved solids; an overflow protects the tower; chemical dosing points add inhibitor and biocide.'),
    applications=['Process and power-plant cooling-water systems', 'HVAC chiller condenser water'],
    key_points=['Make-up = evaporation + drift + blowdown', 'Cycles of concentration ≈ 3 – 6', 'Evaporation ≈ 0.15 % of flow per °C range', 'Sump depth gives pump submergence'],
    principle=[step('Hot water is sprayed over the fill.', 'hot_water_distribution', overlay='flow'), step('Air and water exchange heat in the fill and rain zone.', 'fill_eliminators', overlay='temperature'),
               step('Cooled water collects in the basin.', 'water', overlay='temperature'), step('Screens protect the pumps at the sump.', 'sump_screens', overlay='flow'),
               step('The float valve adds make-up; blowdown limits concentration.', 'float_arm')],
    curve='Cold-water temperature vs wet-bulb temperature at constant range.',
    params=wu(P('Basins ≈ 5 – 100 m per cell side; depth ≈ 0.5 – 2 m'), P('≈ 100 – 50,000', 'm³/h circulation'), P('Cold water ≈ 25 – 32 °C; approach ≈ 3 – 5 °C', '—'), P('— (static; pumps separate)', '—')),
    install=_BASIN, maint=_m([M('Check level, conductivity and chemical dosing.', 'outlets_blowdown', 'daily')], [M('Clean screens; check make-up valve.', 'sump_screens', 'weekly')],
                             [M('Drain and clean silt; repair concrete; inspect fill.', 'basin')], _NL),
    failures=[F('Scaling', ['Deposits on exchangers'], ['Too many cycles, no blowdown'], ['Increase blowdown; inhibitor'], 'outlets_blowdown'),
              F('Biological growth / Legionella risk', ['Slime, high counts'], ['Poor biocide control'], ['Biocide programme; cleaning; risk assessment'], 'water')],
    quiz=[Q('Make-up water equals…', ['Evaporation + drift + blowdown', 'Evaporation only', 'Flow rate', 'Zero'], 0, 'Balance.'), Q('Why blowdown?', ['Limit dissolved-solids concentration', 'Cool water', 'Add oxygen', 'Lower level'], 0, 'Concentration.'),
          Q('What protects the pumps?', ['Sump screens', 'Louvres', 'Fill', 'Fan'], 0, 'Screens.')],
    selection=['Basin storage for system volume and pump submergence; sump to HI 9.8.'], safety=['Legionella control; confined space in sumps; slippery surfaces.'], refs=['CTI', 'HI 9.8'])

MODULES['cooling_tower_fan'] = mod(
    definition=('A cooling tower fan is a large, slow axial fan that draws air through an induced-draught tower. It runs inside a flared fan stack that recovers velocity pressure, and is driven by a motor '
                'outside the humid air through a drive shaft and a right-angle gearbox.'),
    applications=['Induced-draught counterflow and crossflow cooling towers', 'Air-cooled heat exchangers (similar fans)'],
    key_points=['Large diameter, low speed (tip ≲ 60 m/s)', 'Adjustable-pitch blades set load', 'Stack recovers velocity pressure', 'Vibration switch trips on imbalance'],
    principle=[step('The motor drives the shaft from outside the stack.', 'motor', overlay='flow'), step('The gearbox turns the drive 90° and reduces speed.', 'gearbox'),
               step('The fan draws air up through fill.', 'fan_rotor', overlay='flow'), step('The stack recovers pressure as air leaves.', 'fan_deck_stack', overlay='pressure')],
    curve='Fan static pressure and power vs airflow for different blade pitches.',
    params=wu(P('Fan diameter ≈ 2 – 15 m'), P('≈ 50 – 2000', 'm³/s air'), P('Static pressure ≈ 100 – 250 Pa; ≈ 60 – 300 rpm', '—'), P('≈ 5 – 250', 'kW')),
    install=_ROT, maint=_m([M('Check vibration and unusual noise.', 'gearbox', 'daily')], [M('Check blade pitch, tip clearance and bolts.', 'fan_rotor', 'quarterly')], [M('Rebalance; replace blades/couplings.', 'drive_shaft')], _LUBE),
    failures=[F('High vibration', ['Vibration trip'], ['Blade imbalance, ice, loose bolts'], ['Inspect, rebalance, re-torque'], 'fan_rotor'), F('Coupling failure', ['Shaft not turning'], ['Misalignment'], ['Replace, realign'], 'drive_shaft')],
    quiz=[Q('Why is the motor outside the stack?', ['Keeps it out of hot, humid air', 'For looks', 'Shorter cable', 'Less noise only'], 0, 'Environment.'),
          Q('What does the flared stack do?', ['Recovers velocity pressure', 'Adds water', 'Heats air', 'Holds oil'], 0, 'Velocity recovery.'), Q('How is fan load adjusted?', ['Blade pitch (or VFD)', 'Stack height', 'Oil', 'Valves'], 0, 'Pitch.')],
    selection=['Select for air flow and static pressure at design; check noise and tip speed.'], safety=['Lock out before deck entry; vibration cut-out; guard couplings.'], refs=['CTI'])

MODULES['cooling_tower_gearbox'] = mod(
    definition=('A cooling tower gearbox is a right-angle reducer between the motor drive shaft and the fan. A spiral-bevel gear set turns the drive through 90° and a helical stage completes about a 10:1 '
                'reduction to the vertical output shaft, which carries the fan hub and its thrust. Gears dip in an oil bath that splash-lubricates the bearings.'),
    applications=['Cooling tower fans', 'Air-cooled condenser and large agitator drives (similar right-angle reducers)'],
    key_points=['Speed down, torque up', 'Spiral-bevel 90° stage + helical stage', 'Service factor ≥ ≈ 2.0 for CT duty', 'Remote oil gauge and fill outside the stack'],
    principle=[step('Input shaft and pinion turn at motor speed.', 'input_pinion', overlay='flow'), step('The bevel gear turns the drive 90°.', 'intermediate_shaft', overlay='pressure'),
               step('The helical stage reduces speed further.', 'output_shaft'), step('Gears dip in oil that splashes onto bearings.', 'oil_bath'), step('The output shaft carries the fan.', 'output_shaft', overlay='flow')],
    curve='Gearbox efficiency vs load; oil temperature vs ambient.',
    params=wu(P('Housing ≈ 0.4 – 2 m'), P('Ratio ≈ 5 – 20 : 1', '—'), P('Input ≈ 1000 – 1800 rpm; output ≈ 60 – 300 rpm', '—'), P('≈ 5 – 250', 'kW')),
    install=_ROT, maint=_m([M('Check remote oil level and vibration.', 'accessories', 'daily')], [M('Oil analysis (water!).', 'oil_bath', 'quarterly')], [M('Inspect gear contact; replace bearings/seals.', 'bearings')], _LUBE),
    failures=[F('Water in oil', ['Milky oil, rust'], ['Breather/seal failure'], ['Change oil; fix breather/seal'], 'oil_bath'), F('Bearing failure', ['Noise, heat, vibration'], ['Low oil, contamination'], ['Replace; root cause'], 'bearings')],
    quiz=[Q('Why a bevel stage?', ['To turn the drive through 90°', 'To increase speed', 'For cooling', 'For oil'], 0, '90°.'), Q('Output torque relative to input?', ['≈ ratio × input × efficiency', 'Same', 'Lower', 'Zero'], 0, 'Torque up.'),
          Q('Main oil contaminant risk?', ['Water from humid air', 'Sand only', 'Steam', 'None'], 0, 'Water.')],
    selection=['Select for motor power × service factor, ratio, fan thrust.'], safety=['Lock out drive; hot oil; access platforms.'], refs=['CTI STD-111', 'AGMA'])

# ===================================================================== fire protection & wastewater
MODULES['emergency_diesel_firewater_system'] = mod(
    definition=('An emergency diesel firewater system is a fire pump driven by a dedicated diesel engine so firefighting water is available even if electrical power fails. The listed controller starts it '
                'automatically when fire-main pressure falls; it delivers rated flow at rated pressure to hydrants, monitors and sprinklers. A jockey pump keeps the main pressurised.'),
    applications=['Refinery, chemical, power and alumina plant fire mains', 'Large buildings and tank farms'],
    key_points=['Independent of electrical supply', '150 % of rated flow at ≥ 65 % of rated pressure (NFPA 20 style)', 'Two battery sets; weekly run test', 'Jockey pump for leakage make-up'],
    principle=[step('Pressure drops when a hydrant or sprinkler opens.', 'controller_batteries'), step('The controller starts the diesel engine.', 'diesel_engine'),
               step('The engine drives the split-case pump.', 'drive_train', overlay='flow'), step('The impeller raises pressure.', 'impeller', overlay='pressure'),
               step('Water goes to the fire main; the relief valve limits pressure.', 'discharge_piping', overlay='flow')],
    curve='Fire-pump curve: rated point, 150 % point and churn pressure.',
    params=wu(P('Pumps ≈ 100 – 5000 gpm (≈ 25 – 1100 m³/h)'), P('≈ 25 – 1100', 'm³/h'), P('≈ 7 – 15 bar rated', '—'), P('Engine ≈ 30 – 600', 'kW')),
    install=_SKID, maint=_m([M('Weekly no-flow run; check batteries, fuel, oil, coolant.', 'diesel_engine', 'weekly')], [M('Annual flow test through the test header.', 'discharge_piping', 'annually')],
                            [M('Engine overhaul per hours; pump wear rings.', 'impeller')], _LUBE),
    failures=[F('Fails to start', ['Controller alarm'], ['Flat batteries, no fuel, starter fault'], ['Second battery set; fuel checks; maintenance'], 'controller_batteries'),
              F('Low pressure at rated flow', ['Test shows low curve'], ['Wear rings worn, suction problem'], ['Overhaul pump; check suction'], 'impeller')],
    quiz=[Q('Why diesel drive?', ['Works when electrical power fails', 'Cheaper fuel', 'Quieter', 'No maintenance'], 0, 'Independence.'), Q('What does the jockey pump do?', ['Keeps the main pressurised', 'Fights fires', 'Cools the engine', 'Fuels the engine'], 0, 'Pressure maintenance.'),
          Q('How is pump performance checked?', ['Flow test through the test header', 'By eye', 'By noise', 'Never'], 0, 'Flow test.')],
    selection=['Rated flow/pressure from fire-water demand study; listed equipment per governing code.'], safety=['Exhaust, hot surfaces, rotating parts; never leave in "off" without impairment procedure.'], refs=['NFPA 20', 'NFPA 25'])

MODULES['sewage_lift_station'] = mod(
    definition=('A sewage lift station collects sewage in a wet well and pumps it up into a rising main or higher sewer. Submersible non-clog pumps sit on duckfoot bends and can be lifted out on guide rails; '
                'floats or a level transmitter start and stop them; check and gate valves sit in a separate dry valve chamber.'),
    applications=['Municipal and plant sewage networks', 'Industrial site drainage and effluent transfer'],
    key_points=['Wet-well volume limits starts per hour', 'Duty/standby alternation', 'Non-clog impellers pass solids', 'Rising-main velocity ≈ 0.7–2.5 m/s'],
    principle=[step('Sewage flows in through the inlet screen.', 'inlet_screen', overlay='flow'), step('The level rises in the wet well.', 'sewage'),
               step('The duty pump starts on level.', 'level_controls'), step('The pump lifts sewage up the riser.', 'impeller_1', overlay='pressure'),
               step('Check and gate valves in the chamber lead to the rising main.', 'valves_rising_main', overlay='flow')],
    curve='System curve vs pump curve as the well level changes.',
    params=wu(P('Wet wells ≈ 1.5 – 6 m diameter'), P('≈ 10 – 2000', 'm³/h'), P('Static lift ≈ 3 – 30 m', '—'), P('≈ 2 – 300 per pump', 'kW')),
    install=_BASIN, maint=_m([M('Check run hours, alarms and basket.', 'inlet_screen', 'daily')], [M('Clean floats; check pump insulation and seal monitor.', 'level_controls', 'monthly')],
                             [M('Lift pumps; replace seals/wear parts.', 'pump_1')], _LUBE),
    failures=[F('Pump ragging', ['High current, low flow'], ['Wipes and rags'], ['Lift and clean; chopper pump/screen'], 'impeller_1'), F('High-level alarm', ['Flooding risk'], ['Pump failure, power cut'], ['Standby pump; generator; tanker'], 'level_controls')],
    quiz=[Q('Why limit pump starts per hour?', ['Motor overheating', 'Water quality', 'Smell', 'Paint'], 0, 'Motor.'), Q('How are pumps removed?', ['Lifted on guide rails without entering the well', 'Through the sewer', 'By draining', 'Never'], 0, 'Guide rails.'),
          Q('Main hazard entering a wet well?', ['H₂S / oxygen deficiency (confined space)', 'Noise', 'Cold', 'Light'], 0, 'Gas.')],
    selection=['Pumps for peak flow at duty head; wet-well volume V ≈ T·Q/4 for cycle time T.'], safety=['Confined space permits, gas testing; lock-out; vent odour.'], refs=['EN 752', 'HI 9.8', 'Metcalf & Eddy'])

MODULES['effluent_treatment_plant'] = mod(
    definition=('An effluent treatment plant (ETP) cleans industrial wastewater before discharge or reuse. Screening removes coarse solids, equalisation evens out flow and strength, neutralisation corrects pH, '
                'an activated-sludge aeration tank lets bacteria consume dissolved organic matter, and a secondary clarifier settles the biomass; most is returned (RAS) and the excess is wasted (WAS).'),
    applications=['Industrial effluents from food, chemical, textile, refinery and paper plants', 'Combined industrial/sanitary wastewater at sites'],
    key_points=['Primary → secondary treatment train', 'DO ≈ 1.5–2 mg/L; MLSS ≈ 2000–4000 mg/L', 'RAS keeps biomass; WAS removes growth', 'Typically > 90 % BOD removal'],
    principle=[step('Bar screen removes rags and debris.', 'bar_screen', overlay='flow'), step('Equalisation evens out flow and load.', 'equalisation_tank'),
               step('pH is corrected in the neutralisation tank.', 'ph_control'), step('Bacteria consume organics with air from the diffusers.', 'diffusers', overlay='pressure'),
               step('The clarifier settles sludge; clear effluent overflows.', 'sc_tank', overlay='flow')],
    curve='BOD removal vs sludge age (SRT) and F/M ratio.',
    params=wu(P('Plants ≈ 50 – 50,000 m³/d'), P('≈ 50 – 50,000', 'm³/day'), P('HRT ≈ 6 – 24 h (aeration); SRT ≈ 5 – 20 d', '—'), P('Mainly aeration ≈ 0.3 – 1 kWh/m³', 'kWh/m³')),
    install=_BASIN, maint=_m([M('Check DO, pH, MLSS, sludge blanket and effluent quality.', 'mixed_liquor', 'daily')], [M('Clean screens; check diffusers and blower.', 'blower', 'monthly')],
                             [M('Drain aeration tank; replace diffuser membranes.', 'diffusers')], _LUBE),
    failures=[F('Sludge bulking', ['Poor settling, turbid effluent'], ['Filamentous bacteria (low DO, low F/M, nutrients)'], ['Fix DO/nutrients; chlorinate RAS'], 'sc_mud'),
              F('Toxic shock', ['DO rises, treatment stops'], ['Toxic discharge'], ['Divert/hold in equalisation; reseed'], 'mixed_liquor')],
    quiz=[Q('What do the bacteria need from the diffusers?', ['Oxygen', 'Chlorine', 'Heat', 'Light'], 0, 'Oxygen.'), Q('What is RAS?', ['Returned activated sludge to keep the biomass', 'Raw sewage', 'Rain', 'Acid'], 0, 'RAS.'),
          Q('Why equalise?', ['Even out flow and strength for stable treatment', 'Add bacteria', 'Remove grit only', 'Cool water'], 0, 'Equalisation.')],
    selection=['From flow and load (BOD, COD, TSS, N, P), discharge limits and space.'], safety=['H₂S and confined spaces; biological hazards — hygiene; chemicals.'], refs=['Metcalf & Eddy'])
