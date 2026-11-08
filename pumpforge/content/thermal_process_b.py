"""Learning content — Thermal & Process Equipment, part B (EQ-235 … EQ-246): evaporators, dryers, combustion."""
from pumpforge.learning import mod, step, P, F, Q, M
from content.thermal_process_a import tp, _maint, _HX_INST, _FIRED_INST, _NOLUBE

MODULES = {}

_EV_INST = dict(
    foundation=['Support vessels on structure/legs designed for operating and flooded weights; allow thermal growth of calandrias and vapour lines.'],
    alignment=['Vertical calandrias plumb (falling-film distribution depends on it); slope liquor lines for drainage.'],
    piping=['Vapour lines sized for low ΔP; condensate drained by traps or level control; vents for non-condensables on each steam chest.',
            'Vacuum system (condenser + vacuum pump/ejector) for the last effect.'],
    commissioning=['Leak/vacuum test; water trials (wetting, levels); bring steam on slowly; set levels and densities; CIP routine.'])
_DRY_INST = dict(
    foundation=['Structure designed for equipment, product and dynamic loads; explosion venting directed to a safe area.'],
    alignment=['Align fans, rotary valves and drives; level chambers and beds.'],
    piping=['Air/gas ducts with dampers and expansion joints; dust collection (cyclone, bag filter); explosion isolation where required (ATEX/NFPA).'],
    commissioning=['Air balance; heat-up curve; water trials then product; check outlet temperature/moisture control and interlocks.'])
_COMB_INST = dict(
    foundation=['Foundations for weight, thermal growth and dynamic loads; refractory dry-out after installation.'],
    alignment=['Burner and fan alignment; kiln/rotor alignment for rotating equipment.'],
    piping=['Fuel train per burner management standards; air ducts; flue gas path to air-pollution control; emissions monitoring (CEMS).'],
    commissioning=['Refractory dry-out; purge and light-off; tune combustion; verify residence-time temperature and emissions.'])

# ===================================================================== evaporators
MODULES['flash_evaporator'] = mod(
    definition=('A flash evaporator separates vapour from a liquid by a sudden drop in pressure. The liquid is first heated under pressure so it cannot boil; it then passes a pressure-reducing valve into a '
                'vessel at lower pressure, where part of it flashes into vapour. The vapour leaves through a demister at the top and the concentrated liquid from the bottom.'),
    applications=['Multi-stage flash (MSF) desalination stages', 'Condensate and blowdown flash recovery', 'Concentration of solutions without heating surfaces in the vessel'],
    key_points=['No heating surface in the flash vessel — less fouling', 'Flash fraction ≈ cp·(T_in − T_sat)/h_fg', 'Demister prevents carry-over', 'Vessel pressure sets the flashing temperature'],
    principle=[step('The feed heater heats the liquid under pressure.', 'feed_heater', overlay='flow'), step('The flash valve reduces the pressure.', 'flash_valve', overlay='pressure'),
               step('In the vessel part of the liquid flashes to vapour.', 'flash_vessel'), step('The demister removes droplets from the vapour.', 'demister'),
               step('Concentrated liquid leaves from the bottom.', 'concentrate', overlay='flow')],
    curve='Fraction flashed rises with the difference between inlet temperature and vessel saturation temperature.',
    params=tp(P('Vessel ~ 0.5 – 4 m diameter'), P('Feed heater ~ 0.1 – 50', 'MW'), P('Feed ~ 100 – 180; vessel ~ 40 – 120', '°C'), P('Feed ~ 1 – 1000', 't/h')),
    install=_EV_INST,
    maint=_maint([M('Monitor vessel pressure, level and vapour quality.', 'flash_vessel', 'daily')], [M('Check demister ΔP; inspect flash valve trim.', 'demister', 'quarterly')],
                 [M('Inspect vessel for erosion at the inlet.', 'nozzles')], _NOLUBE),
    failures=[F('Carry-over of liquid', ['Contaminated vapour/condensate'], ['Demister damaged, high level, foaming'], ['Repair demister; control level'], 'demister'),
              F('Valve erosion', ['Poor control'], ['Two-phase flashing flow'], ['Hardened trim; angle valve'], 'flash_valve')],
    quiz=[Q('What causes flashing?', ['Sudden pressure reduction below the liquid\'s saturation pressure', 'Adding heat in the vessel', 'Cooling', 'Mixing air'], 0, 'Pressure drop.'),
          Q('Why heat the feed under pressure?', ['So it does not boil before the flash valve', 'To cool it', 'To add air', 'No reason'], 0, 'Suppress boiling.'),
          Q('What does the demister do?', ['Removes droplets from the vapour', 'Heats the liquid', 'Measures level', 'Pumps liquid'], 0, 'Entrainment control.')],
    selection=['Choose vessel size for vapour velocity (Souders–Brown) and residence time; multiple stages for high recovery.'],
    safety=['Relief valve on vessel; flashing hot liquid and steam burn hazard.'],
    refs=['Perry\'s Chemical Engineers\' Handbook — Evaporation'])

