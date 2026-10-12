#!/usr/bin/env python3
"""Tap4Fun F2P pay-conversion analysis on schema-faithful calibrated sample."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "tap4fun_sample.csv"
OUT = ROOT / "outputs" / "tap4fun"
OUT.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid", context="talk")
plt.rcParams.update({
    "figure.dpi": 140,
    "savefig.dpi": 160,
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.labelsize": 12,
    # Prefer CJK-capable fonts when present; fall back silently
    "font.sans-serif": [
        "Noto Sans CJK SC", "Noto Sans CJK JP", "WenQuanYi Micro Hei",
        "Arial Unicode MS", "DejaVu Sans", "sans-serif",
    ],
    "axes.unicode_minus": False,
})


def _sh_band(level: int) -> str:
    if level <= 2:
        return "0-2"
    if level <= 5:
        return "3-5"
    if level <= 8:
        return "6-8"
    if level <= 11:
        return "9-11"
    return "12+"


def _online_band(m: float) -> str:
    if m < 5:
        return "<5m"
    if m < 15:
        return "5-15m"
    if m < 60:
        return "15-60m"
    if m < 180:
        return "60-180m"
    return "180m+"


def main() -> None:
    df = pd.read_csv(DATA)
    n = len(df)
    df["is_payer_7"] = df["pay_price"] > 0
    df["is_payer_45"] = df["prediction_pay_price"] > 0
    df["sh_band"] = df["bd_stronghold_level"].astype(int).map(_sh_band)
    df["online_band"] = df["avg_online_minutes"].map(_online_band)

    n_payer_7 = int(df["is_payer_7"].sum())
    n_payer_45 = int(df["is_payer_45"].sum())
    rate_7 = n_payer_7 / n
    rate_45 = n_payer_45 / n
    arpu_7 = float(df["pay_price"].mean())
    arppu_7 = float(df.loc[df["is_payer_7"], "pay_price"].mean())
    arpu_45 = float(df["prediction_pay_price"].mean())
    arppu_45 = float(df.loc[df["is_payer_45"], "prediction_pay_price"].mean())
    mean_pay_count_payers = float(df.loc[df["is_payer_7"], "pay_count"].mean())
    mean_pay_count_all = float(df["pay_count"].mean())
    online_all = float(df["avg_online_minutes"].mean())
    online_payer = float(df.loc[df["is_payer_7"], "avg_online_minutes"].mean())
    online_non = float(df.loc[~df["is_payer_7"], "avg_online_minutes"].mean())
    median_online_payer = float(df.loc[df["is_payer_7"], "avg_online_minutes"].median())
    median_online_non = float(df.loc[~df["is_payer_7"], "avg_online_minutes"].median())

    # Stronghold × 7d PUR
    sh_order = ["0-2", "3-5", "6-8", "9-11", "12+"]
    sh_stats = (
        df.groupby("sh_band", observed=True)
        .agg(
            n=("user_id", "count"),
            payers=("is_payer_7", "sum"),
            pur=("is_payer_7", "mean"),
            arpu=("pay_price", "mean"),
            mean_online=("avg_online_minutes", "mean"),
        )
        .reindex(sh_order)
    )
    sh_stats["payers"] = sh_stats["payers"].astype(int)

    online_order = ["<5m", "5-15m", "15-60m", "60-180m", "180m+"]
    online_stats = (
        df.groupby("online_band", observed=True)
        .agg(
            n=("user_id", "count"),
            payers=("is_payer_7", "sum"),
            pur=("is_payer_7", "mean"),
            arpu=("pay_price", "mean"),
        )
        .reindex(online_order)
    )

    metrics = {
        "n": n,
        "payers_7d": n_payer_7,
        "payers_45d": n_payer_45,
        "pay_rate_7d": rate_7,
        "pay_rate_45d": rate_45,
        "arpu_7d": arpu_7,
        "arppu_7d": arppu_7,
        "arpu_45d": arpu_45,
        "arppu_45d": arppu_45,
        "mean_pay_count_all": mean_pay_count_all,
        "mean_pay_count_payers": mean_pay_count_payers,
        "mean_online_all": online_all,
        "mean_online_payer_7d": online_payer,
        "mean_online_nonpayer_7d": online_non,
        "median_online_payer_7d": median_online_payer,
        "median_online_nonpayer_7d": median_online_non,
        "stronghold_bands": {
            k: {
                "n": int(sh_stats.loc[k, "n"]),
                "payers": int(sh_stats.loc[k, "payers"]),
                "pur": float(sh_stats.loc[k, "pur"]),
                "arpu": float(sh_stats.loc[k, "arpu"]),
            }
            for k in sh_order
            if k in sh_stats.index and pd.notna(sh_stats.loc[k, "n"])
        },
        "disclosure": (
            "Sample is schema-faithful stratified & calibrated to published "
            "DataCastle Tap4Fun aggregates — not the raw contest train file."
        ),
    }
    (OUT / "metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # ---------- Charts ----------
    palette = sns.color_palette("deep")

    # 1) Pay rate 7d vs 45d
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    labels = ["7d 付费率\n(pay_price>0)", "45d 付费率\n(prediction_pay_price>0)"]
    vals = [rate_7 * 100, rate_45 * 100]
    bars = ax.bar(labels, vals, color=[palette[0], palette[1]], width=0.55)
    for b, v, cnt in zip(bars, vals, [n_payer_7, n_payer_45]):
        ax.text(
            b.get_x() + b.get_width() / 2,
            b.get_height() + 0.05,
            f"{v:.2f}%\nn={cnt:,}",
            ha="center",
            va="bottom",
            fontsize=11,
        )
    ax.set_ylabel("付费率 Pay rate (%)")
    ax.set_title("F2P 付费率 · 7d vs 45d (n=100,000)")
    ax.set_ylim(0, max(vals) * 1.35)
    ax.axhline(2.0, color="gray", ls="--", lw=1, alpha=0.7, label="~2% contest ref")
    ax.legend(loc="upper right", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "pay_rate_7d_45d.png")
    plt.close(fig)

    # 2) ARPU / ARPPU 7d vs 45d
    fig, ax = plt.subplots(figsize=(8.0, 4.8))
    x = np.arange(2)
    w = 0.35
    arpu = [arpu_7, arpu_45]
    arppu = [arppu_7, arppu_45]
    b1 = ax.bar(x - w / 2, arpu, w, label="ARPU", color=palette[2])
    b2 = ax.bar(x + w / 2, arppu, w, label="ARPPU", color=palette[3])
    ax.set_xticks(x)
    ax.set_xticklabels(["7d (pay_price)", "45d (prediction_pay_price)"])
    ax.set_ylabel("Revenue per user")
    ax.set_title("ARPU vs ARPPU · 7d / 45d")
    ax.set_yscale("log")
    for bars in (b1, b2):
        for b in bars:
            h = b.get_height()
            ax.text(
                b.get_x() + b.get_width() / 2,
                h * 1.08,
                f"{h:.2f}",
                ha="center",
                va="bottom",
                fontsize=10,
            )
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "arpu_arppu.png")
    plt.close(fig)

    # 3) pay_count distribution among 7d payers
    fig, ax = plt.subplots(figsize=(8.0, 4.8))
    pc = df.loc[df["is_payer_7"], "pay_count"]
    # Cap display at P99 for readability
    cap = int(np.percentile(pc, 99))
    sns.histplot(pc.clip(upper=cap), bins=min(40, cap), ax=ax, color=palette[4], edgecolor="white")
    ax.axvline(pc.mean(), color="crimson", ls="--", lw=1.5, label=f"mean={pc.mean():.2f}")
    ax.axvline(pc.median(), color="navy", ls=":", lw=1.5, label=f"median={pc.median():.0f}")
    ax.set_xlabel("pay_count (7d payers, capped at P99)")
    ax.set_ylabel("Users")
    ax.set_title(f"付费次数 pay_count · 7d payers (n={n_payer_7:,})")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "pay_count_dist.png")
    plt.close(fig)

    # 4) Payer vs non-payer online time
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.8))
    means = [online_non, online_payer]
    meds = [median_online_non, median_online_payer]
    labels_pn = ["Non-payer", "Payer (7d)"]
    axes[0].bar(labels_pn, means, color=[palette[0], palette[1]], width=0.55)
    for i, (m, md) in enumerate(zip(means, meds)):
        axes[0].text(i, m + max(means) * 0.02, f"mean {m:.1f}\nmed {md:.1f}", ha="center", fontsize=10)
    axes[0].set_ylabel("avg_online_minutes")
    axes[0].set_title("Mean / median online time")
    axes[0].set_ylim(0, max(means) * 1.25)

    # Box/violin capped
    plot_df = df.copy()
    cap_on = float(np.percentile(df["avg_online_minutes"], 99))
    plot_df["online_capped"] = plot_df["avg_online_minutes"].clip(upper=cap_on)
    plot_df["payer_lbl"] = np.where(plot_df["is_payer_7"], "Payer", "Non-payer")
    sns.boxplot(
        data=plot_df,
        x="payer_lbl",
        y="online_capped",
        hue="payer_lbl",
        order=["Non-payer", "Payer"],
        hue_order=["Non-payer", "Payer"],
        ax=axes[1],
        palette=[palette[0], palette[1]],
        showfliers=False,
        legend=False,
    )
    axes[1].set_xlabel("")
    axes[1].set_ylabel(f"avg_online_minutes (cap P99≈{cap_on:.0f})")
    axes[1].set_title("Online time distribution")
    fig.suptitle("付费 vs 非付费 · 在线时长对比", y=1.02, fontsize=14)
    fig.tight_layout()
    fig.savefig(OUT / "payer_vs_nonpayer_online.png", bbox_inches="tight")
    plt.close(fig)

    # 5) Stronghold band × PUR (segment)
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    pur_pct = sh_stats["pur"].values * 100
    bars = ax.bar(sh_order, pur_pct, color=sns.color_palette("Blues_d", len(sh_order)))
    for b, row in zip(bars, sh_stats.itertuples()):
        ax.text(
            b.get_x() + b.get_width() / 2,
            b.get_height() + 0.4,
            f"{row.pur*100:.1f}%\nn={int(row.n):,}",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    ax.set_xlabel("bd_stronghold_level band")
    ax.set_ylabel("7d 付费率 (%)")
    ax.set_title("分段：主城等级 × 7d 付费率 (PUR)")
    ax.set_ylim(0, max(pur_pct) * 1.35)
    fig.tight_layout()
    fig.savefig(OUT / "segment_stronghold_pur.png")
    plt.close(fig)

    # 6) Online band × PUR (segment)
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    op = online_stats["pur"].values * 100
    bars = ax.bar(online_order, op, color=sns.color_palette("Oranges_d", len(online_order)))
    for b, row in zip(bars, online_stats.itertuples()):
        ax.text(
            b.get_x() + b.get_width() / 2,
            b.get_height() + max(op) * 0.02,
            f"{row.pur*100:.1f}%\nn={int(row.n):,}",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    ax.set_xlabel("avg_online_minutes band")
    ax.set_ylabel("7d 付费率 (%)")
    ax.set_title("分段：在线时长 × 7d 付费率 (PUR)")
    ax.set_ylim(0, max(op) * 1.35)
    fig.tight_layout()
    fig.savefig(OUT / "segment_online_pur.png")
    plt.close(fig)

    # 7) Pay price distribution (7d payers, log)
    fig, ax = plt.subplots(figsize=(8.0, 4.8))
    pp = df.loc[df["is_payer_7"], "pay_price"]
    sns.histplot(np.log10(pp.clip(lower=0.01)), bins=30, ax=ax, color=palette[5], edgecolor="white")
    ax.set_xlabel("log10(pay_price)")
    ax.set_ylabel("Users")
    ax.set_title(f"7d pay_price 分布 (payers n={n_payer_7:,})")
    ax.axvline(np.log10(pp.median()), color="navy", ls=":", label=f"median={pp.median():.2f}")
    ax.axvline(np.log10(pp.mean()), color="crimson", ls="--", label=f"mean={pp.mean():.2f}")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "pay_price_dist.png")
    plt.close(fig)

    # ---------- Report ----------
    sh_rows = "\n".join(
        f"| {k} | {int(sh_stats.loc[k, 'n']):,} | {int(sh_stats.loc[k, 'payers']):,} | "
        f"{sh_stats.loc[k, 'pur']*100:.2f}% | {sh_stats.loc[k, 'arpu']:.3f} |"
        for k in sh_order
    )
    on_rows = "\n".join(
        f"| {k} | {int(online_stats.loc[k, 'n']):,} | {int(online_stats.loc[k, 'payers']):,} | "
        f"{online_stats.loc[k, 'pur']*100:.2f}% | {online_stats.loc[k, 'arpu']:.3f} |"
        for k in online_order
    )

    report = f"""# Tap4Fun F2P 付费转化报告 / Pay-Conversion Report

