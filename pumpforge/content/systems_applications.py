"""Learning content — special-purpose systems (29–31) and industrial application modules (32–39)."""
from pumpforge.learning import mod, step, P, F, Q, M
from content.rotodynamic_a import _ALIGN_H, _PIPE_H, _COMM_C

MODULES = {}

MODULES['jet_pump_eductor'] = mod(
    definition=('A jet pump (eductor or ejector) has no moving parts. A motive fluid under pressure accelerates through a converging nozzle into a high-velocity jet; '
                'the low static pressure and momentum of the jet entrain the suction fluid, the two streams mix in the throat, and the diffuser converts velocity back into pressure.'),
    applications=['Tank mixing and sludge suspension', 'Priming centrifugal pumps and vacuum duties', 'Deep-well jet pumps for domestic water', 'Chemical induction and dewatering', 'Steam ejectors for condenser vacuum'],
    key_points=['No moving parts — robust and simple', 'Efficiency typically 10–35 %', 'Performance set by area ratio and flow ratio', 'Handles solids, corrosives and gas'],
    principle=[step('Motive liquid accelerates through the converging nozzle into a fast jet.', 'motive_nozzle', overlay='flow'),
               step('Around the jet the pressure falls, drawing suction fluid into the suction chamber.', 'body', overlay='flow'),
               step('In the throat the streams exchange momentum and mix.', 'body', overlay='flow'),
               step('The diffuser slows the mixture and recovers pressure.', 'body', overlay='flow'), step('Gauges on motive, suction and discharge show the operating point.', 'instruments', cut=False)],
    curve='Entrained flow falls as discharge back-pressure rises; performance depends on the nozzle-to-throat area ratio.',
    params=dict(flow=P('depends on motive flow; entrainment ratio ~0.5 – 4', 'suction/motive'), head=P('—'), pressure=P('motive 2 – 10 typical (liquid)', 'bar'), speed=P('—', '', 'no moving parts'),
                efficiency=P('10 – 35', '%'), extra={'suction_lift': P('up to ~7', 'm (liquid motive)')}),
    install=dict(foundation=['Pipe-supported.'], alignment=['Straight pipe runs before motive and after discharge.'], piping=['Avoid restrictions on the discharge; size motive supply for the design pressure.'],
                 commissioning=['Set motive pressure; check suction and discharge pressures against the design.']),
    maint=dict(routine=[M('Monitor motive and suction pressure.', 'instruments', 'daily')], periodic=[M('Measure nozzle bore wear.', 'motive_nozzle', 'annually')],
               overhaul=[M('Inspect throat for erosion.', 'body')], lubrication=['None.']),
    failures=[F('Nozzle wear', ['Higher motive flow, lower suction'], ['Erosion'], ['Replace nozzle'], 'motive_nozzle'), F('Blockage', ['No suction'], ['Debris in nozzle'], ['Strainer on motive line'], 'motive_nozzle'),
              F('Back-flow into suction', ['Motive fluid exits suction'], ['Discharge blocked'], ['Clear discharge; fit check valve'], 'body')],
    quiz=[Q('What creates suction in an eductor?', ['An impeller', 'The high-velocity motive jet', 'A piston', 'A vacuum pump'], 1, 'Jet entrainment.'),
          Q('Typical eductor efficiency?', ['80–90 %', '10–35 %', '100 %', '50–60 %'], 1, 'Mixing losses are large.'),
          Q('Main advantage?', ['High efficiency', 'No moving parts', 'Low motive flow', 'High head'], 1, 'Very robust.')],
)

