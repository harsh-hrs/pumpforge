"""Learning content — Material Handling & Heavy Machinery, part B (EQ-210 … EQ-227):
stockyard machines, conveyors, pneumatic conveying, lifting equipment, hydraulics."""
from pumpforge.learning import mod, step, P, F, Q, M
from content.material_handling_a import mh, _maint

MODULES = {}

_YARD_INST = dict(
    foundation=['Rails on a continuous foundation (ballast or concrete beam) to the specified tolerances for gauge, level and straightness; rail joints welded or tight-fished.',
                'Design for wheel loads including wind and storm conditions; fit storm anchors/rail clamps and end stops with buffers.'],
    alignment=['Align the machine\'s yard-conveyor interface (tripper or feed chute) with the yard conveyor; check slew bearing level and bolt pre-tension.'],
    piping=['Power and control by cable reel (festoon or motorised reel) along the rail track; anti-collision and boom-to-pile sensors.',
            'Dust suppression water supply and sprays at transfer points where required.'],
    commissioning=['Test travel, slew, luff and conveyor drives individually, then interlocks (slew limits, anti-collision, overload, wind speed cut-out).',
                   'Load-test the boom conveyor and record power; check stability calculations against the as-built mass.'])
_CONV_INST = dict(
    foundation=['Support the conveyor stringers and drive frames on steelwork or plinths designed for belt tension, material load and drive torque.'],
    alignment=['Survey the structure so all pulleys and idlers are square to the centre line; train the belt empty, then loaded.'],
    piping=['Chutes designed for the material trajectory to centre-load the belt; skirts and dust seals at loading points; belt cleaners and plough at the discharge.'],
    commissioning=['Check pull-wire emergency stops, belt-drift and speed switches; run empty and loaded; record take-up position and motor current.'])
_LIFT_INST = dict(
    foundation=['Runway beams, columns or pillar foundations designed for the crane wheel/moment loads including dynamic and test loads (structural engineer sign-off).'],
    alignment=['Rails/beams within span, level and straightness tolerances; end stops and buffers fitted.'],
    piping=['Power supply via conductor rails, festoon or cable reel; mainline isolator accessible; pendant or radio control labelled with directions.'],
    commissioning=['Function-test all motions and limit switches (hoist upper/lower, travel); check brakes; proof load test and thorough examination by a competent person before first use, per the applicable standard and local regulations.'])
_HYD_INST = dict(
    foundation=['Mount on a level, rigid base with access for filters, gauges and fill; drip tray/bund under the reservoir.'],
    alignment=['Align motor and pump with the bell housing and coupling; mount cylinders so the rod is not side-loaded (use spherical bearings/clevises).'],
    piping=['Clean (pickled/flushed) pipework sized for velocity (typical guide: suction ≲ 1.2 m/s, pressure 3–6 m/s, return ≲ 3 m/s); hoses not twisted or rubbing; correct fittings for pressure.',
            'Fit pressure gauges/test points, and relief protection on every pressure source.'],
    commissioning=['Fill through a filter with the specified oil; flush the system to the target cleanliness (ISO 4406 code).',
                   'Bleed air; start with relief valves backed off, then set pressures; check for leaks, temperatures and noise.'])
_GEAR_LUBE = ['Gearboxes: oil to grade and change interval; open gears and slew bearing: grease to schedule.', 'Wheels and pulley bearings: grease to schedule.']

# ===================================================================== stockyard machines
_BOOM_FAIL = [F('Boom conveyor belt damage', ['Spillage, belt edge wear'], ['Mistracking, material build-up, impact at the transfer'], ['Re-train belt; clean; repair chutes'], 'superstructure'),
              F('Slew bearing wear', ['Rocking, noise, increased tilt clearance'], ['Lubrication failure, overload'], ['Measure tilt; grease; replace if limits exceeded'], 'superstructure'),
              F('Long-travel misalignment', ['Wheel flange wear, crabbing'], ['Rail misalignment, uneven wheel diameters'], ['Survey rails; match wheels'], 'portal')]

MODULES['stacker'] = mod(
    definition=('A stacker builds stockpiles of bulk material such as coal, iron ore and limestone. It travels on rails beside the yard conveyor. A tripper on the yard conveyor raises the material '
                'onto the stacker\'s boom conveyor; the boom can slew (rotate) and luff (raise and lower) to place the material where it is needed on the pile. '
                'A counterweight balances the boom.'),
    applications=['Coal stockyards at power plants and ports', 'Iron ore and limestone blending beds', 'Bulk export/import terminals'],
    key_points=['Travel, slew and luff motions', 'Boom conveyor discharges at the tip', 'Stacking methods: cone shell, chevron, windrow (for blending)', 'Counterweight keeps the machine stable'],
    principle=[step('Material arrives on the yard conveyor.', 'yard_conveyor', overlay='flow'), step('The portal travels along the rails to the stacking position.', 'portal'),
               step('The boom conveyor carries material to the boom tip; the superstructure slews to spread it.', 'superstructure', overlay='flow'),
               step('Material falls from the tip and builds the stockpile.', 'stockpile')],
    curve='Stacking rate equals the yard conveyor rate; pile capacity ∝ pile length × cross-section (angle of repose).',
    params=mh(P('Boom ~ 20 – 60 m'), P('~ 100 – 1000 (total connected)', 'kW'), P('Boom belt ~ 2 – 5 m/s; travel ~ 0.1 – 0.5 m/s', 'm/s'), P('~ 500 – 10 000+', 't/h')),
    install=_YARD_INST,
    maint=_maint([M('Walk-down: belt, chutes, spillage, cable reel.', 'superstructure', 'daily')], [M('Check rails, wheels and buffers.', 'rails', 'monthly')],
                 [M('Slew bearing inspection; boom structure NDT; conveyor pulleys.', 'superstructure')], _GEAR_LUBE),
    failures=_BOOM_FAIL,
    quiz=[Q('Which motion rotates the boom about a vertical axis?', ['Luffing', 'Slewing', 'Travelling', 'Tripping'], 1, 'Slew = rotate.'),
          Q('What is the job of the counterweight?', ['Balance the boom and keep the machine stable', 'Weigh the coal', 'Drive the belt', 'Cool the motors'], 0, 'Stability.'),
          Q('Chevron/windrow stacking is used to…', ['Blend material of varying quality', 'Save paint', 'Increase dust', 'Stop the belt'], 0, 'Blending beds.')],
    selection=['Choose boom length and height from pile width/height; capacity from the yard conveyor rate; consider wind and seismic design.'],
    safety=['Anti-collision with other machines; wind speed limits and storm pins; exclusion zone around the boom and pile.'],
    refs=['ISO 5049-1 — Mobile equipment for continuous handling of bulk materials (design rules)', 'FEM 2.131/2.132 — Design rules for mobile equipment for continuous handling of bulk materials'])

