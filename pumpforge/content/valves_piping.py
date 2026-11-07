"""Learning content — Valves & Piping additional equipment (EQ-118 … EQ-140)."""
from pumpforge.learning import mod, step, P, F, Q, M

MODULES = {}

_V_INSTALL = dict(
    foundation=['Support the valve and adjoining pipe so the body does not carry pipe weight or thermal loads; heavy valves need their own supports.'],
    alignment=['Align flanges face-to-face and bore-to-bore before bolting; never pull pipes into place with the bolts.',
               'Respect the flow-direction arrow on the body.'],
    piping=['Flush the line before installing the valve so welding debris cannot damage seats.', 'Provide isolation and drain/vent points for maintenance.',
            'Allow access for the handwheel/actuator and for removal of internals.'],
    commissioning=['Check the valve strokes fully and smoothly.', 'Pressure-test the line (shell test) with the valve partly open; do not use the valve to blind a test above its seat rating.',
                   'Record the as-installed position and set points.'])
_V_LUBE = ['Lubricate stem threads and operator gearing per the manufacturer; most wetted internals need no lubrication.']


def vp(size, pressure, temperature, capacity, **extra):
    return dict(size=size, pressure_rating=pressure, temperature=temperature, flow_capacity=capacity, extra=extra)


MODULES['needle_valve'] = mod(
    definition=('A needle valve is a small globe-type valve whose long tapered needle moves into a matching seat orifice on a fine-threaded stem. '
                'Many turns of the handle change the open area only slightly, so it gives precise throttling and tight shut-off of small flows.'),
    applications=['Instrument and gauge isolation', 'Sampling and analyser lines', 'Fine metering of gases and liquids', 'Hydraulic and pneumatic test rigs', 'Bleed and vent valves'],
    key_points=['Fine thread = precise adjustment', 'Flow under the seat', 'Not for slurries or solids', 'Do not overtighten'],
    principle=[step('Fluid enters below the seat orifice.', 'body', overlay='flow'), step('The conical needle sits in the orifice; its position sets the annular flow area.', 'stem'),
               step('Turning the handle raises the needle a small distance on a fine thread — flow increases gradually.', 'stem', operate=True),
               step('Packing under the gland nut seals the stem.', 'bonnet'), step('Fluid leaves through the outlet into the tubing.', 'tubing', overlay='flow')],
    curve='Approximately linear flow vs. turns over most of the stroke; very small Cv.',
    params=vp(P('1/8" – 1" (DN 6 – 25)'), P('up to ~400 (bar-stock, size dependent)', 'bar'), P('-50 to 230 (PTFE packing); higher with graphite', '°C'), P('Cv ≈ 0.01 – 2', '')),
    install=_V_INSTALL, maint=dict(routine=[M('Check stem packing for leaks.', 'bonnet', 'monthly')], periodic=[M('Adjust gland nut; replace packing if needed.', 'bonnet', 'as needed')],
                                   overhaul=[M('Inspect needle and seat for wire-drawing; replace valve if seat is damaged.', 'stem')], lubrication=_V_LUBE),
    failures=[F('Seat leakage (passing)', ['Flow when closed'], ['Over-tightening damaged seat', 'Debris/erosion'], ['Replace valve or needle; fit filter'], 'stem'),
              F('Stem leakage', ['Leak at gland'], ['Worn packing'], ['Adjust/repack'], 'bonnet')],
    quiz=[Q('Why does a needle valve allow precise flow control?', ['Large bore', 'Fine thread + tapered needle change area slowly per turn', 'It has a spring', 'It is quarter-turn'], 1, 'Many turns produce a small area change.'),
          Q('A needle valve is NOT suitable for…', ['Gauge isolation', 'Slurry service', 'Gas metering', 'Sampling'], 1, 'Small passages clog and erode.'),
          Q('What happens if a needle valve is overtightened?', ['Nothing', 'Needle and seat can be damaged, causing passing', 'Flow increases', 'It opens'], 1, 'Soft seats deform.')],
    selection=['Choose stem tip (sharp, blunt, soft-seat) for metering vs. shut-off.'],
)

MODULES['pinch_valve'] = mod(
    definition=('A pinch valve controls flow by squeezing a flexible elastomer sleeve. Open, it is a straight full-bore tube; closed, the sleeve is pinched shut. '
                'Only the sleeve touches the fluid, so it handles abrasive slurries, powders and corrosive liquids without pockets or crevices.'),
    applications=['Mineral and alumina slurries (red mud, lime, tailings)', 'Cement, sand and powder conveying', 'Wastewater sludge', 'Chemical and food dosing'],
    key_points=['Full bore, no dead pockets', 'Sleeve is the only wear part', 'Double-pinch closes on the centreline', 'Pressure and temperature limited by the elastomer'],
    principle=[step('Open: slurry passes straight through the full-bore sleeve.', 'sleeve', overlay='flow'), step('Turning the handwheel drives the upper pinch bar down.', 'handwheel'),
               step('Links pull the lower bar up at the same time (double pinch).', 'lower_pinch_bar'), step('The sleeve flattens and seals across the bore.', 'sleeve', operate=True),
               step('The housing contains the sleeve and supports the mechanism.', 'housing', cut=False)],
    curve='Near-linear to equal-percentage throttling over the middle of the stroke; avoid long throttling at very small openings (wear).',
    params=vp(P('DN 25 – 600'), P('up to ~10 – 16', 'bar'), P('-20 to 100 (natural rubber ~ 80)', '°C', 'elastomer dependent'), P('Full bore — Kv ≈ that of straight pipe', '')),
    install=_V_INSTALL, maint=dict(routine=[M('Check for sleeve leakage at the housing drain.', 'housing', 'weekly')], periodic=[M('Replace sleeve on schedule or at first sign of cracking.', 'sleeve', 'per cycles/hours')],
                                   overhaul=[M('Check pinch bars and stem threads.', 'upper_pinch_bar')], lubrication=_V_LUBE),
    failures=[F('Sleeve rupture', ['Leak from housing'], ['Fatigue, abrasion, over-closing'], ['Replace sleeve; set closing stop'], 'sleeve'),
              F('Incomplete closure', ['Passing'], ['Solids trapped, worn sleeve'], ['Cycle/flush; replace sleeve'], 'sleeve')],
    quiz=[Q('What is the only wetted part of a pinch valve?', ['Pinch bars', 'Elastomer sleeve', 'Housing', 'Handwheel'], 1, 'The process touches only the sleeve.'),
          Q('Why are pinch valves popular for slurries?', ['High temperature rating', 'Full bore, no pockets, replaceable wear part', 'Quarter turn', 'Metal seats'], 1, 'Nothing for solids to wear or jam.'),
          Q('What limits a pinch valve\'s pressure/temperature?', ['Handwheel size', 'The elastomer sleeve', 'Flange bolts', 'Paint'], 1, 'Elastomer properties.')],
)

MODULES['float_valve'] = mod(
    definition=('A float valve automatically keeps a tank at a set level. A float on a lever arm rises with the liquid; the lever pushes a plunger onto the seat '
                'and throttles the inlet until it closes at the full level. When liquid is drawn off, the float drops and the valve reopens.'),
    applications=['Water storage and break tanks', 'Cooling-tower basins', 'Livestock troughs and cisterns', 'Make-up to process tanks'],
    key_points=['Self-acting — no power needed', 'Lever multiplies float force', 'Throttles progressively near full level', 'Fit an overflow in case it fails'],
    principle=[step('Water enters through the inlet pipe and seat.', 'inlet_pipe', overlay='flow'), step('As the level rises the float lifts.', 'float_lever', operate=True),
               step('The lever pushes the plunger and washer towards the seat, reducing flow.', 'plunger'), step('At full level the washer seals the seat and flow stops.', 'valve_body'),
               step('When water is used the level falls, the float drops and the valve opens again.', 'water_level')],
    curve='Proportional throttling over the last part of the float travel.',
    params=vp(P('1/2" – 6" (larger: pilot float valves)'), P('up to ~10 – 16', 'bar supply'), P('0 to 60', '°C'), P('Depends on seat size and supply pressure', '')),
    install=_V_INSTALL | dict(piping=['Fit an isolating valve upstream and an overflow/warning pipe on the tank.', 'Keep the float free of walls and baffles.']),
    maint=dict(routine=[M('Check level is maintained and no overflow.', 'water_level', 'weekly')], periodic=[M('Replace the washer when passing.', 'plunger', 'as needed')],
               overhaul=[M('Check float for leaks and lever pivot for wear.', 'float_lever')], lubrication=['Pivot pins: no lubrication for potable water service; keep clean.']),
    failures=[F('Overflow', ['Water at overflow'], ['Worn washer, punctured float, stuck lever'], ['Replace washer/float; free pivot'], 'float_lever'),
              F('Water hammer / noise', ['Banging on closing'], ['High supply pressure, valve too large'], ['Reduce pressure; delayed-action valve'], 'valve_body')],
    quiz=[Q('What supplies the closing force in a float valve?', ['A motor', 'Buoyancy of the float, multiplied by the lever', 'A solenoid', 'Pump pressure'], 1, 'Lever advantage.'),
          Q('Why is an overflow pipe still needed?', ['To fill faster', 'In case the float valve fails open', 'For cooling', 'It is not'], 1, 'Safety backup.'),
          Q('As the level rises the valve…', ['Opens', 'Throttles progressively and then closes', 'Does nothing', 'Reverses'], 1, 'Proportional action.')],
)

