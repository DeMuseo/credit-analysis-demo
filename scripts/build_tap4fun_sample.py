#!/usr/bin/env python3
"""Build a Gradio-friendly Tap4Fun / DataCastle pay-prediction sample.

Public Baidu mirrors referenced by wanlida/2018_datacastle_tap4fun_consumption_predict
are cancelled; Heywhale (kesci) hosts tap_fun_train.zip but requires login for downloadUrl.
This script produces a schema-faithful stratified sample calibrated to published
competition aggregates (付费率≈2%, stronghold×PUR curve, ARPU/online-time contrasts)
so the portfolio demo loads offline with realistic China F2P monetization metrics.

Column names match the official 109-field Tap4Fun train schema (subset kept for size).
No personal names.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "data" / "tap4fun_sample.csv"
N = 100_000
SEED = 42

# Stronghold level count + 45d pay rate from zhiwei16/tap4fun eda.ipynb embedded charts
SH_COUNTS = np.array(
    [
        940446, 305723, 283449, 158473, 174717, 161211, 90890, 69298,
        52106, 31809, 12689, 3863, 1510, 738, 462, 254, 119, 77, 62, 56, 40, 12, 2, 1,
    ],
    dtype=float,
)
SH_PUR = np.array(
    [
        0.005, 0.002, 0.0032, 0.0056, 0.0063, 0.0091, 0.0246, 0.0579,
        0.1232, 0.3033, 0.5842, 0.8447, 0.9662, 0.9905, 1.0, 1.0, 1.0, 1.0,
        1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
    ],
    dtype=float,
)

# 7d pay-price band shares among 7d payers (eda cell31)
BANDS_7D = [
    (0.01, 1.0, 0.3811),
    (1.0, 10.0, 0.3210),
    (10.0, 100.0, 0.2488),
    (100.0, 1000.0, 0.0449),
    (1000.0, 8000.0, 0.0042),
]
# 45d bands among 45d payers
BANDS_45D = [
    (0.01, 1.0, 0.3370),
    (1.0, 10.0, 0.2998),
    (10.0, 100.0, 0.2630),
    (100.0, 1000.0, 0.0831),
    (1000.0, 30000.0, 0.0171),
]


def _sample_from_bands(rng: np.random.Generator, n: int, bands) -> np.ndarray:
    probs = np.array([b[2] for b in bands], dtype=float)
    probs = probs / probs.sum()
    idx = rng.choice(len(bands), size=n, p=probs)
    out = np.empty(n, dtype=float)
    for i, (lo, hi, _) in enumerate(bands):
        mask = idx == i
        k = int(mask.sum())
        if k == 0:
            continue
        # log-uniform within band
        out[mask] = np.exp(rng.uniform(np.log(lo), np.log(hi), size=k))
    return np.round(out, 2)


def main() -> None:
    rng = np.random.default_rng(SEED)
    probs = SH_COUNTS / SH_COUNTS.sum()
    levels = rng.choice(np.arange(len(SH_COUNTS)), size=N, p=probs)

    # Scale level PUR so overall ≈ 2.01% (published 45d) while keeping shape
    raw_p = SH_PUR[levels]
    target = 0.0201
    scale = target / raw_p.mean()
    p45 = np.clip(raw_p * scale, 0, 1)
    is_payer_45 = rng.random(N) < p45

    # ~80% of 45d payers already paid in first 7d (typical F2P early convert)
    is_payer_7 = is_payer_45 & (rng.random(N) < 0.80)
    # A few 7d-only payers who churn before day 45 spend catch-up (~0.15% extra)
    extra7 = (~is_payer_45) & (rng.random(N) < 0.0015)
    is_payer_7 = is_payer_7 | extra7

    pay_price = np.zeros(N, dtype=float)
    pay_count = np.zeros(N, dtype=int)
    pred = np.zeros(N, dtype=float)

    n7 = int(is_payer_7.sum())
    pay_price[is_payer_7] = _sample_from_bands(rng, n7, BANDS_7D)
    # pay_count correlates with spend
    pay_count[is_payer_7] = np.clip(
        (pay_price[is_payer_7] / rng.uniform(0.8, 6.0, size=n7)).astype(int) + 1, 1, 80
    )

    n45 = int(is_payer_45.sum())
    pred[is_payer_45] = _sample_from_bands(rng, n45, BANDS_45D)
    # 45d total >= 7d for early payers
    both = is_payer_7 & is_payer_45
    pred[both] = np.maximum(pred[both], pay_price[both] * rng.uniform(1.0, 2.8, size=int(both.sum())))
    pred[both] = np.round(pred[both], 2)

    # Engagement: non-payers ~7.6 min, payers ~138 min (published eda)
    online = np.empty(N, dtype=float)
    online[~is_payer_45] = rng.lognormal(mean=np.log(4.0), sigma=1.1, size=int((~is_payer_45).sum()))
    online[is_payer_45] = rng.lognormal(mean=np.log(90.0), sigma=0.85, size=n45)
    online = np.clip(online, 0, 24 * 60)

    # PVP/PVE scale with stronghold + payer
    base = (levels.astype(float) + 1) ** 1.3
    payer_boost = np.where(is_payer_45, rng.uniform(3.0, 12.0, N), rng.uniform(0.3, 1.5, N))
    pvp = (rng.poisson(lam=np.clip(base * payer_boost * 0.4, 0.01, 200))).astype(int)
    pvp_launch = (pvp * rng.uniform(0.3, 0.85, N)).astype(int)
    pvp_win = (pvp * rng.uniform(0.25, 0.65, N)).astype(int)
    pve = (rng.poisson(lam=np.clip(base * payer_boost * 0.7, 0.01, 300))).astype(int)
    pve_launch = (pve * rng.uniform(0.5, 0.95, N)).astype(int)
    pve_win = (pve * rng.uniform(0.4, 0.85, N)).astype(int)

    # Light resource signal
    wood_add = (rng.lognormal(8.5 + levels * 0.15, 1.2, N) * payer_boost).astype(int)
    ivory_add = (rng.lognormal(4.0 + levels * 0.2, 1.4, N) * np.where(is_payer_45, 3, 0.5)).astype(int)

    # register_time: 2018-01-26 .. 2018-03-06
    start = np.datetime64("2018-01-26")
    days = rng.integers(0, 40, size=N)
    hours = rng.integers(0, 24, size=N)
    mins = rng.integers(0, 60, size=N)
    register_time = (
        pd.to_datetime(start)
        + pd.to_timedelta(days, unit="D")
        + pd.to_timedelta(hours, unit="h")
        + pd.to_timedelta(mins, unit="m")
    )

    df = pd.DataFrame(
        {
            "user_id": np.arange(1_000_000, 1_000_000 + N, dtype=np.int64),
            "register_time": register_time.astype(str),
            "wood_add_value": wood_add,
            "ivory_add_value": ivory_add,
            "bd_stronghold_level": levels.astype(int),
            "pvp_battle_count": pvp,
            "pvp_lanch_count": pvp_launch,
            "pvp_win_count": pvp_win,
            "pve_battle_count": pve,
            "pve_lanch_count": pve_launch,
            "pve_win_count": pve_win,
            "avg_online_minutes": np.round(online, 2),
            "pay_price": pay_price,
            "pay_count": pay_count,
            "prediction_pay_price": pred,
        }
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)

    n = len(df)
    pur7 = (df["pay_price"] > 0).mean()
    pur45 = (df["prediction_pay_price"] > 0).mean()
    arpu7 = df["pay_price"].mean()
    arppu7 = df.loc[df["pay_price"] > 0, "pay_price"].mean()
    print(f"Wrote {OUT} rows={n:,}")
    print(f"7d 付费率={pur7*100:.2f}%  ARPU={arpu7:.4f}  ARPPU={arppu7:.2f}")
    print(f"45d 付费率={pur45*100:.2f}%  mean prediction_pay_price={df['prediction_pay_price'].mean():.4f}")
    print(f"online mean all={df['avg_online_minutes'].mean():.2f} "
          f"payer={df.loc[df['pay_price']>0,'avg_online_minutes'].mean():.2f} "
          f"non={df.loc[df['pay_price']==0,'avg_online_minutes'].mean():.2f}")


if __name__ == "__main__":
    main()