MODULES['falling_film_evaporator'] = mod(
    definition=('In a falling film evaporator, liquid is spread at the top of long vertical tubes and flows down the inside walls as a thin film, while steam condenses on the outside. The liquid evaporates from '
                'the film surface; vapour and concentrate leave at the bottom and are split in a separator. Residence time is short and the temperature difference small.'),
    applications=['Dairy (milk concentration), juices, sugar', 'Pharmaceuticals and heat-sensitive chemicals', 'Mechanical vapour recompression (MVR) systems'],
    key_points=['Thin film → high heat transfer at low ΔT', 'Short residence time — gentle on products', 'Distribution must wet every tube', 'Recirculation keeps the minimum wetting rate'],
    principle=[step('Feed enters the top head and the distributor wets every tube.', 'distributor', overlay='flow'), step('A thin liquid film falls down inside the tubes.', 'calandria_tubes'),
               step('Steam condenses on the outside of the tubes.', 'calandria', overlay='temperature'), step('Vapour and concentrate separate in the separator.', 'separator', overlay='flow'),
               step('The recirculation pump returns liquid to the top.', 'recirc_pump')],
    curve='Heat-transfer coefficient vs film Reynolds number; dry patches form below the minimum wetting rate.',
    params=tp(P('Tubes ~ 25 – 50 mm, 6 – 12 m long'), P('~ 0.5 – 50', 'MW'), P('Boiling ~ 40 – 100 (often under vacuum)', '°C'), P('Evaporation ~ 1 – 100', 't/h')),
    install=_EV_INST,
    maint=_maint([M('Monitor ΔT, wetting rate and product concentration.', 'calandria', 'daily')], [M('CIP cleaning of tubes and distributor.', 'distributor', 'daily/weekly')],
                 [M('Inspect tubes; check distributor holes.', 'calandria_tubes')], ['Pump bearings and seals per maker.']),
    failures=[F('Dry patches/fouling', ['Burnt deposits, falling capacity'], ['Poor distribution, low wetting rate'], ['Clean distributor; increase recirculation'], 'distributor'),
              F('Entrainment losses', ['Product in condensate'], ['Separator overloaded'], ['Reduce rate; improve separator'], 'separator')],
    quiz=[Q('Why are falling film evaporators good for heat-sensitive products?', ['Short residence time and small ΔT', 'They use flames', 'Long hold-up', 'High pressure'], 0, 'Gentle evaporation.'),
          Q('What is critical at the top of the tubes?', ['Even liquid distribution', 'Paint', 'Noise', 'Air'], 0, 'Wetting.'),
          Q('Where does steam condense?', ['Outside the tubes in the calandria', 'Inside the tubes', 'In the separator', 'In the pump'], 0, 'Shell side.')],
    selection=['Size tube length/number for wetting rate and heat flux; use with vapour recompression for energy savings.'],
    safety=['Hot surfaces and steam; vacuum vessels must be rated for full vacuum.'],
    refs=['Perry\'s Handbook — Evaporators', 'GEA/Alfa Laval evaporator guides'])