MODULES['foot_valve'] = mod(
    definition=('A foot valve is a non-return valve with a strainer fitted at the bottom end of a pump suction pipe. It opens when the pump draws liquid, '
                'and closes when the pump stops so the suction line stays full and the pump stays primed. The strainer keeps solids out.'),
    applications=['Centrifugal pumps lifting from sumps, wells and tanks', 'Fire pumps on open water sources (where permitted)', 'Irrigation and dewatering', 'Marine bilge suctions'],
    key_points=['Keeps the pump primed', 'Adds suction loss — size generously', 'Must stay submerged', 'Strainer needs cleaning'],
    principle=[step('With the pump running, suction lifts the poppet off its seat.', 'poppet', overlay='flow', operate=True), step('Liquid passes the strainer basket into the valve.', 'strainer', overlay='flow'),
               step('Flow rises through the suction pipe to the pump.', 'suction_pipe', overlay='flow'), step('When the pump stops, the spring and the water column close the poppet.', 'guide_spring'),
               step('The suction line stays full, so the pump restarts without priming.', 'body')],
    curve='Pressure loss rises with flow squared; check it in the NPSHa calculation.',
    params=vp(P('DN 25 – 300'), P('up to ~16', 'bar'), P('0 to 80 (elastomer seal)', '°C'), P('Loss coefficient K ≈ 1 – 4 incl. strainer (design dependent)', '')),
    install=_V_INSTALL | dict(piping=['Keep the foot valve at least ~1–1.5 pipe diameters above the sump floor and well below the minimum level (check ANSI/HI 9.8).',
                                      'Make the suction pipe airtight and rising to the pump.']),
    maint=dict(routine=[M('Check pump stays primed after stops.', 'poppet', 'weekly')], periodic=[M('Lift and clean the strainer.', 'strainer', 'monthly')],
               overhaul=[M('Replace seat seal and spring.', 'guide_spring')], lubrication=['None.']),
    failures=[F('Loss of prime', ['Pump runs but no flow after restart'], ['Poppet held open by debris, worn seal'], ['Clean/replace seal'], 'poppet'),
              F('Cavitation from blocked strainer', ['Noise, low flow'], ['Clogged basket'], ['Clean strainer, enlarge open area'], 'strainer')],
    quiz=[Q('Main purpose of a foot valve?', ['Throttle flow', 'Keep the suction line full so the pump stays primed', 'Raise pressure', 'Measure flow'], 1, 'Non-return at the suction end.'),
          Q('A blocked foot-valve strainer can cause…', ['Higher NPSHa', 'Cavitation and low flow', 'Overspeed', 'Nothing'], 1, 'Extra suction loss reduces NPSHa.'),
          Q('Where is a foot valve installed?', ['On the discharge', 'At the bottom of the suction pipe', 'At the pump casing', 'On the tank roof'], 1, 'Submerged at the inlet.')],
)

MODULES['solenoid_valve'] = mod(
    definition=('A solenoid valve is an electrically operated on/off valve. Current in the coil creates a magnetic field that lifts a plunger. In the pilot-operated '
                '(servo) type modelled, the plunger opens a small pilot orifice; the pressure above the diaphragm bleeds to the outlet and line pressure lifts the '
                'diaphragm off the main seat. When the coil is switched off the spring closes the pilot and the diaphragm reseats.'),
    applications=['Water, air and gas shut-off in automation', 'Burner fuel shut-off (safety shut-off valves)', 'Cooling water and process utilities', 'Pneumatic control circuits', 'Irrigation'],
    key_points=['Normally closed (NC) or normally open (NO)', 'Pilot-operated needs a minimum ΔP; direct-acting does not', 'Fast acting — beware water hammer', 'Coil voltage and duty must match'],
    principle=[step('De-energised: the spring holds the plunger on the pilot orifice; inlet pressure above the diaphragm keeps it closed.', 'plunger', operate=False),
               step('Energised: the coil field pulls the plunger up.', 'coil', overlay='magnetic_field'),
               step('The pilot orifice opens; cover pressure escapes to the outlet faster than the bleed hole refills it.', 'diaphragm'),
               step('Line pressure lifts the diaphragm and flow passes the main orifice.', 'diaphragm', overlay='flow'),
               step('De-energising lets the plunger drop; pressure builds above the diaphragm and the valve closes.', 'armature_tube')],
    curve='On/off device; response time from tens of milliseconds (direct) to ~1 s (large pilot valves).',
    params=vp(P('1/8" – 3" (DN 3 – 80)'), P('up to ~16 – 40 (body); min ΔP ≈ 0.1 – 0.5 bar for pilot types', 'bar'), P('-10 to 90 (NBR); up to ~180 (PTFE/FKM, steam types)', '°C'),
              P('Kv ≈ 0.1 – 100', 'm³/h'), coil=P('12/24 V DC, 24/110/230 V AC; ~5 – 20 W', '')),
    install=_V_INSTALL | dict(piping=['Fit a strainer upstream — dirt blocks the bleed and pilot orifices.', 'Install with the coil upward where recommended.']),
    maint=dict(routine=[M('Check coil temperature and operation.', 'coil', 'monthly')], periodic=[M('Clean diaphragm, bleed and pilot orifices.', 'diaphragm', 'per service')],
               overhaul=[M('Replace diaphragm, plunger seal and spring with a repair kit.', 'plunger')], lubrication=['None — do not oil the plunger tube.']),
    failures=[F('Valve does not open', ['Coil energised, no flow'], ['ΔP below minimum', 'Burnt coil', 'Blocked pilot'], ['Check ΔP, coil resistance, clean pilot'], 'coil'),
              F('Valve does not close', ['Flow continues'], ['Blocked bleed hole, torn diaphragm, dirt on seat'], ['Clean/replace diaphragm'], 'diaphragm'),
              F('Coil burn-out', ['Coil open-circuit, smell'], ['Wrong voltage, stuck plunger (AC)'], ['Correct voltage; free plunger'], 'coil')],
    quiz=[Q('Why does a pilot-operated solenoid valve need a minimum pressure difference?', ['To cool the coil', 'Line pressure is what lifts the diaphragm', 'For the spring', 'It does not'], 1, 'Servo-assisted opening.'),
          Q('NC means…', ['Normally closed: closed when de-energised', 'Never closes', 'No coil', 'Needle controlled'], 0, 'Fail-closed on power loss.'),
          Q('A common cause of AC coil burn-out is…', ['Low pressure', 'Plunger stuck so the coil draws high inrush current', 'Clean water', 'Too short cable'], 1, 'AC coil current falls only when the plunger closes the magnetic circuit.', 'intermediate')],
)

