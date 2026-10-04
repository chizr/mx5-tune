#!/usr/bin/env python3
"""Read, diff and edit ME442 / MEITE calibration files (.mecal).

A .mecal file is UTF-8 XML with CRLF line endings. Edits made here replace
values in place as text, so every byte outside the changed values is kept
exactly as MEITE wrote it. Never re-serialise the XML with a library.

CLI:
  mecal.py dump FILE                 human-readable listing (used as git textconv)
  mecal.py diff OLD NEW              semantic diff of settings and tables
  mecal.py table FILE NAME|ID        print one table as a grid
  mecal.py params FILE NAME|ID       print one driver's settings
  mecal.py find FILE TEXT            list tables/drivers whose name contains TEXT

Library (import mecal):
  txt = mecal.load(path)             -> str
  txt = mecal.set_param(txt, driver, param, value, occurrence=0)
  txt = mecal.set_cells(txt, table, {flat_index: value}, tag="output")
  mecal.save(txt, path)              writes bytes and checks the XML parses
  mecal.table_values(txt, table, tag) -> list[float]
"""
import re
import sys
import xml.etree.ElementTree as ET


# ---------- loading / saving ----------
def load(path):
    with open(path, "rb") as f:
        return f.read().decode("utf-8")


def save(txt, path):
    ET.fromstring(txt.encode("utf-8"))  # raises if the XML is broken
    with open(path, "wb") as f:
        f.write(txt.encode("utf-8"))


def _root(path_or_txt):
    if path_or_txt.lstrip().startswith("<"):
        return ET.fromstring(path_or_txt.encode("utf-8"))
    return ET.parse(path_or_txt).getroot()


# ---------- text-level block location ----------
def _block(txt, kind, key):
    """Return the regex match for a <TableModel>/<DriverModel> by id or exact name."""
    pat = rf"<{kind}>(?:(?!</{kind}>).)*?</{kind}>"
    hits = []
    for m in re.finditer(pat, txt, re.S):
        b = m.group(0)
        bid = re.search(r"<id>([^<]*)</id>", b).group(1)
        name = re.search(r"<name>([^<]*)</name>", b).group(1).strip()
        if str(key) == bid or str(key).strip() == name:
            hits.append(m)
    if len(hits) != 1:
        raise KeyError(f"{kind} {key!r}: {len(hits)} matches")
    return hits[0]


def _fmt(v):
    return f"{float(v):g}"


def set_param(txt, driver, param, value, occurrence=0):
    """Set a driver setting. Some drivers repeat a name (e.g. 'Enabled' twice in
    'EPS: Oil'); pass occurrence=1 for the second one."""
    m = _block(txt, "DriverModel", driver)
    b = m.group(0)
    params = [p for p in re.finditer(r"<DriverModelParam>.*?</DriverModelParam>", b, re.S)
              if re.search(r"<name>" + re.escape(param) + r"</name>",
                           p.group(0).split("<options>")[0])]
    if len(params) <= occurrence:
        raise KeyError(f"{driver!r} has no param {param!r} (occurrence {occurrence})")
    p = params[occurrence]
    s = p.group(0)
    v = list(re.finditer(r"<value>([^<]*)</value>", s))
    assert len(v) == 1
    s2 = s[:v[0].start(1)] + _fmt(value) + s[v[0].end(1):]
    b2 = b[:p.start()] + s2 + b[p.end():]
    return txt[:m.start()] + b2 + txt[m.end():]


def table_values(txt, table, tag="output"):
    m = _block(txt, "TableModel", table)
    inner = re.search(rf"<{tag}>(.*?)</{tag}>", m.group(0), re.S).group(1)
    return [float(x) for x in re.findall(r"<float>([^<]*)</float>", inner)]


def set_cells(txt, table, changes, tag="output"):
    """changes = {flat_index: value}. For 2D tables index = row * cols + col,
    where rows follow input_1 (load) and cols follow input_0 (rpm)."""
    m = _block(txt, "TableModel", table)
    b = m.group(0)
    om = re.search(rf"<{tag}>(.*?)</{tag}>", b, re.S)
    inner = om.group(1)
    floats = list(re.finditer(r"<float>([^<]*)</float>", inner))
    for i, v in sorted(changes.items(), reverse=True):
        f = floats[i]
        inner = inner[:f.start()] + f"<float>{_fmt(v)}</float>" + inner[f.end():]
    b2 = b[:om.start(1)] + inner + b[om.end(1):]
    return txt[:m.start()] + b2 + txt[m.end():]


