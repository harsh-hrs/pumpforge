"""Learning content — rotary (17–24) and reciprocating (25–28) positive-displacement pumps."""
from pumpforge.learning import mod, step, P, F, Q, M

MODULES = {}

_PD_RELIEF = 'Fit a pressure-relief valve (integral or in the discharge line) — a positive-displacement pump will build pressure until something breaks if the discharge is blocked.'
_PD_COMM = ['Never start against a closed discharge valve.', 'Fill the pump with liquid (or ensure the suction is flooded) before start — avoid dry running unless the design allows it.',
            'Check rotation direction.', 'Verify the relief-valve set pressure.']
_PD_PIPE = ['Size the suction line for low velocity (viscous liquids need large suction pipes); provide a strainer.', _PD_RELIEF,
            'Support piping independently of the pump.']

MODULES['external_gear_pump'] = mod(
    definition=('An external gear pump uses two meshing gears turning in a close-fitting housing. Liquid is trapped in the spaces between the gear teeth and the casing, carried around the outside from suction to discharge, '
                'and forced out where the teeth mesh. Flow is nearly proportional to speed and almost independent of pressure.'),
    applications=['Lubricating oil and fuel oil transfer', 'Hydraulic power units (high-pressure gear pumps)', 'Polymer, resin and chemical metering', 'Lube-oil systems on turbines and compressors'],
    key_points=['Positive displacement: flow ∝ speed', 'Needs a relief valve', 'Clean, lubricating liquids', 'Volumetric efficiency falls as clearances wear and viscosity drops'],
    principle=[step('As the teeth come out of mesh on the suction side, the expanding space draws liquid in.', 'drive_gear_shaft', overlay='flow'),
               step('Liquid is trapped between the teeth and the housing and carried around the outside of both gears.', 'pump_body', overlay='flow'),
               step('On the discharge side the teeth mesh again and squeeze the liquid out.', 'idler_gear_shaft', overlay='flow'),
               step('Bushings support the gear shafts and are lubricated by the pumped liquid.', 'bushing_front_drive'),
               step('The integral relief valve opens and recirculates flow if discharge pressure exceeds its setting.', 'relief_poppet')],
    curve='Flow almost constant with pressure (slight fall from slip); power rises linearly with pressure; flow rises linearly with speed.',
    params=dict(flow=P('0.1 – 300', 'm³/h'), head=P('—', '', 'PD pumps are rated by pressure'), pressure=P('up to 20 (transfer); up to ~250–300 (hydraulic gear pumps)', 'bar'),
                speed=P('300 – 3,600', 'rpm', 'lower for viscous liquids'), efficiency=P('volumetric 85 – 98; overall 50 – 85', '%'),
                extra={'viscosity': P('1 – 100,000', 'cSt'), 'displacement': P('per revolution, fixed', 'cm³/rev')}),
    selection=['Reduce speed as viscosity rises to avoid cavitation in the tooth spaces.', 'Use hardened gears and bushings for poor-lubricity liquids.'],
    install=dict(foundation=['Baseplate or flange mounting.'], alignment=['Coupling alignment as for centrifugal pumps.'], piping=_PD_PIPE, commissioning=_PD_COMM),
    maint=dict(routine=[M('Check discharge pressure and noise.', 'pump_body', 'daily'), M('Check the shaft seal.', 'mechanical_seal', 'daily')],
               periodic=[M('Verify relief-valve setting.', 'relief_adjuster', 'annually')], overhaul=[M('Measure gear end and tip clearances and bushing wear.', 'bushing_front_drive')],
               lubrication=['Internal bushings lubricated by the pumped liquid.']),
    failures=[F('Loss of flow (slip)', ['Lower flow at pressure'], ['Worn clearances', 'Low viscosity'], ['Replace gears/bushings'], 'drive_gear_shaft'),
              F('Cavitation noise', ['Whining, rattling'], ['Too high speed for the viscosity', 'Clogged strainer'], ['Reduce speed; clean strainer'], 'pump_body'),
              F('Relief valve chatter', ['Noise, flow loss'], ['Setting too close to operating pressure'], ['Reset'], 'relief_poppet')],
    quiz=[Q('Where does the liquid travel in an external gear pump?', ['Through the mesh of the teeth', 'Around the outside of the gears, between teeth and casing', 'Through the shaft', 'Through the relief valve'], 1, 'Not through the mesh.'),
          Q('Why must a gear pump have a relief valve?', ['To prime it', 'Pressure rises until failure if the discharge is blocked', 'To cool it', 'To reduce noise'], 1, 'PD pumps do not have a shut-off head.'),
          Q('Doubling the speed of a gear pump roughly…', ['Halves the flow', 'Doubles the flow', 'Does not change flow', 'Quadruples head'], 1, 'Flow ∝ speed × displacement.'),
          Q('Slip in a gear pump increases when…', ['Viscosity falls or clearances wear', 'Speed drops only', 'Pressure falls', 'Never'], 0, 'Leakage back through clearances.', 'intermediate')],
)

