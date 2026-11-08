"""Learning content — Alumina Refinery (Bayer process) equipment, EQ-271 … EQ-295."""
from pumpforge.learning import mod, step, P, F, Q, M

MODULES = {}


def ar(size, capacity, conditions, power, **extra):
    """Required parameters for the alumina_refinery family: size, capacity, operating_conditions, power_rating."""
    ref = {'manufacturer': None, 'model': None, 'datasheet': None,
           'rated_point': {'capacity': None, 'operating_temperature': None, 'operating_pressure': None, 'solids_or_liquor_composition': None, 'power_kW': None},
           'status': 'empty — fill from the refinery datasheet / mass balance'}
    return dict(size=size, capacity=capacity, operating_conditions=conditions, power_rating=power, reference_model=ref, extra=extra)


def _m(r, p, o, l):
    return dict(routine=r, periodic=p, overhaul=o, lubrication=l)


_TANK = dict(foundation=['Ring-wall or slab foundation designed for full liquid/slurry weight plus agitator dynamic loads; settlement monitoring for large tanks.'],
             alignment=['Tank plumb and level; agitator shaft vertical and concentric; check gearbox mounting.'],
             piping=['Nozzles sized for slurry velocity (avoid settling and erosion); flush connections; scaling-resistant design and descaling access.',
                     'Caustic service: suitable materials, gaskets and spray shields; eyewash/safety showers nearby.'],
             commissioning=['Water trials (agitator run with water, check vibration and power); then caustic/slurry; verify levels, interlocks and spillage containment (bunds).'])
_MACH = dict(foundation=['Massive foundation designed for dynamic loads (maker data); grout base plates.'],
             alignment=['Align drive train (motor–gearbox–pinion) and check gear mesh/backlash; level rollers/trunnions.'],
             piping=['Feed and discharge chutes free of the moving machine; water/liquor supplies with isolation; dust or spray containment.'],
             commissioning=['No-load run (rotation, vibration, temperatures); then load gradually; record power and throughput baselines.'])
_THK = dict(foundation=['Large ring foundation or concrete tank; centre pier carries the rake drive and torque.'],
            alignment=['Level launders so overflow is even all round; centre the drive and shaft.'],
            piping=['Feed to feedwell with flocculant dosing points; underflow pumps with standby and flushing; overflow to downstream.'],
            commissioning=['Fill with water, run rakes and test torque alarms and lift; start feed and flocculant; build mud bed gradually.'])
_PV = dict(foundation=['Supports designed for operating, test and wind/seismic loads; allow thermal expansion.'],
           alignment=['Vertical vessels plumb; let-down valves and lines supported against vibration.'],
           piping=['Relief protection per code; erosion-resistant fittings at let-down points; steam traps/condensate removal; insulation.'],
           commissioning=['Hydro-test; heat up slowly; check relief settings, levels, temperatures and pressures; test interlocks.'])
_SOL = dict(foundation=['Structure designed for equipment and product loads; dust-tight enclosures where needed.'],
            alignment=['Align drives and rollers/belts; level chambers and floors.'],
            piping=['Air, water and dust connections with isolation; chutes free of moving parts.'],
            commissioning=['Run empty; check air/water flows, temperatures and interlocks; then product.'])
_LUBE = ['Gearboxes and bearings: oil/grease to maker schedule; open gears with spray lubrication where fitted.']
_NL = ['Agitator gearbox oil and motor bearings per maker; no lubrication for static parts.']

# ===================================================================== bauxite preparation
MODULES['bauxite_stockpile_reclaimer'] = mod(
    definition=('A bridge-type scraper reclaimer recovers bauxite from a blending stockpile. A harrow rakes across the whole pile face so material slides down to a chain scraper at the foot of the pile, '
                'which drags it to the yard conveyor. Because the pile was stacked in many thin layers, reclaiming the full face gives a well-blended feed to the refinery.'),
    applications=['Bauxite blending yards at alumina refineries', 'Coal, limestone and ore blending beds'],
    key_points=['Full-face reclaiming = blending', 'Harrow loosens, scraper conveys', 'Bridge travels slowly into the pile', 'Blending effect depends on number of stacked layers'],
    principle=[step('The pile is stacked in many thin chevron layers.', 'stockpile'), step('The harrow rakes the face so bauxite slides down.', 'harrow'),
               step('The chain scraper drags it to the side.', 'scraper', overlay='flow'), step('The bridge advances into the pile.', 'bridge'), step('The yard conveyor carries it to grinding.', 'ycbelt', overlay='flow')],
    curve='Blending effect (standard deviation in / out) improves with number of layers.',
    params=ar(P('Bridge span ~ 30 – 60 m'), P('~ 500 – 3000', 't/h'), P('Ambient; bauxite moisture ~ 5 – 15 %', '—'), P('~ 100 – 600 (total)', 'kW')),
    install=_MACH, maint=_m([M('Check harrow tines and scraper chain.', 'harrow', 'daily')], [M('Chain elongation and sprocket wear.', 'scraper_frame', 'monthly')], [M('Replace chain/flights; structural inspection.', 'bridge')], _LUBE),
    failures=[F('Chain breakage', ['Stop, spillage'], ['Wear, sticky bauxite'], ['Replace links; adjust tension'], 'scraper'), F('Poor blending', ['Feed grade swings'], ['Too few layers, end effects'], ['Adjust stacking; reclaim full face'], 'stockpile')],
    quiz=[Q('Why reclaim across the full face?', ['To take a slice of every stacked layer → blending', 'It is faster', 'Less dust', 'No reason'], 0, 'Blending.'),
          Q('What loosens the pile face?', ['The harrow', 'The conveyor', 'Water', 'The rails'], 0, 'Harrow.'), Q('What carries bauxite to the side conveyor?', ['Chain scraper', 'Bucket wheel', 'Pump', 'Air'], 0, 'Scraper.')],
    selection=['Size bridge for pile cross-section; capacity for refinery demand.'], safety=['Exclusion zone at the pile face (slumping); guards on chain.'], refs=['ISO 5049-1'])

MODULES['bauxite_washing_drum'] = mod(
    definition=('A bauxite washing (scrubbing) drum tumbles crushed bauxite with water. Lifters raise the lumps and drop them so they rub against each other and clay is washed off. A trommel screen at the '
                'discharge separates washed bauxite from the clay-rich fines, which carry much of the reactive silica.'),
    applications=['Beneficiation of lateritic/karstic bauxites with clay', 'Removing reactive silica before digestion'],
    key_points=['Attrition scrubbing in water', 'Removes clay and reactive silica', 'Trommel splits washed product and fines', 'Speed ~ 50–75 % of critical'],
    principle=[step('Bauxite and water enter through the feed chute.', 'feed_chute', overlay='flow'), step('The drum turns; lifters raise and drop the lumps.', 'shell'),
               step('Sprays add water to carry clay away.', 'spray_header'), step('The trommel separates washed lumps from fines.', 'trommel'), step('Products leave via chutes.', 'discharge_chutes', overlay='flow')],
    curve='Clay removal vs residence time and water ratio.',
    params=ar(P('Drum ~ 2 – 4 m diameter, 6 – 12 m long'), P('~ 100 – 1000', 't/h'), P('Ambient; water ~ 1 – 3 m³/t', '—'), P('~ 100 – 1000', 'kW')),
    install=_MACH, maint=_m([M('Check liners, sprays and trommel.', 'trommel', 'daily')], [M('Gear mesh and roller alignment.', 'girth_tyres', 'monthly')], [M('Reline drum.', 'shell')], _LUBE),
    failures=[F('Liner wear', ['Holes, noise'], ['Abrasion'], ['Reline'], 'shell'), F('Screen blinding', ['Fines in product'], ['Sticky clay'], ['More water; screen panel change'], 'trommel')],
    quiz=[Q('Why wash bauxite?', ['Remove clay and reactive silica', 'Add moisture', 'Cool it', 'Dissolve alumina'], 0, 'Lower silica.'),
          Q('What does the trommel do?', ['Screens washed product from fines', 'Grinds', 'Heats', 'Pumps'], 0, 'Screening.'), Q('Scrubbing works by…', ['Attrition between lumps', 'Magnetism', 'Flotation', 'Heat'], 0, 'Attrition.')],
    selection=['Size by throughput and residence time from washability tests.'], safety=['Guard tyres and gears; lock out before entry.'], refs=['Wills\' Mineral Processing Technology'])