MODULES['reclaimer'] = mod(
    definition=('A bucket wheel reclaimer recovers material from a stockpile. A wheel with buckets turns at the end of a slewing boom. As the boom slews across the pile face, the buckets dig material '
                'and tip it onto the boom conveyor, which carries it to the centre of the machine and down onto the yard conveyor. The machine advances along the rails a little after each pass.'),
    applications=['Reclaiming coal, ore and limestone from stockpiles', 'Feeding power plants, sinter plants and ship loaders', 'Blending (bridge or boom types)'],
    key_points=['Continuous digging by bucket wheel', 'Slew + travel + luff to follow the pile face', 'Reclaim rate controlled by slew speed and cut depth', 'Material flows from wheel → boom belt → centre chute → yard conveyor'],
    principle=[step('The bucket wheel turns and its buckets cut into the pile face.', 'bucket_wheel'), step('Buckets tip material onto the boom conveyor.', 'coal', overlay='flow'),
               step('The boom slews from side to side across the pile.', 'superstructure'),
               step('The boom belt carries the material back to the centre chute and the yard conveyor.', 'yard_conveyor', overlay='flow')],
    curve='Reclaim rate rises with slew speed and cut depth; slew speed is varied across the arc to keep the rate constant.',
    params=mh(P('Wheel ~ 4 – 10 m; boom ~ 25 – 60 m'), P('~ 200 – 1500 (total)', 'kW'), P('Wheel ~ 5 – 10 rpm', 'rpm'), P('~ 500 – 10 000+', 't/h')),
    install=_YARD_INST,
    maint=_maint([M('Inspect buckets, teeth and wheel chute.', 'bucket_wheel', 'daily')], [M('Wheel drive gearbox oil analysis; slew drive inspection.', 'superstructure', 'monthly')],
                 [M('Replace bucket lips/teeth; overhaul wheel drive.', 'bucket_wheel')], _GEAR_LUBE),
    failures=_BOOM_FAIL + [F('Bucket tooth wear', ['Falling rate, high wheel power'], ['Abrasive material'], ['Replace teeth/lips'], 'bucket_wheel')],
    quiz=[Q('How is reclaim rate mainly controlled?', ['Slew speed and cut depth', 'Paint thickness', 'Rail size', 'Pile colour'], 0, 'Digging parameters.'),
          Q('Where does the material go after the buckets?', ['Onto the boom conveyor, then to the yard conveyor', 'Back to the pile', 'Into the counterweight', 'Into the cab'], 0, 'Flow path.'),
          Q('Why does the slew speed vary across the arc?', ['The cut cross-section changes with angle, so speed is adjusted to keep the rate constant', 'To make noise', 'To cool the wheel', 'It does not vary'], 0, 'Constant rate.')],
    selection=['Select wheel diameter and bucket size for rate and material; check digging forces for hard/compact material.'],
    safety=['Exclusion zone at the pile toe (pile collapse); anti-collision; wind limits.'],
    refs=['ISO 5049-1', 'FEM 2.131/2.132'])

MODULES['stacker_reclaimer'] = mod(
    definition=('A bucket wheel stacker-reclaimer does both jobs with one machine. Its boom conveyor is reversible. In stacking mode the yard conveyor feeds material up to the boom, which carries '
                'it to the tip and builds the pile. In reclaiming mode the belt runs the other way: the bucket wheel digs material and the boom carries it back to the yard conveyor (which also reverses).'),
    applications=['Smaller stockyards where one machine can handle both duties', 'Power-plant coal yards', 'Port stockyards'],
    key_points=['Reversible boom conveyor', 'One machine stacks OR reclaims at any time', 'Lower capital cost than two machines', 'Throughput limited because duties cannot run together'],
    principle=[step('Stacking mode: material from the yard conveyor goes up the boom to the tip.', 'yard_conveyor', overlay='flow'),
               step('Reclaiming mode: the bucket wheel digs material from the pile.', 'bucket_wheel'),
               step('The reversible boom belt carries reclaimed material back to the centre.', 'superstructure', overlay='flow'),
               step('The machine travels and slews to work the whole pile.', 'portal')],
    curve='Yard availability limited: total hours = stacking hours + reclaiming hours.',
    params=mh(P('Boom ~ 25 – 50 m; wheel ~ 4 – 8 m'), P('~ 200 – 1200 (total)', 'kW'), P('Belt ~ 2 – 5 m/s; wheel ~ 5 – 10 rpm', 'm/s'), P('~ 500 – 6000', 't/h')),
    install=_YARD_INST,
    maint=_maint([M('Inspect wheel, belt and chutes for both modes.', 'bucket_wheel', 'daily')], [M('Check reversing interlocks and tripper.', 'yard_conveyor', 'monthly')],
                 [M('Overhaul wheel and slew drives.', 'superstructure')], _GEAR_LUBE),
    failures=_BOOM_FAIL,
    quiz=[Q('What makes a stacker-reclaimer able to do both duties?', ['A reversible boom conveyor plus a bucket wheel', 'Two booms', 'A pump', 'A crane hook'], 0, 'Reversible belt.'),
          Q('A disadvantage compared with separate machines is…', ['It cannot stack and reclaim at the same time', 'It has no wheel', 'It is always more expensive', 'It cannot travel'], 0, 'One duty at a time.'),
          Q('In reclaim mode the boom belt runs…', ['Towards the machine centre', 'Towards the tip', 'Not at all', 'Vertically'], 0, 'Reverse direction.')],
    selection=['Use when stacking and reclaiming schedules can be separated; check total yard throughput.'],
    safety=['Mode-change interlocks for belt direction; anti-collision; wind limits.'],
    refs=['ISO 5049-1', 'FEM 2.131/2.132'])

MODULES['bucket_wheel_excavator'] = mod(
    definition=('A bucket wheel excavator (BWE) is a continuous mining machine used in large open-cast mines. A rotating wheel of buckets on the end of a boom cuts overburden, lignite or coal from the bench '
                'as the boom slews. The material falls onto the boom conveyor and is transferred through the machine to the discharge boom, which loads the mine\'s belt conveyor system. '
                'Crawler tracks move the machine.'),
    applications=['Lignite and brown-coal open-cast mines', 'Overburden removal', 'Large earth-moving projects in soft-to-medium material'],
    key_points=['Continuous digging — high output', 'Crawler-mounted, slewing upper structure', 'Suited to soft/medium, non-blocky material', 'Feeds mine conveyor systems'],
    principle=[step('The bucket wheel turns and cuts into the bench.', 'bucket_wheel'), step('Material falls onto the boom conveyor and travels to the centre.', 'spoil', overlay='flow'),
               step('The superstructure slews to sweep the wheel across the face.', 'superstructure'),
               step('The discharge boom loads the material onto the mine conveyor; crawlers advance the machine.', 'discharge_boom', overlay='flow')],
    curve='Theoretical output = bucket volume × discharges per minute × fill factor ÷ swell factor; actual output depends on digging resistance and slew technique.',
    params=mh(P('Compact BWE wheel ~ 3 – 8 m; giant BWEs wheel ~ 20 m'), P('~ 0.5 – 15+ (MW range for large units)', 'MW'), P('Wheel ~ 3 – 10 rpm', 'rpm'), P('~ 500 – 10 000+', 'm³/h')),
    install=dict(foundation=['Prepared, levelled bench with adequate ground-bearing capacity for crawler pressure; drainage of the working level.'],
                 alignment=['Plan bench height and block width to match wheel diameter and boom reach.'],
                 piping=['Power by trailing cable from a mine substation via cable reel; communications with conveyor control.'],
                 commissioning=['Assemble and test each drive; check slew/luff brakes, wheel overload protection and collision sensors; trial digging.']),
    maint=_maint([M('Inspect bucket teeth and lips, wheel chute and belts.', 'bucket_wheel', 'daily')], [M('Inspect crawler pads, rollers and drive.', 'crawlers', 'weekly')],
                 [M('Structural inspections (NDT) of boom and mast; slew bearing.', 'superstructure')], _GEAR_LUBE),
    failures=[F('Tooth/bucket wear', ['High wheel power, falling output'], ['Abrasive or hard material'], ['Change teeth; adjust cutting technique'], 'bucket_wheel'),
              F('Crawler damage', ['Broken pads, track derailing'], ['Soft ground, rocks'], ['Improve bench preparation; replace pads'], 'crawlers')],
    quiz=[Q('What is the main advantage of a BWE?', ['Continuous high output digging', 'It can dig hard granite easily', 'It needs no power', 'It is small'], 0, 'Continuous excavation.'),
          Q('How does material leave the BWE?', ['Via boom and discharge conveyors to the mine belt system', 'By trucks loaded by hand', 'Through a pipe', 'It stays on the wheel'], 0, 'Conveyor loading.'),
          Q('BWEs are best suited to…', ['Soft-to-medium materials like lignite and overburden', 'Blasted hard rock only', 'Liquids', 'Fine powders in silos'], 0, 'Digging resistance limits.')],
    selection=['Check digging resistance (cutting force per cm of cutting edge), bench geometry and required output.'],
    safety=['Exclusion zones; slope stability; trailing-cable management; lightning and wind limits.'],
    refs=['Surface mining engineering handbooks (SME)', 'Manufacturer BWE data'])

