"""Learning content — Thermal & Process Equipment, part A (EQ-228 … EQ-234, EQ-247 … EQ-252):
heat exchangers, boilers, heat recovery, fired equipment, gas cooling and cooling water."""
from pumpforge.learning import mod, step, P, F, Q, M

MODULES = {}


def tp(size, duty, temperature, capacity, **extra):
    """Required parameters for the thermal_process family: size, heat_duty, operating_temperature, capacity."""
    ref = {'manufacturer': None, 'model': None, 'datasheet': None,
           'rated_point': {'heat_duty_kW': None, 'flow_or_capacity': None, 'inlet_outlet_temperatures': None, 'design_pressure': None, 'fuel_or_heating_medium': None},
           'status': 'empty — fill from the equipment datasheet / thermal design (TEMA sheet, boiler data sheet)'}
    return dict(size=size, heat_duty=duty, operating_temperature=temperature, capacity=capacity, reference_model=ref, extra=extra)


def _maint(routine, periodic, overhaul, lub):
    return dict(routine=routine, periodic=periodic, overhaul=overhaul, lubrication=lub)


_HX_INST = dict(
    foundation=['Support on saddles or structure designed for the operating and full-of-water (hydro-test) weight; bolt one saddle and slot the other for thermal expansion.'],
    alignment=['Level the unit (or set the specified slope for drainage); leave tube-bundle pull-out space equal to the bundle length.'],
    piping=['Connect nozzles without forcing (check allowable nozzle loads); fit vents at high points and drains at low points on both sides.',
            'Steam-heated units: install a steam trap or level-controlled drain and a vacuum breaker so condensate cannot back up.'],
    commissioning=['Hydro-test both sides per code; vent air; introduce the cold fluid first, then the hot fluid gradually to avoid thermal shock.'])
_BOIL_INST = dict(
    foundation=['Level concrete plinth/foundation designed for operating weight full of water; allow access for tube cleaning and burner maintenance.'],
    alignment=['Level the boiler; align burner and fan; check expansion allowances on headers and casings.'],
    piping=['Fit safety valves with unobstructed discharge piped to a safe place; feedwater with check and isolation valves; blowdown to a blowdown vessel.',
            'Flue/stack sized for the draught required; explosion relief where specified.'],
    commissioning=['Boil-out/chemical clean; hydro-test; set and test safety valves; test low-water cut-outs and flame safeguard (purge, ignition, flame failure); tune combustion (O₂, CO).'])
_FIRED_INST = dict(
    foundation=['Foundations designed for heater weight and thermal growth; refractory dry-out schedule after installation.'],
    alignment=['Burner alignment so flames do not impinge on tubes; check tube supports allow expansion.'],
    piping=['Fuel gas train with double block and bleed, pressure regulation and safety shut-off valves per the burner management system.',
            'Process coil inlet/outlet with flow, pressure and temperature instruments; snuffing steam where required.'],
    commissioning=['Refractory dry-out (controlled heating curve); purge; light-off procedure; set excess air (O₂) and draught; verify tube-metal temperatures.'])
_HVAC_INST = dict(
    foundation=['Mount AHU/coil sections level on a plinth or frame so the drain pan drains fully.'],
    alignment=['Seal sections air-tight; install coils in the correct air-flow direction (counter-flow to water).'],
    piping=['Pipe with isolation valves, strainer, control valve and balancing valve; trap the condensate drain with a water seal deeper than the fan static pressure.'],
    commissioning=['Vent coils, check flow and ΔT, verify valve stroke and control; check that condensate drains; balance air flow.'])
_NOLUBE = ['No lubrication for the static parts — lubricate valve stems, rotating parts and drives per maker.']

# ===================================================================== exchangers
MODULES['reboiler'] = mod(
    definition=('A reboiler supplies heat to the bottom of a distillation column to boil part of the bottom liquid. The vapour produced rises up the column and drives the separation. '
                'In a kettle reboiler, the liquid floods a horizontal tube bundle inside an enlarged shell; steam or hot oil inside the tubes boils the liquid. Vapour leaves from the top; '
                'unvaporised liquid spills over a weir and leaves as bottom product.'),
    applications=['Distillation columns in refineries and chemical plants', 'Gas plants (amine regenerators, stabilisers)', 'Duties with wide boiling ranges or high vaporisation fraction'],
    key_points=['Kettle = pool boiling around a submerged bundle', 'Weir keeps the bundle covered', 'Enlarged shell gives vapour–liquid disengagement', 'Heat duty sets the column boil-up'],
    principle=[step('Bottom liquid from the column enters the kettle shell.', 'nozzles', overlay='flow'), step('Steam enters the channel and condenses inside the U-tubes.', 'channel_head', overlay='flow'),
               step('The submerged tube bundle boils the liquid; vapour bubbles rise.', 'tube_bundle'), step('The weir keeps the bundle flooded; overflow liquid leaves as product.', 'weir'),
               step('Vapour returns to the column through the top nozzles.', 'shell', overlay='flow')],
    curve='Boiling heat flux vs wall superheat (pool-boiling curve): duty rises steeply with ΔT up to the critical heat flux — designs stay well below it.',
    params=tp(P('Shell ~ 1 – 3 m diameter; bundle ~ 3 – 8 m long'), P('~ 0.5 – 30+', 'MW'), P('Process side up to ~ 350; steam ~ 120 – 250', '°C'), P('Vapour ~ 5 – 300', 't/h')),
    install=_HX_INST,
    maint=_maint([M('Monitor steam flow vs boil-up and condensate drainage.', 'channel_head', 'daily')], [M('Trend U-value; check for tube leaks (process in condensate).', 'tube_bundle', 'monthly')],
                 [M('Pull and clean the bundle; inspect tubes (eddy current); replace gaskets.', 'tube_bundle')], _NOLUBE),
    failures=[F('Fouling of the bundle', ['Falling duty, higher steam pressure needed'], ['Polymerisation, salts, coke'], ['Clean; lower wall temperature; antifoulant'], 'tube_bundle'),
              F('Condensate backing up', ['Low duty, hammering'], ['Faulty trap, low steam pressure (stall)'], ['Pump-trap or level-controlled drain'], 'channel_head'),
              F('Liquid entrainment', ['Liquid carried to column'], ['Vapour space too small, foaming'], ['Reduce boil-up; demister'], 'shell')],
    quiz=[Q('What is the purpose of the weir in a kettle reboiler?', ['Keeps the tube bundle submerged', 'Separates steam from condensate', 'Supports the shell', 'Measures flow'], 0, 'Bundle must stay flooded.'),
          Q('Why is the kettle shell enlarged above the bundle?', ['Vapour–liquid disengagement space', 'Decoration', 'To store steam', 'To reduce weight'], 0, 'Lets droplets drop out.'),
          Q('Where does the heating steam flow?', ['Inside the tubes', 'In the shell', 'Through the weir', 'In the column'], 0, 'Tube side.')],
    selection=['Kettle for high vaporisation or wide boiling range; thermosyphon reboilers for lower cost and fouling-prone duties where head allows.'],
    safety=['Relief protection for blocked outlet and tube rupture cases (API 521); isolate and drain before opening.'],
    refs=['TEMA Standards', 'API 660', 'Kister — Distillation Operation'])

