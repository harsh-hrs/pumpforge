#include "calcs.h"

// JS helpers: F(x, d) = x.toFixed(d), N(x) = `${x}`
static inline Str F(double x, int d) { return js_fixed(x, d); }
static inline Str N(double x) { return fmt_num(x); }
static const double G = 9.80665;
static const double PI = 3.141592653589793;
#define S(x) (x).c()

const Calc CALCS[] = {
    {"shell_t", "Shell thickness (ASME VIII UG-27, simplified)", {{"Design pressure P (bar g)", 10}, {"Inside radius R (mm)", 500}, {"Allowable stress S (MPa)", 138}, {"Joint efficiency E", 0.85}, {"Corrosion allowance (mm)", 3}}, 5,
     [](const double* v) { double Pb = v[0], R = v[1], Sa = v[2], E = v[3], ca = v[4]; double P = Pb * 0.1; double tc = P * R / (Sa * E - 0.6 * P), ts = P * R / (2 * Sa * E - 0.4 * P);
        return Str::f("Cylinder (circumferential): t = %s + CA = %s mm\nSphere / hemi head: t = %s + CA = %s mm\nCheck code edition, MAWP and minimum thickness rules.", S(F(tc, 2)), S(F(tc + ca, 2)), S(F(ts, 2)), S(F(ts + ca, 2))); }},
    {"lmtd", "Heat exchanger LMTD & area", {{"Hot in (°C)", 120}, {"Hot out (°C)", 70}, {"Cold in (°C)", 25}, {"Cold out (°C)", 60}, {"Duty Q (kW)", 500}, {"Overall U (W/m²K)", 600}}, 6,
     [](const double* v) { double hi = v[0], ho = v[1], ci = v[2], co = v[3], Q = v[4], U = v[5]; double d1 = hi - co, d2 = ho - ci; double L = fabs(d1 - d2) < 1e-6 ? d1 : (d1 - d2) / log(d1 / d2);
        return Str::f("LMTD (counter-current) = %s K\nRequired area A = Q/(U·LMTD) = %s m²\n(apply F-correction for multipass)", S(F(L, 2)), S(F(Q * 1000 / (U * L), 2))); }},
    {"hvol", "Horizontal tank volume at level", {{"Inside diameter D (m)", 2}, {"Shell length L (m)", 6}, {"Liquid level h (m)", 1.2}}, 3,
     [](const double* v) { double D = v[0], L = v[1], h = v[2]; double R = D / 2, hh = fmin(fmax(h, 0), D); double A = R * R * acos((R - hh) / R) - (R - hh) * sqrt(2 * R * hh - hh * hh); double tot = PI * R * R * L;
        return Str::f("Liquid volume (shell only) = %s m³\nTotal shell volume = %s m³\nFill = %s %% (heads not included)", S(F(A * L, 3)), S(F(tot, 3)), S(F(A * L / tot * 100, 1))); }},
    {"souders", "Separator gas velocity (Souders–Brown)", {{"K factor (m/s)", 0.07}, {"Liquid density ρL (kg/m³)", 800}, {"Gas density ρG (kg/m³)", 20}, {"Gas flow (m³/s actual)", 0.5}}, 4,
     [](const double* v) { double K = v[0], rl = v[1], rg = v[2], Q = v[3]; double vv = K * sqrt((rl - rg) / rg), A = Q / vv;
        return Str::f("Max gas velocity = %s m/s\nMin vessel area = %s m²\nMin diameter = %s m (vertical, mesh pad)", S(F(vv, 3)), S(F(A, 3)), S(F(sqrt(4 * A / PI), 3))); }},
    {"shaft_power", "Shaft power ↔ torque", {{"Power P (kW)", 75}, {"Speed n (rpm)", 1480}}, 2,
     [](const double* v) { double T = v[0] * 1000 * 60 / (2 * PI * v[1]); return Str::f("Torque T = %s N·m\n(P = 2π·n·T / 60)", S(F(T, 1))); }},
    {"sync_speed", "Motor / generator speed & frequency", {{"Frequency f (Hz)", 50}, {"Number of poles p", 4}, {"Actual speed n (rpm)", 1470}}, 3,
     [](const double* v) { double f = v[0], p = v[1], n = v[2]; double ns = 120 * f / p;
        return Str::f("Synchronous speed ns = %s rpm\nSlip s = %s %%\nFrequency for 750 rpm = %s Hz", S(F(ns, 0)), S(F((ns - n) / ns * 100, 2)), S(F(750 * p / 120, 1))); }},
    {"compressor_power", "Compressor power (isentropic)", {{"Inlet pressure p1 (bar abs)", 1.013}, {"Discharge pressure p2 (bar abs)", 8}, {"Inlet flow Q (m³/min)", 10}, {"k = cp/cv", 1.4}, {"Isentropic efficiency (%)", 75}, {"Inlet temperature (°C)", 20}}, 6,
     [](const double* v) { double p1 = v[0], p2 = v[1], Q = v[2], k = v[3], e = v[4], T1 = v[5]; double r = p2 / p1, x = (k - 1) / k, Pi = k / (k - 1) * p1 * 1e5 * Q / 60 * (pow(r, x) - 1) / 1000;
        double T2 = (T1 + 273.15) * (1 + (pow(r, x) - 1) / (e / 100)) - 273.15;
        return Str::f("Pressure ratio = %s\nIsentropic power = %s kW\nShaft power ≈ %s kW\nDischarge temperature ≈ %s °C (no cooling)", S(F(r, 2)), S(F(Pi, 1)), S(F(Pi / (e / 100), 1)), S(F(T2, 0))); }},
    {"drive_ratio", "Gear / belt / chain ratio", {{"Driver teeth or diameter", 16}, {"Driven teeth or diameter", 32}, {"Input speed (rpm)", 1480}, {"Input torque (N·m)", 100}, {"Efficiency (%)", 97}}, 5,
     [](const double* v) { double a = v[0], b = v[1], n = v[2], T = v[3], e = v[4]; double i = b / a;
        return Str::f("Ratio i = %s : 1\nOutput speed = %s rpm\nOutput torque = %s N·m", S(F(i, 3)), S(F(n / i, 1)), S(F(T * i * e / 100, 1))); }},
    {"flywheel", "Flywheel energy", {{"Rim mass (kg)", 500}, {"Mean rim radius (m)", 0.6}, {"Speed (rpm)", 300}, {"Speed drop during stroke (%)", 10}}, 4,
     [](const double* v) { double mkg = v[0], r = v[1], n = v[2], d = v[3]; double I = mkg * r * r, w = 2 * PI * n / 60, E = 0.5 * I * w * w, w2 = w * (1 - d / 100);
        return Str::f("I ≈ %s kg·m² (rim only)\nStored energy = %s kJ\nEnergy released = %s kJ", S(F(I, 1)), S(F(E / 1000, 2)), S(F((E - 0.5 * I * w2 * w2) / 1000, 2))); }},
    {"bed_cap", "Bed-flow capacity (belt / apron / drag chain)", {{"Bed width b (m)", 1.0}, {"Mean bed depth h (m)", 0.15}, {"Speed v (m/s)", 2.0}, {"Bulk density ρ (kg/m³)", 900}, {"Fill / efficiency factor φ", 0.9}}, 5,
     [](const double* v) { double qv = v[0] * v[1] * v[2] * v[4] * 3600;
        return Str::f("Volume flow = %s m³/h\nMass flow = %s t/h\nQ = 3600 · b · h · v · φ · ρ (use the loaded cross-section for troughed belts)", S(F(qv, 1)), S(F(qv * v[3] / 1000, 1))); }},
    {"belt_power", "Belt conveyor power (simplified ISO 5048 / DIN 22101)", {{"Capacity Q (t/h)", 500}, {"Belt speed v (m/s)", 2.5}, {"Length L (m)", 200}, {"Lift H (m, + up)", 10}, {"Moving mass belt + idlers (kg/m)", 60}, {"Artificial friction f", 0.02}, {"Coefficient C (secondary resistances)", 1.45}, {"Drive efficiency η (%)", 90}}, 8,
     [](const double* v) { double Q = v[0], vv = v[1], L = v[2], H = v[3], mm = v[4], f = v[5], C = v[6], e = v[7]; double ml = Q / (3.6 * vv), FU = C * f * L * G * (mm + ml) + H * G * ml, P = FU * vv / 1000;
        return Str::f("Load per metre m'L = %s kg/m\nPeripheral force F_U ≈ %s kN\nPower at pulley ≈ %s kW\nMotor power ≈ %s kW (+ margin)\nC ≈ 1.9 at 80 m … 1.45 at 200 m … 1.1 at 2 km (approx.); f ≈ 0.02 typical.", S(F(ml, 1)), S(F(FU / 1000, 1)), S(F(P, 1)), S(F(P / (e / 100), 1))); }},
    {"screw_cap", "Screw conveyor / feeder capacity", {{"Screw diameter D (mm)", 300}, {"Shaft (pipe) diameter d (mm)", 89}, {"Pitch p (mm)", 300}, {"Speed n (rpm)", 60}, {"Trough loading φ (feeder ≈ 1, conveyor 0.15–0.45)", 0.3}, {"Bulk density ρ (kg/m³)", 800}}, 6,
     [](const double* v) { double D = v[0], d = v[1], p = v[2], n = v[3], f = v[4], r = v[5]; double qv = 60 * PI / 4 * (pow(D / 1000, 2) - pow(d / 1000, 2)) * p / 1000 * n * f;
        return Str::f("Volume flow = %s m³/h\nMass flow = %s t/h\nQ = 60 · π/4 · (D² − d²) · p · n · φ · ρ", S(F(qv, 2)), S(F(qv * r / 1000, 2))); }},
    {"bond", "Crushing/grinding energy (Bond) & reduction ratio", {{"Feed size F80 (mm)", 150}, {"Product size P80 (mm)", 25}, {"Bond work index Wi (kWh/t)", 14}, {"Throughput (t/h)", 300}}, 4,
     [](const double* v) { double Fz = v[0], Pp = v[1], Wi = v[2], T = v[3]; double W = 10 * Wi * (1 / sqrt(Pp * 1000) - 1 / sqrt(Fz * 1000));
        return Str::f("Reduction ratio F80/P80 = %s : 1\nSpecific energy W = %s kWh/t\nPower ≈ %s kW (net, before machine-specific factors)\nW = 10 · Wi · (1/√P80 − 1/√F80), sizes in µm.", S(F(Fz / Pp, 1)), S(F(W, 2)), S(F(W * T, 0))); }},
    {"hoist", "Hoist power & rope force", {{"Load incl. hook block (t)", 10}, {"Hoisting speed (m/min)", 5}, {"Falls of rope (parts of line)", 4}, {"Mechanism efficiency η (%)", 85}}, 4,
     [](const double* v) { double m = v[0], vv = v[1], n = v[2], e = v[3]; double W = m * 1000 * G, P = W * vv / 60 / (e / 100) / 1000;
        return Str::f("Load weight = %s kN\nMotor power ≈ %s kW\nRope force per fall ≈ %s kN (ideal; add sheave losses)\nSelect rope MBF ≥ rope force × design factor per the crane standard.", S(F(W / 1000, 1)), S(F(P, 1)), S(F(W / n / 1000, 1))); }},
    {"hyd_cyl", "Hydraulic cylinder force & speed", {{"Bore D (mm)", 100}, {"Rod d (mm)", 56}, {"Pressure p (bar)", 160}, {"Pump flow Q (L/min)", 60}}, 4,
     [](const double* v) { double D = v[0], d = v[1], p = v[2], Q = v[3]; double A = PI / 4 * pow(D / 1000, 2), Ar = A - PI / 4 * pow(d / 1000, 2), q = Q / 60000;
        return Str::f("Bore area = %s cm²   Annulus = %s cm²\nPush (extend) F = %s kN\nPull (retract) F = %s kN\nExtend speed = %s m/s   Retract speed = %s m/s\nHydraulic power = %s kW",
            S(F(A * 1e4, 1)), S(F(Ar * 1e4, 1)), S(F(p * 1e5 * A / 1000, 1)), S(F(p * 1e5 * Ar / 1000, 1)), S(F(q / A, 3)), S(F(q / Ar, 3)), S(F(p * Q / 600, 1))); }},
    {"accum", "Accumulator usable volume (gas law)", {{"Nominal gas volume V0 (L)", 10}, {"Pre-charge p0 (bar g)", 90}, {"Min. system pressure p1 (bar g)", 100}, {"Max. system pressure p2 (bar g)", 200}, {"Polytropic exponent n (1 isothermal, 1.4 adiabatic)", 1.4}}, 5,
     [](const double* v) { double V = v[0], p0 = v[1], p1 = v[2], p2 = v[3], n = v[4]; auto a = [](double x) { return x + 1.013; };
        double dV = V * (pow(a(p0) / a(p1), 1 / n) - pow(a(p0) / a(p2), 1 / n));
        return Str::f("Usable volume ΔV = %s L\nPre-charge / p1 = %s %%  (bladder: ≈ 90 %% typical)\nCompression ratio p2/p0 = %s  (check maker limit, often ≤ 4 for bladders)\nAbsolute pressures used in the gas law.", S(F(dV, 2)), S(F(p0 / p1 * 100, 0)), S(F(a(p2) / a(p0), 2))); }},
    {"trommel", "Drum / trommel critical speed", {{"Drum inside diameter D (m)", 2.0}, {"Operating speed (rpm)", 10}}, 2,
     [](const double* v) { double nc = 42.3 / sqrt(v[0]);
        return Str::f("Critical speed n_c = %s rpm\nOperating = %s %% of critical\nTrommels ≈ 30–40 %%, ball/rod mills ≈ 65–80 %% of critical.", S(F(nc, 1)), S(F(v[1] / nc * 100, 0))); }},
    {"flash", "Flash fraction (flash steam / flash evaporation)", {{"Liquid inlet temperature T1 (°C)", 180}, {"Saturation temperature after pressure drop T2 (°C)", 100}, {"Liquid cp (kJ/kg·K)", 4.2}, {"Latent heat h_fg at T2 (kJ/kg)", 2257}, {"Liquid flow (kg/h)", 10000}}, 5,
     [](const double* v) { double x = fmax(0, v[2] * (v[0] - v[1]) / v[3]), m = v[4];
        return Str::f("Flash fraction ≈ %s %%\nVapour ≈ %s kg/h   Liquid ≈ %s kg/h\nx ≈ cp·(T1 − T2)/h_fg (use steam tables for accuracy)", S(F(x * 100, 1)), S(F(x * m, 0)), S(F((1 - x) * m, 0))); }},
    {"dryer_load", "Dryer evaporation load & heat", {{"Wet feed rate (kg/h)", 1000}, {"Initial moisture (% wet basis)", 40}, {"Final moisture (% wet basis)", 5}, {"Heat per kg evaporated incl. losses (kJ/kg)", 3500}}, 4,
     [](const double* v) { double Fd = v[0], x1 = v[1], x2 = v[2], q = v[3]; double dry = Fd * (1 - x1 / 100), prod = dry / (1 - x2 / 100), W = Fd - prod;
        return Str::f("Dry solids = %s kg/h\nProduct = %s kg/h\nWater evaporated = %s kg/h\nHeat ≈ %s kW  (convective dryers often ~ 3 000 – 6 000 kJ/kg water)", S(F(dry, 0)), S(F(prod, 0)), S(F(W, 0)), S(F(W * q / 3600, 0))); }},
    {"excess_air", "Excess air from flue-gas O₂", {{"O₂ in dry flue gas (%)", 3}}, 1,
     [](const double* v) { double o = v[0];
        return Str::f("Excess air ≈ %s %%\nλ (air ratio) ≈ %s\nApproximation for complete combustion; typical gas ~ 10–20 %%, oil ~ 15–25 %%, coal ~ 20–40 %%.", S(F(o / (20.9 - o) * 100, 0)), S(F(20.9 / (20.9 - o), 2))); }},
    {"boiler_eff", "Boiler efficiency (direct method)", {{"Steam flow (kg/h)", 10000}, {"Steam enthalpy (kJ/kg)", 2780}, {"Feedwater enthalpy (kJ/kg)", 440}, {"Fuel flow (kg/h or Nm³/h)", 760}, {"Fuel calorific value (kJ/kg or kJ/Nm³)", 35800}}, 5,
     [](const double* v) { double Q = v[0] * (v[1] - v[2]), I = v[3] * v[4];
        return Str::f("Heat to steam = %s kW\nFuel input = %s kW\nEfficiency ≈ %s %%  (state GCV or NCV basis)", S(F(Q / 3600, 0)), S(F(I / 3600, 0)), S(F(Q / I * 100, 1))); }},
    {"ct", "Cooling tower range, approach, make-up", {{"Circulating flow (m³/h)", 1000}, {"Hot water in (°C)", 38}, {"Cold water out (°C)", 30}, {"Air wet-bulb (°C)", 26}, {"Cycles of concentration", 4}}, 5,
     [](const double* v) { double Q = v[0], th = v[1], tc = v[2], wb = v[3], coc = v[4]; double R = th - tc, E = 0.00153 * Q * R, B = E / (coc - 1);
        return Str::f("Range = %s °C   Approach = %s °C\nHeat rejected ≈ %s MW\nEvaporation ≈ %s m³/h (≈ 0.15 %%/°C rule)\nBlowdown ≈ %s m³/h   Make-up ≈ %s m³/h (+ drift)",
            S(F(R, 1)), S(F(tc - wb, 1)), S(F(Q * 1000 / 3600 * 4.18 * R / 1000, 2)), S(F(E, 1)), S(F(B, 1)), S(F(E + B, 1))); }},
    {"stokes", "Stokes settling / rise velocity", {{"Droplet/particle diameter (µm)", 100}, {"Particle/droplet density (kg/m³)", 850}, {"Continuous-phase density (kg/m³)", 1000}, {"Continuous-phase viscosity (cP)", 1.0}}, 4,
     [](const double* v) { double D = v[0] * 1e-6, rp = v[1], rc = v[2], mu = v[3]; double vv = G * D * D * (rc - rp) / (18 * mu / 1000);
        return Str::f("Velocity = %s mm/s  (%s)\n= %s m/h\nRe = %s (Stokes valid for Re < ~1)", S(F(fabs(vv) * 1000, 3)), vv > 0 ? "rises" : "settles", S(F(fabs(vv) * 3600, 2)), S(F(rc * fabs(vv) * D / (mu / 1000), 3))); }},
    {"gforce", "Centrifuge g-force", {{"Bowl/basket inner radius r (mm)", 250}, {"Speed n (rpm)", 3000}}, 2,
     [](const double* v) { double w = 2 * PI * v[1] / 60, g = w * w * v[0] / 1000 / G;
        return Str::f("Relative centrifugal force ≈ %s × g\nPeripheral speed = %s m/s\nRCF = ω²r / g", S(F(g, 0)), S(F(w * v[0] / 1000, 1))); }},
    {"membrane", "Membrane flux, recovery & rejection", {{"Feed flow (m³/h)", 100}, {"Permeate flow (m³/h)", 80}, {"Membrane area (m²)", 4000}, {"Feed concentration (mg/L)", 500}, {"Permeate concentration (mg/L)", 25}}, 5,
     [](const double* v) { double Qf = v[0], Qp = v[1], A = v[2], cf = v[3], cp = v[4];
        return Str::f("Flux = %s L/m²·h (LMH)\nRecovery = %s %%\nRejection = %s %%\nConcentrate = %s m³/h at ≈ %s mg/L", S(F(Qp * 1000 / A, 1)), S(F(Qp / Qf * 100, 1)), S(F((1 - cp / cf) * 100, 1)), S(F(Qf - Qp, 1)), S(F((Qf * cf - Qp * cp) / (Qf - Qp), 0))); }},
    {"adsorber", "Adsorber bed life (simplified)", {{"Bed mass (kg)", 2000}, {"Working capacity (kg adsorbate per 100 kg adsorbent)", 8}, {"Flow (m³/h, actual)", 500}, {"Inlet contaminant (g/m³)", 5}}, 4,
     [](const double* v) { double load = v[2] * v[3] / 1000, cap_kg = v[0] * v[1] / 100;
        return Str::f("Contaminant load = %s kg/h\nUsable capacity ≈ %s kg\nTime to breakthrough ≈ %s h\nUse dynamic (working) capacity incl. MTZ and ageing, not equilibrium capacity.", S(F(load, 2)), S(F(cap_kg, 0)), S(F(cap_kg / load, 1))); }},
    {"bayer_yield", "Precipitation yield (Bayer A/C)", {{"Caustic C (g/L as Na₂CO₃)", 230}, {"A/C ratio pregnant liquor", 0.70}, {"A/C ratio spent liquor", 0.40}, {"Liquor flow (m³/h)", 1500}}, 4,
     [](const double* v) { double y = v[0] * (v[1] - v[2]), al = y * v[3] / 1000;
        return Str::f("Yield = %s g/L Al₂O₃\nAlumina = %s t/h  (%s t/d)\nHydrate Al(OH)₃ ≈ %s t/h (×156/102)\nA = Al₂O₃, C = caustic as Na₂CO₃ (refinery convention).", S(F(y, 1)), S(F(al, 1)), S(F(al * 24, 0)), S(F(al * 1.53, 1))); }},
    {"thickener", "Thickener area from solids flux", {{"Solids feed (t/h)", 200}, {"Design solids flux (t/m²·d)", 15}}, 2,
     [](const double* v) { double A = v[0] * 24 / v[1];
        return Str::f("Required area ≈ %s m²\nDiameter ≈ %s m (single unit)\nUse test-work flux with safety factor; high-rate thickeners with flocculant allow higher flux.", S(F(A, 0)), S(F(sqrt(4 * A / PI), 1))); }},
    {"slurry", "Slurry solids % from density", {{"Slurry density (kg/m³)", 1450}, {"Liquid density (kg/m³)", 1250}, {"Solids density (kg/m³)", 2400}}, 3,
     [](const double* v) { double m = v[0], l = v[1], sd = v[2]; double cw = sd * (m - l) / (m * (sd - l)), cv = (m - l) / (sd - l);
        return Str::f("Solids by weight Cw = %s %%\nSolids by volume Cv = %s %%\nSolids concentration = %s kg/m³ slurry", S(F(cw * 100, 1)), S(F(cv * 100, 1)), S(F(cw * m, 0))); }},
    {"chlor", "Chlorine dose & C·t", {{"Water flow (m³/h)", 500}, {"Chlorine dose (mg/L)", 2.0}, {"Free residual after contact (mg/L)", 0.5}, {"Contact tank volume (m³)", 300}, {"Baffle factor T10/T (0.1 unbaffled … 0.7 serpentine)", 0.5}}, 5,
     [](const double* v) { double Q = v[0], d = v[1], c = v[2], V = v[3], bf = v[4]; double kg = Q * d * 24 / 1000, t = V / Q * 60, t10 = t * bf;
        return Str::f("Chlorine use ≈ %s kg/day\nMean contact time = %s min · effective T10 ≈ %s min\nC·t ≈ %s mg·min/L\nCompare with required C·t for the target organism, pH and temperature (regulatory tables).", S(F(kg, 1)), S(F(t, 1)), S(F(t10, 1)), S(F(c * t10, 1))); }},
    {"g_mix", "Mixing power from velocity gradient G", {{"Velocity gradient G (s⁻¹)", 50}, {"Basin volume V (m³)", 200}, {"Water viscosity μ (cP; ≈ 1.0 at 20 °C)", 1.0}, {"Detention time t (min)", 20}}, 4,
     [](const double* v) { double g = v[0], V = v[1], mu = v[2], t = v[3]; double P = g * g * mu / 1000 * V;
        return Str::f("Power to water P = G²·μ·V ≈ %s kW\nG·t = %s (flocculation ≈ 10⁴ – 10⁵)\nRapid mix G ≈ 300–1000 s⁻¹ (10–60 s); flocculation G ≈ 10–70 s⁻¹.", S(F(P / 1000, 2)), S(F(g * t * 60, 0))); }},
    {"softener", "Ion-exchange resin volume & regenerant", {{"Flow (m³/h)", 20}, {"Ionic load / hardness (mg/L as CaCO₃)", 250}, {"Run length between regenerations (h)", 12}, {"Operating capacity (g CaCO₃ per L resin)", 45}, {"Regenerant dose (g per L resin)", 150}}, 5,
     [](const double* v) { double load = v[0] * v[1] * v[2], L = load / v[3];
        return Str::f("Load per run = %s kg as CaCO₃\nResin volume ≈ %s L (%s m³)\nRegenerant per regeneration ≈ %s kg\nUse resin-maker capacity curves (depends on regenerant level, water and temperature).", S(F(load / 1000, 1)), S(F(L, 0)), S(F(L / 1000, 2)), S(F(L * v[4] / 1000, 0))); }},
    {"receiver", "Air receiver size for a demand event", {{"Air demand to cover (free air, m³/min)", 10}, {"Duration (min)", 1}, {"Atmospheric pressure (bar a)", 1.013}, {"Start pressure (bar g)", 7.5}, {"Minimum allowed pressure (bar g)", 6.0}}, 5,
     [](const double* v) { double Q = v[0], t = v[1], pa = v[2], p1 = v[3], p2 = v[4]; double V = t * Q * pa / (p1 - p2);
        return Str::f("Receiver volume V = t·Q·p₀/(p₁ − p₂) ≈ %s m³\nStored usable free air ≈ %s m³\nRules of thumb vary; check compressor control band and cycling.", S(F(V, 2)), S(F(V * (p1 - p2) / pa, 1))); }},
    {"bearing_life", "Rolling bearing basic rating life (ISO 281)", {{"Dynamic load rating C (kN)", 50}, {"Equivalent dynamic load P (kN)", 5}, {"Speed n (rpm)", 1500}, {"Bearing type: 1 = ball, 2 = roller", 1}}, 4,
     [](const double* v) { double C = v[0], Pd = v[1], n = v[2]; double p = floor(v[3] + 0.5) == 2 ? 10.0 / 3 : 3, L = pow(C / Pd, p);
        return Str::f("L10 = (C/P)^%s = %s million revolutions\nL10h = %s hours at %s rpm\n90 %% of bearings reach this life; contamination and lubrication factors (a_ISO) can raise or cut it greatly.", p == 3 ? "3" : "10/3", S(F(L, 0)), S(F(L * 1e6 / (60 * n), 0)), S(N(n))); }},
    {"balance_grade", "Permissible residual unbalance (ISO 21940-11)", {{"Balance grade G (mm/s), e.g. 6.3 or 2.5", 6.3}, {"Rotor mass (kg)", 50}, {"Maximum service speed (rpm)", 1500}, {"Number of correction planes", 2}}, 4,
     [](const double* v) { double Gg = v[0], m = v[1], n = v[2], pl = v[3]; double w = 2 * PI * n / 60, e = Gg / w * 1000, U = e * m;
        return Str::f("Permissible eccentricity e_per = G/ω = %s µm\nU_per = %s g·mm total  (≈ %s g·mm per plane, symmetric rotor)\ne.g. at radius 100 mm: %s g total", S(F(e, 1)), S(F(U, 0)), S(F(U / fmax(1, floor(pl + 0.5)), 0)), S(F(U / 100, 1))); }},
    {"regrease", "Bearing relubrication quantity", {{"Bearing outside diameter D (mm)", 160}, {"Bearing width B (mm)", 40}}, 2,
     [](const double* v) { return Str::f("Replenishment G ≈ 0.005 × D × B = %s g per relubrication\nInitial fill: bearing full, housing ≈ 30–50 %%. Interval from the maker's chart (n·dm, temperature, contamination).", S(F(0.005 * v[0] * v[1], 1))); }},
    {"alignment", "Rim & face readings → offset and angularity", {{"Rim reading at 12 o'clock (mm, zeroed)", 0}, {"Rim reading at 6 o'clock (mm)", -0.24}, {"Face reading at 12 (mm, zeroed)", 0}, {"Face reading at 6 (mm)", 0.06}, {"Face reading diameter (mm)", 150}}, 5,
     [](const double* v) { double off = (v[1] - v[0]) / 2, ang = (v[3] - v[2]) / v[4] * 100;
        return Str::f("Vertical offset at the indicator plane = %s mm (½ of rim change; sign = which way the measured shaft sits)\nVertical angularity = %s mm per 100 mm\nRepeat at 3 & 9 o'clock for horizontal; then calculate foot moves.", S(F(off, 3)), S(F(ang, 3))); }},
    {"psv_gas", "PSV required area — gas/vapour, critical flow (API 520 simplified)", {{"Relieving rate W (kg/h)", 10000}, {"Relieving pressure P1 (kPa abs) = set + overpressure + atm", 1200}, {"Relieving temperature (K)", 400}, {"Molecular weight M", 30}, {"Ratio of specific heats k", 1.3}, {"Compressibility Z", 0.95}, {"Discharge coefficient Kd", 0.975}}, 7,
     [](const double* v) { double W = v[0], P1 = v[1], T = v[2], Mw = v[3], k = v[4], Z = v[5], Kd = v[6]; double C = 0.03948 * sqrt(k * pow(2 / (k + 1), (k + 1) / (k - 1))), A = W / (C * Kd * P1) * sqrt(T * Z / Mw);
        return Str::f("C = %s\nRequired effective area A ≈ %s mm²\nSelect the next larger API 526 orifice (e.g. D 71, E 126, F 198, G 325, H 506, J 830, K 1186, L 1841, M 2323, N 2800, P 4116, Q 7129, R 10323, T 16774 mm²). Kb, Kc = 1 assumed — verify with API 520.", S(F(C, 4)), S(F(A, 0))); }},
    {"flare_rad", "Flare radiation at grade (point-source estimate)", {{"Flare gas rate (kg/s)", 20}, {"Net heating value (MJ/kg)", 46}, {"Fraction of heat radiated F", 0.2}, {"Transmissivity τ", 1.0}, {"Distance from flame centre (m)", 60}}, 5,
     [](const double* v) { double w = v[0], lhv = v[1], Fr = v[2], tau = v[3], D = v[4]; double q = tau * Fr * w * lhv * 1e3 / (4 * PI * D * D);
        return Str::f("Radiation ≈ %s kW/m² at %s m\nAPI 521 guidance (verify): ≈ 1.58 kW/m² continuous exposure, ≈ 4.73 kW/m² for a few minutes with protection, ≈ 6.31 kW/m² brief escape.\nDistance for 1.58 kW/m²: ≈ %s m from flame centre.", S(F(q, 2)), S(N(D)), S(F(sqrt(tau * Fr * w * lhv * 1e3 / (4 * PI * 1.58)), 0))); }},
    {"bag_area", "Baghouse cloth area & bag count", {{"Gas flow (m³/min, actual)", 1500}, {"Air-to-cloth ratio (m/min)", 1.2}, {"Bag diameter (mm)", 150}, {"Bag length (m)", 6}}, 4,
     [](const double* v) { double A = v[0] / v[1], a = PI * v[2] / 1000 * v[3];
        return Str::f("Net cloth area ≈ %s m²\nArea per bag ≈ %s m² → ≈ %s bags (+ spare compartment if cleaned off-line)", S(F(A, 0)), S(F(a, 2)), S(N(ceil(A / a)))); }},
    {"dilution", "Ventilation: air changes & gas dilution", {{"Room volume (m³)", 300}, {"Ventilation rate (m³/h)", 3600}, {"Gas leak rate (m³/h, as gas)", 0.5}, {"Gas LEL (vol %)", 5.0}}, 4,
     [](const double* v) { double V = v[0], Q = v[1], g = v[2], lel = v[3]; double ach = Q / V, c = g / (Q + g) * 100;
        return Str::f("Air changes = %s per hour\nSteady-state concentration ≈ %s vol %% = %s %% LEL (perfect mixing)\nTime to purge from C0 to 1 %% of C0 ≈ %s min. Real rooms need a mixing / safety factor.", S(F(ach, 1)), S(F(c, 3)), S(F(c / lel * 100, 1)), S(F(log(100) / ach * 60, 0))); }},
    {"pump_power", "Pump power", {{"Flow Q (m³/h)", 100}, {"Head H (m)", 50}, {"Density ρ (kg/m³)", 1000}, {"Pump efficiency η (%)", 75}, {"Motor efficiency (%)", 94}}, 5,
     [](const double* v) { double ph = v[2] * G * v[0] / 3600 * v[1] / 1000, ps = ph / (v[3] / 100);
        return Str::f("Hydraulic power  %s kW\nShaft power      %s kW\nElectrical input %s kW", S(F(ph, 2)), S(F(ps, 2)), S(F(ps / (v[4] / 100), 2))); }},
    {"affinity", "Affinity laws (speed change)", {{"Speed n1 (rpm)", 2950}, {"Speed n2 (rpm)", 1475}, {"Flow Q1 (m³/h)", 100}, {"Head H1 (m)", 50}, {"Power P1 (kW)", 18}}, 5,
     [](const double* v) { double k = v[1] / v[0];
        return Str::f("Q2 = %s m³/h\nH2 = %s m\nP2 = %s kW\n(valid for the same impeller; approximate for large changes)", S(F(v[2] * k, 1)), S(F(v[3] * k * k, 1)), S(F(v[4] * pow(k, 3), 2))); }},
    {"npsha", "NPSH available", {{"Pressure on liquid surface (kPa abs)", 101.3}, {"Vapour pressure (kPa abs)", 2.34}, {"Density ρ (kg/m³)", 998}, {"Static height of liquid above pump centreline z (m, negative = lift)", 2}, {"Suction losses hf (m)", 0.8}, {"NPSHr of pump (m)", 3}}, 6,
     [](const double* v) { double a = (v[0] - v[1]) * 1000 / (v[2] * G) + v[3] - v[4], req = v[5];
        return Str::f("NPSHa = %s m\nMargin = %s m  (ratio %s)\nCheck margin against ANSI/HI 9.6.1 for the application.", S(F(a, 2)), S(F(a - req, 2)), S(F(a / req, 2))); }},
    {"ns", "Specific speed", {{"Speed n (rpm)", 1480}, {"Flow per eye Q (m³/h)", 500}, {"Head per stage H (m)", 40}}, 3,
     [](const double* v) { double n = v[0], Q = v[1], H = v[2]; double nq = n * sqrt(Q / 3600) / pow(H, 0.75), us = n * sqrt(Q * 4.4029) / pow(H * 3.2808, 0.75);
        return Str::f("n_q (metric, m³/s, m) = %s\nN_s (US, gpm, ft) = %s\n< ~1,500 radial · 4,000–9,000 mixed · > 9,000 axial (US units, approx.)", S(F(nq, 1)), S(F(us, 0))); }},
    {"valve", "Valve flow coefficient (liquids)", {{"Kv (m³/h at 1 bar)", 40}, {"Pressure drop ΔP (bar)", 0.5}, {"Specific gravity SG", 1.0}}, 3,
     [](const double* v) { return Str::f("Flow Q = %s m³/h\nCv = %s (US gpm at 1 psi)\nNon-choked, turbulent liquid flow (IEC 60534-2-1 simplified).", S(F(v[0] * sqrt(v[1] / v[2]), 2)), S(F(v[0] * 1.156, 1))); }},
    {"dpmeter", "Differential-pressure flowmeter", {{"Pipe ID D (mm)", 100}, {"Beta ratio β = d/D", 0.6}, {"Discharge coefficient C", 0.605}, {"ΔP (kPa)", 25}, {"Density ρ (kg/m³)", 998}}, 5,
     [](const double* v) { double D = v[0], b = v[1], C = v[2], dp = v[3], r = v[4]; double d = D / 1000 * b, q = C / sqrt(1 - pow(b, 4)) * PI / 4 * d * d * sqrt(2 * dp * 1000 / r);
        return Str::f("Volume flow ≈ %s m³/h\nMass flow ≈ %s t/h\nTypical C: orifice ~0.60, nozzle ~0.98, venturi ~0.985 (ISO 5167; liquid, ε = 1).", S(F(q * 3600, 2)), S(F(q * r * 3600 / 1000, 2))); }},
    {"pipe", "Pipe velocity & friction loss", {{"Flow Q (m³/h)", 100}, {"Pipe ID (mm)", 102}, {"Length L (m)", 100}, {"Roughness ε (mm)", 0.045}, {"Density ρ (kg/m³)", 998}, {"Viscosity μ (cP)", 1.0}}, 6,
     [](const double* v) { double Q = v[0], D = v[1], L = v[2], e = v[3], r = v[4], mu = v[5]; double d = D / 1000, A = PI * d * d / 4, vv = Q / 3600 / A, Re = r * vv * d / (mu / 1000);
        double f = Re < 2300 ? 64 / Re : 0.25 / pow(log10(e / 1000 / (3.7 * d) + 5.74 / pow(Re, 0.9)), 2), hf = f * L / d * vv * vv / (2 * G);
        return Str::f("Velocity v = %s m/s\nReynolds Re = %s (%s)\nFriction factor f = %s (Swamee–Jain)\nHead loss = %s m  ·  ΔP = %s bar", S(F(vv, 2)), S(F(Re, 0)), Re < 2300 ? "laminar" : "turbulent", S(F(f, 4)), S(F(hf, 2)), S(F(hf * r * G / 1e5, 3))); }},
    {"insul", "Insulated pipe heat loss (per metre)", {{"Pipe temperature (°C)", 180}, {"Ambient (°C)", 25}, {"Pipe OD (mm)", 114.3}, {"Insulation thickness (mm)", 50}, {"Insulation k (W/m·K)", 0.045}, {"Outer surface coefficient h (W/m²·K)", 10}}, 6,
     [](const double* v) { double Tp = v[0], Ta = v[1], OD = v[2], t = v[3], k = v[4], h = v[5]; double r1 = OD / 2000, r2 = r1 + t / 1000;
        double q = (Tp - Ta) / (log(r2 / r1) / (2 * PI * k) + 1 / (2 * PI * r2 * h)), qb = 2 * PI * r1 * h * (Tp - Ta);
        return Str::f("Insulated loss ≈ %s W/m\nSurface temperature ≈ %s °C\nBare pipe (same h) ≈ %s W/m  →  saving %s %%\n(simplified: combined convection/radiation in h)", S(F(q, 1)), S(F(Ta + q / (2 * PI * r2 * h), 1)), S(F(qb, 0)), S(F(100 * (1 - q / qb), 0))); }},
    {"units", "Unit converter", {{"Value", 1}, {"Quantity: 1 pressure, 2 flow, 3 power, 4 temperature, 5 length", 1}}, 2,
     [](const double* v) { double x = v[0]; double q = floor(v[1] + 0.5); Str s = N(x);
        if (q == 1) return Str::f("%s bar = %s kPa = %s psi = %s mH₂O = %s atm", S(s), S(F(x * 100, 3)), S(F(x * 14.5038, 3)), S(F(x * 10.197, 3)), S(F(x / 1.01325, 4)));
        if (q == 2) return Str::f("%s m³/h = %s L/s = %s L/min = %s US gpm", S(s), S(F(x / 3.6, 3)), S(F(x * 16.667, 2)), S(F(x * 4.4029, 2)));
        if (q == 3) return Str::f("%s kW = %s hp", S(s), S(F(x * 1.341, 3)));
        if (q == 4) return Str::f("%s °C = %s °F = %s K", S(s), S(F(x * 9 / 5 + 32, 2)), S(F(x + 273.15, 2)));
        if (q == 5) return Str::f("%s mm = %s in", S(s), S(F(x / 25.4, 4)));
        return Str("Choose 1–5"); }},
};
const int NCALCS = (int)(sizeof(CALCS) / sizeof(CALCS[0]));