MODULES['airlift_pump'] = mod(
    definition=('An airlift pump injects compressed air near the bottom of a submerged riser pipe. The air–water mixture inside the riser is lighter than the surrounding water, '
                'so the heavier outside water column pushes it up and out at the top. It has no moving parts in the liquid.'),
    applications=['Wastewater treatment: sludge return and scum removal', 'Aquaculture water circulation', 'Groundwater sampling and well development', 'Dredging and sand lifting'],
    key_points=['Lift depends on submergence ratio', 'Gentle, clog-free', 'Low efficiency', 'Requires compressed air'],
    principle=[step('The blower supplies compressed air to the foot piece at the bottom of the riser.', 'blower'), step('Air bubbles mix with water in the riser, lowering its density.', 'air_bubbles'),
               step('The denser water outside the riser pushes the mixture upward.', 'riser_pipe', overlay='flow'), step('At the top the separator releases the air and the water discharges.', 'separator', overlay='flow')],
    curve='Water flow rises with air flow to a maximum, then falls; higher submergence ratio gives better efficiency.',
    params=dict(flow=P('small to large — depends on riser diameter and air flow'), head=P('lift up to several metres; deep wells more', 'm'), pressure=P('air pressure ≥ submergence head', 'bar'),
                speed=P('—'), efficiency=P('~20 – 50', '%'), extra={'submergence_ratio': P('~0.4 – 0.7', 'submergence / (submergence + lift)')}),
    install=dict(foundation=['Riser fixed in the tank or well.'], alignment=['Riser vertical.'], piping=['Air line with check valve and control valve.'], commissioning=['Adjust air flow for the required water flow.']),
    maint=dict(routine=[M('Check air flow and pressure.', 'air_controls', 'daily')], periodic=[M('Clean foot piece/diffuser.', 'foot_piece', 'monthly')], overhaul=[M('Service blower.', 'blower')],
               lubrication=['Blower per manual.']),
    failures=[F('Reduced flow', ['Less discharge'], ['Clogged foot piece, low submergence'], ['Clean; raise level'], 'foot_piece'), F('Blower failure', ['No air'], ['Filter blocked'], ['Service blower'], 'blower')],
    quiz=[Q('Why does water rise in an airlift riser?', ['A propeller lifts it', 'The air–water mixture is lighter than the surrounding water', 'Vacuum at the top', 'A piston'], 1, 'Density difference.'),
          Q('Submergence ratio is…', ['Air/water ratio', 'Submergence divided by (submergence + lift)', 'Riser length/diameter', 'Lift/air pressure'], 1, 'Higher ratio → better efficiency.'),
          Q('Main advantage in wastewater?', ['High head', 'No moving parts in sludge; clog-free', 'High efficiency', 'No air needed'], 1, 'Gentle and robust.')],
)

MODULES['archimedes_screw_pump'] = mod(
    definition=('An Archimedes screw pump is a large, slowly rotating screw set at an incline in an open trough. Each turn of the flights traps a pocket of water and lifts it up the slope to discharge at the top. '
                'It handles large flows at low lift, passes debris and is self-regulating: flow follows the inlet level.'),
    applications=['Wastewater treatment plant inlet lift', 'Storm water and land drainage', 'Return activated sludge', 'Hydropower (reverse operation as a generator)'],
    key_points=['Low speed (20–100 rpm)', 'Self-regulating with inlet level', 'Clog-free; gentle on fish', 'Lift limited (~8–10 m per screw)'],
    principle=[step('Water at the lower basin fills the pockets between flights at the bottom of the screw.', 'lower_basin', overlay='flow'),
               step('The rotating screw lifts each pocket up the trough.', 'screw', overlay='flow'), step('Pockets empty into the outlet channel at the top.', 'outlet_channel', overlay='flow'),
               step('A gear reducer and motor drive the screw at low speed; bearings at both ends carry it.', 'gear_reducer', cut=False)],
    curve='Flow rises with inlet level up to the "fill point"; efficiency stays high over a wide range of flows.',
    params=dict(flow=P('0.01 – 5+', 'm³/s'), head=P('up to ~8 – 10', 'm per screw'), pressure=P('—'), speed=P('20 – 100', 'rpm', 'lower for larger diameters'), efficiency=P('65 – 80', '%'),
                extra={'inclination': P('22 – 38', '°', '30–38° typical'), 'diameter': P('0.3 – 5', 'm')}),
    install=dict(foundation=['Concrete trough and supports for upper and lower bearings.'], alignment=['Screw-to-trough gap set precisely along the length.'],
                 piping=['Open channels; trash screens upstream optional.'], commissioning=['Check trough clearance and lower bearing lubrication.']),
    maint=dict(routine=[M('Check lower bearing lubrication.', 'lower_bearing', 'weekly')], periodic=[M('Change gearbox oil.', 'gear_reducer', 'per manual')],
               overhaul=[M('Inspect flights and trough gap.', 'screw')], lubrication=['Grease to the submerged lower bearing (automatic lubricator).']),
    failures=[F('Lower bearing failure', ['Noise, wobble'], ['Lubrication loss'], ['Restore lubrication'], 'lower_bearing'), F('Trough gap growth', ['Lower flow'], ['Wear of trough grout'], ['Regrout'], 'trough')],
    quiz=[Q('Why is an Archimedes screw "self-regulating"?', ['A VFD controls it', 'Flow automatically follows the inlet water level', 'It has a float valve', 'It is not'], 1, 'Pockets fill only as far as the level allows.'),
          Q('Typical rotation speed?', ['20–100 rpm', '1,500 rpm', '3,000 rpm', '10,000 rpm'], 0, 'Very slow.'),
          Q('Main limitation?', ['Low flow', 'Limited lift per screw', 'Cannot handle debris', 'Needs priming'], 1, 'About 8–10 m.')],
)