MODULES['preheater'] = mod(
    definition=('A preheater heats a fluid before it enters the main process, recovering heat that would otherwise be lost. In a closed feedwater heater, steam extracted from a turbine condenses '
                'on the outside of U-tubes and heats boiler feedwater flowing inside. The condensate collects at the bottom (drain-cooling zone) and drains to the next heater.'),
    applications=['Boiler feedwater heaters (LP/HP) in power plants', 'Crude and process feed preheating', 'Combustion air or fuel oil preheating'],
    key_points=['Raises the temperature of the incoming fluid using waste or bled heat', 'Shell side condenses steam at near-constant temperature', 'Each feedwater heater stage improves Rankine cycle efficiency', 'Impingement plate protects tubes at steam inlet'],
    principle=[step('Feedwater enters the channel and flows through the U-tubes.', 'channel', overlay='flow'), step('Steam enters the shell; an impingement plate protects the tubes.', 'baffles'),
               step('Steam condenses on the tubes, giving its latent heat to the water.', 'tube_bundle', overlay='temperature'), step('Condensate collects and is drained under level control.', 'condensate'),
               step('Heated feedwater leaves through the channel outlet.', 'nozzles', overlay='flow')],
    curve='Terminal temperature difference (TTD = steam sat. T − water outlet T) and drain-cooler approach (DCA) are the main performance indicators.',
    params=tp(P('Shell ~ 0.5 – 2.5 m diameter'), P('~ 0.5 – 50', 'MW'), P('Feedwater ~ 30 – 300 (HP heaters)', '°C'), P('~ 20 – 2000', 't/h water')),
    install=_HX_INST,
    maint=_maint([M('Watch TTD, DCA and drain level.', 'condensate', 'daily')], [M('Check vent operation (non-condensables).', 'nozzles', 'monthly')],
                 [M('Inspect tubes (eddy current); plug leaking tubes.', 'tube_bundle')], _NOLUBE),
    failures=[F('Tube leak', ['Rising drain level, high drain flow'], ['Erosion at steam inlet, vibration, corrosion'], ['Plug tubes; check impingement plate'], 'tube_bundle'),
              F('High TTD', ['Lower outlet temperature'], ['Air blanketing (vent blocked), fouling'], ['Clear vent; clean'], 'shell')],
    quiz=[Q('What heats the feedwater in a closed feedwater heater?', ['Condensing extraction steam', 'Electric heaters', 'Flue gas', 'Cooling water'], 0, 'Latent heat of steam.'),
          Q('Why vent non-condensable gases?', ['They blanket the tubes and reduce heat transfer', 'For noise', 'To raise pressure', 'They do not matter'], 0, 'Air blanketing.'),
          Q('What does TTD measure?', ['Steam saturation temperature minus water outlet temperature', 'Tube thickness', 'Total duty', 'Drain flow'], 0, 'Heater performance.')],
    selection=['Size for duty, TTD and DCA targets; select tube material for water chemistry; U-tube for thermal flexibility.'],
    safety=['Protect against tube rupture overpressure of the shell; never isolate the shell relief path.'],
    refs=['HEI Standards for Closed Feedwater Heaters', 'TEMA Standards'])