MODULES['three_way_valve'] = mod(
    definition=('A three-way valve has three ports. Used as a diverting valve it sends one inlet to either of two outlets; used as a mixing valve it combines two '
                'inlets into one outlet. The L-port ball valve modelled connects the bottom inlet to outlet A or outlet B as the ball is rotated.'),
    applications=['Diverting flow between two units (duty/standby filters, heat-exchanger bypass)', 'Temperature control by mixing hot and cold streams', 'Sampling and tank selection', 'Hydraulic and pneumatic switching'],
    key_points=['L-port: one path at a time; T-port: can connect all three', 'Port/flow pattern must be checked on the chart', 'Lever pointer shows the flow path'],
    principle=[step('Flow enters the bottom port.', 'pipework', overlay='flow'), step('The L-shaped bore in the ball connects the inlet to outlet A.', 'ball'),
               step('Rotating the lever turns the ball inside its seats.', 'stem_lever', operate=True), step('Now the bore connects the inlet to outlet B; outlet A is shut.', 'ball', overlay='flow'),
               step('PTFE seats seal against the ball.', 'seats')],
    curve='On/off switching (ball types); globe-type three-way control valves give modulating mixing/diverting.',
    params=vp(P('DN 8 – 200'), P('up to ~40 – 100 (class dependent)', 'bar'), P('-20 to 200 (PTFE seats)', '°C'), P('Kv per path ≈ similar to a full/reduced-bore ball valve', '')),
    install=_V_INSTALL, maint=dict(routine=[M('Check lever position matches the required path.', 'stem_lever', 'each operation')], periodic=[M('Operate through full travel to prevent sticking.', 'ball', 'quarterly')],
                                   overhaul=[M('Replace seats and stem seals.', 'seats')], lubrication=_V_LUBE),
    failures=[F('Cross-port leakage', ['Flow to the wrong outlet'], ['Worn seats'], ['Replace seats'], 'seats'), F('Wrong flow path', ['Process upset'], ['Wrong port pattern or orientation'], ['Check port chart'], 'ball')],
    quiz=[Q('A diverting three-way valve…', ['Mixes two inlets', 'Sends one inlet to one of two outlets', 'Has two ports', 'Only throttles'], 1, 'Diverting vs. mixing.'),
          Q('What tells the operator which path is open?', ['The flange colour', 'The lever/pointer orientation', 'The bolt pattern', 'Nothing'], 1, 'Lever aligns with flow path.'),
          Q('Difference between L-port and T-port balls?', ['None', 'T-port can connect three ports at once; L-port connects only two', 'L-port is larger', 'T-port is for gas only'], 1, 'Port patterns.', 'intermediate')],
)

MODULES['four_way_valve'] = mod(
    definition=('A four-way directional control valve connects a pressure supply P and a return T to two working ports A and B. Shifting the spool reverses the '
                'connections — P→A with B→T, or P→B with A→T — so a double-acting cylinder or motor reverses direction. The same idea is used in pneumatic '
                'valves and in heat-pump reversing valves.'),
    applications=['Hydraulic cylinders and motors (presses, gates, mobile machinery)', 'Pneumatic actuators', 'Heat-pump refrigerant reversing', 'Valve actuators'],
    key_points=['Ports P, T, A, B', 'Spool lands open/close annular grooves', 'Solenoid, pilot, lever or mechanical operation', 'Cleanliness critical (tight clearances)'],
    principle=[step('Pump flow enters port P; port T returns to tank.', 'hydraulic_lines', overlay='flow'), step('Solenoid a shifts the spool: P connects to A and B to T.', 'spool', operate=True),
               step('Oil to A pushes the piston; oil from the other side returns through B to T.', 'piston_rod', overlay='flow'),
               step('Solenoid b shifts the spool back: P→B and A→T, so the cylinder retracts.', 'solenoids'), step('The spool lands seal against the bore between ports.', 'body')],
    curve='Directional valve: pressure drop P→A / B→T rises with flow (Δp–Q curves in data sheets).',
    params=vp(P('NG 6 – 32 (ISO 4401 / CETOP)'), P('up to ~315 – 350', 'bar'), P('-20 to 80 (oil)', '°C'), P('up to ~60 – 1,000', 'L/min', 'size dependent')),
    install=_V_INSTALL | dict(piping=['Mount on a flat, clean subplate with correct O-rings.', 'Flush the system to the specified ISO 4406 cleanliness before connecting.']),
    maint=dict(routine=[M('Check for external leaks and coil function.', 'solenoids', 'daily')], periodic=[M('Monitor oil cleanliness and filter ΔP.', 'hydraulic_lines', 'per plan')],
               overhaul=[M('Inspect spool and bore for scoring.', 'spool')], lubrication=['Lubricated by the hydraulic oil.']),
    failures=[F('Spool sticking', ['Cylinder does not move'], ['Silting, varnish, contamination'], ['Clean valve, improve filtration'], 'spool'),
              F('Cylinder drift', ['Load creeps'], ['Internal leakage across lands, cylinder seal leak'], ['Pilot check valves; repair'], 'piston_rod'),
              F('Coil failure', ['No shift'], ['Voltage, heat'], ['Replace coil'], 'solenoids')],
    quiz=[Q('In position 1, P connects to A. Where does B connect?', ['P', 'T (tank)', 'Nowhere', 'A'], 1, 'B→T lets the cylinder exhaust.'),
          Q('What reverses the cylinder?', ['Changing pump speed', 'Shifting the spool to the other position', 'Closing T', 'Bleeding air'], 1, 'Cross-connection reverses.'),
          Q('Which standard covers subplate mounting patterns?', ['ISO 5167', 'ISO 4401', 'API 610', 'ISO 2858'], 1, 'CETOP/NG patterns.', 'intermediate')],
)

MODULES['vacuum_relief_valve'] = mod(
    definition=('A vacuum relief valve (vacuum breaker) admits air into a tank or vessel when its internal pressure falls below a set vacuum, preventing implosion. '
                'Vacuum is created when a tank is pumped out, when hot vapours condense or when weather cools a tank. When the set point is reached, atmospheric '
                'pressure pushes the pallet open against its spring or weight; air flows in until pressures balance.'),
    applications=['Atmospheric and low-pressure storage tanks', 'Evaporators, condensers and steam-heated vessels', 'Pipelines at high points (vacuum breakers)', 'Tank trucks and IBCs'],
    key_points=['Set vacuum must be below the tank\'s vacuum design rating', 'Sized for maximum pump-out + thermal in-breathing (API 2000)', 'Screens must not be blocked'],
    principle=[step('Normally the spring holds the pallet against the seat — the tank is sealed.', 'pallet', operate=False),
               step('As the tank is emptied, internal pressure drops below atmospheric.', 'tank_roof'),
               step('At the set vacuum, atmospheric pressure pushes the pallet inward against the spring.', 'pallet', operate=True),
               step('Air enters through the hood and screen into the tank.', 'hood_screen', overlay='flow'), step('When pressure equalises the spring recloses the pallet.', 'spring')],
    curve='Flow capacity rises with overpressure (vacuum) above the set point; full lift at ~10 % overpressure for many designs.',
    params=vp(P('DN 50 – 300'), P('set vacuum ≈ -2 to -50 mbar (storage tanks)', 'mbar g'), P('-40 to 200', '°C'), P('Air capacity per API 2000 sizing (Nm³/h)', '')),
    install=_V_INSTALL | dict(piping=['Mount vertically on a roof nozzle at least as large as the valve inlet.', 'Keep the inlet free from frost and product build-up; heat-trace if needed.']),
    maint=dict(routine=[M('Inspect screen and hood for blockage, ice or nests.', 'hood_screen', 'monthly')], periodic=[M('Lift-test the pallet and check seat.', 'pallet', 'annually')],
               overhaul=[M('Replace pallet seal and spring.', 'spring')], lubrication=['None — clean, dry seats.']),
    failures=[F('Tank collapse', ['Buckled roof/shell'], ['Blocked screen, stuck pallet, undersized valve'], ['Inspect, resize per API 2000'], 'hood_screen'),
              F('Leakage / emissions', ['Vapour release'], ['Damaged seat'], ['Replace seat/seal'], 'pallet')],
    quiz=[Q('What causes vacuum in a storage tank?', ['Filling', 'Pumping out and cooling/condensing vapour', 'Heating the roof', 'Nitrogen blanket'], 1, 'Out-breathing vs. in-breathing.'),
          Q('Which way does the pallet move to open?', ['Outward', 'Inward into the tank', 'Sideways', 'It rotates'], 1, 'Atmosphere pushes it in.'),
          Q('Which standard covers tank venting sizing?', ['API 610', 'API 2000 / ISO 28300', 'ISO 5167', 'NFPA 20'], 1, 'Venting standard.')],
)

