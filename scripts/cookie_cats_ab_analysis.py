#!/usr/bin/env python3
"""Cookie Cats retention A/B analysis: gate_30 vs gate_40."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "cookie_cats.csv"
OUT = ROOT / "outputs" / "cookie_cats"
OUT.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid", context="talk")
plt.rcParams.update({
    "figure.dpi": 140,
    "savefig.dpi": 160,
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.labelsize": 12,
})


def two_prop_z(success_a, n_a, success_b, n_b):
    """Two-proportion z-test (gate_40 vs gate_30). Returns z, p (two-sided)."""
    p_a = success_a / n_a
    p_b = success_b / n_b
    p_pool = (success_a + success_b) / (n_a + n_b)
    se = np.sqrt(p_pool * (1 - p_pool) * (1 / n_a + 1 / n_b))
    if se == 0:
        return 0.0, 1.0
    z = (p_b - p_a) / se
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    return float(z), float(p)


def chi2_ret(df, col):
    """Chi-square test of independence: version x retention."""
    ct = pd.crosstab(df["version"], df[col])
    chi2, p, dof, _ = stats.chi2_contingency(ct)
    return float(chi2), float(p), int(dof)


def main():
    df = pd.read_csv(DATA)
    n_raw = len(df)

    n_dup = int(df["userid"].duplicated().sum())
    if n_dup:
        df = df.drop_duplicates(subset=["userid"], keep="first")
    n = len(df)

    for col in ("retention_1", "retention_7"):
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.lower().isin(["true", "1", "yes"])
        else:
            df[col] = df[col].astype(bool)

    df["version"] = df["version"].astype(str)
    assert set(df["version"].unique()) <= {"gate_30", "gate_40"}

    versions = ["gate_30", "gate_40"]
    summary = {}
    for v in versions:
        sub = df[df["version"] == v]
        nv = len(sub)
        r1 = float(sub["retention_1"].mean())
        r7 = float(sub["retention_7"].mean())
        s1 = int(sub["retention_1"].sum())
        s7 = int(sub["retention_7"].sum())
        summary[v] = {
            "n": nv,
            "retention_1": r1,
            "retention_7": r7,
            "retention_1_n": s1,
            "retention_7_n": s7,
            "mean_gamerounds": float(sub["sum_gamerounds"].mean()),
            "median_gamerounds": float(sub["sum_gamerounds"].median()),
            "p99_gamerounds": float(sub["sum_gamerounds"].quantile(0.99)),
            "max_gamerounds": int(sub["sum_gamerounds"].max()),
        }

    g30, g40 = summary["gate_30"], summary["gate_40"]

    def lift(a, b):
        abs_l = b - a
        rel_l = (b - a) / a if a else float("nan")
        return abs_l, rel_l

    d1_abs, d1_rel = lift(g30["retention_1"], g40["retention_1"])
    d7_abs, d7_rel = lift(g30["retention_7"], g40["retention_7"])

    z1, p1 = two_prop_z(g30["retention_1_n"], g30["n"], g40["retention_1_n"], g40["n"])
    z7, p7 = two_prop_z(g30["retention_7_n"], g30["n"], g40["retention_7_n"], g40["n"])
    chi1, pchi1, _ = chi2_ret(df, "retention_1")
    chi7, pchi7, _ = chi2_ret(df, "retention_7")

    overall_max = int(df["sum_gamerounds"].max())
    overall_p99 = float(df["sum_gamerounds"].quantile(0.99))
    extreme_note = (
        f"Max sum_gamerounds={overall_max:,}; P99≈{overall_p99:.0f}. "
        f"A few players have extremely high rounds; charts cap at ~P99 for readability."
    )

    metrics = {
        "n_raw": n_raw,
        "n_after_dedupe": n,
        "n_duplicates_removed": n_dup,
        "by_version": summary,
        "d1_abs_lift_gate40_minus_gate30": d1_abs,
        "d1_rel_lift": d1_rel,
        "d7_abs_lift_gate40_minus_gate30": d7_abs,
        "d7_rel_lift": d7_rel,
        "d1_z": z1,
        "d1_pvalue_z": p1,
        "d7_z": z7,
        "d7_pvalue_z": p7,
        "d1_chi2": chi1,
        "d1_pvalue_chi2": pchi1,
        "d7_chi2": chi7,
        "d7_pvalue_chi2": pchi7,
        "outlier_note": extreme_note,
    }
    with open(OUT / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    # (a) D1/D7 retention bars
    fig, ax = plt.subplots(figsize=(9, 5.5))
    x = np.arange(2)
    w = 0.35
    r1_vals = [g30["retention_1"] * 100, g40["retention_1"] * 100]
    r7_vals = [g30["retention_7"] * 100, g40["retention_7"] * 100]
    bars1 = ax.bar(x - w / 2, r1_vals, w, label="D1 retention", color="#4C78A8")
    bars7 = ax.bar(x + w / 2, r7_vals, w, label="D7 retention", color="#F58518")
    ax.set_xticks(x)
    ax.set_xticklabels(["gate_30 (control)", "gate_40 (treatment)"])
    ax.set_ylabel("Retention rate (%)")
    ax.set_title("Cookie Cats A/B: D1 & D7 Retention by Gate Version")
    ax.set_ylim(0, max(r1_vals + r7_vals) * 1.25)
    ax.legend(loc="upper right")
    for bars in (bars1, bars7):
        for b in bars:
            h = b.get_height()
            ax.annotate(
                f"{h:.2f}%",
                xy=(b.get_x() + b.get_width() / 2, h),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=10,
            )
    ax.text(
        0.5,
        0.02,
        f"D1 lift (40-30): {d1_abs*100:+.2f}pp ({d1_rel*100:+.2f}%), p={p1:.4f}\n"
        f"D7 lift (40-30): {d7_abs*100:+.2f}pp ({d7_rel*100:+.2f}%), p={p7:.4f}",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=9,
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
    )
    fig.tight_layout()
    path_a = OUT / "retention_bars_d1_d7.png"
    fig.savefig(path_a, bbox_inches="tight")
    plt.close(fig)

    # (b) gamerounds violin/box capped
    cap = int(np.ceil(overall_p99))
    df_plot = df.copy()
    df_plot["gamerounds_capped"] = df_plot["sum_gamerounds"].clip(upper=cap)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))
    sns.violinplot(
        data=df_plot,
        x="version",
        y="gamerounds_capped",
        order=versions,
        ax=axes[0],
        inner="quartile",
        palette={"gate_30": "#4C78A8", "gate_40": "#F58518"},
    )
    axes[0].set_title(f"Game rounds distribution (capped at P99={cap})")
    axes[0].set_xlabel("Version")
    axes[0].set_ylabel("sum_gamerounds (capped)")

    sns.boxplot(
        data=df_plot,
        x="version",
        y="gamerounds_capped",
        order=versions,
        ax=axes[1],
        showfliers=False,
        palette={"gate_30": "#4C78A8", "gate_40": "#F58518"},
    )
    for i, v in enumerate(versions):
        m = summary[v]["mean_gamerounds"]
        med = summary[v]["median_gamerounds"]
        axes[1].scatter(i, min(m, cap), color="black", zorder=5, s=40, label="mean" if i == 0 else None)
        axes[1].annotate(
            f"mean={m:.1f}\nmed={med:.0f}",
            xy=(i, min(m, cap)),
            xytext=(8, 8),
            textcoords="offset points",
            fontsize=9,
        )
    axes[1].set_title("Game rounds boxplot (no extreme outliers shown)")
    axes[1].set_xlabel("Version")
    axes[1].set_ylabel("sum_gamerounds (capped)")
    handles, labels_ = axes[1].get_legend_handles_labels()
    if handles:
        axes[1].legend(loc="upper right", fontsize=9)
    fig.suptitle("Play intensity by version", y=1.02)
    fig.tight_layout()
    path_b = OUT / "gamerounds_violin_box.png"
    fig.savefig(path_b, bbox_inches="tight")
    plt.close(fig)

    # (c) retention by playtime band
    bins = [0, 1, 5, 20, 50, 100, np.inf]
    labels = ["0", "1-4", "5-19", "20-49", "50-99", "100+"]
    df["play_band"] = pd.cut(df["sum_gamerounds"], bins=bins, labels=labels, right=False)

    band_rows = []
    for v in versions:
        for band in labels:
            sub = df[(df["version"] == v) & (df["play_band"] == band)]
            if len(sub) == 0:
                continue
            band_rows.append(
                {
                    "version": v,
                    "play_band": band,
                    "n": len(sub),
                    "d1": sub["retention_1"].mean() * 100,
                    "d7": sub["retention_7"].mean() * 100,
                }
            )
    band_df = pd.DataFrame(band_rows)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    for ax, metric, title in zip(
        axes,
        ["d1", "d7"],
        ["D1 retention by playtime band", "D7 retention by playtime band"],
    ):
        for v, color in zip(versions, ["#4C78A8", "#F58518"]):
            sub = band_df[band_df["version"] == v]
            ax.plot(
                sub["play_band"].astype(str),
                sub[metric],
                marker="o",
                label=v,
                color=color,
                linewidth=2,
            )
        ax.set_xlabel("sum_gamerounds band")
        ax.set_ylabel("Retention (%)")
        ax.set_title(title)
        ax.legend()
        ax.set_ylim(0, 100)
    fig.suptitle("Retention rises with early play intensity (both arms)", y=1.02)
    fig.tight_layout()
    path_c = OUT / "retention_by_playtime_band.png"
    fig.savefig(path_c, bbox_inches="tight")
    plt.close(fig)

    # (d) funnel summary
    fig, ax = plt.subplots(figsize=(10, 6))
    stages = ["Assigned", "Played >=1\nround", "D1 retained", "D7 retained"]
    funnel = {}
    for v in versions:
        sub = df[df["version"] == v]
        assigned = len(sub)
        played = int((sub["sum_gamerounds"] >= 1).sum())
        d1 = int(sub["retention_1"].sum())
        d7 = int(sub["retention_7"].sum())
        funnel[v] = [assigned, played, d1, d7]

    y = np.arange(len(stages))
    h = 0.35
    base_max = max(funnel["gate_30"][0], funnel["gate_40"][0])
    for i, (v, color) in enumerate(zip(versions, ["#4C78A8", "#F58518"])):
        vals = funnel[v]
        offset = -h / 2 if i == 0 else h / 2
        bars = ax.barh(y + offset, vals, height=h, color=color, label=v, alpha=0.9)
        for bar, val in zip(bars, vals):
            pct = 100 * val / vals[0] if vals[0] else 0
            ax.text(
                val + base_max * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{val:,} ({pct:.1f}%)",
                va="center",
                fontsize=9,
            )

    ax.set_yticks(y)
    ax.set_yticklabels(stages)
    ax.invert_yaxis()
    ax.set_xlabel("Players")
    ax.set_title("Cookie Cats A/B funnel: Assigned -> Played -> D1 -> D7")
    ax.legend(loc="lower right")
    ax.text(
        0.98,
        0.02,
        "Rates of D1/D7 are of Assigned (same base as primary metrics).",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=8,
        style="italic",
    )
    fig.tight_layout()
    path_d = OUT / "funnel_summary.png"
    fig.savefig(path_d, bbox_inches="tight")
    plt.close(fig)

    if d7_abs < 0 and p7 < 0.05:
        rec_en = (
            "Prefer keeping the first gate at level 30 (gate_30). "
            "Moving the gate to level 40 (gate_40) shows lower D1 and D7 retention; "
            "the D7 difference is statistically significant at conventional alpha=0.05. "
            "Do not ship gate_40 based on this experiment alone."
        )
        rec_cn = (
            "建议保留关卡门槛在第30关（gate_30）。"
            "将门槛移至第40关（gate_40）后，D1与D7留存均更低；"
            "D7差异在alpha=0.05下具有统计显著性。"
            "仅凭本实验结果，不建议上线 gate_40。"
        )
        verdict = "gate_30 better / gate_30 更优"
    elif d7_abs < 0:
        rec_en = (
            "Lean toward gate_30. Point estimates favor gate_30 on D1 and D7; "
            "treat D7 evidence as suggestive and confirm with power / sequential checks."
        )
        rec_cn = (
            "倾向保留 gate_30。点估计上 D1/D7 均优于 gate_40；"
            "D7证据偏弱时建议复核功效与序贯分析。"
        )
        verdict = "lean gate_30 / 倾向 gate_30"
    else:
        rec_en = "Results do not clearly favor gate_30; review lifts and p-values before deciding."
        rec_cn = "结果未明显支持 gate_30；决策前请复核提升幅度与p值。"
        verdict = "inconclusive / 尚不明确"

    report = f"""# Cookie Cats Retention A/B Report / Cookie Cats 留存 A/B 报告