MODULES['internal_gear_pump'] = mod(
    definition=('An internal gear pump has a large outer rotor with internal teeth driving a smaller idler gear on an offset pin; a crescent-shaped partition separates the suction and discharge sides. '
                'Liquid fills the spaces between teeth as they unmesh, is carried around both sides of the crescent and is forced out as the teeth re-mesh.'),
    applications=['Viscous liquids: asphalt, molasses, resins, chocolate, adhesives', 'Fuel oil and lube oil', 'Paints and inks', 'Chemical transfer'],
    key_points=['Excellent for high viscosity at low speed', 'Smooth, low-pulsation flow', 'Reversible by changing rotation', 'Only two moving parts'],
    principle=[step('Rotor and idler teeth unmesh at the suction port, creating expanding cavities.', 'rotor', overlay='flow'),
               step('Liquid is carried in the rotor teeth over the crescent and in the idler teeth under it.', 'crescent_pin', overlay='flow'),
               step('Teeth re-mesh at the discharge port and push the liquid out.', 'idler', overlay='flow'),
               step('The head carries the idler pin and crescent; end clearance is set at the head.', 'head')],
    curve='Flow nearly constant vs pressure; increases linearly with speed.',
    params=dict(flow=P('0.1 – 350', 'm³/h'), pressure=P('up to ~17', 'bar'), head=P('—'), speed=P('20 – 1,750', 'rpm', 'low for viscous'), efficiency=P('volumetric 80 – 98', '%'),
                extra={'viscosity': P('1 – 1,000,000', 'cSt')}),
    install=dict(foundation=['Baseplate.'], alignment=['Coupling alignment.'], piping=_PD_PIPE, commissioning=_PD_COMM + ['Heat jacketed pumps before start for viscous products.']),
    maint=dict(routine=[M('Check seal and noise.', 'mechanical_seal', 'daily')], periodic=[M('Adjust end clearance as wear progresses.', 'head', 'per wear')],
               overhaul=[M('Replace idler bushing and pin.', 'idler')], lubrication=['Bracket bearings grease-lubricated.']),
    failures=[F('Idler bushing wear', ['Noise, flow loss'], ['Poor lubricity, abrasives'], ['Harder bushing materials'], 'idler'),
              F('Cavitation', ['Noise'], ['Speed too high for viscosity'], ['Reduce speed'], 'rotor')],
    quiz=[Q('What separates suction and discharge in an internal gear pump?', ['A valve', 'The crescent', 'The seal', 'The coupling'], 1, 'A fixed crescent partition.'),
          Q('Internal gear pumps are especially suited to…', ['Low-viscosity water at high head', 'High-viscosity liquids at low speed', 'Slurry with large solids', 'Gas compression'], 1, 'Large cavities, low speed.'),
          Q('How many moving parts does the pumping element have?', ['One', 'Two', 'Four', 'Eight'], 1, 'Rotor and idler.')],
)

MODULES['twin_screw_pump'] = mod(
    definition=('A twin screw pump has two intermeshing screws that do not touch: timing gears outside the pumping chamber transmit the drive and keep the clearances. '
                'Cavities formed between the screw flights and the casing move axially from suction to discharge, giving a smooth, non-pulsating flow. External bearings let it handle poor-lubricity and multiphase fluids.'),
    applications=['Crude oil and multiphase (oil + gas + water) boosting', 'Tank-farm and terminal transfer', 'Bitumen, heavy fuel and viscous chemicals', 'Food and hygienic products (sanitary designs)'],
    key_points=['Screws do not touch — timing gears', 'Handles high gas fractions and solids better than three-screw', 'Double-suction screws balance axial thrust', 'Very low pulsation'],
    principle=[step('Liquid enters at both ends of the double-flow screws.', 'casing', overlay='flow'), step('Sealed cavities between the flights and casing move towards the centre as the screws rotate.', 'rotor_1', overlay='flow'),
               step('The timing gears drive the second screw and keep the flights from touching.', 'timing_gear_1'), step('Liquid leaves at the centre discharge; opposed flows cancel axial thrust.', 'rotor_2', overlay='flow')],
    curve='Flow almost constant vs pressure; slip rises with pressure and falls with viscosity.',
    params=dict(flow=P('1 – 5,000', 'm³/h'), pressure=P('up to 40–100', 'bar', 'design dependent'), head=P('—'), speed=P('300 – 3,600', 'rpm'), efficiency=P('50 – 85', '%'),
                extra={'viscosity': P('1 – 1,000,000+', 'cSt'), 'gas_volume_fraction': P('up to ~90–97 (multiphase designs)', '%')}),
    install=dict(foundation=['Baseplate.'], alignment=['Coupling alignment.'], piping=_PD_PIPE, commissioning=_PD_COMM),
    maint=dict(routine=[M('Check bearing temperature and timing-gear oil.', 'gearbox', 'daily')], periodic=[M('Change gearbox oil.', 'gearbox', 'per manual')],
               overhaul=[M('Check screw-to-casing clearances and timing.', 'rotor_1')], lubrication=['External bearings and timing gears oil-lubricated.']),
    failures=[F('Screw rubbing', ['Noise, scoring'], ['Timing gear wear', 'Thermal growth'], ['Re-time; replace gears'], 'timing_gear_1'),
              F('Wear', ['Flow loss'], ['Abrasives'], ['Hardened screws/liners'], 'rotor_2')],
    quiz=[Q('Why don\'t the screws in a twin screw pump touch?', ['They are magnetic', 'Timing gears keep them apart', 'They are soft', 'They are not meshed'], 1, 'Non-contacting design.'),
          Q('Why is a twin screw pump good for multiphase flow?', ['It compresses gas in sealed cavities without contact wear', 'It has a large impeller', 'It cannot run dry', 'It has no bearings'], 0, 'External bearings and no contact.', 'intermediate'),
          Q('Double-flow screws are used to…', ['Increase pulsation', 'Balance axial thrust', 'Reduce flow', 'Add a seal'], 1, 'Opposed screws cancel thrust.')],
)