MODULES['pressure_sustaining_valve'] = mod(
    definition=('A pressure sustaining valve maintains a minimum pressure UPSTREAM of itself. Its adjustable pilot senses inlet pressure: above the set point the '
                'pilot releases pressure from the control chamber and the main valve opens; below it, the pilot admits inlet pressure to the chamber and the valve '
                'throttles or closes. It keeps high areas of a network supplied, prevents pumps running out on their curves and holds back-pressure on processes.'),
    applications=['Water distribution zones and transfer mains', 'Pump discharge (prevent run-out / cavitation)', 'Filter back-pressure', 'Priority supply to elevated areas'],
    key_points=['Controls upstream pressure (PRV controls downstream)', 'Modulating, hydraulically operated by line pressure', 'Pilot set point adjustable', 'Needs clean water for the pilot circuit'],
    principle=[step('Inlet pressure acts under the disc and through the pilot circuit.', 'body', overlay='flow'), step('The pilot compares inlet pressure with its spring setting.', 'pilot_system'),
               step('If inlet pressure rises above the set point the pilot vents the cover chamber and the disc opens.', 'disc_diaphragm', operate=True),
               step('If inlet pressure falls, the pilot fills the cover chamber; the spring and pressure push the disc towards the seat.', 'cover_spring'),
               step('The disc settles in a position that holds the inlet pressure at the set point.', 'disc_diaphragm', overlay='flow')],
    curve='Valve opening varies with demand; inlet pressure held within a narrow band (± a few % of set point).',
    params=vp(P('DN 50 – 600'), P('PN 16 – 25 (up to PN 40)', 'bar'), P('0 to 80 (water)', '°C'), P('Kv ≈ 50 – 5,000', 'm³/h')),
    install=_V_INSTALL | dict(piping=['Install isolating valves and a strainer upstream of the pilot circuit.', 'Provide pressure gauges on inlet and outlet for setting.']),
    maint=dict(routine=[M('Check inlet pressure holds at set point.', 'pilot_system', 'weekly')], periodic=[M('Clean pilot strainer and restriction.', 'pilot_system', 'quarterly')],
               overhaul=[M('Inspect diaphragm, disc and seat.', 'disc_diaphragm')], lubrication=['None.']),
    failures=[F('Hunting / instability', ['Pressure oscillates'], ['Oversized valve, dirty needle valve, air in cover'], ['Adjust speed control, bleed air, resize'], 'pilot_system'),
              F('Fails to close', ['Upstream pressure collapses'], ['Torn diaphragm, debris on seat'], ['Replace diaphragm, clean seat'], 'disc_diaphragm'),
              F('Cavitation', ['Noise, seat damage'], ['High ΔP at low flow'], ['Anti-cavitation trim, staged reduction'], 'body')],
    quiz=[Q('A pressure sustaining valve controls…', ['Downstream pressure', 'Upstream (inlet) pressure', 'Flow rate', 'Temperature'], 1, 'Back-pressure valve.'),
          Q('What moves the main valve?', ['An electric motor', 'Line pressure in the control chamber, set by the pilot', 'A float', 'Hand only'], 1, 'Hydraulically operated.'),
          Q('Why is it used on pump discharges?', ['To prime the pump', 'To prevent run-out beyond the pump curve and protect against cavitation', 'To measure flow', 'To heat water'], 1, 'Holds head on the pump.')],
)

MODULES['steam_trap'] = mod(
    definition=('A steam trap is an automatic valve that discharges condensate and air from steam systems while preventing live steam from escaping. In the inverted '
                'bucket trap, steam under the bucket makes it float and close the valve; when condensate fills the bucket and the trapped steam escapes through the '
                'vent hole, the bucket sinks, opens the valve and system pressure pushes the condensate out.'),
    applications=['Steam main drip legs', 'Heat exchangers, reboilers and coils', 'Steam tracing', 'Turbine and plant steam systems (alumina digestion, evaporation)'],
    key_points=['Mechanical (bucket, float), thermostatic and thermodynamic families', 'Failed-open traps waste energy; failed-closed traps waterlog equipment', 'Regular trap surveys pay back quickly'],
    principle=[step('Condensate from the steam line enters through the inlet riser.', 'body', overlay='flow'), step('Steam entering under the bucket makes it buoyant — the bucket rises.', 'bucket', operate=True),
               step('The lever presses the valve head onto the seat — no steam escapes.', 'valve_lever'),
               step('Steam condenses / vents through the bucket hole; condensate fills the bucket and it sinks.', 'condensate'),
               step('The valve opens and condensate is pushed out to the return line.', 'pipework', overlay='flow')],
    curve='Intermittent discharge; capacity depends on orifice size and differential pressure.',
    params=vp(P('1/2" – 2"'), P('up to ~17 – 45 (orifice selected for max ΔP)', 'bar'), P('up to ~400', '°C'), P('Condensate capacity ~ 10 – 5,000+', 'kg/h')),
    install=_V_INSTALL | dict(piping=['Install below the drain point with a strainer and isolation valves; provide a test/sight point.', 'Prime (fill) inverted bucket traps before start-up.']),
    maint=dict(routine=[M('Survey traps with ultrasound/temperature.', 'body', 'quarterly – annually')], periodic=[M('Clean strainer.', 'pipework', 'semi-annually')],
               overhaul=[M('Replace valve and seat mechanism.', 'valve_lever')], lubrication=['None.']),
    failures=[F('Blowing steam (failed open)', ['Live steam at outlet, high return temperature'], ['Lost water seal, worn seat'], ['Re-prime, replace mechanism'], 'valve_lever'),
              F('Blocked (failed closed)', ['Cold trap, waterlogged equipment'], ['Dirt, closed vent'], ['Clean strainer and orifice'], 'bucket'),
              F('Water hammer', ['Banging in steam lines'], ['Condensate not drained'], ['Restore trap function, proper drip legs'], 'body')],
    quiz=[Q('What makes the inverted bucket float?', ['Condensate', 'Steam trapped under the bucket', 'A spring', 'A motor'], 1, 'Steam buoyancy.'),
          Q('A trap that has failed open…', ['Waterlogs equipment', 'Wastes live steam', 'Saves energy', 'Stops flow'], 1, 'Energy loss.'),
          Q('Best routine check for steam traps?', ['Paint them', 'Ultrasonic/temperature survey', 'Shake them', 'Nothing'], 1, 'Trap surveys.')],
)

MODULES['flame_arrestor'] = mod(
    definition=('A flame arrestor is a passive device that lets gas flow but stops a flame propagating through it. Its element divides the flow into many narrow '
                'channels; a flame entering them loses heat to the metal so quickly that it cannot sustain combustion and is extinguished.'),
    applications=['Storage tank vents (with PV valves)', 'Vapour recovery and vent headers', 'Flare and incinerator lines', 'Gas burner and biogas lines'],
    key_points=['Gap selected for the gas explosion group (MESG)', 'Deflagration vs. detonation designs', 'Installation distance limits for in-line types', 'Fouling raises ΔP'],
    principle=[step('Gas flows through the housing; the housing enlarges so velocity in the element is low.', 'housing', overlay='flow'),
               step('The crimped-ribbon element creates thousands of narrow triangular channels.', 'element'),
               step('A flame front travelling back towards the element enters the channels.', 'flame_front', operate=True),
               step('Heat is drawn into the metal walls; the flame cools below ignition and goes out.', 'element', overlay='quench')],
    curve='Pressure drop rises approximately with flow² and with element fouling.',
    params=vp(P('DN 15 – 600'), P('Operating up to ~1.1 – 2 (deflagration); detonation types higher', 'bar abs'), P('Max operating ~60 °C typical for certification (verify)', '°C'),
              P('Flow vs. ΔP per data sheet', ''), gas_group=P('IIA, IIB1–IIB3, IIC (ISO 16852)', '')),
    install=_V_INSTALL | dict(piping=['Respect the maximum distance between ignition source and arrestor stated in the certificate.', 'Provide ΔP monitoring and access for element removal.']),
    maint=dict(routine=[M('Check ΔP or flow restriction.', 'element', 'monthly')], periodic=[M('Remove and clean the element.', 'element', 'per fouling, e.g. annually')],
               overhaul=[M('Replace element after a flame event or damage.', 'element')], lubrication=['None.']),
    failures=[F('Element fouling/blocking', ['High ΔP, tank pressure/vacuum problems'], ['Polymerising vapours, dust, ice'], ['Clean; heat trace'], 'element'),
              F('Flame transmission', ['Fire downstream'], ['Wrong gas group, damaged element, stabilised burning beyond rating'], ['Correct selection, temperature sensor'], 'element')],
    quiz=[Q('How does a flame arrestor stop a flame?', ['By water spray', 'By cooling it in narrow metal channels', 'By closing a valve', 'By nitrogen'], 1, 'Heat transfer quenching.'),
          Q('What determines the element gap size?', ['Pipe colour', 'Gas explosion group (MESG)', 'Flow direction', 'Bolt size'], 1, 'Narrower for hydrogen (IIC).'),
          Q('Rising pressure drop across an arrestor indicates…', ['Normal operation', 'Element fouling', 'Higher flame speed', 'Leak'], 1, 'Clean the element.')],
)

