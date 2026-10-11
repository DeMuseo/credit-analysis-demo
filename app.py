"""
Zhang Yuelun — Bilingual Consumer Credit / Drainage Analysis Portfolio Demo
花呗风格消费信贷调研 × 引流转化探索性分析 · Gradio 作品集 Demo
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
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

DATA_PATH = Path(__file__).resolve().parent / "data" / "huabei_style_survey.csv"

# Column display names (CN)
COL_CN = {
    "user_id": "用户ID",
    "city": "城市",
    "age_group": "年龄段",
    "income_band": "收入档",
    "channel": "引流渠道",
    "product": "产品/活动",
    "credit_limit": "授信额度",
    "utilization_pct": "额度使用率%",
    "monthly_spend": "月消费额",
    "overdue_flag": "逾期标记",
    "risk_tier": "风险分层",
    "converted": "是否转化",
}


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    # light cleaning (portfolio demo of pandas hygiene)
    df = df.drop_duplicates(subset=["user_id"])
    df["overdue_flag"] = df["overdue_flag"].astype(int)
    df["converted"] = df["converted"].astype(int)
    df["utilization_pct"] = pd.to_numeric(df["utilization_pct"], errors="coerce").clip(0, 100)
    df["credit_limit"] = pd.to_numeric(df["credit_limit"], errors="coerce")
    df["monthly_spend"] = pd.to_numeric(df["monthly_spend"], errors="coerce")
    df = df.dropna(subset=["city", "channel", "risk_tier"])
    return df


DF = load_data()


def overview_metrics(df: pd.DataFrame) -> str:
    n = len(df)
    if n == 0:
        return "当前筛选无数据 / No rows under current filters."
    overdue_rate = df["overdue_flag"].mean() * 100
    conv_rate = df["converted"].mean() * 100
    avg_util = df["utilization_pct"].mean()
    avg_limit = df["credit_limit"].mean()
    avg_spend = df["monthly_spend"].mean()
    high_risk = (df["risk_tier"] == "高风险").mean() * 100
    return (
        f"### 概览指标 Overview\n"
        f"- **样本数 Samples**: {n:,}\n"
        f"- **逾期率 Overdue rate**: {overdue_rate:.1f}%\n"
        f"- **转化率 Conversion rate**: {conv_rate:.1f}%\n"
        f"- **高风险占比 High-risk share**: {high_risk:.1f}%\n"
        f"- **平均额度使用率 Avg utilization**: {avg_util:.1f}%\n"
        f"- **平均授信额度 Avg credit limit**: ¥{avg_limit:,.0f}\n"
        f"- **平均月消费 Avg monthly spend**: ¥{avg_spend:,.0f}"
    )


def auto_insights(df: pd.DataFrame) -> str:
    """Short Chinese auto-insight text from filtered slice."""
    if len(df) == 0:
        return "暂无洞察：当前筛选条件下无样本。"

    lines = ["### 自动洞察 Auto Insights（中文）", ""]

    # Channel conversion ranking
    ch = (
        df.groupby("channel")
        .agg(n=("user_id", "count"), conv=("converted", "mean"), overdue=("overdue_flag", "mean"))
        .query("n >= 10")
        .sort_values("conv", ascending=False)
    )
    if not ch.empty:
        best = ch.index[0]
        worst = ch.index[-1]
        lines.append(
            f"1. **引流渠道**：转化率最高为「{best}」({ch.loc[best, 'conv']*100:.1f}%)，"
            f"最低为「{worst}」({ch.loc[worst, 'conv']*100:.1f}%). "
            f"可优先加大高效渠道投放，并对低转化渠道做素材/人群复盘。"
        )

    # Risk vs utilization
    util_high = df[df["utilization_pct"] >= 70]
    if len(util_high) >= 10:
        ov = util_high["overdue_flag"].mean() * 100
        ov_all = df["overdue_flag"].mean() * 100
        lines.append(
            f"2. **额度使用率**：使用率≥70% 子群逾期率 {ov:.1f}% "
            f"（全量 {ov_all:.1f}%）。高使用率与逾期正相关，适合作为风险预警特征。"
        )

    # City risk
    city = (
        df.groupby("city")
        .agg(n=("user_id", "count"), overdue=("overdue_flag", "mean"))
        .query("n >= 15")
        .sort_values("overdue", ascending=False)
    )
    if not city.empty:
        top_city = city.index[0]
        lines.append(
            f"3. **城市差异**：「{top_city}」逾期率相对偏高 "
            f"({city.loc[top_city, 'overdue']*100:.1f}%, n={int(city.loc[top_city, 'n'])})，"
            f"建议结合当地客群结构与产品渗透做分层运营。"
        )

    # Age / income cross hint
    age = (
        df.groupby("age_group")
        .agg(conv=("converted", "mean"), n=("user_id", "count"))
        .query("n >= 15")
        .sort_values("conv", ascending=False)
    )
    if not age.empty:
        a0 = age.index[0]
        lines.append(
            f"4. **年龄段**：「{a0}」转化相对更好 ({age.loc[a0, 'conv']*100:.1f}%)，"
            f"可与收入档做交叉（类似 SQL `GROUP BY age_group, income_band`）细化增长策略。"
        )

    lines.append("")
    lines.append(
        "_方法提示：筛选 ≈ WHERE；分组指标 ≈ GROUP BY + AVG；清洗含去重、类型转换、缺失处理。_"
    )
    return "\n".join(lines)


def apply_filters(
    city: str,
    channel: str,
    risk_tier: str,
    age_group: str,
    util_min: float,
    util_max: float,
    overdue_only: bool,
) -> pd.DataFrame:
    df = DF.copy()
    if city and city != "全部 / All":
        df = df[df["city"] == city]
    if channel and channel != "全部 / All":
        df = df[df["channel"] == channel]
    if risk_tier and risk_tier != "全部 / All":
        df = df[df["risk_tier"] == risk_tier]
    if age_group and age_group != "全部 / All":
        df = df[df["age_group"] == age_group]
    df = df[(df["utilization_pct"] >= util_min) & (df["utilization_pct"] <= util_max)]
    if overdue_only:
        df = df[df["overdue_flag"] == 1]
    return df


def chart_channel_conversion(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    if len(df) == 0:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        ax.set_axis_off()
        return fig
    g = (
        df.groupby("channel")
        .agg(conversion=("converted", "mean"), n=("user_id", "count"))
        .sort_values("conversion", ascending=True)
    )
    ax.barh(g.index, g["conversion"] * 100, color="#3B82F6")
    ax.set_xlabel("Conversion rate (%)")
    ax.set_title("引流渠道转化率 / Channel conversion")
    for i, (rate, n) in enumerate(zip(g["conversion"] * 100, g["n"])):
        ax.text(rate + 0.3, i, f"{rate:.1f}% (n={n})", va="center", fontsize=8)
    fig.tight_layout()
    return fig


def chart_risk_util(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    if len(df) == 0:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        ax.set_axis_off()
        return fig
    order = ["低风险", "中风险", "高风险"]
    colors = {"低风险": "#22C55E", "中风险": "#F59E0B", "高风险": "#EF4444"}
    for tier in order:
        sub = df[df["risk_tier"] == tier]
        if len(sub) == 0:
            continue
        ax.scatter(
            sub["utilization_pct"],
            sub["monthly_spend"],
            s=18,
            alpha=0.55,
            label=tier,
            c=colors[tier],
        )
    ax.set_xlabel("Utilization %")
    ax.set_ylabel("Monthly spend (¥)")
    ax.set_title("风险分层 × 使用率 / 月消费 Risk vs utilization")
    ax.legend(title="Risk tier", fontsize=8)
    fig.tight_layout()
    return fig


def chart_city_overdue(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    if len(df) == 0:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        ax.set_axis_off()
        return fig
    g = (
        df.groupby("city")
        .agg(overdue_rate=("overdue_flag", "mean"), n=("user_id", "count"))
        .sort_values("overdue_rate", ascending=False)
    )
    ax.bar(g.index, g["overdue_rate"] * 100, color="#8B5CF6")
    ax.set_ylabel("Overdue rate (%)")
    ax.set_title("城市逾期率 / City overdue rate")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    return fig


def run_analysis(
    city, channel, risk_tier, age_group, util_min, util_max, overdue_only, sample_n
):
    df = apply_filters(city, channel, risk_tier, age_group, util_min, util_max, overdue_only)
    metrics = overview_metrics(df)
    insights = auto_insights(df)
    display = df.rename(columns=COL_CN).head(int(sample_n))
    fig1 = chart_channel_conversion(df)
    fig2 = chart_risk_util(df)
    fig3 = chart_city_overdue(df)
    return metrics, insights, display, fig1, fig2, fig3


ALL = "全部 / All"
city_choices = [ALL] + sorted(DF["city"].unique().tolist())
channel_choices = [ALL] + sorted(DF["channel"].unique().tolist())
risk_choices = [ALL] + ["低风险", "中风险", "高风险"]
age_choices = [ALL] + sorted(DF["age_group"].unique().tolist())

INTRO = """
## 张悦伦 · 数据分析作品集 Demo / Zhang Yuelun — Data Analyst Portfolio

