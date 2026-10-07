# Log index

Name logs `YYYY-MM-DD_HHMM_<source>_<what>.csv` (`sd` = ME442 SD card, `meite-pc` = MEITE laptop log). Newest first.

| File | Calibration in car | Turbo | Fuel | What | Notes |
| --- | --- | --- | --- | --- | --- |
| 2026-10-07_1028_meite-pc_drive.csv | v7 | hybrid + Forge actuator | unknown age | 1,196 s drive, max 5,178 rpm / 117 kPa (~4 s above 105 kPa), ambient 15 °C | All channels incl. per-cylinder knock. 6 knock retard events (5 at 2,200–2,650 rpm × 90–115 kPa). Return-to-idle dips. Last second is key-off garbage. Original name: ME442-V2B-PNP_2026_10_07_10_28_31.csv |
| 2026-10-07_0948_meite-pc_warmup-idle-tests.csv | v7 | hybrid + Forge actuator | unknown age | 1,292 s cold start and run sheet Part A: PS switch 09:58, voltage test ~10:01, idle duty sweep 10:04:47–10:08:36, spark scatter blips ~10:09:48 | Stationary, but VSS reads up to 42 km/h at 09:59:57–10:05:59 (spurious?). Original name: ME442-V2B-PNP_2026_10_07_09_48_46.csv |
| 2026-07-18_1644_sd_onboard-no3.csv | v1 (assumed; file is the 18 Jul cal) | hybrid + Forge actuator | unknown age | 259 s light street driving, max 4,000 rpm / 115 kPa | Overrun cut off. Shows decel lean / CL trim wind-up and +10% idle trim. No per-cylinder knock channels. Original name: OnBoardLog_2026_18_7_16_44_No3.csv |
| 2025-12-08_1439_meite-pc_all-channels.csv | older cal; same boosted timing as v1 | standard TD04 | unknown | 998 s mixed driving, max 5,000 rpm / 133 kPa | All channels incl. per-cylinder knock. Basis for v5 knock work. Idle settings differ from now. Original name: ME442-V2B-PNP_2025_12_08_14_39_56.csv |