MODULES['bauxite_grinding_mill'] = mod(
    definition=('A ball mill grinds bauxite wet in spent caustic liquor. The rotating shell lifts steel balls that cascade onto the charge, crushing and abrading the bauxite into a fine slurry. Grinding exposes the '
                'alumina minerals so they dissolve quickly in digestion.'),
    applications=['Bauxite grinding in Bayer refineries', 'Wet grinding of ores'],
    key_points=['Speed ~ 65–78 % of critical', 'Ball charge ~ 30–40 % of volume', 'Grinding in spent liquor starts dissolution', 'Product size controlled by screens/cyclones'],
    principle=[step('Bauxite and liquor enter through the feed trunnion.', 'feed_discharge', overlay='flow'), step('The shell rotates, driven through the girth gear.', 'girth_tyres'),
               step('Balls cascade and break the bauxite.', 'charge', overlay='pressure'), step('Slurry overflows through the discharge trunnion.', 'heads_trunnions', overlay='flow'), step('Bearings carry the mill.', 'bearings_drive')],
    curve='Specific energy vs product size (Bond law).',
    params=ar(P('Mill ~ 3 – 5 m diameter'), P('~ 100 – 500', 't/h'), P('Liquor temperature ~ 60 – 100 °C', '°C'), P('~ 1 – 5', 'MW')),
    install=_MACH, maint=_m([M('Monitor power, bearing temperatures, noise.', 'bearings_drive', 'continuous')], [M('Ball top-up; liner inspection.', 'charge', 'weekly')], [M('Reline; gear inspection.', 'shell')], _LUBE),
    failures=[F('Overload/overfilling', ['Power drop, noise change'], ['Too much feed'], ['Reduce feed'], 'charge'), F('Liner/bolt failure', ['Leaks, noise'], ['Wear, impact'], ['Replace liners'], 'shell')],
    quiz=[Q('Typical mill speed?', ['~ 65–78 % of critical', '100 %', '10 %', '200 %'], 0, 'Cascading.'),
          Q('Why grind in spent liquor?', ['Starts dissolution and makes slurry', 'Cools the mill', 'Lubricates balls', 'No reason'], 0, 'Process slurry.'), Q('What drives the shell?', ['Pinion and girth gear', 'Belt on balls', 'Hydraulics', 'Air'], 0, 'Gear drive.')],
    selection=['Size by Bond work index and required product size.'], safety=['Lock out and inch-drive procedures; never enter a rotating mill.'], refs=['Wills\' Mineral Processing Technology'])

MODULES['bauxite_slurry_mixing_tank'] = mod(
    definition=('A bauxite slurry mixing tank receives ground bauxite slurry and spent liquor and keeps the solids suspended with an agitator. It buffers flow between grinding and digestion and is where slurry density is adjusted.'),
    applications=['Slurry storage and density control before desilication/digestion', 'Buffering between grinding and digestion', 'Mixing ground bauxite with spent liquor (liquor-to-solids ratio)'],
    key_points=['Agitator keeps solids suspended', 'Hours of residence buffer the plant', 'Density control (solids %)', 'Pre-desilication starts here'],
    principle=[step('Ground slurry and liquor enter.', 'nozzles', overlay='flow'), step('The agitator mixes and suspends solids.', 'mx_agitator', overlay='pressure'),
               step('Level and density are measured.', 'mx_tank'), step('The pump sends slurry onward.', 'slurry_pump', overlay='flow')],
    curve='Just-suspended speed (Zwietering) vs particle size and solids loading.',
    params=ar(P('Tank ~ 8 – 20 m diameter'), P('Residence ~ 4 – 12 h', 'h'), P('~ 70 – 100 °C', '°C'), P('Agitator ~ 30 – 200', 'kW')),
    install=_TANK, maint=_m([M('Check agitator, level, density.', 'mx_agitator', 'daily')], [M('Inspect impeller wear and scale.', 'mx_agitator', 'shutdown')], [M('Gearbox overhaul.', 'mx_drive')], _NL),
    failures=[F('Solids settling', ['Sanding, high torque at restart'], ['Agitator stop, low speed'], ['Restart procedures; air sparge'], 'mx_slurry'), F('Scaling', ['Reduced volume'], ['DSP scale'], ['Descale'], 'mx_tank')],
    quiz=[Q('Main job of the agitator?', ['Keep solids suspended', 'Heat slurry', 'Grind', 'Pump'], 0, 'Suspension.'), Q('Why hours of residence?', ['Buffer and start desilication', 'Cooling', 'Noise', 'None'], 0, 'Buffer.'),
          Q('What is controlled here?', ['Slurry density', 'Voltage', 'Colour', 'Pressure only'], 0, 'Density.')],
    selection=['Size tank for residence; agitator for suspension at design solids.'], safety=['Hot caustic — PPE, splash protection.'], refs=['Bayer process practice'])

# ===================================================================== digestion
MODULES['digestion_autoclave'] = mod(
    definition=('Digestion autoclaves are agitated pressure vessels in series where hot caustic liquor dissolves alumina from bauxite (Al(OH)₃ + NaOH → NaAl(OH)₄). Live steam injection heats the slurry to digestion '
                'temperature and the series of vessels provides the residence time.'),
    applications=['High-temperature digestion of boehmitic/diasporic bauxite', 'Low-temperature (gibbsitic) digesters at atmospheric-to-moderate pressure'],
    key_points=['Gibbsite ≈ 140–150 °C; boehmite/diaspore ≈ 230–270 °C', 'Pressures up to ~ 30–35 bar (high temperature)', 'Live steam or indirect heating', 'Scaling and erosion are main issues'],
    principle=[step('Preheated slurry enters autoclave 1.', 'transfer_steam', overlay='flow'), step('Live steam heats it to digestion temperature.', 'ac1_tank', overlay='pressure'),
               step('Agitators keep solids suspended.', 'ac1_agitator'), step('Slurry overflows through the series.', 'ac2_tank', overlay='flow'), step('Digested slurry leaves to flash cooling.', 'ac3_tank')],
    curve='Alumina extraction vs temperature and time; equilibrium A/C ratio limits loading.',
    params=ar(P('Vessels ~ 2 – 4 m diameter, 10 – 20 m tall'), P('~ 500 – 3000', 'm³/h slurry'), P('~ 140 – 270 °C; up to ~ 35 bar', '—'), P('Agitators ~ 30 – 150 each', 'kW')),
    install=_PV, maint=_m([M('Monitor temperature, pressure, agitator load.', 'ac1_drive', 'continuous')], [M('Thickness checks at erosion points.', 'transfer_steam', 'quarterly')], [M('Descale vessels; inspect agitators.', 'ac2_tank')], _NL),
    failures=[F('Scaling', ['Lower volume, heat transfer'], ['DSP/titanate'], ['Descale; better desilication'], 'ac1_tank'), F('Erosion leaks', ['Leaks at transfer lines'], ['High velocity slurry'], ['Hardened fittings'], 'transfer_steam')],
    quiz=[Q('What dissolves the alumina?', ['Hot caustic soda liquor', 'Acid', 'Water only', 'Air'], 0, 'NaOH.'), Q('Why higher temperature for boehmite?', ['It is less soluble/reactive than gibbsite', 'Cheaper', 'Faster pumps', 'None'], 0, 'Mineralogy.'),
          Q('What heats the slurry here?', ['Live steam injection', 'Electric coils only', 'Sunlight', 'Flames inside'], 0, 'Steam.')],
    selection=['Temperature set by bauxite mineralogy; volume by residence time.'], safety=['Hot caustic under pressure — relief protection, lock-out, PPE.'], refs=['Bayer process practice (TMS Light Metals)'])

