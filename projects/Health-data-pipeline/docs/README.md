# Healthcare Claims, Patient Outcomes and Hospital Utilisation Data Platform

An end‑to‑end analytical engineering project using synthetic Synthea healthcare data. The platform:

- Validates 16 CSV source tables against a strict source contract (headers, keys)
- Ingests unchanged records into a persisted DuckDB warehouse
- Transforms with dbt (staging → tested dimensional marts)
- Orchestrates the refresh in Dockerised Apache Airflow
- Exports curated marts as CSV for a Power BI model

Because the source data is synthetic, all metrics and findings are demonstrations only, not clinical findings.

## Project objectives

The completed platform will answer questions such as:

- Which conditions have the highest prevalence?
- Which patient groups have the highest healthcare utilisation?
- What is the average cost per encounter?
- How much cost is covered by payers versus patients?
- Which providers and organisations handle the most encounters?
- Which procedures and medications generate the highest costs?
- What percentage of patients return within 30 days?
- How do encounter volumes and costs change over time?

## Data source

The source is a Synthea CSV sample export. [Synthea](https://synthetichealth.github.io/synthea/) is an open-source generator of realistic-but-not-real patient histories.

The source files remain unchanged in `csv/`. The extract includes 16 tables:

`allergies`, `careplans`, `conditions`, `devices`, `encounters`, `imaging_studies`, `immunizations`, `medications`, `observations`, `organizations`, `patients`, `payer_transitions`, `payers`, `procedures`, `providers`, and `supplies`.

`supplies.csv` is valid but has no data rows in this extract.

## Architecture

```text
Synthea CSV files
        |
        v
Python validation and ingestion (DuckDB Python API)
        |
        v
DuckDB: raw and audit schemas
        |
        v
dbt: staging, intermediate, and marts schemas
        |
        v
CSV exports in data/csv_output
        |
        v
Power BI
```

Apache Airflow will orchestrate the full pipeline after the transformation and export layers are completed.

## Tech stack and tools

- Python 3.11+ (DuckDB Python API, standard library)
- DuckDB (embedded columnar analytics database)
- dbt Core with dbt‑duckdb adapter (SQL transformations and testing)
- Apache Airflow (Docker Compose for local orchestration)
- Power BI (DAX, Power Query, star‑schema modelling)
- Testing: pytest
- Packaging/runtime: `requirements.txt`, virtualenv

## Project structure

```text
.
├── csv/                         # Immutable Synthea CSV source files
├── data/
│   └── warehouse/
│       └── healthcare.duckdb    # Persisted DuckDB warehouse (created after ingestion)
├── src/
│   ├── config.py                # Source-table registry and project paths
│   ├── ingest.py                # CSV validation, audit logging, and DuckDB raw loading
│   ├── run_pipeline.py          # Ingestion command-line entry point
│   └── run_sql.py               # Execute a .sql file with DuckDB
├── sql/analysis/
│   └── check_raw_load.sql       # Raw versus audit row-count reconciliation
├── dbt_healthcare/
│   ├── dbt_project.yml          # dbt project configuration
│   ├── profiles.yml             # Local DuckDB connection profile
│   ├── macros/                  # dbt schema and generic test macros
│   └── models/
│       ├── schema/              # dbt sources and staging tests
│       ├── staging/             # Typed, standardised source models
│       ├── intermediate/        # Reserved for reusable business logic
│       └── marts/               # Reserved for Power BI dimensional models
├── airflow/                     # Reserved for future Airflow DAGs
├── docs/
│   └── project_report.html      # Detailed project report
└── requirements.txt
```

## Prerequisites and setup

Use Python 3.11 or later and create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The required Python packages are:

- `duckdb`
- `pytest`
- `dbt-core`
- `dbt-duckdb`

If dbt installation encounters an SSL certificate verification error:

```bash
python -m pip install --upgrade pip certifi
export SSL_CERT_FILE="$(python -m certifi)"
export REQUESTS_CA_BUNDLE="$SSL_CERT_FILE"
pip install --prefer-binary dbt-core dbt-duckdb
```

Do not disable SSL verification or use `--trusted-host`.

## Step 1: Validate and load source CSV files

Run from the project root:

```bash
python src/run_pipeline.py
```

The ingestion process:

1. Confirms every expected source file exists.
2. Validates exact CSV headers.
3. Checks configured primary keys for blank and duplicate values.
4. Allows the intentionally empty `supplies.csv` file.
5. Loads each source table unchanged into the DuckDB `raw` schema.
6. Writes pipeline and table-level audit records to the DuckDB `audit` schema.

The database is saved at:

```text
data/warehouse/healthcare.duckdb
```

### Inspect raw-load reconciliation

```bash
python src/run_sql.py sql/analysis/check_raw_load.sql
```

The reconciliation query compares source and loaded row counts recorded in `audit.table_loads` with the current `raw` tables. The initial run reconciled all 16 tables successfully.

## Step 2: Configure and verify dbt

Move into the dbt project:

```bash
cd dbt_healthcare
dbt debug --profiles-dir .
```

The dbt profile connects to `../data/warehouse/healthcare.duckdb`. The project uses a custom `generate_schema_name` macro so models are built in the exact schemas `staging`, `intermediate`, and `marts`.

## Step 3: Build staging models

The staging layer converts raw VARCHAR values into typed columns and standardises source names to `snake_case`.

Run every staging model:

```bash
dbt run --select staging --profiles-dir .
```

Or run an individual model:

```bash
dbt run --select stg_encounters --profiles-dir .
```

Completed staging models:

| Model | Purpose |
| --- | --- |
| `stg_patients` | Patient demographics, geography, expenses, and coverage |
| `stg_encounters` | Central utilisation, provider, organisation, payer, and claim-cost events |
| `stg_organizations` | Healthcare organisation attributes and utilisation |
| `stg_providers` | Provider attributes and organisation relationship |
| `stg_payers` | Payer reference, coverage, and aggregate financial metrics |
| `stg_conditions` | Patient diagnosis and condition events |
| `stg_procedures` | Procedure events and base costs |
| `stg_medications` | Medication events, dispenses, and payer coverage |
| `stg_immunizations` | Immunization events and base costs |
| `stg_observations` | Clinical measurements and observation values |
| `stg_payer_transitions` | Longitudinal patient payer coverage |
| `stg_allergies` | Allergy records |
| `stg_careplans` | Care-plan records and reasons |
| `stg_devices` | Device records |
| `stg_imaging_studies` | Imaging-study, body-site, and modality records |
| `stg_supplies` | Supply records; currently produces an empty, schema-complete model |

## Step 4: Run dbt data-quality tests

```bash
dbt test --profiles-dir .
```

The current test suite validates:

- Unique and non-null primary identifiers for core entities.
- Encounter relationships to patients, organisations, providers, and payers.
- Clinical-event relationships to patients and encounters.
- Non-negative cost, utilisation, quantity, and coverage values.

All current staging tests pass.

## Step 5: Build dimensional marts

The completed mart layer provides a Power BI-ready star schema:

| Model | Purpose |
| --- | --- |
| `dim_patient` | Patient demographics, location, and aggregate healthcare expense/coverage measures |
| `dim_organization` | Healthcare organisation attributes and utilisation |
| `dim_provider` | Provider attributes, specialty, and organisation relationship |
| `dim_payer` | Payer reference, coverage, revenue, and membership measures |
| `dim_date` | Calendar attributes for consistent Power BI time-trend analysis |
| `fact_encounter` | Central encounter utilisation, claim cost, payer coverage, and patient responsibility |
| `fact_condition` | Patient condition events and active-condition indicator |
| `fact_procedure` | Procedure events and base costs |
| `fact_medication` | Medication events, total cost, payer coverage, and patient responsibility |
| `fact_immunization` | Immunization events and base costs |
| `fact_readmission` | Inpatient encounters with a 30-day inpatient/emergency return indicator |

Build every mart:

```bash
dbt run --select path:models/marts --profiles-dir .
```

`fact_readmission` uses a completed inpatient encounter as the denominator and flags a later inpatient or emergency encounter within 30 days. It is a synthetic-data operational demonstration, not a clinical readmission measure.

Run all dbt tests, including staging and marts:

```bash
dbt test --profiles-dir .
```

All current mart tests pass.

## Step 6: Export Power BI CSV files

Run from the project root:

```bash
python src/export_powerbi_csv.py
```

The export creates 11 curated mart CSV files and `export_manifest.csv` in
`data/csv_output/`. The manifest records the UTC export timestamp, source table,
file name, and row count for refresh reconciliation.

## Step 7: Run Airflow orchestration in Docker

Docker Desktop must be running. Start Airflow from the project root:

```bash
docker compose up --build -d
docker compose logs -f airflow
```

Open `http://localhost:8080`. To retrieve the generated local development
password:

```bash
docker compose exec airflow cat /opt/airflow/simple_auth_manager_passwords.json.generated
```

Trigger `healthcare_pipeline` manually in the Airflow UI. It runs:

```text
validate_and_load → dbt_run → dbt_test → export_powerbi_csv
```

The successful run confirms the complete automated path from the source CSVs
through validated DuckDB marts to Power BI CSV outputs.

## Current status

Completed:

- Project folder structure.
- Python CSV validation and DuckDB ingestion.
- Raw and audit schemas with row-count reconciliation.
- Reusable Python SQL-file runner.
- dbt-DuckDB configuration and raw source definitions.
- All 16 typed staging models.
- dbt staging-model quality tests.
- Five conformed dimensions and six analytical fact marts.
- dbt mart quality tests for keys, relationships, and non-negative financial values.
- Power BI CSV export and refresh manifest.
- Dockerised Apache Airflow DAG with a verified successful end-to-end run.

Next:

1. Build Power BI dashboards from the exported CSV files.
2. Add supplementary dashboard aggregates only if measures require them.
3. Add Docker and dbt checks to GitHub Actions CI.

## Documentation

Open [`docs/project_report.html`](docs/project_report.html) in a browser for a detailed project report, data inventory, ingestion demonstration, and architecture overview.