MODULES['forced_circulation_evaporator'] = mod(
    definition=('A forced circulation evaporator pumps the liquid at high velocity through a heat exchanger and back to a separator. Because of the static head above the exchanger the liquid is only heated, '
                'not boiled, in the tubes; it flashes when it reaches the lower-pressure separator. This prevents scale and crystal deposits on the heating surface.'),
    applications=['Crystallisation (salts, sodium sulphate)', 'Scaling and viscous liquids', 'Wastewater zero-liquid-discharge concentrators'],
    key_points=['Suppressed boiling in the heater', 'High tube velocity (≈ 1.5–3 m/s)', 'Large circulation pump (high flow, low head)', 'Handles solids and high viscosity'],
    principle=[step('The circulation pump drives liquid through the heater tubes.', 'circulation_pump', overlay='flow'), step('Steam heats the liquid a few degrees in the heater.', 'heater', overlay='temperature'),
               step('Static head keeps the liquid from boiling in the tubes.', 'heater_tubes'), step('In the separator the liquid flashes and vapour leaves.', 'separator', overlay='flow'),
               step('Liquid returns down the loop to the pump.', 'circulation_loop')],
    curve='Temperature rise per pass ~ 2–5 °C; circulation rate ≫ evaporation rate.',
    params=tp(P('Heater ~ 0.5 – 2 m; separator ~ 1 – 6 m diameter'), P('~ 0.5 – 50', 'MW'), P('~ 50 – 120', '°C'), P('Evaporation ~ 1 – 100', 't/h')),
    install=_EV_INST,
    maint=_maint([M('Monitor pump amps, ΔT and slurry density.', 'circulation_pump', 'daily')], [M('Check tube velocity and scaling; flush.', 'heater_tubes', 'weekly')],
                 [M('Inspect pump impeller and tubes for erosion.', 'pump_impeller')], ['Pump bearings and gearbox oil per maker.']),
    failures=[F('Erosion by crystals', ['Thinning tubes, impeller wear'], ['High velocity slurry'], ['Wear-resistant materials'], 'pump_impeller'),
              F('Boiling in tubes (scaling)', ['Rapid fouling'], ['Low static head or high ΔT'], ['Raise head/back-pressure; reduce ΔT'], 'heater_tubes')],
    quiz=[Q('Why does the liquid not boil in the heater tubes?', ['Static head raises its pressure', 'It is too cold', 'There is no steam', 'Pump cools it'], 0, 'Suppressed boiling.'),
          Q('Where does evaporation happen?', ['In the separator (flashing)', 'In the pump', 'In the tubes', 'In the condenser'], 0, 'Flash.'),
          Q('Why high velocity?', ['Reduce fouling and keep solids suspended', 'Reduce power', 'Make noise', 'No reason'], 0, 'Scour.')],
    selection=['Choose for scaling, crystallising or viscous duties; size pump for circulation ratio and velocity.'],
    safety=['Hot, pressurised slurry; lock out pump before opening loop.'],
    refs=['Perry\'s Handbook — Crystallisation/evaporation'])

MODULES['multiple_effect_evaporator'] = mod(
    definition=('A multiple effect evaporator uses the vapour produced in one effect as the heating steam for the next, which works at a lower pressure so its liquid boils at a lower temperature. Only the '
                'first effect takes live steam, so each kilogram of steam evaporates several kilograms of water.'),
    applications=['Sugar, pulp & paper (black liquor), dairy', 'Caustic soda and chemical concentration', 'Desalination (MED)'],
    key_points=['Steam economy ≈ N × (0.8–1) for N effects', 'Pressure and boiling point fall from effect to effect', 'Total ΔT is shared between effects → more area', 'Forward, backward or mixed feed arrangements'],
    principle=[step('Live steam heats effect 1.', 'effect_1', overlay='pressure'), step('Vapour from effect 1 heats effect 2 at lower pressure.', 'vapour_lines', overlay='flow'),
               step('Effect 3 works under vacuum, heated by effect 2 vapour.', 'effect_3'), step('Liquor flows forward from effect to effect.', 'liquor_lines', overlay='flow'),
               step('The last vapour is condensed in the condenser.', 'condenser')],
    curve='Steam economy vs number of effects (diminishing returns as area and capital rise).',
    params=tp(P('Effects ~ 2 – 7'), P('~ 1 – 100', 'MW'), P('Effect 1 ~ 100 – 130; last ~ 50 – 60', '°C'), P('Evaporation ~ 5 – 500', 't/h')),
    install=_EV_INST,
    maint=_maint([M('Monitor pressures, levels and densities of each effect.', 'body_1', 'continuous')], [M('Clean effects in rotation; check vacuum system.', 'condenser', 'weekly')],
                 [M('Inspect tubes and vapour lines.', 'effect_2_tubes')], _NOLUBE),
    failures=[F('Loss of vacuum', ['Falling capacity, rising last-effect temperature'], ['Air leaks, condenser fouling'], ['Leak test; clean condenser'], 'condenser'),
              F('Scaling in later effects', ['Falling ΔT, capacity'], ['Concentration and solubility'], ['Cleaning schedule; antiscalant'], 'effect_3')],
    quiz=[Q('Why does effect 2 run at lower pressure than effect 1?', ['So its liquid boils at a lower temperature than effect 1 vapour', 'For safety', 'Random', 'To save pumps'], 0, 'Temperature driving force.'),
          Q('Steam economy of a 3-effect evaporator is roughly…', ['~2.5–3 kg water per kg steam', '0.1', '10', '100'], 0, 'N × 0.8–1.'),
          Q('Where is the condenser?', ['After the last effect', 'Before effect 1', 'In effect 2', 'None'], 0, 'Last vapour.')],
    selection=['Optimise number of effects vs capital; consider MVR/TVR for further savings.'],
    safety=['Vacuum and pressure ratings; hot liquor; isolate steam before entry.'],
    refs=['McCabe, Smith & Harriott — Unit Operations of Chemical Engineering'])

