# MX-5 NB turbo tune

ME442 calibration, logs and worklog for an NB1 MX-5 with a TD04HL-19T on a built 1.8 BP.

- Calibrations: `calibrations/mx5_nb_me442_vN.mecal`, one file per version (newest = highest `vN`), each also a git tag. Files exist for v7 (rollback: in the car on 2026-10-07), v8 and v10 onward; v1–v6 and v9 are tags only (`v1` = original 18 Jul file).
- Worklog, change log and open items: `docs/worklog.md`
- Next test plan: `docs/run-sheet_v10.pdf` (v7 sheet kept for the record)
- Logs: `logs/` (index in `logs/README.md`)

## Setup

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # then use .venv/bin/python for tools
sh tools/setup-git.sh          # readable diffs for .mecal files
```

## Everyday use

```sh
python3 tools/mecal.py diff calibrations/mx5_nb_me442_v10.mecal calibrations/mx5_nb_me442_v11.mecal
python3 tools/mecal.py diff <(git show v6:calibrations/mx5_nb_me442.mecal) calibrations/mx5_nb_me442_v10.mecal
python3 tools/mecal.py table calibrations/mx5_nb_me442_v10.mecal "Ign. Adv. (Pri 1)"
python3 tools/logtools.py knock logs/<log>.csv
git diff v6 v7 -- calibrations/  # readable after setup-git.sh
```

After a session: if you changed the calibration in MEITE, save it as the next `calibrations/mx5_nb_me442_vN.mecal` (never over an existing version), copy logs into `logs/` with the naming convention, update `logs/README.md`, commit.