MODULES['digestion_heater'] = mod(
    definition=('Digestion heaters are shell & tube exchangers that preheat the bauxite slurry before digestion. Slurry passes several times through the tubes while flash vapour from the multi-stage flash tanks condenses on the outside.'),
    applications=['Regenerative slurry heating before digestion', 'Heating with flash vapour from blow-off tanks', 'Final heating with live steam (last heaters)'],
    key_points=['Uses flash vapour (heat recovery)', 'Multi-pass slurry flow', 'Scale reduces heat transfer', 'Heaters descaled in rotation'],
    principle=[step('Slurry enters the bottom channel head.', 'channel_heads', overlay='flow'), step('It makes several passes through the tubes.', 'tubes', overlay='temperature'),
               step('Flash vapour condenses in the shell.', 'shell'), step('Condensate and non-condensables are removed.', 'nozzles')],
    curve='U-value vs time: falls as scale builds; cleaning restores it.',
    params=ar(P('Shell ~ 1 – 2 m diameter, 8 – 15 m'), P('~ 200 – 1500', 'm³/h slurry'), P('Up to ~ 250 °C', '°C'), P('Duty ~ 5 – 50', 'MW')),
    install=_PV, maint=_m([M('Monitor approach temperatures.', 'tubes', 'daily')], [M('Descaling (hydro-blasting/acid).', 'tubes', 'per schedule')], [M('Tube replacement.', 'tubes')], _NL),
    failures=[F('Scaling', ['Lower outlet temperature'], ['DSP, titanate'], ['Descale; improve desilication'], 'tubes'), F('Tube leaks', ['Slurry in condensate'], ['Erosion'], ['Plug/retube'], 'tubes')],
    quiz=[Q('What heats the slurry?', ['Condensing flash vapour', 'Electric heaters', 'Hot air', 'Flame'], 0, 'Regenerative.'), Q('Why descale regularly?', ['Scale cuts heat transfer', 'Colour', 'Noise', 'Weight'], 0, 'Fouling.'),
          Q('Why vent non-condensables?', ['They blanket the tubes', 'For pressure', 'Not needed', 'Taste'], 0, 'Air blanketing.')],
    selection=['Area from duty with fouling factor; spare heaters for descaling rotation.'], safety=['Isolation and depressurising before descaling.'], refs=['TEMA', 'Bayer practice'])

MODULES['multi_stage_flash_vessel'] = mod(
    definition=('A multi-stage flash train lowers the pressure of hot digested slurry in steps. In each tank some water flashes to steam and the slurry cools; that vapour is used to heat incoming slurry, recovering heat.'),
    applications=['Digestion heat recovery', 'Flash cooling before clarification'],
    key_points=['Stepwise pressure reduction', 'Flash vapour → regenerative heaters', 'Erosion at let-down points', 'Level control per stage'],
    principle=[step('Digested slurry enters tank 1 at high pressure.', 'flash_tank_1', overlay='pressure'), step('Part of the water flashes to steam.', 'slurry_1'),
               step('Vapour goes to the matching heater.', 'piping', overlay='flow'), step('Slurry passes to the next lower-pressure tank.', 'flash_tank_2'), step('The last tank discharges at near-atmospheric pressure.', 'flash_tank_3')],
    curve='Temperature profile falls stage by stage; heat recovered ∝ flash steam.',
    params=ar(P('Tanks ~ 2 – 5 m diameter'), P('~ 500 – 3000', 'm³/h'), P('~ 250 °C → ~ 105 °C, pressure stepping down', '—'), P('— (no drive)', 'kW')),
    install=_PV, maint=_m([M('Check levels and let-down valves.', 'piping', 'daily')], [M('Thickness checks; wear liners.', 'flash_tank_1', 'quarterly')], [M('Valve trim replacement.', 'piping')], _NL),
    failures=[F('Erosion', ['Leaks, thinning'], ['Two-phase high velocity'], ['Wear-resistant liners'], 'flash_tank_1'), F('Carry-over', ['Slurry in vapour lines'], ['High level'], ['Level control'], 'slurry_2')],
    quiz=[Q('Why flash in stages?', ['To recover heat at several pressures', 'To add steam', 'To grind', 'To filter'], 0, 'Regeneration.'), Q('Where does flash vapour go?', ['To slurry heaters', 'To atmosphere always', 'To pumps', 'Nowhere'], 0, 'Heaters.'),
          Q('Main wear mechanism?', ['Erosion at let-down', 'Corrosion only', 'Fatigue only', 'None'], 0, 'Erosion.')],
    selection=['Number of stages vs heat recovery economics.'], safety=['Hot flashing slurry; relief protection.'], refs=['Bayer practice'])

MODULES['desilication_tank'] = mod(
    definition=('Pre-desilication tanks hold the bauxite slurry at about 95–100 °C for several hours so the reactive silica that dissolves re-precipitates as sodalite (desilication product, DSP) before digestion. This protects heaters from scale and keeps silica out of the product.'),
    applications=['Bauxites with reactive silica (kaolinite)', 'Protecting digestion heaters from DSP scale', 'Controlling silica in pregnant liquor and product'],
    key_points=['~ 95–100 °C for ~ 6–10 h', 'Forms sodalite (DSP)', 'DSP locks up caustic and alumina', 'Reduces heater scaling'],
    principle=[step('Slurry enters the top.', 'nozzles', overlay='flow'), step('The coil holds temperature.', 'heating_coil', overlay='temperature'),
               step('The agitator keeps it mixed.', 'ds_agitator'), step('DSP crystals form over hours.', 'ds_slurry'), step('Slurry leaves to digestion.', 'ds_tank', overlay='flow')],
    curve='Silica in liquor vs time — falls towards DSP equilibrium.',
    params=ar(P('Tanks ~ 10 – 20 m diameter'), P('Residence ~ 6 – 10 h', 'h'), P('~ 95 – 100 °C', '°C'), P('Agitator ~ 50 – 200', 'kW')),
    install=_TANK, maint=_m([M('Check temperature and agitator.', 'ds_drive', 'daily')], [M('Descale coils and tank.', 'heating_coil', 'shutdown')], [M('Agitator overhaul.', 'ds_agitator')], _NL),
    failures=[F('Incomplete desilication', ['Heater scaling downstream'], ['Short residence, low temperature'], ['Increase time/temperature'], 'ds_tank'), F('Coil fouling', ['Low temperature'], ['Scale'], ['Descale'], 'heating_coil')],
    quiz=[Q('What forms in desilication?', ['Sodalite (DSP)', 'Gibbsite', 'Oxalate', 'Lime'], 0, 'DSP.'), Q('Why remove silica early?', ['Prevents scaling and product contamination', 'Adds caustic', 'Colour', 'Noise'], 0, 'Scale.'),
          Q('Typical temperature?', ['~ 95–100 °C', '~ 250 °C', '~ 20 °C', '~ 500 °C'], 0, 'Atmospheric.')],
    selection=['Residence from silica kinetics tests.'], safety=['Hot caustic slurry.'], refs=['Bayer practice'])