**数据 / Data:** `data/tap4fun_sample.csv`（n={n:,}）  
**游戏 / Game:** Tap4Fun《野蛮时代》/ Brutal Age（China F2P SLG）  
**任务背景:** 用前 **7 天** 行为字段解释付费转化；`prediction_pay_price` 为竞赛 **45 天** 累计付费标签。

> **披露 / Disclosure:** 本样本为 **schema-faithful 分层校准样例**（`scripts/build_tap4fun_sample.py`，seed=42），对齐公开竞赛汇总指标（≈2% 付费率、主城×PUR 曲线等），**不是** DataCastle 原始 `tap_fun_train.csv`。详见 `data/SOURCE.md`。  
> **EN:** Schema-faithful stratified demo sample calibrated to published aggregates — *not* the raw contest file.

---

## 核心指标 / Key metrics

| 指标 Metric | 7d (`pay_price`) | 45d (`prediction_pay_price`) |
|-------------|-----------------:|-----------------------------:|
| 付费率 Pay rate | **{rate_7*100:.2f}%** ({n_payer_7:,} 人) | **{rate_45*100:.2f}%** ({n_payer_45:,} 人) |
| ARPU | **{arpu_7:.4f}** | **{arpu_45:.4f}** |
| ARPPU | **{arppu_7:.2f}** | **{arppu_45:.2f}** |