MODULES['rupture_disc'] = mod(
    definition=('A rupture (bursting) disc is a non-reclosing pressure-relief device: a thin membrane that bursts at a specified pressure and temperature, '
                'instantly opening a relief path. It reacts in milliseconds and is leak-tight before bursting, so it is used for rapid pressure rise, '
                'toxic/corrosive service, or under a safety valve to protect it.'),
    applications=['Reactors and pressure vessels', 'Upstream of safety valves (isolation from corrosive fluid)', 'Compressed-gas systems', 'Dust explosion venting (vent panels)'],
    key_points=['One-shot: must be replaced after bursting', 'Burst pressure has a tolerance and depends on temperature', 'Operating ratio limits life', 'Correct orientation is essential'],
    principle=[step('The disc is clamped in its holder between flanges.', 'holder'), step('As system pressure rises, the domed disc is strained.', 'disc', operate=True, overlay='pressure'),
               step('At burst pressure it tears along the score lines into petals.', 'disc'), step('The petals fold open and the full bore relieves the pressure.', 'pipework', overlay='flow')],
    curve='Non-reclosing; full opening at burst. Flow resistance expressed as KR for sizing.',
    params=vp(P('DN 6 – 900'), P('Burst ≈ 0.1 to > 1,000 (type dependent)', 'bar g'), P('-200 to 500+', '°C'), P('Full bore after burst; size per API 520 / ISO 4126-6', ''),
              operating_ratio=P('≈ 70 – 95 % of burst pressure (type dependent)', '')),
    install=_V_INSTALL | dict(piping=['Install with the flow arrow towards the outlet; never upside down.', 'Where a disc is below a safety valve, monitor the space between them (telltale gauge).']),
    maint=dict(routine=[M('Check telltale gauge/burst indicator.', 'gauge', 'daily')], periodic=[M('Replace discs on a planned interval (fatigue, corrosion).', 'disc', 'per plan')],
               overhaul=[M('Inspect holder seating surfaces when replacing.', 'holder')], lubrication=['None — do not grease seating faces.']),
    failures=[F('Premature burst', ['Burst below set pressure'], ['Fatigue from pressure cycling, corrosion, damaged on handling'], ['Lower operating ratio, better material'], 'disc'),
              F('Failure to burst at set', ['Overpressure'], ['Installed upside down, wrong disc'], ['Check tag and orientation'], 'holder')],
    quiz=[Q('A rupture disc is…', ['Reclosing', 'Non-reclosing (one-shot)', 'A control valve', 'A flowmeter'], 1, 'Replace after bursting.'),
          Q('Why fit a rupture disc below a safety valve?', ['To increase flow', 'To isolate the valve from corrosive/sticky process fluid and stop leakage', 'To lower set pressure', 'It is never done'], 1, 'Protects the SV.'),
          Q('What is the operating ratio?', ['Burst/operating', 'Operating pressure as a percentage of burst pressure', 'Flow/area', 'Temperature ratio'], 1, 'Limits life.', 'intermediate')],
)

MODULES['sight_glass'] = mod(
    definition=('A sight glass is a window built into piping or vessels so that operators can see the process fluid — whether it is flowing, its colour and clarity, '
                'bubbles, foam or level. The flow-through, double-window type allows light to shine through from the opposite side.'),
    applications=['Visual check of flow and liquid quality', 'Condensate and steam lines', 'Chemical and pharmaceutical batch processes', 'Filling and transfer lines'],
    key_points=['Glass is the weak point — rating and thermal shock limits', 'Even bolting of cover rings', 'Shields/guards where breakage is a hazard'],
    principle=[step('Fluid flows through the chamber.', 'body', overlay='flow'), step('Toughened glass windows let the operator see inside.', 'windows'),
               step('Bubbles and colour indicate gas entrainment or contamination.', 'bubbles', operate=True), step('Cover rings clamp the glass on gaskets.', 'cover_rings')],
    curve='—',
    params=vp(P('DN 15 – 200'), P('up to ~16 – 40', 'bar'), P('up to ~280 (borosilicate)', '°C'), P('Full bore through body', '')),
    install=_V_INSTALL, maint=dict(routine=[M('Check glass for cracks, chips and etching.', 'windows', 'monthly')], periodic=[M('Clean glass.', 'windows', 'as needed')],
                                   overhaul=[M('Replace glass and gaskets; re-torque evenly.', 'cover_rings')], lubrication=['None.']),
    failures=[F('Glass breakage', ['Leak, broken window'], ['Thermal shock, uneven bolting, impact'], ['Replace; fit guard'], 'windows'),
              F('Etched/fogged glass', ['Cannot see'], ['Caustic/HF attack'], ['Mica/PTFE shields'], 'windows')],
    quiz=[Q('Main purpose of a sight glass?', ['Measure flow rate', 'Visual inspection of the process fluid', 'Throttle flow', 'Relieve pressure'], 1, 'Window.'),
          Q('Why must cover rings be tightened evenly?', ['Looks', 'Uneven load can crack the glass', 'Faster', 'No reason'], 1, 'Stress.'),
          Q('Caustic service can…', ['Clean glass', 'Etch glass — use mica/PTFE shields', 'Strengthen glass', 'Nothing'], 1, 'Alkali attack.')],
)

MODULES['flow_indicator'] = mod(
    definition=('A flow indicator gives a simple visual confirmation that liquid is flowing. In the rotor type, a paddle wheel behind a window turns when liquid passes; '
                'the faster it spins, the higher the flow. It is not a measuring instrument but an essential check on cooling, seal-flush and lube lines.'),
    applications=['Seal-flush and quench lines', 'Cooling water to bearings and coolers', 'Lubrication returns', 'Chemical dosing lines'],
    key_points=['Indicates, does not measure', 'Rotor, flapper, ball or variable-area types', 'Window must be kept clean'],
    principle=[step('Liquid enters the body.', 'body', overlay='flow'), step('Flow passes under the rotor and drives its paddles.', 'rotor', operate=True),
               step('The spinning rotor is seen through the window.', 'windows')],
    curve='Rotor speed roughly proportional to flow (indicative only).',
    params=vp(P('DN 8 – 100'), P('up to ~16 – 40', 'bar'), P('up to ~150 (glass/rotor material)', '°C'), P('Low pressure drop', '')),
    install=_V_INSTALL, maint=dict(routine=[M('Confirm rotor turns.', 'rotor', 'each shift')], periodic=[M('Clean window and rotor.', 'windows', 'as needed')],
                                   overhaul=[M('Replace rotor/bearing pins.', 'rotor')], lubrication=['None.']),
    failures=[F('Rotor jammed', ['No rotation with flow'], ['Debris, scale'], ['Clean; fit strainer'], 'rotor'), F('Window fouled', ['Cannot see'], ['Deposits'], ['Clean'], 'windows')],
    quiz=[Q('A rotor flow indicator…', ['Measures exact flow', 'Shows that flow is present', 'Controls flow', 'Relieves pressure'], 1, 'Indication only.'),
          Q('Typical use?', ['Seal flush and cooling lines', 'Gas pipelines', 'Steam traps', 'Fire mains'], 0, 'Confirms small critical flows.'),
          Q('A jammed rotor with flow means…', ['No flow', 'Debris or fouling — clean it', 'Correct operation', 'High flow'], 1, 'Maintenance needed.')],
)

_P_INSTALL = dict(foundation=['Support pipework at the intervals and on the support types shown on the piping drawings; allow for thermal expansion.'],
                  alignment=['Fit up joints within code tolerances; do not force flanges.'],
                  piping=['Follow the isometric drawings and line list (size, class, material).', 'Install gaskets and bolting of the specified type; tighten per ASME PCC-1.'],
                  commissioning=['Flush/blow the line, then hydrotest or pneumatic test to code.', 'Reinstate instruments and remove test blinds.'])

