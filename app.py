"""
Cookie Cats Mobile Game A/B Retention Demo
Cookie Cats 手游关卡门控 A/B 留存分析 · Gradio 作品集 Demo
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import gradio as gr

# ---- Chinese font fallback for matplotlib ----
plt.rcParams["font.sans-serif"] = [
    "Noto Sans CJK SC",
    "Noto Sans CJK JP",
    "WenQuanYi Zen Hei",
    "SimHei",
    "Arial Unicode MS",
    "DejaVu Sans",
]
plt.rcParams["axes.unicode_minus"] = False

DATA_PATH = Path(__file__).resolve().parent / "data" / "cookie_cats.csv"

PLAYTIME_BANDS = {
    "all": (None, None),
    "0": (0, 0),
    "1-5": (1, 5),
    "6-20": (6, 20),
    "21-50": (21, 50),
    "51-100": (51, 100),
    "101+": (101, None),
}

BAND_LABELS_CN = {
    "all": "全部局数",
    "0": "0 局（未开玩）",
    "1-5": "1–5 局",
    "6-20": "6–20 局",
    "21-50": "21–50 局",
    "51-100": "51–100 局",
    "101+": "101+ 局",
}

BAND_LABELS_EN = {
    "all": "All playtime",
    "0": "0 rounds (no play)",
    "1-5": "1–5 rounds",
    "6-20": "6–20 rounds",
    "21-50": "21–50 rounds",
    "51-100": "51–100 rounds",
    "101+": "101+ rounds",
}


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df = df.drop_duplicates(subset=["userid"])
    df["retention_1"] = df["retention_1"].astype(bool)
    df["retention_7"] = df["retention_7"].astype(bool)
    df["version"] = df["version"].astype(str)
    # Churn proxy: not retained on day 7
    df["churn_proxy"] = ~df["retention_7"]
    return df


DF = load_data()


def _apply_filters(
    version: str,
    playtime_band: str,
) -> pd.DataFrame:
    out = DF
    if version and version != "all":
        out = out[out["version"] == version]
    lo, hi = PLAYTIME_BANDS.get(playtime_band, (None, None))
    if lo is not None:
        out = out[out["sum_gamerounds"] >= lo]
    if hi is not None:
        out = out[out["sum_gamerounds"] <= hi]
    return out


def _pct(series: pd.Series) -> float:
    if len(series) == 0:
        return float("nan")
    return float(series.mean() * 100)


def overview_metrics(df: pd.DataFrame, lang: str) -> str:
    n = len(df)
    if n == 0:
        return "无匹配玩家 / No matching players." if lang == "中文" else "No matching players."

    d1 = _pct(df["retention_1"])
    d7 = _pct(df["retention_7"])
    mean_r = float(df["sum_gamerounds"].mean())
    med_r = float(df["sum_gamerounds"].median())
    churn = _pct(df["churn_proxy"])

    by_v = (
        df.groupby("version")
        .agg(
            n=("userid", "count"),
            d1=("retention_1", "mean"),
            d7=("retention_7", "mean"),
            mean_rounds=("sum_gamerounds", "mean"),
        )
        .reset_index()
    )

    if lang == "中文":
        lines = [
            f"**筛选后玩家数 n** = {n:,}",
            f"**次日留存 D1** = {d1:.2f}%　|　**七日留存 D7** = {d7:.2f}%",
            f"**平均局数** = {mean_r:.1f}　|　**中位局数** = {med_r:.0f}",
            f"**流失代理（非 D7）** = {churn:.2f}%",
            "",
            "### 分版本概览",
        ]
        for _, row in by_v.iterrows():
            lines.append(
                f"- `{row['version']}`: n={int(row['n']):,} · "
                f"D1={row['d1']*100:.2f}% · D7={row['d7']*100:.2f}% · "
                f"均局={row['mean_rounds']:.1f}"
            )
    else:
        lines = [
            f"**Players (filtered) n** = {n:,}",
            f"**Day-1 retention (D1)** = {d1:.2f}%　|　**Day-7 retention (D7)** = {d7:.2f}%",
            f"**Mean rounds** = {mean_r:.1f}　|　**Median rounds** = {med_r:.0f}",
            f"**Churn proxy (not D7)** = {churn:.2f}%",
            "",
            "### By version",
        ]
        for _, row in by_v.iterrows():
            lines.append(
                f"- `{row['version']}`: n={int(row['n']):,} · "
                f"D1={row['d1']*100:.2f}% · D7={row['d7']*100:.2f}% · "
                f"mean rounds={row['mean_rounds']:.1f}"
            )
    return "\n".join(lines)


def auto_insights(df: pd.DataFrame, lang: str) -> str:
    if len(df) == 0:
        return "—"

    g = (
        DF.groupby("version")
        .agg(d1=("retention_1", "mean"), d7=("retention_7", "mean"), n=("userid", "count"))
    )
    if "gate_30" not in g.index or "gate_40" not in g.index:
        return "—"

    d1_30, d1_40 = g.loc["gate_30", "d1"] * 100, g.loc["gate_40", "d1"] * 100
    d7_30, d7_40 = g.loc["gate_30", "d7"] * 100, g.loc["gate_40", "d7"] * 100
    delta_d1 = d1_30 - d1_40
    delta_d7 = d7_30 - d7_40

    # Playtime vs retention (full data insight)
    bands_order = ["0", "1-5", "6-20", "21-50", "51-100", "101+"]
    band_d7 = []
    for b in bands_order:
        lo, hi = PLAYTIME_BANDS[b]
        sub = DF
        if lo is not None:
            sub = sub[sub["sum_gamerounds"] >= lo]
        if hi is not None:
            sub = sub[sub["sum_gamerounds"] <= hi]
        if len(sub):
            band_d7.append((b, _pct(sub["retention_7"])))

    zero_share = (DF["sum_gamerounds"] == 0).mean() * 100

    if lang == "中文":
        tips = [
            f"1. **全量对照**：gate_30 的 D1={d1_30:.2f}%、D7={d7_30:.2f}%；"
            f"gate_40 的 D1={d1_40:.2f}%、D7={d7_40:.2f}%。",
            f"2. **门控策略**：将首道关卡从 30 移到 40 后，D1 差 {delta_d1:+.2f} pp，"
            f"D7 差 {delta_d7:+.2f} pp（正值表示 gate_30 更高）。"
            "若目标是留存，实验倾向**保留 gate_30**。",
            f"3. **开玩率**：约 {zero_share:.1f}% 玩家局数为 0；"
            "早期漏斗（安装→首局）与门控位置同样关键。",
            "4. **局数带与 D7**：局数越高，七日留存通常越高——"
            + "；".join(f"{b}→{v:.1f}%" for b, v in band_d7)
            + "。可用局数带做分层运营与召回。",
            "5. **流失代理**：以「未 D7 留存」作 churn proxy，"
            "适合和付费/关卡通过率一起做游戏策略看板（本 demo 仅用公开留存字段）。",
        ]
    else:
        tips = [
            f"1. **Full A/B**: gate_30 D1={d1_30:.2f}%, D7={d7_30:.2f}%; "
            f"gate_40 D1={d1_40:.2f}%, D7={d7_40:.2f}%.",
            f"2. **Gate strategy**: moving the first gate 30→40 shows D1 Δ {delta_d1:+.2f} pp "
            f"and D7 Δ {delta_d7:+.2f} pp (positive = gate_30 higher). "
            "For retention, evidence favors **keeping gate_30**.",
            f"3. **Activation**: ~{zero_share:.1f}% of players have 0 rounds; "
            "install→first-session funnel matters alongside gate placement.",
            "4. **Playtime bands vs D7**: more rounds ↔ higher D7 — "
            + "; ".join(f"{b}→{v:.1f}%" for b, v in band_d7)
            + ". Use bands for segmented ops / re-engagement.",
            "5. **Churn proxy**: treating non–D7 retention as churn is a simple "
            "strategy KPI alongside monetization (this demo uses public retention fields only).",
        ]
    return "\n\n".join(tips)


def chart_retention_by_gate(df: pd.DataFrame, lang: str):
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    if len(df) == 0:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        ax.axis("off")
        return fig

    g = (
        df.groupby("version")[["retention_1", "retention_7"]]
        .mean()
        .reindex(["gate_30", "gate_40"])
        .dropna(how="all")
        * 100
    )
    x = np.arange(len(g.index))
    w = 0.35
    ax.bar(x - w / 2, g["retention_1"], w, label="D1" if lang != "中文" else "次日 D1", color="#4C78A8")
    ax.bar(x + w / 2, g["retention_7"], w, label="D7" if lang != "中文" else "七日 D7", color="#F58518")
    ax.set_xticks(x)
    ax.set_xticklabels(g.index)
    ax.set_ylabel("%")
    title = "留存率对比（按门控版本）" if lang == "中文" else "Retention by gate version"
    ax.set_title(title)
    ax.legend()
    ax.set_ylim(0, max(50, g.values.max() * 1.25 if len(g) else 50))
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return fig


def chart_rounds_dist(df: pd.DataFrame, lang: str):
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    if len(df) == 0:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        ax.axis("off")
        return fig

    # Cap display at 99th percentile to avoid extreme outlier skew
    cap = int(np.percentile(DF["sum_gamerounds"], 99))
    for ver, color in [("gate_30", "#4C78A8"), ("gate_40", "#F58518")]:
        sub = df[df["version"] == ver]["sum_gamerounds"]
        if len(sub) == 0:
            continue
        clipped = sub.clip(upper=cap)
        ax.hist(
            clipped,
            bins=40,
            alpha=0.55,
            label=ver,
            color=color,
            density=True,
        )
    ax.set_xlabel("sum_gamerounds (capped at p99)" if lang != "中文" else "局数 sum_gamerounds（截断至 p99）")
    ax.set_ylabel("Density" if lang != "中文" else "密度")
    title = "游戏局数分布（分版本）" if lang == "中文" else "Game rounds distribution by version"
    ax.set_title(title)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return fig


def chart_churn_proxy(df: pd.DataFrame, lang: str):
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    if len(df) == 0:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        ax.axis("off")
        return fig

    # Churn proxy rate by playtime band × version
    rows = []
    for b in ["0", "1-5", "6-20", "21-50", "51-100", "101+"]:
        lo, hi = PLAYTIME_BANDS[b]
        for ver in ["gate_30", "gate_40"]:
            sub = df[df["version"] == ver]
            if lo is not None:
                sub = sub[sub["sum_gamerounds"] >= lo]
            if hi is not None:
                sub = sub[sub["sum_gamerounds"] <= hi]
            if len(sub) == 0:
                continue
            rows.append(
                {
                    "band": b,
                    "version": ver,
                    "churn": _pct(sub["churn_proxy"]),
                    "n": len(sub),
                }
            )
    if not rows:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        ax.axis("off")
        return fig

    plot_df = pd.DataFrame(rows)
    bands = ["0", "1-5", "6-20", "21-50", "51-100", "101+"]
    x = np.arange(len(bands))
    w = 0.35
    for i, (ver, color) in enumerate([("gate_30", "#4C78A8"), ("gate_40", "#F58518")]):
        vals = []
        for b in bands:
            hit = plot_df[(plot_df["band"] == b) & (plot_df["version"] == ver)]
            vals.append(float(hit["churn"].iloc[0]) if len(hit) else np.nan)
        ax.bar(x + (i - 0.5) * w, vals, w, label=ver, color=color)

    ax.set_xticks(x)
    ax.set_xticklabels(bands)
    ax.set_ylabel("%")
    xlab = "局数带" if lang == "中文" else "Playtime band"
    title = (
        "流失代理（非 D7 留存）按局数带 × 版本"
        if lang == "中文"
        else "Churn proxy (not D7) by playtime band × version"
    )
    ax.set_xlabel(xlab)
    ax.set_title(title)
    ax.legend()
    ax.set_ylim(0, 105)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return fig


def run_analysis(version: str, playtime_band: str, lang: str):
    df = _apply_filters(version, playtime_band)
    metrics = overview_metrics(df, lang)
    insights = auto_insights(df, lang)
    fig1 = chart_retention_by_gate(df, lang)
    fig2 = chart_rounds_dist(df, lang)
    fig3 = chart_churn_proxy(df, lang)
    return metrics, insights, fig1, fig2, fig3


def build_ui() -> gr.Blocks:
    version_choices = [("全部 / All", "all"), ("gate_30", "gate_30"), ("gate_40", "gate_40")]
    band_choices = [
        (f"{BAND_LABELS_CN[k]} / {BAND_LABELS_EN[k]}", k) for k in PLAYTIME_BANDS
    ]

    with gr.Blocks(title="Cookie Cats A/B Retention Demo") as demo:
        gr.Markdown(
            """