# ===================================================================== conveyors
MODULES['tripper_conveyor'] = mod(
    definition=('A tripper is a travelling car that runs on rails along a belt conveyor. The belt is led up over the tripper\'s head pulley and back down around a snub pulley, so the material '
                'discharges into a chute on the car. By moving the tripper along the conveyor, one belt can fill a long row of bunkers, silos or a stockpile.'),
    applications=['Filling coal bunkers in power plants', 'Silo/bin filling in cement and mineral plants', 'Stockpile building on yard conveyors'],
    key_points=['Belt forms an S-loop through the tripper', 'Discharges at any point along the conveyor', 'Motorised or belt-propelled travel', 'Belt must have slack/take-up to allow the loop'],
    principle=[step('Material travels along the belt conveyor.', 'cvbelt', overlay='flow'), step('The belt climbs the tripper ramp to the head pulley.', 'tripper_car'),
               step('Material discharges into the tripper chute, which drops it into the bunker below.', 'bunkers', overlay='flow'),
               step('The tripper travels on its rails to fill the next bunker.', 'rails')],
    curve='Belt tension rises at the tripper (lift + extra pulleys) — included in the conveyor power calculation.',
    params=mh(P('Belt ~ 0.65 – 2 m wide'), P('Travel drive ~ 2 – 20', 'kW'), P('Belt ~ 1.5 – 4 m/s; travel ~ 0.1 – 0.3 m/s', 'm/s'), P('~ 100 – 5000', 't/h')),
    install=_CONV_INST,
    maint=_maint([M('Check chute flow and belt tracking at the tripper.', 'tripper_car', 'daily')], [M('Check rails, wheels and travel limit switches.', 'rails', 'monthly')],
                 [M('Replace pulley lagging and bearings.', 'cvpulley_2')], _GEAR_LUBE),
    failures=[F('Belt mistracking at tripper', ['Spillage, edge damage'], ['Pulley misalignment, build-up'], ['Re-align; clean; training idlers'], 'tripper_car'),
              F('Chute blockage', ['Overflow, motor trips'], ['Wet material, full bunker'], ['Level probes; chute design; clear safely'], 'bunkers')],
    quiz=[Q('How does a tripper discharge material?', ['It lifts the belt over a head pulley so material falls into its chute', 'It cuts the belt', 'It reverses the belt', 'It weighs the belt'], 0, 'S-loop over the head pulley.'),
          Q('Why use a tripper?', ['To fill many bunkers from one conveyor', 'To crush coal', 'To dry coal', 'To drive the belt'], 0, 'Distribution.'),
          Q('Which pulley wraps the belt back down after the head pulley?', ['Snub pulley', 'Tail pulley only', 'Bend pulley at the drive', 'There is none'], 0, 'Snub pulley.')],
    selection=['Check additional belt tension from the tripper lift; design chutes for material trajectory; specify travel speed.'],
    safety=['Guard pulleys and nip points; pull-wire stops along the gallery; bunker grating to prevent falls.'],
    refs=['CEMA — Belt Conveyors for Bulk Materials', 'ISO 5048 — Belt conveyors: calculation of operating power and tensile forces'])

MODULES['shuttle_conveyor'] = mod(
    definition=('A shuttle conveyor is a short, reversible belt conveyor mounted on a travelling carriage. Material falls onto it from a fixed feed chute. By running the belt one way or the other and '
                'moving the carriage, it can discharge from either end along a row of bins, so one feed point can fill many bins on both sides.'),
    applications=['Bin and silo filling where a tripper would be too long', 'Coal and coke bunker distribution', 'Grain and fertiliser storage'],
    key_points=['Reversible belt + travelling carriage', 'Discharges from either end', 'Shorter than a tripper system', 'Interlocks prevent discharge with no bin below'],
    principle=[step('Material falls from the fixed feed chute onto the belt.', 'feed_chute', overlay='flow'), step('The belt runs towards the end above the bin being filled.', 'scbelt'),
               step('The carriage travels so the discharging end moves along the bins.', 'carriage'),
               step('The belt reverses to fill the bins on the other side.', 'scpulley_1', overlay='flow')],
    curve='Coverage length ≈ carriage travel + belt length; rate equals the feed rate.',
    params=mh(P('Belt ~ 0.5 – 1.6 m wide, 3 – 30 m long'), P('~ 3 – 75', 'kW'), P('Belt ~ 1 – 3 m/s', 'm/s'), P('~ 50 – 2000', 't/h')),
    install=_CONV_INST,
    maint=_maint([M('Check belt tracking in both directions.', 'scbelt', 'daily')], [M('Check carriage wheels and rails.', 'carriage', 'monthly')],
                 [M('Replace belt, pulleys and bearings.', 'scpulley_2')], _GEAR_LUBE),
    failures=[F('Mistracking after reversal', ['Belt runs off'], ['Directional training idlers, misalignment'], ['Use reversible trainers; align'], 'scbelt'),
              F('Overfill of a bin', ['Spillage'], ['Failed level sensor/interlock'], ['Test level probes; interlocks'], 'rails_bins')],
    quiz=[Q('What allows a shuttle conveyor to fill bins on both sides?', ['Reversible belt and travelling carriage', 'Two motors on the bins', 'A crusher', 'Gravity only'], 0, 'Reversing + travel.'),
          Q('Where does material enter?', ['From a fixed central feed chute', 'From the bins', 'From the rails', 'From the motor'], 0, 'Fixed feed.'),
          Q('Compared with a tripper, a shuttle conveyor…', ['Is shorter and discharges from its ends', 'Uses an S-loop', 'Cannot move', 'Has no belt'], 0, 'End discharge.')],
    selection=['Size carriage travel and belt length to cover the bin row; use reversible belt cleaners and trainers.'],
    safety=['Travel limit switches and end stops; level interlocks; guarding.'],
    refs=['CEMA — Belt Conveyors for Bulk Materials'])