MODULES['economizer'] = mod(
    definition=('An economizer is a heat exchanger in the boiler flue-gas path that preheats the feedwater before it enters the drum, using heat that would otherwise go up the stack. '
                'Banks of serpentine (often finned) tubes carry the water upward while the gas flows down across them — counter-flow.'),
    applications=['Water-tube and packaged boilers', 'HRSGs (economizer section)', 'Shell boilers (add-on stack economizers)'],
    key_points=['Recovers flue-gas heat → higher boiler efficiency', 'Rule of thumb: ~ 1 % fuel saving per ~ 20–25 °C stack-temperature reduction', 'Gas must stay above acid dew point', 'Water must not steam in a non-steaming economizer'],
    principle=[step('Flue gas enters the top of the duct and flows downward.', 'casing', overlay='flow'), step('Feedwater enters the bottom header.', 'headers'),
               step('Water rises through the serpentine tubes, absorbing heat.', 'tube_bank', overlay='temperature'), step('The soot blower cleans deposits from the fins.', 'soot_blower'),
               step('Ash falls to the hopper; heated water goes to the drum.', 'ash_hopper')],
    curve='Recovered heat Q = m_gas · cp · (T_gas,in − T_gas,out) = m_w · cp · (T_w,out − T_w,in).',
    params=tp(P('Bank ~ 1 – 6 m across'), P('~ 0.1 – 50', 'MW'), P('Gas ~ 400 → 150; water ~ 105 → 200', '°C'), P('Water ~ 2 – 1500', 't/h')),
    install=_BOIL_INST,
    maint=_maint([M('Monitor gas and water temperatures and ΔP.', 'casing', 'daily')], [M('Operate soot blowers; inspect for erosion.', 'soot_blower', 'per shift/daily')],
                 [M('Thickness survey of tubes; replace eroded/corroded sections.', 'tube_bank')], ['Soot blower drive lubricated per maker.']),
    failures=[F('Cold-end (acid) corrosion', ['Tube leaks at the gas outlet end'], ['Gas below acid dew point (sulphur fuels), low feedwater temperature'], ['Raise feedwater temperature; bypass'], 'tube_bank'),
              F('Fouling/erosion', ['Rising ΔP; thinning'], ['Ash deposits, high gas velocity'], ['Soot blowing; erosion shields'], 'tube_bank')],
    quiz=[Q('What does an economizer heat?', ['Feedwater', 'Combustion air', 'Steam', 'Fuel'], 0, 'Feedwater.'),
          Q('Why must flue gas stay above the acid dew point?', ['To avoid sulphuric acid condensation and corrosion', 'For draught only', 'To heat air', 'No reason'], 0, 'Cold-end corrosion.'),
          Q('Gas flows down and water up — this is…', ['Counter-flow', 'Parallel flow', 'Cross-flow only', 'No flow'], 0, 'Better temperature driving force.')],
    selection=['Use finned tubes for clean gas (gas firing), bare/wide-spaced tubes for ash-laden gas; check acid dew point.'],
    safety=['Relief valve on economizer if it can be isolated; never isolate water flow with gas flowing.'],
    refs=['ASME BPVC Section I', 'Babcock & Wilcox — Steam: its generation and use'])

MODULES['superheater'] = mod(
    definition=('A superheater raises the temperature of saturated steam from the boiler drum above its saturation temperature. Superheated steam carries more energy per kilogram and stays dry '
                'through most of the turbine. Pendant platens hang in the hottest gas path; an attemperator sprays feedwater between stages to hold the final temperature.'),
    applications=['Utility and industrial water-tube boilers', 'HRSGs', 'Process steam where dry steam is required'],
    key_points=['Highest metal temperatures in the boiler → alloy steels', 'Primary + secondary stages', 'Spray attemperator controls outlet temperature', 'Steam flow cools the tubes — never fire without steam flow'],
    principle=[step('Saturated steam from the drum enters the primary inlet header.', 'nozzles', overlay='flow'), step('The primary platens heat the steam in the cooler gas zone.', 'primary_stage'),
               step('The attemperator sprays water to trim the temperature.', 'link_attemperator'), step('The secondary platens heat the steam to its final temperature.', 'secondary_stage', overlay='temperature'),
               step('Superheated steam leaves to the turbine.', 'gas_pass', overlay='flow')],
    curve='Convective superheaters: outlet temperature rises with load; radiant: falls with load — designs combine both for a flatter curve.',
    params=tp(P('Platens ~ 5 – 30 m long'), P('~ 5 – 500', 'MW'), P('Steam ~ 400 – 600+', '°C'), P('~ 10 – 2000', 't/h steam')),
    install=_BOIL_INST,
    maint=_maint([M('Monitor steam and tube metal temperatures; spray flow.', 'link_attemperator', 'continuous')], [M('Inspect for sagging, erosion and slag.', 'primary_stage', 'outages')],
                 [M('Oxide scale and creep assessment; replace aged sections.', 'secondary_stage')], _NOLUBE),
    failures=[F('Long-term overheating (creep)', ['Bulging, thick-lip ruptures'], ['Internal oxide scale, high metal temperature'], ['Material upgrade; temperature control'], 'secondary_stage'),
              F('Attemperator liner cracking', ['Cracks at spray zone'], ['Thermal shock'], ['Inspect liner; nozzle maintenance'], 'link_attemperator')],
    quiz=[Q('Why superheat steam?', ['More energy per kg and dry steam in the turbine', 'To lower pressure', 'To make water', 'To cool the boiler'], 0, 'Efficiency and blade protection.'),
          Q('How is final steam temperature controlled here?', ['Spray attemperator', 'By opening windows', 'By the condenser', 'By the stack'], 0, 'Spray water.'),
          Q('Superheater tubes are made of…', ['Alloy steels for high temperature', 'Copper', 'Plastic', 'Aluminium'], 0, 'Creep resistance.')],
    selection=['Select material by metal temperature (T11/T22/T91, austenitic); arrange stages for the load range.'],
    safety=['Safety valve on superheater outlet set to lift first so steam flows through the superheater.'],
    refs=['ASME BPVC Section I', 'Babcock & Wilcox — Steam'])