# ===================================================================== dryers
MODULES['spray_dryer'] = mod(
    definition=('A spray dryer converts a liquid (solution, slurry, emulsion) into a dry powder in one step. A high-speed atomiser wheel or nozzle sprays the liquid into hot air in a large chamber; '
                'the fine droplets dry in seconds. Powder falls into the cone and fines are recovered from the exhaust air by a cyclone and/or bag filter.'),
    applications=['Milk powder, coffee, food ingredients', 'Detergents, ceramics, pigments', 'Pharmaceuticals and enzymes'],
    key_points=['Very short drying time', 'Droplets stay near wet-bulb temperature', 'Atomisation sets particle size', 'Explosion protection for combustible powders'],
    principle=[step('Hot air enters through the roof disperser.', 'air_disperser', overlay='flow'), step('The atomiser wheel flings the feed into a fine spray.', 'atomiser_wheel'),
               step('Droplets dry as they spiral down the chamber.', 'drying_chamber', overlay='temperature'), step('Powder collects in the cone and leaves by rotary valve.', 'rotary_valves'),
               step('The cyclone recovers fines from the exhaust air.', 'cyclone', overlay='flow')],
    curve='Outlet air temperature controls final moisture; higher inlet temperature increases capacity for the same air flow.',
    params=tp(P('Chamber ~ 1 – 12 m diameter'), P('~ 0.05 – 30', 'MW'), P('Inlet ~ 150 – 250; outlet ~ 70 – 100', '°C'), P('Evaporation ~ 5 – 20 000', 'kg/h')),
    install=_DRY_INST,
    maint=_maint([M('Check outlet temperature, powder moisture and wall deposits.', 'drying_chamber', 'per shift')], [M('Inspect atomiser wheel wear and vibration.', 'atomiser_wheel', 'weekly')],
                 [M('Overhaul atomiser; inspect explosion vents.', 'atomiser_drive')], ['Atomiser oil system per maker (high speed).']),
    failures=[F('Wall deposits/burning', ['Brown/burnt powder, fires'], ['Wet spray reaching walls, high inlet temperature'], ['Adjust atomisation, air pattern'], 'drying_chamber'),
              F('Atomiser vibration', ['Trip, noise'], ['Wheel wear/imbalance'], ['Balance/replace wheel'], 'atomiser_wheel')],
    quiz=[Q('Why do heat-sensitive products survive spray drying?', ['Evaporating droplets stay near wet-bulb temperature', 'Air is cold', 'No heat used', 'It is slow'], 0, 'Evaporative cooling.'),
          Q('What sets particle size?', ['Atomisation (wheel speed, nozzle)', 'Cone angle', 'Cyclone', 'Stack'], 0, 'Droplet size.'),
          Q('What does the cyclone do?', ['Recovers fines from exhaust air', 'Heats air', 'Atomises feed', 'Cools product'], 0, 'Separation.')],
    selection=['Choose atomiser (wheel vs nozzle) for particle size; chamber size for residence time; co-/counter-current for product.'],
    safety=['Dust explosion: venting/suppression, isolation (NFPA 652/654, ATEX); fire detection.'],
    refs=['Masters — Spray Drying Handbook', 'NFPA 652'])

MODULES['fluidized_bed_dryer'] = mod(
    definition=('A fluidised bed dryer blows hot air up through a perforated distributor plate at a velocity just high enough to lift the particles, so the bed behaves like a boiling liquid. Every particle is '
                'surrounded by hot air, giving fast and even drying. In continuous units the bed flows from the feed point over a weir to the outlet.'),
    applications=['Granules, crystals and pellets (salt, sugar, fertiliser, plastics)', 'Pharmaceutical granules', 'Food powders and agglomerates'],
    key_points=['Air velocity above minimum fluidisation velocity', 'Uniform bed temperature', 'Weir height sets residence time', 'Particles must be fluidisable (not too fine/sticky)'],
    principle=[step('Hot air from the heater enters the plenum.', 'air_system', overlay='flow'), step('The distributor spreads the air evenly.', 'distributor'),
               step('Particles fluidise and dry in the bed.', 'body', overlay='temperature'), step('Dried product overflows the weir to the outlet.', 'weir_feed'),
               step('The cyclone captures fines from exhaust air.', 'cyclone')],
    curve='Bed ΔP vs air velocity: rises then levels off at minimum fluidisation; above terminal velocity particles are blown out.',
    params=tp(P('Bed area ~ 0.5 – 50 m²'), P('~ 0.05 – 20', 'MW'), P('Air ~ 60 – 250', '°C'), P('~ 0.1 – 100', 't/h')),
    install=_DRY_INST,
    maint=_maint([M('Check bed ΔP, temperatures and moisture.', 'distributor', 'per shift')], [M('Clean distributor holes; check cyclone.', 'distributor', 'weekly')],
                 [M('Inspect fan and heater.', 'fan')], ['Fan bearings per maker.']),
    failures=[F('Defluidisation/channelling', ['Wet lumps, hot spots'], ['Sticky feed, blocked distributor'], ['Pre-mix/back-mix feed; clean plate'], 'distributor'),
              F('Excess fines carry-over', ['Cyclone overload'], ['Too high air velocity'], ['Reduce air; adjust'], 'cyclone')],
    quiz=[Q('What is minimum fluidisation velocity?', ['Air velocity at which the bed just lifts', 'Fan speed', 'Weir height', 'Feed rate'], 0, 'Onset of fluidisation.'),
          Q('What sets residence time in a continuous FBD?', ['Weir height and feed rate', 'Paint', 'Cyclone', 'Stack'], 0, 'Bed hold-up.'),
          Q('Why is bed temperature uniform?', ['Intense mixing of the fluidised particles', 'Insulation', 'Cold air', 'No heat'], 0, 'Mixing.')],
    selection=['Check particle size distribution and stickiness; size bed area for air velocity and residence time.'],
    safety=['Dust explosion protection; hot surfaces; lock out fan before entering.'],
    refs=['Mujumdar — Handbook of Industrial Drying'])