MODULES['drag_chain_conveyor'] = mod(
    definition=('A drag chain (en-masse) conveyor moves bulk solids inside an enclosed casing. A chain with flights runs along the bottom; the flights drag the material, and because the material '
                'moves as a solid mass with the chain (the "en-masse" principle), the bed moves even above the flights. It is dust-tight, gentle, and can run horizontal, inclined or vertical.'),
    applications=['Cement, clinker and raw meal', 'Grain and feed handling', 'Coal, ash and wood chips', 'Hot and abrasive materials (with suitable liners)'],
    key_points=['Totally enclosed and dust-tight', 'Low speed (≈ 0.1 – 0.5 m/s)', 'Multiple inlets and outlets possible', 'Chain elongation and wear are the main issues'],
    principle=[step('Material enters through the inlet spout onto the chain.', 'inlet_outlet', overlay='flow'), step('The drive turns the head sprocket, pulling the chain.', 'sprocket_2'),
               step('Flights drag the material bed along the casing bottom as a mass.', 'chain', overlay='flow'), step('Material leaves through the bottom outlet; the chain returns on top.', 'casing')],
    curve='Capacity Q ≈ 3600 · B · h · v · ρ · η (η ~ 0.7–0.9) — linear with chain speed.',
    params=mh(P('Casing width ~ 0.15 – 1.2 m'), P('~ 2 – 110', 'kW'), P('~ 0.1 – 0.5', 'm/s'), P('~ 10 – 1000', 't/h')),
    install=_CONV_INST,
    maint=_maint([M('Check chain tension and noise.', 'sprocket_1', 'daily')], [M('Measure chain elongation; inspect flights and liners.', 'chain', 'quarterly')],
                 [M('Replace chain and sprockets together when worn.', 'chain')], ['Gearmotor oil; take-up screws and bearings greased.']),
    failures=[F('Chain elongation', ['Chain jumps sprockets, noise'], ['Wear of pins/bushes'], ['Adjust take-up; replace chain+sprockets'], 'chain'),
              F('Casing floor wear', ['Holes, leaks'], ['Abrasive material'], ['Wear liners'], 'casing')],
    quiz=[Q('What is the "en-masse" principle?', ['Material moves as a solid mass with the chain', 'Material is blown by air', 'Material falls freely', 'Material is weighed'], 0, 'Mass flow.'),
          Q('A key advantage of drag chain conveyors is…', ['Dust-tight enclosure', 'Very high speed', 'Open top', 'No chain'], 0, 'Enclosed.'),
          Q('Why replace chain and sprockets together?', ['Worn sprockets quickly wear new chain', 'For colour matching', 'It is required by law', 'They are one part'], 0, 'Pitch mismatch.')],
    selection=['Choose casing width/chain speed for the volumetric rate; materials and liners for temperature and abrasion.'],
    safety=['Lock out before opening inspection doors; chain nip at sprockets.'],
    refs=['CEMA — Bulk handling conveyors', 'Manufacturer en-masse conveyor data'])

MODULES['pneumatic_conveying_system'] = mod(
    definition=('A pneumatic conveying system transports powders and granules through a closed pipeline using air (or nitrogen). In a dilute-phase pressure system, a blower supplies air, '
                'a rotary airlock feeds the solids into the line, and the particles are carried in suspension at high air velocity. At the destination, a receiver with a bag filter '
                'separates the solids from the air and drops them into the silo.'),
    applications=['Cement, fly ash and flour transfer', 'Plastic pellets and powders', 'Food and pharmaceutical powders', 'Bulk tanker unloading'],
    key_points=['Dilute phase: high velocity (≈ 15–30 m/s), particles suspended', 'Dense phase: low velocity, plugs/dunes — gentler, less wear', 'Flexible routing; enclosed and clean', 'Bends are the main wear and degradation points'],
    principle=[step('The blower supplies conveying air.', 'blower', overlay='flow'), step('The rotary airlock feeds solids from the hopper into the air stream.', 'feed_hopper_valve'),
               step('Particles are carried along the pipeline and around long-radius bends.', 'pipeline', overlay='flow'),
               step('The receiver and bag filter separate solids from the air; solids drop into the silo.', 'receiver_filter'), step('The silo stores the delivered material.', 'silo')],
    curve='Pressure drop vs air velocity (state diagram): too low velocity → saltation and blockage; too high → wear, degradation and power waste.',
    params=mh(P('Pipeline ~ 50 – 250 mm bore; up to a few hundred m'), P('~ 5 – 300', 'kW'), P('Air velocity ~ 15 – 30 (dilute); < ~ 10 (dense)', 'm/s'), P('~ 0.5 – 100+', 't/h')),
    install=_CONV_INST | dict(piping=['Use long-radius or special wear-resistant bends; align flanges perfectly (steps cause wear and blockages).',
                                      'Fit pressure transmitters along the line and a pressure relief on the blower; earth the pipeline (static).']),
    maint=_maint([M('Monitor line pressure and blower current.', 'blower', 'daily')], [M('Check bends for wear (thickness gauging); check filter ΔP.', 'pipeline', 'monthly')],
                 [M('Replace filter bags, bends and airlock rotor.', 'receiver_filter')], ['Blower: oil level and change interval; airlock bearings greased.']),
    failures=[F('Line blockage', ['Rising pressure, no delivery'], ['Air velocity too low, overfeeding, moisture'], ['Clear; increase air or reduce feed; dry air'], 'pipeline'),
              F('Bend wear-through', ['Leaks, dust'], ['Abrasive material at high velocity'], ['Wear-resistant bends; lower velocity'], 'pipeline'),
              F('Filter blinding', ['High ΔP, back-pressure'], ['Moist air, cleaning failure'], ['Check pulse cleaning; replace bags'], 'receiver_filter')],
    quiz=[Q('In dilute-phase conveying, particles are…', ['Suspended in high-velocity air', 'Pushed as solid plugs', 'Carried on a belt', 'Pumped as slurry'], 0, 'Suspension flow.'),
          Q('Where does most wear occur?', ['At bends', 'At the silo roof', 'In the blower silencer', 'In straight lines only'], 0, 'Impact at bends.'),
          Q('What happens if the air velocity is too low?', ['Particles settle and the line can block', 'Wear increases', 'Nothing', 'The material heats'], 0, 'Saltation.')],
    selection=['Choose dilute vs dense phase from material friability/abrasion and distance; size air flow for pick-up velocity with margin.'],
    safety=['Dust explosion risk with combustible dusts — earthing, explosion venting/suppression per ATEX/NFPA; relief valves on pressure sources.'],
    refs=['Mills, D. — Pneumatic Conveying Design Guide', 'NFPA 652/654 — combustible dust (where applicable)'])

MODULES['vibrating_conveyor'] = mod(
    definition=('A vibrating (oscillating) conveyor moves material along a trough by repeated small, angled strokes. The trough is supported on inclined leaf springs (rockers) and driven by an '
                'eccentric crank. Each stroke moves the trough forward and up, throwing the material slightly forward; on the return stroke the trough slides back underneath it. '
                'Many designs run near the natural frequency of the spring system, which keeps drive power low.'),
    applications=['Hot castings and foundry sand', 'Food products (easy to clean, gentle)', 'Chemicals and abrasive granules', 'Distribution and spreading'],
    key_points=['No belt or chain — trough is the only contact part', 'Gentle, easy-clean, good for hot/abrasive material', 'Spring angle sets the stroke direction', 'Conveying speed typically ≈ 0.1 – 0.3 m/s'],
    principle=[step('Material is fed onto the trough.', 'trough', overlay='flow'), step('The eccentric drive turns and the connecting arm pushes the trough.', 'eccentric_drive'),
               step('The inclined leaf springs guide the trough forward and up on each stroke.', 'rockers'),
               step('Particles hop forward a little each cycle and discharge at the end.', 'parts', overlay='flow')],
    curve='Conveying speed rises with stroke and frequency; above a throw number of ~1, particles leave the trough each cycle.',
    params=mh(P('Trough ~ 0.2 – 1.5 m wide, up to ~ 30 m'), P('~ 0.5 – 30', 'kW'), P('~ 5 – 15 Hz (300 – 900 strokes/min)', 'Hz'), P('~ 1 – 500', 't/h')),
    install=_CONV_INST | dict(foundation=['Anchor the base frame firmly — or use a balanced (counter-oscillating) design to reduce forces transmitted to the floor.']),
    maint=_maint([M('Check stroke, noise and material flow.', 'trough', 'daily')], [M('Inspect leaf springs and rubber bushes; check bolts.', 'rockers', 'monthly')],
                 [M('Replace springs, connecting-arm bushes and eccentric bearings.', 'connecting_arm')], ['Eccentric shaft bearings: grease to schedule.']),
    failures=[F('Leaf spring cracking', ['Change in stroke, noise'], ['Fatigue, over-stroke'], ['Replace in sets; check tuning'], 'rockers'),
              F('Slow conveying', ['Material piles up'], ['Low stroke, worn bushes, sticky material'], ['Adjust drive; replace bushes; clean trough'], 'eccentric_drive')],
    quiz=[Q('What sets the direction of trough motion?', ['The angle of the leaf springs', 'Trough colour', 'Feed rate', 'Motor size only'], 0, 'Springs guide the motion.'),
          Q('Why are vibrating conveyors used for hot castings?', ['Only the steel trough contacts the material — no belt to burn', 'They are cold', 'They have rubber belts', 'They are slow'], 0, 'All-steel contact.'),
          Q('Running near natural frequency means…', ['Low drive power for a given stroke', 'No vibration', 'Higher noise only', 'No springs'], 0, 'Resonance assists.')],
    selection=['Size trough for rate at the conveying speed; select natural-frequency or brute-force design; balanced design for weak floors.'],
    safety=['Guard the drive; keep clear of the oscillating trough; lock out before clearing.'],
    refs=['CEMA — Vibrating conveyors', 'Manufacturer data'])