MODULES['air_preheater'] = mod(
    definition=('An air preheater transfers heat from the boiler flue gas to the incoming combustion air. In the rotary regenerative (Ljungström) type, a slowly rotating rotor packed with corrugated '
                'steel plates passes alternately through the gas and air streams: the plates absorb heat in the gas and release it to the air.'),
    applications=['Coal, oil and gas-fired utility boilers', 'Large industrial boilers and furnaces'],
    key_points=['Hotter air → better combustion and efficiency', 'Rotor ≈ 1–3 rpm', 'Air-to-gas leakage through seals is the main loss', 'Cold end prone to acid corrosion/fouling'],
    principle=[step('Hot flue gas passes down through one half of the rotor.', 'ducts', overlay='flow'), step('The rotor turns slowly, carrying heated plates to the air side.', 'rotor', overlay='temperature'),
               step('Combustion air flows up through the other half and is heated.', 'housing', overlay='flow'), step('Seals and sector plates limit leakage between the streams.', 'sector_plates_seals'),
               step('The drive turns the rotor through a pinion and pin rack.', 'drive')],
    curve='Air outlet temperature rises with gas inlet temperature and rotor speed up to a limit; leakage % rises as seals wear.',
    params=tp(P('Rotor ~ 3 – 20 m diameter'), P('~ 5 – 300', 'MW'), P('Gas ~ 350 → 130; air ~ 30 → 300', '°C'), P('Air ~ 50 – 5000', 't/h')),
    install=_BOIL_INST,
    maint=_maint([M('Monitor ΔP, leakage (O₂ rise) and temperatures.', 'housing', 'daily')], [M('Soot blowing/washing of the matrix.', 'rotor', 'per schedule')],
                 [M('Adjust/replace seals; replace cold-end baskets.', 'sector_plates_seals')], ['Rotor support/guide bearings: oil per maker; drive gearbox oil.']),
    failures=[F('High air-to-gas leakage', ['Higher fan power, O₂ rise across heater'], ['Seal wear, rotor distortion'], ['Adjust/replace seals'], 'sector_plates_seals'),
              F('Cold-end fouling/corrosion', ['ΔP rise'], ['Acid condensation, ammonium bisulphate'], ['Raise cold-end temperature; wash; enamelled baskets'], 'rotor')],
    quiz=[Q('How does a regenerative air preheater work?', ['A rotor stores heat in gas and releases it in air', 'Gas and air mix', 'Electric heating', 'Water transfers heat'], 0, 'Regeneration.'),
          Q('Main loss mechanism?', ['Air leakage to gas side past seals', 'Noise', 'Paint', 'Vibration'], 0, 'Seal leakage.'),
          Q('Typical rotor speed is…', ['About 1–3 rpm', '1500 rpm', '100 rpm', '0 rpm'], 0, 'Slow rotation.')],
    selection=['Compare regenerative vs tubular recuperative heaters for leakage tolerance and size; check cold-end temperature.'],
    safety=['Fire risk from deposits — fire detection and washing systems; lock out the drive before entry.'],
    refs=['ASME PTC 4.3', 'Babcock & Wilcox — Steam'])

MODULES['steam_generator'] = mod(
    definition=('A packaged steam generator (fire-tube or shell boiler) makes steam for heating and process use. The burner fires into a large furnace tube; the hot gases turn in a reversal chamber and '
                'pass back and forth through banks of smoke tubes (2nd and 3rd passes) before leaving through the stack. All these heating surfaces are surrounded by water inside the shell.'),
    applications=['Factories, hospitals, food and textile plants', 'District and process heating', 'Up to roughly 20–30 t/h steam at moderate pressure'],
    key_points=['Hot gas inside tubes, water outside (fire-tube)', 'Three passes improve heat recovery', 'Large water content → stable under load swings', 'Low-water protection is critical'],
    principle=[step('The burner mixes fuel and air and fires into the furnace tube (1st pass).', 'burner', overlay='flow'), step('The flame radiates heat to the furnace wall and water around it.', 'flame'),
               step('Gases turn in the rear reversal chamber into the 2nd-pass tubes.', 'reversal_chamber'), step('The front smoke box turns them into the 3rd pass and on to the stack.', 'smoke_boxes_stack'),
               step('Water boils around the tubes; steam leaves through the main steam valve.', 'fittings', overlay='flow')],
    curve='Efficiency vs load: best near 50–80 % load; stack temperature rises at high load.',
    params=tp(P('Shell ~ 1.5 – 4 m diameter, 3 – 8 m long'), P('~ 0.3 – 20', 'MW'), P('Steam ~ 120 – 230 (≈ 1 – 25 bar g sat.)', '°C'), P('~ 0.5 – 30', 't/h steam')),
    install=_BOIL_INST,
    maint=_maint([M('Check water level gauges, blowdown, low-water alarm test.', 'fittings', 'daily')], [M('Combustion check (O₂/CO), clean tubes.', 'burner', 'monthly')],
                 [M('Statutory inspection; internal/external examination; safety valve overhaul.', 'shell', 'annual')], ['Burner fan motor bearings greased; no lubrication for pressure parts.']),
    failures=[F('Low water / overheating', ['Furnace deformation, cracks'], ['Failed level control, feed pump trip'], ['Test cut-outs; never add cold water to an overheated boiler'], 'furnace'),
              F('Scale formation', ['Rising stack temperature, overheating'], ['Poor water treatment'], ['Water treatment; descale'], 'smoke_tubes'),
              F('Flame failure', ['Lockout'], ['Fuel supply, ignition, flame sensor'], ['Check BMS; purge; restart'], 'burner')],
    quiz=[Q('In a fire-tube boiler the hot gas flows…', ['Inside the tubes', 'Outside the tubes', 'Through the water', 'Not at all'], 0, 'Fire inside tubes.'),
          Q('Why three passes?', ['More heat transfer, lower stack temperature', 'To reduce pressure', 'To store fuel', 'For noise'], 0, 'Better heat recovery.'),
          Q('Why test low-water cut-outs regularly?', ['To prevent overheating of exposed surfaces', 'To save water', 'To clean tubes', 'Not needed'], 0, 'Safety.')],
    selection=['Fire-tube for moderate pressure and capacity; water-tube for higher pressure/capacity.'],
    safety=['Operate only with tested safety valves, level controls and flame safeguard; blowdown safely.'],
    refs=['EN 12953 — Shell boilers', 'ASME BPVC Section I', 'Spirax Sarco — The Steam and Condensate Loop'])