MODULES['pipe_spool'] = mod(
    definition=('A pipe spool is a prefabricated assembly of pipe, fittings and flanges welded in a workshop and installed as one piece on site. Shop fabrication gives '
                'controlled welding, inspection and coating, shortens site work, and every spool is traceable through its spool number, weld map and inspection records.'),
    applications=['Process plants (refineries, alumina, chemicals)', 'Power and utility piping', 'Skids and modules', 'Pipeline stations'],
    key_points=['Defined by isometric and spool drawings', 'Shop butt welds + field flanged joints', 'Weld map, NDT and test records for traceability', 'Transport size limits'],
    principle=[step('Straight pipe and a long-radius elbow change direction.', 'spool_pipe', overlay='flow'), step('A tee and reducer form a smaller branch.', 'tee_reducer', overlay='flow'),
               step('Weld-neck flanges let the spool bolt into the line.', 'flanges'), step('At the field joint a gasket and stud bolts seal the flanges.', 'mating_joint'),
               step('The tag identifies line, spool and weld numbers.', 'spool_tag', cut=False)],
    curve='—',
    params=vp(P('DN 15 – 1,200+'), P('Per piping class (e.g. ASME 150 – 2500)', ''), P('Per material and class', '°C'), P('Pressure loss per elbow/tee K-values', ''),
              weld_examination=P('5 – 100 % RT/UT per fluid service (ASME B31.3)', '')),
    install=_P_INSTALL, maint=dict(routine=[M('Check flange joints for leaks.', 'mating_joint', 'per inspection plan')], periodic=[M('Thickness survey at elbows and tees.', 'spool_pipe', 'per RBI')],
                                   overhaul=[M('Replace gaskets when joints are broken.', 'mating_joint')], lubrication=['Lubricate stud threads at assembly (specified compound).']),
    failures=[F('Flange leakage', ['Weeping joint'], ['Uneven bolting, damaged face, wrong gasket'], ['Retighten per PCC-1; replace gasket'], 'mating_joint'),
              F('Weld defect', ['Leak at weld, NDT indication'], ['Poor fit-up or procedure'], ['Repair per WPS, re-examine'], 'spool_pipe'),
              F('Erosion-corrosion', ['Wall thinning'], ['High velocity at elbows'], ['Thicker wall, lower velocity'], 'tee_reducer')],
    quiz=[Q('Why prefabricate spools?', ['Cheaper paint', 'Better weld quality and inspection, less site work', 'They are lighter', 'No reason'], 1, 'Shop conditions.'),
          Q('What document shows the spool to be built?', ['P&ID', 'Isometric / spool drawing', 'Pump curve', 'Data sheet'], 1, 'Isometrics.'),
          Q('Which code governs process piping fabrication?', ['ASME B31.3', 'API 610', 'NFPA 20', 'ISO 5167'], 0, 'Process piping.')],
)

MODULES['pipe_manifold'] = mod(
    definition=('A pipe manifold (header) is a large pipe that distributes flow to — or collects flow from — several branch lines. Each branch has an isolation valve so it '
                'can be opened, closed or maintained independently. Headers keep velocities low so all branches receive similar pressure.'),
    applications=['Cooling-water and steam distribution', 'Pump suction and discharge headers', 'Gas and chemical distribution', 'Well-test and sampling manifolds'],
    key_points=['Header area ≥ sum of branch areas helps even distribution', 'Branch reinforcement per code', 'Drains at low points, vents at high points'],
    principle=[step('Flow enters the header.', 'header', overlay='flow'), step('Opening a branch valve lets flow into that branch.', 'lever_1', operate=True),
               step('Branches open in sequence and draw from the common header.', 'branch_valves', overlay='flow'), step('The gauge shows header pressure; the drain empties it.', 'gauge_drain')],
    curve='Header pressure falls slightly along its length as branches draw flow.',
    params=vp(P('Header DN 50 – 1,000'), P('Per piping class', ''), P('Per service', '°C'), P('Sum of branch flows; velocity ~1–3 m/s for liquids (typical)', '')),
    install=_P_INSTALL, maint=dict(routine=[M('Check branch valve positions and leaks.', 'branch_valves', 'per round')], periodic=[M('Drain sediment.', 'gauge_drain', 'monthly')],
                                   overhaul=[M('Inspect header for corrosion at dead legs.', 'header')], lubrication=_V_LUBE),
    failures=[F('Uneven distribution', ['Far branches starved'], ['Undersized header'], ['Larger header, balancing valves'], 'header'),
              F('Dead-leg corrosion', ['Pitting'], ['Stagnant ends'], ['Eliminate dead legs, flush'], 'header')],
    quiz=[Q('What does a manifold do?', ['Measures flow', 'Distributes or collects flow among several branches', 'Relieves pressure', 'Heats fluid'], 1, 'Header.'),
          Q('Why keep header velocity low?', ['Noise only', 'So all branches see similar pressure', 'To save paint', 'No reason'], 1, 'Even distribution.'),
          Q('Ball-valve lever in line with the pipe means…', ['Closed', 'Open', 'Half open', 'Broken'], 1, 'Quarter-turn convention.')],
)

_FM_INSTALL = dict(foundation=['Support the meter run; avoid vibration at the transmitter.'],
                   alignment=['Centre the element precisely in the pipe bore (eccentricity affects accuracy).'],
                   piping=['Provide straight upstream/downstream lengths per ISO 5167 for the fittings present, or use a flow conditioner.',
                           'Slope impulse lines: liquids — transmitter below taps; gas — transmitter above taps.'],
                   commissioning=['Fill/vent impulse lines; zero the transmitter with the equalising valve.', 'Check the flow computation (β, density, units).'])

MODULES['orifice_plate'] = mod(
    definition=('An orifice plate flowmeter is a plate with a precise sharp-edged hole clamped between flanges. The restriction accelerates the flow and lowers its static '
                'pressure; a DP transmitter measures the pressure difference across the plate, and flow is calculated from the square root of ΔP (ISO 5167-2). '
                'It is simple, inexpensive and standardised, but causes a high permanent pressure loss.'),
    applications=['Process flow measurement (liquids, gases, steam)', 'Natural gas metering (AGA 3)', 'Pump minimum-flow detection', 'Restriction orifices (pressure reduction)'],
    key_points=['Flow ∝ √ΔP — turndown ~3–4:1 per transmitter', 'Sharp edge and straight runs govern accuracy', 'Bevel faces downstream', 'Permanent loss ~40–90 % of ΔP depending on β'],
    principle=[step('Flow approaches the plate with a developed velocity profile.', 'meter_run', overlay='flow'), step('The bore forces the flow to contract and accelerate.', 'plate', overlay='flow', operate=True),
               step('Pressure is lowest at the vena contracta just downstream.', 'plate', overlay='pressure'), step('Taps in the orifice flanges transmit p1 and p2 to the DP transmitter.', 'dp_transmitter'),
               step('Downstream, pressure partly recovers; the rest is permanent loss.', 'meter_run', overlay='pressure')],
    curve='ΔP rises with flow²; flow computed as q = K·√ΔP.',
    params=vp(P('DN 50 – 1,000 (ISO 5167 range)'), P('Per flange class', ''), P('Per material', '°C'), P('β = 0.1 – 0.75; uncertainty of C ≈ 0.5 – 1 % (ISO 5167-2)', ''),
              turndown=P('≈ 3 – 4:1 (single DP transmitter)', '')),
    install=_FM_INSTALL, maint=dict(routine=[M('Check transmitter zero.', 'dp_transmitter', 'monthly')], periodic=[M('Pull and inspect plate edge and flatness.', 'plate', 'annually')],
                                    overhaul=[M('Replace plate if edge is rounded or plate bowed.', 'plate')], lubrication=['None.']),
    failures=[F('Reading low', ['Under-reads'], ['Rounded/worn edge, plate installed backwards'], ['Replace/reinstall plate'], 'plate'),
              F('Erratic reading', ['Noisy ΔP'], ['Gas in liquid impulse lines, swirl'], ['Vent lines, add conditioner'], 'dp_transmitter'),
              F('Deposits', ['Drift'], ['Fouling upstream face'], ['Clean plate'], 'plate')],
    quiz=[Q('Flow through an orifice plate is proportional to…', ['ΔP', '√ΔP', 'ΔP²', '1/ΔP'], 1, 'Bernoulli: v ∝ √ΔP.'),
          Q('Where is the lowest pressure?', ['Upstream of the plate', 'At the vena contracta just downstream', 'Far downstream', 'In the transmitter'], 1, 'Narrowest jet.'),
          Q('Which device has the highest permanent pressure loss?', ['Venturi tube', 'Orifice plate', 'Flow nozzle', 'All equal'], 1, 'Abrupt expansion losses.'),
          Q('Beta ratio is…', ['d/D (bore/pipe diameter)', 'ΔP/p1', 'Flow/area', 'Temperature ratio'], 0, 'Geometry ratio.', 'intermediate')],
)