# ------------------------------------------------------------------ applications
MODULES['boiler_feedwater_pump'] = mod(
    definition=('A boiler feedwater pump delivers hot water from the deaerator to the boiler or steam generator at a pressure above drum pressure. '
                'It is a horizontal multistage centrifugal pump — ring-section (BB4) or barrel (BB5) — with a balance device for axial thrust and a minimum-flow line to protect it at low boiler demand.'),
    applications=['Utility and industrial power plants', 'Cogeneration and process steam boilers', 'Alumina refinery steam and power plants', 'Heat-recovery steam generators (HRSG)'],
    key_points=['Built from: Horizontal Multistage Pump (module 3)', 'Hot, near-saturated suction — NPSH critical (booster pump or elevated deaerator)', 'Warm-up and minimum-flow protection', 'Speed control by VFD, fluid coupling or turbine drive on large units'],
    principle=[step('Hot water from the deaerator enters the suction casing.', 'suction_casing', overlay='flow'), step('Five stages raise the pressure in equal steps.', 'stage_casing_3', overlay='pressure'),
               step('The balance drum and leak-off line balance the axial thrust.', 'balance_drum_bush', overlay='thrust'), step('Water leaves the discharge casing towards the economiser and boiler drum.', 'discharge_casing', overlay='flow')],
    curve='Steep multistage curve; feedwater control by speed or control valve; minimum flow recirculation at low load.',
    params=dict(flow=P('5 – 2,000+', 'm³/h'), head=P('300 – 3,000+', 'm'), pressure=P('30 – 300+', 'bar discharge'), speed=P('2,950 – 6,000+', 'rpm'), efficiency=P('70 – 85', '%'),
                extra={'feed_temperature': P('100 – 200+', '°C')}),
    install=dict(foundation=['Rigid foundation; thermal growth allowance; centreline-supported casings for hot service.'], alignment=_ALIGN_H + ['Hot alignment check.'],
                 piping=['Booster pump or sufficient deaerator elevation for NPSHa.', 'Automatic recirculation (minimum flow) valve on discharge.'], commissioning=['Warm up the casing evenly before start.'] + _COMM_C[1:]),
    maint=dict(routine=[M('Monitor balance leak-off and thrust bearing.', 'balance_leakoff_line', 'daily')], periodic=[M('Check recirculation valve operation.', 'discharge_casing', 'monthly')],
               overhaul=[M('Inspect first-stage impeller for cavitation; measure clearances.', 'impeller_1')], lubrication=['Forced or ring oil.']),
    failures=[F('Cavitation at first stage', ['Noise, pitting'], ['Deaerator level/pressure transients'], ['Booster pump; NPSH margin'], 'impeller_1'),
              F('Thermal shock', ['Rubbing, seizure'], ['Cold start on hot water'], ['Warm-up procedure'], 'stage_casing_1'), F('Balance device wear', ['Leak-off rise'], ['Erosion'], ['Overhaul'], 'balance_drum_bush')],
    quiz=[Q('Why is NPSH critical for feedwater pumps?', ['Water is near saturation at the suction', 'Flow is low', 'Water is cold', 'Pumps are small'], 0, 'Hot deaerated water flashes easily.'),
          Q('What protects the pump at low boiler demand?', ['Higher speed', 'Minimum-flow recirculation valve', 'Closing suction', 'Removing a stage'], 1, 'Keeps a minimum flow.'),
          Q('Which pump design is this application built on?', ['Axial flow', 'Horizontal multistage centrifugal', 'Gear pump', 'Peristaltic'], 1, 'Module 3.')],
)