# ---------- parsed views ----------
def _floats(e):
    return [float(x.text) for x in e.findall("float")] if e is not None else []


def tables(root):
    yield from root.find("tables")


def drivers(root):
    yield from root.find("drivers")


def _param_value(p):
    v = p.findtext("value")
    for o in p.iter("comboBoxOption"):
        if o.findtext("id") == v:
            return f"{v} ({o.findtext('name')})"
    return v


def fmt_table(t):
    g = lambda v: f"{v:g}"
    cols, rows = int(t.findtext("cols")), int(t.findtext("rows"))
    x, y, o = _floats(t.find("input_0")), _floats(t.find("input_1")), _floats(t.find("output"))
    out = [f"## TABLE {t.findtext('id')} {t.findtext('name').strip()}  "
           f"[x={t.findtext('input_0_name')} y={t.findtext('input_1_name')} out={t.findtext('output_name')}]"]
    out.append("        " + " ".join(f"{g(v):>7}" for v in x))
    if rows > 1:
        for j in range(rows):
            out.append(f"{g(y[j]):>7} " + " ".join(f"{g(o[j*cols+k]):>7}" for k in range(cols)))
    else:
        out.append("        " + " ".join(f"{g(v):>7}" for v in o))
    return "\n".join(out)


def fmt_driver(d):
    out = [f"## DRIVER {d.findtext('id')} {d.findtext('name')}"]
    for p in d.find("configParams"):
        out.append(f"  {p.findtext('name')}: {_param_value(p)}")
    return "\n".join(out)


def dump(path):
    r = _root(path)
    parts = [fmt_driver(d) for d in sorted(drivers(r), key=lambda d: d.findtext("name"))]
    parts += [fmt_table(t) for t in sorted(tables(r), key=lambda t: t.findtext("name").strip())]
    return "\n\n".join(parts) + "\n"


def flatten(path):
    r = _root(path)
    D = {}
    for d in drivers(r):
        seen = {}
        for p in d.find("configParams"):
            n = p.findtext("name"); seen[n] = seen.get(n, 0) + 1
            key = f"{d.findtext('name')} / {n}" + (f" #{seen[n]}" if seen[n] > 1 else "")
            D[key] = _param_value(p)
    for t in tables(r):
        for tag in ("input_0", "input_1", "output"):
            for i, v in enumerate(_floats(t.find(tag))):
                D[f"{t.findtext('name').strip()} / {tag}[{i}]"] = v
    return D


def diff(a, b):
    A, B = flatten(a), flatten(b)
    lines = []
    for k in sorted(set(A) | set(B)):
        va, vb = A.get(k), B.get(k)
        if isinstance(va, float) and isinstance(vb, float) and abs(va - vb) < 1e-4:
            continue
        if va != vb:
            lines.append(f"{k}: {va} -> {vb}")
    return "\n".join(lines)


def main(argv):
    if len(argv) < 3:
        print(__doc__); return 1
    cmd, f = argv[1], argv[2]
    if cmd == "dump":
        sys.stdout.write(dump(f))
    elif cmd == "diff":
        print(diff(f, argv[3]) or "(no differences)")
    elif cmd in ("table", "params"):
        r = _root(f); key = argv[3]
        items = tables(r) if cmd == "table" else drivers(r)
        for e in items:
            if key in (e.findtext("id"), e.findtext("name").strip()):
                print(fmt_table(e) if cmd == "table" else fmt_driver(e)); return 0
        print(f"not found: {key}"); return 1
    elif cmd == "find":
        r = _root(f); q = argv[3].lower()
        for e in list(drivers(r)) + list(tables(r)):
            if q in e.findtext("name").lower():
                kind = "driver" if e.find("configParams") is not None else "table"
                print(f"{kind:6} {e.findtext('id')}  {e.findtext('name').strip()}")
    else:
        print(__doc__); return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
