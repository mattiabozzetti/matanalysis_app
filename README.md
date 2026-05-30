# Football Scouting Lab

Streamlit app for football player scouting. The first operational module is a **Football Manager / ScoutLab-style Player Card** for outfield players.

## What is included

- Repository-based data loading: no repeated manual upload in the app.
- **Processed dataset committed in the repo**: `data/processed/players_enriched.csv.gz`.
- Raw Excel datasets are **not committed**. They can be kept locally in `data/raw/` when you need to rebuild the processed file.
- Player Card with:
  - raw or possession-adjusted values;
  - non-linear sigmoid possession adjustment;
  - metric families: Final Product, Shooting, Creation, Receiving, Dribbling, Progression, Passing Accuracy, Active Defending, Duels, Ball Security;
  - percentile bars for every metric;
  - selectable percentile context: player league, Big Five, all leagues, custom leagues;
  - selectable role comparison bucket: CB, FB, MF, AM and W, FW;
  - role-weighted overall;
  - two bottom radar charts: Playing Style and Performance, both in percentile units.

## Repository structure

```text
football_scouting_streamlit_app/
├── app.py
├── pages/
│   └── 1_Player_Card.py
├── src/
│   ├── data_loader.py
│   ├── metric_catalog.py
│   ├── preprocessing.py
│   ├── scoring.py
│   └── ui.py
├── scripts/
│   └── build_processed_data.py
├── data/
│   ├── raw/
│   │   └── .gitkeep
│   └── processed/
│       └── players_enriched.csv.gz
├── requirements.txt
└── .streamlit/config.toml
```

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Update the data later

Raw Excel files are ignored by Git so the repo stays light. To rebuild the processed dataset:

1. Put the new Excel files locally in `data/raw/` with these exact names:

```text
Players Dataset.xlsx
Team Dataset.xlsx
GK Dataset.xlsx
```

2. Run:

```bash
python scripts/build_processed_data.py
```

3. Commit only the updated processed file:

```text
data/processed/players_enriched.csv.gz
```

## Current preprocessing rules

- The Saudi `Al-Arabi SC` is normalized as `Al-Arabi SC Saudi` for the team-context join.
- Calendar-year seasons are accepted: if the player file has `2025-2026` and the team file has `2025`, the merge tries a fallback to the first year.
- `Meizhou Hakka` and `Changchun Yatai` are excluded from this first pipeline.
- GK players are not included in the first Player Card module. A GK-specific module will be added later.

## GitHub / Streamlit Cloud note

This version commits only the processed dataset, not the raw Excel files. This is better for GitHub and Streamlit Cloud. Use a private repository if the processed data are not meant to be public.
