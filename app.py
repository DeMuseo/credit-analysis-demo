"""
Tap4Fun / DataCastle · China F2P 付费率 & 转化 Portfolio Demo
Bilingual Gradio for game strategy / monetization analytics.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import gradio as gr

plt.rcParams["font.sans-serif"] = [
    "Noto Sans CJK SC",
    "Noto Sans CJK JP",
    "WenQuanYi Zen Hei",
    "SimHei",
    "Arial Unicode MS",
    "DejaVu Sans",
]
plt.rcParams["axes.unicode_minus"] = False

DATA_PATH = Path(__file__).resolve().parent / "data" / "tap4fun_sample.csv"

ONLINE_BANDS = {
    "all": (None, None),
    "0-1": (0, 1),
    "1-5": (1, 5),
    "5-30": (5, 30),
    "30-120": (30, 120),
    "120+": (120, None),
}

SH_BANDS = {
    "all": (None, None),
    "0-2": (0, 2),
    "3-5": (3, 5),
    "6-8": (6, 8),
    "9-11": (9, 11),
    "12+": (12, None),
}


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df = df.drop_duplicates(subset=["user_id"])
    for c in ("pay_price", "pay_count", "avg_online_minutes", "bd_stronghold_level"):
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    if "prediction_pay_price" in df.columns:
        df["prediction_pay_price"] = pd.to_numeric(
            df["prediction_pay_price"], errors="coerce"
        ).fillna(0)
    else:
        df["prediction_pay_price"] = np.nan
    df["is_payer_7d"] = df["pay_price"] > 0
    df["is_payer_45d"] = df["prediction_pay_price"] > 0
    return df


DF = load_data()
HAS_PRED = DF["prediction_pay_price"].notna().any() and (DF["prediction_pay_price"] >= 0).any()


def _apply_filters(
    payer_status: str,
    online_band: str,
    sh_band: str,
) -> pd.DataFrame:
    out = DF
    if payer_status == "payer_7d":
        out = out[out["is_payer_7d"]]
    elif payer_status == "non_payer_7d":
        out = out[~out["is_payer_7d"]]
    elif payer_status == "payer_45d":
        out = out[out["is_payer_45d"]]
    elif payer_status == "non_payer_45d":
        out = out[~out["is_payer_45d"]]

    lo, hi = ONLINE_BANDS.get(online_band, (None, None))
    if lo is not None:
        out = out[out["avg_online_minutes"] >= lo]
    if hi is not None:
        out = out[out["avg_online_minutes"] <= hi]

    lo, hi = SH_BANDS.get(sh_band, (None, None))
    if lo is not None:
        out = out[out["bd_stronghold_level"] >= lo]
    if hi is not None:
        out = out[out["bd_stronghold_level"] <= hi]
    return out


def overview_metrics(df: pd.DataFrame, lang: str) -> str:
    n = len(df)
    if n == 0:
        return "无匹配玩家 / No matching players." if lang == "中文" else "No matching players."

    payers7 = int(df["is_payer_7d"].sum())
    pur7 = payers7 / n * 100
    rev7 = float(df["pay_price"].sum())
    arpu7 = rev7 / n
    arppu7 = rev7 / payers7 if payers7 else float("nan")
    mean_cnt = float(df.loc[df["is_payer_7d"], "pay_count"].mean()) if payers7 else float("nan")
    mean_online = float(df["avg_online_minutes"].mean())
    mean_sh = float(df["bd_stronghold_level"].mean())

    payers45 = int(df["is_payer_45d"].sum()) if HAS_PRED else 0
    pur45 = payers45 / n * 100 if HAS_PRED else float("nan")
    rev45 = float(df["prediction_pay_price"].sum()) if HAS_PRED else float("nan")
    arpu45 = rev45 / n if HAS_PRED else float("nan")
    arppu45 = rev45 / payers45 if HAS_PRED and payers45 else float("nan")

    online_p = float(df.loc[df["is_payer_7d"], "avg_online_minutes"].mean()) if payers7 else float("nan")
    online_np = float(df.loc[~df["is_payer_7d"], "avg_online_minutes"].mean())
    pvp_p = float(df.loc[df["is_payer_7d"], "pvp_battle_count"].mean()) if payers7 else float("nan")
    pvp_np = float(df.loc[~df["is_payer_7d"], "pvp_battle_count"].mean())
    pve_p = float(df.loc[df["is_payer_7d"], "pve_battle_count"].mean()) if payers7 else float("nan")
    pve_np = float(df.loc[~df["is_payer_7d"], "pve_battle_count"].mean())

    if lang == "中文":
        lines = [
            f"**筛选后玩家 n** = {n:,}",
            f"**7 日付费率（付费率）** = {pur7:.2f}%（付费人数 {payers7:,}）",
            f"**7 日 pay_price 总额** = {rev7:,.2f}　|　**ARPU** = {arpu7:.4f}　|　**ARPPU** = {arppu7:.2f}",
            f"**付费玩家均 pay_count** = {mean_cnt:.2f}" if payers7 else "**付费玩家均 pay_count** = —",
            f"**均在线时长 avg_online_minutes** = {mean_online:.2f}　|　**均要塞等级** = {mean_sh:.2f}",
        ]
        if HAS_PRED:
            lines.append(
                f"**45 日 prediction_pay_price 付费率** = {pur45:.2f}%　|　"
                f"**ARPU45** = {arpu45:.4f}　|　**ARPPU45** = {arppu45:.2f}"
            )
        lines += [
            "",
            "### 付费 vs 非付费（7 日）参与度",
            f"- 在线分钟：付费 {online_p:.1f} vs 非付费 {online_np:.1f}",
            f"- PVP 场次：付费 {pvp_p:.1f} vs 非付费 {pvp_np:.1f}",
            f"- PVE 场次：付费 {pve_p:.1f} vs 非付费 {pve_np:.1f}",
        ]
    else:
        lines = [
            f"**Players (filtered) n** = {n:,}",
            f"**7d pay rate (付费率)** = {pur7:.2f}% ({payers7:,} payers)",
            f"**7d pay_price revenue** = {rev7:,.2f}　|　**ARPU** = {arpu7:.4f}　|　**ARPPU** = {arppu7:.2f}",
            f"**Mean pay_count (payers)** = {mean_cnt:.2f}" if payers7 else "**Mean pay_count (payers)** = —",
            f"**Mean avg_online_minutes** = {mean_online:.2f}　|　**Mean stronghold** = {mean_sh:.2f}",
        ]
        if HAS_PRED:
            lines.append(
                f"**45d prediction_pay_price pay rate** = {pur45:.2f}%　|　"
                f"**ARPU45** = {arpu45:.4f}　|　**ARPPU45** = {arppu45:.2f}"
            )
        lines += [
            "",
            "### Payer vs non-payer engagement (7d)",
            f"- Online minutes: payer {online_p:.1f} vs non-payer {online_np:.1f}",
            f"- PVP battles: payer {pvp_p:.1f} vs non-payer {pvp_np:.1f}",
            f"- PVE battles: payer {pve_p:.1f} vs non-payer {pve_np:.1f}",
        ]
    return "\n".join(lines)


def auto_insights(df: pd.DataFrame, lang: str) -> str:
    if len(df) == 0:
        return "—"
    n = len(DF)
    pur7 = DF["is_payer_7d"].mean() * 100
    pur45 = DF["is_payer_45d"].mean() * 100 if HAS_PRED else float("nan")
    arppu = DF.loc[DF["is_payer_7d"], "pay_price"].mean()
    # Stronghold bands vs pay rate
    band_notes = []
    for label, (lo, hi) in SH_BANDS.items():
        if label == "all":
            continue
        sub = DF
        if lo is not None:
            sub = sub[sub["bd_stronghold_level"] >= lo]
        if hi is not None:
            sub = sub[sub["bd_stronghold_level"] <= hi]
        if len(sub) == 0:
            continue
        band_notes.append(f"{label}→{sub['is_payer_7d'].mean()*100:.1f}%")

    online_ratio = (
        DF.loc[DF["is_payer_7d"], "avg_online_minutes"].mean()
        / max(DF.loc[~DF["is_payer_7d"], "avg_online_minutes"].mean(), 1e-6)
    )

    if lang == "中文":
        tips = [
            f"1. **大盘付费率**：样本 n={n:,}，7 日付费率 ≈ {pur7:.2f}%"
            + (f"，45 日（prediction_pay_price>0）≈ {pur45:.2f}%。" if HAS_PRED else "。")
            + "与 DataCastle《野蛮时代》公开约 2% 付费比例同量级，适合中国 F2P 转化看板。",
            f"2. **ARPPU vs ARPU**：付费用户人均 7 日消费约 {arppu:.1f}；"
            "付费率低时 ARPU 被大量零付费稀释——运营应同时盯 **付费率漏斗** 与 **高价值分层（鲸鱼）**。",
            f"3. **参与度杠杆**：付费玩家日均在线约为非付费的 {online_ratio:.1f}×；"
            "PVP/PVE 同样显著更高。可把「高活跃未付费」做成礼包/首充转化池。",
            "4. **要塞等级 × 付费率**："
            + "；".join(band_notes)
            + "。中后期等级付费率跃升，说明养成深度与付费意愿绑定——适合按等级段投放礼包。",
            "5. **策略提示（非信贷）**：本 demo 面向 **游戏商业化 / 数值运营**："
            "用 7 日 pay_price、pay_count 与 45 日 prediction_pay_price 做早中期 LTV 对照，"
            "而不是信用评分。",
        ]
    else:
        tips = [
            f"1. **Pay rate**: n={n:,}, 7d pay rate ≈ {pur7:.2f}%"
            + (f", 45d (prediction_pay_price>0) ≈ {pur45:.2f}%." if HAS_PRED else ".")
            + " Same order of magnitude as the public DataCastle Brutal Age ~2% payer share — "
            "useful for China F2P conversion dashboards.",
            f"2. **ARPPU vs ARPU**: ~{arppu:.1f} mean 7d spend among payers; "
            "low pay rate dilutes ARPU — track **conversion funnel** and **whale tiers** together.",
            f"3. **Engagement lever**: payers average ~{online_ratio:.1f}× online time vs non-payers; "
            "PVP/PVE follows. Target high-engagement non-payers for first-purchase offers.",
            "4. **Stronghold × pay rate**: "
            + "; ".join(band_notes)
            + ". Pay rate jumps at mid/late levels — segment IAP packs by progression.",
            "5. **Framing**: game **monetization / economy ops**, not credit scoring — "
            "7d pay_price/pay_count vs optional 45d prediction_pay_price for early LTV.",
        ]
    return "\n\n".join(tips)


def chart_pay_rate_by_stronghold(df: pd.DataFrame, lang: str):
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    if len(df) == 0:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        ax.axis("off")
        return fig

    g = (
        df.groupby("bd_stronghold_level")
        .agg(n=("user_id", "count"), pur=("is_payer_7d", "mean"))
        .reset_index()
    )
    g = g[g["bd_stronghold_level"] <= 15]  # rare high levels sparse
    ax.bar(g["bd_stronghold_level"], g["pur"] * 100, color="#4C78A8", alpha=0.85)
    ax.set_xlabel("bd_stronghold_level" if lang != "中文" else "要塞等级 bd_stronghold_level")
    ax.set_ylabel("%")
    ax.set_title(
        "7 日付费率 × 要塞等级" if lang == "中文" else "7d pay rate by stronghold level"
    )
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return fig


def chart_pay_price_dist(df: pd.DataFrame, lang: str):
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    payers = df[df["is_payer_7d"]]
    if len(payers) == 0:
        ax.text(0.5, 0.5, "No payers", ha="center", va="center")
        ax.axis("off")
        return fig
    cap = float(np.percentile(payers["pay_price"], 99))
    ax.hist(payers["pay_price"].clip(upper=cap), bins=40, color="#F58518", alpha=0.85)
    ax.set_xlabel("pay_price (7d, p99-capped)" if lang != "中文" else "pay_price（7 日，截断至 p99）")
    ax.set_ylabel("Count" if lang != "中文" else "人数")
    ax.set_title(
        "付费玩家 7 日消费分布" if lang == "中文" else "7d pay_price distribution (payers)"
    )
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return fig


def chart_engagement_compare(df: pd.DataFrame, lang: str):
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    if len(df) == 0:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        ax.axis("off")
        return fig

    metrics = [
        ("avg_online_minutes", "在线分钟" if lang == "中文" else "Online min"),
        ("pvp_battle_count", "PVP" if lang == "中文" else "PVP battles"),
        ("pve_battle_count", "PVE" if lang == "中文" else "PVE battles"),
        ("bd_stronghold_level", "要塞等级" if lang == "中文" else "Stronghold"),
    ]
    payer = df[df["is_payer_7d"]]
    non = df[~df["is_payer_7d"]]
    x = np.arange(len(metrics))
    w = 0.35
    p_vals = [float(payer[c].mean()) if len(payer) else 0 for c, _ in metrics]
    n_vals = [float(non[c].mean()) if len(non) else 0 for c, _ in metrics]
    # normalize each metric to non-payer=1 for readability when scales differ
    norm_p, norm_n = [], []
    for pv, nv in zip(p_vals, n_vals):
        base = nv if nv > 1e-9 else 1.0
        norm_n.append(1.0)
        norm_p.append(pv / base)

    ax.bar(x - w / 2, norm_n, w, label="非付费 / non-payer", color="#4C78A8")
    ax.bar(x + w / 2, norm_p, w, label="付费 / payer", color="#F58518")
    ax.set_xticks(x)
    ax.set_xticklabels([lab for _, lab in metrics])
    ax.set_ylabel("相对非付费 (=1)" if lang == "中文" else "Relative to non-payer (=1)")
    ax.set_title(
        "付费 vs 非付费参与度（相对倍数）"
        if lang == "中文"
        else "Payer vs non-payer engagement (relative)"
    )
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return fig


def run_analysis(payer_status: str, online_band: str, sh_band: str, lang: str):
    df = _apply_filters(payer_status, online_band, sh_band)
    return (
        overview_metrics(df, lang),
        auto_insights(df, lang),
        chart_pay_rate_by_stronghold(df, lang),
        chart_pay_price_dist(df, lang),
        chart_engagement_compare(df, lang),
    )


def build_ui() -> gr.Blocks:
    payer_choices = [
        ("全部 / All", "all"),
        ("7日付费 / 7d payers", "payer_7d"),
        ("7日非付费 / 7d non-payers", "non_payer_7d"),
        ("45日付费 / 45d payers", "payer_45d"),
        ("45日非付费 / 45d non-payers", "non_payer_45d"),
    ]
    online_choices = [
        ("全部在线 / All", "all"),
        ("0–1 min", "0-1"),
        ("1–5 min", "1-5"),
        ("5–30 min", "5-30"),
        ("30–120 min", "30-120"),
        ("120+ min", "120+"),
    ]
    sh_choices = [
        ("全部要塞 / All", "all"),
        ("0–2", "0-2"),
        ("3–5", "3-5"),
        ("6–8", "6-8"),
        ("9–11", "9-11"),
        ("12+", "12+"),
    ]

    with gr.Blocks(title="Tap4Fun F2P Pay-Rate Demo") as demo:
        gr.Markdown(
            """
