# Power BI DAX Measures

This file contains all DAX measures created for the MIMIC-IV healthcare analytics project.

## 1. Hospital Overview

```DAX
Total Patients =
DISTINCTCOUNT(vw_admission_overview[patient_id])
```

```DAX
Total Admissions =
DISTINCTCOUNT(vw_admission_overview[admission_id])
```

```DAX
Average LOS =
AVERAGE(vw_admission_overview[length_of_stay_days])
```

```DAX
In-Hospital Deaths =
CALCULATE(
    DISTINCTCOUNT(vw_admission_overview[admission_id]),
    vw_admission_overview[died_in_hospital] = TRUE()
)
```

```DAX
30-Day Readmissions =
CALCULATE(
    DISTINCTCOUNT(vw_admission_overview[admission_id]),
    vw_admission_overview[is_30_day_readmission] = TRUE()
)
```

```DAX
Readmission Rate =
DIVIDE(
    [30-Day Readmissions],
    [Total Admissions],
    0
)
```

> Format `Readmission Rate` as a percentage.

## 2. Diagnosis Analysis

```DAX
Diagnosis Records =
COUNTROWS(vw_diagnosis_analysis)
```

```DAX
Diagnosed Patients =
DISTINCTCOUNT(vw_diagnosis_analysis[patient_id])
```

```DAX
Primary Diagnoses =
CALCULATE(
    COUNTROWS(vw_diagnosis_analysis),
    vw_diagnosis_analysis[is_primary_diagnosis] = TRUE()
)
```

## 3. Medication Analysis

```DAX
Total Prescriptions =
COUNTROWS(vw_prescription_analysis)
```

```DAX
Patients Receiving Medication =
DISTINCTCOUNT(vw_prescription_analysis[patient_id])
```

```DAX
Unique Drugs =
DISTINCTCOUNT(vw_prescription_analysis[drug_name])
```

```DAX
Avg Prescription Duration =
AVERAGE(
    vw_prescription_analysis[prescription_duration_days]
)
```

## 4. Hospital Operations

```DAX
Total Transfers =
COUNTROWS(vw_transfer_analysis)
```

```DAX
Transferred Patients =
DISTINCTCOUNT(vw_transfer_analysis[patient_id])
```

```DAX
Avg Transfer Duration =
AVERAGE(vw_transfer_analysis[transfer_duration_hours])
```

```DAX
Total Procedures =
COUNTROWS(vw_procedure_analysis)
```

```DAX
Procedure Patients =
DISTINCTCOUNT(vw_procedure_analysis[patient_id])
```

## Summary

A total of **18 DAX measures** were created across four Power BI dashboard pages:

- Hospital Overview
- Diagnosis Analysis
- Medication Analysis
- Hospital Operations
