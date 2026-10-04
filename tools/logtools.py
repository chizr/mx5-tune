#!/usr/bin/env python3
"""Load and analyse ME442 CSV logs (SD-card OnBoardLog and MEITE PC logs).

Gotchas handled here:
  * data rows end with a trailing comma, so pandas must use index_col=False
    or every column shifts one place left;
  * MEITE PC logs put a space after each comma in the header (" RPM").

CLI:
  logtools.py summary LOG            duration, rate, ranges of key channels
  logtools.py lambda LOG             closed-loop lambda trim by rpm x MAP
  logtools.py knock LOG              per-cylinder knock rise vs own baseline
  logtools.py idle LOG               warm idle rpm / duty / AFR, by fan state
"""
import sys
import pandas as pd


def load(path):
    df = pd.read_csv(path, index_col=False, low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    return df.copy()


KEY = ["RPM", "MAP", "TPS", "VSS Speed", "Coolant Temp.", "Intake Air Temp.", "Oil Temp.",
       "Oil Press.", "Fuel Press.", "Battery Voltage", "Injector duty", "Ign. Adv. Final",
       "Lambda Curr AFR 1", "Inj. Lambda Trim", "Boost Final Duty", "Knock Reading Raw"]


def summary(df):
    t = df["Time"]
    print(f"{len(df)} rows, {t.iloc[-1]:.0f} s, ~{1 / t.diff().median():.0f} Hz")
    cols = [c for c in KEY if c in df]
    print(df[cols].describe().T[["min", "50%", "max"]].round(2).to_string())
    print("knock per-cylinder channels:", "Knock Cyl 1 Peak" in df)


def lambda_by_load(df):
    s = df[(df.get("Lambda Status", 16) == 16) & (df["Lambda Curr AFR 1"] < 20)].copy()
    s["rpm"] = pd.cut(s.RPM, [0, 1200, 1800, 2500, 3200, 4100, 5500, 8000])
    s["map"] = pd.cut(s.MAP, [0, 25, 35, 45, 60, 80, 100, 120, 160, 240])
    print("mean closed-loop trim (1.10 = ECU adding 10% fuel):")
    print(s.pivot_table(index="map", columns="rpm", values="Inj. Lambda Trim",
                        aggfunc="mean", observed=True).round(2).to_string())
    print(f"time at +/-20% limit: {(df['Inj. Lambda Trim'] >= 1.195).mean():.1%} / "
          f"{(df['Inj. Lambda Trim'] <= 0.805).mean():.1%}")


def knock_ratios(df):
    """Each cylinder's 90th-percentile peak relative to its own 35-60 kPa reading
    at the same rpm. The single sensor hears cyl 2/3 loudest, so compare ratios,
    not raw levels. Cyl 2/3 rising much more than 1/4 under load = suspect knock."""
    P = [f"Knock Cyl {c} Peak" for c in range(1, 5)]
    if P[0] not in df:
        print("no per-cylinder knock channels in this log"); return
    d = df.copy()
    d["rpm"] = pd.cut(d.RPM, [0, 1200, 2000, 3000, 4000, 5200, 8000])
    d["map"] = pd.cut(d.MAP, [0, 35, 60, 90, 110, 140, 240])
    q = d.groupby(["rpm", "map"], observed=True)[P].quantile(0.9)
    q.columns = ["c1", "c2", "c3", "c4"]
    base_iv = pd.Interval(35, 60, closed="right")
    for rb in q.index.get_level_values(0).unique():
        sub = q.xs(rb, level="rpm")
        if base_iv not in sub.index:
            continue
        print(f"\nrpm {rb}  (ratio vs own 35-60 kPa)")
        print((sub / sub.loc[base_iv]).round(2).to_string())


def idle(df):
    i = df[(df.TPS < 1) & (df["VSS Speed"] < 1) & (df["Coolant Temp."] > 80)]
    if "Idle Status" in i:
        i = i[i["Idle Status"] == 5]
    cols = [c for c in ["RPM", "Idle PWM Duty", "Lambda Curr AFR 1", "Inj. Lambda Trim",
                        "Ign. Adv. Final", "Battery Voltage", "MAP"] if c in i]
    by = "Pri. Fan Status" if "Pri. Fan Status" in i else None
    print(len(i), "warm idle samples")
    print((i.groupby(by)[cols].median() if by else i[cols].median()).round(2).to_string())


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    fn = {"summary": summary, "lambda": lambda_by_load, "knock": knock_ratios, "idle": idle}[sys.argv[1]]
    fn(load(sys.argv[2]))
