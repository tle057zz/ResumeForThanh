# Power BI

**Published dashboard:** [MIMIC Analytics Dashboard](https://app.powerbi.com/view?r=eyJrIjoiYWIwMDQ2MmItZTk2YS00NmRkLTlmNmUtMDljMjUwYTY1MWU0IiwidCI6ImJlOTdiY2NhLWEzZTItNDc4Yy1iMWM1LWQ5YTRkMWI2NTY3YyJ9)

**DAX measures:** [mimic_powerbi_dax_measures.md](mimic_powerbi_dax_measures.md) — all 18 measures across four dashboard pages.

Place Power BI desktop files (`.pbix`) and connection notes here.

## Data sources

Power BI connects to the Databricks SQL Warehouse, querying Gold-layer views in `workspace.mimic`:

- `vw_admission_overview`
- `vw_diagnosis_analysis`
- `vw_prescription_analysis`
- `vw_transfer_analysis`
- `vw_procedure_analysis`