MODULES['three_screw_pump'] = mod(
    definition=('A three screw pump has a central power rotor that drives two idler rotors through the liquid film; the screws are in rolling contact and form sealed chambers that move axially. '
                'It produces smooth, quiet, pulsation-free flow at high pressure and needs a clean, lubricating liquid.'),
    applications=['Lube and seal oil for turbines and compressors', 'Fuel oil and fuel injection supply', 'Hydraulic elevators and presses', 'Machine-tool coolant/hydraulics'],
    key_points=['Idlers driven hydraulically by the power rotor — no timing gears', 'Low noise and pulsation', 'High pressure capability', 'Clean lubricating liquids only'],
    principle=[step('Liquid enters at the suction end of the rotors.', 'casing', overlay='flow'), step('The power rotor turns and drives the two idlers through the liquid film.', 'power_rotor'),
               step('Sealed chambers between the flights move axially towards the discharge.', 'idler_right', overlay='flow'), step('Hydraulic balancing pistons reduce axial thrust on the rotors.', 'housing_insert')],
    curve='Near-constant flow vs pressure; very low pulsation.',
    params=dict(flow=P('0.5 – 500', 'm³/h'), pressure=P('up to 80 – 160', 'bar'), head=P('—'), speed=P('1,000 – 3,600', 'rpm'), efficiency=P('70 – 90', '%'),
                extra={'viscosity': P('2 – 5,000+', 'cSt')}),
    install=dict(foundation=['Baseplate or vertical tank-top mounting.'], alignment=['Coupling alignment.'], piping=_PD_PIPE, commissioning=_PD_COMM),
    maint=dict(routine=[M('Check noise and discharge pressure.', 'casing', 'daily')], periodic=[M('Check bearing and seal.', 'bearing', 'per manual')], overhaul=[M('Inspect rotor flanks for wear.', 'power_rotor')],
               lubrication=['Pumped oil lubricates the rotors; ball bearing per manual.']),
    failures=[F('Wear from contaminants', ['Flow loss, noise'], ['Dirty oil'], ['Improve filtration'], 'idler_left'), F('Cavitation', ['Noise'], ['Cold, viscous oil at start'], ['Warm oil; reduce speed'], 'power_rotor')],
    quiz=[Q('How are the idler rotors driven?', ['Timing gears', 'By the power rotor through the liquid film (hydraulic drive)', 'Belts', 'Separate motors'], 1, 'No timing gears.'),
          Q('Why is a three screw pump popular for lube-oil systems?', ['It handles slurry', 'Quiet, low-pulsation, high-pressure delivery of clean oil', 'It has no rotors', 'Cheapest'], 1, 'Smooth flow.'),
          Q('Liquid requirement?', ['Abrasive slurry', 'Clean lubricating liquid', 'Gas only', 'Any'], 1, 'Contact between rotors.')],
)