| 指标 | 数值 |
|------|-----:|
| 全体 mean `pay_count` | {mean_pay_count_all:.4f} |
| 付费用户 mean `pay_count` | **{mean_pay_count_payers:.2f}** |
| 全体 mean 在线分钟 | {online_all:.2f} |
| 付费用户 mean / median 在线 | **{online_payer:.1f}** / {median_online_payer:.1f} |
| 非付费 mean / median 在线 | **{online_non:.1f}** / {median_online_non:.1f} |
| 付费/非付费 在线倍率 (mean) | **{online_payer/online_non:.1f}×** |

**CN 解读:** 前 7 天仅约 **{rate_7*100:.2f}%** 转化；到 45 天升至 **{rate_45*100:.2f}%**。付费高度集中——ARPPU 远高于 ARPU（7d ARPPU≈{arppu_7:.0f} vs ARPU≈{arpu_7:.2f}）。付费用户日均在线约为非付费的 **{online_payer/online_non:.0f} 倍**，说明深度参与与付费强相关。

**EN:** Early convert ≈{rate_7*100:.2f}% by day 7, ≈{rate_45*100:.2f}% by day 45. Spend is whale-skewed (ARPPU ≫ ARPU). Payers average ~{online_payer/online_non:.0f}× non-payer online time.