**主题 Theme**：消费信贷调研 × 引流转化探索性分析  
（风格对齐花呗用户调研 / 渠道引流复盘）

**本 Demo 展示 Demonstrates**
- **pandas 清洗**：去重、类型转换、缺失处理、范围裁剪  
- **SQL-ish 筛选**：城市 / 渠道 / 风险 / 年龄段 / 使用率区间 ≈ `WHERE`  
- **可视化**：渠道转化、风险×使用率散点、城市逾期率  
- **自动洞察**：基于当前筛选切片的中文结论摘要  

数据为可复现的合成调研样本（600 行），便于本地与 Spaces 轻量启动，无需 GPU。
"""

with gr.Blocks(title="Zhang Yuelun | Credit Drainage Analysis") as demo:
    gr.Markdown(INTRO)
    with gr.Row():
        with gr.Column(scale=1):
            city = gr.Dropdown(city_choices, value=ALL, label="城市 City")
            channel = gr.Dropdown(channel_choices, value=ALL, label="引流渠道 Channel")
            risk_tier = gr.Dropdown(risk_choices, value=ALL, label="风险分层 Risk tier")
            age_group = gr.Dropdown(age_choices, value=ALL, label="年龄段 Age group")
            util_min = gr.Slider(0, 100, value=0, step=1, label="使用率下限 Util % min")
            util_max = gr.Slider(0, 100, value=100, step=1, label="使用率上限 Util % max")
            overdue_only = gr.Checkbox(label="仅逾期样本 Overdue only", value=False)
            sample_n = gr.Slider(10, 100, value=30, step=5, label="表格样本行数 Table sample size")
            btn = gr.Button("运行分析 / Run analysis", variant="primary")
        with gr.Column(scale=2):
            metrics_md = gr.Markdown()
            insights_md = gr.Markdown()

    table = gr.Dataframe(label="筛选样本表 Filtered sample", wrap=True)
    with gr.Row():
        plot1 = gr.Plot(label="Chart 1")
        plot2 = gr.Plot(label="Chart 2")
    plot3 = gr.Plot(label="Chart 3")

    inputs = [city, channel, risk_tier, age_group, util_min, util_max, overdue_only, sample_n]
    outputs = [metrics_md, insights_md, table, plot1, plot2, plot3]
    btn.click(run_analysis, inputs=inputs, outputs=outputs)
    demo.load(run_analysis, inputs=inputs, outputs=outputs)

if __name__ == "__main__":
    demo.launch()