MODULES['firewater_pump_package'] = mod(
    definition=('A firewater pump package supplies water to sprinklers, hydrants and deluge systems. Typically a listed horizontal split-case pump driven by a diesel engine (or electric motor) is installed with a controller, a jockey pump that maintains system pressure, a relief valve and a test header. '
                'NFPA 20 governs the arrangement and performance.'),
    applications=['Industrial plants and refineries', 'Alumina refineries and mineral processing plants', 'Warehouses and high-rise buildings', 'Terminals and tank farms'],
    key_points=['Built from: Horizontal Split Case Pump (module 2) or Vertical Turbine Pump (module 4)', 'Listed pumps: ≥150 % rated flow at ≥65 % rated pressure; shut-off ≤140 % (NFPA 20 — verify edition)',
                'Jockey pump keeps the network pressurised', 'Weekly churn tests and annual flow tests'],
    principle=[step('The jockey pump keeps the fire main pressurised against small leaks.', 'jockey_pump'), step('On a pressure drop the controller starts the main fire pump.', 'controllers'),
               step('The diesel engine drives the split-case pump through a drive shaft.', 'diesel_engine'), step('The split-case pump delivers the fire flow to the network.', 'impeller', overlay='flow'),
               step('The main relief valve and test header allow testing and protect against over-pressure.', 'test_header', cut=False)],
    curve='Listed fire-pump curve shape per NFPA 20: rated point, ≥65 % pressure at 150 % flow, ≤140 % pressure at shut-off.',
    params=dict(flow=P('25 – 5,000', 'US gpm rated (NFPA 20 standard ratings — verify)'), head=P('40 – 200', 'm'), pressure=P('up to ~20', 'bar'), speed=P('1,470 – 2,950', 'rpm'), efficiency=P('60 – 85', '%'),
                extra={'fuel_tank': P('≈ 5 L per kW (1 gal/hp) + allowances — verify NFPA 20', '')}),
    install=dict(foundation=['Dedicated, fire-separated pump room; rigid baseplate.'], alignment=_ALIGN_H, piping=['Suction from a reliable source (tank/reservoir); no throttling on suction.', 'Test header or flow meter loop; relief valve per standard.'],
                 commissioning=['Acceptance test at churn, 100 % and 150 % flow.', 'Controller and engine start tests (both batteries).']),
    maint=dict(routine=[M('Weekly churn test run.', 'diesel_engine', 'weekly'), M('Check batteries and fuel level.', 'batteries', 'weekly')], periodic=[M('Annual flow test at 0, 100, 150 % rated flow.', 'test_header', 'annually')],
               overhaul=[M('Inspect split-case pump internals.', 'impeller')], lubrication=['Engine oil; pump bearings.']),
    failures=[F('Engine fails to start', ['Controller alarm'], ['Batteries, fuel'], ['Battery maintenance, fuel checks'], 'batteries'),
              F('Low flow at test', ['Below curve'], ['Impeller wear, suction blockage'], ['Overhaul; clean suction'], 'impeller')],
    quiz=[Q('What does the jockey pump do?', ['Supplies fire flow', 'Maintains system pressure against small leaks', 'Drives the engine', 'Tests the relief valve'], 1, 'Prevents nuisance starts of the main pump.'),
          Q('NFPA 20 requires a listed fire pump at 150 % rated flow to deliver at least…', ['100 % pressure', '65 % rated pressure', '0 %', '140 %'], 1, 'Verify current edition.', 'intermediate'),
          Q('Which pump design is used here?', ['Horizontal split case', 'Gear pump', 'Peristaltic', 'Airlift'], 0, 'Module 2.')],
)