MODULES['progressive_cavity_pump'] = mod(
    definition=('A progressive cavity (PC) pump has a single-helix metal rotor turning eccentrically inside a double-helix elastomer stator. '
                'The rotor and stator form sealed cavities that progress from suction to discharge without changing shape, so the pump moves viscous, shear-sensitive and solids-laden liquids gently with a smooth flow.'),
    applications=['Wastewater sludge and polymer dosing', 'Food (fruit pulp, dough)', 'Oil-field and mining slurries', 'Paper, paint and adhesives', 'Alumina: flocculant dosing and thickener underflow (selected duties)'],
    key_points=['Flow ∝ speed; pressure capability ∝ number of stages (≈ 6 bar per stage typical)', 'Never run dry — the stator burns', 'Universal-joint or flexible connecting rod', 'Low shear, low pulsation'],
    principle=[step('The rotor turns eccentrically inside the stator, driven through a connecting rod with universal joints.', 'connecting_rod'),
               step('Sealed cavities form at the suction end and fill with liquid.', 'suction_housing', overlay='flow'),
               step('The cavities progress along the stator to the discharge without changing volume.', 'stator', overlay='flow'),
               step('The interference fit between rotor and stator seals the cavities; more stages hold more pressure.', 'rotor')],
    curve='Flow almost linear with speed; slip increases with pressure and decreases with viscosity.',
    params=dict(flow=P('0.01 – 500', 'm³/h'), pressure=P('up to ~48 (multi-stage)', 'bar', 'about 6 bar per stage typical — verify'), head=P('—'), speed=P('50 – 500', 'rpm'),
                efficiency=P('50 – 80', '%'), extra={'viscosity': P('1 – 1,000,000', 'cP'), 'solids': P('up to ~60', '% by volume', 'design dependent')}),
    install=dict(foundation=['Baseplate with gearmotor.'], alignment=['Gearmotor coupling alignment.'], piping=_PD_PIPE + ['Leave space to remove the stator from the rotor (pull-out length).'],
                 commissioning=_PD_COMM + ['Dry-run protection (temperature or flow sensor in the stator).']),
    maint=dict(routine=[M('Check discharge pressure and seal.', 'mechanical_seal', 'daily')], periodic=[M('Inspect universal joints and their sleeves.', 'connecting_rod', 'per manual')],
               overhaul=[M('Replace stator when slip rises; check rotor chrome plating.', 'stator')], lubrication=['Joints grease-filled and sealed by sleeves.']),
    failures=[F('Dry running stator burn', ['Rubber smell, rapid flow loss'], ['Empty suction'], ['Dry-run protection'], 'stator'),
              F('Stator wear / swelling', ['Flow loss or high torque'], ['Abrasives; chemical incompatibility; temperature'], ['Correct elastomer'], 'stator'),
              F('Joint failure', ['Knocking'], ['Torn sleeve, lost grease'], ['Replace joint and sleeve'], 'connecting_rod')],
    quiz=[Q('What determines the pressure a PC pump can develop?', ['Speed', 'Number of stages (stator length)', 'Motor size only', 'Pipe size'], 1, 'Each stage holds roughly the same pressure.'),
          Q('Why must a PC pump not run dry?', ['Rotor rusts', 'The elastomer stator overheats and burns', 'It loses prime', 'Seal leaks'], 1, 'Friction heat.'),
          Q('Why is a PC pump good for shear-sensitive liquids?', ['High speed', 'Cavities move gently without changing shape', 'Large impeller', 'Uses air'], 1, 'Low shear.'),
          Q('What allows the rotor to orbit eccentrically while the drive shaft turns concentrically?', ['Timing gears', 'Connecting rod with universal (or flexible) joints', 'Belts', 'Magnets'], 1, 'Joints accommodate eccentric motion.', 'intermediate')],
)

MODULES['rotary_lobe_pump'] = mod(
    definition=('A rotary lobe pump has two lobed rotors that turn in opposite directions without touching, driven and timed by external timing gears. '
                'Liquid is carried around the outside of each rotor between the lobes and the casing; large cavities and gentle action make it ideal for hygienic and solids-laden products.'),
    applications=['Food, beverage and dairy (hygienic, CIP/SIP)', 'Pharmaceutical', 'Wastewater sludge', 'Paint, polymers and pulp'],
    key_points=['Non-contacting rotors — timing gears', 'Large cavities pass soft solids', 'Reversible', 'Hygienic designs to EHEDG/3-A'],
    principle=[step('Lobes unmesh at the suction port and draw liquid in.', 'rotor_1', overlay='flow'), step('Liquid is carried around the outside of each rotor.', 'rotor_case', overlay='flow'),
               step('Lobes re-mesh and displace the liquid to the discharge.', 'rotor_2', overlay='flow'), step('Timing gears in the gearbox synchronise the rotors.', 'timing_gear_1')],
    curve='Flow ∝ speed; slip rises with pressure, falls with viscosity.',
    params=dict(flow=P('0.1 – 1,000', 'm³/h'), pressure=P('up to ~12 – 30', 'bar'), head=P('—'), speed=P('50 – 1,000', 'rpm'), efficiency=P('50 – 85', '%'), extra={'viscosity': P('1 – 1,000,000', 'cP')}),
    install=dict(foundation=['Baseplate; hygienic frames for food.'], alignment=['Coupling alignment.'], piping=_PD_PIPE, commissioning=_PD_COMM),
    maint=dict(routine=[M('Check seals and gearbox oil level.', 'gearbox', 'daily')], periodic=[M('Change gearbox oil.', 'gearbox', 'per manual')],
               overhaul=[M('Check rotor clearances and timing.', 'rotor_1')], lubrication=['Gearbox oil bath.']),
    failures=[F('Rotor contact', ['Knocking, metal in product'], ['Timing gear or bearing wear', 'Over-pressure'], ['Re-time, replace bearings'], 'timing_gear_2'),
              F('Seal leakage', ['Product at the seal'], ['Dry running seals'], ['Flush/quench'], 'shaft_seals')],
    quiz=[Q('What keeps the lobes from touching?', ['Springs', 'Timing gears', 'Liquid film only', 'Magnets'], 1, 'External timing gears.'),
          Q('Lobe pumps are popular in food plants because…', ['High head', 'Hygienic, gentle, easy to clean', 'No gears', 'They self-heat'], 1, 'CIP-able designs.'),
          Q('Flow direction of a lobe pump can be reversed by…', ['Changing rotation', 'Changing gears', 'It cannot', 'Adding a valve'], 0, 'Symmetric design.')],
)