MODULES['waste_heat_recovery_boiler'] = mod(
    definition=('A waste heat recovery boiler (HRSG) makes steam from hot exhaust gas — for example from a gas turbine, engine, kiln or furnace. The gas passes the superheater, evaporator and economizer '
                'in turn; water circulates naturally between the steam drum and the evaporator tubes.'),
    applications=['Combined-cycle power plants (gas turbine + steam turbine)', 'Cogeneration (CHP)', 'Cement kilns, glass furnaces, sulphuric acid plants'],
    key_points=['No fuel needed (unless supplementary firing)', 'Pinch and approach temperatures set recovery', 'Natural circulation drum design', 'Low-temperature end limited by dew point'],
    principle=[step('Hot exhaust gas enters through the inlet transition.', 'casing', overlay='flow'), step('The superheater meets the hottest gas.', 'superheater', overlay='temperature'),
               step('The evaporator boils water; steam–water mixture rises to the drum.', 'evaporator'), step('The drum separates steam; downcomers feed water back.', 'steam_drum'),
               step('The economizer heats feedwater in the coolest gas before the stack.', 'economizer')],
    curve='T–Q diagram: gas cooling line vs water/steam heating line — the closest point is the pinch.',
    params=tp(P('Casing ~ 3 – 25 m tall'), P('~ 1 – 300', 'MW'), P('Gas inlet ~ 450 – 650 (GT exhaust)', '°C'), P('~ 5 – 400', 't/h steam')),
    install=_BOIL_INST,
    maint=_maint([M('Monitor drum level, pinch and stack temperature.', 'steam_drum', 'continuous')], [M('Water chemistry; FAC inspections.', 'circulation_piping', 'monthly')],
                 [M('Inspect tubes and headers; casing liners.', 'evaporator')], _NOLUBE),
    failures=[F('Flow-accelerated corrosion', ['Thinning in economizer/evaporator'], ['Low pH, low oxygen, high velocity'], ['Chemistry control; Cr-Mo material'], 'economizer'),
              F('Thermal fatigue', ['Header cracks'], ['Frequent starts (cycling)'], ['Controlled ramp rates; design for cycling'], 'superheater')],
    quiz=[Q('What is the "pinch point"?', ['Smallest gas-to-water temperature difference at the evaporator', 'Stack outlet', 'Drum level', 'Pump speed'], 0, 'Sets recovery.'),
          Q('Order of sections along the gas path:', ['Superheater → evaporator → economizer', 'Economizer first', 'Evaporator last', 'Random'], 0, 'Hottest to coolest.'),
          Q('What drives natural circulation?', ['Density difference between downcomer water and riser mixture', 'A pump', 'Gravity on steam', 'Fans'], 0, 'Thermosyphon.')],
    selection=['Choose pressure levels and pinch/approach from economics; add supplementary firing if more steam is needed.'],
    safety=['Gas bypass/diverter interlocks; drum safety valves; purge before GT start.'],
    refs=['Ganapathy — Waste Heat Boiler Deskbook', 'ASME BPVC Section I'])

MODULES['heat_recovery_system'] = mod(
    definition=('A run-around coil heat recovery system recovers heat from exhaust air to preheat the incoming supply air. A finned coil in the exhaust duct heats a pumped water–glycol loop, '
                'which carries the heat to a second coil in the supply duct. The two airstreams never meet.'),
    applications=['Hospitals, laboratories and clean rooms (no cross-contamination)', 'Retrofits where ducts are far apart', 'Industrial process exhaust heat recovery'],
    key_points=['Airstreams stay separate', 'Ducts can be far apart', 'Effectiveness typically ~ 45–65 %', 'Glycol protects against freezing'],
    principle=[step('Warm exhaust air passes the exhaust coil.', 'exhaust_coil', overlay='temperature'), step('The glycol loop absorbs that heat.', 'glycol_loop'),
               step('The pump circulates glycol to the supply coil.', 'loop_pump', overlay='flow'), step('Cold supply air is warmed by the supply coil.', 'supply_coil'),
               step('Fans move both airstreams.', 'supply_fan')],
    curve='Effectiveness ε = (T_supply,out − T_supply,in) / (T_exhaust,in − T_supply,in).',
    params=tp(P('Coil face ~ 0.5 – 10 m²'), P('~ 10 – 2000', 'kW'), P('Air ~ −20 → 35', '°C'), P('Air ~ 1 – 100', 'm³/s')),
    install=_HVAC_INST,
    maint=_maint([M('Check pump and loop temperatures.', 'loop_pump', 'weekly')], [M('Check glycol concentration and coil cleanliness.', 'glycol_loop', 'seasonal')],
                 [M('Clean coils; replace pump seals.', 'exhaust_coil')], ['Pump/fan motor bearings per maker.']),
    failures=[F('Frost on exhaust coil', ['Rising ΔP, falling recovery'], ['Very cold supply air, low glycol temperature'], ['Three-way valve frost control'], 'exhaust_coil'),
              F('Low effectiveness', ['Small temperature rise'], ['Fouled coils, low glycol flow, air in loop'], ['Clean; vent; check pump'], 'glycol_loop')],
    quiz=[Q('Why use a run-around coil instead of a plate exchanger?', ['Airstreams stay fully separate and ducts can be apart', 'It is always more efficient', 'No pump needed', 'No coils'], 0, 'Separation and flexibility.'),
          Q('What carries the heat between coils?', ['Water–glycol loop', 'Air', 'Refrigerant only', 'Steam'], 0, 'Glycol loop.'),
          Q('Typical effectiveness is about…', ['45–65 %', '99 %', '5 %', '200 %'], 0, 'Moderate.')],
    selection=['Optimise coil rows and glycol flow; check frost protection and pump energy vs recovered heat.'],
    safety=['Glycol handling; isolate electrical supply before maintenance.'],
    refs=['ASHRAE Handbook — Air-to-air energy recovery equipment'])