MODULES['chemical_dosing_system'] = mod(
    definition=('A chemical dosing system stores a treatment chemical and injects it accurately into a process stream using metering pumps. '
                'It typically comprises a storage tank with mixer and level gauge, duty and standby diaphragm metering pumps, suction and discharge lines with calibration column, pulsation dampener and back-pressure valve, all on a bunded skid with a control panel.'),
    applications=['Water treatment: chlorine, coagulants, pH control', 'Cooling-water and boiler chemical treatment', 'Alumina: flocculant, antiscalant and caustic dosing', 'Oil & gas: corrosion inhibitor, methanol injection'],
    key_points=['Built from: Diaphragm Metering Pump (module 27) or Plunger Pump (module 26)', 'Duty/standby pumps', 'Bund (secondary containment)', 'Flow-pacing to process flow'],
    principle=[step('The chemical is prepared in the storage tank and kept mixed by the agitator.', 'storage_tank'), step('The duty metering pump draws chemical through the suction line.', 'metering_pump_duty', overlay='flow'),
               step('The diaphragm displaces a set volume each stroke into the discharge line.', 'diaphragm_duty', overlay='flow'),
               step('The control panel paces stroke rate to the process flow or analyser signal.', 'control_panel', cut=False), step('The bund contains any leakage.', 'bund_skid', cut=False)],
    curve='Flow ∝ stroke length × frequency; calibrate with the calibration column.',
    params=dict(flow=P('0.1 L/h – 10 m³/h'), head=P('—'), pressure=P('up to ~20 (mechanical diaphragm)', 'bar'), speed=P('up to ~180', 'strokes/min'), efficiency=P('—'),
                extra={'accuracy': P('±1 – 2', '%'), 'bund_volume': P('≥ 110 % of largest tank (common rule — verify local regulations)', '')}),
    install=dict(foundation=['Level bunded skid; chemical-resistant surfaces.'], alignment=['Integral drives.'], piping=['Compatible materials (PVC, PVDF, stainless); injection quill at the dosing point; back-pressure valve.'],
                 commissioning=['Calibrate each pump; test duty/standby changeover; test leak and level alarms.']),
    maint=dict(routine=[M('Check tank level and dosing rate.', 'level_gauge', 'daily')], periodic=[M('Calibrate pumps.', 'metering_pump_duty', 'monthly'), M('Replace diaphragms and valves.', 'diaphragm_duty', 'per manual')],
               overhaul=[M('Inspect tank, mixer and piping for chemical attack.', 'storage_tank')], lubrication=['Pump gear oil.']),
    failures=[F('Over- or under-dosing', ['Process off-spec'], ['Siphoning, gas lock, worn valves'], ['Back-pressure valve, degassing, valve service'], 'discharge_line'),
              F('Chemical leak', ['Liquid in bund'], ['Fitting failure, material incompatibility'], ['Repair; correct materials'], 'bund_skid')],
    quiz=[Q('Why does a dosing skid have a bund?', ['To support the pumps', 'Secondary containment of chemical leaks', 'To mix chemicals', 'For cooling'], 1, 'Spill containment.'),
          Q('What tool is used to check the actual dosing rate?', ['Pressure gauge', 'Calibration column', 'Thermometer', 'Level switch'], 1, 'Timed drawdown.'),
          Q('Why duty and standby pumps?', ['Double flow', 'Continuity of dosing during maintenance or failure', 'Lower cost', 'Noise'], 1, 'Redundancy.')],
)

MODULES['condensate_extraction_pump'] = mod(
    definition=('A condensate extraction pump (CEP) removes condensate from the condenser hotwell, which is under vacuum and at saturation, and pumps it through the low-pressure heaters to the deaerator. '
                'Because NPSH available is very low, it is a vertical can pump (VS6) whose first-stage impeller sits deep below the hotwell level.'),
    applications=['Steam power plants and combined-cycle plants', 'Industrial turbine condensers (alumina, sugar, paper)'],
    key_points=['Built from: Vertical Can Pump (module 5)', 'Suction under vacuum at saturation', 'Can vent line back to condenser', 'Usually 2×100 % or 3×50 % pumps'],
    principle=[step('Condensate flows from the hotwell into the can.', 'suction_can', overlay='flow'), step('The liquid height above the first stage provides the NPSH.', 'impeller_1'),
               step('Five bowl stages raise the pressure.', 'bowl_3'), step('The can vent returns released vapour to the condenser.', 'can_vent_line', cut=False),
               step('A minimum-flow line protects the pump at low load.', 'min_flow_line', cut=False)],
    curve='Vertical multistage curve; first-stage NPSHr design is critical.',
    params=dict(flow=P('50 – 3,000', 'm³/h'), head=P('100 – 400', 'm'), pressure=P('up to ~40', 'bar'), speed=P('~1,480', 'rpm'), efficiency=P('75 – 85', '%')),
    install=dict(foundation=['Can in a pit below the condenser; head on sole plate.'], alignment=['Plumb; motor alignment.'], piping=['Vent line to condenser; seal water to avoid air in-leakage at the gland.'],
                 commissioning=['Vent can; check seal water; verify minimum flow.']),
    maint=dict(routine=[M('Check seal water and vibration.', 'mechanical_seal', 'daily')], periodic=[M('Check vent line.', 'can_vent_line', 'monthly')], overhaul=[M('Inspect first stage.', 'impeller_1')],
               lubrication=['Motor thrust bearing oil.']),
    failures=[F('Air in-leakage', ['Dissolved oxygen rise'], ['Gland leaking under vacuum'], ['Seal water'], 'mechanical_seal'), F('First-stage cavitation', ['Noise'], ['Low hotwell level'], ['Level control'], 'impeller_1')],
    quiz=[Q('Why is a CEP a vertical can pump?', ['To save space only', 'Hotwell NPSHa is very low; the can puts the first stage deep below the level', 'For higher speed', 'For cooling'], 1, 'Static head adds NPSH.'),
          Q('What is the vent line for?', ['Cooling', 'Return vapour from the can to the condenser', 'Priming', 'Draining oil'], 1, 'Prevents vapour locking.'),
          Q('Which module is it built on?', ['Vertical Can Pump', 'AODD', 'Lobe', 'Jet'], 0, 'Module 5.')],
)