MODULES['flash_dryer'] = mod(
    definition=('A flash (pneumatic) dryer dries wet granular or powdered material while conveying it in a hot gas stream. The feed is dispersed into hot gas at a venturi and carried up a drying duct at high '
                'velocity; surface moisture evaporates within seconds. A cyclone separates the product, and an exhaust fan pulls the gas through the system.'),
    applications=['Starch, gluten, fibres', 'Mineral concentrates, gypsum, clays', 'Chemicals with mostly surface moisture'],
    key_points=['Contact time only seconds', 'Good for surface moisture', 'Simple, compact, continuous', 'Product must be dispersible'],
    principle=[step('The air heater supplies hot gas.', 'air_heater', overlay='flow'), step('The feeder disperses wet material into the gas at the venturi.', 'feeder'),
               step('Particles dry as they are carried up the drying duct.', 'drying_duct', overlay='temperature'), step('The cyclone separates the product.', 'cyclone'),
               step('The exhaust fan draws gas through the system to the stack.', 'exhaust_fan', overlay='flow')],
    curve='Moisture removed vs gas inlet temperature and duct length; internal moisture needs longer residence (consider ring dryers).',
    params=tp(P('Duct ~ 0.3 – 2 m diameter, 10 – 30 m tall'), P('~ 0.2 – 30', 'MW'), P('Gas inlet ~ 150 – 600; outlet ~ 70 – 120', '°C'), P('~ 0.5 – 50', 't/h')),
    install=_DRY_INST,
    maint=_maint([M('Check outlet temperature and product moisture.', 'cyclone', 'per shift')], [M('Inspect duct bends for erosion; feeder wear.', 'drying_duct', 'monthly')],
                 [M('Fan balancing; cyclone inspection.', 'exhaust_fan')], ['Fan and feeder bearings per maker.']),
    failures=[F('Duct build-up', ['Rising ΔP'], ['Sticky feed, poor dispersion'], ['Back-mix dry product; improve disperser'], 'drying_duct'),
              F('Wet product', ['High moisture'], ['Low gas temperature, overload'], ['Adjust heat input/feed'], 'air_heater')],
    quiz=[Q('Why are flash dryers suited to surface moisture?', ['Contact time is only seconds', 'They are slow', 'They use vacuum', 'They tumble product'], 0, 'Short residence.'),
          Q('What carries the particles?', ['The hot gas stream', 'A belt', 'A screw', 'Gravity only'], 0, 'Pneumatic transport.'),
          Q('What separates product from gas?', ['Cyclone', 'Fan', 'Burner', 'Venturi'], 0, 'Cyclone.')],
    selection=['Use for free-flowing, surface-wet materials; check gas velocity vs particle terminal velocity.'],
    safety=['Explosion protection for combustible dusts; fire detection in duct.'],
    refs=['Mujumdar — Handbook of Industrial Drying'])

