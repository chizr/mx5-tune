#!/usr/bin/env python3
"""Live ECU data from MEITE's Comms Log window (Windows only; needs pywinauto, pywin32).

MEITE shows every frame it receives from the ECU in Logging -> Comms. Log as hex text.
This reads that text in the background (window messages only: it never takes focus,
clicks or types), decodes the frames, then deletes just the text it has read so the
box doesn't grow without limit. Frames MEITE appends after a read are kept, because
the delete covers only what was there when it was read, cut at a whole line.

It never writes to the ECU or changes MEITE's settings. If the Comms Log isn't open it
opens it from the Logging menu (a menu command, no focus change).

Frame (ME442-V2B-PNP, firmware 4.2.1, DEF v62): 840 bytes, "ME", uint16 LE length (831),
little-endian fields, 2-byte checksum at the end. Field offsets come from
tools/meite_frame_map.json (built by meite_framemap.py from a capture); channels that
haven't varied in a capture yet aren't mapped.

CLI:
  meite_comms.py watch [SECONDS] [--keep]   print frame rate and key fields once a second
                                            (--keep: don't trim the Comms Log)
  meite_comms.py capture SECONDS OUT.txt    start PC logging, save every frame with a
                                            timestamp for SECONDS, stop PC logging; feed
                                            both to meite_framemap.py to extend the map
"""
import glob
import json
import os
import re
import struct
import sys
import time

FRAME_LEN = 840
LINE = re.compile(r"ECU -> PC\(COM\d+\):\s*([0-9A-F]{2}(?:-[0-9A-F]{2})*)")
MAIN_TITLE = "Motorsport Electronics Integrated Tuning Environment"
MAP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "meite_frame_map.json")
FMT = {"f32": "<f", "u8": "<B", "i8": "<b", "u16": "<H", "i16": "<h", "u32": "<I", "i32": "<i"}
# Found at key-on only (value constant in the mapping capture): provisional.
EXTRA = {"Intake Air Temp.": {"offset": 17, "type": "i16", "scale": 1}}
WATCH = ["RPM", "MAP", "Lambda Curr AFR 1", "Inj. Lambda Trim", "Ign. Adv. Final", "Coolant Temp.",
         "Intake Air Temp.", "Oil Press.", "Fuel Press.", "Battery Voltage"]


def load_map():
    chans = dict(EXTRA)
    if os.path.exists(MAP_PATH):
        chans.update(json.load(open(MAP_PATH))["channels"])
    return chans


CHANNELS = load_map()


def decode(frame, names=None):
    out = {}
    for k in (names or CHANNELS):
        c = CHANNELS.get(k)
        if c:
            out[k] = struct.unpack_from(FMT[c["type"]], frame, c["offset"])[0] * c["scale"]
    return out


class CommsLog:
    def __init__(self, trim=True):
        import win32api
        import win32con
        import win32gui
        from pywinauto import Desktop
        self._api, self._con, self._gui = win32api, win32con, win32gui
        self.trim = trim
        win = self._find(Desktop)
        if win is None:
            self._open_from_menu()
            time.sleep(1.5)
            win = self._find(Desktop)
        if win is None:
            raise RuntimeError("Comms Log window not found (is MEITE open and connected?)")
        self.edit = [c for c in win.descendants() if c.class_name().startswith("WindowsForms10.EDIT")][0]

    @staticmethod
    def _find(Desktop):
        w = [w for w in Desktop(backend="win32").windows() if w.window_text() == "Comms Log"]
        return w[0] if w else None

    @staticmethod
    def _open_from_menu():
        from pywinauto import Application
        main = Application(backend="win32").connect(title_re=MAIN_TITLE + ".*").top_window()
        log = [t for t in main.menu().items() if t.text().replace("&", "") == "Logging"][0]
        item = [i for i in log.sub_menu().items() if i.text().split("\t")[0].strip().lower() == "comms. log"]
        item[0].select()  # posts the menu command; MEITE stays in the background

    def read(self):
        """Return complete frames received since the last read; trim what was read."""
        txt = self.edit.window_text()
        cut = txt.rfind("\n") + 1
        frames = [bytes.fromhex(f.replace("-", "")) for f in LINE.findall(txt[:cut])]
        if self.trim and cut:
            h = self.edit.handle
            self._api.SendMessage(h, self._con.EM_SETSEL, 0, cut)
            self._gui.SendMessage(h, self._con.EM_REPLACESEL, 0, "")
        return [f for f in frames if len(f) == FRAME_LEN and f[:2] == b"ME"]

    def length(self):
        return self._gui.SendMessage(self.edit.handle, self._con.WM_GETTEXTLENGTH, 0, 0)


def watch(seconds, trim=True):
    log = CommsLog(trim=trim)
    log.read()  # drop the backlog
    t0 = time.time()
    total = 0
    while time.time() - t0 < seconds:
        time.sleep(1.0)
        fr = log.read()
        total += len(fr)
        rate = total / (time.time() - t0)
        vals = decode(fr[-1], WATCH) if fr else {}
        shown = "  ".join(f"{k}={v:.4g}" for k, v in vals.items())
        print(f"{time.time() - t0:5.1f}s  {len(fr):3d} frames ({rate:4.1f}/s)  box {log.length():>7} chars  {shown}")
    return total


def _logging_menu(want):
    from pywinauto import Application
    main = Application(backend="win32").connect(title_re=MAIN_TITLE + ".*").top_window()
    log = [t for t in main.menu().items() if t.text().replace("&", "") == "Logging"][0]
    item = [i for i in log.sub_menu().items() if i.text().split("\t")[0].strip().lower() == want]
    if len(item) != 1:
        raise SystemExit(f"Logging menu item {want!r} not found (PC logging already in that state?)")
    item[0].select()


def capture(seconds, out):
    """PC log + every Comms Log frame over the same window, for meite_framemap.py."""
    logdir = os.path.expandvars(r"%USERPROFILE%\OneDrive\Desktop\MELogs")
    log = CommsLog(trim=True)
    log.read()
    before = set(glob.glob(os.path.join(logdir, "*.csv")))
    _logging_menu("start pc logging")
    t0, n = time.time(), 0
    try:
        with open(out, "w") as f:
            while time.time() - t0 < seconds:
                time.sleep(0.5)
                fr = log.read()
                now = time.time()
                for k, b in enumerate(fr):  # spread over the batch at ~10 Hz
                    f.write(f"{now - 0.1 * (len(fr) - 1 - k):.3f} {b.hex()}\n")
                n += len(fr)
    finally:
        _logging_menu("stop pc logging")
    time.sleep(2)
    new = sorted(set(glob.glob(os.path.join(logdir, "*.csv"))) - before)
    print(f"{n} frames ({n / (time.time() - t0 - 2):.1f}/s) -> {out}")
    print("PC log:", new, "(StartTime is in MELogs/LoggingInfo.xml)")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "watch":
        secs = float(sys.argv[2]) if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else 10
        watch(secs, trim="--keep" not in sys.argv)
    elif cmd == "capture" and len(sys.argv) > 3:
        capture(float(sys.argv[2]), sys.argv[3])
    else:
        print(__doc__)
        sys.exit(1)
