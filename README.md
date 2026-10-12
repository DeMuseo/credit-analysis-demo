---
title: Cookie Cats A/B Retention Demo
emoji: 🐱
colorFrom: orange
colorTo: purple
sdk: gradio
sdk_version: 5.49.1
app_file: app.py
pinned: false
license: mit
short_description: Bilingual Cookie Cats mobile game A/B retention demo
---

# Cookie Cats · 手游关卡门控 A/B 留存 Demo

Bilingual Gradio portfolio demo for **game strategy / growth analytics** roles.

Interactive analysis of the classic **Cookie Cats** gate A/B experiment: players were randomly assigned to `gate_30` (control) or `gate_40` (first gate moved later). The app slices by version and playtime band, then surfaces D1/D7 retention, rounds distribution, and a simple churn proxy.

## What / Why

Mobile games often force a wait (or IAP) at a “gate.” Moving that gate changes early progression friction and can move **day-1 / day-7 retention**. This demo shows a reproducible analyst workflow:

1. Load real experiment rows  
2. Filter by version & playtime bands  
3. Aggregate retention & engagement  
4. Chart gate comparison, rounds distribution, churn-by-band  
5. Narrate short bilingual auto-insights for stakeholders  

Useful as a portfolio piece for game ops, product analytics, and A/B strategy interviews.

## Dataset (real experiment — not synthetic)

| Item | Detail |
|------|--------|
| File | `data/cookie_cats.csv` (~90,189 players) |
| Columns | `userid`, `version` (`gate_30` / `gate_40`), `sum_gamerounds`, `retention_1`, `retention_7` |
| Kaggle | [mursideyarkin/mobile-games-ab-testing-cookie-cats](https://www.kaggle.com/datasets/mursideyarkin/mobile-games-ab-testing-cookie-cats) |
| Mirror used here | [ryanschaub/Mobile-Games-A-B-Testing-with-Cookie-Cats](https://github.com/ryanschaub/Mobile-Games-A-B-Testing-with-Cookie-Cats) (`cookie_cats.csv` raw) |
| Attribution | **Tactile Entertainment** (Cookie Cats). Dataset commonly used in DataCamp / Kaggle A/B tutorials. |

See `data/SOURCE.md` for download notes. This is **real Cookie Cats A/B experiment data**, not synthetic survey rows.

## What’s in the app

- **Overview metrics**: n, D1/D7 by version, mean/median rounds, churn proxy  
- **Filters**: version (`all` / `gate_30` / `gate_40`), playtime bands (0, 1–5, …, 101+)  
- **Charts**: retention by gate, rounds distribution (density, p99-capped), churn proxy by band × version  
- **Auto-insights**: short CN/EN strategy notes (gate keep vs move, activation, bands)  
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

GitHub repo name may still be `credit-analysis-demo` (legacy). Content and branding are **Cookie Cats / mobile game A/B retention**, not consumer credit.
