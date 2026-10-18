#!/usr/bin/env python3
"""Record speed from a Dragy GPS (BLE) alongside ECU logs. Windows/Linux/macOS, needs `bleak`.

Protocol (Dragy V7.0, firmware MD69 2.0.00; worked out from the Dragy app's Bluetooth
traffic on 2026-10-18): after connecting, the app reads a 2-byte challenge from
characteristic fd03, writes a 4-byte answer back (the Dragy drops the link if it's wrong), and
enables notifications on fd02. The answer function is kept in tools/dragy_secret.py, which is
git-ignored and not published. fd02 then streams ASCII lines at 10 Hz:

  @,speed,hhmmss.ss(UTC),lat,lon,fix(0/1),sats,hdop,altitude,N/S,E/W,course,

Position (lat, lon, hemispheres) and altitude are DROPPED here before anything is written:
this repo is public. Saved columns: unix time, GPS UTC time, speed (as sent; unit to be
confirmed against the ECU's VSS: probably km/h), fix, sats, hdop, course.

The Dragy talks to one device at a time: close the Dragy phone app first, and don't pair it
in Windows (bleak connects without pairing).

CLI:
  dragy.py record SECONDS OUT.csv     record (prints a status line every 5 s)
"""
import asyncio
import csv
import sys
import time

from bleak import BleakClient, BleakScanner

START_CHAR = "0000fd03-0000-1000-8000-00805f9b34fb"
try:  # handshake answer lives in a local, git-ignored file (not published)
    from dragy_secret import answer as handshake_answer
except ImportError:
    handshake_answer = None
DATA_CHAR = "0000fd02-0000-1000-8000-00805f9b34fb"
COLUMNS = ["unix_time", "gps_utc", "speed", "fix", "sats", "hdop", "course"]


def parse(line):
    """One '@' sentence -> dict without position/altitude, or None."""
    f = line.strip().split(",")
    if len(f) < 12 or f[0] != "@":
        return None
    num = lambda s: float(s) if s not in ("", None) else None
    return {"gps_utc": f[2], "speed": num(f[1]), "fix": int(f[5] or 0), "sats": int(f[6] or 0),
            "hdop": num(f[7]), "course": num(f[11])}


async def record(seconds, out):
    dev = await BleakScanner.find_device_by_filter(lambda d, ad: (d.name or "").startswith("DRG"), timeout=20)
    if not dev:
        sys.exit("Dragy not found (powered? phone app closed?)")
    buf = bytearray()
    rows = []

    def on_data(_, data):
        nonlocal buf
        buf += data
        while b"\r\n" in buf:
            line, _, rest = bytes(buf).partition(b"\r\n")
            buf = bytearray(rest)
            r = parse(line.decode("ascii", "replace"))
            if r:
                r["unix_time"] = round(time.time(), 3)
                rows.append(r)

    if handshake_answer is None:
        sys.exit("tools/dragy_secret.py (local, not in the repo) is missing: no handshake answer")
    async with BleakClient(dev, timeout=40) as c:
        token = bytes(await c.read_gatt_char(START_CHAR))[:2]
        await c.write_gatt_char(START_CHAR, handshake_answer(token), response=True)
        await c.start_notify(DATA_CHAR, on_data)
        print(f"connected to {dev.name} (MTU {c.mtu_size}, token {token.hex()}); "
              f"recording {seconds:.0f} s -> {out}", flush=True)
        with open(out, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=COLUMNS)
            w.writeheader()
            t0, written = time.time(), 0
            while time.time() - t0 < seconds:
                await asyncio.sleep(5)
                for r in rows[written:]:
                    w.writerow(r)
                fh.flush()
                new = rows[written:]
                written = len(rows)
                last = new[-1] if new else None
                print(f"{time.strftime('%H:%M:%S')} {len(new) / 5:.1f} Hz"
                      + (f", fix {last['fix']}, sats {last['sats']}, hdop {last['hdop']}, speed {last['speed']}"
                         if last else ", no data"), flush=True)
            for r in rows[written:]:
                w.writerow(r)
        if c.is_connected:
            await c.stop_notify(DATA_CHAR)
        else:
            print("note: the Dragy disconnected before the end", flush=True)
    print(f"saved {len(rows)} samples", flush=True)


if __name__ == "__main__":
    if len(sys.argv) < 4 or sys.argv[1] != "record":
        print(__doc__)
        sys.exit(1)
    asyncio.run(record(float(sys.argv[2]), sys.argv[3]))