# ===================================================================== lifting
MODULES['screw_jack'] = mod(
    definition=('A screw jack (worm-gear screw jack) lifts or positions loads. A worm on the input shaft drives a worm wheel (gear) inside the housing; the worm wheel turns a nut or the screw, so the '
                'lifting screw moves up or down. The large gear ratio gives a high force from a small motor, and trapezoidal-thread jacks are usually self-locking, holding the load without a brake.'),
    applications=['Lifting platforms and stages', 'Positioning rolls, gates and antennas', 'Synchronised multi-jack lifting systems', 'Valve and damper actuation'],
    key_points=['Worm gear ratio typically ~ 4 : 1 to 32 : 1', 'Trapezoidal screws usually self-locking; ball screws are not (need a brake)', 'Several jacks can be linked by shafts for synchronised lifting', 'Duty cycle limited by heat'],
    principle=[step('The motor turns the worm shaft.', 'worm'), step('The worm drives the worm wheel inside the housing.', 'worm_wheel'),
               step('The worm wheel turns the nut, so the lifting screw translates.', 'lifting_screw'), step('The load platform rises or lowers.', 'load', overlay='flow')],
    curve='Input torque = (load × lead) / (2π × η_screw × gear ratio × η_gear) — efficiency of trapezoidal jacks is low (often ~ 20–40 %), which is why they self-lock.',
    params=mh(P('Capacity ~ 0.5 – 100+ t per jack (larger available)'), P('~ 0.18 – 30', 'kW'), P('Lifting ~ 0.1 – 2 (trapezoidal); higher with ball screws', 'm/min'), P('Load ~ 5 – 1000+', 'kN')),
    install=_LIFT_INST | dict(alignment=['Align the jack so the screw is not side-loaded (use guides for the load); align connecting shafts in multi-jack systems.']),
    maint=_maint([M('Listen for noise; check for backlash and screw lubrication.', 'lifting_screw', 'weekly')], [M('Check backlash in worm gear and nut.', 'worm_wheel', 'quarterly')],
                 [M('Replace worm wheel/nut and bearings when backlash exceeds limits.', 'housing')], ['Grease the screw and gearbox to schedule (high-pressure grease).']),
    failures=[F('Excessive backlash', ['Load drops slightly on reversal'], ['Worn nut/worm wheel'], ['Replace wear parts'], 'worm_wheel'),
              F('Overheating', ['Hot housing, grease breakdown'], ['Duty cycle exceeded'], ['Reduce duty; larger jack; ball screw'], 'housing')],
    quiz=[Q('Why are trapezoidal screw jacks usually self-locking?', ['Low efficiency/friction prevents back-driving', 'They have magnets', 'They have brakes always', 'They are hydraulic'], 0, 'Friction holds load.'),
          Q('What gives the high lifting force?', ['The worm gear ratio and screw lead', 'The motor colour', 'The load platform', 'Gravity'], 0, 'Mechanical advantage.'),
          Q('A ball-screw jack needs…', ['A brake to hold the load', 'No motor', 'Hydraulic oil', 'A larger load'], 0, 'High efficiency = back-drivable.')],
    selection=['Size for static and dynamic load, travel speed, duty cycle and column buckling of the screw.'],
    safety=['Never rely on self-locking under vibration — fit brakes/mechanical stops where people are underneath.'],
    refs=['Manufacturer screw jack catalogues', 'ISO 2901/2904 — Trapezoidal screw threads'])

_CRANE_FAIL = [F('Wire rope damage', ['Broken wires, kinks, corrosion'], ['Wear on sheaves/drum, overload, poor spooling'], ['Inspect and discard per criteria (ISO 4309); correct reeving'], None),
               F('Brake failure', ['Load drift, increased stopping distance'], ['Worn linings, contamination, wrong adjustment'], ['Adjust/replace linings; test brake'], None),
               F('Overload', ['Trip of limiter, structural deformation'], ['Unknown load weight, side pulling'], ['Use load limiter; train riggers'], None)]


def _cf(hoist_pid, rope_pid):
    out = []
    for f in _CRANE_FAIL:
        g = dict(f)
        g['part'] = rope_pid if 'rope' in f['problem'].lower() else hoist_pid
        out.append(g)
    return out


MODULES['gantry_crane'] = mod(
    definition=('A gantry crane has a bridge (one or two girders) supported on legs that run on rails at ground level. A trolley (crab) with a hoist travels across the girders, and the whole gantry travels '
                'along the rails, so the hook can reach any point in a rectangular area. It is used outdoors or where no building structure can carry a runway.'),
    applications=['Shipyards and container terminals', 'Precast concrete and steel stockyards', 'Power plants and dams (maintenance)', 'Rail yards'],
    key_points=['Three motions: hoist, cross-travel (trolley), long-travel (gantry)', 'Legs run on ground rails', 'Duty classification (ISO 4301 / FEM / CMAA) sets design', 'Limit switches and load limiters are essential'],
    principle=[step('The gantry travels along the runway rails (long travel).', 'gantry'), step('The crab/trolley moves across the girders (cross travel).', 'hst_trolley'),
               step('The hoist drum winds the wire rope to raise or lower the hook.', 'hst_rope', overlay='flow'), step('The operator controls from the cab or by radio.', 'cab')],
    curve='Hoist power P ≈ m · g · v / η (W) — e.g. 10 t at 5 m/min with η = 0.85 → ≈ 9.6 kW.',
    params=mh(P('Span ~ 10 – 60 m; lift ~ 6 – 40 m'), P('Hoist ~ 5 – 200', 'kW'), P('Hoist ~ 1 – 15 m/min; travel ~ 20 – 60 m/min', 'm/min'), P('SWL ~ 5 – 500+', 't')),
    install=_LIFT_INST,
    maint=_maint([M('Pre-use check: limits, brakes, rope, hook latch.', 'hst_hook', 'daily/shift')], [M('Inspect ropes, sheaves, wheels and rails.', 'hst_rope', 'monthly')],
                 [M('Thorough examination by a competent person; overhaul hoist gearbox and brakes.', 'gantry', 'per regulation (e.g. 6–12 months)')], _GEAR_LUBE + ['Wire rope: lubricate with rope dressing.']),
    failures=_cf('hst_trolley', 'hst_rope'),
    quiz=[Q('Which motion moves the whole crane along the rails?', ['Long travel', 'Cross travel', 'Hoisting', 'Slewing'], 0, 'Gantry travel.'),
          Q('Hoist power for 10 t at 5 m/min (η 0.85) is about…', ['~ 1 kW', '~ 10 kW', '~ 100 kW', '~ 1 MW'], 1, '9.81e4 × 0.0833 / 0.85 ≈ 9.6 kW.'),
          Q('Why are load limiters fitted?', ['To prevent lifting above the rated load', 'To weigh trucks', 'To speed up', 'To reduce noise'], 0, 'Overload protection.')],
    selection=['Specify SWL, span, lift, speeds, duty class (ISO 4301 group), environment and wind loads.'],
    safety=['Never stand under a suspended load; use trained slingers; check wind speed limits; storm-lock outdoor cranes.'],
    refs=['ISO 4301-1 — Cranes: classification', 'ASME B30.2 — Overhead and gantry cranes', 'ISO 4309 — Wire ropes: care, maintenance, inspection and discard'])