const Calc* calc_find(const char* key) { for (int i = 0; i < NCALCS; i++) if (streq(CALCS[i].key, key)) return &CALCS[i]; return nullptr; }

static const struct { const char* fam; const char* keys[12]; } FAMILY[] = {
    {"safety_environmental", {"psv_gas", "flare_rad", "bag_area", "dilution", "flash", "stokes", "pump_power", "units"}},
    {"mechanical_components", {"bearing_life", "balance_grade", "regrease", "alignment", "drive_ratio", "shaft_power", "sync_speed", "pump_power", "affinity", "units"}},
    {"water_utilities", {"chlor", "g_mix", "softener", "receiver", "ct", "flash", "pump_power", "npsha", "stokes", "pipe", "units"}},
    {"alumina_refinery", {"bayer_yield", "thickener", "slurry", "bond", "trommel", "stokes", "gforce", "flash", "bed_cap", "units"}},
    {"filtration_separation", {"stokes", "gforce", "membrane", "adsorber", "souders", "units"}},
    {"thermal_process", {"lmtd", "flash", "dryer_load", "excess_air", "boiler_eff", "ct", "shell_t", "units"}},
    {"material_handling", {"bed_cap", "belt_power", "screw_cap", "bond", "hoist", "hyd_cyl", "accum", "trommel", "units"}},
    {"static_equipment", {"shell_t", "lmtd", "hvol", "souders", "units"}},
    {"valves_piping", {"valve", "dpmeter", "pipe", "insul", "units"}},
    {"rotating_machinery", {"shaft_power", "sync_speed", "compressor_power", "affinity", "drive_ratio", "flywheel", "units"}},
    {"default", {"pump_power", "affinity", "npsha", "ns", "pipe", "valve", "units"}},
};