MODULES['flow_nozzle'] = mod(
    definition=('A flow nozzle is a differential-pressure flow element with a smoothly curved inlet and a cylindrical throat, installed between flanges. It is more rugged '
                'than an orifice plate, keeps its calibration at high velocities and temperatures, and has a lower permanent loss (ISO 5167-3).'),
    applications=['High-pressure steam and boiler feedwater', 'Power-plant performance tests (ASME PTC 6)', 'Erosive or high-velocity flows', 'Gas flows at high Reynolds number'],
    key_points=['No sharp edge to wear', 'Higher cost than orifice, lower than venturi', 'Throat tap or corner taps per standard'],
    principle=[step('Flow enters the curved nozzle inlet smoothly.', 'nozzle', overlay='flow'), step('Velocity is highest and pressure lowest in the throat.', 'nozzle', overlay='pressure', operate=True),
               step('The DP transmitter measures upstream and throat pressure.', 'dp_transmitter'), step('Downstream the jet expands with partial pressure recovery.', 'meter_run', overlay='flow')],
    curve='ΔP ∝ flow²; discharge coefficient C ≈ 0.98 – 0.99 at high Re.',
    params=vp(P('DN 50 – 600'), P('Per class — common in high-pressure steam', ''), P('Up to ~600 (alloy steel)', '°C'), P('β = 0.3 – 0.8; C ≈ 0.98+', '')),
    install=_FM_INSTALL, maint=dict(routine=[M('Check transmitter zero.', 'dp_transmitter', 'monthly')], periodic=[M('Inspect nozzle throat when line is open.', 'nozzle', 'at outages')],
                                    overhaul=[M('Replace gaskets; check nozzle alignment.', 'carrier_flanges')], lubrication=['None.']),
    failures=[F('Throat deposits', ['Reading drift'], ['Scaling (feedwater chemistry)'], ['Clean; improve water treatment'], 'nozzle'),
              F('Impulse line problems', ['Erratic reading'], ['Steam/condensate imbalance'], ['Condensate pots, fill lines'], 'dp_transmitter')],
    quiz=[Q('Why use a flow nozzle instead of an orifice on high-velocity steam?', ['Cheaper', 'Rugged curved inlet keeps calibration and has lower loss', 'Easier to install', 'No transmitter needed'], 1, 'No sharp edge to erode.'),
          Q('Where is pressure lowest in a flow nozzle?', ['Inlet', 'Throat', 'Upstream pipe', 'Transmitter'], 1, 'Highest velocity.'),
          Q('Which standard covers nozzles?', ['ISO 5167-3', 'API 610', 'ISO 2858', 'NFPA 20'], 0, 'ISO 5167-3.')],
)

MODULES['venturi_tube'] = mod(
    definition=('A venturi tube measures flow with a smooth convergent cone, a short throat and a long divergent cone. Velocity rises and pressure falls in the throat '
                '(Bernoulli); the gentle diffuser recovers most of that pressure, so the permanent loss is only about 5–20 % of the measured ΔP — the lowest of '
                'the DP meters. It also tolerates dirty liquids (ISO 5167-4).'),
    applications=['Large water and wastewater mains', 'Cooling-water and raw-water intakes', 'Slurry and dirty liquids', 'Energy-sensitive pumping systems'],
    key_points=['Lowest permanent loss of DP meters', 'Long and costly but durable', 'Piezometer rings average pressure around the circumference'],
    principle=[step('Flow enters the inlet cylinder (upstream tap).', 'venturi', overlay='flow'), step('The convergent cone accelerates the flow; pressure falls.', 'venturi', overlay='pressure', operate=True),
               step('In the throat velocity is highest and pressure lowest (throat tap).', 'dp_transmitter'),
               step('The divergent cone slows the flow and recovers most of the pressure.', 'venturi', overlay='pressure')],
    curve='ΔP ∝ flow²; C ≈ 0.98 – 0.995 (ISO 5167-4).',
    params=vp(P('DN 50 – 1,200+'), P('Per class', ''), P('Per material', '°C'), P('β = 0.3 – 0.75; permanent loss ≈ 5 – 20 % of ΔP', '')),
    install=_FM_INSTALL, maint=dict(routine=[M('Check zero and impulse lines.', 'dp_transmitter', 'monthly')], periodic=[M('Flush piezometer rings and taps.', 'venturi', 'quarterly')],
                                    overhaul=[M('Inspect throat for deposits.', 'venturi')], lubrication=['None.']),
    failures=[F('Blocked taps', ['Flat or erratic reading'], ['Solids in taps'], ['Rod out/flush taps'], 'venturi'), F('Deposits in throat', ['Over-reading'], ['Scaling'], ['Clean'], 'venturi')],
    quiz=[Q('Why does a venturi tube have low permanent pressure loss?', ['Sharp edge', 'Gradual diffuser recovers pressure', 'No throat', 'It is short'], 1, 'Gentle divergence.'),
          Q('Bernoulli says that where velocity rises…', ['Static pressure rises', 'Static pressure falls', 'Nothing changes', 'Temperature rises'], 1, 'Energy conservation.'),
          Q('Which DP meter suits large water mains best for energy saving?', ['Orifice', 'Venturi tube', 'Needle valve', 'Rupture disc'], 1, 'Low loss.')],
)

_PIG_INSTALL = dict(foundation=['Barrel on saddles/foundations designed for pig impact and thermal movement.'], alignment=['Align barrel, reducer and pipeline so pigs pass freely.'],
                    piping=['Trap valve must be full bore; kicker/bypass sized to drive the pig.', 'Provide vents, drains, pressure gauge and pig signaller.'],
                    commissioning=['Gauge-pig run to prove bore.', 'Test door interlock and pressure-warning device.'])

MODULES['pig_launcher'] = mod(
    definition=('A pig launcher is the pipeline trap used to insert a pig — a cleaning, batching, gauging or in-line inspection device — into a flowing pipeline. '
                'The pig is loaded through a quick-opening closure into an oversize barrel; after the door is closed and the barrel pressurised, valves are lined up '
                'so flow through the kicker line enters behind the pig and pushes it through the reducer into the pipeline.'),
    applications=['Oil, gas and product pipelines', 'Slurry and water pipelines', 'Pipeline commissioning (dewatering, drying)', 'In-line inspection (intelligent pigs)'],
    key_points=['Never open the door under pressure — interlock', 'Strict line-up sequence', 'Barrel oversize to load the pig'],
    principle=[step('The pig is loaded through the closure door into the barrel.', 'closure', operate=False), step('The door is closed; the barrel is filled, vented and pressurised.', 'barrel'),
               step('The trap valve is opened and the kicker valve admits flow behind the pig.', 'valves', overlay='flow'),
               step('Flow pushes the pig through the reducer into the pipeline.', 'pig', operate=True), step('The signaller confirms the pig has left.', 'pig_signaller')],
    curve='Pig speed typically ~1 – 5 m/s (liquids) depending on flow and pig type (verify for inspection pigs).',
    params=vp(P('Pipeline DN 100 – 1,400; barrel ~1–2 sizes larger'), P('Per pipeline class', ''), P('Per service', '°C'), P('Kicker flow sized to drive the pig', '')),
    install=_PIG_INSTALL, maint=dict(routine=[M('Check door seal and interlock before each use.', 'closure', 'each operation')], periodic=[M('Function-test valves and signaller.', 'valves', 'quarterly')],
                                     overhaul=[M('Inspect barrel for corrosion and debris.', 'barrel')], lubrication=['Closure hinge and locking mechanism per manufacturer.']),
    failures=[F('Pig stuck in reducer/trap', ['Pig not launched, ΔP rises'], ['Insufficient kicker flow, wrong pig size'], ['Increase differential, correct pig'], 'pig'),
              F('Door seal leak', ['Leak at closure'], ['Damaged seal'], ['Replace seal'], 'closure')],
    quiz=[Q('What drives the pig out of the launcher?', ['A winch', 'Flow through the kicker line behind the pig', 'Gravity', 'A motor'], 1, 'Differential pressure.'),
          Q('Most important safety rule?', ['Paint the barrel', 'Never open the closure while pressurised', 'Use a big pig', 'Run fast'], 1, 'Interlocks.'),
          Q('Why is the barrel oversized?', ['Looks', 'To load the pig and let flow get behind it', 'To slow the flow', 'No reason'], 1, 'Loading and kick.')],
)