MODULES['jib_crane'] = mod(
    definition=('A jib crane has a horizontal arm (jib) fixed to a vertical pillar or wall. The jib slews (rotates) around the pillar, and an electric hoist on a trolley travels along the jib. '
                'This covers a circular area around a workstation or machine.'),
    applications=['Machine shops and workstations', 'Loading bays', 'Maintenance of pumps, motors and valves', 'Shipboard and dockside use'],
    key_points=['Slewing arc up to 360° (pillar type)', 'Covers a circular working area', 'Foundation must take a large overturning moment', 'Usually manual or powered slew'],
    principle=[step('The pillar and foundation carry the load and overturning moment.', 'pillar'), step('The jib arm slews around the pillar.', 'jib_arm'),
               step('The hoist trolley travels along the jib to set the radius.', 'hoist_trolley'), step('The hoist lifts the hook and load.', 'hook_load', overlay='flow')],
    curve='Overturning moment at the foundation ≈ (load + hoist) × outreach + jib self-weight moment.',
    params=mh(P('Outreach ~ 2 – 10 m; height ~ 3 – 8 m'), P('Hoist ~ 0.5 – 10', 'kW'), P('Hoist ~ 2 – 8 m/min; slew manual or ~ 0.5 – 1 rpm', 'm/min'), P('SWL ~ 0.25 – 10', 't')),
    install=_LIFT_INST | dict(foundation=['Pillar on a reinforced foundation (or certified anchor system) designed for the overturning moment; check slab thickness and concrete strength.']),
    maint=_maint([M('Pre-use check of hoist, hook and slew.', 'hook_load', 'daily')], [M('Check anchor bolts and slew bearing.', 'pillar', 'quarterly')],
                 [M('Thorough examination; replace slew bearing/hoist wear parts.', 'jib_arm', 'per regulation')], _GEAR_LUBE),
    failures=_cf('hoist_trolley', 'rope'),
    quiz=[Q('What shape of area does a pillar jib crane cover?', ['Rectangle', 'Circle (or sector)', 'Line', 'Triangle'], 1, 'Slewing.'),
          Q('What is the key foundation load?', ['Overturning moment', 'Torsion only', 'Thermal', 'None'], 0, 'Load × outreach.'),
          Q('The trolley on the jib sets the…', ['Radius (outreach) of the hook', 'Lift height', 'Slew speed', 'Rated load'], 0, 'Radius.'),
          Q('A 2 t load at 4 m outreach gives an overturning moment (load only) of about…', ['8 kN·m', '78 kN·m', '780 kN·m', '0.8 kN·m'], 1, '2000 kg × 9.81 × 4 m ≈ 78 kN·m (plus hoist and jib weight).')],
    selection=['Specify SWL, outreach, height under jib, slew arc and duty.'],
    safety=['Keep slewing area clear; do not exceed rated load at maximum outreach.'],
    refs=['ASME B30.11 — Monorails and underhung cranes (jib cranes covered in ASME B30.11 / local codes; to be verified)', 'ISO 4301-1'])

MODULES['monorail_hoist'] = mod(
    definition=('A monorail hoist runs on a single fixed I-beam track, which may be straight or curved. A trolley rolls on the lower flange of the beam and carries an electric chain or wire-rope hoist. '
                'It moves loads along a fixed path — for example from a loading bay to a machine or around a production line.'),
    applications=['Production and assembly lines', 'Moving loads along a fixed route (curves, switches)', 'Maintenance lifting over equipment rows', 'Warehouses'],
    key_points=['Single beam, fixed path', 'Trolley runs on the lower flange', 'Curves and switches allow complex routes', 'Pendant or radio control'],
    principle=[step('The I-beam track is hung from the building structure.', 'track'), step('The trolley travels along the lower flange.', 'hst_trolley', overlay='flow'),
               step('The hoist raises the hook block and load.', 'hst_hook'), step('The operator uses the pendant control.', 'pendant')],
    curve='Beam selection: check flange bending under wheel loads (local) as well as overall beam bending and deflection.',
    params=mh(P('I-beam track; curve radius ≥ maker\'s minimum'), P('Hoist ~ 0.5 – 15', 'kW'), P('Hoist ~ 2 – 8 m/min; trolley ~ 10 – 30 m/min', 'm/min'), P('SWL ~ 0.25 – 10', 't')),
    install=_LIFT_INST,
    maint=_maint([M('Pre-use check of hoist, chain, hook latch and limit switches.', 'hst_hook', 'daily')], [M('Measure chain wear and lubricate; check track wear and hangers.', 'track', 'monthly')],
                 [M('Thorough examination; overhaul hoist.', 'hst_trolley', 'per regulation')], ['Load chain: lubricate; gearbox: oil/grease to schedule.']),
    failures=_cf('hst_trolley', 'hst_rope') + [F('Flange wear', ['Wheel marks, thinning flange'], ['Wheel misalignment, overload'], ['Measure flange thickness; replace beam section'], 'track')],
    quiz=[Q('Where do monorail trolley wheels run?', ['On the lower flange of the I-beam', 'On the floor', 'On top of the beam', 'In the web'], 0, 'Underhung trolley.'),
          Q('A monorail moves loads along…', ['A fixed path', 'Any point in a rectangle', 'A circle only', 'Vertical only'], 0, 'Single track.'),
          Q('What must be checked on the beam besides overall bending?', ['Local flange bending under wheel loads', 'Paint', 'Colour', 'Nothing'], 0, 'Flange bending.'),
          Q('Why must open track ends have end stops?', ['To stop the trolley running off the beam', 'To hold the pendant', 'To lubricate the wheels', 'To set the hoist speed'], 0, 'Prevents the trolley and load falling.')],
    selection=['Choose beam size from load, span between hangers and flange bending; hoist from SWL, lift and duty.'],
    safety=['End stops on open track ends; check switches interlock; never side-pull.'],
    refs=['ASME B30.11 — Monorails and underhung cranes', 'ASME B30.16 — Overhead underhung and stationary hoists'])