---

## 分段：主城等级 × 7d 付费率

| 主城 band | n | 付费人数 | 7d PUR | 7d ARPU |
|-----------|--:|--------:|-------:|--------:|
{sh_rows}

**CN:** 高等级主城段 PUR 显著抬升（12+ 接近饱和），低等级占多数但几乎不付费——典型 F2P「漏斗窄、头部厚」结构。  
**EN:** PUR rises sharply with stronghold progression; mass at low levels barely pays.

---

## 分段：在线时长 × 7d 付费率

| 在线 band | n | 付费人数 | 7d PUR | 7d ARPU |
|-----------|--:|--------:|-------:|--------:|
{on_rows}

**CN:** 在线越长付费率越高；短时用户构成大盘、几乎零转化。  
**EN:** Longer sessions correlate with higher PUR; short-session majority drives near-zero conversion.

---

## 图表 / Charts

| 文件 | 说明 |
|------|------|
| `pay_rate_7d_45d.png` | 7d / 45d 付费率对比 |
| `arpu_arppu.png` | ARPU vs ARPPU（7d / 45d，对数轴） |
| `pay_count_dist.png` | 付费用户 `pay_count` 分布 |
| `payer_vs_nonpayer_online.png` | 付费 vs 非付费在线时长 |
| `segment_stronghold_pur.png` | 主城等级 × PUR |
| `segment_online_pur.png` | 在线时长 × PUR |
| `pay_price_dist.png` | 7d `pay_price` 对数分布 |

