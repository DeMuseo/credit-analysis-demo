# 消费信贷 × 引流分析 Gradio Demo

**作者 Author**: 张悦伦 (Zhang Yuelun) — 求职向数据分析作品集  
**主题**: 花呗风格用户调研 / 渠道引流转化 · 探索性分析

## What this demonstrates

| Skill | How it shows up in the app |
| --- | --- |
| **pandas cleaning** | Deduplicate `user_id`, coerce numerics, clip utilization to 0–100, drop null keys |
| **SQL-ish filters** | City / channel / risk / age / utilization range ≈ `WHERE`; group metrics ≈ `GROUP BY` + `AVG` |
| **Visualization** | Matplotlib: channel conversion bars, risk×utilization scatter, city overdue rates |
| **Insight writing** | Auto-generated short Chinese conclusions from the filtered slice |

Dataset: bundled synthetic survey CSV (`data/huabei_style_survey.csv`, 600 rows) so the app starts lightly with no GPU and no heavy Hugging Face download.

## Run locally

```bash
cd hf-portfolio-demo   # or your clone path
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Or one-liner if a venv is already active: `pip install -r requirements.txt && python app.py`

Then open the local Gradio URL printed in the terminal (usually `http://127.0.0.1:7860`).

Verified locally with Gradio 5.x + pandas 2.x + matplotlib 3.x (CPU only).

## Project layout

```
hf-portfolio-demo/
├── app.py                          # Gradio UI + analysis
├── data/huabei_style_survey.csv    # bundled sample data
├── requirements.txt
├── README.md
└── PROJECT_NOTES.md                # GitHub blurb + Spaces deploy notes
```

## Notes

- Bilingual UI labels (Chinese / English).
- Charts use a CJK-capable font when available; otherwise labels may fall back to DejaVu.
- This repo does **not** assume a live Hugging Face Space unless you deploy one yourself (see `PROJECT_NOTES.md`).