MODULES['electric_winch'] = mod(
    definition=('An electric winch pulls or lifts loads by winding a wire rope onto a drum. A motor drives the drum through a reduction gearbox, and a spring-applied brake holds the load when power is off. '
                'Winches haul wagons, pull equipment into place, tension cables or act as the hoist on cranes and lifts.'),
    applications=['Haulage of rail wagons and skips', 'Mooring and marine handling', 'Construction and erection pulling', 'Hoist drives'],
    key_points=['Rope line pull drops as the rope layers build up (larger effective drum radius)', 'Spring-applied, power-released brake', 'Keep minimum dead turns on the drum', 'Fleet angle controls spooling'],
    principle=[step('The motor drives the gearbox.', 'motor_brake'), step('The gearbox turns the drum at low speed with high torque.', 'gearbox'),
               step('The rope winds onto the grooved drum.', 'drum'), step('The rope pulls the load.', 'load', overlay='flow')],
    curve='Line pull F = drum torque / effective radius; line speed = ω × radius — both change from first to outer rope layer.',
    params=mh(P('Drum ~ 0.2 – 2 m diameter'), P('~ 2 – 500', 'kW'), P('Line speed ~ 5 – 60', 'm/min'), P('Line pull ~ 5 – 500+', 'kN')),
    install=_LIFT_INST | dict(alignment=['Align the first sheave with the drum centre so the fleet angle stays within the maker\'s limit (typically about 0.5–1.5° plain drum, up to ~2° grooved — check maker).']),
    maint=_maint([M('Check brake, rope spooling and dead turns.', 'drum', 'daily')], [M('Inspect rope; check gearbox oil.', 'rope', 'monthly')],
                 [M('Overhaul gearbox and brake; replace rope.', 'gearbox')], ['Gearbox oil; drum bearings greased; rope dressing.']),
    failures=_cf('motor_brake', 'rope') + [F('Poor spooling', ['Rope crossing, crushing on drum'], ['Fleet angle too large, slack rope'], ['Re-align sheave; spooling gear'], 'drum')],
    quiz=[Q('Why does line pull fall as rope builds up on the drum?', ['The effective radius increases', 'The motor weakens', 'The rope gets lighter', 'It does not'], 0, 'F = T / r.'),
          Q('What holds the load if power fails?', ['Spring-applied brake', 'The rope', 'Gravity', 'Nothing'], 0, 'Fail-safe brake.'),
          Q('Why keep dead turns on the drum?', ['To reduce load on the rope anchor', 'For decoration', 'To speed up', 'To cool the rope'], 0, 'Friction carries most of the load.')],
    selection=['Size for line pull at the outermost working layer, speed and duty; rope per D/d ratio and safety factor.'],
    safety=['Stand clear of the rope line (snap-back zone); never step over a tensioned rope.'],
    refs=['ISO 4309 — Wire rope discard criteria', 'EN 14492-1 — Power-driven winches and hoists (to be verified)'])

# ===================================================================== hydraulics
MODULES['hydraulic_power_unit'] = mod(
    definition=('A hydraulic power unit (HPU) supplies pressurised oil to hydraulic actuators. An electric motor drives a pump (gear, vane or piston) through a bell housing and coupling. The pump draws oil '
                'from the reservoir and delivers it through a manifold with a pressure relief valve and check valve. Return oil passes through a filter and cooler back to the tank.'),
    applications=['Presses, injection moulding and machine tools', 'Mobile and marine hydraulics (deck machinery)', 'Steel mills and test rigs', 'Valve actuators and lifts'],
    key_points=['Pump makes flow; the load makes pressure', 'Relief valve limits maximum pressure', 'Cleanliness (ISO 4406) is the key to reliability', 'Reservoir typically sized ~ 3–5 × pump flow per minute (industrial rule of thumb)'],
    principle=[step('The motor drives the pump through the coupling.', 'coupling'), step('The pump draws oil from the reservoir through the suction strainer.', 'motor_pump', overlay='pressure'),
               step('Oil goes to the valve block; the relief valve limits the pressure.', 'valve_block', overlay='pressure'),
               step('Return oil passes the return filter and cooler back to the tank.', 'filter_breather'), step('The cooler fan removes heat from the oil.', 'cooler_fan')],
    curve='Hydraulic power P = p · Q / 600 (kW, with p in bar and Q in L/min); input power = P / η_overall.',
    params=mh(P('Reservoir ~ 20 – 2000 L'), P('~ 1 – 500', 'kW'), P('Motor ~ 1500 rpm (50 Hz 4-pole)', 'rpm'), P('Flow ~ 5 – 1000 L/min at ~ 50 – 350 bar', 'L/min')),
    install=_HYD_INST,
    maint=_maint([M('Check oil level, temperature and filter indicators.', 'reservoir', 'daily')], [M('Oil sample (ISO 4406 particle count, water, acidity).', 'oil', 'quarterly')],
                 [M('Replace filters, breather and seals; check pump wear (case drain flow for piston pumps).', 'motor_pump')], ['Motor bearings greased; hydraulic oil changed by condition.']),
    failures=[F('Overheating', ['Oil > ~ 60 °C'], ['Cooler fouled, relief valve blowing, internal leakage'], ['Clean cooler; check relief setting and pump wear'], 'cooler'),
              F('Pump cavitation', ['Noise, erosion, low output'], ['Blocked strainer, low oil level, cold oil'], ['Clean strainer; correct level; warm up oil'], 'motor_pump'),
              F('Contamination', ['Valve sticking, wear'], ['Poor filtration, dirty breather'], ['Improve filtration; flush; replace breather'], 'filter_breather')],
    quiz=[Q('What determines system pressure in a hydraulic circuit?', ['The pump', 'The load resistance (limited by the relief valve)', 'The tank size', 'The oil colour'], 1, 'Pump makes flow; load makes pressure.'),
          Q('Hydraulic power at 200 bar and 60 L/min is…', ['2 kW', '20 kW', '200 kW', '0.2 kW'], 1, '200 × 60 / 600 = 20 kW.'),
          Q('Most hydraulic failures are caused by…', ['Contaminated oil', 'Paint colour', 'Too much cooling', 'Low electricity price'], 0, 'Cleanliness.')],
    selection=['Size pump flow from actuator speeds; pressure from the highest force; add margin; select filtration for the most sensitive component.'],
    safety=['Release stored pressure (accumulators!) before opening any line; never search for leaks by hand — injection injury risk.'],
    refs=['ISO 4413 — Hydraulic fluid power: general rules and safety requirements', 'ISO 4406 — Hydraulic fluid cleanliness code'])

MODULES['hydraulic_cylinder'] = mod(
    definition=('A hydraulic cylinder converts fluid pressure into straight-line force and motion. In a double-acting cylinder, oil fed to the cap end pushes the piston and extends the rod; oil fed to the '
                'rod end retracts it. Seals on the piston separate the two chambers; rod seals and a wiper in the gland keep oil in and dirt out.'),
    applications=['Excavators, loaders and cranes', 'Presses and injection moulding machines', 'Gate, valve and damper actuation', 'Steel and paper mills'],
    key_points=['F_extend = p × π D²/4', 'F_retract = p × π (D² − d²)/4 (smaller)', 'Speed v = Q / A', 'Check rod buckling for long strokes'],
    principle=[step('Oil enters the cap-end port A.', 'ports', overlay='pressure'), step('Pressure on the full piston area pushes the piston and rod out.', 'piston_rod', overlay='pressure'),
               step('Oil in the rod-end annulus returns through port B.', 'oil_rod_side'), step('Reversing the ports retracts the rod.', 'oil_cap_side')],
    curve='Force ∝ pressure × area; speed ∝ flow / area — retract is faster than extend for the same flow because the annulus area is smaller.',
    params=mh(P('Bore ~ 25 – 500 mm; stroke up to several m'), P('Set by the HPU (p × Q)', 'kW'), P('Rod speed ~ 0.05 – 0.5 typical', 'm/s'), P('Force ~ 1 – 10 000+', 'kN')),
    install=_HYD_INST,
    maint=_maint([M('Check rod for scoring and leaks at the gland.', 'end_caps', 'daily')], [M('Check mounting pins and bushes.', 'barrel', 'monthly')],
                 [M('Re-seal; re-chrome or replace rod; hone barrel.', 'piston_rod')], ['Grease clevis pins and spherical bearings.']),
    failures=[F('Rod seal leak', ['Oil on rod'], ['Scored rod, worn seal, contamination'], ['Replace seals; repair rod; improve wiper'], 'end_caps'),
              F('Internal leakage (piston seal)', ['Drift under load, slow'], ['Worn piston seal, scored barrel'], ['Re-seal; hone barrel'], 'piston_rod'),
              F('Rod buckling/bending', ['Bent rod, seal damage'], ['Side load, long stroke under compression'], ['Check Euler buckling; add guides'], 'piston_rod')],
    quiz=[Q('Why is the retract force smaller than extend force?', ['The rod reduces the effective area on the rod side', 'Oil is thinner', 'Gravity', 'Seals'], 0, 'Annulus area.'),
          Q('Extension speed equals…', ['Flow / bore area', 'Pressure × area', 'Force / flow', 'Stroke × pressure'], 0, 'v = Q/A.'),
          Q('Force from a 100 mm bore at 100 bar is about…', ['~ 7.9 kN', '~ 79 kN', '~ 790 kN', '~ 0.79 kN'], 1, '10 MPa × 0.00785 m² ≈ 78.5 kN.')],
    selection=['Size bore for the force at the available pressure with margin; check rod buckling; choose mounting and cushioning.'],
    safety=['Support loads mechanically before working on cylinders; release pressure; beware of trapped pressure (pressure intensification in the rod end if the port is blocked).'],
    refs=['ISO 6020/ISO 6022 — Hydraulic cylinder mounting dimensions', 'ISO 4413'])