MODULES['quench_tower'] = mod(
    definition=('A quench tower cools a hot gas stream very quickly by spraying water or a recirculated liquid into it. As the fine droplets evaporate, they absorb heat, so the gas drops to near its '
                'adiabatic saturation temperature within a short distance. Excess liquid collects in the sump and is recirculated.'),
    applications=['Incinerator and thermal oxidizer off-gas before scrubbers/filters', 'Sulphuric acid and chemical plants', 'Cooling gas before baghouses'],
    key_points=['Rapid cooling by evaporation', 'Protects downstream equipment', 'Limits dioxin re-formation window in incineration', 'Wet–dry interface is highly corrosive'],
    principle=[step('Hot gas enters the top of the tower.', 'nozzles', overlay='flow'), step('Spray nozzles atomise the quench liquid.', 'spray_nozzles'),
               step('Droplets evaporate and cool the gas rapidly.', 'shell', overlay='temperature'), step('Unevaporated liquid collects in the sump.', 'sump'),
               step('The pump recirculates liquid to the sprays.', 'recirc_pump', overlay='flow')],
    curve='Gas temperature vs distance falls steeply under the sprays and levels off near adiabatic saturation.',
    params=tp(P('Diameter ~ 0.5 – 5 m'), P('Heat removed ~ 0.1 – 50', 'MW'), P('Gas ~ 1000 → 70–90 (wet quench)', '°C'), P('Gas ~ 1 000 – 200 000', 'm³/h')),
    install=_HX_INST | dict(foundation=['Vertical vessel on legs/skirt; allow for wet weight and thermal growth; corrosion-resistant materials or linings.']),
    maint=_maint([M('Check spray pressure, sump level and outlet temperature.', 'spray_nozzles', 'daily')], [M('Inspect nozzles for plugging/erosion.', 'spray_nozzles', 'monthly')],
                 [M('Inspect lining at the wet–dry zone.', 'shell')], ['Pump bearings per maker.']),
    failures=[F('Nozzle plugging', ['Outlet temperature high'], ['Solids in recirculated liquid'], ['Strainers, blowdown; clean nozzles'], 'spray_nozzles'),
              F('Corrosion at wet–dry line', ['Leaks, lining failure'], ['Acid condensation, chlorides'], ['Alloy/lining upgrade'], 'shell')],
    quiz=[Q('How does a quench tower cool gas?', ['Evaporation of sprayed liquid', 'Refrigeration', 'Fans only', 'Radiation to sky'], 0, 'Latent heat.'),
          Q('Why quench rapidly after incineration?', ['To limit dioxin re-formation in ~200–400 °C range', 'To heat gas', 'To make steam', 'For noise'], 0, 'De-novo synthesis window.'),
          Q('Where is corrosion worst?', ['At the wet–dry interface', 'In the pump motor', 'At the stack top', 'Nowhere'], 0, 'Acid condensation.')],
    selection=['Size for gas flow, inlet temperature and target outlet; choose co-current spray for very hot gas.'],
    safety=['Emergency quench water supply on loss of pumps (protects downstream equipment); hot gas hazards.'],
    refs=['EPA Air Pollution Control Cost Manual'])