MODULES['cooling_water_pump'] = mod(
    definition=('A cooling water pump circulates large flows of water at moderate head through heat exchangers, condensers and cooling towers. '
                'The model shows a horizontal split-case double-suction pump with suction isolation, discharge check and isolation valves and gauges; vertical turbine or axial-flow pumps are used for large intakes.'),
    applications=['Power-plant condenser cooling', 'Refinery and alumina plant cooling-water circuits', 'HVAC condenser water', 'Process cooling loops'],
    key_points=['Built from: Horizontal Split Case Pump (module 2); alternatives VT (4) and axial (11)', 'High flow, 20–40 m head typical', 'Water quality drives materials (seawater: bronze/duplex)'],
    principle=[step('Water enters through the suction isolation valve.', 'station_valves', overlay='flow'), step('The double-suction impeller adds energy.', 'impeller', overlay='flow'),
               step('The discharge check valve prevents back-flow when the pump stops.', 'station_valves', overlay='flow'), step('Gauges confirm operating point.', 'pressure_gauges', cut=False)],
    curve='Split-case curve; parallel operation of duty pumps is common — check the system curve.',
    params=dict(flow=P('500 – 30,000+', 'm³/h'), head=P('15 – 60', 'm'), pressure=P('up to ~16', 'bar'), speed=P('490 – 1,480', 'rpm'), efficiency=P('80 – 90', '%')),
    install=dict(foundation=['Rigid foundation.'], alignment=_ALIGN_H, piping=_PIPE_H, commissioning=_COMM_C),
    maint=dict(routine=[M('Check vibration, seals and bearing temperature.', 'bearing_inboard', 'daily')], periodic=[M('Exercise valves.', 'station_valves', 'quarterly')],
               overhaul=[M('Lift upper casing; inspect impeller and wear rings.', 'upper_casing')], lubrication=['Bearing oil/grease.']),
    failures=[F('Fouling and corrosion', ['Lower flow'], ['Untreated water'], ['Water treatment, materials'], 'impeller'), F('Water hammer', ['Bang on stop'], ['Fast-closing check valve'], ['Damped check valve'], 'station_valves')],
    quiz=[Q('Typical cooling-water pump duty?', ['Low flow, very high head', 'High flow, moderate head', 'Metering', 'Vacuum'], 1, 'Circulation.'),
          Q('Why is a check valve on the discharge?', ['To prime', 'To stop back-flow and reverse rotation when the pump stops', 'To throttle', 'To filter'], 1, 'Protects pump.'),
          Q('Built from which module?', ['Horizontal Split Case Pump', 'Peristaltic', 'Plunger', 'AODD'], 0, 'Module 2.')],
)

