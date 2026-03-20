# Spotify Music Analytics — Data Pipeline & Dashboard

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.31-red)](https://streamlit.io)
[![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## Overview

An end-to-end data engineering and analytics project built on 85,000 Spotify tracks (2015–2025). The project takes a raw Kaggle CSV, runs it through a modular cleaning pipeline, loads it into a SQLite database with a SQL query layer, and surfaces insights through an interactive multi-page Streamlit dashboard.

Built as a portfolio project to demonstrate real-world data skills: ETL design, exploratory data analysis, SQL analytics, and dashboard development.

## Live Demo

> Deploy to [Streamlit Cloud](https://streamlit.io/cloud) — instructions in Setup section below.

## Dashboard Preview

| Overview | Audio Features Explorer |
|----------|------------------------|
| KPI cards, top artists, genre distribution | Interactive scatter, correlation heatmap, filters |

| Trend Analysis | Artist Deep Dive |
|----------------|-----------------|
| Popularity over time, stacked area chart | Radar chart, track table, head-to-head comparison |

## Architecture

```
Raw CSV (85k rows)
      │
      ▼
┌─────────────────┐
│  data_cleaning  │  normalize → dedupe → fill nulls → fix types → engineer features
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   pipeline.py   │  ETL: cleaned CSV → SQLite (3 tables: tracks, artists, genres)
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
queries.py  spotify_cleaned.csv
(SQL layer)       │
    │             │
    └──────┬───────┘
           ▼
    ┌─────────────┐
    │  Streamlit  │  4-page interactive dashboard
    │  dashboard  │
    └─────────────┘
```

## Key Insights

1. **Danceability is the #1 popularity predictor** — tracks with danceability > 0.6 consistently outperform average. Vocal-led, groove-heavy tracks dominate streaming charts.

2. **Genre boundaries are blurring** — the popularity gap between genres has narrowed year-on-year (2015–2025). Audio energy and mood now matter more than genre label.

3. **The 3–4 minute sweet spot is real** — tracks in this range score the highest average popularity. Ultra-short (<2 min) and long-form (>6 min) tracks underperform on streaming metrics.

4. **Instrumentalness kills chart performance** — high instrumentalness is strongly negatively correlated with popularity. 80%+ of high-performing tracks have a lead vocalist.

5. **Consistent artists beat one-hit wonders** — prolific artists (10+ tracks) show lower popularity variance and higher average scores, likely due to algorithmic playlist reinforcement.

## Tech Stack

| Tool | Purpose |
|------|---------|
| **Python 3.10+** | Core language |
| **pandas 2.2** | Data manipulation & cleaning |
| **matplotlib + seaborn** | Static visualisations (notebooks) |
| **Plotly** | Interactive visualisations (dashboard) |
| **SQLite** | Relational database layer |
| **Streamlit 1.31** | Web dashboard framework |
| **Jupyter** | Exploratory analysis notebooks |

## Project Structure

```
01-spotify-data-pipeline/
├── data/
│   ├── raw/                          # Original CSV (gitignored)
│   └── processed/                    # spotify_cleaned.csv + spotify.db
├── notebooks/
│   ├── 01_data_loading.ipynb         # Shape, dtypes, nulls, distributions
│   ├── 02_cleaning.ipynb             # Step-by-step cleaning with before/after
│   ├── 03_eda.ipynb                  # 15 visualisations across 5 sections
│   └── 04_insights.ipynb             # 5 business insights with SQL queries
├── src/
│   ├── __init__.py
│   ├── data_cleaning.py              # Reusable cleaning functions
│   ├── pipeline.py                   # ETL: CSV → clean → SQLite
│   └── queries.py                    # SQL query helper functions
├── dashboard/
│   └── app.py                        # 4-page Streamlit dashboard
├── assets/
│   └── architecture.png              # Pipeline diagram
├── requirements.txt
├── .gitignore
├── setup.sh
└── README.md
```

## Setup & Installation

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/01-spotify-data-pipeline.git
cd 01-spotify-data-pipeline

# 2. Run setup (creates venv and installs dependencies)
chmod +x setup.sh && ./setup.sh
source venv/bin/activate

# 3. Add the dataset
# Download from: https://www.kaggle.com/datasets/rohiteng/spotify-music-analytics-dataset-20152025
# Place the CSV file at: data/raw/spotify_2015_2025_85k.csv

# 4. Run the ETL pipeline
python src/pipeline.py

# 5. Launch the dashboard
streamlit run dashboard/app.py
```

### Deploy to Streamlit Cloud

1. Push this repo to GitHub (the `data/processed/` folder must contain `spotify_cleaned.csv`)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo, set main file to `dashboard/app.py`
4. Click Deploy

## Data Pipeline Details

**Source:** Spotify Music Analytics Dataset (Kaggle) — 85,000 tracks, 19 columns

**Cleaning steps applied:**
- Column names normalised to `lowercase_snake_case`
- Duplicate rows removed (0 found in this dataset)
- Missing values: text columns → `'Unknown'`, numerical → median fill
- `release_date` converted from string to `datetime64`
- `mode`, `key` converted to categorical dtype (they're musical labels, not numbers)
- `explicit` converted to boolean

**Features engineered:**
- `release_year`, `release_month` — extracted from `release_date`
- `duration_min` — duration in minutes (more human-readable than ms)
- `popularity_tier` — Low / Medium / High buckets (0-33 / 34-66 / 67-100)
- `energy_level` — Low / Medium / High based on energy score
- `is_danceable` — boolean flag (danceability > 0.6)
- `stream_millions` — stream count in millions

**SQLite schema (3 tables):**
- `tracks` — all 85,000 rows with all original + engineered columns
- `artists` — aggregated per artist: track count, avg popularity, avg audio features, total streams
- `genres` — aggregated per genre: same metrics as artists

## Notebooks

| Notebook | What it covers |
|----------|----------------|
| `01_data_loading` | Raw data inspection — shape, dtypes, nulls, duplicates, value distributions |
| `02_cleaning` | Step-by-step cleaning with before/after comparisons and a final Data Quality Report |
| `03_eda` | 15 charts: distributions, correlations, categorical analysis, time trends, pair plots |
| `04_insights` | 5 business insights backed by SQL queries and supporting visualisations |

## What I Learned

- How to design a modular, reusable ETL pipeline with proper separation of concerns
- Handling real-world data quality issues (type mismatches, sparse nulls, categorical encoding)
- Building a multi-table SQLite schema and a SQL query abstraction layer
- Dashboard design principles: KPIs first, filters in sidebar, interactive charts with Plotly
- Git workflow for data projects: gitignoring raw data while committing processed outputs

## License

MIT - free to use, modify, and distribute.
