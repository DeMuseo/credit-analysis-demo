---
title: Consumer Credit Analysis Demo
emoji: 📊
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 5.49.1
app_file: app.py
pinned: false
license: mit
short_description: Bilingual consumer credit drainage analysis demo
---

# 花呗风格消费信贷调研 · 引流转化分析 Demo

Bilingual Gradio portfolio demo for data-analyst / risk-strategy applications.

## What this is

An interactive analysis app built on synthetic “Huabei-style” consumer credit survey data. It shows how a data analyst would clean survey rows, slice by city / channel / risk tier, and turn the cuts into conversion and overdue metrics plus charts—useful as a portfolio piece for roles that care about drainage (获客引流), credit usage, and early risk signals.

## What’s inside

- **Dataset**: `data/huabei_style_survey.csv` — synthetic users with city, age band, income band, acquisition channel, product, credit limit, utilization, spend, overdue flag, risk tier, and conversion.
- **Filters**: city, channel, risk tier (and related cuts in the UI).
- **Overview metrics**: sample size, overdue rate, conversion rate, high-risk share, average utilization / limit / spend.
- **Charts**: channel conversion, risk mix, utilization vs spend-style views (matplotlib).
- **UI**: bilingual CN/EN Gradio interface.

## Stack

Python · pandas · matplotlib · Gradio

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

## Note on the data

Rows are **synthetic / demo-only**, styled after common consumer-credit survey fields. They are not real customer records and should not be treated as production risk or compliance evidence.