# Cookie Cats · 手游关卡门控 A/B 留存 Demo
### Mobile game gate A/B retention analysis (portfolio)

**Cookie Cats**（Tactile Entertainment）将玩家随机分到 `gate_30` / `gate_40`，
观察局数与次日/七日留存。本 demo 面向**游戏策略 / 增长分析**岗位作品集展示。

Real Cookie Cats experiment data (~90k players) — not synthetic.
            """
        )

        with gr.Row():
            lang = gr.Radio(["中文", "English"], value="中文", label="语言 / Language")
            version = gr.Dropdown(
                choices=version_choices,
                value="all",
                label="版本 / Version",
            )
            playtime = gr.Dropdown(
                choices=band_choices,
                value="all",
                label="局数带 / Playtime band",
            )
            btn = gr.Button("分析 / Analyze", variant="primary")

        metrics_md = gr.Markdown()
        insights_md = gr.Markdown(label="Insights")

        with gr.Row():
            plot1 = gr.Plot(label="Retention by gate")
            plot2 = gr.Plot(label="Rounds distribution")
        plot3 = gr.Plot(label="Churn proxy")

        gr.Markdown(
            """
---
**Data:** `data/cookie_cats.csv` · Kaggle `mursideyarkin/mobile-games-ab-testing-cookie-cats`  
**Attribution:** Tactile Entertainment / DataCamp-style Cookie Cats A/B tutorial dataset  
**Stack:** Python · pandas · matplotlib · Gradio
            """
        )

        inputs = [version, playtime, lang]
        outputs = [metrics_md, insights_md, plot1, plot2, plot3]
        btn.click(run_analysis, inputs=inputs, outputs=outputs)
        demo.load(run_analysis, inputs=inputs, outputs=outputs)

    return demo


if __name__ == "__main__":
    app = build_ui()
    app.launch(server_name="0.0.0.0", server_port=7860)