MODULES['sliding_vane_pump'] = mod(
    definition=('A sliding vane pump has a slotted rotor mounted off-centre in a cylindrical liner; vanes slide in the slots and are pushed against the liner by centrifugal force, push rods or springs. '
                'As the rotor turns, the space between adjacent vanes grows at the suction side and shrinks at the discharge side, displacing a fixed volume per revolution. Vanes self-compensate for wear.'),
    applications=['LPG, refrigerants and solvents (thin liquids)', 'Fuel and oil transfer, truck unloading', 'Aviation fuel hydrant systems', 'Hydraulic vane pumps'],
    key_points=['Good with thin, volatile liquids', 'Vanes compensate for wear', 'Good suction and dry-priming capability', 'Not for abrasives'],
    principle=[step('The rotor sits off-centre in the liner.', 'rotor'), step('Vanes slide out and keep contact with the liner as the rotor turns.', 'vane_1'),
               step('The expanding volume between vanes draws liquid in at the suction port.', 'liner', overlay='flow'), step('The shrinking volume pushes liquid out at the discharge port.', 'casing', overlay='flow')],
    curve='Near-constant flow vs pressure; good volumetric efficiency even with low viscosity.',
    params=dict(flow=P('1 – 500', 'm³/h'), pressure=P('up to ~10 – 15 (transfer); up to ~200+ hydraulic', 'bar'), head=P('—'), speed=P('300 – 1,800', 'rpm'), efficiency=P('60 – 90', '%'),
                extra={'viscosity': P('0.2 – 20,000', 'cSt')}),
    install=dict(foundation=['Baseplate.'], alignment=['Coupling alignment.'], piping=_PD_PIPE + ['For LPG: vapour-return line and bypass valve.'], commissioning=_PD_COMM),
    maint=dict(routine=[M('Check noise and seal.', 'mechanical_seal', 'daily')], periodic=[M('Inspect vanes for wear (length).', 'vane_1', 'per manual')],
               overhaul=[M('Replace vanes and liner when worn.', 'liner')], lubrication=['Bearings grease-lubricated.']),
    failures=[F('Vane wear / breakage', ['Flow loss, noise'], ['Abrasives, dry running'], ['Replace vanes; filter'], 'vane_3'),
              F('Vapour lock with LPG', ['No flow'], ['Low NPSHa, warm product'], ['Vapour return, larger suction'], 'casing')],
    quiz=[Q('What keeps the vanes in contact with the liner?', ['Gravity', 'Centrifugal force (plus push rods/springs)', 'Magnets', 'Timing gears'], 1, 'Vanes slide outward.'),
          Q('Why are vane pumps good for LPG?', ['They handle thin liquids with good volumetric efficiency', 'They are large', 'They have impellers', 'They need no seal'], 0, 'Self-compensating vanes.'),
          Q('Vane wear is automatically compensated because…', ['The motor speeds up', 'Vanes slide further out', 'The liner shrinks', 'It is not'], 1, 'Self-adjusting.')],
)

MODULES['peristaltic_pump'] = mod(
    definition=('A peristaltic (hose) pump moves liquid by squeezing a flexible hose or tube with rollers or shoes on a rotor. '
                'The occlusion travels along the hose, pushing the liquid ahead of it; the hose recovers its shape behind the shoe and draws in more liquid. The liquid touches only the hose.'),
    applications=['Abrasive slurries and lime milk', 'Chemical dosing (sodium hypochlorite, ferric chloride)', 'Mining and alumina: thickener underflow sampling, reagent dosing', 'Food, pharma and lab'],
    key_points=['Only the hose is wetted — no seals or valves', 'Can run dry; self-priming to high suction lift', 'Accurate dosing (flow ∝ speed)', 'Hose life is the main cost'],
    principle=[step('A shoe on the rotor squeezes the hose closed.', 'rotor'), step('As the rotor turns, the occlusion moves along the hose and pushes liquid out.', 'hose', overlay='flow'),
               step('The hose springs back behind the shoe, creating suction.', 'hose', overlay='flow'), step('The housing is part-filled with lubricant to reduce hose wear and heat.', 'pump_housing')],
    curve='Flow ∝ speed; slight fall with pressure as the hose deforms.',
    params=dict(flow=P('0.001 – 100', 'm³/h'), pressure=P('up to ~15–16', 'bar', 'hose pumps'), head=P('—'), speed=P('5 – 100', 'rpm (hose pumps)'), efficiency=P('—', '', 'lower than other PD types'),
                extra={'suction_lift': P('up to ~9', 'm'), 'solids': P('up to ~80', '% (soft solids, slurries)')}),
    install=dict(foundation=['Baseplate.'], alignment=['Gearmotor alignment.'], piping=['Flexible connections; pulsation dampeners on long lines.', _PD_RELIEF], commissioning=['Check lubricant level; check hose installation and shimming.']),
    maint=dict(routine=[M('Check for hose leakage (leak detector).', 'hose', 'daily')], periodic=[M('Change hose at planned intervals.', 'hose', 'per run-hours')],
               overhaul=[M('Inspect shoes and bearings.', 'rotor')], lubrication=['Hose lubricant in housing; gearbox oil.']),
    failures=[F('Hose rupture', ['Leak alarm'], ['End of life, over-pressure, chemical attack'], ['Replace; check pressure and material'], 'hose'),
              F('Overheating', ['Hot housing'], ['High speed, low lubricant'], ['Reduce speed; refill lubricant'], 'pump_housing')],
    quiz=[Q('What is the only part in contact with the pumped liquid?', ['Rotor', 'Hose/tube', 'Shoes', 'Bearings'], 1, 'No seals or valves.'),
          Q('Can a peristaltic pump run dry?', ['Yes, without damage', 'No, never', 'Only with water', 'Only at high speed'], 0, 'No internal contact surfaces in the liquid.'),
          Q('The main wear item is…', ['Impeller', 'The hose', 'Wear ring', 'Valve seat'], 1, 'Hose fatigue.')],
)