# ===================================================================== precipitation & classification
MODULES['precipitation_tank_agitator'] = mod(
    definition=('Precipitators are large tanks in which cooled, seeded pregnant liquor deposits gibbsite (aluminium hydroxide): NaAl(OH)₄ → Al(OH)₃ + NaOH. A slow draft-tube agitator circulates the slurry, keeping hydrate suspended with low shear so crystals grow and agglomerate.'),
    applications=['Gibbsite precipitation trains (often 10–20 tanks)', 'Agglomeration stage (fine seed, higher temperature)', 'Growth stage (coarse seed, interstage cooling)'],
    key_points=['Residence ~ 30–60 h', 'Cooling ~ 75–80 → 60–65 °C', 'Seed charge drives growth', 'Low shear protects crystals'],
    principle=[step('Pregnant liquor and seed enter.', 'interstage_cooling', overlay='flow'), step('The impeller pushes slurry down the draft tube.', 'pr_agitator'),
               step('Slurry rises in the annulus and circulates.', 'pr_tank'), step('Crystals grow as alumina precipitates.', 'pr_slurry', overlay='temperature'), step('Interstage cooling raises yield.', 'interstage_cooling')],
    curve='Yield vs temperature and A/C ratio; particle size distribution vs seed and temperature.',
    params=ar(P('Tanks ~ 10 – 14 m diameter, 30 – 40 m tall'), P('~ 1000 – 4000', 'm³/h liquor (train)'), P('~ 80 → 60 °C', '°C'), P('Agitator ~ 50 – 150', 'kW')),
    install=_TANK, maint=_m([M('Monitor temperature profile and solids.', 'pr_slurry', 'daily')], [M('Descale tank walls and draft tube.', 'pr_tank', 'cycle')], [M('Agitator gearbox overhaul.', 'pr_drive')], _NL),
    failures=[F('Scale build-up', ['Loss of volume'], ['Hydrate scale'], ['Descale in rotation'], 'pr_tank'), F('Fine product', ['Weak, fine hydrate'], ['Oxalate, too much nucleation'], ['Control oxalate; temperature'], 'pr_slurry')],
    quiz=[Q('What precipitates?', ['Gibbsite Al(OH)₃', 'Sodalite', 'Calcium carbonate', 'Oxalate'], 0, 'Hydrate.'), Q('Why add seed?', ['Surface for crystal growth', 'Colour', 'Heat', 'Pressure'], 0, 'Growth.'),
          Q('Why cool between tanks?', ['Increases supersaturation and yield', 'Saves power', 'Reduces noise', 'No reason'], 0, 'Yield.')],
    selection=['Train volume from yield/kinetics; agitator for suspension at low shear.'], safety=['Hot caustic; confined space for descaling.'], refs=['Bayer practice'])

MODULES['seed_classification_unit'] = mod(
    definition=('A seed classification unit splits precipitated hydrate by size. In a gravity classifier, coarse crystals settle against the rising liquor and leave in the underflow as product; fine crystals are carried up with the overflow and returned as seed.'),
    applications=['Product/seed split in precipitation circuits', 'Fine-seed recovery for agglomeration', 'Control of product particle size'],
    key_points=['Upflow velocity sets the cut size', 'Coarse = product; fine = seed', 'Controls product size distribution', 'Often combined with cyclones'],
    principle=[step('Hydrate slurry enters the feedwell.', 'feedwell', overlay='flow'), step('Coarse crystals settle to the cone.', 'classifier_tank'),
               step('Fines rise to the overflow launder.', 'liquor', overlay='pressure'), step('The underflow pump takes product.', 'underflow_pump', overlay='flow')],
    curve='Partition (Tromp) curve: fraction to underflow vs particle size.',
    params=ar(P('Tank ~ 5 – 15 m diameter'), P('~ 200 – 2000', 'm³/h'), P('~ 60 – 75 °C', '°C'), P('Pumps ~ 30 – 150', 'kW')),
    install=_THK, maint=_m([M('Check underflow density and size.', 'underflow_pump', 'per shift')], [M('Clear scale in cone.', 'classifier_tank', 'monthly')], [M('Pump overhaul.', 'underflow_pump')], _NL),
    failures=[F('Wrong cut', ['Product too fine/coarse'], ['Flow or density change'], ['Adjust overflow rate'], 'classifier_tank'), F('Cone blockage', ['No underflow'], ['Scale, coarse build-up'], ['Flush; descale'], 'classifier_tank')],
    quiz=[Q('What goes to the underflow?', ['Coarse hydrate (product)', 'Fines', 'Air', 'Steam'], 0, 'Product.'), Q('What sets the cut size?', ['Upflow velocity', 'Colour', 'Motor', 'Pipe size'], 0, 'Rise rate.'),
          Q('Fines are used as…', ['Seed', 'Waste', 'Fuel', 'Nothing'], 0, 'Seed.')],
    selection=['Area from upflow velocity for target cut.'], safety=['Hot caustic.'], refs=['Bayer practice'])

MODULES['classification_hydrocyclone'] = mod(
    definition=('Hydrocyclones classify slurries by particle size using centrifugal force. Slurry fed tangentially spins in the cyclone; coarse particles move to the wall and leave at the apex, while fines and most of the liquid leave through the central vortex finder.'),
    applications=['Hydrate classification', 'Mill circuit classification', 'Sand separation'],
    key_points=['d50 cut size ↓ with smaller diameter and higher pressure', 'Apex size controls underflow density', 'Avoid "roping"', 'Clusters on radial manifolds'],
    principle=[step('Feed enters the distributor.', 'distributor', overlay='flow'), step('Tangential entry creates a vortex.', 'cyclones', overlay='pressure'),
               step('Coarse particles spiral down to the apex.', 'cyclones'), step('Fines go up the vortex finder to the overflow launder.', 'launders', overlay='flow')],
    curve='Partition curve; d50 ≈ f(D^1.5…, ΔP^−0.25…) per Plitt/maker correlations.',
    params=ar(P('Cyclones ~ 0.1 – 0.8 m diameter'), P('~ 20 – 500', 'm³/h per cyclone'), P('Feed ~ 0.5 – 2 bar', 'bar'), P('Feed pump ~ 50 – 500', 'kW')),
    install=_SOL, maint=_m([M('Watch underflow shape (spray vs rope).', 'cyclones', 'per shift')], [M('Measure apex wear.', 'cyclones', 'weekly')], [M('Replace liners.', 'cyclones')], _NL),
    failures=[F('Roping', ['Thick rope underflow, coarse overflow'], ['Overloaded apex'], ['Larger apex; more cyclones'], 'cyclones'), F('Apex wear', ['Dilute underflow'], ['Abrasion'], ['Replace apex'], 'cyclones')],
    quiz=[Q('Coarse particles leave through…', ['The apex (underflow)', 'Vortex finder', 'Feed', 'Launder top'], 0, 'Underflow.'), Q('Smaller cyclone diameter gives…', ['Finer cut', 'Coarser cut', 'No change', 'No flow'], 0, 'Finer d50.'),
          Q('What is roping?', ['Overloaded apex discharging a dense rope', 'Normal spray', 'Air entry', 'Leak'], 0, 'Overload.')],
    selection=['Choose diameter for d50 and number for flow.'], safety=['Pressurised slurry; lock out before liner changes.'], refs=['Svarovsky — Hydrocyclones'])