MODULES['hydraulic_accumulator'] = mod(
    definition=('A hydraulic accumulator stores energy as compressed gas. In a bladder accumulator, a rubber bladder inside a steel shell is pre-charged with nitrogen. When system pressure rises above '
                'the pre-charge, oil flows in and compresses the gas; when pressure falls, the gas pushes the oil back out. A poppet valve at the oil port stops the bladder being extruded.'),
    applications=['Emergency/backup energy (e.g. closing valves, braking)', 'Supplementing pump flow for short peaks', 'Absorbing pressure shocks and pulsations', 'Compensating for thermal expansion and leakage'],
    key_points=['Pre-charge with NITROGEN only — never oxygen or air', 'Bladder type: pre-charge ≈ 0.9 × minimum system pressure (rule of thumb)', 'Gas law sets usable volume (p·Vⁿ = constant)', 'Pressure vessel — design/inspection codes apply'],
    principle=[step('The bladder is pre-charged with nitrogen through the gas valve.', 'gas_valve', overlay='pressure'), step('System pressure rises; oil enters through the poppet port.', 'oil_port'),
               step('Oil compresses the bladder and gas.', 'bladder', overlay='pressure'), step('When the system needs flow, gas pressure pushes the oil back out.', 'oil', overlay='flow')],
    curve='Usable volume ΔV = V₀·(p₀/p₁)^(1/n) − V₀·(p₀/p₂)^(1/n) (n = 1 isothermal, ≈ 1.4 adiabatic).',
    params=mh(P('~ 0.2 – 200 L nominal'), P('n/a — stores energy (E ≈ ∫p dV)', 'kJ'), P('Discharge in ms (shock) to s (emergency)', 's'), P('Max pressure ~ 200 – 690', 'bar')),
    install=_HYD_INST | dict(foundation=['Mount vertically (gas valve up for bladder type) with clamps that do not restrict the shell; allow access to the gas valve.'],
                             piping=['Fit a safety block with isolation, bleed-down valve and relief valve.']),
    maint=_maint([M('Check system pressure behaviour (pump cycling).', 'shell', 'weekly')], [M('Check pre-charge with a charging kit (oil side drained).', 'gas_valve', '3–6 months')],
                 [M('Replace bladder; periodic pressure-vessel inspection per regulations.', 'bladder')], ['No lubrication — keep the gas valve cap fitted.']),
    failures=[F('Loss of pre-charge', ['Pump cycles more often, poor damping'], ['Gas valve leak, bladder permeation'], ['Recharge with nitrogen; replace valve core'], 'gas_valve'),
              F('Bladder rupture', ['Gas in oil, no accumulator effect'], ['Over-compression (pre-charge too low), age'], ['Replace bladder; correct pre-charge'], 'bladder')],
    quiz=[Q('Which gas is used for pre-charging?', ['Nitrogen', 'Oxygen', 'Air', 'Hydrogen'], 0, 'Inert — oxygen/air risk diesel-effect explosion.'),
          Q('Typical bladder pre-charge is about…', ['90 % of minimum system pressure', '200 % of max pressure', 'Atmospheric', 'Equal to maximum pressure'], 0, 'Rule of thumb ≈ 0.9 × p_min.'),
          Q('What does the poppet valve at the oil port do?', ['Stops the bladder extruding into the port', 'Charges the gas', 'Measures pressure', 'Cools the oil'], 0, 'Anti-extrusion.')],
    selection=['Size from required ΔV between p_min and p_max using the gas law; choose bladder/piston/diaphragm type for flow rate and compression ratio.'],
    safety=['Always discharge the oil side before any work; an accumulator keeps the system pressurised after the pump stops.', 'Charge with nitrogen only using a regulator.'],
    refs=['ISO 4413', 'Pressure equipment regulations (e.g. PED 2014/68/EU)'])

MODULES['hydraulic_control_valve_assembly'] = mod(
    definition=('A hydraulic control valve assembly mounts several valves on a manifold block. Drilled galleries carry the pump pressure (P) and the tank return (T) to each valve station. Directional '
                'valves route oil to the actuator work ports (A and B); a relief valve limits pressure; flow-control valves set actuator speed. Mounting valves on a manifold saves piping and leak points.'),
    applications=['Industrial machine hydraulics', 'Mobile machinery control', 'Test rigs and presses', 'Process valve actuation'],
    key_points=['P = pressure, T = tank, A/B = work ports', 'Standard interface patterns (ISO 4401, "CETOP")', 'Spool position decides the flow path', 'Fewer pipes = fewer leaks'],
    principle=[step('Pump oil enters the P gallery.', 'manifold', overlay='pressure'), step('The solenoid shifts the directional spool.', 'spool_1'),
               step('P is connected to a work port and the other port returns to T.', 'work_ports', overlay='flow'),
               step('The relief valve limits pressure; the flow control sets speed.', 'relief_valve')],
    curve='Pressure drop across each valve rises with flow squared (Δp ∝ Q²); valves are sized for an acceptable Δp at rated flow.',
    params=mh(P('Interface sizes NG6 – NG32 (ISO 4401)'), P('Set by the HPU', 'kW'), P('Spool shift ~ 20 – 80 ms (solenoid)', 'ms'), P('~ 10 – 1000+ L/min, up to ~ 350 bar', 'L/min')),
    install=_HYD_INST,
    maint=_maint([M('Check for external leaks and solenoid temperatures.', 'directional_valve_1', 'daily')], [M('Check relief setting with a test gauge.', 'relief_valve', 'quarterly')],
                 [M('Replace seals and solenoid coils; clean spools.', 'spool_1')], ['No lubrication — oil cleanliness is key.']),
    failures=[F('Spool sticking', ['Actuator does not move or moves slowly'], ['Contamination (silting), varnish'], ['Clean; improve filtration'], 'spool_1'),
              F('Relief valve chattering', ['Noise, pressure oscillation'], ['Wrong setting, worn seat'], ['Reset/repair'], 'relief_valve')],
    quiz=[Q('What does port "T" stand for?', ['Tank (return)', 'Temperature', 'Torque', 'Test'], 0, 'Return to tank.'),
          Q('What sets actuator speed?', ['Flow control valve (flow rate)', 'Relief valve only', 'Gauge', 'Manifold colour'], 0, 'Speed ∝ flow.'),
          Q('Why use a manifold?', ['Fewer pipes and leak points; compact', 'More noise', 'Higher cost always', 'No reason'], 0, 'Compactness and reliability.')],
    selection=['Size valves for flow at acceptable Δp; choose spool centre (closed, tandem, open) for the circuit; specify voltage and connectors.'],
    safety=['Lock out and depressurise before removing valves; manual overrides can move actuators unexpectedly.'],
    refs=['ISO 4401 — Mounting surfaces for 4-port directional valves', 'ISO 1219-1 — Graphic symbols', 'ISO 4413'])