// firstBy: [regex over the module id, preferred calculators]; first matching rule wins (as in the web)
static const struct { const char* re; const char* keys[3]; } FIRST_BY[] = {
    {"pressure_relief|knockout", {"psv_gas", "stokes"}}, {"flare_stack", {"flare_rad"}}, {"baghouse|dry_scrubber", {"bag_area"}}, {"ventilation|fire_and_gas", {"dilution"}},
    {"blowdown", {"flash"}}, {"grease|centralized_lub", {"regrease", "bearing_life"}}, {"bearing_housing|thrust_bearing|journal_bearing", {"bearing_life"}},
    {"balancing|impeller|^rotor$", {"balance_grade"}}, {"alignment", {"alignment"}}, {"stator", {"sync_speed"}}, {"gear_assembly|coupling|universal_joint", {"drive_ratio", "shaft_power"}},
    {"chlorination|ozonation|uv_disinfection", {"chlor"}}, {"flash_mixer|flocculation|clariflocculator", {"g_mix"}}, {"lamella", {"stokes", "g_mix"}},
    {"softener|demineral|mixed_bed|degasser_tower", {"softener"}}, {"air_receiver|instrument_air|nitrogen_generation", {"receiver"}}, {"cooling_tower", {"ct"}},
    {"condensate_recovery|steam_distribution", {"flash", "pipe"}}, {"sewage_lift|firewater|chemical_injection", {"pump_power", "npsha"}},
    {"hydraulic_(cylinder|power|control)", {"hyd_cyl", "accum"}}, {"accumulator", {"accum", "hyd_cyl"}}, {"crusher", {"bond"}}, {"trommel", {"trommel"}},
    {"screw_(feeder|conveyor)", {"screw_cap"}}, {"crane|hoist|winch|jack", {"hoist"}}, {"conveyor|stacker|reclaimer|tripper|feeder|excavator", {"bed_cap", "belt_power"}},
    {"flash_evap|forced_circ|multiple_effect|falling_film", {"flash"}}, {"dryer", {"dryer_load"}},
    {"furnace|combustor|oxidizer|incinerator|steam_generator|economizer|superheater|air_preheater", {"excess_air", "boiler_eff"}}, {"cooling_water|quench", {"ct"}},
    {"centrifuge", {"gforce"}}, {"filtration_system|membrane", {"membrane"}}, {"adsorber|desiccant|dehydration", {"adsorber"}}, {"precipitation|seed_class", {"bayer_yield"}},
    {"washer|settling|clarifier", {"thickener"}}, {"grinding_mill", {"bond"}}, {"washing_drum", {"trommel"}}, {"mixing_tank|digestion|desilication", {"slurry"}},
};