MODULES['piston_pump'] = mod(
    definition=('A reciprocating piston pump uses a piston with seals moving back and forth in a cylinder liner; suction and discharge check valves make the flow one-way. '
                'Double-acting designs pump on both strokes. Flow is proportional to speed and stroke and nearly independent of pressure, but it pulsates.'),
    applications=['Mud pumps for drilling', 'High-pressure water and process injection', 'Pipeline and slurry transport (piston/plunger diaphragm)', 'Hydraulic test benches'],
    key_points=['Double-acting duplex piston pump in the model', 'Pulsating flow — use dampeners', 'Valves are the main wear part', 'Relief valve mandatory'],
    principle=[step('The crankshaft turns; connecting rods and crossheads convert rotation into straight-line motion.', 'crankshaft'),
               step('As the piston moves back, the suction valve opens and liquid fills the cylinder.', 'suction_valve_front_1', overlay='flow'),
               step('On the forward stroke the suction valve closes and the discharge valve opens.', 'discharge_valve_front_1', overlay='flow'),
               step('Double-acting: the other side of the piston pumps on the return stroke.', 'piston_1'), step('Rod packing seals the piston rod where it leaves the fluid end.', 'rod_packing_1')],
    curve='Flow ∝ speed; nearly vertical flow-pressure line; pressure limited by mechanical rating and relief valve.',
    params=dict(flow=P('0.1 – 200', 'm³/h'), pressure=P('up to ~200', 'bar', 'higher pressures normally use plungers'), head=P('—'), speed=P('50 – 300', 'strokes/min'), efficiency=P('85 – 95', '% (mechanical × volumetric)')),
    install=dict(foundation=['Massive foundation for reciprocating forces.'], alignment=['Gear reducer and motor alignment.'],
                 piping=['Pulsation dampeners on suction and discharge.', 'Short, large suction; acceleration head must be included in NPSHa.', _PD_RELIEF], commissioning=_PD_COMM),
    maint=dict(routine=[M('Check packing leakage and crankcase oil.', 'rod_packing_1', 'daily')], periodic=[M('Inspect valves and seats.', 'suction_valve_front_1', 'per wear')],
               overhaul=[M('Replace liners and piston seals.', 'liner_1')], lubrication=['Crankcase splash or pressure lubrication.']),
    failures=[F('Valve wear', ['Loss of flow, knocking'], ['Abrasives, cavitation'], ['Replace valves/seats'], 'discharge_valve_front_1'),
              F('Pulsation / pipe vibration', ['Shaking pipework'], ['No/ineffective dampener'], ['Charge dampeners'], 'fluid_end'),
              F('Cavitation from acceleration head', ['Knocking on suction'], ['Long suction line'], ['Shorten line, suction stabiliser'], 'suction_valve_rear_1')],
    quiz=[Q('What makes the flow one-way in a piston pump?', ['The crankshaft', 'Suction and discharge check valves', 'The motor', 'The packing'], 1, 'Valves.'),
          Q('"Double-acting" means…', ['Two motors', 'The piston pumps on both strokes', 'Two speeds', 'Two seals'], 1, 'Both sides of the piston work.'),
          Q('Why are pulsation dampeners used?', ['To prime', 'To smooth the pulsating flow and reduce pipe vibration', 'To cool', 'To filter'], 1, 'Reciprocating flow pulsates.'),
          Q('Acceleration head on the suction side…', ['Is negligible', 'Reduces available NPSH and must be included', 'Increases flow', 'Only affects discharge'], 1, 'Accelerating the suction column costs pressure.', 'intermediate')],
)

