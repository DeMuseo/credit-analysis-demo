# Project notes — GitHub blurb & Spaces deploy

## Suggested GitHub README blurb (short)

> Interactive Gradio portfolio demo for **** (data analyst). 
> Explores a Huabei-style consumer-credit survey: channel drainage conversion, utilization vs risk, and city overdue rates. 
> Stack: **pandas** cleaning + SQL-ish filters, **matplotlib** charts, bilingual CN/EN UI, auto Chinese insights. 
> Run: `pip install -r requirements.txt && python app.py`

## Hugging Face Spaces — deploy steps (not deployed yet)

Only follow these when you are ready to publish. This project was **not** auto-deployed.

1. Create a Space: https://huggingface.co/new-space 
 - SDK: **Gradio** 
 - Hardware: **CPU basic** (enough for this demo) 
 - Visibility: Public (or Private while drafting)

2. Push this folder as the Space repo root (files at repo root, not nested extra levels):

 ```bash
 # from hf-portfolio-demo/
 git init
 git add app.py requirements.txt README.md data/huabei_style_survey.csv
 git commit -m "Initial Gradio credit drainage portfolio demo"
 # create empty Space first, then:
 git remote add space https://huggingface.co/spaces/<YOUR_HF_USERNAME>/<SPACE_NAME>
 git push space main
 ```

 Or use the Space web UI **Files** tab to upload `app.py`, `requirements.txt`, `README.md`, and `data/huabei_style_survey.csv`.

3. Spaces will build from `requirements.txt` and run `app.py` automatically for Gradio SDK Spaces.

4. Optional: add a Space README YAML header at the top of `README.md`:

 ```yaml
 ---
 title: Credit Drainage Demo
 emoji: 📊
 colorFrom: blue
 colorTo: purple
 sdk: gradio
 sdk_version: "4.44.0"
 app_file: app.py
 pinned: false
 ---
 ```

5. If `huggingface-cli` login / token is unavailable on this machine, deploy from your own laptop or the HF website after `huggingface-cli login`.

## Resume talking points

- Framed as **consumer risk + growth/drainage** analysis (aligns with Huabei survey / channel review experience).
- Emphasize reproducible pipeline: clean → filter → aggregate → visualize → narrate.
- Call out bilingual delivery for cross-team stakeholders.