MODULES['cooling_coil'] = mod(
    definition=('A cooling coil cools and dehumidifies air in an air-handling unit. Chilled water (or refrigerant) flows through copper tubes bonded to thin aluminium fins. Air passing over the cold fins '
                'is cooled; where the fin surface is below the air\'s dew point, water vapour condenses and drains to a pan.'),
    applications=['Air-handling units and fan-coils', 'Process air cooling', 'Data centre cooling'],
    key_points=['Sensible + latent cooling', 'Face velocity ≈ 2–2.5 m/s to avoid moisture carry-over', 'Counter-flow piping', 'Drain pan must drain fully (hygiene)'],
    principle=[step('Warm, humid air enters the coil section.', 'casing', overlay='flow'), step('Chilled water flows through the finned tubes.', 'coil', overlay='temperature'),
               step('Moisture condenses on the fins and drips into the pan.', 'drain_pan'), step('The valve modulates water flow to hold the air temperature.', 'headers_valve'),
               step('The fan delivers the cooled air.', 'fan')],
    curve='On a psychrometric chart the air moves towards the coil apparatus dew point; bypass factor describes air that misses the fins.',
    params=tp(P('Coil face ~ 0.2 – 15 m²; 4 – 10 rows'), P('~ 5 – 1500', 'kW'), P('CHW ~ 6 → 12; air ~ 27 → 13', '°C'), P('Air ~ 0.2 – 30', 'm³/s')),
    install=_HVAC_INST,
    maint=_maint([M('Check drain pan and trap.', 'drain_pan', 'monthly')], [M('Clean coil fins; check valve operation.', 'coil', 'quarterly/annual')],
                 [M('Replace coil if leaking or corroded.', 'coil')], ['Fan bearings per maker.']),
    failures=[F('Drain pan overflow', ['Water in the AHU, microbial growth'], ['Blocked drain, trap without seal'], ['Clean; correct trap depth'], 'drain_pan'),
              F('Low capacity', ['Air too warm'], ['Fouled fins, air in coil, low CHW flow'], ['Clean; vent; balance'], 'coil')],
    quiz=[Q('Why does water condense on the coil?', ['Fin surface is below the air dew point', 'Water leaks', 'Fan heat', 'Rain'], 0, 'Dehumidification.'),
          Q('Why limit face velocity?', ['To avoid blowing droplets off the coil', 'To save copper', 'To increase noise', 'No reason'], 0, 'Carry-over.'),
          Q('What controls leaving-air temperature?', ['Chilled-water control valve', 'Drain pan', 'Casing', 'Filter'], 0, 'Modulating valve.')],
    selection=['Select rows/fin spacing for sensible and latent load; check air ΔP and water ΔP.'],
    safety=['Lock out fan before entering the AHU; clean pans to prevent Legionella/microbial growth.'],
    refs=['AHRI 410', 'ASHRAE Handbook — HVAC Systems and Equipment'])

MODULES['cooling_water_distribution_system'] = mod(
    definition=('A cooling water distribution system circulates water between a cooling tower and the plant\'s heat users. Pumps draw cold water from the tower basin and send it through supply headers '
                'to exchangers and condensers; warmed water returns to the tower, where a small part evaporates and cools the rest.'),
    applications=['Power plants and refineries', 'Chemical and manufacturing plants', 'HVAC chilled-water condensers'],
    key_points=['Range = return − supply temperature', 'Approach = supply − wet-bulb temperature', 'Make-up replaces evaporation, drift and blowdown', 'Water treatment controls scale, corrosion and biology'],
    principle=[step('Cold water collects in the tower basin.', 'basin_water'), step('CW pumps send it into the supply header.', 'cw_pump_1', overlay='flow'),
               step('Users (coolers, condensers) pick up heat.', 'users', overlay='temperature'), step('Warm water returns to the tower distribution.', 'headers'),
               step('Water falls through the fill; the fan draws air up and evaporation cools it.', 'tower_fan')],
    curve='Tower performance curve: cold-water temperature vs wet-bulb for given range and flow.',
    params=tp(P('Header ~ 100 – 2000 mm; tower cells ~ 1 – 20'), P('~ 0.5 – 1000+', 'MW'), P('Supply ~ 25 – 32; return ~ 35 – 42', '°C'), P('~ 100 – 100 000', 'm³/h')),
    install=dict(foundation=['Tower basin and pump pits on reinforced foundations; pumps on plinths with adequate submergence.'],
                 alignment=['Align pump–motor sets; level tower fans and gear drives.'],
                 piping=['Size headers for velocity ≈ 1.5–3 m/s; strainers before users; balancing valves; air release at high points.'],
                 commissioning=['Flush system; passivate; set chemical treatment; balance flows to users; test standby pump auto-start.']),
    maint=_maint([M('Check pumps, basin level, conductivity and chemical dosing.', 'cw_pump_1', 'daily')], [M('Clean strainers; inspect fill and drift eliminators.', 'fill_distribution', 'monthly')],
                 [M('Overhaul pumps and fan gearboxes; inspect tower structure.', 'tower_fan')], ['Pump bearings, fan gearbox oil per maker.']),
    failures=[F('Scaling/fouling of users', ['Rising approach temperatures at exchangers'], ['High cycles of concentration, poor treatment'], ['Adjust blowdown and chemicals'], 'users'),
              F('Legionella risk', ['Positive samples'], ['Stagnant water, warm temperatures, poor biocide control'], ['Biocide programme, cleaning, risk assessment'], 'cooling_tower')],
    quiz=[Q('What is the cooling tower "range"?', ['Return minus supply temperature', 'Supply minus wet-bulb', 'Fan speed', 'Basin depth'], 0, 'Range.'),
          Q('What is "approach"?', ['Supply temperature minus air wet-bulb temperature', 'Return minus supply', 'Pump head', 'Fill height'], 0, 'Approach.'),
          Q('Make-up water replaces…', ['Evaporation, drift and blowdown', 'Only drift', 'Nothing', 'Steam'], 0, 'Losses.')],
    selection=['Size tower for heat load, design wet-bulb and approach; pumps for flow and header losses with standby.'],
    safety=['Legionella control; lock out fans before entering; chemical handling.'],
    refs=['CTI ATC-105', 'ASHRAE Handbook — Cooling towers'])