**Experiment:** First in-game gate at level 30 vs 40 (`gate_30` vs `gate_40`)  
**Data:** `data/cookie_cats.csv` (Tactile Entertainment / public Cookie Cats A/B dataset)  
**Analyst output for:** Lunny  

---

## Sample / 样本量

| Metric | Value |
|--------|------:|
| Rows loaded | {n_raw:,} |
| Duplicate `userid` removed | {n_dup:,} |
| Analysis N | {n:,} |
| gate_30 N | {g30['n']:,} |
| gate_40 N | {g40['n']:,} |

---

## Retention rates / 留存率

| Version | D1 | D7 | Mean rounds | Median rounds |
|---------|-----:|-----:|------------:|--------------:|
| gate_30 | {g30['retention_1']*100:.2f}% | {g30['retention_7']*100:.2f}% | {g30['mean_gamerounds']:.2f} | {g30['median_gamerounds']:.0f} |
| gate_40 | {g40['retention_1']*100:.2f}% | {g40['retention_7']*100:.2f}% | {g40['mean_gamerounds']:.2f} | {g40['median_gamerounds']:.0f} |

### Lift (gate_40 - gate_30) / 提升幅度

| Horizon | Absolute (pp) | Relative | Two-prop z | p (z) | chi2 p |
|---------|--------------:|---------:|-----------:|------:|-------:|
| D1 | {d1_abs*100:+.3f} | {d1_rel*100:+.2f}% | {z1:.3f} | {p1:.4f} | {pchi1:.4f} |
| D7 | {d7_abs*100:+.3f} | {d7_rel*100:+.2f}% | {z7:.3f} | {p7:.4f} | {pchi7:.4f} |

