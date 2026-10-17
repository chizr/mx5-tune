#!/usr/bin/env python3
"""Read MEITE's screen through Windows UI Automation (Windows only, needs pywinauto).

MEITE must be open. The only thing this ever clicks is a view tab (START,
Mapping, Idle, ...), selected through UI Automation's Invoke; it never types,
edits, saves or talks to the ECU. It puts MEITE back on the tab it started on.

Driver settings (property grids) are readable with their values. Tables are
custom-drawn, so only their names are readable; their cells live in the .mecal.

CLI:
  meite_check.py map [OUT.md [FILE.mecal]]
                                     walk every tab, write where each driver and
                                     table lives (default docs/meite_layout.md);
                                     with FILE, also list what is on no tab
  meite_check.py check FILE.mecal    compare every visible setting with FILE and check
                                     FILE is the one open; visits each tab that holds a
                                     driver once (from docs/meite_layout.md if present)
"""
import math
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mecal  # noqa: E402

TITLE = "Motorsport Electronics Integrated Tuning Environment"
TABLE_KINDS = ("Table1dControl", "Table2dControl", "Table3dControl")


# ---------- connecting and tabs ----------
def window():
    from pywinauto import Desktop
    wins = [w for w in Desktop(backend="uia").windows() if w.window_text().startswith(TITLE)]
    if len(wins) != 1:
        sys.exit(f"expected one MEITE window, found {len(wins)}: is MEITE open?")
    return wins[0]


def _by_id(w, ctype, auto_id):
    return [e for e in w.descendants(control_type=ctype) if e.element_info.automation_id == auto_id]


def tabs(w):
    bar = _by_id(w, "MenuBar", "tabMenuStrip")[0]
    return {t.window_text(): t for t in bar.children()}


def active_tab(tb):
    on = [n for n, t in tb.items() if t.legacy_properties().get("State", 0) & 0x10]  # checked
    return on[0] if on else None


def goto(tb, name, timeout=5.0):
    """Select a view tab. This is the only action this module takes in MEITE."""
    for attempt in range(2):  # a busy UI (or a click by the user) can swallow the first invoke
        tb[name].invoke()
        end = time.time() + timeout
        while active_tab(tb) != name and time.time() < end:
            time.sleep(0.1)
        if active_tab(tb) == name:
            break
    else:
        raise RuntimeError(f"tab {name!r} did not become active (is someone using MEITE?)")
    time.sleep(0.8)  # let the view build its widgets


def loaded_name(w):
    """Status-bar labels; one of them is the open calibration's name."""
    bar = [e for e in w.descendants(control_type="StatusBar")][0]
    return [t.window_text() for t in bar.descendants(control_type="Text") if t.window_text()]


# ---------- reading a view ----------
def _settings(grid_table):
    """[(category, name, value)] in display order. Categories have no value of their own."""
    out = []
    for cat in grid_table.children(control_type="DataItem"):
        kids = cat.children(control_type="DataItem")
        if not kids:  # uncategorised setting
            out.append(("", cat.window_text(), cat.legacy_properties().get("Value", "")))
        for it in kids:
            out.append((cat.window_text(), it.window_text(), it.legacy_properties().get("Value", "")))
    return out


def read_view(w):
    """[{'kind': 'driver'|'table', 'name': str, 'settings': [...]}] for the current tab."""
    root = _by_id(w, "Pane", "ApplicationTab")[0].children()[0]
    widgets = []
    for wid in root.children():
        kind = wid.element_info.automation_id
        if kind == "DriverControl":
            panel = _by_id(wid, "Pane", "gridScrollPanel")
            label = [t.window_text() for t in _by_id(wid, "Text", "label") if t.window_text()]
            name = panel[0].window_text() if panel else (label[0] if label else "?")
            table = panel[0].descendants(control_type="Table") if panel else []
            widgets.append({"kind": "driver", "name": name,
                            "settings": _settings(table[0]) if table else []})
        elif kind in TABLE_KINDS:
            label = [t.window_text() for t in _by_id(wid, "Text", "label") if t.window_text()]
            widgets.append({"kind": "table", "name": label[0] if label else "?", "settings": []})
    return widgets


