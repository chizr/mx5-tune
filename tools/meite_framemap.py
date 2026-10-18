#!/usr/bin/env python3
"""Build the ECU frame map (tools/meite_frame_map.json) from a paired capture: a MEITE PC log
plus the Comms Log frames recorded at the same time (meite_comms.py capture).

Method: pair each PC-log row with the frame it came from (key raw channels match exactly),
then for each channel find the (offset, type, scale) that reproduces the logged value, to the
CSV's 2-decimal rounding, in >= 97% of rows. Only channels that vary during the capture can
be located; constant ones are listed as unmapped. Where several widths fit one offset, the
width is limited by the next mapped offset, and temperatures / errors / deltas get signed types.
Merge mode keeps earlier entries and adds or confirms channels from a new capture.

CLI:
  meite_framemap.py build PCLOG.csv START_ISO FRAMES.txt [--merge]
      START_ISO: the log's StartTime from MELogs/LoggingInfo.xml
      FRAMES.txt: '<unix time> <hex frame>' per line (meite_comms.py capture)
"""
import json
import os
import sys
from datetime import datetime

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import logtools  # noqa: E402

MAP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "meite_frame_map.json")
TYPES = {"f32": ("<f4", 4), "u8": ("u1", 1), "i8": ("i1", 1), "u16": ("<u2", 2), "i16": ("<i2", 2),
         "u32": ("<u4", 4), "i32": ("<i4", 4)}
KEYS = ["RPM", "Coolant Temp. Raw", "O2 Raw", "Oil Temp. Raw", "Oil Press. Raw", "MAP Raw",
        "Battery Voltage Raw", "Int. WB UA Raw"]
SIGNED_HINTS = ("Temp.", "Err", "Delta", "Adv", "Trim", "Angle")


def load_frames(path):
    rows = [l.split() for l in open(path) if l.strip()]
    ft = np.array([float(r[0]) for r in rows])
    F = np.frombuffer(b"".join(bytes.fromhex(r[1]) for r in rows), dtype=np.uint8).reshape(len(rows), -1)
    return ft, F


def series(F, off, typ):
    dt, n = TYPES[typ]
    with np.errstate(all="ignore"):
        return np.ascontiguousarray(F[:, off:off + n]).view(dt).ravel().astype(float)


def locate(df, ut, ft, F, key_map):
    """Pair rows to frames using channels already known (key_map: name -> (off, type))."""
    keys = {c: series(F, *key_map[c]) for c in KEYS if c in key_map and c in df}
    pair, score = np.full(len(df), -1), np.zeros(len(df))
    for i in range(len(df)):
        g = int(np.searchsorted(ft, ut[i]))
        lo, hi = max(0, g - 20), min(len(ft), g + 20)
        s = sum((keys[c][lo:hi] == df[c].values[i]).astype(int) for c in keys)
        pair[i], score[i] = lo + int(np.argmax(s)), s.max()
    need = max(3, len(keys) - 2)
    return pair[score >= need], df[score >= need], len(keys), need


def scan(F, P, y):
    """Candidates that reproduce y in >= 97% of rows AND in >= 95% of the rows where y is
    away from its most common value (otherwise a mostly-zero channel matches any mostly-zero
    byte). Channels with fewer than 20 such rows are too sparse to locate."""
    L = F.shape[1]
    vals, counts = np.unique(y, return_counts=True)
    off_mode = y != vals[np.argmax(counts)]
    if off_mode.sum() < 20:
        return []
    hits = []
    for off in range(4, L - 2):
        for typ, (_, n) in TYPES.items():
            if off + n > L - 2:
                continue
            x = series(F, off, typ)[P]
            if not np.all(np.isfinite(x)):
                continue
            for scale in (1, 0.1, 0.01, 0.001):
                ok = np.abs(x * scale - y) <= 0.0051 + np.abs(y) * 1e-6
                frac, frac_var = float(np.mean(ok)), float(np.mean(ok[off_mode]))
                if frac >= 0.97 and frac_var >= 0.95:
                    hits.append({"offset": off, "type": typ, "scale": scale, "frac": round(frac, 3),
                                 "frac_varying": round(frac_var, 3)})
                    break
    return hits