MODULES['hydraulic_power_pack_pump'] = mod(
    definition=('A hydraulic power pack (HPU) supplies pressurised oil to hydraulic cylinders and motors. A motor drives a positive-displacement pump — here an external gear pump inside the reservoir bell housing — '
                'with relief and directional valves on a manifold, an accumulator, filters, a cooler and instrumentation.'),
    applications=['Presses and machine tools', 'Valve actuators and gate operators', 'Mobile and marine equipment', 'Alumina and steel plant hydraulics (filter presses, kiln drives)'],
    key_points=['Built from: External Gear Pump (17); vane or piston pumps for higher pressures', 'Relief valve sets maximum pressure', 'Cleanliness (ISO 4406) governs component life'],
    principle=[step('The motor drives the gear pump through the bell housing and coupling.', 'gear_pump'), step('The pump draws oil from the reservoir through the suction strainer.', 'suction_strainer', overlay='flow'),
               step('Oil is delivered to the valve manifold; the relief valve limits pressure.', 'valve_manifold', overlay='flow'), step('The accumulator stores energy and smooths pressure.', 'accumulator'),
               step('Return oil passes the filter and cooler back to the reservoir.', 'return_filter', overlay='flow')],
    curve='Flow ∝ speed × displacement; pressure set by load up to the relief setting.',
    params=dict(flow=P('1 – 500', 'L/min'), head=P('—'), pressure=P('70 – 350', 'bar'), speed=P('1,450 – 1,800', 'rpm'), efficiency=P('80 – 92 (gear/vane/piston pump overall)', '%'),
                extra={'oil_cleanliness': P('ISO 4406 e.g. 18/16/13 or better', '', 'system dependent')}),
    install=dict(foundation=['Level, vibration-isolated base.'], alignment=['Bell housing ensures alignment.'], piping=['Suction line short and large; hoses rated for pressure.'], commissioning=['Flush system; bleed air; set relief valve.']),
    maint=dict(routine=[M('Check oil level and temperature.', 'breather_level', 'daily')], periodic=[M('Replace return filter element.', 'return_filter', 'per ΔP indicator'), M('Check accumulator pre-charge.', 'accumulator', '6 months')],
               overhaul=[M('Oil analysis and change.', 'reservoir')], lubrication=['Hydraulic oil (ISO VG 32/46/68).']),
    failures=[F('Overheating', ['Hot oil'], ['Relief valve bypassing continuously, cooler fouled'], ['Adjust/repair; clean cooler'], 'oil_cooler'), F('Pump wear from contamination', ['Slow actuators'], ['Dirty oil'], ['Filtration'], 'gear_pump'),
              F('Pump cavitation', ['Noise'], ['Clogged strainer, cold oil'], ['Clean; warm oil'], 'suction_strainer')],
    quiz=[Q('What sets the maximum system pressure?', ['Pump speed', 'The relief valve', 'Oil level', 'Cooler'], 1, 'Relief valve.'),
          Q('Why is oil cleanliness critical?', ['Colour', 'Contaminants wear pumps and valves', 'Smell', 'It is not'], 1, 'Tight clearances.'),
          Q('What does the accumulator do?', ['Cools oil', 'Stores pressurised oil energy and dampens pulsations', 'Filters oil', 'Drives the pump'], 1, 'Gas-charged energy store.')],
)

MODULES['lubricating_oil_pump'] = mod(
    definition=('A lubricating-oil system (console) supplies clean, cooled oil at controlled pressure to the bearings of turbines, compressors and large pumps. '
                'Main and standby pumps — here three-screw pumps — draw from a reservoir and deliver through twin coolers, duplex filters and pressure control valves; API 614 governs special-purpose systems.'),
    applications=['Steam and gas turbines', 'Centrifugal compressors', 'Large pumps and gearboxes', 'Alumina refinery turbine-generators and blowers'],
    key_points=['Built from: Three Screw Pump (20) or External Gear Pump (17)', 'Main + standby with auto-start on low pressure', 'Duplex filters and coolers switchable on-line', 'API 614 (verify edition)'],
    principle=[step('The main pump draws oil from the reservoir.', 'pump_main', overlay='flow'), step('The screw rotors deliver smooth, pulsation-free flow.', 'rotor_main'),
               step('Oil passes the cooler and duplex filter.', 'duplex_filter', overlay='flow'), step('Pressure control valves regulate header pressure; the standby pump auto-starts on low pressure.', 'pressure_control')],
    curve='Screw pump near-constant flow; header pressure by control valve.',
    params=dict(flow=P('50 – 3,000', 'L/min'), head=P('—'), pressure=P('header ~1.5 – 3; pump discharge up to ~10–16', 'bar'), speed=P('1,450 – 3,000', 'rpm'), efficiency=P('70 – 85', '%'),
                extra={'oil_grade': P('ISO VG 32 / 46 typical (turbine oil)')}),
    install=dict(foundation=['Console skid on level base.'], alignment=['Pump/motor alignment.'], piping=['Stainless oil piping downstream of filters; flushing to cleanliness before start.'], commissioning=['Oil flush; test auto-start of standby pump.']),
    maint=dict(routine=[M('Check header pressure and filter ΔP.', 'duplex_filter', 'daily')], periodic=[M('Switch filters and change elements.', 'duplex_filter', 'per ΔP'), M('Oil analysis.', 'reservoir', 'quarterly')],
               overhaul=[M('Inspect pumps and coolers.', 'pump_standby')], lubrication=['Self-lubricated by oil.']),
    failures=[F('Low header pressure trip', ['Turbine trip'], ['Pump wear, filter blockage'], ['Standby auto-start test'], 'pressure_control'), F('Water in oil', ['Milky oil'], ['Cooler leak'], ['Repair cooler'], 'coolers')],
    quiz=[Q('Why is a standby pump fitted?', ['Double pressure', 'Automatically takes over if header pressure falls', 'Cools oil', 'Filters oil'], 1, 'Protects the machine bearings.'),
          Q('Why duplex filters?', ['More flow', 'Element can be changed without stopping', 'Cheaper', 'Lower pressure'], 1, 'Switchable.'),
          Q('Which pump type is used in this model?', ['Three screw', 'Axial', 'Airlift', 'AODD'], 0, 'Module 20.')],
)