**EN:** Negative lift means gate_40 retained *fewer* players than gate_30.  
**CN:** 负向提升表示 gate_40 留存低于 gate_30。

---

## Outliers / 极端值说明

{extreme_note}

EN: Distributions of `sum_gamerounds` are heavily right-skewed; medians are far below means.  
CN: 游戏局数右偏严重，均值远高于中位数；作图时对极端值做了封顶以便阅读。

---

## Charts / 图表

| File | Description |
|------|-------------|
| `retention_bars_d1_d7.png` | D1/D7 retention bars by version |
| `gamerounds_violin_box.png` | Violin + box of play rounds (capped) |
| `retention_by_playtime_band.png` | Retention by playtime band |
| `funnel_summary.png` | Funnel: Assigned -> Played -> D1 -> D7 |

---

## Recommendation / 结论建议

**Verdict:** {verdict}

**EN:** {rec_en}

**CN:** {rec_cn}

### Confidence caveats / 置信度与局限

**EN:**
- This is a large-N online experiment; small absolute lifts can still be statistically significant.
- Primary decision metric here is **D7 retention** (business-relevant stickiness); D1 is directional support.
- No multiple-testing correction applied beyond reporting both D1 and D7; treat p-values as descriptive of this pre-specified contrast.
- Playtime is post-treatment (affected by gate placement), so banded retention charts are exploratory, not causal mediators you can freely condition on for the A/B call.
- External validity: results apply to this game economy / cohort; re-test if monetization or onboarding changes.

