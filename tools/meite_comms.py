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
little-endian fields, 2-byte checksum at the end. Field offsets below were found by
matching key-on values and are provisional until a full mapping run (engine running,
PC log alongside) confirms them.

CLI:
  meite_comms.py watch [SECONDS]     print frame rate and decoded fields once a second
  meite_comms.py watch SECONDS --keep  same, but don't trim the Comms Log
"""
import re
import struct
import sys
import time

FRAME_LEN = 840
LINE = re.compile(r"ECU -> PC\(COM\d+\):\s*([0-9A-F]{2}(?:-[0-9A-F]{2})*)")
MAIN_TITLE = "Motorsport Electronics Integrated Tuning Environment"

# name: (offset, struct format). Provisional: from key-on matching on 2026-10-17.
FIELDS = {
    "Battery Voltage": (11, "<f"),
    "Intake Air Temp.": (17, "<H"),
    "Coolant Temp.": (21, "<H"),
    "Oil Temp.": (45, "<H"),
    "Lambda Curr AFR 1": (316, "<f"),
    "MAP": (574, "<f"),
}


def decode(frame):
    return {k: struct.unpack_from(fmt, frame, off)[0] for k, (off, fmt) in FIELDS.items()}


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
        vals = decode(fr[-1]) if fr else {}
        shown = "  ".join(f"{k.split()[0]} {v:.2f}" if isinstance(v, float) else f"{k.split()[0]} {v}"
                          for k, v in vals.items())
        print(f"{time.time() - t0:5.1f}s  {len(fr):3d} frames ({rate:4.1f}/s)  box {log.length():>7} chars  {shown}")
    return total


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] != "watch":
        print(__doc__)
        sys.exit(1)
    secs = float(sys.argv[2]) if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else 10
    watch(secs, trim="--keep" not in sys.argv)