MODULES['sewage_pumping_system'] = mod(
    definition=('A sewage pumping (lift) station collects wastewater flowing by gravity into a wet well and pumps it through a rising main to a higher sewer or treatment plant. '
                'Two submersible non-clog pumps on guide rails run duty/standby under float or level control; check and gate valves in a separate valve chamber allow each pump to be serviced.'),
    applications=['Municipal sewerage networks', 'Industrial and refinery effluent collection', 'Storm water', 'Building and campus drainage'],
    key_points=['Built from: Submersible Sewage Pump (module 8)', 'Wet-well volume limits motor starts per hour', 'Self-cleansing velocity in the rising main', 'H₂S safety: ventilation and gas detection'],
    principle=[step('Sewage enters through the inlet and screen basket.', 'inlet_screen', overlay='flow'), step('Floats start the duty pump at the start level.', 'float_switches', cut=False),
               step('The non-clog impeller lifts sewage through the duckfoot and riser.', 'impeller_duty', overlay='flow'),
               step('Check and gate valves in the valve chamber lead to the rising main.', 'station_valves', overlay='flow'), step('The standby pump starts if the level keeps rising.', 'pump_standby')],
    curve='System curve = static lift + rising-main friction; two pumps in parallel for peak flow.',
    params=dict(flow=P('5 – 5,000', 'm³/h station'), head=P('5 – 60', 'm'), pressure=P('—'), speed=P('700 – 2,900', 'rpm'), efficiency=P('40 – 80', '%'),
                extra={'starts_per_hour': P('≤ 6 – 15', '', 'per motor manufacturer — verify'), 'rising_main_velocity': P('≈ 0.7 – 2', 'm/s', 'verify local design codes')}),
    install=dict(foundation=['Concrete wet well; benching to prevent deposits.'], alignment=['Guide rails plumb.'], piping=['Valve chamber dry and accessible; air valves at rising-main high points.'],
                 commissioning=['Set levels; test alarms and telemetry; test alternation.']),
    maint=dict(routine=[M('Check run hours and alarms.', 'control_kiosk', 'weekly')], periodic=[M('Clean wet well and screen basket.', 'inlet_screen', 'monthly'), M('Exercise valves.', 'station_valves', 'quarterly')],
               overhaul=[M('Lift pumps; check seals and impellers.', 'pump_duty')], lubrication=['Pump oil chambers.']),
    failures=[F('Pump clogging', ['High current, low flow'], ['Wipes, rags'], ['Screening, chopper impellers'], 'impeller_duty'), F('Septicity and odour', ['H₂S'], ['Long retention'], ['Reduce retention; ventilation'], 'wet_well'),
              F('Float failure', ['Overflow or dry run'], ['Fat build-up'], ['Clean; level transmitter'], 'float_switches')],
    quiz=[Q('What limits the minimum wet-well volume?', ['Pipe size', 'Maximum motor starts per hour', 'Colour', 'Rail length'], 1, 'Volume between start and stop levels.'),
          Q('Why are the valves in a separate dry chamber?', ['Looks', 'Maintenance without entering the wet well', 'Lower cost', 'Cooling'], 1, 'Safety and access.'),
          Q('Which hazard requires ventilation in wet wells?', ['Oxygen excess', 'H₂S and methane', 'Steam', 'Nitrogen'], 1, 'Septic gases.')],
)