# ===================================================================== residue
MODULES['red_mud_washer'] = mod(
    definition=('Red mud washers are thickeners arranged in a counter-current decantation (CCD) train. Mud is pumped forward from washer to washer while wash water flows backward; each stage dilutes and recovers the dissolved caustic soda and alumina in the mud.'),
    applications=['Residue washing in Bayer refineries', 'Counter-current decantation in hydrometallurgy (e.g. copper, uranium)'],
    key_points=['Counter-current flow', 'Typically 4–7 washers', 'Flocculant aids settling', 'Soda recovery ↑ with stages and underflow density'],
    principle=[step('Mud from the settler enters washer 1.', 'w1_feedwell', overlay='flow'), step('Mud settles and rakes move it to the cone.', 'w1_rakes'),
               step('Underflow goes forward to the next washer.', 'interstage_piping', overlay='flow'), step('Overflow liquor goes backward.', 'w2_tank', overlay='pressure'), step('Washed mud leaves the last washer.', 'w3_mud')],
    curve='Soluble loss vs number of stages and wash ratio.',
    params=ar(P('Washers ~ 20 – 50 m diameter'), P('~ 100 – 400', 't/h mud'), P('~ 60 – 100 °C', '°C'), P('Rake drives ~ 10 – 40 each', 'kW')),
    install=_THK, maint=_m([M('Monitor torque, bed level, overflow clarity.', 'w1_drive', 'continuous')], [M('Check flocculant system.', 'interstage_piping', 'daily')], [M('Rake and drive inspection.', 'w2_rakes')], _NL),
    failures=[F('Rake bogging', ['High torque trip'], ['Mud bed too high'], ['Increase underflow; lift rakes'], 'w1_rakes'), F('Dirty overflow', ['Solids in liquor'], ['Poor flocculation'], ['Adjust flocculant'], 'w1_clear')],
    quiz=[Q('In CCD, wash water flows…', ['Opposite to the mud', 'With the mud', 'Not at all', 'Upward only'], 0, 'Counter-current.'), Q('What is recovered?', ['Caustic soda and alumina', 'Iron', 'Silica', 'Water only'], 0, 'Soda.'),
          Q('Why flocculant?', ['Faster settling', 'Colour', 'Heat', 'Foam'], 0, 'Settling.')],
    selection=['Stage count and wash ratio from soda-loss economics.'], safety=['Caustic; rake torque protection.'], refs=['Bayer practice'])

MODULES['mud_settling_tank'] = mod(
    definition=('The mud settler (primary thickener) separates red mud from pregnant liquor after digestion. Flocculant added in the feedwell makes the mud settle quickly; clear liquor overflows to polishing filtration and thickened mud is pumped to the washers.'),
    applications=['Primary residue (red mud) separation after digestion', 'High-rate thickening in mineral processing'],
    key_points=['High-rate thickening with flocculant', 'Overflow clarity is critical', 'Rake drive torque monitored', 'Underflow density control'],
    principle=[step('Diluted digested slurry enters the feedwell.', 'st_feedwell', overlay='flow'), step('Flocculant forms flocs that settle.', 'st_mud'),
               step('Clear liquor overflows.', 'st_clear', overlay='pressure'), step('Rakes move mud to the cone; pump takes underflow.', 'st_rakes'), step('The drive turns the rakes slowly.', 'st_drive')],
    curve='Settling flux curve; overflow clarity vs flocculant dose.',
    params=ar(P('Settler ~ 20 – 50 m diameter'), P('~ 1000 – 3000', 'm³/h'), P('~ 100 °C', '°C'), P('Rake drive ~ 10 – 50', 'kW')),
    install=_THK, maint=_m([M('Overflow clarity and torque.', 'st_drive', 'continuous')], [M('Flocculant system check.', 'piping', 'daily')], [M('Inspect rakes.', 'st_rakes')], _NL),
    failures=[F('Poor clarity', ['Solids in overflow'], ['Low flocculant, overload'], ['Adjust dose/rate'], 'st_clear'), F('High torque', ['Trip'], ['Mud build-up'], ['Increase underflow'], 'st_rakes')],
    quiz=[Q('What overflows?', ['Clear pregnant liquor', 'Mud', 'Steam', 'Sand'], 0, 'Liquor.'), Q('What helps mud settle?', ['Flocculant', 'Heat', 'Air', 'Magnets'], 0, 'Floc.'),
          Q('Where does the underflow go?', ['To the washers', 'To precipitation', 'To calcination', 'To stack'], 0, 'CCD.')],
    selection=['Area from settling tests; flocculant type from trials.'], safety=['Hot caustic.'], refs=['Bayer practice'])

MODULES['sand_separator'] = mod(
    definition=('A sand separator removes coarse sand from red mud slurry. In an inclined screw classifier, sand settles in a pool and a slowly turning screw rakes it up the incline, draining it, while fine mud overflows to the washers.'),
    applications=['Sand removal in Bayer residue circuits', 'Mineral sand classification'],
    key_points=['Separates > ~ 100 µm sand', 'Protects thickeners and pumps', 'Washed sand used for construction', 'Screw slowly drags sand'],
    principle=[step('Slurry enters the pool.', 'trough_tank', overlay='flow'), step('Sand settles; fines stay suspended.', 'pool_slurry', overlay='pressure'),
               step('The screw rakes sand up the incline.', 'screw'), step('Sand discharges at the top.', 'drive_discharge')],
    curve='Sand recovery vs overflow rate and pool area.',
    params=ar(P('Screw ~ 0.5 – 2 m diameter'), P('~ 10 – 200', 't/h sand'), P('~ 60 – 100 °C', '°C'), P('~ 5 – 50', 'kW')),
    install=_SOL, maint=_m([M('Check sand moisture and screw.', 'screw', 'daily')], [M('Inspect wear shoes.', 'screw', 'monthly')], [M('Replace flights.', 'screw')], _LUBE),
    failures=[F('Screw overload', ['Trip'], ['Sand surge'], ['Raise screw; regulate feed'], 'screw'), F('Fines in sand', ['Wet, muddy sand'], ['High feed rate'], ['Reduce rate; more wash'], 'pool_slurry')],
    quiz=[Q('What overflows the weir?', ['Fine mud slurry', 'Sand', 'Steam', 'Oil'], 0, 'Fines.'), Q('What moves sand up?', ['Spiral screw', 'Belt', 'Air', 'Pump'], 0, 'Screw.'),
          Q('Why remove sand early?', ['Reduce erosion downstream', 'Add heat', 'Colour', 'None'], 0, 'Erosion.')],
    selection=['Size pool for overflow rate; screw for sand load.'], safety=['Guard screw; lock out.'], refs=['Classifier maker data'])

# ===================================================================== filtration & product
MODULES['alumina_hydrate_filter'] = mod(
    definition=('A rotary vacuum drum filter separates alumina hydrate from liquor. The drum turns partly submerged in slurry; vacuum draws liquor through the cloth so a cake forms, is washed and dried, and is then released by air blow-back and a scraper.'),
    applications=['Product hydrate filtration', 'Seed filtration'],
    key_points=['Continuous vacuum filtration', 'Zones: form, wash, dry, discharge', 'Cloth condition critical', 'Wash removes soda'],
    principle=[step('The drum dips into slurry and a cake forms.', 'slurry', overlay='pressure'), step('The cake is washed by sprays.', 'wash_sprays'),
               step('The vacuum valve switches zones.', 'vacuum_system', overlay='flow'), step('The scraper discharges the cake.', 'scraper_chute'), step('The drive turns the drum.', 'drive_agitator')],
    curve='Filtration rate ∝ ΔP / (μ·(cake + cloth resistance)).',
    params=ar(P('Drum ~ 2 – 4 m diameter, 3 – 6 m long'), P('~ 20 – 100', 't/h hydrate'), P('Vacuum ~ 0.4 – 0.8 bar below atm.', 'bar'), P('~ 10 – 50 (plus vacuum pump)', 'kW')),
    install=_SOL, maint=_m([M('Check cake, cloth and vacuum.', 'filter_sectors', 'per shift')], [M('Wash cloth; check valve wear plate.', 'vacuum_system', 'weekly')], [M('Replace cloth.', 'drum')], _LUBE),
    failures=[F('Cloth blinding', ['Wet cake, low rate'], ['Scale, fines'], ['Acid wash; replace'], 'drum'), F('Vacuum loss', ['Thin cake'], ['Valve wear, leaks'], ['Repair'], 'vacuum_system')],
    quiz=[Q('What forms the cake?', ['Vacuum draws liquor through the cloth', 'Gravity only', 'Heat', 'Magnets'], 0, 'Vacuum.'), Q('How is cake removed?', ['Blow-back and scraper', 'Water jet only', 'Not removed', 'Fan'], 0, 'Discharge.'),
          Q('Why wash the cake?', ['Remove soda', 'Cool', 'Colour', 'Weight'], 0, 'Purity.')],
    selection=['Area from leaf tests.'], safety=['Rotating drum — guards; caustic.'], refs=['Filtration handbooks'])

