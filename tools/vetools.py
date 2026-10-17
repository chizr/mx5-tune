#!/usr/bin/env python3
"""VE table analysis from closed-loop logs: coverage, per-cell fuel need, smooth fit.

"Need" for a sample = lambda trim x measured AFR / target AFR: how much more fuel
the engine wanted than the base VE gave (1.20 = 20% more). Only steady, warm,
closed-loop, fuelled samples are used (no overrun, TPS and MAP not moving).

CLI:
  vetools.py coverage CAL LOG [LOG...]          steady seconds per VE cell
  vetools.py need CAL LOG [LOG...]              median need per cell (nearest cell)
  vetools.py fit CAL OUT_CAL LOG [LOG...]       smooth least-squares fit of the
        light-load region, written to OUT_CAL. CAL must be the calibration that
        was IN THE CAR when the logs were recorded. Options (anywhere):
        --into NEWEST           copy the fitted cells into this calibration instead
                                of CAL (use the latest version, or later edits are lost)
        --rows 1-5 --cols 1-7   free cell index range (default 24-64 kPa x 1250-3800 rpm)
        --lam 2                 curvature penalty (higher = smoother, less faithful)
        --rich 1.02:1-4         multiply rows 1-4 of the result by 1.02 (prefer rich)

The fit uses the ECU's bilinear interpolation weights, so each sample constrains
the four cells around it, plus a second-difference penalty along rpm and load.
Cells outside the free range stay fixed and act as boundary conditions. v14 was
made with: fit v12 v14 --into v13 --lam 2 --rich 1.02:1-4 on the 2026-10-16 and
2026-10-17 drives (both recorded with v10/v12, which share the same VE table).
"""
import sys
import numpy as np
import pandas as pd

import logtools
import mecal

T = 'Inj. Base VE (1)'


def table(cal):
    t = mecal.load(cal)
    xs = np.array(mecal.table_values(t, T, 'input_0'))
    ys = np.array(mecal.table_values(t, T, 'input_1'))
    return xs, ys, np.array(mecal.table_values(t, T)).reshape(len(ys), len(xs))


def steady(logs, clt=75):
    out = []
    for f in logs:
        d = logtools.load(f)
        d = d[(d.Time > 2) & (d.Time < d.Time.max() - 2) & (d['Coolant Temp.'] > clt) & (d.RPM > 500)].copy()
        d['hz'] = 1 / d.Time.diff().median()
        ok = (d.TPS.diff(3).abs() < 2) & (d.MAP.diff(3).abs() < 4)
        out.append(d[ok])
    return pd.concat(out)


def closed_loop(s):
    s = s[(s['Lambda Status'] == 16) & (s['Overrun Status'] == 0) & s['Lambda Curr AFR 1'].between(10, 20)].copy()
    s['need'] = (s['Inj. Lambda Trim'] * s['Lambda Curr AFR 1'] / s['Inj. Target AFR']).clip(0.7, 1.5)
    return s


def nearest(s, xs, ys):
    return (np.array([np.abs(ys - m).argmin() for m in s.MAP]),
            np.array([np.abs(xs - r).argmin() for r in s.RPM]))


def grid(m, xs, ys, fmt):
    df = pd.DataFrame(m, index=[f'{y:g}' for y in ys], columns=[f'{x / 1000:g}k' for x in xs]).iloc[::-1]
    return df.map(fmt).to_string()


def coverage(cal, logs):
    xs, ys, _ = table(cal)
    s = steady(logs)
    ri, ci = nearest(s, xs, ys)
    m = np.zeros((len(ys), len(xs)))
    np.add.at(m, (ri, ci), 1 / s.hz.values)
    print('steady seconds per VE cell ("." = none):')
    print(grid(m, xs, ys, lambda v: '.' if v < 0.5 else f'{v:.0f}'))


def need(cal, logs, min_n=30):
    xs, ys, _ = table(cal)
    s = closed_loop(steady(logs))
    ri, ci = nearest(s, xs, ys)
    m = np.full((len(ys), len(xs)), np.nan)
    g = pd.DataFrame({'r': ri, 'c': ci, 'n': s.need.values}).groupby(['r', 'c']).n.agg(['median', 'size'])
    for (r, c), row in g[g['size'] >= min_n].iterrows():
        m[r, c] = row['median']
    print(f'median fuel need per cell (cells with >= {min_n} samples):')
    print(grid(m, xs, ys, lambda v: '.' if np.isnan(v) else f'{v:.2f}'))


