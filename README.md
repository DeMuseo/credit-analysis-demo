---
title: Tap4Fun F2P Pay-Rate Demo
emoji: 🎮
colorFrom: blue
colorTo: orange
sdk: gradio
sdk_version: 5.49.1
app_file: app.py
pinned: false
license: mit
short_description: Bilingual Tap4Fun China F2P pay-rate monetization demo
---

# Tap4Fun · DataCastle 付费率 / 转化 Demo

Bilingual Gradio portfolio demo for **game strategy / monetization (China F2P)** roles.

Interactive analysis of **Tap4Fun / DataCastle《野蛮时代》付费预测** schema: first-7-day behavior → optional 45-day `prediction_pay_price`. The app surfaces **付费率**, `pay_count`, `pay_price`, ARPU/ARPPU, and payer vs non-payer engagement — framed as **game commercial ops**, not credit scoring.

## What / Why

China F2P titles typically convert only ~**2%** of new users to payers. Analysts slice by progression (e.g. stronghold level), online time, and PVP/PVE to find conversion levers and early LTV signals.

1. Load Tap4Fun-schema player rows  
2. Filter by payer status / online band / stronghold band  
3. Aggregate 付费率, ARPU, ARPPU, pay_count  
4. Chart pay rate × stronghold, pay_price distribution, engagement contrast  
5. Narrate short bilingual auto-insights for stakeholders  

## Dataset

| Item | Detail |
|------|--------|
| File | `data/tap4fun_sample.csv` (100k rows, ~2% payers) |
| Key fields | `pay_price`, `pay_count`, `prediction_pay_price`, `avg_online_minutes`, `bd_stronghold_level`, PVP/PVE |
| Competition | DataCastle 2018 游戏玩家付费金额预测（Tap4Fun） |
| Notes | See `data/SOURCE.md` — full ~2.3M train mirrors were unreachable without login; sample is schema-faithful & calibrated to published aggregates |

Secondary: Cookie Cats A/B retention CSV under `data/cookie_cats/` (not main UI).

## What’s in the app

- **Overview**: n, 7d/45d 付费率, pay_price revenue, ARPU/ARPPU, mean pay_count  
- **Filters**: payer status, online-time bands, stronghold bands  
- **Charts**: pay rate × stronghold, 7d pay_price distribution, payer vs non-payer engagement  
- **Auto-insights**: CN/EN monetization notes  
- **UI**: bilingual 中文 / English Gradio  

## Stack

Python · pandas · matplotlib · Gradio

## Run locally

```bash
cd hf-portfolio-demo   # or clone this repo
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open the local Gradio URL (default `http://127.0.0.1:7860`).

## Repo note

GitHub repo name may still be `credit-analysis-demo` (legacy). Content and branding are **Tap4Fun / China F2P 付费率 & monetization**, not consumer credit.