MODULES['paddle_dryer'] = mod(
    definition=('A paddle dryer is an indirect (conduction) dryer: two hollow shafts carrying wedge-shaped paddles turn inside a steam-jacketed trough. Steam or thermal oil inside the jacket, shafts and '
                'paddles heats the material, while the paddles mix and convey it towards the outlet weir. Only a small vapour stream leaves.'),
    applications=['Sewage and industrial sludge drying', 'Pastes and filter cakes', 'Chemicals needing closed, solvent-recovery drying'],
    key_points=['Large heated surface per volume (shafts + paddles + jacket)', 'Material never touches the heating medium', 'Small vapour flow — easy treatment/recovery', 'Self-cleaning wedge paddles'],
    principle=[step('Wet feed enters at one end.', 'vapour_dome', overlay='flow'), step('Steam heats the jacketed trough.', 'jacketed_trough', overlay='temperature'),
               step('The hollow paddle shafts, also steam-heated, mix and convey the material.', 'paddle_shaft_1'), step('Rotary joints feed steam into the turning shafts.', 'rotary_joints'),
               step('Dried product leaves over the outlet weir; vapour leaves the dome.', 'outlet')],
    curve='Drying rate falls as material passes the sticky phase and the falling-rate period; residence time set by weir and fill.',
    params=tp(P('Heating area ~ 5 – 400 m²'), P('~ 0.1 – 10', 'MW'), P('Steam ~ 150 – 200', '°C'), P('Evaporation ~ 0.1 – 10', 't/h')),
    install=_DRY_INST,
    maint=_maint([M('Check drive current, steam pressure and condensate removal.', 'drive', 'daily')], [M('Inspect rotary joints and seals.', 'rotary_joints', 'monthly')],
                 [M('Inspect paddles for wear; repair hard-facing.', 'paddle_shaft_2')], ['Gearbox oil; shaft bearings greased per maker.']),
    failures=[F('Overload in sticky phase', ['High torque, trips'], ['Wet feed concentration'], ['Back-mix dry product; control feed'], 'drive'),
              F('Rotary joint leakage', ['Steam leaks'], ['Seal wear'], ['Replace seals'], 'rotary_joints')],
    quiz=[Q('A paddle dryer heats the material by…', ['Conduction from heated surfaces (indirect)', 'Hot air blown through it', 'Microwaves', 'Flames'], 0, 'Indirect.'),
          Q('Why is the vapour stream small?', ['No drying air is used', 'It is cold', 'No water', 'Fans are off'], 0, 'Only evaporated moisture.'),
          Q('How does steam reach the rotating shafts?', ['Through rotary joints', 'Through bearings', 'Through the weir', 'It does not'], 0, 'Rotary joints.')],
    selection=['Size heating area from evaporation and specific evaporation rate; check sticky-phase torque.'],
    safety=['Hot surfaces; rotating paddles — lock out before opening covers.'],
    refs=['Mujumdar — Handbook of Industrial Drying'])

MODULES['vacuum_dryer'] = mod(
    definition=('A rotary double-cone vacuum dryer dries batches of heat-sensitive or solvent-wet powders. The double-cone vessel turns slowly on trunnions, tumbling the product against its heated jacket. '
                'A vacuum pump lowers the pressure so the moisture or solvent boils at a low temperature; vapour passes a filter and is condensed.'),
    applications=['Pharmaceutical APIs and intermediates', 'Fine chemicals and solvent recovery', 'Heat-sensitive foods'],
    key_points=['Low pressure → low boiling point', 'Gentle tumbling, closed system', 'Solvent recovery in condenser', 'Batch operation'],
    principle=[step('Wet product is charged through the manway.', 'double_cone'), step('Hot water/steam/thermal oil heats the jacket.', 'double_cone', overlay='pressure'),
               step('The vessel rotates slowly and the product tumbles.', 'powder'), step('Vapour is drawn through the trunnion to filter and condenser.', 'vacuum_system', overlay='flow'),
               step('The drive turns the vessel on its trunnions.', 'drive')],
    curve='Drying curve: constant-rate period then falling-rate period; vacuum level sets product temperature.',
    params=tp(P('Working volume ~ 0.05 – 10 m³'), P('~ 5 – 200', 'kW'), P('Jacket ~ 50 – 150; product ~ 30 – 60', '°C'), P('Batch ~ 20 – 5000', 'kg')),
    install=_DRY_INST,
    maint=_maint([M('Check vacuum level, jacket temperature, seal condition.', 'vacuum_system', 'per batch')], [M('Clean filter; check condenser.', 'vacuum_system', 'weekly')],
                 [M('Replace trunnion seals and bearings.', 'stands_trunnions')], ['Drive gearbox oil; trunnion bearings greased.']),
    failures=[F('Vacuum leaks', ['Slow drying'], ['Seal wear'], ['Replace seals; leak test'], 'stands_trunnions'),
              F('Lump formation', ['Uneven drying'], ['Product stickiness'], ['Lump breakers; adjust temperature'], 'powder')],
    quiz=[Q('Why dry under vacuum?', ['Liquid boils at lower temperature', 'Faster rotation', 'Cheaper heating', 'Prevent tumbling'], 0, 'Boiling point falls with pressure.'),
          Q('How does vapour leave?', ['Through a line in the trunnion to the filter and condenser', 'Through the manway', 'Through the drive', 'It stays'], 0, 'Trunnion.'),
          Q('Why condense the vapour?', ['To recover solvents and protect the vacuum pump', 'To heat the jacket', 'For noise', 'No reason'], 0, 'Recovery.')],
    selection=['Choose volume and heating area for batch size and cycle time; solvent compatibility of seals.'],
    safety=['Flammable solvents: inerting, ATEX electrical equipment; vessel rated for full vacuum.'],
    refs=['Pharmaceutical engineering guides (ISPE)'])