绝对路径前缀：`/workspace/hf-portfolio-demo/outputs/tap4fun/`

---

## 运营启示 / Implications（简）

1. **早期识别:** 7d 已捕获大部分 45d 付费用户 → 前几天行为可做高价值预警。  
2. **参与度杠杆:** 在线与主城进度强相关付费 → 新手引导、日活任务优先于盲目打折。  
3. **头部结构:** ARPPU ≫ ARPU → 需分层运营（小额转化 + 大 R 维系），避免只看均值。

**EN:** Day-7 payers largely predict day-45 spenders; engagement/progression beats blanket discounts; whale skew demands tiered ops.

---

## 局限 / Caveats

- 样本为校准演示数据，不可当作真实竞赛训练集做模型排行。  
- 在线/主城与付费存在互为因果，分段图属探索相关，非严格因果。  
- 货币单位沿用竞赛字段（未做汇率换算）。

---

*Generated by `scripts/tap4fun_pay_analysis.py`*
"""
    (OUT / "report.md").write_text(report, encoding="utf-8")

    summary = f"""# Tap4Fun sample metrics (n={n:,})

| Metric | Value |
|--------|-------|
| 7d 付费率 | {rate_7*100:.2f}% ({n_payer_7:,} payers) |
| 7d ARPU | {arpu_7:.4f} |
| 7d ARPPU | {arppu_7:.2f} |
| Mean pay_count (payers) | {mean_pay_count_payers:.2f} |
| 45d 付费率 (prediction_pay_price>0) | {rate_45*100:.2f}% |
| 45d ARPU / ARPPU | {arpu_45:.2f} / {arppu_45:.2f} |
| Mean online (all / payer / non) | {online_all:.2f} / {online_payer:.1f} / {online_non:.1f} |

Generated by `scripts/tap4fun_pay_analysis.py` (data from `build_tap4fun_sample.py`, seed=42).
Disclosure: schema-faithful calibrated sample — not raw contest file.
"""
    (OUT / "metrics_summary.md").write_text(summary, encoding="utf-8")

    print("Wrote charts + report to", OUT)
    print(json.dumps({k: metrics[k] for k in (
        "n", "payers_7d", "payers_45d", "pay_rate_7d", "pay_rate_45d",
        "arpu_7d", "arppu_7d", "arpu_45d", "arppu_45d",
        "mean_pay_count_payers", "mean_online_payer_7d", "mean_online_nonpayer_7d",
    )}, indent=2))


if __name__ == "__main__":
    main()