# ===================================================================== fired
MODULES['gas_fired_furnace'] = mod(
    definition=('A gas-fired process heater (furnace) heats a process fluid flowing through tubes. Burners fire into a refractory-lined radiant box; tubes along the walls absorb radiant heat. '
                'The flue gas then flows up through a convection section, where more tubes recover heat, and leaves by the stack. A damper controls the draught.'),
    applications=['Crude and vacuum heaters in refineries', 'Reformer and cracking heaters', 'Hot-oil heaters'],
    key_points=['Radiant section absorbs most heat', 'Convection section recovers heat from cooler gas', 'Draught and excess air control efficiency and safety', 'Tube-metal temperature limits firing'],
    principle=[step('Burners fire fuel gas into the radiant box.', 'burners', overlay='flow'), step('Flames radiate heat to the radiant tubes.', 'flame_1', overlay='temperature'),
               step('Flue gas rises through the convection section.', 'convection_section'), step('The stack and damper control the draught.', 'stack_damper'),
               step('Process fluid flows through convection then radiant tubes.', 'radiant_tubes', overlay='flow')],
    curve='Efficiency vs excess air: too little → CO and unburnt fuel; too much → heat lost in the stack. Typical target O₂ ~ 2–3 % (gas).',
    params=tp(P('Box ~ 3 – 20 m'), P('~ 1 – 150', 'MW'), P('Process outlet ~ 200 – 850; flue gas ~ 700 – 1000', '°C'), P('Process ~ 10 – 1000', 't/h')),
    install=_FIRED_INST,
    maint=_maint([M('Monitor O₂, draught, tube-metal temperatures, flame pattern.', 'burners', 'per shift')], [M('Clean burner tips; check damper.', 'stack_damper', 'monthly')],
                 [M('Inspect tubes (creep, coke) and refractory.', 'radiant_tubes', 'turnaround')], ['Damper actuator and fan bearings per maker.']),
    failures=[F('Flame impingement', ['Hot spots, tube bulging'], ['Burner misalignment, poor air distribution'], ['Re-align burners; adjust registers'], 'radiant_tubes'),
              F('Positive pressure at arch', ['Hot gas leaks'], ['Damper closed too far'], ['Restore draught (≈ −2 to −5 mmH₂O at arch)'], 'stack_damper')],
    quiz=[Q('Which section absorbs most of the heat?', ['Radiant', 'Convection', 'Stack', 'Damper'], 0, 'Radiation dominates.'),
          Q('Why control excess air?', ['Efficiency and safe combustion', 'For colour', 'To heat the stack', 'No reason'], 0, 'O₂ control.'),
          Q('What limits firing rate?', ['Tube-metal temperature and heat flux', 'Paint', 'Stack height only', 'Burner colour'], 0, 'Tube integrity.')],
    selection=['Design to API 560; tube thickness by API 530; low-NOx burners where required.'],
    safety=['Burner management system with purge, flame detection and fuel shut-offs; never relight without purge.'],
    refs=['API 560', 'API 530', 'API 556 — Instrumentation for fired heaters'])

MODULES['electric_furnace'] = mod(
    definition=('An electric arc furnace (EAF) melts steel scrap or direct-reduced iron with electric arcs. A transformer supplies very high current to three graphite electrodes; arcs form between the '
                'electrode tips and the charge. Electrode height is regulated to hold the arc. The melt is refined and tapped through a bottom tap hole.'),
    applications=['Steel making from scrap (mini-mills)', 'Stainless and special steels', 'Foundries'],
    key_points=['Electric energy melts the charge', 'Electrodes consumed in operation', 'Water-cooled panels and roof', 'Foamy slag shields walls and improves efficiency'],
    principle=[step('Scrap is charged with the roof swung aside.', 'roof'), step('The transformer supplies high current to the electrodes.', 'transformer', overlay='flow'),
               step('Arcs between electrodes and scrap melt the charge.', 'arc_1', overlay='temperature'), step('Electrode regulation keeps the arc length steady.', 'electrode_1'),
               step('The molten steel is tapped through the bottom tap.', 'molten_bath', overlay='flow')],
    curve='Electrical energy ≈ 350–450 kWh per tonne of steel (typical modern EAF, depends on charge and chemical energy).',
    params=tp(P('Shell ~ 4 – 10 m diameter'), P('Transformer ~ 20 – 300', 'MVA'), P('Tap ~ 1600 – 1650', '°C'), P('Heat size ~ 20 – 300', 't')),
    install=dict(foundation=['Heavy foundation for tilting loads; water-cooling systems with leak detection.'], alignment=['Electrode masts aligned with roof ports.'],
                 piping=['Cooling water to panels/roof; off-gas duct to fume treatment; oxygen and carbon injection.'],
                 commissioning=['Test cooling water flows, electrode regulation, tilt and emergency systems; dry refractory.']),
    maint=_maint([M('Inspect panels for leaks, electrode joints.', 'shell', 'every heat')], [M('Refractory gunning/repair.', 'shell', 'daily')],
                 [M('Replace roof/panels; transformer maintenance.', 'transformer')], ['Hydraulic system oil and filters; tilt bearings greased.']),
    failures=[F('Water leak into furnace', ['Steam, explosion risk'], ['Panel cracks'], ['Immediate shutdown; repair panels'], 'shell'),
              F('Electrode breakage', ['Arc loss'], ['Scrap cave-in, joint failure'], ['Proper charging; joint torque'], 'electrode_1')],
    quiz=[Q('What melts the steel in an EAF?', ['Electric arcs', 'Gas burners only', 'Induction coils', 'Steam'], 0, 'Arcs.'),
          Q('Why are wall panels water-cooled?', ['To protect them from the arc radiation and heat', 'To cool steel', 'To make steam', 'For noise'], 0, 'Protection.'),
          Q('What is a major explosion hazard?', ['Water contacting molten steel', 'Too much scrap', 'Low current', 'Cold roof'], 0, 'Steam explosion.')],
    selection=['Size by heat size, tap-to-tap time and transformer power.'],
    safety=['Molten metal and water: strict leak detection; arc flash/EMF; PPE and exclusion zones.'],
    refs=['IEC 60519', 'AIST — Making, Shaping and Treating of Steel'])