def choose(name, hits, next_off):
    """Pick one hit: lowest offset; width limited by the next mapped offset; f32 first,
    then signed for temperatures/errors, else unsigned."""
    off = min(h["offset"] for h in hits)
    at = [h for h in hits if h["offset"] == off]
    room = (next_off - off) if next_off else 4
    signed = any(s in name for s in SIGNED_HINTS) and "Raw" not in name  # raw ADC counts are unsigned
    order = ["f32"] + (["i16", "i8", "u16", "u8"] if signed else ["u16", "u8", "i16", "i8"]) + ["u32", "i32"]
    fit = [h for t in order for h in at if h["type"] == t and TYPES[t][1] <= room]
    pick = fit[0] if fit else at[0]
    alts = sorted({h["offset"] for h in hits} - {off})
    return {**pick, "alt_offsets": alts}


def build(csv, start_iso, frames, merge):
    df = logtools.load(csv)
    ut = datetime.fromisoformat(start_iso).timestamp() + df["Time"].values
    ft, F = load_frames(frames)
    old = json.load(open(MAP_PATH)) if (merge and os.path.exists(MAP_PATH)) else {"channels": {}}
    seed = {c: (v["offset"], v["type"]) for c, v in old["channels"].items()}
    seed = seed or {"RPM": (537, "u16"), "Coolant Temp. Raw": (19, "u16"), "O2 Raw": (592, "u16"),
                    "Oil Temp. Raw": (43, "u16"), "Oil Press. Raw": (47, "u16"), "MAP Raw": (572, "u16"),
                    "Battery Voltage Raw": (9, "u16"), "Int. WB UA Raw": (771, "u16")}
    P, Y, nkeys, need = locate(df, ut, ft, F, seed)
    print(f"paired {len(P)} of {len(df)} rows (>= {need} of {nkeys} key channels exact)")
    cols = [c for c in df.columns if c not in ("Time", "Marker") and not c.startswith("Unnamed")]
    found, constant = {}, []
    for c in cols:
        y = Y[c].values.astype(float)
        if np.std(y) <= 1e-6:
            constant.append(c)
            continue
        hits = scan(F, P, y)
        if hits:
            found[c] = hits
        else:
            print("  no exact match:", c)
    firsts = sorted({min(h["offset"] for h in hs) for hs in found.values()} |
                    {v["offset"] for v in old["channels"].values()})
    chans = dict(old["channels"])
    for c, hs in found.items():
        off = min(h["offset"] for h in hs)
        nxt = next((o for o in firsts if o > off), None)
        entry = choose(c, hs, nxt)
        prev = chans.get(c)
        entry["captures"] = (prev.get("captures", 0) if prev else 0) + 1
        if prev and (prev["offset"], prev["type"]) != (entry["offset"], entry["type"]):
            entry["conflict"] = f"earlier capture had @{prev['offset']} {prev['type']}"
        chans[c] = entry
    unmapped = sorted(set(old.get("unmapped", [])) | set(constant)) if merge else sorted(constant)
    unmapped = [c for c in unmapped if c not in chans]
    out = {"frame_len": int(F.shape[1]), "product": "ME442-V2B-PNP", "firmware": "4.2.1", "def_version": 62,
           "note": "Offsets found by matching a PC log to Comms Log frames recorded together. "
                   "alt_offsets: other places the same values appeared (copies, or equal channels).",
           "channels": dict(sorted(chans.items(), key=lambda kv: kv[1]["offset"])), "unmapped": unmapped}
    json.dump(out, open(MAP_PATH, "w", newline="\n"), indent=1)
    print(f"{len(found)} channels located this capture; map now has {len(chans)}; "
          f"{len(unmapped)} unmapped (constant in every capture so far) -> {MAP_PATH}")


if __name__ == "__main__":
    if len(sys.argv) < 5 or sys.argv[1] != "build":
        print(__doc__)
        sys.exit(1)
    build(sys.argv[2], sys.argv[3], sys.argv[4], "--merge" in sys.argv)