MODULES['hydrate_washing_system'] = mod(
    definition=('A horizontal vacuum belt filter dewaters and washes hydrate. The belt moves over vacuum boxes; hot condensate washes the cake in counter-current stages so soda content is reduced using little water.'),
    applications=['Product hydrate washing before calcination', 'Washing of chemical and mineral filter cakes'],
    key_points=['Counter-current washing', 'Separate filtrate zones', 'Low soda target', 'Continuous'],
    principle=[step('Slurry is fed onto the belt.', 'feed_wash', overlay='flow'), step('Vacuum boxes form and dewater the cake.', 'vacuum_boxes', overlay='pressure'),
               step('Wash sprays rinse the cake.', 'cake'), step('Filtrates collect in separate receivers.', 'filtrate_receivers'), step('Cake discharges at the head.', 'discharge_chute', overlay='flow')],
    curve='Residual soda vs wash ratio (counter-current curve).',
    params=ar(P('Belt ~ 1 – 4 m wide, 10 – 40 m long'), P('~ 30 – 150', 't/h hydrate'), P('Wash ~ 90 °C condensate', '°C'), P('~ 15 – 75 (plus vacuum pumps)', 'kW')),
    install=_SOL, maint=_m([M('Check belt tracking and sprays.', 'bfbelt', 'per shift')], [M('Wash cloth; check seals.', 'vacuum_boxes', 'weekly')], [M('Replace cloth/belt.', 'bfbelt')], _LUBE),
    failures=[F('High soda in cake', ['Product off-spec'], ['Poor washing, cracked cake'], ['Adjust wash; flatten cake'], 'cake'), F('Belt mistracking', ['Edge damage'], ['Misalignment'], ['Re-track'], 'bfbelt')],
    quiz=[Q('Why counter-current wash?', ['Less water for the same soda removal', 'Faster belt', 'Hotter cake', 'No reason'], 0, 'Efficiency.'), Q('Where is vacuum applied?', ['Boxes under the belt', 'Above', 'In the chute', 'Nowhere'], 0, 'Vacuum boxes.'),
          Q('Wash liquid used?', ['Hot condensate', 'Caustic', 'Oil', 'Seawater'], 0, 'Condensate.')],
    selection=['Size from cake formation and wash times.'], safety=['Moving belt; hot water.'], refs=['Belt filter maker data'])

MODULES['calcination_fluidized_bed_cooler'] = mod(
    definition=('A fluidised bed cooler cools hot calcined alumina. The alumina flows through fluidised chambers with immersed water-cooled tube bundles; fluidising air keeps it moving and is warmed for reuse in the calciner.'),
    applications=['Stationary (gas-suspension / circulating fluid bed) calciner product cooling', 'Cooling other hot granular products (e.g. cement raw materials, catalysts)'],
    key_points=['Indirect water cooling + air', 'Counter-flow water', 'Product < ~ 80 °C', 'Heat recovered to combustion air'],
    principle=[step('Hot alumina enters the first chamber.', 'nozzles', overlay='flow'), step('Air fluidises the bed.', 'air_plenum'),
               step('Tube bundles remove heat.', 'cooling_bundles', overlay='temperature'), step('Alumina flows over weirs to the outlet.', 'cooler_body')],
    curve='Outlet temperature vs bed area and water flow.',
    params=ar(P('Bed ~ 10 – 60 m²'), P('~ 50 – 250', 't/h'), P('~ 250 → 80 °C', '°C'), P('Fluidising blowers ~ 50 – 300', 'kW')),
    install=_SOL, maint=_m([M('Check outlet temperature and water flow.', 'cooling_bundles', 'continuous')], [M('Inspect nozzles and bundles for erosion.', 'cooling_bundles', 'shutdown')], [M('Replace bundles.', 'cooling_bundles')], _LUBE),
    failures=[F('Tube leak', ['Wet alumina, steam'], ['Erosion'], ['Isolate bundle; repair'], 'cooling_bundles'), F('Defluidisation', ['Hot spots'], ['Blocked distributor'], ['Clean'], 'air_plenum')],
    quiz=[Q('How is alumina cooled?', ['Water-cooled tubes in a fluid bed', 'Direct water spray', 'Ice', 'Vacuum'], 0, 'Indirect.'), Q('Why fluidise?', ['Good heat transfer and flow', 'Colour', 'Pressure', 'Noise'], 0, 'Mixing.'),
          Q('Warm air is reused as…', ['Combustion air', 'Waste', 'Instrument air', 'Nothing'], 0, 'Recovery.')],
    selection=['Area from heat duty.'], safety=['Hot product; water leak hazard.'], refs=['Calciner literature'])

MODULES['alumina_cooler'] = mod(
    definition=('A rotary alumina cooler is a slowly rotating drum whose outside is sprayed with water. Hot alumina tumbles inside and is cooled through the steel shell, never touching the water.'),
    applications=['Cooling calcined alumina (rotary kiln plants)', 'Cooling other hot bulk solids'],
    key_points=['Indirect cooling through the shell', 'Lifters improve contact', 'No product wetting', 'Shell water must not scale'],
    principle=[step('Hot alumina enters the drum.', 'hoods', overlay='flow'), step('The drum rotates and tumbles it.', 'girth_tyres'),
               step('Sprays cool the shell.', 'spray_system', overlay='temperature'), step('Cooled alumina discharges.', 'shell')],
    curve='Outlet temperature vs drum length, speed and water flow.',
    params=ar(P('Drum ~ 2 – 4 m diameter, 15 – 40 m long'), P('~ 20 – 120', 't/h'), P('~ 300 → 80 °C', '°C'), P('~ 50 – 200', 'kW')),
    install=_MACH, maint=_m([M('Check spray pattern and temperatures.', 'spray_system', 'daily')], [M('Roller and tyre inspection.', 'supports_drive', 'monthly')], [M('Shell inspection; descale exterior.', 'shell')], _LUBE),
    failures=[F('Shell scaling', ['Hot product'], ['Hard water'], ['Water treatment; clean'], 'spray_system'), F('Tyre wear', ['Noise'], ['Misalignment'], ['Re-align rollers'], 'girth_tyres')],
    quiz=[Q('Does water touch the alumina?', ['No — indirect cooling', 'Yes', 'Sometimes', 'Only at start'], 0, 'Indirect.'), Q('Why lifters?', ['Better contact with cooled wall', 'Grinding', 'Noise', 'Weight'], 0, 'Contact.'),
          Q('What turns the drum?', ['Girth gear drive', 'Water', 'Air', 'Gravity'], 0, 'Drive.')],
    selection=['Size from duty and residence.'], safety=['Rotating equipment guards.'], refs=['Process cooler literature'])

