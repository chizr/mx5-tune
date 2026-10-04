# MX-5 NB turbo tune — worklog

Last updated 2026-10-04. Calibration in the repo: `calibrations/mx5_nb_me442.mecal` at tag `v7`, **not yet burned or driven**.

## Car and hardware

NB1 MX-5 10th Anniversary (6-speed, no VVT), RHD, ~200,000 km on the car. Built 1.8 BP with stock pistons, Motorsport Electronics turbo kit, 98 RON pump fuel. No AC.

| Part | Detail |
| --- | --- |
| Engine build | Honed and blueprinted ~500 km before 2026-10-04 (still running in). Stock pistons, new aftermarket forged rods, new bearings, stiffer valve springs, aftermarket damper, coolant reroute |
| ECU | Motorsport Electronics ME442-V2B-PNP, firmware 4.2.1, tuned in MEITE |
| Turbo | TD04HL-19T hybrid (ME kit, pre-clocked), internal wastegate |
| Wastegate actuator | Forge, green spring (believed to be the lightest) |
| Intake and exhaust | Sjunk2 intake; sports cat; full 2.5" exhaust |
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

Versions are git tags on `calibrations/mx5_nb_me442.mecal`. `v1` is the original file (`18Jul_boost_pwm_limits.mecal`). All of v2–v7 were made offline on 2026-10-04 and are reproducible byte-for-byte with `tools/mecal.py`. Newest first.

| Tag | Area | Setting | Before | After | Why |
| --- | --- | --- | --- | --- | --- |
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
- **Engine rebuild timing.** The engine was honed and blueprinted ~500 km before 2026-10-04. If the logs predate the rebuild, the knock baselines, oil pressure references and VE findings may not hold for the rebuilt engine (new bearings, rings, stiffer valve springs). Re-check them from new logs.
- **Boost control** has no base duty (OL and CL initial duty tables all zero). In July, duty sat at a flat 65% as MAP crossed 105 kPa, which looks like a fixed spool value rather than PID output.

## Open items

Next: burn v7, then work through `docs/run-sheet_v7.pdf` and commit the logs.

- [ ] Burn v7 after spot-checking in MEITE: dead time axis accepted, lean protection error direction, oil protection settings
- [ ] Driveway: idle valve duty sweep (30→17%, fan off, wheel straight) to set warm idle duty for 1,000 rpm
- [x] Power steering idle-up works (Chris, 2026-10-04); still worth confirming the switch channel in a log
- [ ] Driveway: idle voltage test for dead times (lights, fan, demister; closed loop off)
- [ ] Driveway: confirm IAT reads ambient on a cold start; check sensor type
- [ ] Driveway: idle spark scatter, start ±3°; confirm sign (more advance below target)
- [ ] Road: overrun / return-to-idle log with v7
- [ ] Road: knock baseline and reproduction runs
- [ ] Road: solenoid unplugged test (spring pressure only)
- [ ] Road: open loop boost duty steps in 3rd, over-boost cut ~20 kPa above expected
- [ ] Confirm whether the Dec 2025 and Jul 2026 logs were before or after the rebuild
- [ ] Fix gear detection: record tyre size and confirm the final drive, then check `VSS Calc. Speed` against GPS speed and correct the VSS/final drive settings
- [ ] Fill boost CL initial duty table from duty-step logs; enable "use initial duty table"; revisit PID
- [ ] Correct light-load VE from the new overrun log (or long term trim, then bake in)
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
| Hot oil pressure, normal minimum | ~245 kPa @1,000; ~320 @2,000; ~385 @3,000; ~445 @5,000 rpm |
| Fuel pressure | 300 kPa above MAP |
| Battery voltage, running | 13.8–14.6 V |
| Injector headroom | 640 cc × 4 at 85% duty ≈ 330–350 crank hp |
| Boost targets (table 1) | 150 kPa below 2,500 rpm; peak 190 kPa at 4,000–5,000 rpm; 170 kPa from 6,500 rpm |
| Rev limit | 7,400 rpm warm; 5,000 rpm at 115 °C coolant |