def _weights(v, ax):
    v = np.clip(v, ax[0], ax[-1])
    i = np.clip(np.searchsorted(ax, v) - 1, 0, len(ax) - 2)
    return i, (v - ax[i]) / (ax[i + 1] - ax[i])


def fit(cal, out, logs, rows=(1, 5), cols=(1, 7), lam=2.0, rich=None, into=None):
    xs, ys, ve = table(cal)
    ny, nx = ve.shape
    s = closed_loop(steady(logs))
    ci, cf = _weights(s.RPM.values, xs)
    ri, rf = _weights(s.MAP.values, ys)
    corners = [(ri, ci, (1 - cf) * (1 - rf)), (ri, ci + 1, cf * (1 - rf)), (ri + 1, ci, (1 - cf) * rf), (ri + 1, ci + 1, cf * rf)]
    old = sum(ve[r, c] * w for r, c, w in corners)
    target = s.need.values * old
    free = [(r, c) for r in range(rows[0], rows[1] + 1) for c in range(cols[0], cols[1] + 1)]
    idx = {rc: k for k, rc in enumerate(free)}
    A, b = [], []
    for k in range(len(s)):
        row, rhs = np.zeros(len(free)), target[k]
        for r, c, w in corners:
            if (r[k], c[k]) in idx:
                row[idx[(r[k], c[k])]] += w[k]
            else:
                rhs -= w[k] * ve[r[k], c[k]]
        if row.sum() > 0.05:
            A.append(row); b.append(rhs)
    A, b = np.array(A), np.array(b)
    R, rb = [], []
    for r in range(ny):
        for c in range(nx):
            for dr, dc in ((0, 1), (1, 0)):
                pts = [(r - dr, c - dc), (r, c), (r + dr, c + dc)]
                if not all(0 <= p[0] < ny and 0 <= p[1] < nx for p in pts) or not any(p in idx for p in pts):
                    continue
                row, rhs = np.zeros(len(free)), 0.0
                for p, co in zip(pts, (1, -2, 1)):
                    if p in idx:
                        row[idx[p]] += co
                    else:
                        rhs -= co * ve[p]
                R.append(row); rb.append(rhs)
    scale = lam * np.sqrt(len(b) / 1000)
    sol, *_ = np.linalg.lstsq(np.vstack([A, np.array(R) * scale]), np.concatenate([b, np.array(rb) * scale]), rcond=None)
    new = ve.copy()
    for (r, c), k in idx.items():
        new[r, c] = sol[k]
    if rich:
        f, (r0, r1) = rich
        new[r0:r1 + 1, cols[0]:cols[1] + 1] *= f
    t = mecal.load(into or cal)
    t = mecal.set_cells(t, T, {r * nx + c: round(float(new[r, c]), 2) for r, c in free})
    mecal.save(t, out)
    pred = sum(new[r, c] * w for r, c, w in corners) / old
    err = pred / s.need.values - 1
    print(f'{len(b)} samples. Median fuel error: before {np.median(1 / s.need.values - 1) * 100:+.1f}%, after {np.median(err) * 100:+.1f}% '
          f'(10-90%: {np.percentile(err, 10) * 100:+.0f}..{np.percentile(err, 90) * 100:+.0f}%). Wrote {out}')


def _range(v):
    a, b = v.split('-')
    return int(a), int(b)


if __name__ == '__main__':
    pos, opts, a = [], {}, sys.argv[1:]
    while a:
        x = a.pop(0)
        if x.startswith('--'):
            opts[x[2:]] = a.pop(0)
        else:
            pos.append(x)
    if len(pos) < 3:
        print(__doc__); sys.exit(1)
    cmd = pos[0]
    if cmd == 'coverage':
        coverage(pos[1], pos[2:])
    elif cmd == 'need':
        need(pos[1], pos[2:])
    elif cmd == 'fit' and len(pos) >= 4:
        rich = None
        if 'rich' in opts:
            f, rr = opts['rich'].split(':')
            rich = (float(f), _range(rr))
        fit(pos[1], pos[2], pos[3:], rows=_range(opts.get('rows', '1-5')), cols=_range(opts.get('cols', '1-7')),
            lam=float(opts.get('lam', 2)), rich=rich, into=opts.get('into'))
    else:
        print(__doc__); sys.exit(1)