MODULES['pig_receiver'] = mod(
    definition=('A pig receiver is the trap at the downstream end of a pipeline section that catches the arriving pig and the debris it pushes. Flow is routed through '
                'the barrel so the pig is carried in; after it arrives, the trap is isolated, drained and depressurised, and the pig is removed through the closure door.'),
    applications=['Oil, gas and product pipelines', 'Slurry pipelines', 'Pipeline cleaning and inspection campaigns'],
    key_points=['Barrel long enough for pig trains and debris', 'Check for hazardous deposits (pyrophoric iron sulphide, NORM) before opening', 'Door interlock'],
    principle=[step('The trap valve is opened so flow passes through the barrel.', 'valves', overlay='flow'), step('The arriving pig is carried through the reducer into the barrel.', 'pig', operate=True),
               step('Flow leaves via the outlet line back to the station.', 'pipeline_kicker', overlay='flow'), step('The signaller confirms arrival; the trap is isolated, drained and vented.', 'pig_signaller'),
               step('The closure is opened and the pig and debris are removed.', 'closure')],
    curve='—',
    params=vp(P('Pipeline DN 100 – 1,400'), P('Per pipeline class', ''), P('Per service', '°C'), P('—', '')),
    install=_PIG_INSTALL, maint=dict(routine=[M('Check closure seal and interlock.', 'closure', 'each operation')], periodic=[M('Clean barrel and drains.', 'barrel', 'after each run')],
                                     overhaul=[M('Inspect valves for seat damage from debris.', 'valves')], lubrication=['Closure mechanism.']),
    failures=[F('Debris blocking drains', ['Cannot drain trap'], ['Wax, sludge'], ['Larger drains, flushing'], 'barrel'), F('Pyrophoric fire on opening', ['Smouldering debris'], ['Iron sulphide exposed to air'], ['Keep wet, inert'], 'closure')],
    quiz=[Q('What must be done before opening a receiver door?', ['Nothing', 'Isolate, drain, depressurise and check for hazardous deposits', 'Increase flow', 'Open the kicker'], 1, 'Safe isolation.'),
          Q('Why might receiver debris be hazardous?', ['It is cold', 'It may contain pyrophoric iron sulphide or NORM', 'It is magnetic', 'It is never hazardous'], 1, 'Pipeline deposits.'),
          Q('How does the pig enter the receiver?', ['Pulled by cable', 'Carried by the flow through the open trap valve', 'Gravity', 'Manually'], 1, 'Flow-driven.')],
)

MODULES['pipe_insulation_system'] = mod(
    definition=('A pipe insulation system reduces heat loss from hot lines (or heat gain to cold lines), keeps process temperatures stable, protects people from hot surfaces '
                'and prevents condensation. A hot-service system typically has an anti-corrosion coating, one or more insulation layers with staggered joints, and a '
                'weatherproof metal cladding with bands, plus insulated supports.'),
    applications=['Steam and condensate lines', 'Hot process lines (alumina digestion liquor, oil)', 'Cold/cryogenic lines (with vapour barrier)', 'Personnel protection'],
    key_points=['Wet insulation loses most of its insulating value', 'Corrosion under insulation (CUI) is a major hazard', 'Thickness from economic/process/safety criteria'],
    principle=[step('Hot fluid flows in the pipe.', 'process_pipe', overlay='flow'), step('The coating protects the steel from corrosion under insulation.', 'coating'),
               step('Insulation layers slow heat flow from the pipe surface.', 'insulation', overlay='heat_loss'), step('Cladding keeps rain out and protects the insulation.', 'cladding'),
               step('Insulated shoes support the pipe without a thermal bridge.', 'support')],
    curve='Heat loss falls steeply with the first centimetres of insulation, then more slowly (economic thickness).',
    params=vp(P('Pipe DN 15 – 1,200'), P('—', ''), P('-196 to 650 (material dependent)', '°C'), P('Thermal conductivity k ≈ 0.03 – 0.07 W/m·K (mineral wool, mean temp dependent)', ''),
              surface_temperature=P('≤ ~55–60 for personnel protection (verify local rules)', '°C')),
    install=_P_INSTALL | dict(piping=['Coat and dry the pipe before insulating.', 'Stagger joints between layers; overlap cladding to shed water; seal penetrations.']),
    maint=dict(routine=[M('Inspect cladding for damage and open seams.', 'cladding', 'per round')], periodic=[M('Thermographic survey for hot spots.', 'insulation', 'annually')],
               overhaul=[M('Remove insulation at suspect locations for CUI inspection.', 'coating')], lubrication=['None.']),
    failures=[F('Corrosion under insulation (CUI)', ['Hidden wall loss, leaks'], ['Water ingress through damaged cladding', 'Coating breakdown'], ['Repair cladding, coat pipe, inspect per RBI'], 'coating'),
              F('Wet / damaged insulation', ['Hot spots, energy loss'], ['Mechanical damage, rain'], ['Replace insulation and seal cladding'], 'insulation')],
    quiz=[Q('Why must insulation stay dry?', ['Colour', 'Water destroys its insulating value and causes CUI', 'Weight only', 'No reason'], 1, 'Wet insulation conducts heat.'),
          Q('What does the cladding do?', ['Insulate', 'Keep weather out and protect insulation', 'Support the pipe', 'Heat the pipe'], 1, 'Jacketing.'),
          Q('CUI means…', ['Cold under ice', 'Corrosion under insulation', 'Cladding unit index', 'Certified insulation'], 1, 'Major integrity hazard.')],
)

MODULES['pipe_tracing_system'] = mod(
    definition=('A pipe tracing system supplies heat to a pipe to replace what it loses through its insulation, keeping the product above its freezing, congealing or '
                'crystallisation temperature. Steam tracing runs small tubes of steam alongside the pipe, drained by a trap; electric tracing uses a self-regulating '
                'heating cable controlled by a thermostat. Both are covered by insulation.'),
    applications=['Caustic and liquor lines in alumina refineries', 'Heavy fuel oil, bitumen and sulphur', 'Water and instrument lines in freezing climates', 'Viscous chemicals'],
    key_points=['Tracing maintains temperature; it does not heat up cold lines quickly', 'Steam: trap at each tracer end; electric: earth-leakage protection', 'Insulation is part of the system'],
    principle=[step('Product flows in the process pipe.', 'process_pipe', overlay='flow'), step('Steam flows in the tracer tube and condenses, releasing heat to the pipe.', 'steam_tracer', overlay='heat_input'),
               step('The tracer trap drains condensate.', 'tracer_trap'), step('Electric cable spiralled on the pipe heats it; its output falls as the pipe warms.', 'electric_tracer', overlay='heat_input'),
               step('Insulation keeps the heat in.', 'insulation')],
    curve='Heat input matched to heat loss at design ambient; self-regulating cable output decreases with temperature.',
    params=vp(P('Pipe DN 15 – 600'), P('Steam 3 – 10 (tracer)', 'bar g'), P('Maintain ~5 – 150 (product dependent)', '°C'), P('Electric: ~10 – 60 W/m (cable dependent)', '')),
    install=_P_INSTALL | dict(piping=['Steam tracers: free-draining, one trap per circuit, no pockets.', 'Electric: fix cable with tape/bands, install end seals and power connection per certification.']),
    maint=dict(routine=[M('Check product temperature / thermostat.', 'electric_tracer', 'daily in cold season')], periodic=[M('Survey tracer traps.', 'tracer_trap', 'before winter')],
               overhaul=[M('Insulation-resistance test of heating circuits.', 'electric_tracer')], lubrication=['None.']),
    failures=[F('Line freezing / plugging', ['Product solidifies'], ['Failed trap, cable fault, wet insulation'], ['Repair circuit, replace insulation'], 'steam_tracer'),
              F('Ground fault trip', ['Circuit trips'], ['Damaged cable or seals'], ['Locate and repair'], 'electric_tracer')],
    quiz=[Q('Purpose of tracing?', ['Increase flow', 'Replace heat lost through insulation to keep product warm', 'Measure temperature', 'Cool the pipe'], 1, 'Temperature maintenance.'),
          Q('What drains a steam tracer?', ['A pump', 'A steam trap at the tracer end', 'A vent', 'A filter'], 1, 'Trap per circuit.'),
          Q('Self-regulating cable output…', ['Rises with temperature', 'Falls as the pipe warms', 'Is constant', 'Is zero'], 1, 'Polymer matrix.')],
)