**CN:**
- 大样本下很小的绝对差值也可能显著；请同时看提升幅度与业务意义。
- 主决策指标建议以 **D7 留存** 为准；D1 作方向性佐证。
- 未做额外多重比较校正；p 值用于本预设对比的描述。
- 游戏局数受门槛位置影响，分箱留存图属探索性分析，不宜当作可随意条件化的因果中介。
- 外部效度有限：换经济系统或新手流程后应复测。

---

*Generated by `scripts/cookie_cats_ab_analysis.py`*
"""
    (OUT / "report.md").write_text(report, encoding="utf-8")

    print("=== KEY NUMBERS ===")
    print(f"N gate_30={g30['n']:,}  gate_40={g40['n']:,}  (dupes removed={n_dup})")
    print(
        f"D1: gate_30={g30['retention_1']*100:.2f}%  gate_40={g40['retention_1']*100:.2f}%  "
        f"lift={d1_abs*100:+.3f}pp ({d1_rel*100:+.2f}%)  z={z1:.3f} p={p1:.4f}"
    )
    print(
        f"D7: gate_30={g30['retention_7']*100:.2f}%  gate_40={g40['retention_7']*100:.2f}%  "
        f"lift={d7_abs*100:+.3f}pp ({d7_rel*100:+.2f}%)  z={z7:.3f} p={p7:.4f}"
    )
    print(f"Mean rounds: 30={g30['mean_gamerounds']:.2f}  40={g40['mean_gamerounds']:.2f}")
    print(f"Median rounds: 30={g30['median_gamerounds']:.0f}  40={g40['median_gamerounds']:.0f}")
    print(f"Charts: {path_a.name}, {path_b.name}, {path_c.name}, {path_d.name}")
    print(f"Report: {OUT / 'report.md'}")
    print(f"Verdict: {verdict}")


if __name__ == "__main__":
    main()