// tiny matcher for the patterns above: top-level alternation, one (a|b) group, ^ and $ anchors
static bool alt_match(const char* id, const char* a, int n) {
    const char* lp = (const char*)memchr(a, '(', (size_t)n);
    if (lp) {
        const char* rp = (const char*)memchr(lp, ')', (size_t)(a + n - lp));
        if (!rp) return false;
        const char* s = lp + 1;
        while (s < rp) {
            const char* e = s; while (e < rp && *e != '|') e++;
            char buf[160]; int k = 0;
            for (const char* q = a; q < lp && k < 150; q++) buf[k++] = *q;
            for (const char* q = s; q < e && k < 150; q++) buf[k++] = *q;
            for (const char* q = rp + 1; q < a + n && k < 150; q++) buf[k++] = *q;
            if (alt_match(id, buf, k)) return true;
            s = e + 1;
        }
        return false;
    }
    bool hb = n && a[0] == '^', he = n && a[n - 1] == '$';
    const char* s = a + (hb ? 1 : 0); int m = n - (hb ? 1 : 0) - (he ? 1 : 0);
    int L = (int)strlen(id);
    if (m > L) return false;
    if (hb && he) return m == L && !memcmp(id, s, (size_t)m);
    if (hb) return !memcmp(id, s, (size_t)m);
    if (he) return !memcmp(id + L - m, s, (size_t)m);
    for (int i = 0; i + m <= L; i++) if (!memcmp(id + i, s, (size_t)m)) return true;
    return false;
}
static bool re_test(const char* re, const char* id) {
    int depth = 0; const char* st = re;
    for (const char* p = re;; p++) {
        if (*p == '(') depth++; else if (*p == ')') depth--;
        if ((*p == '|' && depth == 0) || !*p) { if (alt_match(id, st, (int)(p - st))) return true; if (!*p) break; st = p + 1; }
    }
    return false;
}

void calc_keys_for(const char* id, const char* fam, Vec<const char*>& out) {
    out.clear();
    const char* const* keys0 = nullptr;
    for (auto& f : FAMILY) if (streq(f.fam, fam)) keys0 = f.keys;
    if (!keys0) for (auto& f : FAMILY) if (streq(f.fam, "default")) keys0 = f.keys;
    const char* const* pref = nullptr;
    for (auto& r : FIRST_BY) if (re_test(r.re, id)) { pref = r.keys; break; }
    auto in0 = [&](const char* k) { for (int i = 0; i < 12 && keys0[i]; i++) if (streq(keys0[i], k)) return true; return false; };
    auto inp = [&](const char* k) { if (!pref) return false; for (int i = 0; i < 3 && pref[i]; i++) if (streq(pref[i], k)) return true; return false; };
    if (pref) for (int i = 0; i < 3 && pref[i]; i++) if (in0(pref[i])) out.push(pref[i]);
    for (int i = 0; i < 12 && keys0[i]; i++) if (!inp(keys0[i])) out.push(keys0[i]);
}