# ===================================================================== combustion
MODULES['fluidized_bed_combustor'] = mod(
    definition=('A bubbling fluidised bed combustor burns fuel inside a hot bed of sand fluidised by air blown up through a distributor. The well-mixed, hot bed burns low-grade or variable fuels '
                'completely at a moderate temperature; in-bed tubes raise steam, and a cyclone returns fines to the bed.'),
    applications=['Biomass and waste-to-energy boilers', 'Low-grade coal and lignite', 'Sludge incineration'],
    key_points=['Bed ~ 800–900 °C: low NOx, in-bed sulphur capture with limestone', 'Fuel-flexible', 'Large thermal inertia', 'Erosion of in-bed surfaces'],
    principle=[step('Fluidising air enters the wind box.', 'air_inlet', overlay='flow'), step('The distributor nozzles spread air across the bed.', 'air_distributor'),
               step('Fuel drops into the bubbling sand bed and burns.', 'fuel_feed', overlay='temperature'), step('In-bed tubes absorb heat.', 'in_bed_tubes'),
               step('The cyclone returns fines; flue gas goes to heat recovery.', 'cyclone_return', overlay='flow')],
    curve='Bed temperature vs fuel/air ratio; agglomeration risk rises above ash softening temperatures.',
    params=tp(P('Bed area ~ 1 – 100 m²'), P('~ 1 – 300', 'MW(th)'), P('Bed ~ 800 – 900', '°C'), P('Fuel ~ 0.5 – 100', 't/h')),
    install=_COMB_INST,
    maint=_maint([M('Monitor bed temperature and ΔP.', 'combustor_shell', 'continuous')], [M('Drain bed ash; check nozzles.', 'ash_drain', 'daily')],
                 [M('Inspect in-bed tubes for erosion; refractory.', 'in_bed_tubes')], ['Fans and feeders per maker.']),
    failures=[F('Bed agglomeration', ['Defluidisation, hot spots'], ['Alkali-rich fuels, high temperature'], ['Bed material change; additives; lower T'], 'combustor_shell'),
              F('Tube erosion', ['Thinning'], ['Bed particle impact'], ['Shields, studs, lower velocity'], 'in_bed_tubes')],
    quiz=[Q('Why do FBCs produce less NOx?', ['Lower combustion temperature (~ 850 °C)', 'No air', 'Special fuel', 'Higher temperature'], 0, 'Low thermal NOx.'),
          Q('How is sulphur captured?', ['Limestone added to the bed', 'Water spray', 'Not possible', 'By the stack'], 0, 'CaO + SO₂.'),
          Q('What keeps the bed fluidised?', ['Air blown up through the distributor', 'Paddles', 'Vibration', 'Gravity'], 0, 'Air.')],
    selection=['BFB for biomass/waste up to medium sizes; CFB for larger, higher-velocity units.'],
    safety=['Bed slumping/hot-restart procedures; dust and hot ash; BMS.'],
    refs=['Basu — Combustion and Gasification in Fluidized Beds', 'NFPA 85'])

