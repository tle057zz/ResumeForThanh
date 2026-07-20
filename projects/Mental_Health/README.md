# Mental Health Analytics & Reporting System

An end-to-end analytics project exploring teen mental health patterns. It includes:
- A Power BI model and dashboards for business-facing insights
- A Python application (Dash + Plotly + Flask + SQLite) integrated into the portfolio site for interactive analysis

Live links:
- Live Dash app: `https://www.thanhle.it.com/mental-health/`
- Power BI report: `https://app.powerbi.com/view?r=eyJrIjoiNTAxMDY3MTUtMDg4Ni00M2IzLThhN2ItMmMzZGVmNzBmMGQ1IiwidCI6ImJlOTdiY2NhLWEzZTItNDc4Yy1iMWM1LWQ5YTRkMWI2NTY3YyJ9`

> Note: On free/low-resource cloud instances, Dash interactions may feel slower. The Power BI report provides a smooth hosted alternative.

## Features

- Star-schema data model (fact + dimensions for Age, Gender, Platform, Social Interaction)
- Cross-filtering visuals and DataTables with robust selection/deselection
- KPI cards and multi-tab dashboards:
  - Overview, Social Media Impact, Stress & Anxiety, Demographics & Lifestyle
- “Key Insights” written sections under each dashboard
- Responsive layout and small-page DataTables for low-memory deployments
- Download link for the original dataset
- Robust data-path resolution via environment variable

## Tech Stack

- Data: CSVs (processed star schema), Pandas
- Visualization: Plotly Express/Graph Objects, Dash
- Web: Flask (Dash mounted at `/mental-health/`)
- BI: Power BI (DAX, Power Query, Data Modelling)
- Storage: SQLite (site analytics)

## Data and Paths

Expected processed files inside a single folder (set once via env var):
- `Fact_TeenMentalHealth.csv`
- `Dim_Age.csv`
- `Dim_Gender.csv`
- `Dim_Platform.csv`
- `Dim_SocialInteraction.csv`

The Dash app resolves the data directory in this order:
1) `MENTAL_HEALTH_DATA_DIR` environment variable (recommended for production)
2) `projects/Mental_Health/processed`
3) `<repo root>/projects/Mental_Health/processed`

Raw file for reference: `Teen_Mental_Health_Dataset.csv`  
Notebook used for preprocessing: `teen_mental_health_preprocessing.ipynb`

## Local Development

Prerequisites: Python 3.12+

```bash
# from repo root
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# optional, if data lives outside the repo
export MENTAL_HEALTH_DATA_DIR="/absolute/path/to/processed"

# run the site (Dash is mounted in Flask)
export FLASK_APP=app.py
flask run -p 8000
# or: python app.py  (set debug/use_reloader in code as preferred)
```

Open: `http://127.0.0.1:8000/mental-health/`

Dataset download (served by Flask): `http://127.0.0.1:8000/mental-health/download`

## Production (example)

```bash
export MENTAL_HEALTH_DATA_DIR="/absolute/path/to/processed"
gunicorn -w 2 -b 0.0.0.0:8000 "app:app"
```

Ensure your reverse proxy allows the mounted subpath `/mental-health/`. The Dash registration happens at Flask import time.

## Repository Structure (excerpt)

```
projects/
  Mental_Health/
    dash_app.py
    processed/
      Dim_Age.csv
      Dim_Gender.csv
      Dim_Platform.csv
      Dim_SocialInteraction.csv
      Fact_TeenMentalHealth.csv
    Teen_Mental_Health_Dataset.csv          # optional raw reference
    teen_mental_health_preprocessing.ipynb  # preprocessing steps
    README.md
```

## Resume Entry (LaTeX)

Copy-paste the following snippet directly into your LaTeX resume:

```latex
\resumeProjectHeading
  {\textbf{Mental Health Analytics \& Reporting System} $|$
  \footnotesize\emph{
  Python (Pandas, Plotly, Plotly Dash, Flask),
  SQLite,
  Power BI (DAX, Power Query, Data Modelling)}}%
  {}

\resumeItemListStart

  \resumeItem{
  Converted broad questions about digital behaviour and mental health into
  measurable reporting requirements, audience segments, KPIs, and interactive
  analysis features.
  }

  \resumeItem{
  Used \textbf{Python, Pandas, and Power Query} to clean, transform,
  standardise, and validate behavioural, demographic, and platform data.
  }

  \resumeItem{
  Designed a Power BI star schema with a fact table and dimensions for age,
  gender, platform, and interaction, enabling reliable filtering and
  cross-segment analysis.
  }

  \resumeItem{
  Developed \textbf{12+ DAX measures} and
  \textbf{four Power BI dashboards with 10+ visualisations}, using KPI cards,
  slicers, drill-down analysis, and cross-filtering.
  }

  \resumeItem{
  Rebuilt the reporting solution as an interactive analytical application
  using Pandas, Plotly Dash, Flask, and SQLite, adding automated insights,
  filters, responsive charts, and downloadable outputs.
  }

  \resumeItem{
  Identified \textbf{351 high-usage users}, representing
  \textbf{29\% of the dataset}, and documented findings and limitations for
  further investigation.
  }

  \resumeItem{
  \href{https://github.com/tle057zz/ResumeForThanh/tree/main/projects/Mental_Health}
  {\underline{GitHub}}
  $|$
  \href{https://www.thanhle.it.com/mental-health/}
  {\underline{Live Demo}}
  }

\resumeItemListEnd
```