MODULES['alumina_storage_silo'] = mod(
    definition=('An alumina storage silo stores smelter-grade alumina. An aerated floor of air-slide pads fluidises the product so it flows to the discharge; a bin-vent filter releases displaced air during filling, and trucks or rail cars are loaded below.'),
    applications=['Product storage at refineries, ports and smelters', 'Buffer storage before ship or rail loading'],
    key_points=['Aeration prevents bridging', 'Bin-vent filter controls dust', 'Radar level monitoring', 'Pressure/vacuum relief'],
    principle=[step('Alumina fills from the top.', 'roof_equipment', overlay='flow'), step('It is stored in the silo.', 'alumina'),
               step('Air-slide pads fluidise it.', 'aeration_discharge', overlay='pressure'), step('It discharges to the tanker.', 'tanker', overlay='flow')],
    curve='Discharge rate vs aeration air flow.',
    params=ar(P('Silo ~ 10 – 40 m diameter'), P('~ 5 000 – 100 000', 't'), P('Ambient; aeration ~ 0.1 – 0.6 bar', '—'), P('Aeration blowers ~ 10 – 100', 'kW')),
    install=_SOL, maint=_m([M('Check level and filter ΔP.', 'roof_equipment', 'daily')], [M('Check aeration pads.', 'aeration_discharge', 'annual')], [M('Structural inspection.', 'silo_shell')], ['Blowers per maker.']),
    failures=[F('Bridging/rat-holing', ['No flow'], ['Failed aeration'], ['Repair pads; check air'], 'aeration_discharge'), F('Overfill', ['Dust release'], ['Level failure'], ['Test level/alarms'], 'roof_equipment')],
    quiz=[Q('Why aerate the floor?', ['Fluidise alumina so it flows', 'Cool it', 'Dry it', 'Colour'], 0, 'Flow.'), Q('Bin-vent filter purpose?', ['Release air, keep dust in', 'Add air', 'Measure level', 'None'], 0, 'Dust.'),
          Q('Why P/V relief?', ['Protect silo from pressure/vacuum', 'For noise', 'For level', 'None'], 0, 'Structure.')],
    selection=['Capacity from shipping logistics.'], safety=['Never enter silos without permits (engulfment).'], refs=['EN 1991-4'])

MODULES['alumina_pneumatic_conveying_system'] = mod(
    definition=('A dense-phase pneumatic system conveys alumina in batches. A blow tank is filled through a dome valve, sealed, pressurised and the alumina is pushed through the pipeline as slow-moving plugs. Low velocity limits attrition and pipe wear.'),
    applications=['Alumina transfer to silos and smelter pot-feeding systems', 'Conveying abrasive or friable powders (cement, fly ash, catalysts)'],
    key_points=['Low velocity, high pressure', 'Batch cycle: fill → pressurise → convey', 'Boosters prevent blockage', 'Gentle on product'],
    principle=[step('The dome valve opens and the blow tank fills.', 'dome_valve'), step('The tank is sealed and pressurised.', 'blow_tank', overlay='pressure'),
               step('Plugs move through the line.', 'conveying_line', overlay='flow'), step('The receiving silo collects the alumina.', 'receiving_silo')],
    curve='Pressure drop vs solids loading and distance (dense-phase state diagram).',
    params=ar(P('Line ~ 100 – 250 mm'), P('~ 10 – 100', 't/h'), P('~ 2 – 6', 'bar'), P('Compressor share ~ 20 – 200', 'kW')),
    install=_SOL, maint=_m([M('Check cycle times and pressures.', 'blow_tank', 'daily')], [M('Inspect dome valve seal.', 'dome_valve', 'monthly')], [M('Replace bends.', 'conveying_line')], ['Valve actuators per maker.']),
    failures=[F('Line blockage', ['Pressure rises, no flow'], ['Wet product, booster fault'], ['Purge; check boosters'], 'conveying_line'), F('Seal leakage', ['Long cycles'], ['Worn dome seal'], ['Replace seal'], 'dome_valve')],
    quiz=[Q('Dense phase means…', ['Low-velocity plugs at high pressure', 'High velocity suspension', 'Belt conveying', 'Gravity flow'], 0, 'Dense.'), Q('Why for alumina?', ['Low attrition and wear', 'Cheaper air', 'Faster', 'Noisy'], 0, 'Gentle.'),
          Q('What seals the tank?', ['Dome valve', 'Gate', 'Bag', 'Nothing'], 0, 'Dome.')],
    selection=['Pilot tests for pressure drop; size air for distance.'], safety=['Pressure vessels; depressurise before maintenance.'], refs=['Mills — Pneumatic Conveying Design Guide'])

# ===================================================================== liquor treatment & environment
MODULES['causticization_tank'] = mod(
    definition=('A causticization reactor regenerates caustic soda from sodium carbonate in the liquor by reaction with slaked lime: Na₂CO₃ + Ca(OH)₂ → 2 NaOH + CaCO₃. The calcium carbonate is separated and the recovered caustic returns to the process.'),
    applications=['Caustic recovery in Bayer refineries', 'Lime causticizing of green liquor in pulp mills'],
    key_points=['Lime slaker prepares milk of lime', 'CaCO₃ precipitates', 'Conditions limit alumina loss as calcium aluminate', 'Lowers carbonate in liquor'],
    principle=[step('Lime is slaked to milk of lime.', 'lime_slaker'), step('Milk of lime and liquor enter the reactor.', 'piping', overlay='flow'),
               step('The agitator mixes; CaCO₃ forms.', 'cz_agitator', overlay='pressure'), step('Slurry leaves for separation.', 'cz_tank')],
    curve='Causticization efficiency vs liquor concentration and temperature.',
    params=ar(P('Reactor ~ 3 – 8 m diameter'), P('~ 50 – 300', 'm³/h liquor'), P('~ 90 – 100 °C', '°C'), P('Agitator ~ 15 – 75', 'kW')),
    install=_TANK, maint=_m([M('Check lime feed and agitator.', 'lime_slaker', 'daily')], [M('Descale reactor.', 'cz_tank', 'shutdown')], [M('Slaker overhaul.', 'slaker_paddles')], _NL),
    failures=[F('Low efficiency', ['High carbonate'], ['Poor lime quality, wrong conditions'], ['Check lime; adjust temperature'], 'cz_slurry'), F('Slaker blockage', ['Lime build-up'], ['Grit, low water'], ['Clean; adjust water'], 'lime_slaker')],
    quiz=[Q('Why causticize?', ['Regenerate NaOH from Na₂CO₃', 'Make alumina', 'Remove iron', 'Cool liquor'], 0, 'Caustic recovery.'), Q('What precipitates?', ['Calcium carbonate', 'Gibbsite', 'Oxalate', 'Sodalite'], 0, 'CaCO₃.'),
          Q('What does the slaker produce?', ['Milk of lime', 'Steam', 'Acid', 'Air'], 0, 'Ca(OH)₂.')],
    selection=['Size from carbonate removal rate.'], safety=['Lime is caustic and exothermic on slaking.'], refs=['Bayer practice'])

MODULES['oxalate_removal_system'] = mod(
    definition=('An oxalate removal system takes a side-stream of liquor, cools and seeds it so sodium oxalate crystallises in a controlled way, and separates the crystals in hydrocyclones or filters. Clean liquor returns; part of the crystals is recycled as seed.'),
    applications=['Liquor purification in Bayer refineries', 'Controlling organic impurities to protect hydrate quality'],
    key_points=['Oxalate comes from organic matter in bauxite', 'Uncontrolled oxalate spoils hydrate quality', 'Seeded cooling crystallisation', 'Crystals destroyed (lime/burning)'],
    principle=[step('Side-stream liquor enters the crystallizer.', 'piping', overlay='flow'), step('Cooling jacket lowers temperature.', 'cooling_jacket', overlay='temperature'),
               step('Oxalate grows on seed crystals.', 'ox_slurry'), step('The hydrocyclone separates crystals.', 'hydrocyclone'), step('Seed is recycled.', 'feed_pump')],
    curve='Oxalate solubility vs temperature and caustic.',
    params=ar(P('Crystallizer ~ 3 – 8 m diameter'), P('~ 20 – 200', 'm³/h'), P('Cooled to ~ 40 – 60 °C', '°C'), P('~ 15 – 75', 'kW')),
    install=_TANK, maint=_m([M('Monitor oxalate in liquor.', 'ox_slurry', 'daily')], [M('Clean jacket/cyclone.', 'cooling_jacket', 'monthly')], [M('Cyclone liner replacement.', 'hydrocyclone')], _NL),
    failures=[F('Oxalate breakthrough', ['Fine hydrate in precipitation'], ['Poor removal'], ['Increase side-stream'], 'ox_tank'), F('Jacket scaling', ['Poor cooling'], ['Scale'], ['Descale'], 'cooling_jacket')],
    quiz=[Q('Where does oxalate come from?', ['Organic matter in bauxite', 'Lime', 'Steam', 'Air'], 0, 'Organics.'), Q('Why remove it?', ['It ruins hydrate quality', 'Colour', 'Taste', 'No reason'], 0, 'Quality.'),
          Q('How is it crystallised?', ['Cooling and seeding', 'Heating', 'Acid', 'Magnet'], 0, 'Seeded cooling.')],
    selection=['Side-stream size from oxalate input rate.'], safety=['Caustic liquor.'], refs=['Bayer practice'])

