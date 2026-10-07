# MX-5 NB turbo tune

ME442 calibration, logs and worklog for an NB1 MX-5 with a TD04HL-19T on a built 1.8 BP.

- Calibration: `calibrations/mx5_nb_me442.mecal` (versions are git tags `v1`…; `v1` = original 18 Jul file)
- Worklog, change log and open items: `docs/worklog.md`
- Next test plan: `docs/run-sheet_v9.pdf` (v7 sheet kept for the record)
- Logs: `logs/` (index in `logs/README.md`)

## Setup

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # then use .venv/bin/python for tools
sh tools/setup-git.sh          # readable diffs for .mecal files
```

## Everyday use

```sh
python3 tools/mecal.py diff <(git show v6:calibrations/mx5_nb_me442.mecal) calibrations/mx5_nb_me442.mecal
python3 tools/mecal.py table calibrations/mx5_nb_me442.mecal "Ign. Adv. (Pri 1)"
python3 tools/logtools.py knock logs/<log>.csv
git diff v6 v7 -- calibrations/  # readable after setup-git.sh
```

After a session: save the calibration from MEITE over `calibrations/mx5_nb_me442.mecal`, copy logs into `logs/` with the naming convention, update `logs/README.md`, commit.