def driver_tabs(layout="docs/meite_layout.md"):
    """From a map file: the fewest tabs (first listed per driver) that show every driver."""
    if not os.path.exists(layout):
        return None
    need = set()
    for line in open(layout, encoding="utf-8"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 3 and cells[1] == "driver":
            need.add(cells[2].split(", ")[0])
    return need


def walk(w, only=None):
    """Visit every tab (or just those in `only`), return {tab: widgets}, then go back
    to the starting tab."""
    tb = tabs(w)
    start = active_tab(tb)
    views = {}
    try:
        for name in tb:
            if only is not None and name.strip() not in only:
                continue
            goto(tb, name)
            views[name] = read_view(w)
    finally:
        if start:
            goto(tb, start)
    return views


# ---------- map ----------
def write_map(views, path, cal=None):
    where = {}
    for tab, ws in views.items():
        for wd in ws:
            where.setdefault((wd["kind"], wd["name"]), []).append(tab)
    on_tabs = {name.split(" [")[0].strip() for _, name in where}
    L = ["# MEITE layout: where each setting and table lives",
         "",
         "Generated by `tools/meite_check.py map` from MEITE's view tabs. Names only; values live in the .mecal.",
         "Driver settings are readable in MEITE's UI; tables are custom-drawn (name only).",
         "",
         "## By tab", ""]
    for tab, ws in views.items():
        L.append(f"### {tab.strip()}")
        L.append("")
        if not ws:
            L.append("- (no drivers or tables; gauges or readouts only)")
        for wd in ws:
            if wd["kind"] == "table":
                L.append(f"- Table: {wd['name']}")
            else:
                cats = {}
                for cat, n, _ in wd["settings"]:
                    cats.setdefault(cat, []).append(n)
                body = "; ".join((f"*{c}*: " if c else "") + ", ".join(ns) for c, ns in cats.items())
                L.append(f"- Driver **{wd['name']}**: {body}")
        L.append("")
    L += ["## Index", "", "| Item | Kind | Tabs |", "| --- | --- | --- |"]
    for (kind, name), tl in sorted(where.items(), key=lambda kv: kv[0][1].lower()):
        L.append(f"| {name} | {kind} | {', '.join(t.strip() for t in tl)} |")
    if cal:
        r = mecal._root(cal)
        drv = sorted(d.findtext("name") for d in mecal.drivers(r) if d.findtext("name") not in on_tabs)
        tbl = sorted(t.findtext("name").strip() for t in mecal.tables(r)
                     if t.findtext("name").strip() not in on_tabs)
        L += ["", "## Not on any tab", "",
              f"In `{os.path.basename(cal)}` but on none of the view tabs: open these from MEITE's "
              "left-hand tree (or search box). Edit them in the .mecal with `tools/mecal.py` as usual.", "",
              f"- Drivers ({len(drv)}): " + ", ".join(drv),
              f"- Tables ({len(tbl)}): " + ", ".join(tbl)]
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")


# ---------- check ----------
def _label(file_value):
    """'0 (Open Loop)' -> 'Open Loop'; plain numbers unchanged."""
    m = re.match(r"^-?[\d.]+ \((.*)\)$", file_value or "")
    return m.group(1) if m else file_value


def _same(ui, fv):
    a, b = ui.strip(), _label(fv).strip()
    if a == b:
        return True
    try:
        return math.isclose(float(a), float(b), rel_tol=1e-4, abs_tol=1e-4)
    except ValueError:
        return False


def file_settings(path):
    """{driver: [(section, label as MEITE shows it, value)]}. MEITE appends the first
    measurement unit to the name ('MAP Min' -> 'MAP Min(KPa)') and groups by SectionName."""
    out = {}
    for d in mecal.drivers(mecal._root(path)):
        rows = out.setdefault(d.findtext("name"), [])
        for p in d.find("configParams"):
            mu = p.find("MeasurementUnitTypes")
            units = [u.tag for u in mu] if mu is not None else []
            label = p.findtext("name") + (f"({units[0]})" if units else "")
            rows.append((p.findtext("SectionName") or "", label, mecal._param_value(p)))
    return out


def _lookup(rows, category, name):
    hits = [r for r in rows if r[1] == name]
    if len(hits) > 1:  # repeated name, e.g. 'Enabled' under Oil Temp. and Oil Pressure
        hits = [r for r in hits if r[0] == category] or hits
    return hits[0] if len(hits) == 1 else None


def check(views, path, status):
    F = file_settings(path)
    D = mecal.flatten(path)
    seen, ok, bad, unknown = set(), 0, [], []
    for tab, ws in views.items():
        for wd in ws:
            if wd["kind"] != "driver" or wd["name"] in seen:
                continue
            seen.add(wd["name"])
            for cat, n, v in wd["settings"]:
                hit = _lookup(F.get(wd["name"], []), cat, n)
                where = f"{wd['name']} / {(cat + ' / ') if cat else ''}{n}"
                if hit is None:
                    unknown.append(f"{where} = {v!r} ({tab.strip()})")
                elif _same(v, hit[2]):
                    ok += 1
                else:
                    bad.append(f"{where}: MEITE {v!r}, file {hit[2]!r} ({tab.strip()})")
    stem = re.split(r"[\\/]", path)[-1].rsplit(".", 1)[0]
    connected = any(s.startswith("Connected") for s in status)
    open_ok = connected or stem in status
    if connected:
        print(f"connected to the ECU ({[s for s in status if s.startswith('Connected')][0]}): "
              f"comparing what the ECU holds with {stem}")
    else:
        print(f"open in MEITE: {'yes' if open_ok else 'NO'} (looking for {stem!r} in status bar {status})")
    print(f"{ok} settings match, {len(bad)} differ, {len(unknown)} not in file; "
          f"{len(seen)} drivers shown in MEITE's tabs")
    for b in bad:
        print("  DIFFERS", b)
    for u in unknown:
        print("  not in file:", u)
    not_on_tabs = sorted({k.split(" / ")[0] for k in D if " / " in k and not isinstance(D[k], float)} - seen)
    if not_on_tabs:
        print("drivers not on any tab (check in the left-hand tree):", ", ".join(not_on_tabs))
    return 0 if open_ok and not bad else 1


def main(argv):
    if len(argv) < 2 or argv[1] not in ("map", "check") or (argv[1] == "check" and len(argv) < 3):
        print(__doc__)
        return 1
    w = window()
    status = loaded_name(w)
    only = driver_tabs() if argv[1] == "check" else None
    views = walk(w, only)
    print(f"visited {len(views)} tabs: {', '.join(t.strip() for t in views)}")
    if argv[1] == "map":
        out = argv[2] if len(argv) > 2 else "docs/meite_layout.md"
        write_map(views, out, argv[3] if len(argv) > 3 else None)
        print(f"{len(views)} tabs mapped -> {out}")
        return 0
    return check(views, argv[2], status)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