MODULES['sodium_oxalate_filter'] = mod(
    definition=('A horizontal pressure-leaf filter separates sodium oxalate crystals from liquor. Slurry is pumped into the closed shell; cake forms on vertical mesh leaves while filtrate leaves through the manifold. The shell then rolls back and the cake is sluiced off.'),
    applications=['Oxalate removal', 'Polishing filtration'],
    key_points=['Batch pressure filtration', 'Leaves on manifold', 'Retractable shell for discharge', 'Sluicing removes cake'],
    principle=[step('Slurry fills the shell.', 'shell', overlay='pressure'), step('Cake forms on the leaves.', 'leaves'),
               step('Filtrate leaves via the manifold.', 'fixed_head', overlay='flow'), step('The shell opens; cake is sluiced into the hopper.', 'sluice_header')],
    curve='Filtrate volume vs time (constant-pressure filtration).',
    params=ar(P('Shell ~ 1 – 2.5 m diameter'), P('Area ~ 20 – 150', 'm²'), P('~ 2 – 6', 'bar'), P('Feed pump ~ 15 – 75', 'kW')),
    install=_PV, maint=_m([M('Check cycle and filtrate clarity.', 'leaves', 'per cycle')], [M('Inspect leaf screens.', 'leaves', 'monthly')], [M('Replace leaves; shell seal.', 'shell')], ['Shell drive/hydraulics per maker.']),
    failures=[F('Torn leaf', ['Cloudy filtrate'], ['Damage, wear'], ['Replace leaf'], 'leaves'), F('Seal leak', ['Leakage'], ['Worn seal'], ['Replace'], 'shell')],
    quiz=[Q('Where does cake form?', ['On the leaves', 'In the manifold', 'On the shell', 'In the pump'], 0, 'Leaves.'), Q('How is cake removed?', ['Shell opens; sluicing', 'Vacuum', 'Fan', 'Heat'], 0, 'Discharge.'),
          Q('Pressure filtration means…', ['Slurry pumped in under pressure', 'Vacuum', 'Gravity', 'Centrifugal'], 0, 'Pressure.')],
    selection=['Area from filtration tests.'], safety=['Depressurise before opening.'], refs=['Leaf filter maker data'])

MODULES['process_liquor_clarifier'] = mod(
    definition=('A multi-tray clarifier stacks several conical settling trays in one tank, each with its own feed, overflow and rake arms on a common shaft. It multiplies settling area to remove fine solids from process liquor in a small footprint.'),
    applications=['Liquor clarification', 'Green-liquor/process liquor polishing'],
    key_points=['Settling depends on area, not depth', 'Stacked trays multiply area', 'Common rake shaft', 'Small footprint'],
    principle=[step('Feed enters each tray.', 'feed_overflow', overlay='flow'), step('Solids settle on the trays.', 'trays', overlay='pressure'),
               step('Rakes push solids to downcomers.', 'rakes'), step('Clear liquor overflows.', 'tank'), step('Solids leave from the bottom.', 'mud_layers')],
    curve='Overflow rate per unit area vs clarity.',
    params=ar(P('Tank ~ 10 – 30 m diameter, 3 – 5 trays'), P('~ 200 – 1500', 'm³/h'), P('~ 60 – 100 °C', '°C'), P('Rake drive ~ 10 – 40', 'kW')),
    install=_THK, maint=_m([M('Check overflow clarity per tray.', 'trays', 'daily')], [M('Torque trend.', 'drive', 'continuous')], [M('Inspect trays and rakes.', 'rakes')], _NL),
    failures=[F('Tray overload', ['Solids carry-over'], ['Uneven feed split'], ['Balance feeds'], 'trays'), F('Rake torque', ['Trip'], ['Build-up'], ['Increase underflow'], 'rakes')],
    quiz=[Q('Why stack trays?', ['More settling area in one footprint', 'More depth', 'Heat', 'Noise'], 0, 'Area.'), Q('What do rakes do?', ['Move solids to downcomers', 'Mix', 'Heat', 'Pump'], 0, 'Rakes.'),
          Q('Settling capacity depends mainly on…', ['Area', 'Depth', 'Colour', 'Shape'], 0, 'Area.')],
    selection=['Total area from settling tests.'], safety=['Caustic.'], refs=['Clarifier design references'])

MODULES['alumina_dust_collection_system'] = mod(
    definition=('An electrostatic precipitator (ESP) removes alumina dust from calciner off-gas. High-voltage discharge electrodes charge the dust particles, which drift to earthed collecting plates. Rappers knock the dust into hoppers and it is returned to product.'),
    applications=['Calciner and kiln off-gas cleaning', 'Power-plant fly ash'],
    key_points=['Corona charging at high voltage', 'Efficiency > 99.5 % typical', 'Low pressure drop', 'Dust resistivity matters'],
    principle=[step('Dusty gas enters through the distribution screens.', 'casing', overlay='flow'), step('Discharge electrodes create a corona.', 'discharge_electrodes', overlay='pressure'),
               step('Charged dust collects on plates.', 'collecting_plates'), step('Rappers drop it into hoppers.', 'rappers'), step('The T/R set supplies HV.', 'tr_set')],
    curve='Deutsch–Anderson: η = 1 − exp(−w·A/Q).',
    params=ar(P('Casing ~ 5 – 15 m high, several fields'), P('Gas ~ 100 000 – 1 000 000', 'm³/h'), P('~ 150 – 350 °C; 40 – 100 kV DC', '—'), P('T/R sets ~ 50 – 500', 'kW')),
    install=_SOL, maint=_m([M('Monitor spark rate, voltage, current.', 'tr_set', 'continuous')], [M('Check rappers and hopper evacuation.', 'rappers', 'weekly')], [M('Internal inspection; electrode repair.', 'discharge_electrodes', 'shutdown')], ['Rapper drives per maker.']),
    failures=[F('Back-corona', ['Low efficiency'], ['High dust resistivity'], ['Gas conditioning; pulse energisation'], 'collecting_plates'), F('Broken electrode', ['Short circuit, field trip'], ['Fatigue'], ['Replace'], 'discharge_electrodes')],
    quiz=[Q('How is dust charged?', ['Corona discharge at high voltage', 'Water spray', 'Magnets', 'Friction'], 0, 'Corona.'), Q('What removes dust from plates?', ['Rappers', 'Fans', 'Water', 'Air jets only'], 0, 'Rapping.'),
          Q('Collection efficiency formula?', ['Deutsch–Anderson', 'Bernoulli', 'Stokes only', 'Ohm'], 0, 'η = 1 − e^(−wA/Q).')],
    selection=['Size SCA (specific collection area) from dust properties.'], safety=['Lethal HV — earthing and interlocks before entry.'], refs=['White — Industrial Electrostatic Precipitation'])