MODULES['thermal_oxidizer'] = mod(
    definition=('A thermal oxidizer destroys volatile organic compounds (VOCs), odours and hazardous air pollutants by burning them. Contaminated air is preheated in a recuperator, heated by a burner and held '
                'in a refractory-lined chamber at high temperature for long enough to oxidise the pollutants to CO₂ and water.'),
    applications=['Paint, coating and printing exhausts', 'Chemical and pharmaceutical vents', 'Odour control'],
    key_points=['3 T\'s: temperature, time, turbulence', 'Destruction efficiency typically ≥ 98–99 %', 'Recuperator cuts fuel use', 'LEL monitoring of inlet stream'],
    principle=[step('The fan draws VOC-laden air into the system.', 'fan', overlay='flow'), step('The recuperator preheats it with hot clean gas.', 'recuperator', overlay='temperature'),
               step('The burner raises it to oxidation temperature.', 'burner'), step('The chamber holds the gas for the required residence time.', 'combustion_chamber'),
               step('Clean gas gives up heat and leaves the stack.', 'stack', overlay='flow')],
    curve='Destruction efficiency rises with temperature and residence time.',
    params=tp(P('Chamber ~ 1 – 4 m diameter'), P('Burner ~ 0.1 – 10', 'MW'), P('~ 760 – 870 (higher for halogenated)', '°C'), P('Air ~ 1 000 – 100 000', 'm³/h')),
    install=_COMB_INST,
    maint=_maint([M('Check chamber temperature, LEL and emissions.', 'combustion_chamber', 'continuous')], [M('Inspect burner and flame sensor.', 'burner', 'monthly')],
                 [M('Inspect recuperator for leaks and refractory.', 'recuperator')], ['Fan bearings per maker.']),
    failures=[F('Recuperator leak', ['Lower destruction efficiency'], ['Thermal fatigue'], ['Repair; temperature-ramp limits'], 'recuperator'),
              F('High LEL at inlet', ['Trip'], ['Process upset'], ['Dilution air; interlocks'], 'fan')],
    quiz=[Q('What are the "3 T\'s"?', ['Temperature, time, turbulence', 'Tubes, tanks, towers', 'Torque, thrust, tension', 'None'], 0, 'Combustion fundamentals.'),
          Q('Why a recuperator?', ['Preheat incoming air to save fuel', 'Cool the stack', 'Add VOC', 'No reason'], 0, 'Heat recovery.'),
          Q('Typical oxidation temperature?', ['~ 760–870 °C', '~ 100 °C', '~ 2000 °C', '~ 30 °C'], 0, 'VOC destruction.')],
    selection=['Recuperative vs regenerative (RTO, ~ 95 % heat recovery) vs catalytic, depending on VOC concentration and flow.'],
    safety=['LEL monitoring; flame arrestors on vent inlets; BMS.'],
    refs=['EPA Air Pollution Control Cost Manual', 'NFPA 86'])

MODULES['incinerator'] = mod(
    definition=('A rotary kiln incinerator burns solid, sludge and liquid wastes. The waste, fed at the upper end, tumbles down the slowly rotating, slightly inclined kiln as it dries, burns and becomes ash. '
                'The gases pass to a secondary combustion chamber where an afterburner completes combustion before heat recovery, quenching and gas cleaning.'),
    applications=['Hazardous and clinical waste', 'Industrial and chemical wastes', 'Contaminated soils'],
    key_points=['Kiln rotation tumbles and mixes waste', 'SCC: ≥ 850 °C for ≥ 2 s (EU IED; 1100 °C for > 1 % halogens)', 'Ash discharged and quenched', 'Extensive gas cleaning follows'],
    principle=[step('Waste is fed into the kiln at the feed end.', 'feed_hood', overlay='flow'), step('The rotating kiln tumbles the waste as it burns.', 'rotary_kiln'),
               step('The kiln burner keeps temperature.', 'kiln_flame'), step('Gases are completed in the secondary chamber.', 'secondary_chamber', overlay='temperature'),
               step('Hot gas leaves to heat recovery and pollution control.', 'gas_outlet', overlay='flow')],
    curve='Residence time of solids in the kiln depends on slope, speed, diameter and length.',
    params=tp(P('Kiln ~ 2 – 5 m diameter, 8 – 20 m long'), P('~ 5 – 50', 'MW(th)'), P('Kiln ~ 850 – 1200; SCC ≥ 850 / 1100', '°C'), P('Waste ~ 1 – 20', 't/h')),
    install=_COMB_INST,
    maint=_maint([M('Monitor SCC temperature, CO, O₂ and shell temperatures.', 'secondary_chamber', 'continuous')], [M('Inspect tyres, rollers, seals.', 'supports_drive', 'weekly')],
                 [M('Reline refractory; replace seals.', 'rotary_kiln')], ['Roller bearings and girth gear lubricated per maker.']),
    failures=[F('Refractory failure', ['Shell hot spots'], ['Thermal shock, slag attack'], ['Shell scanner; reline'], 'rotary_kiln'),
              F('Low SCC temperature', ['Emission limit breach risk'], ['Afterburner fault, wet waste'], ['Auxiliary burner; waste feed interlock'], 'secondary_chamber')],
    quiz=[Q('What does the secondary combustion chamber ensure?', ['Complete burn-out of gases at temperature and residence time', 'Ash cooling', 'Waste feeding', 'Kiln rotation'], 0, '850 °C / 2 s.'),
          Q('Why is the kiln inclined and rotating?', ['To move and tumble the waste towards the ash end', 'For looks', 'To cool it', 'To store gas'], 0, 'Transport and mixing.'),
          Q('EU minimum SCC temperature for wastes > 1 % halogenated organics is…', ['1100 °C', '850 °C', '600 °C', '400 °C'], 0, 'IED requirement.')],
    selection=['Rotary kiln for mixed hazardous wastes; grate for MSW; FBC for homogeneous fuels/sludge.'],
    safety=['Waste acceptance controls; emergency vent stack procedures; hot ash; CEMS.'],
    refs=['Directive 2010/75/EU (Industrial Emissions)', 'Niessen — Combustion and Incineration Processes'])