MODULES['plunger_pump'] = mod(
    definition=('A plunger pump uses a smooth plunger that moves through stationary packing into the fluid chamber, displacing liquid on each stroke; spring-loaded check valves direct the flow. '
                'Because the seal is stationary, plunger pumps reach much higher pressures than piston pumps. Triplex designs (three plungers 120° apart) smooth the flow.'),
    applications=['High-pressure water jetting and descaling', 'Oil & gas injection (glycol, methanol, water)', 'Reverse osmosis high-pressure feed (small units)', 'Alumina: high-pressure slurry feed (with diaphragm or packing flush)', 'Hydrostatic testing'],
    key_points=['Stationary packing, moving plunger', 'Triplex reduces pulsation', 'API 674 for process service', 'Very high pressures'],
    principle=[step('The crankshaft drives three crossheads 120° apart.', 'crankshaft'), step('A plunger withdraws and the suction valve opens.', 'suction_valve_1', overlay='flow'),
               step('The plunger advances; the discharge valve opens and liquid is forced out.', 'discharge_valve_1', overlay='flow'), step('Stationary packing seals the plunger.', 'packing_1'),
               step('The distance piece separates the fluid end from the crankcase.', 'distance_piece', cut=False)],
    curve='Flow ∝ speed; pressure limited by rating.',
    params=dict(flow=P('0.01 – 200', 'm³/h'), pressure=P('up to ~1,000 (water jetting >2,000)', 'bar'), head=P('—'), speed=P('100 – 500', 'crank rpm'), efficiency=P('85 – 95', '%')),
    install=dict(foundation=['Rigid foundation.'], alignment=['Drive alignment.'], piping=['Dampeners; suction stabiliser.', _PD_RELIEF], commissioning=_PD_COMM + ['Check packing lubrication/flush.']),
    maint=dict(routine=[M('Check packing leakage.', 'packing_1', 'daily'), M('Check crankcase oil.', 'crankcase', 'daily')], periodic=[M('Inspect valves.', 'suction_valve_2', 'per wear')],
               overhaul=[M('Replace plungers and packing.', 'plunger_1')], lubrication=['Crankcase oil; packing lubricator if fitted.']),
    failures=[F('Packing leakage', ['Leakage at stuffing box'], ['Worn packing, scored plunger'], ['Repack; replace plunger'], 'packing_1'),
              F('Valve failure', ['Pressure drop, knocking'], ['Wear, debris'], ['Replace valve'], 'discharge_valve_2'), F('Cavitation', ['Knocking'], ['Insufficient NPSHa incl. acceleration head'], ['Boost suction'], 'suction_valve_3')],
    quiz=[Q('Main difference between a plunger and a piston pump?', ['Plunger has no valves', 'Plunger seal is stationary (packing), piston seal moves with the piston', 'Piston pumps are higher pressure', 'None'], 1, 'Hence higher pressure capability.'),
          Q('Why triplex?', ['Three times the pressure', 'Smoother flow from three phased plungers', 'Cheaper', 'Fewer valves'], 1, 'Overlapping strokes reduce pulsation.'),
          Q('Which standard covers reciprocating pumps for refinery service?', ['API 610', 'API 674', 'API 675', 'ISO 2858'], 1, 'API 674 — reciprocating; API 675 — metering.', 'intermediate')],
)

MODULES['diaphragm_metering_pump'] = mod(
    definition=('A diaphragm metering pump delivers a precise, adjustable volume per stroke: a diaphragm separates the liquid from the drive, and its stroke is set by a stroke-length adjustment and speed. '
                'In the hydraulic design modelled, a plunger moves hydraulic oil that flexes the diaphragm, so the diaphragm is evenly supported and suits higher pressures.'),
    applications=['Chemical dosing: chlorine/hypochlorite, coagulants, acids, caustic', 'Boiler and cooling-water treatment', 'Refinery and oil-field chemical injection', 'Alumina: flocculant and additive dosing'],
    key_points=['Leak-free (diaphragm)', 'Accuracy typically ±1 % steady-state (API 675)', 'Turndown 10:1 by stroke, more with speed', 'Check valves on the liquid end'],
    principle=[step('The motor drives a worm gear and eccentric that move the plunger back and forth.', 'eccentric'),
               step('The stroke-length knob sets how far the plunger travels — the flow adjustment.', 'stroke_knob'),
               step('The plunger pushes hydraulic oil, which flexes the diaphragm.', 'hydraulic_housing'),
               step('On the suction stroke the suction check valve opens and the liquid end fills.', 'suction_valve', overlay='flow'),
               step('On the discharge stroke the diaphragm pushes the liquid out through the discharge check valve.', 'discharge_valve', overlay='flow')],
    curve='Flow nearly linear with stroke length and speed; almost independent of pressure.',
    params=dict(flow=P('0.1 L/h – 30 m³/h', ''), pressure=P('up to ~20 (mechanical); up to ~350+ (hydraulic diaphragm)', 'bar'), head=P('—'), speed=P('20 – 180', 'strokes/min'),
                efficiency=P('—', '', 'accuracy matters more'), extra={'steady_state_accuracy': P('±1', '%', 'API 675 criterion'), 'turndown': P('10:1 (stroke), up to 100:1 with VFD')}),
    install=dict(foundation=['Skid or bund.'], alignment=['Integral drive.'], piping=['Back-pressure valve to prevent siphoning; pulsation dampener; calibration column on suction.', _PD_RELIEF],
                 commissioning=['Prime the liquid end; calibrate flow at several stroke settings.']),
    maint=dict(routine=[M('Check dosing rate with the calibration column.', 'liquid_end', 'weekly')], periodic=[M('Replace diaphragm.', 'diaphragm', 'per manual'), M('Clean/replace check valves.', 'suction_valve', 'per manual')],
               overhaul=[M('Change hydraulic and gear oil.', 'drive_housing')], lubrication=['Gear oil and hydraulic oil per manual.']),
    failures=[F('Inaccurate dosing', ['Wrong flow'], ['Dirty check valves, air in liquid end', 'No back-pressure (siphoning)'], ['Clean valves; vent; fit back-pressure valve'], 'discharge_valve'),
              F('Diaphragm rupture', ['Leak detector alarm'], ['Fatigue, over-pressure'], ['Replace diaphragm'], 'diaphragm'),
              F('Gas locking', ['No delivery'], ['Off-gassing chemicals (hypochlorite)'], ['Degassing liquid end'], 'liquid_end')],
    quiz=[Q('How is the flow of a metering pump usually adjusted?', ['Throttling valve', 'Stroke length and stroke frequency', 'Impeller trimming', 'Bypass only'], 1, 'Both change displaced volume per time.'),
          Q('Why fit a back-pressure valve on a dosing line into a low-pressure point?', ['To increase flow', 'To prevent siphoning/over-dosing', 'To cool', 'To prime'], 1, 'Ensures valves seat properly.'),
          Q('Which standard covers controlled-volume (metering) pumps?', ['API 610', 'API 674', 'API 675', 'NFPA 20'], 2, 'API 675.', 'intermediate'),
          Q('Advantage of hydraulic actuation of the diaphragm?', ['Lower cost', 'Diaphragm evenly supported by oil — higher pressures and longer life', 'No oil needed', 'Higher speed'], 1, 'Balanced pressure across the diaphragm.')],
)