# Tap4Fun · DataCastle 付费率 / 转化 Demo
### China F2P game monetization portfolio (Brutal Age / 野蛮时代 schema)

用注册后 **7 日** 行为字段（`pay_price` / `pay_count` / 在线与 PVP·PVE）观察 **付费率、ARPU/ARPPU**，
并对照可选的 **45 日 `prediction_pay_price`**。面向 **游戏策略 / 商业化运营**，不是信贷风控。

Cookie Cats A/B 留存数据仍保留在 `data/cookie_cats/`（次要参考），主 UI 为 Tap4Fun。
            """
        )

        with gr.Row():
            lang = gr.Radio(["中文", "English"], value="中文", label="语言 / Language")
            payer = gr.Dropdown(choices=payer_choices, value="all", label="付费状态 / Payer filter")
            online = gr.Dropdown(choices=online_choices, value="all", label="在线时长带 / Online band")
            stronghold = gr.Dropdown(choices=sh_choices, value="all", label="要塞等级带 / Stronghold")
            btn = gr.Button("分析 / Analyze", variant="primary")

        metrics_md = gr.Markdown()
        insights_md = gr.Markdown()

        with gr.Row():
            plot1 = gr.Plot(label="Pay rate × stronghold")
            plot2 = gr.Plot(label="pay_price distribution")
        plot3 = gr.Plot(label="Engagement compare")

        gr.Markdown(
            """
---
**Data:** `data/tap4fun_sample.csv` · schema from DataCastle 2018 Tap4Fun 付费金额预测  
**See:** `data/SOURCE.md` · **Stack:** Python · pandas · matplotlib · Gradio
            """
        )

        inputs = [payer, online, stronghold, lang]
        outputs = [metrics_md, insights_md, plot1, plot2, plot3]
        btn.click(run_analysis, inputs=inputs, outputs=outputs)
        demo.load(run_analysis, inputs=inputs, outputs=outputs)

    return demo


if __name__ == "__main__":
    app = build_ui()
    app.launch(server_name="0.0.0.0", server_port=7860)
