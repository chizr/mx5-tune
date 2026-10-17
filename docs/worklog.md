# MX-5 NB turbo tune — worklog

Last updated 2026-10-07. Calibration to load: `calibrations/mx5_nb_me442_v15.mecal` (tag `v15`), **not yet burned or driven**; includes v13/v14 (v13 superseded before burning). v12 is in the car (burned and driven 2026-10-17; oil now reads ~2 kPa engine-off). v7 was burned and driven 2026-10-07 (Part A of the run sheet plus a 20 min drive; filled-in page 1: `docs/run_sheet_v7.jpg`).

## Car and hardware

NB1 MX-5 10th Anniversary (6-speed, no VVT), RHD, ~200,000 km on the car. Built 1.8 BP with stock pistons, Motorsport Electronics turbo kit, 98 RON pump fuel. No AC.

| Part | Detail |
| --- | --- |
| Engine build | Honed and blueprinted before Dec 2025; ~500 km since (still running in). Stock pistons, new aftermarket forged rods, new bearings, stiffer valve springs, aftermarket damper, coolant reroute |
| ECU | Motorsport Electronics ME442-V2B-PNP, firmware 4.2.1, tuned in MEITE |
| Turbo | Eight Nine pre-clocked TD04-19T hybrid (sold by BOFI Racing): billet 19T compressor, HL turbine wheel, **0.41 A/R** turbine housing, Subaru flange, internal wastegate with port enlarged 11%. Vendor rates it ~300 hp and says it keeps standard TD04 spool; supplied with an 8 psi actuator. Fitted in 2026 (before Jul), replacing a standard TD04 |
| Wastegate actuator | Forge, single port, green spring (lightest in Forge's kit). Forge rating (T2 049): starts opening ~5 psi / 0.35 bar (~135 kPa abs), running ~10 psi / 0.7 bar (~170 kPa abs); the 048 (big) green is 0.7 bar. Fitted with the hybrid. A stronger Forge spring is on hand |
| Intake and exhaust | Skunk2 intake; sports cat; full 2.5" exhaust |
| Boost solenoid | Pierburg 3-port, 30 Hz, on LS1 |
| Injectors | Bosch EV14 640 cc/min (ME INJ-650 kit), exact Bosch part number unknown |
| Fuel system | Aftermarket rising-rate regulator, 300 kPa above manifold (confirmed in logs); pump believed to be DW200 |
| Lambda | Internal Bosch LSU 4.9 wideband |
| Knock | Single sensor (Digitune, IIRC); ECU splits readings per cylinder by crank window; sensor hears cylinders 2 and 3 loudest |
| IAT | Intercooler outlet; calibration matches Bosch 2.5 kΩ NTC curve; possibly a slow brass-bodied type |
| Other sensors | Oil pressure, oil temperature, fuel pressure. No EGT sensor fitted. |
| Idle | PWM idle valve, open loop. Primary fan adder +2%; power steering (extra load) switch on Dig In 1, +6%. Chris confirms the idle-up works, though it hasn't shown up in the logs so far |
| Gearbox | 6-speed. Calibration ratios 3.76, 2.269, 1.646, 1.257, 1.000, 0.843; final drive 3.636 (not confirmed against the car) |
| Chassis | BC coilovers; Enkei RPF1 15×7 wheels (tyre size not recorded); new front brakes waiting to be fitted |

Target: about 260–290 crank hp daily on 98 RON, inside stock-piston limits. The 19T runs out near 300 crank hp anyway.

## Calibration change log

Versions are git tags; from v10 each version is also its own file `calibrations/mx5_nb_me442_vN.mecal` (also exported for v7, the rollback, and v8; the others: `git show vN:calibrations/mx5_nb_me442.mecal`). `v1` is the original file (`18Jul_boost_pwm_limits.mecal`). All of v2–v7 were made offline on 2026-10-04 and are reproducible byte-for-byte with `tools/mecal.py`. Newest first.

| Tag | Area | Setting | Before | After | Why |
| --- | --- | --- | --- | --- | --- |
| v15 | Fuel | Inj. Target AFR, 100 and 115 kPa rows (all rpm) | 100: 13.0–12.7; 115: 12.5–12.4 | 100: 12.5; 115: 12.2 | Knock zone (2,750–3,500 rpm × 92–115 kPa) is the on/off-boost transition. 100 kPa is still closed loop (max 105), so actual AFR follows the target there; at 115 kPa (open loop) fuel rises ~2–3%. Boost logs already run ~0.5 AFR richer than target, so the full boost targets wait for a dyno VE pass |
| v14 | Fuel | Inj. Base VE (1), 24–64 kPa × 1,250–3,800 rpm (35 cells) | v13 per-cell values (or v12) | Smooth least-squares fit to 14,231 steady closed-loop samples (2026-10-16/17), using the ECU's bilinear interpolation weights plus a curvature penalty; then +2% on 24–53 kPa (prefer rich). v12→v14: up to +63% at 33 kPa × 2,250 rpm, ~0% from 64 kPa | v13 matched the data cell-by-cell but stayed lumpy. Predicted light-cruise fuel error: v12 −18.5%, v13 −0.9%, v14 +0.8% (10–90%: −8..+11%). Also fills the 3,800 rpm dip. Plot: `docs/ve_v12_vs_v14.png` |
| v13 | Fuel | Inj. Base VE (1), 24–53 kPa × 1,250–3,400 rpm (18 cells) | e.g. 33 kPa: 48.71, 47.36, 32.65, 41.79, 41.64 (1,550–3,400 rpm) | ×1.05–1.39 per cell, e.g. 33 kPa: 56.99, 60.62, 45.38, 53.91, 53.30 | Closed loop at its +20% limit 16% of warm time in light cruise, still lean (15.4–16.8 AFR). Factors = trim × measured AFR ÷ target from steady closed-loop data, 2026-10-16/17. 53 kPa × 3,400 rpm (no data) set ×1.07 to match its row and keep VE rising with load |
| v12 | Sensors | Oil Press. HRT first point | 0 V → 0 kPa | 0.5 V → 0 kPa | Matches the sensor doc (0.5 V = 0, 4.5 V = 1,000 kPa). Engine-off oil read 113 kPa; oil pressure now logs true gauge kPa (true ≈ 1.125 × old − 125) |
| v12 | Engine protection | EPS: Oil P Limit (1,000→4,000+ rpm, true kPa) | 130, 150, 180, 200, 220, 230, 240… (= true 21, 44, 78, 100, 123, 134, 145) | 60, 90, 130, 160, 180, 190, 200… | ~55% of the lowest normal hot readings (true p5: idle 143, 2,000 rpm 255, 3,000 rpm 304, 4,000 rpm 331, 5,000 rpm 354). Old limits were near zero at low rpm in true terms |
| v11 | Ignition | Ign. Adv. (Pri 1), 97 kPa × 3,000/3,500/4,000 rpm; 111 kPa × 2,500–4,000 rpm | 97: 23.0, 25.75, 29.0; 111: 17.75, 21.0, 23.25, 25.5 | 97: 21.0, 23.75, 28.0; 111: 16.75, 19.0, 21.25, 24.5 (−2° at 3,000/3,500, −1° at 2,500/111 and 4,000) | 2026-10-16: 7 knock retard events at 2,740–3,530 rpm × 98–114 kPa, cyl 2/3 |
| v11 | Idle | Idle OL Duty, 80 °C and up | 21.5 | 22.0 | Warm idle 947 rpm fan off at 21.5% (target 1,000) |
| v10 | Boost | PWM Min Duty | 10% | 0% | Solenoid re-plumbed: less duty now means less boost, so a lower floor is safe, and C2 (0% duty) becomes a true spring-only test instead of possibly clamping to 10%. PWM Max Duty stays 80% until C3 duty steps show what duty gives the 190 kPa peak target |
| v9 | Boost | Abs. Max Boost (over-boost cut) | 225 kPa | 190 kPa (temporary) | First boost runs after re-plumbing the solenoid: 20 kPa above the green spring's ~170 kPa running pressure. Equals the 190 kPa peak target, so closed-loop boost at peak target will hit the cut; revisit after B4/B5 |
| v8 | Ignition | Ign. Adv. (Pri 1), 83 and 97 kPa rows × 2,000–3,000 rpm | 83 kPa: 23.25, 26.25, 28.75; 97 kPa: 19.5, 22.5, 25.0 | −2° each; −1° at 3,500 rpm (83 kPa 30.5→29.5, 97 kPa 26.75→25.75) | 5 of 6 knock retard events on 2026-10-07 were at 2,200–2,650 rpm × 89–115 kPa, cyl 3/2 |
| v8 | Idle | Idle OL Duty, 80 °C and up | 22.5 | 21.5 | Sweep: 22.5% ≈ 1,030 rpm, 21% ≈ 986; target 1,000 |
| v7 | Engine protection | Oil pressure protection (2nd "Enabled" in EPS: Oil) | Off | On | Turbo oil feed is the biggest remaining risk |
| v7 | Engine protection | Oil P limit (kPa, 1000→4000+ rpm) | 400 flat | 130, 150, 180, 200, 220, 230, 240… | About 55% of the healthy hot minimum in both logs |
| v7 | Engine protection | Oil trigger time / action | 50 ms / none | 300 ms / 2,000 rpm limit | Ignore brief cornering surge; force a lift on real loss |
| v6 | Idle | Idle OL Duty, warm (60, 70, 75, 80 °C+) | 25.5, 25.1, 24.1, 25.1 | 24.5, 23.5, 23.0, 22.5 | Idle ~1,210 rpm vs 1,000 target; first step only |
| v5 | Ignition | Ign. Adv. (Pri 1), 2,000–3,500 rpm × 111–240 kPa | — | −2° (−1° at 97 kPa and at 4,000 rpm); one unreachable cell clamped to 0° | Per-cylinder logs suggest light knock on cyl 2/3 on boost |
| v5 | Knock | Knock control | Off | On | Insurance before dyno |
| v5 | Knock | Knock Acc. Val. (1000→8000 rpm) | 270 flat to 3,000, rising | 400, 400, 380, 370, 380, 420, 480, 520, 580, 620, 660, 700, 720, 740… | ~1.4× clean noise floor; replay of Dec log flags only cyl 2/3 on boost |
| v5 | Knock | Min rpm / max retard / recovery | 700 / 10° / 0.2° per rotation | 1,200 / 8° / 0.2° per 10 rotations | Avoid idle noise; slower recovery |
| v4 | Lambda | Closed loop MAP minimum | 20 kPa | 26 kPa | Stop CL chasing lean decel readings (decel 17–25 kPa, idle 29–32) |
| v4 | Overrun | Max TPS | 0.1% | 1% | Closed-throttle TPS reads up to 0.07% |
| v4 | Ignition | Ign. Adv. (Pri 1), 1,000–2,000 rpm × 55–97 kPa | — | −2° (−1° at 2,000 rpm) | 524 knock reading on a low-rpm pull-away |
| v3 | Boost | Abs. Max Boost (over-boost cut) | 210 kPa | 225 kPa | 210 was too close to future targets |
| v3 | Boost | Gear limit, 1st and 2nd | 300 kPa | 185 kPa | Traction and low-gear safety |
| v3 | Ignition | IAT timing add (50, 60, 70, 75, 80 °C+) | 0 | −1, −2, −3, −3.5, −4° | Pull timing on hot charge air |
| v3 | Lambda | Closed loop MAP maximum | 250 kPa | 105 kPa | No closed-loop trimming on boost |
| v3 | Engine protection | General enable | Off | On | Needed for any protection to act |
| v3 | Engine protection | Lean protection | Off | On: ≥130 kPa, ≥50% TPS, ≥2,500 rpm, 0.8 AFR error, 300 ms, 3,000 rpm limit | Catch lean running under boost |
| v3 | Overrun | Fuel cut | Off | On: return 1,800 rpm, 0.4 s return, 20% re-entry trim for 0.3 s | Smoother return to idle than the old settings |
| v2 | Fuel | Dead time voltage axis | 8–16 V, then 16 V repeated | 8, 9, 10, 11, 12, 12.5, 13, 13.25, 13.5, 13.75, 14, 14.25, 14.5, 15, 15.5, 16 V | Finer resolution around alternator voltage |
| v2 | Fuel | Dead time values | 12 V 1.65, 13 V 1.12 ms (kink) | Smooth curve: 12 V 1.52, 13 V 1.21 ms, in-between values interpolated (log-PCHIP) | Remove 12–13 V step; running voltage barely changed |

Not changed yet: VE table, AFR targets, boost targets, boost duty tables, PID gains, idle spark scatter, fuel pressure protection, oil temperature protection.

## Findings so far

### 2026-10-17: first v12 drive (44 min)

Logs: `logs/2026-10-17_0834_meite-pc_key-on-leakdown.csv`, `logs/2026-10-17_0837_meite-pc_cold-start-drive.csv`. BOV was connected normally for these logs; Chris removed and capped its reference (vacuum) line **afterwards**, to rule out a boost leak. Caveat for the next logs: with no reference, the BOV can't vent on lift (compressor surge) and, on many designs, is held shut on boost by its spring alone, so it may leak *more*. Bench-test it (10–15 psi on the inlet, reference open; then vacuum on the reference should open it) or blank it off; otherwise reconnect. Fuel: old tank with octane booster (to confirm).

- **v12 oil fix works:** engine-off 1.9 kPa. Hot idle 149–160 kPa true.
- **Idle on target:** fan off 996 rpm at 22.0%; fan on 988–1,030 at 24%. Warm idle MAP 31.9 kPa (p5–p95 30.6–33.8): ~70 kPa / ~20.7 inHg below atmosphere, normal for a healthy BP and steady (no sign of a vacuum leak).
- **MAP sensor:** HRT is linear 0 V = 5 kPa to 5 V = 400 kPa (4-bar). Engine off it reads 101.8–102.0 kPa across three logs: plausible barometric pressure. To verify, compare with a nearby weather station's *station* pressure (not sea-level QNH) at the time of a key-on log.
- **Fuel pressure leak-down confirmed:** 161 → 97 kPa in 20 s, 58 at 60 s, 23 at 194 s. Cold start with 21 kPa at crank took 2.5 s.
- **Knock: now cylinder 3, and partly off boost.** 6 retard events, cyl 3 14 of 17 counts. Events at 2,750–2,985 rpm × 92–110 kPa (20.7–22.4° at 92–99 kPa: still fed by the 83 kPa row's 24.25–26.75° at 2,500–3,000), one at 1,448 rpm × 86 kPa / 15% TPS, and one at **3,371 rpm × 46 kPa with 2% TPS**, which can't be detonation: cyl 3's window is picking up noise. Ratios on boost: cyl 3 1.35–1.69×, cyl 2 1.33–1.50×, cyl 1/4 1.1–1.2×. Real knock and noise are now mixed; det cans on a dyno are the way to separate them. Possible cyl 3 noise sources: loose heat shield or exhaust contact near the sensor, injector or valvetrain tick (stiffer springs).
- **Light-load VE hole, confirmed.** Warm, closed-loop trim sat at its +20% limit 16% of the time, nearly all in light cruise (0.5–15% TPS, 33–42 kPa, 1,800–3,200 rpm), where AFR still read 15.4–16.8. From steady closed-loop samples in both warm drives (trim × measured AFR ÷ target), the base VE needs ×1.15–1.39 at 24–43 kPa × 1,550–3,400 rpm (worst 33 kPa × 2,250 rpm, ×1.39, 1,197 samples), ×1.05–1.08 at 53 kPa, ~×1.0 from 64 kPa up. The 2,250 rpm column is 20–30% below its neighbours at 24–43 kPa.
- **Acceleration fuelling is adequate.** 19 tip-ins from steady fuelled running: median lean blip only +0.5 AFR over target in the first 0.5 s (above +1.5 in 20–30%), then a rich trough of −1.2 to −2.3 AFR. The big lean readings on tip-in are from coming straight out of overrun fuel cut (exhaust still lean at the sensor) or from the lean cruise cells above. On boost AFR 11.7–12.4 vs 12.4–12.9 target: slightly richer than target.
- **Boost:** still short bursts (longest 2.1 s above 105 kPa; only 26 samples at 90%+ TPS). Peak 123 kPa in 2nd at 60% TPS. BOV was still connected here.


### 2026-10-16: cold/hot starts and first full-throttle runs (v10 assumed)

Logs: `logs/2026-10-16_1921_*` and `logs/2026-10-16_1940_*`. Fuel age not yet recorded.

- **Slow starts track fuel pressure at crank, which bleeds down fast.** The pump only runs at key-on prime (2 s) and again once the ECU syncs, so pressure at crank is whatever is left. Cold (14 °C), 86 kPa at crank 33 s after key-on: 2.2 s cranking (sync +0.3 s, pump/300 kPa +0.9 s, running +2.2 s). Hot, ~124 kPa (key-on ~10 s before): ~1.1 s. Hot, 209 kPa (just after shutdown): instant. Leak-down: 304→215 kPa in 7.5 s; 187→138 in 7 s; 140→124 in 6 s. A healthy system holds for minutes. Suspects: pump check valve, rising-rate regulator, or a leaking injector (less likely: hot start caught clean at 14.8–15.2 AFR). Once running, starts are clean (no stumble), so crank/after-start fuel tables look fine.
- **Boost: plumbing fix works; runs still too short.** With full throttle (TPS now reaches 100%), duty goes to 65–80% and MAP climbs steadily: 107→120 kPa over 1.7 s at 2,580–3,360 rpm in 3rd; 107→126 kPa over 1.1 s at 3,000–3,480 rpm. Every run ended at 3,300–3,800 rpm with boost still rising, and knock retard (−8°) hit mid-run in 3 of 5. No sign yet of a boost fault; the 19T is only coming on at 3,300–3,800 rpm.
- **Part-throttle boost: hybrid vs old TD04, after the fix.** 90th-pct MAP at 2,500–4,000 rpm, 30–75% TPS, 2nd–4th gear: old TD04 (Dec) 120–132 kPa; hybrid 98–109 kPa. Matches Chris's feel: the old turbo built boost on part throttle, the hybrid barely gets above atmospheric there. Expected for the larger HL turbine housing and 19T compressor. Calibration can help a little (no knock retard mid-spool, boost duty tables, light-load fuelling) but not change the character. Road speed limits make sustained pulls impractical: use a load-bearing dyno for C2/C3, spool mapping and knock with det cans.
- **Knock moved up and got stronger.** 7 retard events, all at 2,740–3,530 rpm × 98–114 kPa, 20–24° advance, AFR 12.0–12.7; cyl 2 (6 events) and cyl 3 (4) only. Cyl 2 peaked at 620 against a 482 threshold. Ratios vs own baseline at 110–140 kPa: cyl 2 1.7–1.9×, cyl 3 1.5–1.8×, cyl 1/4 1.1–1.2× (stronger than 1.3–1.4× on 7 Oct, now with more load). Only one event was in the v8 area (2,741 rpm, 105 kPa). Treat as real knock until fresh fuel proves otherwise.
- **Oil pressure conversion table is missing its 0.5 V zero point.** Sensor: combined oil pressure/temperature unit (M10×1.0, ANA V5 pressure / V6 temp, 5 V ref). Engine off it outputs 0.51 V (raw 6,662), the usual zero for a 0.5–4.5 V sensor, but `Oil Press. HRT` maps 0 V→0 and 4.5 V→1,000 kPa, so rest reads 113 kPa. `Fuel Press. HRT` has the correct 0.5 V→0 point. If the oil sensor is also 0–10 bar over 0.5–4.5 V: true = 1.125 × logged − 125 kPa. Hot oil (85 °C+), true: idle 600–1,200 rpm median 167 (p5 143, min 95); 1,800–2,500 rpm 292; 2,500–3,200 rpm 320; 4,200–5,500 rpm 365 kPa. Healthy. But the v7 limits in true terms are only 21 kPa at 1,000 rpm rising to 145 kPa at 4,000+: far too lax at low rpm. Fix the HRT and re-base the limits once the sensor's full-scale is confirmed (the sensor doc's HRT values are in an image).
- **Idle:** warm, fan off 947 rpm at 21.5% (target 1,000); fan on 1,017 at 23.5%. After a hot restart ~810 rpm at 23.5% for the first 20–30 s.
- **Coolant** peaked at 94 °C with the fan cycling; 111 °C readings are first/last-sample logging artefacts. No protection trips.


### 2026-10-07: first v7 logs

Logs: `logs/2026-10-07_0948_meite-pc_warmup-idle-tests.csv` (cold start, Part A) and `logs/2026-10-07_1028_meite-pc_drive.csv` (20 min drive, max 5,178 rpm / 117 kPa, only ~4 s above 105 kPa). Ambient 15 °C. Fuel ~6 months old (98 RON). First per-cylinder knock data on the hybrid turbo.

- **Knock on the hybrid: same cyl 2/3 pattern, and knock control is now acting on it.** Knock retard fired 6 times, each to −7 to −8°, recovering over ~8 s. Five of six were at **2,200–2,650 rpm, 89–115 kPa**, as the car came onto boost, at 22–26° advance. Cylinder 3 logged 7 of 12 knock events, cyl 2 three, cyl 1 and 4 one each. Ratios vs own light-load baseline at 90–140 kPa: cyl 2/3 1.3–1.4×, cyl 1/4 1.1–1.2×, the same as December on the old turbo. The 2,000–3,000 rpm × 83–97 kPa cells (22.5–28.75°) were barely touched by v4/v5, and that is where it happens. Treat as probable light knock. Caveat: the fuel was ~6 months old, and stale 98 loses octane, so some of this may be the fuel; re-log on fresh fuel. The sixth event (5,178 rpm, 60 kPa, 1st gear, rpm jumped 3,000→5,178 in 0.5 s) looks different: possibly wheelspin/clutch slip or mechanical noise; Chris to say what happened at ~10:46:17.
- **Knock response is heavy-handed.** Retard step 1.5° with "Rots./retard step" 0 takes it to the 8° limit within ~0.1 s on a single marginal event. Safe, but costs a lot of power for borderline readings.
- **Return to idle still dips.** After a blip or tip-out, AFR spikes to 17–24 for ~1 s as fuel returns, closed loop winds to +20%, then overshoots to ~12.1 AFR and rpm sags to ~690 (lowest 562 rpm while running). Trim sat at +20% for 8% of the drive: 742 samples were light throttle cruise (VE lean, below), 141 were closed-throttle returns.
- **Light-load VE still lean in cruise.** Mean trim at 25–45 kPa: +9–14% from 1,200 to 4,100 rpm; 45–100 kPa within ±5%. At idle the picture splits by rpm: in the duty sweep, trim was −7% at 840–900 rpm, ~−2% at 1,000–1,040 and +10–13% at 1,200–1,480 rpm (all 29–32 kPa).
- **Warm idle: v6 is close.** Target is 1,000 rpm. Sweep (fan off, CL on, coolant 87–92 °C): 30% 1,482; 27% 1,363; 25% 1,191; 23% 1,041; 22% 1,014; 21% 986; 19% 898; 17% 837 rpm. MAP 29–32 kPa throughout, so no extra-air floor: the valve has full authority. The v6 cell (22.5% at 80 °C+) gives ~1,030 rpm. About 21.5% would hit 1,000.
- **Power steering switch works:** 09:58:31, idle duty 22.5→28.5% (+6%), rpm rose ~100.
- **Idle spark scatter:** set and seen working (adds advance when rpm is below target, e.g. 23.9° at 689 rpm).
- **IAT responds now:** 14–19 °C on the drive, rising at idle and falling when moving. Cold start read 12 °C against a stated 15 °C ambient; a cold-soaked intercooler can read under air temperature, so not conclusive. Sensor body: silver (type still unknown).
- **Dead-time voltage test (A4):** closed-loop trim frozen (limit 20%→0%). Chris saw AFR richen slightly with each load, to 14.2 with everything on. Battery voltage only moved 14.17–14.30 V, so the change isn't dead time; it follows idle rpm (1,040–1,110) across the idle VE cells, which run rich near 1,000 rpm and lean above 1,100 (see sweep). Dead times are fine at running voltage; low-voltage dead times remain untested.
- **Gear detection error confirmed:** 3rd read as 2 in 515 of 733 samples; 4th as 3 in 311 of 312.
- **Hot oil pressure (oil 90–99 °C):** median 258 kPa at 800–1,200 rpm, 367 at 1,800–2,500, 414 at 3,200–4,200; minimum while running 180+ kPa. Clear of v7 limits.
- **Coolant** peaked at 95 °C with fan cycling. No protection trips.
- **Boost:** brief only. Duty went straight to the 80% max while spooling (PID saturated below target, as expected for 150 kPa at 2,500 rpm). AFR on boost 11.5–13.1.
- **Log artefacts:** the last second of the drive log (key-off) shows 113 °C coolant/oil, 50 kPa oil, 6.9 V and 983 knock. Ignore. One 17.5 V single-sample spike in the warm-up log at 10:05:57.

### Earlier (Jul 2026 and Dec 2025 logs)

Biggest finding: closed-loop lambda chasing lean decel readings explains the rich, sagging return to idle. Second: cylinders 2 and 3 show a knock-like pattern at 2,000–4,000 rpm on boost.

Logs: `logs/2026-07-18_1644_sd_onboard-no3.csv` (259 s, light street driving, max 115 kPa) and `logs/2025-12-08_1439_meite-pc_all-channels.csv` (998 s, all channels incl. per-cylinder knock, max 133 kPa). The December log ran the same boosted timing as v1.

- **Decel and idle droop.** With fuel cut off, decel injector pulses are tiny (median 0.32 ms) and the wideband reads 24–50+ AFR. Closed loop wound trim to +20% and carried it into idle: AFR ~12.5 vs 14.4 target as rpm sagged to 980 (18 Jul, 121–124 s). Addressed in v3/v4: closed loop limited to 26–105 kPa, overrun cut re-enabled.
- **Light-load VE ~10% lean.** Steady idle trim +10%, cruise +5–15%, ~0% by 80–100 kPa. Dead time explains at most ~0.06 ms of it. Correct from a clean post-v7 log.
- **Knock, cylinders 2 and 3.** Relative to each cylinder's own 35–60 kPa baseline, cyl 2/3 rise 1.4–1.7× at 2,000–4,000 rpm and 90–140 kPa; cyl 1/4 only 1.1–1.2×. Fades above 4,000 rpm. Consistent with light knock, not proof. Det cans on the dyno.
- **The 524 knock reading** (18 Jul, 1,400 rpm, 77 kPa pull-away) looks like load noise: all four cylinders rise similarly there.
- **Fuel pressure** holds 300 kPa above MAP ±3 kPa. Regulator fine.
- **Oil pressure** hot minimum ~245 kPa at 1,000 rpm rising to ~445 kPa at 5,000 rpm. Healthy.
- **IAT** flat at 27–29 °C for the whole December log, no response to boost or idle. Suspect slow sensor.
- **Idle valve:** 27.1% = 25.1% table + 2% fan adder gave ~1,214 rpm warm in July. December idle data is confounded by the fan adder and older mechanical settings; use July/new data only.
- **Gear detection reads one gear low in 3rd and 4th** (Dec log, gear from km/h per 1,000 rpm vs `VSS Gear`). 1st and 2nd are correct. 3rd reads as 2 in 267 of 355 samples; 4th reads as 3 in 189 of 190. The six gearbox ratios match the 6-speed, so the error is likely the final drive, tyre size or VSS pulse setting. Effect: the 185 kPa 1st/2nd boost limit (v3) usually applies in 3rd too. That errs safe, but it must be fixed before gear-based boost work.
- **Which hardware each log saw.** Both logs are after the engine rebuild, so oil pressure references, idle and light-load findings hold for this engine. The December log was on the **old standard TD04**: its boost-side findings (cyl 2/3 knock pattern at 90–140 kPa, max 133 kPa) came from a different turbo with different spool, exhaust back-pressure and charge temperatures. Off-boost knock noise floors (used for v5 thresholds) are engine noise and should carry over. The v5 timing pull stays as a precaution, but the knock picture on the hybrid needs new per-cylinder logs.
- **Boost control** has no base duty (OL and CL initial duty tables all zero). In July, duty sat at a flat 65% as MAP crossed 105 kPa, which looks like a fixed spool value rather than PID output.

## Open items

**Fixed 2026-10-07 (Chris re-plumbed the solenoid; C2/C3 will confirm on the road).** Original note: **boost solenoid plumbed backwards (confirmed).** Bench test: with the solenoid unpowered, the boost supply port is blocked and the actuator port connects to the vent, so the actuator sees no pressure at 0% duty (below 105 kPa, or if the solenoid loses power) and the wastegate stays shut until the 225 kPa over-boost cut. Above 105 kPa the 65–80% duty then feeds boost *to* the actuator, which fits the 115–117 kPa ceiling. Stay off boost and do not run B4 until it is re-plumbed so unpowered = supply connected to actuator. Don't fix it with `PWM Solenoid Control` = Inverted: that keeps the unsafe failure mode.

Next: work through `docs/run-sheet_v15.pdf` (leak test, burn v15, off-boost drives on the old fuel, then fresh-fuel boost and knock runs).

- [x] **Re-plumb boost solenoid** (done 2026-10-07). Unpowered: actuator ↔ vent, supply blocked (confirmed). Check 12 V pairing; if supply ↔ actuator, swap the supply and vent hoses. Re-test: unpowered supply → actuator; 12 V actuator → vent. Required before any boost running or B4
- [ ] After re-plumbing, boost duty will hold the gate shut for the first time on this turbo (PID untuned, no initial duty table, 65% step at 105 kPa). v9 sets the over-boost cut to 190 kPa for B4/B5; reset it once duty tables are done
- [ ] Boost leak test (cap turbo inlet, pressurise intake to ~1 bar) before B4, if not done since the hybrid went on
- [x] Burn v7 (2026-10-07)
- [x] Idle valve duty sweep (2026-10-07): ~21.5% for 1,000 rpm warm, fan off
- [x] Power steering idle-up works; confirmed in log 2026-10-07
- [ ] Idle voltage test for dead times: retry with lower idle rpm or more load so voltage actually drops
- [x] IAT responds (2026-10-07); sensor type still unknown (silver body)
- [x] Idle spark scatter set and working (2026-10-07)
- [x] Overrun / return-to-idle log with v7 (2026-10-07): still dips, see findings
- [ ] **Knock at 3,000–3,500 rpm × 98–114 kPa (2026-10-16): no more boost runs until v12 is in and the tank is fresh 98** (octane booster added to the old fuel; run it down). v11 pulls the timing there
- [ ] Wastegate preload check (engine cold/off) — higher priority now: the turbo's small 0.41 A/R housing and the vendor's "standard TD04 spool" claim mean turbo size alone shouldn't cost 20–30 kPa at part throttle, and its 11% larger wastegate port gives exhaust pressure more area to push the flap open against the light green spring (opens ~5 psi vs the vendor's 8 psi actuator). Aim for opening pressure near 8 psi with preload, or try the supplied 8 psi actuator if available. Check: rod preload against the closed flap (per Forge instructions), opening pressure with a hand pump (green should start moving ~5 psi / 0.35 bar), flap seats fully and the arm moves freely. Low preload would let exhaust pressure crack the flap at part throttle and slow spool; ECU logs can't separate this from turbo size. Re-check C2 spring-only boost after any adjustment
- [ ] BOV: bench-test (holds 10–15 psi on the inlet with reference open; opens on vacuum) or blank off for a test; don't drive long with the reference line removed (surge on lift)
- [ ] Fill VE data gaps (2026-10-17 coverage, `docs/ve_coverage.png`; aim ≥20 s steady per cell): 3,400–4,300 rpm at any load (e.g. 3rd at ~60–75 km/h, steady); 64–100 kPa at 1,850–3,400 rpm (steady moderate throttle, hills in 4th/5th); 1,250–1,550 rpm at 43–53 kPa. Nothing steady above 115 kPa or 3,800 rpm: dyno. Don't lug: keep under ~60 kPa below 1,500 rpm
- [ ] AFR targets on boost: after the boost VE is corrected on the dyno (actual = target), move to ~11.5–11.8 from ~140 kPa and ~11.0 near peak (rule-of-thumb for stock pistons; confirm with EGT/det cans). Closed loop stays off above 105 kPa
- [ ] Fuel pressure leak-down: after shutdown, watch fuel pressure in MEITE while pinching the return line (holds → regulator) or the feed between pump and rail (holds → pump check valve); neither → injector. Workaround: key on, wait for the pump to stop, crank straight away
- [x] Oil pressure HRT fixed and oil limits re-based in true kPa (v12). After burning: engine-off oil should read ~0
- [ ] Idle: v11 sets 22.0% (was 947 rpm at 21.5%). Hot restart still idles ~810 rpm for 20–30 s; look at an after-start idle adder if it persists
- [ ] Knock: v8 pulls 2° at 2,000–3,000 rpm × 83–97 kPa. Re-log on fresh fuel: expect fewer or no retard events, and cyl 3 ratio on boost nearer 1.1–1.2×
- [ ] Boost: hybrid tops out at 115–117 kPa in both logs (Jul, Oct), only 2–4 s above 105 kPa; old TD04 (Dec) made 123–132 kPa at 2,500–3,500 rpm on similar part throttle, at 90% duty. Part is the bigger compressor and short bursts, but a ceiling suggests: light green spring cracking early, the 80% `PWM Max Duty` cap (was 90% in Dec), or solenoid plumbed backwards. B4 (0% duty, 3rd, full throttle) gives the spring-only ceiling; B5 duty steps show which way duty moves boost. Green spring rating (Forge): opens ~135 kPa abs, runs ~170 kPa abs, so it can't explain a 115–117 kPa ceiling even with the backwards plumbing. More likely the low boost is mostly short part-throttle bursts plus the bigger compressor. Keep the green spring: its spring-only boost already sits inside the 150–190 kPa targets, and a stronger one would raise the floor and the failure-mode boost above what stock pistons should see
- [ ] Return-to-idle dip: lean spike (17–24 AFR) as fuel returns after a blip, then CL overshoot. Look at overrun re-entry fuel and closed-throttle fuelling (separate change)
- [ ] Knock control: consider gentler retard (smaller step or rotations per step) once timing is safer
- [ ] Road: solenoid unplugged test (spring pressure only)
- [ ] Road: open loop boost duty steps in 3rd, over-boost cut ~20 kPa above expected
- [x] Logs vs rebuild: both after (Chris, 2026-10-04)
- [x] Jul 2026 log was on the hybrid with the Forge actuator (Chris, 2026-10-04)
- [ ] Fix gear detection: record tyre size and confirm the final drive, then check `VSS Calc. Speed` against GPS speed and correct the VSS/final drive settings
- [ ] Fill boost CL initial duty table from duty-step logs; enable "use initial duty table"; revisit PID
- [ ] Light-load VE corrected in v13, smoothed in v14. After burning: closed-loop trim at 24–53 kPa × 1,500–3,400 rpm should sit within ±5% and rarely hit +20%. Then check the 3,800 rpm column at 33/43 kPa (40.1/49.9, well below 3,400 rpm's 53.3/62.8), which had too little data
- [ ] Extend top VE row 205 → ~230 kPa before raising boost targets
- [ ] Ask Motorsport Electronics for the INJ-650 dead time table; read injector part number if visible
- [ ] ME442 manual: does fuel pressure protection compare fuel − MAP? What does "CL Req. Boost Delta" do?
- [ ] Optional hardware: pre-turbo pressure and temperature sensors on spare analog inputs
- [ ] Dyno: det cans at 2,000–4,000 rpm on boost; knock threshold calibration; final timing

Decided: no AC, so AC control stays disabled. Boost targets stay as they are (max 190 kPa) until the duty tables are done. Do knock and boost runs on fresh fuel only; note fuel age on every log.

## Logging and reference numbers

Log everything the December log had, at 10 Hz, including per-cylinder knock (off in the July SD logging setup).

| Reference | Value |
| --- | --- |
| Warm idle MAP | 29–32 kPa |
| Closed-throttle decel MAP | 17–25 kPa |
| Warm idle (July) | ~1,214 rpm at 27.1% duty (fan on) |
| Knock noise floor, loudest cylinder (clean, 35–90 kPa) | ~250–300 below 3,000 rpm; ~370 at 4,000–4,500 |
| Hot oil pressure (true gauge, from v12) | median ~167 kPa at idle (p5 143); ~292 @1,800–2,500; ~320 @2,500–3,200; ~365 @4,200–5,500 rpm. Logs before v12 read 1.125×true+~110 high |
| Fuel pressure | 300 kPa above MAP |
| Battery voltage, running | 13.8–14.6 V |
| Injector headroom | 640 cc × 4 at 85% duty ≈ 330–350 crank hp |
| Boost targets (table 1) | 150 kPa below 2,500 rpm; peak 190 kPa at 4,000–5,000 rpm; 170 kPa from 6,500 rpm |
| Rev limit | 7,400 rpm warm; 5,000 rpm at 115 °C coolant |