MODULES['aodd_pump'] = mod(
    definition=('An air-operated double-diaphragm (AODD) pump uses compressed air to push two diaphragms connected by a shaft. While one diaphragm discharges liquid, the other draws liquid in; '
                'an air valve shifts the air at each stroke end, and check balls make the flow one-way. It can run dry, self-primes and stalls safely against a closed valve.'),
    applications=['Chemical and solvent transfer', 'Slurries, paints, sludge', 'Drum and tank emptying', 'Mining dewatering', 'Hazardous areas (no electric motor)'],
    key_points=['Discharge pressure cannot exceed the air pressure (1:1 models)', 'Dead-heads safely — stalls', 'Pulsating flow', 'Air consumption makes it less energy-efficient'],
    principle=[step('Compressed air enters the chamber behind one diaphragm, pushing it outward and discharging liquid.', 'diaphragm_left', overlay='flow'),
               step('The shaft pulls the other diaphragm inward, drawing liquid through its inlet ball valve.', 'diaphragm_right', overlay='flow'),
               step('At the end of the stroke the pilot valve shifts the air spool, reversing the air flow.', 'air_valve_spool'),
               step('Check balls in the manifolds open and close to keep the flow one-way.', 'ball_inlet_left', overlay='flow'), step('Exhaust air leaves through the muffler.', 'muffler', cut=False)],
    curve='Flow falls as discharge pressure rises; at a given air pressure the pump stalls when discharge pressure equals air pressure.',
    params=dict(flow=P('up to ~70', 'm³/h', 'largest 3-inch models — verify per manufacturer'), pressure=P('up to ~8.6 (1:1); ~17 for 2:1 pressure-boosting models', 'bar'), head=P('—'),
                speed=P('—', '', 'stroke rate set by air flow'), efficiency=P('low (compressed-air driven)', ''),
                extra={'solids': P('up to ~10', 'mm', 'size dependent'), 'dry_suction_lift': P('up to ~5–7', 'm')}),
    install=dict(foundation=['Free-standing or bolted; vibration isolation pads.'], alignment=['None (air-driven).'],
                 piping=['Flexible connections reduce vibration; pulsation dampener on discharge.', 'Air supply with filter–regulator; air shut-off valve.'],
                 commissioning=['Start with low air pressure; increase gradually.', 'Ground the pump for flammable liquids.']),
    maint=dict(routine=[M('Check for leakage at the muffler (diaphragm failure sign).', 'muffler', 'daily')], periodic=[M('Replace diaphragms.', 'diaphragm_left', 'per hours'), M('Inspect balls and seats.', 'ball_outlet_left', 'per hours')],
               overhaul=[M('Rebuild the air valve.', 'air_valve')], lubrication=['Most modern air valves are lube-free.']),
    failures=[F('Diaphragm rupture', ['Product out of the exhaust'], ['Fatigue, chemical attack'], ['Replace; check material'], 'diaphragm_left'),
              F('Air valve stalling / icing', ['Pump stops'], ['Wet air, high air pressure drop'], ['Dry air, de-icing'], 'air_valve'),
              F('Check-ball wear', ['Low flow'], ['Abrasives'], ['Replace balls/seats'], 'ball_inlet_right')],
    quiz=[Q('Maximum discharge pressure of a standard 1:1 AODD pump is about…', ['Twice the air pressure', 'Equal to the air supply pressure', 'Unlimited', 'Half the air pressure'], 1, 'It stalls when pressures balance.'),
          Q('What happens if the discharge valve is closed?', ['The pump bursts', 'The pump stalls safely', 'The motor overloads', 'It cavitates'], 1, 'Air-driven pumps dead-head.'),
          Q('Liquid coming out of the exhaust muffler indicates…', ['Normal operation', 'A ruptured diaphragm', 'Low air pressure', 'High flow'], 1, 'Diaphragm failure.'),
          Q('Which parts make the flow one-way?', ['Diaphragms', 'Check balls and seats', 'The air valve', 'The shaft'], 1, 'Ball valves.')],
)
